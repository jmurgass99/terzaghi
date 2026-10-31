"""Durabilidad y vida útil del hormigón (Suite 2).

Modelos de iniciación de la corrosión de armaduras:
- chlorides: difusión de cloruros por la 2ª ley de Fick (EN 206 / ACI 365).
- carbonation: avance del frente de carbonatación (ley de la raíz del tiempo).
"""
from terzaghi.durability.carbonation import (
    carbonation_coefficient,
    carbonation_depth,
    time_to_depth,
)
from terzaghi.durability.chlorides import ChlorideInput, concentration, time_to_initiation

__all__ = [
    "ChlorideInput",
    "concentration",
    "time_to_initiation",
    "carbonation_coefficient",
    "carbonation_depth",
    "time_to_depth",
]
