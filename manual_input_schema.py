"""
manual_input_schema.py — Nguồn sự thật duy nhất (Single Source of Truth)
Khai báo mã input, nhãn hiển thị, giá trị mặc định, kiểm tra dữ liệu và
chuyển đổi 2 chiều giữa JSON snapshot và DataFrame cho Báo cáo 1 & 2.
"""

import hashlib
import re
import unicodedata
import pandas as pd

REPORT_1_CODE = "report_1"
REPORT_2_CODE = "report_2"

DOT_COLUMN = "ĐỢT HỌC THỬ"
REPORT_2_ADVISOR_COLUMN = "Số CVHT đi làm"

# ==========================================
# 1. KHAI BÁO SCHEMA CHO BÁO CÁO 1
# ==========================================
REPORT_1_INPUT_SPECS = [
    {
        "code": "r1_other_deposit",
        "column": "Cọc Khác",
        "label": "Cọc Khác",
        "default": 0,
    },
    {
        "code": "r1_trial_deposit_total",
        "column": "Tổng Cọc Học Thử",
        "label": "Tổng Cọc Học Thử",
        "default": 0,
    },
]

REPORT_1_CODE_MAP = {spec["code"]: spec for spec in REPORT_1_INPUT_SPECS}
REPORT_1_COL_TO_CODE = {spec["column"]: spec["code"] for spec in REPORT_1_INPUT_SPECS}


# ==========================================
# 2. KHAI BÁO SCHEMA CHO BÁO CÁO 2
# ==========================================
# Các số liệu chung theo từng đợt
REPORT_2_DOT_INPUT_SPECS = [
    {
        "code": "r2_zalo_group_data",
        "column": "Data vào nhóm Zalo",
        "label": "Vào nhóm Zalo",
        "default": 0,
    },
    {
        "code": "r2_ordered_data",
        "column": "Data order",
        "label": "Data order",
        "default": 0,
    },
    {
        "code": "r2_active_advisor_count",
        "column": REPORT_2_ADVISOR_COLUMN,
        "label": REPORT_2_ADVISOR_COLUMN,
        "default": 0,
    },
]

REPORT_2_DOT_CODE_MAP = {spec["code"]: spec for spec in REPORT_2_DOT_INPUT_SPECS}
REPORT_2_COL_TO_CODE = {spec["column"]: spec["code"] for spec in REPORT_2_DOT_INPUT_SPECS}

# Mapping chuẩn cố định cho 3 nhóm nguồn Báo cáo 2
REPORT_2_SOURCE_PRESETS = {
    "Trường Chinh": "r2_duplicate_truong_chinh",
    "Cầu Giấy": "r2_duplicate_cau_giay",
    "Khác": "r2_duplicate_khac",
}

REPORT_2_CODE_TO_SOURCE = {code: src for src, code in REPORT_2_SOURCE_PRESETS.items()}


def normalize_source_name(name: str) -> str:
    """Loại bỏ dấu tiếng Việt và ký tự đặc biệt để sinh slug ổn định."""
    if not name:
        return "khac"
    # Chuẩn hóa unicode NFD rồi bỏ các ký tự dấu
    s = unicodedata.normalize("NFD", str(name))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "d")
    # Thay thế ký tự không phải chữ và số thành _
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower())
    s = s.strip("_")
    return s or "khac"


def get_r2_duplicate_code(source_name: str) -> str:
    """Trả về mã input chuẩn hóa cho nguồn data trùng của Báo cáo 2."""
    if source_name in REPORT_2_SOURCE_PRESETS:
        return REPORT_2_SOURCE_PRESETS[source_name]
    norm = normalize_source_name(source_name)
    return f"r2_duplicate_{norm}"


def get_hash(val: str, length: int = 8) -> str:
    """Sinh chuỗi hash ổn định."""
    return hashlib.md5(str(val).encode("utf-8")).hexdigest()[:length]


def get_widget_key(report_code: str, input_code: str, dot_name: str) -> str:
    """
    Sinh widget key dạng {input_code}_{trial_session_hash}.
    Giúp Streamlit phân biệt rõ ràng từng ô trên giao diện.
    """
    dot_hash = get_hash(dot_name, length=8)
    return f"{input_code}_{dot_hash}"


# ==========================================
# 3. KIỂM TRA & XÁC THỰC GIÁ TRỊ (VALIDATION)
# ==========================================
def validate_metric_value(metric_value: dict, strict=False) -> dict:
    """
    Xác thực metric_value là JSON 1 cấp, các giá trị là số nguyên không âm.
    Loại bỏ hoặc ép kiểu các giá trị không hợp lệ.
    """
    if strict:
        if not isinstance(metric_value, dict) or any(
            not isinstance(k, str) or not k or type(v) is not int
            or v < 0 or v > 9007199254740991
            for k, v in metric_value.items()
        ):
            raise ValueError("Giá trị nhập phải là JSON một cấp, số nguyên không âm trong giới hạn an toàn.")
        return dict(metric_value)
    if not isinstance(metric_value, dict):
        return {}
    cleaned = {}
    for k, v in metric_value.items():
        if not isinstance(k, str):
            continue
        try:
            num = int(v)
            cleaned[k] = max(0, num)
        except (ValueError, TypeError):
            cleaned[k] = 0
    return cleaned


# ==========================================
# 4. CHUYỂN ĐỔI SNAPSHOT ↔ DATAFRAME
# ==========================================

def snapshot_to_report_1_row(snapshot: dict, dot_name: str) -> dict:
    """Chuyển đổi snapshot sang dict dòng cho Báo cáo 1."""
    row = {DOT_COLUMN: dot_name}
    for spec in REPORT_1_INPUT_SPECS:
        code = spec["code"]
        col = spec["column"]
        default_val = spec["default"]
        val = snapshot.get(code, default_val) if snapshot else default_val
        try:
            row[col] = max(0, int(val))
        except (ValueError, TypeError):
            row[col] = default_val
    return row


def build_report_1_df(drafts_by_dot: dict[str, dict], unique_dots: list[str]) -> pd.DataFrame:
    """
    Dựng dot_manual_df cho Báo cáo 1 từ dictionary các bản nháp theo đợt.
    """
    rows = []
    for dot in unique_dots:
        snap = drafts_by_dot.get(str(dot), {})
        rows.append(snapshot_to_report_1_row(snap, str(dot)))

    columns = [DOT_COLUMN] + [spec["column"] for spec in REPORT_1_INPUT_SPECS]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)[columns]


def snapshot_to_report_2_data(
    snapshot: dict, dot_name: str, unique_nguons: list[str]
) -> tuple[dict, list[dict]]:
    """
    Chuyển đổi snapshot thành dữ liệu dòng cho Báo cáo 2:
    - dot_row: số liệu chung theo đợt (Zalo, Order, Số CVHT)
    - nguon_rows: danh sách các dòng data trùng cho từng nguồn
    """
    snapshot = snapshot or {}
    
    # 1. Số liệu chung theo đợt
    dot_row = {DOT_COLUMN: dot_name}
    for spec in REPORT_2_DOT_INPUT_SPECS:
        code = spec["code"]
        col = spec["column"]
        default_val = spec["default"]
        val = snapshot.get(code, default_val)
        try:
            dot_row[col] = max(0, int(val))
        except (ValueError, TypeError):
            dot_row[col] = default_val

    # 2. Data trùng theo từng nguồn
    nguon_rows = []
    for nguon in unique_nguons:
        code = get_r2_duplicate_code(nguon)
        val = snapshot.get(code, 0)
        try:
            val_int = max(0, int(val))
        except (ValueError, TypeError):
            val_int = 0
        nguon_rows.append({
            DOT_COLUMN: dot_name,
            "Nguồn": nguon,
            "Data trùng": val_int,
        })

    return dot_row, nguon_rows


def build_report_2_dfs(
    drafts_by_dot: dict[str, dict], unique_dots: list[str], unique_nguons: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Dựng dot_manual_df và dot_nguon_manual_df cho Báo cáo 2 từ drafts_by_dot.
    """
    dot_rows = []
    nguon_rows = []
    for dot in unique_dots:
        snap = drafts_by_dot.get(str(dot), {})
        d_row, n_rows = snapshot_to_report_2_data(snap, str(dot), unique_nguons)
        dot_rows.append(d_row)
        nguon_rows.extend(n_rows)

    dot_columns = [DOT_COLUMN] + [spec["column"] for spec in REPORT_2_DOT_INPUT_SPECS]
    nguon_columns = [DOT_COLUMN, "Nguồn", "Data trùng"]

    dot_df = pd.DataFrame(dot_rows, columns=dot_columns) if dot_rows else pd.DataFrame(columns=dot_columns)
    nguon_df = pd.DataFrame(nguon_rows, columns=nguon_columns) if nguon_rows else pd.DataFrame(columns=nguon_columns)

    return dot_df, nguon_df
