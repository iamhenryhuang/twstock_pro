"""
Flask 擴展統一存取點
db 實例定義在 database.models，此處重新匯出供 Blueprint 和 forms 使用，
統一導入路徑，避免各模組直接依賴 database.models 的內部結構。
"""

from flask_login import LoginManager

# db 定義在 database.models（避免循環 import）
# 此處匯出讓其他模組可以 from app.extensions import db
from database.models import db  # noqa: F401

login_manager = LoginManager()
