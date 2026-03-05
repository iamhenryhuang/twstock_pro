"""
Blueprint: member
會員功能路由 - 控制台、個人資料、密碼修改、自選股管理
"""

from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from database import db, Watchlist, SearchHistory
from app.forms import ProfileForm, ChangePasswordForm
from utils.twse import get_stock_basic_info, get_stock_name

member_bp = Blueprint('member', __name__)


# ── 儀表板 ───────────────────────────────────────────────

@member_bp.route('/dashboard')
@login_required
def dashboard():
    """會員控制台"""
    watchlist = (
        db.session.query(Watchlist)
        .filter_by(user_id=current_user.id)
        .order_by(Watchlist.created_at.desc())
        .all()
    )
    recent_searches = (
        db.session.query(SearchHistory)
        .filter_by(user_id=current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(10)
        .all()
    )
    features = current_user.get_membership_features()

    return render_template(
        'member/dashboard.html',
        watchlist=watchlist,
        recent_searches=recent_searches,
        features=features,
        current_time=datetime.now(),
    )


# ── 個人資料 ─────────────────────────────────────────────

@member_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """個人資料頁面"""
    form = ProfileForm(current_user.email)

    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.email = form.email.data
        db.session.commit()
        flash('個人資料已更新', 'success')
        return redirect(url_for('member.profile'))

    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone
        form.email.data = current_user.email

    return render_template('member/profile.html', form=form)


@member_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密碼"""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('密碼已成功修改', 'success')
            return redirect(url_for('member.profile'))
        else:
            flash('目前密碼不正確', 'danger')

    return render_template('member/change_password.html', form=form)


# ── 自選股 ───────────────────────────────────────────────

@member_bp.route('/watchlist')
@login_required
def watchlist():
    """自選股列表（含即時股價）"""
    items = (
        db.session.query(Watchlist)
        .filter_by(user_id=current_user.id)
        .order_by(Watchlist.created_at.desc())
        .all()
    )

    for item in items:
        try:
            info = get_stock_basic_info(item.stock_code)
            if info and not info.get('錯誤'):
                item.current_price = info.get('即時股價', info.get('收盤價'))
                item.change = info.get('漲跌價差')
                item.change_percent = info.get('漲跌幅')
            else:
                item.current_price = item.change = item.change_percent = 'N/A'
        except Exception:
            item.current_price = item.change = item.change_percent = 'N/A'

    features = current_user.get_membership_features()
    return render_template(
        'member/watchlist.html',
        watchlist=items,
        features=features,
        current_time=datetime.now(),
    )


@member_bp.route('/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    """加入自選股"""
    stock_code = request.form.get('stock_code', '').strip().upper()
    notes = request.form.get('notes', '').strip()

    if not stock_code:
        flash('請輸入股票代號', 'warning')
        return redirect(url_for('member.watchlist'))

    # 會員數量限制
    features = current_user.get_membership_features()
    limit = features.get('watchlist_limit')
    if limit:
        current_count = db.session.query(Watchlist).filter_by(
            user_id=current_user.id
        ).count()
        if current_count >= limit:
            flash(f'您的會員等級最多只能添加 {limit} 支自選股', 'warning')
            return redirect(url_for('member.watchlist'))

    # 重複檢查
    existing = db.session.query(Watchlist).filter_by(
        user_id=current_user.id, stock_code=stock_code
    ).first()
    if existing:
        flash('此股票已在您的自選股中', 'info')
        return redirect(url_for('member.watchlist'))

    # 驗證股票代號
    stock_info = get_stock_basic_info(stock_code)
    if not stock_info or stock_info.get('錯誤'):
        flash('無法找到此股票代號', 'danger')
        return redirect(url_for('member.watchlist'))

    item = Watchlist(
        user_id=current_user.id,
        stock_code=stock_code,
        stock_name=stock_info.get('股票名稱'),
        added_price=stock_info.get('即時股價', stock_info.get('收盤價')),
        notes=notes,
    )
    db.session.add(item)
    db.session.commit()

    flash(f'已將 {stock_code} {stock_info.get("股票名稱", "")} 加入自選股', 'success')
    return redirect(url_for('member.watchlist'))


@member_bp.route('/watchlist/remove/<int:item_id>')
@login_required
def remove_from_watchlist(item_id):
    """移除自選股（透過 ID）"""
    item = db.session.query(Watchlist).filter_by(
        id=item_id, user_id=current_user.id
    ).first()
    if item:
        label = f"{item.stock_code} {item.stock_name or ''}".strip()
        db.session.delete(item)
        db.session.commit()
        flash(f'已移除自選股：{label}', 'success')
    else:
        flash('找不到此自選股項目', 'warning')
    return redirect(url_for('member.watchlist'))


@member_bp.route('/watchlist/remove/code/<stock_code>')
@login_required
def remove_from_watchlist_by_code(stock_code):
    """移除自選股（透過股票代號）"""
    item = db.session.query(Watchlist).filter_by(
        user_id=current_user.id, stock_code=stock_code.upper()
    ).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash(f'已移除自選股：{stock_code}', 'success')
    else:
        flash('找不到此自選股項目', 'warning')
    return redirect(url_for('member.watchlist'))
