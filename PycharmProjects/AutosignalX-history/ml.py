import os
import pandas as pd
from datetime import datetime, timedelta
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score
import time

# === נתיב לבסיס קבצי נרות ===
CANDLES_BASE_DIR = "data/historical_kline"  # עדכן לפי הנתיב אצלך
SIGNALS_FILE = "all_data_btc - No result.csv"  # עדכן אם שם הקובץ שונה
PERFORMANCE_LOG = "model_performance_log.csv"

# === פונקציה לטעינת כל קבצי הנרות מראש (cache) ===
def load_all_candles(symbol, interval, start_date, end_date):
    print(f"🚀 טוען את כל הנרות של {symbol} ב-{interval} מ-{start_date} עד {end_date}...")
    current_date = start_date
    candles_cache = {}

    while current_date <= end_date:
        year, month, day = current_date.year, current_date.month, current_date.day
        filename = f"{symbol}_{year:04d}-{month:02d}-{day:02d}_{interval}.csv"
        filepath = os.path.join(
            CANDLES_BASE_DIR, symbol, f"{year:04d}", f"{month:02d}", f"{day:02d}", interval, filename
        )
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            candles_cache[current_date] = df
        else:
            print(f"⚠️ לא נמצא קובץ: {filepath}")
        current_date += timedelta(days=1)
    print(f"✅ סיום טעינת נרות. סך הכל ימים: {len(candles_cache)}")
    return candles_cache

# === הפוך שורת סיגנל לפיצ'רים עם שימוש ב-cache ===
def build_features_from_signal_cached(row, candles_cache):
    symbol = row['symbol']
    interval = row['interval']
    signal_time = pd.to_datetime(row['time'], dayfirst=True, errors='coerce')

    candles = []
    current_date = signal_time.date()
    days_checked = 0
    max_days_back = 60
    n = 5

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

    return {
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

# === טען את המודל הטוב ביותר מהרישום ===
def load_best_model():
    if not os.path.exists(PERFORMANCE_LOG):
        return None, None
    df_perf = pd.read_csv(PERFORMANCE_LOG)
    if df_perf.empty:
        return None, None
    best_row = df_perf.loc[df_perf['auc'].idxmax()]
    best_model_file = best_row['model_file']
    if os.path.exists(best_model_file):
        print(f"⚡️ טוען את המודל הטוב ביותר: {best_model_file} עם AUC={best_row['auc']:.3f}")
        model = lgb.Booster(model_file=best_model_file)
        return model, best_row['auc']
    return None, None

# === שמירת ביצועי מודל בלוג ===
def save_model_performance(model_file, auc, accuracy):
    if os.path.exists(PERFORMANCE_LOG):
        df_perf = pd.read_csv(PERFORMANCE_LOG)
    else:
        df_perf = pd.DataFrame(columns=['date', 'model_file', 'auc', 'accuracy'])
    new_row = {
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'model_file': model_file,
        'auc': auc,
        'accuracy': accuracy
    }
    df_perf = pd.concat([df_perf, pd.DataFrame([new_row])], ignore_index=True)
    df_perf.to_csv(PERFORMANCE_LOG, index=False)
    print(f"✅ שמרתי את ביצועי המודל בלוג.")

# === שלב ראשי ===
start_time_total = time.time()

df_signals = pd.read_csv(SIGNALS_FILE, dtype={"interval": str}, low_memory=False)
df_signals['time'] = pd.to_datetime(df_signals['time'], dayfirst=True, errors='coerce')

# סנן עסקאות סגורות בלבד
df_signals = df_signals[df_signals['result'].isin(['TP Hit', 'SL Hit'])]

# טווח תאריכים לטעינת הנרות
start_date = df_signals['time'].min().date() - timedelta(days=65)
end_date = df_signals['time'].max().date()

start_time_cache = time.time()
symbol_example = df_signals.iloc[0]['symbol']
interval_example = df_signals.iloc[0]['interval']
candles_cache = load_all_candles(symbol_example, interval_example, start_date, end_date)
end_time_cache = time.time()
print(f"⏱️ זמן טעינת נרות: {end_time_cache - start_time_cache:.2f} שניות")

features_list = []
targets = []

start_time_features = time.time()
for _, row in df_signals.iterrows():
    feats = build_features_from_signal_cached(row, candles_cache)
    if feats:
        features_list.append(feats)
        target = 1 if row['result'] == 'TP Hit' else 0
        targets.append(target)
end_time_features = time.time()
print(f"⏱️ זמן בניית פיצ'רים: {end_time_features - start_time_features:.2f} שניות")

df_features = pd.DataFrame(features_list)
df_features['target'] = targets

X = df_features.drop(columns=["target"])
y = df_features["target"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

best_model, best_auc = load_best_model()

start_time_train = time.time()

if best_model is not None:
    print("⚡️ משתמש במודל הטוב ביותר מהרישום לאימון והערכה")
    clf = lgb.LGBMClassifier(n_estimators=100, class_weight='balanced')
    clf._Booster = best_model
    # ממשיך לאמן על סט האימון - אפשר להוסיף אימון מחדש עם פרמטרים מתקדמים כאן
    clf.fit(X_train, y_train)
else:
    print("🚀 מאמן מודל חדש...")
    clf = lgb.LGBMClassifier(n_estimators=100, class_weight='balanced')
    clf.fit(X_train, y_train)

end_time_train = time.time()
print(f"⏱️ זמן אימון מודל: {end_time_train - start_time_train:.2f} שניות")

# הערכת המודל
y_pred = clf.predict(X_test)
y_proba = clf.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred))
auc = roc_auc_score(y_test, y_proba)
accuracy = accuracy_score(y_test, y_pred)
print(f"AUC: {auc:.4f} | Accuracy: {accuracy:.4f}")

# שמירת מודל רק אם הביצועים טובים יותר
if best_auc is None or auc > best_auc:
    model_name = f"model_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_auc{auc:.4f}.txt"
    clf.booster_.save_model(model_name)
    print(f"✅ שמרתי מודל חדש: {model_name}")
    save_model_performance(model_name, auc, accuracy)
else:
    print("ℹ️ המודל החדש לא שיפר את הביצועים - לא שמרתי.")

# חיזוי עסקה אחרונה
signal = X_test.iloc[[-1]]
prob = clf.predict_proba(signal)[0][1]
print(f"הסתברות הצלחה לעסקה האחרונה: {round(prob * 100, 2)}%")

end_time_total = time.time()
print(f"⏱️ זמן כולל להרצה: {end_time_total - start_time_total:.2f} שניות")
