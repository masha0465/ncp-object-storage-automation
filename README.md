# NCP Object Storage 통합 자동화 플랫폼

**NCP 클라우드 QA 자동화 포트폴리오 프로젝트**

---

## 📋 목차

- [프로젝트 개요](#프로젝트-개요)
- [Phase 1: API 자동화 테스트](#phase-1-api-자동화-테스트)
- [Phase 2: 통합 파이프라인](#phase-2-통합-파이프라인)
- [주요 성과](#주요-성과)
- [기술 스택](#기술-스택)
- [실행 방법](#실행-방법)
- [프로젝트 구조](#프로젝트-구조)

---

## 🎯 프로젝트 개요

NCP Object Storage를 중심으로 **API 테스트 자동화**부터 **3개 서비스 통합 파이프라인**까지 구축한 클라우드 QA 자동화 프로젝트입니다.

### 진화 과정
```
Phase 1 (2025.08)         Phase 2 (2025.10)
API 테스트 자동화    →    통합 파이프라인
43개 테스트              9개 E2E 시나리오
단일 서비스              3개 서비스 통합
```

---

## 📌 Phase 1: API 자동화 테스트

### 개요
NCP Object Storage의 S3 호환 API에 대한 포괄적인 자동화 테스트 스위트를 개발하여 서비스 품질과 S3 표준 호환성을 검증합니다.

### 주요 성과
* **테스트 커버리지**: 43개 테스트 케이스
* **성공률**: 83% (5/6 핵심 테스트)
* **호환성 이슈 발견**: S3 표준과 다른 에러 코드 반환 발견
* **기술적 이슈 해결**: boto3 최신 버전 호환성 문제 해결

### 발견된 이슈
1. **boto3 버전 호환성**: 최신 버전(1.40.x)에서 AccessDenied 오류
   - 해결: 1.28.57로 다운그레이드
2. **S3 표준 불일치**: HEAD 요청 시 '404' 대신 'NoSuchKey' 반환해야 함
   - NCP 팀에 개선 제안

### Phase 1 실행 방법
```bash
# Phase 1 테스트 실행
pytest test_ncp_storage.py -v --html=reports/report.html
```

---

## 🚀 Phase 2: 통합 파이프라인

### 개요
Object Storage, CDN+, Image Optimizer 3개 NCP 서비스를 통합한 **프로덕션 레디** 미디어 처리 파이프라인을 구축했습니다.

### 🎯 핵심 기능

#### 1. **미디어 파이프라인**
```
업로드 → 최적화 → CDN 배포 → 검증
```
- 자동 이미지 최적화 (WebP/JPEG)
- CDN 캐시 자동 Purge
- 배포 상태 실시간 검증

#### 2. **정적 웹사이트 배포**
```
HTML/CSS/JS/이미지 → 일괄 최적화 → CDN 배포
```
- 8개 파일 동시 처리
- 자동 Content-Type 설정
- 배포 완료 후 200 OK 검증

#### 3. **실시간 모니터링**
- Streamlit 대시보드
- 업로드/최적화/CDN 성능 시각화
- 비용 절감 효과 분석

### 주요 성과

#### 정량적 지표
| 지표 | 목표 | 실제 결과 | 달성 |
|------|------|-----------|------|
| 통합 테스트 통과율 | 100% | 100% (9/9) | ✅ |
| 이미지 압축률 | 60% | **88.5%** | ✅ 초과달성 |
| 최적화 속도 (FHD) | <1.5초 | **0.17초** | ✅ 초과달성 |
| 최적화 속도 (4K) | <3.0초 | **0.66초** | ✅ 초과달성 |
| 실제 NCP 연동 | 성공 | ✅ 성공 | ✅ |
| CI/CD 파이프라인 | 구축 | ✅ 6 Jobs 통과 | ✅ |

#### 테스트 결과 (9개 E2E 시나리오)

**통합 파이프라인 (5개)**
```
✅ test_single_image_full_pipeline      단일 이미지 전체 파이프라인
✅ test_static_website_deployment       정적 웹사이트 배포 (8개 파일)
✅ test_large_file_multipart_upload     대용량 파일 멀티파트 업로드
✅ test_cdn_cache_hit_verification      CDN 캐시 검증
✅ test_optimization_quality_threshold  품질별 압축률 검증
```

**에러 처리 (2개)**
```
✅ test_network_retry_logic             네트워크 재시도 (3회)
✅ test_partial_failure_rollback        부분 실패 롤백
```

**성능 테스트 (2개)**
```
✅ test_concurrent_uploads              동시 업로드 (5개 파일)
✅ test_optimization_speed              최적화 속도 벤치마크
```

### Phase 2 실행 방법

#### 1. 데모 실행
```bash
# 전체 파이프라인 데모
python demo.py

# 예상 출력:
# ✓ 3개 이미지 최적화 (88.5% 평균 압축)
# ✓ 파이프라인 처리 시간: 2.0초
```

#### 2. 통합 테스트
```bash
# 환경 변수 설정
export NCP_ACCESS_KEY="your_access_key"
export NCP_SECRET_KEY="your_secret_key"

# 테스트 실행
pytest tests/integration/test_e2e_pipeline.py -v -s

# 예상 결과: 9 passed in 28s
```

#### 3. 대시보드 실행
```bash
# Streamlit 대시보드
streamlit run src/monitoring/dashboard.py

# 브라우저에서 http://localhost:8501 자동 열림
```

---

## 🏆 주요 성과 비교

### Phase 1 vs Phase 2

| 항목 | Phase 1 | Phase 2 |
|------|---------|---------|
| **서비스 범위** | Object Storage 단독 | Storage + CDN+ + Optimizer 통합 |
| **테스트 수** | 43개 API 테스트 | 9개 E2E + 6개 Unit |
| **테스트 유형** | API 기능 검증 | 통합 시나리오 검증 |
| **최적화** | 없음 | 60-88% 이미지 압축 |
| **모니터링** | 로그 기반 | 실시간 대시보드 (Streamlit) |
| **자동화** | pytest | pytest + GitHub Actions CI/CD |
| **실제 연동** | Object Storage | Object Storage + CDN+ + Optimizer |

### 통합 성과
```
✅ 총 테스트: 52개 (Phase 1: 43 + Phase 2: 9)
✅ 통과율: 100% (Phase 2 기준)
✅ 발견된 이슈: 2건 (S3 호환성)
✅ 이미지 압축률: 88.5% (Phase 2)
✅ CI/CD: GitHub Actions 6 Jobs 통과
✅ 실행 시간: 3분 미만 (전체 파이프라인)
```

---

## 🛠️ 기술 스택

### Backend & Testing
- **Python 3.11.9**
- **pytest 8.4.1** (테스트 프레임워크)
- **boto3 1.34.144** (NCP Object Storage SDK)
- **Pillow 10.4.0** (이미지 처리)
- **tenacity 8.5.0** (재시도 로직)

### Monitoring & Visualization
- **Streamlit 1.38.0** (실시간 대시보드)
- **Plotly 5.24.0** (인터랙티브 차트)
- **Pandas 2.2.2** (데이터 분석)

### DevOps
- **GitHub Actions** (CI/CD)
- **Docker** (컨테이너화)
- **pytest-html** (리포트 생성)

### NCP Services
- **Object Storage** (S3 호환)
- **CDN+** (캐시 제어)
- **Image Optimizer** (이미지 최적화)

---

## 📂 프로젝트 구조

```
ncp-object-storage-automation/
│
├── 📄 Phase 1 (API 테스트)
│   ├── test_ncp_storage.py          # Phase 1 메인 테스트
│   ├── issues-found.md              # 발견된 이슈 문서
│   └── portfolio-summary.md         # Phase 1 요약
│
├── 📦 Phase 2 (통합 파이프라인)
│   ├── src/
│   │   ├── storage/
│   │   │   └── client.py            # Object Storage 클라이언트
│   │   ├── optimizer/
│   │   │   └── image_processor.py   # 이미지 최적화
│   │   ├── cdn/
│   │   │   └── manager.py           # CDN 매니저
│   │   ├── pipeline/
│   │   │   └── media_pipeline.py    # 파이프라인 오케스트레이션
│   │   └── monitoring/
│   │       └── dashboard.py         # 실시간 대시보드
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   └── test_basic.py        # 단위 테스트 (6개)
│   │   ├── integration/
│   │   │   └── test_e2e_pipeline.py # 통합 테스트 (9개)
│   │   └── performance/
│   │       └── benchmark_optimizer.py # 성능 벤치마크
│   │
│   ├── config/
│   │   └── config.yaml              # Phase 1 + 2 통합 설정
│   │
│   ├── .github/
│   │   └── workflows/
│   │       └── phase2_integration.yml # CI/CD 파이프라인
│   │
│   ├── docs/
│   │   ├── PORTFOLIO.md             # 포트폴리오 문서
│   │   └── PROJECT_STRUCTURE.md     # 프로젝트 구조 가이드
│   │
│   ├── demo.py                      # 통합 데모 스크립트
│   ├── requirements.txt             # Python 패키지
│   └── README.md                    # 이 파일
│
└── reports/                         # 테스트 결과 리포트
```

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/masha0465/ncp-object-storage-automation.git
cd ncp-object-storage-automation

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일 생성:
```bash
NCP_ACCESS_KEY=your_access_key
NCP_SECRET_KEY=your_secret_key
NCP_ENDPOINT_URL=https://kr.object.ncloudstorage.com
NCP_REGION=kr-standard
```

### 3. 실행

```bash
# Phase 1 테스트
pytest test_ncp_storage.py -v

# Phase 2 데모
python demo.py

# Phase 2 통합 테스트
pytest tests/integration/ -v -s

# 대시보드
streamlit run src/monitoring/dashboard.py
```

---

## 📊 CI/CD 파이프라인

GitHub Actions를 통한 자동화된 테스트 및 배포:

```yaml
✅ 단위 테스트 (45초)
✅ 보안 검사 (1분 5초)
✅ 통합 테스트 (52초)
✅ 성능 벤치마크 (35초)
✅ Docker 이미지 빌드 (52초)
✅ 테스트 리포트 생성 (4초)
```

**총 실행 시간**: 약 3분

---

## 🎓 학습 성과

### Phase 1에서 Phase 2로의 진화

#### Phase 1 (2025.08)
- ✅ NCP Object Storage API 이해
- ✅ S3 호환성 검증
- ✅ 호환성 이슈 2건 발견
- ✅ pytest 기반 테스트 프레임워크 구축

#### Phase 2 (2025.10)
- ✅ 3개 NCP 서비스 통합
- ✅ 엔드투엔드 파이프라인 구축
- ✅ 실시간 모니터링 시스템
- ✅ CI/CD 파이프라인 구축
- ✅ Production-ready 아키텍처

### 기술적 성장
```
단일 API 테스트 → 통합 시나리오 검증
수동 실행 → 완전 자동화 (CI/CD)
로그 모니터링 → 실시간 대시보드
개념 증명 → 프로덕션 레디
```

---

## 💼 포트폴리오 하이라이트

> **"NCP 자격증 공부를 실전 프로젝트로 승화"**
> 
> Phase 1에서 API 테스트 자동화로 시작하여,
> Phase 2에서 3개 서비스를 통합한 프로덕션 레디 파이프라인을 완성했습니다.
> 
> **9년 클라우드 QA 경험**을 활용하여:
> - ✅ S3 호환성 이슈 발견 및 리포트
> - ✅ 엔드투엔드 통합 검증
> - ✅ 데이터 기반 품질 관리
> - ✅ CI/CD 자동화 구축

### 정량적 증거
```
✅ 52개 테스트 (Phase 1: 43 + Phase 2: 9 + Unit: 6)
✅ 88.5% 이미지 압축률 달성
✅ 실제 NCP 환경 연동 성공
✅ GitHub Actions CI/CD 구축
✅ 3분 이내 전체 파이프라인 실행
```

---

## 🔗 관련 링크

- **GitHub Repository**: [ncp-object-storage-automation](https://github.com/masha0465/ncp-object-storage-automation)
- **포트폴리오 문서**: [PORTFOLIO.md](docs/PORTFOLIO.md)
- **이슈 트래킹**: [issues-found.md](issues-found.md)

---

## 👤 작성자

**김선아**
- Email: masha0465@gmail.com
- GitHub: [@masha0465](https://github.com/masha0465)
- 경력: 9년 클라우드 QA (AWS, Azure, K8s)

---

## 📝 라이선스

이 프로젝트는 포트폴리오 목적으로 작성되었습니다.

---

**프로젝트 상태**: ✅ Production Ready  
**마지막 업데이트**: 2025-10-28
