from config import INDICATOR_CONDITIONS


def strategy_rsi_macd(df):

    RSI_OVERSOLD = INDICATOR_CONDITIONS["RSI_OVERSOLD"]
    EMA_SHORT = INDICATOR_CONDITIONS["EMA_SHORT"]
    EMA_LONG = INDICATOR_CONDITIONS["EMA_LONG"]
    VOLUME_LOOKBACK = INDICATOR_CONDITIONS["VOLUME_LOOKBACK"]

    df = df.copy()
    last = df.iloc[-1]
    prev = df.iloc[-2]

    buy_score = 0
    reasons = []

    if prev['rsi'] < RSI_OVERSOLD and last['rsi'] > RSI_OVERSOLD:
        buy_score += 1
        reasons.append("RSI יצא ממכירת יתר")

    if prev['macd'] < prev['macd_signal'] and last['macd'] > last['macd_signal']:
        buy_score += 1
        reasons.append("MACD חצה מעלה")

    if prev['ema_short'] < prev['ema_long'] and last['ema_short'] > last['ema_long']:
        buy_score += 1
        reasons.append("EMA חצה")

    avg_vol = df['volume'].rolling(VOLUME_LOOKBACK).mean().iloc[-1]
    if last['volume'] > avg_vol:
        buy_score += 1
        reasons.append("ווליום גבוה מהממוצע")

    # מחזירים את שני הערכים: הציון והרשימה עם הסיבות
    return buy_score, reasons
