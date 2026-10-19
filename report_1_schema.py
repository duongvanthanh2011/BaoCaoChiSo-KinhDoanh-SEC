"""Trạng thái, công thức và ngưỡng KPI dùng riêng cho Báo cáo 1."""

REPORT_1_SCHEMA_VERSION = 5
GROUP_COLUMNS = ['ĐỢT HỌC THỬ', 'Phòng ban', 'Người phụ trách']
IDENTITY_COLUMNS = ['Thời gian xuất data', *GROUP_COLUMNS]
TOTAL_FIELD = 'Tổng data đã chia'
BASE_FIELD = 'Tổng data đã chia (trừ sai số, sai đối tượng)'

# Tổng gồm L1..L17 và L1.1 (57), không gồm L0 (1).
ASSIGNED_IDS = (16, 57, 39, 58, 23, 21, 59, 60, 15, 51, 6, 52, 32, 45, 22, 41, 44, 13)
INVALID_IDS = (22, 41)
ERROR_FIELD = 'Data sai số, sai đối tượng, SEC từ chối, TĐKTC'

# field, numerator IDs, target, yellow lower/upper bounds, direction
KPI_SPECS = (
    ('Chưa gọi CVHT', (16,), '0%', 0, 0, 'zero'),
    ('Đang trao đổi', (23, 21, 59, 60, 15, 51, 6), '60% (±5%)', 55, 60, 'higher'),
    ('Tiềm năng trước học thử', (21, 59, 60, 15, 51, 6), '30% (±5%)', 25, 30, 'higher'),
    ('Tiềm năng sau học thử', (60, 15, 51, 6), '15% (±3%)', 12, 15, 'higher'),
    ('Đã cọc chốt', (15, 51, 6), '12% (±2%)', 10, 12, 'higher'),
    (ERROR_FIELD, (45, 22, 41, 44), '6%–8%', 6, 8, 'lower'),
)
KPI_HEADERS = {
    field: f'{field}/ Tổng data chia trừ sai số, sai đối tượng'
    for field, *_ in KPI_SPECS
}
KPI_HEADERS[ERROR_FIELD] = f'{ERROR_FIELD}/ Tổng data đã chia'

# Cột nhập tay và cột tỷ lệ tổng cọc theo đợt học thử
TRIAL_DEPOSIT_FIELD = 'Tổng cọc'
TRIAL_DEPOSIT_RATIO_FIELD = 'Tổng cọc buổi học thử/Tổng data đã chia (trừ sai số, sai đối tượng)'
TRIAL_DEPOSIT_VISIBLE_FIELD = '_r1_show_trial_deposit'
KPI_HEADERS[TRIAL_DEPOSIT_RATIO_FIELD] = TRIAL_DEPOSIT_RATIO_FIELD


def count_field(field):
    return f'_r1_count_{field}'


COUNT_FIELDS = [TOTAL_FIELD, BASE_FIELD, *(count_field(s[0]) for s in KPI_SPECS)]
DISPLAY_COLUMNS = [
    *IDENTITY_COLUMNS, TOTAL_FIELD, BASE_FIELD, ERROR_FIELD,
    *(s[0] for s in KPI_SPECS if s[0] != ERROR_FIELD),
    TRIAL_DEPOSIT_RATIO_FIELD,
]
ALL_COLUMNS = [
    *DISPLAY_COLUMNS,
    *(count_field(s[0]) for s in KPI_SPECS),
    TRIAL_DEPOSIT_FIELD,
    TRIAL_DEPOSIT_VISIBLE_FIELD,
]


def kpi_denominator(field):
    """Chỉ KPI sai số dùng tổng đã chia; các KPI còn lại dùng tổng hợp lệ."""
    return TOTAL_FIELD if field == ERROR_FIELD else BASE_FIELD


def kpi_color(value, low, high, direction):
    if direction == 'zero':
        return 'ffcccc' if value > 0 else 'ccffcc'
    if direction == 'higher':
        return 'ccffcc' if value > high else ('fff2cc' if value >= low else 'ffcccc')
    return 'ccffcc' if value < low else ('fff2cc' if value <= high else 'ffcccc')


def calculate_percentages(frame):
    """Tỷ lệ 0..100; không có mẫu số hợp lệ thì để trống, không đánh giá KPI."""
    for field, *_ in KPI_SPECS:
        denominator = frame[kpi_denominator(field)].where(frame[kpi_denominator(field)] > 0)
        frame[field] = frame[count_field(field)] / denominator * 100
    # Không còn L1 là đạt, kể cả nhóm không có data hợp lệ.
    field = KPI_SPECS[0][0]
    frame.loc[frame[count_field(field)] == 0, field] = 0.0
    return frame
