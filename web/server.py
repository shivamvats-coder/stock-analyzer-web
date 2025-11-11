from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.loader import load_csv
from core.sort_algos import merge_sort_by_company
from core.search import find_company_block
from core.analytics import average_volume, price_summary

app = FastAPI()

# Allow frontend (mobile/laptop) to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS & JS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")


@app.get("/")
def home():
    return FileResponse("web/templates/index.html")


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

    # Convert objects to dict for JSON
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
        "company": ticker.upper(),
        "records": records,
        "analytics": analytics
    }
