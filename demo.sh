#!/bin/bash

# Simple demo script to populate S3 bucket with test data
# Creates 50 objects across 5 directory layers

set -e

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Configuration
BUCKET_NAME="demo-bucket-$(date +%s)"
TOTAL_OBJECTS=50
LAYERS=5

# Set AWS CLI endpoint if using LocalStack
if [[ "${AWS_ENDPOINT_URL}" == *"localhost"* ]]; then
    AWS_CLI_ENDPOINT="--endpoint-url ${AWS_ENDPOINT_URL}"
else
    AWS_CLI_ENDPOINT=""
fi

# Create bucket
echo "Creating bucket: ${BUCKET_NAME}"
if [[ "${AWS_REGION}" != "us-east-1" && -z "${AWS_ENDPOINT_URL}" ]]; then
    aws s3api create-bucket --bucket "${BUCKET_NAME}" --region "${AWS_REGION}" --create-bucket-configuration LocationConstraint="${AWS_REGION}" ${AWS_CLI_ENDPOINT} > /dev/null
else
    aws s3api create-bucket --bucket "${BUCKET_NAME}" --region "${AWS_REGION:-us-east-1}" ${AWS_CLI_ENDPOINT} > /dev/null
fi

# Create objects in nested directories
objects_per_layer=$((TOTAL_OBJECTS / LAYERS))

for i in $(seq 1 ${LAYERS}); do
    # Build directory path
    dir_path="level1"
    for j in $(seq 2 $i); do
        dir_path="${dir_path}/sublevel${j}"
    done
    
    # Create objects for this layer
    for j in $(seq 1 ${objects_per_layer}); do
        s3_key="${dir_path}/file_${i}_${j}.txt"
        echo "" | aws s3 cp - "s3://${BUCKET_NAME}/${s3_key}" ${AWS_CLI_ENDPOINT} > /dev/null 2>&1
    done
done

# Add a 100MB file to demonstrate pricing calculation
echo "Adding 100MB file for pricing demo..."
dd if=/dev/zero bs=1M count=100 2>/dev/null | aws s3 cp - "s3://${BUCKET_NAME}/large_file_100mb.bin" ${AWS_CLI_ENDPOINT} > /dev/null 2>&1

echo "Testing S3 lister..."
poetry run python -m src.main "${BUCKET_NAME}" --json 
# Cleanup
aws s3 rb "s3://${BUCKET_NAME}" --force ${AWS_CLI_ENDPOINT} > /dev/null 2>&1
