"""
Capacidad portante de zapatas — formulación multi-código.

Modelos:
    Terzaghi (1943)        — base original, todos los códigos
    Meyerhof (1963)        — factores de forma
    Vesic (1973)           — factores compresibilidad
    Brinch Hansen (1970)   — EN 1997, NSR-10 referencia

Códigos cubiertos (factores parciales):
    EU/SG: EN 1997-1 §6.5.2 + Annex D (γ_R,v = 1.4 R3, γ_φ = 1.25, γ_c = 1.4)
    US:    ACI 318 / AASHTO LRFD §10.6 (φ = 0.45 a 0.55)
    CO:    NSR-10 §H.4.7 (FS ≥ 3 estático, FS ≥ 2 sísmico)
    AU:    AS 5100.3 / Foundation Code AS 2159 (φ = 0.40–0.70 según método)
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, pi, radians, tan
from typing import Any, Literal


@dataclass(frozen=True)
class BearingCapacityInput:
    B_m: float                          # ancho zapata
    L_m: float                          # largo
    D_f_m: float                        # profundidad desplante
    phi_deg: float                      # ángulo fricción
    c_kPa: float = 0.0                  # cohesión
    gamma_kN_m3: float = 18.0
    method: Literal["terzaghi", "meyerhof", "vesic", "brinch_hansen"] = "vesic"


@dataclass(frozen=True)
class BearingCapacityResult:
    q_ult_kPa: float                    # capacidad última
    q_adm_kPa: float                    # con FS o γ_R aplicado
    Nc: float
    Nq: float
    Ngamma: float
    code_applied: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "q_ult_kPa": self.q_ult_kPa, "q_adm_kPa": self.q_adm_kPa,
            "Nc": self.Nc, "Nq": self.Nq, "Ngamma": self.Ngamma,
            "code_applied": self.code_applied,
        }


def _bearing_factors(phi_deg: float, method: str
                       ) -> tuple[float, float, float]:
    phi = radians(phi_deg)
    Nq = exp(pi * tan(phi)) * (tan(pi / 4 + phi / 2)) ** 2
    Nc = (Nq - 1) / max(tan(phi), 1e-9) if phi_deg > 0 else 5.14
    if method == "terzaghi":
        Ngamma = (Nq - 1) * tan(1.4 * phi)
    elif method == "meyerhof":
        Ngamma = (Nq - 1) * tan(1.4 * phi)
    elif method == "vesic":
        Ngamma = 2 * (Nq + 1) * tan(phi)
    elif method == "brinch_hansen":
        Ngamma = 1.5 * (Nq - 1) * tan(phi)
    else:
        raise ValueError(f"método '{method}' no soportado")
    return Nc, Nq, Ngamma


def evaluate_bearing(inp: BearingCapacityInput, code: str = "EU"
                      ) -> BearingCapacityResult:
    """Calcula q_ult y aplica el factor parcial/FS del código."""
    Nc, Nq, Ngamma = _bearing_factors(inp.phi_deg, inp.method)

    # Factores de forma simplificados (Meyerhof / Vesic)
    sB_L = inp.B_m / inp.L_m if inp.L_m > 0 else 1.0
    Sc = 1 + 0.2 * sB_L
    Sq = 1 + 0.1 * sB_L
    Sgamma = 1 - 0.1 * sB_L

    q = inp.gamma_kN_m3 * inp.D_f_m  # sobrecarga
    q_ult = (
        inp.c_kPa * Nc * Sc
        + q * Nq * Sq
        + 0.5 * inp.gamma_kN_m3 * inp.B_m * Ngamma * Sgamma
    )

    # Aplicar factor por código
    if code in ("EU", "SG"):
        q_adm = q_ult / 1.40        # γ_R,v = 1.4 (R3 EC7)
    elif code == "US":
        q_adm = 0.50 * q_ult         # φ ≈ 0.50 (AASHTO LRFD)
    elif code == "CO":
        q_adm = q_ult / 3.0          # FS = 3 (NSR-10 estático)
    elif code == "AU":
        q_adm = 0.45 * q_ult         # AS 2159 método Brinch Hansen
    else:
        raise ValueError(f"código '{code}' no soportado")

    return BearingCapacityResult(
        q_ult_kPa=q_ult, q_adm_kPa=q_adm,
        Nc=Nc, Nq=Nq, Ngamma=Ngamma, code_applied=code,
    )


__all__ = ["BearingCapacityInput", "BearingCapacityResult", "evaluate_bearing"]
