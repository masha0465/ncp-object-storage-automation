"""
이미지 최적화 모듈
- 리사이징, 포맷 변환, 품질 최적화
- WebP, JPEG 압축
- 다중 해상도 썸네일 생성
"""
from PIL import Image
import io
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """최적화 결과"""
    success: bool
    original_size: int
    optimized_size: int
    reduction_percent: float
    format: str
    dimensions: Tuple[int, int]
    error: Optional[str] = None


class ImageProcessor:
    """이미지 최적화 프로세서"""
    
    SUPPORTED_FORMATS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
    
    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'total_original_size': 0,
            'total_optimized_size': 0
        }
    
    def optimize_image(
        self, 
        input_path: str, 
        output_path: str = None,
        target_format: str = 'webp',
        quality: int = 80,
        max_dimension: int = None
    ) -> OptimizationResult:
        """
        이미지 최적화
        
        Args:
            input_path: 원본 이미지 경로
            output_path: 출력 경로 (미지정 시 원본 경로에 덮어쓰기)
            target_format: 대상 포맷 (webp, jpeg, png)
            quality: 품질 (1-100)
            max_dimension: 최대 크기 (가로/세로 중 큰 쪽 기준)
        
        Returns:
            OptimizationResult
        """
        try:
            # 원본 파일 크기
            original_size = Path(input_path).stat().st_size
            
            # 이미지 로드
            with Image.open(input_path) as img:
                # EXIF 회전 정보 적용
                img = self._fix_orientation(img)
                
                original_dimensions = img.size
                
                # 리사이징
                if max_dimension:
                    img = self._resize_keep_aspect(img, max_dimension)
                
                # RGB 변환 (투명도 처리)
                if target_format.lower() in ['jpeg', 'jpg']:
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # 흰색 배경으로 변환
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                
                # 출력 경로 결정
                if not output_path:
                    output_path = str(Path(input_path).with_suffix(f'.{target_format}'))
                
                # 최적화 옵션
                save_kwargs = {
                    'quality': quality,
                    'optimize': True
                }
                
                if target_format.lower() == 'webp':
                    save_kwargs['method'] = 4  # 압축 알고리즘 강도
                elif target_format.lower() in ['jpeg', 'jpg']:
                    save_kwargs['progressive'] = True
                
                # 저장
                img.save(output_path, format=target_format.upper(), **save_kwargs)
                
                # 최적화된 파일 크기
                optimized_size = Path(output_path).stat().st_size
                
                # 통계 업데이트
                self.stats['total_processed'] += 1
                self.stats['total_original_size'] += original_size
                self.stats['total_optimized_size'] += optimized_size
                
                reduction = ((original_size - optimized_size) / original_size) * 100
                
                return OptimizationResult(
                    success=True,
                    original_size=original_size,
                    optimized_size=optimized_size,
                    reduction_percent=round(reduction, 2),
                    format=target_format,
                    dimensions=img.size
                )
        
        except Exception as e:
            return OptimizationResult(
                success=False,
                original_size=0,
                optimized_size=0,
                reduction_percent=0,
                format=target_format,
                dimensions=(0, 0),
                error=str(e)
            )
    
    def generate_thumbnails(
        self, 
        input_path: str, 
        sizes: List[Dict[str, int]],
        output_dir: str = None,
        format: str = 'webp',
        quality: int = 80
    ) -> List[Dict]:
        """
        다중 해상도 썸네일 생성
        
        Args:
            input_path: 원본 이미지 경로
            sizes: [{'name': 'large', 'width': 1920, 'height': 1080}, ...]
            output_dir: 출력 디렉토리
            format: 출력 포맷
            quality: 품질
        
        Returns:
            생성된 썸네일 정보 리스트
        """
        results = []
        
        if not output_dir:
            output_dir = Path(input_path).parent / 'thumbnails'
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        original_name = Path(input_path).stem
        
        for size_config in sizes:
            size_name = size_config['name']
            width = size_config['width']
            height = size_config['height']
            
            output_path = f"{output_dir}/{original_name}_{size_name}.{format}"
            
            try:
                with Image.open(input_path) as img:
                    # 비율 유지하며 크기 조정
                    img.thumbnail((width, height), Image.Resampling.LANCZOS)
                    
                    # RGB 변환
                    if format.lower() in ['jpeg', 'jpg'] and img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    img.save(output_path, format=format.upper(), quality=quality, optimize=True)
                    
                    results.append({
                        'name': size_name,
                        'path': output_path,
                        'dimensions': img.size,
                        'size_bytes': Path(output_path).stat().st_size,
                        'success': True
                    })
            
            except Exception as e:
                results.append({
                    'name': size_name,
                    'path': output_path,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def optimize_to_memory(
        self, 
        image_bytes: bytes, 
        target_format: str = 'webp',
        quality: int = 80
    ) -> Tuple[bytes, OptimizationResult]:
        """
        메모리에서 이미지 최적화 (파일 I/O 없음)
        
        Returns:
            (최적화된 이미지 바이트, 결과)
        """
        try:
            original_size = len(image_bytes)
            
            with Image.open(io.BytesIO(image_bytes)) as img:
                img = self._fix_orientation(img)
                
                if target_format.lower() in ['jpeg', 'jpg'] and img.mode != 'RGB':
                    img = img.convert('RGB')
                
                output_buffer = io.BytesIO()
                img.save(output_buffer, format=target_format.upper(), quality=quality, optimize=True)
                
                optimized_bytes = output_buffer.getvalue()
                optimized_size = len(optimized_bytes)
                
                reduction = ((original_size - optimized_size) / original_size) * 100
                
                result = OptimizationResult(
                    success=True,
                    original_size=original_size,
                    optimized_size=optimized_size,
                    reduction_percent=round(reduction, 2),
                    format=target_format,
                    dimensions=img.size
                )
                
                return optimized_bytes, result
        
        except Exception as e:
            return image_bytes, OptimizationResult(
                success=False,
                original_size=len(image_bytes),
                optimized_size=len(image_bytes),
                reduction_percent=0,
                format=target_format,
                dimensions=(0, 0),
                error=str(e)
            )
    
    def _resize_keep_aspect(self, img: Image.Image, max_dimension: int) -> Image.Image:
        """비율 유지하며 리사이징"""
        width, height = img.size
        
        if width > max_dimension or height > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return img
    
    def _fix_orientation(self, img: Image.Image) -> Image.Image:
        """EXIF 회전 정보 적용"""
        try:
            exif = img._getexif()
            if exif:
                orientation = exif.get(0x0112)  # Orientation 태그
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            pass
        
        return img
    
    def get_statistics(self) -> Dict:
        """최적화 통계 조회"""
        if self.stats['total_processed'] == 0:
            return self.stats
        
        total_reduction = self.stats['total_original_size'] - self.stats['total_optimized_size']
        avg_reduction = (total_reduction / self.stats['total_original_size']) * 100
        
        return {
            **self.stats,
            'total_reduction_bytes': total_reduction,
            'average_reduction_percent': round(avg_reduction, 2)
        }
