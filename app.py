from flask import Flask, render_template, request, jsonify, url_for, redirect, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, AnonymousUserMixin
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None
from utils.twse import get_stock_basic_info, get_market_summary, get_stock_name, get_stock_chart_data
from utils.news import get_yahoo_stock_top_news


from database import db, User, Watchlist, SearchHistory, PriceAlert
from forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm, WatchlistForm, PriceAlertForm
import os
import secrets

# 載入環境變數
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# 全域配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///stock_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化擴展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '請先登入以訪問此頁面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def home():
    """首頁 - 股票搜尋和大盤資訊"""
    try:
        # 獲取大盤摘要
        market_info = get_market_summary()
        # 過濾不顯示項目：指數名稱、無效成交量
        try:
            filtered_market_info = {}
            for k, v in (market_info or {}).items():
                if k == '指數名稱':
                    continue
                if k == '成交量' and (v in [None, '', 'N/A', '-', '0', 0]):
                    continue
                filtered_market_info[k] = v
            market_info = filtered_market_info
        except Exception:
            pass
        
        # 熱門股票列表 - 使用真實API數據
        popular_codes = ['2330', '0050', '0056', '006208', '2317', '2454', '2412', '00878']
        popular_stocks = []
        
        for code in popular_codes:
            try:
                stock_info = get_stock_basic_info(code)
                if stock_info and not stock_info.get('錯誤'):
                    popular_stocks.append({
                        'code': code,
                        'name': stock_info.get('股票名稱', get_stock_name(code)),
                        'price': stock_info.get('收盤價', stock_info.get('即時股價', 'N/A')),
                        'change': stock_info.get('漲跌價差', 'N/A'),
                        'change_percent': stock_info.get('漲跌幅', 'N/A'),
                        'volume': stock_info.get('成交量', 'N/A')
                    })
                else:
                    # 如果API失敗，使用基本信息
                    popular_stocks.append({
                        'code': code,
                        'name': get_stock_name(code),
                        'price': 'N/A',
                        'change': 'N/A',
                        'change_percent': 'N/A',
                        'volume': 'N/A'
                    })
            except Exception as stock_error:
                print(f"獲取股票 {code} 資料失敗: {stock_error}")
                # 添加基本信息作為備用
                popular_stocks.append({
                    'code': code,
                    'name': get_stock_name(code),
                    'price': 'N/A',
                    'change': 'N/A',
                    'change_percent': 'N/A',
                    'volume': 'N/A'
                })
        # 市場新聞（Yahoo 熱門前3則）
        market_news = []
        try:
            market_news = get_yahoo_stock_top_news(3)
        except Exception as _:
            market_news = []

        # 台北時區時間與市場開盤狀態（週一至週五 09:00-13:30）
        now_tpe = datetime.now(ZoneInfo('Asia/Taipei')) if ZoneInfo else datetime.now()
        try:
            is_weekday = now_tpe.weekday() < 5
            open_time = now_tpe.replace(hour=9, minute=0, second=0, microsecond=0)
            close_time = now_tpe.replace(hour=13, minute=30, second=0, microsecond=0)
            market_open = is_weekday and open_time <= now_tpe <= close_time
        except Exception:
            market_open = False

        return render_template('home.html', 
                             market_info=market_info,
                             popular_stocks=popular_stocks,
                             market_news=market_news,
                             market_open=market_open,
                             current_time=now_tpe)
        
    except Exception as e:
        print(f"首頁錯誤: {e}")
        return render_template('home.html', 
                             market_info={'錯誤': '無法載入大盤資訊'},
                             popular_stocks=[],
                             market_news=[],
                             market_open=False,
                             current_time=datetime.now(ZoneInfo('Asia/Taipei')) if ZoneInfo else datetime.now())


@app.route('/stock')
def stock_page():
    """個股頁面"""
    stock_code = request.args.get('code', '').strip().upper()
    if not stock_code:
        return render_template('stock.html', 
                             stock_code='',
                             stock_info=None,
                             error='請輸入股票代碼')

    # 若輸入為公司名稱，嘗試找出股票代碼
    # 僅當輸入不是純數字或英數字時才嘗試名稱查找
    import re
    
    # 清理輸入，移除空格和特殊字符
    stock_code = re.sub(r'[^\w\u4e00-\u9fff]', '', stock_code)
    
    # 檢查是否為中文名稱，如果是則進行轉換
    if re.search(r'[\u4e00-\u9fff]', stock_code):
        # 反查常見股票名稱
        name_to_code = {
            '台積電': '2330',
            '鴻海': '2317',
            '聯發科': '2454',
            '元大台灣50': '0050',
            '元大高股息': '0056',
            '富邦台50': '006208',
            '國泰永續高股息': '00878',
            '群益台灣精選高息': '00919',
        }
        if stock_code in name_to_code:
            stock_code = name_to_code[stock_code]
            print(f"✅ 中文名稱轉換: {stock_code}")
    
    # 檢查是否為英文名稱，如果是則進行轉換
    elif not re.match(r'^[0-9]+$', stock_code):
        # 英文名稱對應
        english_to_code = {
            'TSMC': '2330',
            'TSMC.TW': '2330',
            'FOXCONN': '2317',
            'MTK': '2454',
        }
        if stock_code in english_to_code:
            stock_code = english_to_code[stock_code]
            print(f"✅ 英文名稱轉換: {stock_code}")

    try:
        # 獲取股票資訊
        stock_info = get_stock_basic_info(stock_code)
        if stock_info and not stock_info.get('錯誤'):
            # 記錄搜尋歷史
            try:
                search_history = SearchHistory(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    stock_code=stock_code,
                    stock_name=stock_info.get('股票名稱'),
                    search_price=stock_info.get('即時股價', stock_info.get('收盤價')),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:500]
                )
                db.session.add(search_history)
                db.session.commit()
            except:
                # 記錄失敗不影響主要功能
                pass
            
            # 檢查是否在自選股中
            in_watchlist = False
            if current_user.is_authenticated:
                in_watchlist = db.session.query(Watchlist).filter_by(
                    user_id=current_user.id, 
                    stock_code=stock_code
                ).first() is not None
            
            return render_template('stock.html',
                                 stock_code=stock_code,
                                 stock_info=stock_info,
                                 error=None,
                                 in_watchlist=in_watchlist,
                                 current_time=datetime.now())
        else:
            error_msg = stock_info.get('錯誤', '無法找到股票資料') if stock_info else '無法找到股票資料'
            return render_template('stock.html',
                                 stock_code=stock_code,
                                 stock_info=None,
                                 error=error_msg)
            
    except Exception as e:
        print(f"股票頁面錯誤: {e}")
        return render_template('stock.html',
                             stock_code=stock_code,
                             stock_info=None,
                             error=f'系統錯誤: {str(e)}')


@app.route('/search')
def search_redirect():
    """搜尋重導向"""
    stock_code = request.args.get('q', '').strip()
    if stock_code:
        return redirect(url_for('stock_page', code=stock_code))
    return redirect(url_for('home'))


@app.route('/tools/dividend', methods=['GET', 'POST'])
def dividend_calculator():
    """股息計算器"""
    result = None
    # 表單預設值
    defaults = {
        'price': '',
        'annual_dividend': '',
        'shares': '1000',
        'growth_rate': '0',
        'years': '1',
        'reinvest': 'on',
        'payout_frequency': '4'  # 年配=1、半年配=2、季配=4、月配=12（預設季配）
    }

    if request.method == 'POST':
        def to_float(value, default=0.0):
            try:
                return float(str(value).replace(',', '').strip())
            except Exception:
                return default

        def to_int(value, default=0):
            try:
                return int(str(value).strip())
            except Exception:
                return default

        price = to_float(request.form.get('price'))
        annual_dividend = to_float(request.form.get('annual_dividend'))
        shares = to_int(request.form.get('shares'), 0)
        growth_rate = to_float(request.form.get('growth_rate')) / 100.0  # 轉為倍數（年成長）
        years = max(1, to_int(request.form.get('years'), 1))
        reinvest = request.form.get('reinvest') == 'on'
        payout_frequency = to_int(request.form.get('payout_frequency'), 1)
        if payout_frequency not in [1, 2, 4, 12]:
            payout_frequency = 1

        # 更新預設值回填
        defaults.update({
            'price': request.form.get('price', ''),
            'annual_dividend': request.form.get('annual_dividend', ''),
            'shares': request.form.get('shares', ''),
            'growth_rate': request.form.get('growth_rate', ''),
            'years': request.form.get('years', ''),
            'reinvest': 'on' if reinvest else '',
            'payout_frequency': str(payout_frequency)
        })

        if price > 0 and annual_dividend >= 0 and shares >= 0:
            # 當年殖利率（以年化股利 / 價格）
            div_yield = (annual_dividend / price) * 100 if price > 0 else 0

            # 年度模擬（支援配息頻率，年/半年/季/月）
            current_shares = shares
            current_annual_dividend = annual_dividend
            total_dividends = 0.0
            yearly = []

            for year in range(1, years + 1):
                year_cash = 0.0
                year_added = 0
                period_div_per_share = current_annual_dividend / payout_frequency if payout_frequency > 0 else current_annual_dividend

                for _ in range(payout_frequency):
                    cash = current_shares * period_div_per_share
                    year_cash += cash
                    if reinvest and price > 0:
                        added = int(cash // price)
                        if added > 0:
                            current_shares += added
                            year_added += added

                total_dividends += year_cash

                yearly.append({
                    'year': year,
                    'dividend_per_share': round(current_annual_dividend, 4),
                    'cash_dividend': round(year_cash, 2),
                    'added_shares': year_added,
                    'ending_shares': current_shares
                })

                # 年度成長率（年化）
                current_annual_dividend = current_annual_dividend * (1 + growth_rate)

            result = {
                'yield_percent': round(div_yield, 2),
                'total_dividends': round(total_dividends, 2),
                'final_shares': current_shares,
                'years': years,
                'yearly': yearly,
                'payout_frequency': payout_frequency,
            }

    return render_template('tools/dividend_calculator.html', defaults=defaults, result=result)


@app.route('/tools/allocation')
def allocation_tool():
    """資產配置工具"""
    return render_template('tools/allocation.html')


@app.route('/tools/ta')
def technical_analysis_tool():
    """技術分析工具"""
    return render_template('tools/ta.html')


@app.route('/tools/dca')
def dca_tool():
    """定期定額試算器"""
    return render_template('tools/dca.html')


@app.route('/tools/ai')
def ai_price_prediction_tool():
    """AI 股價預測（趨勢外推版）"""
    return render_template('tools/ai.html')


@app.route('/tools/screener')
def stock_screener_tool():
    """股票選股工具"""
    return render_template('tools/screener.html')

@app.route('/news')
def news_page():
    """新聞頁面"""
    try:
        news_list = get_yahoo_stock_top_news(20)
    except Exception as e:
        print(f"獲取新聞失敗: {e}")
        news_list = []
    now = datetime.now(ZoneInfo('Asia/Taipei')) if ZoneInfo else datetime.now()
    return render_template('news.html', news_list=news_list, current_time=now)


# === 會員系統路由 ===

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登入頁面"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'歡迎回來，{user.username}！', 'success')
            
            # 重導向到原本要訪問的頁面
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('用戶名或密碼錯誤', 'danger')
    
    return render_template('auth/login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """註冊頁面"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('註冊成功！請登入您的帳戶', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """登出"""
    username = current_user.username
    logout_user()
    flash(f'{username}，您已成功登出', 'info')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    """會員控制台"""
    # 獲取用戶自選股
    watchlist = db.session.query(Watchlist).filter_by(user_id=current_user.id).order_by(Watchlist.created_at.desc()).all()
    
    # 獲取最近搜尋記錄
    recent_searches = db.session.query(SearchHistory).filter_by(user_id=current_user.id).order_by(SearchHistory.created_at.desc()).limit(10).all()
    
    # 獲取會員功能
    features = current_user.get_membership_features()
    
    return render_template('member/dashboard.html', 
                         watchlist=watchlist,
                         recent_searches=recent_searches,
                         features=features,
                         current_time=datetime.now())


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """個人資料"""
    form = ProfileForm(current_user.email)
    
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.email = form.email.data
        db.session.commit()
        flash('個人資料已更新', 'success')
        return redirect(url_for('profile'))
    
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone
        form.email.data = current_user.email
    
    return render_template('member/profile.html', form=form)


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密碼"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('密碼已成功修改', 'success')
            return redirect(url_for('profile'))
        else:
            flash('目前密碼不正確', 'danger')
    
    return render_template('member/change_password.html', form=form)


@app.route('/watchlist')
@login_required
def watchlist():
    """自選股列表"""
    watchlist_items = db.session.query(Watchlist).filter_by(user_id=current_user.id).order_by(Watchlist.created_at.desc()).all()
    
    # 獲取即時股價
    for item in watchlist_items:
        try:
            stock_info = get_stock_basic_info(item.stock_code)
            if stock_info and not stock_info.get('錯誤'):
                item.current_price = stock_info.get('即時股價', stock_info.get('收盤價'))
                item.change = stock_info.get('漲跌價差')
                item.change_percent = stock_info.get('漲跌幅')
        except:
            item.current_price = 'N/A'
            item.change = 'N/A'
            item.change_percent = 'N/A'
    
    features = current_user.get_membership_features()
    return render_template('member/watchlist.html', 
                         watchlist=watchlist_items,
                         features=features,
                         current_time=datetime.now())


@app.route('/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    """加入自選股"""
    stock_code = request.form.get('stock_code', '').strip().upper()
    notes = request.form.get('notes', '').strip()
    
    if not stock_code:
        flash('請輸入股票代號', 'warning')
        return redirect(url_for('watchlist'))
    
    # 檢查會員限制
    features = current_user.get_membership_features()
    if features.get('watchlist_limit'):
        current_count = db.session.query(Watchlist).filter_by(user_id=current_user.id).count()
        if current_count >= features['watchlist_limit']:
            flash(f'您的會員等級最多只能添加 {features["watchlist_limit"]} 支自選股', 'warning')
            return redirect(url_for('watchlist'))
    
    # 檢查是否已存在
    existing = db.session.query(Watchlist).filter_by(user_id=current_user.id, stock_code=stock_code).first()
    if existing:
        flash('此股票已在您的自選股中', 'info')
        return redirect(url_for('watchlist'))
    
    # 獲取股票資訊
    stock_info = get_stock_basic_info(stock_code)
    if not stock_info or stock_info.get('錯誤'):
        flash('無法找到此股票代號', 'danger')
        return redirect(url_for('watchlist'))
    
    # 加入自選股
    watchlist_item = Watchlist(
        user_id=current_user.id,
        stock_code=stock_code,
        stock_name=stock_info.get('股票名稱'),
        added_price=stock_info.get('即時股價', stock_info.get('收盤價')),
        notes=notes
    )
    
    db.session.add(watchlist_item)
    db.session.commit()
    
    flash(f'已將 {stock_code} {stock_info.get("股票名稱", "")} 加入自選股', 'success')
    return redirect(url_for('watchlist'))


@app.route('/watchlist/remove/<int:item_id>')
@login_required
def remove_from_watchlist(item_id):
    """移除自選股"""
    item = db.session.query(Watchlist).filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        stock_name = f"{item.stock_code} {item.stock_name or ''}"
        db.session.delete(item)
        db.session.commit()
        flash(f'已移除自選股：{stock_name}', 'success')
    else:
        flash('找不到此自選股項目', 'warning')
    
    return redirect(url_for('watchlist'))


@app.route('/watchlist/remove/code/<stock_code>')
@login_required
def remove_from_watchlist_by_code(stock_code):
    """透過股票代號移除自選股"""
    item = db.session.query(Watchlist).filter_by(user_id=current_user.id, stock_code=stock_code.upper()).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash(f'已移除自選股：{stock_code}', 'success')
    else:
        flash('找不到此自選股項目', 'warning')
    return redirect(url_for('watchlist'))


# === API 端點 ===

@app.route('/api/stock/<stock_code>')
def api_stock(stock_code):
    """API: 獲取個股資訊"""
    try:
        stock_info = get_stock_basic_info(stock_code)
        
        if stock_info and not stock_info.get('錯誤'):
            return jsonify({
                'success': True,
                'data': stock_info,
                'timestamp': datetime.now().isoformat()
            })
        else:
            error_msg = stock_info.get('錯誤', '無法找到股票資料') if stock_info else '無法找到股票資料'
            return jsonify({
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/stock/<stock_code>/chart')
def api_stock_chart(stock_code):
    """API: 獲取股票圖表資料"""
    try:
        days = request.args.get('days', 7, type=int)
        # 限制天數範圍
        days = max(1, min(days, 30))
        
        chart_data = get_stock_chart_data(stock_code, days)
        
        if chart_data and chart_data.get('success'):
            return jsonify({
                'success': True,
                'data': chart_data['data'],
                'period': chart_data['period'],
                'stock_code': stock_code,
                'timestamp': datetime.now().isoformat()
            })
        else:
            error_msg = chart_data.get('error', '無法獲取圖表資料') if chart_data else '無法獲取圖表資料'
            return jsonify({
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/market')
def api_market():
    """API: 獲取大盤資訊"""
    try:
        market_info = get_market_summary()
        
        return jsonify({
            'success': True,
            'data': market_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/popular')
def api_popular():
    """API: 獲取熱門股票清單"""
    try:
        popular_codes = ['2330', '0050', '0056', '2317', '2454', '2882', '2412', '00878']
        popular_stocks = []
        
        for code in popular_codes:
            try:
                stock_info = get_stock_basic_info(code)
                if stock_info and not stock_info.get('錯誤'):
                    popular_stocks.append({
                        'code': code,
                        'name': stock_info.get('股票名稱', get_stock_name(code)),
                        'price': stock_info.get('收盤價', 'N/A'),
                        'change': stock_info.get('漲跌價差', 'N/A'),
                        'change_percent': stock_info.get('漲跌幅', 'N/A')
                    })
            except:
                # 如果個別股票失敗，跳過
                continue
        
        return jsonify({
            'success': True,
            'data': popular_stocks,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/search')
def api_search():
    """API: 搜尋股票代號與名稱"""
    q = request.args.get('q', '').strip()
    limit = min(request.args.get('limit', 10, type=int), 20)
    if not q:
        return jsonify({'results': []})
    try:
        # 常用股票名單作即時搜尋
        all_stocks = [
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
        q_lower = q.lower()
        results = [s for s in all_stocks if q_lower in s['code'].lower() or q in s['name']]
        if not results:
            # fallback: try direct code lookup
            results = [{'code': q.upper(), 'name': get_stock_name(q.upper())}]
        return jsonify({'results': results[:limit]})
    except Exception as e:
        return jsonify({'results': [], 'error': str(e)})


@app.route('/api/watchlist/add', methods=['POST'])
@login_required
def api_add_to_watchlist():
    """API: 加入自選股"""
    try:
        data = request.get_json()
        stock_code = data.get('stock_code', '').strip().upper()
        
        if not stock_code:
            return jsonify({
                'success': False,
                'message': '股票代碼不能為空'
            })
        
        # 檢查是否已存在
        existing = db.session.query(Watchlist).filter_by(
            user_id=current_user.id,
            stock_code=stock_code
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': '該股票已在自選股中'
            })
        
        # 獲取股票名稱
        from utils.twse import get_stock_name
        stock_name = get_stock_name(stock_code)
        
        # 添加到自選股
        watchlist_item = Watchlist(
            user_id=current_user.id,
            stock_code=stock_code,
            stock_name=stock_name
        )
        db.session.add(watchlist_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{stock_name} 已加入自選股'
        })
        
    except Exception as e:
        print(f"加入自選股錯誤: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '操作失敗，請稍後再試'
        })


@app.route('/api/screener', methods=['POST'])
def api_stock_screener():
    """API: 股票選股 - Windows 兼容版"""
    try:
        from utils.stock_screener import StockScreener
        import threading
        import time
        
        data = request.get_json() or {}
        criteria = data.get('criteria', {})
        
        print(f"🔍 收到選股請求，條件: {criteria}")
        
        # 創建選股器實例
        screener = StockScreener()
        
        # 使用線程實現超時控制（Windows 兼容）
        results = []
        exception_occurred = None
        
        def run_screening():
            try:
                nonlocal results
                results = screener.screen_stocks(criteria)
            except Exception as e:
                nonlocal exception_occurred
                exception_occurred = e
        
        # 啟動篩選線程
        screening_thread = threading.Thread(target=run_screening)
        screening_thread.daemon = True
        screening_thread.start()
        
        # 等待結果或超時（60秒）
        screening_thread.join(timeout=60)
        
        if screening_thread.is_alive():
            print("⏰ 選股處理超時")
            return jsonify({
                'success': False,
                'error': '處理時間過長，請稍後再試或調整篩選條件',
                'timestamp': datetime.now().isoformat()
            }), 408
        
        if exception_occurred:
            raise exception_occurred
        
        # 確保結果是有效的
        if not isinstance(results, list):
            results = []
        
        # 限制回傳結果數量（避免回應過大）
        max_results = 30
        if len(results) > max_results:
            results = results[:max_results]
        
        print(f"✅ 選股完成，回傳 {len(results)} 支股票")
        
        return jsonify({
            'success': True,
            'results': results,
            'total_count': len(results),
            'criteria': criteria,
            'message': f'成功篩選出 {len(results)} 支股票',
            'timestamp': datetime.now().isoformat()
        })
        
    except ImportError as e:
        print(f"選股模組載入錯誤: {e}")
        return jsonify({
            'success': False,
            'error': '選股模組載入失敗，請確認系統設定',
            'timestamp': datetime.now().isoformat()
        }), 500
        
    except Exception as e:
        print(f"選股API錯誤: {e}")
        return jsonify({
            'success': False,
            'error': f'選股處理失敗: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/screener/strategies')
def api_screener_strategies():
    """API: 獲取預設選股策略"""
    try:
        from utils.stock_screener import StockScreener
        
        screener = StockScreener()
        strategies = screener.get_preset_strategies()
        
        return jsonify({
            'success': True,
            'strategies': strategies,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"獲取策略錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500



# === 錯誤處理 ===

@app.errorhandler(404)
def not_found(error):
    """404 錯誤頁面"""
    return render_template('error.html', 
                         error_code=404,
                         error_message='頁面不存在'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 錯誤頁面"""
    return render_template('error.html',
                         error_code=500,
                         error_message='伺服器內部錯誤'), 500


# === 模板過濾器 ===

@app.template_filter('format_number')
def format_number(value):
    """格式化數字顯示"""
    try:
        if value and value != 'N/A':
            # 移除逗號並轉換為浮點數
            num = float(str(value).replace(',', ''))
            return f"{num:,.0f}"
        return value
    except:
        return value


@app.template_filter('format_price')
def format_price(value):
    """格式化價格顯示"""
    try:
        if value and value != 'N/A':
            num = float(str(value).replace(',', ''))
            return f"{num:.2f}"
        return value
    except:
        return value


@app.template_filter('change_class')
def change_class(value):
    """根據漲跌返回 CSS 類別"""
    try:
        if value and value != 'N/A':
            if value.startswith('+'):
                return 'text-success'  # 綠色 (上漲)
            elif value.startswith('-'):
                return 'text-danger'   # 紅色 (下跌)
        return 'text-muted'  # 灰色 (無變化)
    except:
        return 'text-muted'


if __name__ == '__main__':
    # 確保資料夾存在
    os.makedirs('static', exist_ok=True)
    
    print("🚀 台股財經網站啟動中...")
    print("📊 支援即時股價查詢")
    print("👤 會員系統已整合")
    print("🌐 網址: http://127.0.0.1:5000")
    
    # 確保資料庫表存在
    with app.app_context():
        try:
            db.create_all()
            print("✅ 資料庫已初始化")
        except Exception as e:
            print(f"❌ 資料庫初始化錯誤: {e}")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
    
