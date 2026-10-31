"""Pilote en perfil estratificado: capacidad axial y curvas p-y.

Pilote hincado de 0,6 m y 18 m en arcilla blanda sobre arena, con nivel
freático a 2 m. Se calcula la capacidad axial (fuste + punta, con FS) y se
generan las curvas p-y de Matlock (arcilla blanda) y Reese (arena) a varias
profundidades, listas para alimentar un modelo de muelles no lineales.

Ejecutar:  python examples/02_pile_axial_and_py_curves.py
"""
from dataclasses import asdict

from terzaghi.piles.axial_capacity import Pile, SoilLayer, axial_capacity
from terzaghi.piles.py_curves import py_matlock_soft_clay, py_reese_sand

LAYERS = [
    SoilLayer(top_m=0.0, bottom_m=8.0, kind="clay", Su_kPa=35.0),
    SoilLayer(top_m=8.0, bottom_m=25.0, kind="sand", phi_deg=34.0),
]


def main() -> None:
    pile = Pile(diameter_m=0.6, length_m=18.0, water_table_m=2.0, delta_ratio=0.8)
    r = axial_capacity(pile, LAYERS, FS=2.5)
    print("Capacidad axial (pilote Ø0,60 m, L = 18 m):")
    for k, v in asdict(r).items():
        print(f"  {k:<24} {v if not isinstance(v, float) else round(v, 1)}")

    print("\nCurvas p-y (p en kN/m, y en m): valores a y = 0,25·y_max")
    for z in (2.0, 5.0):
        p, y = py_matlock_soft_clay(z_m=z, D_m=pile.diameter_m, su_kPa=35.0, gamma_kN_m3=17.0)
        i = len(y) // 4
        print(f"  arcilla z = {z:4.1f} m: p_ult ≈ {p.max():7.1f} kN/m, p(y={y[i]:.4f} m) = {p[i]:.1f} kN/m")
    for z in (10.0, 15.0):
        p, y = py_reese_sand(z_m=z, D_m=pile.diameter_m, phi_deg=34.0)
        i = len(y) // 4
        print(f"  arena   z = {z:4.1f} m: p_max ≈ {p.max():7.1f} kN/m, p(y={y[i]:.4f} m) = {p[i]:.1f} kN/m")


if __name__ == "__main__":
    main()
