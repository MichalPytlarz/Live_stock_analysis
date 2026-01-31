import time
import pandas as pd
import sys
import os
from gnews import GNews
from transformers import pipeline
from deep_translator import GoogleTranslator

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.database_manager import init_db, save_sentiment_results

# 1. Configuration
init_db()  # Ensure tables exist
translator = GoogleTranslator(source='pl', target='en')
google_news = GNews(language='pl', country='PL', period='2d', max_results=15)

# Load the FinBERT model (may take a while on first download)
print("Ładowanie modelu FinBERT NLP...")
nlp_pipe = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")

def process_all_companies():
    # Load ticker list from your CSV
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'companies.csv')
    df_companies = pd.read_csv(csv_path)
    
    for _, row in df_companies.iterrows():
        ticker = row['ticker']
        name = row['name']
        
        print(f"Analizowanie: {name} ({ticker})...")
        
        try:
            # Fetch news
            news = google_news.get_news(f'{name} akcje giełda')
            if not news:
                print(f"Brak newsów dla {name}")
                continue
                
            headlines_pl = [item['title'] for item in news]
            processed_data = []
            scores = []
            
            # FinBERT score mapping
            score_map = {'Positive': 1.0, 'Negative': -1.0, 'Neutral': 0.0}

            for text in headlines_pl:
                # Translate to English (for FinBERT)
                text_en = translator.translate(text)
                
                # NLP analysis
                result = nlp_pipe(text_en)[0]
                label = result['label']
                conf = result['score']
                
                processed_data.append((text, label))
                scores.append(score_map[label] * conf)
            
            # Compute average and save to the database
            avg_score = sum(scores) / len(scores) if scores else 0
            save_sentiment_results(ticker, avg_score, len(processed_data), processed_data)
            print(f"Zapisano: {name} | Score: {avg_score:.2f}")
            
        except Exception as e:
            print(f"Błąd przy {name}: {e}")
            continue

# 2. Main loop (e.g., every 30 minutes)
if __name__ == "__main__":
    while True:
        print(f"\n--- Rozpoczynam cykl analizy: {time.ctime()} ---")
        process_all_companies()
        print("\n--- Cykl zakończony. Zasypiam na 30 minut. ---")
        time.sleep(1800) # 1800 seconds = 30 minutes
