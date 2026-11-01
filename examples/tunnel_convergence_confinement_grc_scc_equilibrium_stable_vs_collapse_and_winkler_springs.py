"""Método de convergencia-confinamiento para un túnel circular: curva de reacción del terreno (Mohr-Coulomb elastoplástico), curva del sostenimiento, punto de equilibrio y muelles de Winkler.

Túnel R₀ = 3 m a presión litostática P₀ = 500 kPa en roca E = 120 MPa, ν = 0,25, c = 150 kPa, φ = 30°;
anillo de hormigón 200 mm (E = 30 GPa) colocado cuando ha ocurrido el 30 % de la convergencia libre.
P_cr = (2P₀ − σ_cm)/(k_p + 1) separa la rama elástica (u = (1 + ν)/E·(P₀ − P_i)·R₀) de la plástica con
radio R_p; la rigidez del anillo es K_s = E_s·t/(R₀²(1 − ν_s²)). El equilibrio se resuelve por bisección y
se traducen los parámetros a un muelle de Winkler elastoplástico (k, p_y, u_y). Segundo caso: suelo
blando (E = 25 MPa, c = 50 kPa, φ = 25°) con P₀ = 1200 kPa y un anillo de 100 mm colocado al 80 % → colapso:
la convergencia libre llega al 46 % del radio y la zona plástica a casi 4 radios.

Ejecutar:  python examples/tunnel_convergence_confinement_grc_scc_equilibrium_stable_vs_collapse_and_winkler_springs.py
"""
import math

from terzaghi.tunnels import TunnelWinklerInput, calculate_tunnel_confinement

ESTABLE = TunnelWinklerInput(R0_m=3.0, P0_kPa=500.0, E_soil_MPa=120.0, nu_soil=0.25, c_kPa=150.0, phi_deg=30.0, E_liner_GPa=30.0, nu_liner=0.20, thickness_mm=200.0, unsupported_convergence_ratio=0.30, n_points=60)
COLAPSO = TunnelWinklerInput(R0_m=4.0, P0_kPa=1200.0, E_soil_MPa=25.0, nu_soil=0.35, c_kPa=50.0, phi_deg=25.0, E_liner_GPa=5.0, nu_liner=0.20, thickness_mm=100.0, unsupported_convergence_ratio=0.80, n_points=40)


def main() -> None:
    for titulo, inp in (("Túnel en roca competente (R₀ = 3 m, P₀ = 500 kPa, anillo 200 mm)", ESTABLE), ("Suelo blando (R₀ = 4 m, P₀ = 1200 kPa, E = 25 MPa, anillo 100 mm al 80 % de convergencia)", COLAPSO)):
        r = calculate_tunnel_confinement(inp)
        kp = (1 + math.sin(math.radians(inp.phi_deg))) / (1 - math.sin(math.radians(inp.phi_deg)))
        scm = 2 * inp.c_kPa * math.cos(math.radians(inp.phi_deg)) / (1 - math.sin(math.radians(inp.phi_deg)))
        print(f"=== {titulo} ===")
        print(f"  k_p = {kp:.2f}, σ_cm = 2c·cos φ/(1 − sin φ) = {scm:.1f} kPa → P_cr = (2P₀ − σ_cm)/(k_p + 1) = {(2 * inp.P0_kPa - scm) / (kp + 1):.1f} kPa (paquete {r.Pcr_kPa:.1f})")
        print(f"  Convergencia libre máxima u(P_i = 0) = {r.max_convergence_unsupported_mm:.1f} mm ({r.max_convergence_unsupported_mm / (inp.R0_m * 1000) * 100:.2f} % de R₀); radio plástico a P_i = 0: R_p = {r.R_p_at_zero_pressure_m:.2f} m ({r.R_p_at_zero_pressure_m / inp.R0_m:.2f}·R₀)")
        print(f"  Anillo: K_s = E·t/(R₀²(1 − ν²)) = {r.K_support_kPa_mm:.1f} kPa/mm, activado en u = {r.liner_activation_displacement_mm:.1f} mm")
        print(f"  Equilibrio: {r.equilibrium_status} — p_eq = {r.equilibrium_pressure_kPa:.1f} kPa ({r.equilibrium_pressure_kPa / inp.P0_kPa * 100:.1f} % de P₀) en u = {r.equilibrium_displacement_mm:.2f} mm")
        print(f"  Winkler elastoplástico: k = E/(R₀(1 + ν)) = {r.k_winkler_static_kN_m3:,.0f} kN/m³, p_y = σ_cm = {r.p_yield_kPa:.1f} kPa, u_y = {r.u_yield_mm:.2f} mm")
        print("  Curva de reacción del terreno (P_i, u):")
        idx = [0, len(r.pi_support_pressure_kPa) // 6, len(r.pi_support_pressure_kPa) // 3, len(r.pi_support_pressure_kPa) // 2, 2 * len(r.pi_support_pressure_kPa) // 3, -1]
        print("    " + "  ".join(f"({r.pi_support_pressure_kPa[i]:.0f} kPa, {r.radial_displacement_mm[i]:.2f} mm)" for i in idx))
        print()
    r = calculate_tunnel_confinement(ESTABLE)
    u_el = (1 + ESTABLE.nu_soil) / (ESTABLE.E_soil_MPa * 1e3) * (ESTABLE.P0_kPa - r.Pcr_kPa) * ESTABLE.R0_m * 1e3
    print(f"Comprobación: desplazamiento al final de la rama elástica u(P_cr) = (1 + ν)/E·(P₀ − P_cr)·R₀ = {u_el:.2f} mm; el anillo de 200 mm toma el {r.equilibrium_pressure_kPa / ESTABLE.P0_kPa * 100:.0f} % de P₀ porque llega tarde (30 %) y la roca ya ha relajado.")
    print("La rama plástica es la simplificada ((P₀ − P_cr)(R_p/R₀)² + (P_cr − P_i)) y no la de Hoek con (1 − 2ν): orden de magnitud para anteproyecto; el colapso se declara si la convergencia libre supera el 10 % de R₀, si el anillo no equilibra o si supera su tensión de aro (ε_y = 0,0015).")


if __name__ == "__main__":
    main()
