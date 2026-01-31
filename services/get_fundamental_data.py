import yfinance as yf
from config import SECTOR_MAPPING
def format_market_cap(market_cap):
    """
    Formats market capitalization in appropriate units
    
    Args:
        market_cap: Capitalization in base units
    
    Returns:
        Formatted string with appropriate unit
    """
    if market_cap == 0 or market_cap is None:
        return "N/A"
    
    # Convert to billions if >= 1 billion
    if market_cap >= 1_000_000_000:
        value = market_cap / 1_000_000_000
        return f"{value:.2f} MLD"
    # Convert to millions if >= 1 million
    elif market_cap >= 1_000_000:
        value = market_cap / 1_000_000
        return f"{value:.2f} MLN"
    # For values smaller than a million
    else:
        return f"{market_cap:,.0f}"

def get_fundamental_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Fetch sector from Yahoo Finance
    sector_en = info.get("sector", "Unknown")
    # Map to Polish name
    sector_pl = SECTOR_MAPPING.get(sector_en, "Inne")
    
    # Select only what we need
    raw_div_yield = info.get("dividendYield")
    if raw_div_yield is None:
        div_yield = 0
    else:
        div_yield = raw_div_yield if raw_div_yield > 1 else raw_div_yield * 100

    fundamentals = {
        "name": info.get("longName", ticker),
        "sector": sector_pl,
        "pe_ratio": info.get("trailingPE", "N/A"),
        "forward_pe": info.get("forwardPE", "N/A"),
        "pb_ratio": info.get("priceToBook", "N/A"),
        "div_yield": div_yield,
        "margin": info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0,
        "market_cap": info.get("marketCap", 0),
        "market_cap_formatted": format_market_cap(info.get("marketCap", 0))
    }
    return fundamentals