# NCP Object Storage API 자동화 테스트

## 프로젝트 개요
NCP Object Storage의 S3 호환 API에 대한 포괄적인 자동화 테스트 스위트를 개발하여 서비스 품질과 S3 표준 호환성을 검증합니다.

## 주요 성과
- **테스트 커버리지**: 6개 테스트 케이스 (83% 성공률)
- **호환성 이슈 발견**: S3 표준과 다른 에러 코드 반환 발견
- **기술적 이슈 해결**: boto3 최신 버전 호환성 문제 해결

## 기술 스택
- Python 3.11.9
- pytest 8.4.1
- boto3 1.28.57 (호환성 문제로 다운그레이드)
- NCP Object Storage S3 Compatible API

## 발견된 이슈
1. **boto3 버전 호환성**: 최신 버전(1.40.x)에서 AccessDenied 오류
2. **S3 표준 불일치**: HEAD 요청 시 '404' 대신 'NoSuchKey' 반환해야 함

## 실행 방법
```bash
pip install -r requirements.txt
pytest test_ncp_storage.py -v --html=reports/report.html