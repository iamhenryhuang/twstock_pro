# TaiwanStock Pro

A professional, high-performance financial analysis platform for the Taiwan stock market. Designed with a clean, grid-based aesthetic to provide a streamlined experience for traders and investors.

## Features

- **Real-time Market Insights**: Live market summaries with instant price updates and trend indicators.
- **Stock Lookup & Detail**: Search by code or company name to access detailed stock views with real-time quotes.
- **Advanced Watchlist**: Seamlessly track and manage your favorite stocks in a professional, high-density interface.
- **Smart History**: Keep track of your recent searches and market interactions for quick access.
- **Multi-tier Membership**: Integrated user system with scaled features for Pro and VIP members.
- **Professional Design**: Refined dark-mode interface optimized for data density and long-term use, minimizing "generic AI" aesthetic bloat.

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
│   └── news.py           # News scraper
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
- `POST /api/watchlist/add` - Add to watchlist (login required)

### Main Pages

- `/` - Market homepage with real-time summaries
- `/stock?code=2330` - Comprehensive stock detail view
- `/dashboard` - Personalized member control panel
- `/watchlist` - Focused watchlist management
- `/profile` - Secure account & settings management

## Database Structure

The system uses an optimized SQLite database with the following core entities:

- **Users**: Authentication and membership tier tracking (Free, Pro, VIP)
- **Watchlists**: Persistence for user-tracked symbols
- **Search History**: Intelligent tracking of recent market lookups

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
- Flask 2.3+ (Core Application)
- SQLAlchemy (Persistence)
- Flask-Login & Scrypt Hashing (Security)
- Requests & BeautifulSoup4 (Live Data Pipeline)

**Frontend**
- Custom CSS (Modern, Data-Dense Design)
- Google Fonts: Inter & JetBrains Mono
- Bootstrap Icons (Interface Symbols)
- Dynamic Data Visualization (Charts)

**Data Sources**
- TWSE Official Live API
- Yahoo Finance (Redundant Fallback)

## Data Caching

The app uses JSON caching to reduce API calls. Cache files are stored in the `cache/` directory with a 5-minute TTL.

## Membership Levels

- **Free**: Real-time stock lookup, personalized watchlist (up to 10 stocks)
- **Pro**: Extended watchlist (up to 100 stocks), price alerts, and enhanced data history
- **VIP**: Unlimited watchlist, native API access, and priority support

## Notes

- Market hours: Monday to Friday, 9:00 AM - 1:30 PM (Taipei time)
- Stock codes can be entered as numbers (e.g., 2330) or company names
- Some features require user registration
