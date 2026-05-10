from dotenv import load_dotenv
import pandas as pd
import os
import boto3
import io

load_dotenv()

print("ENDPOINT:", os.getenv("R2_ENDPOINT"))
print("BUCKET:", os.getenv("R2_BUCKET_NAME"))
print("KEY:", os.getenv("R2_ACCESS_KEY"))

s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
    )

def read_from_lake(path: str) -> pd.DataFrame:
    bucket = os.getenv("R2_BUCKET_NAME")
    response = s3.get_object(Bucket=bucket, Key=path)
    print("ENDPOINT:", os.getenv("R2_ENDPOINT"))
    print("BUCKET:", os.getenv("R2_BUCKET_NAME"))
    print("KEY:", os.getenv("R2_ACCESS_KEY"))
    return pd.read_csv(io.BytesIO(response["Body"].read()))

def list_lake_files(prefix: str) -> list[str]:
    response = s3.list_objects_v2(Bucket=os.getenv("R2_BUCKET_NAME"), Prefix=prefix)
    return [obj["Key"] for obj in response.get("Contents", [])]

# response = s3.list_objects_v2(Bucket=os.getenv("R2_BUCKET_NAME"))
# for obj in response.get("Contents", []):
#     print(obj["Key"])