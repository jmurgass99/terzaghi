# -*- coding: utf-8 -*-
"""Mander, Priestley y Park (1988): K = f'cc/f'co de la ec. 7 y exponente r de Popovics.

Hasta la 1.1.0 la expresión de K llevaba un «1,0 +» de más (K exactamente 1,0 por encima
de la fuente: 2,58 en vez de 1,58 para 1 % de cuantía y f'c = 30 MPa) y r = 5/(K − 1) en vez
de E_c/(E_c − E_sec).

Desarrollo a mano del caso de referencia (f'c = 30, f_yh = 420, ρ_x = ρ_y = 0,01,
núcleo 400 × 400, s = 100, s' = 80, 8 barras, w' = 100 mm):
    Σw'² = 8·100² = 80 000 ; A_c = 160 000 ; (1 − 80 000/(6·160 000)) = 0,91667
    (1 − 80/800)² = 0,81  →  k_e = 0,74250
    f_l = k_e·ρ·f_yh = 0,7425·0,01·420 = 3,1185 MPa ; x = f_l/f'c = 0,10395
    K = −1,254 + 2,254·√(1 + 7,94·0,10395) − 2·0,10395 = −1,254 + 3,0458 − 0,2079 = 1,5839
"""
from __future__ import annotations

import math

import pytest

from terzaghi.materials import mander_confined_concrete


def _ref():
    return mander_confined_concrete(fc=30.0, fyh=420.0, rho_x=0.01, rho_y=0.01,
                                    b_core_mm=400.0, h_core_mm=400.0, s_mm=100.0)


def test_K_matches_hand_calculation():
    r = _ref()
    ke = (1.0 - 80000.0 / (6.0 * 160000.0)) * (1.0 - 80.0 / 800.0) ** 2
    fl = ke * 0.01 * 420.0
    x = fl / 30.0
    K = -1.254 + 2.254 * math.sqrt(1.0 + 7.94 * x) - 2.0 * x
    assert K == pytest.approx(1.5839, abs=2e-3)
    assert r.K_confinement == pytest.approx(K, rel=1e-9)
    assert r.fcc_MPa == pytest.approx(30.0 * K, rel=1e-9)
    assert r.eps_cc == pytest.approx(0.002 * (1.0 + 5.0 * (K - 1.0)), rel=1e-9)


def test_unconfined_limit_is_K_one_and_curve_peaks_at_eps_cc():
    r0 = mander_confined_concrete(fc=30.0, fyh=420.0, rho_x=1e-9, rho_y=1e-9,
                                  b_core_mm=400.0, h_core_mm=400.0, s_mm=100.0)
    assert r0.K_confinement == pytest.approx(1.0, abs=1e-6)
    assert r0.fcc_MPa == pytest.approx(30.0, rel=1e-6)
    r = _ref()
    eps, sig = zip(*r.sigma_eps)
    i_peak = max(range(len(sig)), key=lambda i: sig[i])
    assert max(sig) == pytest.approx(r.fcc_MPa, rel=0.02)
    assert abs(eps[i_peak] - r.eps_cc) <= (eps[1] - eps[0]) * 1.01
    # r de Popovics: Ec = 5000·√30 = 27 386 MPa ; Esec = fcc/eps_cc
    Ec = 5000.0 * math.sqrt(30.0)
    Esec = r.fcc_MPa / r.eps_cc
    rr = Ec / (Ec - Esec)
    x = eps[-1] / r.eps_cc
    sigma_u = r.fcc_MPa * x * rr / (rr - 1.0 + x ** rr)
    assert sig[-1] == pytest.approx(sigma_u, rel=1e-9)
    assert sig[-1] > 0.5 * r.fcc_MPa   # rama descendente suave, no vertical
