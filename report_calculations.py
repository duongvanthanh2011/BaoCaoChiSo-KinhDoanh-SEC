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
from data_processing import expand_report_3_sources_with_weights
from time_utils import format_fetch_time


REPORT_2_ADVISOR_COLUMN = 'Số CVHT đi làm'
REPORT_2_AVERAGE_COLUMN = 'Data trung bình/ngày/CVHT'


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
            # "Tổng số Data" là số bản ghi, không phụ thuộc Mã KH có hay không.
            Count=("SAI SỐ - SAI ĐỐI TƯỢNG", "size"),
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


def expand_weighted_sources(
    df_filtered,
    extra_columns=None,
    source_weights_column="_sources_with_weights",
):
    """
    Mở rộng _sources_with_weights thành từng dòng riêng biệt theo trọng số.
    Dùng chung cho Báo cáo 2 và Báo cáo 3 để tránh lặp logic.

    Args:
        df_filtered: DataFrame đã lọc, chứa cột trọng số nguồn.
        extra_columns: Dict {tên_cột_nguồn: giá_trị_mặc_định} cho các cột bổ sung
                       (ví dụ {"Nhóm tuổi": "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG"}).
        source_weights_column: Tên cột chứa danh sách (nguồn, trọng số).

    Returns:
        pd.DataFrame với các cột: ĐỢT HỌC THỬ, Nguồn, Weight, + extra_columns.
    """
    extra_columns = extra_columns or {}
    rows = []
    for _, row in df_filtered.iterrows():
        sources_weights = row.get(source_weights_column)
        if not isinstance(sources_weights, list):
            sources_weights = [("Khác", 1.0)]

        dot = row.get("ĐỢT HỌC THỬ", "Chưa xác định")
        if not isinstance(dot, str) or not dot.strip():
            dot = "Chưa xác định"

        # Lấy giá trị các cột bổ sung từ row gốc
        extra_vals = {}
        for col_name, default_val in extra_columns.items():
            val = row.get(col_name)
            if not isinstance(val, str) or not val.strip():
                val = default_val
            extra_vals[col_name] = val

        for source_classified, weight in sources_weights:
            entry = {
                "ĐỢT HỌC THỬ": dot,
                "Nguồn": source_classified,
                "Weight": weight,
            }
            entry.update(extra_vals)
            rows.append(entry)

    return pd.DataFrame(rows)


def compute_report_2(df_filtered):
    """
    Tính toán Báo cáo 2: Theo Đợt học thử & Nguồn khách hàng.
    Sử dụng logic phân loại nguồn và chia trọng số 1/N.
    """
    cols_order = [
        'Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Nguồn',
        'Tổng data chạy được', 'Data trùng', 'Tổng data cần liên hệ',
        'Data vào nhóm Zalo', 'Data order', REPORT_2_AVERAGE_COLUMN,
        'Tỷ lệ data thực tế/data order'
    ]

    if df_filtered.empty:
        return pd.DataFrame(columns=cols_order)

    fetch_time = st.session_state.get("fetch_time") or format_fetch_time()

    expanded_df = expand_weighted_sources(df_filtered)
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
    result_2[REPORT_2_AVERAGE_COLUMN] = 0.0
    result_2['Tỷ lệ data thực tế/data order'] = 0.0

    result_2 = result_2[cols_order]

    return result_2


# ==========================================
# CÁC HÀM TRỢ GIÚP XUẤT FILE EXCEL CHO PYTHON
# ==========================================

def compute_excel_percentages(df_excel):
    """
    Tính toán tỷ lệ phần trăm động trên DataFrame phục vụ xuất Excel.
    Tái sử dụng chung để tránh lặp logic toán học.
    """
    tot = pd.to_numeric(df_excel['Tổng số Data'], errors='coerce')
    base = pd.to_numeric(df_excel['Tổng số data trừ sai số'], errors='coerce')

    def safe_percentage(numerator, denominator):
        """Chỉ tính phần trăm khi mẫu số dương; tránh NaN và +/-inf."""
        numerator = pd.to_numeric(numerator, errors='coerce')
        valid_denominator = denominator.where(denominator > 0)
        return (numerator / valid_denominator * 100).fillna(0.0)

    df_excel['% sai số-sai đối tượng/ Tổng data đã chia'] = safe_percentage(df_excel['Sai Số - Sai Đối Tượng'], tot)
    df_excel['% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng'] = safe_percentage(df_excel['Tiềm Năng Chưa Gọi'], base)
    df_excel['% data Chưa trao đổi được + autocall / Tổng data đã chia trừ sai số-sai đối tượng'] = safe_percentage(df_excel['Data Chưa Trao Đổi + Auto Call'], base)
    df_excel['% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng'] = safe_percentage(df_excel['Data Trao Đổi Được'], base)
    df_excel['% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng'] = safe_percentage(df_excel['Data Tiềm Năng'], base)
    df_excel['% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng'] = safe_percentage(df_excel['Data Cọc Chốt'], base)

    default_tong_coc = pd.Series(0, index=df_excel.index, dtype=float)
    tong_coc = pd.to_numeric(df_excel.get('Tổng Cọc Học Thử', default_tong_coc), errors='coerce').fillna(0)
    df_excel['% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng'] = safe_percentage(tong_coc, base)
    return df_excel


def build_excel_with_subtotals(df, aggregate_fn, pre_process_group_fn=None):
    """
    Xây dựng DataFrame Excel hoàn chỉnh với dòng tổng theo đợt và dòng tổng cộng.
    Dùng chung cho prepare_excel_report_1, _2, _3 để tránh lặp cấu trúc loop+concat.

    Args:
        df: DataFrame gốc (đã copy).
        aggregate_fn: Callable(group_df, time_val, dot_label, nguon_label) → dict (dòng tổng).
        pre_process_group_fn: Optional Callable(group_df) → group_df. Xử lý group trước khi append
                              (ví dụ: xóa Zalo/Order ở Report 2).

    Returns:
        pd.DataFrame hoàn chỉnh với subtotal rows và grand total row.
    """
    if df.empty:
        return df

    result_parts = []
    for dot_name in df['ĐỢT HỌC THỬ'].unique():
        group = df[df['ĐỢT HỌC THỬ'] == dot_name].copy()

        # Xử lý trước nếu cần (ví dụ: ẩn cột ở dòng chi tiết)
        display_group = pre_process_group_fn(group) if pre_process_group_fn else group
        result_parts.append(display_group)

        time_val = group['Thời gian xuất data'].iloc[0] if len(group) > 0 else ''
        subtotal = aggregate_fn(group, time_val, f'TỔNG {dot_name}', '')
        result_parts.append(pd.DataFrame([subtotal]))

    df_result = pd.concat(result_parts, ignore_index=True)

    # Tính dòng TỔNG CỘNG từ dòng chi tiết (không tính dòng tổng đợt)
    detail_mask = ~df_result['ĐỢT HỌC THỬ'].astype(str).str.startswith('TỔNG ')
    detail_rows = df_result[detail_mask]
    time_val = df_result['Thời gian xuất data'].iloc[0] if len(df_result) > 0 else ''
    total_row = aggregate_fn(detail_rows, time_val, 'TỔNG CỘNG', '')

    df_result = pd.concat([df_result, pd.DataFrame([total_row])], ignore_index=True)
    return df_result


def _aggregate_report_1_row(dot_manual_df=None):
    """Trả về một hàm aggregate cho Report 1 (closure chứa dot_manual_df)."""
    def aggregate_fn(group, time_val, dot_label, nguon_label):
        sub_data = group['Tổng số Data'].sum()
        sub_sai_so = group['Sai Số - Sai Đối Tượng'].sum()
        sub_base = sub_data - sub_sai_so
        sub_tn_chua_goi = group['Tiềm Năng Chưa Gọi'].sum()
        sub_chua_trao_doi_autocall = group['Data Chưa Trao Đổi + Auto Call'].sum()
        sub_trao_doi = group['Data Trao Đổi Được'].sum()
        sub_tiem_nang = group['Data Tiềm Năng'].sum()
        sub_coc_chot = group['Data Cọc Chốt'].sum()

        # Lấy giá trị nhập tay cho đợt/tổng cộng
        coc_khac = 0
        tong_coc_ht = 0
        # Tên đợt thực tế (bỏ prefix "TỔNG ")
        real_dot = dot_label.replace('TỔNG ', '') if dot_label.startswith('TỔNG ') else None
        if dot_manual_df is not None and not dot_manual_df.empty:
            if dot_label == 'TỔNG CỘNG':
                coc_khac = int(dot_manual_df['Cọc Khác'].sum())
                tong_coc_ht = int(dot_manual_df['Tổng Cọc Học Thử'].sum())
            elif real_dot:
                m_row = dot_manual_df[dot_manual_df['ĐỢT HỌC THỬ'] == real_dot]
                if not m_row.empty:
                    coc_khac = int(m_row['Cọc Khác'].iloc[0])
                    tong_coc_ht = int(m_row['Tổng Cọc Học Thử'].iloc[0])

        return {
            'Thời gian xuất data': time_val,
            'ĐỢT HỌC THỬ': dot_label,
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
    return aggregate_fn


def prepare_excel_report_1(df_edited, dot_manual_df=None):
    """Tính toán bảng hoàn chỉnh gồm phần trăm, dòng tổng đợt và dòng tổng cộng cho Report 1 (dùng cho download Excel)."""
    df_excel = df_edited.copy()

    # Xóa giá trị Cọc Khác và Tổng Cọc Học Thử ở cấp người phụ trách
    # (giá trị này thuộc cấp đợt, sẽ hiển thị ở dòng tổng đợt)
    df_excel['Cọc Khác'] = 0
    df_excel['Tổng Cọc Học Thử'] = 0

    df_excel = compute_excel_percentages(df_excel)

    if df_excel.empty:
        return df_excel

    return build_excel_with_subtotals(
        df_excel,
        aggregate_fn=_aggregate_report_1_row(dot_manual_df)
    )


def calculate_report_2_average_metrics(df_rows, dot_manual_df=None):
    """
    Tính Data trung bình/ngày/CVHT theo từng đợt và trung bình các đợt hợp lệ.

    Đợt có Số CVHT đi làm <= 0 nhận giá trị 0 và không tham gia grand average.
    """
    if df_rows is None or df_rows.empty:
        return {}, 0.0

    advisor_by_dot = {}
    if dot_manual_df is not None and not dot_manual_df.empty:
        for _, row in dot_manual_df.iterrows():
            dot_name = str(row.get('ĐỢT HỌC THỬ', ''))
            advisor_count = pd.to_numeric(row.get(REPORT_2_ADVISOR_COLUMN, 0), errors='coerce')
            advisor_by_dot[dot_name] = int(advisor_count) if pd.notna(advisor_count) and advisor_count > 0 else 0

    data_by_dot = (
        df_rows.assign(
            _dot_key=df_rows['ĐỢT HỌC THỬ'].astype(str),
            _total_data=pd.to_numeric(df_rows['Tổng data chạy được'], errors='coerce').fillna(0.0),
        )
        .groupby('_dot_key', sort=False)['_total_data']
        .sum()
    )

    averages_by_dot = {}
    valid_averages = []
    for dot_name, total_data in data_by_dot.items():
        advisor_count = advisor_by_dot.get(dot_name, 0)
        average_value = float(total_data) / advisor_count if advisor_count > 0 else 0.0
        averages_by_dot[dot_name] = average_value
        if advisor_count > 0:
            valid_averages.append(average_value)

    grand_average = sum(valid_averages) / len(valid_averages) if valid_averages else 0.0
    return averages_by_dot, grand_average


def aggregate_report_2_rows(
    df_rows,
    time_val,
    dot_val,
    nguon_val,
    dot_manual_values=None,
    data_average_value=None,
):
    """Tính tổng các cột cho Báo cáo 2 từ một DataFrame con và trả về 1 dict đại diện cho dòng tổng."""
    tot_data = round(float(df_rows['Tổng data chạy được'].sum()), 2)
    tot_trung = int(df_rows['Data trùng'].sum()) if 'Data trùng' in df_rows else 0
    tot_lien_he = round(tot_data + tot_trung, 2)
    
    if dot_manual_values:
        tot_zalo = int(dot_manual_values.get('Data vào nhóm Zalo', 0))
        tot_order = int(dot_manual_values.get('Data order', 0))
    else:
        tot_zalo = int(df_rows['Data vào nhóm Zalo'].sum()) if 'Data vào nhóm Zalo' in df_rows else 0
        tot_order = int(df_rows['Data order'].sum()) if 'Data order' in df_rows else 0

    if data_average_value is None:
        data_average_value = (
            float(pd.to_numeric(df_rows[REPORT_2_AVERAGE_COLUMN], errors='coerce').fillna(0.0).sum())
            if REPORT_2_AVERAGE_COLUMN in df_rows else 0.0
        )

    return {
        'Thời gian xuất data': time_val,
        'ĐỢT HỌC THỬ': dot_val,
        'Nguồn': nguon_val,
        'Tổng data chạy được': tot_data,
        'Data trùng': tot_trung,
        'Tổng data cần liên hệ': tot_lien_he,
        'Data vào nhóm Zalo': tot_zalo,
        'Data order': tot_order,
        REPORT_2_AVERAGE_COLUMN: float(data_average_value),
        'Tỷ lệ data thực tế/data order': round(tot_data / tot_order * 100, 2) if tot_order else 0.0,
    }

def _get_dot_manual_values(dot_manual_df, dot_name):
    """Trích xuất giá trị nhập tay cho một đợt cụ thể từ dot_manual_df."""
    if dot_manual_df is None or dot_manual_df.empty:
        return None
    m_row = dot_manual_df[dot_manual_df['ĐỢT HỌC THỬ'] == dot_name]
    if m_row.empty:
        return None
    return {
        'Data vào nhóm Zalo': int(m_row['Data vào nhóm Zalo'].iloc[0]),
        'Data order': int(m_row['Data order'].iloc[0]),
        REPORT_2_ADVISOR_COLUMN: int(m_row[REPORT_2_ADVISOR_COLUMN].iloc[0]),
    }


def _aggregate_report_2_row_factory(dot_manual_df=None):
    """Trả về aggregate_fn cho Report 2 (closure chứa dot_manual_df)."""
    def aggregate_fn(group, time_val, dot_label, nguon_label):
        real_dot = dot_label.replace('TỔNG ', '') if dot_label.startswith('TỔNG ') else None
        averages_by_dot, grand_average = calculate_report_2_average_metrics(group, dot_manual_df)
        if dot_label == 'TỔNG CỘNG':
            dot_vals = {
                'Data vào nhóm Zalo': int(dot_manual_df['Data vào nhóm Zalo'].sum()) if dot_manual_df is not None and not dot_manual_df.empty else 0,
                'Data order': int(dot_manual_df['Data order'].sum()) if dot_manual_df is not None and not dot_manual_df.empty else 0,
            }
            data_average_value = grand_average
        elif real_dot:
            dot_vals = _get_dot_manual_values(dot_manual_df, real_dot)
            data_average_value = averages_by_dot.get(str(real_dot), 0.0)
        else:
            dot_vals = None
            data_average_value = 0.0
        return aggregate_report_2_rows(
            group,
            time_val,
            dot_label,
            nguon_label,
            dot_manual_values=dot_vals,
            data_average_value=data_average_value,
        )
    return aggregate_fn


def _hide_dot_level_cols_r2(group):
    """Ẩn các cột chỉ hiển thị ở cấp đợt (Zalo, Order, BQ, Tỷ lệ) ở dòng chi tiết nguồn."""
    display = group.copy()
    display['Data vào nhóm Zalo'] = None
    display['Data order'] = None
    display[REPORT_2_AVERAGE_COLUMN] = None
    display['Tỷ lệ data thực tế/data order'] = None
    return display


def prepare_excel_report_2(df_edited, dot_manual_df=None):
    """Tính toán bảng hoàn chỉnh gồm phần trăm và dòng tổng cộng cho Report 2 (dùng cho download Excel)."""
    df_excel = df_edited.copy()
    if df_excel.empty:
        return df_excel

    return build_excel_with_subtotals(
        df_excel,
        aggregate_fn=_aggregate_report_2_row_factory(dot_manual_df),
        pre_process_group_fn=_hide_dot_level_cols_r2
    )


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

    # Dữ liệu đang có trong session từ trước khi nâng cấp có thể chưa có cột này.
    report_3_source_column = "_report_3_sources_with_weights"
    df_report_3 = df_filtered.copy()
    if report_3_source_column not in df_report_3.columns:
        source_details = df_report_3.get(
            "account_source_details",
            pd.Series(index=df_report_3.index, dtype=object),
        )
        df_report_3[report_3_source_column] = source_details.apply(
            expand_report_3_sources_with_weights
        )

    expanded_df = expand_weighted_sources(
        df_report_3,
        extra_columns={"Nhóm tuổi": "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG"},
        source_weights_column=report_3_source_column,
    )
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
    pivot["HS cấp 2+3"] = pivot.get("Học sinh cấp 2", 0) + pivot.get("Học sinh cấp 3", 0)
    pivot["SV + DL <45"] = pivot.get("Sinh viên", 0) + pivot.get("Người đi làm dưới 45 tuổi", 0)
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
    
    df_result = build_excel_with_subtotals(
        df_excel,
        aggregate_fn=aggregate_report_3_rows
    )
    
    # Tính các cột % cho Excel
    for g in AGE_GROUPS:
        df_result[f"{g} (%)"] = (df_result[g] / df_result['TỔNG'].replace(0, 1) * 100).where(df_result['TỔNG'] > 0, 0).round(2)
        
    df_result['HS cấp 2+3 (%)'] = (df_result['HS cấp 2+3'] / df_result['TỔNG'].replace(0, 1) * 100).where(df_result['TỔNG'] > 0, 0).round(2)
    df_result['SV + DL <45 (%)'] = (df_result['SV + DL <45'] / df_result['TỔNG'].replace(0, 1) * 100).where(df_result['TỔNG'] > 0, 0).round(2)
    df_result['Khác (HS1+45-60+60+Chưa điền) (%)'] = (df_result['Khác (HS1+45-60+60+Chưa điền)'] / df_result['TỔNG'].replace(0, 1) * 100).where(df_result['TỔNG'] > 0, 0).round(2)
    
    return df_result
