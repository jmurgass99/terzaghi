"""Tests para evaluación de licuación Boulanger-Idriss 2014."""
import pytest

from terzaghi.liquefaction import LiquefactionInput, evaluate_liquefaction


class TestBoulangerIdriss:
    def test_arena_densa_no_licua(self):
        r = evaluate_liquefaction(LiquefactionInput(
            depth_m=5, sigma_v_kPa=90, sigma_v_eff_kPa=60,
            N1_60_cs=30, a_max_g=0.3, Mw=7.5,
        ))
        assert r.FS > 1.0

    def test_arena_suelta_licua(self):
        r = evaluate_liquefaction(LiquefactionInput(
            depth_m=5, sigma_v_kPa=90, sigma_v_eff_kPa=60,
            N1_60_cs=5, a_max_g=0.5, Mw=7.5,
        ))
        assert r.FS < 1.0
        assert not r.is_safe

    def test_msf_disminuye_con_Mw(self):
        # Mw mayor → más ciclos significativos → MSF menor
        small_Mw = evaluate_liquefaction(LiquefactionInput(
            depth_m=5, sigma_v_kPa=90, sigma_v_eff_kPa=60,
            N1_60_cs=15, a_max_g=0.3, Mw=6.0,
        ))
        large_Mw = evaluate_liquefaction(LiquefactionInput(
            depth_m=5, sigma_v_kPa=90, sigma_v_eff_kPa=60,
            N1_60_cs=15, a_max_g=0.3, Mw=8.5,
        ))
        assert small_Mw.MSF > large_Mw.MSF

    def test_input_invalido(self):
        with pytest.raises(ValueError):
            evaluate_liquefaction(LiquefactionInput(
                depth_m=5, sigma_v_kPa=90, sigma_v_eff_kPa=0,
                N1_60_cs=15, a_max_g=0.3,
            ))
