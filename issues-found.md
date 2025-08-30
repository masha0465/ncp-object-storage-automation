# 발견된 이슈 목록

## 이슈 1: boto3 최신 버전 호환성 문제

**문제**: boto3 1.40.18 버전에서 NCP Object Storage PutObject 작업 시 AccessDenied 오류 발생

**재현 방법**:
- boto3==1.40.18, botocore==1.40.18 설치
- NCP Object Storage에 파일 업로드 시도
- 결과: AccessDenied 오류 발생

**해결 방법**: boto3==1.28.57, botocore==1.31.57로 다운그레이드

**영향도**: 높음 (최신 boto3 기능 사용 불가)

## 이슈 2: S3 API 표준 호환성 문제

**문제**: HEAD 요청으로 존재하지 않는 객체 조회 시 표준과 다른 에러 코드 반환

**예상 동작**: Error Code = 'NoSuchKey'
**실제 동작**: Error Code = '404'

**재현 방법**:
```python
s3_client.head_object(Bucket='bucket_name', Key='nonexistent_key')
# 반환: ClientError with Code='404'
# 예상: ClientError with Code='NoSuchKey'