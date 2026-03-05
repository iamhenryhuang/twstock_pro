"""
Blueprint: tools
投資工具路由 - 股息計算器、資產配置、技術分析、定期定額、AI預測、選股
"""

from flask import Blueprint, render_template, request

tools_bp = Blueprint('tools', __name__, url_prefix='/tools')


@tools_bp.route('/dividend', methods=['GET', 'POST'])
def dividend_calculator():
    """股息計算器"""
    result = None
    defaults = {
        'price': '',
        'annual_dividend': '',
        'shares': '1000',
        'growth_rate': '0',
        'years': '1',
        'reinvest': 'on',
        'payout_frequency': '4',   # 季配
    }

    if request.method == 'POST':
        def _float(val, default=0.0):
            try:
                return float(str(val).replace(',', '').strip())
            except Exception:
                return default

        def _int(val, default=0):
            try:
                return int(str(val).strip())
            except Exception:
                return default

        price = _float(request.form.get('price'))
        annual_dividend = _float(request.form.get('annual_dividend'))
        shares = _int(request.form.get('shares'), 0)
        growth_rate = _float(request.form.get('growth_rate')) / 100.0
        years = max(1, _int(request.form.get('years'), 1))
        reinvest = request.form.get('reinvest') == 'on'
        payout_frequency = _int(request.form.get('payout_frequency'), 1)
        if payout_frequency not in [1, 2, 4, 12]:
            payout_frequency = 1

        defaults.update({
            'price': request.form.get('price', ''),
            'annual_dividend': request.form.get('annual_dividend', ''),
            'shares': request.form.get('shares', ''),
            'growth_rate': request.form.get('growth_rate', ''),
            'years': request.form.get('years', ''),
            'reinvest': 'on' if reinvest else '',
            'payout_frequency': str(payout_frequency),
        })

        if price > 0 and annual_dividend >= 0 and shares >= 0:
            div_yield = (annual_dividend / price) * 100 if price > 0 else 0

            current_shares = shares
            current_annual_div = annual_dividend
            total_dividends = 0.0
            yearly = []

            for year in range(1, years + 1):
                year_cash = 0.0
                year_added = 0
                period_div = (current_annual_div / payout_frequency
                              if payout_frequency > 0 else current_annual_div)

                for _ in range(payout_frequency):
                    cash = current_shares * period_div
                    year_cash += cash
                    if reinvest and price > 0:
                        added = int(cash // price)
                        if added > 0:
                            current_shares += added
                            year_added += added

                total_dividends += year_cash
                yearly.append({
                    'year': year,
                    'dividend_per_share': round(current_annual_div, 4),
                    'cash_dividend': round(year_cash, 2),
                    'added_shares': year_added,
                    'ending_shares': current_shares,
                })
                current_annual_div *= (1 + growth_rate)

            result = {
                'yield_percent': round(div_yield, 2),
                'total_dividends': round(total_dividends, 2),
                'final_shares': current_shares,
                'years': years,
                'yearly': yearly,
                'payout_frequency': payout_frequency,
            }

    return render_template('tools/dividend_calculator.html',
                           defaults=defaults, result=result)


@tools_bp.route('/allocation')
def allocation_tool():
    """資產配置工具"""
    return render_template('tools/allocation.html')


@tools_bp.route('/ta')
def technical_analysis_tool():
    """技術分析工具"""
    return render_template('tools/ta.html')


@tools_bp.route('/dca')
def dca_tool():
    """定期定額試算器"""
    return render_template('tools/dca.html')


@tools_bp.route('/ai')
def ai_price_prediction_tool():
    """AI 股價預測（趨勢外推版）"""
    return render_template('tools/ai.html')


@tools_bp.route('/screener')
def stock_screener_tool():
    """股票選股工具"""
    return render_template('tools/screener.html')
