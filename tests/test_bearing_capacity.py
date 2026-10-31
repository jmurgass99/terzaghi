"""Tests bearing capacity multi-código."""
import pytest

from terzaghi.bearing_capacity import BearingCapacityInput, evaluate_bearing


@pytest.fixture
def base_input():
    return BearingCapacityInput(
        B_m=2.0, L_m=3.0, D_f_m=1.5,
        phi_deg=30, c_kPa=10, gamma_kN_m3=18,
        method="vesic",
    )


class TestBearing:
    def test_5_codigos(self, base_input):
        for code in ("EU", "SG", "US", "CO", "AU"):
            r = evaluate_bearing(base_input, code=code)
            assert r.q_ult_kPa > 0
            assert r.q_adm_kPa > 0
            assert r.q_adm_kPa < r.q_ult_kPa

    def test_co_mas_conservador(self, base_input):
        # NSR-10 FS=3 → q_adm más bajo
        eu = evaluate_bearing(base_input, code="EU")
        co = evaluate_bearing(base_input, code="CO")
        assert co.q_adm_kPa < eu.q_adm_kPa

    def test_metodos_diferentes(self):
        terz = evaluate_bearing(BearingCapacityInput(
            B_m=2, L_m=3, D_f_m=1.5, phi_deg=30, method="terzaghi",
        ), code="EU")
        ves = evaluate_bearing(BearingCapacityInput(
            B_m=2, L_m=3, D_f_m=1.5, phi_deg=30, method="vesic",
        ), code="EU")
        assert ves.Ngamma != terz.Ngamma
