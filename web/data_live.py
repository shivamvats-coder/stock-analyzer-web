import yfinance as yf
import pandas as pd

def fetch_yf_ohlc(ticker: str, period: str = "6mo", interval: str = "1d"):
    """
    Yahoo Finance se OHLCV fetch.
    Returns: list[dict] -> {date, open, high, low, close, volume}
    Note: Indian stocks ke liye usually ticker ke end me '.NS' lagta hai (e.g., TCS.NS, RELIANCE.NS).
    """
    t = ticker.strip().upper()
    df = yf.download(t, period=period, interval=interval, auto_adjust=False, progress=False)
    if df is None or df.empty:
        return []

    df = df.reset_index()
    date_col = "Date" if "Date" in df.columns else "Datetime"
    df[date_col] = pd.to_datetime(df[date_col]).dt.date

    out = []
    for _, row in df.iterrows():
        out.append({
            "date": str(row[date_col]),
            "open": float(row.get("Open", 0.0)),
            "high": float(row.get("High", 0.0)),
            "low": float(row.get("Low", 0.0)),
            "close": float(row.get("Close", 0.0)),
            "volume": int(row.get("Volume", 0) or 0),
        })
    return out

def add_ma_ema(records, windows=(5, 10, 20)):
    """
    Simple Moving Average (SMA) + Exponential Moving Average (EMA).
    Output: {"ma": {5:[...],10:[...],...}, "ema": {...}}
    """
    if not records:
        return {"ma": {}, "ema": {}}
    closes = pd.Series([r["close"] for r in records], dtype="float64")
    ma, ema = {}, {}
    for w in windows:
        ma[w] = list(closes.rolling(window=w, min_periods=1).mean().round(4))
        ema[w] = list(closes.ewm(span=w, adjust=False).mean().round(4))
    return {"ma": ma, "ema": ema}
