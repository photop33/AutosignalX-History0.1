import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="📈 תוצאות TP/SL", layout="wide")
st.title("📈 תוצאות - פענוח סיגנלים TP & SL")

CSV_PATH = os.path.join("strategy_signals_results_with_tp_sl.csv")

# כפתור רענון שמפעיל טעינה מחדש של הקובץ
refresh = st.button("🔁 רענן טבלה")

# טען את הקובץ אם קיים
if not os.path.exists(CSV_PATH):
    st.error("❌ הקובץ לא נמצא.")
    st.stop()

try:
    if refresh or True:  # תמיד טוען מחדש, אבל הכפתור מאפשר "שליטה"
        df = pd.read_csv(CSV_PATH)
        st.success(f"✅ נטענו {len(df)} שורות.")
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"שגיאה בטעינה: {e}")
