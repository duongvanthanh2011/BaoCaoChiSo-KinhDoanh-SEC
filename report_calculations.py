"""
report_calculations.py — Module tính toán số liệu và chuẩn bị dữ liệu Excel
Chứa:
- Thêm cột chỉ báo nhãn
- Tính toán dữ liệu tổng hợp cho Báo cáo 1 & 2
- Tính toán tỷ lệ phần trăm và cấu trúc dòng Tổng cộng cho xuất Excel
"""

import streamlit as st
import pandas as pd
from report_utils import (
    COC_CHOT_LABELS,
    SAI_SO_SAI_DOI_TUONG_LABELS,
    TIEM_NANG_CHUA_GOI_LABELS,
    TIEM_NANG_LABELS,
    TRAO_DOI_LABELS,
    CHUA_TRAO_DOI_AUTO_CALL_LABELS,
)
from data_processing import _classify_nguon
from time_utils import format_fetch_time

def add_indicator_columns(df_filtered):
    """
    Tạo các cột chỉ báo (0/1) trên dữ liệu đã lọc.
    Cần gọi trước khi tính báo cáo.
    """
    indicator_label_map = {
        "Data_trao_doi_duoc": TRAO_DOI_LABELS,
        "Data_tiem_nang": TIEM_NANG_LABELS,
        "Data_coc_chot": COC_CHOT_LABELS,
        "SAI SỐ - SAI ĐỐI TƯỢNG": SAI_SO_SAI_DOI_TUONG_LABELS,
        "TIỀM NĂNG CHƯA GỌI": TIEM_NANG_CHUA_GOI_LABELS,
        "Data_chua_trao_doi_autocall": CHUA_TRAO_DOI_AUTO_CALL_LABELS,
    }

    relation_series = df_filtered["Mối quan hệ"]
    for column_name, labels in indicator_label_map.items():
        df_filtered[column_name] = relation_series.isin(labels).astype(int)
    
    return df_filtered


def compute_report_1(df_filtered):
    """
    Tính toán Báo cáo 1: Theo Đợt học thử & Người phụ trách (dưới dạng flat DataFrame).
    """
    if df_filtered.empty:
        cols = [
            'Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Phòng ban', 'Người phụ trách',
            'Sai Số - Sai Đối Tượng', 'Tiềm Năng Chưa Gọi', 'Data Chưa Trao Đổi + Auto Call',
            'Data Trao Đổi Được', 'Data Tiềm Năng', 'Data Cọc Chốt', 'Tổng số Data',
            'Tổng số data trừ sai số', 'Cọc Khác', 'Tổng Cọc Học Thử',
            '% sai số-sai đối tượng/ Tổng data đã chia', 
            '% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng', 
            '% data Chưa trao đổi được + autocall / Tổng data đã chia trừ sai số-sai đối tượng',
            '% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng', 
            '% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng', 
            '% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng',
            '% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'
        ]
        return pd.DataFrame(columns=cols)

    fetch_time = st.session_state.get("fetch_time") or format_fetch_time()

    result = (
        df_filtered
        .groupby(["ĐỢT HỌC THỬ", "Phòng ban", "Người phụ trách"])
        .agg(
            sai_so_sai_doi_tuong=("SAI SỐ - SAI ĐỐI TƯỢNG", "sum"),
            tiem_nang_chua_goi=("TIỀM NĂNG CHƯA GỌI", "sum"),
            Data_chua_trao_doi_autocall=("Data_chua_trao_doi_autocall", "sum"),
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
        "Data_chua_trao_doi_autocall": "Data Chưa Trao Đổi + Auto Call",
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
    result['% data Chưa trao đổi được + autocall / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0
    result['% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0
    result['% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0
    result['% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0
    result['% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'] = 0.0

    cols_order = [
        'Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Phòng ban', 'Người phụ trách',
        'Sai Số - Sai Đối Tượng', 'Tiềm Năng Chưa Gọi', 'Data Chưa Trao Đổi + Auto Call',
        'Data Trao Đổi Được', 'Data Tiềm Năng', 'Data Cọc Chốt', 'Tổng số Data',
        'Tổng số data trừ sai số', 'Cọc Khác', 'Tổng Cọc Học Thử',
        '% sai số-sai đối tượng/ Tổng data đã chia', 
        '% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng', 
        '% data Chưa trao đổi được + autocall / Tổng data đã chia trừ sai số-sai đối tượng',
        '% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng', 
        '% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng', 
        '% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng',
        '% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'
    ]
    result = result[cols_order]

    int_cols = [
        'Sai Số - Sai Đối Tượng', 'Tiềm Năng Chưa Gọi', 'Data Chưa Trao Đổi + Auto Call',
        'Data Trao Đổi Được', 'Data Tiềm Năng', 'Data Cọc Chốt', 'Tổng số Data',
        'Tổng số data trừ sai số', 'Cọc Khác', 'Tổng Cọc Học Thử'
    ]
    result[int_cols] = result[int_cols].astype(int)

    return result


def compute_report_2(df_filtered):
    """
    Tính toán Báo cáo 2: Theo Đợt học thử & Nguồn khách hàng.
    Sử dụng logic phân loại nguồn và chia trọng số 1/N.
    """
    cols_order = [
        'Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Nguồn',
        'Tổng data chạy được', 'Data trùng', 'Tổng data cần liên hệ',
        'Data vào nhóm Zalo', 'Data order', 'Data trùng bình quân 1 ngày trên 1 cố vấn',
        'Tỷ lệ data thực tế/data order'
    ]

    if df_filtered.empty:
        return pd.DataFrame(columns=cols_order)

    fetch_time = st.session_state.get("fetch_time") or format_fetch_time()

    # Expand weighted sources
    rows = []
    for _, row in df_filtered.iterrows():
        sources_weights = row.get("_sources_with_weights")
        if not isinstance(sources_weights, list):
            sources_weights = [("Khác", 1.0)]
        
        dot = row.get("ĐỢT HỌC THỬ", "Chưa xác định")
        if not isinstance(dot, str) or not dot.strip():
            dot = "Chưa xác định"
        
        for source_classified, weight in sources_weights:
            rows.append({
                "ĐỢT HỌC THỬ": dot,
                "Nguồn": source_classified,
                "Weight": weight
            })

    expanded_df = pd.DataFrame(rows)
    
    if expanded_df.empty:
        return pd.DataFrame(columns=cols_order)

    result_2 = (
        expanded_df.groupby(["ĐỢT HỌC THỬ", "Nguồn"])["Weight"]
        .sum()
        .reset_index()
    )

    result_2.rename(columns={
        "Weight": "Tổng data chạy được"
    }, inplace=True)

    result_2['Thời gian xuất data'] = fetch_time
    result_2['Data trùng'] = 0
    result_2['Tổng data cần liên hệ'] = result_2['Tổng data chạy được']
    result_2['Data vào nhóm Zalo'] = 0
    result_2['Data order'] = 0
    result_2['Data trùng bình quân 1 ngày trên 1 cố vấn'] = 0.0
    result_2['Tỷ lệ data thực tế/data order'] = 0.0

    result_2 = result_2[cols_order]

    result_2['Tổng data chạy được'] = result_2['Tổng data chạy được'].round(2)
    result_2['Tổng data cần liên hệ'] = result_2['Tổng data cần liên hệ'].round(2)

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
    df_excel['% data Chưa trao đổi được + autocall / Tổng data đã chia trừ sai số-sai đối tượng'] = (df_excel['Data Chưa Trao Đổi + Auto Call'] / base * 100).fillna(0)
    df_excel['% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng'] = (df_excel['Data Trao Đổi Được'] / base * 100).fillna(0)
    df_excel['% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng'] = (df_excel['Data Tiềm Năng'] / base * 100).fillna(0)
    df_excel['% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng'] = (df_excel['Data Cọc Chốt'] / base * 100).fillna(0)
    
    tong_coc = pd.to_numeric(df_excel.get('Tổng Cọc Học Thử', 0), errors='coerce').fillna(0)
    df_excel['% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'] = (tong_coc / base * 100).fillna(0)
    return df_excel


def prepare_excel_report_1(df_edited, dot_manual_df=None):
    """Tính toán bảng hoàn chỉnh gồm phần trăm, dòng tổng đợt và dòng tổng cộng cho Report 1 (dùng cho download Excel)."""
    df_excel = df_edited.copy()
    
    # Xóa giá trị Cọc Khác và Tổng Cọc Học Thử ở cấp người phụ trách
    # (giá trị này thuộc cấp đợt, sẽ hiển thị ở dòng tổng đợt)
    df_excel['Cọc Khác'] = 0
    df_excel['Tổng Cọc Học Thử'] = 0
    
    df_excel = compute_excel_percentages(df_excel)
    
    if not df_excel.empty:
        # Xây dựng bảng với dòng tổng theo từng đợt
        result_parts = []
        for dot_name in df_excel['ĐỢT HỌC THỬ'].unique():
            group = df_excel[df_excel['ĐỢT HỌC THỬ'] == dot_name]
            result_parts.append(group)
            
            # Lấy giá trị nhập tay cho đợt này
            coc_khac = 0
            tong_coc_ht = 0
            if dot_manual_df is not None and not dot_manual_df.empty:
                dot_row = dot_manual_df[dot_manual_df['ĐỢT HỌC THỬ'] == dot_name]
                if not dot_row.empty:
                    coc_khac = int(dot_row['Cọc Khác'].iloc[0])
                    tong_coc_ht = int(dot_row['Tổng Cọc Học Thử'].iloc[0])
            
            # Tạo dòng tổng đợt
            sub_data = group['Tổng số Data'].sum()
            sub_sai_so = group['Sai Số - Sai Đối Tượng'].sum()
            sub_base = sub_data - sub_sai_so
            sub_tn_chua_goi = group['Tiềm Năng Chưa Gọi'].sum()
            sub_chua_trao_doi_autocall = group['Data Chưa Trao Đổi + Auto Call'].sum()
            sub_trao_doi = group['Data Trao Đổi Được'].sum()
            sub_tiem_nang = group['Data Tiềm Năng'].sum()
            sub_coc_chot = group['Data Cọc Chốt'].sum()
            
            subtotal = {
                'Thời gian xuất data': group['Thời gian xuất data'].iloc[0],
                'ĐỢT HỌC THỬ': f'TỔNG {dot_name}',
                'Phòng ban': '',
                'Người phụ trách': '',
                'Sai Số - Sai Đối Tượng': sub_sai_so,
                'Tiềm Năng Chưa Gọi': sub_tn_chua_goi,
                'Data Chưa Trao Đổi + Auto Call': sub_chua_trao_doi_autocall,
                'Data Trao Đổi Được': sub_trao_doi,
                'Data Tiềm Năng': sub_tiem_nang,
                'Data Cọc Chốt': sub_coc_chot,
                'Tổng số Data': sub_data,
                'Tổng số data trừ sai số': sub_base,
                'Cọc Khác': coc_khac,
                'Tổng Cọc Học Thử': tong_coc_ht,
                '% sai số-sai đối tượng/ Tổng data đã chia': (sub_sai_so / sub_data * 100) if sub_data else 0,
                '% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng': (sub_tn_chua_goi / sub_base * 100) if sub_base else 0,
                '% data Chưa trao đổi được + autocall / Tổng data đã chia trừ sai số-sai đối tượng': (sub_chua_trao_doi_autocall / sub_base * 100) if sub_base else 0,
                '% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng': (sub_trao_doi / sub_base * 100) if sub_base else 0,
                '% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng': (sub_tiem_nang / sub_base * 100) if sub_base else 0,
                '% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng': (sub_coc_chot / sub_base * 100) if sub_base else 0,
                '% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng': (tong_coc_ht / sub_base * 100) if sub_base else 0,
            }
            result_parts.append(pd.DataFrame([subtotal]))
        
        df_excel = pd.concat(result_parts, ignore_index=True)
        
        # Dòng TỔNG CỘNG cuối cùng — chỉ tính từ dòng chi tiết (không tính dòng tổng đợt)
        person_mask = ~df_excel['ĐỢT HỌC THỬ'].astype(str).str.startswith('TỔNG ')
        person_rows = df_excel[person_mask]
        
        total_coc_khac = int(dot_manual_df['Cọc Khác'].sum()) if dot_manual_df is not None and not dot_manual_df.empty else 0
        total_tong_coc = int(dot_manual_df['Tổng Cọc Học Thử'].sum()) if dot_manual_df is not None and not dot_manual_df.empty else 0
        
        tot_data = person_rows['Tổng số Data'].sum()
        tot_sai_so = person_rows['Sai Số - Sai Đối Tượng'].sum()
        tot_base = tot_data - tot_sai_so
        tot_tn_chua_goi = person_rows['Tiềm Năng Chưa Gọi'].sum()
        tot_chua_trao_doi_autocall = person_rows['Data Chưa Trao Đổi + Auto Call'].sum()
        tot_trao_doi = person_rows['Data Trao Đổi Được'].sum()
        tot_tiem_nang = person_rows['Data Tiềm Năng'].sum()
        tot_coc_chot = person_rows['Data Cọc Chốt'].sum()
        
        total_row = {
            'Thời gian xuất data': df_excel['Thời gian xuất data'].iloc[0] if len(df_excel) > 0 else '',
            'ĐỢT HỌC THỬ': 'TỔNG CỘNG',
            'Phòng ban': '',
            'Người phụ trách': '',
            'Sai Số - Sai Đối Tượng': tot_sai_so,
            'Tiềm Năng Chưa Gọi': tot_tn_chua_goi,
            'Data Chưa Trao Đổi + Auto Call': tot_chua_trao_doi_autocall,
            'Data Trao Đổi Được': tot_trao_doi,
            'Data Tiềm Năng': tot_tiem_nang,
            'Data Cọc Chốt': tot_coc_chot,
            'Tổng số Data': tot_data,
            'Tổng số data trừ sai số': tot_base,
            'Cọc Khác': total_coc_khac,
            'Tổng Cọc Học Thử': total_tong_coc,
            '% sai số-sai đối tượng/ Tổng data đã chia': (tot_sai_so / tot_data * 100) if tot_data else 0,
            '% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng': (tot_tn_chua_goi / tot_base * 100) if tot_base else 0,
            '% data Chưa trao đổi được + autocall / Tổng data đã chia trừ sai số-sai đối tượng': (tot_chua_trao_doi_autocall / tot_base * 100) if tot_base else 0,
            '% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng': (tot_trao_doi / tot_base * 100) if tot_base else 0,
            '% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng': (tot_tiem_nang / tot_base * 100) if tot_base else 0,
            '% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng': (tot_coc_chot / tot_base * 100) if tot_base else 0,
            '% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng': (total_tong_coc / tot_base * 100) if tot_base else 0,
        }
        
        df_excel = pd.concat([df_excel, pd.DataFrame([total_row])], ignore_index=True)

    return df_excel


def aggregate_report_2_rows(df_rows, time_val, dot_val, nguon_val, dot_manual_values=None):
    """Tính tổng các cột cho Báo cáo 2 từ một DataFrame con và trả về 1 dict đại diện cho dòng tổng."""
    tot_data = round(float(df_rows['Tổng data chạy được'].sum()), 2)
    tot_trung = int(df_rows['Data trùng'].sum()) if 'Data trùng' in df_rows else 0
    tot_lien_he = round(tot_data + tot_trung, 2)
    
    if dot_manual_values:
        tot_zalo = int(dot_manual_values.get('Data vào nhóm Zalo', 0))
        tot_order = int(dot_manual_values.get('Data order', 0))
        tot_trung_bq = round(float(dot_manual_values.get('Data trùng bình quân 1 ngày trên 1 cố vấn', 0.0)), 2)
    else:
        tot_zalo = int(df_rows['Data vào nhóm Zalo'].sum()) if 'Data vào nhóm Zalo' in df_rows else 0
        tot_order = int(df_rows['Data order'].sum()) if 'Data order' in df_rows else 0
        tot_trung_bq = round(float(df_rows['Data trùng bình quân 1 ngày trên 1 cố vấn'].sum()), 2) if 'Data trùng bình quân 1 ngày trên 1 cố vấn' in df_rows else 0.0

    return {
        'Thời gian xuất data': time_val,
        'ĐỢT HỌC THỬ': dot_val,
        'Nguồn': nguon_val,
        'Tổng data chạy được': tot_data,
        'Data trùng': tot_trung,
        'Tổng data cần liên hệ': tot_lien_he,
        'Data vào nhóm Zalo': tot_zalo,
        'Data order': tot_order,
        'Data trùng bình quân 1 ngày trên 1 cố vấn': tot_trung_bq,
        'Tỷ lệ data thực tế/data order': round(tot_data / tot_order * 100, 2) if tot_order else 0.0,
    }

def prepare_excel_report_2(df_edited, dot_manual_df=None):
    """Tính toán bảng hoàn chỉnh gồm phần trăm và dòng tổng cộng cho Report 2 (dùng cho download Excel)."""
    df_excel = df_edited.copy()

    if df_excel.empty:
        return df_excel

    result_parts = []
    
    for dot_name in df_excel['ĐỢT HỌC THỬ'].unique():
        group = df_excel[df_excel['ĐỢT HỌC THỬ'] == dot_name].copy()
        
        # Ở cấp nguồn chi tiết: không hiển thị Data Zalo, Order, BQ, Tỷ lệ (chỉ hiển thị ở dòng tổng đợt)
        group_display = group.copy()
        group_display['Data vào nhóm Zalo'] = None
        group_display['Data order'] = None
        group_display['Data trùng bình quân 1 ngày trên 1 cố vấn'] = None
        group_display['Tỷ lệ data thực tế/data order'] = None
        result_parts.append(group_display)

        time_val = group['Thời gian xuất data'].iloc[0] if len(group) > 0 else ''
        
        dot_zalo = 0
        dot_order = 0
        dot_trung_bq = 0.0
        if dot_manual_df is not None and not dot_manual_df.empty:
            m_row = dot_manual_df[dot_manual_df['ĐỢT HỌC THỬ'] == dot_name]
            if not m_row.empty:
                dot_zalo = int(m_row['Data vào nhóm Zalo'].iloc[0])
                dot_order = int(m_row['Data order'].iloc[0])
                dot_trung_bq = round(float(m_row['Data trùng bình quân 1 ngày trên 1 cố vấn'].iloc[0]), 2)
        else:
            dot_zalo = int(group['Data vào nhóm Zalo'].sum())
            dot_order = int(group['Data order'].sum())
            dot_trung_bq = round(float(group['Data trùng bình quân 1 ngày trên 1 cố vấn'].sum()), 2)

        subtotal = aggregate_report_2_rows(
            group,
            time_val,
            f'TỔNG {dot_name}',
            '',
            dot_manual_values={
                'Data vào nhóm Zalo': dot_zalo,
                'Data order': dot_order,
                'Data trùng bình quân 1 ngày trên 1 cố vấn': dot_trung_bq
            }
        )
        result_parts.append(pd.DataFrame([subtotal]))

    df_excel = pd.concat(result_parts, ignore_index=True)

    # Tính dòng TỔNG CỘNG
    detail_mask = ~df_excel['ĐỢT HỌC THỬ'].astype(str).str.startswith('TỔNG ')
    detail_rows = df_excel[detail_mask]
    
    time_val = df_excel['Thời gian xuất data'].iloc[0] if len(df_excel) > 0 else ''
    
    tot_zalo = int(dot_manual_df['Data vào nhóm Zalo'].sum()) if dot_manual_df is not None and not dot_manual_df.empty else 0
    tot_order = int(dot_manual_df['Data order'].sum()) if dot_manual_df is not None and not dot_manual_df.empty else 0
    tot_trung_bq = round(float(dot_manual_df['Data trùng bình quân 1 ngày trên 1 cố vấn'].sum()), 2) if dot_manual_df is not None and not dot_manual_df.empty else 0.0

    total_row = aggregate_report_2_rows(
        detail_rows,
        time_val,
        'TỔNG CỘNG',
        '',
        dot_manual_values={
            'Data vào nhóm Zalo': tot_zalo,
            'Data order': tot_order,
            'Data trùng bình quân 1 ngày trên 1 cố vấn': tot_trung_bq
        }
    )

    df_excel = pd.concat([df_excel, pd.DataFrame([total_row])], ignore_index=True)
    return df_excel


# ==========================================
# BÁO CÁO 3: THỐNG KÊ THEO NGUỒN & ĐỘ TUỔI
# ==========================================

def compute_report_3(df_filtered):
    """
    Tính toán Báo cáo 3: Ma trận Nguồn × Độ tuổi phân theo Đợt học thử với trọng số.
    
    Returns:
        pd.DataFrame với các cột:
        - Thời gian xuất data
        - ĐỢT HỌC THỬ
        - Nguồn
        - Các nhóm tuổi (8 cột)
        - TỔNG
        - Nhóm tổng hợp: HS cấp 2+3, SV + DL <45, Khác (HS1+45-60+60+Chưa điền)
    """
    from data_processing import AGE_GROUPS

    cols_order = (
        ['Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Nguồn']
        + AGE_GROUPS
        + ['TỔNG', 'HS cấp 2+3', 'SV + DL <45', 'Khác (HS1+45-60+60+Chưa điền)']
    )

    if df_filtered.empty:
        return pd.DataFrame(columns=cols_order)
    
    fetch_time = st.session_state.get("fetch_time") or format_fetch_time()

    # Expand weighted sources with ĐỢT HỌC THỬ
    rows = []
    for _, row in df_filtered.iterrows():
        sources_weights = row.get("_sources_with_weights")
        if not isinstance(sources_weights, list):
            sources_weights = [("Khác", 1.0)]
        
        dot = row.get("ĐỢT HỌC THỬ", "Chưa xác định")
        if not isinstance(dot, str) or not dot.strip():
            dot = "Chưa xác định"
        
        age_group = row.get("Nhóm tuổi")
        if not isinstance(age_group, str) or not age_group.strip():
            age_group = "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG"
        
        for source_classified, weight in sources_weights:
            rows.append({
                "ĐỢT HỌC THỬ": dot,
                "Nguồn": source_classified,
                "Nhóm tuổi": age_group,
                "Weight": weight
            })

    expanded_df = pd.DataFrame(rows)
    if expanded_df.empty:
        return pd.DataFrame(columns=cols_order)
    
    # Pivot table: sum weights by (ĐỢT HỌC THỬ, Nguồn, Nhóm tuổi)
    pivot = (
        expanded_df
        .groupby(["ĐỢT HỌC THỬ", "Nguồn", "Nhóm tuổi"])["Weight"]
        .sum()
        .unstack(fill_value=0)
    )
    
    # Reindex với toàn bộ AGE_GROUPS
    pivot = pivot.reindex(columns=AGE_GROUPS, fill_value=0)
    
    # Tính TỔNG theo hàng (tổng tất cả nhóm tuổi của nguồn đó trong đợt đó)
    pivot["TỔNG"] = pivot[AGE_GROUPS].sum(axis=1)
    
    # Consolidated groups
    # HS cấp 2 + HS cấp 3
    pivot["HS cấp 2+3"] = pivot.get("Học sinh cấp 2", 0) + pivot.get("Học sinh cấp 3", 0)
    
    # SV + Người đi làm dưới 45
    pivot["SV + DL <45"] = pivot.get("Sinh viên", 0) + pivot.get("Người đi làm dưới 45 tuổi", 0)
    
    # Khác: HS1 + 45-60 + 60+ + Chưa điền
    pivot["Khác (HS1+45-60+60+Chưa điền)"] = (
        pivot.get("Học sinh cấp 1", 0) +
        pivot.get("Người đi làm từ 45 đến dưới 60 tuổi", 0) +
        pivot.get("Người trên 60 tuổi", 0) +
        pivot.get("SALE CHƯA ĐIỀN & ĐIỀN TRÙNG", 0)
    )
    
    # Reset index để đưa ĐỢT HỌC THỬ và Nguồn thành các cột bình thường
    result_df = pivot.reset_index()
    result_df.columns.name = None
    result_df.insert(0, 'Thời gian xuất data', fetch_time)
    
    result_df = result_df[cols_order]
    
    # Round all numeric columns to 2 decimals
    numeric_cols = result_df.select_dtypes(include=['number']).columns
    result_df[numeric_cols] = result_df[numeric_cols].round(2)
    
    return result_df


def aggregate_report_3_rows(df_rows, time_val, dot_val, nguon_val):
    """Tính tổng các cột cho Báo cáo 3 từ một DataFrame con và trả về 1 dict đại diện cho dòng tổng."""
    from data_processing import AGE_GROUPS
    
    row_dict = {
        'Thời gian xuất data': time_val,
        'ĐỢT HỌC THỬ': dot_val,
        'Nguồn': nguon_val,
    }
    
    for g in AGE_GROUPS:
        row_dict[g] = round(float(df_rows[g].sum()), 2) if g in df_rows else 0.0
        
    tot = round(float(df_rows['TỔNG'].sum()), 2) if 'TỔNG' in df_rows else 0.0
    row_dict['TỔNG'] = tot
    
    # Consolidated groups
    row_dict['HS cấp 2+3'] = round(float(df_rows['HS cấp 2+3'].sum()), 2) if 'HS cấp 2+3' in df_rows else 0.0
    row_dict['SV + DL <45'] = round(float(df_rows['SV + DL <45'].sum()), 2) if 'SV + DL <45' in df_rows else 0.0
    row_dict['Khác (HS1+45-60+60+Chưa điền)'] = (
        round(float(df_rows['Khác (HS1+45-60+60+Chưa điền)'].sum()), 2)
        if 'Khác (HS1+45-60+60+Chưa điền)' in df_rows else 0.0
    )
    
    return row_dict


def prepare_excel_report_3(df_report_3):
    """Chuẩn bị DataFrame hoàn chỉnh cho Report 3 để xuất Excel (bao gồm dòng tổng đợt, tổng cộng và các cột %)."""
    if df_report_3.empty:
        return df_report_3
        
    df_excel = df_report_3.copy()
    from data_processing import AGE_GROUPS
    
    result_parts = []
    
    for dot_name in df_excel['ĐỢT HỌC THỬ'].unique():
        group = df_excel[df_excel['ĐỢT HỌC THỬ'] == dot_name].copy()
        result_parts.append(group)
        
        time_val = group['Thời gian xuất data'].iloc[0] if len(group) > 0 else ''
        subtotal = aggregate_report_3_rows(group, time_val, f'TỔNG {dot_name}', '')
        result_parts.append(pd.DataFrame([subtotal]))
        
    df_result = pd.concat(result_parts, ignore_index=True)
    
    # Tính dòng TỔNG CỘNG
    detail_mask = ~df_result['ĐỢT HỌC THỬ'].astype(str).str.startswith('TỔNG ')
    detail_rows = df_result[detail_mask]
    time_val = df_result['Thời gian xuất data'].iloc[0] if len(df_result) > 0 else ''
    total_row = aggregate_report_3_rows(detail_rows, time_val, 'TỔNG CỘNG', '')
    
    df_result = pd.concat([df_result, pd.DataFrame([total_row])], ignore_index=True)
    
    # Tính các cột % cho Excel
    for g in AGE_GROUPS:
        df_result[f"{g} (%)"] = (df_result[g] / df_result['TỔNG'].replace(0, 1) * 100).where(df_result['TỔNG'] > 0, 0).round(2)
        
    df_result['HS cấp 2+3 (%)'] = (df_result['HS cấp 2+3'] / df_result['TỔNG'].replace(0, 1) * 100).where(df_result['TỔNG'] > 0, 0).round(2)
    df_result['SV + DL <45 (%)'] = (df_result['SV + DL <45'] / df_result['TỔNG'].replace(0, 1) * 100).where(df_result['TỔNG'] > 0, 0).round(2)
    df_result['Khác (HS1+45-60+60+Chưa điền) (%)'] = (df_result['Khác (HS1+45-60+60+Chưa điền)'] / df_result['TỔNG'].replace(0, 1) * 100).where(df_result['TỔNG'] > 0, 0).round(2)
    
    return df_result
