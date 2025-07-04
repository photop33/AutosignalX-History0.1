import os
import time
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report

from data_loading import load_all_candles
from feature_engineering import build_features_from_signal_cached
from modeling import train_or_load_model

BASE_DIR = r"C:\Users\LiorSw\PycharmProjects\AutosignalX-history\ML\log"
MODEL_FILE = os.path.join(BASE_DIR, "lgbm_model.txt")
SIGNALS_FILE=os.path.join(BASE_DIR, "all_data_btc - No result.csv")
def main():
    start_time_total = time.time()

    df_signals = pd.read_csv(SIGNALS_FILE, dtype={"interval": str}, low_memory=False)
    df_signals['time'] = pd.to_datetime(df_signals['time'], dayfirst=True, errors='coerce')
    df_signals = df_signals[df_signals['result'].isin(['TP Hit', 'SL Hit'])]

    start_date = df_signals['time'].min().date() - pd.Timedelta(days=65)
    end_date = df_signals['time'].max().date()

    symbol_example = df_signals.iloc[0]['symbol']
    interval_example = df_signals.iloc[0]['interval']

    candles_cache = load_all_candles(symbol_example, interval_example, start_date, end_date)

    features_list = []
    targets = []

    for _, row in df_signals.iterrows():
        feats = build_features_from_signal_cached(row, candles_cache)
        if feats:
            features_list.append(feats)
            target = 1 if row['result'] == 'TP Hit' else 0
            targets.append(target)

    df_features = pd.DataFrame(features_list)
    df_features['target'] = targets

    # המרת קטגוריות לפיצ'רים בינאריים (אם יש)
    X = pd.get_dummies(df_features.drop(columns=["target"]))
    y = df_features["target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # וודא התאמה מלאה של העמודות בין אימון לבדיקה (מילוי אפסים להבדלים)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

    clf, X_test, y_test = train_or_load_model(X_train, y_train, X_test, y_test)

    # חישוב הסתברויות וחיזוי
    if hasattr(clf, "predict_proba"):
        y_proba = clf.predict_proba(X_test)[:, 1]
    else:
        y_proba = clf.predict(X_test)  # במקרה של Booster

    y_pred = (y_proba > 0.5).astype(int)

    print(classification_report(y_test, y_pred))
    print("AUC:", roc_auc_score(y_test, y_proba))

    signal = X_test.iloc[[-1]]
    if hasattr(clf, "predict_proba"):
        prob = clf.predict_proba(signal)[0][1]
    else:
        prob = clf.predict(signal)[0]

    print(f"הסתברות הצלחה לעסקה האחרונה: {round(prob * 100, 2)}%")

    end_time_total = time.time()
    print(f"⏱️ זמן כולל להרצה: {end_time_total - start_time_total:.2f} שניות")

if __name__ == "__main__":
    main()
