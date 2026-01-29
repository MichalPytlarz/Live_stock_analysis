from datetime import datetime, timedelta


def get_market_status():
    """
    Sprawdza status giełdy i zwraca informację o otwarciu
    
    Returns:
        tuple: (is_open: bool, message: str)
    """
    now = datetime.now()
    weekday = now.weekday()  # 0=Poniedziałek, 6=Niedziela
    hour = now.hour
    minute = now.minute
    
    # Weekend (sobota=5, niedziela=6)
    if weekday >= 5:
        # Ile dni do poniedziałku
        days_to_monday = 7 - weekday
        monday = now + timedelta(days=days_to_monday)
        monday_9am = monday.replace(hour=9, minute=0, second=0)
        time_diff = monday_9am - now
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        return False, f"Do otwarcia: {hours}h {minutes}min (Poniedziałek 9:00)"
    
    # Dzień roboczy
    if hour < 9:
        # Przed otwarciem
        opening = now.replace(hour=9, minute=0, second=0)
        time_diff = opening - now
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        return False, f"Do otwarcia: {hours}h {minutes}min"
    elif 9 <= hour < 17:
        # Giełda otwarta
        return True, "🟢 Giełda otwarta"
    else:
        # Po zamknięciu - pokaż czas do jutrzejszego otwarcia
        if weekday == 4:  # Piątek
            monday = now + timedelta(days=3)
            monday_9am = monday.replace(hour=9, minute=0, second=0)
            time_diff = monday_9am - now
            hours = int(time_diff.total_seconds() // 3600)
            return False, f"Do otwarcia: {hours}h (Poniedziałek 9:00)"
        else:
            tomorrow_9am = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
            time_diff = tomorrow_9am - now
            hours = int(time_diff.total_seconds() // 3600)
            return False, f"Do otwarcia giełdy: {hours}h"
