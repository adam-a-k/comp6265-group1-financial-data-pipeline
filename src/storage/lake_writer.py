import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os
import boto3

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
)

def write_to_lake(df, filename):

    csv_buffer = df.to_csv(index=False).encode()
    s3.put_object(
        Bucket=os.getenv("R2_BUCKET_NAME"),
        Key=filename,
        Body=csv_buffer
    )