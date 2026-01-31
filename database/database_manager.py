import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "stocks_analysis.db"

def init_db():
    """Initializes the database and creates tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Aggregated sentiment table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_history (
            ticker TEXT,
            timestamp DATETIME,
            avg_score FLOAT,
            news_count INTEGER,
            PRIMARY KEY (ticker, timestamp)
        )
    ''')
    
    # Individual headlines table
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
    """Saves analysis results to the database"""
    conn = sqlite3.connect(DB_NAME)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save average
    conn.execute('''
        INSERT INTO sentiment_history (ticker, timestamp, avg_score, news_count)
        VALUES (?, ?, ?, ?)
    ''', (ticker, now, avg_score, news_count))
    
    # Save details (headlines_data is a list of tuples: (headline, label))
    for headline, label in headlines_data:
        conn.execute('''
            INSERT INTO news_details (ticker, headline, sentiment_label, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (ticker, headline, label, now))
        
    conn.commit()
    conn.close()

def get_sentiment_trend(ticker, limit=10):
    """Fetches sentiment history for a Streamlit chart"""
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT ticker, timestamp, avg_score FROM sentiment_history WHERE ticker = '{ticker}' ORDER BY timestamp DESC LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_worker_status():
    """Checks sentiment worker status and returns the last update"""
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
        # 1. Weekends -> Monday 09:00
        if dt.weekday() >= 5:
            days_to_add = 7 - dt.weekday()
            return (dt + pd.Timedelta(days=days_to_add)).replace(hour=9, minute=0, second=0)
        
        # 2. Night (after session 17:00+) -> Next day 09:00
        if dt.hour >= 17:
            # If Friday evening -> move to Monday
            if dt.weekday() == 4:
                return (dt + pd.Timedelta(days=3)).replace(hour=9, minute=0, second=0)
            return (dt + pd.Timedelta(days=1)).replace(hour=9, minute=0, second=0)
        
        # 3. Early morning (before 09:00) -> Today 09:00
        if dt.hour < 9:
            return dt.replace(hour=9, minute=0, second=0)
        
        return dt

    # Shift news timestamps
    df['trading_timestamp'] = df['timestamp'].apply(map_to_trading_hours)

    # KEY STEP: Grouping and averaging
    # If we have 10 overnight news items, all will get trading_timestamp 09:00 and be averaged
    df_aggregated = df.groupby('trading_timestamp').agg({
        'avg_score': 'mean',
        'ticker': 'first' # keep ticker
    }).reset_index()
    df_aggregated.rename(columns={'trading_timestamp': 'timestamp'}, inplace=True)

    return df_aggregated.sort_values('timestamp')