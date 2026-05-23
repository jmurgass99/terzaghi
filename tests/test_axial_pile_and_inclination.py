"""Capacidad axial de pilote (α/β) + correcciones inclinación/excentricidad."""
import math

import pytest

from geojm.piles.axial_capacity import (
    Pile,
    SoilLayer,
    api_alpha,
    axial_capacity,
)
from geojm.bearing_inclination import effective_dimensions, inclination_factors


class TestAlpha:
    def test_psi_menor_1(self):
        # psi = Su/sv = 50/100 = 0.5 <= 1 -> alpha = 0.5*0.5^-0.5
        assert api_alpha(50.0, 100.0) == pytest.approx(min(0.5 * 0.5 ** -0.5, 1.0), rel=1e-9)

    def test_acotado_a_1(self):
        # psi pequeño (arcilla blanda, Su << sv) -> alpha tendería a >1, capado a 1.0
        assert api_alpha(10.0, 200.0) == 1.0

    def test_alpha_decrece_con_psi(self):
        # OC clay (psi alto) tiene menor adhesión que NC clay (psi bajo).
        assert api_alpha(200.0, 10.0) < api_alpha(50.0, 100.0)


class TestAxialClay:
    def test_pilote_arcilla_homogenea(self):
        # D=0.5, L=10, Su=50 kPa, una capa de arcilla.
        layers = [SoilLayer(0.0, 12.0, "clay", gamma_kN_m3=18.0, Su_kPa=50.0)]
        r = axial_capacity(Pile(diameter_m=0.5, length_m=10.0, water_table_m=99.0), layers, FS=2.5)
        # Punta: q_b = 9*Su = 450 kPa; A_base = pi*0.25/... = pi*0.5^2/4 = 0.19635
        area_base = math.pi * 0.5 ** 2 / 4.0
        assert r.Q_base_kN == pytest.approx(9.0 * 50.0 * area_base, rel=1e-9)
        # Fuste > 0 y total coherente.
        assert r.Q_skin_kN > 0
        assert r.Q_ult_kN == pytest.approx(r.Q_skin_kN + r.Q_base_kN, rel=1e-12)
        assert r.Q_allow_kN == pytest.approx(r.Q_ult_kN / 2.5, rel=1e-12)

    def test_mas_largo_mas_capacidad(self):
        layers = [SoilLayer(0.0, 30.0, "clay", Su_kPa=60.0)]
        corto = axial_capacity(Pile(0.5, 8.0, water_table_m=99.0), layers)
        largo = axial_capacity(Pile(0.5, 16.0, water_table_m=99.0), layers)
        assert largo.Q_ult_kN > corto.Q_ult_kN


class TestAxialSand:
    def test_pilote_arena(self):
        layers = [SoilLayer(0.0, 20.0, "sand", gamma_kN_m3=19.0, phi_deg=34.0)]
        r = axial_capacity(Pile(0.4, 12.0, water_table_m=2.0), layers, FS=3.0)
        assert r.Q_skin_kN > 0 and r.Q_base_kN > 0
        assert r.Q_ult_kN > r.Q_allow_kN  # FS aplicado


class TestInclinationEccentricity:
    def test_area_efectiva_meyerhof(self):
        ea = effective_dimensions(3.0, 4.0, e_B_m=0.3, e_L_m=0.0)
        assert ea.B_eff_m == pytest.approx(3.0 - 0.6)
        assert ea.L_eff_m == 4.0
        assert ea.area_m2 == pytest.approx(2.4 * 4.0)

    def test_inclinacion_sin_horizontal_es_1(self):
        ic, iq, ig = inclination_factors(1000.0, 0.0, 10.0, 30.0, 2.0, 2.0)
        assert (ic, iq, ig) == (1.0, 1.0, 1.0)

    def test_inclinacion_reduce_capacidad(self):
        ic, iq, ig = inclination_factors(1000.0, 200.0, 0.0, 30.0, 2.0, 2.0)
        assert 0.0 < iq < 1.0
        assert ig < iq  # i_gamma usa exponente m+1 -> menor
        assert 0.0 <= ic <= 1.0

    def test_mas_horizontal_mas_reduccion(self):
        _, iq_lo, _ = inclination_factors(1000.0, 100.0, 0.0, 30.0, 2.0, 2.0)
        _, iq_hi, _ = inclination_factors(1000.0, 400.0, 0.0, 30.0, 2.0, 2.0)
        assert iq_hi < iq_lo
