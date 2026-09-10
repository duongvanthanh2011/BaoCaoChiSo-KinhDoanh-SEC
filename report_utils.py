"""
report_utils.py — Tiện ích và cấu hình dùng chung cho báo cáo
Chứa:
- Nhãn phân loại mối quan hệ
- Các đối tượng định dạng JS (valueFormatter, cellStyle, valueGetter) cho AgGrid
- Các hàm cấu hình cột và đồng bộ trạng thái chỉnh sửa dùng chung
"""

import streamlit as st
import pandas as pd
from st_aggrid.shared import JsCode

# ==========================================
# NHÃN PHÂN LOẠI MỐI QUAN HỆ
# ==========================================
TRAO_DOI_LABELS = [
    "ĐANG TRAO ĐỔI",
    "HỌC VIÊN TIỀM NĂNG",
    "ĐÃ CỌC",
    "ĐÃ CHỐT - TIỀM NĂNG UPSALE",
    "ĐÃ CHỐT FULL",
]

TIEM_NANG_LABELS = [
    "HỌC VIÊN TIỀM NĂNG",
    "ĐÃ CỌC",
    "ĐÃ CHỐT - TIỀM NĂNG UPSALE",
    "ĐÃ CHỐT FULL",
]

COC_CHOT_LABELS = [
    "ĐÃ CỌC",
    "ĐÃ CHỐT - TIỀM NĂNG UPSALE",
    "ĐÃ CHỐT FULL",
]

COC_COL_SUFFIX = " (Cọc Chốt)"

SAI_SO_SAI_DOI_TUONG_LABELS = [
    "SAI SỐ",
    "SAI ĐỐI TƯỢNG.",
    "SAI SỐ - SAI ĐỐI TƯỢNG",
]

TIEM_NANG_CHUA_GOI_LABELS = [
    "TIỀM NĂNG CHƯA GỌI CVHT",
    "DATA MỚI CHƯA GỌI CVHT",
    "DATA CHƯA GỌI CVHT BACK LẠI",
]

CHUA_TRAO_DOI_AUTO_CALL_LABELS = [
    "CHƯA TRAO ĐỔI ĐƯỢCC",
    "CHƯA TRAO ĐỔI ĐƯỢC",
    "AUTO CALL",
]

# ==========================================
# CẤU HÌNH PHẦN TRĂM & TÔ MÀU KPI CHO AGGRID
# ==========================================

# Formatter hiển thị tỉ lệ phần trăm
pct_formatter = JsCode("""
function(params) {
    if (params.value === undefined || params.value === null) {
        return '';
    }
    return Number(params.value).toFixed(2) + '%';
}
""")

# Luật tô màu nền KPI dựa trên giá trị phần trăm
style_pct_saiso = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val > 7) return {'backgroundColor':'#ffcccc'};
    if (val >= 3) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ccffcc'};
}
""")

style_pct_tn_chua_goi = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    return val > 0 ? {'backgroundColor':'#ffcccc'} : {'backgroundColor':'#ccffcc'};
}
""")

style_pct_chua_trao_doi_autocall = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 30) return {'backgroundColor':'#ffcccc'};
    if (val >= 20) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ccffcc'};
}
""")

style_pct_traodoi = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 60) return {'backgroundColor':'#ccffcc'};
    if (val >= 50) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ffcccc'};
}
""")

style_pct_tiemnang = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 30) return {'backgroundColor':'#ccffcc'};
    if (val >= 25) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ffcccc'};
}
""")

style_pct_coc = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 15) return {'backgroundColor':'#ccffcc'};
    if (val >= 12) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ffcccc'};
}
""")


# JS Getters dùng để tính toán tỉ lệ động ở cả dòng con và dòng tổng nhóm (group / total footers)
getter_pct_saiso = JsCode("""
function(params) {
    var val = 0, total = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
    }
    return total ? (val / total * 100) : 0;
}
""")

getter_pct_tn_chua_goi = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Tiềm Năng Chưa Gọi'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Tiềm Năng Chưa Gọi'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

getter_pct_chua_trao_doi_autocall = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Data Chưa Trao Đổi + Auto Call'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Data Chưa Trao Đổi + Auto Call'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

getter_pct_traodoi = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Data Trao Đổi Được'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Data Trao Đổi Được'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

getter_pct_tiemnang = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Data Tiềm Năng'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Data Tiềm Năng'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

getter_pct_coc = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.group) {
        val = params.node.aggData ? (params.node.aggData['Data Cọc Chốt'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        val = params.data ? (params.data['Data Cọc Chốt'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

getter_pct_tong_coc = JsCode("""
function(params) {
    var val = 0, total = 0, saiSo = 0;
    if (params.node && params.node.rowPinned) {
        val = params.data ? (params.data['Tổng Cọc Học Thử'] || 0) : 0;
        total = params.data ? (params.data['Tổng số Data'] || 0) : 0;
        saiSo = params.data ? (params.data['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else if (params.node && (params.node.group || params.node.footer) && params.node.level === 0) {
        val = params.node.aggData ? (params.node.aggData['Tổng Cọc Học Thử'] || 0) : 0;
        total = params.node.aggData ? (params.node.aggData['Tổng số Data'] || 0) : 0;
        saiSo = params.node.aggData ? (params.node.aggData['Sai Số - Sai Đối Tượng'] || 0) : 0;
    } else {
        return null;
    }
    var base = total - saiSo;
    return base > 0 ? (val / base * 100) : 0;
}
""")

style_pct_tong_coc = JsCode("""
function(params){
    var val = params.value;
    if (val === undefined || val === null) return {};
    if (val >= 10) return {'backgroundColor':'#ccffcc'};
    if (val >= 7) return {'backgroundColor':'#fff2cc'};
    return {'backgroundColor':'#ffcccc'};
}
""")

# ==========================================
# JS GETTERS & STYLES CHO BÁO CÁO 2
# ==========================================

formatter_float_2_decimals = JsCode("""
function(params) {
    var val = params.value;
    if (val === undefined || val === null || val === '') {
        if (params.node && params.node.group && params.node.aggData) {
            val = params.node.aggData[params.colDef.field];
        }
    }
    if (val === undefined || val === null || val === '') return '0';
    var num = Number(val);
    if (isNaN(num)) return val;
    if (num === Math.floor(num)) return num.toString();
    return num.toFixed(2);
}
""")

formatter_r2_dot_manual_value = JsCode("""
function(params) {
    if (params.node && (params.node.rowPinned || params.node.group || params.node.footer)) {
        var val = params.value;
        if (val === undefined || val === null || val === '') {
            if (params.node.aggData) {
                val = params.node.aggData[params.colDef.field];
            }
        }
        if (val === undefined || val === null || val === '') return '';
        var num = Number(val);
        if (isNaN(num)) return val;
        return num.toString();
    }
    return '';
}
""")

formatter_r2_data_average = JsCode("""
function(params) {
    if (params.node && (params.node.rowPinned || params.node.group || params.node.footer)) {
        var val = params.value;
        if (val === undefined || val === null || val === '') {
            if (params.node.aggData) {
                val = params.node.aggData[params.colDef.field];
            }
        }
        if (val === undefined || val === null || val === '') return '';
        var num = Number(val);
        if (isNaN(num)) return val;
        return num.toFixed(2);
    }
    return '';
}
""")

getter_pct_r2_full = JsCode("""
function(params) {
    var totalData = 0, dataOrder = 0;
    if (params.node && params.node.rowPinned) {
        totalData = params.data ? (params.data['Tổng data chạy được'] || 0) : 0;
        dataOrder = params.data ? (params.data['Data order'] || 0) : 0;
    } else if (params.node && (params.node.group || params.node.footer) && params.node.level === 0) {
        totalData = params.node.aggData ? (params.node.aggData['Tổng data chạy được'] || 0) : 0;
        dataOrder = params.node.aggData ? (params.node.aggData['Data order'] || 0) : 0;
    } else {
        // Chỉ tính theo từng đợt, không tính riêng cho từng nhóm nguồn
        return null;
    }
    return dataOrder > 0 ? (totalData / dataOrder * 100) : 0;
}
""")

style_pct_r2_full = JsCode("""
function(params) {
    var val = params.value;
    if (val === undefined || val === null || isNaN(val)) return {};
    if (val >= 95 && val <= 105) return {'backgroundColor':'#ccffcc'};
    return {'backgroundColor':'#fff2cc'};
}
""")


# ==========================================
# JS GETTERS & FORMATTERS CHO BÁO CÁO 3
# ==========================================

formatter_r3_age_group = JsCode("""
class CellRenderer {
    init(params) {
        this.eGui = document.createElement('span');
        var colField = params.colDef.field;
        var cocField = colField + ' (Cọc Chốt)';
        var val = params.value;
        var cocVal = undefined;
        var total = 0;
        var cocTotal = 0;

        if (params.node && params.node.rowPinned) {
            if (val === undefined || val === null) {
                val = params.data ? (params.data[colField] || 0) : 0;
            }
            cocVal = params.data ? (params.data[cocField] || 0) : 0;
            total = params.data ? (params.data['TỔNG'] || 0) : 0;
            cocTotal = params.data ? (params.data['TỔNG (Cọc Chốt)'] || 0) : 0;
        } else if (params.node && (params.node.group || params.node.footer)) {
            if (params.node.aggData) {
                if (val === undefined || val === null) {
                    val = params.node.aggData[colField] || 0;
                }
                cocVal = params.node.aggData[cocField] || 0;
                total = params.node.aggData['TỔNG'] || 0;
                cocTotal = params.node.aggData['TỔNG (Cọc Chốt)'] || 0;
            } else if (params.data) {
                if (val === undefined || val === null) {
                    val = params.data[colField] || 0;
                }
                cocVal = params.data[cocField] || 0;
                total = params.data['TỔNG'] || 0;
                cocTotal = params.data['TỔNG (Cọc Chốt)'] || 0;
            }
        } else {
            if (params.data) {
                if (val === undefined || val === null) {
                    val = params.data[colField] || 0;
                }
                cocVal = params.data[cocField] || 0;
                total = params.data['TỔNG'] || 0;
                cocTotal = params.data['TỔNG (Cọc Chốt)'] || 0;
            }
        }

        if (val === undefined || val === null) {
            this.eGui.innerHTML = '';
            return;
        }

        var num = Number(val);
        if (isNaN(num)) num = 0;
        var numStr = (num % 1 === 0) ? num.toString() : num.toFixed(2);
        var pct = total > 0 ? (num / total * 100) : 0;

        var cocNum = Number(cocVal);
        if (isNaN(cocNum)) cocNum = 0;
        var cocNumStr = (cocNum % 1 === 0) ? cocNum.toString() : cocNum.toFixed(2);
        var cocPct = cocTotal > 0 ? (cocNum / cocTotal * 100) : 0;

        this.eGui.innerHTML = numStr + ' (' + pct.toFixed(2) + '%) / ' + '<span style="color:#1565C0;font-weight:600">' + cocNumStr + ' (' + cocPct.toFixed(2) + '%)</span>';
    }
    getGui() {
        return this.eGui;
    }
}
""")

style_r3_at_least_80_green = JsCode("""
function(params) {
    var val = params.value;
    if (val === undefined || val === null) {
        if (params.node && (params.node.group || params.node.footer) && params.node.aggData) {
            val = params.node.aggData[params.colDef.field] || 0;
        } else if (params.data) {
            val = params.data[params.colDef.field] || 0;
        } else {
            val = 0;
        }
    }

    var total = 0;
    if (params.node && (params.node.group || params.node.footer) && params.node.aggData) {
        total = params.node.aggData['TỔNG'] || 0;
    } else if (params.data) {
        total = params.data['TỔNG'] || 0;
    }

    var pct = total > 0 ? (Number(val) / Number(total) * 100) : 0;
    return pct >= 80
        ? {'backgroundColor': '#ccffcc'}
        : {'backgroundColor': '#ffcccc'};
}
""")

style_r3_at_most_20_green = JsCode("""
function(params) {
    var val = params.value;
    if (val === undefined || val === null) {
        if (params.node && (params.node.group || params.node.footer) && params.node.aggData) {
            val = params.node.aggData[params.colDef.field] || 0;
        } else if (params.data) {
            val = params.data[params.colDef.field] || 0;
        } else {
            val = 0;
        }
    }

    var total = 0;
    if (params.node && (params.node.group || params.node.footer) && params.node.aggData) {
        total = params.node.aggData['TỔNG'] || 0;
    } else if (params.data) {
        total = params.data['TỔNG'] || 0;
    }

    var pct = total > 0 ? (Number(val) / Number(total) * 100) : 0;
    return pct <= 20
        ? {'backgroundColor': '#ccffcc'}
        : {'backgroundColor': '#ffcccc'};
}
""")

formatter_r3_tong = JsCode("""
class CellRenderer {
    init(params) {
        this.eGui = document.createElement('span');
        var val = params.value;
        var cocVal = undefined;

        if (params.node && params.node.rowPinned) {
            if (val === undefined || val === null) {
                val = params.data ? (params.data['TỔNG'] || 0) : 0;
            }
            cocVal = params.data ? (params.data['TỔNG (Cọc Chốt)'] || 0) : 0;
        } else if (params.node && (params.node.group || params.node.footer)) {
            if (params.node.aggData) {
                if (val === undefined || val === null) {
                    val = params.node.aggData['TỔNG'] || 0;
                }
                cocVal = params.node.aggData['TỔNG (Cọc Chốt)'] || 0;
            } else if (params.data) {
                if (val === undefined || val === null) {
                    val = params.data['TỔNG'] || 0;
                }
                cocVal = params.data['TỔNG (Cọc Chốt)'] || 0;
            }
        } else {
            if (params.data) {
                if (val === undefined || val === null) {
                    val = params.data['TỔNG'] || 0;
                }
                cocVal = params.data['TỔNG (Cọc Chốt)'] || 0;
            }
        }

        if (val === undefined || val === null) {
            this.eGui.innerHTML = '';
            return;
        }

        var num = Number(val);
        if (isNaN(num)) num = 0;
        var numStr = (num % 1 === 0) ? num.toString() : num.toFixed(2);

        var cocNum = Number(cocVal);
        if (isNaN(cocNum)) cocNum = 0;
        var cocNumStr = (cocNum % 1 === 0) ? cocNum.toString() : cocNum.toFixed(2);

        var pct = 0;
        var cocPct = 0;

        if (params.node && params.node.rowPinned) {
            pct = 100;
            cocPct = 100;
        } else if (params.node && (params.node.group || params.node.footer) && params.node.level === 0) {
            var grandTotal = 0;
            var grandTotalCoc = 0;
            if (params.api && typeof params.api.getPinnedTopRow === 'function') {
                var topRow = params.api.getPinnedTopRow(0);
                if (topRow && topRow.data) {
                    grandTotal = topRow.data['TỔNG'] || 0;
                    grandTotalCoc = topRow.data['TỔNG (Cọc Chốt)'] || 0;
                }
            }
            pct = grandTotal > 0 ? (num / grandTotal * 100) : 100;
            cocPct = grandTotalCoc > 0 ? (cocNum / grandTotalCoc * 100) : (cocNum > 0 ? 100 : 0);
        } else if (params.node && params.node.parent && params.node.parent.aggData) {
            var dotTotal = params.node.parent.aggData['TỔNG'] || 0;
            var dotTotalCoc = params.node.parent.aggData['TỔNG (Cọc Chốt)'] || 0;
            pct = dotTotal > 0 ? (num / dotTotal * 100) : 0;
            cocPct = dotTotalCoc > 0 ? (cocNum / dotTotalCoc * 100) : 0;
        } else {
            pct = 100;
            cocPct = 100;
        }

        this.eGui.innerHTML = numStr + ' (' + pct.toFixed(2) + '%) / ' + '<span style="color:#1565C0;font-weight:600">' + cocNumStr + ' (' + cocPct.toFixed(2) + '%)</span>';
    }
    getGui() {
        return this.eGui;
    }
}
""")


# ==========================================

formatter_merged = JsCode("""
function(params) {
    var val = params.value || 0;
    var field = params.colDef.field;
    var baseField = (field === 'Sai Số - Sai Đối Tượng') ? 'Tổng số Data' : 'Tổng số data trừ sai số';
    var base = 0;
    if (params.node && params.node.group) {
        base = params.node.aggData ? (params.node.aggData[baseField] || 0) : 0;
    } else {
        base = params.data ? (params.data[baseField] || 0) : 0;
    }
    var pct = base ? (val / base * 100) : 0;
    return val + ' (' + pct.toFixed(2) + '%)';
}
""")

style_merged = JsCode("""
function(params) {
    var val = params.value || 0;
    var field = params.colDef.field;
    var baseField = (field === 'Sai Số - Sai Đối Tượng') ? 'Tổng số Data' : 'Tổng số data trừ sai số';
    var base = 0;
    if (params.node && params.node.group) {
        base = params.node.aggData ? (params.node.aggData[baseField] || 0) : 0;
    } else {
        base = params.data ? (params.data[baseField] || 0) : 0;
    }
    var pct = base ? (val / base * 100) : 0;
    
    if (field === 'Sai Số - Sai Đối Tượng') {
        if (pct > 7) return {'backgroundColor':'#ffcccc'};
        if (pct >= 3) return {'backgroundColor':'#fff2cc'};
        return {'backgroundColor':'#ccffcc'};
    }
    if (field === 'Tiềm Năng Chưa Gọi') {
        return pct > 0 ? {'backgroundColor':'#ffcccc'} : {'backgroundColor':'#ccffcc'};
    }
    if (field === 'Data Chưa Trao Đổi + Auto Call') {
        if (pct >= 30) return {'backgroundColor':'#ffcccc'};
        if (pct >= 20) return {'backgroundColor':'#fff2cc'};
        return {'backgroundColor':'#ccffcc'};
    }
    if (field === 'Data Trao Đổi Được') {
        if (pct >= 60) return {'backgroundColor':'#ccffcc'};
        if (pct >= 50) return {'backgroundColor':'#fff2cc'};
        return {'backgroundColor':'#ffcccc'};
    }
    if (field === 'Data Tiềm Năng') {
        if (pct >= 30) return {'backgroundColor':'#ccffcc'};
        if (pct >= 25) return {'backgroundColor':'#fff2cc'};
        return {'backgroundColor':'#ffcccc'};
    }
    if (field === 'Data Cọc Chốt') {
        if (pct >= 15) return {'backgroundColor':'#ccffcc'};
        if (pct >= 12) return {'backgroundColor':'#fff2cc'};
        return {'backgroundColor':'#ffcccc'};
    }
    return {};
}
""")


# ==========================================
# HÀM TIỆN ÍCH DÙNG CHUNG CHO BẢNG AGGRID
# ==========================================

def configure_standard_grid_columns(gb, count_cols):
    """
    Cấu hình các cột số lượng và cột tỷ lệ KPI chuẩn cho GridOptionsBuilder.
    Tái sử dụng cho cả Báo cáo 1 và Báo cáo 2 để loại bỏ lặp mã nguồn.
    """
    # Cấu hình tự động xuống dòng cho header
    gb.configure_default_column(wrapHeaderText=True, autoHeaderHeight=True)

    # Cọc Khác, Tổng Cọc Học Thử — ẩn khỏi grid, nhập tay ở bảng riêng theo đợt
    gb.configure_column("Cọc Khác", hide=True, aggFunc="sum", width=100)
    gb.configure_column("Tổng Cọc Học Thử", hide=True, aggFunc="sum", width=120)

    # Thiết lập hàm tính tổng (sum) cho các cột đếm
    for c in count_cols:
        # Nếu cột đếm là cột cần gộp với phần trăm, ta sẽ định nghĩa cụ thể bên dưới
        if c not in ["Sai Số - Sai Đối Tượng", "Tiềm Năng Chưa Gọi", "Data Chưa Trao Đổi + Auto Call", "Data Trao Đổi Được", "Data Tiềm Năng", "Data Cọc Chốt", "Cọc Khác", "Tổng Cọc Học Thử"]:
            gb.configure_column(c, aggFunc="sum", width=100 if len(c) < 15 else 115)

    # Cấu hình đặc biệt cho các cột số lượng gộp phần trăm
    gb.configure_column(
        "Sai Số - Sai Đối Tượng",
        headerName="% sai số-sai đối tượng/ Tổng data đã chia",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )
    gb.configure_column(
        "Tiềm Năng Chưa Gọi",
        headerName="% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )
    gb.configure_column(
        "Data Chưa Trao Đổi + Auto Call",
        headerName="% data Chưa trao đổi được + autocall / Tổng data đã chia trừ sai số-sai đối tượng",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        # cellStyle=style_merged,
        width=120
    )
    gb.configure_column(
        "Data Trao Đổi Được",
        headerName="% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )
    gb.configure_column(
        "Data Tiềm Năng",
        headerName="% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )
    gb.configure_column(
        "Data Cọc Chốt",
        headerName="% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng",
        aggFunc="sum",
        valueFormatter=formatter_merged,
        cellStyle=style_merged,
        width=120
    )

    # Ẩn các cột phần trăm cũ trên UI của AgGrid
    gb.configure_column("% sai số-sai đối tượng/ Tổng data đã chia", hide=True)
    gb.configure_column("% data tiềm năng chưa gọi / Tổng data đã chia trừ sai số-sai đối tượng", hide=True)
    gb.configure_column("% data Chưa trao đổi được + autocall / Tổng data đã chia trừ sai số-sai đối tượng", hide=True)
    gb.configure_column("% data trao đổi được / Tổng data đã chia trừ sai số-sai đối tượng", hide=True)
    gb.configure_column("% data tiềm năng / Tổng data đã chia trừ sai số-sai đối tượng", hide=True)
    gb.configure_column("% data cọc chốt / Tổng data đã chia trừ sai số-sai đối tượng", hide=True)

    # Hiển thị cột % Tổng cọc buổi học thử (có tô màu KPI)
    gb.configure_column(
        "% Tổng cọc buổi học thử / Tổng data đã chia trừ sai số-sai đối tượng",
        valueGetter=getter_pct_tong_coc,
        valueFormatter=pct_formatter,
        cellStyle=style_pct_tong_coc,
        width=160
    )


def configure_report2_grid_columns(gb, count_cols=None):
    """
    Cấu hình các cột cho Báo cáo 2: Nguồn, Tổng data chạy được, các cột nhập tay,
    và cột tỷ lệ.
    """
    # Cấu hình tự động xuống dòng cho header
    gb.configure_default_column(wrapHeaderText=True, autoHeaderHeight=True)

    gb.configure_column(
        "Tổng data chạy được",
        aggFunc="sum",
        valueFormatter=formatter_float_2_decimals,
        width=130
    )

    gb.configure_column(
        "Data trùng",
        aggFunc="sum",
        width=120
    )
        
    gb.configure_column(
        "Tổng data cần liên hệ",
        aggFunc="sum",
        valueFormatter=formatter_float_2_decimals,
        width=140
    )

    gb.configure_column(
        "Data vào nhóm Zalo",
        aggFunc="sum",
        valueFormatter=formatter_r2_dot_manual_value,
        width=130
    )

    gb.configure_column(
        "Data order",
        aggFunc="sum",
        valueFormatter=formatter_r2_dot_manual_value,
        width=130
    )

    gb.configure_column(
        "Data trung bình/ngày/CVHT",
        aggFunc="sum",
        valueFormatter=formatter_r2_data_average,
        width=160
    )

    gb.configure_column(
        "Tỷ lệ data thực tế/data order",
        valueGetter=getter_pct_r2_full,
        cellStyle=style_pct_r2_full,
        valueFormatter=pct_formatter,
        width=160
    )


def configure_report3_grid_columns(gb):
    """
    Cấu hình các cột cho Báo cáo 3: Ma trận Nguồn × Nhóm tuổi.
    Bao gồm 7 nhóm tuổi, cột TỔNG, và 3 nhóm gộp, tất cả đều hiển thị Số lượng (%).
    """
    # Cấu hình tự động xuống dòng cho header
    gb.configure_default_column(wrapHeaderText=True, autoHeaderHeight=True)

    from data_processing import (
        AGE_GROUPS,
        REPORT_3_SCHOOL_WORKER_COLUMN,
        REPORT_3_STUDENT_YOUNG_COLUMN,
        REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN,
    )

    for col in AGE_GROUPS:
        gb.configure_column(
            col,
            aggFunc="sum",
            cellRenderer=formatter_r3_age_group,
            width=160
        )

    gb.configure_column(
        "TỔNG",
        aggFunc="sum",
        cellRenderer=formatter_r3_tong,
        width=160,
        cellStyle={'fontWeight': 'bold'}
    )

    gb.configure_column(
        REPORT_3_STUDENT_YOUNG_COLUMN,
        aggFunc="sum",
        cellRenderer=formatter_r3_age_group,
        cellStyle=style_r3_at_least_80_green,
        width=210,
    )
    gb.configure_column(
        REPORT_3_SCHOOL_WORKER_COLUMN,
        aggFunc="sum",
        cellRenderer=formatter_r3_age_group,
        cellStyle=style_r3_at_most_20_green,
        width=210,
    )
    gb.configure_column(
        REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN,
        aggFunc="sum",
        cellRenderer=formatter_r3_age_group,
        cellStyle=style_r3_at_least_80_green,
        width=230,
    )

    # 11 cột cọc chốt ẩn nhưng có aggFunc="sum" để tính aggData trong group footer cho formatter đọc
    for col in AGE_GROUPS + ['TỔNG'] + [
        REPORT_3_STUDENT_YOUNG_COLUMN,
        REPORT_3_SCHOOL_WORKER_COLUMN,
        REPORT_3_STUDENT_YOUNG_UNFILLED_COLUMN,
    ]:
        gb.configure_column(f"{col}{COC_COL_SUFFIX}", hide=True, aggFunc="sum", width=100)


# ==========================================
# JS GETTERS & CẤU HÌNH CỘT CHO BÁO CÁO 4
# ==========================================

getter_r4_data_per_bill = JsCode("""
function(params) {
    var total = 0, bill = 0;
    if (params.node && params.node.rowPinned) {
        total = params.data ? (params.data['Tổng data'] || 0) : 0;
        bill = params.data ? (params.data['Bill cọc'] || 0) : 0;
    } else if (params.node && (params.node.group || params.node.footer)) {
        total = params.node.aggData ? (params.node.aggData['Tổng data'] || 0) : 0;
        bill = params.node.aggData ? (params.node.aggData['Bill cọc'] || 0) : 0;
    } else {
        total = params.data ? (params.data['Tổng data'] || 0) : 0;
        bill = params.data ? (params.data['Bill cọc'] || 0) : 0;
    }
    return bill > 0 ? (total / bill) : 0;
}
""")

getter_r4_bill_per_data = JsCode("""
function(params) {
    var total = 0, bill = 0;
    if (params.node && params.node.rowPinned) {
        total = params.data ? (params.data['Tổng data'] || 0) : 0;
        bill = params.data ? (params.data['Bill cọc'] || 0) : 0;
    } else if (params.node && (params.node.group || params.node.footer)) {
        total = params.node.aggData ? (params.node.aggData['Tổng data'] || 0) : 0;
        bill = params.node.aggData ? (params.node.aggData['Bill cọc'] || 0) : 0;
    } else {
        total = params.data ? (params.data['Tổng data'] || 0) : 0;
        bill = params.data ? (params.data['Bill cọc'] || 0) : 0;
    }
    return total > 0 ? (bill / total * 100) : 0;
}
""")


def configure_report4_grid_columns(gb):
    """
    Cấu hình các cột cho Báo cáo 4: Thống kê Nguồn Onl / Off / Tổng.
    Mỗi bảng có 5 cột: Nguồn, Tổng data, Bill cọc, Data/Bill, Bill/Data (%).
    """
    gb.configure_default_column(wrapHeaderText=True, autoHeaderHeight=True)
    gb.configure_column("Tổng data", aggFunc="sum", valueFormatter=formatter_float_2_decimals, width=120)
    gb.configure_column("Bill cọc", aggFunc="sum", valueFormatter=formatter_float_2_decimals, width=120)
    gb.configure_column("Data/Bill", valueGetter=getter_r4_data_per_bill, valueFormatter=formatter_float_2_decimals, width=120)
    gb.configure_column("Bill/Data (%)", valueGetter=getter_r4_bill_per_data, valueFormatter=pct_formatter, width=130)


# ==========================================
# JS GETTERS & CẤU HÌNH CỘT CHO BÁO CÁO 5 (TRUYỀN THÔNG)
# ==========================================

def make_r5_data_per_bill_getter(group_name):
    """Tạo JsCode tính Data/Bill cho một nhóm tuổi hoặc TỔNG."""
    d_col = f"{group_name}_Data"
    b_col = f"{group_name}_Bill cọc"
    return JsCode(f"""
function(params) {{
    var total = 0, bill = 0;
    if (params.node && params.node.rowPinned) {{
        total = params.data ? (params.data['{d_col}'] || 0) : 0;
        bill = params.data ? (params.data['{b_col}'] || 0) : 0;
    }} else if (params.node && (params.node.group || params.node.footer)) {{
        total = params.node.aggData ? (params.node.aggData['{d_col}'] || 0) : 0;
        bill = params.node.aggData ? (params.node.aggData['{b_col}'] || 0) : 0;
    }} else {{
        total = params.data ? (params.data['{d_col}'] || 0) : 0;
        bill = params.data ? (params.data['{b_col}'] || 0) : 0;
    }}
    return bill > 0 ? (total / bill) : 0;
}}
""")


def make_r5_bill_per_data_getter(group_name):
    """Tạo JsCode tính Bill/Data (%) cho một nhóm tuổi hoặc TỔNG."""
    d_col = f"{group_name}_Data"
    b_col = f"{group_name}_Bill cọc"
    return JsCode(f"""
function(params) {{
    var total = 0, bill = 0;
    if (params.node && params.node.rowPinned) {{
        total = params.data ? (params.data['{d_col}'] || 0) : 0;
        bill = params.data ? (params.data['{b_col}'] || 0) : 0;
    }} else if (params.node && (params.node.group || params.node.footer)) {{
        total = params.node.aggData ? (params.node.aggData['{d_col}'] || 0) : 0;
        bill = params.node.aggData ? (params.node.aggData['{b_col}'] || 0) : 0;
    }} else {{
        total = params.data ? (params.data['{d_col}'] || 0) : 0;
        bill = params.data ? (params.data['{b_col}'] || 0) : 0;
    }}
    return total > 0 ? (bill / total * 100) : 0;
}}
""")


def _get_r5_js_getters():
    from data_processing import AGE_GROUPS
    all_groups = AGE_GROUPS + ['TỔNG']
    d_getters = {g: make_r5_data_per_bill_getter(g) for g in all_groups}
    b_getters = {g: make_r5_bill_per_data_getter(g) for g in all_groups}
    return d_getters, b_getters


_R5_DATA_GETTERS, _R5_BILL_GETTERS = None, None


def configure_report5_grid_columns(gb):
    """
    Cấu hình các cột cho Báo cáo 5: Nguồn Onl/Off × Nhóm tuổi (Truyền Thông).
    Gồm 2 cột cố định bên trái (Thời gian xuất data, Nguồn) và 8 nhóm cột (7 nhóm tuổi + 1 TỔNG),
    mỗi nhóm chứa 4 cột con: Data, Bill cọc, Data/Bill, Bill/Data (%).
    """
    global _R5_DATA_GETTERS, _R5_BILL_GETTERS
    from data_processing import AGE_GROUPS

    if _R5_DATA_GETTERS is None or _R5_BILL_GETTERS is None:
        _R5_DATA_GETTERS, _R5_BILL_GETTERS = _get_r5_js_getters()

    gb.configure_default_column(wrapHeaderText=True, autoHeaderHeight=True)

    col_defs = {
        'Thời gian xuất data': {
            'headerName': 'Thời gian xuất data',
            'field': 'Thời gian xuất data',
            'width': 140,
            'pinned': 'left',
        },
        'Nguồn': {
            'headerName': 'Nguồn',
            'field': 'Nguồn',
            'width': 200,
            'pinned': 'left',
        },
    }

    for group in AGE_GROUPS + ['TỔNG']:
        is_tong = (group == 'TỔNG')
        cell_style = {'fontWeight': 'bold'} if is_tong else None

        def _make_child(name, field, width, **kwargs):
            c = {'headerName': name, 'field': field, 'width': width, **kwargs}
            if cell_style:
                c['cellStyle'] = cell_style
            return c

        children = [
            _make_child('Data', f"{group}_Data", 95, aggFunc='sum', valueFormatter=formatter_float_2_decimals),
            _make_child('Bill cọc', f"{group}_Bill cọc", 95, aggFunc='sum', valueFormatter=formatter_float_2_decimals),
            _make_child('Data/Bill', f"{group}_Data/Bill", 95, valueGetter=_R5_DATA_GETTERS[group], valueFormatter=formatter_float_2_decimals),
            _make_child('Bill/Data (%)', f"{group}_Bill/Data (%)", 110, valueGetter=_R5_BILL_GETTERS[group], valueFormatter=pct_formatter),
        ]

        col_defs[group] = {
            'headerName': group,
            'children': children,
        }

    gb._GridOptionsBuilder__grid_options['columnDefs'] = col_defs


def update_manual_inputs_in_state(grid_response, state_key, keys, editable_cols=None):
    """
    Đồng bộ dữ liệu nhập tay từ phản hồi AgGrid vào session state.
    editable_cols: danh sách cột nhập tay cần sync (mặc định: Cọc Khác, Tổng Cọc Học Thử).
    """
    if editable_cols is None:
        editable_cols = ['Cọc Khác', 'Tổng Cọc Học Thử']

    if grid_response is not None and 'data' in grid_response:
        updated_df = pd.DataFrame(grid_response['data'])
        if not updated_df.empty:
            present_cols = [c for c in editable_cols if c in updated_df.columns]
            if present_cols:
                updated_clean = updated_df.dropna(subset=keys)
                updated_clean = updated_clean.groupby(keys, as_index=False)[present_cols].first()

                df_state = st.session_state[state_key]
                orig_cols = list(df_state.columns)

                df_state_idx = df_state.set_index(keys)
                updated_idx = updated_clean.set_index(keys)

                df_state_idx.update(updated_idx[present_cols])

                df_updated = df_state_idx.reset_index()
                st.session_state[state_key] = df_updated[orig_cols]
