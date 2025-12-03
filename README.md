# TaiwanStock Pro

台股投資分析平台 - Bloomberg 風格的專業股票查詢與分析工具

## 專案亮點

1. **多重資料源整合與智能快取**  
   整合證交所官方API與Yahoo Finance備援系統，使用 Flask + Requests + BeautifulSoup4 實現資料爬取，搭配 JSON 快取機制達成5分鐘智能快取，確保99%資料可用性與查詢效能優化。

2. **機構級專業金融介面**  
   採用 Jinja2 模板引擎 + Bootstrap 5 + 自訂CSS 打造 Bloomberg Terminal 風格設計，使用響應式 Grid 系統支援多裝置訪問，提供機構級投資分析體驗。

3. **完整投資分析工具套件**  
   基於 Python 數值計算 + NumPy/Pandas 開發股息計算器、技術指標分析(RSI/MACD)、智能選股系統等5項專業工具，搭配 SQLAlchemy ORM + SQLite 實現用戶數據管理。

## 主要功能

- 即時股價查詢（證交所 + Yahoo Finance 雙備援）
- 技術分析工具（MA、RSI、MACD）
- 智能選股系統
- 股息計算器（支援再投入複利計算）
- 會員系統（三級權限管理）
- 自選股管理
- Bloomberg 風格專業介面

## 快速開始

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動應用
python app.py
```

訪問 http://localhost:5000

## 技術架構

**後端**
- Flask 2.3+ (Web 框架)
- SQLAlchemy 3.0+ (ORM)
- Flask-Login (認證)
- Requests + BeautifulSoup4 (資料爬取)
- NumPy + Pandas (數值計算)

**前端**
- Jinja2 模板
- Bootstrap 5
- Bloomberg 風格自訂 CSS
- Chart.js (圖表)

**資料來源**
- 證交所即時 API
- Yahoo Finance API

## API 端點

### REST API
```
GET  /api/stock/<code>              # 個股即時資料
GET  /api/stock/<code>/chart        # 圖表資料 (參數: days=1-30)
GET  /api/market                    # 大盤資料
GET  /api/popular                   # 熱門股票
POST /api/screener                  # 股票篩選
POST /api/watchlist/add             # 加入自選股 (需登入)
```

### 頁面路由
```
/                       # 首頁
/stock?code=2330       # 個股頁面
/tools/dividend        # 股息計算器
/tools/ta              # 技術分析
/tools/screener        # 智能選股
/dashboard             # 會員儀表板 (需登入)
/watchlist             # 自選股 (需登入)
```

## 專案結構

```
financial_web/
├── app.py                 # Flask 主程式
├── models.py              # 資料模型
├── forms.py               # 表單驗證
├── requirements.txt       # 依賴套件
├── database/              # 資料庫管理
├── utils/                 # 工具模組
│   ├── twse.py           # 台股 API 整合
│   ├── news.py           # 新聞爬蟲
│   └── stock_screener.py # 選股引擎
├── templates/             # HTML 模板
├── static/                # CSS/JS 靜態檔案
└── cache/                 # JSON 快取
```

## 資料庫

SQLite 資料庫包含三個表：
- `users` - 使用者與會員等級
- `watchlists` - 自選股
- `search_history` - 搜尋記錄

```bash
# 管理資料庫
python database/manage.py

# 檢視資料
python db_viewer.py
```