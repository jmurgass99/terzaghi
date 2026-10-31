"""Mecanica de suelos no saturados - van Genuchten + Bishop.

van Genuchten (1980): theta(psi) = theta_r + (theta_s - theta_r) / [1 + (alpha*psi)^n]^m
Bishop (1959): tau = c' + (sigma - u_a + chi*(u_a - u_w)) * tan(phi')
"""
from __future__ import annotations

from dataclasses import dataclass
from math import tan, radians


@dataclass(frozen=True)
class VanGenuchtenParams:
    theta_r: float = 0.05
    theta_s: float = 0.45
    alpha_1_m: float = 1.0      # 1/m
    n: float = 2.0
    code: str = "EU"

    @property
    def m(self) -> float:
        return 1.0 - 1.0 / self.n


def theta_of_psi(psi_m: float, p: VanGenuchtenParams) -> float:
    if psi_m <= 0:
        return p.theta_s
    Se = (1.0 + (p.alpha_1_m * psi_m) ** p.n) ** (-p.m)
    return p.theta_r + (p.theta_s - p.theta_r) * Se


def chi_bishop(psi_m: float, p: VanGenuchtenParams) -> float:
    """Parametro chi de Bishop ~ grado de saturacion efectivo."""
    theta = theta_of_psi(psi_m, p)
    return (theta - p.theta_r) / (p.theta_s - p.theta_r)


def shear_strength_unsat(
    sigma_kPa: float,
    u_a_kPa: float,
    u_w_kPa: float,
    psi_m: float,
    c_kPa: float,
    phi_deg: float,
    vg: VanGenuchtenParams,
) -> float:
    chi = chi_bishop(psi_m, vg)
    sigma_eff = sigma_kPa - u_a_kPa + chi * (u_a_kPa - u_w_kPa)
    return c_kPa + sigma_eff * tan(radians(phi_deg))


__all__ = ["VanGenuchtenParams", "theta_of_psi", "chi_bishop", "shear_strength_unsat"]
