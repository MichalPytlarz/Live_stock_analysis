import pandas as pd
import yfinance as yf
from stockstats import StockDataFrame
import streamlit as st


def fetch_market_data(ticker: str, period: str = "3d", interval: str = "15m", include_oil: bool = True) -> pd.DataFrame:
    """
    Pobiera dane dla głównego papieru wartościowego oraz dane pomocnicze (ropa, USD/PLN)
    
    Args:
        ticker: Symbol giełdowy (np. "PKN.WA")
        period: Okres pobierania (np. "3d", "1d")
        interval: Interwał czasu (np. "15m", "1h", "1d")
        include_oil: Czy pobierać dane o ropie Brent
    
    Returns:
        DataFrame z synchronizowanymi danymi
    """
    try:
        # Pobieramy dane akcji
        stock = yf.download(ticker, period=period, interval=interval)
        
        # Pobieramy opcjonalnie ropę i USD/PLN
        if include_oil:
            oil = yf.download("BZ=F", period=period, interval=interval)['Close']
        usdpln = yf.download("PLN=X", period=period, interval=interval)['Close']
        
        # Naprawa MultiIndex (dla yfinance)
        if isinstance(stock.columns, pd.MultiIndex):
            stock.columns = stock.columns.get_level_values(0)
        
        df = stock.copy()
        df.columns = df.columns.str.lower()
        
        # Synchronizacja danych
        if include_oil:
            df['oil_price'] = oil
        df['usdpln'] = usdpln
        df = df.ffill().sort_index()
        
        return df
    except Exception as e:
        raise Exception(f"Błąd przy pobieraniu danych: {str(e)}")


def engineer_features(df: pd.DataFrame, include_oil: bool = True) -> pd.DataFrame:
    """
    Dodaje engineerskie cechy dla modelu ML (RSI, EMA, zmiana procentowa)
    
    Args:
        df: DataFrame z danymi rynkowymi
        include_oil: Czy używać ceny ropy jako cechy
    
    Returns:
        DataFrame z dodatkowymi kolumnami
    """
    df = df.copy()
    
    # Feature Engineering
    stock = StockDataFrame.retype(df.copy())
    df['rsi'] = stock['rsi_14']
    df['ema_20'] = stock['close_20_ema']
    
    if include_oil and 'oil_price' in df.columns:
        df['oil_chg'] = df['oil_price'].pct_change(fill_method=None)
    else:
        df['oil_chg'] = 0  # Domyślna wartość jeśli nie mamy danych o ropie
    
    df['usd_chg'] = df['usdpln'].pct_change(fill_method=None)
    
    # Target - wzrost za 3 godziny
    df['target'] = (df['close'].shift(-3) > df['close']).astype(int)
    
    return df.dropna()


@st.cache_data(ttl=60)
def load_data_cached(ticker: str, period: str = "3d", interval: str = "15m", include_oil: bool = True) -> pd.DataFrame:
    """
    Pobiera i inżynieruje cechy z cache'owaniem (TTL 60 sekund)
    
    Args:
        ticker: Symbol giełdowy
        period: Okres pobierania
        interval: Interwał czasu
        include_oil: Czy pobierać dane o ropie
    
    Returns:
        Przygotowany DataFrame gotowy do predykcji
    """
    raw_data = fetch_market_data(ticker, period, interval, include_oil=include_oil)
    return engineer_features(raw_data, include_oil=include_oil)
