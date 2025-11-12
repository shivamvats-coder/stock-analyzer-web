from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.loader import load_csv
from core.sort_algos import merge_sort_by_company
from core.search import find_company_block
from core.analytics import average_volume, price_summary

from web.data_live import fetch_yf_ohlc, add_ma_ema

app = FastAPI()

# Allow all origins (simple demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS/JS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

@app.get("/")
def home():
    return FileResponse("web/templates/index.html")

# --- Sample CSV data endpoint (existing functionality) ---
@app.get("/api/company/{ticker}")
def get_company_data(ticker: str):
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

    return {
        "company": ticker.strip().upper(),
        "records": records,
        "analytics": analytics
    }

# --- NEW: Live data (Yahoo Finance) with MA/EMA ---
@app.get("/api/live/{ticker}")
def live_company_data(
    ticker: str,
    period: str = Query("6mo", description="1mo,3mo,6mo,1y,2y,5y,max"),
    interval: str = Query("1d", description="1d,1wk,1mo")
):
    records = fetch_yf_ohlc(ticker, period=period, interval=interval)
    if not records:
        return JSONResponse({"error": "No live data found"}, status_code=404)

    highs  = max(r["high"] for r in records)
    lows   = min(r["low"]  for r in records)
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
            "ema": me["ema"],
        }
    }
