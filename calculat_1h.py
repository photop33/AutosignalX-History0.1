import pandas as pd

# הנתיבים (רצוי להגדיר משתנים/פורמטרים אוטומטיים!)
path_prev = r"C:/Users/LiorSw/PycharmProjects/AutosignalX-history/data/historical_kline/BTCUSDT/2025/05/21/1h/BTCUSDT_2025-05-21_1h.csv"
path_curr = r"C:/Users/LiorSw/PycharmProjects/AutosignalX-history/data/historical_kline/BTCUSDT/2025/05/22/1h/BTCUSDT_2025-05-22_1h.csv"

# קריאה
df_prev = pd.read_csv(path_prev, parse_dates=['time'])
df_curr = pd.read_csv(path_curr, parse_dates=['time'])

# קח את השורה האחרונה של אתמול (23:00)
last_row_prev = df_prev.iloc[[-1]]

# חבר לראש הנתונים של היום הנוכחי
df_combined = pd.concat([last_row_prev, df_curr], ignore_index=True)
df_combined = df_combined.sort_values('time').set_index('time')

# שים לב: עכשיו כשאתה עושה shift/resample – ה־4H שלך יתחיל מ־23:00 של היום הקודם!
df_combined.index = df_combined.index - pd.Timedelta(hours=1)

agg_dict = {
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum',
    # שאר העמודות...
}

for col in df_combined.columns:
    if col not in agg_dict:
        agg_dict[col] = 'mean'

df_4h = df_combined.resample('4H').agg(agg_dict)
df_4h = df_4h.dropna(subset=['open', 'close'])

# אם תרצה להחזיר את השעה המקורית
df_4h.index = df_4h.index + pd.Timedelta(hours=1)

df_4h.to_csv("BTCUSDT_2025-05-22_4h.csv")
print(df_4h.head())
