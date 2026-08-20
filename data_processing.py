"""
data_processing.py — Module xử lý và biến đổi dữ liệu
Chứa các hàm:
- Xây dựng bộ lọc API (filtering conditions)
- Mở rộng nguồn khách hàng con (Nested Set)
- Biến đổi DataFrame sau khi nhận dữ liệu từ API
"""

import pandas as pd
from datetime import datetime, time, timezone, timedelta

# Định nghĩa múi giờ Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))


def build_department_options(users_list):
    """
    Tạo danh sách phòng ban unique để hiển thị trên UI.
    Output phù hợp cho st.multiselect.
    """
    if not users_list:
        return []

    dept_map = {}
    for user in users_list:
        dept_id = user.get("dept_id")
        dept_name = user.get("dept_name")
        if dept_id is None or not dept_name:
            continue
        if dept_id not in dept_map:
            dept_map[dept_id] = {
                "dept_id": dept_id,
                "dept_name": dept_name,
            }

    return sorted(dept_map.values(), key=lambda x: x["dept_name"] or "")


def build_user_ids_by_departments(selected_departments, users_list):
    """
    Từ danh sách phòng ban đã chọn, trả về list user_id của toàn bộ nhân viên thuộc các phòng ban đó.
    Đây là list sẽ dùng cho filtering_conditions["account_manager:in"].
    """
    if not selected_departments or not users_list:
        return []

    selected_dept_ids = {
        str(item.get("dept_id"))
        for item in selected_departments
        if item.get("dept_id") is not None
    }

    if not selected_dept_ids:
        return []

    user_ids = set()
    for user in users_list:
        dept_id = user.get("dept_id")
        user_id = user.get("user_id")

        if dept_id is None or user_id is None:
            continue

        if str(dept_id) in selected_dept_ids:
            try:
                user_ids.add(int(user_id))
            except (ValueError, TypeError):
                continue

    return sorted(user_ids)

def convert_date_to_timestamp(date_obj, is_end_of_day=False):
    """
    Chuyển đổi datetime.date hoặc chuỗi ("YYYY-MM-DD") sang số giây tính từ epoch.
    - is_end_of_day=False: lấy thời điểm 00:00:00 của ngày.
    - is_end_of_day=True: lấy thời điểm 23:59:59 của ngày.
    """
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        
    if is_end_of_day:
        target_time = time(23, 59, 59)
    else:
        target_time = time.min
        
    dt = datetime.combine(date_obj, target_time).replace(tzinfo=VN_TZ)
    return int(dt.timestamp())


def expand_source_ids(selected_sources, all_sources_list):
    """
    Mở rộng danh sách nguồn: nếu chọn nguồn cha thì tự động thêm tất cả nguồn con.
    Sử dụng mô hình Nested Set (lft/rgt).

    Args:
        selected_sources: List các nguồn đã chọn từ UI
        all_sources_list: Toàn bộ danh sách nguồn từ API

    Returns:
        List[int]: Danh sách ID nguồn đã mở rộng (bao gồm cả con)
    """
    if not selected_sources:
        return []

    src_ids_selected = [int(x["id"]) for x in selected_sources if "id" in x]
    src_ids = list(src_ids_selected)  # bắt đầu với các nguồn đã chọn trực tiếp

    for parent in selected_sources:
        p_lft = parent.get("lft", 0)
        p_rgt = parent.get("rgt", 0)
        if p_lft and p_rgt and p_rgt > p_lft + 1:
            # Nguồn này có con (rgt > lft + 1 trong nested set)
            for child in all_sources_list:
                c_lft = child.get("lft", 0)
                c_rgt = child.get("rgt", 0)
                c_id = child.get("id")
                if c_lft > p_lft and c_rgt < p_rgt and c_id not in src_ids:
                    src_ids.append(int(c_id))

    return src_ids


def build_filtering_conditions(manager_ids, src_ids, type_ids, date_range):
    """
    Xây dựng bộ lọc cho API (cấu trúc "filtering" theo docs của Getfly).

    Args:
        manager_ids: List ID người phụ trách đã chọn
        src_ids: List ID nguồn đã mở rộng
        type_ids: List ID nhóm khách hàng
        date_range: Tuple/list (start_date, end_date)

    Returns:
        dict: Filtering conditions cho API
    """
    filtering_conditions = {}

    if manager_ids:
        filtering_conditions["account_manager:in"] = manager_ids

    if src_ids:
        filtering_conditions["account_source:in"] = src_ids

    if type_ids:
        filtering_conditions["account_type:in"] = type_ids

    if len(date_range) == 2:
        start_timestamp = convert_date_to_timestamp(date_range[0], is_end_of_day=False)
        end_timestamp = convert_date_to_timestamp(date_range[1], is_end_of_day=True)

        filtering_conditions["created_at:gte"] = str(start_timestamp)
        filtering_conditions["created_at:lte"] = str(end_timestamp)

    return filtering_conditions


def _get_filtered_sources(x, src_ids):
    """Lọc nguồn khách hàng theo bộ lọc nếu có lọc theo nguồn."""
    if not isinstance(x, list) or not x:
        return ["Chưa xác định"]
    if src_ids:
        filter_set = set(src_ids)
        labels = []
        for item in x:
            try:
                item_id = int(item.get("id"))
            except (ValueError, TypeError):
                continue
            if item_id in filter_set and item.get("label"):
                labels.append(item.get("label"))
        return labels if labels else ["Chưa xác định"]
    else:
        return [item.get("label", "") for item in x if item.get("label")]


def _get_dot_hoc_thu(fields):
    """Trích xuất 'dot_hoc_thu' từ 'detail_custom_fields' và định dạng thành ngày nếu là Unix timestamp."""
    if not isinstance(fields, dict):
        return "Chưa xác định"
    val = fields.get("dot_hoc_thu")
    if val is None or val == "" or val == []:
        return "Chưa xác định"
    try:
        ts = int(float(str(val)))
        if 946684800 < ts < 4102444800:
            return datetime.fromtimestamp(ts, tz=VN_TZ).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        pass
    return str(val)


def _map_account_types(val, type_map, type_ids):
    """Map ID loại khách hàng sang tên hiển thị."""
    if not val:
        return "Nhóm Chung"
    if isinstance(val, (int, float)):
        try:
            v_int = int(val)
        except (ValueError, TypeError):
            return "Nhóm Chung"
        if type_ids and v_int not in type_ids:
            return "Nhóm Chung"
        return type_map.get(str(v_int), "Nhóm Chung")
    if isinstance(val, str):
        ids = [x.strip() for x in val.split(",") if x.strip()]
        if type_ids:
            valid_ids = []
            for x in ids:
                try:
                    if int(x) in type_ids:
                        valid_ids.append(x)
                except (ValueError, TypeError):
                    pass
            ids = valid_ids
        names = [type_map.get(x) for x in ids if x in type_map]
        return ", ".join(names) if names else "Nhóm Chung"
    if isinstance(val, list):
        if type_ids:
            names = []
            for x in val:
                try:
                    if int(x) in type_ids and str(x) in type_map:
                        names.append(type_map[str(x)])
                except (ValueError, TypeError):
                    pass
        else:
            names = [type_map.get(str(x)) for x in val if str(x) in type_map]
        return ", ".join(names) if names else "Nhóm Chung"
    return "Nhóm Chung"


def _classify_nguon(label):
    """Phân loại nguồn khách hàng dựa trên 3 ký tự đầu của label."""
    if not isinstance(label, str) or not label.strip():
        return "KHÁC"
    prefix = label[:3].upper()
    if prefix == "ADS":
        lower = label.lower()
        if "trường chinh" in lower or "truong chinh" in lower:
            return "ADS - Trường Chinh"
        if "cầu giấy" in lower or "cau giay" in lower:
            return "ADS - Cầu Giấy"
        return "ADS - Khác"
    if prefix == "ORG":
        return "ORG"
    return "KHÁC"


# ==========================================
# PHÂN LOẠI NHÓM TUỔI TỪ TRƯỜNG DESCRIPTION
# ==========================================

AGE_GROUPS = [
    "Học sinh cấp 1",
    "Học sinh cấp 2",
    "Học sinh cấp 3",
    "Sinh viên",
    "Người đi làm dưới 45 tuổi",
    "Người đi làm từ 45 đến dưới 60 tuổi",
    "Người trên 60 tuổi",
    "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG"
]

# Lookup dict: lowercase → tên chuẩn trong AGE_GROUPS (dùng cho so sánh case-insensitive)
_AGE_GROUP_LOOKUP = {g.lower(): g for g in AGE_GROUPS[:-1]}

def classify_age_group(description):
    """
    Phân loại nhóm tuổi từ trường description.
    So sánh case-insensitive: "Sinh Viên" → "Sinh viên", "Người đi làm dưới 45 Tuổi" → "Người đi làm dưới 45 tuổi"
    Nếu rỗng hoặc không khớp 7 nhóm đầu → SALE CHƯA ĐIỀN & ĐIỀN TRÙNG
    """
    if not description or not isinstance(description, str) or not description.strip():
        return "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG"
    desc = description.strip().lower()
    canonical = _AGE_GROUP_LOOKUP.get(desc)
    if canonical:
        return canonical
    return "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG"

# ==========================================
# PHÂN LOẠI NGUỒN VỚI PRIORITY RULES
# ==========================================

def classify_source_with_priority(label):
    """
    Phân loại nguồn theo 3 nhóm:
    1. Khác (chứa 'staff' hoặc 'org')
    2. Trường Chinh (kết hợp Ads Trường Chinh + Google Ads: chứa 'gg', 'trường chinh', 'truong chinh')
    3. Cầu Giấy (Ads Cầu Giấy: chứa 'cầu giấy', 'cau giay')
    4. Khác (các trường hợp còn lại)
    """
    if not isinstance(label, str):
        return "Khác"
    
    label_lower = label.lower()
    
    # Priority 1: Khác (chứa staff hoặc org)
    if "staff" in label_lower or "org" in label_lower:
        return "Khác"
    
    # Priority 2: Trường Chinh (kết hợp Ads Trường Chinh + Google Ads)
    if "gg" in label_lower or "trường chinh" in label_lower or "truong chinh" in label_lower:
        return "Trường Chinh"
    
    # Priority 3: Cầu Giấy (Ads Cầu Giấy)
    if "cầu giấy" in label_lower or "cau giay" in label_lower:
        return "Cầu Giấy"
    
    return "Khác"


def classify_report_3_source(label):
    """Phân loại nguồn riêng cho Báo cáo 3 theo thứ tự ưu tiên nghiệp vụ."""
    if not isinstance(label, str):
        return "Khác"

    label_lower = label.lower()

    # Giữ nguyên ưu tiên cao nhất của nhóm Khác như logic cũ.
    if "staff" in label_lower or "org" in label_lower:
        return "Khác"

    # GG ưu tiên hơn các từ khóa địa điểm.
    if "gg" in label_lower:
        return "Google Ads"

    if "cầu giấy" in label_lower or "cau giay" in label_lower:
        return "Ads Cầu Giấy"

    if "trường chinh" in label_lower or "truong chinh" in label_lower:
        return "Ads Trường Chinh"

    return "Khác"


# ==========================================
# PHÂN BỔ TRỌNG SỐ CHO CÁC NGUỒN
# ==========================================

def _expand_sources_with_classifier(account_source_details, classifier):
    """Chia đều trọng số của một khách hàng và phân loại từng nguồn."""
    if not isinstance(account_source_details, list) or len(account_source_details) == 0:
        return [("Khác", 1.0)]

    weight = 1.0 / len(account_source_details)
    result = []
    for source_item in account_source_details:
        label = source_item.get("label", "") if isinstance(source_item, dict) else ""
        result.append((classifier(label), weight))
    return result


def expand_sources_with_weights(account_source_details):
    """
    Mở rộng danh sách nguồn với trọng số.
    Mỗi khách hàng có N nguồn → mỗi nguồn được 1/N trọng số.
    
    Returns:
        List of tuples: [(source_classified, weight), ...]
    """
    return _expand_sources_with_classifier(account_source_details, classify_source_with_priority)


def expand_report_3_sources_with_weights(account_source_details):
    """Mở rộng nguồn theo trọng số với bộ phân loại riêng của Báo cáo 3."""
    return _expand_sources_with_classifier(account_source_details, classify_report_3_source)


def transform_dataframe(df, src_ids, type_ids, account_types_list, users_list=None):
    """
    Biến đổi DataFrame thô từ API thành DataFrame sạch cho báo cáo.

    Thực hiện:
    1. Lọc và tách nguồn khách hàng thành list
    2. Đổi tên cột cho dễ đọc
    3. Trích xuất đợt học thử từ custom fields
    4. Map ID nhóm khách hàng sang tên
    4.5. Map người phụ trách sang tên phòng ban
    5. Xử lý giá trị NaN

    Args:
        df: DataFrame thô từ API
        src_ids: List ID nguồn đã lọc (để filter nguồn trong mỗi record)
        type_ids: List ID nhóm khách hàng đã lọc
        account_types_list: Toàn bộ danh sách nhóm khách hàng từ API (dùng để map tên)
        users_list: Danh sách người dùng từ API (dùng để lấy phòng ban)

    Returns:
        pd.DataFrame: DataFrame đã biến đổi, sẵn sàng cho báo cáo
    """
    # 1. Xử lý cột nguồn khách hàng (lồng nhau) → list
    df["_nguon_kh_list"] = df.get("account_source_details", pd.Series(dtype=object)).apply(
        lambda x: _get_filtered_sources(x, src_ids)
    )

    # 2. Đổi tên các trường API cho giống format báo cáo
    df.rename(columns={
        "relation_name": "Mối quan hệ",
        "mgr_display_name": "Người phụ trách",
        "account_code": "Mã KH"
    }, inplace=True)

    # 3. Trích xuất "ĐỢT HỌC THỬ" từ custom fields
    if "detail_custom_fields" in df.columns:
        df["ĐỢT HỌC THỬ"] = df["detail_custom_fields"].apply(_get_dot_hoc_thu)
    else:
        df["ĐỢT HỌC THỬ"] = "Chưa xác định"

    # 4. Map nhóm khách hàng từ ID sang tên
    type_map = {str(item["id"]): item.get("account_type_name", "") for item in account_types_list if "id" in item}

    if "account_type" in df.columns:
        df["Nhóm khách hàng"] = df["account_type"].apply(
            lambda val: _map_account_types(val, type_map, type_ids)
        )
    else:
        df["Nhóm khách hàng"] = "Nhóm Chung"

    # 4.5. Map account_manager sang phòng ban
    if "account_manager" in df.columns and users_list:
        user_to_dept = {}
        for u in users_list:
            u_id = u.get("user_id")
            if u_id is not None:
                dept_name = u.get("dept_name") or "Chưa xác định"
                user_to_dept[str(u_id)] = dept_name
                try:
                    user_to_dept[int(u_id)] = dept_name
                except (ValueError, TypeError):
                    pass
        df["Phòng ban"] = df["account_manager"].map(user_to_dept).fillna("Chưa xác định")
    else:
        df["Phòng ban"] = "Chưa xác định"

    # 5. Đảm bảo không có giá trị NaN làm gãy thuật toán
    df["Mối quan hệ"] = df["Mối quan hệ"].fillna("CHƯA XÁC ĐỊNH")
    df["Người phụ trách"] = df["Người phụ trách"].fillna("Chưa phân bổ")

    # 6. Thêm cột phân loại nhóm tuổi từ description
    if "description" in df.columns:
        df["Nhóm tuổi"] = df["description"].apply(classify_age_group)
    else:
        # Fallback nếu API không trả về description
        df["Nhóm tuổi"] = "SALE CHƯA ĐIỀN & ĐIỀN TRÙNG"
    
    # 7. Thêm cột nguồn với trọng số riêng cho Báo cáo 2 và 3.
    source_details = df.get(
        "account_source_details",
        pd.Series(index=df.index, dtype=object),
    )
    df["_sources_with_weights"] = source_details.apply(
        expand_sources_with_weights
    )
    df["_report_3_sources_with_weights"] = source_details.apply(
        expand_report_3_sources_with_weights
    )

    return df
