"""
Propagacion de ondas SH 1D — metodo equivalente lineal (DEEPSOIL / SHAKE91).

Incluye:
    - Modelo desacoplado capa por capa (Roesset 1977, retrocompatible por defecto)
    - Recursión exacta de matriz de transferencia / impedancia multicapa de
      Kramer (1996) §7.2.3 con contraste de impedancia complejo α_m entre estratos
      y frente al semiespacio elástico de roca basal (``use_impedance_recursion=True``).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Literal, Sequence

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


def transfer_function_multilayer_kramer(
    omegas: np.ndarray,
    profile: Sequence[SoilLayer1D],
    bedrock_Vs: float = 1500.0,
    bedrock_density: float = 2500.0,
    input_motion_type: Literal["outcrop", "within"] = "outcrop",
) -> tuple[np.ndarray, list[np.ndarray]]:
    """Recursión exacta de amplitudes de onda SH multicapa (Kramer 1996 §7.2.3).

    En la superficie libre (estrato 1, z_1 = 0): A_1 = B_1 = 1.
    Para cada interfaz m -> m+1 (m = 1..N, donde N+1 es la roca basal):
      α_m = (ρ_m · Vs*_m) / (ρ_{m+1} · Vs*_{m+1})
      A_{m+1} = 0.5 · A_m · (1 + α_m) · e^{i·k_m·h_m} + 0.5 · B_m · (1 - α_m) · e^{-i·k_m·h_m}
      B_{m+1} = 0.5 · A_m · (1 - α_m) · e^{i·k_m·h_m} + 0.5 · B_m · (1 + α_m) · e^{-i·k_m·h_m}

    Devuelve ``(H_total, layer_top_amplitudes)`` donde:
      - Para ``input_motion_type="outcrop"``: H_total(ω) = (A_1 + B_1) / (2 · A_{N+1}) = 1 / A_{N+1}
      - Para ``input_motion_type="within"``:  H_total(ω) = (A_1 + B_1) / (A_{N+1} + B_{N+1}) = 2 / (A_{N+1} + B_{N+1})
    """
    if not profile:
        return np.ones_like(omegas, dtype=complex), []

    A_m = np.ones_like(omegas, dtype=complex)
    B_m = np.ones_like(omegas, dtype=complex)
    layer_amplitudes: list[np.ndarray] = []

    n_layers = len(profile)
    for m, layer in enumerate(profile):
        Vs_star_m = layer.Vs_m_s * (1.0 + 1j * layer.damping_ratio)
        imp_m = layer.density_kg_m3 * Vs_star_m

        if m + 1 < n_layers:
            nxt = profile[m + 1]
            Vs_star_next = nxt.Vs_m_s * (1.0 + 1j * nxt.damping_ratio)
            imp_next = nxt.density_kg_m3 * Vs_star_next
        else:
            imp_next = complex(bedrock_density * bedrock_Vs)

        alpha_m = imp_m / imp_next
        k_m = omegas / Vs_star_m
        kh = k_m * layer.thickness_m
        kh = np.where(np.abs(np.imag(kh)) > 50.0, np.real(kh) + 50.0j * np.sign(np.imag(kh)), kh)

        exp_pos = np.exp(1j * kh)
        exp_neg = np.exp(-1j * kh)

        # Amplitude at mid-height of layer m for strain estimation
        A_mid = A_m * np.exp(0.5j * kh)
        B_mid = B_m * np.exp(-0.5j * kh)
        layer_amplitudes.append(A_mid + B_mid)

        A_next = 0.5 * A_m * (1.0 + alpha_m) * exp_pos + 0.5 * B_m * (1.0 - alpha_m) * exp_neg
        B_next = 0.5 * A_m * (1.0 - alpha_m) * exp_pos + 0.5 * B_m * (1.0 + alpha_m) * exp_neg
        A_m, B_m = A_next, B_next

    if input_motion_type == "within":
        denom = A_m + B_m
        denom = np.where(np.abs(denom) < 1e-20, 1e-20, denom)
        H_total = 2.0 / denom
    else:
        denom = np.where(np.abs(A_m) < 1e-20, 1e-20, A_m)
        H_total = 1.0 / denom

    layer_transfers = [amp * H_total / 2.0 for amp in layer_amplitudes]
    return H_total, layer_transfers


def _response_spectrum(
    accel: np.ndarray, dt: float,
    periods: np.ndarray, damping: float = 0.05,
) -> np.ndarray:
    """Espectro de respuesta pseudo-aceleracion (Newmark beta method con sub-stepping)."""
    Sa = np.zeros(len(periods))
    for i, T in enumerate(periods):
        if T < 1e-10:
            Sa[i] = np.max(np.abs(accel))
            continue
        n_sub = max(1, int(ceil(dt / (T / 20.0))))
        if n_sub > 1:
            t_orig = np.arange(len(accel)) * dt
            dt_use = dt / n_sub
            t_fine = np.linspace(0.0, t_orig[-1], (len(accel) - 1) * n_sub + 1)
            ag_use = np.interp(t_fine, t_orig, accel)
        else:
            dt_use = dt
            ag_use = accel

        omega_n = 2.0 * np.pi / T
        c = 2.0 * damping * omega_n
        k = omega_n ** 2
        beta_n = 0.25
        gamma_n = 0.5
        a0 = 1.0 / (beta_n * dt_use ** 2) + gamma_n * c / (beta_n * dt_use)
        a1 = 1.0 / (beta_n * dt_use) + (gamma_n / beta_n - 1.0) * c
        a2 = (1.0 / (2.0 * beta_n) - 1.0) + dt_use * (gamma_n / (2.0 * beta_n) - 1.0) * c
        k_eff = k + a0

        u = 0.0
        v = 0.0
        a_prev = 0.0
        max_abs_a = 0.0

        for j in range(len(ag_use)):
            p_eff = -ag_use[j] + a0 * u + a1 * v + a2 * a_prev
            u_new = p_eff / k_eff
            du = u_new - u
            v_new = gamma_n / (beta_n * dt_use) * du - (gamma_n / beta_n - 1.0) * v \
                    - dt_use * (gamma_n / (2.0 * beta_n) - 1.0) * a_prev
            a_new = du / (beta_n * dt_use ** 2) - v / (beta_n * dt_use) \
                    - (1.0 / (2.0 * beta_n) - 1.0) * a_prev
            abs_total = abs(a_new + ag_use[j])
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
    use_impedance_recursion: bool = False,
    input_motion_type: Literal["outcrop", "within"] = "outcrop",
) -> SiteResponseResult:
    """Propaga acelerograma desde bedrock hasta la superficie.

    Cuando ``use_impedance_recursion=True``, utiliza la recursión multicapa de
    Kramer (1996) con contraste de impedancia entre capas y semiespacio de roca.
    """
    n = input_accel.size
    fft_input = np.fft.rfft(input_accel)
    freqs = np.fft.rfftfreq(n, dt_s)
    omegas = 2.0 * np.pi * freqs

    gamma_max_list: list[float] = []

    if use_impedance_recursion:
        H_total, layer_transfers = transfer_function_multilayer_kramer(
            omegas=omegas,
            profile=profile,
            bedrock_Vs=bedrock_Vs,
            bedrock_density=bedrock_density,
            input_motion_type=input_motion_type,
        )
        for layer, H_layer_mid in zip(profile, layer_transfers):
            accel_mid = np.fft.irfft(fft_input * H_layer_mid, n=n)
            velocity = np.cumsum(accel_mid) * dt_s
            velocity -= np.mean(velocity)
            gamma_max = np.max(np.abs(velocity)) / layer.Vs_m_s
            gamma_max_list.append(float(gamma_max))
    else:
        H_total = np.ones_like(omegas, dtype=complex)
        for layer in profile:
            xi = layer.damping_ratio
            Vs_star = layer.Vs_m_s * (1.0 + 1j * xi)
            k = np.divide(omegas, Vs_star, out=np.zeros_like(omegas, dtype=complex),
                          where=np.abs(Vs_star) > 0)
            kh = k * layer.thickness_m
            kh = np.where(np.abs(np.imag(kh)) > 50, np.real(kh) + 50j, kh)
            cos_kh = np.cos(kh)
            cos_kh = np.where(np.abs(cos_kh) < 1e-20, 1e-20, cos_kh)
            H_layer = 1.0 / cos_kh
            H_total *= H_layer

            fft_surface_at_layer = fft_input * H_total
            surface_at_layer = np.fft.irfft(fft_surface_at_layer, n=n)
            velocity = np.cumsum(surface_at_layer) * dt_s
            velocity -= np.mean(velocity)
            gamma_max = np.max(np.abs(velocity)) / layer.Vs_m_s
            gamma_max_list.append(float(gamma_max))

    fft_surface = fft_input * H_total
    surface_accel = np.fft.irfft(fft_surface, n=n).astype(float)

    pga_input = np.max(np.abs(input_accel))
    pga_surface = np.max(np.abs(surface_accel))
    amp_factor = float(pga_surface / max(pga_input, 1e-9))

    H_mag = np.abs(H_total)
    idx_peak = int(np.argmax(H_mag[1:])) + 1
    f_peak = float(freqs[idx_peak]) if idx_peak < len(freqs) else 0.0

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


__all__ = [
    "SoilLayer1D",
    "SiteResponseResult",
    "propagate_1d",
    "transfer_function_multilayer_kramer",
]
