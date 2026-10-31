"""GOLDEN — CRR de Boulanger & Idriss (2014) para SPT.

Modulo bajo prueba: ``terzaghi.liquefaction.boulanger_idriss``.

FUENTE (ecuaciones publicadas, citadas por numero y reproducidas):
    Boulanger, R. W. & Idriss, I. M. (2014), "CPT and SPT Based Liquefaction
    Triggering Procedures", Report No. UCD/CGM-14/01, Center for Geotechnical
    Modeling, Dept. of Civil and Environmental Engineering, University of
    California, Davis. (Version resumida: Idriss, I. M. & Boulanger, R. W.,
    "Soil Liquefaction During Earthquakes", EERI MNO-12, 2a ed. 2014.)

    Ec. (33)/(34) — curva de resistencia ciclica base, M = 7.5, sigma'_vc = 1 atm:

        CRR_{M7.5, sigma'=1atm} = exp[  (N1)60cs / 14.1
                                      + ((N1)60cs / 126)^2
                                      - ((N1)60cs / 23.6)^3
                                      + ((N1)60cs / 25.4)^4
                                      - 2.8 ]

        valida hasta (N1)60cs = 37.5 (la curva se hace asintotica).

    Ec. (72) — Magnitude Scaling Factor:
        MSF = 1 + (MSF_max - 1) * [ 8.64 * exp(-M/4) - 1.325 ]
        MSF_max = 1.09 + ((N1)60cs / 31.5)^2  <= 2.2
        Por construccion MSF(M = 7.5) = 1.0 exactamente.

    Ec. (11)/(51) — factor de sobrecarga:
        K_sigma = 1 - C_sigma * ln(sigma'_vc / P_a)  <= 1.1
        C_sigma = 1 / (18.9 - 2.55 * sqrt((N1)60cs))  <= 0.3

    Ec. (2) — demanda ciclica:
        CSR = 0.65 * (a_max/g) * (sigma_vc / sigma'_vc) * r_d
    y  FS_liq = (CRR / CSR) * MSF * K_sigma.

DESARROLLO ESCRITO — CRR para (N1)60cs = 20 (ec. 34):
    20 / 14.1        = +1.4184397
    (20 / 126)^2     = +0.0251953
    (20 / 23.6)^3    = -0.6086309
    (20 / 25.4)^4    = +0.3844015
    constante        = -2.8000000
    suma             = -1.5805944
    CRR = exp(-1.5805944) = 0.2058527      -> 0.2059

DESARROLLO ESCRITO — CRR para (N1)60cs = 10:
    10 / 14.1        = +0.7092199
    (10 / 126)^2     = +0.0062988
    (10 / 23.6)^3    = -0.0760789
    (10 / 25.4)^4    = +0.0240251
    constante        = -2.8000000
    suma             = -2.1365351
    CRR = exp(-2.1365351) = 0.1180632      -> 0.1181

Ambos caen sobre la curva publicada de la figura de triggering SPT del
informe (CRR ~ 0.12 para (N1)60cs = 10 y CRR ~ 0.21 para (N1)60cs = 20,
a M = 7.5 y sigma'_vc = 1 atm).

DISCREPANCIA MENOR DOCUMENTADA: la implementacion satura (N1)60cs en 37.0
(``min(N1_60cs, 37.0)``) mientras el informe declara el limite de validez de
la ec. (34) en 37.5. Diferencia sin efecto practico (por encima de 37 el FS
ya es enorme), pero no es el numero del paper.
"""
from __future__ import annotations

import math

import pytest

from terzaghi.liquefaction.boulanger_idriss import (
    BoulangerIdrissInput,
    evaluate_bi2014,
)
from terzaghi.liquefaction.boulanger_idriss import (
    _crr_m75,
    _k_sigma_bi2014,
    _msf_bi2014,
)


def _crr_referencia(N: float) -> float:
    """Ec. (34) de Boulanger & Idriss (2014), escrita de forma independiente."""
    return math.exp(
        N / 14.1 + (N / 126.0) ** 2 - (N / 23.6) ** 3 + (N / 25.4) ** 4 - 2.8
    )


def test_golden_crr_n1_60cs_20() -> None:
    """CRR_{M7.5,1atm} para (N1)60cs = 20 -> 0.2058527 (desarrollo en el
    docstring del modulo, ec. 34 B&I 2014)."""
    assert _crr_referencia(20.0) == pytest.approx(0.2058527, abs=1e-7)
    assert _crr_m75(20.0) == pytest.approx(0.2058527, abs=1e-7)


def test_golden_crr_n1_60cs_10() -> None:
    """CRR_{M7.5,1atm} para (N1)60cs = 10 -> 0.1180632 (ec. 34 B&I 2014)."""
    assert _crr_referencia(10.0) == pytest.approx(0.1180632, abs=1e-7)
    assert _crr_m75(10.0) == pytest.approx(0.1180632, abs=1e-7)


@pytest.mark.parametrize("N,CRR_pub", [
    (5.0, 0.0861),
    (15.0, 0.1561),
    (25.0, 0.2900),
    (30.0, 0.4849),
])
def test_golden_crr_curva_completa(N: float, CRR_pub: float) -> None:
    """Mas puntos de la misma curva publicada (ec. 34), a 4 decimales."""
    assert _crr_referencia(N) == pytest.approx(CRR_pub, abs=5e-5)
    assert _crr_m75(N) == pytest.approx(CRR_pub, abs=5e-5)


def test_golden_msf_es_uno_en_m75_por_definicion() -> None:
    """Identidad del paper (ec. 72): MSF(M = 7.5) = 1.0.

        8.64 * exp(-7.5/4) - 1.325 = 8.64 * 0.1533550 - 1.325
                                   = 1.3249869 - 1.325 = -1.31e-5
    de modo que MSF = 1 + (MSFmax - 1)(-1.31e-5) ~ 1.0 con error < 1e-5
    (el paper redondea el 1.325; no es un error de la implementacion).
    """
    corchete = 8.64 * math.exp(-7.5 / 4.0) - 1.325
    assert corchete == pytest.approx(0.0, abs=2e-5)
    for N in (10.0, 20.0, 30.0):
        assert _msf_bi2014(7.5, N) == pytest.approx(1.0, abs=1e-4)


def test_golden_msf_max_y_msf_m6() -> None:
    """MSF_max = 1.09 + ((N1)60cs/31.5)^2 y MSF a M = 6.0, (N1)60cs = 20.

        MSF_max = 1.09 + (20/31.5)^2 = 1.09 + 0.4031242 = 1.4931242
        8.64*exp(-6/4) - 1.325 = 8.64*0.2231302 - 1.325 = 1.9278446 - 1.325
                               = 0.6028446
        MSF = 1 + 0.4931242 * 0.6028446 = 1.2972773
    """
    MSFmax = 1.09 + (20.0 / 31.5) ** 2
    assert MSFmax == pytest.approx(1.4931242, abs=1e-7)
    msf = 1.0 + (MSFmax - 1.0) * (8.64 * math.exp(-6.0 / 4.0) - 1.325)
    assert msf == pytest.approx(1.2972773, abs=1e-6)
    assert _msf_bi2014(6.0, 20.0) == pytest.approx(1.2972773, abs=1e-6)


def test_golden_k_sigma_a_una_atmosfera_y_a_dos() -> None:
    """K_sigma (ec. 11): vale 1.0 exactamente a sigma'_vc = P_a = 100 kPa.

    A sigma'_vc = 200 kPa con (N1)60cs = 20:
        C_sigma = 1/(18.9 - 2.55*sqrt(20)) = 1/(18.9 - 11.4039) = 1/7.4961
                = 0.1334035
        K_sigma = 1 - 0.1334035 * ln(2) = 1 - 0.1334035*0.6931472 = 0.9075317
    """
    assert _k_sigma_bi2014(100.0, 20.0) == pytest.approx(1.0, abs=1e-12)

    C_sigma = 1.0 / (18.9 - 2.55 * math.sqrt(20.0))
    assert C_sigma == pytest.approx(0.1334035, abs=1e-7)
    k = 1.0 - C_sigma * math.log(2.0)
    assert k == pytest.approx(0.9075317, abs=1e-7)
    assert _k_sigma_bi2014(200.0, 20.0) == pytest.approx(0.9075317, abs=1e-7)


def test_golden_fs_cadena_completa_a_m75_y_1atm() -> None:
    """En el punto de referencia del paper (M = 7.5, sigma'_vc = 1 atm) los
    dos ajustes valen 1, de modo que FS se reduce a CRR/CSR — comprobable a
    mano sin ambiguedad.

    Datos: z = 6.0 m, sigma_vc = 130 kPa, sigma'_vc = 100 kPa,
           (N1)60cs = 20, a_max = 0.30 g, M = 7.5.

        r_d = exp(alpha + beta*M), alpha = -1.012 - 1.126 sin(6/11.73 + 5.133),
              beta = 0.106 + 0.118 sin(6/11.28 + 5.142)      [ec. 6-8]
        CSR = 0.65 * 0.30 * (130/100) * r_d
        MSF = 1.0 (M = 7.5)   ;  K_sigma = 1.0 (sigma'_vc = 1 atm)
        FS  = CRR/CSR = 0.2058527 / CSR
    """
    inp = BoulangerIdrissInput(
        depth_m=6.0, sigma_v_kPa=130.0, sigma_v_eff_kPa=100.0,
        N1_60cs=20.0, a_max_g=0.30, Mw=7.5,
    )
    res = evaluate_bi2014(inp)

    alpha = -1.012 - 1.126 * math.sin(6.0 / 11.73 + 5.133)
    beta = 0.106 + 0.118 * math.sin(6.0 / 11.28 + 5.142)
    rd = math.exp(alpha + beta * 7.5)
    assert res.rd == pytest.approx(rd, rel=1e-12)

    CSR = 0.65 * 0.30 * (130.0 / 100.0) * rd
    assert res.CSR == pytest.approx(CSR, rel=1e-12)

    assert res.MSF == pytest.approx(1.0, abs=1e-4)
    assert res.K_sigma == pytest.approx(1.0, abs=1e-12)
    assert res.CRR == pytest.approx(0.2058527, abs=1e-7)
    assert res.FS == pytest.approx(0.2058527 / CSR, rel=1e-4)
    assert res.is_liquefiable is (res.FS < 1.0)
