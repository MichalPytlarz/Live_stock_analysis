import pandas as pd

def map_to_trading_hours(dt):
    # Jeśli weekend (sobota=5, niedziela=6) -> przesuń na poniedziałek 09:00
    if dt.weekday() >= 5:
        days_to_add = 7 - dt.weekday()
        return (dt + pd.Timedelta(days=days_to_add)).replace(hour=9, minute=0, second=0)
    
    # Jeśli po sesji (po 17:00) -> przesuń na jutro 09:00
    if dt.hour >= 17:
        return (dt + pd.Timedelta(days=1)).replace(hour=9, minute=0, second=0)
    
    # Jeśli przed sesją (przed 09:00) -> przesuń na dziś 09:00
    if dt.hour < 9:
        return dt.replace(hour=9, minute=0, second=0)
    
    return dt
