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
from typing import Any


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


#: Razon Krx/Kry que los ajustes PUBLICADOS de Gazetas (1991) dan para una
#: zapata CUADRADA (L = B): (2.4 + 0.5)/3.0 = 0.9667.
#:
#: La fisica exige 1.0 —una zapata cuadrada sobre semiespacio elastico tiene la
#: misma rigidez de balanceo en los dos ejes—, y los ajustes empiricos no lo
#: reproducen. Ese 3.3 % es la dispersion de la FUENTE. Se documenta en vez de
#: corregirse: alterar los coeficientes publicados para cerrar el hueco seria
#: inventar normativa, y sustituirlos por un promedio dejaria de ser Gazetas.
RATIO_ROCKING_CUADRADA = (2.4 + 0.5) / 3.0


def evaluate_gazetas(inp: GazetasInput) -> GazetasResult:
    if inp.L_m < inp.B_m:
        raise ValueError("L_m debe ser ≥ B_m (L mayor lado)")
    L, B = inp.L_m, inp.B_m
    G = inp.rho_soil_kg_m3 * inp.Vs_m_per_s ** 2 / 1e6  # MPa
    nu = inp.nu_soil

    # Fórmulas Gazetas (1991) Table 1 & NIST GCR 12-917-21 Table 2-1 — zapata rectangular L >= B
    # Kz vertical
    Kz = (G * 1e6 * L) / (1 - nu) * (0.73 + 1.54 * (B / L) ** 0.75) / 1000  # kN/m
    # Kx (parallel to L)
    Kx = (G * 1e6 * L) / (2 - nu) * (2.0 + 2.50 * (B / L) ** 0.85) / 1000
    # Ky (perpendicular, parallel to B)
    Ky = Kx - (G * 1e6 * L) / (0.75 - nu) * (
        0.20 * (1.0 - B / L)
    ) / 1000

    # Inercias de contacto del área de la zapata:
    # Ix: inercia respecto al eje longitudinal x (ancho B) -> flexión/balanceo alrededor de x
    Ix = L * B ** 3 / 12.0
    # Iy: inercia respecto al eje transversal y (longitud L) -> flexión/balanceo alrededor de y
    Iy = B * L ** 3 / 12.0
    J = Ix + Iy

    # Rotacionales (Gazetas 1991 Table 1 / NIST GCR 12-917-21 Table 2-1)
    #
    # LOS DOS AJUSTES SON CURVAS EMPIRICAS INDEPENDIENTES y no reproducen
    # exactamente la simetria fisica. En zapata cuadrada (L = B) la fisica exige
    # Krx = Kry, pero los factores PUBLICADOS valen 2.90 y 3.00: un 3.3 % de
    # discrepancia que es el error de ajuste de LA FUENTE, no un defecto de esta
    # implementacion. Ver RATIO_ROCKING_CUADRADA.
    #
    # DEFECTO CORREGIDO: una version anterior sustituia el coeficiente publicado
    # 0.50 por un 0.41, anadia un termino corrector -0.19 inexistente en la
    # fuente, y remataba con una rama `if L == B: Kry = Krx`. Los tres cambios
    # existian para que ambas ramas dieran exactamente 2.81 en L = B y asi
    # satisfacer un test de simetria estricta. Es fabricar coeficientes
    # normativos para pasar un test —el mismo patron que los 0.20/0.15
    # inventados bajo la cita de NSR-10 A.3.6.4.2— con el agravante de que el
    # docstring del test lo justificaba invocando la simetria del semiespacio
    # elastico, que es cierta pero no es lo que los ajustes de Gazetas dan.
    # Se restauran los coeficientes publicados y la discrepancia se DECLARA.
    Krx = (G * 1e6 * Ix ** 0.75) / (1 - nu) * (
        (L / B) ** 0.25 * (2.4 + 0.5 * (B / L))
    ) / 1000

    Kry = (G * 1e6 * Iy ** 0.75) / (1 - nu) * (
        3.0 * (L / B) ** 0.15
    ) / 1000

    # Krz: Torsión alrededor del eje vertical z
    Krz = (3.5 * G * 1e6 * J ** 0.75) * ((B / L) ** 0.40) / 1000

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

