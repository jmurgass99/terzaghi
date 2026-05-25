"""Suite 2.2 — Avance del frente de carbonatación del hormigón.

Modelo de la raíz del tiempo (EN 206, fib Bulletin 34):

    d_c(t) = K_c · √t

donde d_c es la profundidad carbonatada (mm), t el tiempo (años) y K_c el
coeficiente de carbonatación (mm/√año). El coeficiente depende de la
relación agua/cemento, del contenido de ceniza volante y de la humedad
relativa ambiental:

    K_c = K_ref · (w/c / 0.5)² · (1 + 0.01·%cv) · exp[ -((RH-60)/30)² ]

La carbonatación es máxima a humedad relativa intermedia (~60 %): en seco
falta agua para disolver el CO₂ y saturado los poros bloquean su difusión.
La ceniza volante consume hidróxido cálcico (reserva alcalina) y acelera el
frente. La vida útil hasta despasivación es t = (recubrimiento / K_c)².
"""
from __future__ import annotations

import math

K_REF_MM_SQRT_YR = 4.0  # referencia: w/c=0.5, 0% cv, HR=60%


def carbonation_coefficient(w_c: float, fly_ash_pct: float, rh_pct: float) -> float:
    """Coeficiente de carbonatación K_c (mm/√año)."""
    if w_c <= 0:
        raise ValueError("w/c debe ser > 0")
    f_wc = (w_c / 0.5) ** 2
    f_fa = 1.0 + 0.01 * fly_ash_pct
    f_rh = math.exp(-(((rh_pct - 60.0) / 30.0) ** 2))
    return K_REF_MM_SQRT_YR * f_wc * f_fa * f_rh


def carbonation_depth(t_years: float, K_c: float) -> float:
    """Profundidad carbonatada (mm) tras `t_years`."""
    if t_years < 0:
        raise ValueError("t debe ser >= 0")
    return K_c * math.sqrt(t_years)


def time_to_depth(d_mm: float, K_c: float) -> float:
    """Años para que el frente alcance la profundidad `d_mm` (inversa)."""
    if K_c <= 0:
        raise ValueError("K_c debe ser > 0")
    return (d_mm / K_c) ** 2
