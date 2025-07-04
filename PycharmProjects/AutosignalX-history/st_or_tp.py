import pandas as pd
import requests
import os
from datetime import datetime
import sys
import io


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# === הגדרות ===
SIGNALS_FILE = "strategy_signals_output.csv"
OUTPUT_FILE = "strategy_signals_results_with_tp_sl.csv"
BINANCE_API = "https://api.binance.com"
MAX_CANDLES = 1000  # עד כמות נרות קדימה לבדיקה

# ✅ קאשינג לפי סימבול + יום
candles_cache = {}

def to_milliseconds(dt):
    return int(dt.timestamp() * 1000)

def fetch_candles(symbol, start_time, limit=MAX_CANDLES):
    """ משיכת נרות 5m מ-Binance עם קאשינג לפי סימבול + יום """
    date_key = f"{symbol}_{start_time.strftime('%Y-%m-%d')}"
    if date_key in candles_cache:
        return candles_cache[date_key]

    params = {
        "symbol": symbol,
        "interval": "5m",
        "startTime": to_milliseconds(start_time),
        "limit": limit
    }
    url = f"{BINANCE_API}/api/v3/klines"
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(f"⚠️ שגיאה בבקשה ל-Binance עבור {symbol}: {r.text}")
        return None

    raw = r.json()
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df = df[["open_time", "high", "low"]]

    candles_cache[date_key] = df
    return df

# טעינת סיגנלים
if not os.path.exists(SIGNALS_FILE) or os.path.getsize(SIGNALS_FILE) == 0:
    print(f"⚠️ הקובץ {SIGNALS_FILE} לא קיים או ריק – אין מה לבדוק")
    exit()

df = pd.read_csv(SIGNALS_FILE)
df["time"] = pd.to_datetime(df["time"], errors="coerce")

required_cols = {"symbol", "time", "interval", "entry_price", "TP", "SL"}
if not required_cols.issubset(df.columns):
    raise ValueError(f"❌ חסרות עמודות בקובץ. נדרשות: {required_cols}")

results = []

# הרצת הבדיקה
for _, row in df.iterrows():
    symbol = row["symbol"]
    entry_time = row["time"]
    entry_price = float(row["entry_price"])
    tp = float(row["TP"])
    sl = float(row["SL"])
    result = "Still Open"
    cross_time = None

    print(f"\n🔍 בודק {symbol} | כניסה: {entry_price} | TP: {tp} | SL: {sl} | מ־{entry_time}")
    candles = fetch_candles(symbol, entry_time)

    if candles is not None:
        for _, candle in candles.iterrows():
            high = candle["high"]
            low = candle["low"]
            candle_time = candle["open_time"]

            if high >= tp and low <= sl:
                if abs(tp - entry_price) < abs(entry_price - sl):
                    result = "TP Hit"
                else:
                    result = "SL Hit"
                cross_time = candle_time
                print(f"⚔️ גם TP וגם SL באותו נר. נבחר: {result} | זמן: {cross_time}")
                break
            elif high >= tp:
                result = "TP Hit"
                cross_time = candle_time
                print(f"✅ TP Hit ב־{cross_time}")
                break
            elif low <= sl:
                result = "SL Hit"
                cross_time = candle_time
                print(f"🛑 SL Hit ב־{cross_time}")
                break
        else:
            print("⏳ לא נמצאה חציית TP או SL")
    else:
        print("⚠️ לא הוחזרו נרות")

    row["result"] = result
    row["cross_line_time"] = cross_time
    results.append(row)

# חישוב רווח/הפסד באחוזים
results_df = pd.DataFrame(results)

def calc_pnl(row):
    entry = float(row['entry_price'])
    tp = float(row['TP'])
    sl = float(row['SL'])
    result = row['result']
    if result == "TP Hit":
        return round((tp - entry) / entry * 100, 2)
    elif result == "SL Hit":
        return round((sl - entry) / entry * 100, 2)
    else:
        return None

results_df['PnL_%'] = results_df.apply(calc_pnl, axis=1)


# === שלב הוספת פיצ'רי נר לכל עסקה ===

master_rows = []
for idx, row in results_df.iterrows():
    symbol = row["symbol"]
    interval = row["interval"]
    signal_time = row["time"] if isinstance(row["time"], pd.Timestamp) else pd.to_datetime(row["time"])
    date_part = signal_time.strftime("%Y/%m/%d")
    base_dir = f"data/historical_kline/{symbol}/{date_part}/{interval}"
    filename = f"{symbol}_{signal_time.strftime('%Y-%m-%d')}_{interval}.csv"
    full_path = os.path.join(base_dir, filename)

    candle_features = {}
    if os.path.exists(full_path):
        raw_df = pd.read_csv(full_path)
        if "time" in raw_df.columns:
            raw_df["time"] = pd.to_datetime(raw_df["time"])
            candle = raw_df.loc[raw_df["time"] == signal_time]
            if candle.empty:
                candle = raw_df.iloc[(raw_df["time"] - signal_time).abs().argsort()[:1]]
            if not candle.empty:
                candle_features = candle.iloc[0].to_dict()
    # איחוד בין כל הנתונים
    full_row = dict(row)
    for col, val in candle_features.items():
        if col not in full_row:
            full_row[col] = val
    master_rows.append(full_row)

master_df = pd.DataFrame(master_rows)

# שמור את המאסטר הסופי
MASTER_FILE = "strategy_signals_master.csv"
try:
    master_df.to_csv(MASTER_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ נשמר לקובץ: {MASTER_FILE}")
except PermissionError:
    print(f"\n❌ פתוח - סגור אותו ותריץ שוב {MASTER_FILE} האקסל ")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ שגיאה לא צפויה בשמירת הקובץ: {e}")
    sys.exit(1)
