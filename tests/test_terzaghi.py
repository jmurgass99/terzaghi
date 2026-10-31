"""Tests para Terzaghi — P-y curves, grupo de pilotes, Mander."""
import numpy as np
import pytest

from terzaghi.piles import (
    py_matlock_soft_clay,
    py_reese_sand,
    pile_group_efficiency_lateral,
)
from terzaghi.materials import mander_confined_concrete


# ---------------------------------------------------------------------
# P-y Matlock
# ---------------------------------------------------------------------

class TestMatlockPY:
    def test_monotonia_y_no_negativo(self):
        p, y = py_matlock_soft_clay(z_m=3, D_m=0.8, su_kPa=50)
        assert np.all(p >= 0)
        assert np.all(np.diff(y) > 0)

    def test_saturacion_en_p_ult(self):
        p, y = py_matlock_soft_clay(z_m=3, D_m=0.8, su_kPa=50)
        # Última mitad debe ser ≈ constante (p_ult)
        assert np.std(p[-5:]) < np.std(p[:5])


class TestReeseSandPY:
    def test_hiperbolica_creciente(self):
        p, y = py_reese_sand(z_m=2, D_m=0.6, phi_deg=32)
        assert np.all(np.diff(p) >= 0)
        assert p[0] == 0.0


class TestPileGroup:
    def test_eficiencia_creciente_con_espaciamiento(self):
        eff_3 = pile_group_efficiency_lateral(s_over_D=3, rows=3).global_efficiency
        eff_5 = pile_group_efficiency_lateral(s_over_D=5, rows=3).global_efficiency
        assert eff_5 > eff_3

    def test_una_fila_solo_leading(self):
        r = pile_group_efficiency_lateral(s_over_D=5, rows=1)
        assert r.global_efficiency == r.p_multiplier_leading

    def test_invalid_rows(self):
        with pytest.raises(ValueError):
            pile_group_efficiency_lateral(s_over_D=3, rows=0)


class TestMander:
    def test_K_confinement_mayor_que_uno(self):
        r = mander_confined_concrete(
            fc=28, fyh=420, rho_x=0.012, rho_y=0.012,
            b_core_mm=420, h_core_mm=420, s_mm=100,
        )
        assert r.K_confinement > 1.0
        assert r.fcc_MPa > 28

    def test_curva_no_negativa(self):
        r = mander_confined_concrete(
            fc=28, fyh=420, rho_x=0.012, rho_y=0.012,
            b_core_mm=420, h_core_mm=420, s_mm=100,
        )
        assert all(s >= 0 for _, s in r.sigma_eps)
        assert r.eps_cu > r.eps_cc

    def test_input_invalido(self):
        with pytest.raises(ValueError):
            mander_confined_concrete(
                fc=-1, fyh=420, rho_x=0.01, rho_y=0.01,
                b_core_mm=400, h_core_mm=400, s_mm=100,
            )
