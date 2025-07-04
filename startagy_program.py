import pandas as pd
import os
from datetime import datetime, timedelta
import importlib
import ta
import sys
import io
from config import ACTIVE_STRATEGIES, STRATEGY_THRESHOLDS, symbol as config_symbol, interval, start_time_str, end_time_str

print("Start Startagy")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# === הגדרות קבועות לחישוב SL/TP ===
SL_MULTIPLIER = 1.5
RR_RATIO = 2.0
base_dir = "data/historical_kline"

# 📥 טען את רשימת הסימבולים מקובץ volatile_symbols.txt
def load_volatile_symbols(path="logs/volatile_symbols.txt"):
    if not os.path.exists(path):
        print(f"⚠️ קובץ לא נמצא: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("🗓️") and not line.startswith("📊")
        ]


# 📥 טען נתונים לפי טווח תאריכים
def load_data_from_time_range(symbol, interval, start_time_str, end_time_str):
    def parse_time(t):
        return datetime.strptime(t, "%Y-%m-%d %H:%M")
    start_time = parse_time(start_time_str)
    end_time   = parse_time(end_time_str)
    current_date = start_time.date()
    end_date = end_time.date()
    all_dfs = []

    while current_date <= end_date:
        curr_name = f"{symbol}_{current_date.strftime('%Y-%m-%d')}_{interval}.csv"
        curr_path = os.path.normpath(os.path.join(
            base_dir, symbol,
            current_date.strftime("%Y"),
            current_date.strftime("%m"),
            current_date.strftime("%d"),
            interval, curr_name
        ))
        print(f"מחפש קובץ: {curr_path}")
        if os.path.exists(curr_path):
            df = pd.read_csv(curr_path)
            df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%d %H:%M:%S")
            df = df[(df["time"] >= start_time) & (df["time"] <= end_time)]
            if not df.empty:
                all_dfs.append(df)
                print(f"✅ נטענו {len(df)} שורות מקובץ: {curr_path}")
        else:
            print(f"❌ לא נמצא קובץ: {curr_path}")
        current_date += timedelta(days=1)

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        print(f"📊 סה\"כ נרות שנטענו: {len(final_df)}")
        return final_df
    else:
        print("⚠️ לא נמצאו נתונים כלל.")
        return pd.DataFrame()

# 🧠 אסטרטגיות
strategies = {}
for strat_name in ACTIVE_STRATEGIES:
    module = importlib.import_module(f"strategies.{strat_name}")
    func = getattr(module, strat_name)
    strategies[strat_name] = func

# 🎯 החלט על רשימת הסימבולים
if config_symbol is None or str(config_symbol).lower() == "none" or str(config_symbol).strip() == "":
    symbols = load_volatile_symbols()
    symbols = [s for s in symbols if not s.startswith("🗓️") and not s.startswith("📊")]  # סינון שורות טקסט
    if not symbols:
        print("❌ לא נמצאו סימבולים בקובץ volatile_symbols.txt")
        exit()
    print(f"🔄 מריץ אסטרטגיות על {len(symbols)} סימבולים מקובץ volatile_symbols.txt")
else:
    symbols = [config_symbol]
    print(f"🔄 מריץ אסטרטגיה על סימבול בודד מתוך config.py: {config_symbol}")

# 🚀 הרצת אסטרטגיות על כל סימבול
all_results = []
for symbol in symbols:
    print(f"\n🚀 מריץ אסטרטגיה על {symbol}")
    df_result = load_data_from_time_range(symbol, interval, start_time_str, end_time_str)

    if df_result.empty:
        print(f"❌ אין נתונים עבור {symbol} — מדלג.")
        continue

    for name, func in strategies.items():
        try:
            threshold = STRATEGY_THRESHOLDS.get(name, 1)
            for i, row in df_result.iterrows():
                score, reasons = func(df_result.iloc[:i+1])
                if score >= threshold:
                    entry_price = row["close"]
                    atr = None
                    if i >= 14:
                        sub_df = df_result.iloc[max(0, i - 14):i + 1]
                        atr = ta.volatility.AverageTrueRange(
                            high=sub_df["high"],
                            low=sub_df["low"],
                            close=sub_df["close"],
                            window=14
                        ).average_true_range().iloc[-1]

                    if atr and not pd.isna(atr):
                        sl_price = entry_price - SL_MULTIPLIER * atr
                        tp_price = entry_price + SL_MULTIPLIER * RR_RATIO * atr
                    else:
                        sl_price = None
                        tp_price = None

                    print(f"✅ סיגנל: {symbol}, אסטרטגיה={name}, ציון={score}, זמן={row['time']}")
                    all_results.append({
                        "symbol": symbol,
                        "strategy": name,
                        "score": score,
                        "reasons": "; ".join(reasons),
                        "time": row["time"],
                        "interval": interval,
                        "entry_price": entry_price,
                        "SL": sl_price,
                        "TP": tp_price
                    })
        except Exception as e:
            print(f"⚠️ שגיאה באסטרטגיה {name}: {e}")

# 💾 שמירה לקובץ
signals_df = pd.DataFrame(all_results)
signals_df.to_csv("strategy_signals_output.csv", index=False, encoding="utf-8-sig")
print("✅ נשמרו סיגנלים לקובץ strategy_signals_output.csv")
