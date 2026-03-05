"""
Jinja2 模板過濾器
從 app.py 抽出，由 create_app() 統一注冊
"""


def format_number(value):
    """格式化數字顯示（加千分位）"""
    try:
        if value and value != 'N/A':
            num = float(str(value).replace(',', ''))
            return f"{num:,.0f}"
        return value
    except Exception:
        return value


def format_price(value):
    """格式化價格顯示（保留兩位小數）"""
    try:
        if value and value != 'N/A':
            num = float(str(value).replace(',', ''))
            return f"{num:.2f}"
        return value
    except Exception:
        return value


def change_class(value):
    """根據漲跌值返回對應的 Bootstrap CSS 類別"""
    try:
        if value and value != 'N/A':
            if str(value).startswith('+'):
                return 'text-success'   # 綠色（上漲）
            elif str(value).startswith('-'):
                return 'text-danger'    # 紅色（下跌）
        return 'text-muted'             # 灰色（無變化）
    except Exception:
        return 'text-muted'


# 供 create_app() 批量注冊用
ALL_FILTERS = {
    'format_number': format_number,
    'format_price': format_price,
    'change_class': change_class,
}
