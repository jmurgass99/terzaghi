"""
Correcciones de capacidad portante por carga inclinada y excéntrica.

ESTADO: MÓDULO SUPERADO / SHIM DE RETROCOMPATIBILIDAD.
La formulación canónica de capacidad portante de cimentación superficial del monorepo
es ``foundationdesignjm.analysis.bearing_capacity`` (EN 1997-1:2004 Anexo D), que integra
tanto el área efectiva de Meyerhof como los factores de inclinación de Vesic / EC7
directamente dentro de la ecuación analítica global.

Este módulo se conserva como shim para no romper consumidores legacy.
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass


@dataclass(frozen=True)
class EffectiveArea:
    B_eff_m: float
    L_eff_m: float

    @property
    def area_m2(self) -> float:
        return self.B_eff_m * self.L_eff_m


def effective_dimensions(B_m: float, L_m: float, e_B_m: float = 0.0, e_L_m: float = 0.0) -> EffectiveArea:
    """Área efectiva de Meyerhof: B' = B−2e_B, L' = L−2e_L (recorta la excentricidad).

    DEPRECADO: Usar directamente foundationdesignjm.analysis.bearing_capacity.
    """
    warnings.warn(
        "geojm.bearing_inclination.effective_dimensions está deprecada. "
        "La canónica foundationdesignjm.analysis.bearing_capacity incorpora "
        "las dimensiones efectivas e_x, e_y automáticamente.",
        DeprecationWarning,
        stacklevel=2,
    )
    B_eff = max(B_m - 2.0 * abs(e_B_m), 0.0)
    L_eff = max(L_m - 2.0 * abs(e_L_m), 0.0)
    return EffectiveArea(B_eff, L_eff)


def inclination_factors(V_kN: float, H_kN: float, c_kPa: float, phi_deg: float,
                        B_eff_m: float, L_eff_m: float) -> tuple[float, float, float]:
    """Factores de inclinación i_c, i_q, i_γ (Vesic / EN 1997 Anexo D).

    DEPRECADO: Usar directamente foundationdesignjm.analysis.bearing_capacity.
    """
    warnings.warn(
        "geojm.bearing_inclination.inclination_factors está deprecada. "
        "La canónica foundationdesignjm.analysis.bearing_capacity calcula "
        "los factores de inclinación EN 1997-1 Anexo D directamente.",
        DeprecationWarning,
        stacklevel=2,
    )
    if H_kN <= 0 or V_kN <= 0:
        return 1.0, 1.0, 1.0
    phi = math.radians(phi_deg)
    # Exponente m (carga en dirección B): m = (2 + B/L)/(1 + B/L).
    ratio = B_eff_m / L_eff_m if L_eff_m > 0 else 1.0
    m = (2.0 + ratio) / (1.0 + ratio)
    Ca = c_kPa * B_eff_m * L_eff_m  # adhesión total en la base (cohesión × área)
    denom = V_kN + Ca / max(math.tan(phi), 1e-9) if phi_deg > 0 else V_kN
    iq = (1.0 - H_kN / denom) ** m if denom > 0 else 0.0
    iq = max(iq, 0.0)
    igamma = (1.0 - H_kN / denom) ** (m + 1.0) if denom > 0 else 0.0
    igamma = max(igamma, 0.0)
    if phi_deg > 0:
        Nq = math.exp(math.pi * math.tan(phi)) * math.tan(math.pi / 4 + phi / 2) ** 2
        ic = iq - (1.0 - iq) / (Nq - 1.0)
    else:
        # phi = 0 (arcilla no drenada): i_c = 1 − m·H/(B'·L'·c)
        ic = 1.0 - m * H_kN / (B_eff_m * L_eff_m * c_kPa) if c_kPa > 0 else 1.0
    return max(ic, 0.0), iq, igamma


__all__ = ["EffectiveArea", "effective_dimensions", "inclination_factors"]

