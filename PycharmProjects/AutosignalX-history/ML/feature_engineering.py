from datetime import timedelta
import pandas as pd

def build_features_from_signal_cached(row, candles_cache, n=5, max_days_back=60):
    symbol = row['symbol']
    interval = row['interval']
    signal_time = pd.to_datetime(row['time'], dayfirst=True, errors='coerce')

    candles = []
    current_date = signal_time.date()
    days_checked = 0

    while len(candles) < n and days_checked < max_days_back:
        current_date -= timedelta(days=1)
        days_checked += 1

        daily_data = candles_cache.get(current_date)
        if daily_data is not None:
            filtered = daily_data[daily_data['time'] < signal_time]
            candles.extend(filtered.sort_values('time', ascending=False).to_dict("records"))

    if len(candles) < 2:
        return None

    c1, c2 = candles[0], candles[1]
    avg_vol = sum(c['volume'] for c in candles) / len(candles)

    features = {
        'close_lag_1': c1['close'],
        'close_lag_2': c2['close'],
        'rsi_lag_1': c1['rsi'],
        'rsi_lag_2': c2['rsi'],
        'macd_lag_1': c1['macd'],
        'adx_lag_1': c1['adx'],
        'volume_lag_1': c1['volume'],
        'volume_rolling_5': avg_vol,
        'hour': signal_time.hour,
        'day_of_week': signal_time.dayofweek,
        'month': signal_time.month
    }

    # דוגמא של תבניות לחיפוש ב-'reasons'
    patterns = [
        "engulfing שורי",
        "תבנית hammer",
        "פריצה כלפי מעלה",
        "ווליום תומך בפריצה",
        "קפיצה מעל vwap",
        "נפח מסחר גבוה"
    ]

    reasons_text = str(row.get('reasons', '')).lower()
    for p in patterns:
        features[f'reason_{p}'] = int(p in reasons_text)

    # קטגוריה מהאסטרטגיה
    strategy_val = str(row.get("strategy", "unknown"))
    features[f'strategy_{strategy_val}'] = 1

    return features
