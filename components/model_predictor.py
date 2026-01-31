import pandas as pd
import numpy as np
import joblib
from pathlib import Path


class ModelPredictor:
    """Class for managing ML models and predictions"""
    
    def __init__(self, model_path: str = 'pkn_wa_ai_model.pkl'):
        """
        Initializes the predictor
        
        Args:
            model_path: Path to the model file
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
        """Loads the model from file"""
        if Path(self.model_path).exists():
            self.model = joblib.load(self.model_path)
        else:
            self.model = None
    
    def is_model_available(self) -> bool:
        """Checks whether the model is available"""
        return self.model is not None
    
    def predict(self, data: pd.DataFrame) -> tuple:
        """
        Runs prediction
        
        Args:
            data: DataFrame with required features
        
        Returns:
            (predictions, probabilities) - arrays with predictions and probabilities
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
        Returns a prediction for the last data row
        
        Args:
            data: DataFrame with data
        
        Returns:
            Dictionary with prediction, probability, and class
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
        Generates buy/sell signals based on the model
        
        Args:
            data: DataFrame with data
            min_confidence: Minimum confidence for a signal (0.0 - 1.0)
        
        Returns:
            DataFrame with additional columns (buy_signal, sell_signal)
        """
        if not self.is_model_available():
            return data.copy()
        
        data = data.copy()
        _, probabilities = self.predict(data)
        
        # Signals
        data['buy_signal'] = (probabilities[:, 1] > min_confidence).astype(int)
        data['sell_signal'] = (probabilities[:, 0] > min_confidence).astype(int)
        
        return data
