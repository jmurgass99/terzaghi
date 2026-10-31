# -*- coding: utf-8 -*-
"""Golden tests — factores de capacidad portante y qult EC7 anclados a fichas.

Fichas ancla:
  **W00675** "Examples of geotechnical design according to Eurocode 7" (UPC,
  Foundation Structures): tabla de factores Nq/Nc/Nγ para φ=25..35° y dos
  ejemplos resueltos (zapata cuadrada DA2 y zapata corrida con nivel freático).
  **W00672** "Shallow Foundations Part 1 2025" (UPC): Nγ(32°)=22.02 y área
  efectiva por excentricidad e=0.15 m → B'=1.70 m, A'=3.40 m².

Oráculo independiente — todos los valores recalculados a mano con las fórmulas
normativas transcritas (Reissner/Prandtl + Vesić 1973 / Meyerhof 1963), nunca
reimportando la función bajo prueba:

    Nq = e^(π·tanφ)·tan²(45+φ/2) ;  Nc = (Nq−1)/tanφ
    Nγ(Vesić)   = 2·(Nq+1)·tanφ  ;  Nγ(Meyerhof) = (Nq−1)·tan(1.4φ)

    φ=25: Nq=10.6621, Nc=20.7205, Nγv=10.8763
    φ=28: Nq=14.7199, Nc=25.8033, Nγv=16.7168
    φ=30: Nq=18.4011, Nc=30.1396, Nγv=22.4025
    φ=32: Nq=23.1768, Nc=35.4903, Nγv=30.2147
    φ=35: Nq=33.2961, Nc=46.1236, Nγv=48.0288

ERRATAS documentadas de las fichas (regla de oro de la campaña):
  1. W00675 rotula su tabla "(Hansen, EN 1997-1 Annex D)". FALSO en el Nγ:
     los valores impresos son VESIĆ 2(Nq+1)tanφ (p.ej. 30.22 a 32°); Annex D
     da 2(Nq−1)tanφ = 27.71 y Hansen 1970 da 1.5(Nq−1)tanφ = 20.78. Nq y Nc
     sí son los clásicos comunes a todos. Se ancla a los valores impresos
     (= Vesić, método 'vesic' de Terzaghi).
  2. W00675 GT1 imprime sq = 1+sin32° = "1.527"; lo correcto es 1.530
     (sin32° = 0.5299). Con sq exacto, qult = 1338 kPa (ficha imprime 1334,
     Δ=0.3%); Rk = 4830 kN (ficha 4815); Rd = 3450 kN (ficha 3439). Se ancla
     al recálculo con tolerancia que cubre la ficha.
  3. W00672 imprime la fórmula "Nγ = 2(Nq−1)tanφ (Hansen)" pero su valor de
     ejemplo Nγ(32°)=22.02 corresponde a MEYERHOF (Nq−1)tan(1.4φ)=22.020.
     Se ancla el valor al método 'meyerhof' de Terzaghi y se documenta el
     desajuste fórmula↔valor.
  4. W00672 dice "qult ≈ 680 kPa" para su ejemplo (φ=32°, B=2, Df=1): NO es
     reproducible con sus propios datos y factores (la composición da ~814
     kPa sin forma). NO se ancla ese número (ver informe).
"""
import math

import pytest

from terzaghi.bearing_capacity import BearingCapacityInput, evaluate_bearing
from terzaghi.bearing_inclination import effective_dimensions

# Tabla W00675 (impresa) y recálculo a mano (Vesić). Columnas: Nq, Nc, Ngamma.
TABLA_W00675 = {
    25: (10.66, 20.72, 10.88),
    28: (14.72, 25.80, 16.72),
    30: (18.40, 30.14, 22.40),
    32: (23.18, 35.49, 30.22),
    35: (33.30, 46.12, 48.03),
}
RECALC_MANO = {
    25: (10.6621, 20.7205, 10.8763),
    28: (14.7199, 25.8033, 16.7168),
    30: (18.4011, 30.1396, 22.4025),
    32: (23.1768, 35.4903, 30.2147),
    35: (33.2961, 46.1236, 48.0288),
}


def _factors(phi: float, method: str = "vesic"):
    """Extrae (Nq, Nc, Ngamma) del resultado de evaluate_bearing."""
    r = evaluate_bearing(BearingCapacityInput(
        B_m=1.0, L_m=1.0, D_f_m=1.0, phi_deg=phi, method=method), code="EU")
    return r.Nq, r.Nc, r.Ngamma


class TestTablaFactoresW00675:
    """Tabla Nq/Nc/Nγ de W00675 == método 'vesic' de Terzaghi (5 filas)."""

    @pytest.mark.parametrize("phi", sorted(TABLA_W00675))
    def test_fila_tabla(self, phi):
        Nq, Nc, Ng = _factors(phi, "vesic")
        Nq_f, Nc_f, Ng_f = TABLA_W00675[phi]
        Nq_m, Nc_m, Ng_m = RECALC_MANO[phi]
        # Ancla primaria: recálculo a mano (3 decimales).
        assert Nq == pytest.approx(Nq_m, abs=2e-3)
        assert Nc == pytest.approx(Nc_m, abs=2e-3)
        assert Ng == pytest.approx(Ng_m, abs=2e-3)
        # Ancla secundaria: valores impresos en la ficha (2 decimales).
        assert Nq == pytest.approx(Nq_f, abs=0.02)
        assert Nc == pytest.approx(Nc_f, abs=0.02)
        assert Ng == pytest.approx(Ng_f, abs=0.02)

    def test_nc_phi_cero_es_5_14(self):
        # Nc(φ=0) = π+2 = 5.14 (W00672, EN 1997-1 Annex D).
        _, Nc, _ = _factors(0.0, "vesic")
        assert Nc == pytest.approx(5.14, abs=0.01)


class TestNgammaMeyerhofW00672:
    """Errata 3: el valor Nγ(32°)=22.02 de W00672 es Meyerhof, no su fórmula."""

    def test_ngamma_meyerhof_32_es_22_02(self):
        _, _, Ng = _factors(32.0, "meyerhof")
        # Recalc a mano: (23.1768-1)*tan(44.8 deg) = 22.1768*0.99304 = 22.0225
        assert Ng == pytest.approx(22.0225, abs=5e-3)
        assert Ng == pytest.approx(22.02, abs=0.01)      # ficha W00672

    def test_formula_impresa_annexD_no_da_22(self):
        # La fórmula impresa en W00672 (2(Nq-1)tanφ, Annex D) daría 27.71:
        # el desajuste fórmula<->valor queda documentado con aritmética.
        Nq, _, _ = _factors(32.0, "vesic")
        annexD = 2.0 * (Nq - 1.0) * math.tan(math.radians(32.0))
        assert annexD == pytest.approx(27.712, abs=0.02)
        assert abs(annexD - 22.02) > 5.0


class TestAreaEfectivaW00672:
    """Área efectiva Meyerhof: e=0.15 m -> B'=1.70 m, A'=3.40 m² (W00672)."""

    def test_B_eff_y_area(self):
        ea = effective_dimensions(2.0, 2.0, e_B_m=0.15)
        assert ea.B_eff_m == pytest.approx(1.70, abs=1e-9)   # B-2e
        assert ea.L_eff_m == pytest.approx(2.00, abs=1e-9)
        assert ea.area_m2 == pytest.approx(3.40, abs=1e-9)   # ficha W00672


class TestZapataCuadradaDA2W00675:
    """GT1 de W00675: zapata cuadrada B=2 m, φ'=32°, c'=0, γ=18, Df=1.5, e=0.05.

    La ficha compone qult = q·Nq·sq + 0.5·γ·B·Nγ·sγ con sq=1+sinφ (cuadrada),
    sγ=0.7, B=2.0 en el término Nγ y área con B'=1.9 m (procedimiento de la
    ficha; Annex D usaría B' también en el término Nγ — documentado).
    Terzaghi no expone esos factores de forma en evaluate_bearing (usa Meyerhof
    simplificado), así que el golden ancla los FACTORES de Terzaghi dentro de la
    composición transcrita de la ficha.
    """

    def test_qult_Rk_Rd(self):
        Nq, _, Ng = _factors(32.0, "vesic")
        sq = 1.0 + math.sin(math.radians(32.0))       # 1.5299 (ficha: "1.527")
        s_gamma = 1.0 - 0.3                            # 0.70 cuadrada
        q = 18.0 * 1.5                                 # 27 kPa sobrecarga
        qult = q * Nq * sq + 0.5 * 18.0 * 2.0 * Ng * s_gamma
        # Recalc a mano: 27*23.174*1.5299 + 18*30.213*0.7 = 957.3 + 380.7
        assert qult == pytest.approx(1338.0, abs=2.0)      # oráculo recalculado
        assert qult == pytest.approx(1334.0, rel=0.005)    # ficha (sq truncado)

        B_eff = effective_dimensions(2.0, 2.0, e_B_m=0.05).B_eff_m
        assert B_eff == pytest.approx(1.90, abs=1e-9)      # ficha W00675
        Rk = qult * B_eff ** 2
        assert Rk == pytest.approx(4830.0, abs=8.0)        # recalc (ficha: 4815)
        Rd = Rk / 1.4                                       # γR;v=1.4 (DA2, R2)
        assert Rd == pytest.approx(3450.0, abs=6.0)        # recalc (ficha: 3439)

    def test_gamma_Rv_14_en_evaluate_bearing_EU(self):
        # El factor DA2 γR;v=1.4 de W00675/W00672 es el que aplica Terzaghi en EU.
        r = evaluate_bearing(BearingCapacityInput(
            B_m=2.0, L_m=2.0, D_f_m=1.5, phi_deg=32.0, gamma_kN_m3=18.0,
            method="vesic"), code="EU")
        assert r.q_adm_kPa == pytest.approx(r.q_ult_kPa / 1.4, rel=1e-12)


class TestZapataCorridaGwtW00675:
    """GT2 de W00675: corrida B=2 m, φ'=28°, c'=10 kPa, γ=18 sobre base,
    γ'=10 bajo NF; qult = c·Nc + q·Nq + 0.5·γ'·B·Nγ = 822.6 kPa (ficha: 822).

    evaluate_bearing usa un único γ (no admite γ' distinto bajo la base), por
    eso el golden compone el qult con los factores de Terzaghi y la fórmula
    transcrita de la ficha (corrida: factores de forma = 1).
    """

    def test_qult_822(self):
        Nq, Nc, Ng = _factors(28.0, "vesic")
        qult = 10.0 * Nc + 27.0 * Nq + 0.5 * 10.0 * 2.0 * Ng
        # Recalc a mano: 258.03 + 397.44 + 167.17 = 822.6
        assert qult == pytest.approx(822.6, abs=0.5)   # oráculo recalculado
        assert qult == pytest.approx(822.0, rel=0.002)  # ficha W00675
