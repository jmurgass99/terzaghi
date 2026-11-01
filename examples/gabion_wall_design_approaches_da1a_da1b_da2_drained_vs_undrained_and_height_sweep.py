"""El mismo muro de gaviones por los tres enfoques de diseño de EN 1997-1 (DA1-a, DA1-b, DA2), en condición drenada y no drenada, y cuántos cursos hacen falta según la altura.

Muro escalonado de 1,0 a 3,0 m de ancho, relleno φ' = 34°, γ = 19, c_u = 100 kPa, sobrecarga 20 kPa. DA1-a
factoriza acciones (γ_G 1,35, γ_Q 1,5); DA1-b factoriza materiales (γ_cu 1,4) y la resistencia al
hundimiento (γ_Rb 1,25); DA2 factoriza acciones y la resistencia al deslizamiento (γ_Rh 1,1). Después se
quitan cursos de arriba (H = 5, 4, 3 m) para ver qué verificación gobierna en cada altura.

Ejecutar:  python examples/gabion_wall_design_approaches_da1a_da1b_da2_drained_vs_undrained_and_height_sweep.py
"""
from terzaghi.gabion_wall import DESIGN_APPROACHES, GabionLayer, GabionSoil, GabionWall

ANCHOS = (1.0, 1.5, 2.0, 2.5, 3.0)
SOIL = GabionSoil(gamma_s=19.0, phi_deg=34.0, c_kPa=0.0, cu_kPa=100.0, surcharge_kPa=20.0)


def fs(wall):
    return {c.name.split()[0]: c.FS for c in wall.verify_all()}


def main() -> None:
    print("Factores parciales por enfoque de diseño (EN 1997-1 Anexo A, muros):")
    for da, g in DESIGN_APPROACHES.items():
        print(f"  {da:5} γ_G = {g['gG']:.2f}, γ_Q = {g['gQ']:.2f}, γ_φ = {g['gphi']:.2f}, γ_cu = {g['gcu']:.2f}, γ_Rh = {g['gRh']:.2f}, γ_Rb = {g['gRb']:.2f}")
    print(f"\nMuro de 5 cursos (H = 5 m, B = 3 m): FS = R_d/E_d por verificación")
    print(f"  {'enfoque':8} {'condición':11} {'S_A [kN/m]':>10} {'ULS-1 hund.':>11} {'ULS-2 desl.':>11} {'ULS-3 vuelco':>12}")
    for da in DESIGN_APPROACHES:
        for drained in (False, True):
            w = GabionWall([GabionLayer(b) for b in ANCHOS], SOIL, 23.0, da, drained)
            f = fs(w)
            print(f"  {da:8} {'drenada' if drained else 'no drenada':11} {w.active_thrust():10.1f} {f['ULS-1']:11.2f} {f['ULS-2']:11.2f} {f['ULS-3']:12.2f}")
    print("\nCursos necesarios según la altura (DA1-a, no drenado): se quitan cursos por arriba")
    print(f"  {'H [m]':>5} {'anchos [m]':>26} {'W [kN/m]':>8} {'ULS-1':>6} {'ULS-2':>6} {'ULS-3':>6} {'curso crítico ULS-6':>19}  gobierna")
    for n in (5, 4, 3, 2):
        anchos = ANCHOS[-n:]
        w = GabionWall([GabionLayer(b) for b in anchos], SOIL, 23.0, "DA1a", False)
        f = fs(w)
        internos = w.internal_stability()
        crit = min(internos, key=lambda c: c.FS)
        gob = min(f, key=f.get)
        print(f"  {w.H:5.0f} {str(anchos):>26} {w.weight_and_moment()[0]:8.0f} {f['ULS-1']:6.2f} {f['ULS-2']:6.2f} {f['ULS-3']:6.2f} {crit.name.split('(')[0].strip() + f' FS {crit.FS:.2f}':>19}  {gob}")
    print("\nEn las dos condiciones gobierna el deslizamiento (FS 2,2–2,7). En drenado el empuje es un 57 % mayor (γ en vez de γ − γ_w) y el deslizamiento baja a 2,4 (fricción N·tan φ'), mientras el hundimiento se dispara con N_q y N_γ de φ' = 34°. "
          "DA1-b castiga el hundimiento no drenado (c_u/1,4 y γ_Rb = 1,25: de 3,74 a 2,89) y DA2 el deslizamiento (γ_Rh = 1,1): hay que comprobar las dos combinaciones de DA1, no elegir una.")


if __name__ == "__main__":
    main()
