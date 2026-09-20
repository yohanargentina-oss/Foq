"""
Module de Calibration RLCD pour Foq.
Garantit l'alignement strict entre probabilités prédites et réalité statistique :
si Foq annonce 80 % de confiance, l'événement se produit réellement dans 80 % des cas.
"""

import json
import math
import os
from typing import Dict, List, Tuple, Any, Optional
import numpy as np


class BrierScore:
    """Calcul du Brier Score (règle de score strictement propre)."""

    @staticmethod
    def compute(probabilities: List[float], outcomes: List[int]) -> float:
        """
        probabilities: probabilités attribuées à la classe vraie (ou vecteur p_i)
        outcomes: 1 si correct, 0 si incorrect
        """
        assert len(probabilities) == len(outcomes), "Tailles discordantes."
        if not probabilities:
            return 0.0
        diffs = [(p - y) ** 2 for p, y in zip(probabilities, outcomes)]
        return float(np.mean(diffs))


class ExpectedCalibrationError:
    """
    Calcul de l'ECE (Expected Calibration Error).
    Divise les prédictions en M bins d'intervalles de confiance et mesure l'écart absolu
    entre l'exactitude empirique et la confiance moyenne.
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins

    def compute(self, confidences: List[float], correctness: List[bool]) -> Dict[str, Any]:
        """
        confidences: probabilité du choix retenu (ex: [0.85, 0.92, ...])
        correctness: True si la prédiction était exacte, False sinon
        """
        n = len(confidences)
        if n == 0:
            return {"ece": 0.0, "bins": []}

        conf = np.array(confidences)
        corr = np.array(correctness, dtype=float)

        bin_boundaries = np.linspace(0.0, 1.0, self.n_bins + 1)
        ece = 0.0
        bin_details = []

        for i in range(self.n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]

            # Éléments dans le bin
            if i == self.n_bins - 1:
                in_bin = (conf >= bin_lower) & (conf <= bin_upper)
            else:
                in_bin = (conf >= bin_lower) & (conf < bin_upper)

            count = int(np.sum(in_bin))
            if count > 0:
                acc = float(np.mean(corr[in_bin]))
                avg_conf = float(np.mean(conf[in_bin]))
                gap = abs(acc - avg_conf)
                ece += (count / n) * gap

                bin_details.append({
                    "bin_range": (round(bin_lower, 2), round(bin_upper, 2)),
                    "count": count,
                    "accuracy": round(acc, 4),
                    "confidence": round(avg_conf, 4),
                    "gap": round(gap, 4),
                })

        return {
            "ece": float(ece),
            "ece_percentage": f"{ece * 100:.2f}%",
            "bins": bin_details,
        }


class TemperatureScaler:
    """
    Couche de mise à l'échelle par température (Temperature Scaling / Platt Scaling).
    Ajuste la température T pour éliminer la sur-confiance des réseaux de neurones.
    """

    def __init__(self, temperature: float = 1.0):
        self.temperature = max(0.01, float(temperature))

    def scale_logits(self, logits: Dict[str, float]) -> Dict[str, float]:
        """Applique la température T aux logits avant softmax."""
        if abs(self.temperature - 1.0) < 1e-4:
            return logits
        return {k: v / self.temperature for k, v in logits.items()}

    def scale_probabilities(self, logprobs: Dict[str, float]) -> Dict[str, float]:
        """
        Prend des logprobs brutes ln(p_i), re-calibre via la température T
        et renvoie les nouvelles probabilités normalisées.
        """
        keys = list(logprobs.keys())
        raw_vals = np.array([logprobs[k] for k in keys])

        scaled = raw_vals / self.temperature
        shift = scaled - np.max(scaled)
        exps = np.exp(shift)
        probs = exps / np.sum(exps)

        return {k: float(p) for k, p in zip(keys, probs)}

    def fit(self, dataset: List[Dict[str, Any]]) -> float:
        """
        Optimise la température T sur un ensemble d'exemples de validation
        pour minimiser la perte de calibration (Log-Loss / NLL).
        """
        from scipy.optimize import minimize_scalar

        def nll_loss(T: float) -> float:
            if T <= 0.05:
                return 1e9
            total_loss = 0.0
            for item in dataset:
                logprobs = item["logprobs"]
                target = item["correct_choice"]
                if target not in logprobs:
                    continue
                keys = list(logprobs.keys())
                vals = np.array([logprobs[k] for k in keys]) / T
                shift = vals - np.max(vals)
                exps = np.exp(shift)
                probs = exps / np.sum(exps)
                target_idx = keys.index(target)
                prob_target = max(1e-12, probs[target_idx])
                total_loss += -math.log(prob_target)
            return total_loss / max(1, len(dataset))

        res = minimize_scalar(nll_loss, bounds=(0.1, 5.0), method="bounded")
        self.temperature = float(res.x)
        return self.temperature


class CalibrationProfile:
    """Sauvegarde et chargement d'un profil de calibration."""

    _DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration_profile.json")

    def __init__(self, filepath: str = _DEFAULT):
        self.filepath = filepath
        self.temperature = 1.0
        self.ece = 0.0
        self.brier_score = 0.0
        self.model_alias = "foq"
        self.timestamp = ""

    def load(self) -> bool:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.temperature = data.get("temperature", 1.0)
                    self.ece = data.get("ece", 0.0)
                    self.brier_score = data.get("brier_score", 0.0)
                    self.model_alias = data.get("model_alias", "foq")
                    self.timestamp = data.get("timestamp", "")
                    return True
            except Exception:
                return False
        return False

    def save(self) -> None:
        import datetime
        data = {
            "model_alias": self.model_alias,
            "temperature": self.temperature,
            "ece": self.ece,
            "brier_score": self.brier_score,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
