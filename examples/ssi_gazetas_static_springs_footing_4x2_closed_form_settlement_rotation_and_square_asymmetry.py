"""Muelles estáticos de Gazetas (1991) para una zapata 4 × 2 m: las seis rigideces en forma cerrada, asiento y giro elásticos bajo carga, y la asimetría de balanceo que la fuente deja en zapata cuadrada.

Suelo ρ = 2000 kg/m³, V_s = 200 m/s (G = ρV_s² = 80 MPa), ν = 0,35. K_z = G·L/(1 − ν)·(0,73 + 1,54·(B/L)^0,75),
K_x = G·L/(2 − ν)·(2 + 2,5·(B/L)^0,85), K_y = K_x − 0,2·G·L/(0,75 − ν)·(1 − B/L), K_rx = G·I_x^0,75/(1 − ν)·(L/B)^0,25·
(2,4 + 0,5·B/L), K_ry = 3·G·I_y^0,75/(1 − ν)·(L/B)^0,15, K_t = 3,5·G·J^0,75·(B/L)^0,4. Con P = 1620 kN el asiento
es P/K_z = 2,0 mm. En zapata cuadrada los ajustes publicados dan K_rx/K_ry = 2,9/3,0 = 0,967 aunque la física
pida 1: el paquete lo declara en vez de retocar los coeficientes.

Ejecutar:  python examples/ssi_gazetas_static_springs_footing_4x2_closed_form_settlement_rotation_and_square_asymmetry.py
"""
from terzaghi.gazetas_springs import RATIO_ROCKING_CUADRADA, GazetasInput, evaluate_gazetas, gazetas_elastic_support_and_settlement

L, B, VS, RHO, NU = 4.0, 2.0, 200.0, 2000.0, 0.35


def main() -> None:
    r = evaluate_gazetas(GazetasInput(L_m=L, B_m=B, Vs_m_per_s=VS, rho_soil_kg_m3=RHO, nu_soil=NU))
    G = RHO * VS ** 2 / 1e3  # kPa
    Ix, Iy = L * B ** 3 / 12, B * L ** 3 / 12
    mano = {"K_z": G * L / (1 - NU) * (0.73 + 1.54 * (B / L) ** 0.75), "K_x": G * L / (2 - NU) * (2 + 2.5 * (B / L) ** 0.85)}
    mano["K_y"] = mano["K_x"] - 0.2 * G * L / (0.75 - NU) * (1 - B / L)
    mano["K_rx"] = G * Ix ** 0.75 / (1 - NU) * (L / B) ** 0.25 * (2.4 + 0.5 * B / L)
    mano["K_ry"] = 3 * G * Iy ** 0.75 / (1 - NU) * (L / B) ** 0.15
    mano["K_t"] = 3.5 * G * (Ix + Iy) ** 0.75 * (B / L) ** 0.4
    paquete = {"K_z": r.Kz_kN_per_m, "K_x": r.Kx_kN_per_m, "K_y": r.Ky_kN_per_m, "K_rx": r.Krx_kNm_per_rad, "K_ry": r.Kry_kNm_per_rad, "K_t": r.Krz_kNm_per_rad}
    print(f"Zapata {L} × {B} m, G = ρV_s² = {r.G_soil_MPa:.0f} MPa, ν = {NU}; I_x = {Ix:.3f} m⁴, I_y = {Iy:.3f} m⁴\n")
    print(f"  {'rigidez':6} {'a mano':>14} {'paquete':>14} {'unidad':>9}")
    for k in mano:
        print(f"  {k:6} {mano[k]:14.1f} {paquete[k]:14.1f} {'kN/m' if k in ('K_z', 'K_x', 'K_y') else 'kN·m/rad':>9}")
    s = gazetas_elastic_support_and_settlement(L_m=L, B_m=B, P_kN=1620.37, Mx_kNm=400.0, My_kNm=900.0, Vs_m_per_s=VS, rho_soil_kg_m3=RHO, nu_soil=NU)
    print(f"\nApoyo elástico con P = 1620,4 kN, M_x = 400, M_y = 900 kN·m: asiento P/K_z = {s.vertical_settlement_mm:.3f} mm; giros M/K_r = {s.rotation_x_rad * 1e3:.3f} y {s.rotation_y_rad * 1e3:.3f} mrad; unidades declaradas: {s.units['Kz']}, {s.units['Krx']}")
    print(f"  Giro × semilado: δ_borde ≈ θ_x·B/2 = {s.rotation_x_rad * B / 2 * 1e3:.3f} mm y θ_y·L/2 = {s.rotation_y_rad * L / 2 * 1e3:.3f} mm, a sumar o restar al asiento uniforme.\n")
    print("Zapata cuadrada: K_x = K_y exacto y K_rx/K_ry = (2,4 + 0,5)/3,0 según los coeficientes publicados")
    for lado in (1.5, 3.0, 6.0):
        q = evaluate_gazetas(GazetasInput(lado, lado, VS, RHO, NU))
        print(f"  B = L = {lado} m: K_x/K_y = {q.Kx_kN_per_m / q.Ky_kN_per_m:.6f}; K_rx/K_ry = {q.Krx_kNm_per_rad / q.Kry_kNm_per_rad:.4f} (= {RATIO_ROCKING_CUADRADA:.4f}, un 3,3 % de asimetría de la fuente)")
    print("\nEstas son rigideces estáticas de semiespacio homogéneo sin empotramiento: con la zapata enterrada Gazetas multiplica por factores de empotramiento (no incluidos) y con estratos finos hay que usar el V_s medio del bulbo. "
          "En la corrección K_x − K_y el paquete emplea la longitud total L donde Gazetas escribe la semilongitud; el término es del orden del 3 % de K y está pendiente de contrastar.")


if __name__ == "__main__":
    main()
