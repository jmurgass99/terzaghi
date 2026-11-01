"""Impedancias dinámicas de una zapata 5 × 3 m: rigideces dependientes de la frecuencia, amortiguadores de radiación (Lysmer) y amortiguamiento material, de 1 a 20 Hz.

Suelo ρ = 1850 kg/m³, V_s = 180 m/s, ν = 0,35, ξ_material = 5 %. `calculate_ssi_springs` parte de las
rigideces estáticas de Gazetas y aplica a_0 = ω·(B/2)/V_s: k_z = 1 − 0,05·(a_0 − 1) para a_0 > 1, k_rx = 1 − 0,15·a_0,
k_ry = 1 − 0,20·a_0; radiación C_z = ρ·V_La·A con V_La = 3,4·V_s/(π(1 − ν)) (analogía de Lysmer), C_x = ρ·V_s·A,
C_rx = ρ·V_La·I_x, C_t = ρ·V_s·J; material C_mat = 2·K·ξ/ω. Se tabula de 1 a 20 Hz y se saca el
amortiguamiento equivalente ξ_eq = C·ω/(2K) que vería un modelo de un grado de libertad.

Ejecutar:  python examples/ssi_dynamic_impedances_radiation_damping_frequency_sweep_and_material_damping_dashpots.py
"""
import math

from terzaghi.ssi_springs import SsiSpringsInput, calculate_ssi_springs

L, B, VS, RHO, NU, XI = 5.0, 3.0, 180.0, 1850.0, 0.35, 0.05


def main() -> None:
    VLa = 3.4 * VS / (math.pi * (1 - NU))
    print(f"Zapata {L} × {B} m, V_s = {VS} m/s, ρ = {RHO} kg/m³, ν = {NU}; V_La = 3,4·V_s/(π(1 − ν)) = {VLa:.1f} m/s; ξ_material = {XI:.0%}\n")
    r1 = calculate_ssi_springs(SsiSpringsInput(L_m=L, B_m=B, Vs_m_per_s=VS, rho_soil_kg_m3=RHO, nu_soil=NU, frequency_Hz=1.0, material_damping=XI))
    print(f"Rigideces estáticas: K_z = {r1.Kz_static_kN_m:,.0f} kN/m, K_x = {r1.Kx_static_kN_m:,.0f}, K_y = {r1.Ky_static_kN_m:,.0f}, K_rx = {r1.Krx_static_kNm_rad:,.0f} kN·m/rad, K_ry = {r1.Kry_static_kNm_rad:,.0f}, K_t = {r1.Krz_static_kNm_rad:,.0f}")
    print(f"Radiación (no depende de f): C_z = ρ·V_La·A = {r1.Cz_radiation_kNs_m:,.0f} kN·s/m, C_x = ρ·V_s·A = {r1.Cx_radiation_kNs_m:,.0f}, C_rx = ρ·V_La·I_x = {r1.Crx_radiation_kNms_rad:,.0f} kN·m·s/rad, C_ry = {r1.Cry_radiation_kNms_rad:,.0f}, C_t = {r1.Crz_radiation_kNms_rad:,.0f}\n")
    print(f"  {'f [Hz]':>6} {'a_0':>6} {'K_z,din/K_z':>11} {'K_rx,din/K_rx':>13} {'K_ry,din/K_ry':>13} {'C_z total [kN·s/m]':>18} {'ξ_eq,z':>7} {'C_rx total':>12} {'ξ_eq,rx':>8} {'C_mat/C_rad (z)':>15}")
    for f in (1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0):
        r = calculate_ssi_springs(SsiSpringsInput(L_m=L, B_m=B, Vs_m_per_s=VS, rho_soil_kg_m3=RHO, nu_soil=NU, frequency_Hz=f, material_damping=XI))
        w = r.omega_rad_s
        xi_z = r.Cz_total_kNs_m * w / (2 * r.Kz_dynamic_kN_m)
        xi_rx = r.Crx_total_kNms_rad * w / (2 * r.Krx_dynamic_kNm_rad)
        print(f"  {f:6.1f} {r.a0_dimensionless:6.3f} {r.Kz_dynamic_kN_m / r.Kz_static_kN_m:11.3f} {r.Krx_dynamic_kNm_rad / r.Krx_static_kNm_rad:13.3f} {r.Kry_dynamic_kNm_rad / r.Kry_static_kNm_rad:13.3f} {r.Cz_total_kNs_m:18,.0f} {xi_z:7.2f} {r.Crx_total_kNms_rad:12,.0f} {xi_rx:8.2f} {(r.Cz_total_kNs_m - r.Cz_radiation_kNs_m) / r.Cz_radiation_kNs_m:15.3f}")
    print("\nA 1 Hz (periodos de edificio) manda el amortiguamiento material, 1,6 veces la radiación, porque C_mat = 2Kξ/ω crece al bajar ω; a 2 Hz van parejos y desde 4 Hz domina la radiación. "
          "El ξ_eq vertical pasa del 50 % hacia 15 Hz: por eso las cimentaciones superficiales en suelo firme apenas vibran verticalmente a frecuencias de maquinaria.")
    print("Los factores k(a_0) y los dashpots de radiación son los de la tabla de Gazetas para cimentación superficial SIN los coeficientes c̄(a_0) de baja frecuencia (que reducen el amortiguamiento de balanceo a a_0 < 1): del lado optimista en rocking a frecuencias bajas.")


if __name__ == "__main__":
    main()
