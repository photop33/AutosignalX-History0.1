import pandas as pd
import streamlit as st
import os
import subprocess
import codecs

from datetime import datetime, time
# נתיב config
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.py"))
PYTHON_PATH = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
VOLATILE_FILE = os.path.join("logs", "volatile_symbols.txt")

# -- טען ערכים נוכחיים --
config_vars = {}
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    exec(f.read(), config_vars)

st.title("🔍 מערכת סריקה")
st.header("⚙️ הגדרות סריקה")



# --- SCAN_FROM ו-SCAN_TO באותה שורה עם תאריך ושעה ---
col1, col2 = st.columns(2)

with col1:
    scan_from_date = st.date_input("SCAN_FROM - תאריך", value=pd.to_datetime(config_vars.get("SCAN_FROM", datetime.now())))
    scan_from_time = st.time_input("שעה התחלה", value=(pd.to_datetime(config_vars.get("SCAN_FROM", datetime.now())).time() if config_vars.get("SCAN_FROM") else time(0, 0)))

with col2:
    scan_to_date = st.date_input("SCAN_TO - תאריך", value=pd.to_datetime(config_vars.get("SCAN_TO", datetime.now())))
    scan_to_time = st.time_input("שעה סיום", value=(pd.to_datetime(config_vars.get("SCAN_TO", datetime.now())).time() if config_vars.get("SCAN_TO") else time(23, 59)))

SCAN_FROM = f"{scan_from_date} {scan_from_time.strftime('%H:%M')}"
SCAN_TO = f"{scan_to_date} {scan_to_time.strftime('%H:%M')}"

# --- INTERVAL selectbox ---
interval_options = ["1m", "5m", "15m", "30m", "1h", "4h", "8h", "12h", "1d", "1w", "1y"]
col_interval, col_symbol = st.columns([1, 2])  # אפשר לשחק עם היחס


with col_symbol:
    symbol_scan_str = st.text_input(
        "symbol_scan (סימבול/ים, פסיק=הפרדה, ריק=הכל)",
        value=",".join(config_vars.get("symbol_scan", []))
    )
    symbol_scan = [s.strip() for s in symbol_scan_str.split(",") if s.strip()]



with col_interval:
    INTERVAL = st.selectbox("INTERVAL", interval_options,
                            index=interval_options.index(config_vars.get("INTERVAL", "1h")) if config_vars.get(
                                "INTERVAL", "1h") in interval_options else 4)

# --- שאר השדות באותה שורה ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    VOLATILITY_THRESHOLD = st.number_input("Volatility % - שינוי תנועה  (0 = כבוי)", value=config_vars.get("VOLATILITY_THRESHOLD") or 0.0, step=0.01)

with col2:
    PCT_CHANGE_THRESHOLD = st.number_input("Change Day - שינוי יומי  (0 = כבוי)", value=config_vars.get("PCT_CHANGE_THRESHOLD") or 0.0, step=0.01)

with col3:
    MIN_VOLUME = st.number_input("MIN_VOLUME \n", value=config_vars.get("MIN_VOLUME") or 0)

with col4:
    FILTER_MODE = st.selectbox("FILTER_MODE \n ", ["AND", "OR"], index=0 if config_vars.get("FILTER_MODE") == "AND" else 1)

if st.button("💾 שמור הגדרות סריקה"):
    # קריאת כל הקונפיג, עדכון רק שדות נבחרים, שמירה חזרה (לא מוחקים שדות קיימים אחרים)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_code = f.read()
    local_vars = {}
    exec(config_code, local_vars)
    # עדכון שדות
    local_vars["SCAN_FROM"] = SCAN_FROM
    local_vars["SCAN_TO"] = SCAN_TO
    local_vars["INTERVAL"] = INTERVAL
    local_vars["symbol_scan"] = symbol_scan
    local_vars["VOLATILITY_THRESHOLD"] = VOLATILITY_THRESHOLD
    local_vars["PCT_CHANGE_THRESHOLD"] = PCT_CHANGE_THRESHOLD
    local_vars["MIN_VOLUME"] = MIN_VOLUME
    local_vars["FILTER_MODE"] = FILTER_MODE


    def format_val(val):
        if isinstance(val, str):
            return f'"{val}"'
        elif isinstance(val, list):
            return "[" + ", ".join(f'"{v}"' for v in val) + "]"
        return str(val)


    config_txt = ""
    for k, v in local_vars.items():
        if k.startswith("__"): continue
        config_txt += f"{k} = {format_val(v)}\n"

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(config_txt)

    st.success("ההגדרות נשמרו!")

st.divider()  # מפריד יפה בין אזור הגדרות לאזור ריצה

# ---- חלק תחתון: כפתור סריקה ----
st.header("🚀 הרצת סריקה בפועל")
st.code(f"🔧 Python Executable: {PYTHON_PATH}")

if st.button("🚀 הרץ סריקה (scan.py)"):
    with st.spinner("מריץ סריקה..."):
        result = subprocess.run([PYTHON_PATH, "scan.py"], capture_output=True, text=True)
        st.subheader("📄 פלט ההרצה:")
        try:
            decoded_out = result.stdout.encode().decode('unicode_escape')
            st.code(decoded_out)
        except Exception:
            st.code(result.stdout)

        if os.path.exists(VOLATILE_FILE):
            st.subheader("🪙 מטבעות תנודתיים שנמצאו:")
            with open(VOLATILE_FILE, "r", encoding="utf-8") as f:
                symbols = f.read().splitlines()
                st.write(symbols)
        else:
            st.warning("⚠️ לא נמצא קובץ volatile_symbols.txt")
