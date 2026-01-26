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
    query = f"SELECT timestamp, avg_score FROM sentiment_history WHERE ticker = '{ticker}' ORDER BY timestamp DESC LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df