"""
Evaluación de potencial de licuación — Boulanger & Idriss (2014).

Variables clave:
    CSR = 0.65 · (σ_v/σ'_v) · a_max/g · r_d
    CRR = f(N1_60_cs)                              [Idriss-Boulanger 2014]
    FS = CRR · MSF · K_σ / CSR

donde:
    N1_60_cs : SPT corregido a sismología, energía 60% y fino-equivalente.
    MSF : factor de magnitud (escala a Mw=7.5)
    K_σ : factor de presión de confinamiento
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Any

from .boulanger_idriss import (
    BoulangerIdrissInput,
    BoulangerIdrissResult,
    ProfileLiquefactionResult,
    _k_sigma_bi2014,
    _rd_bi2014,
    evaluate_bi2014,
    evaluate_spt_profile_liquefaction,
)


@dataclass(frozen=True)
class LiquefactionInput:
    depth_m: float
    sigma_v_kPa: float       # esfuerzo vertical total
    sigma_v_eff_kPa: float   # esfuerzo vertical efectivo
    N1_60_cs: float          # SPT corregido + fino-equivalente
    a_max_g: float           # PGA (g)
    Mw: float = 7.5          # magnitud de momento


@dataclass(frozen=True)
class LiquefactionResult:
    CSR: float
    CRR: float
    MSF: float
    K_sigma: float
    FS: float
    is_safe: bool             # FS ≥ 1.2

    def to_dict(self) -> dict[str, Any]:
        return {
            "CSR": self.CSR, "CRR": self.CRR,
            "MSF": self.MSF, "K_sigma": self.K_sigma,
            "FS": self.FS, "is_safe": self.is_safe,
        }


def _r_d(depth_m: float, Mw: float) -> float:
    """Factor de reducción por profundidad r_d = exp(α(z) + β(z)·M), Idriss (1999) /
    Boulanger & Idriss (2014) ec. 6–8, con α(z) = −1,012 − 1,126·sin(z/11,73 + 5,133) y
    β(z) = 0,106 + 0,118·sin(z/11,28 + 5,142).

    Hasta la 1.1.0 esta vía omitía los senos (α = −1,012 − 1,126·z/11,73, …): a 5 m daba
    r_d = 0,74 en vez de 0,96 y a 10 m 0,61 en vez de 0,86, con lo que la demanda CSR
    salía un 20–30 % baja. Ahora delega en ``boulanger_idriss._rd_bi2014``.
    """
    return float(_rd_bi2014(depth_m, Mw))


def _CRR(N1_60_cs: float) -> float:
    """CRR a Mw=7.5, σ'v=100kPa — Idriss & Boulanger 2014 Eq. 70."""
    N = min(N1_60_cs, 37.0)
    return float(exp(
        N / 14.1
        + (N / 126.0) ** 2
        - (N / 23.6) ** 3
        + (N / 25.4) ** 4
        - 2.8
    ))


def _MSF(Mw: float, N1_60_cs: float) -> float:
    """Magnitude Scaling Factor — Boulanger & Idriss 2014."""
    MSF_max = 1.09 + (N1_60_cs / 31.5) ** 2
    MSF_max = min(MSF_max, 2.2)
    msf_raw = 1.0 + (MSF_max - 1.0) * (8.64 * exp(-Mw / 4.0) - 1.325)
    return float(min(msf_raw, MSF_max))  # No lower clamp: MSF < 1.0 is physically valid for Mw > 7.5


def _K_sigma(sigma_v_eff_kPa: float, N1_60_cs: float) -> float:
    """Factor de sobrecarga K_σ = 1 − C_σ·ln(σ'_v/P_a) ≤ 1,1 (B&I 2014 ec. 11/51).

    Hasta la 1.1.0 esta vía usaba 1 − C_σ·√(σ'_v/100): valía 0,89 en vez de 1,0 a
    100 kPa y 0,92 en vez de 1,08 a 50 kPa. Ahora delega en
    ``boulanger_idriss._k_sigma_bi2014``.
    """
    return float(_k_sigma_bi2014(sigma_v_eff_kPa, N1_60_cs))


def evaluate_liquefaction(inp: LiquefactionInput,
                            fs_threshold: float = 1.2
                            ) -> LiquefactionResult:
    if inp.sigma_v_eff_kPa <= 0:
        raise ValueError("sigma_v_eff_kPa debe ser > 0")
    rd = _r_d(inp.depth_m, inp.Mw)
    CSR = 0.65 * (inp.sigma_v_kPa / inp.sigma_v_eff_kPa) * inp.a_max_g * rd
    CRR = _CRR(inp.N1_60_cs)
    Mw_val = inp.Mw
    MSF = _MSF(Mw_val, inp.N1_60_cs)
    K_sigma = _K_sigma(inp.sigma_v_eff_kPa, inp.N1_60_cs)
    FS = (CRR * MSF * K_sigma) / max(CSR, 1e-9)
    return LiquefactionResult(
        CSR=CSR, CRR=CRR, MSF=MSF, K_sigma=K_sigma,
        FS=FS, is_safe=FS >= fs_threshold,
    )


__all__ = [
    "LiquefactionInput",
    "LiquefactionResult",
    "evaluate_liquefaction",
    "BoulangerIdrissInput",
    "BoulangerIdrissResult",
    "ProfileLiquefactionResult",
    "evaluate_bi2014",
    "evaluate_spt_profile_liquefaction",
]

