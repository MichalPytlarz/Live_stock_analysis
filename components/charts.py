import plotly.graph_objects as go
import pandas as pd


def create_candlestick_chart(
    data: pd.DataFrame,
    ticker: str,
    buy_signals: pd.DataFrame = None,
    sell_signals: pd.DataFrame = None
) -> go.Figure:
    """
    Tworzy wykres świecowy z sygnałami
    
    Args:
        data: DataFrame z danymi OHLC
        ticker: Symbol papieru wartościowego
        buy_signals: DataFrame z sygnałami kupna
        sell_signals: DataFrame z sygnałami sprzedaży
    
    Returns:
        Figura Plotly
    """
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Notowania'
    )])
    
    # Dodanie linii EMA
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['ema_20'],
        name='EMA 20',
        line=dict(color='orange')
    ))
    
    # Sygnały kupna
    if buy_signals is not None and not buy_signals.empty:
        fig.add_trace(go.Scatter(
            x=buy_signals.index,
            y=buy_signals['close'],
            mode='markers',
            marker=dict(symbol='triangle-up', size=10, color='#00ff00'),
            name='AI: Sugerowany Wzrost'
        ))
    
    # Sygnały sprzedaży
    if sell_signals is not None and not sell_signals.empty:
        fig.add_trace(go.Scatter(
            x=sell_signals.index,
            y=sell_signals['close'],
            mode='markers',
            marker=dict(symbol='triangle-down', size=10, color='#ff0000'),
            name='AI: Sugerowany Spadek'
        ))
    
    fig.update_layout(
        title=f"Wykres techniczny {ticker}",
        xaxis_rangeslider_visible=False,
        yaxis_title="Cena w PLN"
    )
    
    return fig


def create_oil_chart(data: pd.DataFrame) -> go.Figure:
    """
    Tworzy wykres dla ceny ropy Brent
    
    Args:
        data: DataFrame z danymi
    
    Returns:
        Figura Plotly
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['oil_price'],
        mode='lines',
        name='Ropa Brent (USD)',
        line=dict(color='silver', width=2)
    ))
    
    fig.update_layout(
        title="🛢️ Notowania Ropy Brent (BZ=F)",
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_rangeslider_visible=False,
        yaxis_title="Cena w USD"
    )
    
    return fig
