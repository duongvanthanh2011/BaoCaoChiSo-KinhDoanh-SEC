"""
report_components.py - Component UI dung chung cho cac bao cao.
"""

import hashlib

import pandas as pd
import streamlit as st


DOT_COLUMN = 'ĐỢT HỌC THỬ'


def normalize_dot_manual_df(dot_manual_df, unique_dots, number_columns, float_columns=None):
    """Giữ đúng danh sách đợt và ép các cột nhập tay về số không âm (hỗ trợ cả float và int)."""
    base_df = pd.DataFrame({DOT_COLUMN: list(unique_dots)})
    columns = [DOT_COLUMN] + list(number_columns)
    float_cols_set = set(float_columns or [])

    if dot_manual_df is None or len(dot_manual_df) == 0:
        for col in number_columns:
            base_df[col] = 0.0 if col in float_cols_set else 0
        return base_df[columns]

    manual_df = pd.DataFrame(dot_manual_df).copy()
    for col in columns:
        if col not in manual_df.columns:
            manual_df[col] = 0.0 if col in float_cols_set else (0 if col in number_columns else "")

    manual_df = manual_df[columns].drop_duplicates(DOT_COLUMN, keep='last')
    normalized_df = base_df.merge(manual_df, on=DOT_COLUMN, how='left')

    for col in number_columns:
        if col in float_cols_set:
            normalized_df[col] = (
                pd.to_numeric(normalized_df[col], errors='coerce')
                .fillna(0.0)
                .clip(lower=0.0)
                .round(2)
            )
        else:
            normalized_df[col] = (
                pd.to_numeric(normalized_df[col], errors='coerce')
                .fillna(0)
                .clip(lower=0)
                .astype(int)
            )

    return normalized_df[columns]


def hash_dot_manual_df(dot_manual_df):
    """Tao hash on dinh de ep component bang bao cao reload khi so nhap tay doi."""
    payload = dot_manual_df.to_json(orient='records', force_ascii=False)
    return hashlib.md5(payload.encode('utf-8')).hexdigest()[:12]


def render_dot_manual_inputs(title, state_key, unique_dots, number_columns, input_key_prefixes, float_columns=None, display_labels=None):
    """
    Render bảng nhập số theo từng đợt học thử với định dạng và chiều cao đồng bộ chuẩn xác.

    Trả về:
    - manual_df: DataFrame gồm DOT_COLUMN và các number_columns.
    - manual_hash: hash của manual_df để dùng làm một phần key cho AgGrid.
    """
    unique_dots = list(unique_dots)
    number_columns = list(number_columns)
    float_cols_set = set(float_columns or [])
    labels_map = display_labels or {}
    
    st.session_state[state_key] = normalize_dot_manual_df(
        st.session_state.get(state_key),
        unique_dots,
        number_columns,
        float_columns=float_columns
    )

    # Tiêu đề với chiều cao và font size đồng nhất
    st.markdown(f"<div style='font-size: 15px; font-weight: 600; color: #1E293B; margin-bottom: 8px; height: 24px; line-height: 24px;'>{title}</div>", unsafe_allow_html=True)

    manual_by_dot = st.session_state[state_key].set_index(DOT_COLUMN)
    col_widths = [1.3] + [1.0] * len(number_columns)
    header_cols = st.columns(col_widths)
    header_cols[0].markdown(f"<div style='height: 38px; display: flex; align-items: flex-end; font-weight: 700; font-size: 13px;'>{DOT_COLUMN}</div>", unsafe_allow_html=True)
    for idx, col in enumerate(number_columns, start=1):
        col_label = labels_map.get(col, col)
        header_cols[idx].markdown(f"<div style='height: 38px; display: flex; align-items: flex-end; font-weight: 700; font-size: 13px; line-height: 1.2;'>{col_label}</div>", unsafe_allow_html=True)

    manual_rows = []
    for dot_name in unique_dots:
        dot_hash = hashlib.md5(str(dot_name).encode("utf-8")).hexdigest()[:12]
        row_cols = st.columns(col_widths)
        row_cols[0].markdown(f"<div style='height: 38px; display: flex; align-items: center; font-size: 13px; font-weight: 500;'>{dot_name}</div>", unsafe_allow_html=True)

        row_data = {DOT_COLUMN: dot_name}
        for idx, col in enumerate(number_columns, start=1):
            key_prefix = input_key_prefixes.get(col, f"{state_key}_{idx}")
            input_key = f"{key_prefix}_{dot_hash}"
            is_float = col in float_cols_set
            
            if is_float:
                current_value = float(manual_by_dot.at[dot_name, col]) if dot_name in manual_by_dot.index else 0.0
                if input_key not in st.session_state:
                    st.session_state[input_key] = current_value

                row_data[col] = row_cols[idx].number_input(
                    col,
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key=input_key,
                    label_visibility="collapsed",
                )
            else:
                current_value = int(manual_by_dot.at[dot_name, col]) if dot_name in manual_by_dot.index else 0
                if input_key not in st.session_state:
                    st.session_state[input_key] = current_value

                row_data[col] = row_cols[idx].number_input(
                    col,
                    min_value=0,
                    step=1,
                    format="%d",
                    key=input_key,
                    label_visibility="collapsed",
                )

        manual_rows.append(row_data)

    manual_df = normalize_dot_manual_df(pd.DataFrame(manual_rows), unique_dots, number_columns, float_columns=float_columns)
    st.session_state[state_key] = manual_df
    return manual_df, hash_dot_manual_df(manual_df)


def normalize_dot_nguon_manual_df(dot_manual_df, unique_pairs, number_columns):
    """Giữ đúng danh sách (đợt, nguồn) và ép các cột nhập tay về số nguyên không âm."""
    base_df = pd.DataFrame(unique_pairs, columns=[DOT_COLUMN, 'Nguồn'])
    columns = [DOT_COLUMN, 'Nguồn'] + list(number_columns)

    if dot_manual_df is None or len(dot_manual_df) == 0:
        for col in number_columns:
            base_df[col] = 0
        return base_df[columns]

    manual_df = pd.DataFrame(dot_manual_df).copy()
    for col in columns:
        if col not in manual_df.columns:
            manual_df[col] = 0 if col in number_columns else ""

    manual_df = manual_df[columns].drop_duplicates([DOT_COLUMN, 'Nguồn'], keep='last')
    normalized_df = base_df.merge(manual_df, on=[DOT_COLUMN, 'Nguồn'], how='left')

    for col in number_columns:
        normalized_df[col] = (
            pd.to_numeric(normalized_df[col], errors='coerce')
            .fillna(0)
            .clip(lower=0)
            .astype(int)
        )

    return normalized_df[columns]


def render_dot_nguon_manual_inputs(title, state_key, unique_pairs, number_columns, input_key_prefixes):
    """
    Render bảng nhập số theo từng đợt học thử VÀ nguồn.
    unique_pairs là danh sách các tuple (ĐỢT HỌC THỬ, Nguồn).
    """
    number_columns = list(number_columns)
    st.session_state[state_key] = normalize_dot_nguon_manual_df(
        st.session_state.get(state_key),
        unique_pairs,
        number_columns,
    )

    st.markdown(f"#### {title}")

    # Set index to both DOT_COLUMN and 'Nguồn'
    manual_by_pair = st.session_state[state_key].set_index([DOT_COLUMN, 'Nguồn'])
    
    # 2 columns for headers, plus number_columns
    header_cols = st.columns([1.5, 1.5] + [1] * len(number_columns))
    header_cols[0].markdown(f"**{DOT_COLUMN}**")
    header_cols[1].markdown("**Nguồn**")
    for idx, col in enumerate(number_columns, start=2):
        header_cols[idx].markdown(f"**{col}**")

    manual_rows = []
    # Khai báo biến lưu đợt học thử hiện tại để hiển thị đẹp hơn
    current_dot = None

    for dot_name, nguon_name in unique_pairs:
        pair_hash = hashlib.md5(f"{dot_name}_{nguon_name}".encode("utf-8")).hexdigest()[:12]
        row_cols = st.columns([1.5, 1.5] + [1] * len(number_columns))
        
        # Chỉ in tên đợt ở dòng đầu tiên của đợt đó
        if dot_name != current_dot:
            row_cols[0].write(f"**{dot_name}**")
            current_dot = dot_name
        else:
            row_cols[0].write("")

        row_cols[1].write(str(nguon_name))

        row_data = {DOT_COLUMN: dot_name, 'Nguồn': nguon_name}
        for idx, col in enumerate(number_columns, start=2):
            key_prefix = input_key_prefixes.get(col, f"{state_key}_{idx}")
            input_key = f"{key_prefix}_{pair_hash}"
            
            current_value = 0
            if (dot_name, nguon_name) in manual_by_pair.index:
                current_value = int(manual_by_pair.at[(dot_name, nguon_name), col])

            if input_key not in st.session_state:
                st.session_state[input_key] = current_value

            row_data[col] = row_cols[idx].number_input(
                col,
                min_value=0,
                step=1,
                format="%d",
                key=input_key,
                label_visibility="collapsed",
            )

        manual_rows.append(row_data)

    manual_df = normalize_dot_nguon_manual_df(pd.DataFrame(manual_rows), unique_pairs, number_columns)
    st.session_state[state_key] = manual_df
    return manual_df, hash_dot_manual_df(manual_df)


def render_dot_nguon_matrix_inputs(title, state_key, unique_dots, unique_nguons, key_prefix="r2_trung"):
    """
    Render bảng nhập Data trùng dạng ma trận (mỗi dòng là 1 Đợt, các cột là các Nguồn).
    Giúp giao diện cực kỳ gọn gàng, giảm 70% chiều dài dọc.
    
    Trả về:
    - manual_df: DataFrame gồm ['ĐỢT HỌC THỬ', 'Nguồn', 'Data trùng']
    - manual_hash: hash của manual_df
    """
    unique_dots = list(unique_dots)
    unique_nguons = list(unique_nguons)
    
    if state_key not in st.session_state:
        st.session_state[state_key] = {}
        
    # Tiêu đề với chiều cao và font size đồng nhất
    st.markdown(f"<div style='font-size: 15px; font-weight: 600; color: #1E293B; margin-bottom: 8px; height: 24px; line-height: 24px;'>{title}</div>", unsafe_allow_html=True)
    
    col_widths = [1.3] + [1.0] * len(unique_nguons)
    header_cols = st.columns(col_widths)
    header_cols[0].markdown(f"<div style='height: 38px; display: flex; align-items: flex-end; font-weight: 700; font-size: 13px;'>{DOT_COLUMN}</div>", unsafe_allow_html=True)
    for idx, nguon in enumerate(unique_nguons, start=1):
        header_cols[idx].markdown(f"<div style='height: 38px; display: flex; align-items: flex-end; font-weight: 700; font-size: 13px; line-height: 1.2;'>{nguon}</div>", unsafe_allow_html=True)
        
    manual_rows = []
    for dot_name in unique_dots:
        dot_hash = hashlib.md5(str(dot_name).encode("utf-8")).hexdigest()[:8]
        row_cols = st.columns(col_widths)
        row_cols[0].markdown(f"<div style='height: 38px; display: flex; align-items: center; font-size: 13px; font-weight: 500;'>{dot_name}</div>", unsafe_allow_html=True)
        
        for idx, nguon in enumerate(unique_nguons, start=1):
            nguon_hash = hashlib.md5(str(nguon).encode("utf-8")).hexdigest()[:6]
            input_key = f"{key_prefix}_{dot_hash}_{nguon_hash}"
            
            current_val = st.session_state.get(state_key, {}).get((str(dot_name), str(nguon)), 0)
            if input_key not in st.session_state:
                st.session_state[input_key] = int(current_val)
                
            val = row_cols[idx].number_input(
                f"{dot_name}_{nguon}",
                min_value=0,
                step=1,
                format="%d",
                key=input_key,
                label_visibility="collapsed"
            )
            
            st.session_state[state_key][(str(dot_name), str(nguon))] = val
            manual_rows.append({
                DOT_COLUMN: dot_name,
                'Nguồn': nguon,
                'Data trùng': val
            })
            
    manual_df = pd.DataFrame(manual_rows)
    return manual_df, hash_dot_manual_df(manual_df)
