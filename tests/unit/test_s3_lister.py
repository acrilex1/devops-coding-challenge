import os
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

import pytest

from src.s3_lister import S3Lister


class TestS3Lister:
    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "test_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret",
        "AWS_REGION": "us-west-2"
    })
    def test_s3_lister_initialization(self):
        """Test that S3Lister initializes properly with environment variables."""
        lister = S3Lister()
        assert lister.session is not None
        assert lister.pricing_service is not None
        assert lister.aws_config is not None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test that S3Lister works as an async context manager."""
        with patch.dict(os.environ, {
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret",
            "AWS_REGION": "us-west-2"
        }):
            async with S3Lister() as lister:
                assert isinstance(lister, S3Lister)

    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "test_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret",
        "AWS_REGION": "us-west-2"
    })
    @pytest.mark.asyncio
    async def test_get_bucket_creation_date(self):
        """Test getting bucket creation date from list_buckets."""
        lister = S3Lister()
        
        # Mock the S3 client
        mock_client = AsyncMock()
        test_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        mock_client.list_buckets.return_value = {
            "Buckets": [
                {"Name": "bucket1", "CreationDate": test_date},
                {"Name": "bucket2", "CreationDate": datetime(2023, 2, 1, tzinfo=timezone.utc)}
            ]
        }
        
        lister._s3_client = mock_client
        
        # Test finding existing bucket
        result = await lister._get_bucket_creation_date(mock_client, "bucket1")
        assert result == test_date
        
        # Test bucket not found
        result = await lister._get_bucket_creation_date(mock_client, "nonexistent")
        assert result is None

    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "test_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret",
        "AWS_REGION": "us-west-2"
    })
    @pytest.mark.asyncio
    async def test_process_bucket_objects_recursive_listing(self):
        """Test the recursive prefix-based object listing logic."""
        lister = S3Lister()
        
        # Mock the S3 client and paginator
        mock_client = AsyncMock()
        mock_paginator = MagicMock()  # Use MagicMock instead of AsyncMock for the paginator
        mock_client.get_paginator = MagicMock(return_value=mock_paginator)  # Make get_paginator synchronous
        
        # Mock pricing service
        lister.pricing_service.get_s3_pricing = AsyncMock(return_value=0.023)
        
        # Setup test data with hierarchical structure
        test_date = datetime(2023, 6, 15, tzinfo=timezone.utc)
        
        # Root level objects and common prefixes
        root_page = {
            "Contents": [
                {
                    "Key": "file1.txt",
                    "Size": 1024,
                    "LastModified": test_date,
                    "StorageClass": "STANDARD"
                }
            ],
            "CommonPrefixes": [
                {"Prefix": "folder1/"},
                {"Prefix": "folder2/"}
            ]
        }
        
        # folder1/ contents
        folder1_page = {
            "Contents": [
                {
                    "Key": "folder1/file2.txt",
                    "Size": 2048,
                    "LastModified": test_date,
                    "StorageClass": "STANDARD_IA"
                }
            ],
            "CommonPrefixes": []
        }
        
        # folder2/ contents
        folder2_page = {
            "Contents": [
                {
                    "Key": "folder2/file3.txt",
                    "Size": 4096,
                    "LastModified": test_date,
                    "StorageClass": "GLACIER"
                }
            ],
            "CommonPrefixes": []
        }
        
        # Mock paginate calls for different prefixes
        def mock_paginate(**kwargs):
            prefix = kwargs.get("Prefix", "")
            if prefix == "":
                # Root level
                async def root_iterator():
                    yield root_page
                return root_iterator()
            elif prefix == "folder1/":
                async def folder1_iterator():
                    yield folder1_page
                return folder1_iterator()
            elif prefix == "folder2/":
                async def folder2_iterator():
                    yield folder2_page
                return folder2_iterator()
        
        mock_paginator.paginate.side_effect = mock_paginate
        
        # Test the recursive listing
        count, size, last_modified, cost = await lister._process_bucket_objects(mock_client, "test-bucket")
        
        # Verify results
        assert count == 3  # 3 files total
        assert size == 7168  # 1024 + 2048 + 4096
        assert last_modified == test_date
        
        # Verify paginator was called with correct prefixes
        expected_calls = [
            {"Bucket": "test-bucket", "Prefix": "", "Delimiter": "/"},
            {"Bucket": "test-bucket", "Prefix": "folder1/", "Delimiter": "/"},
            {"Bucket": "test-bucket", "Prefix": "folder2/", "Delimiter": "/"}
        ]
        
        # Check that paginate was called the expected number of times
        assert mock_paginator.paginate.call_count == 3
        
        # Verify pricing service was called for each storage class
        assert lister.pricing_service.get_s3_pricing.call_count == 3

    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "test_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret",
        "AWS_REGION": "us-west-2"
    })
    @pytest.mark.asyncio
    async def test_process_bucket_objects_empty_bucket(self):
        """Test processing an empty bucket."""
        lister = S3Lister()
        
        # Mock the S3 client and paginator for empty bucket
        mock_client = AsyncMock()
        mock_paginator = MagicMock()  # Use MagicMock instead of AsyncMock for the paginator
        mock_client.get_paginator = MagicMock(return_value=mock_paginator)  # Make get_paginator synchronous
        
        # Mock empty response
        def empty_iterator():
            async def async_empty():
                yield {"Contents": [], "CommonPrefixes": []}
            return async_empty()
        
        mock_paginator.paginate.side_effect = lambda **kwargs: empty_iterator()
        
        # Test empty bucket
        count, size, last_modified, cost = await lister._process_bucket_objects(mock_client, "empty-bucket")
        
        # Verify results for empty bucket
        assert count == 0
        assert size == 0
        assert cost == 0.0
        # last_modified should be the minimum datetime
        assert last_modified.year == 1

    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "test_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret",
        "AWS_REGION": "us-west-2"
    })
    @pytest.mark.asyncio
    async def test_process_bucket_objects_default_storage_class(self):
        """Test that objects without StorageClass default to STANDARD."""
        lister = S3Lister()
        
        # Mock the S3 client and paginator
        mock_client = AsyncMock()
        mock_paginator = MagicMock()  # Use MagicMock instead of AsyncMock for the paginator
        mock_client.get_paginator = MagicMock(return_value=mock_paginator)  # Make get_paginator synchronous
        
        # Mock pricing service
        lister.pricing_service.get_s3_pricing = AsyncMock(return_value=0.023)
        
        # Setup test data without StorageClass
        test_date = datetime(2023, 6, 15, tzinfo=timezone.utc)
        test_page = {
            "Contents": [
                {
                    "Key": "file1.txt",
                    "Size": 1024,
                    "LastModified": test_date
                    # Note: No StorageClass specified
                }
            ],
            "CommonPrefixes": []
        }
        
        def mock_iterator():
            async def async_iter():
                yield test_page
            return async_iter()
        
        mock_paginator.paginate.side_effect = lambda **kwargs: mock_iterator()
        
        # Test processing
        count, size, last_modified, cost = await lister._process_bucket_objects(mock_client, "test-bucket")
        
        # Verify STANDARD was used as default
        lister.pricing_service.get_s3_pricing.assert_called_once_with("STANDARD")
        assert count == 1
        assert size == 1024

    @patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "test_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret",
        "AWS_REGION": "us-west-2"
    })
    @pytest.mark.asyncio
    async def test_get_bucket_with_creation_date(self):
        """Test get_bucket when creation_date is provided."""
        lister = S3Lister()
        
        # Mock the session.client context manager
        mock_context = AsyncMock()
        mock_client = AsyncMock()
        mock_context.__aenter__.return_value = mock_client
        mock_context.__aexit__.return_value = None
        lister.session.client = MagicMock(return_value=mock_context)
        
        # Mock _process_bucket_objects
        test_date = datetime(2023, 6, 15, tzinfo=timezone.utc)
        creation_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        
        async def mock_process_bucket_objects(s3_client, bucket_name):
            return 100, 1048576, test_date, 0.024
        
        lister._process_bucket_objects = mock_process_bucket_objects
        
        # Test with provided creation_date
        result = await lister.get_bucket("test-bucket", creation_date)
        
        # Verify result structure
        assert result is not None
        assert result["name"] == "test-bucket"
        assert result["creation_date"] == creation_date
        assert result["nb_files"] == 100
        assert result["total_size_bytes"] == 1048576
        assert result["total_size_gb"] == 0.001  # 1048576 bytes = 0.001 GB
        assert result["last_modified"] == test_date
        assert result["estimated_monthly_cost_usd"] == 0.024
