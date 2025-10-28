#!/usr/bin/env python3
"""
NCP Object Storage Pipeline - Quick Start Demo
빠른 시작 데모 스크립트
"""
import os
from pathlib import Path
from PIL import Image
import yaml

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)

print("=" * 60)
print("🚀 NCP Object Storage 통합 파이프라인 데모")
print("=" * 60)

# Step 1: 환경 확인
print("\n[1/5] 환경 확인...")
try:
    from src.storage.client import NCPStorageClient
    from src.optimizer.image_processor import ImageProcessor
    from src.cdn.manager import CDNManager
    from src.pipeline.media_pipeline import MediaPipeline
    print("✓ 모든 모듈 임포트 성공")
except ImportError as e:
    print(f"✗ 모듈 임포트 실패: {e}")
    print("  실행: pip install -r requirements.txt")
    exit(1)

# Step 2: 설정 로드
print("\n[2/5] 설정 로드...")
try:
    with open('config/config.yaml', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print("✓ config.yaml 로드 성공")
except Exception as e:
    print(f"✗ 설정 로드 실패: {e}")
    exit(1)

# Step 3: 테스트 이미지 생성
print("\n[3/5] 테스트 이미지 생성...")
demo_dir = Path("demo_output")
demo_dir.mkdir(exist_ok=True)

test_images = []
for i, (width, height, color) in enumerate([
    (1920, 1080, 'blue'),
    (1280, 720, 'red'),
    (640, 480, 'green')
]):
    img_path = demo_dir / f"test_{i+1}_{width}x{height}.jpg"
    img = Image.new('RGB', (width, height), color=color)
    img.save(img_path, format='JPEG', quality=95)
    test_images.append(img_path)
    print(f"  ✓ 생성: {img_path.name} ({width}x{height})")

# Step 4: 이미지 최적화 데모
print("\n[4/5] 이미지 최적화 실행...")
processor = ImageProcessor()

for img_path in test_images:
    output_path = demo_dir / f"{img_path.stem}_optimized.webp"
    result = processor.optimize_image(
        str(img_path),
        str(output_path),
        target_format='webp',
        quality=80
    )
    
    if result.success:
        print(f"  ✓ {img_path.name}")
        print(f"    - 원본: {result.original_size / 1024:.1f}KB")
        print(f"    - 최적화: {result.optimized_size / 1024:.1f}KB")
        print(f"    - 감소율: {result.reduction_percent:.1f}%")
    else:
        print(f"  ✗ 실패: {result.error}")

# Step 5: 통계 출력
print("\n[5/5] 최적화 통계...")
stats = processor.get_statistics()
print(f"  - 처리된 파일: {stats['total_processed']}개")
print(f"  - 원본 용량: {stats['total_original_size'] / (1024*1024):.2f}MB")
print(f"  - 최적화 용량: {stats['total_optimized_size'] / (1024*1024):.2f}MB")
print(f"  - 평균 감소율: {stats['average_reduction_percent']:.1f}%")
print(f"  - 절감 용량: {stats['total_reduction_bytes'] / (1024*1024):.2f}MB")

# 결과 파일 목록
print("\n" + "=" * 60)
print("✅ 데모 완료!")
print("=" * 60)
print(f"\n생성된 파일 위치: {demo_dir.absolute()}")
print("\n다음 단계:")
print("  1. 환경 변수 설정:")
print("     export NCP_ACCESS_KEY='your_key'")
print("     export NCP_SECRET_KEY='your_secret'")
print("  2. 전체 테스트 실행:")
print("     pytest tests/integration/ -v -s")
print("  3. 모니터링 대시보드 실행:")
print("     streamlit run src/monitoring/dashboard.py")
print()

# Mock 파이프라인 실행 (실제 NCP 연동 없이)
print("\n[보너스] Mock 파이프라인 시뮬레이션...")
print("  (실제 NCP 연동은 환경 변수 설정 후 가능)")
try:
    # Mock 클라이언트 (환경 변수 없어도 동작)
    print("  ✓ Storage 클라이언트 초기화 (Mock)")
    print("  ✓ CDN 매니저 초기화 (Mock)")
    print("  ✓ 파이프라인 준비 완료")
    print("\n  실제 NCP 연동 시 다음 작업 수행:")
    print("    1. Object Storage 업로드")
    print("    2. CDN Purge 요청")
    print("    3. 캐시 상태 확인")
    print("    4. 배포 검증")
except Exception as e:
    print(f"  ℹ️  Mock 모드: {e}")

print("\n" + "=" * 60)
print("📚 더 알아보기:")
print("  - README.md: 프로젝트 전체 설명")
print("  - docs/PORTFOLIO.md: 포트폴리오 문서")
print("  - tests/: 테스트 코드 및 사용 예제")
print("=" * 60)
