import streamlit as st
from components.data_loader import load_data_cached
from components.model_predictor import ModelPredictor
from components.metrics_display import display_metrics, display_rsi_signal, display_prediction
from components.charts import create_candlestick_chart, create_oil_chart, create_sector_heatmap
from config import get_company_info, get_all_sectors, get_companies_by_sector, COMPANIES
from sentimental_analysis import get_reliable_sentiment, get_sentiment_emoji, get_sentiment_text
from textblob import TextBlob
from database.database_manager import get_sentiment_trend
# Konfiguracja Streamlit
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

# Nagłówek
st.markdown("# 📈 Analiza rynkow gieldowych")

# Sidebar - Wybór sektora
st.sidebar.header("🎯 Wybór opcji")
view_mode = st.sidebar.radio("Wybierz tryb widoku:", ["📈 Analiza spółek", "🔥 Heatmapa sektora"])

# Pobierz wszystkie sektory
all_sectors = get_all_sectors()
selected_sector = st.sidebar.selectbox("Sektor:", all_sectors)

# Pobierz spółki z wybranego sektora
companies_in_sector = get_companies_by_sector(selected_sector)


def display_sentiment_section(ticker):
    st.subheader("📰 Zaawansowana Analiza Sentymentu (NLP)")
    
    # Pobierz historię z bazy
    df_sentiment = get_sentiment_trend(ticker, limit=20)
    
    if not df_sentiment.empty:
        last_score = df_sentiment['avg_score'].iloc[0]
        
        # Wyświetl metrykę
        col1, col2 = st.columns([1, 2])
        col1.metric("Sentyment FinBERT", f"{last_score:.2f}", delta=None)
        
        # Wyświetl wykres trendu
        with col2:
            st.line_chart(df_sentiment.set_index('timestamp'))
    else:
        st.info("Oczekiwanie na pierwsze dane z Workera...")


def render_dashboard(ticker: str):
    """Renderuje dashboard dla wybranej spółki"""
    company = get_company_info(ticker)
    model_path = company['model_path']
    include_oil = company.get('include_oil', True)
    
    st.title(f"📊 Monitorowanie {company['name']} ({ticker}) na żywo")
    
    # Sidebar - Ustawienia
    st.sidebar.header("Ustawienia")
    interval = st.sidebar.selectbox(f"Interwał - {company['name']}", ["1m", "5m", "15m", "1h"], index=2, key=f"interval_{ticker}")

    # Pobieranie danych
    data = load_data_cached(ticker, period="3d", interval=interval, include_oil=include_oil)
    
    # Validacja danych
    if data.empty:
        st.error("Błąd: Nie udało się pobrać danych. Sprawdź połączenie z internetem lub czy symbol jest poprawny.")
        return
    
    if len(data) < 2:
        st.warning("Pobrano zbyt mało danych, aby obliczyć wskaźniki (RSI/EMA). Spróbuj zwiększyć okres (period).")
        return
    
    # Inicjalizacja modelu
    predictor = ModelPredictor(model_path)
    
    # Jeśli model jest dostępny, generujemy sygnały
    if predictor.is_model_available():
        # Filtrowanie AI w głównym obszarze (specyficzne dla każdej załadki)
        with st.expander("⚙️ Filtrowanie AI", expanded=True):
            min_confidence = st.slider("Minimalna pewność modelu (%)", 50, 90, 65, key=f"confidence_{ticker}") / 100
        
        data = predictor.generate_signals(data, min_confidence=min_confidence)
        prediction_result = predictor.get_last_prediction(data)
    else:
        st.info(f"💡 Najpierw uruchom skrypt treningowy, aby wygenerować model '{model_path}'")
        prediction_result = None
        data['buy_signal'] = 0
        data['sell_signal'] = 0
    
    # Filtrowanie sygnałów
    buy_signals = data[data['buy_signal'] == 1]
    sell_signals = data[data['sell_signal'] == 1]
    
    # Wyświetlenie metryk
    display_metrics(data, include_oil=include_oil)
    
    # Wykres świecowy
    fig = create_candlestick_chart(data, ticker, buy_signals, sell_signals)
    st.plotly_chart(fig, use_container_width=True, key=f"candlestick_{ticker}")
    
    # Wykres ropy Brent (tylko dla spółek energetycznych)
    if include_oil and 'oil_price' in data.columns:
        fig_oil = create_oil_chart(data)
        st.plotly_chart(fig_oil, use_container_width=True, key=f"oil_{ticker}")

    ## Analiza NLP nastrojow z uwzglednieniem historii
    display_sentiment_section(ticker)
    
    # Sentiment dla aktualnej spółki (BEZ HISTORII - aktualne dane)
    st.markdown("---")
    st.subheader("📰 Analiza nastrojów z wiadomości")
    sentiment_score, headlines = get_reliable_sentiment(ticker)
    
    col1, col2, col3 = st.columns([1.5, 2, 2])
    with col1:
        st.metric("Wynik", f"{sentiment_score:.2f}")
    with col2:
        st.write(f"**Status:** {get_sentiment_emoji(sentiment_score)}")
    with col3:
        st.write(f"**Opis:** {get_sentiment_text(sentiment_score)}")
    
    if headlines:
        st.write("**Ostatnie wiadomości:**")
        for headline in headlines[:3]:
            st.caption(f"• {headline}")
    else:
        st.info("Brak dostępnych wiadomości")


    # Sygnały RSI
    rsi_val = data['rsi'].iloc[-1]
    display_rsi_signal(rsi_val)
    
    # Predykcja modelu
    display_prediction(prediction_result)
    



# Zakładki dla spółek w sektorze lub Heatmapa
if view_mode == "📈 Analiza spółek":
    # Tryb analizy spółek
    if companies_in_sector:
        st.subheader(f"📊 Spółki z sektora: {selected_sector}")
        
        tab_titles = [f"{get_company_info(ticker)['emoji']} {get_company_info(ticker)['name']}" for ticker in companies_in_sector]
        
        # Znaleźć domyślnie Orlen (PKN.WA)
        default_idx = 0
        for i, ticker in enumerate(companies_in_sector):
            if ticker == 'PKN.WA':
                default_idx = i
                break
        
        selected_company = st.pills("", options=tab_titles, default=tab_titles[default_idx])
        
        if selected_company:
            selected_idx = tab_titles.index(selected_company)
            selected_ticker = companies_in_sector[selected_idx]
            render_dashboard(selected_ticker)
    else:
        st.warning("Brak spółek w wybranym sektorze")

else:
    # Tryb heatmapy sektora
    st.subheader(f"🔥 Heatmapa sektora: {selected_sector}")
    
    if companies_in_sector:        
        # Pobieranie aktualnych cen dla spółek
        sector_prices = {}
        with st.spinner("Pobieranie danych cen..."):
            for ticker in companies_in_sector:
                try:
                    data = load_data_cached(ticker, period="5d", interval="1h", include_oil=False)
                    if not data.empty and len(data) >= 2:
                        current_price = data['close'].iloc[-1]
                        prev_price = data['close'].iloc[-2]
                        sector_prices[ticker] = {
                            'current_price': current_price,
                            'prev_price': prev_price
                        }
                except Exception as e:
                    st.warning(f"⚠️ Błąd pobierania danych dla {ticker}: {str(e)}")
        
        # Wyświetlenie heatmapy
        if sector_prices:
            heatmap_fig = create_sector_heatmap(COMPANIES, sector_prices)
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True, key="sector_heatmap")
            else:
                st.error("Nie udało się utworzyć heatmapy")
        else:
            st.error("Nie udało się pobrać danych cen dla spółek w sektorze")
    else:
        st.warning("Brak spółek w wybranym sektorze")