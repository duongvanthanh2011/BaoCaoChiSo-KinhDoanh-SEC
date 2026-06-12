import streamlit as st
import pandas as pd
import requests
import io
import os
from dotenv import load_dotenv
from datetime import datetime

# Load biến môi trường từ file .env
load_dotenv()
API_KEY = os.getenv("GETFLY_API_KEY")
if not API_KEY and "GETFLY_API_KEY" in st.secrets:
    API_KEY = st.secrets["GETFLY_API_KEY"]

URL_BASE = os.getenv("GETFLY_URL_BASE")
if not URL_BASE and "GETFLY_URL_BASE" in st.secrets:
    URL_BASE = st.secrets["GETFLY_URL_BASE"]
if not URL_BASE:
    URL_BASE = "https://sec.getflycrm.com"


HEADERS = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

# ==========================================
# 0. HÀM CACHE LẤY DỮ LIỆU DANH MỤC TỪ API
# ==========================================
@st.cache_data(ttl=600)
def get_account_types(api_key, url_base):
    if not api_key:
        return []
    url = f"{url_base}/api/v6.1/account_types"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    params = {
        "fields": "id,level,account_type_name,account_type_code,description,invalid,parent_id",
        "limit": 1000
    }
    try:
        res = requests.get(url, headers=headers, params=params, json=params, timeout=15)
        res.raise_for_status()
        return res.json().get("data", [])
    except Exception as e:
        st.warning(f"⚠️ Không thể tải danh sách Nhóm khách hàng: {e}")
        return []

@st.cache_data(ttl=600)
def get_account_sources(api_key, url_base):
    if not api_key:
        return []
    url = f"{url_base}/api/v6.1/account_sources"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    params = {
        "fields": "id,source_name,source_code,valid,parent_id,lft,rgt,lvl",
        "limit": 1000
    }
    try:
        res = requests.get(url, headers=headers, params=params, json=params, timeout=15)
        res.raise_for_status()
        return res.json().get("data", [])
    except Exception as e:
        st.warning(f"⚠️ Không thể tải danh sách Nguồn khách hàng: {e}")
        return []

@st.cache_data(ttl=600)
def get_users(api_key, url_base):
    if not api_key:
        return []
    url = f"{url_base}/api/v6.1/users"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    users = []
    offset = 0
    limit = 1000
    has_more = True
    try:
        while has_more:
            params = {
                "fields": "user_id,contact_name,user_name,dept_id,dept_name",
                "limit": limit,
                "offset": offset
            }
            res = requests.get(url, headers=headers, params=params, json=params, timeout=15)
            res.raise_for_status()
            data_response = res.json()
            batch = data_response.get("data", [])
            if not batch:
                break
            users.extend(batch)
            has_more = data_response.get("has_more", False)
            if has_more:
                offset += limit
            else:
                break
        return users
    except Exception as e:
        st.warning(f"⚠️ Không thể tải danh sách Người phụ trách: {e}")
        return []

# Tải trước dữ liệu danh mục để đưa vào bộ lọc
account_types_list = get_account_types(API_KEY, URL_BASE)
account_sources_list = get_account_sources(API_KEY, URL_BASE)
users_list = get_users(API_KEY, URL_BASE)

# Cấu hình giao diện rộng rãi
st.set_page_config(page_title="Tổng hợp Báo cáo Học viên", layout="wide")
st.title("📊 Tổng hợp & Phân tích Dữ liệu Học viên (Tích hợp API)")

# Khởi tạo session state để lưu trữ dữ liệu sau khi lấy từ API nhằm hỗ trợ bộ lọc hậu kỳ (post-filter)
if "raw_df" not in st.session_state:
    st.session_state["raw_df"] = None
if "filtered_src_ids" not in st.session_state:
    st.session_state["filtered_src_ids"] = []
if "filtered_type_ids" not in st.session_state:
    st.session_state["filtered_type_ids"] = []

if not API_KEY:
    st.warning("⚠️ Chưa cấu hình `GETFLY_API_KEY` trong file `.env`. Hãy cấu hình để sử dụng đầy đủ chức năng.")

# ==========================================
# 1. GIAO DIỆN CHỌN BỘ LỌC (Lọc từ API)
# ==========================================
st.markdown("---")
st.subheader("🔍 Thiết lập tham số tải dữ liệu")
st.info("Chọn các điều kiện bên dưới để tối ưu lượng dữ liệu tải từ hệ thống. NẾU KHÔNG CHỌN BỘ LỌC THÌ DỮ LIỆU TRẢ VỀ RẤT LÂU")

# Sắp xếp các lựa chọn để hiển thị đẹp mắt
account_types_options = sorted(account_types_list, key=lambda x: x.get("account_type_name") or "")
account_sources_options = sorted(account_sources_list, key=lambda x: x.get("lft") or 0)
users_options = sorted(users_list, key=lambda x: x.get("contact_name") or "")

# Tạo form để người dùng điền thông số trước khi gọi API
with st.form("api_filter_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        selected_managers = st.multiselect(
            "Người phụ trách",
            options=users_options,
            format_func=lambda x: f"{x.get('contact_name')} ({x.get('dept_name', 'Chưa rõ')})" if x.get('dept_name') else x.get('contact_name'),
            help="Chọn một hoặc nhiều người phụ trách. Để trống để tải tất cả."
        )
        today = datetime.today().date()
        first_day_of_month = today.replace(day=1)
        date_range = st.date_input("Khoảng ngày tạo (Created_at)", [first_day_of_month, today])


    with col2:
        selected_sources = st.multiselect(
            "Nguồn khách hàng",
            options=account_sources_options,
            format_func=lambda x: ("— " * max(0, (x.get("lvl", 1) - 1))) + x.get("source_name", ""),
            help="Chọn nguồn cha sẽ tự động bao gồm tất cả nguồn con. Để trống để tải tất cả."
        )
        selected_types = st.multiselect(
            "Nhóm khách hàng",
            options=account_types_options,
            format_func=lambda x: x.get("account_type_name"),
            help="Chọn một hoặc nhiều nhóm khách hàng. Để trống để tải tất cả."
        )

    submitted = st.form_submit_button("🚀 Tải dữ liệu & Tạo báo cáo")

# ==========================================
# 2. XỬ LÝ GỌI API & CHUẨN BỊ DỮ LIỆU
# ==========================================
if submitted:
    if not API_KEY:
        st.error("Chưa cấu hình GETFLY_API_KEY trong file .env")
        st.stop()

    with st.spinner("Đang kết nối API và tải dữ liệu (có thể mất vài giây nếu dữ liệu lớn)..."):
        # 2.1. Xây dựng bộ lọc cho API (Cấu trúc "filtering" theo docs của Getfly)
        filtering_conditions = {}
        src_ids = []
        type_ids = []
        
        if selected_managers:
            mgr_ids = [int(x["user_id"]) for x in selected_managers if "user_id" in x]
            if mgr_ids:
                filtering_conditions["account_manager:in"] = mgr_ids
                
        if selected_sources:
            # Mở rộng danh sách nguồn: nếu chọn nguồn cha thì tự động thêm tất cả nguồn con
            # sử dụng mô hình Nested Set (lft/rgt)
            src_ids_selected = [int(x["id"]) for x in selected_sources if "id" in x]
            src_ids = list(src_ids_selected)  # bắt đầu với các nguồn đã chọn trực tiếp
            for parent in selected_sources:
                p_lft = parent.get("lft", 0)
                p_rgt = parent.get("rgt", 0)
                if p_lft and p_rgt and p_rgt > p_lft + 1:
                    # Nguồn này có con (rgt > lft + 1 trong nested set)
                    for child in account_sources_list:
                        c_lft = child.get("lft", 0)
                        c_rgt = child.get("rgt", 0)
                        c_id = child.get("id")
                        if c_lft > p_lft and c_rgt < p_rgt and c_id not in src_ids:
                            src_ids.append(int(c_id))
            if src_ids:
                filtering_conditions["account_source:in"] = src_ids

        if selected_types:
            type_ids = [int(x["id"]) for x in selected_types if "id" in x]
            if type_ids:
                filtering_conditions["account_type:in"] = type_ids

        # Nếu có chọn ngày (from - to)
        if len(date_range) == 2:
            start_date = date_range[0].strftime("%Y-%m-%d")
            end_date = date_range[1].strftime("%Y-%m-%d")
            filtering_conditions["created_at:gte"] = start_date
            filtering_conditions["created_at:lte"] = end_date

        # 2.2. Vòng lặp lấy toàn bộ dữ liệu thỏa mãn điều kiện (Paginator)
        all_records = []
        offset = 0
        limit = 3000  # Khuyên dùng: Giảm xuống 2000 để API xử lý nhanh hơn, tránh bị treo giữa chừng
        
        url = f"{URL_BASE}/api/v6.1/accounts"
        has_more = True
        
        while has_more:
            params = {
                "fields": "id,created_at,detail_custom_fields,account_code,account_name,account_manager,relation_id,mgr_display_name,relation_name,account_source,account_source_details,detail_custom_fields_display_value,account_type",
                "limit": limit,
                "offset": offset
            }
            
            # Nếu có điều kiện lọc, chuyển đổi cấu trúc phù hợp với URL Query của Getfly
            if filtering_conditions:
                params["filtering"] = filtering_conditions 

            try:
                # SỬA: Chuyển từ json= sang params= để truyền lên URL, thêm timeout=30 giây
                res = requests.get(url, headers=HEADERS, json=params, timeout=60)
                res.raise_for_status()
                data_response = res.json()
                
                batch_data = data_response.get("data", [])
                
                # Kiểm tra nếu API trả về mảng rỗng thì dừng ngay lập tức
                if not batch_data or len(batch_data) == 0:
                    break
                    
                all_records.extend(batch_data)
                
                # Kiểm tra trường "has_more" từ phản hồi của API để tiếp tục hoặc dừng
                has_more = data_response.get("has_more", False)
                if has_more:
                    offset += limit
                
            except requests.exceptions.Timeout:
                st.error("⏳ API quá tải hoặc phản hồi quá lâu (Timeout). Hãy giảm giá trị 'limit' xuống hoặc thắt chặt bộ lọc ngày để giảm lượng dữ liệu.")
                st.stop()
            except Exception as e:
                st.error(f"❌ Lỗi phát sinh khi gọi API: {e}")
                st.stop()
                
        if not all_records:
             st.warning("Không tìm thấy dữ liệu nào phù hợp với bộ lọc.")
             st.stop()
             
        # 2.3. Chuyển đổi JSON thành DataFrame và Mapping tên cột
        df = pd.DataFrame(all_records)
        
        # Xử lý các cột lồng nhau (Nested JSON): tách từng nguồn khách hàng thành danh sách riêng biệt
        # Mỗi bản ghi có N nguồn sẽ được nhân thành N dòng,
        # ta lưu dạng list để sau này explode cho Báo cáo 2
        # SỬA: Lọc nguồn khách hàng theo bộ lọc nếu có lọc theo nguồn
        def get_filtered_sources(x):
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

        df["_nguon_kh_list"] = df.get("account_source_details", pd.Series(dtype=object)).apply(get_filtered_sources)
        
        # Đổi tên các trường API cho giống format file Excel cũ
        # LƯU Ý: Trường "ĐỢT HỌC THỬ" và "Nhóm khách hàng" hiện không có trong API Response mẫu bạn cung cấp.
        # Tạm thời gán bằng một giá trị mặc định để logic Báo cáo cũ không bị gãy (Missing column).
        # Bạn cần tìm field tương ứng trong Getfly để map vào đây (có thể từ custom_fields).
        df.rename(columns={
            "relation_name": "Mối quan hệ",
            "mgr_display_name": "Người phụ trách",
            "account_code": "Mã KH"
        }, inplace=True)
        
        # Trích xuất "dot_hoc_thu" từ "detail_custom_fields" và định dạng thành ngày nếu là Unix timestamp
        def get_dot_hoc_thu(fields):
            if not isinstance(fields, dict):
                return "Chưa xác định"
            val = fields.get("dot_hoc_thu")
            if val is None or val == "" or val == []:
                return "Chưa xác định"
            try:
                ts = int(float(str(val)))
                if 946684800 < ts < 4102444800:
                    return datetime.fromtimestamp(ts).strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass
            return str(val)

        if "detail_custom_fields" in df.columns:
            df["ĐỢT HỌC THỬ"] = df["detail_custom_fields"].apply(get_dot_hoc_thu)
        else:
            df["ĐỢT HỌC THỬ"] = "Chưa xác định"

        # Bản đồ tên loại khách hàng từ account_types_list
        type_map = {str(item["id"]): item.get("account_type_name", "") for item in account_types_list if "id" in item}
        
        def map_account_types(val):
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

        if "account_type" in df.columns:
            df["Nhóm khách hàng"] = df["account_type"].apply(map_account_types)
        else:
            df["Nhóm khách hàng"] = "Nhóm Chung"

        # Đảm bảo không có giá trị NaN làm gãy thuật toán
        df["Mối quan hệ"] = df["Mối quan hệ"].fillna("CHƯA XÁC ĐỊNH")
        df["Người phụ trách"] = df["Người phụ trách"].fillna("Chưa phân bổ")

        st.session_state["raw_df"] = df
        st.session_state["filtered_src_ids"] = src_ids
        st.session_state["filtered_type_ids"] = type_ids
        st.success(f"Đã tải thành công {len(df)} bản ghi từ hệ thống.")

# ==========================================
# 3. HIỂN THỊ BÁO CÁO & BỘ LỌC SAU KHI TẢI DỮ LIỆU
# ==========================================
if st.session_state["raw_df"] is not None:
    df_raw = st.session_state["raw_df"]
    src_ids = st.session_state["filtered_src_ids"]
    type_ids = st.session_state["filtered_type_ids"]

    st.markdown("---")
    st.subheader("⚙️ Bộ lọc báo cáo (Sau khi tải dữ liệu)")
    
    # Lấy danh sách đợt học thử duy nhất từ dữ liệu đã tải
    unique_sessions = sorted([str(x) for x in df_raw["ĐỢT HỌC THỬ"].unique() if x is not None])
    
    selected_sessions = st.multiselect(
        "Lọc theo Đợt học thử",
        options=unique_sessions,
        default=unique_sessions,
        help="Chọn một hoặc nhiều đợt học thử để tính toán lại báo cáo bên dưới."
    )
    
    # Lọc dữ liệu theo đợt học thử đã chọn
    if selected_sessions:
        df_filtered = df_raw[df_raw["ĐỢT HỌC THỬ"].isin(selected_sessions)].copy()
    else:
        df_filtered = df_raw.copy()

    # Bắt đầu tính toán báo cáo từ dữ liệu đã lọc
    with st.spinner("Đang tự động xử lý các luồng báo cáo..."):
        # 1. Định nghĩa các nhãn thuộc mỗi nhóm
        trao_doi_labels = ["ĐANG TRAO ĐỔI", "HỌC VIÊN TIỀM NĂNG", "ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]
        tiem_nang_labels = ["HỌC VIÊN TIỀM NĂNG", "ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]
        coc_chot_labels = ["ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]

        # 2. Tạo các cột chỉ báo (0/1) TRÊN DỮ LIỆU ĐÃ LỌC
        df_filtered["Data_trao_doi_duoc"] = df_filtered["Mối quan hệ"].isin(trao_doi_labels).astype(int)
        df_filtered["Data_tiem_nang"]     = df_filtered["Mối quan hệ"].isin(tiem_nang_labels).astype(int)
        df_filtered["Data_coc_chot"]      = df_filtered["Mối quan hệ"].isin(coc_chot_labels).astype(int)

        # ==========================================
        # BÁO CÁO 1
        # ==========================================
        result = (
            df_filtered
            .groupby(["ĐỢT HỌC THỬ", "Người phụ trách"])
            .agg(
                Data_trao_doi_duoc=("Data_trao_doi_duoc", "sum"),
                Data_tiem_nang=("Data_tiem_nang", "sum"),
                Data_coc_chot=("Data_coc_chot", "sum"),
                Count=("Mã KH", "count"),
            )
        )

        result['Tỉ lệ trao đổi được'] = (result['Data_trao_doi_duoc'] / result['Count']) * 100
        result['Tỉ lệ tiềm năng'] = (result['Data_tiem_nang'] / result['Count']) * 100
        result['Tỉ lệ cọc/chốt'] = (result['Data_coc_chot'] / result['Count']) * 100
        result = result.fillna(0) # Tránh lỗi chia cho 0 nếu có

        # Bổ sung thêm dòng TỔNG CỘNG ở cuối bảng
        if not result.empty:
            result.loc[("TỔNG CỘNG", ""), :] = [
                result["Data_trao_doi_duoc"].sum(),
                result["Data_tiem_nang"].sum(),
                result["Data_coc_chot"].sum(),
                result["Count"].sum(),
                result["Tỉ lệ trao đổi được"].mean(),
                result["Tỉ lệ tiềm năng"].mean(),
                result["Tỉ lệ cọc/chốt"].mean()
            ]
            int_cols_1 = ["Data_trao_doi_duoc", "Data_tiem_nang", "Data_coc_chot", "Count"]
            result[int_cols_1] = result[int_cols_1].astype(int)

        # ==========================================
        # BÁO CÁO 2 — Tách từng nguồn riêng biệt (explode)
        # ==========================================
        df_exploded = df_filtered.explode("_nguon_kh_list").copy()
        df_exploded.rename(columns={"_nguon_kh_list": "Nguồn khách hàng"}, inplace=True)

        result_2 = (
            df_exploded
            .groupby(["Nguồn khách hàng", "Nhóm khách hàng"])
            .agg(
                Data_trao_doi_duoc=("Data_trao_doi_duoc", "sum"),
                Data_tiem_nang=("Data_tiem_nang", "sum"),
                Data_coc_chot=("Data_coc_chot", "sum"),
                Count=("Mã KH", "count"),
            )
        )

        result_2['Tỉ lệ trao đổi được (%)'] = (result_2['Data_trao_doi_duoc'] / result_2['Count']) * 100
        result_2['Tỉ lệ tiềm năng (%)'] = (result_2['Data_tiem_nang'] / result_2['Count']) * 100
        result_2['Tỉ lệ cọc/chốt (%)'] = (result_2['Data_coc_chot'] / result_2['Count']) * 100
        result_2 = result_2.fillna(0)
        result_2.rename_axis(["Nguồn khách hàng", "Nhóm khách hàng"], inplace=True)

        # Bổ sung thêm dòng TỔNG CỘNG ở cuối bảng
        if not result_2.empty:
            result_2.loc[("TỔNG CỘNG", ""), :] = [
                result_2["Data_trao_doi_duoc"].sum(),
                result_2["Data_tiem_nang"].sum(),
                result_2["Data_coc_chot"].sum(),
                result_2["Count"].sum(),
                result_2["Tỉ lệ trao đổi được (%)"].mean(),
                result_2["Tỉ lệ tiềm năng (%)"].mean(),
                result_2["Tỉ lệ cọc/chốt (%)"].mean()
            ]
            int_cols_2 = ["Data_trao_doi_duoc", "Data_tiem_nang", "Data_coc_chot", "Count"]
            result_2[int_cols_2] = result_2[int_cols_2].astype(int)

    st.success("Tạo báo cáo thành công!")

    tab1, tab2 = st.tabs(["📋 Báo cáo 1: Theo Đợt học thử & Người phụ trách", "🌐 Báo cáo 2: Theo Nguồn khách hàng & Nhóm"])

    # Định dạng các cột số để giải quyết triệt để lỗi số thập phân
    num_cols_1 = ['Data_trao_doi_duoc', 'Data_tiem_nang', 'Data_coc_chot', 'Count', 'Tỉ lệ trao đổi được', 'Tỉ lệ tiềm năng', 'Tỉ lệ cọc/chốt']
    num_cols_2 = ['Data_trao_doi_duoc', 'Data_tiem_nang', 'Data_coc_chot', 'Count', 'Tỉ lệ trao đổi được (%)', 'Tỉ lệ tiềm năng (%)', 'Tỉ lệ cọc/chốt (%)']
    
    # Cấu hình format hiển thị cho Styler (giữ 2 chữ số thập phân)
    format_dict_1 = {'Tỉ lệ trao đổi được': "{:.2f}", 'Tỉ lệ tiềm năng': "{:.2f}", 'Tỉ lệ cọc/chốt': "{:.2f}"}
    format_dict_2 = {'Tỉ lệ trao đổi được (%)': "{:.2f}", 'Tỉ lệ tiềm năng (%)': "{:.2f}", 'Tỉ lệ cọc/chốt (%)': "{:.2f}"}

    # --- GIAO DIỆN TAB 1 ---
    with tab1:
        st.subheader("Bản xem trước: Báo cáo theo Đợt học thử & Người phụ trách")
        styled_1 = result.style.background_gradient(cmap='Blues_r', subset=num_cols_1).format(format_dict_1)
        st.dataframe(styled_1, width='stretch')

        buffer_1 = io.BytesIO()
        with pd.ExcelWriter(buffer_1, engine='openpyxl') as writer:
            result.round(2).to_excel(writer, sheet_name='BC_Hoc_Thu_Phu_Trach')
        
        st.download_button(
            label="📥 Tải xuống Báo cáo 1 (Excel)",
            data=buffer_1.getvalue(),
            file_name="Bao_cao_Dot_Hoc_Thu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- GIAO DIỆN TAB 2 ---
    with tab2:
        st.subheader("Bản xem trước: Báo cáo theo Nguồn khách hàng & Nhóm khách hàng")
        styled_2 = result_2.style.background_gradient(cmap='Greens_r', subset=num_cols_2).format(format_dict_2)
        st.dataframe(styled_2, use_container_width=True)

        buffer_2 = io.BytesIO()
        with pd.ExcelWriter(buffer_2, engine='openpyxl') as writer:
            result_2.round(2).to_excel(writer, sheet_name='BC_Nguon_Nhom_KH')
        
        st.download_button(
            label="📥 Tải xuống Báo cáo 2 (Excel)",
            data=buffer_2.getvalue(),
            file_name="Bao_cao_Nguon_Khach_Hang.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )