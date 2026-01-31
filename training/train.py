import yfinance as yf
import pandas as pd
from stockstats import StockDataFrame
from xgboost import XGBClassifier
import joblib
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COMPANIES

def get_sentiment_data_from_db(ticker: str) -> pd.DataFrame:
    """
    Here you should connect a query to your SQLite database.
    Returns a DataFrame with columns [timestamp, sentiment_score, news_volume]
    """
    # Temporarily return an empty DF if you don't have a DB fetch module yet
    return pd.DataFrame(columns=['sentiment_score', 'news_volume'])

def get_fundamental_data(ticker: str):
    """Fetches current fundamental metrics"""
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

def prepare_data(ticker: str, period: str = "2y", interval: str = "1h", include_oil: bool = True) -> pd.DataFrame:
    print(f"📊 Pobieranie danych dla {ticker} ({period}, {interval})...")
    
    # 1. Fetch price data
    stock = yf.download(ticker, period=period, interval=interval)
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = stock.columns.get_level_values(0)
    
    df = stock.copy()
    df.columns = df.columns.str.lower()
    
    # 2. External data (Oil, USDPLN)
    if include_oil:
        oil = yf.download("BZ=F", period=period, interval=interval)['Close']
        if isinstance(oil, pd.DataFrame): oil = oil.iloc[:, 0]
        df['oil_price'] = oil
        
    usdpln = yf.download("PLN=X", period=period, interval=interval)['Close']
    if isinstance(usdpln, pd.DataFrame): usdpln = usdpln.iloc[:, 0]
    df['usdpln'] = usdpln
    
    df = df.ffill().sort_index()
    
    # 3. Technical indicators
    stock_indicators = StockDataFrame.retype(df.copy())
    df['rsi'] = stock_indicators['rsi_14']
    df['ema_20'] = stock_indicators['close_20_ema']
    df['oil_chg'] = df['oil_price'].pct_change(fill_method=None) if include_oil else 0
    df['usd_chg'] = df['usdpln'].pct_change(fill_method=None)
    
    # 4. NEW: Sentiment (merge_asof matches news to the nearest prior price hour)
    sentiment_df = get_sentiment_data_from_db(ticker)
    if not sentiment_df.empty:
        sentiment_df['timestamp'] = pd.to_datetime(sentiment_df['timestamp'])
        df = pd.merge_asof(df.sort_index(), sentiment_df.sort_index(), 
                           left_index=True, right_on='timestamp', direction='backward')
    else:
        df['sentiment_score'] = 0
        df['news_volume'] = 0
    
    # 5. NEW: Fundamentals (apply current values to the full history)
    fundamentals = get_fundamental_data(ticker)
    df['pe_ratio'] = fundamentals['pe_ratio']
    df['pb_ratio'] = fundamentals['pb_ratio']
    df['profit_margin'] = fundamentals['profit_margin']
    
    # 6. Target: Will price be higher in 3 hours?
    df['target'] = (df['close'].shift(-3) > df['close']).astype(int)
    
    return df.dropna()

def train_model(ticker: str, model_path: str, company_name: str, include_oil: bool = True):
    try:
        df = prepare_data(ticker, include_oil=include_oil)
        
        if df.empty:
            print(f"❌ Błąd: Brak danych dla {company_name}")
            return False
        
        # Updated feature list (must match ModelPredictor)
        features = [
            'rsi', 'ema_20', 'close', 'oil_chg', 'usd_chg', 
            'sentiment_score', 'news_volume', 
            'pe_ratio', 'pb_ratio', 'profit_margin'
        ]
        
        X = df[features]
        y = df['target']
        
        print(f"🔧 Trenowanie modelu XGBoost dla {company_name} ({len(X)} próbek)...")
        
        # XGBoost Classifier
        model = XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            random_state=42,
            n_jobs=-1,
            eval_metric='logloss'
        )
        
        model.fit(X, y)
        
        # Save
        model_dir = Path(model_path).parent
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)
        
        print(f"✅ Sukces! Model zapisany w {model_path}")
        return True
        
    except Exception as e:
        print(f"❌ Błąd przy trenowaniu {company_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def train_all_models():
    """Trains models for all companies"""
    print("🚀 Rozpoczęcie trenowania modeli dla wszystkich spółek...\n")
    
    success_count = 0
    for company_key, company_info in COMPANIES.items():
        ticker = company_info['ticker']
        model_path = company_info['model_path']
        company_name = company_info['name']
        include_oil = company_info.get('include_oil', True)
        
        if train_model(ticker, model_path, company_name, include_oil=include_oil):
            success_count += 1
        print()
    
    print(f"📈 Podsumowanie: {success_count}/{len(COMPANIES)} modeli trenowanych pomyślnie!")


if __name__ == "__main__":
    train_all_models()
