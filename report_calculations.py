"""
report_calculations.py — Module tính toán số liệu và chuẩn bị dữ liệu Excel
Chứa:
- Thêm cột chỉ báo nhãn
- Tính toán dữ liệu tổng hợp cho Báo cáo 1, 2, 3, 4
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
from data_processing import (
    AGE_GROUPS,
    REPORT_3_CONSOLIDATED_COLUMNS,
    REPORT_3_SCHOOL_WORKER_COLUMN,
    REPORT_3_STUDENT_YOUNG_COLUMN,
    REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN,
    REPORT_4_ONL_ROWS,
    REPORT_4_OFF_ROWS,
    classify_age_group,
    expand_report_3_sources_with_weights,
    expand_report_4_sources_with_weights,
)
from time_utils import format_fetch_time


REPORT_2_ADVISOR_COLUMN = 'Số CVHT đi làm'
REPORT_2_AVERAGE_COLUMN = 'Data trung bình/ngày/CVHT'
COC_COL_SUFFIX = " (Cọc Chốt)"


def get_cached_base_reports(raw_df, selected_sessions, revision):
    """Một bộ kết quả nền trong từng phiên; input không làm tính lại dữ liệu CRM."""
    sessions = tuple(sorted(set(str(s) for s in selected_sessions)))
    key = (revision, id(raw_df), sessions, st.session_state.get('fetch_time'))
    cached = st.session_state.get('_base_reports_cache')
    if cached is None or cached['key'] != key:
        filtered = raw_df[raw_df['ĐỢT HỌC THỬ'].isin(sessions)].copy() if sessions else raw_df.copy()
        filtered = add_indicator_columns(filtered)
        results = (
            compute_report_1(filtered),
            compute_report_2(filtered),
            compute_report_3(filtered),
            compute_report_4(filtered),
            compute_report_5(filtered),
        )
        cached = {'key': key, 'results': results}
        st.session_state['_base_reports_cache'] = cached
    return tuple(
        r.copy() if isinstance(r, pd.DataFrame) else {k: v.copy() for k, v in r.items()}
        for r in cached['results']
    )


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
    numeric_columns=None,
    source_weights_column="_sources_with_weights",
):
    """
    Mở rộng _sources_with_weights thành từng dòng riêng biệt theo trọng số.
    Dùng chung cho Báo cáo 2 và Báo cáo 3 để tránh lặp logic.

    Args:
        df_filtered: DataFrame đã lọc, chứa cột trọng số nguồn.
        extra_columns: Dict {tên_cột_nguồn: giá_trị_mặc_định} cho các cột bổ sung
                       (ví dụ {"Nhóm tuổi": "Chưa điền"}).
        numeric_columns: Danh sách cột số copy nguyên giá trị từ dòng gốc vào dòng expand
                         (mặc định 0 nếu thiếu/không phải số).
        source_weights_column: Tên cột chứa danh sách (nguồn, trọng số).

    Returns:
        pd.DataFrame với các cột: ĐỢT HỌC THỬ, Nguồn, Weight, + extra_columns + numeric_columns.
    """
    extra_columns = extra_columns or {}
    numeric_columns = numeric_columns or []
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

        for num_col in numeric_columns:
            val = row.get(num_col)
            try:
                val = float(val) if pd.notna(val) else 0.0
            except (ValueError, TypeError):
                val = 0.0
            extra_vals[num_col] = val

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
    Bao gồm 7 nhóm tuổi, TỔNG, 3 nhóm tổng hợp và 11 cột Cọc Chốt tương ứng.
    
    Returns:
        pd.DataFrame với các cột:
        - Thời gian xuất data
        - ĐỢT HỌC THỬ
        - Nguồn
        - Các nhóm tuổi (7 cột)
        - TỔNG
        - Ba nhóm tổng hợp theo yêu cầu nghiệp vụ
        - 11 cột cọc chốt tương ứng (sẽ ẩn trên AgGrid)
    """
    coc_columns = [
        f"{c}{COC_COL_SUFFIX}"
        for c in AGE_GROUPS + ['TỔNG'] + REPORT_3_CONSOLIDATED_COLUMNS
    ]
    cols_order = (
        ['Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Nguồn']
        + AGE_GROUPS
        + ['TỔNG']
        + REPORT_3_CONSOLIDATED_COLUMNS
        + coc_columns
    )

    if df_filtered.empty:
        return pd.DataFrame(columns=cols_order)
    
    fetch_time = st.session_state.get("fetch_time") or format_fetch_time()

    # Dữ liệu đang có trong session từ trước khi nâng cấp có thể chưa có cột này.
    report_3_source_column = "_report_3_sources_with_weights"
    df_report_3 = df_filtered.copy()

    # Fallback an toàn: nếu "Data_coc_chot" chưa có trong df_report_3
    if "Data_coc_chot" not in df_report_3.columns:
        if "Mối quan hệ" in df_report_3.columns:
            df_report_3["Data_coc_chot"] = df_report_3["Mối quan hệ"].isin(COC_CHOT_LABELS).astype(int)
        elif "relation_name" in df_report_3.columns:
            df_report_3["Data_coc_chot"] = df_report_3["relation_name"].isin(COC_CHOT_LABELS).astype(int)
        else:
            df_report_3["Data_coc_chot"] = 0

    # Luôn phân loại lại từ description để session cũ không giữ nhóm tuổi cũ.
    # Nếu không còn description, chuẩn hóa cột Nhóm tuổi hiện có theo schema mới.
    if "description" in df_report_3.columns:
        df_report_3["Nhóm tuổi"] = df_report_3["description"].apply(classify_age_group)
    else:
        age_values = df_report_3.get(
            "Nhóm tuổi",
            pd.Series(index=df_report_3.index, dtype=object),
        )
        df_report_3["Nhóm tuổi"] = age_values.apply(classify_age_group)

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
        extra_columns={"Nhóm tuổi": "Chưa điền"},
        numeric_columns=["Data_coc_chot"],
        source_weights_column=report_3_source_column,
    )
    if expanded_df.empty:
        return pd.DataFrame(columns=cols_order)
    
    # Trọng số Cọc Chốt: Weight_coc = Weight * Data_coc_chot
    expanded_df["Weight_coc"] = expanded_df["Weight"] * expanded_df["Data_coc_chot"]

    # Pivot table: sum weights và coc_weights by (ĐỢT HỌC THỬ, Nguồn, Nhóm tuổi) trong 1 lần groupby
    grouped = (
        expanded_df
        .groupby(["ĐỢT HỌC THỬ", "Nguồn", "Nhóm tuổi"])[["Weight", "Weight_coc"]]
        .sum()
    )
    
    pivot = grouped["Weight"].unstack(fill_value=0).reindex(columns=AGE_GROUPS, fill_value=0)
    pivot_coc = grouped["Weight_coc"].unstack(fill_value=0).reindex(columns=AGE_GROUPS, fill_value=0)
    
    # Đổi tên các cột pivot_coc thành f"{g}{COC_COL_SUFFIX}"
    pivot_coc = pivot_coc.rename(columns={g: f"{g}{COC_COL_SUFFIX}" for g in AGE_GROUPS})

    # Tính TỔNG theo hàng
    pivot["TỔNG"] = pivot[AGE_GROUPS].sum(axis=1)
    coc_age_cols = [f"{g}{COC_COL_SUFFIX}" for g in AGE_GROUPS]
    pivot_coc[f"TỔNG{COC_COL_SUFFIX}"] = pivot_coc[coc_age_cols].sum(axis=1)
    
    # Các nhóm tổng hợp mới (thường)
    pivot[REPORT_3_STUDENT_YOUNG_COLUMN] = (
        pivot.get("Sinh Viên", 0)
        + pivot.get("Người đi làm dưới 35 Tuổi", 0)
    )
    pivot[REPORT_3_SCHOOL_WORKER_COLUMN] = (
        pivot.get("Học sinh cấp 2", 0)
        + pivot.get("Học sinh cấp 3", 0)
        + pivot.get("Người đi làm từ 35 - 50 Tuổi", 0)
    )
    pivot[REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN] = (
        pivot[REPORT_3_STUDENT_YOUNG_COLUMN]
        + pivot.get("Chưa điền", 0)
    )

    # Các nhóm tổng hợp mới (Cọc Chốt - cùng công thức trên các cột coc)
    pivot_coc[f"{REPORT_3_STUDENT_YOUNG_COLUMN}{COC_COL_SUFFIX}"] = (
        pivot_coc.get(f"Sinh Viên{COC_COL_SUFFIX}", 0)
        + pivot_coc.get(f"Người đi làm dưới 35 Tuổi{COC_COL_SUFFIX}", 0)
    )
    pivot_coc[f"{REPORT_3_SCHOOL_WORKER_COLUMN}{COC_COL_SUFFIX}"] = (
        pivot_coc.get(f"Học sinh cấp 2{COC_COL_SUFFIX}", 0)
        + pivot_coc.get(f"Học sinh cấp 3{COC_COL_SUFFIX}", 0)
        + pivot_coc.get(f"Người đi làm từ 35 - 50 Tuổi{COC_COL_SUFFIX}", 0)
    )
    pivot_coc[f"{REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN}{COC_COL_SUFFIX}"] = (
        pivot_coc[f"{REPORT_3_STUDENT_YOUNG_COLUMN}{COC_COL_SUFFIX}"]
        + pivot_coc.get(f"Chưa điền{COC_COL_SUFFIX}", 0)
    )

    # Ghép 2 pivot lại
    combined = pd.concat([pivot, pivot_coc], axis=1)

    # Reset index để đưa ĐỢT HỌC THỬ và Nguồn thành các cột bình thường
    result_df = combined.reset_index()
    result_df.columns.name = None
    result_df.insert(0, 'Thời gian xuất data', fetch_time)
    
    result_df = result_df[cols_order]
    
    return result_df


def aggregate_report_3_rows(df_rows, time_val, dot_val, nguon_val):
    """Tính tổng các cột cho Báo cáo 3 từ một DataFrame con và trả về 1 dict đại diện cho dòng tổng."""
    row_dict = {
        'Thời gian xuất data': time_val,
        'ĐỢT HỌC THỬ': dot_val,
        'Nguồn': nguon_val,
    }
    
    for g in AGE_GROUPS:
        row_dict[g] = round(float(df_rows[g].sum()), 2) if g in df_rows else 0.0
        
    tot = round(float(df_rows['TỔNG'].sum()), 2) if 'TỔNG' in df_rows else 0.0
    row_dict['TỔNG'] = tot
    
    for col in REPORT_3_CONSOLIDATED_COLUMNS:
        row_dict[col] = round(float(df_rows[col].sum()), 2) if col in df_rows else 0.0
    
    # 11 cột Cọc Chốt
    for col in AGE_GROUPS + ['TỔNG'] + REPORT_3_CONSOLIDATED_COLUMNS:
        coc_col = f"{col}{COC_COL_SUFFIX}"
        row_dict[coc_col] = round(float(df_rows[coc_col].sum()), 2) if coc_col in df_rows else 0.0

    return row_dict


def _format_r3_excel_cell(val, tong, coc_val, coc_tong):
    """
    Format ô Báo cáo 3 cho Excel theo dạng: 'num (pct%) / cocNum (cocPct%)'.
    - Số nguyên giữ nguyên không decimal, số lẻ làm tròn 2 chữ số thập phân.
    - % làm tròn 2 chữ số (ví dụ '10.00%').
    - Mẫu số tong <= 0 hoặc coc_tong <= 0 thì pct tương ứng = 0.00%.
    """
    try:
        v = float(val) if pd.notna(val) else 0.0
    except (ValueError, TypeError):
        v = 0.0
        
    try:
        t = float(tong) if pd.notna(tong) else 0.0
    except (ValueError, TypeError):
        t = 0.0

    try:
        cv = float(coc_val) if pd.notna(coc_val) else 0.0
    except (ValueError, TypeError):
        cv = 0.0
        
    try:
        ct = float(coc_tong) if pd.notna(coc_tong) else 0.0
    except (ValueError, TypeError):
        ct = 0.0

    v_str = str(int(v)) if v.is_integer() else f"{v:.2f}"
    pct = (v / t * 100) if t > 0 else 0.0

    cv_str = str(int(cv)) if cv.is_integer() else f"{cv:.2f}"
    coc_pct = (cv / ct * 100) if ct > 0 else 0.0

    return f"{v_str} ({pct:.2f}%) / {cv_str} ({coc_pct:.2f}%)"


def prepare_excel_report_3(df_report_3):
    """Chuẩn bị DataFrame hoàn chỉnh cho Report 3 để xuất Excel (bao gồm dòng tổng đợt, tổng cộng và gộp chuỗi cọc chốt)."""
    out_cols = (
        ['Thời gian xuất data', 'ĐỢT HỌC THỬ', 'Nguồn']
        + AGE_GROUPS
        + ['TỔNG']
        + REPORT_3_CONSOLIDATED_COLUMNS
    )
    if df_report_3.empty:
        return pd.DataFrame(columns=out_cols)
        
    df_excel = df_report_3.copy()
    
    df_result = build_excel_with_subtotals(
        df_excel,
        aggregate_fn=aggregate_report_3_rows
    )
    
    # Thu thập TỔNG và TỔNG (Cọc Chốt) của từng đợt và của TỔNG CỘNG
    dot_totals = {}
    grand_total_val = 0.0
    grand_total_coc = 0.0
    coc_tong_col = f"TỔNG{COC_COL_SUFFIX}"
    
    for _, r in df_result.iterrows():
        dot_str = str(r['ĐỢT HỌC THỬ'])
        if dot_str == 'TỔNG CỘNG':
            grand_total_val = float(r.get('TỔNG', 0.0))
            grand_total_coc = float(r.get(coc_tong_col, 0.0))
        elif dot_str.startswith('TỔNG '):
            dot_name = dot_str[len('TỔNG '):]
            dot_totals[dot_name] = {
                'total': float(r.get('TỔNG', 0.0)),
                'coc_total': float(r.get(coc_tong_col, 0.0)),
            }

    target_cols = AGE_GROUPS + REPORT_3_CONSOLIDATED_COLUMNS
    formatted_rows = []

    for _, row in df_result.iterrows():
        new_row = {
            'Thời gian xuất data': row.get('Thời gian xuất data', ''),
            'ĐỢT HỌC THỬ': row.get('ĐỢT HỌC THỬ', ''),
            'Nguồn': row.get('Nguồn', ''),
        }
        dot_str = str(row.get('ĐỢT HỌC THỬ', ''))
        row_total = float(row.get('TỔNG', 0.0))
        row_coc_total = float(row.get(coc_tong_col, 0.0))

        # Format 7 nhóm tuổi + 3 cột gộp
        for col in target_cols:
            col_coc = f"{col}{COC_COL_SUFFIX}"
            val = row.get(col, 0.0)
            coc_val = row.get(col_coc, 0.0)
            new_row[col] = _format_r3_excel_cell(val, row_total, coc_val, row_coc_total)

        # Format cột TỔNG
        if dot_str == 'TỔNG CỘNG':
            t_denom = row_total
            c_denom = row_coc_total
        elif dot_str.startswith('TỔNG '):
            t_denom = grand_total_val
            c_denom = grand_total_coc
        else:
            # Dòng chi tiết: theo đợt tương ứng
            dot_info = dot_totals.get(dot_str, {'total': 0.0, 'coc_total': 0.0})
            t_denom = dot_info['total']
            c_denom = dot_info['coc_total']

        new_row['TỔNG'] = _format_r3_excel_cell(row_total, t_denom, row_coc_total, c_denom)
        formatted_rows.append(new_row)

    return pd.DataFrame(formatted_rows)[out_cols]


# ==========================================
# TÍNH TOÁN BÁO CÁO 4: NGUỒN ONL / OFF / TỔNG
# ==========================================

REPORT_4_COLS = [
    'Thời gian xuất data',
    'Nguồn',
    'Tổng data',
    'Bill cọc',
    'Data/Bill',
    'Bill/Data (%)',
]


def _calc_r4_metrics(df_table, fetch_time):
    """Bổ sung Thời gian xuất data và tính Data/Bill, Bill/Data(%)."""
    df = df_table.copy()
    if 'Thời gian xuất data' not in df.columns:
        df.insert(0, 'Thời gian xuất data', fetch_time)
    else:
        df['Thời gian xuất data'] = fetch_time

    tot = pd.to_numeric(df['Tổng data'], errors='coerce').fillna(0.0)
    bill = pd.to_numeric(df['Bill cọc'], errors='coerce').fillna(0.0)

    df['Tổng data'] = tot.round(2)
    df['Bill cọc'] = bill.round(2)
    df['Data/Bill'] = (tot / bill.where(bill > 0)).fillna(0.0).round(2)
    df['Bill/Data (%)'] = (bill / tot.where(tot > 0) * 100).fillna(0.0).round(2)

    return df[REPORT_4_COLS]


def _merge_with_templates(rec_df, data_cols):
    """
    Tách rec_df theo cột 'Table' (onl/off), merge left với template cố định,
    cộng dồn tạo bảng Tổng. Dùng chung cho BC4 và BC5.

    Args:
        rec_df: DataFrame có cột 'Table' và 'Nguồn', cùng các data_cols.
        data_cols: List tên cột số cần group + sum.
    Returns:
        (onl_res, off_res, tong_res) — 3 DataFrame đã merge template và fill 0.
    """
    template = pd.DataFrame({'Nguồn': REPORT_4_ONL_ROWS})
    off_template = pd.DataFrame({'Nguồn': REPORT_4_OFF_ROWS})

    def _build_table(table_key, tmpl):
        if (
            not rec_df.empty
            and 'Table' in rec_df.columns
            and (rec_df['Table'] == table_key).any()
        ):
            grouped = (
                rec_df[rec_df['Table'] == table_key]
                .groupby('Nguồn', as_index=False)[data_cols]
                .sum()
            )
            result = tmpl.merge(grouped, on='Nguồn', how='left')
        else:
            result = tmpl.copy()
            for c in data_cols:
                result[c] = 0.0
        for c in data_cols:
            result[c] = pd.to_numeric(result.get(c), errors='coerce').fillna(0.0)
        return result

    onl_res = _build_table('onl', template)
    off_res = _build_table('off', off_template)

    combined = pd.concat([onl_res, off_res], ignore_index=True)
    tong_grouped = combined.groupby('Nguồn', as_index=False)[data_cols].sum()
    tong_res = template.merge(tong_grouped, on='Nguồn', how='left')
    for c in data_cols:
        tong_res[c] = pd.to_numeric(tong_res.get(c), errors='coerce').fillna(0.0)

    return onl_res, off_res, tong_res


def build_report_4_tables(df_filtered, fetch_time):
    """
    Trả về dict {'onl': df, 'off': df, 'tong': df} — mỗi df theo REPORT_4_COLS.
    Tổng hợp toàn bộ data trong bộ lọc (không group theo Đợt học thử).
    Hàm pure pandas, không phụ thuộc st.session_state (thuận tiện kiểm thử).
    """
    if df_filtered.empty:
        empty = pd.DataFrame(columns=REPORT_4_COLS)
        return {'onl': empty, 'off': empty.copy(), 'tong': empty.copy()}

    df_calc = df_filtered.copy()

    # Tương thích phiên cũ: tự sinh cột trọng số BC4 nếu thiếu
    if "_report_4_sources_with_weights" not in df_calc.columns:
        source_details = df_calc.get(
            "account_source_details",
            pd.Series(index=df_calc.index, dtype=object),
        )
        df_calc["_report_4_sources_with_weights"] = source_details.apply(
            expand_report_4_sources_with_weights
        )

    # Đảm bảo có cột chỉ báo Data_coc_chot
    if "Data_coc_chot" not in df_calc.columns:
        relation_series = df_calc.get("Mối quan hệ", pd.Series(index=df_calc.index, dtype=object)).fillna("")
        df_calc["Data_coc_chot"] = relation_series.isin(COC_CHOT_LABELS).astype(int)

    # Expand từng bản ghi theo nguồn khớp và trọng số
    records = []
    for _, row in df_calc.iterrows():
        is_coc = int(row.get("Data_coc_chot", 0))
        sources = row.get("_report_4_sources_with_weights", [])
        if isinstance(sources, list):
            for s_key, weight in sources:
                parts = s_key.split("::", 1)
                if len(parts) == 2:
                    records.append({
                        "Table": parts[0],
                        "Nguồn": parts[1],
                        "Weight": float(weight),
                        "BillWeight": float(weight) * is_coc,
                    })

    rec_df = pd.DataFrame(records)

    # Sử dụng hàm dùng chung để merge với template cố định
    onl_res, off_res, tong_res = _merge_with_templates(rec_df, ['Weight', 'BillWeight'])

    # Đổi tên cột chuẩn hóa và tính toán tỷ lệ
    onl_res = onl_res.rename(columns={'Weight': 'Tổng data', 'BillWeight': 'Bill cọc'})
    off_res = off_res.rename(columns={'Weight': 'Tổng data', 'BillWeight': 'Bill cọc'})
    tong_res = tong_res.rename(columns={'Weight': 'Tổng data', 'BillWeight': 'Bill cọc'})

    return {
        'onl': _calc_r4_metrics(onl_res, fetch_time),
        'off': _calc_r4_metrics(off_res, fetch_time),
        'tong': _calc_r4_metrics(tong_res, fetch_time),
    }


def compute_report_4(df_filtered):
    """Tính toán Báo cáo 4 từ DataFrame đã lọc (giao diện tương thích st.session_state)."""
    if df_filtered.empty:
        empty = pd.DataFrame(columns=REPORT_4_COLS)
        return {'onl': empty, 'off': empty.copy(), 'tong': empty.copy()}
    try:
        fetch_time = st.session_state.get("fetch_time") or format_fetch_time()
    except Exception:
        fetch_time = format_fetch_time()
    return build_report_4_tables(df_filtered, fetch_time)


def aggregate_report_4_rows(df_rows, time_val, nguon_val):
    """Tổng data/Bill cọc (round 2) + tính lại Data/Bill, Bill/Data(%) từ tổng — cho dòng TỔNG CỘNG."""
    tot = round(float(df_rows['Tổng data'].sum()), 2) if 'Tổng data' in df_rows and not df_rows.empty else 0.0
    bill = round(float(df_rows['Bill cọc'].sum()), 2) if 'Bill cọc' in df_rows and not df_rows.empty else 0.0
    data_per_bill = round(tot / bill, 2) if bill > 0 else 0.0
    bill_per_data = round(bill / tot * 100, 2) if tot > 0 else 0.0
    return {
        'Thời gian xuất data': time_val,
        'Nguồn': nguon_val,
        'Tổng data': tot,
        'Bill cọc': bill,
        'Data/Bill': data_per_bill,
        'Bill/Data (%)': bill_per_data,
    }


def prepare_excel_report_4(df_table):
    """Xây dựng DataFrame Excel hoàn chỉnh cho Báo cáo 4 với dòng tổng cộng."""
    if df_table.empty:
        return df_table
    df_excel = df_table.copy()
    time_val = df_excel['Thời gian xuất data'].iloc[0] if len(df_excel) > 0 else ''
    total_row = aggregate_report_4_rows(df_excel, time_val, 'TỔNG CỘNG')
    return pd.concat([df_excel, pd.DataFrame([total_row])], ignore_index=True)


# ==========================================
# TÍNH TOÁN BÁO CÁO 5: TRUYỀN THÔNG (NGUỒN ONL/OFF × NHÓM TUỔI)
# ==========================================

REPORT_5_METRIC_SUFFIXES = ['_Data', '_Bill cọc', '_Data/Bill', '_Bill/Data (%)']


def _r5_col_order():
    """Thứ tự cột chuẩn cho DataFrame của Báo cáo 5."""
    cols = ['Thời gian xuất data', 'Nguồn']
    for group in AGE_GROUPS + ['TỔNG']:
        for suffix in REPORT_5_METRIC_SUFFIXES:
            cols.append(f"{group}{suffix}")
    return cols


def build_report_5_tables(df_filtered, fetch_time):
    """
    Xây dựng 3 bảng Onl / Off / Tổng cho Báo cáo 5.
    Kết hợp phân loại nguồn regex BC4 với ma trận nhóm tuổi BC3.
    Mỗi bảng có cấu trúc: Nguồn × (nhóm tuổi × 4 chỉ số).

    Returns:
        dict {'onl': df, 'off': df, 'tong': df}
    """
    col_order = _r5_col_order()

    if df_filtered.empty:
        empty = pd.DataFrame(columns=col_order)
        return {'onl': empty, 'off': empty.copy(), 'tong': empty.copy()}

    df_calc = df_filtered.copy()

    # --- Fallback an toàn cho các cột cần thiết (tái sử dụng logic BC4) ---
    if "Data_coc_chot" not in df_calc.columns:
        rel = df_calc.get(
            "Mối quan hệ", pd.Series(index=df_calc.index, dtype=object)
        ).fillna("")
        df_calc["Data_coc_chot"] = rel.isin(COC_CHOT_LABELS).astype(int)

    if "Nhóm tuổi" not in df_calc.columns:
        if "description" in df_calc.columns:
            df_calc["Nhóm tuổi"] = df_calc["description"].apply(classify_age_group)
        else:
            df_calc["Nhóm tuổi"] = "Chưa điền"

    if "_report_4_sources_with_weights" not in df_calc.columns:
        source_details = df_calc.get(
            "account_source_details",
            pd.Series(index=df_calc.index, dtype=object),
        )
        df_calc["_report_4_sources_with_weights"] = source_details.apply(
            expand_report_4_sources_with_weights
        )

    # --- Expand: mỗi nguồn khớp regex × nhóm tuổi → 1 bản ghi ---
    records = []
    for _, row in df_calc.iterrows():
        is_coc = int(row.get("Data_coc_chot", 0))
        age_group = row.get("Nhóm tuổi", "Chưa điền")
        if not isinstance(age_group, str) or not age_group.strip():
            age_group = "Chưa điền"
        sources = row.get("_report_4_sources_with_weights", [])
        if isinstance(sources, list):
            for s_key, weight in sources:
                parts = s_key.split("::", 1)
                if len(parts) == 2:
                    w = float(weight)
                    records.append({
                        "Table": parts[0],
                        "Nguồn": parts[1],
                        "Nhóm tuổi": age_group,
                        "Weight": w,
                        "BillWeight": w * is_coc,
                    })

    rec_df = pd.DataFrame(records)

    # Danh sách cột base (có thể sum khi merge templates)
    data_cols_age = [f"{g}_Data" for g in AGE_GROUPS]
    bill_cols_age = [f"{g}_Bill cọc" for g in AGE_GROUPS]
    sum_cols = data_cols_age + bill_cols_age + ["TỔNG_Data", "TỔNG_Bill cọc"]

    if rec_df.empty:
        # Không có bản ghi khớp regex → bảng template toàn số 0
        onl_res, off_res, tong_res = _merge_with_templates(
            pd.DataFrame(columns=['Table', 'Nguồn'] + sum_cols), sum_cols
        )
    else:
        # --- GroupBy + Pivot ---
        grouped = (
            rec_df
            .groupby(['Table', 'Nguồn', 'Nhóm tuổi'])[['Weight', 'BillWeight']]
            .sum()
            .reset_index()
        )

        pivot_data = grouped.pivot_table(
            index=['Table', 'Nguồn'], columns='Nhóm tuổi',
            values='Weight', aggfunc='sum', fill_value=0.0,
        )
        pivot_bill = grouped.pivot_table(
            index=['Table', 'Nguồn'], columns='Nhóm tuổi',
            values='BillWeight', aggfunc='sum', fill_value=0.0,
        )

        # Đảm bảo tất cả 7 nhóm tuổi tồn tại
        for g in AGE_GROUPS:
            if g not in pivot_data.columns:
                pivot_data[g] = 0.0
            if g not in pivot_bill.columns:
                pivot_bill[g] = 0.0

        # Đổi tên cột: {tuổi} → {tuổi}_Data / {tuổi}_Bill cọc
        pivot_data = pivot_data[AGE_GROUPS].rename(
            columns={g: f"{g}_Data" for g in AGE_GROUPS}
        )
        pivot_bill = pivot_bill[AGE_GROUPS].rename(
            columns={g: f"{g}_Bill cọc" for g in AGE_GROUPS}
        )

        combined = pd.concat([pivot_data, pivot_bill], axis=1).reset_index()

        # TỔNG theo hàng (sum 7 nhóm tuổi)
        combined["TỔNG_Data"] = combined[data_cols_age].sum(axis=1)
        combined["TỔNG_Bill cọc"] = combined[bill_cols_age].sum(axis=1)

        # Merge với template cố định (dùng chung với BC4)
        onl_res, off_res, tong_res = _merge_with_templates(combined, sum_cols)

    # --- Tính chỉ số phái sinh cho mỗi bảng ---
    for df_table in [onl_res, off_res, tong_res]:
        for group_name in AGE_GROUPS + ["TỔNG"]:
            d_col = f"{group_name}_Data"
            b_col = f"{group_name}_Bill cọc"
            d = df_table[d_col]
            b = df_table[b_col]
            df_table[f"{group_name}_Data/Bill"] = (
                (d / b.where(b > 0)).fillna(0.0).round(2)
            )
            df_table[f"{group_name}_Bill/Data (%)"] = (
                (b / d.where(d > 0) * 100).fillna(0.0).round(2)
            )
        df_table.insert(0, 'Thời gian xuất data', fetch_time)

    return {
        'onl': onl_res[col_order],
        'off': off_res[col_order],
        'tong': tong_res[col_order],
    }


def compute_report_5(df_filtered):
    """Tính toán Báo cáo 5 từ DataFrame đã lọc (giao diện tương thích st.session_state)."""
    col_order = _r5_col_order()
    if df_filtered.empty:
        empty = pd.DataFrame(columns=col_order)
        return {'onl': empty, 'off': empty.copy(), 'tong': empty.copy()}
    try:
        fetch_time = st.session_state.get("fetch_time") or format_fetch_time()
    except Exception:
        fetch_time = format_fetch_time()
    return build_report_5_tables(df_filtered, fetch_time)


def aggregate_report_5_rows(df_rows, time_val, nguon_val):
    """Tính dòng TỔNG CỘNG cho BC5 — sum cột _Data/_Bill cọc, tính lại Data/Bill và Bill/Data(%)."""
    row_dict = {'Thời gian xuất data': time_val, 'Nguồn': nguon_val}
    for group_name in AGE_GROUPS + ['TỔNG']:
        d_col = f"{group_name}_Data"
        b_col = f"{group_name}_Bill cọc"
        d = round(float(df_rows[d_col].sum()), 2) if d_col in df_rows else 0.0
        b = round(float(df_rows[b_col].sum()), 2) if b_col in df_rows else 0.0
        row_dict[d_col] = d
        row_dict[b_col] = b
        row_dict[f"{group_name}_Data/Bill"] = round(d / b, 2) if b > 0 else 0.0
        row_dict[f"{group_name}_Bill/Data (%)"] = round(b / d * 100, 2) if d > 0 else 0.0
    return row_dict


def prepare_excel_report_5(df_table):
    """Thêm dòng TỔNG CỘNG vào cuối bảng BC5 cho xuất Excel."""
    if df_table.empty:
        return df_table
    df_excel = df_table.copy()
    time_val = df_excel['Thời gian xuất data'].iloc[0] if len(df_excel) > 0 else ''
    total_row = aggregate_report_5_rows(df_excel, time_val, 'TỔNG CỘNG')
    return pd.concat([df_excel, pd.DataFrame([total_row])], ignore_index=True)
