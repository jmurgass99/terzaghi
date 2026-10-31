# -*- coding: utf-8 -*-
"""Golden tests — Mononobe-Okabe, rama +kv de la ficha W00678.

Ficha ancla: **W00678** "Seismic design of foundations" (UPC, mismo ejemplo
que W00704, que ya ancla la rama ψ=12.5°/Kae=0.471 en
``test_gabion_wall_safety.py``). Aquí se ancla la OTRA rama del ejemplo:

Caso: muro H=6 m, γ=18 kN/m³, φ=36°, δ=20°, kh=0.2, kv=0.1; valores de
diseño EC8 (γφ=1.25): φd = atan(tan36/1.25) = 30.16°, δd = 16.23°.

  Rama "+kv" de la ficha: ψ = atan(kh/(1+kv)) = atan(0.2/1.1) = 10.30°.
  CONVENCIÓN: Terzaghi usa ψ = atan(kh/(1−kv)) ⇒ esta rama se obtiene pasando
  kv = −0.1 (el signo de kv del código es opuesto a la etiqueta de la ficha,
  igual que documenta el test de W00704).

Oráculo independiente — M-O transcrito a mano (EC8 Anexo E / M-O clásico),
con φd=30.1594°, δd=16.2298°, ψ=10.3049°, β=θ=0:

  Kae = cos²(φd−ψ) / { cosψ·cos(δd+ψ)·[1+√(sin(φd+δd)·sin(φd−ψ) /
        cos(δd+ψ))]² } = 0.88468 / 2.04520 = 0.4326

  Ed  = ½·Kae·γ·H²·(1+kv) = 0.4326·324·1.1 = 154.2 kN/m   (ficha: 154.7)
  He  = [PA·H/3 + (Ed−PA)·H/2] / Ed ≈ 2.37 m               (ficha: 2.38)

ERRATA documentada (regla de oro): la ficha W00678 imprime "K=0.446" para
esta rama, pero ese valor NO se reproduce con M-O y sus propios φd/δd/ψ
(recalc: 0.432−0.434 según redondeo de ángulos). Su propio Ed=154.7 kN/m
implica K = 154.7/(324·1.1) = 0.434, que SÍ coincide con el recálculo
(Δ=0.4%). Se ancla al recálculo 0.4326, no al 0.446 impreso.
"""
import pytest

from terzaghi.gabion_wall_safety import (
    active_thrust_coulomb,
    mononobe_okabe_seismic_coefficient,
)

GAMMA = 18.0    # kN/m3
H = 6.0         # m
PHI_D = 30.16   # deg = atan(tan(36)/1.25)   (γφ=1.25, EC8/EC7 M2)
DELTA_D = 16.23  # deg = atan(tan(20)/1.25)
KH = 0.2
KV_FICHA_MAS = -0.1   # rama "+kv" ficha (ψ=atan(0.2/1.1)) en convención Terzaghi


class TestKaeRamaMasKvW00678:
    """Kae de la rama ψ=10.3° — ancla al recálculo, documenta errata 0.446."""

    def test_Kae_recalculado_0_4326(self):
        Kae = mononobe_okabe_seismic_coefficient(
            phi_deg=PHI_D, kh=KH, kv=KV_FICHA_MAS, delta_deg=DELTA_D)
        # Oráculo a mano (ver docstring): 0.4326 con ángulos exactos;
        # 0.4319-0.4333 según el redondeo de φd/δd a 2 decimales.
        assert Kae == pytest.approx(0.4326, abs=2e-3)
        # La errata impresa (0.446) queda FUERA del ancla:
        assert abs(Kae - 0.446) > 0.01

    def test_Ed_reproduce_el_de_la_ficha(self):
        # Ed = ½·Kae·γ·H²·(1+kv); ficha: 154.7 kN/m (recalc: 154.0-154.2).
        Kae = mononobe_okabe_seismic_coefficient(
            phi_deg=PHI_D, kh=KH, kv=KV_FICHA_MAS, delta_deg=DELTA_D)
        Ed = 0.5 * Kae * GAMMA * H ** 2 * 1.1
        assert Ed == pytest.approx(154.1, abs=0.8)       # oráculo recalculado
        assert Ed == pytest.approx(154.7, rel=0.01)      # ficha W00678
        # Consistencia interna de la ficha: su Ed implica K=0.434, no 0.446.
        assert 154.7 / (0.5 * GAMMA * H ** 2 * 1.1) == pytest.approx(0.434, abs=1e-3)


class TestAlturaEquivalenteW00678:
    """Punto de aplicación combinado He del empuje sísmico total.

    Estático (triangular) a H/3; incremento sísmico ΔPae a H/2 (EC8).
    Recalc con PA=96.65 y Ed=154.2: He = (193.3+172.7)/154.2 = 2.373 m.
    """

    def test_He_2_37(self):
        Pa = active_thrust_coulomb(GAMMA, H, PHI_D, delta_deg=DELTA_D)
        Kae = mononobe_okabe_seismic_coefficient(
            phi_deg=PHI_D, kh=KH, kv=KV_FICHA_MAS, delta_deg=DELTA_D)
        Ed = 0.5 * Kae * GAMMA * H ** 2 * 1.1
        He = (Pa * H / 3.0 + (Ed - Pa) * H / 2.0) / Ed
        assert He == pytest.approx(2.373, abs=0.01)      # oráculo recalculado
        assert He == pytest.approx(2.38, abs=0.02)       # ficha W00678/W00704

    def test_Ed_mayor_que_estatico(self):
        # Coherencia física: el empuje sísmico total supera al estático.
        Pa = active_thrust_coulomb(GAMMA, H, PHI_D, delta_deg=DELTA_D)
        Kae = mononobe_okabe_seismic_coefficient(
            phi_deg=PHI_D, kh=KH, kv=KV_FICHA_MAS, delta_deg=DELTA_D)
        Ed = 0.5 * Kae * GAMMA * H ** 2 * 1.1
        assert Ed > Pa
