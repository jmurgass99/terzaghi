"""Resortes dinámicos y amortiguadores de interacción suelo-estructura (SSI) según Gazetas (1991) y Novak.

Calcula las impedancias dinámicas complejas (rigideces dinámicas y dashpots de amortiguamiento)
para las 6 cimientos superficiales rectangulares.
"""

from __future__ import annotations

import math
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schemas de Entrada Pydantic v2
# ---------------------------------------------------------------------------

class SsiSpringsInput(BaseModel):
    """Parámetros de entrada para el cálculo de resortes dinámicos SSI."""
    L_m: float = Field(..., description="Longitud mayor de la zapata en metros", gt=0.0)
    B_m: float = Field(..., description="Ancho menor de la zapata en metros", gt=0.0)
    Vs_m_per_s: float = Field(..., description="Velocidad de ondas de cortante del suelo (Vs) en m/s", gt=0.0)
    rho_soil_kg_m3: float = Field(1900.0, description="Densidad del suelo en kg/m³", gt=0.0)
    nu_soil: float = Field(0.35, description="Relación de Poisson del suelo (nu)", ge=0.0, le=0.5)
    frequency_Hz: float = Field(5.0, description="Frecuencia de excitación del sistema en Hz", gt=0.0)
    material_damping: float = Field(0.05, description="Razón de amortiguamiento material/histerético del suelo (damping ratio, e.g. 0.05 = 5%)", ge=0.0, le=0.5)


# ---------------------------------------------------------------------------
# Schemas de Salida Pydantic v2
# ---------------------------------------------------------------------------

class SsiSpringsOutput(BaseModel):
    """Resultados de impedancias dinámicas SSI (stiffness + damping)."""
    G_soil_MPa: float
    omega_rad_s: float
    a0_dimensionless: float
    
    # Rigideces estáticas base
    Kz_static_kN_m: float
    Kx_static_kN_m: float
    Ky_static_kN_m: float
    Krx_static_kNm_rad: float
    Kry_static_kNm_rad: float
    Krz_static_kNm_rad: float
    
    # Rigideces dinámicas (multiplicadas por k(omega))
    Kz_dynamic_kN_m: float
    Kx_dynamic_kN_m: float
    Ky_dynamic_kN_m: float
    Krx_dynamic_kNm_rad: float
    Kry_dynamic_kNm_rad: float
    Krz_dynamic_kNm_rad: float
    
    # Amortiguamiento por radiación (dashpots)
    Cz_radiation_kNs_m: float
    Cx_radiation_kNs_m: float
    Cy_radiation_kNs_m: float
    Crx_radiation_kNms_rad: float
    Cry_radiation_kNms_rad: float
    Crz_radiation_kNms_rad: float
    
    # Amortiguamiento equivalente total (radiación + material)
    Cz_total_kNs_m: float
    Cx_total_kNs_m: float
    Cy_total_kNs_m: float
    Crx_total_kNms_rad: float
    Cry_total_kNms_rad: float
    Crz_total_kNms_rad: float


# ---------------------------------------------------------------------------
# Core Algorítmico SSI Gazetas/Novak
# ---------------------------------------------------------------------------

def calculate_ssi_springs(inp: SsiSpringsInput) -> SsiSpringsOutput:
    """Calcula las impedancias dinámicas aplicando Gazetas (1991) y Novak."""
    if inp.L_m < inp.B_m:
        raise ValueError("L_m debe ser mayor o igual a B_m (L_m representa el lado largo).")
        
    L = inp.L_m
    B = inp.B_m
    A_footing = L * B  # Área en m²
    
    # 1. Propiedades dinámicas del suelo
    # G = rho * Vs^2
    G_Pa = inp.rho_soil_kg_m3 * (inp.Vs_m_per_s ** 2)
    G_MPa = G_Pa / 1e6
    nu = inp.nu_soil
    
    omega = 2.0 * math.pi * inp.frequency_Hz  # rad/s
    
    # Frecuencia adimensional a0 = (omega * B_half) / Vs
    # Nota: Muchas referencias usan la mitad del ancho (B/2) para la definición estándar de a0.
    B_half = B / 2.0
    a0 = (omega * B_half) / inp.Vs_m_per_s
    
    # Velocidad de compresión "Lysmer's Analog" (waves of compression in infinite space)
    # VLa = 3.4 / (pi * (1 - nu)) * Vs
    VLa = (3.4 * inp.Vs_m_per_s) / (math.pi * (1.0 - nu))
    
    # Inercias de área de la fundación
    Ix = (B * (L ** 3)) / 12.0  # Rocking alrededor del eje corto X
    Iy = (L * (B ** 3)) / 12.0  # Rocking alrededor del eje largo Y
    J_polar = Ix + Iy           # Torsión
    
    # 2. Rigideces estáticas de Gazetas (1991)
    # Vertical Z
    Kz_static = ((G_Pa * L) / (1.0 - nu)) * (0.73 + 1.54 * ((B / L) ** 0.75))
    
    # Horizontal X (dirección paralela al eje largo L)
    Kx_static = ((G_Pa * L) / (2.0 - nu)) * (2.0 + 2.5 * ((B / L) ** 0.85))
    
    # Horizontal Y (dirección paralela al eje corto B)
    Ky_static = Kx_static - ((G_Pa * L) / (0.75 - nu)) * (0.1 * (1.0 - B / L))
    
    # Rotación Rocking alrededor de X (Krx)
    Krx_static = ((G_Pa * (Iy ** 0.75)) / (1.0 - nu)) * (3.0 * ((L / B) ** 0.15))
    
    # Rotación Rocking alrededor de Y (Kry)
    Kry_static = ((G_Pa * (Ix ** 0.75)) / (1.0 - nu)) * (3.73 * ((L / B) ** 2.4) + 0.27)
    
    # Torsión Z (Krz)
    Krz_static = G_Pa * (((B**2 + L**2) * B * L) ** 0.75) * 4.25
    
    # Convertir rigideces estáticas a kN/m y kN-m/rad
    Kz_s_kN = Kz_static / 1000.0
    Kx_s_kN = Kx_static / 1000.0
    Ky_s_kN = Ky_static / 1000.0
    Krx_s_kNm = Krx_static / 1000.0
    Kry_s_kNm = Kry_static / 1000.0
    Krz_s_kNm = Krz_static / 1000.0
    
    # 3. Factores modificadores de rigidez dinámica k(omega)
    # Según Gazetas, para cimientos superficiales rectangulares:
    k_z = 1.0 if a0 <= 1.0 else (1.0 - 0.05 * (a0 - 1.0))
    k_z = max(k_z, 0.6)
    
    # Traslacionales horizontales k_x, k_y son prácticamente 1.0 para cimientos superficiales
    k_x = 1.0
    k_y = 1.0
    
    # Rotacionales rocking: disminuyen levemente con la frecuencia
    k_rx = max(1.0 - 0.15 * a0, 0.5)
    k_ry = max(1.0 - 0.20 * a0, 0.4)
    
    # Torsional k_rz es prácticamente 1.0
    k_rz = 1.0
    
    # Rigideces dinámicas finales (kN/m o kN-m/rad)
    Kz_dyn = Kz_s_kN * k_z
    Kx_dyn = Kx_s_kN * k_x
    Ky_dyn = Ky_s_kN * k_y
    Krx_dyn = Krx_s_kNm * k_rx
    Kry_dyn = Kry_s_kNm * k_ry
    Krz_dyn = Krz_s_kNm * k_rz
    
    # 4. Amortiguamiento por radiación (dashpots) en N-s/m o N-s*m/rad
    # Vertical: Cz = rho * VLa * A_footing
    Cz_rad = inp.rho_soil_kg_m3 * VLa * A_footing
    
    # Horizontal (cortante): Cx, Cy = rho * Vs * A_footing
    Cx_rad = inp.rho_soil_kg_m3 * inp.Vs_m_per_s * A_footing
    Cy_rad = Cx_rad
    
    # Rocking X (alrededor del eje largo): Crx = rho * VLa * Iy
    Crx_rad = inp.rho_soil_kg_m3 * VLa * Iy
    
    # Rocking Y (alrededor del eje corto): Cry = rho * VLa * Ix
    Cry_rad = inp.rho_soil_kg_m3 * VLa * Ix
    
    # Torsión Z: Crz = rho * Vs * J_polar
    Crz_rad = inp.rho_soil_kg_m3 * inp.Vs_m_per_s * J_polar
    
    # Convertir a kNs/m o kNms/rad
    Cz_r_kN = Cz_rad / 1000.0
    Cx_r_kN = Cx_rad / 1000.0
    Cy_r_kN = Cy_rad / 1000.0
    Crx_r_kNm = Crx_rad / 1000.0
    Cry_r_kNm = Cry_rad / 1000.0
    Crz_r_kNm = Crz_rad / 1000.0
    
    # 5. Amortiguamiento total (radiación + histerético del material)
    # Hysteretic damping dashpot equivalent: C_mat = (2 * K_static * material_damping) / omega
    C_mat_factor = (2.0 * inp.material_damping) / omega if omega > 0.0 else 0.0
    
    Cz_tot = Cz_r_kN + Kz_s_kN * C_mat_factor
    Cx_tot = Cx_r_kN + Kx_s_kN * C_mat_factor
    Cy_tot = Cy_r_kN + Ky_s_kN * C_mat_factor
    Crx_tot = Crx_r_kNm + Krx_s_kNm * C_mat_factor
    Cry_tot = Cry_r_kNm + Kry_s_kNm * C_mat_factor
    Crz_tot = Crz_r_kNm + Krz_s_kNm * C_mat_factor
    
    return SsiSpringsOutput(
        G_soil_MPa=G_MPa,
        omega_rad_s=omega,
        a0_dimensionless=a0,
        
        Kz_static_kN_m=Kz_s_kN,
        Kx_static_kN_m=Kx_s_kN,
        Ky_static_kN_m=Ky_s_kN,
        Krx_static_kNm_rad=Krx_s_kNm,
        Kry_static_kNm_rad=Kry_s_kNm,
        Krz_static_kNm_rad=Krz_s_kNm,
        
        Kz_dynamic_kN_m=Kz_dyn,
        Kx_dynamic_kN_m=Kx_dyn,
        Ky_dynamic_kN_m=Ky_dyn,
        Krx_dynamic_kNm_rad=Krx_dyn,
        Kry_dynamic_kNm_rad=Kry_dyn,
        Krz_dynamic_kNm_rad=Krz_dyn,
        
        Cz_radiation_kNs_m=Cz_r_kN,
        Cx_radiation_kNs_m=Cx_r_kN,
        Cy_radiation_kNs_m=Cy_r_kN,
        Crx_radiation_kNms_rad=Crx_r_kNm,
        Cry_radiation_kNms_rad=Cry_r_kNm,
        Crz_radiation_kNms_rad=Crz_r_kNm,
        
        Cz_total_kNs_m=Cz_tot,
        Cx_total_kNs_m=Cx_tot,
        Cy_total_kNs_m=Cy_tot,
        Crx_total_kNms_rad=Crx_tot,
        Cry_total_kNms_rad=Cry_tot,
        Crz_total_kNms_rad=Crz_tot,
    )
