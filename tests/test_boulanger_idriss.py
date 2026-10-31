"""Tests para B&I 2014 simplificado — GJ-004.

Caso referencia: N1_60=15, amax=0.3g, M=7.5, z=5m.
FS esperado ~0.8-1.0 (arena moderadamente suelta, sismo fuerte).
"""
import pytest

from terzaghi.liquefaction.boulanger_idriss import (
    BoulangerIdrissInput,
    BoulangerIdrissResult,
    evaluate_bi2014,
    _rd_bi2014,
    _crr_m75,
    _msf_bi2014,
    _k_sigma_bi2014,
)


class TestBoulangerIdriss2014:

    def _reference_input(self) -> BoulangerIdrissInput:
        """Caso: z=5m, arena con N1_60cs=15, amax=0.3g, M=7.5."""
        # sigma_v ~ 18*5 = 90 kPa, sigma'_v ~ 90 - 10*5*0.6 = 60 kPa (NF a 2m)
        return BoulangerIdrissInput(
            depth_m=5.0,
            sigma_v_kPa=90.0,
            sigma_v_eff_kPa=60.0,
            N1_60cs=15.0,
            a_max_g=0.3,
            Mw=7.5,
        )

    def test_fs_rango_referencia(self):
        """FS para caso referencia ~0.59 (N1_60cs=15, amax=0.3g, z=5m, Mw=7.5)."""
        r = evaluate_bi2014(self._reference_input())
        assert 0.4 < r.FS < 0.8

    def test_is_liquefiable_coherente(self):
        r = evaluate_bi2014(self._reference_input())
        assert r.is_liquefiable == (r.FS < 1.0)

    def test_arena_densa_no_licua(self):
        """N1_60cs=30 con amax moderado no deberia licuar."""
        inp = BoulangerIdrissInput(
            depth_m=5, sigma_v_kPa=90, sigma_v_eff_kPa=60,
            N1_60cs=30, a_max_g=0.2, Mw=7.5,
        )
        r = evaluate_bi2014(inp)
        assert r.FS > 1.0
        assert not r.is_liquefiable

    def test_arena_suelta_licua(self):
        """N1_60cs=5 con amax fuerte deberia licuar."""
        inp = BoulangerIdrissInput(
            depth_m=5, sigma_v_kPa=90, sigma_v_eff_kPa=60,
            N1_60cs=5, a_max_g=0.5, Mw=7.5,
        )
        r = evaluate_bi2014(inp)
        assert r.FS < 1.0
        assert r.is_liquefiable

    def test_rd_decrece_con_profundidad(self):
        """rd debe decrecer con la profundidad."""
        rd_5 = _rd_bi2014(5.0, 7.5)
        rd_15 = _rd_bi2014(15.0, 7.5)
        assert rd_5 > rd_15

    def test_rd_satura_a_34m(self):
        """rd se satura a z=34m."""
        rd_34 = _rd_bi2014(34.0, 7.5)
        rd_50 = _rd_bi2014(50.0, 7.5)
        assert rd_34 == pytest.approx(rd_50)

    def test_crr_crece_con_N(self):
        """CRR debe crecer con N1_60cs."""
        assert _crr_m75(10) < _crr_m75(20) < _crr_m75(30)

    def test_msf_m75_cercano_a_1(self):
        """MSF a Mw=7.5 debe ser cercano a 1.0."""
        msf = _msf_bi2014(7.5)
        assert 0.8 < msf < 1.2

    def test_msf_decrece_con_Mw(self):
        """Mayor magnitud → mas ciclos → MSF menor."""
        assert _msf_bi2014(6.0) > _msf_bi2014(7.5) > _msf_bi2014(8.5)

    def test_msf_saturado_a_1_8(self):
        """MSF no debe exceder 1.8."""
        msf_small = _msf_bi2014(4.0)
        assert msf_small <= 1.8

    def test_k_sigma_cercano_a_1_a_100kPa(self):
        """K_sigma a sigma'_v=100kPa (Pa) debe ser ~1.0."""
        Ks = _k_sigma_bi2014(100.0, 15.0)
        assert 0.9 < Ks < 1.1

    def test_k_sigma_limitado(self):
        """K_sigma debe estar entre 0.5 y 1.1."""
        Ks_low = _k_sigma_bi2014(500.0, 15.0)
        Ks_high = _k_sigma_bi2014(20.0, 15.0)
        assert Ks_low >= 0.5
        assert Ks_high <= 1.1

    def test_input_invalido_sigma_cero(self):
        with pytest.raises(ValueError):
            evaluate_bi2014(BoulangerIdrissInput(
                depth_m=5, sigma_v_kPa=90, sigma_v_eff_kPa=0,
                N1_60cs=15, a_max_g=0.3,
            ))

    def test_input_invalido_amax_cero(self):
        with pytest.raises(ValueError):
            evaluate_bi2014(BoulangerIdrissInput(
                depth_m=5, sigma_v_kPa=90, sigma_v_eff_kPa=60,
                N1_60cs=15, a_max_g=0,
            ))

    def test_to_dict(self):
        r = evaluate_bi2014(self._reference_input())
        d = r.to_dict()
        assert "FS" in d
        assert "CSR" in d
        assert "is_liquefiable" in d
