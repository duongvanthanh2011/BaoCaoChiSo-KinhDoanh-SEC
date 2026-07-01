"""
report_components.py - Component UI dung chung cho cac bao cao.
"""

import hashlib

import pandas as pd
import streamlit as st


DOT_COLUMN = 'ĐỢT HỌC THỬ'


def normalize_dot_manual_df(dot_manual_df, unique_dots, number_columns):
    """Giu dung danh sach dot va ep cac cot nhap tay ve so nguyen khong am."""
    base_df = pd.DataFrame({DOT_COLUMN: list(unique_dots)})
    columns = [DOT_COLUMN] + list(number_columns)

    if dot_manual_df is None or len(dot_manual_df) == 0:
        for col in number_columns:
            base_df[col] = 0
        return base_df[columns]

    manual_df = pd.DataFrame(dot_manual_df).copy()
    for col in columns:
        if col not in manual_df.columns:
            manual_df[col] = 0 if col in number_columns else ""

    manual_df = manual_df[columns].drop_duplicates(DOT_COLUMN, keep='last')
    normalized_df = base_df.merge(manual_df, on=DOT_COLUMN, how='left')

    for col in number_columns:
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


def render_dot_manual_inputs(title, state_key, unique_dots, number_columns, input_key_prefixes):
    """
    Render bang nhap so theo tung dot hoc thu bang number_input rieng cho tung o.

    Tra ve:
    - manual_df: DataFrame gom DOT_COLUMN va cac number_columns.
    - manual_hash: hash cua manual_df de dung lam mot phan key cho AgGrid.
    """
    unique_dots = list(unique_dots)
    number_columns = list(number_columns)
    st.session_state[state_key] = normalize_dot_manual_df(
        st.session_state.get(state_key),
        unique_dots,
        number_columns,
    )

    st.markdown(f"#### {title}")

    manual_by_dot = st.session_state[state_key].set_index(DOT_COLUMN)
    header_cols = st.columns([2] + [1] * len(number_columns))
    header_cols[0].markdown(f"**{DOT_COLUMN}**")
    for idx, col in enumerate(number_columns, start=1):
        header_cols[idx].markdown(f"**{col}**")

    manual_rows = []
    for dot_name in unique_dots:
        dot_hash = hashlib.md5(str(dot_name).encode("utf-8")).hexdigest()[:12]
        row_cols = st.columns([2] + [1] * len(number_columns))
        row_cols[0].write(str(dot_name))

        row_data = {DOT_COLUMN: dot_name}
        for idx, col in enumerate(number_columns, start=1):
            key_prefix = input_key_prefixes.get(col, f"{state_key}_{idx}")
            input_key = f"{key_prefix}_{dot_hash}"
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

    manual_df = normalize_dot_manual_df(pd.DataFrame(manual_rows), unique_dots, number_columns)
    st.session_state[state_key] = manual_df
    return manual_df, hash_dot_manual_df(manual_df)
