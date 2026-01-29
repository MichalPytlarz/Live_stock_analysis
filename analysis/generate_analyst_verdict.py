def generate_analyst_verdict(ticker_change, sector_change, avg_sentiment):
    # Relacja spółka vs sektor (tzw. Alpha)
    alpha = ticker_change - sector_change
    
    if avg_sentiment > 0.2:
        if alpha > 0.5:
            return "🚀 LIDER WZROSTÓW: Sentyment pozytywny, a spółka bije swój sektor. Silny trend.", "green"
        elif alpha < -0.5:
            return "⚠️ SŁABOŚĆ RELATYWNA: Newsy są dobre, ale spółka zostaje w tyle za branżą. Uwaga!", "orange"
        else:
            return "✅ ZDROWY WZROST: Spółka rośnie zgodnie z optymizmem i trendem sektora.", "blue"
            
    elif avg_sentiment < -0.2:
        if alpha < -0.5:
            return "📉 PANIKA: Negatywne newsy i spółka spada mocniej niż branża. Wysokie ryzyko.", "red"
        elif alpha > 0.5:
            return "🛡️ ODPORNOŚĆ: Sentyment jest słaby, ale spółka trzyma się lepiej niż branża.", "yellow"
        else:
            return "📉 ZGODNY SPADEK: Sentyment i branża są pod presją. Spółka płynie z prądem.", "gray"
            
    return "⚖️ NEUTRALNIE: Brak wyraźnych sygnałów z NLP lub sektora.", "white"