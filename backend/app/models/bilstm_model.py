"""
Bi-LSTM degradation-prediction model.

Takes a sequence of past health scores (0-100) for a panel and forecasts
future health at fixed horizons (30 / 60 / 90 days by default).
"""
from typing import List
import torch
import torch.nn as nn

FORECAST_HORIZONS_DAYS = [30, 60, 90]


class DegradationBiLSTM(nn.Module):
    def __init__(self, input_dim: int = 1, hidden_dim: int = 32, num_layers: int = 2,
                 num_horizons: int = len(FORECAST_HORIZONS_DAYS)):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.2 if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Linear(32, num_horizons),
        )

    def forward(self, x):
        # x: (B, T, 1)
        out, _ = self.lstm(x)
        last_step = out[:, -1, :]  # (B, hidden_dim*2)
        return self.head(last_step)  # (B, num_horizons) -> delta from current health

    @torch.no_grad()
    def predict(self, history: List[float]) -> List[dict]:
        """
        history: list of past health scores, oldest first (e.g. [96, 94, 91, 87, 81])
        Returns list of {"day": d, "predicted_health": v}
        """
        self.eval()
        if len(history) == 0:
            history = [80.0]
        x = torch.tensor(history, dtype=torch.float32).view(1, -1, 1) / 100.0
        deltas = self.forward(x)[0]  # raw model output, treated as fractional decline
        current = history[-1]
        forecast = []
        for i, day in enumerate(FORECAST_HORIZONS_DAYS):
            # Model predicts a decline fraction; combine with a simple trend fallback
            # so output stays sane even for an untrained/lightly-trained model.
            trend = _linear_trend_decline(history, day)
            model_component = float(torch.tanh(deltas[i]).item()) * 15  # bounded influence
            predicted = max(0.0, min(100.0, current - trend - abs(model_component) * 0.2))
            forecast.append({"day": day, "predicted_health": round(predicted, 1)})
        return forecast


def _linear_trend_decline(history: List[float], day: int) -> float:
    """Fallback/blend: estimate decline over `day` days from the recent slope of history."""
    if len(history) < 2:
        return day * 0.05
    slope = (history[0] - history[-1]) / max(1, len(history) - 1)  # health loss per inspection
    slope = max(slope, 0.0)
    per_day = slope / 7.0  # assume ~weekly inspections
    return per_day * day