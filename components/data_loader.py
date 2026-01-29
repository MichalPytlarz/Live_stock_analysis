import pandas as pd
import yfinance as yf
from stockstats import StockDataFrame
import streamlit as st
from database.database_manager import get_sentiment_trend


def get_sentiment_for_model(ticker: str) -> pd.DataFrame:
    """
    Pobiera dane sentymentu z bazy dla modelu ML
    
    Args:
        ticker: Symbol giełdowy
    
    Returns:
        DataFrame z kolumnami [timestamp, sentiment_score, news_volume]
    """
    try:
        # Pobierz ostatnie 100 wpisów sentymentu
        sentiment_df = get_sentiment_trend(ticker, limit=100)
        
        if sentiment_df.empty:
            return pd.DataFrame(columns=['timestamp', 'sentiment_score', 'news_volume'])
        
        # Przygotuj DataFrame
        sentiment_df['timestamp'] = pd.to_datetime(sentiment_df['timestamp'])
        sentiment_df = sentiment_df.rename(columns={'avg_score': 'sentiment_score'})
        
        # news_volume - jeśli nie ma w bazie, ustaw na 1
        if 'news_count' in sentiment_df.columns:
            sentiment_df = sentiment_df.rename(columns={'news_count': 'news_volume'})
        else:
            sentiment_df['news_volume'] = 1
        
        return sentiment_df[['timestamp', 'sentiment_score', 'news_volume']].set_index('timestamp')
    except Exception as e:
        print(f"⚠️ Błąd pobierania sentymentu dla {ticker}: {str(e)}")
        return pd.DataFrame(columns=['timestamp', 'sentiment_score', 'news_volume'])


def get_fundamental_features(ticker: str) -> dict:
    """Pobiera wskaźniki fundamentalne dla spółki"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'pe_ratio': info.get('trailingPE', 0) or 0,
            'pb_ratio': info.get('priceToBook', 0) or 0,
            'profit_margin': info.get('profitMargins', 0) or 0
        }
    except:
        return {'pe_ratio': 0, 'pb_ratio': 0, 'profit_margin': 0}


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


def engineer_features(df: pd.DataFrame, ticker: str, include_oil: bool = True) -> pd.DataFrame:
    """
    Dodaje engineerskie cechy dla modelu ML (RSI, EMA, zmiana procentowa)
    
    Args:
        df: DataFrame z danymi rynkowymi
        ticker: Symbol giełdowy (do pobrania fundamentów)
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
    
    # NOWOŚĆ: Dodanie sentymentu z bazy danych
    sentiment_df = get_sentiment_for_model(ticker)
    
    if not sentiment_df.empty:
        # Synchronizuj timezone - usuń timezone z indexu df jeśli istnieje
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Synchronizacja danych sentymentu z cenami (merge_asof dopasowuje najbliższy wcześniejszy timestamp)
        df = pd.merge_asof(
            df.sort_index(), 
            sentiment_df.sort_index(), 
            left_index=True, 
            right_index=True, 
            direction='backward'
        )
        # Forward fill - propaguj ostatnią znaną wartość sentymentu
        df['sentiment_score'] = df['sentiment_score'].ffill()
        df['news_volume'] = df['news_volume'].ffill()
        # Wypełnij pozostałe NaN zerami (jeśli nie ma wcześniejszych danych)
        df['sentiment_score'] = df['sentiment_score'].fillna(0)
        df['news_volume'] = df['news_volume'].fillna(0)
    else:
        # Jeśli brak danych sentymentu, ustaw na 0
        df['sentiment_score'] = 0
        df['news_volume'] = 0
    
    # NOWOŚĆ: Dodanie fundamentów
    fundamentals = get_fundamental_features(ticker)
    df['pe_ratio'] = fundamentals['pe_ratio']
    df['pb_ratio'] = fundamentals['pb_ratio']
    df['profit_margin'] = fundamentals['profit_margin']
    
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
    return engineer_features(raw_data, ticker, include_oil=include_oil)
