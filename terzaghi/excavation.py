"""
EN 1997-1 §10 / §12 — Estabilidad de excavaciones (Terzaghi-Peck).

Verifica:
    1. Estabilidad del fondo (basal heave) — Terzaghi 1943
    2. Levantamiento por flotación (uplift) del tapón impermeable o columna de suelo
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
    plug_thickness_m: float | None = None  # espesor del tapón impermeable bajo el fondo (EN 1997-1 §10.2)
    piezometric_head_m: float | None = None  # altura piezométrica en la base del tapón
    hydraulic_gradient_i: float | None = None  # gradiente hidráulico de salida para chequeo de sifonamiento


@dataclass(frozen=True)
class ExcavationResult:
    N_b: float                       # factor estabilidad Terzaghi (= (γ·H + q)/su)
    FS_basal_heave: float            # Terzaghi: FS = (5.14·su / (γ·H + q))
    FS_uplift: float                 # contra flotación (uplift)
    is_safe: bool
    FS_piping: float | None = None   # contra sifonamiento i_crit / i

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "N_b": self.N_b,
            "FS_basal_heave": self.FS_basal_heave,
            "FS_uplift": self.FS_uplift,
            "is_safe": self.is_safe,
        }
        if self.FS_piping is not None:
            d["FS_piping"] = self.FS_piping
        return d


def check_excavation(inp: ExcavationInput,
                       FS_min: float = 1.5) -> ExcavationResult:
    if inp.depth_m <= 0 or inp.width_m <= 0:
        raise ValueError("depth_m y width_m deben ser > 0")
    H = inp.depth_m
    gamma = inp.gamma_kN_m3
    su = inp.su_kPa
    q = inp.surcharge_kPa
    gamma_w = 9.81

    # 1. Estabilidad del fondo Terzaghi
    N_b = (gamma * H + q) / max(su, 1e-9)
    FS_basal = (5.14 * su) / (gamma * H + q)

    # 2. Levantamiento por flotación (EN 1997-1 §10.2)
    if inp.plug_thickness_m is not None:
        if inp.plug_thickness_m <= 0:
            raise ValueError("plug_thickness_m debe ser > 0")
        T_plug = inp.plug_thickness_m
        if inp.piezometric_head_m is not None:
            h_w = max(inp.piezometric_head_m, 0.0)
        else:
            # Nivel freático medido desde la superficie original: la base del tapón está a z = H + T_plug
            h_w = max((H + T_plug) - inp.water_table_depth_m, 0.0)
        FS_uplift = (gamma * T_plug) / (gamma_w * h_w) if h_w > 0 else float("inf")
    elif inp.water_table_depth_m < H:
        h_w = H - inp.water_table_depth_m
        FS_uplift = (gamma * H) / (gamma_w * h_w + 1e-9)
    else:
        FS_uplift = float("inf")

    # 3. Sifonamiento (piping) si se proporciona gradiente hidráulico de salida
    FS_piping: float | None = None
    piping_ok = True
    if inp.hydraulic_gradient_i is not None:
        if inp.hydraulic_gradient_i < 0:
            raise ValueError("hydraulic_gradient_i debe ser >= 0")
        i_crit = max((gamma - gamma_w) / gamma_w, 0.0)
        FS_piping = i_crit / inp.hydraulic_gradient_i if inp.hydraulic_gradient_i > 0 else float("inf")
        piping_ok = FS_piping >= FS_min

    is_safe = FS_basal >= FS_min and FS_uplift >= FS_min and piping_ok

    return ExcavationResult(
        N_b=N_b,
        FS_basal_heave=FS_basal,
        FS_uplift=FS_uplift,
        is_safe=is_safe,
        FS_piping=FS_piping,
    )


__all__ = ["ExcavationInput", "ExcavationResult", "check_excavation"]
