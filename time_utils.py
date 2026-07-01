"""
time_utils.py - Tien ich thoi gian dung chung.
"""

from datetime import datetime, timezone, timedelta


VN_TZ = timezone(timedelta(hours=7))


def get_vn_now():
    """Tra ve thoi diem hien tai theo mui gio Viet Nam (UTC+7)."""
    return datetime.now(VN_TZ)


def format_fetch_time():
    """Dinh dang thoi gian xuat data dung cho cac bao cao."""
    return get_vn_now().strftime("%Hh%M ngày %d/%m")
