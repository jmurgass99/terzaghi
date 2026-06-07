# -*- coding: utf-8 -*-
"""Golden tests — empuje activo de Coulomb y empuje sismico Mononobe-Okabe.

Ancla las funciones de ``geojm.gabion_wall_safety`` al ejemplo numerico resuelto
de la ficha maestra **W00704** (UPC, Prof. A. Drougkas, "Seismic design of
foundations - Retaining wall"), que reporta todos los valores intermedios.

Caso W00704: muro H=6 m; arena densa seca gamma=18 kN/m3, phi=36, delta=20;
demanda sismica kh=0.2, kv=0.1. La ficha aplica los factores parciales EC8 a la
resistencia del suelo ANTES de calcular los coeficientes (gamma_phi=1.25):
    phi_d = atan(tan(36)/1.25) = 30.2 deg ;  delta_d = atan(tan(20)/1.25) = 16.2 deg

Clausulas / formulas ancladas (valores cerrados, NO tautologicos):
  - Coulomb (EC7 §9, condicion drenada, beta=theta=0):
        KA = cos^2(phi-beta) /
             {cos^2(beta)*cos(beta+delta)*[1+sqrt(sin(phi+delta)sin(phi-theta)/
              (cos(beta+delta)cos(beta-theta)))]^2}
        -> con phi_d=30.2, delta_d=16.2: KA = 0.298 (ficha W00704).
        PA = 1/2 * KA * gamma * H^2 = 96.6 kN/m (ficha W00704).
  - Mononobe-Okabe (Coulomb en campo rotado el angulo sismico psi=atan(kh/(1-kv))):
        -> con phi_d=30.2, delta_d=16.2, kh=0.2, kv=0.1: Kae = 0.471 (ficha W00704).
        En el limite kh=0 (psi=0) M-O DEBE colapsar al KA estatico de Coulomb (0.298).

El golden es honesto porque KA y Kae tienen valor cerrado para (phi, delta, kh, kv)
dados; se anclan a los numeros publicados en la ficha, no al output del propio codigo.
"""
import math

import pytest

from geojm.gabion_wall_safety import (
    active_thrust_coulomb,
    mononobe_okabe_seismic_coefficient,
)

# --- Datos del ejemplo resuelto W00704 (angulos de diseno ya reducidos por gamma_phi=1.25) ---
GAMMA = 18.0   # kN/m3, arena densa seca
H = 6.0        # m, altura del muro
PHI_D = 30.2   # deg, phi de diseno = atan(tan(36)/1.25)
DELTA_D = 16.2  # deg, delta de diseno = atan(tan(20)/1.25)
KH = 0.2       # coef. sismico horizontal
KV = 0.1       # coef. sismico vertical


class TestCoulombGoldenW00704:
    """Empuje activo estatico de Coulomb anclado a W00704 (EC7 §9)."""

    def test_Ka_coulomb_vale_0_298(self):
        # KA = 2*PA/(gamma*H^2). La funcion devuelve PA directamente.
        Pa = active_thrust_coulomb(GAMMA, H, PHI_D, delta_deg=DELTA_D)
        Ka = 2.0 * Pa / (GAMMA * H ** 2)
        assert Ka == pytest.approx(0.298, abs=0.001)   # ficha W00704

    def test_empuje_activo_PA_vale_96_6_kN_m(self):
        Pa = active_thrust_coulomb(GAMMA, H, PHI_D, delta_deg=DELTA_D)
        assert Pa == pytest.approx(96.6, abs=0.5)      # ficha W00704

    def test_Ka_crece_al_reducir_phi(self):
        # Monotonia fisica: menor friccion -> mayor empuje activo.
        pa_lo = active_thrust_coulomb(GAMMA, H, 28.0, delta_deg=DELTA_D)
        pa_hi = active_thrust_coulomb(GAMMA, H, 34.0, delta_deg=DELTA_D)
        assert pa_lo > pa_hi


class TestMononobeOkabeGoldenW00704:
    """Empuje sismico activo de Mononobe-Okabe anclado a W00704 (EC8 §)."""

    def test_kh_cero_colapsa_a_coulomb_estatico(self):
        # Limite robusto a la convencion: sin sismo (kh=0, psi=0) M-O == Coulomb KA.
        Kae0 = mononobe_okabe_seismic_coefficient(phi_deg=PHI_D, kh=0.0, kv=0.0,
                                                  delta_deg=DELTA_D)
        Pa = active_thrust_coulomb(GAMMA, H, PHI_D, delta_deg=DELTA_D)
        Ka_static = 2.0 * Pa / (GAMMA * H ** 2)
        assert Kae0 == pytest.approx(Ka_static, abs=1e-6)
        assert Kae0 == pytest.approx(0.298, abs=0.001)   # ficha W00704

    def test_Kae_sismico_vale_0_471(self):
        # GOLDEN bug-catcher: el termino sismico psi debe entrar tambien en el
        # radical del denominador (cos(beta+delta+psi)). Valor cerrado ficha.
        # NOTA convencion: el codigo usa psi=atan(kh/(1-kv)); por tanto pasar
        # kv=+0.1 reproduce la fila "-kv" de la ficha (theta=12.5, K=0.471).
        # El signo de kv del codigo es OPUESTO a la etiqueta de la ficha.
        Kae = mononobe_okabe_seismic_coefficient(phi_deg=PHI_D, kh=KH, kv=KV,
                                                 delta_deg=DELTA_D)
        assert Kae == pytest.approx(0.471, abs=0.002)    # ficha W00704

    def test_Kae_mayor_que_estatico(self):
        # El sismo siempre incrementa el empuje activo: Kae > KA.
        Kae = mononobe_okabe_seismic_coefficient(phi_deg=PHI_D, kh=KH, kv=KV,
                                                 delta_deg=DELTA_D)
        Pa = active_thrust_coulomb(GAMMA, H, PHI_D, delta_deg=DELTA_D)
        Ka_static = 2.0 * Pa / (GAMMA * H ** 2)
        assert Kae > Ka_static
