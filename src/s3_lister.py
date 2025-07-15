import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dateutil.tz import tzutc
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import ListBucketsOutputTypeDef
from .aws_config import get_aws_config
from .pricing_service import PricingService
from typing import AsyncContextManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Lister:
    """S3 bucket analysis and cost estimation service."""
    
    def __init__(self):
        """Initialize the S3 lister with AWS session and service dependencies."""
        self.session = aioboto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        self.aws_config = get_aws_config()
        self.pricing_service = PricingService()

    async def get_bucket(self, name: str, creation_date: Optional[datetime] = None) -> Optional[Dict]:
        """
        Get information about a specific S3 bucket.
        
        Args:
            name: The bucket name to analyze
            creation_date: Optional creation date (if already known from list_buckets)
            
        Returns:
            Dictionary containing bucket information or None if bucket is empty/inaccessible
        """
        logger.info(f"Getting bucket with name {name}")

        try:
            s3_client_context = self.session.client(
                "s3", 
                endpoint_url=self.endpoint_url, 
                config=self.aws_config
            )
        
            async with s3_client_context as s3_client:
                # Get creation date if not provided
                if creation_date is None:
                    creation_date = await self._get_bucket_creation_date(s3_client, name)
                
                # Process bucket objects and calculate cost per object
                object_count, bucket_size, last_modified, estimated_cost = await self._process_bucket_objects(s3_client, name)
            
            if object_count == 0:
                return None
            
            estimated_cost = round(estimated_cost, 4)
            size_gb = bucket_size / (1024 ** 3)
            
            result = {
                "name": name,
                "creation_date": creation_date,
                "nb_files": object_count,
                "total_size_bytes": bucket_size,
                "total_size_gb": round(size_gb, 4),
                "last_modified": last_modified,
                "estimated_monthly_cost_usd": estimated_cost,
            }
            
            return result
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"Failed to process bucket '{name}': {error_code}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing bucket '{name}': {e}")
            return None

    async def list_buckets(self) -> List[Dict]:
        """
        List all S3 buckets and their information.
        
        Returns:
            List of dictionaries containing bucket information
        """
        all_buckets_info = []
        results = []
                
        # Process buckets concurrently with optional rate limiting
        max_concurrent_str = os.getenv("MAX_CONCURRENT_BUCKETS", "").strip()
        max_concurrent = int(max_concurrent_str) if max_concurrent_str.isdigit() else None
        
        # Create semaphore only if we have a valid limit
        semaphore = asyncio.Semaphore(max_concurrent) if max_concurrent else None
        
        try:
            s3_client_context = self.session.client(
                "s3", 
                endpoint_url=self.endpoint_url, 
                config=self.aws_config
            )
        
            async with s3_client_context as s3_client:
                # List all buckets
                response = await s3_client.list_buckets()
                buckets = response.get("Buckets", [])
                
                if not buckets:
                    logger.info("No buckets found in account")
                    return []
                
                # Warning about potential costs and confirmation
                bucket_count = len(buckets)
                logger.warning(f"Found {bucket_count} buckets. Analyzing all buckets may incur API costs.")
                
                if not self._prompt_user_confirmation(bucket_count):
                    logger.info("Operation cancelled by user")
                    sys.exit(0)
                
                # Process all buckets concurrently  
                tasks = [self._process_single_bucket(semaphore, bucket) for bucket in buckets]
                results = await asyncio.gather(*tasks, return_exceptions=True)
        
        except ClientError as e:
            logger.error(f"Failed to list buckets: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
            
        # Filter out None results and exceptions
        for result in results:
            if isinstance(result, dict):
                all_buckets_info.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Exception during bucket processing: {result}")
        
        return all_buckets_info
    
    async def __aenter__(self) -> "S3Lister":
        """Enter async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit async context manager."""
        pass

    async def _get_bucket_creation_date(self, s3_client: S3Client, bucket_name: str) -> Optional[datetime]:
        """
        Get bucket creation date by listing all buckets and filtering.
        NOTE: This is known to be inefficient for accounts with many buckets,
        but sadly there is no direct API to get creation date for a single bucket.
        """
        try:
            response: Optional[ListBucketsOutputTypeDef] = await s3_client.list_buckets()
            for bucket_info in response.get("Buckets", []):
                if bucket_info["Name"] == bucket_name:
                    return bucket_info["CreationDate"]
            return None
        except Exception as e:
            logger.error(f"Failed to get creation date for bucket {bucket_name}: {e}")
            return None

    async def _process_bucket_objects(self, s3_client: S3Client, bucket_name: str) -> tuple[int, int, datetime, float]:
        """
        Process all objects in a bucket using recursive prefix listing and return 
        count, size, last modified date, and estimated monthly cost.
        
        This implementation is based on the approach described in:
        "Listing 67 Billion Objects in 1 Bucket" by Joshua Robinson
        https://joshua-robinson.medium.com/listing-67-billion-objects-in-1-bucket-806e4895130f
        
        This method is more efficient than sequential pagination for buckets with 
        hierarchical folder structures as it can process prefixes in parallel.
        """
        last_modified = datetime.min.replace(tzinfo=tzutc())
        object_count = 0
        bucket_size = 0
        estimated_monthly_cost = 0.0

        async def _list_prefix(current_prefix: str = "", delimiter: str = "/") -> AsyncGenerator[Dict, None]:
            """Recursively list objects under a specific prefix."""
            paginator = s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=bucket_name,
                Prefix=current_prefix,
                Delimiter=delimiter
            )
            
            async for page in page_iterator:
                # Yield files directly under this prefix
                for obj in page.get("Contents", []):
                    yield obj
                
                # Recursively process subdirectories
                for common_prefix in page.get("CommonPrefixes", []):
                    sub_prefix = common_prefix["Prefix"]
                    async for sub_obj in _list_prefix(sub_prefix, delimiter):
                        yield sub_obj
        
        # Process all objects using recursive listing
        async for obj in _list_prefix():
            if obj["LastModified"] > last_modified:
                last_modified = obj["LastModified"]
            object_count += 1
            
            # Get storage class (defaults to STANDARD if not specified)
            storage_class = obj.get("StorageClass", "STANDARD")
            obj_size = obj["Size"]
            bucket_size += obj_size
            
            # Calculate cost for this object
            pricing_per_gb = await self.pricing_service.get_s3_pricing(storage_class)
            obj_size_gb = obj_size / (1024 ** 3)
            estimated_monthly_cost += pricing_per_gb * obj_size_gb
        
        return object_count, bucket_size, last_modified, estimated_monthly_cost

    async def _process_single_bucket(self, semaphore: Optional[asyncio.Semaphore], bucket_info: Dict) -> Optional[Dict]:
        """Process a single bucket with optional semaphore control."""
        bucket_name = bucket_info["Name"]
        creation_date = bucket_info.get("CreationDate")
        logger.info(f"Getting bucket info for {bucket_name}")
        
        async def _do_work():
            try:
                return await self.get_bucket(bucket_name, creation_date)
            except Exception as e:
                logger.error(f"Failed to process bucket {bucket_name}: {e}")
                return None
        
        # Use semaphore if provided, otherwise run directly
        if semaphore:
            async with semaphore:
                return await _do_work()
        else:
            return await _do_work()

    def _prompt_user_confirmation(self, bucket_count: int) -> bool:
        """Prompt user for confirmation unless in CI/CD environment."""
        if os.getenv("CI"):
            return True
        
        try:
            confirmation = input(f"Continue analyzing {bucket_count} buckets? (y/N): ")
            return confirmation.lower() in ["y", "yes"]
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            return False
