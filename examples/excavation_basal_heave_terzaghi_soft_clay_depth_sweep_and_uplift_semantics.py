"""Estabilidad del fondo de una excavación en arcilla blanda (Terzaghi-Peck): número de estabilidad y FS de levantamiento de fondo según la profundidad, y qué significa el FS de flotación del paquete.

Excavación de 5 × 10 m en arcilla c_u = 40 kPa, γ = 18 kN/m³, sobrecarga 10 kPa. `check_excavation` da
N_b = (γ·H + q)/c_u y FS = 5,14·c_u/(γ·H + q) (N_c = 5,14 de Prandtl, sin el factor de forma ni de
profundidad de Skempton, luego del lado seguro) y, si hay nivel freático dentro de la excavación, un
FS de flotación γ·H/(γ_w·h_w) que usa la PROFUNDIDAD DE EXCAVACIÓN, no el espesor del tapón de arcilla:
se muestra con números por qué hay que leerlo con cuidado.

Ejecutar:  python examples/excavation_basal_heave_terzaghi_soft_clay_depth_sweep_and_uplift_semantics.py
"""
from terzaghi.excavation import ExcavationInput, check_excavation

SU, GAMMA, Q = 40.0, 18.0, 10.0


def main() -> None:
    print(f"Arcilla c_u = {SU:.0f} kPa, γ = {GAMMA:.0f} kN/m³, sobrecarga {Q:.0f} kPa, excavación 5 × 10 m (FS mínimo 1,5)\n")
    print(f"  {'H [m]':>5} {'N_b = (γH + q)/c_u':>18} {'FS fondo = 5,14·c_u/(γH + q)':>28} {'Skempton N_c(H/B, B/L)':>22} {'FS con N_c Skempton':>19}  veredicto")
    for H in (2.0, 4.0, 6.0, 8.0, 10.0, 12.0):
        r = check_excavation(ExcavationInput(depth_m=H, width_m=5.0, length_m=10.0, su_kPa=SU, gamma_kN_m3=GAMMA, surcharge_kPa=Q))
        Nc_sk = min(5.0 * (1 + 0.2 * 5.0 / 10.0) * (1 + 0.2 * H / 5.0), 7.5 * (1 + 0.2 * 5.0 / 10.0))
        print(f"  {H:5.1f} {r.N_b:18.2f} {r.FS_basal_heave:28.2f} {Nc_sk:22.2f} {Nc_sk * SU / (GAMMA * H + Q):19.2f}  {'ok' if r.is_safe else 'NO'}")
    H_crit = (5.14 * SU / 1.5 - Q) / GAMMA
    print(f"\n  Profundidad máxima con FS = 1,5 y N_c = 5,14: H = (5,14·c_u/1,5 − q)/γ = {H_crit:.2f} m; con N_c de Skempton (5·(1 + 0,2·B/L)·(1 + 0,2·H/B) ≤ 7,5·(1 + 0,2·B/L)) se llega más hondo.")
    print("\nFlotación: el paquete calcula FS_uplift = γ·H/(γ_w·h_w) con h_w = H − z_NF")
    for H, z_nf in ((6.0, 2.0), (6.0, 4.0), (10.0, 2.0)):
        r = check_excavation(ExcavationInput(depth_m=H, width_m=5.0, length_m=10.0, su_kPa=SU, gamma_kN_m3=GAMMA, water_table_depth_m=z_nf))
        t = 3.0
        print(f"  H = {H:.0f} m, NF a {z_nf:.0f} m → h_w = {H - z_nf:.0f} m: FS_uplift (paquete) = {r.FS_uplift:.2f}; con un tapón de arcilla de t = {t:.0f} m bajo el fondo y acuífero confinado, FS real = γ·t/(γ_w·(h_w + t)) = {GAMMA * t / (9.81 * (H - z_nf + t)):.2f}")
    print("  El valor del paquete compara el peso de la columna EXCAVADA con la presión del agua: es un indicador de que hay agua por encima del fondo, no el equilibrio del tapón. Para el tapón hace falta su espesor y la carga piezométrica del acuífero inferior; el paquete no los tiene como entrada.")
    print("\nCon c_u = 40 kPa la excavación no pasa de unos 7 m con FS = 1,5 (N_c = 5,14); más allá hacen falta pantallas empotradas bajo el fondo, mejora del terreno o rebajar el nivel freático.")


if __name__ == "__main__":
    main()
