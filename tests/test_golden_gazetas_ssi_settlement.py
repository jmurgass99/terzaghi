"""Golden test para resortes de Gazetas (1991) como apoyos elásticos SSI y asentamiento vertical P/k exacto.

Fuente:
Gazetas, G. (1991), "Formulas and Charts for Impedances of Surface and Embedded Foundations",
Journal of Geotechnical Engineering, ASCE, Vol. 117, No. 9, pp. 1363-1381.

Derivación analítica a mano:
----------------------------
Zapata rectangular: L = 4.00 m, B = 2.00 m (L/B = 2.0, B/L = 0.50).
Suelo:
    ρ = 2000.0 kg/m³
    Vs = 200.0 m/s
    ν = 0.35
    Módulo de corte: G = ρ · Vs² = 2000 · 200² = 80.0 MPa (80000.0 kPa).

1. Rigidez vertical Kz (Gazetas 1991 Tabla 4):
    Kz = [G · L / (1 - ν)] · [0.73 + 1.54 · (B/L)^0.75]
    (B/L)^0.75 = 0.5^0.75 = 0.5946035575
    Factor de forma = 0.73 + 1.54 · 0.5946035575 = 1.6456894786
    G · L / (1 - ν) = 80000 · 4.00 / 0.65 = 492307.6923077 kN/m
    Kz = 492307.6923077 · 1.6456894786 = 810185.5562 kN/m.

2. Solicitación y Asentamiento vertical P/Kz:
    Carga vertical P = 1620.3711124 kN
    Asentamiento vertical elástico exacto:
        w = P / Kz = 1620.3711124 / 810185.5562 = 0.0020000 m = 2.0000 mm.

3. Unidades declaradas:
    Todas las rigideces y deformaciones reportan explícitamente sus unidades ingenieriles.
"""
from __future__ import annotations

import math
import pytest
from geojm.gazetas_springs import (
    GazetasInput,
    evaluate_gazetas,
    gazetas_elastic_support_and_settlement,
)


def test_golden_gazetas_springs_closed_form_and_p_over_k_settlement():
    """GOLDEN. Validación cerrada de Gazetas (1991) y asentamiento P/Kz."""
    L, B = 4.0, 2.0
    Vs = 200.0
    rho = 2000.0
    nu = 0.35

    # 1. Cálculo directo con evaluate_gazetas
    res = evaluate_gazetas(
        GazetasInput(L_m=L, B_m=B, Vs_m_per_s=Vs, rho_soil_kg_m3=rho, nu_soil=nu)
    )

    G_expected_MPa = rho * (Vs ** 2) / 1e6
    assert res.G_soil_MPa == pytest.approx(80.0, rel=1e-6)

    # Verificación de Kz analítico a mano
    factor_forma = 0.73 + 1.54 * (0.5 ** 0.75)
    kz_expected = (80000.0 * 4.0 / (1.0 - 0.35)) * factor_forma
    assert res.Kz_kN_per_m == pytest.approx(kz_expected, rel=1e-6)
    assert res.Kz_kN_per_m == pytest.approx(810185.556, rel=1e-3)

    # 2. Deformación P / Kz con API de apoyo elástico y unidades declaradas
    P_test_kN = 1620.3711124
    support_res = gazetas_elastic_support_and_settlement(
        L_m=L,
        B_m=B,
        P_kN=P_test_kN,
        Mx_kNm=0.0,
        My_kNm=0.0,
        Vs_m_per_s=Vs,
        rho_soil_kg_m3=rho,
        nu_soil=nu,
    )

    # Unidades obligatorias declaradas
    assert support_res.units["Kz"] == "kN/m"
    assert support_res.units["Krx"] == "kNm/rad"
    assert support_res.units["vertical_settlement_mm"] == "mm"

    # Asentamiento vertical exacto P / Kz = 2.000 mm
    assert support_res.vertical_settlement_m == pytest.approx(0.0020, rel=1e-5)
    assert support_res.vertical_settlement_mm == pytest.approx(2.0000, rel=1e-5)
