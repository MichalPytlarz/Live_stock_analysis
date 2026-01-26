import yfinance as yf
import pandas as pd
from stockstats import StockDataFrame
from sklearn.ensemble import RandomForestClassifier
import joblib
from pathlib import Path
from config import COMPANIES

def prepare_data(ticker: str, period: str = "2y", interval: str = "1h", include_oil: bool = True) -> pd.DataFrame:
    """
    Pobiera i przygotowuje dane do treningu
    
    Args:
        ticker: Symbol giełdowy
        period: Okres pobierania
        interval: Interwał czasu
        include_oil: Czy pobierać dane o ropie Brent
    
    Returns:
        DataFrame gotowy do treningu
    """
    print(f"📊 Pobieranie danych dla {ticker} ({period}, {interval})...")
    
    # 1. Pobieranie danych akcji
    stock = yf.download(ticker, period=period, interval=interval)
    
    # Pobieramy opcjonalnie ropę i USD/PLN
    if include_oil:
        oil = yf.download("BZ=F", period=period, interval=interval)['Close']
    usdpln = yf.download("PLN=X", period=period, interval=interval)['Close']
    
    # 2. Naprawa MultiIndex
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = stock.columns.get_level_values(0)
    
    df = stock.copy()
    df.columns = df.columns.str.lower()
    
    # 3. Łączenie w jeden DataFrame
    if include_oil:
        df['oil_price'] = oil
    df['usdpln'] = usdpln
    df = df.ffill().sort_index()
    
    # 4. Dodawanie wskaźników
    stock_indicators = StockDataFrame.retype(df.copy())
    df['rsi'] = stock_indicators['rsi_14']
    df['ema_20'] = stock_indicators['close_20_ema']
    
    if include_oil and 'oil_price' in df.columns:
        df['oil_chg'] = df['oil_price'].pct_change(fill_method=None)
    else:
        df['oil_chg'] = 0  # Domyślna wartość
    
    df['usd_chg'] = df['usdpln'].pct_change(fill_method=None)
    
    # 5. Target: Czy cena za 3h będzie wyższa?
    df['target'] = (df['close'].shift(-3) > df['close']).astype(int)
    
    return df.dropna()


def train_model(ticker: str, model_path: str, company_name: str, include_oil: bool = True):
    """
    Trenuje i zapisuje model dla danej spółki
    
    Args:
        ticker: Symbol giełdowy
        model_path: Ścieżka do zapisu modelu
        company_name: Nazwa spółki
        include_oil: Czy używać danych o ropie
    """
    try:
        # Przygotowanie danych
        df = prepare_data(ticker, include_oil=include_oil)
        
        if df.empty:
            print(f"❌ Błąd: Brak danych dla {company_name}")
            return False
        
        # Trening modelu
        features = ['rsi', 'ema_20', 'close', 'oil_chg', 'usd_chg']
        X = df[features]
        y = df['target']
        
        print(f"🔧 Trenowanie modelu dla {company_name} ({len(X)} próbek)...")
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X, y)
        
        # Tworzenie folderu jeśli nie istnieje
        model_dir = Path(model_path).parent
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Zapis modelu
        joblib.dump(model, model_path)
        print(f"✅ Sukces! Model '{model_path}' został zapisany.")
        return True
        
    except Exception as e:
        print(f"❌ Błąd przy trenowaniu {company_name}: {str(e)}")
        return False


def train_all_models():
    """Trenuje modele dla wszystkich spółek"""
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