import os
import pandas as pd

base_dir = r"C:\Users\LiorSw\PycharmProjects\AutosignalX-history\data\historical_kline\BTCUSDT"
all_files = []

for year in os.listdir(base_dir):
    year_dir = os.path.join(base_dir, year)
    if not os.path.isdir(year_dir):
        continue
    for month in os.listdir(year_dir):
        month_dir = os.path.join(year_dir, month)
        if not os.path.isdir(month_dir):
            continue
        for day in os.listdir(month_dir):
            day_dir = os.path.join(month_dir, day)
            if not os.path.isdir(day_dir):
                continue
            for interval in os.listdir(day_dir):
                interval_dir = os.path.join(day_dir, interval)
                if not os.path.isdir(interval_dir):
                    continue
                for file in os.listdir(interval_dir):
                    if file.endswith(".csv"):
                        all_files.append(os.path.join(interval_dir, file))

print(f"נמצאו {len(all_files)} קבצי CSV לסריקה.")

if not all_files:
    print("❌ לא נמצאו קבצים. בדוק את עץ התיקיות והנתיב!")
else:
    # קריאה ואיחוד כל הקבצים
    df_list = [pd.read_csv(f) for f in all_files]
    df = pd.concat(df_list, ignore_index=True)
    df.to_csv("all_candles_merged.csv", index=False)
    print("✅ איחוד קבצים הסתיים! נשמר ל־all_candles_merged.csv")
