"""
reports.py — Module hiển thị báo cáo
Chứa các hàm:
- render_report_1: Hiển thị Báo cáo 1
- render_report_2: Hiển thị Báo cáo 2
- render_report_3: Hiển thị Báo cáo 3

Re-export các hàm từ report_calculations để tương thích ngược với app.py:
- add_indicator_columns
- compute_report_1
- compute_report_2
"""

import streamlit as st
import pandas as pd
from st_aggrid.grid_options_builder import GridOptionsBuilder

# Import các phần từ các module con
from report_utils import (
    configure_standard_grid_columns,
    configure_report2_grid_columns,
    configure_report3_grid_columns
)
from report_components import (
    render_dot_manual_inputs,
    render_dot_nguon_manual_inputs,
    render_dot_nguon_matrix_inputs,
    render_aggrid_report,
    render_excel_download,
    assign_dot_manual_to_first_row
)
from report_calculations import (
    add_indicator_columns, 
    compute_report_1, 
    compute_report_2, 
    compute_report_3,
    prepare_excel_report_1,
    prepare_excel_report_2,
    prepare_excel_report_3,
    aggregate_report_2_rows,
    aggregate_report_3_rows
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
    df_to_show = assign_dot_manual_to_first_row(
        df_to_show, dot_manual_df,
        ['Cọc Khác', 'Tổng Cọc Học Thử']
    )
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

    # Dòng tổng cố định ở đầu bảng — tổng từ bảng nhập tay theo đợt
    pinned_row = None
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

    # Hiển thị AgGrid
    render_aggrid_report(df_to_show, gb, pinned_row, f"grid_report_1_v3_{manual_hash}")

def render_report_2(result_2):
    """Hiển thị Báo cáo 2: Theo Đợt học thử & Nguồn khách hàng."""
    st.subheader("Bản xem trước: Báo cáo theo Đợt học thử & Nguồn khách hàng")

    state_key = "report_2_edited_df"
    dot_manual_key = "report_2_dot_manual"
    dot_nguon_manual_key = "report_2_dot_nguon_manual"

    df_to_show = result_2.copy()

    # ====== GIAO DIỆN NHẬP LIỆU GỌN GÀNG: EXPANDER + 2 CỘT SONG SONG ======
    unique_dots = sorted(df_to_show['ĐỢT HỌC THỬ'].unique().tolist())
    present_nguons = df_to_show['Nguồn'].unique().tolist()
    preferred_order = ["Trường Chinh", "Cầu Giấy", "Khác"]
    unique_nguons = [ng for ng in preferred_order if ng in present_nguons] + [ng for ng in present_nguons if ng not in preferred_order]
    if not unique_nguons:
        unique_nguons = preferred_order

    with st.expander("✏️ Bảng nhập số liệu thực tế (Data trùng, Zalo, Order, BQ)", expanded=True):
        col_input_1, col_input_2 = st.columns(2)

        with col_input_1:
            dot_nguon_manual_df, hash_nguon = render_dot_nguon_matrix_inputs(
                "Data trùng theo nguồn",
                dot_nguon_manual_key,
                unique_dots,
                unique_nguons,
                key_prefix="r2_trung"
            )

        with col_input_2:
            dot_manual_cols = ['Data vào nhóm Zalo', 'Data order', 'Data trùng bình quân 1 ngày trên 1 cố vấn']
            dot_manual_df, hash_dot = render_dot_manual_inputs(
                "Số liệu chung theo đợt",
                dot_manual_key,
                unique_dots,
                dot_manual_cols,
                {
                    'Data vào nhóm Zalo': 'r2_data_zalo',
                    'Data order': 'r2_data_order',
                    'Data trùng bình quân 1 ngày trên 1 cố vấn': 'r2_data_trung_bq',
                },
                float_columns=['Data trùng bình quân 1 ngày trên 1 cố vấn'],
                display_labels={
                    'Data vào nhóm Zalo': 'Vào nhóm Zalo',
                    'Data order': 'Data order',
                    'Data trùng bình quân 1 ngày trên 1 cố vấn': 'Trùng BQ/ngày'
                }
            )

    manual_hash = f"{hash_nguon}_{hash_dot}"

    # Cập nhật Data trùng cho từng (Đợt, Nguồn)
    df_to_show['Data trùng'] = 0
    if not dot_nguon_manual_df.empty:
        dot_nguon_map = dot_nguon_manual_df.set_index(['ĐỢT HỌC THỬ', 'Nguồn'])['Data trùng'].to_dict()
        df_to_show['Data trùng'] = df_to_show.apply(
            lambda r: int(dot_nguon_map.get((str(r['ĐỢT HỌC THỬ']), str(r['Nguồn'])), 0)),
            axis=1
        )

    # Cập nhật Data vào nhóm Zalo, Data order, Data trùng bình quân vào dòng đầu tiên của mỗi đợt
    r2_float_cast = lambda v: round(float(v), 2)
    df_to_show = assign_dot_manual_to_first_row(
        df_to_show, dot_manual_df,
        ['Data vào nhóm Zalo', 'Data order', 'Data trùng bình quân 1 ngày trên 1 cố vấn'],
        type_map={'Data trùng bình quân 1 ngày trên 1 cố vấn': r2_float_cast}
    )

    df_to_show['Tổng data cần liên hệ'] = (df_to_show['Tổng data chạy được'] + df_to_show['Data trùng']).round(2)
    df_to_show['Tỷ lệ data thực tế/data order'] = 0.0

    # Đảm bảo thứ tự cột chuẩn xác: Thời gian xuất data -> ĐỢT HỌC THỬ -> Nguồn -> ...
    cols_order = [
        'Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Nguồn',
        'Tổng data chạy được', 'Data trùng', 'Tổng data cần liên hệ',
        'Data vào nhóm Zalo', 'Data order', 'Data trùng bình quân 1 ngày trên 1 cố vấn',
        'Tỷ lệ data thực tế/data order'
    ]
    df_to_show = df_to_show[cols_order]
    st.session_state[state_key] = df_to_show

    # Xây dựng GridOptions cho AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_to_show)

    # Thiết lập nhóm phân cấp: ĐỢT HỌC THỬ ẩn, Thời gian xuất data và Nguồn hiển thị pinned
    gb.configure_column("ĐỢT HỌC THỬ", rowGroup=True, hide=True)
    gb.configure_column("Thời gian xuất data", width=140, pinned="left")
    gb.configure_column("Nguồn", width=200, pinned="left")

    # Cấu hình các cột cho báo cáo 2
    configure_report2_grid_columns(gb)

    # Dòng tổng cố định ở đầu bảng (pinned top row)
    pinned_row = None
    if not df_to_show.empty:
        time_val = df_to_show['Thời gian xuất data'].iloc[0] if len(df_to_show) > 0 else ''
        total_zalo = int(dot_manual_df['Data vào nhóm Zalo'].sum()) if not dot_manual_df.empty else 0
        total_order = int(dot_manual_df['Data order'].sum()) if not dot_manual_df.empty else 0
        total_trung_bq = round(float(dot_manual_df['Data trùng bình quân 1 ngày trên 1 cố vấn'].sum()), 2) if not dot_manual_df.empty else 0.0

        pinned_row = aggregate_report_2_rows(
            df_to_show,
            time_val,
            '',
            '📊 TỔNG CỘNG',
            dot_manual_values={
                'Data vào nhóm Zalo': total_zalo,
                'Data order': total_order,
                'Data trùng bình quân 1 ngày trên 1 cố vấn': total_trung_bq
            }
        )

    # Hiển thị AgGrid
    render_aggrid_report(df_to_show, gb, pinned_row, f"grid_report_2_v3_{manual_hash}")

    # Chuẩn bị dữ liệu Excel hoàn chỉnh và nút download
    df_excel = prepare_excel_report_2(st.session_state[state_key], dot_manual_df)
    render_excel_download(
        df_excel,
        sheet_name='BC_Nguon_Khach_Hang',
        file_name='Bao_cao_Nguon_Khach_Hang.xlsx',
        button_label='📥 Tải xuống Báo cáo 2 (Excel)'
    )



def render_report_3(result_3):
    """Hiển thị Báo cáo 3: Ma trận Nguồn × Nhóm tuổi theo Đợt học thử bằng AgGrid."""
    st.subheader("Bản xem trước: Báo cáo theo Đợt học thử, Nguồn & Nhóm tuổi")
    
    if result_3.empty:
        st.warning("⚠️ Không có dữ liệu để hiển thị.")
        return
    
    df_to_show = result_3.copy()

    # Xây dựng GridOptions cho AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_to_show)

    # Thiết lập nhóm phân cấp: ĐỢT HỌC THỬ ẩn (làm row group), Nguồn hiển thị
    gb.configure_column("ĐỢT HỌC THỬ", rowGroup=True, hide=True)
    gb.configure_column("Thời gian xuất data", width=140, pinned="left")
    gb.configure_column("Nguồn", width=200, pinned="left")

    # Cấu hình các cột nhóm tuổi, tổng và nhóm gộp
    configure_report3_grid_columns(gb)

    # Dòng tổng cố định ở đầu bảng (pinned top row)
    pinned_row = None
    if not df_to_show.empty:
        time_val = df_to_show['Thời gian xuất data'].iloc[0] if len(df_to_show) > 0 else ''
        pinned_row = aggregate_report_3_rows(df_to_show, time_val, '', '📊 TỔNG CỘNG')

    # Hiển thị AgGrid (đồng nhất giao diện & font chữ với Báo cáo 1 và 2)
    render_aggrid_report(df_to_show, gb, pinned_row, "grid_report_3_v1")

    # Chuẩn bị dữ liệu Excel hoàn chỉnh và nút download
    df_excel = prepare_excel_report_3(df_to_show)
    render_excel_download(
        df_excel,
        sheet_name='BC_Nguon_Tuoi',
        file_name='Bao_cao_Nguon_Tuoi.xlsx',
        button_label='📥 Tải xuống Báo cáo 3 (Excel)'
    )
