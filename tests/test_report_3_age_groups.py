import unittest
from unittest.mock import patch

import pandas as pd
from st_aggrid import GridOptionsBuilder

from data_processing import (
    AGE_GROUPS,
    REPORT_3_CONSOLIDATED_COLUMNS,
    REPORT_3_SCHOOL_WORKER_COLUMN,
    REPORT_3_STUDENT_YOUNG_COLUMN,
    REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN,
    classify_age_group,
)
from report_calculations import compute_report_3, prepare_excel_report_3
from report_utils import configure_report3_grid_columns


class Report3AgeGroupTests(unittest.TestCase):
    def test_classify_new_age_groups_case_insensitively(self):
        cases = {
            " HỌC SINH CẤP 2 ": "Học sinh cấp 2",
            "học sinh cấp 3": "Học sinh cấp 3",
            "sinh viên": "Sinh Viên",
            "NGƯỜI ĐI LÀM DƯỚI 35 TUỔI": "Người đi làm dưới 35 Tuổi",
            "người đi làm từ 35 - 50 tuổi": "Người đi làm từ 35 - 50 Tuổi",
            "Độ tuổi khác": "Độ tuổi khác",
            "Chưa điền": "Chưa điền",
        }

        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(classify_age_group(value), expected)

    def test_old_and_unknown_labels_are_other(self):
        old_or_unknown_values = [
            "Học sinh cấp 1",
            "Người đi làm dưới 45 Tuổi",
            "Người đi làm từ 45 đến dưới 60 tuổi",
            "Người trên 60 tuổi",
            "Mất gốc",
        ]

        for value in old_or_unknown_values:
            with self.subTest(value=value):
                self.assertEqual(classify_age_group(value), "Độ tuổi khác")

    def test_missing_and_legacy_unfilled_labels_are_unfilled(self):
        for value in ["", "   ", None, "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG"]:
            with self.subTest(value=value):
                self.assertEqual(classify_age_group(value), "Chưa điền")

    def test_compute_report_3_uses_new_schema_and_aggregates(self):
        descriptions = AGE_GROUPS + ["Người đi làm dưới 45 Tuổi", "   "]
        df = pd.DataFrame({
            "ĐỢT HỌC THỬ": ["Đợt 1"] * len(descriptions),
            "description": descriptions,
            "_report_3_sources_with_weights": [
                [("Google Ads", 1.0)] for _ in descriptions
            ],
        })

        with patch("report_calculations.st.session_state", {"fetch_time": "04/09/2026 10:00"}):
            result = compute_report_3(df)

        expected_columns = (
            ["Thời gian xuất data", "ĐỢT HỌC THỬ", "Nguồn"]
            + AGE_GROUPS
            + ["TỔNG"]
            + REPORT_3_CONSOLIDATED_COLUMNS
        )
        self.assertEqual(list(result.columns), expected_columns)

        row = result.iloc[0]
        self.assertEqual(row["TỔNG"], 9.0)
        self.assertEqual(row["Độ tuổi khác"], 2.0)
        self.assertEqual(row["Chưa điền"], 2.0)
        self.assertEqual(row[REPORT_3_STUDENT_YOUNG_COLUMN], 2.0)
        self.assertEqual(row[REPORT_3_SCHOOL_WORKER_COLUMN], 3.0)
        self.assertEqual(row[REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN], 4.0)

        for old_column in [
            "HS cấp 2+3",
            "SV + DL <45",
            "Khác (HS1+45-60+60+Chưa điền)",
        ]:
            self.assertNotIn(old_column, result.columns)

    def test_compute_report_3_normalizes_stale_session_age_groups(self):
        df = pd.DataFrame({
            "ĐỢT HỌC THỬ": ["Đợt 1", "Đợt 1", "Đợt 1"],
            "Nhóm tuổi": [
                "Sinh Viên",
                "Người đi làm dưới 45 Tuổi",
                "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG",
            ],
            "_report_3_sources_with_weights": [
                [("Google Ads", 1.0)],
                [("Google Ads", 1.0)],
                [("Google Ads", 1.0)],
            ],
        })

        with patch("report_calculations.st.session_state", {"fetch_time": "04/09/2026 10:00"}):
            result = compute_report_3(df)

        row = result.iloc[0]
        self.assertEqual(row["Sinh Viên"], 1.0)
        self.assertEqual(row["Độ tuổi khác"], 1.0)
        self.assertEqual(row["Chưa điền"], 1.0)
        self.assertEqual(row["TỔNG"], 3.0)
        self.assertEqual(row[REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN], 2.0)

    def test_excel_has_only_new_consolidated_percentages(self):
        df = pd.DataFrame([{
            "Thời gian xuất data": "04/09/2026 10:00",
            "ĐỢT HỌC THỬ": "Đợt 1",
            "Nguồn": "Google Ads",
            **{group: 1.0 for group in AGE_GROUPS},
            "TỔNG": float(len(AGE_GROUPS)),
            REPORT_3_CONSOLIDATED_COLUMNS[0]: 2.0,
            REPORT_3_CONSOLIDATED_COLUMNS[1]: 3.0,
            REPORT_3_CONSOLIDATED_COLUMNS[2]: 3.0,
        }])

        excel = prepare_excel_report_3(df)

        for col in AGE_GROUPS + REPORT_3_CONSOLIDATED_COLUMNS:
            self.assertIn(f"{col} (%)", excel.columns)
        self.assertNotIn("SV + DL <45 (%)", excel.columns)
        self.assertNotIn("Khác (HS1+45-60+60+Chưa điền) (%)", excel.columns)

    def test_grid_uses_expected_color_rules_for_consolidated_columns(self):
        columns = (
            ["Thời gian xuất data", "ĐỢT HỌC THỬ", "Nguồn"]
            + AGE_GROUPS
            + ["TỔNG"]
            + REPORT_3_CONSOLIDATED_COLUMNS
        )
        builder = GridOptionsBuilder.from_dataframe(pd.DataFrame(columns=columns))
        configure_report3_grid_columns(builder)
        column_defs = {
            col["field"]: col for col in builder.build()["columnDefs"]
        }

        student_style = column_defs[REPORT_3_STUDENT_YOUNG_COLUMN]["cellStyle"].js_code
        school_style = column_defs[REPORT_3_SCHOOL_WORKER_COLUMN]["cellStyle"].js_code
        unfilled_style = column_defs[REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN]["cellStyle"].js_code

        self.assertIn("pct >= 80", student_style)
        self.assertIn("pct <= 20", school_style)
        self.assertIn("pct >= 80", unfilled_style)
        for style in [student_style, school_style, unfilled_style]:
            self.assertIn("#ccffcc", style)
            self.assertIn("#ffcccc", style)


if __name__ == "__main__":
    unittest.main()
