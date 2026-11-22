"""
Calendar Dimension (dim_date) Generator
Generates full calendar dimension records with rich temporal attributes.
"""
from datetime import date, timedelta
from typing import List, Dict, Any
import pandas as pd

def generate_date_dimension(start_year: int = 2023, end_year: int = 2026) -> pd.DataFrame:
    """Generate calendar dimension records between start_year and end_year inclusive."""
    start_dt = date(start_year, 1, 1)
    end_dt = date(end_year, 12, 31)
    
    records = []
    curr = start_dt
    
    # Common US Federal Holidays (simplified date matches)
    def check_holiday(d: date) -> bool:
        if d.month == 1 and d.day == 1: return True # New Year
        if d.month == 7 and d.day == 4: return True # July 4
        if d.month == 11 and d.day >= 22 and d.day <= 28 and d.weekday() == 3: return True # Thanksgiving
        if d.month == 12 and d.day == 25: return True # Christmas
        return False

    while curr <= end_dt:
        date_key = int(curr.strftime("%Y%m%d"))
        day_of_week = curr.isoweekday() # 1=Mon, 7=Sun
        is_weekend = day_of_week in [6, 7]
        cal_quarter = (curr.month - 1) // 3 + 1
        
        records.append({
            "date_key": date_key,
            "full_date": curr.isoformat(),
            "day_of_week": day_of_week,
            "day_name": curr.strftime("%A"),
            "day_of_month": curr.day,
            "day_of_year": int(curr.strftime("%j")),
            "week_of_year": int(curr.strftime("%V")),
            "month_number": curr.month,
            "month_name": curr.strftime("%B"),
            "calendar_quarter": cal_quarter,
            "calendar_year": curr.year,
            "is_weekend": is_weekend,
            "is_holiday": check_holiday(curr)
        })
        curr += timedelta(days=1)
        
    return pd.DataFrame(records)
