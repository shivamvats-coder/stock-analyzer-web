from typing import List
from .models import Record

# Merge Sort (stable), key = (date, company)  -> date pe sort, tie ho to company
def merge_sort_by_date(arr: List[Record]) -> List[Record]:
    # Time: O(n log n), Space: O(n)
    if len(arr) <= 1:
        return arr[:]
    mid = len(arr) // 2
    left = merge_sort_by_date(arr[:mid])
    right = merge_sort_by_date(arr[mid:])
    return _merge_by_date(left, right)

def _merge_by_date(left: List[Record], right: List[Record]) -> List[Record]:
    i = j = 0
    out: List[Record] = []
    while i < len(left) and j < len(right):
        # Compare by (date, company) — stable tie-breaker
        if (left[i].date, left[i].company) <= (right[j].date, right[j].company):
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    # append leftovers
    if i < len(left): out.extend(left[i:])
    if j < len(right): out.extend(right[j:])
    return out

from typing import List
from .models import Record

# ---- already defined above: merge_sort_by_date ----

# Merge Sort (stable), key = (company, date)
# Time: O(n log n), Space: O(n)
def merge_sort_by_company(arr: List[Record]) -> List[Record]:
    if len(arr) <= 1:
        return arr[:]
    mid = len(arr) // 2
    left = merge_sort_by_company(arr[:mid])
    right = merge_sort_by_company(arr[mid:])
    return _merge_by_company(left, right)

def _merge_by_company(left: List[Record], right: List[Record]) -> List[Record]:
    i = j = 0
    out: List[Record] = []
    while i < len(left) and j < len(right):
        if (left[i].company, left[i].date) <= (right[j].company, right[j].date):
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    if i < len(left): out.extend(left[i:])
    if j < len(right): out.extend(right[j:])
    return out
