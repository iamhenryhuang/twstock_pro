"""
集中式配置管理
支援 development / testing / production 環境切換
"""

import os
import secrets
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """基礎配置（所有環境共用）"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 快取設定
    CACHE_DURATION = int(os.environ.get('CACHE_DURATION', 300))  # 5 分鐘
    CACHE_DIR = os.environ.get('CACHE_DIR', 'cache')

    # 熱門股票清單
    POPULAR_STOCK_CODES = [
        '2330', '0050', '0056', '006208',
        '2317', '2454', '2412', '00878',
    ]


class DevelopmentConfig(BaseConfig):
    """開發環境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 'sqlite:///stock_app.db'
    )


class TestingConfig(BaseConfig):
    """測試環境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    """正式環境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 'sqlite:///stock_app.db'
    )


# 配置對應表
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
