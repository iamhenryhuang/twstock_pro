"""
快取工具模組
從 utils/twse.py 抽出，提供通用的文件型快取機制
"""

import os
import json
from datetime import datetime, timedelta

CACHE_DIR = os.environ.get('CACHE_DIR', 'cache')
CACHE_DURATION = int(os.environ.get('CACHE_DURATION', 300))  # 預設 5 分鐘

os.makedirs(CACHE_DIR, exist_ok=True)


def get_cache(key: str):
    """
    讀取快取資料。
    若快取不存在或已過期則回傳 None。
    """
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        if datetime.now() - cache_time < timedelta(seconds=CACHE_DURATION):
            return cache_data['data']
    except Exception as e:
        print(f"❌ 讀取快取失敗 [{key}]: {e}")
    return None


def save_cache(key: str, data) -> None:
    """
    儲存資料至快取。
    快取格式：{'timestamp': ISO格式時間, 'data': 實際資料}
    """
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ 儲存快取失敗 [{key}]: {e}")


def clear_cache(key: str) -> bool:
    """清除指定快取"""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        if os.path.exists(cache_file):
            os.remove(cache_file)
            return True
    except Exception as e:
        print(f"❌ 清除快取失敗 [{key}]: {e}")
    return False
