"""Muro de gaviones escalonado de 5 m (ejemplo de M. Hanif, EN 1997-1 DA1-a, no drenado): hundimiento, deslizamiento y vuelco, estabilidad interna por cursos y círculo global.

Cinco cursos de 1 m con anchos 1,0/1,5/2,0/2,5/3,0 m (trasdós alineado), gavión γ = 23 kN/m³; relleno
γ = 19, φ' = 34° (K_a de Rankine = 0,28), c_u = 100 kPa, sobrecarga 20 kPa. El ejemplo publica W = 230 kN/m,
q_f = 5,14·c_u = 514 kPa y FS ≈ 3,3 (hundimiento), 3,08 (deslizamiento) y 3,83 (vuelco). `GabionWall`
reproduce W y q_f; el hundimiento usa la anchura efectiva B' = B − 2e (el ejemplo usa B completa) y los
factores parciales DA1-a (γ_G = 1,35, γ_Q = 1,5, material y resistencia 1,0). Se añaden los seis cursos
(deslizamiento curso a curso) y un círculo de deslizamiento global en no drenado.

Ejecutar:  python examples/gabion_wall_hanif_example_da1a_undrained_uls_1_2_3_internal_courses_and_global_circle.py
"""
import math

from terzaghi.gabion_wall import DESIGN_APPROACHES, GabionLayer, GabionSoil, GabionWall, Ka_rankine


def main() -> None:
    layers = [GabionLayer(w) for w in (1.0, 1.5, 2.0, 2.5, 3.0)]
    soil = GabionSoil(gamma_s=19.0, phi_deg=34.0, c_kPa=0.0, cu_kPa=100.0, surcharge_kPa=20.0)
    wall = GabionWall(layers=layers, soil=soil, gamma_gab=23.0, design_approach="DA1a", drained=False)
    W, M = wall.weight_and_moment()
    print(f"Muro H = {wall.H:.0f} m, B = {wall.B:.1f} m; K_a = (1 − sin 34°)/(1 + sin 34°) = {Ka_rankine(34):.3f} (ejemplo 0,28); W = {W:.0f} kN/m (230); M_estab = {M:.1f} kN·m/m")
    print(f"Empuje activo característico S_A = ½·K_a·γ'·H² + K_a·q·H = {wall.active_thrust():.1f} kN/m (γ' = γ − γ_w en no drenado); q_f = 5,14·c_u = {5.14 * 100:.0f} kPa")
    print(f"Factores parciales {wall.design_approach}: {DESIGN_APPROACHES[wall.design_approach]}\n")
    print(f"  {'verificación':30} {'E_d':>9} {'R_d':>9} {'FS = R_d/E_d':>12} {'unidades':>8}  ok   ejemplo Hanif")
    ref = {"ULS-1": "3,3 (con B completa)", "ULS-2": "3,08", "ULS-3": "3,83"}
    for c in wall.verify_all():
        print(f"  {c.name:30} {c.E_d:9.1f} {c.R_d:9.1f} {c.FS:12.2f} {c.units:>8}  {str(c.ok):5} {ref[c.name.split()[0]]}")
    print("\nEstabilidad interna (deslizamiento de cada curso sobre el inferior, ULS-6):")
    for c in wall.internal_stability():
        print(f"  {c.name:32} H = {c.E_d:6.1f} kN/m  R_d = {c.R_d:6.1f} kN/m  FS = {c.FS:5.2f}  {'ok' if c.ok else 'NO'}")
    r, La = 7.0, 2 * math.pi * 7.0 * (110 / 360)
    circ = dict(r_m=r, La_m=La, W_kN=W + 0.5 * 19 * 3.0 * 5.0, d_m=1.8)
    g = wall.global_stability_undrained(**circ)
    print(f"\nCírculo global no drenado (r = {r} m, arco {La:.1f} m, bloque {circ['W_kN']:.0f} kN/m con brazo {circ['d_m']} m): M_R = c_u·L_a·r = {g.R_d:.0f}, M_A = {g.E_d:.0f} kN·m/m → FS = {g.FS:.2f}")
    print(f"`verify_full` devuelve {len(wall.verify_full(global_circle=circ))} comprobaciones (3 externas + 5 cursos + 1 global).")
    print("\nW, K_a y q_f coinciden con el ejemplo; los FS no son comparables uno a uno (3,7/2,7/4,7 frente a 3,3/3,08/3,83) porque el paquete aplica los factores parciales DA1-a a las acciones (γ_G = 1,35) y usa B' = B − 2e en el hundimiento, mientras el ejemplo compara valores característicos con B completa. "
          "Los datos del círculo global son de entrada (radio, arco, peso, brazo): el paquete no busca el círculo crítico; para eso está `slipcircle`.")


if __name__ == "__main__":
    main()
