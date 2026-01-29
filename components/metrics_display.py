import streamlit as st
import pandas as pd
from datetime import datetime


def display_metrics(data: pd.DataFrame, ticker: str = None, include_oil: bool = True):
    """
    Wyświetla metryki w kolumnach
    
    Args:
        data: DataFrame z danymi
        ticker: Symbol giełdowy (do określenia waluty)
        include_oil: Czy wyświetlać dane o ropie
    """
    # Określenie jednostki waluty na podstawie tickera
    currency = "USD" if ticker and "BTC-USD" in ticker else "PLN"
    
    # Dane ceny
    current_price = data['close'].iloc[-1]
    prev_price = data['close'].iloc[-2]
    price_change = current_price - prev_price
    
    # Dane USD/PLN
    usd_now = data['usdpln'].iloc[-1]
    usd_prev = data['usdpln'].iloc[-2]
    usd_diff = usd_now - usd_prev
    
    # Liczba kolumn zależy od tego czy mamy ropę
    if include_oil and 'oil_price' in data.columns:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Dane ropy
        oil_now = data['oil_price'].iloc[-1]
        oil_prev = data['oil_price'].iloc[-2]
        oil_diff = oil_now - oil_prev
        
        # Wyświetlenie
        col1.metric("Cena", f"{current_price:.2f} {currency}", f"{price_change:.2f} {currency}")
        col2.metric(f"RSI (14) ~ {'Ryzyko wzrostu' if data['rsi'].iloc[-1] < 30 else 'Ryzyko spadku'}", f"{data['rsi'].iloc[-1]:.2f}")
        col3.metric("Ostatnia aktualizacja", datetime.now().strftime("%H:%M:%S"))
        col4.metric("Ropa Brent (USD)", f"{oil_now:.2f}$", f"{oil_diff:.2f}$")
        col5.metric("USD/PLN", f"{usd_now:.4f} zł", f"{usd_diff:.4f} zł")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        # Wyświetlenie bez ropy
        col1.metric("Cena", f"{current_price:.2f} {currency}", f"{price_change:.2f} {currency}")
        col2.metric(f"RSI (14) ~ {'Ryzyko wzrostu' if data['rsi'].iloc[-1] < 30 else 'Ryzyko spadku'}", f"{data['rsi'].iloc[-1]:.2f}")
        col3.metric("Ostatnia aktualizacja", datetime.now().strftime("%H:%M:%S"))


def display_prediction(prediction_dict: dict):
    """
    Wyświetla wynik predykcji modelu ML
    
    Args:
        prediction_dict: Słownik z wynikami predykcji
    """

    st.subheader("🤖 Predykcja Modelu ML (XGB) na podstawie analizy fundamentalnej i sentymentu (Predykcja na 3 kolejne godziny do przodu)")
    if prediction_dict is None:
        st.warning("Model niedostępny")
        return
    
    if prediction_dict['prediction'] == 1:
        st.success(
            f"🤖 AI PRZEWIDUJE: WZROST\n"
            f"Prawdopodobieństwo: {prediction_dict['prob_up']:.2%}"
        )
    else:
        st.error(
            f"🤖 AI PRZEWIDUJE: SPADEK\n"
            f"Prawdopodobieństwo: {prediction_dict['prob_down']:.2%}"
        )
