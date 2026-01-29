import yfinance as yf
import pandas as pd
import plotly.express as px


def get_market_overview(companies_dict):
    overview_list = []
    for ticker, info in companies_dict.items():
        # Pobieramy dane (interwał 1d, okres 2d, aby obliczyć zmianę)
        df = yf.download(ticker, period="2d", interval="1d", progress=False)
        if not df.empty and len(df) >= 2:
            last_close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            change = ((last_close - prev_close) / prev_close) * 100
            
            overview_list.append({
                "ticker": ticker,
                "name": info['name'],
                "sector": info['sector'],
                "change": round(change, 2),
                "price": round(last_close, 2)
            })
    return pd.DataFrame(overview_list)


def create_sector_heatmap(df):
    fig = px.treemap(
        df,
        path=[px.Constant("GPW & Inne"), 'sector', 'name'], # Hierarchia: Rynek -> Sektor -> Spółka
        values=None, # Możesz tu wstawić wolumen, jeśli go pobierasz
        color='change',
        color_continuous_scale='RdYlGn', # Skala: Red-Yellow-Green
        color_continuous_midpoint=0,
        hover_data=['price', 'ticker'],
        custom_data=['change']
    )
    
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Zmiana: %{customdata[0]}%<br>Cena: %{value}"
    )
    
    fig.update_layout(margin=dict(t=30, l=10, r=10, b=10))
    return fig
