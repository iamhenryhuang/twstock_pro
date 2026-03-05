"""
應用程式進入點
取代原 app.py 底部的 if __name__ == '__main__' 區塊
"""

import os
from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # 確保資料庫表格存在
    with app.app_context():
        from app.extensions import db
        try:
            db.create_all()
            print("✅ 資料庫已初始化")
        except Exception as e:
            print(f"❌ 資料庫初始化錯誤: {e}")

    print("🚀 台股財經網站啟動中...")
    print("📊 支援即時股價查詢")
    print("👤 會員系統已整合")
    print("🌐 網址: http://127.0.0.1:5000")

    app.run(debug=True, host='127.0.0.1', port=5000)
