import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from botocore.config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _build_cli_command(*args):
    """
    Build CLI command with optional debugpy support.
    
    If E2E_DEBUG=1 environment variable is set, runs the CLI under debugpy for debugging.
    Otherwise runs normally.
    
    Args:
        *args: Arguments to pass to the CLI
        
    Returns:
        list: Command to execute
    """
    if os.getenv("E2E_DEBUG") == "1":
        return [sys.executable, "-m", "debugpy",  "--listen", "5678", "--wait-for-client", "-m", "src.main"] + list(args)
    else:
        return [sys.executable, "-m", "src.main"] + list(args)

@pytest.fixture
def test_bucket_with_files():
    """Create two test buckets with some files for CLI testing."""
    import asyncio
    import aioboto3
    from src.aws_config import get_aws_config
    
    bucket_name_1 = f"test-bucket-1-{uuid.uuid4().hex[:8]}"
    bucket_name_2 = f"test-bucket-2-{uuid.uuid4().hex[:8]}"
    
    async def setup():
        session = aioboto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        
        aws_config = get_aws_config()
        endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        
        async with session.client("s3", endpoint_url=endpoint_url, config=aws_config) as client:
            region = os.getenv("AWS_REGION", "us-east-1")
            
            # Create both buckets
            for bucket_name in [bucket_name_1, bucket_name_2]:
                if region != "us-east-1":
                    await client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": region}
                    )
                else:
                    await client.create_bucket(Bucket=bucket_name)
            
            # Add test files to first bucket (3 files)
            test_files_1 = [
                ("file1.txt", b"Hello World 1" * 100000),  # ~1.3MB
                ("file2.txt", b"Hello World 2 - This is a longer content" * 50000),  # ~2.1MB  
                ("folder/file3.txt", b"Hello World 3 in a folder" * 75000),  # ~1.95MB
            ]
            
            for key, content in test_files_1:
                await client.put_object(
                    Bucket=bucket_name_1,
                    Key=key,
                    Body=content
                )
            
            # Add test files to second bucket (2 files)
            test_files_2 = [
                ("data/file1.txt", b"Data file 1" * 80000),  # ~0.88MB
                ("data/file2.txt", b"Data file 2 - Different content" * 60000),  # ~1.8MB
            ]
            
            for key, content in test_files_2:
                await client.put_object(
                    Bucket=bucket_name_2,
                    Key=key,
                    Body=content
                )
    
    async def cleanup():
        session = aioboto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        
        config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
        endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        
        async with session.client("s3", endpoint_url=endpoint_url, config=config) as client:
            # Clean up both buckets
            for bucket_name in [bucket_name_1, bucket_name_2]:
                try:
                    response = await client.list_objects_v2(Bucket=bucket_name)
                    if "Contents" in response:
                        for obj in response["Contents"]:
                            await client.delete_object(
                                Bucket=bucket_name,
                                Key=obj["Key"]
                            )
                    await client.delete_bucket(Bucket=bucket_name)
                except Exception as e:
                    print(f"Cleanup error for {bucket_name}: {e}")
    
    # Setup
    asyncio.run(setup())
    
    yield (bucket_name_1, bucket_name_2)
    
    # Cleanup
    asyncio.run(cleanup())


class TestE2ECliOutput:
    """End-to-end tests focusing on CLI output and user experience."""
    
    def test_cli_with_specific_bucket(self, test_bucket_with_files):
        """Test CLI output when analyzing a specific bucket."""
        bucket_name_1, bucket_name_2 = test_bucket_with_files
        
        # Test with the first bucket (3 files)
        result = subprocess.run(
            _build_cli_command(bucket_name_1, "--json"),
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Assert the command succeeded
        assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
        
        # Parse JSON output
        import json
        try:
            output_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result.stdout}")
        
        # Should be a list with one bucket
        assert isinstance(output_data, list)
        assert len(output_data) == 1
        
        bucket_data = output_data[0]
        
        # Check that the bucket data has expected fields
        assert bucket_data["name"] == bucket_name_1
        assert "creation_date" in bucket_data
        assert bucket_data["nb_files"] == 3
        assert "total_size_bytes" in bucket_data
        assert bucket_data["total_size_bytes"] > 0
        assert "total_size_gb" in bucket_data
        assert bucket_data["total_size_gb"] > 0
        assert "last_modified" in bucket_data
        assert "estimated_monthly_cost_usd" in bucket_data
        assert bucket_data["estimated_monthly_cost_usd"] >= 0

    def test_cli_with_nonexistent_bucket(self):
        """Test CLI behavior with non-existent bucket."""
        nonexistent_bucket = f"nonexistent-bucket-{uuid.uuid4().hex[:8]}"
        
        # Run the CLI command
        result = subprocess.run(
            _build_cli_command(nonexistent_bucket),
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Assert the command failed appropriately (exits with 1)
        assert result.returncode == 1
        
        # Check error message in stderr
        error_output = result.stderr
        assert nonexistent_bucket in error_output
        assert ("does not exist" in error_output or 
                "access denied" in error_output.lower() or
                "Failed to process bucket" in error_output or
                "not found, empty, or inaccessible" in error_output)

    def test_cli_list_all_buckets(self, test_bucket_with_files):
        """Test CLI output when listing all buckets."""
        bucket_name_1, bucket_name_2 = test_bucket_with_files
        
        # Set environment variable to skip user confirmation
        env = os.environ.copy()
        env["CI"] = "true"
        
        # Run the CLI command without bucket parameter, with JSON output
        result = subprocess.run(
            _build_cli_command("--json"),
            capture_output=True,
            text=True,
            env=env,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Assert the command succeeded
        assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
        
        # Parse JSON output
        import json
        try:
            output_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result.stdout}")
        
        # Should be a list of buckets
        assert isinstance(output_data, list)
        
        # Find our test buckets in the results
        test_bucket_1_data = None
        test_bucket_2_data = None
        for bucket in output_data:
            if bucket.get("name") == bucket_name_1:
                test_bucket_1_data = bucket
            elif bucket.get("name") == bucket_name_2:
                test_bucket_2_data = bucket
        
        # Both test buckets should be found
        assert test_bucket_1_data is not None, f"Could not find test bucket {bucket_name_1} in output"
        assert test_bucket_2_data is not None, f"Could not find test bucket {bucket_name_2} in output"
        
        # Check data for both buckets
        assert test_bucket_1_data["nb_files"] == 3
        assert test_bucket_2_data["nb_files"] == 2
