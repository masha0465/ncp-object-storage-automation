"""
NCP CDN+ 연동 모듈
- CDN 배포 설정
- 캐시 Purge/Warm-up
- 캐시 히트율 모니터링
"""
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime


class CDNManager:
    """NCP CDN+ 관리 클라이언트"""
    
    def __init__(self, api_endpoint: str, service_id: str, access_key: str, secret_key: str):
        """
        Args:
            api_endpoint: CDN+ API 엔드포인트
            service_id: CDN 서비스 ID
            access_key: NCP Access Key
            secret_key: NCP Secret Key
        """
        self.api_endpoint = api_endpoint
        self.service_id = service_id
        self.access_key = access_key
        self.secret_key = secret_key
        self.session = requests.Session()
    
    def purge_cache(self, paths: List[str], purge_type: str = 'path') -> Dict:
        """
        캐시 무효화 (Purge)
        
        Args:
            paths: 무효화할 경로 리스트 ['/images/photo.jpg', ...]
            purge_type: 'path' 또는 'all'
        
        Returns:
            Purge 요청 결과
        """
        # 실제 NCP CDN+ API 호출 시뮬레이션
        # 실무에서는 NCP API 문서에 따라 인증 헤더 및 요청 형식 구현
        
        purge_request = {
            'service_id': self.service_id,
            'purge_type': purge_type,
            'paths': paths,
            'timestamp': datetime.now().isoformat()
        }
        
        # Mock 응답 (실제 구현 시 API 호출)
        return {
            'success': True,
            'purge_id': f"purge_{int(time.time())}",
            'status': 'in_progress',
            'paths_count': len(paths),
            'estimated_time_sec': len(paths) * 2  # 경로당 약 2초 예상
        }
    
    def wait_for_purge(self, purge_id: str, timeout: int = 300, poll_interval: int = 5) -> Dict:
        """
        Purge 완료 대기
        
        Args:
            purge_id: Purge 요청 ID
            timeout: 최대 대기 시간 (초)
            poll_interval: 상태 확인 주기 (초)
        
        Returns:
            최종 Purge 상태
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.check_purge_status(purge_id)
            
            if status['status'] == 'completed':
                return {
                    'success': True,
                    'purge_id': purge_id,
                    'duration_sec': time.time() - start_time
                }
            elif status['status'] == 'failed':
                return {
                    'success': False,
                    'purge_id': purge_id,
                    'error': status.get('error', 'Unknown error')
                }
            
            time.sleep(poll_interval)
        
        return {
            'success': False,
            'purge_id': purge_id,
            'error': 'Timeout waiting for purge completion'
        }
    
    def check_purge_status(self, purge_id: str) -> Dict:
        """Purge 상태 확인"""
        # Mock 응답
        return {
            'purge_id': purge_id,
            'status': 'completed',  # in_progress, completed, failed
            'progress_percent': 100
        }
    
    def get_cache_statistics(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        캐시 통계 조회
        
        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
        
        Returns:
            캐시 히트율, 트래픽 등 통계
        """
        # Mock 데이터 (실제로는 CDN+ API에서 조회)
        return {
            'service_id': self.service_id,
            'period': {
                'start': start_date or '2025-10-01',
                'end': end_date or '2025-10-28'
            },
            'metrics': {
                'cache_hit_rate': 87.5,  # 캐시 히트율 (%)
                'total_requests': 1_250_000,
                'cache_hits': 1_093_750,
                'cache_misses': 156_250,
                'bandwidth_gb': 1_250.5,
                'avg_response_time_ms': 45
            }
        }
    
    def configure_origin(self, origin_url: str, settings: Dict = None) -> Dict:
        """
        원본 서버 설정 (Object Storage URL)
        
        Args:
            origin_url: Object Storage 엔드포인트 URL
            settings: 추가 설정 (캐시 TTL, 압축 등)
        
        Returns:
            설정 결과
        """
        default_settings = {
            'cache_ttl_sec': 86400,  # 24시간
            'enable_compression': True,
            'compression_types': ['text/html', 'text/css', 'application/javascript', 'image/svg+xml'],
            'enable_cors': True
        }
        
        if settings:
            default_settings.update(settings)
        
        config = {
            'service_id': self.service_id,
            'origin_url': origin_url,
            'settings': default_settings
        }
        
        # Mock 응답
        return {
            'success': True,
            'config': config,
            'message': 'CDN origin configured successfully'
        }
    
    def test_cdn_response(self, url: str) -> Dict:
        """
        CDN 응답 테스트 (캐시 헤더 검증)
        
        Args:
            url: 테스트할 CDN URL
        
        Returns:
            응답 정보 및 캐시 상태
        """
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000  # ms
            
            cache_status = response.headers.get('X-Cache', 'UNKNOWN')
            age = response.headers.get('Age', '0')
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'cache_status': cache_status,  # HIT, MISS, BYPASS
                'cache_age_sec': int(age),
                'content_type': response.headers.get('Content-Type'),
                'content_length': int(response.headers.get('Content-Length', 0)),
                'headers': {
                    'cache-control': response.headers.get('Cache-Control'),
                    'etag': response.headers.get('ETag'),
                    'last-modified': response.headers.get('Last-Modified')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def batch_purge_by_pattern(self, pattern: str) -> Dict:
        """
        패턴 기반 일괄 Purge
        
        Args:
            pattern: URL 패턴 (예: '/images/*.jpg')
        
        Returns:
            Purge 결과
        """
        # Mock 구현
        return {
            'success': True,
            'pattern': pattern,
            'estimated_paths': 150,
            'purge_id': f"batch_purge_{int(time.time())}",
            'message': f"Purging all paths matching pattern: {pattern}"
        }


class CacheController:
    """캐시 제어 유틸리티"""
    
    def __init__(self, cdn_manager: CDNManager):
        self.cdn = cdn_manager
        self.purge_history = []
    
    def smart_purge(self, updated_files: List[str]) -> Dict:
        """
        스마트 Purge: 변경된 파일만 선택적으로 무효화
        
        Args:
            updated_files: 업데이트된 파일 경로 리스트
        
        Returns:
            Purge 결과 및 통계
        """
        if not updated_files:
            return {'success': True, 'message': 'No files to purge'}
        
        # Purge 실행
        result = self.cdn.purge_cache(updated_files)
        
        # 히스토리 기록
        self.purge_history.append({
            'timestamp': datetime.now().isoformat(),
            'files_count': len(updated_files),
            'purge_id': result.get('purge_id')
        })
        
        return result
    
    def get_purge_statistics(self) -> Dict:
        """Purge 통계"""
        if not self.purge_history:
            return {'total_purges': 0}
        
        total_files = sum(h['files_count'] for h in self.purge_history)
        
        return {
            'total_purges': len(self.purge_history),
            'total_files_purged': total_files,
            'last_purge': self.purge_history[-1]['timestamp'] if self.purge_history else None
        }
