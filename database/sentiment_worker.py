import time
import pandas as pd
from gnews import GNews
from transformers import pipeline
from database_manager import init_db, save_sentiment_results
from deep_translator import GoogleTranslator

# 1. Konfiguracja
init_db()  # Upewnij się, że tabele istnieją
translator = GoogleTranslator(source='pl', target='en')
google_news = GNews(language='pl', country='PL', period='2d', max_results=15)

# Załaduj model FinBERT (może chwilę potrwać przy pierwszym pobieraniu)
print("Ładowanie modelu FinBERT NLP...")
nlp_pipe = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")

def process_all_companies():
    # Wczytaj listę tickerów z Twojego CSV
    df_companies = pd.read_csv('companies.csv') # upewnij się, że nazwa pliku się zgadza
    
    for _, row in df_companies.iterrows():
        ticker = row['ticker']
        name = row['name']
        
        print(f"Analizowanie: {name} ({ticker})...")
        
        try:
            # Pobierz newsy
            news = google_news.get_news(f'{name} akcje giełda')
            if not news:
                print(f"Brak newsów dla {name}")
                continue
                
            headlines_pl = [item['title'] for item in news]
            processed_data = []
            scores = []
            
            # Mapowanie punktowe FinBERT
            score_map = {'Positive': 1.0, 'Negative': -1.0, 'Neutral': 0.0}

            for text in headlines_pl:
                # Tłumaczenie na angielski (dla FinBERT)
                text_en = translator.translate(text)
                
                # Analiza NLP
                result = nlp_pipe(text_en)[0]
                label = result['label']
                conf = result['score']
                
                processed_data.append((text, label))
                scores.append(score_map[label] * conf)
            
            # Oblicz średnią i zapisz do bazy
            avg_score = sum(scores) / len(scores) if scores else 0
            save_sentiment_results(ticker, avg_score, len(processed_data), processed_data)
            print(f"Zapisano: {name} | Score: {avg_score:.2f}")
            
        except Exception as e:
            print(f"Błąd przy {name}: {e}")
            continue

# 2. Pętla główna (np. co 30 minut)
if __name__ == "__main__":
    while True:
        print(f"\n--- Rozpoczynam cykl analizy: {time.ctime()} ---")
        process_all_companies()
        print("\n--- Cykl zakończony. Zasypiam na 30 minut. ---")
        time.sleep(1800) # 1800 sekund = 30 minut