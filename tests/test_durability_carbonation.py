"""Suite 2.2 — Avance del frente de carbonatación (ley de la raíz del tiempo).

Comprobaciones cerradas:
  d(4t) / d(t) = 2  exactamente   (d = K·√t)
  time_to_depth es la inversa exacta de carbonation_depth.
"""
import pytest

from geojm.durability.carbonation import (
    carbonation_coefficient,
    carbonation_depth,
    time_to_depth,
)


def test_sqrt_time_law_doubling():
    # d(4t)/d(t) = 2 para cualquier K
    K = 3.5
    assert carbonation_depth(40.0, K) / carbonation_depth(10.0, K) == pytest.approx(2.0)


def test_inverse_roundtrip():
    K = 4.0
    d = carbonation_depth(25.0, K)
    assert time_to_depth(d, K) == pytest.approx(25.0, rel=1e-12)


def test_depth_zero_at_t_zero():
    assert carbonation_depth(0.0, 5.0) == 0.0


def test_K_increases_with_water_cement_ratio():
    # Mayor relación a/c → hormigón más poroso → mayor Kc
    k_low = carbonation_coefficient(w_c=0.45, fly_ash_pct=0.0, rh_pct=65.0)
    k_high = carbonation_coefficient(w_c=0.65, fly_ash_pct=0.0, rh_pct=65.0)
    assert k_high > k_low


def test_K_increases_with_fly_ash():
    # La ceniza volante reduce la reserva alcalina → carbonatación más rápida
    k_no = carbonation_coefficient(w_c=0.5, fly_ash_pct=0.0, rh_pct=65.0)
    k_fa = carbonation_coefficient(w_c=0.5, fly_ash_pct=30.0, rh_pct=65.0)
    assert k_fa > k_no


def test_K_peaks_at_mid_humidity():
    # La carbonatación es máxima a HR intermedia (~50-70%) y cae en seco/saturado
    k_dry = carbonation_coefficient(w_c=0.5, fly_ash_pct=0.0, rh_pct=20.0)
    k_mid = carbonation_coefficient(w_c=0.5, fly_ash_pct=0.0, rh_pct=60.0)
    k_wet = carbonation_coefficient(w_c=0.5, fly_ash_pct=0.0, rh_pct=95.0)
    assert k_mid > k_dry
    assert k_mid > k_wet


def test_service_life_example():
    # Recubrimiento 30 mm, K=3 mm/√año → vida = (30/3)² = 100 años
    assert time_to_depth(30.0, 3.0) == pytest.approx(100.0)
