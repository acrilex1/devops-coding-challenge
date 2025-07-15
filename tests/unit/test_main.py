import asyncio
import sys
from io import StringIO
from unittest.mock import AsyncMock, patch

import pytest
import typer

from src.main import async_main, main, print_as_table, print_as_json


class TestMain:
    """Test cases for main module functions."""
    
    @pytest.mark.parametrize("bucket_data,expected_content", [
        ([{"name": "test-bucket", "nb_files": 5, "total_size_bytes": 1024}], 
         ["test-bucket", "5", "1024"]),
        ([], [])
    ])
    def test_print_as_table(self, capsys, bucket_data, expected_content):
        """Test printing table with various data scenarios."""
        # Act
        print_as_table(bucket_data)
        
        # Assert
        captured = capsys.readouterr()
        if expected_content:
            for content in expected_content:
                assert content in captured.out
        else:
            assert captured.out.strip() == ""

    @pytest.mark.parametrize("bucket_data", [
        [{"name": "test-bucket", "nb_files": 5, "total_size_bytes": 1024, 
          "creation_date": "2023-01-01T00:00:00+00:00"}],
        []
    ])
    def test_print_as_json(self, capsys, bucket_data):
        """Test printing bucket data as JSON with various data scenarios."""
        # Act
        print_as_json(bucket_data)
        
        # Assert
        captured = capsys.readouterr()
        import json
        parsed_json = json.loads(captured.out)
        assert parsed_json == bucket_data

    @pytest.mark.asyncio
    async def test_async_main_with_specific_bucket(self):
        """Test async_main with specific bucket."""
        # Arrange
        mock_bucket_data = {"name": "test-bucket", "nb_files": 3}
        
        with patch("src.main.S3Lister") as mock_s3_lister_class, \
             patch("src.main.print_as_table") as mock_print:
            
            # Mock the S3Lister instance and its methods
            mock_lister = AsyncMock()
            mock_lister.get_bucket.return_value = mock_bucket_data
            mock_s3_lister_class.return_value.__aenter__.return_value = mock_lister
            mock_s3_lister_class.return_value.__aexit__.return_value = None
            
            # Act
            await async_main("test-bucket", json_output=False)
            
            # Assert
            mock_lister.get_bucket.assert_called_once_with("test-bucket")
            mock_print.assert_called_once_with([mock_bucket_data])  # Now expects a list
    
    @pytest.mark.asyncio
    async def test_async_main_with_bucket_not_found(self):
        """Test async_main with bucket that doesn't exist (handled during S3 operations)."""
        # Arrange
        with patch("src.main.S3Lister") as mock_s3_lister_class:
            
            # Mock the S3Lister instance and its methods
            mock_lister = AsyncMock()
            # Simulate bucket not found during get_bucket operation (returns None)
            mock_lister.get_bucket.return_value = None
            mock_s3_lister_class.return_value.__aenter__.return_value = mock_lister
            mock_s3_lister_class.return_value.__aexit__.return_value = None
            
            # Act & Assert
            with pytest.raises(Exception):  # typer.Exit raises SystemExit
                await async_main("nonexistent-bucket", json_output=False)
            
            mock_lister.get_bucket.assert_called_once_with("nonexistent-bucket")
    
    @pytest.mark.asyncio
    async def test_async_main_list_all_buckets(self):
        """Test async_main without bucket parameter (list all)."""
        # Arrange
        mock_bucket_list = [
            {"name": "bucket1", "nb_files": 1},
            {"name": "bucket2", "nb_files": 2}
        ]
        
        with patch("src.main.S3Lister") as mock_s3_lister_class, \
             patch("src.main.print_as_table") as mock_print:
            
            # Mock the S3Lister instance and its methods
            mock_lister = AsyncMock()
            mock_lister.list_buckets.return_value = mock_bucket_list
            mock_s3_lister_class.return_value.__aenter__.return_value = mock_lister
            mock_s3_lister_class.return_value.__aexit__.return_value = None
            
            # Act
            await async_main(None, json_output=False)
            
            # Assert
            mock_lister.list_buckets.assert_called_once()
            mock_print.assert_called_once_with(mock_bucket_list)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("json_output,expected_print_func", [
        (False, "print_as_table"),
        (True, "print_as_json"),
    ])
    async def test_async_main_output_formats(self, json_output, expected_print_func):
        """Test async_main with different output formats."""
        # Arrange
        mock_bucket_data = {"name": "test-bucket", "nb_files": 3}
        
        with patch("src.main.S3Lister") as mock_s3_lister_class, \
             patch(f"src.main.{expected_print_func}") as mock_print:
            
            # Mock the S3Lister instance and its methods
            mock_lister = AsyncMock()
            mock_lister.get_bucket.return_value = mock_bucket_data
            mock_s3_lister_class.return_value.__aenter__.return_value = mock_lister
            mock_s3_lister_class.return_value.__aexit__.return_value = None
            
            # Act
            await async_main("test-bucket", json_output=json_output)
            
            # Assert
            mock_lister.get_bucket.assert_called_once_with("test-bucket")
            mock_print.assert_called_once_with([mock_bucket_data])  # Now expects a list

    @pytest.mark.asyncio
    async def test_async_main_exception_handling(self):
        """Test async_main exception handling."""
        # Arrange
        with patch("src.main.S3Lister") as mock_s3_lister_class, \
             patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            
            # Mock the S3Lister instance and its methods
            mock_lister = AsyncMock()
            mock_lister.get_bucket.side_effect = Exception("Test error")
            mock_s3_lister_class.return_value.__aenter__.return_value = mock_lister
            mock_s3_lister_class.return_value.__aexit__.return_value = None
            
            # Act & Assert
            with pytest.raises(Exception):  # typer.Exit raises click.exceptions.Exit
                await async_main("test-bucket", json_output=False)
            
            assert "Error: Test error" in mock_stderr.getvalue()

    @pytest.mark.parametrize("bucket_name,json_output", [
        ("test-bucket", False),
        (None, True),
        ("another-bucket", True),
    ])
    def test_main_calls_async_main(self, bucket_name, json_output):
        """Test that main properly calls async_main with various parameters."""
        # Arrange
        with patch("src.main.asyncio.run") as mock_run:
            
            # Act
            main(bucket_name, json_output=json_output)
            
            # Assert
            mock_run.assert_called_once()
            # Verify the coroutine passed to asyncio.run
            args, _ = mock_run.call_args
            assert hasattr(args[0], '__await__')  # It's a coroutine
