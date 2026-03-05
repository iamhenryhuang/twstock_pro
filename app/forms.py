"""
表單定義
從根目錄 forms.py 移入，導入路徑已更新為統一透過 app.extensions
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField,
    TextAreaField, FloatField, SelectField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, ValidationError, Optional
)
import email_validator  # noqa: F401 - 確保 email-validator 已安裝
from database import db, User


class LoginForm(FlaskForm):
    """登入表單"""
    username = StringField('用戶名', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('密碼', validators=[DataRequired()])
    submit = SubmitField('登入')


class RegisterForm(FlaskForm):
    """註冊表單"""
    username = StringField('用戶名', validators=[
        DataRequired(),
        Length(min=3, max=20, message='用戶名長度需在 3-20 字符之間')
    ])
    email = StringField('電子信箱', validators=[
        DataRequired(),
        Email(message='請輸入有效的電子信箱')
    ])
    full_name = StringField('真實姓名', validators=[
        Optional(),
        Length(max=50)
    ])
    phone = StringField('電話號碼', validators=[
        Optional(),
        Length(max=20)
    ])
    password = PasswordField('密碼', validators=[
        DataRequired(),
        Length(min=6, message='密碼至少需要 6 位字符')
    ])
    password2 = PasswordField('確認密碼', validators=[
        DataRequired(),
        EqualTo('password', message='密碼不匹配')
    ])
    submit = SubmitField('註冊')

    def validate_username(self, username):
        """檢查用戶名是否已存在"""
        user = db.session.query(User).filter_by(username=username.data).first()
        if user:
            raise ValidationError('此用戶名已被使用，請選擇其他用戶名')

    def validate_email(self, email):
        """檢查電子信箱是否已存在"""
        user = db.session.query(User).filter_by(email=email.data).first()
        if user:
            raise ValidationError('此電子信箱已被註冊，請使用其他信箱')


class ProfileForm(FlaskForm):
    """個人資料表單"""
    full_name = StringField('真實姓名', validators=[
        Optional(),
        Length(max=50)
    ])
    phone = StringField('電話號碼', validators=[
        Optional(),
        Length(max=20)
    ])
    email = StringField('電子信箱', validators=[
        DataRequired(),
        Email(message='請輸入有效的電子信箱')
    ])
    submit = SubmitField('更新資料')

    def __init__(self, original_email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        """檢查電子信箱是否已被其他用戶使用"""
        if email.data != self.original_email:
            user = db.session.query(User).filter_by(email=email.data).first()
            if user:
                raise ValidationError('此電子信箱已被其他用戶使用')


class ChangePasswordForm(FlaskForm):
    """修改密碼表單"""
    current_password = PasswordField('目前密碼', validators=[DataRequired()])
    new_password = PasswordField('新密碼', validators=[
        DataRequired(),
        Length(min=6, message='密碼至少需要 6 位字符')
    ])
    new_password2 = PasswordField('確認新密碼', validators=[
        DataRequired(),
        EqualTo('new_password', message='密碼不匹配')
    ])
    submit = SubmitField('修改密碼')


class WatchlistForm(FlaskForm):
    """自選股表單"""
    stock_code = StringField('股票代號', validators=[
        DataRequired(),
        Length(min=3, max=10, message='股票代號長度需在 3-10 字符之間')
    ])
    notes = TextAreaField('備註', validators=[Optional(), Length(max=500)])
    submit = SubmitField('加入自選')


class PriceAlertForm(FlaskForm):
    """價格提醒表單（付費會員功能）"""
    stock_code = StringField('股票代號', validators=[
        DataRequired(),
        Length(min=3, max=10)
    ])
    alert_type = SelectField('提醒類型', choices=[
        ('above', '高於價格'),
        ('below', '低於價格'),
        ('change_percent', '漲跌幅超過')
    ], validators=[DataRequired()])
    target_price = FloatField('目標價格', validators=[DataRequired()])
    notes = TextAreaField('備註', validators=[Optional(), Length(max=500)])
    submit = SubmitField('設定提醒')
