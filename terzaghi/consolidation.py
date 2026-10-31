# -*- coding: utf-8 -*-
"""
Consolidación 1-D (Terzaghi) y radial con drenes verticales (Barron/Hansbo).

Módulo creado para anclar los goldens de las fichas del máster W00255
("Precarga", Proyecto y Construcción Geotécnicos UPC) y W00254 ("Precarga
slides", ejemplo aeropuerto El Prat). Implementa exactamente las fórmulas
de esas fichas:

  Terzaghi (vertical):
      Uv ≈ sqrt(4·Tv/π)                    para Uv ≤ 0.60
      Uv = 1 − (8/π²)·exp(−π²·Tv/4)        para Uv > 0.60
      t  = Tv·d²/cv        (d = camino de drenaje: H/2 con drenaje doble)

  Barron 1948 (radial, dren ideal):
      Uh = 1 − exp(−8·Th/F(n));   F(n) = ln(n) − 3/4;   n = D/d_w
      Th = ch·t/D²
      D  = 1.05·l (malla triangular) | 1.13·l (malla cuadrada)

  Hansbo 1981 (radial con smear + resistencia del dren):
      F = ln(n/s) + (kh/ks)·ln(s) − 3/4 + π·z·(2H−z)·kh/qw

  Carrillo 1942 (combinación):
      1 − U = (1 − Uv)·(1 − Uh)

UNIDADES (explícitas en los nombres para evitar bugs de unidades):
    cv, ch  [m²/año]      t [años]      d, D, H, z [m]
    kh      [m/año]       qw [m³/año]   Tv, Th, Uv, Uh, U [adimensional]

Nota: la pareja de ramas de Uv es la aproximación clásica de Terzaghi; en el
cruce Uv≈0.60 (Tv≈0.283) ambas ramas difieren <0.5% (discontinuidad inherente
a la aproximación, documentada en W00255).

Refs: Terzaghi (1943); Barron (1948); Hansbo (1981); Carrillo (1942);
fichas W00254, W00255.
"""
from __future__ import annotations

import math

_8_PI2 = 8.0 / math.pi ** 2       # 0.8105695...
_PI2_4 = math.pi ** 2 / 4.0       # 2.4674011...

# Coeficiente D/l por patrón de malla de drenes (ficha W00255).
_DRAIN_PATTERN_COEF = {"triangular": 1.05, "square": 1.13}


def Uv_terzaghi(Tv: float) -> float:
    """Grado medio de consolidación vertical Uv(Tv) [0..1], Terzaghi 1943.

    Aproximación de dos ramas (ficha W00255): raíz para Uv ≤ 0.60 y
    exponencial (primer término de la serie) para Uv > 0.60.
    """
    if Tv < 0:
        raise ValueError("Tv >= 0")
    u_sqrt = math.sqrt(4.0 * Tv / math.pi)
    if u_sqrt <= 0.60:
        return u_sqrt
    return 1.0 - _8_PI2 * math.exp(-_PI2_4 * Tv)


def Tv_from_Uv(Uv: float) -> float:
    """Factor de tiempo vertical Tv para un grado de consolidación dado.

    Inversa exacta de las dos ramas de ``Uv_terzaghi``.
    Golden W00255: Uv=0.90 -> Tv = 0.848.
    """
    if not 0.0 <= Uv < 1.0:
        raise ValueError("0 <= Uv < 1")
    if Uv <= 0.60:
        return math.pi / 4.0 * Uv ** 2
    return -math.log((1.0 - Uv) / _8_PI2) / _PI2_4


def time_years_vertical(Tv: float, d_drain_m: float, cv_m2_per_year: float) -> float:
    """t = Tv·d²/cv [años]. d = camino de drenaje (H/2 si drenaje doble)."""
    if d_drain_m <= 0 or cv_m2_per_year <= 0:
        raise ValueError("d_drain_m > 0 y cv > 0")
    return Tv * d_drain_m ** 2 / cv_m2_per_year


def Tv_vertical(cv_m2_per_year: float, t_years: float, d_drain_m: float) -> float:
    """Tv = cv·t/d² (adimensional)."""
    if d_drain_m <= 0:
        raise ValueError("d_drain_m > 0")
    return cv_m2_per_year * t_years / d_drain_m ** 2


def drain_influence_diameter_m(spacing_m: float, pattern: str = "triangular") -> float:
    """Diámetro de influencia D del dren: 1.05·l (triangular) | 1.13·l (cuadrada)."""
    try:
        coef = _DRAIN_PATTERN_COEF[pattern]
    except KeyError:
        raise ValueError(f"pattern '{pattern}' no soportado: {sorted(_DRAIN_PATTERN_COEF)}")
    if spacing_m <= 0:
        raise ValueError("spacing_m > 0")
    return coef * spacing_m


def Fn_barron(n: float) -> float:
    """F(n) = ln(n) − 3/4 (Barron 1948, dren ideal). n = D/d_w > 1."""
    if n <= 1.0:
        raise ValueError("n = D/d_w > 1")
    return math.log(n) - 0.75


def Fn_hansbo(n: float, s: float = 1.0, kh_over_ks: float = 1.0,
              z_m: float = 0.0, H_drain_m: float = 0.0,
              kh_m_per_year: float = 0.0,
              qw_m3_per_year: float | None = None) -> float:
    """F de Hansbo 1981 con smear y resistencia del dren.

    F = ln(n/s) + (kh/ks)·ln(s) − 3/4 + π·z·(2H−z)·kh/qw

    s = r_s/r_w (radio smear/radio dren); kh/ks relación de permeabilidades;
    qw capacidad de descarga del dren [m³/año] (None = dren ideal, sin término
    de resistencia). Con s=1 y qw=None colapsa a ``Fn_barron``.
    El término de resistencia es adimensional: [m]·[m]·[m/año]/[m³/año].
    """
    if n <= 1.0 or s < 1.0:
        raise ValueError("n > 1 y s >= 1")
    F = math.log(n / s) + kh_over_ks * math.log(s) - 0.75
    if qw_m3_per_year is not None:
        if qw_m3_per_year <= 0:
            raise ValueError("qw > 0")
        F += math.pi * z_m * (2.0 * H_drain_m - z_m) * kh_m_per_year / qw_m3_per_year
    return F


def Uh_radial(Th: float, Fn: float) -> float:
    """Uh = 1 − exp(−8·Th/F(n)) [0..1] (Barron/Hansbo)."""
    if Th < 0 or Fn <= 0:
        raise ValueError("Th >= 0 y Fn > 0")
    return 1.0 - math.exp(-8.0 * Th / Fn)


def Th_from_Uh(Uh: float, Fn: float) -> float:
    """Th = −F(n)·ln(1−Uh)/8 (inversa de ``Uh_radial``)."""
    if not 0.0 <= Uh < 1.0:
        raise ValueError("0 <= Uh < 1")
    if Fn <= 0:
        raise ValueError("Fn > 0")
    return -Fn * math.log(1.0 - Uh) / 8.0


def time_years_radial(Th: float, D_m: float, ch_m2_per_year: float) -> float:
    """t = Th·D²/ch [años]."""
    if D_m <= 0 or ch_m2_per_year <= 0:
        raise ValueError("D_m > 0 y ch > 0")
    return Th * D_m ** 2 / ch_m2_per_year


def Th_radial(ch_m2_per_year: float, t_years: float, D_m: float) -> float:
    """Th = ch·t/D² (adimensional)."""
    if D_m <= 0:
        raise ValueError("D_m > 0")
    return ch_m2_per_year * t_years / D_m ** 2


def U_combined_carrillo(Uv: float, Uh: float) -> float:
    """Consolidación combinada vertical+radial: 1−U = (1−Uv)·(1−Uh) (Carrillo 1942)."""
    if not (0.0 <= Uv <= 1.0 and 0.0 <= Uh <= 1.0):
        raise ValueError("Uv y Uh en [0, 1]")
    return 1.0 - (1.0 - Uv) * (1.0 - Uh)


__all__ = [
    "Uv_terzaghi", "Tv_from_Uv", "time_years_vertical", "Tv_vertical",
    "drain_influence_diameter_m", "Fn_barron", "Fn_hansbo",
    "Uh_radial", "Th_from_Uh", "time_years_radial", "Th_radial",
    "U_combined_carrillo",
]
