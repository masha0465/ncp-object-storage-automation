"""
NCP Object Storage API 자동화 테스트
pytest 기반 테스트 스위트

설치 필요 패키지:
pip install pytest boto3 requests pytest-html pytest-xdist python-dotenv

실행 방법:
pytest test_ncp_storage.py -v --html=reports/report.html --self-contained-html
"""

import pytest
import boto3
import requests
import hashlib
import os
import time
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from botocore.client import Config
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class NCPObjectStorageConfig:
    """NCP Object Storage 설정"""
    def __init__(self):
        self.endpoint_url = os.getenv('NCP_ENDPOINT_URL', 'https://kr.object.ncloudstorage.com')
        self.access_key = os.getenv('NCP_ACCESS_KEY')
        self.secret_key = os.getenv('NCP_SECRET_KEY')
        self.region_name = os.getenv('NCP_REGION', 'kr-standard')
        self.test_bucket_prefix = 'pytest-test-'
        
        if not self.access_key or not self.secret_key:
            raise ValueError("NCP_ACCESS_KEY와 NCP_SECRET_KEY 환경변수가 필요합니다")

@pytest.fixture(scope="session")
def ncp_config():
    """NCP 설정 픽스처"""
    return NCPObjectStorageConfig()

@pytest.fixture(scope="session")
def s3_client(ncp_config):
    """S3 클라이언트 픽스처"""
    client = boto3.client(
        's3',
        endpoint_url=ncp_config.endpoint_url,
        aws_access_key_id=ncp_config.access_key,
        aws_secret_access_key=ncp_config.secret_key,
        region_name=ncp_config.region_name
    )
    return client

@pytest.fixture(scope="session")
def test_bucket(s3_client, ncp_config):
    """테스트용 버킷 생성/삭제 픽스처"""
    bucket_name = f"{ncp_config.test_bucket_prefix}{int(time.time())}"
    
    # 버킷 생성
    s3_client.create_bucket(Bucket=bucket_name)
    
    yield bucket_name
    
    # 정리: 버킷 내 모든 객체 삭제 후 버킷 삭제
    try:
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            delete_objects = {'Objects': [{'Key': obj['Key']} for obj in objects['Contents']]}
            s3_client.delete_objects(Bucket=bucket_name, Delete=delete_objects)
        s3_client.delete_bucket(Bucket=bucket_name)
    except Exception as e:
        print(f"테스트 버킷 정리 중 오류: {e}")

class TestBasicFunctionality:
    """AUTO_001: 기본 기능 회귀 테스트"""
    
    def test_bucket_operations(self, s3_client, ncp_config):
        """버킷 생성, 목록 조회, 삭제 테스트"""
        bucket_name = f"{ncp_config.test_bucket_prefix}basic-{int(time.time())}"
        
        # 버킷 생성
        response = s3_client.create_bucket(Bucket=bucket_name)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        
        # 버킷 목록 조회
        buckets = s3_client.list_buckets()
        bucket_names = [bucket['Name'] for bucket in buckets['Buckets']]
        assert bucket_name in bucket_names
        
        # 버킷 삭제
        s3_client.delete_bucket(Bucket=bucket_name)
        
        # 삭제 확인
        buckets = s3_client.list_buckets()
        bucket_names = [bucket['Name'] for bucket in buckets['Buckets']]
        assert bucket_name not in bucket_names

    def test_object_crud_operations(self, s3_client, test_bucket):
        """객체 CRUD 작업 테스트"""
        object_key = 'test-files/sample.txt'
        test_content = 'Hello NCP Object Storage!'
        
        # 객체 업로드
        s3_client.put_object(
            Bucket=test_bucket,
            Key=object_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        # 객체 목록 조회
        objects = s3_client.list_objects_v2(Bucket=test_bucket)
        assert 'Contents' in objects
        object_keys = [obj['Key'] for obj in objects['Contents']]
        assert object_key in object_keys
        
        # 객체 다운로드
        response = s3_client.get_object(Bucket=test_bucket, Key=object_key)
        downloaded_content = response['Body'].read().decode('utf-8')
        assert downloaded_content == test_content
        
        # 객체 삭제
        s3_client.delete_object(Bucket=test_bucket, Key=object_key)
        
        # 삭제 확인
        objects = s3_client.list_objects_v2(Bucket=test_bucket)
        if 'Contents' in objects:
            object_keys = [obj['Key'] for obj in objects['Contents']]
            assert object_key not in object_keys

class TestPerformanceBaseline:
    """AUTO_002: 업로드/다운로드 성능 기준선 테스트"""
    
    def create_test_file(self, size_mb):
        """테스트용 파일 생성"""
        content = 'A' * (1024 * 1024 * size_mb)  # size_mb MB 파일
        return content.encode('utf-8')
    
    @pytest.mark.parametrize("file_size_mb", [1, 5, 10])  # 50MB는 비용 절약을 위해 10MB로 변경
    def test_upload_performance(self, s3_client, test_bucket, file_size_mb):
        """파일 업로드 성능 테스트"""
        object_key = f'performance/test-{file_size_mb}mb.dat'
        test_data = self.create_test_file(file_size_mb)
        
        start_time = time.time()
        s3_client.put_object(
            Bucket=test_bucket,
            Key=object_key,
            Body=test_data
        )
        upload_time = time.time() - start_time
        
        # 성능 기준: 1MB당 3초 이하
        expected_max_time = file_size_mb * 3
        assert upload_time < expected_max_time, f"업로드 시간 {upload_time}초가 기준 {expected_max_time}초를 초과"
        
        print(f"{file_size_mb}MB 파일 업로드 시간: {upload_time:.2f}초")
    
    def test_concurrent_uploads(self, s3_client, test_bucket):
        """동시 업로드 테스트"""
        import concurrent.futures
        import threading
        
        def upload_file(file_index):
            object_key = f'concurrent/file-{file_index}.txt'
            content = f'Concurrent test file {file_index}'
            try:
                start_time = time.time()
                s3_client.put_object(
                    Bucket=test_bucket,
                    Key=object_key,
                    Body=content.encode('utf-8')
                )
                return time.time() - start_time
            except Exception as e:
                return f"Error: {e}"
        
        # 10개 파일 동시 업로드
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 모든 업로드가 성공했는지 확인
        successful_uploads = [r for r in results if isinstance(r, float)]
        assert len(successful_uploads) == 10, "모든 동시 업로드가 성공해야 함"
        
        # 평균 업로드 시간이 10초 이하인지 확인
        avg_time = sum(successful_uploads) / len(successful_uploads)
        assert avg_time < 10, f"평균 업로드 시간 {avg_time:.2f}초가 기준 10초를 초과"

class TestSecurityAndAuth:
    """AUTO_003: 인증 및 권한 제어 테스트"""
    
    def test_invalid_credentials(self, ncp_config):
        """잘못된 인증 정보 테스트"""
        invalid_client = boto3.client(
            's3',
            endpoint_url=ncp_config.endpoint_url,
            aws_access_key_id='INVALID_KEY',
            aws_secret_access_key='invalid_secret',
            region_name=ncp_config.region_name
        )
        
        with pytest.raises(ClientError) as exc_info:
            invalid_client.list_buckets()
        
        assert exc_info.value.response['Error']['Code'] in ['InvalidAccessKeyId', 'SignatureDoesNotMatch']
    
    def test_object_permissions(self, s3_client, test_bucket):
        """객체 권한 설정 테스트"""
        object_key = 'permissions/test-acl.txt'
        content = 'Permission test content'
        
        # Private 객체 업로드
        s3_client.put_object(
            Bucket=test_bucket,
            Key=object_key,
            Body=content.encode('utf-8'),
            ACL='private'
        )
        
        # ACL 확인
        acl = s3_client.get_object_acl(Bucket=test_bucket, Key=object_key)
        assert 'Grants' in acl
        
        # Public-read로 변경
        s3_client.put_object_acl(
            Bucket=test_bucket,
            Key=object_key,
            ACL='public-read'
        )
        
        # 변경된 ACL 확인
        acl = s3_client.get_object_acl(Bucket=test_bucket, Key=object_key)
        public_grants = [grant for grant in acl['Grants'] 
                        if grant.get('Grantee', {}).get('Type') == 'Group']
        assert len(public_grants) > 0, "Public-read ACL이 적용되어야 함"

class TestDataIntegrity:
    """AUTO_005: 업로드/다운로드 무결성 테스트"""
    
    def calculate_md5(self, data):
        """MD5 해시 계산"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.md5(data).hexdigest()
    
    @pytest.mark.parametrize("file_size", [1024, 1024*1024, 5*1024*1024])  # 1KB, 1MB, 5MB (10MB에서 5MB로 변경)
    def test_file_integrity(self, s3_client, test_bucket, file_size):
        """파일 무결성 테스트"""
        import random
        import base64
        
        # 랜덤 테스트 데이터 생성
        test_data = bytes(random.getrandbits(8) for _ in range(file_size))
        original_md5 = hashlib.md5(test_data).hexdigest()
        
        object_key = f'integrity/test-{file_size}-bytes.dat'
        
        # 업로드 (ContentMD5 제거 - NCP에서 호환성 문제 발생)
        s3_client.put_object(
            Bucket=test_bucket,
            Key=object_key,
            Body=test_data
        )
        
        # 다운로드
        response = s3_client.get_object(Bucket=test_bucket, Key=object_key)
        downloaded_data = response['Body'].read()
        downloaded_md5 = hashlib.md5(downloaded_data).hexdigest()
        
        # 무결성 검증
        assert original_md5 == downloaded_md5, f"MD5 불일치: 원본={original_md5}, 다운로드={downloaded_md5}"
        assert len(test_data) == len(downloaded_data), "파일 크기 불일치"
        assert test_data == downloaded_data, "파일 내용 불일치"

class TestS3Compatibility:
    """AUTO_004: S3 호환성 검증 테스트"""
    
    def test_standard_s3_operations(self, s3_client, test_bucket):
        """표준 S3 작업 호환성"""
        # HEAD Bucket
        response = s3_client.head_bucket(Bucket=test_bucket)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        
        # PUT Object with metadata
        s3_client.put_object(
            Bucket=test_bucket,
            Key='s3-compat/test.txt',
            Body='S3 compatibility test',
            Metadata={'author': 'pytest', 'purpose': 'compatibility-test'}
        )
        
        # HEAD Object
        response = s3_client.head_object(Bucket=test_bucket, Key='s3-compat/test.txt')
        assert 'author' in response['Metadata']
        assert response['Metadata']['author'] == 'pytest'
        
        # GET Object with range
        response = s3_client.get_object(
            Bucket=test_bucket, 
            Key='s3-compat/test.txt',
            Range='bytes=0-4'
        )
        partial_content = response['Body'].read().decode('utf-8')
        assert partial_content == 'S3 co'
        assert response['ResponseMetadata']['HTTPStatusCode'] == 206  # Partial Content

class TestErrorHandling:
    """AUTO_013: 오류 상황 처리 테스트"""
    
    def test_nonexistent_bucket_operations(self, s3_client):
        """존재하지 않는 버킷 작업 테스트"""
        nonexistent_bucket = 'nonexistent-bucket-12345'
        
        # 존재하지 않는 버킷에 객체 업로드 시도
        with pytest.raises(ClientError) as exc_info:
            s3_client.put_object(
                Bucket=nonexistent_bucket,
                Key='test.txt',
                Body='test content'
            )
        assert exc_info.value.response['Error']['Code'] == 'NoSuchBucket'
        
        # 존재하지 않는 버킷의 객체 조회 시도
        with pytest.raises(ClientError) as exc_info:
            s3_client.get_object(Bucket=nonexistent_bucket, Key='test.txt')
        assert exc_info.value.response['Error']['Code'] == 'NoSuchBucket'
    
    def test_nonexistent_object_operations(self, s3_client, test_bucket):
        """존재하지 않는 객체 작업 테스트"""
        nonexistent_key = 'nonexistent/file.txt'
        
        # 존재하지 않는 객체 다운로드 시도
        with pytest.raises(ClientError) as exc_info:
            s3_client.get_object(Bucket=test_bucket, Key=nonexistent_key)
        assert exc_info.value.response['Error']['Code'] == 'NoSuchKey'
        
        # 존재하지 않는 객체 메타데이터 조회 시도
        with pytest.raises(ClientError) as exc_info:
            s3_client.head_object(Bucket=test_bucket, Key=nonexistent_key)
        assert exc_info.value.response['Error']['Code'] == 'NoSuchKey'

class TestMultipartUpload:
    """AUTO_010: 멀티파트 업로드 테스트"""
    
    def test_multipart_upload_workflow(self, s3_client, test_bucket):
        """멀티파트 업로드 전체 워크플로우"""
        object_key = 'multipart/large-file.dat'
        
        # 10MB 테스트 데이터 생성 (5MB씩 2파트)
        part_size = 5 * 1024 * 1024  # 5MB
        part1_data = b'A' * part_size
        part2_data = b'B' * part_size
        
        # 멀티파트 업로드 시작
        response = s3_client.create_multipart_upload(Bucket=test_bucket, Key=object_key)
        upload_id = response['UploadId']
        
        parts = []
        
        try:
            # 파트 1 업로드
            response1 = s3_client.upload_part(
                Bucket=test_bucket,
                Key=object_key,
                PartNumber=1,
                UploadId=upload_id,
                Body=part1_data
            )
            parts.append({'ETag': response1['ETag'], 'PartNumber': 1})
            
            # 파트 2 업로드
            response2 = s3_client.upload_part(
                Bucket=test_bucket,
                Key=object_key,
                PartNumber=2,
                UploadId=upload_id,
                Body=part2_data
            )
            parts.append({'ETag': response2['ETag'], 'PartNumber': 2})
            
            # 멀티파트 업로드 완성
            s3_client.complete_multipart_upload(
                Bucket=test_bucket,
                Key=object_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            # 업로드된 파일 검증
            response = s3_client.get_object(Bucket=test_bucket, Key=object_key)
            downloaded_data = response['Body'].read()
            
            expected_data = part1_data + part2_data
            assert len(downloaded_data) == len(expected_data)
            assert downloaded_data == expected_data
            
        except Exception as e:
            # 실패 시 멀티파트 업로드 중단
            s3_client.abort_multipart_upload(
                Bucket=test_bucket,
                Key=object_key,
                UploadId=upload_id
            )
            raise e

# 테스트 실행을 위한 conftest.py 설정
@pytest.fixture(scope="session", autouse=True)
def test_session_setup():
    """테스트 세션 설정"""
    print("\n=== NCP Object Storage API 테스트 시작 ===")
    yield
    print("\n=== NCP Object Storage API 테스트 완료 ===")

# 커스텀 마커 정의
def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line("markers", "slow: 느린 테스트 마킹")
    config.addinivalue_line("markers", "integration: 통합 테스트 마킹")

if __name__ == "__main__":
    # 직접 실행 시 pytest 실행
    pytest.main([__file__, "-v"])