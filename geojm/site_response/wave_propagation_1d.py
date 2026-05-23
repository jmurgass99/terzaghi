"""
Propagacion de ondas SH 1D — metodo equivalente lineal (DEEPSOIL-style).

Modelo de Seed & Idriss (1970) simplificado:
    - Perfil de N capas con Vs, gamma, xi
    - Funcion de transferencia por capa:
      H(omega) = 1 / [cos(k*h) + i*xi*sin(k*h)]
    - Propagacion de bedrock a superficie

Input:
    - Perfil de suelo (capas con Vs, espesor, densidad, amortiguamiento)
    - Acelerograma base (bedrock)

Output:
    - Acelerograma en superficie
    - Espectro de respuesta amplificado
    - Perfil de gamma_max por capa
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class SoilLayer1D:
    """Estrato para analisis de respuesta de sitio 1D."""
    thickness_m: float
    Vs_m_s: float
    density_kg_m3: float = 1900.0
    damping_ratio: float = 0.05


@dataclass(frozen=True)
class SiteResponseResult:
    """Resultados de propagacion 1D."""
    surface_accel: np.ndarray          # acelerograma en superficie (m/s2)
    response_spectrum_Sa: np.ndarray   # espectro de respuesta (g)
    response_spectrum_T: np.ndarray    # periodos (s)
    gamma_max_profile: np.ndarray      # deformacion maxima por capa
    amplification_factor: float        # PGA_surface / PGA_bedrock
    peak_freq_Hz: float                # frecuencia de amplificacion pico


def _response_spectrum(
    accel: np.ndarray, dt: float,
    periods: np.ndarray, damping: float = 0.05,
) -> np.ndarray:
    """Espectro de respuesta pseudo-aceleracion (Newmark beta method)."""
    Sa = np.zeros(len(periods))
    for i, T in enumerate(periods):
        if T < 1e-10:
            Sa[i] = np.max(np.abs(accel))
            continue
        omega_n = 2.0 * np.pi / T
        c = 2.0 * damping * omega_n
        k = omega_n ** 2
        # Newmark constant-average-acceleration (beta=0.25, gamma=0.5)
        beta_n = 0.25
        gamma_n = 0.5
        a0 = 1.0 / (beta_n * dt ** 2) + gamma_n * c / (beta_n * dt)
        a1 = 1.0 / (beta_n * dt) + (gamma_n / beta_n - 1.0) * c
        a2 = (1.0 / (2.0 * beta_n) - 1.0) + dt * (gamma_n / (2.0 * beta_n) - 1.0) * c
        k_eff = k + a0

        u = 0.0
        v = 0.0
        a_prev = 0.0
        max_abs_a = 0.0

        for j in range(len(accel)):
            p_eff = -accel[j] + a0 * u + a1 * v + a2 * a_prev
            u_new = p_eff / k_eff
            du = u_new - u
            v_new = gamma_n / (beta_n * dt) * du - (gamma_n / beta_n - 1.0) * v \
                    - dt * (gamma_n / (2.0 * beta_n) - 1.0) * a_prev
            a_new = du / (beta_n * dt ** 2) - v / (beta_n * dt) \
                    - (1.0 / (2.0 * beta_n) - 1.0) * a_prev
            abs_total = abs(a_new + accel[j])
            if abs_total > max_abs_a:
                max_abs_a = abs_total
            u = u_new
            v = v_new
            a_prev = a_new

        Sa[i] = max_abs_a
    return Sa


def propagate_1d(
    input_accel: np.ndarray,
    dt_s: float,
    profile: Sequence[SoilLayer1D],
    bedrock_Vs: float = 1500.0,
    bedrock_density: float = 2500.0,
) -> SiteResponseResult:
    """Propaga acelerograma desde bedrock hasta la superficie.

    Implementa funcion de transferencia:
        H(omega) = 1 / [cos(k*h) + i*xi*sin(k*h)]
    por cada capa, con k = omega / Vs_complejo.
    """
    n = input_accel.size
    fft_input = np.fft.rfft(input_accel)
    freqs = np.fft.rfftfreq(n, dt_s)
    omegas = 2.0 * np.pi * freqs

    # Funcion de transferencia total
    H_total = np.ones_like(omegas, dtype=complex)

    # Velocity transfer para gamma_max
    gamma_max_list: list[float] = []

    for layer in profile:
        xi = layer.damping_ratio
        # Vs complejo con amortiguamiento histeretico
        Vs_star = layer.Vs_m_s * (1.0 + 1j * xi)
        k = np.divide(omegas, Vs_star, out=np.zeros_like(omegas, dtype=complex),
                       where=np.abs(Vs_star) > 0)
        kh = k * layer.thickness_m

        # Limitar parte imaginaria para evitar overflow
        kh = np.where(np.abs(np.imag(kh)) > 50, np.real(kh) + 50j, kh)

        # H(omega) = 1 / cos(kh)  (Roesset 1977, capa sobre semi-espacio)
        cos_kh = np.cos(kh)
        cos_kh = np.where(np.abs(cos_kh) < 1e-20, 1e-20, cos_kh)
        H_layer = 1.0 / cos_kh

        H_total *= H_layer

        # Deformacion maxima aproximada: gamma ~ peak_velocity / Vs
        fft_surface_at_layer = fft_input * H_total
        surface_at_layer = np.fft.irfft(fft_surface_at_layer, n=n)
        # Integrar aceleracion para obtener velocidad
        velocity = np.cumsum(surface_at_layer) * dt_s
        velocity -= np.mean(velocity)
        gamma_max = np.max(np.abs(velocity)) / layer.Vs_m_s
        gamma_max_list.append(float(gamma_max))

    # Acelerograma en superficie
    fft_surface = fft_input * H_total
    surface_accel = np.fft.irfft(fft_surface, n=n).astype(float)

    # Factor de amplificacion
    pga_input = np.max(np.abs(input_accel))
    pga_surface = np.max(np.abs(surface_accel))
    amp_factor = float(pga_surface / max(pga_input, 1e-9))

    # Frecuencia pico de amplificacion
    H_mag = np.abs(H_total)
    idx_peak = int(np.argmax(H_mag[1:])) + 1  # ignorar DC
    f_peak = float(freqs[idx_peak]) if idx_peak < len(freqs) else 0.0

    # Espectro de respuesta
    periods = np.geomspace(0.01, 4.0, 50)
    g = 9.81
    Sa = _response_spectrum(surface_accel, dt_s, periods, damping=0.05)
    Sa_g = Sa / g

    return SiteResponseResult(
        surface_accel=surface_accel,
        response_spectrum_Sa=Sa_g,
        response_spectrum_T=periods,
        gamma_max_profile=np.array(gamma_max_list),
        amplification_factor=amp_factor,
        peak_freq_Hz=f_peak,
    )


__all__ = ["SoilLayer1D", "SiteResponseResult", "propagate_1d"]
