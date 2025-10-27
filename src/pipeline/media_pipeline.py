"""
통합 미디어 처리 파이프라인
Object Storage → Image Optimizer → CDN+ 연계
"""
import os
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

from ..storage.client import NCPStorageClient
from ..optimizer.image_processor import ImageProcessor
from ..cdn.manager import CDNManager, CacheController


@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""
    success: bool
    steps_completed: List[str]
    file_path: str
    storage_url: str
    cdn_url: str
    optimization_stats: Dict
    total_time_sec: float
    error: str = None


class MediaPipeline:
    """미디어 파일 처리 통합 파이프라인"""
    
    def __init__(
        self, 
        storage_client: NCPStorageClient,
        cdn_manager: CDNManager,
        bucket_name: str,
        cdn_domain: str
    ):
        """
        Args:
            storage_client: Object Storage 클라이언트
            cdn_manager: CDN 매니저
            bucket_name: 버킷 이름
            cdn_domain: CDN 도메인 (예: https://cdn.example.com)
        """
        self.storage = storage_client
        self.cdn = cdn_manager
        self.cache_controller = CacheController(cdn_manager)
        self.optimizer = ImageProcessor()
        self.bucket = bucket_name
        self.cdn_domain = cdn_domain
    
    def deploy_static_website(
        self, 
        source_dir: str, 
        optimize_images: bool = True
    ) -> Dict:
        """
        정적 웹사이트 배포 시나리오
        
        1. 이미지 최적화
        2. Object Storage 업로드
        3. CDN 캐시 Purge
        4. 배포 검증
        
        Args:
            source_dir: 소스 디렉토리
            optimize_images: 이미지 자동 최적화 여부
        
        Returns:
            배포 결과 및 통계
        """
        start_time = datetime.now()
        results = {
            'uploaded_files': [],
            'optimized_images': [],
            'failed_files': [],
            'cdn_purged_paths': []
        }
        
        source_path = Path(source_dir)
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(source_path)
                object_key = str(relative_path).replace('\\', '/')
                
                # 이미지 파일 최적화
                if optimize_images and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    optimized_path = file_path.parent / f"{file_path.stem}_optimized{file_path.suffix}"
                    
                    opt_result = self.optimizer.optimize_image(
                        str(file_path),
                        str(optimized_path),
                        target_format='webp',
                        quality=80
                    )
                    
                    if opt_result.success:
                        upload_file = str(optimized_path)
                        object_key = str(relative_path.with_suffix('.webp')).replace('\\', '/')
                        results['optimized_images'].append({
                            'file': str(file_path),
                            'reduction_percent': opt_result.reduction_percent
                        })
                    else:
                        upload_file = str(file_path)
                else:
                    upload_file = str(file_path)
                
                # Object Storage 업로드
                upload_result = self.storage.upload_file(
                    upload_file,
                    self.bucket,
                    object_key
                )
                
                if upload_result['success']:
                    results['uploaded_files'].append(object_key)
                else:
                    results['failed_files'].append({
                        'file': str(file_path),
                        'error': upload_result.get('error')
                    })
        
        # CDN 캐시 Purge
        if results['uploaded_files']:
            purge_paths = [f"/{path}" for path in results['uploaded_files']]
            purge_result = self.cdn.purge_cache(purge_paths)
            results['cdn_purged_paths'] = purge_paths
            results['purge_status'] = purge_result.get('status')
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': len(results['failed_files']) == 0,
            'total_files': len(results['uploaded_files']) + len(results['failed_files']),
            'uploaded': len(results['uploaded_files']),
            'optimized': len(results['optimized_images']),
            'failed': len(results['failed_files']),
            'duration_sec': duration,
            'details': results,
            'optimization_stats': self.optimizer.get_statistics()
        }
    
    def process_media_library(
        self, 
        image_path: str,
        generate_thumbnails: bool = True,
        thumbnail_sizes: List[Dict] = None
    ) -> PipelineResult:
        """
        미디어 라이브러리 관리 시나리오
        
        1. 원본 업로드
        2. 다중 해상도 썸네일 생성
        3. 전체 최적화 (WebP 변환)
        4. CDN 동기화
        
        Args:
            image_path: 원본 이미지 경로
            generate_thumbnails: 썸네일 생성 여부
            thumbnail_sizes: 썸네일 크기 설정
        
        Returns:
            PipelineResult
        """
        start_time = datetime.now()
        steps_completed = []
        
        try:
            file_name = Path(image_path).name
            
            # Step 1: 원본 업로드
            original_key = f"originals/{file_name}"
            upload_result = self.storage.upload_file(
                image_path,
                self.bucket,
                original_key
            )
            
            if not upload_result['success']:
                raise Exception(f"Upload failed: {upload_result.get('error')}")
            
            steps_completed.append('upload_original')
            storage_url = upload_result['url']
            
            # Step 2: 썸네일 생성
            thumbnail_results = []
            if generate_thumbnails:
                if not thumbnail_sizes:
                    thumbnail_sizes = [
                        {'name': 'large', 'width': 1920, 'height': 1080},
                        {'name': 'medium', 'width': 1280, 'height': 720},
                        {'name': 'small', 'width': 640, 'height': 360}
                    ]
                
                thumbnails = self.optimizer.generate_thumbnails(
                    image_path,
                    thumbnail_sizes,
                    format='webp',
                    quality=80
                )
                
                # 썸네일 업로드
                for thumb in thumbnails:
                    if thumb['success']:
                        thumb_key = f"thumbnails/{Path(thumb['path']).name}"
                        self.storage.upload_file(
                            thumb['path'],
                            self.bucket,
                            thumb_key
                        )
                        thumbnail_results.append(thumb_key)
                
                steps_completed.append('generate_thumbnails')
            
            # Step 3: 최적화된 원본 생성 (WebP)
            optimized_path = Path(image_path).parent / f"{Path(image_path).stem}_optimized.webp"
            opt_result = self.optimizer.optimize_image(
                image_path,
                str(optimized_path),
                target_format='webp',
                quality=85
            )
            
            optimized_key = f"optimized/{Path(optimized_path).name}"
            self.storage.upload_file(
                str(optimized_path),
                self.bucket,
                optimized_key
            )
            
            steps_completed.append('optimize_image')
            
            # Step 4: CDN Purge
            all_paths = [f"/{original_key}", f"/{optimized_key}"] + [f"/{k}" for k in thumbnail_results]
            self.cdn.purge_cache(all_paths)
            steps_completed.append('cdn_sync')
            
            cdn_url = f"{self.cdn_domain}/{optimized_key}"
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return PipelineResult(
                success=True,
                steps_completed=steps_completed,
                file_path=image_path,
                storage_url=storage_url,
                cdn_url=cdn_url,
                optimization_stats={
                    'original_size': opt_result.original_size,
                    'optimized_size': opt_result.optimized_size,
                    'reduction_percent': opt_result.reduction_percent,
                    'thumbnails_generated': len(thumbnail_results)
                },
                total_time_sec=duration
            )
        
        except Exception as e:
            return PipelineResult(
                success=False,
                steps_completed=steps_completed,
                file_path=image_path,
                storage_url='',
                cdn_url='',
                optimization_stats={},
                total_time_sec=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )
    
    def verify_deployment(self, object_key: str) -> Dict:
        """
        배포 검증
        1. Object Storage 존재 확인
        2. CDN 응답 확인
        3. 캐시 상태 확인
        """
        results = {}
        
        # Storage 확인
        storage_meta = self.storage.get_object_metadata(self.bucket, object_key)
        results['storage_exists'] = storage_meta['success']
        
        # CDN 확인
        cdn_url = f"{self.cdn_domain}/{object_key}"
        cdn_response = self.cdn.test_cdn_response(cdn_url)
        results['cdn_accessible'] = cdn_response['success'] and cdn_response.get('status_code') == 200
        results['cdn_cache_status'] = cdn_response.get('cache_status', 'UNKNOWN')
        
        results['verification_passed'] = (
            results['storage_exists'] and 
            results['cdn_accessible']
        )
        
        return results
    
    def get_pipeline_statistics(self) -> Dict:
        """파이프라인 실행 통계"""
        return {
            'optimizer': self.optimizer.get_statistics(),
            'cache_controller': self.cache_controller.get_purge_statistics(),
            'cdn_stats': self.cdn.get_cache_statistics()
        }
