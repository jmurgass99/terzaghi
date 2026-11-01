"""Catálogo de estratigrafías tipo (Santiago, Bogotá, Lima, Andes) para arrancar un anteproyecto y resistencia de suelos no saturados con van Genuchten y Bishop.

`estratigrafias_catalogo` guarda perfiles orientativos (γ, φ', c', E_s, N_60 por estrato) para cuatro
entornos; se listan y se usa Bogotá para una zapata a 2 m. Después, la curva de retención de van
Genuchten θ(ψ) = θ_r + (θ_s − θ_r)/[1 + (αψ)^n]^m y la resistencia de Bishop τ = c' + (σ − u_a + χ·(u_a − u_w))·tan φ'
con χ = grado de saturación efectivo: cuánto aporta la succión en un relleno compactado por encima del
nivel freático y cómo se pierde al saturarse.

Ejecutar:  python examples/stratigraphy_catalog_latin_america_profiles_and_unsaturated_van_genuchten_bishop_suction.py
"""
import math

from terzaghi.estratigrafias_catalogo import get_profile, list_profiles
from terzaghi.unsaturated import VanGenuchtenParams, chi_bishop, shear_strength_unsat, theta_of_psi


def main() -> None:
    print("Perfiles del catálogo:", ", ".join(list_profiles()))
    for name in list_profiles():
        print(f"\n  {name}:")
        print(f"    {'estrato':26} {'z [m]':>9} {'γ [kN/m³]':>9} {'φ′ [°]':>6} {'c′ [kPa]':>8} {'E_s [MPa]':>9} {'N_60':>5}")
        for s in get_profile(name):
            print(f"    {s.name:26} {f'{s.z_top_m:.1f}–{s.z_bot_m:.1f}':>9} {s.gamma_kN_m3:9.1f} {s.phi_deg:6.0f} {s.c_kPa:8.0f} {s.Es_MPa:9.0f} {s.SPT_N60:5d}")
    bog = get_profile("bogota_lacustre")
    capa = next(s for s in bog if s.z_top_m <= 2.0 < s.z_bot_m)
    print(f"\nZapata a 2 m en Bogotá cae en «{capa.name}» (φ' = 0, c = {capa.c_kPa:.0f} kPa): q_ult no drenado ≈ (π + 2)·c_u·1,2 + γ·D = {(math.pi + 2) * capa.c_kPa * 1.2 + capa.gamma_kN_m3 * 2.0:.0f} kPa para zapata cuadrada; "
          f"la arcilla blanda de debajo (c_u = 25 kPa, E_s = 4 MPa, 22 m) es la que manda en el asiento.")
    vg = VanGenuchtenParams(theta_r=0.06, theta_s=0.42, alpha_1_m=0.8, n=1.8)
    print(f"\nRelleno limo-arenoso compactado: van Genuchten θ_r = {vg.theta_r}, θ_s = {vg.theta_s}, α = {vg.alpha_1_m} 1/m, n = {vg.n} (m = 1 − 1/n = {vg.m:.3f}); c' = 5 kPa, φ' = 32°, σ = 60 kPa, u_a = 0")
    print(f"  {'ψ [m]':>6} {'u_w [kPa]':>9} {'θ':>6} {'S_e = χ':>8} {'χ·(u_a − u_w) [kPa]':>19} {'τ [kPa]':>8} {'τ/τ_sat':>7}")
    tau_sat = shear_strength_unsat(60.0, 0.0, 0.0, 0.0, 5.0, 32.0, vg)
    for psi in (0.0, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0):
        uw = -9.81 * psi
        tau = shear_strength_unsat(60.0, 0.0, uw, psi, 5.0, 32.0, vg)
        print(f"  {psi:6.1f} {uw:9.1f} {theta_of_psi(psi, vg):6.3f} {chi_bishop(psi, vg):8.3f} {chi_bishop(psi, vg) * (0.0 - uw):19.1f} {tau:8.1f} {tau / tau_sat:7.2f}")
    print("\nCon 2 m de succión la resistencia sube un 17 % y con 10 m un 27 %: χ cae con la succión pero en este rango (n = 1,8) el producto χ·s sigue creciendo; con n mayor (arenas uniformes) χ cae antes y el producto tiene máximo. "
          "Esa resistencia desaparece al saturarse el relleno (lluvia, rotura de una conducción): no se cuenta en proyecto salvo que se garantice el drenaje.")


if __name__ == "__main__":
    main()
