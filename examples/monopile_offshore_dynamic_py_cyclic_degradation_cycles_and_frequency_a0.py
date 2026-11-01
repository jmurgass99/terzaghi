"""Monopilote eólico de 7 m en arcilla y en arena: curvas p-y cíclicas con degradación por número de ciclos y factor dinámico a_0 = ωD/V_s.

`calculate_monopile_dynamic_py` parte de la curva estática (Matlock en arcilla, Reese simplificado en
arena), reduce p_ult por ciclos con 1 − λ·log₁₀(N) (λ = 0,08, cota 0,3) y multiplica la rigidez inicial
por 1 + β·a_0² (β = 0,15). Se recorren N = 1, 10², 10³, 10⁴ ciclos y frecuencias de 0,1 a 1 Hz
(rotor 1P/3P y oleaje) a z = 6 m. Los coeficientes λ y β son paramétricos, no de norma: el ejemplo
muestra su efecto, no lo valida.

Ejecutar:  python examples/monopile_offshore_dynamic_py_cyclic_degradation_cycles_and_frequency_a0.py
"""
import math

from terzaghi.piles.dynamic_py import MonopileDynamicPyInput, calculate_monopile_dynamic_py

BASE = dict(z_m=6.0, D_m=7.0, Vs_m_per_s=180.0, rho_soil_kg_m3=1950.0, gamma_kN_m3=18.5, eps_50=0.01, n_points=40)


def main() -> None:
    for soil, extra in (("clay", dict(su_kPa=90.0)), ("sand", dict(phi_deg=35.0, k_pH_kN_m3=30_000.0))):
        print(f"=== {soil} — D = 7 m, z = 6 m, V_s = 180 m/s {extra} ===")
        print(f"  {'N ciclos':>8} {'f [Hz]':>6} {'a_0':>6} {'p_ult est. [kN/m]':>17} {'p_ult cíclico [kN/m]':>20} {'reducción':>9} {'mult. rigidez':>13} {'p_din(y = 50 mm) [kN/m]':>23}")
        for N in (1, 100, 1000, 10000):
            for f in (0.2, 1.0):
                r = calculate_monopile_dynamic_py(MonopileDynamicPyInput(soil_type=soil, frequency_Hz=f, num_cycles=N, **BASE, **extra))
                a0 = 2 * math.pi * f * BASE["D_m"] / BASE["Vs_m_per_s"]
                i50 = min(range(len(r.y_m)), key=lambda i: abs(r.y_m[i] - 0.05))
                print(f"  {N:8d} {f:6.2f} {a0:6.3f} {r.p_ult_static_kN_m:17.0f} {r.p_ult_cyclic_kN_m:20.0f} {1 - r.p_ult_cyclic_kN_m / r.p_ult_static_kN_m:9.1%} {r.stiffness_multiplier:13.4f} {r.p_dynamic_kN_m[i50]:23.0f}")
        print()
    r = calculate_monopile_dynamic_py(MonopileDynamicPyInput(soil_type="clay", su_kPa=90.0, frequency_Hz=0.2, num_cycles=1000, **BASE))
    print(f"Arcilla, N = 1000: reducción = 1 − 0,08·log₁₀(1000) = {1 - 0.08 * 3:.2f}; a_0 = 2π·0,2·7/180 = {2 * math.pi * 0.2 * 7 / 180:.4f}, multiplicador 1 + 0,15·a_0² = {1 + 0.15 * (2 * math.pi * 0.2 * 7 / 180) ** 2:.4f}: "
      f"p_ult cíclico {r.p_ult_cyclic_kN_m:.0f} kN/m, y_50 = 2,5·ε_50·D = {2.5 * 0.01 * 7 * 1e3:.0f} mm")
    print("A frecuencias de rotor (0,2–1 Hz) a_0 < 0,25 y la rigidez dinámica apenas sube; lo que manda es la degradación cíclica: 10⁴ ciclos quitan un tercio de p_ult. "
          "DNV-RP-C212 pide curvas cíclicas calibradas con ensayos; estos coeficientes son de anteproyecto.")


if __name__ == "__main__":
    main()
