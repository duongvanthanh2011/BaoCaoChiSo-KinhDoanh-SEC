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

    fetch_time = st.session_state.get("fetch_time") or format_fetch_time()

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

    fetch_time = st.session_state.get("fetch_time") or format_fetch_time()

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
                'Data Trao Đổi Được': sub_trao_doi,
                'Data Tiềm Năng': sub_tiem_nang,
                'Data Cọc Chốt': sub_coc_chot,
                'Tổng số Data': sub_data,
                'Tổng số data trừ sai số': sub_base,
                'Cọc Khác': coc_khac,
                'Tổng Cọc Học Thử': tong_coc_ht,
                '% sai số-sai đối tượng/ Tổng data đã chia': (sub_sai_so / sub_data * 100) if sub_data else 0,
                '% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng': (sub_tn_chua_goi / sub_base * 100) if sub_base else 0,
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
            'Data Trao Đổi Được': tot_trao_doi,
            'Data Tiềm Năng': tot_tiem_nang,
            'Data Cọc Chốt': tot_coc_chot,
            'Tổng số Data': tot_data,
            'Tổng số data trừ sai số': tot_base,
            'Cọc Khác': total_coc_khac,
            'Tổng Cọc Học Thử': total_tong_coc,
            '% sai số-sai đối tượng/ Tổng data đã chia': (tot_sai_so / tot_data * 100) if tot_data else 0,
            '% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng': (tot_tn_chua_goi / tot_base * 100) if tot_base else 0,
            '% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng': (tot_trao_doi / tot_base * 100) if tot_base else 0,
            '% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng': (tot_tiem_nang / tot_base * 100) if tot_base else 0,
            '% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng': (tot_coc_chot / tot_base * 100) if tot_base else 0,
            '% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng': (total_tong_coc / tot_base * 100) if tot_base else 0,
        }
        
        df_excel = pd.concat([df_excel, pd.DataFrame([total_row])], ignore_index=True)

    return df_excel


def prepare_excel_report_2(df_edited, dot_manual_df=None):
    """Tính toán bảng hoàn chỉnh gồm phần trăm và dòng tổng cộng cho Report 2 (dùng cho download Excel)."""
    df_excel = df_edited.copy()

    if dot_manual_df is not None and not dot_manual_df.empty:
        # Data order thuộc cấp đợt, không thuộc từng nguồn chi tiết.
        df_excel['Data order'] = 0
        df_excel['50% data order'] = 0.0
        df_excel['% data đã chia / 50% data order'] = 0.0
        df_excel['% data đã chia / data order'] = 0.0

        result_parts = []
        for dot_name in df_excel['ĐỢT HỌC THỬ'].unique():
            group = df_excel[df_excel['ĐỢT HỌC THỬ'] == dot_name]
            result_parts.append(group)

            data_order = 0
            dot_row = dot_manual_df[dot_manual_df['ĐỢT HỌC THỬ'] == dot_name]
            if not dot_row.empty:
                data_order = int(dot_row['Data order'].iloc[0])

            sub_data = int(group['Tổng số Data'].sum())
            half_order = data_order * 0.5
            subtotal = {
                'Thời gian xuất data': group['Thời gian xuất data'].iloc[0],
                'ĐỢT HỌC THỬ': f'TỔNG {dot_name}',
                'Nguồn': '',
                'Tổng số Data': sub_data,
                'Data order': data_order,
                '50% data order': half_order,
                '% data đã chia / 50% data order': (sub_data / half_order * 100) if half_order else 0,
                '% data đã chia / data order': (sub_data / data_order * 100) if data_order else 0,
            }
            result_parts.append(pd.DataFrame([subtotal]))

        df_excel = pd.concat(result_parts, ignore_index=True)

        detail_mask = ~df_excel['ĐỢT HỌC THỬ'].astype(str).str.startswith('TỔNG ')
        detail_rows = df_excel[detail_mask]
        total_data = int(detail_rows['Tổng số Data'].sum())
        total_order = int(dot_manual_df['Data order'].sum())
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
