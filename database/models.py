"""
資料庫模型定義
db 實例在此定義，由 app/__init__.py 的 create_app() 呼叫 db.init_app(app) 綁定
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# db 必須在此定義（不能從 app.extensions 導入，會造成循環 import）
# create_app() 會呼叫 db.init_app(app) 將此實例與 Flask app 綁定
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用戶模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # 用戶資料
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    # 會員等級 (free, premium, vip)
    membership_level = db.Column(db.String(20), default='free', nullable=False)

    # 時間戳記
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)

    # 是否啟用
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # 關聯
    watchlists = db.relationship('Watchlist', backref='user', lazy=True,
                                  cascade='all, delete-orphan')
    search_history = db.relationship('SearchHistory', backref='user', lazy=True,
                                      cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """設置密碼（hash）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """驗證密碼"""
        return check_password_hash(self.password_hash, password)

    def is_premium(self) -> bool:
        """是否為付費會員"""
        return self.membership_level in ('premium', 'vip')

    def is_vip(self) -> bool:
        """是否為 VIP 會員"""
        return self.membership_level == 'vip'

    def get_membership_features(self) -> dict:
        """取得對應會員等級的功能限制字典"""
        features: dict = {
            'basic_search': True,
            'daily_limit': 50 if self.membership_level == 'free' else None,
            'watchlist_limit': 10 if self.membership_level == 'free' else None,
            'history_days': 7 if self.membership_level == 'free' else None,
        }
        if self.is_premium():
            features.update({
                'advanced_analysis': True,
                'export_data': True,
                'price_alerts': True,
                'daily_limit': 500,
                'watchlist_limit': 100,
                'history_days': 365,
            })
        if self.is_vip():
            features.update({
                'api_access': True,
                'priority_support': True,
                'custom_indicators': True,
                'daily_limit': None,
                'watchlist_limit': None,
                'history_days': None,
            })
        return features

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class Watchlist(db.Model):
    """自選股模型"""
    __tablename__ = 'watchlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_code = db.Column(db.String(10), nullable=False)
    stock_name = db.Column(db.String(100))
    added_price = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_user_stock', 'user_id', 'stock_code'),
        db.UniqueConstraint('user_id', 'stock_code', name='unique_user_stock'),
    )

    def __repr__(self) -> str:
        return f'<Watchlist {self.user_id}:{self.stock_code}>'


class SearchHistory(db.Model):
    """搜尋歷史模型（支援匿名搜尋）"""
    __tablename__ = 'search_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    stock_code = db.Column(db.String(10), nullable=False)
    stock_name = db.Column(db.String(100))
    search_price = db.Column(db.Float)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
        db.Index('idx_stock_created', 'stock_code', 'created_at'),
    )

    def __repr__(self) -> str:
        return f'<SearchHistory {self.user_id}:{self.stock_code}>'


class PriceAlert(db.Model):
    """價格提醒模型（付費會員功能）"""
    __tablename__ = 'price_alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_code = db.Column(db.String(10), nullable=False)
    stock_name = db.Column(db.String(100))
    alert_type = db.Column(db.String(20), nullable=False)   # above | below | change_percent
    target_price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_triggered = db.Column(db.Boolean, default=False, nullable=False)
    triggered_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    user = db.relationship('User', backref='price_alerts')

    __table_args__ = (
        db.Index('idx_user_active', 'user_id', 'is_active'),
        db.Index('idx_stock_active', 'stock_code', 'is_active'),
    )

    def __repr__(self) -> str:
        return f'<PriceAlert {self.user_id}:{self.stock_code}@{self.target_price}>'