"""
report_5_schema.py — Nguồn sự thật duy nhất cho cấu trúc Báo cáo 5 (Truyền Thông).
Tập trung toàn bộ hằng số, danh sách nhóm tuổi, TC, field nội bộ và metadata cột.
Không phụ thuộc Streamlit hoặc pandas.
"""

REPORT_5_SCHEMA_VERSION = 5

REPORT_5_CHANNEL_FACEBOOK = "facebook"
REPORT_5_CHANNEL_GOOGLE = "google"
REPORT_5_CHANNEL_TOTAL = "tong"
# Bảng IV là phạm vi Facebook Data Không Gọi (KOG1..KOG6), không phải SV Offline.
REPORT_5_CHANNEL_DATA_KHONG_GOI = "data_khong_goi"

REPORT_5_TC_ROWS = (
    "TC1", "TC2", "TC3", "TC4", "TC5", "TC6"
)

REPORT_5_PARENT_GROUP = "Phụ huynh có con C2, C3"

REPORT_5_AGE_GROUPS = (
    "Học sinh cấp 2",
    "Học sinh cấp 3",
    REPORT_5_PARENT_GROUP,
    "Sinh Viên",
    "Người đi làm dưới 35 Tuổi",
    "Người đi làm từ 35 - 50 Tuổi",
    "Khác",
)

REPORT_5_DISPLAY_GROUPS = REPORT_5_AGE_GROUPS + ("TỔNG",)

REPORT_5_AGE_METRICS = (
    "SL Data",
    "Tổng tỉ lệ độ tuổi",
    "Bills",
    "Tỉ lệ chốt",
    "%Bills",
)

REPORT_5_ERROR_METRICS = (
    "SL data sai số",
    "Phần trăm data sai số trên Tổng data",
)

REPORT_5_COST_METRICS = (
    "Tổng chi phí",
    "Chi phí/Data hợp lệ",
    "Chi phí/Bill",
)

# Cột thông tin cơ bản
FIELD_TIME = "Thời gian xuất data"
FIELD_SOURCE = "Nguồn"

# Các field nội bộ đặc biệt
FIELD_ERROR_COUNT = "error::count"
FIELD_ERROR_PERCENT = "error::percent"

FIELD_COST_TOTAL = "cost::total"
FIELD_COST_PER_VALID_DATA = "cost::per_valid_data"
FIELD_COST_PER_BILL = "cost::per_bill"


def age_data_field(group: str) -> str:
    return f"age::{group}::data"


def age_bill_field(group: str) -> str:
    return f"age::{group}::bills"


def age_ratio_field(group: str) -> str:
    return f"age::{group}::age_ratio"


def close_ratio_field(group: str) -> str:
    return f"age::{group}::close_ratio"


def bill_share_field(group: str) -> str:
    return f"age::{group}::bill_share"


def get_report_5_fields() -> list[str]:
    """Trả về danh sách đầy đủ tất cả các field nội bộ theo thứ tự chuẩn."""
    fields = [
        FIELD_TIME,
        FIELD_SOURCE,
        FIELD_ERROR_COUNT,
        FIELD_ERROR_PERCENT,
        FIELD_COST_TOTAL,
        FIELD_COST_PER_VALID_DATA,
        FIELD_COST_PER_BILL,
    ]
    for g in REPORT_5_DISPLAY_GROUPS:
        fields.extend([
            age_data_field(g),
            age_ratio_field(g),
            age_bill_field(g),
            close_ratio_field(g),
            bill_share_field(g),
        ])
    return fields


def get_report_5_column_specs(include_costs: bool = True):
    """
    Trả về cấu trúc 2 tầng (Group Header -> List[(Child Header, field_key, format_type, width)])
    dùng chung cho cấu hình AgGrid và xuất Excel.
    """
    specs = [
        (None, [
            ("Thời gian xuất data", FIELD_TIME, "text", 140),
            ("Nguồn", FIELD_SOURCE, "text", 100),
        ]),
        ("Data sai số", [
            ("SL data sai số", FIELD_ERROR_COUNT, "float", 120),
            ("Phần trăm data sai số trên Tổng data", FIELD_ERROR_PERCENT, "pct", 165),
        ]),
    ]
    if include_costs:
        specs.append(("Chi phí", [
            ("Tổng chi phí", FIELD_COST_TOTAL, "currency_int", 130),
            ("Chi phí/Data hợp lệ", FIELD_COST_PER_VALID_DATA, "currency_float", 150),
            ("Chi phí/Bill", FIELD_COST_PER_BILL, "currency_float", 130),
        ]))
    for g in REPORT_5_DISPLAY_GROUPS:
        specs.append((
            g,
            [
                ("SL Data", age_data_field(g), "float", 95),
                ("Tổng tỉ lệ độ tuổi", age_ratio_field(g), "pct", 135),
                ("Bills", age_bill_field(g), "float", 90),
                ("Tỉ lệ chốt", close_ratio_field(g), "pct", 110),
                ("%Bills", bill_share_field(g), "pct", 100),
            ]
        ))
    return specs
