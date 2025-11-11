from typing import List
from .models import Record

# Binary search helpers on array sorted by (company, date)

def _lower_bound_company(a: List[Record], company: str) -> int:
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid].company < company:
            lo = mid + 1
        else:
            hi = mid
    return lo

def _upper_bound_company(a: List[Record], company: str) -> int:
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid].company <= company:
            lo = mid + 1
        else:
            hi = mid
    return lo

def find_company_block(a_company_sorted: List[Record], company: str) -> List[Record]:
    """
    Precondition: a_company_sorted is sorted by (company, date)
    Returns all records for 'company' as a contiguous slice.
    Time: O(log n + k) where k = results count
    """
    if not a_company_sorted:
        return []
    company = company.strip().upper()
    start = _lower_bound_company(a_company_sorted, company)
    end = _upper_bound_company(a_company_sorted, company)
    return a_company_sorted[start:end]
