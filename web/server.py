import os
import csv
import io
import requests
from typing import List, Dict
from fastapi import FastAPI, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.loader import load_csv
from core.sort_algos import merge_sort_by_company
from core.search import find_company_block
from core.analytics import average_volume, price_summary
from web.data_live import fetch_yf_ohlc, add_ma_ema

ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")  # optional

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
    """
    Returns available companies: from sample CSV + curated live tickers.
    Frontend will call this to populate dropdowns.
    """
    # read sample CSV companies
    try:
        data = load_csv("sample_data.csv")
        sample_companies = sorted({r.company for r in data})
    except Exception:
        sample_companies = []

    # curated live tickers (Indian examples); you can edit this list anytime
    curated_live = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "SBIN.NS", "LT.NS", "HINDUNILVR.NS", "BAJFINANCE.NS"
    ]

    return {"sample": sample_companies, "live": curated_live}


@app.get("/api/company/{ticker}")
def get_company_data(ticker: str):
    """
    Existing CSV-based endpoint (keeps previous behavior).
    """
    data = load_csv("sample_data.csv")
    sorted_data = merge_sort_by_company(data)
    result = find_company_block(sorted_data, ticker)

    if not result:
        return JSONResponse({"error": "Company not found"}, status_code=404)

    analytics = {
        "avg_volume": average_volume(result),
        "summary": price_summary(result)
    }

    records = [
        {
            "date": str(r.date),
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
        }
        for r in result
    ]

    return {"company": ticker.strip().upper(), "records": records, "analytics": analytics}


@app.get("/api/live/{ticker}")
def live_company_data(
    ticker: str,
    period: str = Query("6mo"),
    interval: str = Query("1d")
):
    """
    Live data via yfinance (already added earlier).
    """
    records = fetch_yf_ohlc(ticker, period=period, interval=interval)
    if not records:
        return JSONResponse({"error": "No live data found"}, status_code=404)

    highs = max(r["high"] for r in records)
    lows = min(r["low"] for r in records)
    summary = {
        "highest": highs,
        "lowest": lows,
        "first_open": records[0]["open"],
        "last_close": records[-1]["close"]
    }
    avg_vol = sum(r["volume"] for r in records) / max(1, len(records))
    me = add_ma_ema(records, windows=(5, 10, 20))

    return {
        "company": ticker.strip().upper(),
        "records": records,
        "analytics": {
            "avg_volume": avg_vol,
            "summary": summary,
            "ma": me["ma"],
            "ema": me["ema"]
        }
    }


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Accept a CSV upload. Returns parsed records (same shape as other endpoints).
    This is temporary: frontend can use returned records immediately.
    """
    content = await file.read()
    s = content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(s))
    out = []
    for row in reader:
        try:
            d = row.get("date") or row.get("Date")
            o = float(row.get("open") or row.get("Open") or 0)
            h = float(row.get("high") or row.get("High") or 0)
            l = float(row.get("low")  or row.get("Low")  or 0)
            c = float(row.get("close") or row.get("Close") or 0)
            v = int(float(row.get("volume") or row.get("Volume") or 0))
            out.append({"date": str(d).strip(), "open": o, "high": h, "low": l, "close": c, "volume": v})
        except Exception:
            continue
    if not out:
        return JSONResponse({"error":"No valid rows found"}, status_code=400)
    # compute analytics
    highs = max(r["high"] for r in out)
    lows = min(r["low"] for r in out)
    summary = {"highest": highs, "lowest": lows, "first_open": out[0]["open"], "last_close": out[-1]["close"]}
    avg_vol = sum(r["volume"] for r in out) / max(1, len(out))
    me = add_ma_ema(out)
    return {"company": file.filename, "records": out, "analytics": {"avg_volume": avg_vol, "summary": summary, "ma": me["ma"], "ema": me["ema"]}}


@app.post("/api/export")
async def export_csv(payload: Dict = None):
    """
    Accept a JSON payload with 'records' array and return a CSV file response.
    Frontend can POST current filtered records and get a downloadable CSV.
    """
    if not payload or "records" not in payload:
        return JSONResponse({"error": "Invalid payload"}, status_code=400)
    records = payload["records"]
    # build CSV in memory
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date","open","high","low","close","volume"])
    for r in records:
        writer.writerow([r.get("date"), r.get("open"), r.get("high"), r.get("low"), r.get("close"), r.get("volume")])
    buf.seek(0)
    return FileResponse(io.BytesIO(buf.getvalue().encode("utf-8")), media_type="text/csv", filename="export.csv")


@app.get("/api/compare")
def compare_endpoint(
    t1: str = Query(..., description="Ticker 1"),
    t2: str = Query(..., description="Ticker 2"),
    source: str = Query("live", description="live or sample"),
    period: str = Query("6mo"),
    interval: str = Query("1d"),
    mode: str = Query("overlay", description="overlay or stacked")
):
    """
    Compare two tickers. source: live|sample.
    mode: overlay (close-price lines) | stacked (two candlesticks stacked).
    Returns records & analytics for both tickers.
    """
    def load_for(ticker, src):
        if src == "live":
            recs = fetch_yf_ohlc(ticker, period=period, interval=interval)
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

    if (not left["records"]) and (not right["records"]):
        return JSONResponse({"error": "No data for both tickers"}, status_code=404)

    return {"t1": t1.strip().upper(), "t2": t2.strip().upper(), "mode": mode, "left": left, "right": right}


@app.get("/api/av/{ticker}")
def alpha_vantage(ticker: str, function: str = Query("TIME_SERIES_DAILY")):
    """
    Basic Alpha Vantage fetcher. Works only if ALPHA_VANTAGE_KEY is set in env.
    """
    if not ALPHA_KEY:
        return JSONResponse({"error": "Alpha Vantage key not configured on server"}, status_code=501)
    base = "https://www.alphavantage.co/query"
    params = {"function": function, "symbol": ticker, "apikey": ALPHA_KEY, "outputsize": "compact"}
    resp = requests.get(base, params=params, timeout=15)
    if resp.status_code != 200:
        return JSONResponse({"error": "Alpha Vantage request failed"}, status_code=502)
    return JSONResponse(resp.json())
