"""Cấu hình từ biến môi trường hoặc Streamlit Secrets."""
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_setting(name, default=""):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except FileNotFoundError:
        return default


def get_api_key():
    return get_setting("GETFLY_API_KEY")


def get_url_base():
    return get_setting("GETFLY_URL_BASE", "https://sec.getflycrm.com")


def get_headers(api_key):
    return {"X-API-KEY": api_key, "Content-Type": "application/json"}


def get_supabase_url():
    return get_setting("SUPABASE_URL")


def get_supabase_key():
    return get_setting("SUPABASE_SECRET_KEY") or get_setting("SUPABASE_KEY")


def get_supabase_table_name():
    return get_setting("SUPABASE_TABLE_NAME", "NhapLieuGiaTriDauVao")
