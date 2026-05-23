"""
Correlaciones SPT ↔ CPT ↔ parámetros geotécnicos.

Basado en:
    Robertson & Cabal (2014) — CPT Guide
    Skempton (1986) — SPT corrections
    Bowles (1997) — correlaciones empíricas
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log10


@dataclass(frozen=True)
class SoilSample:
    depth_m: float
    N_SPT: float | None = None
    qc_MPa: float | None = None
    fs_kPa: float | None = None
    sigma_v_eff_kPa: float = 100.0


def N60_corrected(N_field: float, energy_ratio: float = 0.60,
                    overburden_kPa: float | None = None) -> float:
    """N1_60 (Skempton). Energy correction → 60%, then overburden."""
    N60 = N_field * (energy_ratio / 0.60)
    if overburden_kPa is None:
        return N60
    Cn = min((100.0 / max(overburden_kPa, 1.0)) ** 0.5, 2.0)
    return N60 * Cn


def qc_from_N(N60: float, soil_type: str = "sand") -> float:
    """qc (MPa) ≈ k·N60. Robertson & Wride 1998."""
    k = {"sand": 0.5, "silty_sand": 0.35, "clay": 0.2}.get(soil_type, 0.4)
    return k * N60


def N_from_qc(qc_MPa: float, soil_type: str = "sand") -> float:
    k = {"sand": 0.5, "silty_sand": 0.35, "clay": 0.2}.get(soil_type, 0.4)
    return qc_MPa / max(k, 1e-6)


def phi_from_N(N1_60: float) -> float:
    """Hatanaka & Uchida (1996) — ángulo fricción interno (°)."""
    if N1_60 <= 0:
        return 0.0
    return (15.4 * N1_60) ** 0.5 + 20.0


def Su_from_qc(qc_MPa: float, sigma_v_kPa: float = 0,
                Nk: float = 15.0) -> float:
    """Su (kPa) ≈ (qc - σv) / Nk para arcillas."""
    qc_kPa = qc_MPa * 1000.0
    return max((qc_kPa - sigma_v_kPa) / Nk, 0.0)


def Es_from_N(N60: float, soil_type: str = "sand") -> float:
    """Módulo de Young drenado (MPa). Bowles 1997."""
    if soil_type == "sand":
        return 0.5 * N60 + 7.0
    if soil_type == "clay":
        return 0.4 * N60 + 2.0
    return 0.4 * N60 + 5.0


__all__ = [
    "SoilSample", "N60_corrected",
    "qc_from_N", "N_from_qc",
    "phi_from_N", "Su_from_qc", "Es_from_N",
]
