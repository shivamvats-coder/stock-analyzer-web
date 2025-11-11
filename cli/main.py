from datetime import datetime
import os
from core.loader import load_csv
from core.sort_algos import merge_sort_by_date, merge_sort_by_company
from core.search import find_company_block
from viz.candlestick import plot_candles
from core.analytics import average_volume, price_summary, export_to_csv

# GLOBAL DATA
DATA = []
DATA_BY_DATE = []
DATA_BY_COMPANY = []

def pretty_print(records, n=5):
    for r in records[:n]:
        print(f"{r.date} | {r.company:10} | O:{r.open} H:{r.high} L:{r.low} C:{r.close} V:{r.volume}")

def load_data():
    global DATA, DATA_BY_DATE, DATA_BY_COMPANY
    DATA = load_csv("sample_data.csv")
    DATA_BY_DATE = merge_sort_by_date(DATA)
    DATA_BY_COMPANY = merge_sort_by_company(DATA)
    print(f"\n✔ Loaded {len(DATA)} records successfully.\n")

def search_company():
    if not DATA_BY_COMPANY:
        print("❌ Load data first!")
        return

    q = input("Enter company ticker: ").strip()
    block = find_company_block(DATA_BY_COMPANY, q)

    if not block:
        print("❌ No records found.\n")
        return

    print(f"\n✔ Found {len(block)} records for {block[0].company}.")
    print(f"   Date Range: {block[0].date} → {block[-1].date}\n")
    pretty_print(block, n=5)

    print("\n--- ANALYTICS ---")
    avg_vol = average_volume(block)
    print(f"Average Volume       : {avg_vol:.2f}")

    summary = price_summary(block)
    print(f"Highest Price        : {summary['highest']}")
    print(f"Lowest Price         : {summary['lowest']}")
    print(f"First Open Price     : {summary['first_open']}")
    print(f"Last Closing Price   : {summary['last_close']}")

    do_export = input("\nExport these records to CSV? (Y/N): ").strip().lower()
    if do_export == "y":
        export_to_csv(block, f"out/{block[0].company}_data.csv")

def plot_candlestick():
    if not DATA_BY_COMPANY:
        print("❌ Load data first!")
        return

    q = input("Enter company for plot: ").strip().upper()
    block = find_company_block(DATA_BY_COMPANY, q)

    if not block:
        print("❌ No records for this company.")
        return

    start = input("Start date (YYYY-MM-DD or blank): ").strip()
    end = input("End date (YYYY-MM-DD or blank): ").strip()

    try:
        filtr = block
        if start:
            s = datetime.strptime(start, "%Y-%m-%d").date()
            filtr = [r for r in filtr if r.date >= s]
        if end:
            e = datetime.strptime(end, "%Y-%m-%d").date()
            filtr = [r for r in filtr if r.date <= e]
    except:
        print("❌ Invalid date format.")
        return

    if not filtr:
        print("❌ No data in this date range.")
        return

    company = filtr[0].company
    os.makedirs("out", exist_ok=True)
    save_path = f"out/candlestick_{company}.png"

    title = f"{company} Candlestick ({filtr[0].date} → {filtr[-1].date})"
    plot_candles(filtr, title=title, save_path=save_path)
    print(f"\n✔ Plot saved to {save_path}\n")

def menu():
    while True:
        print("\n========== STOCK ANALYZER ==========")
        print("1. Load Stock Data")
        print("2. Search by Company")
        print("3. Generate Candlestick Plot")
        print("4. Exit")
        print("====================================")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            load_data()
        elif choice == "2":
            search_company()
        elif choice == "3":
            plot_candlestick()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("❌ Invalid choice. Try again.\n")

if __name__ == "__main__":
    menu()
