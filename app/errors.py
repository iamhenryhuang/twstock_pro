"""
全域 HTTP 錯誤處理器
由 create_app() 透過 register_error_handlers() 注冊至 app
"""

from flask import render_template


def not_found(error):
    """404 - 頁面不存在"""
    return render_template(
        'error.html',
        error_code=404,
        error_message='頁面不存在'
    ), 404


def internal_error(error):
    """500 - 伺服器內部錯誤"""
    return render_template(
        'error.html',
        error_code=500,
        error_message='伺服器內部錯誤'
    ), 500


def register_error_handlers(app):
    """向 Flask app 注冊所有錯誤處理器"""
    app.register_error_handler(404, not_found)
    app.register_error_handler(500, internal_error)
