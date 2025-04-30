from typing import Optional

import typer
from tabulate import tabulate

from s3_lister import get_bucket, list_buckets


def print_as_table(bucket_information):
    print(tabulate(bucket_information, headers="keys"))


def main(bucket: Optional[str] = typer.Argument(None)):
    if bucket:
        if bucket_information := get_bucket(bucket):
            print_as_table([bucket_information])
    else:
        print_as_table(list_buckets())


if __name__ == "__main__":
    typer.run(main)
