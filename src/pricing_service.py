"""
AWS S3 Pricing Service

This module provides pricing information for AWS S3 storage using the AWS Pricing API.
It includes caching to avoid repeated API calls and supports all S3 storage classes.
The service automatically detects the appropriate pricing location based on the AWS region.
"""

import json
import logging
import os
from typing import Dict, Optional

import boto3

from .aws_config import get_aws_config

# Configure logging to only show errors by default  
log_level = os.getenv('LOG_LEVEL', 'ERROR').upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Mapping of AWS regions to AWS Pricing API location names
# Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html
REGION_TO_LOCATION_MAP = {
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)", 
    "us-west-1": "US West (N. California)",
    "us-west-2": "US West (Oregon)",
    "ca-central-1": "Canada (Central)",
    "eu-west-1": "Europe (Ireland)",
    "eu-west-2": "Europe (London)",
    "eu-west-3": "Europe (Paris)",
    "eu-central-1": "Europe (Frankfurt)",
    "eu-north-1": "Europe (Stockholm)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ap-northeast-2": "Asia Pacific (Seoul)",
    "ap-south-1": "Asia Pacific (Mumbai)",
    "sa-east-1": "South America (Sao Paulo)",
    # Add more regions as needed
}

# Default location if region is not found or not set
DEFAULT_PRICING_LOCATION = "US East (N. Virginia)"


class PricingService:
    """Service to handle AWS pricing information with caching."""
    
    def __init__(self):
        self._cache: Dict[str, float] = {}
        self._default_price = float(os.getenv("DEFAULT_S3_PRICE_PER_GB", "0.023"))
        self._current_region = os.getenv("AWS_REGION", "us-east-1")
    
    async def get_s3_pricing(self, storage_class: str = "STANDARD") -> float:
        """
        Get S3 storage pricing per GB-month for a specific storage class.
        
        Args:
            storage_class: S3 storage class (e.g., "STANDARD", "STANDARD_IA", "GLACIER")
                          
        Returns:
            Price per GB-month in USD
        """
        storage_class = storage_class.upper()
        
        # If cache is empty, try to fetch all pricing from AWS
        if not self._cache:
            try:
                pricing_data = await self._fetch_pricing_from_aws()
                self._cache.update(pricing_data)
                logger.info(f"Loaded pricing for {len(self._cache)} storage classes")
            except Exception as e:
                logger.warning(f"Failed to fetch S3 pricing from AWS: {e}. Using default pricing.")
        
        # Return cached value or default
        return self._cache.get(storage_class, self._default_price)
    
    async def _fetch_pricing_from_aws(self) -> Dict[str, float]:
        """
        Fetch all S3 storage class pricing from AWS API for the current region.
        
        Returns:
            Dictionary mapping storage class names to prices per GB-month
        """
        pricing_location = REGION_TO_LOCATION_MAP.get(self._current_region, DEFAULT_PRICING_LOCATION)
        logger.info(f"Fetching S3 pricing for location: {pricing_location}")
        
        pricing_data = await self._fetch_pricing_for_location(pricing_location)
        
        # If no pricing data found for this region, try fallback
        if not pricing_data and pricing_location != DEFAULT_PRICING_LOCATION:
            logger.warning(f"No pricing data found for location '{pricing_location}', falling back to default location")
            pricing_data = await self._fetch_pricing_for_location(DEFAULT_PRICING_LOCATION)
        
        return pricing_data
    
    async def _fetch_pricing_for_location(self, location: str) -> Dict[str, float]:
        """
        Fetch S3 pricing for a specific location.
        
        Args:
            location: AWS Pricing API location name
            
        Returns:
            Dictionary mapping storage class names to prices per GB-month
        """
        pricing_client = boto3.client("pricing", region_name="us-east-1", config=get_aws_config())
        
        response = pricing_client.get_products(
            ServiceCode="AmazonS3",
            Filters=[
                {"Type": "TERM_MATCH", "Field": "location", "Value": location},
                {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Storage"},
            ],
            MaxResults=100
        )
        
        pricing_data = {}
        
        for price_item in response.get("PriceList", []):
            price_data = json.loads(price_item)
            
            # Extract storage class and price
            attributes = price_data.get("product", {}).get("attributes", {})
            storage_class = attributes.get("storageClass", "").upper().replace(" ", "_").replace("-", "_")
            
            if storage_class and "terms" in price_data:
                terms = price_data["terms"]["OnDemand"]
                if terms:
                    price_dimensions = list(terms.values())[0]["priceDimensions"]
                    price_per_gb = float(list(price_dimensions.values())[0]["pricePerUnit"]["USD"])
                    pricing_data[storage_class] = price_per_gb
                    
                    # Also map common aliases
                    if storage_class == "GENERAL_PURPOSE":
                        pricing_data["STANDARD"] = price_per_gb
        
        return pricing_data
