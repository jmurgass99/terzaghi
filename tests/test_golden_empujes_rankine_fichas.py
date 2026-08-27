# -*- coding: utf-8 -*-
"""Golden tests — empujes de Rankine multicapa anclados a fichas del máster.

Fichas ancla (todas del muro en voladizo H=9.65 m, UPC MEEC Q1 2025-26,
informe del propio usuario, EC7 DA2):
  **W00664** "Retaining wall.docx" — informe completo: empujes por estrato,
  sobrecargas y verificaciones DA2.
  **W00677** "RetainingWalls" — mismo muro: deslizamiento DA2 Fdes=366.58 kN/m.
  **W00676** "BasementWall" — ejemplo H=6 m, φ=30°, γ=18, q=10 kPa.
  **W00643** "Teoría de empujes" (Q&A) — fórmulas Ka/K0/Kp y DA2.
  **W00438** "Reservoir Workshop" — σ_h = (1/3)·18·8 = 48 kPa (corroboración).

Geometría/suelos W00664: SOIL1 γ1=19.5 kN/m³, φ1=30°, H1=6 m (superior);
SOIL2 γ2=20 kN/m³, φ2=32°, H2=2.65 m (inferior); sobrecarga uniforme
q=10 kPa; sobrecarga lineal S=10 kN/m a a=1.5 m del muro.

Oráculo independiente (Rankine transcrito a mano, Ka=tan²(45−φ/2)):
    Ka1 = 1/3 (exacto, φ=30°) ; Ka2 = 0.30726 (φ=32°)
    Ea1 = ½·Ka1·γ1·H1²        = ½·(1/3)·19.5·36    = 117.00 kN/m
    Ea2 = ½·Ka2·γ2·H2²        = ½·0.30726·20·2.65² =  21.58 kN/m
    E2' = Ka2·(γ1·H1)·H2      = 0.30726·117·2.65   =  95.27 kN/m
    ES1 = Ka1·q·H1            = (1/3)·10·6         =  20.00 kN/m
    ES2 = Ka2·q·H2            = 0.30726·10·2.65    =   8.14 kN/m
    Es  = 0.6·S               = 0.6·10             =   6.00 kN/m  (H ≥ 3a)
    Σ   = 267.99 kN/m
    brazo Es = H_total − 1.17·a = 9.65 − 1.755     = 7.895 m

La ficha imprime Ea1=116.88, ES1=19.98, Σ=267.75: usa Ka1 truncado a 0.333
(0.1% menos que 1/3). Se ancla al recálculo exacto y se acepta la ficha con
tolerancia relativa 0.5%.

ERRATAS documentadas (regla de oro de la campaña):
  1. W00664 declara "q_k=200 kPa (sobrecarga uniforme)". FALSO: sus propios
     ES1=19.98 y ES2=8.14 solo se reproducen con q=10 kPa. Los 200 kPa son la
     presión ADMISIBLE del terreno (la misma ficha usa qrd=200/1.4=142.86 kPa
     en la comprobación de hundimiento). Los tests usan q=10 kPa.
  2. Magnitudes verificadas dimensionalmente: con q=200 kPa el empuje de
     sobrecarga sería Ka·q·H1=400 kN/m > todo el empuje del suelo — magnitud
     físicamente absurda que delató la errata (lección de unidades).
"""
import pytest

from geojm.gabion_wall import DESIGN_APPROACHES, Ka_rankine, Kp_rankine

# --- Datos W00664 / W00677 ---
G1, PHI1, H1 = 19.5, 30.0, 6.0        # SOIL1 (superior)
G2, PHI2, H2 = 20.0, 32.0, 2.65       # SOIL2 (inferior)
Q_SUR = 10.0                           # kPa (errata 200 kPa documentada arriba)
S_LIN, A_LIN = 10.0, 1.5               # kN/m, m
H_TOT = 9.65                           # m (incluye zapata hf=1 m)


class TestCoeficientesRankine:
    """Ka/Kp de Rankine anclados a W00664/W00643 (EC7 §9, trasdós vertical)."""

    def test_Ka_30_es_un_tercio(self):
        # tan²(45-15) = tan²(30) = 1/3 exacto (W00664: Ka1=1/3; W00643).
        assert Ka_rankine(30.0) == pytest.approx(1.0 / 3.0, abs=1e-12)

    def test_Ka_32_es_0_307(self):
        # Recalc a mano: tan²(29°) = 0.55431² = 0.30726 (ficha W00664: 0.307).
        assert Ka_rankine(32.0) == pytest.approx(0.30726, abs=1e-4)
        assert Ka_rankine(32.0) == pytest.approx(0.307, abs=5e-4)

    def test_Kp_es_reciproco_de_Ka(self):
        # Kp = tan²(45+φ/2) = 1/Ka (W00643: fórmulas 2).
        for phi in (30.0, 32.0):
            assert Ka_rankine(phi) * Kp_rankine(phi) == pytest.approx(1.0, abs=1e-12)


class TestEmpujesMulticapaW00664:
    """Descomposición de empujes del muro de 9.65 m (W00664, tabla 1)."""

    def test_empujes_por_estrato(self):
        Ka1, Ka2 = Ka_rankine(PHI1), Ka_rankine(PHI2)
        Ea1 = 0.5 * Ka1 * G1 * H1 ** 2
        Ea2 = 0.5 * Ka2 * G2 * H2 ** 2
        E2p = Ka2 * (G1 * H1) * H2          # rectangular del estrato superior
        # Oráculo recalculado a mano (exacto):
        assert Ea1 == pytest.approx(117.00, abs=0.01)
        assert Ea2 == pytest.approx(21.58, abs=0.01)
        assert E2p == pytest.approx(95.27, abs=0.01)
        # Ficha W00664 (Ka1 truncado a 0.333): tolerancia 0.5%.
        assert Ea1 == pytest.approx(116.88, rel=0.005)
        assert Ea2 == pytest.approx(21.56, rel=0.005)
        assert E2p == pytest.approx(95.19, rel=0.005)

    def test_sobrecargas_y_total(self):
        Ka1, Ka2 = Ka_rankine(PHI1), Ka_rankine(PHI2)
        ES1 = Ka1 * Q_SUR * H1
        ES2 = Ka2 * Q_SUR * H2
        Es = 0.6 * S_LIN                    # sobrecarga lineal (válida H >= 3a)
        assert ES1 == pytest.approx(20.00, abs=1e-9)    # recalc (ficha: 19.98)
        assert ES2 == pytest.approx(8.14, abs=0.01)     # ficha: 8.14
        assert Es == pytest.approx(6.0, abs=1e-12)      # ficha: 6
        total = (0.5 * Ka1 * G1 * H1 ** 2 + 0.5 * Ka2 * G2 * H2 ** 2
                 + Ka2 * G1 * H1 * H2 + ES1 + ES2 + Es)
        assert total == pytest.approx(267.99, abs=0.02)  # recalc
        assert total == pytest.approx(267.75, rel=0.005)  # ficha W00664

    def test_brazo_sobrecarga_lineal(self):
        # brazo = H_total − 1.17·a = 9.65 − 1.755 = 7.895 m (ficha: 7.90).
        z_Es = H_TOT - 1.17 * A_LIN
        assert z_Es == pytest.approx(7.895, abs=1e-9)
        assert z_Es == pytest.approx(7.90, abs=0.01)     # ficha W00664


class TestDeslizamientoDA2W00677:
    """Fuerza deslizante de diseño DA2 del muro W00664/W00677.

    Fdes = γG·(Ea1+Ea2+E2') + γQ·(ES1+ES2+Es) con γG=1.35, γQ=1.50 (A1, DA2).
    Recalc: 1.35·233.84 + 1.5·34.14 = 315.69 + 51.21 = 366.90 kN/m
    (ficha W00677: 366.58 — diferencia 0.09% por el Ka truncado de la ficha).
    """

    def test_Fdes_366(self):
        gf = DESIGN_APPROACHES["DA2"]
        assert gf["gG"] == 1.35 and gf["gQ"] == 1.50    # tabla 2 W00664
        Ka1, Ka2 = Ka_rankine(PHI1), Ka_rankine(PHI2)
        E_perm = (0.5 * Ka1 * G1 * H1 ** 2 + 0.5 * Ka2 * G2 * H2 ** 2
                  + Ka2 * G1 * H1 * H2)
        E_var = Ka1 * Q_SUR * H1 + Ka2 * Q_SUR * H2 + 0.6 * S_LIN
        Fdes = gf["gG"] * E_perm + gf["gQ"] * E_var
        assert Fdes == pytest.approx(366.90, abs=0.05)   # oráculo recalculado
        assert Fdes == pytest.approx(366.58, rel=0.005)  # ficha W00677


class TestMuroSotanoW00676:
    """Ejemplo W00676: H=6 m, φ'=30°, γ=18 kN/m³, q=10 kPa (muro sótano)."""

    def test_Ea_Es_y_momento(self):
        Ka = Ka_rankine(30.0)
        Ea = 0.5 * Ka * 18.0 * 6.0 ** 2     # triangular, actúa a H/3
        Es = Ka * 10.0 * 6.0                # rectangular, actúa a H/2
        M = Ea * 2.0 + Es * 3.0             # empotramiento en base
        # Oráculo recalculado (Ka=1/3 exacto):
        assert Ea == pytest.approx(108.0, abs=1e-9)
        assert Es == pytest.approx(20.0, abs=1e-9)
        assert M == pytest.approx(276.0, abs=1e-9)
        # Ficha W00676 (Ka truncado 0.333): 107.9 / 20.0 / 275.8.
        assert Ea == pytest.approx(107.9, rel=0.002)
        assert M == pytest.approx(275.8, rel=0.002)


class TestReservoirW00438:
    """Corroboración cruzada W00438: σ_h en el fondo = (1/3)·18·8 = 48 kPa."""

    def test_sigma_h_48(self):
        sigma_h = Ka_rankine(30.0) * 18.0 * 8.0
        assert sigma_h == pytest.approx(48.0, abs=1e-9)  # ficha W00438
