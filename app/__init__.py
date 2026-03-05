"""
Application Factory
使用 create_app() 工廠函數建立 Flask 應用程式實例，
支援環境切換（development / testing / production）
"""

import os
from flask import Flask

from app.config import config_map
from app.filters import ALL_FILTERS
from app.errors import register_error_handlers


def create_app(config_name: str | None = None) -> Flask:
    """
    建立並配置 Flask 應用程式。

    :param config_name: 配置環境名稱，預設讀取 FLASK_ENV 環境變數，
                        無則使用 'development'。
    :return: 已配置完成的 Flask app 實例
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(
        __name__,
        # 指向根目錄下的 templates / static
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
    )

    # ── 載入配置 ──────────────────────────────────────────
    cfg = config_map.get(config_name, config_map['default'])
    app.config.from_object(cfg)

    # ── 初始化擴展 ────────────────────────────────────────
    # db 定義於 database.models，在此綁定 app
    from database import db
    db.init_app(app)

    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '請先登入以訪問此頁面'
    login_manager.login_message_category = 'info'

    # ── 注冊 user_loader ──────────────────────────────────
    from database import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── 注冊 Blueprint ────────────────────────────────────
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.member import member_bp
    from app.blueprints.api import api_bp
    from app.blueprints.tools import tools_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(api_bp)       # url_prefix='/api' 已在 Blueprint 定義
    app.register_blueprint(tools_bp)     # url_prefix='/tools' 已在 Blueprint 定義

    # ── 注冊模板過濾器 ────────────────────────────────────
    for name, func in ALL_FILTERS.items():
        app.jinja_env.filters[name] = func

    # ── 注冊錯誤處理器 ────────────────────────────────────
    register_error_handlers(app)

    # ── 確保快取目錄存在 ──────────────────────────────────
    os.makedirs(app.config.get('CACHE_DIR', 'cache'), exist_ok=True)

    return app
