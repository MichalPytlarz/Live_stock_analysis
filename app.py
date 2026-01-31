import streamlit as st
from components.data_loader import load_data_cached
from components.model_predictor import ModelPredictor
from components.metrics_display import display_metrics, display_prediction
from components.charts import create_candlestick_chart, create_oil_chart, create_sector_heatmap, create_combined_chart
from components.clock import add_dynamic_clock
from config import get_company_info, get_all_sectors, get_companies_by_sector, COMPANIES, METRIC_HELP, METRICS_CONFIG
from analysis.sentiment import get_reliable_sentiment, get_sentiment_emoji, get_sentiment_text
from analysis.market_status import get_market_status
from database.database_manager import get_sentiment_trend, get_processed_sentiment, get_worker_status
from analysis.benchmark import get_sector_info
from services.get_fundamental_data import get_fundamental_data
from datetime import datetime, timedelta
import plotly.graph_objects as go
import pandas as pd
# Streamlit configuration
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

# Display the clock
add_dynamic_clock()

# Header
st.markdown("# 📈 Analiza rynkow gieldowych")

# Sidebar - sector selection
st.sidebar.header("🎯 Wybór opcji")
view_mode = st.sidebar.radio("Wybierz tryb widoku:", ["📈 Analiza spółek", "🔥 Heatmapa sektora"])

# Fetch all sectors
all_sectors = get_all_sectors()
selected_sector = st.sidebar.selectbox("Sektor:", all_sectors)

# Fetch companies from the selected sector
companies_in_sector = get_companies_by_sector(selected_sector)

# Sentiment worker status in the sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Status Workera NLP")
last_update = get_worker_status()

if last_update:
    time_diff = datetime.now() - last_update
    
    if time_diff < timedelta(minutes=45):
        st.sidebar.success("✅ Aktywny")
        st.sidebar.caption(f"Ostatnia aktualizacja: {last_update.strftime('%H:%M:%S')}")
    else:
        st.sidebar.warning("⚠️ Nieaktywny")
        st.sidebar.caption(f"Ostatnia aktywność: {last_update.strftime('%Y-%m-%d %H:%M')}")
else:
    st.sidebar.error("❌ Brak danych")
    st.sidebar.caption("Worker nie był jeszcze uruchomiony")


def display_sentiment_section(ticker):
    st.subheader("📰 Zaawansowana Analiza Sentymentu (NLP)")
    
    # Fetch history from the database
    df_sentiment = get_sentiment_trend(ticker, limit=20)
    
    if not df_sentiment.empty:
        last_score = df_sentiment['avg_score'].iloc[0]
        
        # Display metric
        col1, col2 = st.columns([1, 2])
        col1.metric("Sentyment FinBERT", f"{last_score:.4f}", delta=None)
        
        # Display trend chart with Y-axis formatting
        with col2:
            df_sentiment['timestamp'] = pd.to_datetime(df_sentiment['timestamp'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_sentiment['timestamp'],
                y=df_sentiment['avg_score'],
                mode='lines+markers',
                name='Sentyment',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=6)
            ))
            
            # Min and max lines
            sentiment_min = df_sentiment['avg_score'].min()
            sentiment_max = df_sentiment['avg_score'].max()
            sentiment_min_idx = df_sentiment['avg_score'].idxmin()
            sentiment_max_idx = df_sentiment['avg_score'].idxmax()
            
            # Min line
            fig.add_trace(go.Scatter(
                x=[df_sentiment['timestamp'].iloc[0], df_sentiment['timestamp'].iloc[-1]],
                y=[sentiment_min, sentiment_min],
                mode='lines',
                line=dict(color='#FFD700', width=2, dash='dash'),
                name=f'Min: {sentiment_min:.4f}',
                showlegend=True
            ))
            # Dot at min
            fig.add_trace(go.Scatter(
                x=[df_sentiment.loc[sentiment_min_idx, 'timestamp']],
                y=[sentiment_min],
                mode='markers',
                marker=dict(size=10, color='#FFD700'),
                showlegend=False
            ))
            
            # Max line
            fig.add_trace(go.Scatter(
                x=[df_sentiment['timestamp'].iloc[0], df_sentiment['timestamp'].iloc[-1]],
                y=[sentiment_max, sentiment_max],
                mode='lines',
                line=dict(color='#FF1493', width=2, dash='dash'),
                name=f'Max: {sentiment_max:.4f}',
                showlegend=True
            ))
            # Dot at max
            fig.add_trace(go.Scatter(
                x=[df_sentiment.loc[sentiment_max_idx, 'timestamp']],
                y=[sentiment_max],
                mode='markers',
                marker=dict(size=10, color='#FF1493'),
                showlegend=False
            ))
            
            fig.update_layout(
                height=200,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title="",
                yaxis_title="Wynik",
                showlegend=False,
                dragmode='pan',
                yaxis=dict(
                    tickformat='.4f'
                )
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    else:
        st.info("Oczekiwanie na pierwsze dane z Workera...")

    return df_sentiment

def render_dashboard(ticker: str):

    fundamentals = get_fundamental_data(ticker)

    st.title(f"Dashboard: {fundamentals['name']}")
    st.write(f"**Sektor:** {fundamentals['sector']} | **Kapitalizacja:** {fundamentals['market_cap_formatted']}")


    cols = st.columns(len(METRICS_CONFIG))

    for col, config in zip(cols, METRICS_CONFIG):
        with col:
            # Fetch the value
            raw_value = fundamentals.get(config["key"])
            
            # Display logic: format only if numeric, otherwise show "N/A"
            if isinstance(raw_value, (int, float)):
                display_value = config["format"].format(raw_value)
            else:
                display_value = "N/A"
                
            st.metric(
                label=config["label"],
                value=display_value,
                help=METRIC_HELP.get(config["help_key"], "Brak opisu")
            )

    st.divider()

    company = get_company_info(ticker)
    model_path = company['model_path']
    include_oil = company.get('include_oil', True)
    
    st.title(f"📊 Monitorowanie {company['name']} ({ticker}) na żywo")
    
    # Interval selector above chart + market status
    col_interval, col_spacer, col_market = st.columns([1, 2, 2])
    with col_interval:
        interval = st.selectbox("⏱️ Interwał", ["1m", "5m", "15m", "1h"], index=2, key=f"interval_{ticker}")
    
    with col_market:
        is_open, market_msg = get_market_status()
        if is_open:
            st.success(market_msg)
        else:
            st.info(market_msg)

    # Fetch data
    data = load_data_cached(ticker, period="5d", interval=interval, include_oil=include_oil)
    
    # Data validation
    if data.empty:
        st.error("Błąd: Nie udało się pobrać danych. Sprawdź połączenie z internetem lub czy symbol jest poprawny.")
        return
    
    if len(data) < 2:
        st.warning("Pobrano zbyt mało danych, aby obliczyć wskaźniki (RSI/EMA). Spróbuj zwiększyć okres (period).")
        return
    
    # Model initialization
    predictor = ModelPredictor(model_path)
    
    # If the model is available, generate signals
    if predictor.is_model_available():
        # AI filtering in the main area (specific to each tab)
        with st.expander("⚙️ Filtrowanie AI", expanded=True):
            min_confidence = st.slider("Minimalna pewność modelu (%)", 50, 90, 65, key=f"confidence_{ticker}") / 100
        
        data = predictor.generate_signals(data, min_confidence=min_confidence)
        prediction_result = predictor.get_last_prediction(data)
    else:
        st.info(f"💡 Najpierw uruchom skrypt treningowy, aby wygenerować model '{model_path}'")
        prediction_result = None
        data['buy_signal'] = 0
        data['sell_signal'] = 0
    
    # Signal filtering
    buy_signals = data[data['buy_signal'] == 1]
    sell_signals = data[data['sell_signal'] == 1]
    
    # Display metrics
    display_metrics(data, ticker=ticker, include_oil=include_oil)
    
    # Candlestick chart
    fig = create_candlestick_chart(data, ticker, buy_signals, sell_signals, interval)
    st.plotly_chart(fig, use_container_width=True, key=f"candlestick_{ticker}", config={'scrollZoom': True})
    
    # Brent oil chart (only for energy companies)
    if include_oil and 'oil_price' in data.columns:
        fig_oil = create_oil_chart(data)
        st.plotly_chart(fig_oil, use_container_width=True, key=f"oil_{ticker}", config={'scrollZoom': True})


    ## NLP sentiment analysis with history
    sentiment = display_sentiment_section(ticker)

    bench_ticker, bench_name = get_sector_info(ticker) # Your mapping function
    sector_price_data = load_data_cached(bench_ticker, period="7d", interval="1h")
    
    sentiment_df= get_processed_sentiment(sentiment)


    fig = create_combined_chart(
    price_data=data, 
    sentiment_df=sentiment_df, 
    ticker=ticker,
    sector_data=sector_price_data,
    sector_name=bench_name
)

    # 4. Display
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    # Model prediction
    display_prediction(prediction_result)
    
    # Sentiment for the current company (NO HISTORY - current data)
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

    
    



# Tabs for companies in the sector or heatmap
if view_mode == "📈 Analiza spółek":
    # Company analysis mode
    if companies_in_sector:
        st.subheader(f"📊 Spółki z sektora: {selected_sector}")
        
        tab_titles = [f"{get_company_info(ticker)['emoji']} {get_company_info(ticker)['name']}" for ticker in companies_in_sector]
        
        # Find Orlen (PKN.WA) by default
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
    # Sector heatmap mode
    st.subheader(f"🔥 Heatmapa sektora: {selected_sector}")
    
    if companies_in_sector:         
        # Fetch current prices for companies
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
        
        # Display heatmap
        if sector_prices:
            heatmap_fig = create_sector_heatmap(COMPANIES, sector_prices)
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True, key="sector_heatmap", config={'scrollZoom': True})
            else:
                st.error("Nie udało się utworzyć heatmapy")
        else:
            st.error("Nie udało się pobrać danych cen dla spółek w sektorze")
    else:
        st.warning("Brak spółek w wybranym sektorze")