"""Bridge Terzaghi -> FastSAP: wire P-y curves to SAP nonlinear link springs.

Dado un perfil de suelo discretizado en nodos, genera curvas P-y y produce
los datos de spring no-lineales para SAP (link MultiLinearPlastic).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class PySpringNode:
    z_m: float
    D_m: float
    su_kPa: float | None = None
    phi_deg: float | None = None
    gamma_kN_m3: float = 18.0
    k_pH_kN_m3: float = 25_000.0


@dataclass(frozen=True)
class FastSAPPySpringsConfig:
    nodes: tuple[PySpringNode, ...]
    n_points_curve: int = 12
    epsilon_50: float = 0.01
    code: str = "EU"
    sand_model: Literal["legacy", "reese_1974"] = "legacy"


def build_py_curve(
    node: PySpringNode,
    n: int = 12,
    epsilon_50: float = 0.01,
    sand_model: Literal["legacy", "reese_1974"] = "legacy",
) -> list[tuple[float, float]]:
    """Construye una curva P-y con n puntos (Matlock-clay o Reese-sand).

    Para suelos granulares (``su_kPa is None`` y ``phi_deg > 0``):
      - ``sand_model="legacy"`` (por defecto): mantiene la curva parabólica de retrocompatibilidad.
      - ``sand_model="reese_1974"``: delega en :func:`terzaghi.piles.py_curves.py_reese_sand`
        (Reese, Cox & Koop 1974).
    """
    pts: list[tuple[float, float]] = []
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
        raise ValueError(
            f"PySpringNode z={node.z_m} m: su_kPa = {node.su_kPa} no define una "
            "curva de Matlock (hace falta su > 0)"
        )
    if node.su_kPa is not None:
        Pu = min(
            9 * node.su_kPa * node.D_m,
            (3 + node.gamma_kN_m3 * node.z_m / node.su_kPa + 0.5 * node.z_m / node.D_m) * node.su_kPa * node.D_m,
        )
        y50 = 2.5 * epsilon_50 * node.D_m
        for i in range(n):
            yi = (i / (n - 1)) * 8.0 * y50
            ratio = (yi / y50) ** (1.0 / 3.0) if yi > 0 else 0.0
            Pi = 0.5 * Pu * ratio
            pts.append((yi, min(Pi, Pu)))
    elif sand_model == "reese_1974":
        from ..piles.py_curves import py_reese_sand

        p_arr, y_arr = py_reese_sand(
            z_m=node.z_m,
            D_m=node.D_m,
            phi_deg=float(node.phi_deg),
            gamma_kN_m3=node.gamma_kN_m3,
            k_pH_kN_m3=node.k_pH_kN_m3,
            n_points=n,
        )
        pts = [(float(yi), float(pi)) for yi, pi in zip(y_arr, p_arr)]
    else:
        Pu = 1.5 * node.gamma_kN_m3 * node.z_m * node.phi_deg / 30.0 * node.D_m
        for i in range(n):
            yi = (i / (n - 1)) * 0.05 * node.D_m
            Pi = Pu * (1 - (1 - yi / (0.05 * node.D_m + 1e-9)) ** 2) if yi > 0 else 0.0
            pts.append((yi, max(Pi, 0)))
    return pts


def export_to_fastsap(
    cfg: FastSAPPySpringsConfig,
    client: Any = None,
    dry_run: bool = False,
) -> dict:
    if cfg.code not in {"EU", "AU", "SG", "US", "CO"}:
        raise ValueError(f"code invalido: {cfg.code}")
    curves = {
        f"PY_z{n.z_m:.2f}": build_py_curve(
            n, cfg.n_points_curve, cfg.epsilon_50, sand_model=cfg.sand_model
        )
        for n in cfg.nodes
    }
    if dry_run or client is None:
        return {"curves": curves, "applied": len(curves), "dry_run": True}
    applied = 0
    failed: dict[str, str] = {}
    for name, pts in curves.items():
        try:
            client.PropLink.SetMultiLinearPlastic(name, len(pts), [p[0] for p in pts], [p[1] for p in pts])
            applied += 1
        except Exception as exc:
            failed[name] = str(exc)
    return {"curves": curves, "applied": applied, "failed": failed, "dry_run": False}


__all__ = ["PySpringNode", "FastSAPPySpringsConfig", "build_py_curve", "export_to_fastsap"]
