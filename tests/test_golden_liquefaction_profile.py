"""Golden test para evaluación automática de licuación multicapa según Boulanger & Idriss (2014).

Criterios de entrega:
1. Si no se suministra perfil SPT -> reportar explícitamente "NO EVALUADO (sin datos de SPT)".
2. Si se suministra perfil SPT -> ejecutar Boulanger-Idriss multicapa y reportar FS por estrato.
"""
from __future__ import annotations

import pytest
from terzaghi.liquefaction.boulanger_idriss import (
    evaluate_spt_profile_liquefaction,
    evaluate_bi2014,
    BoulangerIdrissInput,
)


def test_golden_liquefaction_without_spt_profile():
    """GOLDEN. Perfil SPT no suministrado -> 'NO EVALUADO (sin datos de SPT)'."""
    res_none = evaluate_spt_profile_liquefaction(spt_layers=None)
    assert res_none.evaluated is False
    assert res_none.status == "NO EVALUADO (sin datos de SPT)"
    assert res_none.layers == []
    assert res_none.min_FS is None

    res_empty = evaluate_spt_profile_liquefaction(spt_layers=[])
    assert res_empty.evaluated is False
    assert res_empty.status == "NO EVALUADO (sin datos de SPT)"


def test_golden_liquefaction_with_spt_profile_strata():
    """GOLDEN. Perfil SPT suministrado -> evaluación multicapa B&I 2014 con FS por estrato."""
    spt_data = [
        # Estrato 1: Arena suelta superficial (N1_60 = 8) -> susceptible a licuación
        {"depth_m": 3.0, "sigma_v_kPa": 54.0, "sigma_v_eff_kPa": 34.0, "N1_60cs": 8.0},
        # Estrato 2: Arena densa profunda (N1_60 = 30) -> no licuable
        {"depth_m": 8.0, "sigma_v_kPa": 144.0, "sigma_v_eff_kPa": 94.0, "N1_60cs": 30.0},
    ]

    res = evaluate_spt_profile_liquefaction(spt_layers=spt_data, a_max_g=0.35, Mw=7.5)

    assert res.evaluated is True
    assert res.status == "EVALUADO (Boulanger & Idriss 2014)"
    assert len(res.layers) == 2

    layer1 = res.layers[0]
    layer2 = res.layers[1]

    # Estrato 1 debe tener FS < 1.0 (licuable)
    assert layer1["is_liquefiable"] is True
    assert layer1["FS"] < 1.0

    # Estrato 2 debe tener FS > 1.2 (seguro)
    assert layer2["is_liquefiable"] is False
    assert layer2["FS"] > 1.2

    # Verificación de que el mínimo FS reportado es el del estrato 1
    assert res.min_FS == pytest.approx(layer1["FS"], rel=1e-5)
    assert res.has_liquefiable_stratum is True
