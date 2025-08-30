import pytest
import boto3
from dotenv import load_dotenv
import os

load_dotenv()

@pytest.fixture
def s3_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('NCP_ENDPOINT_URL'),
        aws_access_key_id=os.getenv('NCP_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('NCP_SECRET_KEY'),
        region_name=os.getenv('NCP_REGION')
    )

def test_connection(s3_client):
    """기본 연결 테스트"""
    buckets = s3_client.list_buckets()
    assert 'Buckets' in buckets
    print(f"버킷 수: {len(buckets['Buckets'])}")