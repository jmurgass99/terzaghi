"""
Curvas P-y para pilotes sometidos a carga lateral.

- Matlock (1970) — arcilla blanda saturada
- Reese, Cox & Koop (1974) — arena (forma hiperbólica simplificada)

Cada función retorna ``(p_kN_per_m, y_m)`` para usarse como spring no
lineal en SAP/ETABS vía OAPI.
"""
from __future__ import annotations

import numpy as np


def py_matlock_soft_clay(z_m: float, D_m: float, su_kPa: float,
                          gamma_kN_m3: float = 17.0,
                          eps_50: float = 0.02,
                          n_points: int = 50
                          ) -> tuple[np.ndarray, np.ndarray]:
    """Curva P-y de Matlock 1970 (arcilla blanda).

    ``p_ult = min(3 + γ'·z/su + J·z/D, 9) · su · D`` con J=0.5.
    ``y_50 = 2.5·ε_50·D``.
    Tramo cúbico ``p/p_ult = 0.5·(y/y_50)^(1/3)`` hasta ``y=8·y_50`` y luego
    constante ``p = p_ult``.

    Args:
        z_m: profundidad bajo la superficie [m].
        D_m: diámetro del pilote [m].
        su_kPa: resistencia al corte no drenada [kPa].
        gamma_kN_m3: peso específico efectivo del suelo.
        eps_50: deformación al 50% de la resistencia (Matlock 0.02 default).
    """
    J = 0.5
    factor = 3.0 + gamma_kN_m3 * z_m / max(su_kPa, 1e-9) + J * z_m / D_m
    factor = min(factor, 9.0)
    p_ult = factor * su_kPa * D_m  # kN/m

    y_50 = 2.5 * eps_50 * D_m
    y_max = 16.0 * y_50

    y = np.linspace(0.0, y_max, n_points)
    p = np.where(y < 8.0 * y_50,
                 0.5 * p_ult * np.cbrt(y / y_50),
                 p_ult)
    p = np.minimum(p, p_ult)
    return p, y


def py_reese_sand(z_m: float, D_m: float, phi_deg: float,
                   gamma_kN_m3: float = 18.0,
                   k_pH_kN_m3: float = 25_000.0,
                   n_points: int = 50
                   ) -> tuple[np.ndarray, np.ndarray]:
    """Curva P-y simplificada (forma hiperbólica) para arena.

    Implementación abreviada del modelo Reese-Cox-Koop:
    ``p_ult = (Kp² - Ka) · γ·z · D`` (componente de cuña) con un
    máximo de fricción profundo ``Kp·γ·z·D`` — usamos el menor.
    Rigidez inicial ``k = k_pH · z`` (Terzaghi).

    Args:
        z_m, D_m: profundidad y diámetro del pilote [m].
        phi_deg: ángulo de fricción interna [°].
        gamma_kN_m3: peso específico efectivo.
        k_pH_kN_m3: módulo de balasto horizontal (Terzaghi).
    """
    phi = np.radians(phi_deg)
    Kp = (1.0 + np.sin(phi)) / (1.0 - np.sin(phi))
    Ka = 1.0 / Kp
    p_ult_wedge = (Kp ** 2 - Ka) * gamma_kN_m3 * z_m * D_m
    p_ult_deep = Kp * gamma_kN_m3 * z_m * D_m
    p_ult = min(p_ult_wedge, p_ult_deep)
    if p_ult <= 0:
        p_ult = 1e-6

    k_init = k_pH_kN_m3 * max(z_m, 1e-3)
    y_ref = p_ult / k_init
    y_max = 10.0 * y_ref

    y = np.linspace(0.0, y_max, n_points)
    # Forma hiperbólica: p = k_init · y / (1 + y/y_ref)
    p = (k_init * y) / (1.0 + y / y_ref)
    return p, y


__all__ = ["py_matlock_soft_clay", "py_reese_sand"]
