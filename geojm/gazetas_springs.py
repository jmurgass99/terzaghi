"""
Resortes dinámicos de fundación — Gazetas (1991, update 2018) para
zapatas rectangulares en semi-espacio elástico.

Devuelve las 6 rigideces estáticas + dashpots equivalentes:
    Kz, Kx, Ky (traslacionales)
    Krx, Kry, Krz (rotacionales)
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi


@dataclass(frozen=True)
class GazetasInput:
    L_m: float                 # longitud zapata (mayor)
    B_m: float                 # ancho zapata
    Vs_m_per_s: float = 200.0  # velocidad ondas corte del suelo
    rho_soil_kg_m3: float = 1900.0
    nu_soil: float = 0.35


@dataclass(frozen=True)
class GazetasResult:
    Kz_kN_per_m: float
    Kx_kN_per_m: float
    Ky_kN_per_m: float
    Krx_kNm_per_rad: float
    Kry_kNm_per_rad: float
    Krz_kNm_per_rad: float
    G_soil_MPa: float


def evaluate_gazetas(inp: GazetasInput) -> GazetasResult:
    if inp.L_m < inp.B_m:
        raise ValueError("L_m debe ser ≥ B_m (L mayor lado)")
    L, B = inp.L_m, inp.B_m
    G = inp.rho_soil_kg_m3 * inp.Vs_m_per_s ** 2 / 1e6  # MPa
    nu = inp.nu_soil

    # Fórmulas Gazetas (1991) Table 4 — zapata rectangular L > B
    # Kz vertical
    Kz = (G * 1e6 * L) / (1 - nu) * (0.73 + 1.54 * (B / L) ** 0.75) / 1000  # kN/m
    # Kx (parallel to L)
    Kx = (G * 1e6 * L) / (2 - nu) * (2 + 2.5 * (B / L) ** 0.85) / 1000
    # Ky (perpendicular)
    Ky = Kx - (G * 1e6 * L) / (0.75 - nu) * (
        0.1 * (1 - B / L)
    ) / 1000

    # Rotacionales (rocking about long axis y short axis)
    Iy = L * B ** 3 / 12   # rocking about long axis = "Y" → moment about y
    Ix = B * L ** 3 / 12
    Krx = (G * 1e6 * Iy ** 0.75) / (1 - nu) * (
        3.0 * (L / B) ** 0.15
    ) / 1000
    Kry = (G * 1e6 * Ix ** 0.75) / (1 - nu) * (
        3.73 * (L / B) ** 2.4 + 0.27
    ) / 1000
    Krz = (G * 1e6) * ((B ** 2 + L ** 2) * B * L) ** 0.75 * 4.25 / 1000

    return GazetasResult(
        Kz_kN_per_m=Kz, Kx_kN_per_m=Kx, Ky_kN_per_m=Ky,
        Krx_kNm_per_rad=Krx, Kry_kNm_per_rad=Kry, Krz_kNm_per_rad=Krz,
        G_soil_MPa=G,
    )


__all__ = ["GazetasInput", "GazetasResult", "evaluate_gazetas"]
