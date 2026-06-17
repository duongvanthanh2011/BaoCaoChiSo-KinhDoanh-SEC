"""
report_utils.py — Tiện ích và cấu hình dùng chung cho báo cáo
Chứa:
- Nhãn phân loại mối quan hệ
- Các đối tượng định dạng JS (valueFormatter, cellStyle, valueGetter) cho AgGrid
- Các hàm cấu hình cột và đồng bộ trạng thái chỉnh sửa dùng chung
"""

import streamlit as st
import pandas as pd
from st_aggrid.shared import JsCode

# ==========================================
# NHÃN PHÂN LOẠI MỐI QUAN HỆ
# ==========================================
TRAO_DOI_LABELS = ["ĐANG TRAO ĐỔI", "HỌC VIÊN TIỀM NĂNG", "ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]
TIEM_NANG_LABELS = ["HỌC VIÊN TIỀM NĂNG", "ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]
COC_CHOT_LABELS = ["ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]

# ==========================================
# CẤU HÌNH PHẦN TRĂM & TÔ MÀU KPI CHO AGGRID
# ==========================================

# Formatter hiển thị tỉ lệ phần trăm
pct_formatter = JsCode("""
function(params) {
    if (params.value === undefined || params.value === null) {
        return '0.00%';
    }
    return Number(params.value).toFixed(2) + '%';
}
""")

# Luật tô màu nền KPI dựa trên giá trị phần trăm
style_pct_saiso = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    return val > 5 ? {'backgroundColor':'#ffcccc'} : {'backgroundColor':'#ccffcc'};
}
""")

style_pct_tn_chua_goi = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    return val > 0 ? {'backgroundColor':'#ffcccc'} : {'backgroundColor':'#ccffcc'};
}
""")

style_pct_traodoi = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 60) return {'backgroundColor':'#ccffcc'};
    if (val >= 50) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ffcccc'};
}
""")

style_pct_tiemnang = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 30) return {'backgroundColor':'#ccffcc'};
    if (val >= 25) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ffcccc'};
}
""")

style_pct_coc = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 15) return {'backgroundColor':'#ccffcc'};
    if (val >= 12) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ffcccc'};
}
""")


# JS Getters dùng để tính toán tỉ lệ động ở cả dòng con và dòng tổng nhóm (group / total footers)
getter_pct_saiso = JsCode("""
function(params) {
    var val = 0, total = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
    }
    return total ? (val / total * 100) : 0;
}
""")

getter_pct_tn_chua_goi = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Tiềm Năng Chưa Gọi'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Tiềm Năng Chưa Gọi'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

getter_pct_traodoi = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Data Trao Đổi Được'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Data Trao Đổi Được'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

getter_pct_tiemnang = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Data Tiềm Năng'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Data Tiềm Năng'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

getter_pct_coc = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Data Cọc Chốt'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Data Cọc Chốt'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

# ==========================================
# JS GETTERS & STYLES CHO BÁO CÁO 2 (% data đã chia)
# ==========================================

getter_pct_r2_half = JsCode("""
function(params) {
    var totalData = 0, dataOrder = 0;
    if (params.node && params.node.group) {
        totalData = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        dataOrder = params.node.aggData ? (params.node.aggData['Data order'] || 0) : 0;
    } else {
        totalData = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        dataOrder = params.data ? (params.data['Data order'] || 0) : 0;
    }
    var halfOrder = dataOrder * 0.5;
    return halfOrder > 0 ? (totalData / halfOrder * 100) : 0;
}
""")

getter_pct_r2_full = JsCode("""
function(params) {
    var totalData = 0, dataOrder = 0;
    if (params.node && params.node.group) {
        totalData = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        dataOrder = params.node.aggData ? (params.node.aggData['Data order'] || 0) : 0;
    } else {
        totalData = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        dataOrder = params.data ? (params.data['Data order'] || 0) : 0;
    }
    return dataOrder > 0 ? (totalData / dataOrder * 100) : 0;
}
""")

style_pct_r2_full = JsCode("""
function(params) {
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 95 && val <= 105) return {'backgroundColor':'#ccffcc'};
    return {'backgroundColor':'#fff2cc'};
}
""")


# ==========================================
# HÀM TIỆN ÍCH DÙNG CHUNG CHO BẢNG AGGRID
# ==========================================

def configure_standard_grid_columns(gb, count_cols):
    """
    Cấu hình các cột số lượng và cột tỷ lệ KPI chuẩn cho GridOptionsBuilder.
    Tái sử dụng cho cả Báo cáo 1 và Báo cáo 2 để loại bỏ lặp mã nguồn.
    """
    # Cọc Khác, Tổng Cọc Học Thử có thể nhập tay
    gb.configure_column("Cọc Khác", editable=True, width=120)
    gb.configure_column("Tổng Cọc Học Thử", editable=True, width=170)

    # Thiết lập hàm tính tổng (sum) cho các cột đếm
    for c in count_cols:
        gb.configure_column(c, aggFunc="sum", width=130 if len(c) < 15 else 160)

    # Cấu hình các cột phần trăm tính toán động bằng valueGetter và tô màu theo cellStyle
    gb.configure_column(
        "% Sai Số",
        valueGetter=getter_pct_saiso,
        cellStyle=style_pct_saiso,
        valueFormatter=pct_formatter,
        width=180
    )
    gb.configure_column(
        "% Data Tiềm Năng Chưa Gọi",
        valueGetter=getter_pct_tn_chua_goi,
        cellStyle=style_pct_tn_chua_goi,
        valueFormatter=pct_formatter,
        width=210
    )
    gb.configure_column(
        "% Data Trao Đổi Được",
        valueGetter=getter_pct_traodoi,
        cellStyle=style_pct_traodoi,
        valueFormatter=pct_formatter,
        width=190
    )
    gb.configure_column(
        "% Data Tiềm Năng",
        valueGetter=getter_pct_tiemnang,
        cellStyle=style_pct_tiemnang,
        valueFormatter=pct_formatter,
        width=170
    )
    gb.configure_column(
        "% Data Cọc-Chốt",
        valueGetter=getter_pct_coc,
        cellStyle=style_pct_coc,
        valueFormatter=pct_formatter,
        width=160
    )


def configure_report2_grid_columns(gb, count_cols):
    """
    Cấu hình các cột cho Báo cáo 2: Nguồn, Tổng số Data, Data order (nhập tay),
    và 2 cột % tính toán động.
    """
    for c in count_cols:
        gb.configure_column(c, aggFunc="sum", width=150)

    gb.configure_column("Data order", editable=True, aggFunc="sum", width=140)

    gb.configure_column(
        "% data đã chia / 50% data order",
        valueGetter=getter_pct_r2_half,
        valueFormatter=pct_formatter,
        width=240
    )
    gb.configure_column(
        "% data đã chia / data order",
        valueGetter=getter_pct_r2_full,
        cellStyle=style_pct_r2_full,
        valueFormatter=pct_formatter,
        width=240
    )


def update_manual_inputs_in_state(grid_response, state_key, keys, editable_cols=None):
    """
    Đồng bộ dữ liệu nhập tay từ phản hồi AgGrid vào session state.
    editable_cols: danh sách cột nhập tay cần sync (mặc định: Cọc Khác, Tổng Cọc Học Thử).
    """
    if editable_cols is None:
        editable_cols = ['Cọc Khác', 'Tổng Cọc Học Thử']

    if grid_response is not None and 'data' in grid_response:
        updated_df = pd.DataFrame(grid_response['data'])
        if not updated_df.empty:
            present_cols = [c for c in editable_cols if c in updated_df.columns]
            if present_cols:
                updated_clean = updated_df.dropna(subset=keys)
                updated_clean = updated_clean.groupby(keys, as_index=False)[present_cols].first()

                df_state = st.session_state[state_key]
                orig_cols = list(df_state.columns)

                df_state_idx = df_state.set_index(keys)
                updated_idx = updated_clean.set_index(keys)

                df_state_idx.update(updated_idx[present_cols])

                df_updated = df_state_idx.reset_index()
                st.session_state[state_key] = df_updated[orig_cols]
