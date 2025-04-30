from datetime import datetime

import boto3
from dateutil.tz import tzutc
from mypy_boto3_s3 import S3Client

def get_bucket(name):
    print(f"Getting bucket with name {name}")

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(name)

    client = boto3.client("s3")

    last_modified = datetime.min
    last_modified = last_modified.replace(tzinfo=tzutc())
    c = 0
    bucket_size = 0
    cost = 0

    # TODO: use pagination to support buckets with large numbers of objects
    objects = client.list_objects_v2(Bucket=bucket.name)
    if not (contents := objects.get("Contents")):
        return None
    for bucket_object in contents:
        if (new_last_modified := bucket_object["LastModified"]) > last_modified:
            last_modified = new_last_modified
        c += 1
        bucket_size += bucket_object["Size"]
        # TODO: fix the pricing calculation
        cost += round(0.023 * bucket_size / 1024 / 1024 / 1024, 2)

    return dict(
        name=name,
        creation_date=bucket.creation_date,
        nb_files=c,
        total_size_bytes=bucket_size,
        last_modified=last_modified,
        cost=cost,
    )

def list_buckets():
    client: S3Client = boto3.client("s3")

    all_buckets_info = []
    # TODO: use pagination to support accounts with large numbers of buckets
    for bucket in client.list_buckets()["Buckets"]:
        print(f'Getting bucket info for {bucket["Name"]}')
        if bucket_info := get_bucket(bucket["Name"]):
            all_buckets_info.append(bucket_info)

    return all_buckets_info
