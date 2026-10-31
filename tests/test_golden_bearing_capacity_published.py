"""GOLDEN — factores de capacidad portante y q_ult de zapata corrida.

Modulo bajo prueba: ``terzaghi.bearing_capacity``.

FUENTES (soluciones cerradas publicadas, derivadas inline abajo, y sus tablas):

  Nq  — Reissner (1924) / Prandtl (1921), adoptada por Meyerhof, Vesic,
        Brinch Hansen y por EN 1997-1:2004 Anexo D (D.4, condiciones drenadas):
            Nq = e^(pi * tan(phi)) * tan^2(45 + phi/2)
  Nc  — Prandtl (1921), EN 1997-1 Anexo D:
            Nc = (Nq - 1) / tan(phi)   ; Nc = pi + 2 = 5.14 para phi = 0
  Ngamma — depende del autor:
            Vesic (1973)         : N_g = 2 (Nq + 1) tan(phi)
            Meyerhof (1963)      : N_g = (Nq - 1) tan(1.4 phi)
            Brinch Hansen (1970) : N_g = 1.5 (Nq - 1) tan(phi)
        (EN 1997-1 Anexo D usa la de Brinch Hansen, N_g = 2(Nq-1)tan(phi) en
         algunos anexos nacionales; ver NOTA de discrepancias al final.)

  Tabuladas en B. M. Das, "Principles of Foundation Engineering", tabla de
  factores de capacidad portante (columnas Nc, Nq, N_gamma de Vesic, y tabla
  comparativa Meyerhof / Hansen / Vesic), y en EN 1997-1:2004 Anexo D.

VALORES DE REFERENCIA PUBLICADOS (2 decimales, como se tabulan):

    phi     Nc       Nq      N_g Vesic   N_g Meyerhof   N_g Hansen
    20    14.83     6.40        5.39         2.87          2.95
    30    30.14    18.40       22.40        15.67         15.07
    40    75.31    64.20      109.41        93.69         79.54

DESARROLLO ESCRITO para phi = 30 deg (el resto es identico):
    tan(30) = 0.5773503
    pi * tan(30) = 1.8137994 ; e^1.8137994 = 6.1337074
    tan(45 + 15) = tan(60) = 1.7320508 ; al cuadrado = 3.0000000
    Nq = 6.1337074 * 3.0 = 18.4011222          -> tabla 18.40
    Nc = (18.4011222 - 1)/0.5773503 = 30.1396  -> tabla 30.14
    N_g(Vesic)    = 2 * 19.4011222 * 0.5773503 = 22.4025  -> tabla 22.40
    N_g(Meyerhof) = 17.4011222 * tan(42) = 17.4011222 * 0.9004040 = 15.6680
                                                            -> tabla 15.67
    N_g(Hansen)   = 1.5 * 17.4011222 * 0.5773503 = 15.0698  -> tabla 15.07

NOTA DE DISCREPANCIAS ENCONTRADAS (no se "arreglan" aqui, se documentan):

  1. ``method="terzaghi"`` NO devuelve los factores de Terzaghi (1943).
     Terzaghi usa Nq = a^2/(2 cos^2(45+phi/2)) con a = e^((0.75 pi - phi/2) tan phi)
     y Nc = 5.70 para phi = 0. La implementacion devuelve el Nq de
     Prandtl/Reissner y el N_gamma de Meyerhof. En la practica
     ``method="terzaghi"`` == ``method="meyerhof"`` (mismas tres lineas).
     Por eso este fichero NO contiene ningun golden etiquetado "Terzaghi":
     seria un golden falso.
  2. Los factores de forma de ``evaluate_bearing`` (Sc = 1 + 0.2 B/L,
     Sq = 1 + 0.1 B/L, Sg = 1 - 0.1 B/L) no corresponden a ningun juego
     publicado: Vesic da sc = 1 + (B/L)(Nq/Nc), sq = 1 + (B/L) tan(phi),
     sg = 1 - 0.4 B/L ; Meyerhof da sq = sg = 1 + 0.1 Kp B/L. Ademas se
     aplican con independencia del ``method`` elegido. Por eso el golden de
     q_ult usa una zapata CORRIDA (L/B = 1000), donde los tres factores de
     forma valen 1.0000 +/- 0.0001 y no contaminan la comparacion.
     Corregirlos cambiaria el resultado de todos los llamadores: es decision
     del responsable del paquete, no de este test.
"""
from __future__ import annotations

import math

import pytest

from terzaghi.bearing_capacity import (
    BearingCapacityInput,
    evaluate_bearing,
)
from terzaghi.bearing_capacity import _bearing_factors


# (phi_deg, Nc, Nq, N_gamma Vesic) — tabla publicada, 2 decimales
TABLA_VESIC = [
    (20.0, 14.83, 6.40, 5.39),
    (30.0, 30.14, 18.40, 22.40),
    (40.0, 75.31, 64.20, 109.41),
]

# (phi_deg, N_gamma Meyerhof, N_gamma Brinch Hansen)
TABLA_NGAMMA = [
    (20.0, 2.87, 2.95),
    (30.0, 15.67, 15.07),
    (40.0, 93.69, 79.54),
]

# Valores a 4 decimales derivados en el docstring del modulo para phi = 30 deg.
# Se aseveran aqui explicitamente: si un numero se deriva por escrito, se
# comprueba (si no, sobra del docstring).
DERIVADOS_PHI30 = {
    "Nq": 18.4011222,
    "Nc": 30.1396,
    "Ng_vesic": 22.4025,
    "Ng_meyerhof": 15.6680,
    "Ng_hansen": 15.0698,
}


def test_golden_derivados_phi30_del_docstring_se_aseveran() -> None:
    """Los 4 decimales escritos en el desarrollo a mano del docstring del
    modulo, contrastados contra la implementacion con abs=5e-5 (resolucion
    de los propios decimales escritos, no un margen ajustado).
    """
    Nc_v, Nq_v, Ng_v = _bearing_factors(30.0, "vesic")
    _, _, Ng_m = _bearing_factors(30.0, "meyerhof")
    _, _, Ng_h = _bearing_factors(30.0, "brinch_hansen")

    assert Nq_v == pytest.approx(DERIVADOS_PHI30["Nq"], abs=5e-7)
    assert Nc_v == pytest.approx(DERIVADOS_PHI30["Nc"], abs=5e-5)
    assert Ng_v == pytest.approx(DERIVADOS_PHI30["Ng_vesic"], abs=5e-5)
    assert Ng_m == pytest.approx(DERIVADOS_PHI30["Ng_meyerhof"], abs=5e-5)
    assert Ng_h == pytest.approx(DERIVADOS_PHI30["Ng_hansen"], abs=5e-5)


@pytest.mark.parametrize("phi,Nc_pub,Nq_pub,Ng_pub", TABLA_VESIC)
def test_golden_factores_vesic_vs_tabla(phi: float, Nc_pub: float,
                                        Nq_pub: float, Ng_pub: float) -> None:
    """Nc, Nq, N_gamma (Vesic) frente a la tabla publicada.

    Tolerancia absoluta 5e-3 en Nc/Nq y 5e-3 en N_gamma: es la resolucion de
    la tabla (2 decimales), no un margen ajustado para que pase.
    """
    Nc, Nq, Ng = _bearing_factors(phi, "vesic")
    assert Nc == pytest.approx(Nc_pub, abs=5e-3)
    assert Nq == pytest.approx(Nq_pub, abs=5e-3)
    assert Ng == pytest.approx(Ng_pub, abs=5e-3)


@pytest.mark.parametrize("phi,Ng_meyerhof,Ng_hansen", TABLA_NGAMMA)
def test_golden_ngamma_meyerhof_y_hansen(phi: float, Ng_meyerhof: float,
                                          Ng_hansen: float) -> None:
    """N_gamma de Meyerhof (1963) y Brinch Hansen (1970) contra tabla."""
    _, _, Ng_m = _bearing_factors(phi, "meyerhof")
    _, _, Ng_h = _bearing_factors(phi, "brinch_hansen")
    assert Ng_m == pytest.approx(Ng_meyerhof, abs=5e-3)
    assert Ng_h == pytest.approx(Ng_hansen, abs=5e-3)


def test_golden_nq_nc_forma_cerrada_derivada_inline_phi30() -> None:
    """Se asevera el numero derivado en el docstring del modulo, no solo el
    tabulado: Nq = e^(pi tan30) tan^2(60) = 18.4011222, Nc = 30.1396.
    """
    phi = math.radians(30.0)
    Nq_exacto = math.exp(math.pi * math.tan(phi)) * math.tan(math.pi / 4 + phi / 2) ** 2
    Nc_exacto = (Nq_exacto - 1.0) / math.tan(phi)
    assert Nq_exacto == pytest.approx(18.4011222, abs=1e-6)
    assert Nc_exacto == pytest.approx(30.1396, abs=1e-4)

    Nc, Nq, _ = _bearing_factors(30.0, "vesic")
    assert Nq == pytest.approx(Nq_exacto, rel=1e-12)
    assert Nc == pytest.approx(Nc_exacto, rel=1e-12)


def test_golden_nc_phi_cero_prandtl() -> None:
    """phi = 0 (arcilla no drenada): Nc = pi + 2 = 5.1415927, Nq = 1, N_g = 0.

    Prandtl (1921) / EN 1997-1 Anexo D.3 (condiciones no drenadas). Aqui solo
    se asevera el valor PUBLICADO, a la resolucion con que se tabula
    (2 decimales -> abs = 5e-3). El literal 5.14 que la implementacion lleva
    hardcodeado es un valor del codigo, no de la fuente: vive en el test de
    caracterizacion companero.
    """
    Nc, Nq, Ng = _bearing_factors(0.0, "vesic")
    assert math.pi + 2.0 == pytest.approx(5.1415927, abs=1e-7)
    assert Nc == pytest.approx(math.pi + 2.0, abs=5e-3)   # tabla a 2 decimales
    assert Nq == pytest.approx(1.0, rel=1e-12)
    assert Ng == pytest.approx(0.0, abs=1e-12)


@pytest.mark.characterization
def test_caracterizacion_nc_phi_cero_es_literal_514() -> None:
    """CARACTERIZACION (no golden): la implementacion devuelve el literal
    redondeado ``5.14`` en vez de pi + 2 = 5.1415927 (-0.031 %).

    Ambas aserciones fijan una propiedad del CODIGO (el numero hardcodeado y
    su desviacion del valor exacto), no un dato de la fuente. Si alguien
    cambia el literal por pi + 2, este test debe fallar y obligar a revisar
    la documentacion, no ser silenciado.
    """
    Nc, _, _ = _bearing_factors(0.0, "vesic")
    assert Nc == pytest.approx(5.14, abs=1e-9)
    assert Nc != pytest.approx(math.pi + 2.0, abs=1e-6)


def test_golden_qult_zapata_corrida_vesic_calculo_a_mano() -> None:
    """q_ult de zapata CORRIDA en arena — calculo a mano completo.

    Datos: B = 2.00 m, L = 2000 m (L/B = 1000 -> corrida), D_f = 1.50 m,
           c' = 0, phi' = 35 deg, gamma = 18.0 kN/m3, metodo Vesic.

    Factores (formas cerradas del docstring del modulo):
        tan(35) = 0.7002075 ; pi*tan35 = 2.1997669 ; e^() = 9.0229096
        tan(45+17.5) = tan(62.5) = 1.9209821 ; ^2 = 3.6901723
        Nq = 9.0229096 * 3.6901723 = 33.2960915     (tabla publicada: 33.30)
        N_g(Vesic) = 2 * 34.2960915 * 0.7002075 = 48.0287636  (tabla: 48.03)

    Ecuacion general (c' = 0, zapata corrida, factores de forma = 1):
        q = gamma * D_f = 18.0 * 1.50 = 27.00 kPa
        q_ult = q * Nq + 0.5 * gamma * B * N_g
              = 27.00 * 33.2960915 + 0.5 * 18.0 * 2.00 * 48.0287636
              = 898.99447 + 864.51774
              = 1763.5122 kPa

    Este es el unico valor GOLDEN de q_ult: sale de la ecuacion publicada.
    El valor que devuelve la implementacion incluye ademas sus factores de
    forma no publicados (ver NOTA 2 del docstring del modulo) y por eso vive
    en el test de caracterizacion companero de mas abajo.
    """
    inp = BearingCapacityInput(
        B_m=2.0, L_m=2000.0, D_f_m=1.5,
        phi_deg=35.0, c_kPa=0.0, gamma_kN_m3=18.0,
        method="vesic",
    )
    res = evaluate_bearing(inp, code="EU")

    assert res.Nq == pytest.approx(33.2960915, abs=1e-6)
    assert res.Ngamma == pytest.approx(48.0287636, abs=1e-6)

    q_ult_mano_estricto = 27.00 * 33.2960915 + 0.5 * 18.0 * 2.00 * 48.0287636
    assert q_ult_mano_estricto == pytest.approx(1763.5122, abs=1e-3)

    assert res.q_ult_kPa == pytest.approx(q_ult_mano_estricto, abs=5e-3)


@pytest.mark.characterization
def test_caracterizacion_qult_con_factores_de_forma_no_publicados() -> None:
    """CARACTERIZACION (no golden): fija lo que HOY devuelve la implementacion.

    Estos numeros NO proceden de ninguna fuente externa: salen de ejecutar
    ``evaluate_bearing``, cuyos factores de forma (Sc = 1 + 0.2 B/L,
    Sq = 1 + 0.1 B/L, Sg = 1 - 0.1 B/L) no corresponden a ningun juego
    publicado -- ver NOTA 2 del docstring del modulo. Se dejan fijados para
    detectar cambios silenciosos, no para validar contra la literatura.

    Sobre la misma zapata del test anterior (L/B = 1000):
        Sq = 1.0001 ; Sg = 0.9999
        q_ult = 898.99447*1.0001 + 864.51774*0.9999 = 1763.5157 kPa
                (+0.0034 kPa, 2e-6 relativo, sobre los 1763.5122 publicados)
        q_adm = 1763.5157 / 1.40 = 1259.6540 kPa   (gamma_R,v = 1.40, EN 1997-1)
    """
    inp = BearingCapacityInput(
        B_m=2.0, L_m=2000.0, D_f_m=1.5,
        phi_deg=35.0, c_kPa=0.0, gamma_kN_m3=18.0,
        method="vesic",
    )
    res = evaluate_bearing(inp, code="EU")

    assert res.q_ult_kPa == pytest.approx(1763.5157, abs=1e-3)
    assert res.q_adm_kPa == pytest.approx(1259.6540, abs=1e-3)


def test_golden_qult_zapata_corrida_arcilla_no_drenada() -> None:
    """q_ult de zapata corrida sobre arcilla no drenada — calculo a mano.

    Datos: B = 2.00 m, L = 2000 m, D_f = 1.00 m, phi = 0,
           c_u = 50 kPa, gamma = 18.0 kN/m3.

    Prandtl / EN 1997-1 Anexo D.3 (no drenado, zapata corrida, sin
    inclinacion ni excentricidad):
        q_ult = c_u * Nc + q = 50.0 * 5.14 + 18.0 * 1.00
              = 257.00 + 18.00 = 275.00 kPa
    (con Nc = pi + 2 exacto seria 50*5.1415927 + 18 = 275.0796 kPa; la
     implementacion usa el literal 5.14, ver test_golden_nc_phi_cero_prandtl.)

    El valor con los factores de forma no publicados de la implementacion
    vive en el test de caracterizacion companero.
    """
    inp = BearingCapacityInput(
        B_m=2.0, L_m=2000.0, D_f_m=1.0,
        phi_deg=0.0, c_kPa=50.0, gamma_kN_m3=18.0,
        method="vesic",
    )
    res = evaluate_bearing(inp, code="CO")

    q_ult_mano_estricto = 50.0 * 5.14 + 18.0 * 1.0
    assert q_ult_mano_estricto == pytest.approx(275.00, abs=1e-9)
    assert 50.0 * (math.pi + 2.0) + 18.0 == pytest.approx(275.0796, abs=1e-4)

    assert res.q_ult_kPa == pytest.approx(q_ult_mano_estricto, abs=6e-2)


@pytest.mark.characterization
def test_caracterizacion_qult_arcilla_con_factores_de_forma() -> None:
    """CARACTERIZACION (no golden): salida actual de ``evaluate_bearing``.

    Factores de forma no publicados de la implementacion sobre L/B = 1000:
        Sc = 1 + 0.2*0.001 = 1.0002 ; Sq = 1 + 0.1*0.001 = 1.0001
        q_ult = 257.00*1.0002 + 18.00*1.0001 = 257.0514 + 18.0018
              = 275.0532 kPa
        q_adm = 275.0532 / 3 = 91.6844 kPa   (NSR-10 H.4.7, FS = 3 estatico)
    """
    inp = BearingCapacityInput(
        B_m=2.0, L_m=2000.0, D_f_m=1.0,
        phi_deg=0.0, c_kPa=50.0, gamma_kN_m3=18.0,
        method="vesic",
    )
    res = evaluate_bearing(inp, code="CO")

    assert res.q_ult_kPa == pytest.approx(275.0532, abs=1e-3)
    assert res.q_adm_kPa == pytest.approx(91.6844, abs=1e-3)


def test_terzaghi_no_es_terzaghi_discrepancia_documentada() -> None:
    """DISCREPANCIA (documentada, no corregida): ``method="terzaghi"`` devuelve
    exactamente los mismos factores que ``method="meyerhof"``.

    Terzaghi (1943) publica Nq = a^2/(2 cos^2(45+phi/2)) con
    a = e^((0.75 pi - phi/2) tan phi), que para phi = 30 deg da Nq = 22.46,
    no 18.40. Este test fija la discrepancia para que no pase inadvertida
    y falle si alguien la corrige sin actualizar la documentacion.
    """
    ter = _bearing_factors(30.0, "terzaghi")
    mey = _bearing_factors(30.0, "meyerhof")
    assert ter == mey

    # Nq de Terzaghi propiamente dicho, derivado inline:
    phi = math.radians(30.0)
    a = math.exp((0.75 * math.pi - phi / 2.0) * math.tan(phi))
    Nq_terzaghi = a ** 2 / (2.0 * math.cos(math.pi / 4 + phi / 2) ** 2)
    assert Nq_terzaghi == pytest.approx(22.4557, abs=1e-4)  # forma cerrada
    assert Nq_terzaghi == pytest.approx(22.46, abs=1e-2)    # tabla de Terzaghi
    assert ter[1] == pytest.approx(18.4011222, abs=1e-6)   # lo que devuelve
