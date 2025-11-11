from typing import List
from core.models import Record

def average_volume(records: List[Record]) -> float:
    if not records:
        return 0.0
    total = sum(r.volume for r in records)
    return total / len(records)

def price_summary(records: List[Record]) -> dict:
    if not records:
        return {}

    highs = max(r.high for r in records)
    lows  = min(r.low for r in records)
    opens = records[0].open   # after sorting by date
    closes = records[-1].close

    return {
        "highest": highs,
        "lowest": lows,
        "first_open": opens,
        "last_close": closes
    }

def export_to_csv(records: List[Record], filepath: str):
    import csv, os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date","company","open","high","low","close","volume"])
        for r in records:
            writer.writerow([r.date, r.company, r.open, r.high, r.low, r.close, r.volume])

    print(f"✔ Exported to {filepath}")
