from dataclasses import dataclass
from datetime import datetime, date

@dataclass(frozen=True)
class Record:
    date: date
    company: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    @staticmethod
    def from_row(row: dict) -> "Record":
        # Expecting keys: date, company, open, high, low, close, volume
        d = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()
        company = row["company"].strip().upper()

        open_p  = float(row["open"])
        high_p  = float(row["high"])
        low_p   = float(row["low"])
        close_p = float(row["close"])
        vol     = int(row["volume"])

        # Basic validations
        if any(v < 0 for v in (open_p, high_p, low_p, close_p)) or vol < 0:
            raise ValueError("Negative price/volume not allowed.")
        if low_p > high_p or not (low_p <= open_p <= high_p) or not (low_p <= close_p <= high_p):
            raise ValueError("OHLC consistency failed.")

        return Record(
            date=d, company=company,
            open=open_p, high=high_p, low=low_p, close=close_p, volume=vol
        )
