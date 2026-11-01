"""Hormigón confinado de Mander, Priestley y Park (1988) para el núcleo de un pilar: K = f'cc/f'co, deformaciones ε_cc y ε_cu, curva σ-ε de Popovics y el límite sin confinar, listos para una sección de fibras en ETABS/SAP.

Pilar con núcleo 400 × 400 mm (al eje del estribo), f'c = 30 MPa, estribos f_yh = 420 MPa a s = 100 mm
(s' = 80), 8 barras arriostradas con 100 mm libres. k_e = (1 − Σw'²/(6A_c))·(1 − s'/(2b_c))·(1 − s'/(2h_c)),
f_l = k_e·ρ·f_yh, K = −1,254 + 2,254·√(1 + 7,94·f_l/f'c) − 2·f_l/f'c, ε_cc = 0,002·(1 + 5(K − 1)),
ε_cu = 0,004 + 1,4·ρ_s·f_yh·ε_su/f'cc, r = E_c/(E_c − E_sec) con E_c = 5000√f'c. Se barre la cuantía 0,25–2 %
y la separación 75–150 mm, y se muestra que con ρ → 0 se recupera el hormigón sin confinar (K = 1).

Ejecutar:  python examples/mander_confined_concrete_column_core_k_fcc_curve_and_unconfined_limit_for_etabs_fiber.py
"""
import math

from terzaghi.materials import mander_confined_concrete

FC, FYH, BC, HC = 30.0, 420.0, 400.0, 400.0


def main() -> None:
    print(f"Núcleo {BC:.0f} × {HC:.0f} mm, f'c = {FC:.0f} MPa, f_yh = {FYH:.0f} MPa, ε_su = 0,10, E_c = 5000√f'c = {5000 * math.sqrt(FC) / 1e3:.1f} GPa\n")
    print(f"  {'ρ_x = ρ_y':>9} {'s [mm]':>6} {'k_e':>6} {'f_l [MPa]':>9} {'K':>6} {'f′cc [MPa]':>10} {'ε_cc':>7} {'ε_cu':>7} {'r':>5} {'σ(ε_cu)/f′cc':>12}".replace("′", "′"))
    for rho in (0.0025, 0.005, 0.01, 0.015, 0.02):
        for s in (75.0, 100.0, 150.0):
            r = mander_confined_concrete(FC, FYH, rho, rho, BC, HC, s, s_prime_mm=s - 20.0, n_long_bars=8, w_prime_mm=100.0)
            ke = (1 - 8 * 100.0 ** 2 / (6 * BC * HC)) * (1 - (s - 20) / (2 * BC)) * (1 - (s - 20) / (2 * HC))
            Ec, Esec = 5000 * math.sqrt(FC), r.fcc_MPa / r.eps_cc
            print(f"  {rho:9.4f} {s:6.0f} {ke:6.3f} {ke * rho * FYH:9.2f} {r.K_confinement:6.3f} {r.fcc_MPa:10.1f} {r.eps_cc:7.4f} {r.eps_cu:7.4f} {Ec / (Ec - Esec):5.2f} {r.sigma_eps[-1][1] / r.fcc_MPa:12.2f}")
    r = mander_confined_concrete(FC, FYH, 0.01, 0.01, BC, HC, 100.0, s_prime_mm=80.0)
    print(f"\nCaso ρ = 1 %, s = 100 mm: K = {r.K_confinement:.4f} (a mano 1,584), f'cc = {r.fcc_MPa:.1f} MPa, ε_cc = {r.eps_cc:.4f}, ε_cu = {r.eps_cu:.4f}")
    print("  Curva σ-ε (ε, σ [MPa]) para la tabla de material no lineal:")
    pts = r.sigma_eps
    sel = [pts[i] for i in (0, 3, 6, 9, 12, 15, 20, 25, len(pts) - 1)]
    print("    " + "  ".join(f"({e:.4f}, {s:.1f})" for e, s in sel))
    u = mander_confined_concrete(FC, FYH, 1e-9, 1e-9, BC, HC, 100.0)
    print(f"\nLímite sin confinar (ρ → 0): K = {u.K_confinement:.4f}, f'cc = {u.fcc_MPa:.2f} MPa, ε_cc = {u.eps_cc:.4f}, ε_cu = {u.eps_cu:.4f}; σ a 0,004 = {next(s for e, s in u.sigma_eps if e >= 0.004 - 1e-9):.1f} MPa (rama descendente, no cero)")
    print("\nHasta la 1.0 el paquete daba K = 2,58 (f'cc = 77 MPa) por un «1 +» de más en la fórmula y una rama descendente casi vertical (r = 5/(K − 1)): un modelo así sobreestimaba la resistencia del pilar un 60 %. "
          "El k_e implementado omite el divisor (1 − ρ_cc) de Mander (efecto < 3 %) y promedia con f_l,mín en secciones rectangulares (lado seguro).")


if __name__ == "__main__":
    main()
