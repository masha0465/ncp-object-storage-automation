"""
pytest 설정 및 공통 fixture
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .env 파일 로드 (pytest 실행 시 자동)
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"\n✓ .env 파일 로드됨: {env_path}")
    print(f"  NCP_ACCESS_KEY: {os.getenv('NCP_ACCESS_KEY', 'Not found')[:20]}...")
else:
    print(f"\n⚠️ .env 파일 없음: {env_path}")