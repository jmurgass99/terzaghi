"""Consolidación unidimensional de Terzaghi para una precarga (ficha W00255): T_v para el 90 %, 14,1 años con drenaje doble, y la curva U–t con drenaje simple o doble.

Arcilla de 10 m con c_v = 1,5 m²/año drenada por arriba y por abajo (camino de drenaje d = H/2 = 5 m).
U_v(T_v) con las dos ramas clásicas (√(4T_v/π) hasta U = 0,6 y 1 − (8/π²)·e^(−π²T_v/4) después);
T_v(0,90) = 0,848 y t = T_v·d²/c_v = 14,1 años. Con drenaje simple d = H y el tiempo se multiplica
por 4. Se tabula U a 1, 2, 5, 10, 14 y 20 años y el tiempo para 50, 70, 90 y 95 %.

Ejecutar:  python examples/consolidation_terzaghi_1d_precarga_w00255_t90_double_drainage_and_degree_vs_time.py
"""
import math

from terzaghi.consolidation import Tv_from_Uv, Tv_vertical, Uv_terzaghi, time_years_vertical

H, CV = 10.0, 1.5


def main() -> None:
    print(f"Arcilla H = {H:.0f} m, c_v = {CV} m²/año (ficha W00255 «Precarga», UPC)\n")
    Tv90 = Tv_from_Uv(0.90)
    print(f"T_v(U = 90 %) = −(4/π²)·ln(0,1·π²/8) = {Tv90:.5f} (ficha 0,848); comprobación U_v({Tv90:.3f}) = {Uv_terzaghi(Tv90):.4f}")
    print(f"Drenaje doble (d = H/2 = {H / 2:.0f} m): t_90 = T_v·d²/c_v = {time_years_vertical(Tv90, H / 2, CV):.2f} años (ficha 14,1)")
    print(f"Drenaje simple (d = H = {H:.0f} m): t_90 = {time_years_vertical(Tv90, H, CV):.1f} años (×4)\n")
    print(f"  {'U [%]':>5} {'T_v':>7} {'t doble [años]':>14} {'t simple [años]':>15}")
    for U in (0.30, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95):
        Tv = Tv_from_Uv(U)
        print(f"  {U * 100:5.0f} {Tv:7.4f} {time_years_vertical(Tv, H / 2, CV):14.2f} {time_years_vertical(Tv, H, CV):15.1f}")
    print(f"\n  {'t [años]':>8} {'T_v doble':>9} {'U doble [%]':>11} {'T_v simple':>10} {'U simple [%]':>12}")
    for t in (1.0, 2.0, 5.0, 10.0, 14.1, 20.0):
        Tvd, Tvs = Tv_vertical(CV, t, H / 2), Tv_vertical(CV, t, H)
        print(f"  {t:8.1f} {Tvd:9.4f} {Uv_terzaghi(Tvd) * 100:11.1f} {Tvs:10.4f} {Uv_terzaghi(Tvs) * 100:12.1f}")
    Tv_cruce = math.pi / 4 * 0.6 ** 2
    print(f"\nLas dos ramas se cruzan en U = 0,60 (T_v = {Tv_cruce:.4f}): raíz {math.sqrt(4 * Tv_cruce / math.pi):.4f} frente a exponencial {1 - 8 / math.pi ** 2 * math.exp(-math.pi ** 2 * Tv_cruce / 4):.4f} (salto < 0,5 %, inherente a la aproximación clásica).")
    print("Catorce años es inasumible para una obra: de ahí los drenes verticales del caso siguiente, que reducen el camino de drenaje a decenas de centímetros.")


if __name__ == "__main__":
    main()
