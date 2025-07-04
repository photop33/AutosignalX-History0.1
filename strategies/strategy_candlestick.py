def is_bullish_engulfing(prev, curr):
    return (
        prev['close'] < prev['open'] and
        curr['close'] > curr['open'] and
        curr['close'] > prev['open'] and
        curr['open'] < prev['close']
    )

def is_hammer(candle):
    open_ = candle['open']
    close = candle['close']
    high = candle['high']
    low = candle['low']

    body = abs(close - open_)
    candle_range = high - low
    lower_wick = min(open_, close) - low
    upper_wick = high - max(open_, close)

    return (
        close > open_ and  # ✅ נר ירוק בלבד
        body > 0 and
        candle_range > 0 and
        lower_wick >= body * 2 and
        upper_wick <= body * 0.5 and
        (min(open_, close) - low) / candle_range >= 0.5  # גוף בחצי העליון
    )


def strategy_candlestick(df):
    df = df.copy()
    if len(df) < 3:
        return 0, ["לא מספיק נרות"]

    prev = df.iloc[-2]
    last = df.iloc[-1]

    score = 0
    reasons = []

    if is_bullish_engulfing(prev, last):
        score += 1
        reasons.append("Engulfing שורי")

    if is_hammer(last):
        score += 1
        reasons.append("תבנית Hammer")

    return score, reasons
