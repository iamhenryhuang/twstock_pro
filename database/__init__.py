"""
Database 模組
包含模型定義和資料庫管理工具
"""

from .models import db, User, Watchlist, SearchHistory, PriceAlert

__version__ = "2.0.0"

__all__ = [
    'db',
    'User',
    'Watchlist',
    'SearchHistory',
    'PriceAlert',
]