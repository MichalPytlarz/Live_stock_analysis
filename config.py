import pandas as pd
import yfinance as yf
from pathlib import Path
from functools import lru_cache

# Sector mapping (Yahoo Finance Sector -> Polish name)
SECTOR_MAPPING = {
    'Energy': 'Energia',
    'Industrials': 'Przemysł',
    'Financial Services': 'Finanse',
    'Financials': 'Finanse',
    'Technology': 'Technologie',
    'Healthcare': 'Farmacja',
    'Consumer Defensive': 'FMCG',
    'Consumer Cyclical': 'FMCG',
    'Consumer Staples': 'FMCG',
    'Real Estate': 'Nieruchomości',
    'Basic Materials': 'Surowce',
    'Communication Services': 'Telekomunikacja',
    'Utilities': 'Energia',
    'Unknown': 'Inne'
}

METRIC_HELP = {
    "P/E": "**Cena do Zysku (Price/Earnings):** Mówi, ile złotych inwestor płaci za 1 zł zysku netto spółki. Niski wskaźnik może oznaczać okazję, wysoki – że spółka jest droga. [Więcej na GPWTrader](https://gpwtrader.pl/edukacja/wskazniki)",
    "P/B": "**Cena do Wartości Księgowej (Price/Book):** Informuje, jak rynek wycenia majątek netto spółki. Wartość poniżej 1.0 może sugerować niedowartościowanie. [Dowiedz się więcej](https://www.biznesradar.pl/wskazniki-wartosci-rynkowej/C-WK)",
    "DivYield": "**Stopa Dywidendy:** Procentowa wartość dywidendy w stosunku do aktualnej ceny akcji. Im wyższa, tym więcej gotówki trafia do Twojej kieszeni. [Ranking dywidend](https://www.stockwatch.pl/dywidendy/)",
    "Margin": "**Marża Zysku Netto:** Pokazuje, jaki procent przychodów staje się czystym zyskiem. Wysoka marża oznacza dużą efektywność biznesu."
}


METRICS_CONFIG = [
    {"label": "P/E Ratio", "key": "pe_ratio", "help_key": "P/E", "format": "{:.2f}"},
    {"label": "P/B Ratio", "key": "pb_ratio", "help_key": "P/B", "format": "{:.2f}"},
    {"label": "Dywidenda", "key": "div_yield", "help_key": "DivYield", "format": "{:.2f}%"},
    {"label": "Marża Zysku", "key": "margin", "help_key": "Margin", "format": "{:.2f}%"}
]


@lru_cache(maxsize=1)
def load_companies_from_csv() -> dict:
    """Loads companies from CSV"""
    csv_path = Path(__file__).parent / 'data' / 'companies.csv'
    
    if not csv_path.exists():
        print(f"⚠️ Plik {csv_path} nie istnieje. Zwracam pusty słownik.")
        return {}
    
    df = pd.read_csv(csv_path)
    companies = {}
    
    for _, row in df.iterrows():
        ticker = row['ticker']
        # Sector from CSV - check if column exists
        sector = row['sector'] if 'sector' in row and pd.notna(row['sector']) else None
        
        companies[ticker] = {
            'ticker': ticker,
            'name': row['name'],
            'emoji': row['emoji'],
            'include_oil': str(row['include_oil']).strip().lower() in ('true', '1', 'yes'),
            'sector': sector,
            'model_path': f"models/{ticker}/{ticker.replace('.', '_').lower()}_ai_model.pkl"
        }
    
    return companies


def get_sector_from_yahoo(ticker: str) -> str:
    """
    Fetches sector from Yahoo Finance
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Sector name in Polish
    """
    try:
        data = yf.Ticker(ticker)
        sector = data.info.get('sector', 'Unknown')
        return SECTOR_MAPPING.get(sector, 'Inne')
    except Exception as e:
        print(f"⚠️ Błąd pobierania sektora dla {ticker}: {str(e)}")
        return 'Inne'


@lru_cache(maxsize=1)
def load_companies_with_sectors() -> dict:
    """
    Loads companies from CSV and enriches with sectors
    If sector is not defined in CSV, fetches from Yahoo Finance
    
    Returns:
        Dictionary with company information
    """
    companies = load_companies_from_csv()
    
    print("📊 Weryfikacja sektorów...")
    for ticker, company_info in companies.items():
        # If sector is defined in CSV, use it
        if company_info.get('sector'):
            print(f"  {ticker}: {company_info['sector']} (z CSV)")
        else:
            # Fallback: fetch from Yahoo Finance
            sector = get_sector_from_yahoo(ticker)
            company_info['sector'] = sector
            print(f"  {ticker}: {sector} (z Yahoo Finance)")
    
    return companies


# Main COMPANIES dictionary
COMPANIES = load_companies_with_sectors()


def get_company_info(ticker: str) -> dict:
    """
    Fetches company information
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Information dictionary
    """
    return COMPANIES.get(ticker)


def get_all_companies() -> list:
    """Returns a list of available companies (tickers)"""
    return list(COMPANIES.keys())


def get_all_sectors() -> list:
    """Returns unique sectors"""
    sectors = set()
    for company in COMPANIES.values():
        if company:
            sectors.add(company.get('sector', 'Inne'))
    return sorted(list(sectors))


def get_companies_by_sector(sector: str) -> list:
    """
    Returns companies from a given sector
    
    Args:
        sector: Sector name
    
    Returns:
        List of company tickers
    """
    return [
        ticker for ticker, company in COMPANIES.items()
        if company and company.get('sector', 'Inne') == sector
    ]
