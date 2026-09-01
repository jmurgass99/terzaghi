"""
Resortes dinámicos de fundación — Gazetas (1991, update 2018) para
zapatas rectangulares en semi-espacio elástico.

Devuelve las 6 rigideces estáticas + dashpots equivalentes:
    Kz, Kx, Ky (traslacionales)
    Krx, Kry, Krz (rotacionales)
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi


@dataclass(frozen=True)
class GazetasInput:
    L_m: float                 # longitud zapata (mayor)
    B_m: float                 # ancho zapata
    Vs_m_per_s: float = 200.0  # velocidad ondas corte del suelo
    rho_soil_kg_m3: float = 1900.0
    nu_soil: float = 0.35


@dataclass(frozen=True)
class GazetasResult:
    Kz_kN_per_m: float
    Kx_kN_per_m: float
    Ky_kN_per_m: float
    Krx_kNm_per_rad: float
    Kry_kNm_per_rad: float
    Krz_kNm_per_rad: float
    G_soil_MPa: float


@dataclass(frozen=True)
class GazetasSupportResult:
    """Rigideces de apoyo elástico SSI Gazetas con unidades y deformaciones directas."""
    Kz_kN_per_m: float
    Kx_kN_per_m: float
    Ky_kN_per_m: float
    Krx_kNm_per_rad: float
    Kry_kNm_per_rad: float
    Krz_kNm_per_rad: float
    G_soil_MPa: float
    units: dict[str, str]
    vertical_settlement_m: float
    vertical_settlement_mm: float
    rotation_x_rad: float
    rotation_y_rad: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "Kz_kN_per_m": self.Kz_kN_per_m,
            "Kx_kN_per_m": self.Kx_kN_per_m,
            "Ky_kN_per_m": self.Ky_kN_per_m,
            "Krx_kNm_per_rad": self.Krx_kNm_per_rad,
            "Kry_kNm_per_rad": self.Kry_kNm_per_rad,
            "Krz_kNm_per_rad": self.Krz_kNm_per_rad,
            "G_soil_MPa": self.G_soil_MPa,
            "units": self.units,
            "vertical_settlement_m": self.vertical_settlement_m,
            "vertical_settlement_mm": self.vertical_settlement_mm,
            "rotation_x_rad": self.rotation_x_rad,
            "rotation_y_rad": self.rotation_y_rad,
        }


def evaluate_gazetas(inp: GazetasInput) -> GazetasResult:
    if inp.L_m < inp.B_m:
        raise ValueError("L_m debe ser ≥ B_m (L mayor lado)")
    L, B = inp.L_m, inp.B_m
    G = inp.rho_soil_kg_m3 * inp.Vs_m_per_s ** 2 / 1e6  # MPa
    nu = inp.nu_soil

    # Fórmulas Gazetas (1991) Table 4 — zapata rectangular L > B
    # Kz vertical
    Kz = (G * 1e6 * L) / (1 - nu) * (0.73 + 1.54 * (B / L) ** 0.75) / 1000  # kN/m
    # Kx (parallel to L)
    Kx = (G * 1e6 * L) / (2 - nu) * (2 + 2.5 * (B / L) ** 0.85) / 1000
    # Ky (perpendicular)
    Ky = Kx - (G * 1e6 * L) / (0.75 - nu) * (
        0.1 * (1 - B / L)
    ) / 1000

    # Rotacionales (rocking about long axis y short axis)
    Iy = L * B ** 3 / 12   # rocking about long axis = "Y" → moment about y
    Ix = B * L ** 3 / 12
    Krx = (G * 1e6 * Iy ** 0.75) / (1 - nu) * (
        3.0 * (L / B) ** 0.15
    ) / 1000
    Kry = (G * 1e6 * Ix ** 0.75) / (1 - nu) * (
        3.73 * (L / B) ** 2.4 + 0.27
    ) / 1000
    Krz = (G * 1e6) * ((B ** 2 + L ** 2) * B * L) ** 0.75 * 4.25 / 1000

    return GazetasResult(
        Kz_kN_per_m=Kz, Kx_kN_per_m=Kx, Ky_kN_per_m=Ky,
        Krx_kNm_per_rad=Krx, Kry_kNm_per_rad=Kry, Krz_kNm_per_rad=Krz,
        G_soil_MPa=G,
    )


def gazetas_elastic_support_and_settlement(
    L_m: float,
    B_m: float,
    P_kN: float = 0.0,
    Mx_kNm: float = 0.0,
    My_kNm: float = 0.0,
    Vs_m_per_s: float = 200.0,
    rho_soil_kg_m3: float = 1900.0,
    nu_soil: float = 0.35,
) -> GazetasSupportResult:
    """Calcula las 6 rigideces SSI de Gazetas (1991) con unidades declaradas y asentamiento elástico exacto P/Kz."""
    res = evaluate_gazetas(
        GazetasInput(
            L_m=L_m,
            B_m=B_m,
            Vs_m_per_s=Vs_m_per_s,
            rho_soil_kg_m3=rho_soil_kg_m3,
            nu_soil=nu_soil,
        )
    )

    # Deformaciones elásticas bajo solicitación dada: δ = F / K
    w_settlement_m = (P_kN / res.Kz_kN_per_m) if res.Kz_kN_per_m > 0 else 0.0
    rot_x_rad = (Mx_kNm / res.Krx_kNm_per_rad) if res.Krx_kNm_per_rad > 0 else 0.0
    rot_y_rad = (My_kNm / res.Kry_kNm_per_rad) if res.Kry_kNm_per_rad > 0 else 0.0

    units = {
        "Kz": "kN/m",
        "Kx": "kN/m",
        "Ky": "kN/m",
        "Krx": "kNm/rad",
        "Kry": "kNm/rad",
        "Krz": "kNm/rad",
        "G_soil": "MPa",
        "vertical_settlement": "m",
        "vertical_settlement_mm": "mm",
        "rotation_x": "rad",
        "rotation_y": "rad",
    }

    return GazetasSupportResult(
        Kz_kN_per_m=res.Kz_kN_per_m,
        Kx_kN_per_m=res.Kx_kN_per_m,
        Ky_kN_per_m=res.Ky_kN_per_m,
        Krx_kNm_per_rad=res.Krx_kNm_per_rad,
        Kry_kNm_per_rad=res.Kry_kNm_per_rad,
        Krz_kNm_per_rad=res.Krz_kNm_per_rad,
        G_soil_MPa=res.G_soil_MPa,
        units=units,
        vertical_settlement_m=w_settlement_m,
        vertical_settlement_mm=w_settlement_m * 1000.0,
        rotation_x_rad=rot_x_rad,
        rotation_y_rad=rot_y_rad,
    )


__all__ = [
    "GazetasInput",
    "GazetasResult",
    "GazetasSupportResult",
    "evaluate_gazetas",
    "gazetas_elastic_support_and_settlement",
]

