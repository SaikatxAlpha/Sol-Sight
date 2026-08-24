"""
Orchestrates the full SolSight inference pipeline:

  Image + Operational Data
        │
        ▼
  CNN  ──► defect label, confidence, 128-d feature vector
        │
        ▼
  MLP  ──► Healthy / Warning / Critical + health_score
        │
        ▼
  Bi-LSTM (uses this panel's historical health_scores) ──► 30/60/90 day forecast
        │
        ▼
  Maintenance recommendation (rule-based on status + forecast slope)
"""
import io
import os
from typing import List, Optional

import torch
from PIL import Image
from torchvision import transforms

from app.models.cnn_model import DefectCNN, IMAGE_SIZE
from app.models.mlp_model import HealthMLP
from app.models.bilstm_model import DegradationBiLSTM, FORECAST_HORIZONS_DAYS

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "saved_models")

_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class PredictionService:
    """Loads all three models once and exposes a single `.run_inspection()` call."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.cnn = DefectCNN(pretrained=False).to(self.device)
        self.mlp = HealthMLP().to(self.device)
        self.bilstm = DegradationBiLSTM().to(self.device)
        self._load_weights_if_available()
        self.cnn.eval()
        self.mlp.eval()
        self.bilstm.eval()

    def _load_weights_if_available(self):
        for name, model in [("cnn_best.pt", self.cnn), ("mlp_best.pt", self.mlp), ("bilstm_best.pt", self.bilstm)]:
            path = os.path.join(MODEL_DIR, name)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                try:
                    state = torch.load(path, map_location=self.device)
                    model.load_state_dict(state)
                except Exception as e:
                    print(f"[PredictionService] Could not load {name}, using randomly-initialized weights: {e}")
            else:
                print(f"[PredictionService] {name} not found/empty — using randomly-initialized weights for demo.")

    def _numeric_feature_vector(self, voltage, current, temperature, rated_power,
                                 defect_confidence, historical_avg_health) -> torch.Tensor:
        power = voltage * current
        efficiency = (power / rated_power) if rated_power else 0.0
        vals = [voltage, current, power, temperature, efficiency, defect_confidence, historical_avg_health]
        return torch.tensor(vals, dtype=torch.float32, device=self.device)

    def run_inspection(
        self,
        image_bytes: Optional[bytes],
        voltage: float,
        current: float,
        temperature: float,
        rated_power: float,
        history: List[float],
    ) -> dict:
        # --- 1. CNN: defect detection ---
        if image_bytes:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        else:
            img = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), color=(128, 128, 128))
        x = _transform(img).unsqueeze(0).to(self.device)
        defect_label, defect_conf, defect_probs, cnn_features = self.cnn.predict(x)

        # --- 2. MLP: health classification ---
        historical_avg = sum(history) / len(history) if history else 90.0
        numeric_feats = self._numeric_feature_vector(
            voltage, current, temperature, rated_power, defect_conf, historical_avg
        )
        status, health_score, health_probs = self.mlp.predict(cnn_features, numeric_feats)

        # --- 3. Bi-LSTM: degradation forecast ---
        seq = history + [health_score]
        forecast = self.bilstm.predict(seq)

        # --- 4. Power loss + recommendation ---
        power_output = voltage * current
        expected_power = rated_power or power_output
        power_loss_pct = max(0.0, round((1 - power_output / expected_power) * 100, 1)) if expected_power else 0.0
        recommendation = self._build_recommendation(status, defect_label, forecast)

        return {
            "detected_defect": defect_label,
            "confidence": round(defect_conf * 100, 1),
            "defect_probabilities": {k: round(v * 100, 1) for k, v in defect_probs.items()},
            "status": status,
            "health_score": health_score,
            "health_probabilities": {k: round(v * 100, 1) for k, v in health_probs.items()},
            "power_output": round(power_output, 2),
            "power_loss_pct": power_loss_pct,
            "degradation_forecast": forecast,
            "recommendation": recommendation,
        }

    @staticmethod
    def _build_recommendation(status: str, defect: str, forecast: List[dict]) -> str:
        end_health = forecast[-1]["predicted_health"] if forecast else None
        if status == "Critical":
            return f"Critical condition detected ({defect}). Schedule immediate on-site inspection and repair."
        if status == "Warning":
            if end_health is not None and end_health < forecast[0]["predicted_health"] - 5:
                return (f"Degradation is accelerating (projected {end_health}% at "
                        f"{FORECAST_HORIZONS_DAYS[-1]} days). Inspection recommended within the next maintenance cycle.")
            return "Panel shows early warning signs. Monitor closely and plan a routine inspection."
        return "Panel is operating normally. Continue standard maintenance schedule."


# Singleton instance used by the routers
prediction_service = PredictionService()