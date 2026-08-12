"""
reports.py — Module hiển thị báo cáo
Chứa các hàm:
- render_report_1: Hiển thị Báo cáo 1
- render_report_2: Hiển thị Báo cáo 2

Re-export các hàm từ report_calculations để tương thích ngược với app.py:
- add_indicator_columns
- compute_report_1
- compute_report_2
"""

import streamlit as st
import pandas as pd
import io
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

# Import các phần từ các module con
from report_utils import configure_standard_grid_columns, configure_report2_grid_columns
from report_components import render_dot_manual_inputs, render_dot_nguon_manual_inputs
from report_calculations import (
    add_indicator_columns, 
    compute_report_1, 
    compute_report_2,
    compute_report_3,
    prepare_excel_report_1,
    prepare_excel_report_2,
    aggregate_report_2_rows
)

# Re-export để app.py import trực tiếp không bị lỗi
__all__ = [
    'add_indicator_columns',
    'compute_report_1',
    'compute_report_2',
    'compute_report_3',
    'render_report_1',
    'render_report_2',
    'render_report_3'
]


def render_report_1(result):
    """Hiển thị Báo cáo 1 bằng bảng phân cấp AgGrid hỗ trợ chỉnh sửa và tính toán động."""
    st.subheader("Bản xem trước: Báo cáo theo Đợt học thử & Người phụ trách")
    
    state_key = "report_1_edited_df"
    dot_manual_key = "report_1_dot_manual"

    # Báo cáo 1 không còn nhập tay trực tiếp trong AgGrid, nên luôn dùng số liệu mới nhất.
    df_to_show = result.copy()
    
    # ====== BẢNG NHẬP TAY CỌC KHÁC & TỔNG CỌC HỌC THỬ THEO ĐỢT ======
    unique_dots = sorted(df_to_show['ĐỢT HỌC THỬ'].unique().tolist())
    
    dot_manual_df, manual_hash = render_dot_manual_inputs(
        "✏️ Nhập Cọc Khác & Tổng Cọc Học Thử theo Đợt học thử",
        dot_manual_key,
        unique_dots,
        ['Cọc Khác', 'Tổng Cọc Học Thử'],
        {
            'Cọc Khác': 'report_1_coc_khac',
            'Tổng Cọc Học Thử': 'report_1_tong_coc_ht',
        },
    )
    
    # Phân bổ giá trị nhập tay vào dòng đầu tiên mỗi đợt (để aggFunc sum hoạt động đúng ở group footer)
    df_to_show['Cọc Khác'] = 0
    df_to_show['Tổng Cọc Học Thử'] = 0
    for _, row in dot_manual_df.iterrows():
        dot_mask = df_to_show['ĐỢT HỌC THỬ'] == row['ĐỢT HỌC THỬ']
        if dot_mask.any():
            first_idx = df_to_show[dot_mask].index[0]
            df_to_show.at[first_idx, 'Cọc Khác'] = int(row['Cọc Khác'])
            df_to_show.at[first_idx, 'Tổng Cọc Học Thử'] = int(row['Tổng Cọc Học Thử'])
    st.session_state[state_key] = df_to_show
    
    # ====== XÂY DỰNG GRIDOPTIONS CHO AGGRID ======
    gb = GridOptionsBuilder.from_dataframe(df_to_show)
    
    # Thiết lập nhóm phân cấp
    gb.configure_column("ĐỢT HỌC THỬ", rowGroup=True, hide=True)
    gb.configure_column("Phòng ban", rowGroup=True, hide=True)
    gb.configure_column("Thời gian xuất data", width=140, pinned="left")
    gb.configure_column("Người phụ trách", width=160, pinned="left")
    
    # Cấu hình các cột số lượng và tỉ lệ KPI (tái sử dụng từ report_utils)
    count_cols = [
        'Sai Số - Sai Đối Tượng', 'Tiềm Năng Chưa Gọi', 'Data Chưa Trao Đổi + Auto Call',
        'Data Trao Đổi Được', 'Data Tiềm Năng', 'Data Cọc Chốt', 'Tổng số Data',
        'Tổng số data trừ sai số', 'Cọc Khác', 'Tổng Cọc Học Thử'
    ]
    configure_standard_grid_columns(gb, count_cols)

    grid_options = gb.build()
    grid_options["groupIncludeFooter"] = True
    grid_options["groupIncludeTotalFooter"] = True
    grid_options["groupDefaultExpanded"] = -1
    grid_options["suppressAggFuncInHeader"] = True

    # Dòng tổng cố định ở đầu bảng — tổng từ bảng nhập tay theo đợt
    if not df_to_show.empty:
        total_sai_so = int(df_to_show['Sai Số - Sai Đối Tượng'].sum())
        total_data = int(df_to_show['Tổng số Data'].sum())
        total_coc_khac = int(dot_manual_df['Cọc Khác'].sum()) if not dot_manual_df.empty else 0
        total_tong_coc = int(dot_manual_df['Tổng Cọc Học Thử'].sum()) if not dot_manual_df.empty else 0
        pinned_row = {
            'Thời gian xuất data': df_to_show['Thời gian xuất data'].iloc[0],
            'Người phụ trách': '📊 TỔNG DATA XUẤT RA',
            'Sai Số - Sai Đối Tượng': total_sai_so,
            'Tiềm Năng Chưa Gọi': int(df_to_show['Tiềm Năng Chưa Gọi'].sum()),
            'Data Chưa Trao Đổi + Auto Call': int(df_to_show['Data Chưa Trao Đổi + Auto Call'].sum()),
            'Data Trao Đổi Được': int(df_to_show['Data Trao Đổi Được'].sum()),
            'Data Tiềm Năng': int(df_to_show['Data Tiềm Năng'].sum()),
            'Data Cọc Chốt': int(df_to_show['Data Cọc Chốt'].sum()),
            'Tổng số Data': total_data,
            'Tổng số data trừ sai số': total_data - total_sai_so,
            'Cọc Khác': total_coc_khac,
            'Tổng Cọc Học Thử': total_tong_coc,
        }
        grid_options["pinnedTopRowData"] = [pinned_row]

    # Hiển thị AgGrid
    AgGrid(
        df_to_show,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=550,
        server_sync_strategy="server_wins",
        key=f"grid_report_1_v3_{manual_hash}"
    )

def render_report_2(result_2):
    """Hiển thị Báo cáo 2: Theo Đợt học thử & Nguồn khách hàng."""
    st.subheader("Bản xem trước: Báo cáo theo Đợt học thử & Nguồn khách hàng")

    state_key = "report_2_edited_df"
    dot_manual_key = "report_2_dot_manual"

    df_to_show = result_2.copy()

    # ====== BẢNG NHẬP TAY DATA THEO ĐỢT VÀ NGUỒN ======
    unique_pairs = df_to_show[['ĐỢT HỌC THỬ', 'Nguồn']].drop_duplicates().values.tolist()
    unique_pairs = [(str(row[0]), str(row[1])) for row in unique_pairs]
    
    manual_cols = ['Data trùng', 'Data vào nhóm Zalo', 'Data order', 'Data trùng bình quân 1 ngày trên 1 cố vấn']
    dot_manual_df, manual_hash = render_dot_nguon_manual_inputs(
        "✏️ Nhập Số liệu thực tế theo Đợt học thử & Nguồn",
        dot_manual_key,
        unique_pairs,
        manual_cols,
        {
            'Data trùng': 'r2_data_trung',
            'Data vào nhóm Zalo': 'r2_data_zalo',
            'Data order': 'r2_data_order',
            'Data trùng bình quân 1 ngày trên 1 cố vấn': 'r2_data_trung_bq',
        },
    )

    df_to_show['Data trùng'] = 0
    df_to_show['Data vào nhóm Zalo'] = 0
    df_to_show['Data order'] = 0
    df_to_show['Data trùng bình quân 1 ngày trên 1 cố vấn'] = 0

    if not dot_manual_df.empty:
        df_to_show.set_index(['ĐỢT HỌC THỬ', 'Nguồn'], inplace=True)
        dot_manual_idx = dot_manual_df.set_index(['ĐỢT HỌC THỬ', 'Nguồn'])
        df_to_show.update(dot_manual_idx)
        df_to_show.reset_index(inplace=True)

    df_to_show['Tổng data cần liên hệ'] = df_to_show['Tổng data chạy được'] + df_to_show['Data trùng']
    df_to_show['Tỷ lệ data thực tế/data order'] = df_to_show.apply(
        lambda row: (row['Tổng data chạy được'] / row['Data order'] * 100) if row.get('Data order', 0) > 0 else 0.0,
        axis=1
    )
            
    st.session_state[state_key] = df_to_show

    # Xây dựng GridOptions cho AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_to_show)

    # Thiết lập nhóm phân cấp: ĐỢT HỌC THỬ ẩn, Nguồn hiển thị
    gb.configure_column("ĐỢT HỌC THỬ", rowGroup=True, hide=True)
    gb.configure_column("Thời gian xuất data", width=140, pinned="left")
    gb.configure_column("Nguồn", width=200, pinned="left")

    # Cấu hình cột cho báo cáo 2
    count_cols = ['Tổng data chạy được']
    configure_report2_grid_columns(gb, count_cols)

    grid_options = gb.build()
    grid_options["groupIncludeFooter"] = True
    grid_options["groupIncludeTotalFooter"] = True
    grid_options["groupDefaultExpanded"] = -1
    grid_options["suppressAggFuncInHeader"] = True

    # Dòng tổng cố định ở đầu bảng (pinned top row)
    if not df_to_show.empty:
        time_val = df_to_show['Thời gian xuất data'].iloc[0] if len(df_to_show) > 0 else ''
        pinned_row = aggregate_report_2_rows(df_to_show, time_val, '', '📊 TỔNG CỘNG')
        # Loại bỏ Tỷ lệ data thực tế/data order khỏi pinned row nếu bạn muốn Grid tự hiển thị bằng valueGetter.
        # Nhưng để có sẵn value cũng không sao vì valueGetter ưu tiên data row.
        
        grid_options["pinnedTopRowData"] = [pinned_row]

    # Hiển thị AgGrid
    AgGrid(
        df_to_show,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=550,
        server_sync_strategy="server_wins",
        key=f"grid_report_2_v3_{manual_hash}"
    )

    # Chuẩn bị dữ liệu Excel hoàn chỉnh và nút download
    df_excel = prepare_excel_report_2(st.session_state[state_key], dot_manual_df)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_excel.round(2).to_excel(writer, sheet_name='BC_Nguon_Khach_Hang', index=False)

    st.download_button(
        label="📥 Tải xuống Báo cáo 2 (Excel)",
        data=buffer.getvalue(),
        file_name="Bao_cao_Nguon_Khach_Hang.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



def render_report_3(result_3):
    """Hiển thị Báo cáo 3: Ma trận Nguồn × Độ tuổi."""
    st.subheader("Bản xem trước: Báo cáo theo Nguồn khách hàng & Nhóm tuổi")
    
    if result_3.empty:
        st.warning("⚠️ Không có dữ liệu để hiển thị.")
        return
    
    df_to_show = result_3.copy()
    
    # Các cột cần gộp với phần trăm
    cols_to_merge = [
        "Học sinh cấp 1", "Học sinh cấp 2", "Học sinh cấp 3",
        "Sinh viên", "Người đi làm dưới 45 tuổi", 
        "Người đi làm từ 45 đến dưới 60 tuổi", "Người trên 60 tuổi",
        "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG",
        "HS cấp 2+3", "SV + DL <45", "Khác (HS1+45-60+60+Chưa điền)"
    ]
    
    for col in cols_to_merge:
        pct_col = f"{col} (%)"
        if col in df_to_show.columns and pct_col in df_to_show.columns:
            def format_cell(row):
                if pd.isnull(row[col]):
                    return ""
                # Định dạng số lượng: nếu là số nguyên thì không hiện .0, nếu là số lẻ thì hiện tối đa 2 chữ số
                val = row[col]
                val_str = f"{val:g}" if val == int(val) else f"{val:.2f}"
                return f"{val_str} ({row[pct_col]}%)"
                
            df_to_show[col] = df_to_show.apply(format_cell, axis=1)
            df_to_show.drop(columns=[pct_col], inplace=True)
            
    # Hiển thị DataFrame
    st.dataframe(
        df_to_show,
        width='stretch',
        hide_index=False
    )
    
    # Tải xuống Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        result_3.to_excel(writer, sheet_name='BC_Nguon_Tuoi', index=False)
    
    st.download_button(
        label="📥 Tải xuống Báo cáo 3 (Excel)",
        data=buffer.getvalue(),
        file_name="Bao_cao_Nguon_Tuoi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
