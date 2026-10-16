"""Bridge GeoJm -> FastSAP: wire P-y curves to SAP nonlinear link springs.

Dado un perfil de suelo discretizado en nodos, genera curvas P-y y produce
los datos de spring no-lineales para SAP (link MultiLinearPlastic).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PySpringNode:
    z_m: float
    D_m: float
    su_kPa: float | None = None
    phi_deg: float | None = None
    gamma_kN_m3: float = 18.0


@dataclass(frozen=True)
class FastSAPPySpringsConfig:
    nodes: tuple[PySpringNode, ...]
    n_points_curve: int = 12
    epsilon_50: float = 0.01
    code: str = "EU"


def build_py_curve(node: PySpringNode, n: int = 12, epsilon_50: float = 0.01) -> list[tuple[float, float]]:
    """Construye una curva P-y con n puntos (Matlock-clay o Reese-sand)."""
    pts = []
    # PRESENCIA de los datos de resistencia (B49, §8.30). Antes la rama de arena
    # hacia `(node.phi_deg or 30.0)`: un nodo SIN su ni phi --los defaults del
    # dataclass-- y un phi = 0.0 medido salian con la resistencia de una arena
    # de 30 grados (Pu = 48.6 kN/m a z = 3 m, D = 0.6 m), y esa curva se escribia
    # como muelle en SAP. La ruta publicada del hermano, /api/geo/py/reese
    # (geojm/api/app.py:41), ya exige phi con gt=0: aqui se aplica la misma regla.
    if node.su_kPa is None and node.phi_deg is None:
        raise ValueError(
            f"PySpringNode z={node.z_m} m: sin su_kPa ni phi_deg; no se fabrica "
            "una resistencia (antes: arena de 30 grados)"
        )
    if node.su_kPa is None and not (node.phi_deg > 0.0):
        raise ValueError(
            f"PySpringNode z={node.z_m} m: phi_deg = {node.phi_deg} sin su_kPa. Un "
            "suelo sin friccion es cohesivo y le falta su; no es una arena de 30 grados"
        )
    if node.su_kPa is not None and not (node.su_kPa > 0.0):
        # Antes: ZeroDivisionError en `gamma*z/su` sin nombrar el nodo.
        raise ValueError(
            f"PySpringNode z={node.z_m} m: su_kPa = {node.su_kPa} no define una "
            "curva de Matlock (hace falta su > 0)"
        )
    if node.su_kPa is not None:
        Pu = min(9 * node.su_kPa * node.D_m,
                 (3 + node.gamma_kN_m3 * node.z_m / node.su_kPa + 0.5 * node.z_m / node.D_m) * node.su_kPa * node.D_m)
        y50 = 2.5 * epsilon_50 * node.D_m
        for i in range(n):
            yi = (i / (n - 1)) * 8.0 * y50
            ratio = (yi / y50) ** (1.0 / 3.0) if yi > 0 else 0.0
            Pi = 0.5 * Pu * ratio
            pts.append((yi, min(Pi, Pu)))
    else:
        # OJO: esta formula NO es un modelo P-y reconocido (JmWorkbench/README.md:276
        # la llama «inventada»). Sustituirla por `py_reese_sand` --el modelo del
        # propio paquete, documentado para muelles SAP/ETABS-- cambia cada muelle
        # de arena ~2x (phi 32: 51.8 -> 95.9 kN/m): es una decision abierta
        # (§8.30-bis en NIGHT_SHIFT_ERRORS.md), no parte de este arreglo.
        Pu = 1.5 * node.gamma_kN_m3 * node.z_m * node.phi_deg / 30.0 * node.D_m
        for i in range(n):
            yi = (i / (n - 1)) * 0.05 * node.D_m
            Pi = Pu * (1 - (1 - yi / (0.05 * node.D_m + 1e-9)) ** 2) if yi > 0 else 0.0
            pts.append((yi, max(Pi, 0)))
    return pts


def export_to_fastsap(cfg: FastSAPPySpringsConfig, client: Any = None,
                      dry_run: bool = False) -> dict:
    if cfg.code not in {"EU", "AU", "SG", "US", "CO"}:
        raise ValueError(f"code invalido: {cfg.code}")
    curves = {f"PY_z{n.z_m:.2f}": build_py_curve(n, cfg.n_points_curve, cfg.epsilon_50)
              for n in cfg.nodes}
    if dry_run or client is None:
        return {"curves": curves, "applied": len(curves), "dry_run": True}
    applied = 0
    failed: dict[str, str] = {}
    for name, pts in curves.items():
        try:
            client.PropLink.SetMultiLinearPlastic(name, len(pts), [p[0] for p in pts], [p[1] for p in pts])
            applied += 1
        except Exception as exc:  # registra el fallo, no lo traga en silencio
            failed[name] = str(exc)
    return {"curves": curves, "applied": applied, "failed": failed, "dry_run": False}


__all__ = ["PySpringNode", "FastSAPPySpringsConfig", "build_py_curve", "export_to_fastsap"]
