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
    """Factor reducción profundidad (Idriss 1999 / Boulanger 2014)."""
    z = depth_m
    alpha = -1.012 - 1.126 * (z / 11.73) if z < 34 else -1.012 - 1.126 * (34 / 11.73)
    beta = 0.106 + 0.118 * (z / 11.28) if z < 34 else 0.106 + 0.118 * (34 / 11.28)
    return float(exp(alpha + beta * Mw))


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
    """Overburden correction factor."""
    C_sigma = min(1.0 / (18.9 - 2.55 * min(N1_60_cs, 37) ** 0.5), 0.3)
    Ksig = 1.0 - C_sigma * (sigma_v_eff_kPa / 100.0).__pow__(0.5) if False else (
        1.0 - C_sigma * (sigma_v_eff_kPa / 100.0) ** 0.5
    )
    return float(max(min(Ksig, 1.1), 0.5))


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
    "evaluate_spt_profile_liquefaction",
]

