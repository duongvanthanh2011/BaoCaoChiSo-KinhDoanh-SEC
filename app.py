import streamlit as st
import pandas as pd
import io

# Cấu hình giao diện rộng rãi
st.set_page_config(page_title="Tổng hợp Báo cáo Học viên", layout="wide")
st.title("📊 Hệ thống Tổng hợp & Phân tích Dữ liệu Học viên")

# 1. Tải file đầu vào
uploaded_file = st.file_uploader("Vui lòng tải lên file Excel dữ liệu gốc (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Đọc dữ liệu
        df = pd.read_excel(uploaded_file)
        
        # Kiểm tra đầy đủ các cột bắt buộc
        required_columns = ["Mối quan hệ", "Người phụ trách", "ĐỢT HỌC THỬ", "Nguồn khách hàng", "Nhóm khách hàng", "Mã KH"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.error(f"File tải lên thiếu các cột bắt buộc sau: {', '.join(missing_cols)}")
        else:
            # ==========================================
            # BỘ LỌC DỮ LIỆU (Lọc trước khi tính toán)
            # ==========================================
            st.markdown("---")
            st.subheader("🔍 Bộ lọc dữ liệu")
            
            # Tạo 4 cột cho 4 bộ lọc để giao diện cân đối
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                filter_dot_hoc = st.multiselect("ĐỢT HỌC THỬ", options=df["ĐỢT HỌC THỬ"].dropna().unique())
            with col2:
                filter_phu_trach = st.multiselect("Người phụ trách", options=df["Người phụ trách"].dropna().unique())
            with col3:
                filter_nguon = st.multiselect("Nguồn khách hàng", options=df["Nguồn khách hàng"].dropna().unique())
            with col4:
                filter_nhom = st.multiselect("Nhóm khách hàng", options=df["Nhóm khách hàng"].dropna().unique())

            # Áp dụng điều kiện lọc vào DataFrame gốc
            filtered_df = df.copy()
            if filter_dot_hoc:
                filtered_df = filtered_df[filtered_df["ĐỢT HỌC THỬ"].isin(filter_dot_hoc)]
            if filter_phu_trach:
                filtered_df = filtered_df[filtered_df["Người phụ trách"].isin(filter_phu_trach)]
            if filter_nguon:
                filtered_df = filtered_df[filtered_df["Nguồn khách hàng"].isin(filter_nguon)]
            if filter_nhom:
                filtered_df = filtered_df[filtered_df["Nhóm khách hàng"].isin(filter_nhom)]

            # Kiểm tra xem sau khi lọc còn dữ liệu không
            if filtered_df.empty:
                st.warning("Không có dữ liệu nào khớp với điều kiện lọc hiện tại. Vui lòng thử lại!")
            else:
                with st.spinner("Đang tự động xử lý các luồng báo cáo..."):
                    # 1. Định nghĩa các nhãn thuộc mỗi nhóm
                    trao_doi_labels = ["ĐANG TRAO ĐỔI", "HỌC VIÊN TIỀM NĂNG", "ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]
                    tiem_nang_labels = ["HỌC VIÊN TIỀM NĂNG", "ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]
                    coc_chot_labels = ["ĐÃ CỌC", "ĐÃ CHỐT - TIỀM NĂNG UPSALE", "ĐÃ CHỐT FULL"]

                    # 2. Tạo các cột chỉ báo (0/1) TRÊN DỮ LIỆU ĐÃ LỌC (filtered_df)
                    filtered_df["Data_trao_doi_duoc"] = filtered_df["Mối quan hệ"].isin(trao_doi_labels).astype(int)
                    filtered_df["Data_tiem_nang"]     = filtered_df["Mối quan hệ"].isin(tiem_nang_labels).astype(int)
                    filtered_df["Data_coc_chot"]      = filtered_df["Mối quan hệ"].isin(coc_chot_labels).astype(int)

                    # ==========================================
                    # BÁO CÁO 1
                    # ==========================================
                    result = (
                        filtered_df
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

                    # ==========================================
                    # BÁO CÁO 2
                    # ==========================================
                    result_2 = (
                        filtered_df
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
                    # Kết hợp background_gradient và format để hiển thị chính xác
                    styled_1 = result.style.background_gradient(cmap='Blues_r', subset=num_cols_1).format(format_dict_1)
                    st.dataframe(styled_1, width='stretch')

                    buffer_1 = io.BytesIO()
                    with pd.ExcelWriter(buffer_1, engine='openpyxl') as writer:
                        # Vẫn dùng round(2) trước khi xuất Excel để file Excel nhận đúng số
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
                    # Kết hợp background_gradient và format để hiển thị chính xác
                    styled_2 = result_2.style.background_gradient(cmap='Greens_r', subset=num_cols_2).format(format_dict_2)
                    st.dataframe(styled_2, use_container_width=True)

                    buffer_2 = io.BytesIO()
                    with pd.ExcelWriter(buffer_2, engine='openpyxl') as writer:
                        # Vẫn dùng round(2) trước khi xuất Excel để file Excel nhận đúng số
                        result_2.round(2).to_excel(writer, sheet_name='BC_Nguon_Nhom_KH')
                    
                    st.download_button(
                        label="📥 Tải xuống Báo cáo 2 (Excel)",
                        data=buffer_2.getvalue(),
                        file_name="Bao_cao_Nguon_Khach_Hang.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý cấu trúc dữ liệu: {e}")