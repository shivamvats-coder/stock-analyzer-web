import os
import csv
import io
import requests
from typing import List, Dict
from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.loader import load_csv
from core.sort_algos import merge_sort_by_company
from core.search import find_company_block
from core.analytics import average_volume, price_summary
from web.data_live import fetch_yf_ohlc, add_ma_ema

ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")  # optional, for fallback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="web/static"), name="static")

@app.get("/")
def home():
    return FileResponse("web/templates/index.html")


@app.get("/api/companies")
def get_companies():
    try:
        data = load_csv("sample_data.csv")
        sample_companies = sorted({r.company for r in data})
    except Exception:
        sample_companies = []

    curated_live = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "SBIN.NS", "LT.NS", "HINDUNILVR.NS", "BAJFINANCE.NS"
    ]
    return {"sample": sample_companies, "live": curated_live}


@app.get("/api/featured")
def featured_snapshot():
    """
    Return a small snapshot for curated tickers: last close, previous close, pct change.
    """
    curated = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    out = []
    for t in curated:
        recs = fetch_yf_ohlc(t, period="5d", interval="1d")
        if not recs:
            out.append({"ticker": t, "last": None, "prev": None, "pct": None})
            continue
        last = recs[-1]["close"]
        prev = recs[-2]["close"] if len(recs) >= 2 else recs[-1]["open"]
        pct = ((last - prev) / prev * 100) if prev else None
        out.append({"ticker": t, "last": last, "prev": prev, "pct": round(pct, 2) if pct is not None else None})
    return {"featured": out}


def _try_alpha(ticker: str, period: str = "1mo"):
    """
    Very small Alpha Vantage fallback attempt. Returns records in same shape or [].
    Note: requires ALPHA_VANTAGE_KEY env on server.
    """
    if not ALPHA_KEY:
        return []
    base = "https://www.alphavantage.co/query"
    params = {"function": "TIME_SERIES_DAILY", "symbol": ticker, "apikey": ALPHA_KEY, "outputsize": "compact"}
    try:
        r = requests.get(base, params=params, timeout=12)
        if r.status_code != 200:
            return []
        j = r.json()
        # parse Time Series (Daily)
        key = next((k for k in j.keys() if k.startswith("Time Series")), None)
        if not key:
            return []
        ts = j[key]
        items = sorted(ts.items())  # chronological
        out = []
        for date_str, vals in items:
            out.append({
                "date": date_str,
                "open": float(vals.get("1. open", 0)),
                "high": float(vals.get("2. high", 0)),
                "low": float(vals.get("3. low", 0)),
                "close": float(vals.get("4. close", 0)),
                "volume": int(float(vals.get("5. volume", 0)))
            })
        return out
    except Exception:
        return []


def _normalize_india(ticker: str) -> str:
    s = ticker.strip().upper()
    # if looks like NSE short name without suffix, add .NS
    if "." not in s and not s.endswith(".NS"):
        return s + ".NS"
    return s


@app.get("/api/live/{ticker}")
def live_company_data(
    ticker: str,
    period: str = Query("6mo"),
    interval: str = Query("1d")
):
    t = _normalize_india(ticker)
    records = fetch_yf_ohlc(t, period=period, interval=interval)
    if not records:
        # try alpha fallback
        records = _try_alpha(t)
        if not records:
            return JSONResponse({"error": "No live data found"}, status_code=404)

    highs = max(r["high"] for r in records) if records else None
    lows = min(r["low"] for r in records) if records else None
    summary = {
        "highest": highs,
        "lowest": lows,
        "first_open": records[0]["open"] if records else None,
        "last_close": records[-1]["close"] if records else None
    }
    avg_vol = sum(r["volume"] for r in records) / max(1, len(records)) if records else 0
    me = add_ma_ema(records)
    return {"company": t, "records": records, "analytics": {"avg_volume": avg_vol, "summary": summary, "ma": me["ma"], "ema": me["ema"]}}


@app.get("/api/compare")
def compare_endpoint(
    t1: str = Query(...),
    t2: str = Query(...),
    source: str = Query("live"),
    period: str = Query("6mo"),
    interval: str = Query("1d"),
    mode: str = Query("overlay")
):
    def load_for(ticker, src):
        if src == "live":
            tt = _normalize_india(ticker)
            recs = fetch_yf_ohlc(tt, period=period, interval=interval)
            if not recs:
                recs = _try_alpha(tt)
            me = add_ma_ema(recs)
            highs = max(r["high"] for r in recs) if recs else None
            lows = min(r["low"] for r in recs) if recs else None
            avg_vol = (sum(r["volume"] for r in recs)/len(recs)) if recs else 0
            summary = {"highest": highs, "lowest": lows, "first_open": recs[0]["open"] if recs else None, "last_close": recs[-1]["close"] if recs else None}
            return {"records": recs, "analytics": {"avg_volume": avg_vol, "summary": summary, "ma": me["ma"], "ema": me["ema"]}}
        else:
            data = load_csv("sample_data.csv")
            sorted_data = merge_sort_by_company(data)
            res = find_company_block(sorted_data, ticker)
            recs = [{"date": str(r.date), "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in res]
            me = add_ma_ema(recs)
            return {"records": recs, "analytics": {"avg_volume": average_volume(res) if res else 0, "summary": price_summary(res) if res else {}, "ma": me["ma"], "ema": me["ema"]}}

    left = load_for(t1, source)
    right = load_for(t2, source)
    if not left["records"] and not right["records"]:
        return JSONResponse({"error": "No data for both tickers"}, status_code=404)
    return {"t1": t1.strip().upper(), "t2": t2.strip().upper(), "mode": mode, "left": left, "right": right}


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    s = content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(s))
    out = []
    for row in reader:
        try:
            d = row.get("date") or row.get("Date")
            o = float(row.get("open") or row.get("Open") or 0)
            h = float(row.get("high") or row.get("High") or 0)
            l = float(row.get("low") or row.get("Low") or 0)
            c = float(row.get("close") or row.get("Close") or 0)
            v = int(float(row.get("volume") or row.get("Volume") or 0))
            out.append({"date": str(d).strip(), "open": o, "high": h, "low": l, "close": c, "volume": v})
        except Exception:
            continue
    if not out:
        return JSONResponse({"error": "No valid rows found"}, status_code=400)
    highs = max(r["high"] for r in out)
    lows = min(r["low"] for r in out)
    summary = {"highest": highs, "lowest": lows, "first_open": out[0]["open"], "last_close": out[-1]["close"]}
    avg_vol = sum(r["volume"] for r in out) / max(1, len(out))
    me = add_ma_ema(out)
    return {"company": file.filename, "records": out, "analytics": {"avg_volume": avg_vol, "summary": summary, "ma": me["ma"], "ema": me["ema"]}}


@app.post("/api/export")
async def export_csv(payload: Dict = None):
    if not payload or "records" not in payload:
        return JSONResponse({"error": "Invalid payload"}, status_code=400)
    records = payload["records"]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "open", "high", "low", "close", "volume"])
    for r in records:
        writer.writerow([r.get("date"), r.get("open"), r.get("high"), r.get("low"), r.get("close"), r.get("volume")])
    buf.seek(0)
    return FileResponse(io.BytesIO(buf.getvalue().encode("utf-8")), media_type="text/csv", filename="export.csv")
