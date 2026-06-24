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
from report_utils import configure_standard_grid_columns, configure_report2_grid_columns, update_manual_inputs_in_state
from report_calculations import (
    add_indicator_columns, 
    compute_report_1, 
    compute_report_2,
    prepare_excel_report_1,
    prepare_excel_report_2
)

# Re-export để app.py import trực tiếp không bị lỗi
__all__ = [
    'add_indicator_columns',
    'compute_report_1',
    'compute_report_2',
    'render_report_1',
    'render_report_2'
]


def render_report_1(result):
    """Hiển thị Báo cáo 1 bằng bảng phân cấp AgGrid hỗ trợ chỉnh sửa và tính toán động."""
    st.subheader("Bản xem trước: Báo cáo theo Đợt học thử & Người phụ trách")
    
    state_key = "report_1_edited_df"
    
    # Khởi tạo hoặc reset trạng thái chỉnh sửa
    if state_key not in st.session_state or st.session_state[state_key] is None:
        st.session_state[state_key] = result.copy()
    else:
        # Nếu khóa nhóm hoặc số dòng thay đổi (do thay đổi bộ lọc), reset dữ liệu chỉnh sửa
        current_state = st.session_state[state_key]
        if (len(current_state) != len(result) or 
            not (current_state['ĐỢT HỌC THỬ'].equals(result['ĐỢT HỌC THỬ']) and 
                 current_state['Phòng ban'].equals(result['Phòng ban']) and
                 current_state['Người phụ trách'].equals(result['Người phụ trách']))):
            st.session_state[state_key] = result.copy()
            
    df_to_show = st.session_state[state_key]
    
    # Xây dựng GridOptions cho AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_to_show)
    
    # Thiết lập nhóm phân cấp
    gb.configure_column("ĐỢT HỌC THỬ", rowGroup=True, hide=True)
    gb.configure_column("Phòng ban", rowGroup=True, hide=True)
    gb.configure_column("Thời gian xuất data", width=140, pinned="left")
    gb.configure_column("Người phụ trách", width=160, pinned="left")
    
    # Cấu hình các cột số lượng và tỉ lệ KPI (tái sử dụng từ report_utils)
    count_cols = [
        'Sai Số - Sai Đối Tượng', 'Tiềm Năng Chưa Gọi',
        'Data Trao Đổi Được', 'Data Tiềm Năng', 'Data Cọc Chốt', 'Tổng số Data',
        'Tổng số data trừ sai số', 'Cọc Khác', 'Tổng Cọc Học Thử'
    ]
    configure_standard_grid_columns(gb, count_cols)

    grid_options = gb.build()
    grid_options["groupIncludeFooter"] = True
    grid_options["groupIncludeTotalFooter"] = True
    grid_options["groupDefaultExpanded"] = -1
    grid_options["suppressAggFuncInHeader"] = True

    # Dòng tổng cố định ở đầu bảng (pinned top row)
    if not df_to_show.empty:
        total_sai_so = int(df_to_show['Sai Số - Sai Đối Tượng'].sum())
        total_data = int(df_to_show['Tổng số Data'].sum())
        pinned_row = {
            'Thời gian xuất data': df_to_show['Thời gian xuất data'].iloc[0],
            'Người phụ trách': '📊 TỔNG DATA XUẤT RA',
            'Sai Số - Sai Đối Tượng': total_sai_so,
            'Tiềm Năng Chưa Gọi': int(df_to_show['Tiềm Năng Chưa Gọi'].sum()),
            'Data Trao Đổi Được': int(df_to_show['Data Trao Đổi Được'].sum()),
            'Data Tiềm Năng': int(df_to_show['Data Tiềm Năng'].sum()),
            'Data Cọc Chốt': int(df_to_show['Data Cọc Chốt'].sum()),
            'Tổng số Data': total_data,
            'Tổng số data trừ sai số': total_data - total_sai_so,
            'Cọc Khác': int(df_to_show['Cọc Khác'].sum()),
            'Tổng Cọc Học Thử': int(df_to_show['Tổng Cọc Học Thử'].sum()),
        }
        grid_options["pinnedTopRowData"] = [pinned_row]

    # Hiển thị AgGrid
    grid_response = AgGrid(
        df_to_show,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=550,
        key="grid_report_1"
    )

    # Lưu lại thay đổi nhập tay từ người dùng vào session state
    update_manual_inputs_in_state(grid_response, state_key, ['ĐỢT HỌC THỬ', 'Phòng ban', 'Người phụ trách'])

    # Chuẩn bị dữ liệu Excel hoàn chỉnh và nút download
    df_excel = prepare_excel_report_1(st.session_state[state_key])
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_excel.round(2).to_excel(writer, sheet_name='BC_Hoc_Thu_Phu_Trach', index=False)

    st.download_button(
        label="📥 Tải xuống Báo cáo 1 (Excel)",
        data=buffer.getvalue(),
        file_name="Bao_cao_Dot_Hoc_Thu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def render_report_2(result_2):
    """Hiển thị Báo cáo 2: Theo Đợt học thử & Nguồn (ADS-TC, ADS-CG, ORG, KHÁC)."""
    st.subheader("Bản xem trước: Báo cáo theo Đợt học thử & Nguồn khách hàng")

    state_key = "report_2_edited_df"

    # Khởi tạo hoặc reset trạng thái chỉnh sửa
    if state_key not in st.session_state or st.session_state[state_key] is None:
        st.session_state[state_key] = result_2.copy()
    else:
        current_state = st.session_state[state_key]
        if (len(current_state) != len(result_2) or
            not (current_state['ĐỢT HỌC THỬ'].equals(result_2['ĐỢT HỌC THỬ']) and
                 current_state['Nguồn'].equals(result_2['Nguồn']))):
            st.session_state[state_key] = result_2.copy()

    df_to_show = st.session_state[state_key]

    # Xây dựng GridOptions cho AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_to_show)

    # Thiết lập nhóm phân cấp: ĐỢT HỌC THẨ ẩn, Nguồn hiển thị
    gb.configure_column("ĐỢT HỌC THỬ", rowGroup=True, hide=True)
    gb.configure_column("Thời gian xuất data", width=140, pinned="left")
    gb.configure_column("Nguồn", width=200, pinned="left")

    # Cấu hình cột cho báo cáo 2
    count_cols = ['Tổng số Data']
    configure_report2_grid_columns(gb, count_cols)

    grid_options = gb.build()
    grid_options["groupIncludeFooter"] = True
    grid_options["groupIncludeTotalFooter"] = True
    grid_options["groupDefaultExpanded"] = -1
    grid_options["suppressAggFuncInHeader"] = True

    # Dòng tổng cố định ở đầu bảng (pinned top row)
    if not df_to_show.empty:
        total_data = int(df_to_show['Tổng số Data'].sum())
        pinned_row = {
            'Thời gian xuất data': df_to_show['Thời gian xuất data'].iloc[0],
            'Nguồn': '📊 TỔNG DATA XUẤT RA',
            'Tổng số Data': total_data,
            'Data order': 0,
            '50% data order': 0,
        }
        grid_options["pinnedTopRowData"] = [pinned_row]

    # Hiển thị AgGrid
    grid_response = AgGrid(
        df_to_show,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=550,
        key="grid_report_2"
    )

    # Lưu lại thay đổi nhập tay "Data order" từ người dùng
    update_manual_inputs_in_state(
        grid_response, state_key, ['ĐỢT HỌC THỬ', 'Nguồn'],
        editable_cols=['Data order']
    )

    # Chuẩn bị dữ liệu Excel hoàn chỉnh và nút download
    df_excel = prepare_excel_report_2(st.session_state[state_key])

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_excel.round(2).to_excel(writer, sheet_name='BC_Nguon_Khach_Hang', index=False)

    st.download_button(
        label="📥 Tải xuống Báo cáo 2 (Excel)",
        data=buffer.getvalue(),
        file_name="Bao_cao_Nguon_Khach_Hang.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
