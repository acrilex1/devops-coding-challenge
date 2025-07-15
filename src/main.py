import asyncio
import json
import sys
from typing import Optional, Union

import typer
from dotenv import load_dotenv
from tabulate import tabulate

from src.s3_lister import S3Lister

# Load environment variables
load_dotenv()


def print_as_table(bucket_information: list[dict]) -> None:
    """Print bucket information as a formatted table."""
    if not bucket_information:
        print("")
        return
    print(tabulate(bucket_information, headers="keys"))


def print_as_json(bucket_information: list[dict]) -> None:
    """Print bucket information as JSON."""
    if not bucket_information:
        print("[]")
        return
    print(json.dumps(bucket_information, indent=2, default=str))


async def async_main(
    bucket: Optional[str] = typer.Argument(None, help="Specific S3 bucket name to analyze"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON instead of table")
) -> None:
    """Main CLI function to analyze S3 buckets and calculate costs."""
    try:
        async with S3Lister() as lister:
            if bucket:
                info = await lister.get_bucket(bucket)
                if info is None:
                    print(f"Error: Bucket '{bucket}' not found, empty, or inaccessible", file=sys.stderr)
                    raise typer.Exit(1)
                # Wrap single bucket in list for consistent JSON output
                bucket_list = [info]
            else:
                bucket_list = await lister.list_buckets()

            if json_output:
                print_as_json(bucket_list)
            else:
                print_as_table(bucket_list)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


def main(
    bucket: Optional[str] = typer.Argument(None, help="Specific S3 bucket name to analyze"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON instead of table")
) -> None:
    """AWS S3 bucket analyzer CLI - calculates storage costs and metadata."""
    asyncio.run(async_main(bucket, json_output))


if __name__ == "__main__":
    typer.run(main)
