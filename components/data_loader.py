import pandas as pd
import yfinance as yf
from stockstats import StockDataFrame
import streamlit as st
from database.database_manager import get_sentiment_trend


def get_sentiment_for_model(ticker: str) -> pd.DataFrame:
    """
    Fetches sentiment data from the database for the ML model
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        DataFrame with columns [timestamp, sentiment_score, news_volume]
    """
    try:
        # Fetch last 100 sentiment entries
        sentiment_df = get_sentiment_trend(ticker, limit=100)
        
        if sentiment_df.empty:
            return pd.DataFrame(columns=['timestamp', 'sentiment_score', 'news_volume'])
        
        # Prepare DataFrame
        sentiment_df['timestamp'] = pd.to_datetime(sentiment_df['timestamp'])
        sentiment_df = sentiment_df.rename(columns={'avg_score': 'sentiment_score'})
        
        # news_volume - if missing in DB, set to 1
        if 'news_count' in sentiment_df.columns:
            sentiment_df = sentiment_df.rename(columns={'news_count': 'news_volume'})
        else:
            sentiment_df['news_volume'] = 1
        
        return sentiment_df[['timestamp', 'sentiment_score', 'news_volume']].set_index('timestamp')
    except Exception as e:
        print(f"⚠️ Błąd pobierania sentymentu dla {ticker}: {str(e)}")
        return pd.DataFrame(columns=['timestamp', 'sentiment_score', 'news_volume'])


def get_fundamental_features(ticker: str) -> dict:
    """Fetches fundamental metrics for a company"""
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
    Fetches data for the main security and auxiliary data (oil, USD/PLN)
    
    Args:
        ticker: Stock ticker symbol (e.g., "PKN.WA")
        period: Download period (e.g., "3d", "1d")
        interval: Time interval (e.g., "15m", "1h", "1d")
        include_oil: Whether to fetch Brent oil data
    
    Returns:
        DataFrame with synchronized data
    """
    try:
        # Fetch stock data
        stock = yf.download(ticker, period=period, interval=interval)
        
        # Optionally fetch oil and USD/PLN
        if include_oil:
            oil = yf.download("BZ=F", period=period, interval=interval)['Close']
        usdpln = yf.download("PLN=X", period=period, interval=interval)['Close']
        
        # Fix MultiIndex (for yfinance)
        if isinstance(stock.columns, pd.MultiIndex):
            stock.columns = stock.columns.get_level_values(0)
        
        df = stock.copy()
        df.columns = df.columns.str.lower()
        
        # Synchronize data
        if include_oil:
            df['oil_price'] = oil
        df['usdpln'] = usdpln
        df = df.ffill().sort_index()
        
        return df
    except Exception as e:
        raise Exception(f"Błąd przy pobieraniu danych: {str(e)}")


def engineer_features(df: pd.DataFrame, ticker: str, include_oil: bool = True) -> pd.DataFrame:
    """
    Adds engineered features for the ML model (RSI, EMA, percent change)
    
    Args:
        df: DataFrame with market data
        ticker: Stock ticker symbol (for fundamentals)
        include_oil: Whether to use oil price as a feature
    
    Returns:
        DataFrame with additional columns
    """
    df = df.copy()
    
    # Feature engineering
    stock = StockDataFrame.retype(df.copy())
    df['rsi'] = stock['rsi_14']
    df['ema_20'] = stock['close_20_ema']
    
    if include_oil and 'oil_price' in df.columns:
        df['oil_chg'] = df['oil_price'].pct_change(fill_method=None)
    else:
        df['oil_chg'] = 0  # Default value if oil data is missing
    
    df['usd_chg'] = df['usdpln'].pct_change(fill_method=None)
    
    # Target - increase over the next 3 hours
    df['target'] = (df['close'].shift(-3) > df['close']).astype(int)
    
    # NEW: Add sentiment from the database
    sentiment_df = get_sentiment_for_model(ticker)
    
    if not sentiment_df.empty:
        # Sync timezone - remove timezone from df index if present
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Synchronize sentiment with prices (merge_asof matches the nearest earlier timestamp)
        df = pd.merge_asof(
            df.sort_index(), 
            sentiment_df.sort_index(), 
            left_index=True, 
            right_index=True, 
            direction='backward'
        )
        # Forward fill - propagate the last known sentiment value
        df['sentiment_score'] = df['sentiment_score'].ffill()
        df['news_volume'] = df['news_volume'].ffill()
        # Fill remaining NaNs with zeros (if no earlier data)
        df['sentiment_score'] = df['sentiment_score'].fillna(0)
        df['news_volume'] = df['news_volume'].fillna(0)
    else:
        # If sentiment data is missing, set to 0
        df['sentiment_score'] = 0
        df['news_volume'] = 0
    
    # NEW: Add fundamentals
    fundamentals = get_fundamental_features(ticker)
    df['pe_ratio'] = fundamentals['pe_ratio']
    df['pb_ratio'] = fundamentals['pb_ratio']
    df['profit_margin'] = fundamentals['profit_margin']
    
    return df.dropna()


@st.cache_data(ttl=60)
def load_data_cached(ticker: str, period: str = "3d", interval: str = "15m", include_oil: bool = True) -> pd.DataFrame:
    """
    Fetches and engineers features with caching (TTL 60 seconds)
    
    Args:
        ticker: Stock ticker symbol
        period: Download period
        interval: Time interval
        include_oil: Whether to fetch oil data
    
    Returns:
        Prepared DataFrame ready for prediction
    """
    raw_data = fetch_market_data(ticker, period, interval, include_oil=include_oil)
    return engineer_features(raw_data, ticker, include_oil=include_oil)
