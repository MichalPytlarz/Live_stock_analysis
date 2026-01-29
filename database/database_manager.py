import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "stocks_analysis.db"

def init_db():
    """Inicjalizuje bazę danych i tworzy tabele"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela zagregowanych nastrojów
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_history (
            ticker TEXT,
            timestamp DATETIME,
            avg_score FLOAT,
            news_count INTEGER,
            PRIMARY KEY (ticker, timestamp)
        )
    ''')
    
    # Tabela pojedynczych nagłówków
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_details (
            ticker TEXT,
            headline TEXT,
            sentiment_label TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def save_sentiment_results(ticker, avg_score, news_count, headlines_data):
    """Zapisuje wyniki analizy do bazy"""
    conn = sqlite3.connect(DB_NAME)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Zapisz średnią
    conn.execute('''
        INSERT INTO sentiment_history (ticker, timestamp, avg_score, news_count)
        VALUES (?, ?, ?, ?)
    ''', (ticker, now, avg_score, news_count))
    
    # Zapisz detale (headlines_data to lista krotek: (nagłówek, label))
    for headline, label in headlines_data:
        conn.execute('''
            INSERT INTO news_details (ticker, headline, sentiment_label, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (ticker, headline, label, now))
        
    conn.commit()
    conn.close()

def get_sentiment_trend(ticker, limit=10):
    """Pobiera historię nastrojów dla wykresu w Streamlit"""
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT ticker, timestamp, avg_score FROM sentiment_history WHERE ticker = '{ticker}' ORDER BY timestamp DESC LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_worker_status():
    """Sprawdza status sentiment workera - zwraca ostatnią aktualizację"""
    try:
        conn = sqlite3.connect(DB_NAME)
        query = "SELECT MAX(timestamp) as last_update FROM sentiment_history"
        result = pd.read_sql_query(query, conn)
        conn.close()
        
        if result.empty or pd.isna(result['last_update'].iloc[0]):
            return None
        
        return pd.to_datetime(result['last_update'].iloc[0])
    except:
        return None



def get_processed_sentiment(sentiment_df):
    if sentiment_df.empty:
        return sentiment_df

    df = sentiment_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    def map_to_trading_hours(dt):
        # 1. Weekendy -> Poniedziałek 09:00
        if dt.weekday() >= 5:
            days_to_add = 7 - dt.weekday()
            return (dt + pd.Timedelta(days=days_to_add)).replace(hour=9, minute=0, second=0)
        
        # 2. Noc (po sesji 17:00+) -> Następny dzień 09:00
        if dt.hour >= 17:
            # Sprawdź czy to piątek wieczór -> wtedy na poniedziałek
            if dt.weekday() == 4:
                return (dt + pd.Timedelta(days=3)).replace(hour=9, minute=0, second=0)
            return (dt + pd.Timedelta(days=1)).replace(hour=9, minute=0, second=0)
        
        # 3. Wcześnie rano (przed 09:00) -> Dziś 09:00
        if dt.hour < 9:
            return dt.replace(hour=9, minute=0, second=0)
        
        return dt

    # Przesuwamy czasy newsów
    df['trading_timestamp'] = df['timestamp'].apply(map_to_trading_hours)

    # KLUCZOWY MOMENT: Grupowanie i uśrednianie
    # Jeśli mamy 10 newsów z nocy, wszystkie dostaną trading_timestamp 09:00 i zostaną uśrednione
    df_aggregated = df.groupby('trading_timestamp').agg({
        'avg_score': 'mean',
        'ticker': 'first' # zachowujemy ticker
    }).reset_index()
    df_aggregated.rename(columns={'trading_timestamp': 'timestamp'}, inplace=True)

    return df_aggregated.sort_values('timestamp')