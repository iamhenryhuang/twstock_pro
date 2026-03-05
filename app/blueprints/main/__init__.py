"""
Blueprint: main
公開頁面路由 - 首頁、個股、搜尋、新聞
"""

import re
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user

from database import db, SearchHistory, Watchlist
from utils.twse import (
    get_stock_basic_info, get_market_summary,
    get_stock_name
)
from utils.news import get_yahoo_stock_top_news

main_bp = Blueprint('main', __name__)

# 股票名稱快速查表（中文 / 英文 → 股票代號）
_NAME_TO_CODE = {
    '台積電': '2330', '鴻海': '2317', '聯發科': '2454',
    '元大台灣50': '0050', '元大高股息': '0056',
    '富邦台50': '006208', '國泰永續高股息': '00878',
    '群益台灣精選高息': '00919',
}
_ENGLISH_TO_CODE = {
    'TSMC': '2330', 'TSMC.TW': '2330',
    'FOXCONN': '2317', 'MTK': '2454',
}

POPULAR_CODES = ['2330', '0050', '0056', '006208', '2317', '2454', '2412', '00878']


def _get_taipei_now():
    """取得台北時區當前時間"""
    return (
        datetime.now(ZoneInfo('Asia/Taipei'))
        if ZoneInfo else datetime.now()
    )


def _is_market_open(now_tpe) -> bool:
    """判斷台股是否在交易時間內（週一至週五 09:00–13:30）"""
    try:
        if now_tpe.weekday() >= 5:
            return False
        open_time = now_tpe.replace(hour=9, minute=0, second=0, microsecond=0)
        close_time = now_tpe.replace(hour=13, minute=30, second=0, microsecond=0)
        return open_time <= now_tpe <= close_time
    except Exception:
        return False


def _resolve_stock_code(raw_code: str) -> str:
    """
    將使用者輸入解析為標準股票代號。
    支援中文名稱、英文名稱、直接代號輸入三種形式。
    """
    code = re.sub(r'[^\w\u4e00-\u9fff]', '', raw_code.strip().upper())
    if re.search(r'[\u4e00-\u9fff]', code):
        return _NAME_TO_CODE.get(code, code)
    if not re.match(r'^\d+$', code):
        return _ENGLISH_TO_CODE.get(code, code)
    return code


# ── 路由 ────────────────────────────────────────────────

@main_bp.route('/')
def home():
    """首頁 - 大盤資訊與熱門股票"""
    try:
        market_info = get_market_summary()
        # 濾除「指數名稱」和無效成交量
        market_info = {
            k: v for k, v in (market_info or {}).items()
            if k != '指數名稱' and not (k == '成交量' and v in [None, '', 'N/A', '-', '0', 0])
        }
    except Exception:
        market_info = {'錯誤': '無法載入大盤資訊'}

    popular_stocks = []
    for code in POPULAR_CODES:
        try:
            info = get_stock_basic_info(code)
            if info and not info.get('錯誤'):
                popular_stocks.append({
                    'code': code,
                    'name': info.get('股票名稱', get_stock_name(code)),
                    'price': info.get('收盤價', info.get('即時股價', 'N/A')),
                    'change': info.get('漲跌價差', 'N/A'),
                    'change_percent': info.get('漲跌幅', 'N/A'),
                    'volume': info.get('成交量', 'N/A'),
                })
            else:
                popular_stocks.append({
                    'code': code, 'name': get_stock_name(code),
                    'price': 'N/A', 'change': 'N/A',
                    'change_percent': 'N/A', 'volume': 'N/A',
                })
        except Exception as e:
            print(f"獲取熱門股票 {code} 失敗: {e}")
            popular_stocks.append({
                'code': code, 'name': get_stock_name(code),
                'price': 'N/A', 'change': 'N/A',
                'change_percent': 'N/A', 'volume': 'N/A',
            })

    now = _get_taipei_now()
    return render_template(
        'home.html',
        market_info=market_info,
        popular_stocks=popular_stocks,
        market_open=_is_market_open(now),
        current_time=now,
    )


@main_bp.route('/stock')
def stock_page():
    """個股頁面"""
    raw_code = request.args.get('code', '').strip().upper()
    if not raw_code:
        return render_template('stock.html', stock_code='', stock_info=None,
                               error='請輸入股票代碼')

    stock_code = _resolve_stock_code(raw_code)

    try:
        stock_info = get_stock_basic_info(stock_code)
        if stock_info and not stock_info.get('錯誤'):
            # 記錄搜尋歷史（失敗不影響主要功能）
            try:
                history = SearchHistory(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    stock_code=stock_code,
                    stock_name=stock_info.get('股票名稱'),
                    search_price=stock_info.get('即時股價', stock_info.get('收盤價')),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:500],
                )
                db.session.add(history)
                db.session.commit()
            except Exception:
                db.session.rollback()

            in_watchlist = False
            if current_user.is_authenticated:
                in_watchlist = db.session.query(Watchlist).filter_by(
                    user_id=current_user.id,
                    stock_code=stock_code,
                ).first() is not None

            return render_template('stock.html',
                                   stock_code=stock_code,
                                   stock_info=stock_info,
                                   error=None,
                                   in_watchlist=in_watchlist,
                                   current_time=datetime.now())
        else:
            error_msg = (stock_info.get('錯誤', '無法找到股票資料')
                         if stock_info else '無法找到股票資料')
            return render_template('stock.html', stock_code=stock_code,
                                   stock_info=None, error=error_msg)

    except Exception as e:
        print(f"個股頁面錯誤: {e}")
        return render_template('stock.html', stock_code=stock_code,
                               stock_info=None, error=f'系統錯誤: {e}')


@main_bp.route('/search')
def search_redirect():
    """搜尋重導向至個股頁面"""
    q = request.args.get('q', '').strip()
    if q:
        return redirect(url_for('main.stock_page', code=q))
    return redirect(url_for('main.home'))


@main_bp.route('/news')
def news_page():
    """新聞頁面"""
    try:
        news_list = get_yahoo_stock_top_news(20)
    except Exception as e:
        print(f"獲取新聞失敗: {e}")
        news_list = []
    return render_template('news.html',
                           news_list=news_list,
                           current_time=_get_taipei_now())
