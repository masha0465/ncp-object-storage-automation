import pytest
import boto3
import time
import hashlib
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

@pytest.fixture  
def test_bucket(s3_client):
    bucket_name = f"pytest-test-{int(time.time())}"
    s3_client.create_bucket(Bucket=bucket_name)
    yield bucket_name
    
    # 정리
    try:
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            delete_objects = {'Objects': [{'Key': obj['Key']} for obj in objects['Contents']]}
            s3_client.delete_objects(Bucket=bucket_name, Delete=delete_objects)
        s3_client.delete_bucket(Bucket=bucket_name)
    except:
        pass

def test_basic_operations(s3_client, test_bucket):
    """기본 CRUD 작업 테스트"""
    # 업로드 테스트
    s3_client.put_object(Bucket=test_bucket, Key='test.txt', Body='Hello NCP!')
    
    # 다운로드 테스트  
    response = s3_client.get_object(Bucket=test_bucket, Key='test.txt')
    content = response['Body'].read().decode('utf-8')
    assert content == 'Hello NCP!'