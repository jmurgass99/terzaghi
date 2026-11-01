# -*- coding: utf-8 -*-
"""La vía legacy ``evaluate_liquefaction`` y la API usan r_d y K_σ de Boulanger & Idriss (2014).

Hasta la 1.1.0 ``terzaghi.liquefaction._r_d`` omitía los senos de α(z) y β(z) y ``_K_sigma``
usaba √(σ'/100) en vez de ln(σ'/P_a): el FS legacy salía un 13–29 % por encima del de
``evaluate_bi2014`` (lado inseguro). Además ``evaluate_spt_profile_liquefaction`` estaba en
``__all__`` pero no se importaba.
"""
from __future__ import annotations

import math

import pytest

from terzaghi.liquefaction import (
    LiquefactionInput,
    evaluate_bi2014,
    evaluate_liquefaction,
    evaluate_spt_profile_liquefaction,
)
from terzaghi.liquefaction import _K_sigma, _r_d
from terzaghi.liquefaction.boulanger_idriss import BoulangerIdrissInput


@pytest.mark.parametrize("z,sv,sve,N,a,M", [
    (5.0, 90.0, 60.0, 15.0, 0.30, 7.5),
    (6.0, 130.0, 100.0, 20.0, 0.30, 7.5),
    (10.0, 190.0, 120.0, 12.0, 0.25, 7.0),
    (3.0, 54.0, 34.0, 8.0, 0.35, 6.5),
])
def test_legacy_equals_bi2014(z, sv, sve, N, a, M):
    leg = evaluate_liquefaction(LiquefactionInput(z, sv, sve, N, a, M))
    ref = evaluate_bi2014(BoulangerIdrissInput(z, sv, sve, N, a, M))
    assert leg.CSR == pytest.approx(ref.CSR, rel=1e-12)
    assert leg.CRR == pytest.approx(ref.CRR, rel=1e-12)
    assert leg.MSF == pytest.approx(ref.MSF, rel=1e-12)
    assert leg.K_sigma == pytest.approx(ref.K_sigma, rel=1e-12)
    assert leg.FS == pytest.approx(ref.FS, rel=1e-12)


def test_rd_has_the_sines_and_k_sigma_is_one_at_one_atmosphere():
    alpha = -1.012 - 1.126 * math.sin(5.0 / 11.73 + 5.133)
    beta = 0.106 + 0.118 * math.sin(5.0 / 11.28 + 5.142)
    assert _r_d(5.0, 7.5) == pytest.approx(math.exp(alpha + beta * 7.5), rel=1e-12)
    assert _r_d(5.0, 7.5) > 0.9          # el valor antiguo era 0,74
    assert _K_sigma(100.0, 20.0) == pytest.approx(1.0, abs=1e-12)
    assert _K_sigma(50.0, 20.0) > 1.0    # el valor antiguo era < 1


def test_profile_function_is_importable_from_package():
    res = evaluate_spt_profile_liquefaction([
        {"depth_m": 3.0, "sigma_v_kPa": 54.0, "sigma_v_eff_kPa": 34.0, "N1_60cs": 8.0},
    ], a_max_g=0.35, Mw=7.5)
    assert res.evaluated and res.layers[0]["is_liquefiable"] is True
