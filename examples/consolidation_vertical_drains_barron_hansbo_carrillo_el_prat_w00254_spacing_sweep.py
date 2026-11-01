"""Drenes verticales prefabricados: Barron (dren ideal), Hansbo (remoldeo y resistencia del dren) y Carrillo (vertical + radial), con las fichas W00255 y W00254 (aeropuerto de El Prat).

W00255: malla triangular l = 1,5 m, d_w = 0,066 m (banda 100 × 4 mm), c_h = 3 m²/año → D = 1,05·l,
n = D/d_w = 23,9, F(n) = ln n − 3/4 = 2,42, T_h(90 %) = 0,696 y t = 0,575 años (6,9 meses) frente a
14,1 años sin drenes. W00254 (El Prat): l = 2,0 m, c_h = 1,5 m²/año, a los 8 meses U_h = 0,49. Se
recorre la separación de 1,0 a 2,5 m, se añade el remoldeo (s = 2, k_h/k_s = 3) y la resistencia del
dren (q_w = 100 m³/año) de Hansbo, y se combina con la consolidación vertical por Carrillo.

Ejecutar:  python examples/consolidation_vertical_drains_barron_hansbo_carrillo_el_prat_w00254_spacing_sweep.py
"""
from terzaghi.consolidation import (Fn_barron, Fn_hansbo, Th_from_Uh, Th_radial, Tv_from_Uv, Tv_vertical, U_combined_carrillo, Uh_radial,
                                    Uv_terzaghi, drain_influence_diameter_m, time_years_radial, time_years_vertical)

DW, CH, CV, H = 0.066, 3.0, 1.5, 10.0


def main() -> None:
    D = drain_influence_diameter_m(1.5, "triangular")
    n = D / DW
    Fn = Fn_barron(n)
    Th90 = Th_from_Uh(0.90, Fn)
    t90 = time_years_radial(Th90, D, CH)
    print("W00255 — malla triangular l = 1,5 m, d_w = 0,066 m, c_h = 3 m²/año:")
    print(f"  D = 1,05·l = {D:.3f} m; n = D/d_w = {n:.2f} (ficha 23,9); F(n) = ln n − 0,75 = {Fn:.4f} (2,42); T_h(90 %) = {Th90:.4f} (0,696); t_90 = T_h·D²/c_h = {t90:.3f} años = {t90 * 12:.1f} meses (ficha 0,575)")
    print(f"  Sin drenes: {time_years_vertical(Tv_from_Uv(0.90), H / 2, CV):.1f} años → los drenes dividen el plazo por {time_years_vertical(Tv_from_Uv(0.90), H / 2, CV) / t90:.0f}\n")
    print(f"  {'l [m]':>5} {'malla':>10} {'D [m]':>6} {'n':>6} {'F(n)':>6} {'t_90 Barron [meses]':>19} {'t_90 Hansbo s=2,kh/ks=3 [meses]':>31} {'+ q_w = 100 m³/año [meses]':>26}")
    for l in (1.0, 1.25, 1.5, 2.0, 2.5):
        for malla in ("triangular", "square"):
            D_ = drain_influence_diameter_m(l, malla)
            n_ = D_ / DW
            tb = time_years_radial(Th_from_Uh(0.90, Fn_barron(n_)), D_, CH) * 12
            th = time_years_radial(Th_from_Uh(0.90, Fn_hansbo(n_, s=2.0, kh_over_ks=3.0)), D_, CH) * 12
            tq = time_years_radial(Th_from_Uh(0.90, Fn_hansbo(n_, s=2.0, kh_over_ks=3.0, z_m=H / 2, H_drain_m=H, kh_m_per_year=0.3, qw_m3_per_year=100.0)), D_, CH) * 12
            print(f"  {l:5.2f} {malla:>10} {D_:6.3f} {n_:6.1f} {Fn_barron(n_):6.3f} {tb:19.1f} {th:31.1f} {tq:26.1f}")
    print("\nW00254 — El Prat: l = 2,0 m triangular, c_h = 1,5 m²/año, t = 8 meses:")
    D2 = drain_influence_diameter_m(2.0, "triangular")
    n2 = D2 / DW
    Th = Th_radial(1.5, 8 / 12, D2)
    Uh = Uh_radial(Th, Fn_barron(n2))
    print(f"  D = {D2:.2f} m, n = {n2:.1f}, F(n) = {Fn_barron(n2):.3f}; T_h = c_h·t/D² = {Th:.4f} (ficha 0,227); U_h = 1 − e^(−8T_h/F) = {Uh:.3f} (ficha 0,49)")
    Uv = Uv_terzaghi(Tv_vertical(CV, 8 / 12, H / 2))
    print(f"  Vertical a los 8 meses (c_v = 1,5, d = 5 m): U_v = {Uv:.3f}; combinada (Carrillo) 1 − (1 − U_v)(1 − U_h) = {U_combined_carrillo(Uv, Uh):.3f}")
    print("\nEl remoldeo (s = 2, k_h/k_s = 3) alarga el plazo un 60 %; la resistencia del dren con q_w = 100 m³/año añade otro 15–20 % en un estrato de 10 m. "
          "A igual separación la malla cuadrada tarda un 20 % más que la triangular (D = 1,13·l frente a 1,05·l, y el tiempo va con D²).")


if __name__ == "__main__":
    main()
