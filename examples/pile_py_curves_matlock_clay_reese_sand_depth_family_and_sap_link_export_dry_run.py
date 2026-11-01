"""Curvas p-y de Matlock (arcilla blanda) y Reese (arena) a varias profundidades, y su exportación como muelles multilineales para SAP2000 (`export_to_fastsap` en seco).

Pilote de 0,6 m. Matlock (1970): p_ult = min(3 + γ'z/s_u + 0,5·z/D, 9)·s_u·D, y_50 = 2,5·ε_50·D, tramo
cúbico p/p_ult = 0,5·(y/y_50)^(1/3) hasta 8·y_50. Reese-Cox-Koop simplificado en arena: p_ult =
min((K_p² − K_a), K_p)·γ·z·D, rigidez inicial k_pH·z e hipérbola. Se tabulan p_ult y p(y = 10 mm) a
z = 1, 3, 6 y 10 m y se generan los puntos (y, p) que `export_to_fastsap` enviaría a
`PropLink.SetMultiLinearPlastic`. La curva de arena del exportador NO es la de Reese (fórmula sin
referencia, documentada en el código): se compara aquí para que se vea la diferencia.

Ejecutar:  python examples/pile_py_curves_matlock_clay_reese_sand_depth_family_and_sap_link_export_dry_run.py
"""
import numpy as np

from terzaghi.integration.fastsap_pysprings import FastSAPPySpringsConfig, PySpringNode, build_py_curve, export_to_fastsap
from terzaghi.piles import py_matlock_soft_clay, py_reese_sand

D, SU, GAMMA_C, PHI, GAMMA_S = 0.6, 40.0, 17.0 - 9.81, 32.0, 18.0


def p_at(p, y, y0):
    return float(np.interp(y0, y, p))


def main() -> None:
    print(f"Pilote D = {D} m. Arcilla blanda s_u = {SU} kPa (γ' = {GAMMA_C:.2f} kN/m³, ε_50 = 0,02); arena φ' = {PHI}°, γ = {GAMMA_S} kN/m³, k_pH = 25 MN/m³\n")
    print(f"  {'z [m]':>5} {'Matlock p_ult [kN/m]':>20} {'factor N_p':>10} {'y_50 [mm]':>9} {'p(10 mm) [kN/m]':>15} | {'Reese p_ult [kN/m]':>18} {'k_ini [MN/m²]':>13} {'p(10 mm) [kN/m]':>15}")
    for z in (1.0, 3.0, 6.0, 10.0):
        pm, ym = py_matlock_soft_clay(z, D, SU, gamma_kN_m3=GAMMA_C)
        pr, yr = py_reese_sand(z, D, PHI, gamma_kN_m3=GAMMA_S)
        Np = min(3 + GAMMA_C * z / SU + 0.5 * z / D, 9.0)
        print(f"  {z:5.1f} {pm.max():20.1f} {Np:10.2f} {2.5 * 0.02 * D * 1e3:9.1f} {p_at(pm, ym, 0.010):15.1f} | {pr.max():18.1f} {25000 * z / 1e3:13.0f} {p_at(pr, yr, 0.010):15.1f}")
    print("  En arcilla p_ult crece con z hasta N_p = 9 (aquí desde z ≈ 6 m); en arena crece linealmente con z y la hipérbola llega a p_ult solo asintóticamente.\n")

    nodes = tuple(PySpringNode(z_m=z, D_m=D, su_kPa=SU, gamma_kN_m3=GAMMA_C) for z in (1.0, 3.0, 6.0)) + (PySpringNode(z_m=10.0, D_m=D, phi_deg=PHI, gamma_kN_m3=GAMMA_S),)
    cfg = FastSAPPySpringsConfig(nodes=nodes, n_points_curve=8, epsilon_50=0.02, code="EU")
    out = export_to_fastsap(cfg, dry_run=True)
    print(f"Exportación en seco: {out['applied']} muelles, dry_run = {out['dry_run']}; nombres {list(out['curves'])}")
    for name, pts in out["curves"].items():
        print(f"  {name}: " + ", ".join(f"({y * 1e3:.1f} mm, {p:.1f})" for y, p in pts[:4]) + f" … ({pts[-1][0] * 1e3:.1f} mm, {pts[-1][1]:.1f} kN/m)")
    pr10, _ = py_reese_sand(10.0, D, PHI, gamma_kN_m3=GAMMA_S)
    sand_pts = build_py_curve(nodes[-1], n=8)
    print(f"\n  Arena a 10 m: el exportador satura en {max(p for _, p in sand_pts):.1f} kN/m (fórmula 1,5·γ·z·φ/30·D, sin referencia) frente a {pr10.max():.1f} kN/m de `py_reese_sand`: "
          f"razón {pr10.max() / max(p for _, p in sand_pts):.2f}. Para muelles de arena en SAP conviene muestrear `py_reese_sand` directamente.")
    try:
        build_py_curve(PySpringNode(z_m=2.0, D_m=D))
    except ValueError as exc:
        print(f"  Nodo sin s_u ni φ → ValueError: {str(exc)[:80]}… (antes se fabricaba una arena de 30°)")


if __name__ == "__main__":
    main()
