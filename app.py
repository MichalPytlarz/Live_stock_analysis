import streamlit as st
import yfinance as yf
from stockstats import StockDataFrame
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import joblib

st.set_page_config(page_title="Orlen ML Dashboard", layout="wide")

st.title("📊 Monitorowanie Spółki ORLEN (PKN.WA) na żywo")

# Sidebar - Ustawienia
st.sidebar.header("Ustawienia")
ticker = "PKN.WA"
interval = st.sidebar.selectbox("Interwał", ["1m", "5m", "15m", "1h"], index=2)

@st.cache_data(ttl=60)
def load_data(interval):
    # 1. Pobieramy Orlen, Ropę i USD/PLN
    orlen = yf.download("PKN.WA", period="5d", interval=interval)
    oil = yf.download("BZ=F", period="5d", interval=interval)['Close']
    usdpln = yf.download("PLN=X", period="5d", interval=interval)['Close']
    
    # 2. Naprawa MultiIndex (dla yfinance)
    if isinstance(orlen.columns, pd.MultiIndex):
        orlen.columns = orlen.columns.get_level_values(0)
    
    df = orlen.copy()
    df.columns = df.columns.str.lower()
    
    # 3. Synchronizacja danych
    df['oil_price'] = oil
    df['usdpln'] = usdpln
    df = df.ffill().sort_index()
    
    # 4. Feature Engineering (Cechy dla ML)
    stock = StockDataFrame.retype(df.copy())
    df['rsi'] = stock['rsi_14']
    df['ema_20'] = stock['close_20_ema']
    df['oil_chg'] = df['oil_price'].pct_change()
    df['usd_chg'] = df['usdpln'].pct_change()
    
    # 5. Cel (Target) - wzrost za 3 godziny
    df['target'] = (df['close'].shift(-3) > df['close']).astype(int)
    
    return df.dropna()

data = load_data(interval)

if data.empty:
    st.error("Błąd: Nie udało się pobrać danych. Sprawdź połączenie z internetem lub czy symbol jest poprawny.")
    st.stop() # Zatrzymuje działanie Streamlit, by nie szedł dalej do pustego iloc[-1]

if len(data) < 2:
    st.warning("Pobrano zbyt mało danych, aby obliczyć wskaźniki (RSI/EMA). Spróbuj zwiększyć okres (period).")
    st.stop()



try:
    model = joblib.load('orlen_ai_model.pkl')
    
    # Pobieramy dane do predykcji (upewnij się, że kolumny są te same!)
    features = ['rsi', 'ema_20', 'close', 'oil_chg', 'usd_chg']
    last_row = data[features].iloc[-1:]
    
    # Sprawdzamy czy nie ma NaN (np. jeśli ropa nie pobrała się poprawnie)
    if last_row.isnull().values.any():
        st.warning("⚠️ Oczekiwanie na kompletne dane rynkowe...")
    else:
        probabilities = model.predict_proba(data[features])
        
        # 2. Pobieramy wyniki dla ostatniego wiersza (do metryki pod wykresem)
        prediction = model.predict(data[features].iloc[-1:])[0]
        prob_last = probabilities[-1][1] # szansa na wzrost dla ostatniego wpisu

        # 3. Tworzymy sygnały historyczne używając suwaka (min_confidence)
        # Kupno: szansa na wzrost [:, 1] > suwak
        st.sidebar.markdown("---")
        st.sidebar.header("Filtrowanie AI")
        min_confidence = st.sidebar.slider("Minimalna pewność modelu (%)", 50, 90, 65) / 100

        data['buy_signal'] = (probabilities[:, 1] > min_confidence).astype(int)
        # Sprzedaż: szansa na spadek [:, 0] > suwak
        data['sell_signal'] = (probabilities[:, 0] > min_confidence).astype(int)

        # 4. Filtrujemy dane do wyświetlenia na wykresie
        buy_signals = data[data['buy_signal'] == 1]
        sell_signals = data[data['sell_signal'] == 1]
        
except FileNotFoundError:
    st.info("💡 Najpierw uruchom skrypt treningowy, aby wygenerować model 'orlen_ai_model.pkl'")


# Layout: Statystyki na górze
col1, col2, col3, col4, col5 = st.columns(5)
current_price = data['close'].iloc[-1]
prev_price = data['close'].iloc[-2]
change = current_price - prev_price

oil_now = data['oil_price'].iloc[-1]
oil_prev = data['oil_price'].iloc[-2]
oil_diff = oil_now - oil_prev

usd_now = data['usdpln'].iloc[-1]
usd_prev = data['usdpln'].iloc[-2]
usd_diff = usd_now - usd_prev

col1.metric("Cena PKN.WA", f"{current_price:.2f} PLN", f"{change:.2f} PLN")
col2.metric("RSI (14)", f"{data['rsi'].iloc[-1]:.2f}")
col3.metric("Ostatnia aktualizacja", datetime.now().strftime("%H:%M:%S"))
col4.metric("Ropa Brent (USD)", f"{oil_now:.2f}$", f"{oil_diff:.2f}$")
col5.metric("USD/PLN", f"{usd_now:.4f} zł", f"{usd_diff:.4f} zł")

# Wykres świecowy
fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['open'], high=data['high'],
                low=data['low'], close=data['close'], name='Notowania')])

# Dodanie linii EMA
fig.add_trace(go.Scatter(x=data.index, y=data['ema_20'], name='EMA 20', line=dict(color='orange')))

fig.add_trace(go.Scatter(
    x=buy_signals.index,
    y=buy_signals['close'],
    mode='markers',
    marker=dict(symbol='triangle-up', size=10, color='#00ff00'),
    name='AI: Sugerowany Wzrost'
))


fig.add_trace(go.Scatter(
    x=sell_signals.index,
    y=sell_signals['close'],
    mode='markers',
    marker=dict(symbol='triangle-down', size=10, color='#ff0000'),
    name='AI: Sugerowany Spadek'
))


fig.update_layout(title=f"Wykres techniczny {ticker}", xaxis_rangeslider_visible=False, yaxis_title="Cena w PLN")
st.plotly_chart(fig, use_container_width=True)


st.subheader("🛢️ Notowania Ropy Brent (BZ=F)")

fig_oil = go.Figure()

# Wykres liniowy dla ropy
fig_oil.add_trace(go.Scatter(
    x=data.index, 
    y=data['oil_price'], 
    mode='lines', 
    name='Ropa Brent (USD)',
    line=dict(color='silver', width=2)
))

fig_oil.update_layout(
    height=300, 
    margin=dict(l=20, r=20, t=20, b=20),
    xaxis_rangeslider_visible=False,
    yaxis_title="Cena w USD"
)

st.plotly_chart(fig_oil, use_container_width=True)

# Sekcja ML (Szkielet)
st.subheader("🤖 Predykcja Modelu ML")
rsi_val = data['rsi'].iloc[-1]

if rsi_val > 70:
    st.warning("Sygnał: WYKUPIONO (Możliwy spadek)")
elif rsi_val < 30:
    st.success("Sygnał: WYPRZEDANO (Możliwy wzrost)")
else:
    st.info("Sygnał: NEUTRALNY")




data['target'] = (data['close'].shift(-3) > data['close']).astype(int)



if prediction == 1:
    st.success(f"🤖 AI PRZEWIDUJE: WZROST (Prawdopodobieństwo: {prob_last:.2%})")
else:
    st.error(f"🤖 AI PRZEWIDUJE: SPADEK (Prawdopodobieństwo: {1-prob_las.2%})")