"""Curvas P-y dinámicas para monopilotes eólicos de gran diámetro según DNV-RP-C212 / API RP 2GEO.

Calcula curvas P-y cíclicas y dinámicas (frecuenciales) considerando el diámetro del monopilote,
el efecto de degradación cíclica (número de ciclos N) y la amplificación dinámica por inercia del suelo.
"""

from __future__ import annotations

import math
import numpy as np
from typing import List, Tuple
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schemas de Entrada Pydantic v2
# ---------------------------------------------------------------------------

class MonopileDynamicPyInput(BaseModel):
    """Parámetros de entrada para el cálculo de curvas P-y dinámicas en monopilotes."""
    z_m: float = Field(..., description="Profundidad bajo la superficie libre en metros", ge=0.0)
    D_m: float = Field(..., description="Diámetro del monopilote en metros", gt=0.0)
    Vs_m_per_s: float = Field(..., description="Velocidad de ondas de cortante en el suelo en m/s", gt=0.0)
    rho_soil_kg_m3: float = Field(1900.0, description="Densidad del suelo en kg/m³", gt=0.0)
    
    # Parámetros mecánicos de resistencia (dependen de la tipología)
    soil_type: str = Field("clay", description="Tipo de suelo: 'clay' (arcilla) o 'sand' (arena)")
    su_kPa: float = Field(100.0, description="Resistencia al corte no drenada (para arcilla) en kPa", ge=0.0)
    phi_deg: float = Field(32.0, description="Ángulo de fricción interna (para arena) en grados", ge=0.0, le=50.0)
    gamma_kN_m3: float = Field(18.0, description="Peso específico efectivo del suelo en kN/m³", gt=0.0)
    eps_50: float = Field(0.01, description="Deformación al 50% del esfuerzo desviador máximo (arcillas)", gt=0.0)
    k_pH_kN_m3: float = Field(25000.0, description="Módulo de balasto horizontal de Terzaghi en kN/m³", gt=0.0)
    
    # Parámetros dinámicos y cíclicos
    frequency_Hz: float = Field(0.2, description="Frecuencia de la carga del rotor o del oleaje (frecuencia excitación) en Hz", gt=0.0)
    num_cycles: int = Field(1000, description="Número de ciclos de carga acumulados en la tormenta/fatiga", ge=1)
    degradation_coef: float = Field(0.08, description="Coeficiente de degradación cíclica del suelo (lambda_deg)", ge=0.0, le=0.3)
    dynamic_coef: float = Field(0.15, description="Factor de amplificación dinámica del suelo (beta_dyn)", ge=0.0, le=0.5)
    n_points: int = Field(50, description="Número de puntos para trazar la curva P-y", ge=10, le=200)


# ---------------------------------------------------------------------------
# Schemas de Salida Pydantic v2
# ---------------------------------------------------------------------------

class MonopileDynamicPyOutput(BaseModel):
    """Resultados de la curva P-y dinámica para el monopilote."""
    z_m: float
    D_m: float
    p_ult_static_kN_m: float
    p_ult_cyclic_kN_m: float
    stiffness_multiplier: float
    y_m: List[float]
    p_static_kN_m: List[float]
    p_dynamic_kN_m: List[float]


# ---------------------------------------------------------------------------
# Core Algorítmico de Curvas P-y Cíclicas/Dinámicas
# ---------------------------------------------------------------------------

def calculate_monopile_dynamic_py(inp: MonopileDynamicPyInput) -> MonopileDynamicPyOutput:
    """Calcula las curvas P-y estáticas y dinámicas cíclicas para monopilotes eólicos."""
    # 1. Calcular la resistencia última estática p_ult (según tipo de suelo)
    if inp.soil_type.lower() == "clay":
        # Matlock (1970) para arcilla blanda
        J = 0.5
        factor = 3.0 + (inp.gamma_kN_m3 * inp.z_m) / max(inp.su_kPa, 1e-3) + (J * inp.z_m) / inp.D_m
        factor = min(factor, 9.0)
        p_ult_static = factor * inp.su_kPa * inp.D_m  # kN/m
        
        # Parámetro de deformación de referencia
        y_50 = 2.5 * inp.eps_50 * inp.D_m
        y_max = 15.0 * y_50
        y_arr = np.linspace(0.0, y_max, inp.n_points)
        
        # Curva estática base
        p_static = np.where(y_arr < 8.0 * y_50,
                            0.5 * p_ult_static * np.cbrt(y_arr / y_50),
                            p_ult_static)
        p_static = np.minimum(p_static, p_ult_static)
        
    else:  # sand
        # Reese-Cox-Koop simplificado para arena
        phi_rad = math.radians(inp.phi_deg)
        Kp = (1.0 + math.sin(phi_rad)) / (1.0 - math.sin(phi_rad))
        Ka = 1.0 / Kp
        
        p_ult_wedge = (Kp ** 2 - Ka) * inp.gamma_kN_m3 * inp.z_m * inp.D_m
        p_ult_deep = Kp * inp.gamma_kN_m3 * inp.z_m * inp.D_m
        p_ult_static = min(p_ult_wedge, p_ult_deep)
        p_ult_static = max(p_ult_static, 1e-3)
        
        k_init = inp.k_pH_kN_m3 * max(inp.z_m, 1e-3)
        y_ref = p_ult_static / k_init
        y_max = 12.0 * y_ref
        y_arr = np.linspace(0.0, y_max, inp.n_points)
        
        # Curva estática hiperbólica
        p_static = (k_init * y_arr) / (1.0 + y_arr / y_ref)
        
    # 2. Degradación Cíclica debido al número de ciclos N (DNV-RP-C212)
    # p_ult_cyclic = p_ult_static * (1 - lambda_deg * log10(N))
    reduction_factor = 1.0 - inp.degradation_coef * math.log10(inp.num_cycles)
    reduction_factor = max(reduction_factor, 0.3)  # Limitar reducción al 70% de pérdida máximo
    p_ult_cyclic = p_ult_static * reduction_factor
    
    # 3. Factor de Rigidez Dinámica (Frecuencial por efectos de inercia y amortiguamiento por radiación)
    # a0 = omega * D / Vs
    omega = 2.0 * math.pi * inp.frequency_Hz
    a0 = (omega * inp.D_m) / inp.Vs_m_per_s
    
    # stiffness_multiplier = 1 + beta_dyn * a0^2
    stiffness_multiplier = 1.0 + inp.dynamic_coef * (a0 ** 2)
    
    # 4. Generación de las curvas definitivas
    # La curva cíclica y dinámica se construye aplicando la reducción en resistencia (p_ult_cyclic)
    # y la amplificación de rigidez inicial (stiffness_multiplier)
    p_dynamic = []
    for y_val, p_stat_val in zip(y_arr, p_static):
        # Escalamiento de la rigidez inicial y corte por degradación cíclica
        p_dyn_val = p_stat_val * reduction_factor * stiffness_multiplier
        p_dyn_val = min(p_dyn_val, p_ult_cyclic)
        p_dynamic.append(p_dyn_val)
        
    return MonopileDynamicPyOutput(
        z_m=inp.z_m,
        D_m=inp.D_m,
        p_ult_static_kN_m=p_ult_static,
        p_ult_cyclic_kN_m=p_ult_cyclic,
        stiffness_multiplier=stiffness_multiplier,
        y_m=y_arr.tolist(),
        p_static_kN_m=p_static.tolist(),
        p_dynamic_kN_m=p_dynamic,
    )
