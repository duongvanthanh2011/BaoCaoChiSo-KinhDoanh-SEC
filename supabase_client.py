"""
supabase_client.py — Module kết nối và thao tác Supabase
Chứa các hàm:
- Khởi tạo Supabase client
- Lưu raw records từ API
- Lưu kết quả báo cáo (Report 1, Report 2)
- Truy vấn lịch sử báo cáo
"""

import streamlit as st
import json
import uuid
from datetime import datetime

from config import get_supabase_url, get_supabase_key


# ==========================================
# KHỞI TẠO CLIENT
# ==========================================

def get_supabase_client():
    """
    Khởi tạo và trả về Supabase client.
    Trả về None nếu chưa cấu hình URL/key.
    """
    url = get_supabase_url()
    key = get_supabase_key()

    if not url or not key:
        return None

    try:
        from supabase import create_client
        client = create_client(url, key)
        return client
    except Exception as e:
        st.warning(f"⚠️ Không thể kết nối Supabase: {e}")
        return None


# ==========================================
# LƯU RAW RECORDS
# ==========================================

def save_raw_records(records, filters_used=None):
    """
    Lưu danh sách raw records từ API vào table raw_records trên Supabase.

    Args:
        records: List[dict] — dữ liệu thô từ API
        filters_used: dict — bộ lọc đã dùng khi fetch (tùy chọn)

    Returns:
        (success: bool, message: str)
    """
    client = get_supabase_client()
    if client is None:
        return False, "Chưa cấu hình Supabase. Vui lòng thêm SUPABASE_URL và SUPABASE_KEY vào file .env"

    if not records:
        return False, "Không có dữ liệu để lưu."

    try:
        fetch_id = str(uuid.uuid4())
        filters_json = json.dumps(filters_used, ensure_ascii=False) if filters_used else None

        # Chia batch để tránh payload quá lớn (mỗi batch 500 records)
        batch_size = 500
        total_saved = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            rows = []
            for rec in batch:
                rows.append({
                    "fetch_id": fetch_id,
                    "record_data": rec,
                    "account_id": rec.get("id"),
                    "account_code": rec.get("account_code"),
                    "created_at_api": rec.get("created_at"),
                    "filters_used": filters_json,
                })
            client.table("raw_records").insert(rows).execute()
            total_saved += len(rows)

        return True, f"✅ Đã lưu {total_saved} bản ghi vào Supabase (fetch_id: {fetch_id[:8]}...)"

    except Exception as e:
        return False, f"❌ Lỗi khi lưu raw records: {e}"


# ==========================================
# LƯU KẾT QUẢ BÁO CÁO
# ==========================================

def save_report_result(report_type, df_report, filters_used=None):
    """
    Lưu kết quả báo cáo (DataFrame) vào table report_history trên Supabase.

    Args:
        report_type: str — 'report_1', 'report_2', hoặc 'error_tracking'
        df_report: pd.DataFrame — kết quả báo cáo
        filters_used: dict — bộ lọc đã dùng (tùy chọn)

    Returns:
        (success: bool, message: str)
    """
    client = get_supabase_client()
    if client is None:
        return False, "Chưa cấu hình Supabase. Vui lòng thêm SUPABASE_URL và SUPABASE_KEY vào file .env"

    if df_report is None or df_report.empty:
        return False, "Không có dữ liệu báo cáo để lưu."

    try:
        # Chuyển DataFrame sang JSON (orient='records' cho dễ đọc)
        report_data = json.loads(df_report.to_json(orient='records', force_ascii=False, date_format='iso'))

        row = {
            "report_type": report_type,
            "report_data": report_data,
            "filters_used": json.dumps(filters_used, ensure_ascii=False) if filters_used else None,
            "row_count": len(df_report),
        }

        client.table("report_history").insert(row).execute()

        label_map = {
            "report_1": "Báo cáo 1",
            "report_2": "Báo cáo 2",
            "error_tracking": "Dữ liệu lỗi",
        }
        label = label_map.get(report_type, report_type)
        return True, f"✅ Đã lưu {label} ({len(df_report)} dòng) vào Supabase."

    except Exception as e:
        return False, f"❌ Lỗi khi lưu báo cáo: {e}"


# ==========================================
# TRUY VẤN LỊCH SỬ BÁO CÁO
# ==========================================

def get_report_history(report_type=None, limit=10):
    """
    Truy vấn lịch sử báo cáo đã lưu trên Supabase.

    Args:
        report_type: str — lọc theo loại báo cáo (tùy chọn)
        limit: int — số lượng bản ghi trả về (mặc định 10)

    Returns:
        List[dict] hoặc None nếu lỗi
    """
    client = get_supabase_client()
    if client is None:
        return None

    try:
        query = client.table("report_history").select("*").order("created_at", desc=True).limit(limit)

        if report_type:
            query = query.eq("report_type", report_type)

        response = query.execute()
        return response.data

    except Exception as e:
        st.warning(f"⚠️ Không thể truy vấn lịch sử: {e}")
        return None
