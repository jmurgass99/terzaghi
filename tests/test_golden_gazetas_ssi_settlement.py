"""Golden test para resortes de Gazetas (1991) como apoyos elásticos SSI y asentamiento vertical P/k exacto.

Fuente:
Gazetas, G. (1991), "Formulas and Charts for Impedances of Surface and Embedded Foundations",
Journal of Geotechnical Engineering, ASCE, Vol. 117, No. 9, pp. 1363-1381.
NIST GCR 12-917-21, "Soil-Structure Interaction for Building Structures", Table 2-1.

Derivación analítica a mano:
----------------------------
1. Zapata rectangular: L = 4.00 m, B = 2.00 m (L/B = 2.0, B/L = 0.50).
Suelo:
    ρ = 2000.0 kg/m³
    Vs = 200.0 m/s
    ν = 0.35
    Módulo de corte: G = ρ · Vs² = 2000 · 200² = 80.0 MPa (80000.0 kPa).

1.1. Rigidez vertical Kz (Gazetas 1991 Tabla 1):
    Kz = [G · L / (1 - ν)] · [0.73 + 1.54 · (B/L)^0.75]
    (B/L)^0.75 = 0.5^0.75 = 0.5946035575
    Factor de forma = 0.73 + 1.54 · 0.5946035575 = 1.6456894786
    G · L / (1 - ν) = 80000 · 4.00 / 0.65 = 492307.6923077 kN/m
    Kz = 492307.6923077 · 1.6456894786 = 810185.5562 kN/m.

1.2. Rigideces horizontales Kx y Ky:
    Kx = [G · L / (2 - ν)] · [2.0 + 2.50 · (B/L)^0.85] = 656897.16 kN/m
    Ky = Kx - [G · L / (0.75 - ν)] · [0.20 · (1 - B/L)] = 656897.16 - 80000.0 = 576897.16 kN/m.

1.3. Rigideces rotacionales Krx, Kry, Krz:
    Ix = L · B³ / 12 = 4 · 8 / 12 = 8/3 m⁴ -> Ix^0.75 = 2.080084 m³
    Krx = [G · Ix^0.75 / (1 - ν)] · (L/B)^0.25 · [2.4 + 0.50 · (B/L)] = 809387.61 kNm/rad.
    Iy = B · L³ / 12 = 2 · 64 / 12 = 32/3 m⁴ -> Iy^0.75 = 5.883360 m³
    Kry = [G · Iy^0.75 / (1 - ν)] · [3.0 · (L/B)^0.15] = 2418098.16 kNm/rad.
    J = Ix + Iy = 40/3 m⁴ -> J^0.75 = 6.9660 m³
    Krz = 3.5 · G · J^0.75 · (B/L)^0.40 = 1478197.80 kNm/rad.

2. Simetría en zapata cuadrada (L = B): lo que la física exige y lo que la fuente da.

    La física SÍ exige Krx = Kry: una zapata cuadrada sobre semiespacio elástico
    tiene la misma rigidez de balanceo en ambos ejes, y en efecto Ix = Iy = B⁴/12.

    Pero los dos ajustes de Gazetas son CURVAS EMPÍRICAS INDEPENDIENTES y no lo
    reproducen. Con L = B sus factores valen

        Krx: (L/B)^0.25 · [2.4 + 0.50·(B/L)] = 2.90
        Kry: 3.0 · (L/B)^0.15                = 3.00

    o sea Krx/Kry = 2.9/3.0 = 0.9667: un 3.3 % de discrepancia que es la
    DISPERSIÓN DE LA FUENTE, no un defecto de la implementación.

    Una versión anterior de este test aseveraba `Krx == Kry` a rel=1e-12,
    justificándolo justamente con ese argumento físico. Para satisfacerlo se
    sustituyó el coeficiente publicado 0.50 por 0.41, se añadió un término
    corrector -0.19 que no existe en la fuente, y se remató con una rama
    `if L == B: Kry = Krx`. Es decir: se fabricaron coeficientes normativos para
    pasar un test, con un razonamiento físico correcto envolviendo números
    inventados — el mismo patrón que los 0.20/0.15 bajo la cita de NSR-10
    A.3.6.4.2.

    Lo que este test asevera ahora es lo que de verdad se puede aseverar: que la
    razón vale EXACTAMENTE 2.9/3.0, que es constante para cualquier lado, y que
    la discrepancia se queda dentro del 3.5 %. Si alguien vuelve a tocar los
    coeficientes publicados, esa razón deja de valer 0.9667 y el test lo caza.
"""
from __future__ import annotations

import math
import pytest
from geojm.gazetas_springs import (
    RATIO_ROCKING_CUADRADA,
    GazetasInput,
    evaluate_gazetas,
    gazetas_elastic_support_and_settlement,
)
from geojm.ssi_springs import (
    SsiSpringsInput,
    calculate_ssi_springs,
)


def test_golden_gazetas_springs_closed_form_and_p_over_k_settlement():
    """GOLDEN. Validación cerrada de las 6 rigideces de Gazetas (1991) y asentamiento P/Kz."""
    L, B = 4.0, 2.0
    Vs = 200.0
    rho = 2000.0
    nu = 0.35

    res = evaluate_gazetas(
        GazetasInput(L_m=L, B_m=B, Vs_m_per_s=Vs, rho_soil_kg_m3=rho, nu_soil=nu)
    )

    G_expected_MPa = rho * (Vs ** 2) / 1e6
    assert res.G_soil_MPa == pytest.approx(80.0, rel=1e-6)

    # 1. Kz analítico
    factor_forma = 0.73 + 1.54 * (0.5 ** 0.75)
    kz_expected = (80000.0 * 4.0 / (1.0 - 0.35)) * factor_forma
    assert res.Kz_kN_per_m == pytest.approx(kz_expected, rel=1e-6)
    assert res.Kz_kN_per_m == pytest.approx(810185.556, rel=1e-3)

    # 2. Kx y Ky analíticos
    kx_expected = (80000.0 * 4.0 / (2.0 - 0.35)) * (2.0 + 2.50 * (0.5 ** 0.85))
    ky_expected = kx_expected - (80000.0 * 4.0 / (0.75 - 0.35)) * (0.20 * (1.0 - 0.50))
    assert res.Kx_kN_per_m == pytest.approx(kx_expected, rel=1e-6)
    assert res.Ky_kN_per_m == pytest.approx(ky_expected, rel=1e-6)

    # 3. Krx, Kry, Krz analíticos
    ix = 4.0 * (2.0 ** 3) / 12.0
    iy = 2.0 * (4.0 ** 3) / 12.0
    j_pol = ix + iy

    # Coeficientes PUBLICADOS de Gazetas (1991): 0.50, sin termino corrector.
    krx_expected = (80000.0 * (ix ** 0.75) / (1.0 - 0.35)) * ((4.0 / 2.0) ** 0.25 * (2.4 + 0.50 * 0.5))
    kry_expected = (80000.0 * (iy ** 0.75) / (1.0 - 0.35)) * (3.0 * ((4.0 / 2.0) ** 0.15))
    krz_expected = 3.5 * 80000.0 * (j_pol ** 0.75) * (0.5 ** 0.40)

    assert res.Krx_kNm_per_rad == pytest.approx(krx_expected, rel=1e-6)
    assert res.Kry_kNm_per_rad == pytest.approx(kry_expected, rel=1e-6)
    assert res.Krz_kNm_per_rad == pytest.approx(krz_expected, rel=1e-6)

    # 4. Deformación P / Kz con API de apoyo elástico y unidades declaradas
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


@pytest.mark.parametrize("side", [1.0, 2.5, 3.0, 4.0, 5.0, 10.0])
def test_golden_gazetas_square_footing_exact_symmetry(side: float):
    """GOLDEN. Zapata cuadrada: simetria traslacional EXACTA, y la de balanceo
    solo hasta la dispersion del ajuste de la fuente.

    Kx == Ky exactamente, porque el termino corrector de Ky se anula en L = B.

    Krx/Kry == 2.9/3.0 EXACTAMENTE, para cualquier lado. La fisica pediria 1.0;
    los ajustes empiricos de Gazetas dan 0.9667. Forzar el 1.0 exigiria alterar
    los coeficientes publicados, que es lo que se hacia antes y es lo que este
    test existe ahora para impedir.
    """
    Vs = 200.0
    rho = 1900.0
    nu = 0.35

    res = evaluate_gazetas(
        GazetasInput(L_m=side, B_m=side, Vs_m_per_s=Vs, rho_soil_kg_m3=rho, nu_soil=nu)
    )

    # Simetría traslacional horizontal en cuadrada
    assert res.Kx_kN_per_m == pytest.approx(res.Ky_kN_per_m, rel=1e-12), "Asimetría en rigidez traslacional de zapata cuadrada"

    # Balanceo: la razon es la de los coeficientes PUBLICADOS, constante e
    # independiente del lado. Es la guarda contra volver a fabricarlos.
    ratio = res.Krx_kNm_per_rad / res.Kry_kNm_per_rad
    assert ratio == pytest.approx(RATIO_ROCKING_CUADRADA, rel=1e-12), (
        f"lado {side} m: Krx/Kry = {ratio:.6f}, esperado {RATIO_ROCKING_CUADRADA:.6f} "
        f"= 2.9/3.0. Si esto cambia, alguien ha tocado los coeficientes publicados."
    )
    assert ratio == pytest.approx(2.9 / 3.0, rel=1e-12)
    # Y la discrepancia frente a la simetria fisica se queda en la dispersion
    # del ajuste: 3.3 %, declarada, no corregida.
    assert abs(1.0 - ratio) < 0.035


@pytest.mark.parametrize("ratio", [1.0, 1.5, 2.0, 3.0, 4.0])
def test_golden_gazetas_and_ssi_springs_single_source_consistency(ratio: float):
    """GOLDEN. Validación de consistencia cruzada: ssi_springs y gazetas_springs no divergen."""
    B = 3.0
    L = B * ratio
    Vs = 220.0
    rho = 1950.0
    nu = 0.30

    gaz_res = evaluate_gazetas(
        GazetasInput(L_m=L, B_m=B, Vs_m_per_s=Vs, rho_soil_kg_m3=rho, nu_soil=nu)
    )
    ssi_res = calculate_ssi_springs(
        SsiSpringsInput(
            L_m=L,
            B_m=B,
            Vs_m_per_s=Vs,
            rho_soil_kg_m3=rho,
            nu_soil=nu,
            frequency_Hz=5.0,
            material_damping=0.05,
        )
    )

    assert ssi_res.Kz_static_kN_m == pytest.approx(gaz_res.Kz_kN_per_m, rel=1e-12)
    assert ssi_res.Kx_static_kN_m == pytest.approx(gaz_res.Kx_kN_per_m, rel=1e-12)
    assert ssi_res.Ky_static_kN_m == pytest.approx(gaz_res.Ky_kN_per_m, rel=1e-12)
    assert ssi_res.Krx_static_kNm_rad == pytest.approx(gaz_res.Krx_kNm_per_rad, rel=1e-12)
    assert ssi_res.Kry_static_kNm_rad == pytest.approx(gaz_res.Kry_kNm_per_rad, rel=1e-12)
    assert ssi_res.Krz_static_kNm_rad == pytest.approx(gaz_res.Krz_kNm_per_rad, rel=1e-12)

