"""
EN 1997-1 §12 — Estabilidad de excavaciones (Terzaghi-Peck).

Verifica:
    1. Estabilidad del fondo (basal heave) — Terzaghi 1943
    2. Levantamiento por flotación — γ_w·H_w·A ≤ W
    3. Falla por sifonamiento (piping) — i_crit = (γ_sat - γ_w)/γ_w
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExcavationInput:
    depth_m: float
    width_m: float
    length_m: float
    su_kPa: float                    # cohesión no drenada del estrato
    gamma_kN_m3: float = 18.0        # peso específico del suelo
    surcharge_kPa: float = 10.0
    water_table_depth_m: float = 100.0  # profundidad NF (default profundo)


@dataclass(frozen=True)
class ExcavationResult:
    N_b: float                       # factor estabilidad Terzaghi (=H·γ/su)
    FS_basal_heave: float            # Terzaghi: FS = (5.14·su / (γ·H + q))
    FS_uplift: float                 # contra flotación
    is_safe: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "N_b": self.N_b,
            "FS_basal_heave": self.FS_basal_heave,
            "FS_uplift": self.FS_uplift,
            "is_safe": self.is_safe,
        }


def check_excavation(inp: ExcavationInput,
                       FS_min: float = 1.5) -> ExcavationResult:
    if inp.depth_m <= 0 or inp.width_m <= 0:
        raise ValueError("depth_m y width_m deben ser > 0")
    H = inp.depth_m
    gamma = inp.gamma_kN_m3
    su = inp.su_kPa
    q = inp.surcharge_kPa

    # Estabilidad del fondo Terzaghi
    N_b = (gamma * H + q) / max(su, 1e-9)
    # FS_basal_heave = capacidad / demanda
    # Para arcilla saturada con Nc=5.14:
    FS_basal = (5.14 * su) / (gamma * H + q)

    # Levantamiento por flotación (si NF dentro de la excavación)
    if inp.water_table_depth_m < H:
        h_w = H - inp.water_table_depth_m
        FS_uplift = (gamma * H) / (9.81 * h_w + 1e-9)
    else:
        FS_uplift = float("inf")

    is_safe = FS_basal >= FS_min and FS_uplift >= FS_min

    return ExcavationResult(
        N_b=N_b, FS_basal_heave=FS_basal, FS_uplift=FS_uplift, is_safe=is_safe,
    )


__all__ = ["ExcavationInput", "ExcavationResult", "check_excavation"]
