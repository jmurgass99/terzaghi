# -*- coding: utf-8 -*-
"""Golden tests — consolidación Terzaghi/Barron anclados a fichas del máster.

Fichas ancla:
  **W00255** "Precarga" (Proyecto y Construcción Geotécnicos, UPC) — ejemplo
  resuelto: arcilla H=10 m (drenaje doble), cv=1.5 m²/año, ch=3 m²/año;
  drenes en malla triangular l=1.5 m, d_w=0.066 m (band drain 100×4 mm).
  **W00254** "Precarga slides" — ejemplo aeropuerto El Prat: l=2.0 m
  (triangular), D=2.10 m, d_w=0.066 m, t=8 meses, ch=1.5 m²/año.

Todos los valores esperados fueron RECALCULADOS a mano con las fórmulas
normativas transcritas (Terzaghi 1943; Barron 1948; Carrillo 1942), nunca
reimportando la función bajo prueba:

  W00255: Tv90 = -(4/π²)·ln(0.1·π²/8) = 0.84809      (ficha: 0.848)
          t_sin_drenes = 0.84809·(10/2)²/1.5 = 14.13 años   (ficha: 14.1)
          D = 1.05·1.5 = 1.575 m ; n = 1.575/0.066 = 23.864  (ficha: 23.9)
          F(n) = ln(23.864) − 0.75 = 2.4224           (ficha: 2.42)
          Th90 = −F(n)·ln(1−0.9)/8 = 2.4224·2.302585/8 = 0.69721  (ficha: 0.696)
          t_con_drenes = 0.69721·1.575²/3 = 0.5765 años ≈ 6.9 meses (ficha: 0.575)
  W00254: n = 2.10/0.066 = 31.818 ; F(n) = 2.71004    (ficha: 2.71)
          Th = 1.5·(8/12)/2.10² = 0.226757            (ficha: 0.227)
          Uh = 1 − exp(−8·0.226757/2.71004) = 0.48797 (ficha: 0.49)

Las pequeñas diferencias ficha↔recálculo (p.ej. 0.696 vs 0.69721) provienen
de que la ficha encadena valores intermedios redondeados (F=2.42, Th=0.227);
se ancla al recálculo y se acepta la ficha con tolerancia.
"""
import pytest

from terzaghi.consolidation import (
    Fn_barron,
    Fn_hansbo,
    Th_from_Uh,
    Th_radial,
    Tv_from_Uv,
    U_combined_carrillo,
    Uh_radial,
    Uv_terzaghi,
    drain_influence_diameter_m,
    time_years_radial,
    time_years_vertical,
)


class TestTerzaghiVerticalW00255:
    """Consolidación vertical sin drenes (Terzaghi 1943, ficha W00255)."""

    def test_Tv90_vale_0_848(self):
        # Recalc a mano: -(4/pi^2)*ln((1-0.9)*pi^2/8) = 0.84809
        Tv90 = Tv_from_Uv(0.90)
        assert Tv90 == pytest.approx(0.84809, abs=2e-4)   # oráculo recalculado
        assert Tv90 == pytest.approx(0.848, abs=1e-3)     # ficha W00255

    def test_Uv_de_Tv090848_recupera_90pct(self):
        # Ida y vuelta con la rama exponencial: Uv(0.848) = 0.900
        assert Uv_terzaghi(0.848) == pytest.approx(0.900, abs=5e-4)

    def test_tiempo_sin_drenes_14_1_anios(self):
        # d = H/2 = 5 m (drenaje doble); t = Tv90*25/1.5 = 14.13 años.
        # LECCION UNIDADES: cv en m²/año y t en años — nombres explícitos.
        t = time_years_vertical(Tv_from_Uv(0.90), d_drain_m=5.0, cv_m2_per_year=1.5)
        assert t == pytest.approx(14.13, abs=0.02)        # oráculo recalculado
        assert t == pytest.approx(14.1, abs=0.1)          # ficha W00255

    def test_rama_raiz_para_U_bajo(self):
        # Uv = sqrt(4*Tv/pi): Tv=0.197 (valor tabulado clásico U=50%) -> 0.5008
        assert Uv_terzaghi(0.197) == pytest.approx(0.5008, abs=1e-3)


class TestBarronDrenesW00255:
    """Drenes verticales, malla triangular l=1.5 m (Barron 1948, ficha W00255)."""

    D = drain_influence_diameter_m(1.5, "triangular")     # 1.575 m
    N = D / 0.066                                          # 23.864

    def test_diametro_influencia_triangular(self):
        assert self.D == pytest.approx(1.575, abs=1e-9)   # 1.05*l, ficha W00255

    def test_Fn_barron_2_42(self):
        Fn = Fn_barron(self.N)
        assert Fn == pytest.approx(2.4224, abs=5e-4)      # ln(23.864)-0.75 recalc
        assert Fn == pytest.approx(2.42, abs=0.01)        # ficha W00255

    def test_Th90_0_697(self):
        Th = Th_from_Uh(0.90, Fn_barron(self.N))
        assert Th == pytest.approx(0.69721, abs=5e-4)     # -F*ln(0.1)/8 recalc
        assert Th == pytest.approx(0.696, abs=2e-3)       # ficha W00255

    def test_tiempo_con_drenes_0_576_anios(self):
        Th = Th_from_Uh(0.90, Fn_barron(self.N))
        t = time_years_radial(Th, D_m=self.D, ch_m2_per_year=3.0)
        assert t == pytest.approx(0.5765, abs=1e-3)       # recalc: 0.697*1.575²/3
        assert t == pytest.approx(0.575, abs=0.005)       # ficha W00255 (~7 meses)
        assert t * 12 == pytest.approx(7.0, abs=0.2)


class TestElPratW00254:
    """Ejemplo aeropuerto El Prat (ficha W00254): Uh a los 8 meses."""

    def test_cadena_completa_Uh_49pct(self):
        D = drain_influence_diameter_m(2.0, "triangular")            # 2.10 m
        n = D / 0.066                                                 # 31.818
        assert n == pytest.approx(31.818, abs=0.01)                  # ficha: 31.8
        Fn = Fn_barron(n)
        assert Fn == pytest.approx(2.71004, abs=5e-4)                # recalc
        assert Fn == pytest.approx(2.71, abs=0.005)                  # ficha W00254
        Th = Th_radial(ch_m2_per_year=1.5, t_years=8.0 / 12.0, D_m=D)
        assert Th == pytest.approx(0.226757, abs=2e-4)               # recalc
        assert Th == pytest.approx(0.227, abs=1e-3)                  # ficha W00254
        Uh = Uh_radial(Th, Fn)
        assert Uh == pytest.approx(0.48797, abs=5e-4)                # recalc
        assert Uh == pytest.approx(0.49, abs=0.005)                  # ficha W00254


class TestHansboCarrillo:
    """Coherencia Hansbo 1981 y Carrillo 1942 (fórmulas ficha W00255)."""

    def test_hansbo_sin_smear_ni_resistencia_es_barron(self):
        # s=1, qw=None -> F Hansbo == F Barron (colapso exacto).
        assert Fn_hansbo(23.864) == pytest.approx(Fn_barron(23.864), abs=1e-12)

    def test_hansbo_con_smear_aumenta_F(self):
        # Smear (s=2, kh/ks=3) retrasa la consolidación: F mayor que Barron.
        F_smear = Fn_hansbo(23.864, s=2.0, kh_over_ks=3.0)
        # Recalc a mano: ln(23.864/2) + 3*ln(2) - 0.75 = 2.4794 + 2.0794 - 0.75
        #  ... ln(11.932)=2.4794; 3*ln2=2.0794 -> F = 3.8088
        assert F_smear == pytest.approx(3.8088, abs=1e-3)
        assert F_smear > Fn_barron(23.864)

    def test_carrillo_combinada(self):
        # 1-U = (1-0.5)*(1-0.49) -> U = 0.745 (recalc directo).
        assert U_combined_carrillo(0.5, 0.49) == pytest.approx(0.745, abs=1e-9)
