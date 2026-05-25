"""Suite 2.1 — Difusión de cloruros en el hormigón (2ª ley de Fick).

Solución de la ecuación de difusión unidimensional con concentración
superficial constante (EN 206, ACI 365.1R, fib Model Code):

    C(x, t) = C0 + (Cs - C0) · [1 - erf( x / (2·√(D·t)) )]

donde
    C0  = contenido inicial de cloruros en la masa (% peso de cemento),
    Cs  = concentración superficial (% peso de cemento),
    D   = coeficiente de difusión aparente (mm²/año),
    x   = profundidad (mm),  t = tiempo (años).

La iniciación de la corrosión se alcanza cuando, a la profundidad del
recubrimiento, C(x_rec, t) iguala el umbral crítico C_crit.

Sólo usa `math.erf` (stdlib); la inversa se obtiene por bisección para
no depender de scipy.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ChlorideInput:
    Cs_pct: float            # concentración superficial (% peso cemento)
    C0_pct: float            # contenido inicial
    D_mm2_per_year: float    # difusividad aparente (mm²/año)
    cover_mm: float          # recubrimiento de la armadura (mm)
    C_crit_pct: float        # umbral crítico de despasivación

    def __post_init__(self) -> None:
        if self.D_mm2_per_year <= 0:
            raise ValueError("D debe ser > 0")
        if self.cover_mm < 0:
            raise ValueError("recubrimiento debe ser >= 0")


def concentration(x_mm: float, t_years: float, inp: ChlorideInput) -> float:
    """Concentración de cloruros a profundidad `x_mm` y tiempo `t_years`."""
    if t_years <= 0:
        return inp.C0_pct
    arg = x_mm / (2.0 * math.sqrt(inp.D_mm2_per_year * t_years))
    return inp.C0_pct + (inp.Cs_pct - inp.C0_pct) * (1.0 - math.erf(arg))


def _erf_inv(y: float) -> float:
    """Inversa de erf en [0, 1) por bisección (monótona creciente)."""
    if y <= 0.0:
        return 0.0
    if y >= 1.0:
        return math.inf
    lo, hi = 0.0, 6.0  # erf(6) ≈ 1 - 2e-17
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if math.erf(mid) < y:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def time_to_initiation(inp: ChlorideInput) -> float:
    """Años hasta que C en el recubrimiento alcanza el umbral crítico.

    Invierte la ley de Fick:
        (Cs - C_crit)/(Cs - C0) = erf( x / (2√(D·t)) )
        t = x² / (4·D·[erf⁻¹(·)]²)

    Devuelve `math.inf` si el umbral nunca se alcanza (C_crit ≥ Cs).
    """
    denom = inp.Cs_pct - inp.C0_pct
    if denom <= 0:
        return math.inf
    ratio = (inp.Cs_pct - inp.C_crit_pct) / denom
    if ratio <= 0.0:        # C_crit >= Cs: nunca se alcanza
        return math.inf
    if ratio >= 1.0:        # C_crit <= C0: ya iniciado
        return 0.0
    beta = _erf_inv(ratio)
    return inp.cover_mm ** 2 / (4.0 * inp.D_mm2_per_year * beta ** 2)
