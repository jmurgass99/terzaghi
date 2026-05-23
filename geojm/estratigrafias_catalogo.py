"""Catalogo de estratigrafias tipicas Chile / Colombia / Andes.

Datos basicos para inicializar analisis sin trabajo previo.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StratumDef:
    name: str
    z_top_m: float
    z_bot_m: float
    gamma_kN_m3: float
    phi_deg: float
    c_kPa: float
    Es_MPa: float
    SPT_N60: int


_CATALOG: dict[str, tuple[StratumDef, ...]] = {
    "santiago_grava": (
        StratumDef("Relleno", 0, 2, 17, 28, 0, 15, 8),
        StratumDef("Grava 1a depositacion", 2, 8, 22, 42, 0, 120, 50),
        StratumDef("Grava 2a depositacion", 8, 20, 23, 45, 5, 200, 60),
    ),
    "bogota_lacustre": (
        StratumDef("Costra desecada", 0, 3, 16, 0, 30, 8, 4),
        StratumDef("Arcilla blanda", 3, 25, 13, 0, 25, 4, 2),
        StratumDef("Arcilla preconsolidada", 25, 50, 16, 0, 80, 20, 8),
    ),
    "lima_grava": (
        StratumDef("Suelo superficial", 0, 1.5, 17, 30, 5, 20, 10),
        StratumDef("Grava aluvial", 1.5, 30, 21, 40, 0, 150, 50),
    ),
    "andes_volcanico": (
        StratumDef("Ceniza volcanica", 0, 5, 14, 32, 10, 25, 12),
        StratumDef("Toba consolidada", 5, 20, 19, 38, 50, 100, 40),
    ),
}


def list_profiles() -> list[str]:
    return list(_CATALOG.keys())


def get_profile(name: str) -> tuple[StratumDef, ...]:
    if name not in _CATALOG:
        raise KeyError(f"perfil desconocido: {name}; disponibles: {list_profiles()}")
    return _CATALOG[name]


__all__ = ["StratumDef", "list_profiles", "get_profile"]
