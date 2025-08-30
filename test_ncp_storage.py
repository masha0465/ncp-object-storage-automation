"""
NCP Object Storage API 자동화 테스트 - 포트폴리오 버전
"""
import pytest
import boto3
import hashlib
import os
import time
import logging
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestConfig:
    """테스트 설정"""
    def __init__(self):
        self.endpoint_url = os.getenv('NCP_ENDPOINT_URL', 'https://kr.object.ncloudstorage.com')
        self.access_key = os.getenv('NCP_ACCESS_KEY')
        self.secret_key = os.getenv('NCP_SECRET_KEY')
        self.region_name = os.getenv('NCP_REGION', 'kr-standard')
        self.test_bucket_prefix = 'pytest-test-'
        
        if not self.access_key or not self.secret_key:
            raise ValueError("NCP_ACCESS_KEY와 NCP_SECRET_KEY 환경변수가 필요합니다")

@pytest.fixture(scope="session")
def test_config():
    return TestConfig()

@pytest.fixture(scope="session")
def s3_client(test_config):
    """S3 클라이언트 픽스처"""
    client = boto3.client(
        's3',
        endpoint_url=test_config.endpoint_url,
        aws_access_key_id=test_config.access_key,
        aws_secret_access_key=test_config.secret_key,
        region_name=test_config.region_name
    )
    logger.info("NCP Object Storage 클라이언트 초기화 완료")
    return client

@pytest.fixture(scope="session")
def test_bucket(s3_client, test_config):
    """테스트용 버킷 생성/삭제 픽스처"""
    import uuid
    # UUID를 추가해서 고유한 버킷 이름 생성
    bucket_name = f"{test_config.test_bucket_prefix}{int(time.time())}-{uuid.uuid4().hex[:8]}"
    
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        logger.info(f"테스트 버킷 생성: {bucket_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyExists':
            # 기존 버킷이 있다면 삭제 후 재생성
            bucket_name = f"{test_config.test_bucket_prefix}{int(time.time())}-{uuid.uuid4().hex[:8]}"
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            raise
    
    yield bucket_name
    
    # 정리
    try:
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            delete_objects = {'Objects': [{'Key': obj['Key']} for obj in objects['Contents']]}
            s3_client.delete_objects(Bucket=bucket_name, Delete=delete_objects)
        s3_client.delete_bucket(Bucket=bucket_name)
        logger.info(f"테스트 버킷 정리 완료: {bucket_name}")
    except Exception as e:
        logger.error(f"테스트 버킷 정리 중 오류: {e}")

class TestBasicFunctionality:
    """기본 기능 테스트"""
    
    def test_bucket_operations(self, s3_client, test_config):
        """버킷 생성, 조회, 삭제 테스트"""
        logger.info("버킷 기본 작업 테스트 시작")
        
        bucket_name = f"{test_config.test_bucket_prefix}temp-{int(time.time())}"
        
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
        
        logger.info("버킷 기본 작업 테스트 완료")

    def test_object_crud_operations(self, s3_client, test_bucket):
        """객체 CRUD 작업 테스트"""
        logger.info("객체 CRUD 작업 테스트 시작")
        
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
        
        logger.info("객체 CRUD 작업 테스트 완료")

class TestDataIntegrity:
    """데이터 무결성 테스트"""
    
    @pytest.mark.parametrize("file_size", [1024, 1024*1024])  # 1KB, 1MB
    def test_file_integrity(self, s3_client, test_bucket, file_size):
        """파일 무결성 테스트"""
        logger.info(f"{file_size} bytes 파일 무결성 테스트 시작")
        
        import random
        test_data = bytes(random.getrandbits(8) for _ in range(file_size))
        original_md5 = hashlib.md5(test_data).hexdigest()
        
        object_key = f'integrity/test-{file_size}-bytes.dat'
        
        # 업로드 (ContentMD5 제거 - NCP 호환성 이슈로 인해)
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
        assert original_md5 == downloaded_md5
        assert len(test_data) == len(downloaded_data)
        assert test_data == downloaded_data
        
        logger.info(f"무결성 검증 성공: {file_size} bytes")

class TestErrorHandling:
    """오류 처리 테스트"""
    
    def test_nonexistent_bucket_operations(self, s3_client):
        """존재하지 않는 버킷 작업 테스트"""
        logger.info("존재하지 않는 버킷 작업 테스트 시작")
        
        nonexistent_bucket = 'nonexistent-bucket-12345'
        
        with pytest.raises(ClientError) as exc_info:
            s3_client.put_object(
                Bucket=nonexistent_bucket,
                Key='test.txt',
                Body='test content'
            )
        assert exc_info.value.response['Error']['Code'] == 'NoSuchBucket'
        logger.info("예상된 NoSuchBucket 오류 확인")
    
    def test_nonexistent_object_operations(self, s3_client, test_bucket):
        """존재하지 않는 객체 작업 테스트 - 호환성 이슈 테스트"""
        logger.info("존재하지 않는 객체 작업 테스트 시작")
        
        nonexistent_key = 'nonexistent/file.txt'
        
        # GET 요청 테스트
        with pytest.raises(ClientError) as exc_info:
            s3_client.get_object(Bucket=test_bucket, Key=nonexistent_key)
        assert exc_info.value.response['Error']['Code'] == 'NoSuchKey'
        
        # HEAD 요청 테스트 (NCP 호환성 이슈)
        with pytest.raises(ClientError) as exc_info:
            s3_client.head_object(Bucket=test_bucket, Key=nonexistent_key)
        
        error_code = exc_info.value.response['Error']['Code']
        
        # 이 테스트는 의도적으로 실패하도록 설계 (호환성 이슈 문서화)
        if error_code == '404':
            logger.warning("호환성 이슈 발견: HEAD 요청 시 '404' 반환 (표준: 'NoSuchKey')")
        
        assert error_code == 'NoSuchKey', f"S3 표준과 다른 에러 코드: {error_code}"

@pytest.fixture(scope="session", autouse=True)
def test_session_setup():
    """테스트 세션 설정"""
    start_time = datetime.now()
    logger.info("=== NCP Object Storage API 테스트 시작 ===")
    logger.info(f"테스트 시작 시간: {start_time}")
    
    yield
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info("=== NCP Object Storage API 테스트 완료 ===")
    logger.info(f"총 실행 시간: {duration}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])