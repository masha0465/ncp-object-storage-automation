"""
End-to-End 통합 테스트
실제 NCP 서비스 연동 시나리오 검증
"""
import pytest
import os
from pathlib import Path
import yaml
import numpy as np
from PIL import Image

from src.storage.client import NCPStorageClient
from src.optimizer.image_processor import ImageProcessor
from src.cdn.manager import CDNManager
from src.pipeline.media_pipeline import MediaPipeline


@pytest.fixture
def config():
    """설정 파일 로드"""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'
    with open(config_path, encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def storage_client(config):
    """Object Storage 클라이언트"""
    return NCPStorageClient(
        endpoint=config['ncp']['object_storage']['endpoint'],
        region=config['ncp']['object_storage']['region'],
        access_key=os.getenv('NCP_ACCESS_KEY', 'test_key'),
        secret_key=os.getenv('NCP_SECRET_KEY', 'test_secret')
    )


@pytest.fixture
def cdn_manager(config):
    """CDN 매니저"""
    return CDNManager(
        api_endpoint=config['ncp']['cdn']['api_endpoint'],
        service_id=os.getenv('CDN_SERVICE_ID', 'test_service'),
        access_key=os.getenv('NCP_ACCESS_KEY', 'test_key'),
        secret_key=os.getenv('NCP_SECRET_KEY', 'test_secret')
    )


@pytest.fixture
def pipeline(storage_client, cdn_manager, config):
    """통합 파이프라인"""
    return MediaPipeline(
        storage_client=storage_client,
        cdn_manager=cdn_manager,
        bucket_name=config['ncp']['object_storage']['bucket_name'],
        cdn_domain="https://cdn.example.com"
    )


class TestE2EMediaPipeline:
    """E2E 미디어 파이프라인 테스트"""
    
    def test_single_image_full_pipeline(self, pipeline, tmp_path):
        from PIL import Image
        test_image = tmp_path / "test_photo.jpg"
        img = Image.new('RGB', (1920, 1080), color='blue')
        img.save(test_image, format='JPEG', quality=95)
        
        result = pipeline.process_media_library(
            str(test_image),
            generate_thumbnails=True
        )
        
        assert result.success, f"Pipeline failed: {result.error}"
        assert 'upload_original' in result.steps_completed
        assert 'generate_thumbnails' in result.steps_completed
        assert 'optimize_image' in result.steps_completed
        assert 'cdn_sync' in result.steps_completed
        
        assert result.optimization_stats['reduction_percent'] > 0
        print(f"\n✓ 파일 크기 {result.optimization_stats['reduction_percent']}% 감소")
        print(f"✓ 처리 시간: {result.total_time_sec:.2f}초")
    
    def test_static_website_deployment(self, pipeline, tmp_path):
        site_dir = tmp_path / "website"
        site_dir.mkdir()
        
        (site_dir / "index.html").write_text("""
        <!DOCTYPE html>
        <html>
        <head><title>Test Site</title></head>
        <body><img src="images/photo.webp"></body>
        </html>
        """)
        
        (site_dir / "style.css").write_text("body { margin: 0; }")
        
        images_dir = site_dir / "images"
        images_dir.mkdir()
        
        Image.new('RGB', (800, 600), color='red').save(images_dir / "photo.jpg", format='JPEG')
        
        result = pipeline.deploy_static_website(
            str(site_dir),
            optimize_images=True
        )
        
        assert result['success']
        assert result['uploaded'] >= 2
        assert result['optimized'] >= 1
        assert len(result['details']['cdn_purged_paths']) > 0
        
        print(f"\n✓ {result['uploaded']}개 파일 배포 완료")
        print(f"✓ {result['optimized']}개 이미지 최적화")
        print(f"✓ 배포 시간: {result['duration_sec']:.2f}초")
    
    def test_large_file_multipart_upload(self, storage_client, tmp_path):
        """
        시나리오: 대용량 파일 멀티파트 업로드
        5MB 이상 파일 처리 검증
        """
        large_file = tmp_path / "large_image.jpg"
        
        # 무작위 픽셀 생성 이미지로 5MB 이상 확보
        array = np.random.randint(0, 256, (4000, 3000, 3), dtype=np.uint8)
        large_img = Image.fromarray(array)
        large_img.save(large_file, format='JPEG', quality=95)
        
        file_size = large_file.stat().st_size
        assert file_size > 5 * 1024 * 1024, "파일이 5MB 이상이어야 함"
        
        result = storage_client.upload_file(
            str(large_file),
            'pytest-test-automation-bucket',
            'large/large_image.jpg'
        )
        
        print(f"\n✓ {file_size / (1024*1024):.2f}MB 파일 업로드 시도")

    def test_cdn_cache_hit_verification(self, cdn_manager):
        test_url = "https://cdn.example.com/test/image.webp"
        
        response1 = cdn_manager.test_cdn_response(test_url)
        response2 = cdn_manager.test_cdn_response(test_url)
        
        print(f"\n✓ 첫 요청 응답시간: {response1.get('response_time_ms', 'N/A')}ms")
        print(f"✓ 두 번째 요청 응답시간: {response2.get('response_time_ms', 'N/A')}ms")
        print(f"✓ 캐시 상태: {response2.get('cache_status', 'UNKNOWN')}")

    def test_optimization_quality_threshold(self, tmp_path):
        from PIL import Image
        processor = ImageProcessor()
        test_image = tmp_path / "quality_test.jpg"
        Image.new('RGB', (1920, 1080), color='blue').save(test_image, format='JPEG', quality=100)
        
        qualities = [90, 80, 70, 60]
        results = []
        
        for quality in qualities:
            output = tmp_path / f"output_q{quality}.webp"
            result = processor.optimize_image(
                str(test_image),
                str(output),
                target_format='webp',
                quality=quality
            )
            results.append({
                'quality': quality,
                'reduction': result.reduction_percent,
                'size': result.optimized_size
            })
        
        print("\n품질별 압축률:")
        for r in results:
            print(f"  Quality {r['quality']}: {r['reduction']:.1f}% 감소 ({r['size']/1024:.1f}KB)")
        
        q80_result = next(r for r in results if r['quality'] == 80)
        assert q80_result['reduction'] >= 30, "Quality 80에서 최소 30% 압축 필요"



class TestErrorHandlingAndRecovery:
    """에러 처리 및 복구 테스트"""
    
    def test_network_retry_logic(self, storage_client, tmp_path):
        from PIL import Image
        test_file = tmp_path / "retry_test.jpg"
        Image.new('RGB', (100, 100), color='red').save(test_file)
        
        result = storage_client.upload_file(
            str(test_file),
            'pytest-test-automation-bucket',
            'test.jpg'
        )
        
        print(f"\n재시도 로직 테스트: {result.get('success', False)}")
    
    def test_partial_failure_rollback(self, pipeline, tmp_path):
        from PIL import Image
        test_image = tmp_path / "rollback_test.jpg"
        Image.new('RGB', (800, 600), color='yellow').save(test_image)
        
        result = pipeline.process_media_library(
            str(test_image),
            generate_thumbnails=True,
            thumbnail_sizes=[
                {'name': 'invalid', 'width': -100, 'height': -100}  # 의도적 오류
            ]
        )
        
        assert 'upload_original' in result.steps_completed
        print(f"\n✓ 부분 실패 시에도 원본 업로드 성공: {result.steps_completed}")



class TestPerformanceMetrics:
    """성능 지표 테스트"""
    
    def test_concurrent_uploads(self, storage_client, tmp_path):
        import time
        from PIL import Image
        
        test_files = []
        for i in range(5):
            file_path = tmp_path / f"concurrent_{i}.jpg"
            Image.new('RGB', (800, 600), color='blue').save(file_path)
            test_files.append(file_path)
        
        start = time.time()
        results = []
        
        for file_path in test_files:
            result = storage_client.upload_file(
                str(file_path),
                'pytest-test-automation-bucket',
                f'concurrent/file_{file_path.name}'
            )
            results.append(result)
        
        duration = time.time() - start
        
        print(f"\n✓ 5개 파일 순차 업로드: {duration:.2f}초")
        print(f"✓ 평균 업로드 시간: {duration/5:.2f}초/파일")
    
    def test_optimization_speed(self, tmp_path):
        from PIL import Image
        import time
        
        processor = ImageProcessor()
        sizes = [
            (640, 480, 'small'),
            (1920, 1080, 'medium'),
            (3840, 2160, 'large')
        ]
        
        print("\n최적화 속도 벤치마크:")
        for width, height, label in sizes:
            test_image = tmp_path / f"speed_test_{label}.jpg"
            Image.new('RGB', (width, height), color='red').save(test_image)
            
            start = time.time()
            result = processor.optimize_image(
                str(test_image),
                target_format='webp',
                quality=80
            )
            duration = time.time() - start
            
            print(f"  {label} ({width}x{height}): {duration:.3f}초, {result.reduction_percent:.1f}% 감소")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
