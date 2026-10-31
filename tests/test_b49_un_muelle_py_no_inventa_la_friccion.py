"""B49 (§8.30): un nodo P-y sin datos de resistencia salia como arena de 30 grados.

    Pu = 1.5 * gamma * z * (node.phi_deg or 30.0) / 30.0 * D

Medido (z = 3 m, D = 0.6 m): PySpringNode() sin su ni phi -> Pu = 48.6 kN/m, y
PySpringNode(phi_deg=0.0) -> 48.6 kN/m. Los dos IDENTICOS a phi = 30. Y esa
curva se escribia como muelle MultiLinearPlastic en SAP.

La ruta publicada del hermano (/api/geo/py/reese, terzaghi/api/app.py:41) ya exige
phi con gt=0: se aplica la misma regla.

NO SE DECIDE AQUI: la formula de arena en si no es un modelo P-y reconocido.
Sustituirla por `py_reese_sand` cambia cada muelle ~2x: pregunta abierta.
"""
from __future__ import annotations

import pytest

from terzaghi.integration.fastsap_pysprings import (FastSAPPySpringsConfig,
                                                  PySpringNode, build_py_curve,
                                                  export_to_fastsap)


def test_un_nodo_SIN_datos_de_resistencia_no_es_una_arena_de_30() -> None:
    with pytest.raises(ValueError, match="phi_deg"):
        build_py_curve(PySpringNode(z_m=3.0, D_m=0.6))


def test_un_phi_CERO_sin_su_no_es_una_arena_de_30() -> None:
    with pytest.raises(ValueError, match="cohesivo"):
        build_py_curve(PySpringNode(z_m=3.0, D_m=0.6, phi_deg=0.0))


def test_un_su_cero_ya_no_revienta_con_ZeroDivisionError() -> None:
    with pytest.raises(ValueError, match="su_kPa"):
        build_py_curve(PySpringNode(z_m=3.0, D_m=0.6, su_kPa=0.0))


def test_GUARDA_una_arena_declarada_da_lo_de_siempre() -> None:
    pts = build_py_curve(PySpringNode(z_m=3.0, D_m=0.6, phi_deg=30.0))
    assert pts[-1][1] == pytest.approx(48.6, abs=1e-6)


def test_GUARDA_una_arcilla_declarada_no_cambia() -> None:
    assert len(build_py_curve(PySpringNode(z_m=3.0, D_m=0.6, su_kPa=50.0))) == 12


def test_el_lote_no_escribe_un_muelle_fabricado() -> None:
    cfg = FastSAPPySpringsConfig(nodes=(PySpringNode(z_m=3.0, D_m=0.6),))
    with pytest.raises(ValueError):
        export_to_fastsap(cfg, dry_run=True)
