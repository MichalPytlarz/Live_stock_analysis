import pandas as pd
import numpy as np
import joblib
from pathlib import Path


class ModelPredictor:
    """Klasa do zarządzania modelami ML i predykcjami"""
    
    def __init__(self, model_path: str = 'pkn_wa_ai_model.pkl'):
        """
        Inicjalizuje predictor
        
        Args:
            model_path: Ścieżka do pliku modelu
        """
        self.model_path = model_path
        self.model = None
        self.features = [
            'rsi', 'ema_20', 'close', 'oil_chg', 'usd_chg',
            'sentiment_score', 'news_volume',
            'pe_ratio', 'pb_ratio', 'profit_margin'    
        ]
        self.load_model()
    
    def load_model(self):
        """Ładuje model z pliku"""
        if Path(self.model_path).exists():
            self.model = joblib.load(self.model_path)
        else:
            self.model = None
    
    def is_model_available(self) -> bool:
        """Sprawdza czy model jest dostępny"""
        return self.model is not None
    
    def predict(self, data: pd.DataFrame) -> tuple:
        """
        Wykonuje predykcję
        
        Args:
            data: DataFrame z wymaganymi cechami
        
        Returns:
            (predictions, probabilities) - tablice z predykcjami i prawdopodobieństwami
        """
        if not self.is_model_available():
            raise ValueError("Model nie został załadowany")
        
        missing = [f for f in self.features if f not in data.columns]
        if missing:
            raise ValueError(f"Brakujące kolumny w danych: {missing}")
        
        X = data[self.features]
        
        X = X.fillna({'sentiment_score': 0, 'news_volume': 0})
        X = X.ffill().bfill()
        
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        
        return predictions, probabilities
    
    def get_last_prediction(self, data: pd.DataFrame) -> dict:
        """
        Zwraca predykcję dla ostatniego wiersza danych
        
        Args:
            data: DataFrame z danymi
        
        Returns:
            Słownik z predykcją, prawdopodobieństwem i klasą
        """
        if not self.is_model_available():
            return None
        
        try:
            last_row = data[self.features].iloc[-1:]
            predictions, probabilities = self.predict(data)
            
            prediction = predictions[-1]
            prob_up = probabilities[-1][1]
            prob_down = probabilities[-1][0]
            
            return {
                'prediction': prediction,
                'prob_up': prob_up,
                'prob_down': prob_down,
                'label': 'WZROST' if prediction == 1 else 'SPADEK'
            }
        except Exception as e:
            raise ValueError(f"Błąd przy predykcji: {str(e)}")
    
    def generate_signals(self, data: pd.DataFrame, min_confidence: float = 0.65) -> pd.DataFrame:
        """
        Generuje sygnały kupna/sprzedaży na podstawie modelu
        
        Args:
            data: DataFrame z danymi
            min_confidence: Minimalna pewność dla sygnału (0.0 - 1.0)
        
        Returns:
            DataFrame z dodatkowymi kolumnami (buy_signal, sell_signal)
        """
        if not self.is_model_available():
            return data.copy()
        
        data = data.copy()
        _, probabilities = self.predict(data)
        
        # Sygnały
        data['buy_signal'] = (probabilities[:, 1] > min_confidence).astype(int)
        data['sell_signal'] = (probabilities[:, 0] > min_confidence).astype(int)
        
        return data
