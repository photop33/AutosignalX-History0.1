import os
import pandas as pd
from datetime import timedelta

CANDLES_BASE_DIR = r"C:\Users\LiorSw\PycharmProjects\AutosignalX-history\data\historical_kline"

def load_candle(symbol, date, interval):
    year, month, day = date.year, date.month, date.day
    filename = f"{symbol}_{year:04d}-{month:02d}-{day:02d}_{interval}.csv"
    filepath = os.path.join(
        CANDLES_BASE_DIR, symbol, f"{year:04d}", f"{month:02d}", f"{day:02d}", interval, filename
    )
    if not os.path.exists(filepath):
        return None
    df = pd.read_csv(filepath)
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    return df

def load_all_candles(symbol, interval, start_date, end_date):
    print(f"🚀 טוען את כל הנרות של {symbol} ב-{interval} מ-{start_date} עד {end_date}...")
    current_date = start_date
    candles_cache = {}

    while current_date <= end_date:
        df = load_candle(symbol, current_date, interval)
        if df is not None:
            candles_cache[current_date] = df
        else:
            print(f"⚠️ לא נמצא קובץ עבור תאריך {current_date}")
        current_date += timedelta(days=1)
    print(f"✅ סיום טעינת נרות. סך הכל ימים: {len(candles_cache)}")
    return candles_cache
