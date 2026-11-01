"""Cuándo y con qué espesor sostener un túnel: barrido de la convergencia previa a la instalación (10–90 %) y del espesor del anillo (100–400 mm) sobre la presión de equilibrio.

Túnel R₀ = 4 m, P₀ = 800 kPa en terreno E = 60 MPa, ν = 0,30, c = 60 kPa, φ = 25° (P_cr alto: casi toda la
convergencia es plástica). Un anillo instalado pronto se lleva mucha presión (y puede agotarse); uno
tardío trabaja poco pero el terreno ya ha convergido más. El espesor sube K_s linealmente y la capacidad
de aro ε_y·E·t/R₀.

Ejecutar:  python examples/tunnel_support_installation_delay_and_liner_thickness_sweep_equilibrium_pressure.py
"""
from terzaghi.tunnels import TunnelWinklerInput, calculate_tunnel_confinement

BASE = dict(R0_m=4.0, P0_kPa=800.0, E_soil_MPa=60.0, nu_soil=0.30, c_kPa=60.0, phi_deg=25.0, E_liner_GPa=30.0, nu_liner=0.20, n_points=80)


def main() -> None:
    r0 = calculate_tunnel_confinement(TunnelWinklerInput(**BASE, thickness_mm=250.0, unsupported_convergence_ratio=0.3))
    print(f"R₀ = 4 m, P₀ = 800 kPa: P_cr = {r0.Pcr_kPa:.0f} kPa, convergencia libre {r0.max_convergence_unsupported_mm:.1f} mm ({r0.max_convergence_unsupported_mm / 4000 * 100:.2f} % de R₀), R_p(P_i = 0) = {r0.R_p_at_zero_pressure_m:.2f} m\n")
    print("Anillo de 250 mm según el momento de instalación:")
    print(f"  {'conv. previa':>12} {'u_activación [mm]':>17} {'p_eq [kPa]':>10} {'p_eq/P₀':>7} {'u_eq [mm]':>9} {'capacidad aro [kPa]':>19}  estado")
    for ratio in (0.1, 0.2, 0.3, 0.5, 0.7, 0.9):
        r = calculate_tunnel_confinement(TunnelWinklerInput(**BASE, thickness_mm=250.0, unsupported_convergence_ratio=ratio))
        cap = 0.0015 * BASE["E_liner_GPa"] * 1e6 * 0.25 / 4.0
        print(f"  {ratio:12.0%} {r.liner_activation_displacement_mm:17.1f} {r.equilibrium_pressure_kPa:10.1f} {r.equilibrium_pressure_kPa / 800:7.3f} {r.equilibrium_displacement_mm:9.1f} {cap:19.0f}  {r.equilibrium_status}")
    print("\nInstalación al 30 % según el espesor del anillo:")
    print(f"  {'t [mm]':>6} {'K_s [kPa/mm]':>12} {'p_eq [kPa]':>10} {'u_eq [mm]':>9} {'capacidad aro [kPa]':>19} {'uso':>6}  estado")
    for t in (100.0, 150.0, 200.0, 250.0, 300.0, 400.0):
        r = calculate_tunnel_confinement(TunnelWinklerInput(**BASE, thickness_mm=t, unsupported_convergence_ratio=0.3))
        cap = 0.0015 * BASE["E_liner_GPa"] * 1e6 * (t / 1000) / 4.0
        print(f"  {t:6.0f} {r.K_support_kPa_mm:12.1f} {r.equilibrium_pressure_kPa:10.1f} {r.equilibrium_displacement_mm:9.1f} {cap:19.0f} {r.equilibrium_pressure_kPa / cap:6.2f}  {r.equilibrium_status}")
    print("\nRetrasar el anillo del 10 al 50 % de la convergencia baja la presión que recibe de 472 a 98 kPa a costa de 110 mm más de convergencia: es el principio del NATM. "
          "A partir de 100 mm el anillo es tan rígido frente al terreno (K_s ≫ pendiente de la curva de reacción) que p_eq apenas depende del espesor: el equilibrio lo fija el momento de instalación, y el uso de la capacidad de aro se queda por debajo de 0,2. "
          "Un anillo rígido instalado muy pronto en terreno peor puede superar su capacidad de aro (uso > 1) y el paquete lo marca como colapso aunque el terreno sea estable.")


if __name__ == "__main__":
    main()
