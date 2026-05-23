"""
Asentamientos diferenciales — AuditRule (EN 1997-1 Annex H).

Criterio de distorsion angular delta/L:
    > 1/500  para porticos  → WARNING
    > 1/300  para porticos  → ERROR

donde:
    delta = diferencia absoluta de asentamientos entre zapatas adyacentes (mm)
    L     = distancia entre zapatas adyacentes (m)
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Any, Sequence


@dataclass(frozen=True)
class Finding:
    """Resultado de una regla de auditoria."""
    severity: str          # "INFO" | "WARNING" | "ERROR"
    message: str
    footing_a: str
    footing_b: str
    delta_mm: float        # diferencia de asentamiento
    L_m: float             # distancia entre zapatas
    angular_distortion: float  # delta/L (en mm/mm -> adimensional)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "message": self.message,
            "footing_a": self.footing_a,
            "footing_b": self.footing_b,
            "delta_mm": self.delta_mm,
            "L_m": self.L_m,
            "angular_distortion": self.angular_distortion,
        }


# Limites EN 1997-1 Annex H para porticos
_LIMIT_WARNING = 1 / 500   # distorsion angular
_LIMIT_ERROR = 1 / 300


def check_differential_settlement(
    foundations: Sequence[dict[str, Any]],
) -> list[Finding]:
    """Evalua asentamientos diferenciales entre todos los pares de zapatas.

    Args:
        foundations: lista de zapatas, cada una con claves:
            - ``name`` (str): nombre/ID de la zapata
            - ``settlement_mm`` (float): asentamiento calculado en mm
            - ``x`` (float): coordenada x en metros
            - ``y`` (float): coordenada y en metros

    Returns:
        Lista de ``Finding`` con severity WARNING o ERROR si se superan
        los limites de EN 1997-1 Annex H para porticos.
    """
    if len(foundations) < 2:
        return []

    findings: list[Finding] = []
    n = len(foundations)
    for i in range(n):
        for j in range(i + 1, n):
            fa = foundations[i]
            fb = foundations[j]
            delta_mm = abs(fa["settlement_mm"] - fb["settlement_mm"])
            L_m = hypot(fa["x"] - fb["x"], fa["y"] - fb["y"])
            if L_m < 1e-6:
                continue  # misma posicion, ignorar

            # Distorsion angular: delta(m) / L(m) = delta_mm / (1000 * L_m)
            angular = delta_mm / (1000.0 * L_m)

            if angular > _LIMIT_ERROR:
                findings.append(Finding(
                    severity="ERROR",
                    message=(
                        f"Distorsion angular {angular:.5f} > 1/300 "
                        f"entre {fa['name']} y {fb['name']} — "
                        f"dano estructural probable (EN 1997-1 Annex H)"
                    ),
                    footing_a=fa["name"],
                    footing_b=fb["name"],
                    delta_mm=delta_mm,
                    L_m=L_m,
                    angular_distortion=angular,
                ))
            elif angular > _LIMIT_WARNING:
                findings.append(Finding(
                    severity="WARNING",
                    message=(
                        f"Distorsion angular {angular:.5f} > 1/500 "
                        f"entre {fa['name']} y {fb['name']} — "
                        f"posible dano no-estructural (EN 1997-1 Annex H)"
                    ),
                    footing_a=fa["name"],
                    footing_b=fb["name"],
                    delta_mm=delta_mm,
                    L_m=L_m,
                    angular_distortion=angular,
                ))

    return findings


__all__ = ["Finding", "check_differential_settlement"]
