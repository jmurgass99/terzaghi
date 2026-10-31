"""Tests para propagacion de ondas 1D — GJ-003.

Caso: 1 capa homogenea 30m, Vs=200m/s sobre roca.
Frecuencia fundamental esperada: f0 = Vs / (4*H) = 200/(4*30) = 1.67 Hz
Amplificacion esperada: ~2-3x (con 5% amortiguamiento).
"""
import numpy as np
import pytest

from terzaghi.site_response.wave_propagation_1d import (
    SoilLayer1D,
    SiteResponseResult,
    propagate_1d,
)


def _make_input_motion(dt=0.005, duration=10.0, seed=42):
    """Genera un acelerograma sintetico de ruido blanco filtrado."""
    rng = np.random.default_rng(seed)
    n = int(duration / dt)
    accel = rng.normal(scale=0.2, size=n)
    # Filtrar frecuencias altas (simple media movil)
    window = 5
    accel = np.convolve(accel, np.ones(window) / window, mode="same")
    return accel, dt


class TestSiteResponse1D:

    def test_amplificacion_capa_blanda(self):
        """Capa blanda sobre roca debe amplificar a frecuencia resonante."""
        # Usar seno a frecuencia resonante f0 = Vs/(4H) = 1.67 Hz
        f0 = 200.0 / (4.0 * 30.0)
        dt = 0.005
        t = np.arange(0, 10.0, dt)
        accel = 0.1 * np.sin(2 * np.pi * f0 * t)
        profile = [SoilLayer1D(thickness_m=30, Vs_m_s=200, damping_ratio=0.05)]
        result = propagate_1d(accel, dt, profile)
        # Amplificacion a resonancia: tipicamente 2-15x con xi=5%
        assert result.amplification_factor > 2.0
        assert result.amplification_factor < 20.0

    def test_frecuencia_fundamental(self):
        """f0 = Vs/(4H) = 200/(4*30) = 1.67 Hz."""
        accel, dt = _make_input_motion()
        profile = [SoilLayer1D(thickness_m=30, Vs_m_s=200, damping_ratio=0.05)]
        result = propagate_1d(accel, dt, profile)
        f0_teorica = 200.0 / (4.0 * 30.0)
        # Tolerancia +-30% por discretizacion FFT
        assert abs(result.peak_freq_Hz - f0_teorica) / f0_teorica < 0.30

    def test_output_shapes(self):
        """Shapes de arrays de salida deben ser consistentes."""
        accel, dt = _make_input_motion()
        profile = [SoilLayer1D(thickness_m=30, Vs_m_s=200, damping_ratio=0.05)]
        result = propagate_1d(accel, dt, profile)
        # Acelerograma misma longitud que input
        assert result.surface_accel.shape == accel.shape
        # Espectro de respuesta
        assert len(result.response_spectrum_Sa) == len(result.response_spectrum_T)
        assert len(result.response_spectrum_Sa) == 50
        # gamma_max_profile: 1 valor por capa
        assert len(result.gamma_max_profile) == 1

    def test_gamma_max_positivo(self):
        """Deformacion maxima debe ser positiva."""
        accel, dt = _make_input_motion()
        profile = [SoilLayer1D(thickness_m=30, Vs_m_s=200, damping_ratio=0.05)]
        result = propagate_1d(accel, dt, profile)
        assert np.all(result.gamma_max_profile > 0)

    def test_multicapa(self):
        """Perfil multicapa: arcilla blanda + arena densa."""
        accel, dt = _make_input_motion()
        profile = [
            SoilLayer1D(thickness_m=10, Vs_m_s=120, damping_ratio=0.08),
            SoilLayer1D(thickness_m=20, Vs_m_s=300, damping_ratio=0.03),
        ]
        result = propagate_1d(accel, dt, profile)
        assert result.amplification_factor > 1.0
        assert len(result.gamma_max_profile) == 2

    def test_response_spectrum_valores_positivos(self):
        """Espectro de respuesta debe tener valores positivos."""
        accel, dt = _make_input_motion()
        profile = [SoilLayer1D(thickness_m=30, Vs_m_s=200, damping_ratio=0.05)]
        result = propagate_1d(accel, dt, profile)
        assert np.all(result.response_spectrum_Sa >= 0)
        assert np.all(result.response_spectrum_T > 0)

    def test_perfil_vacio_no_amplifica(self):
        """Sin capas, la amplificacion debe ser ~ 1."""
        accel, dt = _make_input_motion()
        result = propagate_1d(accel, dt, profile=[])
        # gamma_max vacio
        assert len(result.gamma_max_profile) == 0
        assert result.amplification_factor == pytest.approx(1.0, abs=0.01)
