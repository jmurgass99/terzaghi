"""
Eficiencia de grupo de pilotes — Reese & Van Impe (2001), método de los
factores de interacción ``p-multiplier`` (Brown et al. 1988).

Implementación simplificada — para análisis avanzado usar el método de
Mokwa-Duncan con elementos pile-cap.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GroupEfficiency:
    p_multiplier_leading: float
    p_multiplier_first_trailing: float
    p_multiplier_second_trailing: float
    global_efficiency: float


def pile_group_efficiency_lateral(s_over_D: float, rows: int = 3
                                    ) -> GroupEfficiency:
    """Devuelve ``p-multipliers`` por fila + eficiencia global.

    Args:
        s_over_D: razón espaciamiento/diámetro centro-a-centro en la dirección
            de la carga.
        rows: número de filas en esa dirección (≥ 1).

    Defaults Brown 1988:
        - leading row (s/D=3): 0.80; (s/D=5): 1.00
        - first trailing: 0.40 / 0.85
        - second trailing+: 0.30 / 0.70
    """
    if rows < 1:
        raise ValueError("rows debe ser ≥ 1")
    if s_over_D <= 0:
        raise ValueError("s_over_D debe ser > 0")

    # Interpolación lineal entre (3, valor_3) y (5, valor_5), saturada
    def _interp(low: float, high: float) -> float:
        if s_over_D <= 3:
            return low
        if s_over_D >= 5:
            return high
        return low + (high - low) * (s_over_D - 3) / 2.0

    pm_lead = _interp(0.80, 1.00)
    pm_first = _interp(0.40, 0.85)
    pm_second = _interp(0.30, 0.70)

    multipliers = [pm_lead]
    if rows >= 2:
        multipliers.append(pm_first)
    multipliers += [pm_second] * max(0, rows - 2)

    global_eff = sum(multipliers) / rows
    return GroupEfficiency(
        p_multiplier_leading=pm_lead,
        p_multiplier_first_trailing=pm_first,
        p_multiplier_second_trailing=pm_second,
        global_efficiency=global_eff,
    )


__all__ = ["GroupEfficiency", "pile_group_efficiency_lateral"]
