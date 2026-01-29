import yfinance as yf
from config import SECTOR_MAPPING
def format_market_cap(market_cap):
    """
    Formatuje kapitalizację rynkową w odpowiednich jednostkach
    
    Args:
        market_cap: Kapitalizacja w wartości bazowej
    
    Returns:
        Sformatowany string z odpowiednią jednostką
    """
    if market_cap == 0 or market_cap is None:
        return "N/A"
    
    # Konwertuj na miliardy jeśli >= 1 miliard
    if market_cap >= 1_000_000_000:
        value = market_cap / 1_000_000_000
        return f"{value:.2f} MLD"
    # Konwertuj na miliony jeśli >= 1 milion
    elif market_cap >= 1_000_000:
        value = market_cap / 1_000_000
        return f"{value:.2f} MLN"
    # Dla wartości mniejszych niż milion
    else:
        return f"{market_cap:,.0f}"

def get_fundamental_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Pobierz sektor z Yahoo Finance
    sector_en = info.get("sector", "Unknown")
    # Mapuj na polską nazwę
    sector_pl = SECTOR_MAPPING.get(sector_en, "Inne")
    
    # Wybieramy tylko to, co nas interesuje
    fundamentals = {
        "name": info.get("longName", ticker),
        "sector": sector_pl,
        "pe_ratio": info.get("trailingPE", "N/A"),
        "forward_pe": info.get("forwardPE", "N/A"),
        "pb_ratio": info.get("priceToBook", "N/A"),
        "div_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
        "margin": info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0,
        "market_cap": info.get("marketCap", 0),
        "market_cap_formatted": format_market_cap(info.get("marketCap", 0))
    }
    return fundamentals