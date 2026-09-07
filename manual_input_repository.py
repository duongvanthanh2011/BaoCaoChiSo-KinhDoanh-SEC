"""Đọc bản mới nhất và lưu phiên bản bằng các RPC có transaction."""

from typing import Optional
from supabase import create_client, Client
from config import get_supabase_url, get_supabase_key, get_supabase_table_name
from manual_input_schema import validate_metric_value


class ManualInputRepository:
    def __init__(self, url=None, key=None, table_name=None):
        self.url = get_supabase_url() if url is None else url
        self.key = get_supabase_key() if key is None else key
        self.table_name = get_supabase_table_name() if table_name is None else table_name
        if self.table_name not in ("NhapLieuGiaTriDauVao", "report_manual_inputs"):
            raise ValueError("Tên bảng nhập liệu không được hỗ trợ.")
        self._client: Optional[Client] = None

    def is_configured(self):
        return bool(self.url and self.key and self.url.startswith("http"))

    def get_client(self):
        if not self.is_configured():
            raise RuntimeError("Chưa cấu hình kết nối Supabase.")
        if self._client is None:
            self._client = create_client(self.url, self.key)
        return self._client

    def load_latest_batch(self, report_code, trial_sessions):
        if not trial_sessions:
            return {}
        client = self.get_client()
        sessions = list(dict.fromkeys(str(s) for s in trial_sessions))
        latest = {}
        # JSON object không chịu giới hạn số dòng SELECT của PostgREST.
        for start in range(0, len(sessions), 200):
            batch = sessions[start:start + 200]
            try:
                data = client.rpc("load_latest_manual_inputs", {
                    "p_table_name": self.table_name,
                    "p_report_code": str(report_code),
                    "p_trial_sessions": batch,
                }).execute().data
                if not isinstance(data, dict) or set(data) != set(batch):
                    raise ValueError("Incomplete latest response")
                for dot, row in data.items():
                    if row is None:  # Database xác nhận chưa có bản ghi.
                        continue
                    latest[dot] = {
                        "id": row["id"],
                        "version_no": int(row["version_no"]),
                        "created_at": row["created_at"],
                        "metric_value": validate_metric_value(row["metric_value"]),
                    }
            except Exception as exc:
                raise RuntimeError(
                    "Không tải được đầy đủ dữ liệu. Kiểm tra kết nối và migration Supabase."
                ) from exc
        return latest

    def save_changes(self, report_code, trial_session, changed_values):
        changes = validate_metric_value(changed_values, strict=True)
        try:
            data = self.get_client().rpc("save_manual_input_changes", {
                "p_table_name": self.table_name,
                "p_report_code": str(report_code),
                "p_trial_session": str(trial_session),
                "p_changes": changes,
            }).execute().data
            if not isinstance(data, dict) or not isinstance(data.get("saved"), bool):
                raise ValueError("Invalid save response")
            return {
                "saved": data["saved"],
                "version_no": int(data["version_no"]),
                "metric_value": validate_metric_value(data["metric_value"]),
            }
        except Exception as exc:
            # Không tự retry/INSERT: RPC có thể đã commit trước timeout.
            raise RuntimeError(
                "Chưa xác nhận được kết quả lưu. Giữ nguyên bản nháp; kiểm tra kết nối "
                "và migration, tải lại để đối chiếu trước khi lưu lại."
            ) from exc


_repository_instance = None


def get_repository():
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = ManualInputRepository()
    return _repository_instance
