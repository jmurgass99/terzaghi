"""
Propagación de ondas SH 1D en suelos estratificados — método equivalente
lineal (estilo SHAKE91 / DEEPSOIL).

Incluye tanto la aproximación desacoplada por capa (por defecto) como la
recursión exacta de impedancias multicapa de Kramer (1996) §7.2.3
(``use_impedance_recursion=True``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

import numpy as np

from .site_response.wave_propagation_1d import (
    SoilLayer1D,
    transfer_function_multilayer_kramer,
)


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
    use_impedance_recursion: bool = False,
    input_motion_type: Literal["outcrop", "within"] = "outcrop",
) -> PropagationResult:
    """Propaga el acelerograma desde bedrock hasta la superficie."""
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

    if use_impedance_recursion:
        layers_1d = [
            SoilLayer1D(
                thickness_m=lay.thickness_m,
                Vs_m_s=lay.Vs_m_per_s,
                density_kg_m3=lay.density_kg_m3,
                damping_ratio=lay.damping_ratio,
            )
            for lay in profile
        ]
        H_total, _ = transfer_function_multilayer_kramer(
            omegas=omegas,
            profile=layers_1d,
            bedrock_Vs=bedrock_Vs,
            bedrock_density=bedrock_density,
            input_motion_type=input_motion_type,
        )
    else:
        H_total = np.ones_like(omegas, dtype=complex)
        for layer in profile:
            zeta = layer.damping_ratio
            Vs_complex = layer.Vs_m_per_s * (1 + 1j * zeta)
            k = omegas / Vs_complex
            kH = k * layer.thickness_m
            kH = np.where(np.abs(np.imag(kH)) > 50, 50 + 1j * 0, kH)
            H = 1.0 / np.cos(kH)
            H_total *= H

    fft_surface = fft * H_total
    surface = np.fft.irfft(fft_surface, n=n)

    amp = np.max(np.abs(surface)) / max(np.max(np.abs(input_accel)), 1e-9)
    H_mag = np.abs(H_total)
    idx = int(np.argmax(H_mag))
    f_peak = float(freqs[idx])

    return PropagationResult(
        surface_accel_m_per_s2=surface.astype(float),
        amplification_factor=float(amp),
        peak_amplification_freq_Hz=f_peak,
    )


__all__ = ["SoilLayer", "PropagationResult", "propagate_sh_wave"]
