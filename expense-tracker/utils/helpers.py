"""
Utility functions for the Expense Tracker application
"""

from datetime import datetime, date, timedelta
from typing import Optional, Union
import calendar


def format_currency(amount: float, symbol: str = '₹') -> str:
    """Format amount as currency string."""
    if amount >= 0:
        return f"{symbol}{amount:,.2f}"
    else:
        return f"-{symbol}{abs(amount):,.2f}"


def format_currency_compact(amount: float, symbol: str = '₹') -> str:
    """Format large amounts in compact form (K, L, Cr)."""
    if amount >= 10000000:  # 1 Crore
        return f"{symbol}{amount/10000000:.1f}Cr"
    elif amount >= 100000:  # 1 Lakh
        return f"{symbol}{amount/100000:.1f}L"
    elif amount >= 1000:
        return f"{symbol}{amount/1000:.1f}K"
    else:
        return f"{symbol}{amount:.0f}"


def parse_date(date_str: str) -> Optional[date]:
    """Parse date string to date object."""
    formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None


def get_date_range(period: str) -> tuple:
    """
    Get start and end dates for common periods.
    
    Args:
        period: 'today', 'this_week', 'this_month', 'last_month', 
                'this_year', 'last_30_days', 'last_90_days'
    
    Returns:
        Tuple of (start_date, end_date)
    """
    today = date.today()
    
    if period == 'today':
        return today, today
    
    elif period == 'this_week':
        start = today - timedelta(days=today.weekday())
        return start, today
    
    elif period == 'this_month':
        start = today.replace(day=1)
        return start, today
    
    elif period == 'last_month':
        last_month_end = today.replace(day=1) - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return last_month_start, last_month_end
    
    elif period == 'this_year':
        start = today.replace(month=1, day=1)
        return start, today
    
    elif period == 'last_30_days':
        start = today - timedelta(days=30)
        return start, today
    
    elif period == 'last_90_days':
        start = today - timedelta(days=90)
        return start, today
    
    elif period == 'all_time':
        return None, None
    
    else:
        return today.replace(day=1), today


def get_month_name(month: int) -> str:
    """Get month name from month number."""
    return calendar.month_name[month]


def get_month_abbr(month: int) -> str:
    """Get abbreviated month name."""
    return calendar.month_abbr[month]


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 0 if new_value == 0 else 100
    return ((new_value - old_value) / old_value) * 100


def validate_amount(amount_str: str) -> Optional[float]:
    """Validate and parse amount string."""
    try:
        # Remove currency symbols and whitespace
        cleaned = amount_str.strip().replace('₹', '').replace('$', '').replace(',', '')
        amount = float(cleaned)
        return amount if amount > 0 else None
    except (ValueError, AttributeError):
        return None


def get_greeting() -> str:
    """Get time-appropriate greeting."""
    hour = datetime.now().hour
    
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"


def days_remaining_in_month() -> int:
    """Calculate days remaining in current month."""
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return last_day - today.day


def get_ordinal_suffix(day: int) -> str:
    """Get ordinal suffix for a day number."""
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f"{day}{suffix}"


def format_date_friendly(d: Union[date, str]) -> str:
    """Format date in a friendly, readable format."""
    if isinstance(d, str):
        d = parse_date(d)
    
    if d is None:
        return "Unknown"
    
    today = date.today()
    
    if d == today:
        return "Today"
    elif d == today - timedelta(days=1):
        return "Yesterday"
    elif d > today - timedelta(days=7):
        return d.strftime("%A")  # Day name
    elif d.year == today.year:
        return d.strftime("%b %d")  # Month Day
    else:
        return d.strftime("%b %d, %Y")  # Month Day, Year


def generate_color_palette(n: int) -> list:
    """Generate a pleasing color palette for charts."""
    base_colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8B500', '#82E0AA', '#F1948A', '#85929E', '#76D7C4'
    ]
    
    if n <= len(base_colors):
        return base_colors[:n]
    
    # If more colors needed, repeat with variations
    extended = base_colors.copy()
    while len(extended) < n:
        extended.extend(base_colors)
    
    return extended[:n]


def truncate_text(text: str, max_length: int = 30) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
