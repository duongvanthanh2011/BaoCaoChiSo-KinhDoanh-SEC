"""
manual_input_state.py — Quản lý trạng thái phiên, bản nháp (draft) và baseline
Đảm bảo bản nháp không bị xóa khi đợt hoặc nguồn bị ẩn bởi bộ lọc Streamlit.
"""

import streamlit as st
from manual_input_schema import validate_metric_value

SESSION_KEY_MANUAL_STATE = "manual_state"


def ensure_manual_state_container():
    """Khởi tạo container quản lý trạng thái nhập tay trong session_state."""
    if SESSION_KEY_MANUAL_STATE not in st.session_state:
        st.session_state[SESSION_KEY_MANUAL_STATE] = {}


def get_session_entry(report_code: str, trial_session: str) -> dict:
    """Lấy bản ghi trạng thái của một (report_code, trial_session). Khởi tạo nếu chưa có."""
    ensure_manual_state_container()
    key = (str(report_code), str(trial_session))
    if key not in st.session_state[SESSION_KEY_MANUAL_STATE]:
        st.session_state[SESSION_KEY_MANUAL_STATE][key] = {
            "load_status": "unloaded",  # unloaded | loaded | error
            "version_no": 0,
            "baseline": {},
            "draft": {},
            "error_msg": None,
        }
    return st.session_state[SESSION_KEY_MANUAL_STATE][key]


def set_loaded_baseline(report_code: str, trial_session: str, version_no: int, baseline_snapshot: dict, *, discard_edits=False):
    """
    Cập nhật baseline sau khi tải thành công từ Supabase.
    Nếu người dùng đã sửa bản nháp trong phiên trước khi tải, giữ lại các ô đã sửa.
    """
    entry = get_session_entry(report_code, trial_session)
    cleaned_snapshot = validate_metric_value(baseline_snapshot)
    
    old_baseline = entry.get("baseline", {})
    current_draft = entry.get("draft", {})

    # Xác định các key người dùng đã chủ động chỉnh sửa trong phiên (draft != old_baseline)
    user_edited_keys = {
        k for k, v in current_draft.items()
        if v != old_baseline.get(k, 0)
    }

    entry["load_status"] = "loaded"
    entry["version_no"] = int(version_no) if version_no else 0
    entry["baseline"] = dict(cleaned_snapshot)
    entry["error_msg"] = None

    # Bản nháp mới: bắt đầu từ baseline, nhưng giữ lại các ô user đã sửa trong phiên
    new_draft = dict(cleaned_snapshot)
    if not discard_edits:
        for k in user_edited_keys:
            new_draft[k] = current_draft[k]
    entry["draft"] = new_draft


def mark_load_error(report_code: str, trial_session: str, error_msg: str):
    """Đánh dấu tải thất bại, lưu thông báo lỗi và giữ nguyên bản nháp hiện tại."""
    entry = get_session_entry(report_code, trial_session)
    entry["load_status"] = "error"
    entry["error_msg"] = str(error_msg)


def on_widget_change(report_code: str, trial_session: str, input_code: str, widget_key: str):
    """
    Callback khi giá trị trên ô widget Streamlit thay đổi.
    Chỉ cập nhật vào bản nháp (draft) trong phiên, KHÔNG gọi database.
    """
    if widget_key in st.session_state:
        val = st.session_state[widget_key]
        try:
            val_int = max(0, int(val))
        except (ValueError, TypeError):
            val_int = 0
        entry = get_session_entry(report_code, trial_session)
        entry["draft"][input_code] = val_int


def get_draft_value(report_code: str, trial_session: str, input_code: str, default: int = 0) -> int:
    """Lấy giá trị hiện tại từ bản nháp."""
    entry = get_session_entry(report_code, trial_session)
    return entry["draft"].get(input_code, default)


def set_draft_value(report_code: str, trial_session: str, input_code: str, value: int):
    """Ghi trực tiếp giá trị vào bản nháp."""
    try:
        val_int = max(0, int(value))
    except (ValueError, TypeError):
        val_int = 0
    entry = get_session_entry(report_code, trial_session)
    entry["draft"][input_code] = val_int


def get_changed_values(report_code: str, trial_session: str, displayed_input_codes: list[str]) -> dict:
    """
    So sánh bản nháp (draft) với baseline theo các mã input đang hiển thị.
    Chỉ trả về các key có giá trị thay đổi (bao gồm cả trường hợp sửa về 0).
    """
    entry = get_session_entry(report_code, trial_session)
    draft = entry.get("draft", {})
    baseline = entry.get("baseline", {})

    changes = {}
    for code in displayed_input_codes:
        draft_val = draft.get(code, 0)
        base_val = baseline.get(code, 0)
        if draft_val != base_val:
            changes[code] = draft_val

    return changes


def has_unsaved_changes(
    report_code: str, trial_sessions: list[str], displayed_codes_by_dot: dict[str, list[str]]
) -> bool:
    """Kiểm tra xem có bất kỳ thay đổi nào chưa lưu đối với các đợt đang hiển thị hay không."""
    for dot in trial_sessions:
        codes = displayed_codes_by_dot.get(str(dot), [])
        if get_changed_values(report_code, str(dot), codes):
            return True
    return False


def apply_saved_snapshot(report_code: str, trial_session: str, new_version_no: int, server_snapshot: dict, submitted_values=None):
    """
    Cập nhật baseline và draft sau khi lưu thành công lên Supabase.
    Ghép server_snapshot vào baseline và draft để nhận các cập nhật mới từ server.
    """
    entry = get_session_entry(report_code, trial_session)
    submitted_values = submitted_values or {}
    pending = {
        k: v for k, v in entry["draft"].items()
        if v != entry["baseline"].get(k, 0)
        and (k not in submitted_values or submitted_values[k] != v)
    }
    set_loaded_baseline(report_code, trial_session, new_version_no, server_snapshot, discard_edits=True)
    entry["draft"].update(pending)


def has_any_draft_changes(report_code, trial_sessions):
    """Bao gồm nguồn đang ẩn trong các đợt sắp tải lại."""
    return any(
        any(v != entry["baseline"].get(k, 0) for k, v in entry["draft"].items())
        for entry in (get_session_entry(report_code, d) for d in trial_sessions)
    )


def sync_manual_widgets(report_code, trial_session, displayed_codes):
    """Chỉ gọi trước khi render widget; reset key thiếu trong snapshot về 0."""
    from manual_input_schema import get_widget_key
    entry = get_session_entry(report_code, trial_session)
    codes = set(displayed_codes) | set(entry["baseline"]) | set(entry["draft"])
    for code in codes:
        st.session_state[get_widget_key(report_code, code, trial_session)] = entry["draft"].get(code, 0)




def get_all_drafts_for_report(report_code: str, trial_sessions: list[str]) -> dict[str, dict]:
    """Trả về dictionary các bản nháp theo đợt {dot_name: draft_dict}."""
    res = {}
    for dot in trial_sessions:
        entry = get_session_entry(report_code, str(dot))
        res[str(dot)] = entry.get("draft", {})
    return res
