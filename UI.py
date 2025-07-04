import streamlit as st
import re
import sys
import subprocess
from datetime import datetime

CONFIG_PATH = "config.py"
MAIN_PATH = "main.py"

def get_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    return text

def get_param(text, key, as_type=str):
    m = re.search(rf'^{key}\s*=\s*(.*)', text, flags=re.MULTILINE)
    if not m:
        return ""
    val = m.group(1).split("#")[0].strip()
    if val == "None":
        return ""
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    if as_type == float:
        try: return float(val)
        except: return ""
    if as_type == int:
        try: return int(val)
        except: return ""
    return val

def set_param(text, key, value, as_type=str, comment=""):
    text = re.sub(rf'^{key}\s*=.*$', '', text, flags=re.MULTILINE)
    value = str(value).replace('"', '').strip()
    if value == "" or value.lower() == "none":
        new_line = f'{key} = None'
    elif as_type == float:
        try: new_line = f'{key} = {float(value)}'
        except: new_line = f'{key} = "{value}"'
    elif as_type == int:
        try: new_line = f'{key} = {int(value)}'
        except: new_line = f'{key} = "{value}"'
    else:
        new_line = f'{key} = "{value}"'
    if comment:
        new_line += f"  # {comment}"
    return text.strip() + f'\n{new_line}\n'

config_txt = get_config()

st.title("⚙️ עריכת config.py + הרצת main.py")

with st.form("edit_config"):
    scan_from = st.text_input("SCAN_FROM (מתאריך):", get_param(config_txt, "SCAN_FROM"))
    scan_to = st.text_input("SCAN_TO (עד תאריך):", get_param(config_txt, "SCAN_TO"))
    interval = st.text_input("INTERVAL (אינטרוול):", get_param(config_txt, "INTERVAL"))
    vol_thresh = st.text_input("VOLATILITY_THRESHOLD:", get_param(config_txt, "VOLATILITY_THRESHOLD"))
    pct_change = st.text_input("PCT_CHANGE_THRESHOLD:", get_param(config_txt, "PCT_CHANGE_THRESHOLD"))
    min_volume = st.text_input("MIN_VOLUME:", get_param(config_txt, "MIN_VOLUME"))
    filter_mode = st.selectbox("FILTER_MODE:", ["AND", "OR"], index=0 if get_param(config_txt, "FILTER_MODE")=="AND" else 1)
    symbol = st.text_input("symbol:", get_param(config_txt, "symbol"))
    interval2 = st.text_input("interval (לאינדיקטור):", get_param(config_txt, "interval"))
    # start_time_str ו־end_time_str נוצרים אוטומטית לפי SCAN_FROM/SCAN_TO

    submitted = st.form_submit_button("💾 שמור הגדרות והרץ main.py")

if submitted:
    new_config = config_txt
    new_config = set_param(new_config, "SCAN_FROM", scan_from)
    new_config = set_param(new_config, "SCAN_TO", scan_to)
    new_config = set_param(new_config, "INTERVAL", interval, as_type=str, comment="אם רוצים להגביל את האינטרוול")
    new_config = set_param(new_config, "VOLATILITY_THRESHOLD", vol_thresh, as_type=float)
    new_config = set_param(new_config, "PCT_CHANGE_THRESHOLD", pct_change, as_type=float)
    new_config = set_param(new_config, "MIN_VOLUME", min_volume, as_type=int)
    new_config = set_param(new_config, "FILTER_MODE", filter_mode, as_type=str)
    new_config = set_param(new_config, "symbol", symbol, as_type=str)
    new_config = set_param(new_config, "interval", interval2, as_type=str)

    # יצירת start_time_str ו-end_time_str אוטומטית בפורמט המתאים
    try:
        dt_start = datetime.strptime(scan_from, "%Y-%m-%d %H:%M")
        start_time_str_for_func = dt_start.strftime("%d/%m/%Y %H:%M")
    except Exception:
        start_time_str_for_func = scan_from  # fallback אם נכשל
    try:
        dt_end = datetime.strptime(scan_to, "%Y-%m-%d %H:%M")
        end_time_str_for_func = dt_end.strftime("%d/%m/%Y %H:%M")
    except Exception:
        end_time_str_for_func = scan_to

    new_config = set_param(new_config, "start_time_str", start_time_str_for_func, as_type=str)
    new_config = set_param(new_config, "end_time_str", end_time_str_for_func, as_type=str)

    # ניקוי רווחים ושורות ריקות
    new_config = "\n".join([l for l in new_config.splitlines() if l.strip() != ""])

    st.code(new_config, language="python")
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(new_config)
    st.success("כל ההגדרות נשמרו בהצלחה!")

    # הרצת main.py
    with st.spinner("מריץ main.py ..."):
        result = subprocess.run([sys.executable, MAIN_PATH], capture_output=True, text=True)
        st.text_area("פלט ההרצה:", f"{result.stdout or ''}\n{result.stderr or ''}", height=300)
        if result.returncode == 0:
            st.success("main.py רץ בהצלחה!")
        else:
            st.error(f"שגיאה בהרצת main.py (קוד {result.returncode})")
