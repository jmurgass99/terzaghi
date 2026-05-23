"""Tests correlaciones + Gazetas."""
import pytest

from geojm.correlations import (
    Es_from_N, N60_corrected, N_from_qc, Su_from_qc, phi_from_N, qc_from_N,
)
from geojm.gazetas_springs import GazetasInput, evaluate_gazetas


class TestCorrelations:
    def test_N60_overburden(self):
        # N60 con overburden alto → Cn < 1
        n0 = N60_corrected(20, overburden_kPa=200)
        n1 = N60_corrected(20, overburden_kPa=50)
        assert n1 > n0

    def test_qc_N_invertible(self):
        N = 20
        qc = qc_from_N(N, "sand")
        N_back = N_from_qc(qc, "sand")
        assert N_back == pytest.approx(N, rel=1e-3)

    def test_phi_monotono(self):
        assert phi_from_N(30) > phi_from_N(10)

    def test_Su_no_negativo(self):
        assert Su_from_qc(1.5, sigma_v_kPa=50) >= 0

    def test_Es_clay_vs_sand(self):
        assert Es_from_N(20, "sand") > Es_from_N(20, "clay")


class TestGazetas:
    def test_rigideces_positivas(self):
        r = evaluate_gazetas(GazetasInput(L_m=4, B_m=2, Vs_m_per_s=200))
        assert r.Kz_kN_per_m > 0
        assert r.Kx_kN_per_m > 0
        assert r.Krx_kNm_per_rad > 0

    def test_L_menor_B_falla(self):
        with pytest.raises(ValueError):
            evaluate_gazetas(GazetasInput(L_m=2, B_m=4))
