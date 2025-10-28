"""
이미지 최적화 성능 벤치마크
"""
import time
from PIL import Image
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.optimizer.image_processor import ImageProcessor

def main():
    processor = ImageProcessor()
    test_dir = Path('perf_test')
    test_dir.mkdir(exist_ok=True)

    # 다양한 크기의 이미지 생성 및 최적화
    sizes = [(640, 480), (1920, 1080), (3840, 2160)]
    results = []

    print("🔥 이미지 최적화 성능 벤치마크")
    print("=" * 50)

    for width, height in sizes:
        img_path = test_dir / f'test_{width}x{height}.jpg'
        Image.new('RGB', (width, height), color='blue').save(img_path, quality=95)
        
        start = time.time()
        result = processor.optimize_image(str(img_path), target_format='webp', quality=80)
        duration = time.time() - start
        
        results.append({
            'size': f'{width}x{height}',
            'duration': duration,
            'reduction': result.reduction_percent
        })
        print(f'✓ {width}x{height}: {duration:.3f}s, {result.reduction_percent:.1f}% 감소')

    print("=" * 50)

    # 성능 기준 검증
    assert all(r['duration'] < 5.0 for r in results), '최적화는 5초 이내여야 함'
    assert all(r['reduction'] > 30 for r in results), '최소 30% 이상 압축 필요'
    
    print('✅ 성능 벤치마크 통과')
    
    # 평균 계산
    avg_duration = sum(r['duration'] for r in results) / len(results)
    avg_reduction = sum(r['reduction'] for r in results) / len(results)
    
    print(f'\n📊 평균 성능')
    print(f'  - 처리 시간: {avg_duration:.3f}초')
    print(f'  - 압축률: {avg_reduction:.1f}%')

if __name__ == '__main__':
    main()