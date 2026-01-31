import pandas as pd

def map_to_trading_hours(dt):
    # If weekend (Saturday=5, Sunday=6) -> shift to Monday 09:00
    if dt.weekday() >= 5:
        days_to_add = 7 - dt.weekday()
        return (dt + pd.Timedelta(days=days_to_add)).replace(hour=9, minute=0, second=0)
    
    # If after session (after 17:00) -> shift to tomorrow 09:00
    if dt.hour >= 17:
        return (dt + pd.Timedelta(days=1)).replace(hour=9, minute=0, second=0)
    
    # If before session (before 09:00) -> shift to today 09:00
    if dt.hour < 9:
        return dt.replace(hour=9, minute=0, second=0)
    
    return dt
