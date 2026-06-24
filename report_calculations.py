"""
report_calculations.py — Module tính toán số liệu và chuẩn bị dữ liệu Excel
Chứa:
- Thêm cột chỉ báo nhãn
- Tính toán dữ liệu tổng hợp cho Báo cáo 1 & 2
- Tính toán tỷ lệ phần trăm và cấu trúc dòng Tổng cộng cho xuất Excel
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from report_utils import TRAO_DOI_LABELS, TIEM_NANG_LABELS, COC_CHOT_LABELS
from data_processing import _classify_nguon

def add_indicator_columns(df_filtered):
    """
    Tạo các cột chỉ báo (0/1) trên dữ liệu đã lọc.
    Cần gọi trước khi tính báo cáo.
    """
    df_filtered["Data_trao_doi_duoc"] = df_filtered["Mối quan hệ"].isin(TRAO_DOI_LABELS).astype(int)
    df_filtered["Data_tiem_nang"]     = df_filtered["Mối quan hệ"].isin(TIEM_NANG_LABELS).astype(int)
    df_filtered["Data_coc_chot"]      = df_filtered["Mối quan hệ"].isin(COC_CHOT_LABELS).astype(int)
    
    # Các chỉ báo mới theo yêu cầu của người dùng
    df_filtered["SAI SỐ - SAI ĐỐI TƯỢNG"] = df_filtered["Mối quan hệ"].isin(["SAI SỐ", "SAI ĐỐI TƯỢNG.", "SAI SỐ - SAI ĐỐI TƯỢNG"]).astype(int)
    df_filtered["TIỀM NĂNG CHƯA GỌI"]     = df_filtered["Mối quan hệ"].isin(["TIỀM NĂNG CHƯA GỌI CVHT", "DATA CHƯA GỌI CVHT"]).astype(int)
    
    return df_filtered


def compute_report_1(df_filtered):
    """
    Tính toán Báo cáo 1: Theo Đợt học thử & Người phụ trách (dưới dạng flat DataFrame).
    """
    if df_filtered.empty:
        cols = [
            'Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Phòng ban', 'Người phụ trách',
            'Sai Số - Sai Đối Tượng', 'Tiềm Năng Chưa Gọi',
            'Data Trao Đổi Được', 'Data Tiềm Năng', 'Data Cọc Chốt', 'Tổng số Data',
            'Tổng số data trừ sai số', 'Cọc Khác', 'Tổng Cọc Học Thử',
            '% sai số-sai đối tượng/ Tổng data đã chia', 
            '% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng', 
            '% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng', 
            '% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng', 
            '% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng',
            '% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'
        ]
        return pd.DataFrame(columns=cols)

    fetch_time = st.session_state.get("fetch_time", datetime.now().strftime("%Hh%M ngày %d/%m"))

    result = (
        df_filtered
        .groupby(["ĐỢT HỌC THỬ", "Phòng ban", "Người phụ trách"])
        .agg(
            sai_so_sai_doi_tuong=("SAI SỐ - SAI ĐỐI TƯỢNG", "sum"),
            tiem_nang_chua_goi=("TIỀM NĂNG CHƯA GỌI", "sum"),
            Data_trao_doi_duoc=("Data_trao_doi_duoc", "sum"),
            Data_tiem_nang=("Data_tiem_nang", "sum"),
            Data_coc_chot=("Data_coc_chot", "sum"),
            Count=("Mã KH", "count"),
        )
        .reset_index()
    )

    result.rename(columns={
        "sai_so_sai_doi_tuong": "Sai Số - Sai Đối Tượng",
        "tiem_nang_chua_goi": "Tiềm Năng Chưa Gọi",
        "Data_trao_doi_duoc": "Data Trao Đổi Được",
        "Data_tiem_nang": "Data Tiềm Năng",
        "Data_coc_chot": "Data Cọc Chốt",
        "Count": "Tổng số Data"
    }, inplace=True)

    result['Thời gian xuất data'] = fetch_time
    result['Tổng số data trừ sai số'] = result['Tổng số Data'] - result['Sai Số - Sai Đối Tượng']
    result['Cọc Khác'] = 0
    result['Tổng Cọc Học Thử'] = 0

    result['% sai số-sai đối tượng/ Tổng data đã chia'] = 0.0
    result['% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0
    result['% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0
    result['% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0
    result['% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0
    result['% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0

    cols_order = [
        'Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Phòng ban', 'Người phụ trách',
        'Sai Số - Sai Đối Tượng', 'Tiềm Năng Chưa Gọi',
        'Data Trao Đổi Được', 'Data Tiềm Năng', 'Data Cọc Chốt', 'Tổng số Data',
        'Tổng số data trừ sai số', 'Cọc Khác', 'Tổng Cọc Học Thử',
        '% sai số-sai đối tượng/ Tổng data đã chia', 
        '% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng', 
        '% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng', 
        '% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng', 
        '% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng',
        '% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'
    ]
    result = result[cols_order]

    int_cols = [
        'Sai Số - Sai Đối Tượng', 'Tiềm Năng Chưa Gọi',
        'Data Trao Đổi Được', 'Data Tiềm Năng', 'Data Cọc Chốt', 'Tổng số Data',
        'Tổng số data trừ sai số', 'Cọc Khác', 'Tổng Cọc Học Thử'
    ]
    result[int_cols] = result[int_cols].astype(int)

    return result


def compute_report_2(df_filtered):
    """
    Tính toán Báo cáo 2: Theo Đợt học thử & Nguồn khách hàng (ADS-TC, ADS-CG, ORG, KHÁC).
    """
    if df_filtered.empty:
        cols = [
            'Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Nguồn',
            'Tổng số Data', 'Data order', '50% data order',
            '% data đã chia / 50% data order', '% data đã chia / data order'
        ]
        return pd.DataFrame(columns=cols)

    fetch_time = st.session_state.get("fetch_time", datetime.now().strftime("%Hh%M ngày %d/%m"))

    df_work = df_filtered.copy()
    df_work['_classified_source'] = df_work['_nguon_kh_list'].apply(
        lambda x: _classify_nguon(x[0]) if isinstance(x, list) and x else "KHÁC"
    )

    result_2 = (
        df_work
        .groupby(["ĐỢT HỌC THỬ", "_classified_source"])
        .agg(Count=("Mã KH", "count"))
        .reset_index()
    )

    result_2.rename(columns={
        "_classified_source": "Nguồn",
        "Count": "Tổng số Data"
    }, inplace=True)

    result_2['Thời gian xuất data'] = fetch_time
    result_2['Data order'] = 0
    result_2['50% data order'] = 0.0

    result_2['% data đã chia / 50% data order'] = 0.0
    result_2['% data đã chia / data order'] = 0.0

    cols_order = [
        'Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Nguồn',
        'Tổng số Data', 'Data order', '50% data order',
        '% data đã chia / 50% data order', '% data đã chia / data order'
    ]
    result_2 = result_2[cols_order]

    result_2['Tổng số Data'] = result_2['Tổng số Data'].astype(int)
    result_2['Data order'] = result_2['Data order'].astype(int)

    return result_2


# ==========================================
# CÁC HÀM TRỢ GIÚP XUẤT FILE EXCEL CHO PYTHON
# ==========================================

def compute_excel_percentages(df_excel):
    """
    Tính toán tỷ lệ phần trăm động trên DataFrame phục vụ xuất Excel.
    Tái sử dụng chung để tránh lặp logic toán học.
    """
    tot = df_excel['Tổng số Data']
    base = df_excel['Tổng số data trừ sai số']
    df_excel['% sai số-sai đối tượng/ Tổng data đã chia'] = (df_excel['Sai Số - Sai Đối Tượng'] / tot * 100).fillna(0)
    df_excel['% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng'] = (df_excel['Tiềm Năng Chưa Gọi'] / base * 100).fillna(0)
    df_excel['% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng'] = (df_excel['Data Trao Đổi Được'] / base * 100).fillna(0)
    df_excel['% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng'] = (df_excel['Data Tiềm Năng'] / base * 100).fillna(0)
    df_excel['% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng'] = (df_excel['Data Cọc Chốt'] / base * 100).fillna(0)
    
    tong_coc = pd.to_numeric(df_excel.get('Tổng Cọc Học Thử', 0), errors='coerce').fillna(0)
    df_excel['% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'] = (tong_coc / base * 100).fillna(0)
    return df_excel


def prepare_excel_report_1(df_edited):
    """Tính toán bảng hoàn chỉnh gồm phần trăm và dòng tổng cộng cho Report 1 (dùng cho download Excel)."""
    df_excel = df_edited.copy()
    df_excel = compute_excel_percentages(df_excel)
    
    if not df_excel.empty:
        total_row = {
            'Thời gian xuất data': df_excel['Thời gian xuất data'].iloc[0] if len(df_excel) > 0 else '',
            'ĐỢT HỌC THỬ': 'TỔNG CỘNG',
            'Phòng ban': '',
            'Người phụ trách': '',
            'Sai Số - Sai Đối Tượng': df_excel['Sai Số - Sai Đối Tượng'].sum(),
            'Tiềm Năng Chưa Gọi': df_excel['Tiềm Năng Chưa Gọi'].sum(),
            'Data Trao Đổi Được': df_excel['Data Trao Đổi Được'].sum(),
            'Data Tiềm Năng': df_excel['Data Tiềm Năng'].sum(),
            'Data Cọc Chốt': df_excel['Data Cọc Chốt'].sum(),
            'Tổng số Data': df_excel['Tổng số Data'].sum(),
            'Cọc Khác': df_excel['Cọc Khác'].sum(),
            'Tổng Cọc Học Thử': df_excel['Tổng Cọc Học Thử'].sum(),
        }

        total_row['Tổng số data trừ sai số'] = total_row['Tổng số Data'] - total_row['Sai Số - Sai Đối Tượng']

        tot_count = total_row['Tổng số Data']
        base = total_row['Tổng số data trừ sai số']
        total_row['% sai số-sai đối tượng/ Tổng data đã chia'] = (total_row['Sai Số - Sai Đối Tượng'] / tot_count * 100) if tot_count else 0
        total_row['% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng'] = (total_row['Tiềm Năng Chưa Gọi'] / base * 100) if base else 0
        total_row['% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng'] = (total_row['Data Trao Đổi Được'] / base * 100) if base else 0
        total_row['% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng'] = (total_row['Data Tiềm Năng'] / base * 100) if base else 0
        total_row['% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng'] = (total_row['Data Cọc Chốt'] / base * 100) if base else 0
        total_row['% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'] = (total_row.get('Tổng Cọc Học Thử', 0) / base * 100) if base else 0

        df_excel = pd.concat([df_excel, pd.DataFrame([total_row])], ignore_index=True)

    return df_excel


def prepare_excel_report_2(df_edited):
    """Tính toán bảng hoàn chỉnh gồm phần trăm và dòng tổng cộng cho Report 2 (dùng cho download Excel)."""
    df_excel = df_edited.copy()

    # Tính % trên từng dòng
    data_order = df_excel['Data order'].replace(0, float('nan'))
    half_order = data_order * 0.5
    df_excel['50% data order'] = half_order.fillna(0)
    df_excel['% data đã chia / 50% data order'] = (df_excel['Tổng số Data'] / half_order * 100).fillna(0)
    df_excel['% data đã chia / data order'] = (df_excel['Tổng số Data'] / data_order * 100).fillna(0)

    if not df_excel.empty:
        total_data = int(df_excel['Tổng số Data'].sum())
        total_order = int(df_excel['Data order'].sum())
        half_total = total_order * 0.5

        total_row = {
            'Thời gian xuất data': df_excel['Thời gian xuất data'].iloc[0] if len(df_excel) > 0 else '',
            'ĐỢT HỌC THỬ': 'TỔNG CỘNG',
            'Nguồn': '',
            'Tổng số Data': total_data,
            'Data order': total_order,
            '50% data order': half_total,
            '% data đã chia / 50% data order': (total_data / half_total * 100) if half_total else 0,
            '% data đã chia / data order': (total_data / total_order * 100) if total_order else 0,
        }

        df_excel = pd.concat([df_excel, pd.DataFrame([total_row])], ignore_index=True)

    return df_excel
