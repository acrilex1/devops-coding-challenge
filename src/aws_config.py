import os
from botocore.config import Config


def get_aws_config() -> Config:
    """Get AWS configuration with retry settings."""
    return Config(
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        retries={
            "max_attempts": int(os.getenv("AWS_MAX_ATTEMPTS", "3")),
            "mode": "adaptive"
        }
    )