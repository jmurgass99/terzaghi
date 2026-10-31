"""Tests para Skempton-Bjerrum."""
import pytest
from terzaghi.skempton_bjerrum import (
    SkemptonBjerrumInput, skempton_bjerrum, differential_settlement_ratio,
)


def test_A1_gives_mu_1():
    r = skempton_bjerrum(SkemptonBjerrumInput(100, A_pore=1.0, H_over_B=1.0))
    assert r.mu == pytest.approx(1.0)
    assert r.settlement_corrected_mm == pytest.approx(100.0)


def test_A0_low_HB_reduces():
    # A=0 (OC clay), H/B=1 -> mu~0.4
    r = skempton_bjerrum(SkemptonBjerrumInput(100, A_pore=0.0, H_over_B=1.0))
    assert 0.3 < r.mu < 0.5


def test_multi_code_accepted():
    for code in ("EU", "USA", "NSR", "AS", "SG"):
        r = skempton_bjerrum(SkemptonBjerrumInput(50, 0.5, 0.5, code=code))
        assert r.settlement_corrected_mm > 0
    with pytest.raises(ValueError):
        skempton_bjerrum(SkemptonBjerrumInput(50, 0.5, 0.5, code="ZZ"))


def test_differential_ratio():
    ratio = differential_settlement_ratio(s1_mm=30, s2_mm=10, span_m=4.0)
    assert ratio == pytest.approx(0.005)
    with pytest.raises(ValueError):
        differential_settlement_ratio(10, 5, 0.0)


def test_invalid_negative_S():
    with pytest.raises(ValueError):
        skempton_bjerrum(SkemptonBjerrumInput(-1, 0.5, 1.0))
