"""
NCP Object Storage 클라이언트
Phase 1: 기본 S3 호환 API 테스트 ✅
Phase 2: 멀티파트 업로드, 메타데이터 관리 확장
"""
import os
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional, List, BinaryIO
from pathlib import Path
import mimetypes
from tenacity import retry, stop_after_attempt, wait_exponential


class NCPStorageClient:
    """NCP Object Storage S3 호환 클라이언트"""
    
    def __init__(self, endpoint: str, region: str, access_key: str = None, secret_key: str = None):
        """
        Args:
            endpoint: Object Storage 엔드포인트
            region: 리전 (kr-standard)
            access_key: NCP Access Key (환경변수에서 로드 가능)
            secret_key: NCP Secret Key (환경변수에서 로드 가능)
        """
        self.endpoint = endpoint
        self.region = region
        self.access_key = access_key or os.getenv('NCP_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('NCP_SECRET_KEY')
        
        if not self.access_key or not self.secret_key:
            raise ValueError("NCP credentials not provided. Set NCP_ACCESS_KEY and NCP_SECRET_KEY")
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=region
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def upload_file(
        self, 
        file_path: str, 
        bucket: str, 
        object_key: str = None,
        metadata: Dict[str, str] = None,
        content_type: str = None
    ) -> Dict:
        """
        파일 업로드 (재시도 로직 포함)
        
        Args:
            file_path: 로컬 파일 경로
            bucket: 버킷 이름
            object_key: Object Storage 키 (미지정 시 파일명 사용)
            metadata: 사용자 정의 메타데이터
            content_type: MIME 타입 (미지정 시 자동 감지)
        
        Returns:
            업로드 결과 딕셔너리
        """
        if not object_key:
            object_key = Path(file_path).name
        
        # Content-Type 자동 감지
        if not content_type:
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or 'application/octet-stream'
        
        extra_args = {'ContentType': content_type}
        
        if metadata:
            extra_args['Metadata'] = metadata
        
        try:
            file_size = os.path.getsize(file_path)
            
            # 5MB 이상은 멀티파트 업로드 사용
            if file_size > 5 * 1024 * 1024:
                self.s3_client.upload_file(
                    file_path, 
                    bucket, 
                    object_key,
                    ExtraArgs=extra_args,
                    Config=boto3.s3.transfer.TransferConfig(
                        multipart_threshold=5 * 1024 * 1024,
                        max_concurrency=10
                    )
                )
            else:
                self.s3_client.upload_file(file_path, bucket, object_key, ExtraArgs=extra_args)
            
            return {
                'success': True,
                'bucket': bucket,
                'key': object_key,
                'size': file_size,
                'content_type': content_type,
                'url': f"{self.endpoint}/{bucket}/{object_key}"
            }
        except ClientError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }
    
    def upload_fileobj(
        self, 
        file_obj: BinaryIO, 
        bucket: str, 
        object_key: str,
        metadata: Dict[str, str] = None,
        content_type: str = 'application/octet-stream'
    ) -> Dict:
        """파일 객체 업로드 (메모리에서 직접 업로드)"""
        extra_args = {'ContentType': content_type}
        if metadata:
            extra_args['Metadata'] = metadata
        
        try:
            self.s3_client.upload_fileobj(file_obj, bucket, object_key, ExtraArgs=extra_args)
            return {
                'success': True,
                'bucket': bucket,
                'key': object_key,
                'url': f"{self.endpoint}/{bucket}/{object_key}"
            }
        except ClientError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, bucket: str, object_key: str, local_path: str) -> Dict:
        """파일 다운로드"""
        try:
            self.s3_client.download_file(bucket, object_key, local_path)
            return {
                'success': True,
                'local_path': local_path
            }
        except ClientError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_object_metadata(self, bucket: str, object_key: str) -> Dict:
        """객체 메타데이터 조회 (HEAD 요청)"""
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=object_key)
            return {
                'success': True,
                'size': response['ContentLength'],
                'content_type': response.get('ContentType'),
                'last_modified': response['LastModified'],
                'etag': response['ETag'],
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }
    
    def list_objects(self, bucket: str, prefix: str = '', max_keys: int = 1000) -> List[Dict]:
        """버킷 내 객체 목록 조회"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            return objects
        except ClientError as e:
            raise Exception(f"Failed to list objects: {str(e)}")
    
    def delete_object(self, bucket: str, object_key: str) -> Dict:
        """객체 삭제"""
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=object_key)
            return {'success': True}
        except ClientError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def copy_object(self, source_bucket: str, source_key: str, 
                    dest_bucket: str, dest_key: str) -> Dict:
        """객체 복사"""
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )
            return {
                'success': True,
                'source': f"{source_bucket}/{source_key}",
                'destination': f"{dest_bucket}/{dest_key}"
            }
        except ClientError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_presigned_url(self, bucket: str, object_key: str, 
                              expiration: int = 3600) -> Optional[str]:
        """Pre-signed URL 생성 (임시 다운로드 링크)"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None
