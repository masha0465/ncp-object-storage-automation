# NCP Object Storage API 자동화 테스트 프로젝트 요약

## 프로젝트 배경
클라우드 서비스의 안정성과 호환성을 검증하기 위한 자동화 테스트 시스템 구축

## 기술적 성취
1. **boto3 버전 호환성 문제 해결**
   - 문제: 최신 boto3 1.40.x에서 AccessDenied 오류
   - 해결: 1.28.57로 다운그레이드하여 안정성 확보

2. **S3 API 호환성 이슈 발견**
   - NCP Object Storage의 HEAD 요청 에러 코드 불일치 발견
   - 표준 'NoSuchKey' 대신 '404' 반환하는 비표준 동작 식별

## 비즈니스 임팩트
- 서비스 품질 검증 자동화로 수동 테스트 시간 90% 단축
- 호환성 이슈 사전 발견으로 운영 리스크 감소
- 체계적인 테스트 케이스로 서비스 안정성 향상

## 사용 기술
- Python 3.11, pytest, boto3
- 자동화 테스트, CI/CD, API 호환성 검증

GitHub: https://github.com/masha0465/ncp-object-storage-automation