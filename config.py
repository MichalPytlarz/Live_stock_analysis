import pandas as pd
import yfinance as yf
from pathlib import Path
from functools import lru_cache

# Mapowanie sektorów (Yahoo Finance Sector -> Polska nazwa)
SECTOR_MAPPING = {
    'Energia': 'Energia',
    'Przemysł': 'Przemysł',
    'Finanse': 'Finanse',
    'Technologie': 'Technologie',
    'Farmacja': 'Farmacja',
    'FMCG': 'FMCG',
    'Nieruchomości': 'Nieruchomości',
    'Surowce': 'Surowce',
    'Telekomunikacja': 'Telekomunikacja',
    'Inne': 'Inne'
}


@lru_cache(maxsize=1)
def load_companies_from_csv() -> dict:
    """Ładuje spółki z CSV"""
    csv_path = Path(__file__).parent / 'companies.csv'
    
    if not csv_path.exists():
        print(f"⚠️ Plik {csv_path} nie istnieje. Zwracam pusty słownik.")
        return {}
    
    df = pd.read_csv(csv_path)
    companies = {}
    
    for _, row in df.iterrows():
        ticker = row['ticker']
        # Sektor z CSV - sprawdzamy czy kolumna istnieje
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
    Pobiera sektor z Yahoo Finance
    
    Args:
        ticker: Symbol giełdowy
    
    Returns:
        Nazwa sektora w języku polskim
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
    Ładuje spółki z CSV i wzbogaca o sektory
    Jeśli sektor nie jest zdefiniowany w CSV, pobiera z Yahoo Finance
    
    Returns:
        Słownik z informacjami o spółkach
    """
    companies = load_companies_from_csv()
    
    print("📊 Weryfikacja sektorów...")
    for ticker, company_info in companies.items():
        # Jeśli sektor jest zdefiniowany w CSV, używamy go
        if company_info.get('sector'):
            print(f"  {ticker}: {company_info['sector']} (z CSV)")
        else:
            # Fallback: pobieramy z Yahoo Finance
            sector = get_sector_from_yahoo(ticker)
            company_info['sector'] = sector
            print(f"  {ticker}: {sector} (z Yahoo Finance)")
    
    return companies


# Główny COMPANIES słownik
COMPANIES = load_companies_with_sectors()


def get_company_info(ticker: str) -> dict:
    """
    Pobiera informacje o spółce
    
    Args:
        ticker: Symbol giełdowy
    
    Returns:
        Słownik z informacjami
    """
    return COMPANIES.get(ticker)


def get_all_companies() -> list:
    """Zwraca listę dostępnych spółek (tickerów)"""
    return list(COMPANIES.keys())


def get_all_sectors() -> list:
    """Zwraca unikalne sektory"""
    sectors = set()
    for company in COMPANIES.values():
        if company:
            sectors.add(company.get('sector', 'Inne'))
    return sorted(list(sectors))


def get_companies_by_sector(sector: str) -> list:
    """
    Zwraca spółki z danego sektora
    
    Args:
        sector: Nazwa sektora
    
    Returns:
        Lista tickerów spółek
    """
    return [
        ticker for ticker, company in COMPANIES.items()
        if company and company.get('sector', 'Inne') == sector
    ]
