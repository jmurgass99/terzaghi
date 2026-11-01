"""Separación Semántica -> Malla de Columna de Suelo (SoilColumnMapping) para Terzaghi.

Mapea estratos sísmicos/geotécnicos (`stratum_to_sublayers`) y tramos de pilote lateral
(`depth_to_pysprings`) a una malla refinada de subcapas 1D para propagación de ondas SH
(recursión de impedancias de Kramer) y muelles no lineales p-y.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np

from .wave_propagation_1d import SoilLayer, propagate_sh_wave


@dataclass(frozen=True)
class SemanticStratum:
    id: str
    thickness_m: float
    Vs_m_per_s: float
    density_kg_m3: float = 1900.0
    damping_ratio: float = 0.05
    p_ult_kN_m: float = 180.0
    k_py_kN_m3: float = 12000.0


@dataclass
class SoilColumnMapping:
    """Mapeo bidireccional Estrato Semántico -> Subcapas 1D y Muelles p-y."""
    stratum_to_sublayers: Dict[str, List[int]] = field(default_factory=dict)
    sublayer_to_stratum: Dict[int, str] = field(default_factory=dict)
    depth_to_pysprings: Dict[str, List[int]] = field(default_factory=dict)


@dataclass
class Sublayer1DNode:
    index: int
    stratum_id: str
    z_mid_m: float
    dz_m: float
    Vs_m_per_s: float
    density_kg_m3: float
    damping_ratio: float
    k_py_secant_kN_m2: float


def build_soil_column_mesh(
    strata: List[SemanticStratum],
    divisions_per_stratum: int = 4,
    lateral_disp_m: float = 0.015,
    bedrock_Vs: float = 1200.0,
) -> Tuple[List[Sublayer1DNode], SoilColumnMapping, Dict[str, float]]:
    """Subdivide cada estrato en `divisions_per_stratum` subcapas y ejecuta propagación SH 1D."""
    div = max(1, int(divisions_per_stratum))
    mapping = SoilColumnMapping()
    sublayers: List[Sublayer1DNode] = []
    wave_layers: List[SoilLayer] = []

    z_cursor = 0.0
    for st in strata:
        dz = st.thickness_m / div
        mapping.stratum_to_sublayers[st.id] = []
        for _ in range(div):
            idx = len(sublayers)
            z_mid = z_cursor + 0.5 * dz
            # Rigidez secante hiperbólica p-y integrada en el espesor dz
            k_sec = (
                (st.p_ult_kN_m * st.k_py_kN_m3 * z_mid)
                / max(st.p_ult_kN_m + st.k_py_kN_m3 * z_mid * abs(lateral_disp_m), 1e-6)
            ) * dz
            sublayers.append(
                Sublayer1DNode(
                    index=idx,
                    stratum_id=st.id,
                    z_mid_m=z_mid,
                    dz_m=dz,
                    Vs_m_per_s=st.Vs_m_per_s,
                    density_kg_m3=st.density_kg_m3,
                    damping_ratio=st.damping_ratio,
                    k_py_secant_kN_m2=k_sec,
                )
            )
            wave_layers.append(
                SoilLayer(
                    thickness_m=dz,
                    Vs_m_per_s=st.Vs_m_per_s,
                    density_kg_m3=st.density_kg_m3,
                    damping_ratio=st.damping_ratio,
                )
            )
            mapping.stratum_to_sublayers[st.id].append(idx)
            mapping.sublayer_to_stratum[idx] = st.id
            z_cursor += dz

    mapping.depth_to_pysprings["PILE-LATERAL"] = list(range(len(sublayers)))

    t = np.linspace(0.0, 4.0, 400)
    ricker = (1.0 - 2.0 * (np.pi * 2.5 * (t - 1.0)) ** 2) * np.exp(-((np.pi * 2.5 * (t - 1.0)) ** 2))
    prop = propagate_sh_wave(
        input_accel=ricker,
        dt_s=float(t[1] - t[0]),
        profile=wave_layers,
        bedrock_Vs=bedrock_Vs,
        use_impedance_recursion=True,
    )

    summary = {
        "total_depth_m": z_cursor,
        "sublayer_count": float(len(sublayers)),
        "amplification_factor": prop.amplification_factor,
        "peak_freq_Hz": prop.peak_amplification_freq_Hz,
        "total_py_stiffness_kN_m": sum(s.k_py_secant_kN_m2 for s in sublayers),
    }
    return sublayers, mapping, summary
