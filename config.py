import pandas as pd
import yfinance as yf
from pathlib import Path
from functools import lru_cache

# Mapowanie sektorów (Yahoo Finance Sector -> Polska nazwa)
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
    """Ładuje spółki z CSV"""
    csv_path = Path(__file__).parent / 'data' / 'companies.csv'
    
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
