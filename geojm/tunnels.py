"""Método de Convergencia-Confinamiento (CCM) y resortes Winkler elastoplásticos para túneles y entibaciones.

Calcula la Curva de Reacción del Terreno (GRC) elastoplástica según Mohr-Coulomb,
la Curva del Soporte (SCC) de concreto/acero, determina el punto de equilibrio
y genera los parámetros de rigidez de resortes Winkler elastoplásticos.
"""

from __future__ import annotations

import math
from typing import List, Tuple
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schemas de Entrada Pydantic v2
# ---------------------------------------------------------------------------

class TunnelWinklerInput(BaseModel):
    """Parámetros de entrada para el análisis de convergencia-confinamiento y resortes Winkler."""
    R0_m: float = Field(..., description="Radio de excavación del túnel circular en metros", gt=0.0)
    P0_kPa: float = Field(..., description="Presión in-situ del terreno far-field (litostática media) en kPa", gt=0.0)
    E_soil_MPa: float = Field(..., description="Módulo de deformación (Young) de la masa de roca/suelo en MPa", gt=0.0)
    nu_soil: float = Field(0.30, description="Relación de Poisson del suelo/roca (nu)", ge=0.0, le=0.5)
    c_kPa: float = Field(..., description="Cohesión característica del terreno en kPa", ge=0.0)
    phi_deg: float = Field(..., description="Ángulo de fricción característica del terreno en grados", ge=0.0, le=50.0)
    
    # Parámetros del Soporte (Lining / Soportes)
    E_liner_GPa: float = Field(30.0, description="Módulo elástico del soporte (e.g. concreto) en GPa", gt=0.0)
    nu_liner: float = Field(0.20, description="Relación de Poisson del soporte", ge=0.0, le=0.4)
    thickness_mm: float = Field(200.0, description="Espesor del revestimiento/soporte en mm", gt=0.0)
    unsupported_convergence_ratio: float = Field(0.30, description="Fracción de convergencia libre ocurrida antes de la instalación del soporte (e.g. 0.30 = 30%)", ge=0.0, le=0.9)
    
    # Puntos de discretización
    n_points: int = Field(50, description="Puntos de trazado para la curva GRC", ge=10, le=200)


# ---------------------------------------------------------------------------
# Schemas de Salida Pydantic v2
# ---------------------------------------------------------------------------

class TunnelWinklerOutput(BaseModel):
    """Resultados del análisis CCM y resortes Winkler del túnel."""
    Pcr_kPa: float
    R_p_at_zero_pressure_m: float
    max_convergence_unsupported_mm: float
    
    # Rigidez de soporte
    K_support_kPa_mm: float
    liner_activation_displacement_mm: float
    
    # Punto de equilibrio
    equilibrium_pressure_kPa: float
    equilibrium_displacement_mm: float
    equilibrium_status: str
    
    # Parámetros de resortes Winkler elastoplásticos
    k_winkler_static_kN_m3: float
    p_yield_kPa: float
    u_yield_mm: float
    
    # Curvas para graficar
    radial_displacement_mm: List[float]
    pi_support_pressure_kPa: List[float]


# ---------------------------------------------------------------------------
# Core Algorítmico de Convergencia-Confinamiento
# ---------------------------------------------------------------------------

def calculate_tunnel_confinement(inp: TunnelWinklerInput) -> TunnelWinklerOutput:
    """Calcula las curvas de reacción del terreno, soporte y equilibrio elastoplástico del túnel."""
    E_Pa = inp.E_soil_MPa * 1e6
    P0_Pa = inp.P0_kPa * 1000.0
    c_Pa = inp.c_kPa * 1000.0
    phi_rad = math.radians(inp.phi_deg)
    
    # 1. Parámetros de Mohr-Coulomb de plastificación
    kp = (1.0 + math.sin(phi_rad)) / (1.0 - math.sin(phi_rad)) if inp.phi_deg > 0 else 1.0
    # Resistencia a compresión simple de la masa rocosa/suelo (sigma_cm)
    sigma_cm_Pa = (2.0 * c_Pa * math.cos(phi_rad)) / (1.0 - math.sin(phi_rad)) if inp.phi_deg > 0 else 2.0 * c_Pa
    
    # Presión interna crítica Pcr que marca el límite elástico/plástico
    Pcr_Pa = (2.0 * P0_Pa - sigma_cm_Pa) / (kp + 1.0)
    Pcr_Pa = max(Pcr_Pa, 0.0)
    Pcr_kPa = Pcr_Pa / 1000.0
    
    # 2. Construcción de la Curva de Reacción del Terreno (GRC)
    pi_vals = []
    u_vals_mm = []
    
    # Rango de presiones internas
    pressures_Pa = [P0_Pa - i * (P0_Pa / (inp.n_points - 1)) for i in range(inp.n_points)]
    
    for Pi in pressures_Pa:
        if Pi >= Pcr_Pa:
            # Fase Elástica
            u = ((1.0 + inp.nu_soil) / E_Pa) * (P0_Pa - Pi) * inp.R0_m
        else:
            # Fase Plástica
            c_cot_phi = c_Pa / math.tan(phi_rad) if inp.phi_deg > 0.0 else 0.0
            if inp.phi_deg > 0.0 and (Pi + c_cot_phi) > 0.0:
                base_rp = (2.0 / (kp + 1.0)) * (P0_Pa + c_cot_phi) / (Pi + c_cot_phi)
                exponent = 1.0 / (kp - 1.0) if abs(kp - 1.0) > 1e-5 else 1.0
                Rp = inp.R0_m * (base_rp ** exponent)
            else:
                Rp = inp.R0_m
                
            u = ((1.0 + inp.nu_soil) / E_Pa) * inp.R0_m * ((P0_Pa - Pcr_Pa) * ((Rp / inp.R0_m) ** 2) + (Pcr_Pa - Pi))
            
        u_vals_mm.append(u * 1000.0)
        pi_vals.append(Pi / 1000.0)
        
    max_conv_unsupported_mm = u_vals_mm[-1]
    
    # 3. Radio plástico máximo a presión interna cero
    if inp.phi_deg > 0.0 and c_Pa > 0.0:
        base_rp_zero = (2.0 / (kp + 1.0)) * (P0_Pa + c_cot_phi) / (c_cot_phi)
        exponent_zero = 1.0 / (kp - 1.0) if abs(kp - 1.0) > 1e-5 else 1.0
        Rp_zero = inp.R0_m * (base_rp_zero ** exponent_zero)
    else:
        Rp_zero = inp.R0_m
        
    # 4. Rigidez y comportamiento del soporte (SCC)
    E_liner_Pa = inp.E_liner_GPa * 1e9
    t_m = inp.thickness_mm / 1000.0
    K_support_Pa_m = (E_liner_Pa * t_m) / ((inp.R0_m ** 2) * (1.0 - (inp.nu_liner ** 2)))
    K_support_kPa_mm = K_support_Pa_m / 1e6
    
    # Desplazamiento de activación del soporte
    liner_activation_disp_mm = inp.unsupported_convergence_ratio * max_conv_unsupported_mm
    
    # 5. Hallar el Punto de Equilibrio mediante interpolación y bisección de alta precisión
    def get_ground_pressure(u_target: float) -> float:
        if u_target <= u_vals_mm[0]:
            return pi_vals[0]
        if u_target >= u_vals_mm[-1]:
            return pi_vals[-1]
        for j in range(1, len(u_vals_mm)):
            if u_vals_mm[j-1] <= u_target <= u_vals_mm[j]:
                denom_interp = u_vals_mm[j] - u_vals_mm[j-1]
                ratio = (u_target - u_vals_mm[j-1]) / denom_interp if denom_interp > 1e-9 else 0.0
                return pi_vals[j-1] + ratio * (pi_vals[j] - pi_vals[j-1])
        return 0.0

    # Comprobar estabilidad física y geométrica
    # Si la convergencia libre máxima sin soporte supera el 10% del radio del túnel,
    # el túnel sufre un colapso plástico incontrolable antes de poder colocar el soporte.
    if max_conv_unsupported_mm > 0.10 * inp.R0_m * 1000.0:
        eq_u = max_conv_unsupported_mm
        eq_P = 0.0
        equilibrium_status = "UNSTABLE_COLLAPSE"
    else:
        # Presión de soporte máxima (a máxima convergencia libre del túnel sin soporte)
        p_s_max = K_support_kPa_mm * (max_conv_unsupported_mm - liner_activation_disp_mm)
        p_g_min = get_ground_pressure(max_conv_unsupported_mm)
        
        if p_s_max < p_g_min:
            # El soporte es tan flexible que incluso al 100% de convergencia no equilibra la presión residual
            eq_u = max_conv_unsupported_mm
            eq_P = 0.0
            equilibrium_status = "UNSTABLE_COLLAPSE"
        else:
            # Resolver p_ground(u) = p_support(u) por bisección en el rango [liner_activation_disp_mm, max_conv_unsupported_mm]
            u_low = liner_activation_disp_mm
            u_high = max_conv_unsupported_mm
            
            # Si ya a u_low la presión del terreno es <= 0 (terreno autoestable sin soporte), equilibra ahí
            if get_ground_pressure(u_low) <= 0.0:
                eq_u = u_low
                eq_P = 0.0
                equilibrium_status = "STABLE"
            else:
                for _ in range(60):
                    u_mid = 0.5 * (u_low + u_high)
                    p_g = get_ground_pressure(u_mid)
                    p_s = K_support_kPa_mm * (u_mid - liner_activation_disp_mm)
                    err = p_g - p_s
                    if abs(err) < 1e-4:
                        break
                    if err > 0.0:
                        u_low = u_mid
                    else:
                        u_high = u_mid
                eq_u = 0.5 * (u_low + u_high)
                eq_P = K_support_kPa_mm * (eq_u - liner_activation_disp_mm)
                
                # Capacidad estructural límite del soporte por aplastamiento (hoop stress yield limit)
                # P_capacity_kPa = yield_strain * E_liner_kPa * t_m / R0
                # Usando yield_strain = 0.0015 para concreto/soporte
                p_capacity_kPa = 0.0015 * (inp.E_liner_GPa * 1e6) * (t_m / inp.R0_m)
                
                if eq_P > p_capacity_kPa:
                    eq_u = max_conv_unsupported_mm
                    eq_P = 0.0
                    equilibrium_status = "UNSTABLE_COLLAPSE"
                elif eq_P < 1e-2 and eq_u >= max_conv_unsupported_mm:
                    # Significa que se estabiliza justo en convergencia libre (autoestable)
                    equilibrium_status = "STABLE"
                else:
                    # El túnel es estable y el revestimiento absorbe presión activa
                    equilibrium_status = "STABLE"
                
    # 6. Parámetros de resortes Winkler Elastoplásticos para análisis estructural
    k_winkler_static_kN_m3 = (inp.E_soil_MPa * 1000.0) / (inp.R0_m * (1.0 + inp.nu_soil))
    p_yield_kPa = sigma_cm_Pa / 1000.0
    u_yield_mm = (p_yield_kPa / (k_winkler_static_kN_m3 + 1e-9)) * 1000.0
    
    return TunnelWinklerOutput(
        Pcr_kPa=Pcr_kPa,
        R_p_at_zero_pressure_m=Rp_zero,
        max_convergence_unsupported_mm=max_conv_unsupported_mm,
        K_support_kPa_mm=K_support_kPa_mm,
        liner_activation_displacement_mm=liner_activation_disp_mm,
        equilibrium_pressure_kPa=eq_P,
        equilibrium_displacement_mm=eq_u,
        equilibrium_status=equilibrium_status,
        k_winkler_static_kN_m3=k_winkler_static_kN_m3,
        p_yield_kPa=p_yield_kPa,
        u_yield_mm=u_yield_mm,
        radial_displacement_mm=u_vals_mm,
        pi_support_pressure_kPa=pi_vals,
    )
