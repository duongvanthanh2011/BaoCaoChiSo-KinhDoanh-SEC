"""
reports.py — Module tính toán và hiển thị báo cáo
Chứa các hàm:
- Tính toán Báo cáo 1: Theo Đợt học thử & Người phụ trách
- Tính toán Báo cáo 2: Theo Nguồn khách hàng & Nhóm
- Hiển thị từng báo cáo trên giao diện Streamlit
"""

import streamlit as st
import pandas as pd
import io


# ==========================================
# NHÃN PHÂN LOẠI MỐI QUAN HỆ
# ==========================================
TRAO_DOI_LABELS = ["ĐANG TRAO ĐỔI", "HỌC VIÊN TIỀM NĂNG", "ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]
TIEM_NANG_LABELS = ["HỌC VIÊN TIỀM NĂNG", "ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]
COC_CHOT_LABELS = ["ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]


def add_indicator_columns(df_filtered):
    """
    Tạo các cột chỉ báo (0/1) trên dữ liệu đã lọc.
    Cần gọi trước khi tính báo cáo.

    Args:
        df_filtered: DataFrame đã lọc theo đợt học thử

    Returns:
        pd.DataFrame: DataFrame với các cột chỉ báo đã thêm
    """
    df_filtered["Data_trao_doi_duoc"] = df_filtered["Mối quan hệ"].isin(TRAO_DOI_LABELS).astype(int)
    df_filtered["Data_tiem_nang"]     = df_filtered["Mối quan hệ"].isin(TIEM_NANG_LABELS).astype(int)
    df_filtered["Data_coc_chot"]      = df_filtered["Mối quan hệ"].isin(COC_CHOT_LABELS).astype(int)
    return df_filtered


def compute_report_1(df_filtered):
    """
    Tính toán Báo cáo 1: Theo Đợt học thử & Người phụ trách.

    Args:
        df_filtered: DataFrame đã có các cột chỉ báo

    Returns:
        pd.DataFrame: Bảng kết quả với dòng TỔNG CỘNG
    """
    result = (
        df_filtered
        .groupby(["ĐỢT HỌC THỬ", "Người phụ trách"])
        .agg(
            Data_trao_doi_duoc=("Data_trao_doi_duoc", "sum"),
            Data_tiem_nang=("Data_tiem_nang", "sum"),
            Data_coc_chot=("Data_coc_chot", "sum"),
            Count=("Mã KH", "count"),
        )
    )

    result['Tỉ lệ trao đổi được'] = (result['Data_trao_doi_duoc'] / result['Count']) * 100
    result['Tỉ lệ tiềm năng'] = (result['Data_tiem_nang'] / result['Count']) * 100
    result['Tỉ lệ cọc/chốt'] = (result['Data_coc_chot'] / result['Count']) * 100
    result = result.fillna(0)  # Tránh lỗi chia cho 0

    # Bổ sung thêm dòng TỔNG CỘNG ở cuối bảng
    if not result.empty:
        result.loc[("TỔNG CỘNG", ""), :] = [
            result["Data_trao_doi_duoc"].sum(),
            result["Data_tiem_nang"].sum(),
            result["Data_coc_chot"].sum(),
            result["Count"].sum(),
            result["Tỉ lệ trao đổi được"].mean(),
            result["Tỉ lệ tiềm năng"].mean(),
            result["Tỉ lệ cọc/chốt"].mean()
        ]
        int_cols = ["Data_trao_doi_duoc", "Data_tiem_nang", "Data_coc_chot", "Count"]
        result[int_cols] = result[int_cols].astype(int)

    return result


def compute_report_2(df_filtered):
    """
    Tính toán Báo cáo 2: Theo Nguồn khách hàng & Nhóm (explode nguồn).

    Args:
        df_filtered: DataFrame đã có các cột chỉ báo

    Returns:
        pd.DataFrame: Bảng kết quả với dòng TỔNG CỘNG
    """
    df_exploded = df_filtered.explode("_nguon_kh_list").copy()
    df_exploded.rename(columns={"_nguon_kh_list": "Nguồn khách hàng"}, inplace=True)

    result_2 = (
        df_exploded
        .groupby(["Nguồn khách hàng", "Nhóm khách hàng"])
        .agg(
            Data_trao_doi_duoc=("Data_trao_doi_duoc", "sum"),
            Data_tiem_nang=("Data_tiem_nang", "sum"),
            Data_coc_chot=("Data_coc_chot", "sum"),
            Count=("Mã KH", "count"),
        )
    )

    result_2['Tỉ lệ trao đổi được (%)'] = (result_2['Data_trao_doi_duoc'] / result_2['Count']) * 100
    result_2['Tỉ lệ tiềm năng (%)'] = (result_2['Data_tiem_nang'] / result_2['Count']) * 100
    result_2['Tỉ lệ cọc/chốt (%)'] = (result_2['Data_coc_chot'] / result_2['Count']) * 100
    result_2 = result_2.fillna(0)
    result_2.rename_axis(["Nguồn khách hàng", "Nhóm khách hàng"], inplace=True)

    # Bổ sung thêm dòng TỔNG CỘNG ở cuối bảng
    if not result_2.empty:
        result_2.loc[("TỔNG CỘNG", ""), :] = [
            result_2["Data_trao_doi_duoc"].sum(),
            result_2["Data_tiem_nang"].sum(),
            result_2["Data_coc_chot"].sum(),
            result_2["Count"].sum(),
            result_2["Tỉ lệ trao đổi được (%)"].mean(),
            result_2["Tỉ lệ tiềm năng (%)"].mean(),
            result_2["Tỉ lệ cọc/chốt (%)"].mean()
        ]
        int_cols = ["Data_trao_doi_duoc", "Data_tiem_nang", "Data_coc_chot", "Count"]
        result_2[int_cols] = result_2[int_cols].astype(int)

    return result_2


def render_report_1(result):
    """Hiển thị Báo cáo 1 trên giao diện Streamlit (bảng + download)."""
    st.subheader("Bản xem trước: Báo cáo theo Đợt học thử & Người phụ trách")

    num_cols = ['Data_trao_doi_duoc', 'Data_tiem_nang', 'Data_coc_chot', 'Count',
                'Tỉ lệ trao đổi được', 'Tỉ lệ tiềm năng', 'Tỉ lệ cọc/chốt']
    format_dict = {
        'Tỉ lệ trao đổi được': "{:.2f}",
        'Tỉ lệ tiềm năng': "{:.2f}",
        'Tỉ lệ cọc/chốt': "{:.2f}"
    }

    styled = result.style.background_gradient(cmap='Blues_r', subset=num_cols).format(format_dict)
    st.dataframe(styled, width='stretch')

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        result.round(2).to_excel(writer, sheet_name='BC_Hoc_Thu_Phu_Trach')

    st.download_button(
        label="📥 Tải xuống Báo cáo 1 (Excel)",
        data=buffer.getvalue(),
        file_name="Bao_cao_Dot_Hoc_Thu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def render_report_2(result_2):
    """Hiển thị Báo cáo 2 trên giao diện Streamlit (bảng + download)."""
    st.subheader("Bản xem trước: Báo cáo theo Nguồn khách hàng & Nhóm khách hàng")

    num_cols = ['Data_trao_doi_duoc', 'Data_tiem_nang', 'Data_coc_chot', 'Count',
                'Tỉ lệ trao đổi được (%)', 'Tỉ lệ tiềm năng (%)', 'Tỉ lệ cọc/chốt (%)']
    format_dict = {
        'Tỉ lệ trao đổi được (%)': "{:.2f}",
        'Tỉ lệ tiềm năng (%)': "{:.2f}",
        'Tỉ lệ cọc/chốt (%)': "{:.2f}"
    }

    styled = result_2.style.background_gradient(cmap='Greens_r', subset=num_cols).format(format_dict)
    st.dataframe(styled, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        result_2.round(2).to_excel(writer, sheet_name='BC_Nguon_Nhom_KH')

    st.download_button(
        label="📥 Tải xuống Báo cáo 2 (Excel)",
        data=buffer.getvalue(),
        file_name="Bao_cao_Nguon_Khach_Hang.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
