from textblob import TextBlob
from googletrans import Translator
import requests
from bs4 import BeautifulSoup
from gnews import GNews
from deep_translator import GoogleTranslator
import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_company_info


google_news = GNews(language='pl', country='PL', period='7d', max_results=5)

@st.cache_data(ttl=3600) # for page refresh every 1h
def get_reliable_sentiment(ticker: str):
    """
    Fetches news sentiment for a company
    
    Args:
        ticker: Stock ticker symbol (e.g., PKN.WA)
    
    Returns:
        (avg_sentiment, headlines) - average sentiment (-1 to 1) and list of headlines
    """
    try:
        # Get company name from config
        company = get_company_info(ticker)
        if not company:
            return 0.0, []
        
        company_name = company['name']
        
        news = google_news.get_news(f'{company_name} akcje giełda')
        if not news:
            return 0.0, []
        
        headlines = [item['title'] for item in news]
        sentiments = []

        # Create translator (synchronous)
        translator = GoogleTranslator(source='pl', target='en')

        for text in headlines:
            # Translation now runs without "coroutine" errors
            translated = translator.translate(text)
            score = TextBlob(translated).sentiment.polarity
            sentiments.append(score)
        
        if not sentiments:
            return 0.0, headlines
            
        avg_sentiment = sum(sentiments) / len(sentiments)
        return avg_sentiment, headlines
    except Exception as e:
        # Log error to the console for you
        st.sidebar.error(f"Sentyment Error ({ticker}): {e}")
        return 0.0, []



def get_sentiment_emoji(score):
    """Returns sentiment text with emoji"""
    if score > 0.1:
        return "🟢 POZYTYWNY"
    elif score < -0.1:
        return "🔴 NEGATYWNY"
    else:
        return "🟡 NEUTRALNY"


def get_sentiment_text(score):
    """Returns a detailed sentiment description"""
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
