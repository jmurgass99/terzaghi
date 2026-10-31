"""Bridge Terzaghi → SlopeStabilityJm.

Convierte parámetros geotécnicos a inputs de los métodos Bishop/Janbu
o Newmark para evaluar estabilidad sísmica de taludes.
"""
from __future__ import annotations

import warnings
from typing import Any


def call_newmark(accelerogram_g, dt_s: float, a_y_g: float) -> Any:
    try:
        from slipcircle.newmark import NewmarkInput, evaluate_newmark
    except ImportError:
        warnings.warn("SlopeStabilityJm no instalado", RuntimeWarning)
        return None
    return evaluate_newmark(NewmarkInput(
        accelerogram_g=accelerogram_g, dt_s=dt_s, a_y_g=a_y_g,
    ))


__all__ = ["call_newmark"]
