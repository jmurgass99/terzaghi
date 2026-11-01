"""
Memoria de calculo — Pile group lateral (Mokwa-Duncan 2001 / Brown et al. 1988).

Render handcalcs paso-a-paso:
    - p-multipliers por fila
    - Capacidad lateral del grupo

Soporta:
    - ``method="mokwa_duncan"`` (por defecto, retrocompatible)
    - ``method="brown_1988"`` (delega en ``terzaghi.piles.group.pile_group_efficiency_lateral``,
      con interpolación entre s/D = 3 y s/D = 5 según Brown et al. 1988 / Reese & Van Impe 2001).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

try:
    import handcalcs.render as _hc_render
    _HAS_HANDCALCS = True
except Exception:
    _HAS_HANDCALCS = False


@dataclass(frozen=True)
class PileGroupLateralInput:
    """Datos de entrada para memoria lateral de grupo de pilotes."""
    n_rows: int                # filas en direccion de la carga
    n_cols: int                # columnas perpendiculares a la carga
    D_m: float                 # diametro del pilote (m)
    s_m: float                 # espaciamiento centro-a-centro (m)
    P_single_kN: float         # capacidad lateral de un pilote individual (kN)
    method: Literal["mokwa_duncan", "brown_1988"] = "mokwa_duncan"


@dataclass(frozen=True)
class PileGroupLateralResult:
    """Resultados de la memoria de grupo lateral."""
    s_over_d: float
    fm_per_row: list[float]
    P_per_row_kN: list[float]
    P_group_kN: float
    efficiency: float
    memo_text: str


def _fm_mokwa_duncan(row_index: int, s_over_d: float) -> float:
    """p-multiplier por fila segun correlacion lineal simplificada Mokwa-Duncan."""
    if row_index <= 1:
        return 1.0
    fm = 0.64 + 0.36 * s_over_d
    return min(fm, 1.0)


def fm_brown_1988(row_index: int, s_over_d: float) -> float:
    """p-multiplier por fila según Brown et al. (1988) / ``terzaghi.piles.group``."""
    from ..piles.group import pile_group_efficiency_lateral

    eff = pile_group_efficiency_lateral(s_over_D=s_over_d, rows=max(row_index, 3))
    if row_index <= 1:
        return eff.p_multiplier_leading
    if row_index == 2:
        return eff.p_multiplier_first_trailing
    return eff.p_multiplier_second_trailing


def render_pile_group_memo(inp: PileGroupLateralInput) -> PileGroupLateralResult:
    """Genera la memoria de calculo paso-a-paso para grupo de pilotes lateral."""
    if inp.n_rows < 1 or inp.n_cols < 1:
        raise ValueError("n_rows y n_cols deben ser >= 1")
    if inp.D_m <= 0 or inp.s_m <= 0:
        raise ValueError("D_m y s_m deben ser > 0")

    s_over_d = inp.s_m / inp.D_m
    n_rows = inp.n_rows
    n_cols = inp.n_cols
    D = inp.D_m
    s = inp.s_m
    P_single = inp.P_single_kN

    fm_list: list[float] = []
    for row in range(1, n_rows + 1):
        if inp.method == "brown_1988":
            fm = fm_brown_1988(row, s_over_d)
        else:
            fm = _fm_mokwa_duncan(row, s_over_d)
        fm_list.append(round(fm, 4))

    P_per_row = [round(fm * P_single * n_cols, 2) for fm in fm_list]
    P_group = sum(P_per_row)

    P_max = n_rows * n_cols * P_single
    efficiency = P_group / P_max if P_max > 0 else 0.0

    memo = _render_memo_text(
        n_rows=n_rows, n_cols=n_cols, D=D, s=s,
        s_over_d=s_over_d, P_single=P_single,
        fm_list=fm_list, P_per_row=P_per_row,
        P_group=P_group, efficiency=efficiency,
        method=inp.method,
    )

    return PileGroupLateralResult(
        s_over_d=round(s_over_d, 3),
        fm_per_row=fm_list,
        P_per_row_kN=P_per_row,
        P_group_kN=round(P_group, 2),
        efficiency=round(efficiency, 4),
        memo_text=memo,
    )


def _render_memo_text(
    n_rows: int, n_cols: int, D: float, s: float,
    s_over_d: float, P_single: float,
    fm_list: list[float], P_per_row: list[float],
    P_group: float, efficiency: float,
    method: str = "mokwa_duncan",
) -> str:
    """Genera texto paso-a-paso de la memoria de calculo."""
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("MEMORIA DE CALCULO — GRUPO DE PILOTES LATERAL")
    method_label = "Brown et al. (1988)" if method == "brown_1988" else "Mokwa-Duncan (2001)"
    lines.append(f"Metodo: {method_label}")
    lines.append("=" * 60)
    lines.append("")

    lines.append("PASO 1: Datos de entrada")
    lines.append("-" * 40)
    lines.append(f"  Filas (n_rows)       = {n_rows}")
    lines.append(f"  Columnas (n_cols)    = {n_cols}")
    lines.append(f"  Diametro (D)         = {D:.3f} m")
    lines.append(f"  Espaciamiento (s)    = {s:.3f} m")
    lines.append(f"  s/D                  = {s_over_d:.3f}")
    lines.append(f"  P_single             = {P_single:.2f} kN")
    lines.append("")

    lines.append(f"PASO 2: p-multipliers por fila ({method_label})")
    lines.append("-" * 40)
    if method == "brown_1988":
        lines.append("  Interpolacion Brown et al. (1988) entre s/D = 3 y s/D = 5:")
    else:
        lines.append("  Fila leading (row 1): fm = 1.0")
        lines.append("  Filas traseras: fm = min(0.64 + 0.36*(s/d), 1.0)")
        lines.append(f"  fm = min(0.64 + 0.36*{s_over_d:.3f}, 1.0)")
        if s_over_d > 0:
            fm_calc = 0.64 + 0.36 * s_over_d
            lines.append(f"  fm = min({fm_calc:.4f}, 1.0) = {min(fm_calc, 1.0):.4f}")
    lines.append("")
    for i, fm in enumerate(fm_list):
        row_label = "leading" if i == 0 else f"trailing {i}"
        lines.append(f"  Fila {i+1} ({row_label}): fm = {fm:.4f}")
    lines.append("")

    lines.append("PASO 3: Capacidad lateral por fila")
    lines.append("-" * 40)
    lines.append("  P_fila = fm * P_single * n_cols")
    lines.append("")
    for i, (fm, P_row) in enumerate(zip(fm_list, P_per_row)):
        lines.append(
            f"  Fila {i+1}: P = {fm:.4f} * {P_single:.2f} * {n_cols} "
            f"= {P_row:.2f} kN"
        )
    lines.append("")

    lines.append("PASO 4: Capacidad total del grupo")
    lines.append("-" * 40)
    lines.append(f"  P_grupo = sum(P_fila) = {P_group:.2f} kN")
    lines.append(f"  P_max (sin reduccion) = {n_rows * n_cols * P_single:.2f} kN")
    lines.append(f"  Eficiencia = P_grupo / P_max = {efficiency:.4f}")
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


__all__ = [
    "PileGroupLateralInput",
    "PileGroupLateralResult",
    "fm_brown_1988",
    "render_pile_group_memo",
]
