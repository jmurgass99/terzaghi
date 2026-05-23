# -*- coding: utf-8 -*-
"""
Design of Gabion Retaining Walls — Stability Safety Auditing
============================================================
Implementa las ecuaciones de empuje sismico lateral mediante Mononobe-Okabe,
calculo de empuje activo seco/saturado, y verificaciones de estabilidad
geotecnica clasica (F.S.) frente a vuelco, deslizamiento y capacidad portante,
segun el documento Design_of_Gabion_Retaining_Structure_as.pdf.
"""
from __future__ import annotations
import math

def active_thrust_coulomb(
    gamma_kN_m3: float,     # Peso volumetrico del suelo (kN/m3)
    H_m: float,             # Altura del muro (m)
    phi_deg: float,         # Angulo de friccion interna (grados)
    beta_deg: float = 0.0,   # Inclinacion del trasdos con la vertical (grados)
    delta_deg: float = 0.0,  # Friccion suelo-muro (grados)
    theta_slope: float = 0.0 # Inclinacion del relleno en la corona (grados)
) -> float:
    """Calcula el coeficiente Ka de Coulomb y el empuje activo total caracteristico."""
    phi = math.radians(phi_deg)
    beta = math.radians(beta_deg)
    delta = math.radians(delta_deg)
    theta = math.radians(theta_slope)
    
    numerator = (math.cos(phi - beta)) ** 2
    denominator_part = math.sqrt(
        (math.sin(phi + delta) * math.sin(phi - theta)) /
        (math.cos(beta + delta) * math.cos(beta - theta))
    )
    denominator = (math.cos(beta) ** 2) * math.cos(beta + delta) * (1.0 + denominator_part) ** 2
    Ka = numerator / denominator if denominator else 0.0
    
    Pa = 0.5 * Ka * gamma_kN_m3 * (H_m ** 2)
    return Pa

def mononobe_okabe_seismic_coefficient(
    phi_deg: float,         # Angulo de friccion interna (grados)
    kh: float,              # Coeficiente sismico horizontal (e.g. 0.15)
    kv: float = 0.0,        # Coeficiente sismico vertical (e.g. 0.0)
    beta_deg: float = 0.0,   # Inclinacion del trasdos (grados)
    delta_deg: float = 0.0,  # Friccion suelo-muro (grados)
    theta_slope: float = 0.0 # Inclinacion del relleno (grados)
) -> float:
    """Calcula el coeficiente sismico activo Kae de Mononobe-Okabe para muros."""
    phi = math.radians(phi_deg)
    beta = math.radians(beta_deg)
    delta = math.radians(delta_deg)
    theta = math.radians(theta_slope)
    
    # Angulo sismico del terreno
    psi = math.atan(kh / (1.0 - kv))
    
    numerator = (math.cos(phi - psi - beta)) ** 2
    denominator_part = math.sqrt(
        (math.sin(phi + delta) * math.sin(phi - psi - theta)) /
        (math.cos(beta + delta) * math.cos(theta - beta))
    )
    denominator = math.cos(psi) * (math.cos(beta) ** 2) * math.cos(beta + delta + psi) * (1.0 + denominator_part) ** 2
    Kae = numerator / denominator if denominator else 0.0
    return Kae

def audit_retaining_wall_safety(
    W_wall_kN: float,       # Peso total del muro de gaviones por metro (kN/m)
    x_cg_m: float,          # Brazo de palanca del centro de gravedad desde la puntera (m)
    H_m: float,             # Altura del muro (m)
    Pa_kN: float,           # Empuje activo horizontal total (kN/m)
    Pv_kN: float = 0.0,     # Fuerza vertical estabilizadora del empuje (kN/m)
    B_base_m: float = 2.0,  # Ancho de la base del muro (m)
    friction_coefficient: float = 0.55, # Friccion base-terreno (tan(delta_base))
    q_allowable_kPa: float = 250.0      # Capacidad portante admisible (kPa)
) -> dict[str, float | bool | str]:
    """Audita los factores de seguridad de un muro de gaviones contra vuelco y deslizamiento.
    
    Según los límites clásicos geotecnicos de ASD (vuelco FS >= 2.0, deslizamiento FS >= 1.5).
    """
    # 1. Momentos
    M_resisting = W_wall_kN * x_cg_m + Pv_kN * B_base_m
    M_overturning = Pa_kN * (H_m / 3.0)
    
    FS_overturning = M_resisting / M_overturning if M_overturning else float("inf")
    
    # 2. Deslizamiento
    N_total = W_wall_kN + Pv_kN
    R_resisting = N_total * friction_coefficient
    FS_sliding = R_resisting / Pa_kN if Pa_kN else float("inf")
    
    # 3. Presiones de contacto
    e = (B_base_m / 2.0) - (M_resisting - M_overturning) / N_total if N_total else 0.0
    # Presión maxima
    if e <= B_base_m / 6.0:
        q_max = (N_total / B_base_m) * (1.0 + 6.0 * e / B_base_m)
    else:
        q_max = 2.0 * N_total / (3.0 * (B_base_m / 2.0 - e))
        
    ok_ov = FS_overturning >= 2.0
    ok_sl = FS_sliding >= 1.5
    ok_q = q_max <= q_allowable_kPa
    
    return {
        "resisting_moment_kNm_m": M_resisting,
        "overturning_moment_kNm_m": M_overturning,
        "FS_overturning": FS_overturning,
        "ok_overturning": ok_ov,
        "resisting_sliding_force_kN_m": R_resisting,
        "driving_sliding_force_kN_m": Pa_kN,
        "FS_sliding": FS_sliding,
        "ok_sliding": ok_sl,
        "eccentricity_m": e,
        "q_max_kPa": q_max,
        "ok_bearing": ok_q,
        "safety_status": "COMPLETAMENTE SEGURO" if (ok_ov and ok_sl and ok_q) else "INSUFICIENTE SEGURIDAD"
    }
