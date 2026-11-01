"""Pile group lateral - metodo Mokwa & Duncan (2001).

Combinacion de resistencia pasiva del bloque + capacidad lateral
individual de cada pilote con factores de reduccion p-multiplicador.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi, radians, tan


@dataclass(frozen=True)
class MokwaDuncanInput:
    n_rows: int
    n_cols: int
    D_m: float
    s_m: float                  # spacing centro-a-centro
    L_pile_m: float
    H_emb_m: float              # profundidad de empotramiento
    phi_deg: float = 30.0
    c_kPa: float = 0.0
    gamma_kN_m3: float = 18.0
    code: str = "EU"


@dataclass(frozen=True)
class MokwaDuncanResult:
    p_multiplier_avg: float
    H_block_kN: float
    H_individual_kN: float
    H_group_total_kN: float
    code: str


_P_MULT_ROWS = {1: 1.0, 2: 0.7, 3: 0.5, 4: 0.4}


def p_multiplier(row_idx: int) -> float:
    return _P_MULT_ROWS.get(row_idx, 0.4)


def analyze(inp: MokwaDuncanInput) -> MokwaDuncanResult:
    if inp.code not in {"EU", "AU", "SG", "US", "CO"}:
        raise ValueError(f"code invalido: {inp.code}")
    # passive block (Rankine)
    phi = radians(inp.phi_deg)
    Kp = ((1 + (tan(phi)) ** 2) ** 0.5 + tan(phi)) ** 2  # = tan²(45° + φ/2)
    Bf = inp.D_m + (inp.n_cols - 1) * inp.s_m
    Pp_block = 0.5 * Kp * inp.gamma_kN_m3 * inp.H_emb_m ** 2 * Bf + 2 * inp.c_kPa * (Kp ** 0.5) * inp.H_emb_m * Bf
    # individual con p-multiplier
    H_ind_unit = 9.0 * inp.c_kPa * inp.D_m * inp.H_emb_m if inp.c_kPa > 0 else \
                 0.5 * Kp * inp.gamma_kN_m3 * inp.H_emb_m ** 2 * inp.D_m
    p_avg = sum(p_multiplier(r + 1) for r in range(inp.n_rows)) / inp.n_rows
    H_ind_total = p_avg * H_ind_unit * inp.n_rows * inp.n_cols
    H_group = min(Pp_block, H_ind_total)
    return MokwaDuncanResult(p_avg, Pp_block, H_ind_total, H_group, inp.code)


__all__ = ["MokwaDuncanInput", "MokwaDuncanResult", "analyze", "p_multiplier"]
