import streamlit as st
import subprocess
import os
import pandas as pd
from datetime import datetime, time

PYTHON_PATH = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
LOG_PATH = os.path.join("logs", "monitor_output.txt")
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.py"))

# טען קונפיג נוכחי
config_vars = {}
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    exec(f.read(), config_vars)

st.title("🧠 מערכת ניטור סיגנלים + בדיקת TP/SL")
st.code(f"🔧 Python Executable: {PYTHON_PATH}")

# ---- כפתור להעתקת הגדרות מסריקה (SCAN) ----
if st.button("📋 העתק הגדרות מסריקה (SCAN)"):
    scan_from = config_vars.get("SCAN_FROM", "")
    scan_to = config_vars.get("SCAN_TO", "")
    interval_val = config_vars.get("INTERVAL", "1d")
    symbols = config_vars.get("symbol_scan", [])

    # פיצול תאריך+שעה
    if scan_from:
        try:
            scan_from_date, scan_from_time = scan_from.split()
            scan_from_date = pd.to_datetime(scan_from_date)
            scan_from_time = datetime.strptime(scan_from_time, "%H:%M").time()
        except Exception:
            scan_from_date = datetime.now().date()
            scan_from_time = time(0, 0)
    else:
        scan_from_date = datetime.now().date()
        scan_from_time = time(0, 0)

    if scan_to:
        try:
            scan_to_date, scan_to_time = scan_to.split()
            scan_to_date = pd.to_datetime(scan_to_date)
            scan_to_time = datetime.strptime(scan_to_time, "%H:%M").time()
        except Exception:
            scan_to_date = datetime.now().date()
            scan_to_time = time(23, 59)
    else:
        scan_to_date = datetime.now().date()
        scan_to_time = time(23, 59)

    st.session_state["start_date"] = scan_from_date
    st.session_state["start_time"] = scan_from_time
    st.session_state["end_date"] = scan_to_date
    st.session_state["end_time"] = scan_to_time
    st.session_state["interval"] = interval_val
    st.session_state["symbol"] = ",".join(symbols) if symbols else ""
    st.rerun()

# --- הגדרות טווח ניתוח ואינטרוול בלבד ---
st.header("🛠️ הגדרות טווח ניתוח ואינטרוול")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "תאריך התחלה",
        value=st.session_state.get("start_date", pd.to_datetime(config_vars.get("start_time_str", datetime.now())))
    )
    start_time = st.time_input(
        "שעת התחלה",
        value=st.session_state.get("start_time", pd.to_datetime(config_vars.get("start_time_str", datetime.now())).time())
    )
with col2:
    end_date = st.date_input(
        "תאריך סיום",
        value=st.session_state.get("end_date", pd.to_datetime(config_vars.get("end_time_str", datetime.now())))
    )
    end_time = st.time_input(
        "שעה סיום",
        value=st.session_state.get("end_time", pd.to_datetime(config_vars.get("end_time_str", datetime.now())).time())
    )

start_time_str = f"{start_date} {start_time.strftime('%H:%M')}"
end_time_str = f"{end_date} {end_time.strftime('%H:%M')}"

interval_options = ["1m", "5m", "15m", "30m", "1h", "4h", "8h", "12h", "1d", "1w", "1y"]
interval = st.selectbox(
    "interval",
    interval_options,
    index=interval_options.index(
        st.session_state.get("interval", config_vars.get("interval", "1d"))
    ) if st.session_state.get("interval", config_vars.get("interval", "1d")) in interval_options else 8
)

symbol = st.text_input(
    "symbol (השאר ריק לריצה על כל הסימבולים)",
    st.session_state.get("symbol", config_vars.get("symbol", ""))
)

# --- הגדרות אסטרטגיות ---
st.header("🎯 סינון אסטרטגיות פעיל (STRATEGY_THRESHOLDS)")

strategy_thresholds = config_vars.get("STRATEGY_THRESHOLDS", {})
new_thresholds = {}

strategy_max_values = {
    "strategy_rsi_macd": 2,
    "strategy_bollinger_macd": 2,
    "strategy_breakout_volume": 3,
    "strategy_breakout": 2,
    "strategy_candlestick": 1,
    "strategy_supertrend_macd": 2,
    "strategy_vwap_bounce": 2,
}

cols_per_row = 3
strategy_items = list(strategy_thresholds.items())

for i in range(0, len(strategy_items), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, (strat, val) in enumerate(strategy_items[i:i+cols_per_row]):
        with cols[j]:
            max_val = strategy_max_values.get(strat, 1)
            new_val = st.number_input(
                label=strat,
                value=int(val),
                min_value=0,
                max_value=max_val,
                step=1,
                label_visibility="visible"
            )
            new_thresholds[strat] = new_val

# --- כפתור שמירה ---
if st.button("💾 שמור הגדרות ניטור"):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_code = f.read()
    local_vars = {}
    exec(config_code, local_vars)

    local_vars["symbol"] = symbol if symbol.strip() else None
    local_vars["interval"] = interval
    local_vars["start_time_str"] = start_time_str
    local_vars["end_time_str"] = end_time_str
    local_vars["STRATEGY_THRESHOLDS"] = new_thresholds

    def format_val(val):
        if val is None:
            return "None"
        if isinstance(val, str):
            return f'"{val}"'
        if isinstance(val, dict):
            inner = ", ".join([f'"{k}": {v}' for k, v in val.items()])
            return f"{{{inner}}}"
        return str(val)

    config_txt = ""
    for k, v in local_vars.items():
        if k.startswith("__"):
            continue
        config_txt += f"{k} = {format_val(v)}\n"

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(config_txt)

    st.success("ההגדרות נשמרו!")

st.divider()

# --- הרצת הסקריפטים ---
if st.button("🚀 הרץ ניטור וסגירת סיגנלים"):
    with st.spinner("🧠 מריץ startagy_program.py..."):
        os.makedirs("logs", exist_ok=True)
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            subprocess.run([PYTHON_PATH, "startagy_program.py"], stdout=f, stderr=subprocess.STDOUT, text=True)

    with st.spinner("📈 מריץ st_or_tp.py..."):
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            subprocess.run([PYTHON_PATH, "st_or_tp.py"], stdout=f, stderr=subprocess.STDOUT, text=True)

    st.subheader("📄 פלט הרצה:")
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        st.code(f.read())
