"""Schema duy nhất của Báo cáo 6: MKT theo vị trí địa lý."""

REPORT_6_SCHEMA_VERSION = 2

REPORT_6_CHANNEL_FACEBOOK = "facebook"
REPORT_6_CHANNEL_GOOGLE = "google"
REPORT_6_CHANNEL_TOTAL = "tong"

REPORT_6_TC_GROUPS = ("TC1", "TC2", "TC3", "TC4", "TC5", "TC6")

FIELD_TIME = "Thời gian xuất data"
FIELD_LOCATION = "Tỉnh/Thành phố"


def tc_data_field(tc: str) -> str:
    return f"tc::{tc}::data"


def tc_location_ratio_field(tc: str) -> str:
    return f"tc::{tc}::location_ratio"


def tc_bills_field(tc: str) -> str:
    return f"tc::{tc}::bills"


def tc_close_ratio_field(tc: str) -> str:
    return f"tc::{tc}::close_ratio"


def tc_bill_share_field(tc: str) -> str:
    return f"tc::{tc}::bill_share"


def get_report_6_fields() -> list[str]:
    fields = [FIELD_TIME, FIELD_LOCATION]
    for tc in REPORT_6_TC_GROUPS:
        fields.extend([
            tc_data_field(tc),
            tc_location_ratio_field(tc),
            tc_bills_field(tc),
            tc_close_ratio_field(tc),
            tc_bill_share_field(tc),
        ])
    return fields


def get_report_6_column_specs():
    """Metadata header hai tầng dùng chung cho AgGrid và Excel."""
    specs = [(None, [
        ("Thời gian xuất data", FIELD_TIME, "text", 140),
        ("Tỉnh/Thành phố", FIELD_LOCATION, "text", 210),
    ])]
    for tc in REPORT_6_TC_GROUPS:
        specs.append((tc, [
            ("SL", tc_data_field(tc), "float", 90),
            ("Tỉ lệ vị trí\n(SL / Tổng data)", tc_location_ratio_field(tc), "pct", 135),
            ("Bills", tc_bills_field(tc), "float", 90),
            ("Tỉ lệ chốt\n(Bills / SL)", tc_close_ratio_field(tc), "pct", 120),
            ("% Bills\n(Bills / Tổng số Bills)", tc_bill_share_field(tc), "pct", 145),
        ]))
    return specs
