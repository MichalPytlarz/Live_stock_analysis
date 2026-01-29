from textblob import TextBlob
from googletrans import Translator
import requests
from bs4 import BeautifulSoup
from gnews import GNews
from deep_translator import GoogleTranslator
import streamlit as st
import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_company_info


google_news = GNews(language='pl', country='PL', period='7d', max_results=5)

@st.cache_data(ttl=3600) # dla odswiezania strony co 1h
def get_reliable_sentiment(ticker: str):
    """
    Pobiera sentyment newsów dla spółki
    
    Args:
        ticker: Symbol giełdowy (np. PKN.WA)
    
    Returns:
        (avg_sentiment, headlines) - średni sentyment (-1 do 1) i lista nagłówków
    """
    try:
        # Pobieramy nazwę spółki z config
        company = get_company_info(ticker)
        if not company:
            return 0.0, []
        
        company_name = company['name']
        
        news = google_news.get_news(f'{company_name} akcje giełda')
        if not news:
            return 0.0, []
        
        headlines = [item['title'] for item in news]
        sentiments = []

        # Tworzymy translator (synchroniczny)
        translator = GoogleTranslator(source='pl', target='en')

        for text in headlines:
            # Tłumaczenie odbywa się teraz bez błędów "coroutine"
            translated = translator.translate(text)
            score = TextBlob(translated).sentiment.polarity
            sentiments.append(score)
        
        if not sentiments:
            return 0.0, headlines
            
        avg_sentiment = sum(sentiments) / len(sentiments)
        return avg_sentiment, headlines
    except Exception as e:
        # Logowanie błędu do konsoli dla Ciebie
        st.sidebar.error(f"Sentyment Error ({ticker}): {e}")
        return 0.0, []



def get_sentiment_emoji(score):
    """Zwraca tekst sentymentu z emoji"""
    if score > 0.1:
        return "🟢 POZYTYWNY"
    elif score < -0.1:
        return "🔴 NEGATYWNY"
    else:
        return "🟡 NEUTRALNY"


def get_sentiment_text(score):
    """Zwraca szczegółowy opis sentymentu"""
    if score > 0.5:
        return "Bardzo pozytywny"
    elif score > 0.1:
        return "Pozytywny"
    elif score < -0.5:
        return "Bardzo negatywny"
    elif score < -0.1:
        return "Negatywny"
    else:
        return "Neutralny"
