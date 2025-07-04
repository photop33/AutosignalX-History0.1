import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
import lightgbm as lgb


df = pd.read_csv("strategy_signals_master.csv")



df['time'] = pd.to_datetime(df['time'])
df['year'] = df['time'].dt.year
df['month'] = df['time'].dt.month
df['day_of_week'] = df['time'].dt.dayofweek
df['hour'] = df['time'].dt.hour

# Lag לדוג' 3 נרות אחורה
for i in range(1, 5):
    df[f'close_lag_{i}'] = df['close'].shift(i)
    df[f'rsi_lag_{i}'] = df['rsi'].shift(i)
    df[f'volume_lag_{i}'] = df['volume'].shift(i)
    df[f'macd_lag_{i}'] = df['macd'].shift(i)
    df[f'adx_lag_{i}'] = df['adx'].shift(i)

# Rolling ממוצע
df['vol_rolling_5'] = df['volume'].rolling(5).mean()
df = df.dropna().reset_index(drop=True)



features = [
    'open','high','low','close','volume','rsi','macd','macd_signal','macd_diff',
    'adx','ema_short','ema_long','bb_width','volatility','atr','cci','parabolic_sar',
    'vwap','wma','trix','bb_upper','bb_middle','bb_lower',
    'hour','day_of_week','month'
] + [col for col in df.columns if col.startswith('interval_')]
target = 'result'  # או target אם הפכת TP Hit=1, SL Hit=0
# מומלץ להמיר ל־0/1:
df['target'] = (df['result'] == "TP Hit").astype(int)
df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')  # dayfirst=True לפורמט שלך
df['hour'] = df['time'].dt.hour
df['day_of_week'] = df['time'].dt.dayofweek  # 0=Monday, 6=Sunday
df['month'] = df['time'].dt.month
df = pd.get_dummies(df, columns=["interval"])




X = df[features]
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False) # time split!



clf = lgb.LGBMClassifier(n_estimators=100)
clf.fit(X_train, y_train)




y_pred = clf.predict(X_test)
y_proba = clf.predict_proba(X_test)[:,1]
print(classification_report(y_test, y_pred))
print("AUC:", roc_auc_score(y_test, y_proba))



# סיגנל חדש, לדוג' השורה האחרונה
signal = X_test.iloc[-1]
prob = clf.predict_proba([signal])[0][1]
print(f"הסתברות הצלחה: {round(prob*100,2)}%")
