-- ==========================================
-- SUPABASE SCHEMA — Tạo các table cho ứng dụng Báo cáo CVHT
-- Chạy SQL này trên Supabase Dashboard > SQL Editor
-- ==========================================

-- Table lưu raw records từ API
CREATE TABLE IF NOT EXISTS raw_records (
    id BIGSERIAL PRIMARY KEY,
    fetch_id UUID DEFAULT gen_random_uuid(),
    record_data JSONB NOT NULL,
    account_id INTEGER,
    account_code TEXT,
    created_at_api BIGINT,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    filters_used JSONB
);

-- Table lưu lịch sử báo cáo đã tính toán
CREATE TABLE IF NOT EXISTS report_history (
    id BIGSERIAL PRIMARY KEY,
    report_type TEXT NOT NULL,
    report_data JSONB NOT NULL,
    filters_used JSONB,
    row_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index cho query nhanh
CREATE INDEX IF NOT EXISTS idx_raw_records_fetch_id ON raw_records(fetch_id);
CREATE INDEX IF NOT EXISTS idx_raw_records_fetched_at ON raw_records(fetched_at);
CREATE INDEX IF NOT EXISTS idx_report_history_type ON report_history(report_type);
CREATE INDEX IF NOT EXISTS idx_report_history_created ON report_history(created_at DESC);
