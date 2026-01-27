import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots



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

    
    if "USD" not in ticker:
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]), # Usuwa weekendy (od soboty do poniedziałku rano)
                dict(bounds=[16, 9], pattern="hour"), # Usuwa godziny poza sesją (17:00 - 09:00)
            ]
        )
    
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

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]), # Usuwa weekendy (od soboty do poniedziałku rano)
            dict(bounds=[16, 9], pattern="hour"), # Usuwa godziny poza sesją (16:00 - 09:00)
        ]
    )
    
    return fig


def create_sector_heatmap(companies_data: dict, sector_prices: dict) -> go.Figure:
    """
    Tworzy heatmapę zmian procentowych spółek w sektorze
    
    Args:
        companies_data: Słownik danych spółek z config
        sector_prices: Słownik z danymi cenowymi {ticker: {current_price, prev_price}}
    
    Returns:
        Figura Plotly heatmapy
    """
    if not sector_prices:
        return None
    
    # Przygotowanie danych dla heatmapy
    tickers = []
    names = []
    changes = []
    colors = []
    
    for ticker, price_data in sector_prices.items():
        if ticker in companies_data:
            company = companies_data[ticker]
            current = price_data.get('current_price', 0)
            prev = price_data.get('prev_price', 0)
            
            if prev > 0:
                change = ((current - prev) / prev) * 100
            else:
                change = 0
            
            tickers.append(ticker)
            names.append(company['name'])
            changes.append(change)
            colors.append('#00ff00' if change >= 0 else '#ff0000')
    
    if not tickers:
        return None
    
    # Tworzenie heatmapy
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=tickers,
        y=changes,
        marker=dict(color=colors),
        text=[f"{change:+.2f}%" for change in changes],
        textposition='auto',
        name='Zmiana (%)',
        hovertemplate='<b>%{customdata}</b><br>Zmiana: %{y:.2f}%<extra></extra>',
        customdata=names
    ))
    
    fig.update_layout(
        title="📊 Heatmapa zmian procentowych sektora",
        xaxis_title="Spółka",
        yaxis_title="Zmiana procentowa (%)",
        height=500,
        hovermode='x unified',
        showlegend=False,
        annotations=[
            dict(
                text="📌 Zmiana procentowa względem ceny z poprzedniej sesji",
                xref="paper", yref="paper",
                x=0, y=-0.15,
                showarrow=False,
                font=dict(size=12, color="gray"),
                align="left"
            )
        ]
    )
    
    return fig








def create_combined_chart(price_data, sentiment_df, ticker):
    # Tworzymy figurę z dwiema osiami Y
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Wykres świecowy (Główna oś Y)
    fig.add_trace(
        go.Candlestick(
            x=price_data.index,
            open=price_data['open'],
            high=price_data['high'],
            low=price_data['low'],
            close=price_data['close'],
            name="Cena"
        ),
        secondary_y=False
    )

    # 2. Wykres sentymentu (Druga oś Y - prawa)
    if sentiment_df is not None and not sentiment_df.empty:
        # Konwersja timestamp na datetime, by pasował do osi X wykresu ceny
        sentiment_df['timestamp'] = pd.to_datetime(sentiment_df['timestamp'])
        
        fig.add_trace(
            go.Scatter(
                x=sentiment_df['timestamp'],
                y=sentiment_df['avg_score'],
                name="Sentyment NLP (FinBERT)",
                line=dict(color='royalblue', width=3, shape='spline'),
                opacity=0.7,
                mode='lines+markers', # Dodaj punkty (markers), żeby widzieć konkretne odczyty
                connectgaps=True
            ),
            secondary_y=True
        )
    # if "USD" not in ticker:
    #     fig.update_xaxes(
    #         rangebreaks=[
    #             dict(bounds=["sat", "mon"]), # Usuwa weekendy (od soboty do poniedziałku rano)
    #             dict(bounds=[16, 9], pattern="hour"), # Usuwa godziny poza sesją (17:00 - 09:00)
    #         ]
    #     )

    ### TODO : MAPPING TO TRADING HOURS NLP Sentimental Analysis

    # Stylizacja
    fig.update_layout(
        title=f"Analiza Korelacji Cena vs Sentyment dla {ticker}",
        xaxis_rangeslider_visible=False,
        height=600,
        template="plotly_dark"
    )

    # Ustawienia osi
    fig.update_yaxes(title_text="Cena (PLN)", secondary_y=False)
    fig.update_yaxes(title_text="Sentyment (-1 do 1)", secondary_y=True, range=[-1, 1])

    return fig