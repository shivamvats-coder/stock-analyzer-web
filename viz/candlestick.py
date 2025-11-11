import os
from typing import List, Optional
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from core.models import Record

def plot_candles(records: List[Record], title: str = "", save_path: Optional[str] = None, show: bool = True):
    """
    Simple candlestick: wick = (low, high), body = (open, close).
    Time: O(k)
    """
    if not records:
        print("[plot_candles] No records to plot.")
        return None

    records = sorted(records, key=lambda r: r.date)
    xs = [mdates.date2num(r.date) for r in records]

    fig, ax = plt.subplots(figsize=(10, 4))

    for x, r in zip(xs, records):
        up = r.close >= r.open
        color = "tab:green" if up else "tab:red"

        # wick
        ax.plot([x, x], [r.low, r.high], linewidth=1)

        # body
        width = 0.6  # day width
        lower = min(r.open, r.close)
        height = abs(r.close - r.open)
        if height == 0:
            height = 0.2  # tiny body so flat days are visible
        rect = Rectangle((x - width / 2, lower), width, height, color=color, alpha=0.85, linewidth=0)
        ax.add_patch(rect)

    ax.set_title(title or "Candlestick")
    ax.set_xlabel("Date"); ax.set_ylabel("Price")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.tight_layout()
        fig.savefig(save_path, dpi=150)
        print(f"[plot_candles] Saved: {save_path}")

    if show:
        plt.show()

    return fig
