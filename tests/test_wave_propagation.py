"""Tests propagación de ondas 1D."""
import numpy as np

from terzaghi.wave_propagation_1d import SoilLayer, propagate_sh_wave


def test_perfil_vacio_no_modifica():
    ag = np.random.randn(2000) * 0.5
    r = propagate_sh_wave(ag, dt_s=0.01, profile=[])
    assert r.amplification_factor == 1.0


def test_amplificacion_capa_blanda():
    rng = np.random.default_rng(1)
    ag = rng.normal(scale=0.3, size=2000)
    profile = [SoilLayer(thickness_m=20, Vs_m_per_s=150, damping_ratio=0.05)]
    r = propagate_sh_wave(ag, dt_s=0.01, profile=profile)
    # Suelo blando suele amplificar
    assert r.amplification_factor > 0.5
    assert r.peak_amplification_freq_Hz > 0
