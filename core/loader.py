import csv
from typing import List
from .models import Record

def load_csv(path: str) -> List[Record]:
    records: List[Record] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"date","company","open","high","low","close","volume"}
        # Normalize fieldnames to lowercase
        fieldnames = [h.lower().strip() for h in (reader.fieldnames or [])]
        if set(fieldnames) != required:
            raise ValueError(f"CSV header must be exactly: {sorted(required)}")
        for i, row in enumerate(reader, start=2):  # header is line 1
            row = {k.lower().strip(): (v or "").strip() for k, v in row.items()}
            try:
                rec = Record.from_row(row)
                records.append(rec)
            except Exception as e:
                print(f"[load_csv] Skipping line {i}: {e}")
    return records
