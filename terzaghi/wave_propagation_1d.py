"""
Propagación de ondas SH 1D en suelos estratificados — método equivalente
lineal simplificado (estilo SHAKE91 / DEEPSOIL).

Asume estratigrafía horizontal homogénea, viaje SH vertical. Para cada
estrato calcula la función de transferencia y propaga el espectro de
Fourier del input al output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class SoilLayer:
    thickness_m: float
    Vs_m_per_s: float
    density_kg_m3: float = 1900.0
    damping_ratio: float = 0.05


@dataclass(frozen=True)
class PropagationResult:
    surface_accel_m_per_s2: np.ndarray
    amplification_factor: float
    peak_amplification_freq_Hz: float


def propagate_sh_wave(
    input_accel: np.ndarray,
    dt_s: float,
    profile: Sequence[SoilLayer],
    bedrock_Vs: float = 1500.0,
    bedrock_density: float = 2500.0,
) -> PropagationResult:
    """Propaga el acelerograma desde bedrock hasta la superficie.

    Modelo simplificado: cada estrato se trata como un oscilador con
    función de transferencia ``H(ω) = 1/cos(k·H + i·ζ·k·H)`` aplicada al
    espectro de Fourier.
    """
    if not profile:
        return PropagationResult(
            surface_accel_m_per_s2=input_accel,
            amplification_factor=1.0,
            peak_amplification_freq_Hz=0.0,
        )

    n = input_accel.size
    fft = np.fft.rfft(input_accel)
    freqs = np.fft.rfftfreq(n, dt_s)
    omegas = 2 * np.pi * freqs

    # Producto de funciones de transferencia capa por capa
    H_total = np.ones_like(omegas, dtype=complex)
    for layer in profile:
        zeta = layer.damping_ratio
        Vs_complex = layer.Vs_m_per_s * (1 + 1j * zeta)
        k = omegas / Vs_complex
        # H(ω) capa simple sobre semi-espacio (Roesset, 1977)
        kH = k * layer.thickness_m
        # Evitar overflow: limitar |Im(kH)| a algo razonable
        kH = np.where(np.abs(np.imag(kH)) > 50, 50 + 1j * 0, kH)
        H = 1.0 / np.cos(kH)
        H_total *= H

    fft_surface = fft * H_total
    surface = np.fft.irfft(fft_surface, n=n)

    amp = np.max(np.abs(surface)) / max(np.max(np.abs(input_accel)), 1e-9)
    # Frecuencia de amplificación pico
    H_mag = np.abs(H_total)
    idx = int(np.argmax(H_mag))
    f_peak = float(freqs[idx])

    return PropagationResult(
        surface_accel_m_per_s2=surface.astype(float),
        amplification_factor=float(amp),
        peak_amplification_freq_Hz=f_peak,
    )


__all__ = ["SoilLayer", "PropagationResult", "propagate_sh_wave"]
