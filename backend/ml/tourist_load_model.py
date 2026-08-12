"""
Tourist Load Forecasting Model.

Uses XGBoost with feature engineering for seasonal, event, and day-of-week effects.
Falls back to a simple historical-average rule when no trained model exists.

DATA LABEL: PREDICTED — all outputs are ML estimates, not official counts.
"""
import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime, timedelta
from typing import Optional
import warnings
warnings.filterwarnings("ignore")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "tourist_load_model.pkl")


class TouristLoadForecaster:
    """
    Predicts daily tourist arrivals per destination.

    Features used:
      - day_of_week (0–6)
      - month (1–12)
      - is_holiday (bool)
      - is_event_period (bool)
      - destination_popularity (float 1–10)
      - estimated_capacity (int)
      - days_since_start (int) — trend proxy
    """

    def __init__(self):
        self.model = None
        self.is_trained = False
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.is_trained = True
            except Exception:
                self.is_trained = False

    def _build_features(self, date: datetime, destination_popularity: float,
                        estimated_capacity: int, is_event: bool) -> np.ndarray:
        dow = date.weekday()
        month = date.month
        is_holiday = 1 if dow in [5, 6] else 0
        is_event_int = 1 if is_event else 0
        # Peak months for Kutch tourism: Nov–Feb
        is_peak_season = 1 if month in [11, 12, 1, 2] else 0
        # Rann Utsav period proxy
        is_utsav = 1 if (month in [11, 12, 1, 2] and is_event_int) else 0

        return np.array([[
            dow, month, is_holiday, is_event_int,
            is_peak_season, is_utsav,
            destination_popularity, estimated_capacity
        ]])

    def train(self, df: pd.DataFrame) -> dict:
        """
        Train on historical data.
        df must have columns:
          date, destination_id, actual_visitors, day_of_week, is_holiday,
          is_event_period, popularity_score, estimated_capacity
        Returns evaluation metrics.
        """
        try:
            from xgboost import XGBRegressor
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

            df = df.dropna(subset=["actual_visitors"])
            df["month"] = pd.to_datetime(df["date"]).dt.month
            df["is_peak_season"] = df["month"].isin([11, 12, 1, 2]).astype(int)
            df["is_utsav"] = ((df["is_peak_season"] == 1) & (df["is_event_period"] == 1)).astype(int)

            features = ["day_of_week", "month", "is_holiday", "is_event_period",
                        "is_peak_season", "is_utsav", "popularity_score", "estimated_capacity"]

            X = df[features].values
            y = df["actual_visitors"].values

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            model = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                                 random_state=42, verbosity=0)
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)

            self.model = model
            self.is_trained = True
            joblib.dump(model, MODEL_PATH)

            return {
                "status": "trained",
                "data_label": "PREDICTED",
                "mae": round(float(mae), 2),
                "rmse": round(float(rmse), 2),
                "r2": round(float(r2), 4),
                "training_samples": len(X_train),
                "note": "Model trained on synthetic demo data. Accuracy reflects demo quality only."
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def predict(self, date: datetime, destination_popularity: float,
                estimated_capacity: int, is_event: bool = False,
                confidence_base: float = 0.85) -> dict:
        """
        Predict visitors for a single date + destination.
        Returns dict with predicted_visitors, confidence_score, factors, data_label.
        """
        features = self._build_features(date, destination_popularity, estimated_capacity, is_event)
        month = date.month
        dow = date.weekday()
        is_peak = month in [11, 12, 1, 2]
        is_weekend = dow in [5, 6]

        if self.is_trained and self.model is not None:
            raw = float(self.model.predict(features)[0])
            predicted = int(max(0, min(round(raw), estimated_capacity)))
            confidence = round(confidence_base + (0.05 if is_peak else 0.0), 2)
            method = "xgboost"
        else:
            # Fallback heuristic
            base = estimated_capacity * 0.35
            if is_peak:
                base *= 1.55
            if is_weekend:
                base *= 1.25
            if is_event:
                base *= 1.7
            predicted = int(min(round(base), estimated_capacity))
            confidence = round(0.65, 2)
            method = "heuristic_fallback"

        utilization = round(predicted / max(estimated_capacity, 1) * 100, 1)

        # Determine load label
        if utilization < 40:
            load_label = "LOW"
        elif utilization < 65:
            load_label = "MODERATE"
        elif utilization < 85:
            load_label = "HIGH"
        else:
            load_label = "CRITICAL"

        factors = []
        if is_peak:
            factors.append("peak tourism season (Nov–Feb)")
        if is_weekend:
            factors.append("weekend")
        if is_event:
            factors.append("Rann Utsav / event period")
        if not factors:
            factors.append("standard weekday / off-season")

        return {
            "data_label": "PREDICTED",
            "predicted_visitors": predicted,
            "estimated_capacity": estimated_capacity,
            "utilization_pct": utilization,
            "load_label": load_label,
            "confidence_score": min(confidence, 0.95),
            "main_factors": factors,
            "method": method,
            "note": "This is a model estimate, not an official count.",
            "forecast_date": date.isoformat(),
        }

    def forecast_week(self, start_date: datetime, destination_popularity: float,
                      estimated_capacity: int, is_event: bool = False) -> list:
        """Return 7-day forecast."""
        return [
            self.predict(start_date + timedelta(days=i), destination_popularity,
                         estimated_capacity, is_event)
            for i in range(7)
        ]
