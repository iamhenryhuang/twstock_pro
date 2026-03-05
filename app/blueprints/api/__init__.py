"""
Blueprint: api
REST API 端點 - /api/*
所有端點統一回傳 JSON 格式
"""

import threading
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from database import db, Watchlist
from utils.twse import (
    get_stock_basic_info, get_market_summary,
    get_stock_name, get_stock_chart_data
)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# 常用股票搜尋清單
_SEARCH_INDEX = [
    {'code': '2330', 'name': '台積電'},
    {'code': '2317', 'name': '鴻海'},
    {'code': '2454', 'name': '聯發科'},
    {'code': '2412', 'name': '中華電'},
    {'code': '2882', 'name': '國泰金'},
    {'code': '2881', 'name': '富邦金'},
    {'code': '2886', 'name': '兆豐金'},
    {'code': '2891', 'name': '中信金'},
    {'code': '0050', 'name': '元大台灣50'},
    {'code': '0056', 'name': '元大高股息'},
    {'code': '006208', 'name': '富邦台50'},
    {'code': '00878', 'name': '國泰永續高股息'},
    {'code': '00919', 'name': '群益台灣精選高息'},
    {'code': '2303', 'name': '聯電'},
    {'code': '3711', 'name': '日月光投控'},
    {'code': '2002', 'name': '中鋼'},
    {'code': '1301', 'name': '台塑'},
    {'code': '1303', 'name': '南亞'},
    {'code': '2308', 'name': '台達電'},
    {'code': '2357', 'name': '華碩'},
]

POPULAR_CODES = ['2330', '0050', '0056', '2317', '2454', '2882', '2412', '00878']


def _now_iso() -> str:
    return datetime.now().isoformat()


# ── 股票資訊 API ─────────────────────────────────────────

@api_bp.route('/stock/<stock_code>')
def api_stock(stock_code):
    """GET /api/stock/<code> - 個股基本資訊"""
    try:
        info = get_stock_basic_info(stock_code)
        if info and not info.get('錯誤'):
            return jsonify({'success': True, 'data': info, 'timestamp': _now_iso()})
        error = info.get('錯誤', '無法找到股票資料') if info else '無法找到股票資料'
        return jsonify({'success': False, 'error': error, 'timestamp': _now_iso()}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'timestamp': _now_iso()}), 500


@api_bp.route('/stock/<stock_code>/chart')
def api_stock_chart(stock_code):
    """GET /api/stock/<code>/chart?days=7 - 股票K線資料"""
    try:
        days = max(1, min(request.args.get('days', 7, type=int), 30))
        chart = get_stock_chart_data(stock_code, days)
        if chart and chart.get('success'):
            return jsonify({
                'success': True,
                'data': chart['data'],
                'period': chart['period'],
                'stock_code': stock_code,
                'timestamp': _now_iso(),
            })
        error = chart.get('error', '無法獲取圖表資料') if chart else '無法獲取圖表資料'
        return jsonify({'success': False, 'error': error, 'timestamp': _now_iso()}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'timestamp': _now_iso()}), 500


@api_bp.route('/market')
def api_market():
    """GET /api/market - 大盤指數"""
    try:
        return jsonify({'success': True, 'data': get_market_summary(), 'timestamp': _now_iso()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'timestamp': _now_iso()}), 500


@api_bp.route('/popular')
def api_popular():
    """GET /api/popular - 熱門股票清單"""
    try:
        results = []
        for code in POPULAR_CODES:
            try:
                info = get_stock_basic_info(code)
                if info and not info.get('錯誤'):
                    results.append({
                        'code': code,
                        'name': info.get('股票名稱', get_stock_name(code)),
                        'price': info.get('收盤價', 'N/A'),
                        'change': info.get('漲跌價差', 'N/A'),
                        'change_percent': info.get('漲跌幅', 'N/A'),
                    })
            except Exception:
                continue
        return jsonify({'success': True, 'data': results, 'timestamp': _now_iso()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'timestamp': _now_iso()}), 500


@api_bp.route('/search')
def api_search():
    """GET /api/search?q=<query>&limit=10 - 股票代號模糊搜尋"""
    q = request.args.get('q', '').strip()
    limit = min(request.args.get('limit', 10, type=int), 20)
    if not q:
        return jsonify({'results': []})
    try:
        q_lower = q.lower()
        results = [
            s for s in _SEARCH_INDEX
            if q_lower in s['code'].lower() or q in s['name']
        ]
        if not results:
            results = [{'code': q.upper(), 'name': get_stock_name(q.upper())}]
        return jsonify({'results': results[:limit]})
    except Exception as e:
        return jsonify({'results': [], 'error': str(e)})


# ── 自選股 API ─────────────────────────────────────────

@api_bp.route('/watchlist/add', methods=['POST'])
@login_required
def api_add_to_watchlist():
    """POST /api/watchlist/add - 加入自選股"""
    try:
        data = request.get_json() or {}
        stock_code = data.get('stock_code', '').strip().upper()

        if not stock_code:
            return jsonify({'success': False, 'message': '股票代碼不能為空'})

        existing = db.session.query(Watchlist).filter_by(
            user_id=current_user.id, stock_code=stock_code
        ).first()
        if existing:
            return jsonify({'success': False, 'message': '該股票已在自選股中'})

        stock_name = get_stock_name(stock_code)
        item = Watchlist(
            user_id=current_user.id,
            stock_code=stock_code,
            stock_name=stock_name,
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({'success': True, 'message': f'{stock_name} 已加入自選股'})

    except Exception as e:
        print(f"加入自選股 API 錯誤: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': '操作失敗，請稍後再試'})


# ── 選股 API ───────────────────────────────────────────

@api_bp.route('/screener', methods=['POST'])
def api_stock_screener():
    """POST /api/screener - 股票篩選（Windows 線程超時版）"""
    try:
        from utils.stock_screener import StockScreener

        criteria = (request.get_json() or {}).get('criteria', {})
        print(f"🔍 收到選股請求，條件: {criteria}")

        screener = StockScreener()
        results = []
        error_box = [None]

        def _run():
            try:
                results.extend(screener.screen_stocks(criteria))
            except Exception as e:
                error_box[0] = e

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=60)

        if t.is_alive():
            return jsonify({
                'success': False,
                'error': '處理時間過長，請稍後再試或調整篩選條件',
                'timestamp': _now_iso(),
            }), 408

        if error_box[0]:
            raise error_box[0]

        if not isinstance(results, list):
            results = []

        results = results[:30]
        print(f"✅ 選股完成，回傳 {len(results)} 支股票")

        return jsonify({
            'success': True,
            'results': results,
            'total_count': len(results),
            'criteria': criteria,
            'message': f'成功篩選出 {len(results)} 支股票',
            'timestamp': _now_iso(),
        })

    except ImportError:
        return jsonify({
            'success': False,
            'error': '選股模組載入失敗，請確認系統設定',
            'timestamp': _now_iso(),
        }), 500
    except Exception as e:
        print(f"選股 API 錯誤: {e}")
        return jsonify({
            'success': False,
            'error': f'選股處理失敗: {e}',
            'timestamp': _now_iso(),
        }), 500


@api_bp.route('/screener/strategies')
def api_screener_strategies():
    """GET /api/screener/strategies - 取得預設選股策略"""
    try:
        from utils.stock_screener import StockScreener
        screener = StockScreener()
        return jsonify({
            'success': True,
            'strategies': screener.get_preset_strategies(),
            'timestamp': _now_iso(),
        })
    except Exception as e:
        print(f"取得策略錯誤: {e}")
        return jsonify({'success': False, 'error': str(e), 'timestamp': _now_iso()}), 500
