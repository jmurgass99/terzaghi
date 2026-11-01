"""
Modelo de Mander, Priestley & Park (1988) — hormigón confinado por
estribos rectangulares. Genera la curva σ-ε y los puntos clave para
inyección como material no-lineal en ETABS/SAP (PMM hinges, fiber
sections, pushover).

Ref: Mander, J.B., Priestley, M.J.N., Park, R. — "Theoretical
Stress-Strain Model for Confined Concrete", J. Struct. Eng. ASCE 114(8).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

import numpy as np


@dataclass(frozen=True)
class MaterialResult:
    fcc_MPa: float       # resistencia confinada pico
    eps_cc: float        # deformación a fcc
    eps_cu: float        # deformación última (rotura del estribo)
    K_confinement: float # factor fcc/fc'
    sigma_eps: list[tuple[float, float]]  # curva σ-ε muestreada

    def to_dict(self) -> dict:
        return {
            "fcc_MPa": self.fcc_MPa, "eps_cc": self.eps_cc,
            "eps_cu": self.eps_cu, "K_confinement": self.K_confinement,
            "sigma_eps": self.sigma_eps,
        }


def _confining_pressure_rect(rho_x: float, rho_y: float,
                              fyh: float, b_core: float, h_core: float,
                              s_mm: float, s_prime_mm: float,
                              n_long_bars: int, w_prime_mm: float
                              ) -> tuple[float, float]:
    """Presiones de confinamiento f_lx, f_ly tras el factor ke (Mander)."""
    A_core = b_core * h_core
    # Coeficiente de efectividad de confinamiento (Mander 1988 Eq. 16)
    sum_wi2 = n_long_bars * w_prime_mm ** 2
    ke_num = (1.0 - sum_wi2 / (6.0 * A_core)) * \
              (1.0 - s_prime_mm / (2.0 * b_core)) * \
              (1.0 - s_prime_mm / (2.0 * h_core))
    ke = ke_num / max(1.0 - 0.0, 1e-6)  # divisor depende de ρ_cc — se simplifica
    ke = max(min(ke, 1.0), 0.0)
    f_lx = ke * rho_x * fyh
    f_ly = ke * rho_y * fyh
    return f_lx, f_ly


def mander_confined_concrete(
    fc: float,                  # f'c [MPa]
    fyh: float,                 # fy del estribo [MPa]
    rho_x: float,               # cuantía volumétrica eje X (Asx / (s·h_core))
    rho_y: float,               # cuantía volumétrica eje Y (Asy / (s·b_core))
    b_core_mm: float,           # ancho del núcleo (medido al CL del estribo)
    h_core_mm: float,           # alto del núcleo
    s_mm: float,                # separación de estribos (centros) [mm]
    s_prime_mm: float | None = None,  # luz libre entre estribos
    n_long_bars: int = 8,       # número de barras longitudinales arriostradas
    w_prime_mm: float = 100.0,  # distancia libre entre barras longitudinales
    eps_su: float = 0.10,       # rotura del acero del estribo
    n_curve_points: int = 30,
) -> MaterialResult:
    """Genera (fcc, ε_cc, ε_cu) y curva σ-ε de Mander 1988."""
    if fc <= 0 or fyh <= 0:
        raise ValueError("fc y fyh deben ser > 0")
    s_prime = s_prime_mm if s_prime_mm is not None else 0.8 * s_mm

    f_lx, f_ly = _confining_pressure_rect(
        rho_x, rho_y, fyh, b_core_mm, h_core_mm,
        s_mm, s_prime, n_long_bars, w_prime_mm,
    )

    # Promedio de presiones (sección rectangular — Mander §3)
    fl_min = min(f_lx, f_ly)
    fl_max = max(f_lx, f_ly)
    # Resistencia confinada, Mander et al. (1988) ec. 7 (confinamiento igual, f_l = f_l,min):
    #     f'cc/f'co = −1,254 + 2,254·√(1 + 7,94·f'l/f'co) − 2·f'l/f'co
    # Hasta la 1.1.0 la expresión llevaba un «1,0 +» de más (1 + 2,254·√(…) − 2x − 1,254),
    # de modo que K salía exactamente 1,0 por encima del valor de la fuente: con 1 % de
    # cuantía en cada dirección y f'c = 30 MPa devolvía K = 2,58 (f'cc = 77 MPa) donde
    # Mander da 1,58 (47 MPa). El límite sin confinar (f_l → 0) debe ser K = 1.
    K = (-1.254 + 2.254 * sqrt(1.0 + 7.94 * fl_min / fc) - 2.0 * fl_min / fc) if fl_min > 0 else 1.0
    K = max(K, 1.0)
    fcc = K * fc
    eps_c0 = 0.002
    eps_cc = eps_c0 * (1.0 + 5.0 * (K - 1.0))

    # Deformación última (Mander Eq. 33)
    rho_s = rho_x + rho_y
    eps_cu = 0.004 + 1.4 * rho_s * fyh * eps_su / fcc

    # Curva σ-ε de Popovics: σ = f'cc·x·r/(r − 1 + x^r), x = ε/ε_cc,
    # r = E_c/(E_c − E_sec) con E_c = 5000·√f'c (MPa) y E_sec = f'cc/ε_cc (Mander ec. 3–6).
    # Hasta la 1.1.0 se usaba r = 5/(K − 1): para K = 1,6 daba r = 8 (rama descendente
    # casi vertical) y para hormigón sin confinar r → ∞ (σ caía a cero tras el pico).
    eps = np.linspace(0.0, eps_cu, n_curve_points)
    Ec = 5000.0 * sqrt(fc)
    Esec = fcc / eps_cc
    r = Ec / max(Ec - Esec, 1e-9)
    x = eps / eps_cc
    sigma = (fcc * x * r) / (r - 1.0 + np.where(x > 0, x ** r, 0.0))
    curve = list(zip(eps.tolist(), sigma.tolist()))

    return MaterialResult(
        fcc_MPa=fcc, eps_cc=eps_cc, eps_cu=eps_cu,
        K_confinement=K, sigma_eps=curve,
    )


__all__ = ["MaterialResult", "mander_confined_concrete"]
