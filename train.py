import yfinance as yf
import pandas as pd
from stockstats import StockDataFrame
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_final_model():
    print("🚀 Pobieranie danych historycznych (Orlen, Ropa, USDPLN)...")
    
    # 1. Pobieranie danych (2 lata, interwał 1h)
    orlen = yf.download("PKN.WA", period="2y", interval="1h")
    oil = yf.download("BZ=F", period="2y", interval="1h")['Close']
    usdpln = yf.download("PLN=X", period="2y", interval="1h")['Close']
    
    # Naprawa MultiIndex
    if isinstance(orlen.columns, pd.MultiIndex):
        orlen.columns = orlen.columns.get_level_values(0)
    
    df = orlen.copy()
    df.columns = df.columns.str.lower()
    
    # 2. Łączenie w jeden DataFrame
    df['oil_price'] = oil
    df['usdpln'] = usdpln
    df = df.ffill().sort_index()
    
    # 3. Dodawanie wskaźników przez stockstats
    stock = StockDataFrame.retype(df.copy())
    df['rsi'] = stock['rsi_14']
    df['ema_20'] = stock['close_20_ema']
    df['oil_chg'] = df['oil_price'].pct_change()
    df['usd_chg'] = df['usdpln'].pct_change()
    
    # 4. Target: Czy cena za 3h będzie wyższa?
    df['target'] = (df['close'].shift(-3) > df['close']).astype(int)
    df = df.dropna()
    
    # 5. Trening modelu
    features = ['rsi', 'ema_20', 'close', 'oil_chg', 'usd_chg']
    X = df[features]
    y = df['target']
    
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    # 6. Zapis
    joblib.dump(model, 'orlen_ai_model.pkl')
    print("✅ Sukces! Model 'orlen_ai_model.pkl' został zapisany.")

if __name__ == "__main__":
    train_final_model()