# TaiwanStock Pro

A stock analysis platform for Taiwan stock market. Real-time quotes, technical analysis tools, and portfolio management.

## Features

- **Stock Lookup**: Search stocks by code or company name, view real-time prices and charts
- **Technical Analysis**: MA, RSI, MACD indicators with interactive charts
- **Stock Screener**: Filter stocks by price, volume, market cap, and other criteria
- **Dividend Calculator**: Calculate dividend yields with reinvestment options
- **Watchlist**: Save stocks to track (requires account)
- **User Accounts**: Three-tier membership system (free, premium, VIP)

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Project Structure

```
twstock_pro/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── forms.py               # Form validation
├── database/              # Database management
│   ├── models.py         # Database models
│   └── manage.py         # Database utilities
├── utils/                 # Utility modules
│   ├── twse.py           # TWSE API integration
│   ├── news.py           # News scraper
│   └── stock_screener.py # Stock screening engine
├── templates/             # HTML templates
├── static/                # CSS and static files
└── cache/                 # JSON cache files
```

## API Endpoints

### REST API

- `GET /api/stock/<code>` - Get stock information
- `GET /api/stock/<code>/chart?days=7` - Get chart data (1-30 days)
- `GET /api/market` - Get market summary
- `GET /api/popular` - Get popular stocks
- `POST /api/screener` - Screen stocks by criteria
- `POST /api/watchlist/add` - Add to watchlist (login required)

### Pages

- `/` - Homepage with market summary
- `/stock?code=2330` - Stock detail page
- `/tools/dividend` - Dividend calculator
- `/tools/ta` - Technical analysis
- `/tools/screener` - Stock screener
- `/dashboard` - User dashboard (login required)
- `/watchlist` - Watchlist management (login required)

## Database

SQLite database with three main tables:

- `users` - User accounts and membership levels
- `watchlists` - User watchlists
- `search_history` - Search history tracking

Manage the database:

```bash
python database/manage.py
```

View database contents:

```bash
python db_viewer.py
```

## Tech Stack

**Backend**
- Flask 2.3+
- SQLAlchemy 3.0+
- Flask-Login
- Requests + BeautifulSoup4

**Frontend**
- Jinja2 templates
- Bootstrap 5
- Custom CSS (Bloomberg-inspired)
- Chart.js

**Data Sources**
- TWSE official API
- Yahoo Finance API (fallback)

## Data Caching

The app uses JSON caching to reduce API calls. Cache files are stored in the `cache/` directory with a 5-minute TTL.

## Membership Levels

- **Free**: Basic stock lookup, limited watchlist (5 stocks)
- **Premium**: Extended watchlist (20 stocks), advanced tools
- **VIP**: Unlimited watchlist, all features

## Notes

- Market hours: Monday to Friday, 9:00 AM - 1:30 PM (Taipei time)
- Stock codes can be entered as numbers (e.g., 2330) or company names
- Some features require user registration
