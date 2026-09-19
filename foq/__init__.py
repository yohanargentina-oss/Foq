"""
Foq - Moteur de décision rapide Système 1 (27B)
Avec calibration RLCD et extraction de probabilités en une passe.
"""

from .engine import FoqEngine, FoqConnectionError, SystemOneResponse
from .calibration import TemperatureScaler, ExpectedCalibrationError, BrierScore, CalibrationProfile
from .schemas import (
    DecisionSchema,
    BinaryChoice,
    ClassificationChoice,
    Boolean,
    Bool,
    BooleanResult,
    BoolResult,
    Noul,
    NoulResult,
    Choice,
    Score,
    Structure,
)
from .security import FoqSecurityGuard, SecurityVerdict, FoqSecurityMiddleware
from .browser import FoqBrowserAgent, DOMPruner

__all__ = [
    "FoqEngine",
    "FoqConnectionError",
    "SystemOneResponse",
    "TemperatureScaler",
    "ExpectedCalibrationError",
    "BrierScore",
    "CalibrationProfile",
    "DecisionSchema",
    "BinaryChoice",
    "ClassificationChoice",
    "Boolean",
    "Bool",
    "BooleanResult",
    "BoolResult",
    "Noul",
    "NoulResult",
    "Choice",
    "Score",
    "Structure",
    "FoqSecurityGuard",
    "SecurityVerdict",
    "FoqSecurityMiddleware",
    "FoqBrowserAgent",
    "DOMPruner",
]
