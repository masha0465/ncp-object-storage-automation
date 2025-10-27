# 📋 NCP QA 재지원 포트폴리오

**지원자**: 김선아  
**작성일**: 2025년 10월 28일  
**GitHub**: https://github.com/masha0465/ncp-object-storage-automation

---

## 1. NCP Object Storage 통합 자동화 플랫폼 (2025.08 - 2025.10)

### 📌 프로젝트 개요

**배경**: NCP Professional 자격증 취득 후 Object Storage S3 호환 API 실제 사용 중 발견한 문제들을 개선하고, 단순 API 테스트를 넘어 **실무에서 활용 가능한 통합 파이프라인**을 구축

**목표**: Object Storage를 중심으로 CDN+, Image Optimizer를 연동한 종합 자동화 플랫폼 구축

---

### 🎯 핵심 성과

#### Phase 1: API 테스트 자동화 (2025.08) ✅
```
✓ S3 API 호환성 이슈 2건 발견 및 리포트
  - HEAD 요청 에러 코드 불일치 (이슈 #13)
  - boto3 버전 호환성 문제 (이슈 #16)

✓ pytest 기반 자동화 프레임워크 구축
  - 테스트 커버리지 85%+
  - GitHub Actions CI/CD 파이프라인
  - 수동 테스트 대비 80% 시간 단축
```

#### Phase 2: 통합 파이프라인 구축 (2025.10) ✨
```
✓ 3개 NCP 서비스 통합 (Storage → Optimizer → CDN+)
✓ 이미지 최적화 자동화: 평균 70% 크기 감소
✓ CDN 캐시 히트율 87% 달성 (목표 80% 초과)
✓ 실시간 모니터링 대시보드 구축 (Streamlit)
✓ 에러 복구 메커니즘: 재시도 로직 + 롤백 자동화
✓ 스토리지 비용 60% 절감 (월 $15 → $6)
```

---

### 🏗️ 기술 아키텍처

```
┌─────────────┐
│ Local Files │
└──────┬──────┘
       │
       ▼
┌────────────────────────────┐
│  Image Optimizer Module     │  ← WebP/AVIF 변환, 70% 압축
└──────┬─────────────────────┘
       │
       ▼
┌────────────────────────────┐
│  NCP Object Storage         │  ← S3 호환 API, 멀티파트 업로드
└──────┬─────────────────────┘
       │
       ▼
┌────────────────────────────┐
│  CDN+ Distribution          │  ← 캐시 제어, 87% 히트율
└──────┬─────────────────────┘
       │
       ▼
┌────────────────────────────┐
│  Monitoring Dashboard       │  ← 실시간 지표, 비용 분석
└────────────────────────────┘
```

---

### 🛠️ 기술 스택

| 카테고리 | 기술 |
|---------|------|
| **Backend** | Python 3.11, boto3, pytest |
| **Image** | Pillow, WebP/AVIF |
| **CI/CD** | GitHub Actions, Docker |
| **Monitoring** | Streamlit, Plotly, Pandas |
| **NCP Services** | Object Storage, CDN+, Image Optimizer |
| **Testing** | pytest, pytest-cov, pytest-asyncio |

---

### 📊 실무 시나리오 검증

#### 시나리오 1: 정적 웹사이트 배포
```python
# 1. 이미지 자동 최적화 (JPEG → WebP)
# 2. Object Storage 업로드
# 3. CDN 배포 및 캐시 Purge
# 4. 배포 검증 (200 OK, 콘텐츠 무결성)

result = pipeline.deploy_static_website(
    source_dir="./website",
    optimize_images=True
)

# 결과: 3개 HTML/CSS + 5개 이미지 = 총 8개 파일 배포
# 이미지 평균 68% 크기 감소, 배포 시간 4.2초
```

#### 시나리오 2: 미디어 라이브러리 관리
```python
# 1. 원본 업로드
# 2. 다중 해상도 썸네일 생성 (1920px, 1280px, 640px)
# 3. 전체 WebP 최적화
# 4. CDN 동기화

result = pipeline.process_media_library(
    image_path="photo.jpg",
    generate_thumbnails=True
)

# 결과: 원본 5.2MB → 최적화 1.8MB (65% 감소)
#       + 3개 썸네일 생성, 총 처리 시간 2.1초
```

#### 시나리오 3: 대용량 파일 처리
```python
# 5MB 이상 파일 → 멀티파트 업로드 자동 전환
# Tenacity 재시도 로직 (Exponential Backoff)
# 네트워크 오류 시 최대 3회 재시도

result = storage.upload_file(
    "large_image.jpg",  # 8.5MB
    bucket="media-library",
    object_key="originals/large.jpg"
)

# 결과: 멀티파트 업로드 성공, 업로드 시간 6.8초
```

---

### 🧪 테스트 전략

#### 단위 테스트 (Unit Tests)
```python
# src/storage/client.py - 92% 커버리지
✓ 기본 CRUD 작업
✓ 멀티파트 업로드 로직
✓ 에러 핸들링 (ClientError)
✓ Pre-signed URL 생성

# src/optimizer/image_processor.py - 88% 커버리지
✓ 다양한 포맷 변환 (JPEG, PNG, WebP)
✓ 품질별 압축률 검증
✓ EXIF 회전 정보 처리
✓ 메모리 최적화 (파일 I/O 없음)

# src/cdn/manager.py - 90% 커버리지
✓ 캐시 Purge 요청
✓ 캐시 상태 확인
✓ CDN 응답 헤더 검증
```

#### 통합 테스트 (Integration Tests)
```python
# tests/integration/test_e2e_pipeline.py
✓ E2E 미디어 파이프라인
✓ 정적 웹사이트 배포
✓ CDN 캐시 히트율 검증
✓ 최적화 품질 임계값 검증

# 테스트 결과
- 총 28개 테스트 케이스
- 전체 통과율 100%
- E2E 테스트 평균 수행 시간: 15초
```

#### 성능 벤치마크
```
이미지 최적화 속도:
  640x480   → 0.3초 (목표: <0.5초) ✓
  1920x1080 → 1.2초 (목표: <1.5초) ✓
  3840x2160 → 2.8초 (목표: <3.0초) ✓

업로드 속도:
  1MB 파일  → 0.8초
  5MB 파일  → 2.5초
  10MB 파일 → 5.2초

압축률:
  JPEG → WebP: 평균 72% 감소
  PNG → WebP:  평균 68% 감소
```

---

### 📈 측정 가능한 성과

#### 정량적 지표
| 지표 | 결과 | 목표 | 달성도 |
|------|------|------|--------|
| 업로드 성공률 | 99.5% | 99.0% | ✅ 초과 |
| 이미지 압축률 | 70% | 60% | ✅ 초과 |
| CDN 캐시 히트율 | 87% | 80% | ✅ 초과 |
| 평균 응답 시간 | 45ms | <500ms | ✅ 초과 |
| 테스트 커버리지 | 87% | 85% | ✅ 초과 |
| 스토리지 비용 절감 | 60% | 40% | ✅ 초과 |

#### 정성적 성과
```
✓ 실무 적용 가능한 프로덕션 레디 코드
✓ 9년 경력 기반 클라우드 베스트 프랙티스 적용
✓ 에러 복구, 재시도 로직 등 엔터프라이즈급 안정성
✓ 실시간 모니터링으로 문제 조기 발견 가능
✓ 명확한 문서화 및 테스트 코드 (유지보수성 우수)
```

---

### 🚨 발견 이슈 및 개선 제안

#### 1. S3 API 표준 준수성 이슈 (이슈 #13)
**문제**: HEAD 요청 시 존재하지 않는 객체에 대해 `403 Forbidden` 반환 (AWS S3는 `404 Not Found`)

**영향도**: S3 표준 준수 애플리케이션에서 에러 처리 로직 불일치 발생 가능

**제안**: NCP Object Storage API가 AWS S3 표준을 완전히 준수하도록 개선

**대응**: 현재는 클라이언트 코드에서 두 가지 에러 코드 모두 처리하도록 구현

#### 2. boto3 버전 호환성 문제 (이슈 #16)
**문제**: boto3 1.28.x 버전에서 멀티파트 업로드 시 간헐적 실패

**해결**: boto3==1.34.144 버전 명시 및 테스트 검증 완료

**권장사항**: NCP 공식 문서에 검증된 boto3 버전 명시 필요

---

### 🎓 학습 및 성장

#### 기술적 깊이
- [x] NCP 3개 서비스 통합 운영 경험
- [x] 클라우드 네이티브 아키텍처 설계 역량
- [x] 이벤트 기반 파이프라인 구축
- [x] 성능 최적화 및 비용 절감 전략

#### QA 엔지니어로서 성장
- [x] 단일 기능 테스트 → **통합 시나리오 검증**
- [x] 수동 테스트 → **완전 자동화 CI/CD**
- [x] 버그 발견 → **성능/비용까지 고려한 품질 관리**

#### 실무 적용 가능성
> "이 프로젝트를 통해 **'NCP 서비스를 단순히 사용하는 것이 아니라,  
> 어떻게 테스트하고 품질을 보증할 것인가'**에 대한 실전 경험을 쌓았습니다.  
>
> 9년간 다양한 클라우드 환경을 테스트하며 쌓은 노하우를  
> NCP 특화 QA 역량으로 발전시키는 것이 이 프로젝트의 궁극적인 목표였습니다."

---

### 🔗 링크

- **GitHub Repository**: https://github.com/masha0465/ncp-object-storage-automation
- **모니터링 대시보드**: `streamlit run src/monitoring/dashboard.py`
- **CI/CD 파이프라인**: [GitHub Actions](https://github.com/masha0465/ncp-object-storage-automation/actions)
- **테스트 리포트**: [Coverage Report](https://codecov.io/gh/masha0465/ncp-object-storage-automation)

---

### 📦 첨부 파일

1. **NCP Object Storage Test Case v1.0.pdf**
   - Phase 1에서 작성한 기본 테스트 케이스
   - 기능/비기능 TC 50+ 케이스

2. **이슈 리스트.pdf**
   - 테스트 중 발견한 이슈 16건
   - 이슈 #13, #16 상세 분석 포함

3. **Phase 2 아키텍처 다이어그램**
   - 통합 파이프라인 구조도
   - 데이터 플로우 및 상호작용

4. **성능 벤치마크 리포트**
   - 최적화 전후 비교 데이터
   - 비용 절감 효과 계산

---

### 💡 차별화 포인트

#### 1. 실무 경험 기반의 문제 해결
- 단순 학습 프로젝트가 아닌, **실제 사용 중 발견한 문제를 해결**
- NCP 서비스 개선에 기여할 수 있는 구체적인 이슈 리포트

#### 2. 엔드투엔드 통합 역량
- 개별 서비스 테스트 → **3개 서비스 통합 파이프라인 구축**
- 실무에서 바로 활용 가능한 프로덕션 레디 수준

#### 3. 데이터 기반 품질 관리
- 정량적 지표 측정 (압축률, 캐시 히트율, 응답 시간)
- 실시간 모니터링 대시보드로 문제 조기 발견

#### 4. 9년 경력의 클라우드 QA 노하우
- AWS, Azure, K8s 경험을 NCP에 적용
- 엔터프라이즈급 안정성 및 에러 처리

---

### 🎯 네이버 클라우드 QA에 지원하는 이유

> "지난 NCP QA 채용 공고에 지원했을 당시, Object Storage API 테스트 자동화를 진행하며  
> **'이 정도로는 부족하다'**는 생각이 들었습니다.
>
> 단순히 API를 테스트하는 것이 아니라,  
> **실제 서비스 파이프라인에서 어떻게 동작하는지,  
> 어떻게 최적화하고 비용을 절감할 수 있는지**까지 검증해야  
> 진정한 QA라고 생각했습니다.
>
> 그래서 Phase 2에서 CDN+, Image Optimizer까지 통합하여  
> **엔드투엔드 품질 보증 체계**를 구축했습니다.
>
> 이번 재지원에서는 이렇게 발전시킨 프로젝트와 함께,  
> **9년간 쌓은 클라우드 QA 경험을 네이버 클라우드 품질 향상에 기여**하고 싶습니다."

---

**작성자**: 김선아  
**연락처**: pingpong_v@naver.com  
**GitHub**: https://github.com/masha0465  
**날짜**: 2025년 10월 28일
