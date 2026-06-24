"""
error_tracking.py — Module theo dõi dữ liệu lỗi (Tab 3)
Chứa các hàm:
- Gọi API với filter account_source [106, 232] + khoảng ngày
- Lọc record có relation_name không rỗng
- Render UI cho Tab 3
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from config import get_api_key, get_url_base, get_headers
from api_client import fetch_accounts_with_progress
from data_processing import convert_date_to_timestamp
from supabase_client import save_report_result


# ==========================================
# CẤU HÌNH
# ==========================================

# Nguồn khách hàng cố định cho tab lỗi
ERROR_SOURCE_IDS = [106, 232]

# Các trường cần lấy từ API
ERROR_FIELDS = (
    "id,created_at,account_code,account_name,"
    "account_manager,relation_id,mgr_display_name,relation_name,"
    "account_source,account_source_details,account_type"
)


# ==========================================
# XỬ LÝ DỮ LIỆU LỖI
# ==========================================

def build_error_filtering(date_range):
    """
    Xây dựng bộ lọc cho API: account_source = [106, 232] + khoảng ngày.

    Args:
        date_range: Tuple/list (start_date, end_date)

    Returns:
        dict: Filtering conditions
    """
    filtering = {
        "account_source:in": ERROR_SOURCE_IDS,
    }

    if len(date_range) == 2:
        start_ts = convert_date_to_timestamp(date_range[0], is_end_of_day=False)
        end_ts = convert_date_to_timestamp(date_range[1], is_end_of_day=True)
        filtering["created_at:gte"] = str(start_ts)
        filtering["created_at:lte"] = str(end_ts)

    return filtering


def process_error_records(records):
    """
    Lọc và biến đổi records: chỉ giữ lại record có relation_name KHÔNG rỗng/null.

    Args:
        records: List[dict] — dữ liệu thô từ API

    Returns:
        pd.DataFrame — DataFrame đã lọc, sẵn sàng hiển thị
    """
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Đổi tên cột cho dễ đọc
    rename_map = {
        "id": "ID",
        "account_code": "Mã KH",
        "account_name": "Tên KH",
        "relation_name": "Mối quan hệ",
        "mgr_display_name": "Người phụ trách",
        "account_source": "Nguồn KH",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    # Lọc: chỉ giữ record có "Mối quan hệ" KHÔNG rỗng/null
    if "Mối quan hệ" in df.columns:
        df = df[df["Mối quan hệ"].notna() & (df["Mối quan hệ"].astype(str).str.strip() != "")]
    else:
        # Không có cột relation_name → không có dữ liệu lỗi
        return pd.DataFrame()

    if df.empty:
        return df

    # Xử lý cột created_at thành ngày tháng dễ đọc
    if "created_at" in df.columns:
        from data_processing import VN_TZ
        df["Ngày tạo"] = pd.to_numeric(df["created_at"], errors="coerce")
        df["Ngày tạo"] = df["Ngày tạo"].apply(
            lambda x: datetime.fromtimestamp(x, tz=VN_TZ).strftime("%d/%m/%Y %H:%M") if pd.notna(x) and x > 0 else ""
        )

    # Chọn cột hiển thị
    display_cols = ["ID", "Mã KH", "Tên KH", "Mối quan hệ", "Người phụ trách", "Ngày tạo"]
    available_cols = [c for c in display_cols if c in df.columns]

    return df[available_cols].reset_index(drop=True)


# ==========================================
# RENDER UI — TAB 3
# ==========================================

def render_error_tracking_tab():
    """Render giao diện Tab 3: Theo dõi Dữ liệu Lỗi."""

    st.subheader("🔴 Theo dõi Dữ liệu Lỗi")
    st.info(
        "Tab này query API với nguồn khách hàng **[106, 232]** trong khoảng ngày đã chọn. "
        "Chỉ hiển thị các record có trường **Mối quan hệ** (relation_name) có giá trị."
    )

    # --- Bộ lọc ngày ---
    today = datetime.today().date()
    first_day = today.replace(day=1)

    col1, col2 = st.columns([2, 1])
    with col1:
        error_date_range = st.date_input(
            "Khoảng ngày tạo (Created_at)",
            [first_day, today],
            key="error_date_range"
        )

    # --- Session state cho Tab 3 ---
    if "error_df" not in st.session_state:
        st.session_state["error_df"] = None
    if "error_raw_records" not in st.session_state:
        st.session_state["error_raw_records"] = None
    if "error_is_loading" not in st.session_state:
        st.session_state["error_is_loading"] = False

    # --- Nút tải dữ liệu ---
    is_loading = st.session_state.get("error_is_loading", False)

    if is_loading:
        st.warning("⏳ Đang tải dữ liệu lỗi... Vui lòng đợi.")

    fetch_clicked = st.button(
        "🚀 Tải dữ liệu lỗi",
        disabled=is_loading,
        key="btn_fetch_error"
    )

    if fetch_clicked and not is_loading:
        api_key = get_api_key()
        if not api_key:
            st.error("Chưa cấu hình GETFLY_API_KEY trong file .env")
            return

        st.session_state["error_is_loading"] = True

        try:
            url_base = get_url_base()
            headers = get_headers(api_key)
            filtering = build_error_filtering(error_date_range)

            all_records, err = fetch_accounts_with_progress(headers, url_base, filtering)

            if err:
                st.error(err)
                st.session_state["error_is_loading"] = False
                return

            if not all_records:
                st.warning("Không tìm thấy dữ liệu nào phù hợp với bộ lọc.")
                st.session_state["error_is_loading"] = False
                return

            # Xử lý và lọc dữ liệu
            df_error = process_error_records(all_records)
            st.session_state["error_df"] = df_error
            st.session_state["error_raw_records"] = all_records

            if df_error.empty:
                st.info("Tất cả record đều không có giá trị 'Mối quan hệ'. Không có dữ liệu lỗi.")
            else:
                st.success(
                    f"Đã tải {len(all_records)} bản ghi từ API. "
                    f"**{len(df_error)}** bản ghi có Mối quan hệ (dữ liệu lỗi)."
                )

        except Exception as e:
            st.error(f"❌ Lỗi không mong muốn: {e}")

        st.session_state["error_is_loading"] = False

    # --- Hiển thị bảng dữ liệu lỗi ---
    df_error = st.session_state.get("error_df")

    if df_error is not None and not df_error.empty:
        st.markdown(f"**📊 Tổng số bản ghi lỗi: {len(df_error)}**")
        st.dataframe(df_error, use_container_width=True, height=450)

        # --- Nút lưu vào Supabase ---
        col_save, col_spacer = st.columns([1, 3])
        with col_save:
            if st.button("💾 Lưu dữ liệu lỗi vào Database", key="btn_save_error"):
                with st.spinner("Đang lưu vào Supabase..."):
                    success, msg = save_report_result(
                        report_type="error_tracking",
                        df_report=df_error,
                        filters_used={"account_source": ERROR_SOURCE_IDS}
                    )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    elif df_error is not None and df_error.empty:
        st.info("Không có dữ liệu lỗi để hiển thị.")
