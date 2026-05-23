"""
Capacidad axial de pilotes — método α (arcilla) y método β (arena).

Q_ult = Q_fuste + Q_punta  (API RP 2A-WSD §6.4; Tomlinson; Das §11).

  Fuste:  arcilla  f_s = α·Su            (α de API, función de Su/σ'v0)
          arena    f_s = β·σ'v = K·tanδ·σ'v
  Punta:  arcilla  q_b = 9·Su
          arena    q_b = N_q·σ'v_base    (acotado a límites prácticos)

Carga admisible:  Q_adm = Q_ult / FS  (FS típico 2.5–3.0 estático), o factores
separados sobre fuste y punta.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Literal

_GAMMA_W = 9.81  # kN/m³


@dataclass(frozen=True)
class SoilLayer:
    top_m: float
    bottom_m: float
    kind: Literal["clay", "sand"]
    gamma_kN_m3: float = 18.0          # peso específico total
    Su_kPa: float = 0.0                # arcilla: resistencia no drenada
    phi_deg: float = 0.0               # arena: ángulo de fricción

    @property
    def thickness(self) -> float:
        return self.bottom_m - self.top_m


@dataclass(frozen=True)
class Pile:
    diameter_m: float
    length_m: float
    water_table_m: float = 0.0          # profundidad del nivel freático (0 = en superficie)
    delta_ratio: float = 0.8            # δ/φ (acero ~0.8, hormigón ~1.0)
    K: float | None = None              # coef. presión lateral; None -> 1-sinφ
    Nq_cap: float = 120.0               # tope de N_q en punta (arena densa)


@dataclass(frozen=True)
class AxialCapacityResult:
    Q_skin_kN: float
    Q_base_kN: float
    Q_ult_kN: float
    Q_allow_kN: float
    FS: float
    per_layer_skin_kN: List[float] = field(default_factory=list)


def api_alpha(Su_kPa: float, sigma_v_eff_kPa: float) -> float:
    """Factor de adhesión α (API RP 2A): función de psi = Su/σ'v0, acotado a 1.0."""
    if sigma_v_eff_kPa <= 0:
        return 0.5
    psi = Su_kPa / sigma_v_eff_kPa
    alpha = 0.5 * psi ** -0.5 if psi <= 1.0 else 0.5 * psi ** -0.25
    return min(alpha, 1.0)


def _sigma_v_eff(depth_m: float, layers: List[SoilLayer], water_table_m: float) -> float:
    """Esfuerzo vertical efectivo σ'v a la profundidad dada (integra γ' por capas)."""
    sv = 0.0
    z = 0.0
    for lay in layers:
        z0 = lay.top_m
        z1 = min(lay.bottom_m, depth_m)
        if z1 <= z0:
            continue
        # Sub-integrar respetando el nivel freático dentro de la capa.
        seg_top, seg_bot = z0, z1
        # Tramo sobre el agua.
        if water_table_m > seg_top:
            dry_bot = min(seg_bot, water_table_m)
            sv += lay.gamma_kN_m3 * (dry_bot - seg_top)
            seg_top = dry_bot
        # Tramo bajo el agua (peso sumergido).
        if seg_bot > seg_top:
            sv += (lay.gamma_kN_m3 - _GAMMA_W) * (seg_bot - seg_top)
        if depth_m <= lay.bottom_m:
            break
    return max(sv, 0.0)


def axial_capacity(pile: Pile, layers: List[SoilLayer], FS: float = 2.5) -> AxialCapacityResult:
    """Capacidad axial a compresión de un pilote en suelo estratificado."""
    perim = math.pi * pile.diameter_m
    area_base = math.pi * pile.diameter_m ** 2 / 4.0

    Q_skin = 0.0
    per_layer: List[float] = []
    for lay in layers:
        top = lay.top_m
        bot = min(lay.bottom_m, pile.length_m)
        if bot <= top:
            per_layer.append(0.0)
            continue
        z_mid = 0.5 * (top + bot)
        sv = _sigma_v_eff(z_mid, layers, pile.water_table_m)
        if lay.kind == "clay":
            fs = api_alpha(lay.Su_kPa, sv) * lay.Su_kPa
        else:  # sand
            phi = math.radians(lay.phi_deg)
            K = pile.K if pile.K is not None else (1.0 - math.sin(phi))
            delta = pile.delta_ratio * phi
            fs = K * math.tan(delta) * sv
        q_layer = fs * perim * (bot - top)
        Q_skin += q_layer
        per_layer.append(q_layer)

    # Punta: capa donde cae la base del pilote.
    base_layer = next((l for l in layers if l.top_m <= pile.length_m <= l.bottom_m), layers[-1])
    if base_layer.kind == "clay":
        q_b = 9.0 * base_layer.Su_kPa
    else:
        sv_base = _sigma_v_eff(pile.length_m, layers, pile.water_table_m)
        phi = math.radians(base_layer.phi_deg)
        Nq = min(math.exp(math.pi * math.tan(phi)) * math.tan(math.pi / 4 + phi / 2) ** 2, pile.Nq_cap)
        q_b = Nq * sv_base
    Q_base = q_b * area_base

    Q_ult = Q_skin + Q_base
    return AxialCapacityResult(
        Q_skin_kN=Q_skin, Q_base_kN=Q_base, Q_ult_kN=Q_ult,
        Q_allow_kN=Q_ult / FS, FS=FS, per_layer_skin_kN=per_layer,
    )


__all__ = ["SoilLayer", "Pile", "AxialCapacityResult", "api_alpha", "axial_capacity"]
