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
TRAO_DOI_LABELS = [
    "ĐANG TRAO ĐỔI",
    "HỌC VIÊN TIỀM NĂNG",
    "ĐÃ CỌC",
    "ĐÃ CHỐT - TIỀM NĂNG UPSALE",
    "ĐÃ CHỐT FULL",
]

TIEM_NANG_LABELS = [
    "HỌC VIÊN TIỀM NĂNG",
    "ĐÃ CỌC",
    "ĐÃ CHỐT - TIỀM NĂNG UPSALE",
    "ĐÃ CHỐT FULL",
]

COC_CHOT_LABELS = [
    "ĐÃ CỌC",
    "ĐÃ CHỐT - TIỀM NĂNG UPSALE",
    "ĐÃ CHỐT FULL",
]

SAI_SO_SAI_DOI_TUONG_LABELS = [
    "SAI SỐ",
    "SAI ĐỐI TƯỢNG.",
    "SAI SỐ - SAI ĐỐI TƯỢNG",
]

TIEM_NANG_CHUA_GOI_LABELS = [
    "TIỀM NĂNG CHƯA GỌI CVHT",
    "DATA MỚI CHƯA GỌI CVHT",
    "DATA CHƯA GỌI CVHT BACK LẠI",
]

# ==========================================
# CẤU HÌNH PHẦN TRĂM & TÔ MÀU KPI CHO AGGRID
# ==========================================

# Formatter hiển thị tỉ lệ phần trăm
pct_formatter = JsCode("""
function(params) {
    if (params.value === undefined || params.value === null) {
        return '';
    }
    return Number(params.value).toFixed(2) + '%';
}
""")

# Luật tô màu nền KPI dựa trên giá trị phần trăm
style_pct_saiso = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val > 7) return {'backgroundColor':'#ffcccc'};
    if (val >= 3) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ccffcc'};
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

getter_pct_tong_coc = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.rowPinned) {
        val = params.data ? (params.data['Tổng Cọc Học Thử'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else if (params.node && (params.node.group || params.node.footer) && params.node.level === 0) {
        val = params.node.aggData ? (params.node.aggData['Tổng Cọc Học Thử'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        return null;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

style_pct_tong_coc = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 10) return {'backgroundColor':'#ccffcc'};
    if (val >= 7) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ffcccc'};
}
""")

# ==========================================
# JS GETTERS & STYLES CHO BÁO CÁO 2 (% data đã chia)
# ==========================================

getter_pct_r2_half = JsCode("""
function(params) {
    var totalData = 0, dataOrder = 0;
    if (params.node && params.node.rowPinned) {
        totalData = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        dataOrder = params.data ? (params.data['Data order'] || 0) : 0;
    } else if (params.node && (params.node.group || params.node.footer) && params.node.level === 0) {
        totalData = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        dataOrder = params.node.aggData ? (params.node.aggData['Data order'] || 0) : 0;
    } else {
        return null;
    }
    var halfOrder = dataOrder * 0.5;
    return halfOrder > 0 ? (totalData / halfOrder * 100) : 0;
}
""")

getter_half_order = JsCode("""
function(params) {
    var dataOrder = 0;
    if (params.node && params.node.rowPinned) {
        dataOrder = params.data ? (params.data['Data order'] || 0) : 0;
    } else if (params.node && (params.node.group || params.node.footer) && params.node.level === 0) {
        dataOrder = params.node.aggData ? (params.node.aggData['Data order'] || 0) : 0;
    } else {
        return null;
    }
    return dataOrder * 0.5;
}
""")

getter_pct_r2_full = JsCode("""
function(params) {
    var totalData = 0, dataOrder = 0;
    if (params.node && params.node.rowPinned) {
        totalData = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        dataOrder = params.data ? (params.data['Data order'] || 0) : 0;
    } else if (params.node && (params.node.group || params.node.footer) && params.node.level === 0) {
        totalData = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        dataOrder = params.node.aggData ? (params.node.aggData['Data order'] || 0) : 0;
    } else {
        return null;
    }
    return dataOrder > 0 ? (totalData / dataOrder * 100) : 0;
}
""")

formatter_r2_dot_manual_value = JsCode("""
function(params) {
    if (params.node && (params.node.rowPinned || params.node.group || params.node.footer)) {
        if (params.value === undefined || params.value === null) return '';
        return params.value;
    }
    return '';
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
# FORMATTERS & STYLES CHO CÁC CỘT GỘP SỐ LƯỢNG & PHẦN TRĂM (TỐI ƯU HÓA)
# ==========================================

formatter_merged = JsCode("""
function(params) {
    var val = params.value || 0;
    var field = params.colDef.field;
    var baseField = (field === 'Sai Số - Sai Đối Tượng') ? 'Tổng số Data' : 'Tổng số data trừ sai số';
    var base = 0;
    if (params.node && params.node.group) {
        base = params.node.aggData ? (params.node.aggData[baseField] || 0) : 0;
    } else {
        base = params.data ? (params.data[baseField] || 0) : 0;
    }
    var pct = base ? (val / base * 100) : 0;
    return val + ' (' + pct.toFixed(2) + '%)';
}
""")

style_merged = JsCode("""
function(params) {
    var val = params.value || 0;
    var field = params.colDef.field;
    var baseField = (field === 'Sai Số - Sai Đối Tượng') ? 'Tổng số Data' : 'Tổng số data trừ sai số';
    var base = 0;
    if (params.node && params.node.group) {
        base = params.node.aggData ? (params.node.aggData[baseField] || 0) : 0;
    } else {
        base = params.data ? (params.data[baseField] || 0) : 0;
    }
    var pct = base ? (val / base * 100) : 0;
    
    if (field === 'Sai Số - Sai Đối Tượng') {
        if (pct > 7) return {'backgroundColor':'#ffcccc'};
        if (pct >= 3) return {'backgroundColor':'#fff2cc'};
        return {'backgroundColor':'#ccffcc'};
    }
    if (field === 'Tiềm Năng Chưa Gọi') {
        return pct > 0 ? {'backgroundColor':'#ffcccc'} : {'backgroundColor':'#ccffcc'};
    }
    if (field === 'Data Trao Đổi Được') {
        if (pct >= 60) return {'backgroundColor':'#ccffcc'};
        if (pct >= 50) return {'backgroundColor':'#fff2cc'};
        return {'backgroundColor':'#ffcccc'};
    }
    if (field === 'Data Tiềm Năng') {
        if (pct >= 30) return {'backgroundColor':'#ccffcc'};
        if (pct >= 25) return {'backgroundColor':'#fff2cc'};
        return {'backgroundColor':'#ffcccc'};
    }
    if (field === 'Data Cọc Chốt') {
        if (pct >= 15) return {'backgroundColor':'#ccffcc'};
        if (pct >= 12) return {'backgroundColor':'#fff2cc'};
        return {'backgroundColor':'#ffcccc'};
    }
    return {};
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
    # Cấu hình tự động xuống dòng cho header
    gb.configure_default_column(wrapHeaderText=True, autoHeaderHeight=True)

    # Cọc Khác, Tổng Cọc Học Thử — ẩn khỏi grid, nhập tay ở bảng riêng theo đợt
    gb.configure_column("Cọc Khác", hide=True, aggFunc="sum", width=100)
    gb.configure_column("Tổng Cọc Học Thử", hide=True, aggFunc="sum", width=120)

    # Thiết lập hàm tính tổng (sum) cho các cột đếm
    for c in count_cols:
        # Nếu cột đếm là cột cần gộp với phần trăm, ta sẽ định nghĩa cụ thể bên dưới
        if c not in ["Sai Số - Sai Đối Tượng", "Tiềm Năng Chưa Gọi", "Data Trao Đổi Được", "Data Tiềm Năng", "Data Cọc Chốt", "Cọc Khác", "Tổng Cọc Học Thử"]:
            gb.configure_column(c, aggFunc="sum", width=100 if len(c) < 15 else 115)

    # Cấu hình đặc biệt cho các cột số lượng gộp phần trăm
    gb.configure_column(
        "Sai Số - Sai Đối Tượng",
        headerName="% sai số-sai đối tượng/ Tổng data đã chia",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )
    gb.configure_column(
        "Tiềm Năng Chưa Gọi",
        headerName="% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )
    gb.configure_column(
        "Data Trao Đổi Được",
        headerName="% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )
    gb.configure_column(
        "Data Tiềm Năng",
        headerName="% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )
    gb.configure_column(
        "Data Cọc Chốt",
        headerName="% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )

    # Ẩn các cột phần trăm cũ trên UI của AgGrid
    gb.configure_column("% sai số-sai đối tượng/ Tổng data đã chia", hide=True)
    gb.configure_column("% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng", hide=True)
    gb.configure_column("% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng", hide=True)
    gb.configure_column("% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng", hide=True)
    gb.configure_column("% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng", hide=True)

    # Hiển thị cột % Tổng cọc buổi học thử (có tô màu KPI)
    gb.configure_column(
        "% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng",
        valueGetter=getter_pct_tong_coc,
        valueFormatter=pct_formatter,
        cellStyle=style_pct_tong_coc,
        width=160
    )


def configure_report2_grid_columns(gb, count_cols):
    """
    Cấu hình các cột cho Báo cáo 2: Nguồn, Tổng số Data, Data order (nhập tay),
    và 2 cột % tính toán động.
    """
    # Cấu hình tự động xuống dòng cho header
    gb.configure_default_column(wrapHeaderText=True, autoHeaderHeight=True)

    for c in count_cols:
        gb.configure_column(c, aggFunc="sum", width=110)

    gb.configure_column(
        "Data order",
        editable=False,
        aggFunc="sum",
        valueFormatter=formatter_r2_dot_manual_value,
        width=110
    )

    gb.configure_column(
        "50% data order",
        valueGetter=getter_half_order,
        width=130
    )

    gb.configure_column(
        "% data đã chia / 50% data order",
        valueGetter=getter_pct_r2_half,
        valueFormatter=pct_formatter,
        width=160
    )
    gb.configure_column(
        "% data đã chia / data order",
        valueGetter=getter_pct_r2_full,
        cellStyle=style_pct_r2_full,
        valueFormatter=pct_formatter,
        width=160
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
