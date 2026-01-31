import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots



def create_candlestick_chart(
    data: pd.DataFrame,
    ticker: str,
    buy_signals: pd.DataFrame = None,
    sell_signals: pd.DataFrame = None,
    interval: str = "15m"
) -> go.Figure:
    """
    Creates a candlestick chart with signals
    
    Args:
        data: DataFrame with OHLC data
        ticker: Security symbol
        buy_signals: DataFrame with buy signals
        sell_signals: DataFrame with sell signals
        interval: Time interval (1m, 5m, 15m, 1h)
    
    Returns:
        Plotly figure
    """
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Notowania'
    )])
    
    # Add EMA line
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['ema_20'],
        name='EMA 20',
        line=dict(color='orange', shape='spline'),
        mode='lines',
        connectgaps=True,
    ))
    
    # Buy signals
    if buy_signals is not None and not buy_signals.empty:
        fig.add_trace(go.Scatter(
            x=buy_signals.index,
            y=buy_signals['close'],
            mode='markers',
            marker=dict(symbol='triangle-up', size=10, color='#00ff00'),
            name='AI: Sugerowany Wzrost'
        ))
    
    # Sell signals
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
                dict(bounds=["sat", "mon"]), # Remove weekends (Saturday to Monday morning)
                dict(bounds=[16, 9], pattern="hour"), # Remove hours outside the session (17:00 - 09:00)
            ]
        )
    
    # Determine currency unit based on ticker
    currency = "USD" if "BTC-USD" in ticker else "PLN"
    
    # Auto-fit initial range to interval
    interval_ranges = {
        "1m": 30,   # Last 30 minutes (30 points)
        "5m": 48,   # Last 4 hours (48 points)
        "15m": 32,  # Last 8 hours (32 points)
        "1h": len(data)  # Full range
    }
    
    points_to_show = interval_ranges.get(interval, len(data))
    start_idx = max(0, len(data) - points_to_show)
    initial_x_range = [data.index[start_idx], data.index[-1]]
    
    # Calculate Y range for VISIBLE data (not all)
    visible_data = data.iloc[start_idx:]
    y_min = visible_data[['low', 'ema_20']].min().min() * 0.98  # 2% margin down
    y_max = visible_data[['high', 'ema_20']].max().max() * 1.02  # 2% margin up
    
    fig.update_layout(
        title=f"Wykres techniczny {ticker}",
        xaxis_rangeslider_visible=False,
        yaxis_title=f"Cena w {currency}",
        xaxis=dict(
            fixedrange=False,
            range=initial_x_range
        ),
        yaxis=dict(
            fixedrange=False,
            range=[y_min, y_max]
        ),
        dragmode='pan'
    )
    
    return fig


def create_oil_chart(data: pd.DataFrame) -> go.Figure:
    """
    Creates a chart for Brent oil price
    
    Args:
        data: DataFrame with data
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['oil_price'],
        mode='lines',
        name='Ropa Brent (USD)',
        line=dict(color='silver', width=2, shape='spline'),
        connectgaps=True,
    ))
    
    # Min and max lines
    oil_min = data['oil_price'].min()
    oil_max = data['oil_price'].max()
    oil_min_idx = data['oil_price'].idxmin()
    oil_max_idx = data['oil_price'].idxmax()
    
    # Min line
    fig.add_trace(go.Scatter(
        x=[data.index[0], data.index[-1]],
        y=[oil_min, oil_min],
        mode='lines',
        line=dict(color='#FFD700', width=2, dash='dash'),
        name=f'Min: {oil_min:.2f}',
        showlegend=True
    ))
    # Dot at min
    fig.add_trace(go.Scatter(
        x=[oil_min_idx],
        y=[oil_min],
        mode='markers',
        marker=dict(size=10, color='#FFD700'),
        showlegend=False
    ))
    
    # Max line
    fig.add_trace(go.Scatter(
        x=[data.index[0], data.index[-1]],
        y=[oil_max, oil_max],
        mode='lines',
        line=dict(color='#FF1493', width=2, dash='dash'),
        name=f'Max: {oil_max:.2f}',
        showlegend=True
    ))
    # Dot at max
    fig.add_trace(go.Scatter(
        x=[oil_max_idx],
        y=[oil_max],
        mode='markers',
        marker=dict(size=10, color='#FF1493'),
        showlegend=False
    ))
    
    # Calculate range to limit zoom
    y_min = data['oil_price'].min() * 0.98
    y_max = data['oil_price'].max() * 1.02
    
    fig.update_layout(
        title="🛢️ Notowania Ropy Brent (BZ=F)",
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_rangeslider_visible=False,
        yaxis_title="Cena w USD",
        xaxis=dict(
            fixedrange=False,
            range=[data.index[0], data.index[-1]]
        ),
        yaxis=dict(
            fixedrange=False,
            range=[y_min, y_max]
        ),
        dragmode='pan'
    )

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]), # Remove weekends (Saturday to Monday morning)
            dict(bounds=[17, 9], pattern="hour"), # Remove hours outside the session (17:00 - 09:00)
        ]
    )
    
    return fig


def create_sector_heatmap(companies_data: dict, sector_prices: dict) -> go.Figure:
    """
    Creates a heatmap of percentage changes for companies in a sector
    
    Args:
        companies_data: Companies data dictionary from config
        sector_prices: Price data dictionary {ticker: {current_price, prev_price}}
    
    Returns:
        Plotly heatmap figure
    """
    if not sector_prices:
        return None
    
    # Prepare data for the heatmap
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
    
    # Create heatmap
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
    
    # Calculate range to limit zoom
    y_min = min(changes) * 1.2 if min(changes) < 0 else min(changes) * 0.8
    y_max = max(changes) * 1.2 if max(changes) > 0 else max(changes) * 0.8
    
    fig.update_layout(
        title="📊 Heatmapa zmian procentowych sektora",
        xaxis_title="Spółka",
        yaxis_title="Zmiana procentowa (%)",
        height=500,
        hovermode='x unified',
        showlegend=False,
        xaxis=dict(
            fixedrange=False,
            range=[-0.5, len(tickers) - 0.5]
        ),
        yaxis=dict(
            fixedrange=False,
            range=[y_min, y_max]
        ),
        dragmode='pan',
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








def create_combined_chart(price_data, sentiment_df, ticker, sector_data=None, sector_name="Sektor"):
    # Create a figure with two Y axes
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # --- COMPANY PRICE STANDARDIZATION ---
    # Calculate percent change relative to the first price in the visible range
    ticker_start_price = price_data['close'].iloc[0]
    ticker_norm = ((price_data['close'] / ticker_start_price) - 1) * 100

    # 1. Standardized price line chart (main Y axis)
    # Use Scatter instead of Candlestick because candles look bad after % normalization
    fig.add_trace(
        go.Scatter(
            x=price_data.index,
            y=ticker_norm,
            name=f"Cena {ticker} (%)",
            line=dict(color='#00ff00', width=3, shape='spline'),
            mode='lines',
            connectgaps=True,
            hovertemplate='%{y:.2f}%'
        ),
        secondary_y=False
    )

    # --- BENCHMARK STANDARDIZATION ---
    if sector_data is not None and not sector_data.empty:
        # Sync and normalize benchmark
        sector_resampled = sector_data['close'].reindex(price_data.index).ffill()
        sector_start_price = sector_resampled.iloc[0]
        sector_norm = ((sector_resampled / sector_start_price) - 1) * 100
        
        fig.add_trace(
            go.Scatter(
                x=sector_resampled.index,
                y=sector_norm,
                name=f"Benchmark: {sector_name} (%)",
                line=dict(color='rgba(255, 255, 255, 0.5)', width=2, dash='dot', shape='spline'),
                mode='lines',
                connectgaps=True,
                hovertemplate='%{y:.2f}%'
            ),
            secondary_y=False
        )

    # 2. Sentiment chart (secondary Y axis - right)
    if sentiment_df is not None and not sentiment_df.empty:
        time_col = 'timestamp' if 'timestamp' in sentiment_df.columns else 'trading_timestamp'
        
        fig.add_trace(
            go.Scatter(
                x=sentiment_df[time_col],
                y=sentiment_df['avg_score'],
                name="Sentyment NLP",
                line=dict(color='royalblue', width=3, shape='spline'),
                mode='lines+markers',
                connectgaps=True
            ),
            secondary_y=True
        )

    # Min and max lines for price (main Y axis)
    ticker_min = ticker_norm.min()
    ticker_max = ticker_norm.max()
    ticker_min_idx = ticker_norm.idxmin()
    ticker_max_idx = ticker_norm.idxmax()
    
    # Min line
    fig.add_trace(
        go.Scatter(
            x=[price_data.index[0], price_data.index[-1]],
            y=[ticker_min, ticker_min],
            mode='lines',
            line=dict(color='#FFD700', width=2, dash='dash'),
            name=f'Min: {ticker_min:.2f}%',
            showlegend=True
        ),
        secondary_y=False
    )
    # Dot at min
    fig.add_trace(
        go.Scatter(
            x=[ticker_min_idx],
            y=[ticker_min],
            mode='markers',
            marker=dict(size=10, color='#FFD700'),
            showlegend=False
        ),
        secondary_y=False
    )
    
    # Max line
    fig.add_trace(
        go.Scatter(
            x=[price_data.index[0], price_data.index[-1]],
            y=[ticker_max, ticker_max],
            mode='lines',
            line=dict(color='#FF1493', width=2, dash='dash'),
            name=f'Max: {ticker_max:.2f}%',
            showlegend=True
        ),
        secondary_y=False
    )
    # Dot at max
    fig.add_trace(
        go.Scatter(
            x=[ticker_max_idx],
            y=[ticker_max],
            mode='markers',
            marker=dict(size=10, color='#FF1493'),
            showlegend=False
        ),
        secondary_y=False
    )

    # --- REMOVE MARKET BREAKS ---
    if "USD" not in ticker:
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
                dict(bounds=[17, 9], pattern="hour"),
            ]
        )

    # Calculate range to limit zoom
    y_min = min(ticker_norm.min(), sector_norm.min() if sector_data is not None and not sector_data.empty else ticker_norm.min()) * 1.2
    y_max = max(ticker_norm.max(), sector_norm.max() if sector_data is not None and not sector_data.empty else ticker_norm.max()) * 1.2
    
    # Layout styling
    fig.update_layout(
        title=f"Analiza Porównawcza (Normalizacja %): {ticker} vs {sector_name}",
        xaxis_rangeslider_visible=False,
        height=650,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            fixedrange=False,
            range=[price_data.index[0], price_data.index[-1]]
        ),
        dragmode='pan'
    )
    
    # Settings for the main Y axis with limits
    fig.update_yaxes(
        title_text="Zmiana skumulowana (%)",
        secondary_y=False,
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='gray',
        range=[y_min, y_max]
    )

    # Settings for the sentiment axis
    fig.update_yaxes(title_text="Sentyment NLP (-1 do 1)", secondary_y=True, range=[-1.1, 1.1], showgrid=False)

    return fig