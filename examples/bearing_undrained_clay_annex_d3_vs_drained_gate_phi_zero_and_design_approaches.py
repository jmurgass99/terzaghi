"""Zapata sobre arcilla no drenada: cláusula D.3 de EN 1997-1 frente a la puerta drenada con φ = 0, y la resistencia de diseño por los tres enfoques de diseño (DA1-C1, DA1-C2, DA2).

Arcilla c_u = 75 kPa, γ = 18 kN/m³, zapatas 2,5 × 2,5 y 2,0 × 4,0 m a 1,5 m, con y sin excentricidad
(e_B = 0,30 m) y con carga inclinada (H/V = 150/1000). La fórmula no drenada es
q_ult = (π + 2)·c_u·s_c·i_c + q, con s_c = 1 + 0,2·B'/L' e i_c = ½·(1 + √(1 − H/(A'·c_u))). La puerta
drenada con φ = 0 y c' = c_u da N_q = 1, s_q = i_q = 1 y el mismo N_c = π + 2: coincide bit a bit. Después
se aplican los factores parciales del Anexo A: DA1-C1 (γ_cu = 1,0, γ_R;v = 1,0), DA1-C2 (γ_cu = 1,4) y
DA2 (γ_R;v = 1,4).

Ejecutar:  python examples/bearing_undrained_clay_annex_d3_vs_drained_gate_phi_zero_and_design_approaches.py
"""
import math

from terzaghi._foundation.bearing_capacity import undrained_bearing_capacity
from terzaghi._foundation.geometry import RectangularFoundation
from terzaghi._foundation.soil import SoilLayer
from terzaghi.bearing_capacity import evaluate_bearing_ec7

CU, GAMMA, DF = 75.0, 18.0, 1.5
CASOS = [("C1 2,5 × 2,5 centrada", 2.5, 2.5, 0.0, 0.0), ("C2 2,0 × 4,0 centrada", 2.0, 4.0, 0.0, 0.0),
         ("C3 2,5 × 2,5, e_B = 0,30", 2.5, 2.5, 0.30, 0.0), ("C4 2,5 × 2,5, H = 150 kN", 2.5, 2.5, 0.0, 150.0)]
DA = {"DA1-C1": dict(gamma_cu=1.0, gamma_Rv=1.0), "DA1-C2": dict(gamma_cu=1.4, gamma_Rv=1.0), "DA2": dict(gamma_cu=1.0, gamma_Rv=1.4)}


def undrained(B, L, e_B, H, **gf):
    return undrained_bearing_capacity(
        foundation=RectangularFoundation(length=L * 1000, width=B * 1000, thickness=400, embedment_depth=DF * 1000),
        soil=SoilLayer(thickness=10.0, friction_angle=0.0, cohesion=0.0, undrained_shear_strength=CU, unit_weight=GAMMA),
        e_y=e_B, H_load=H, **gf)


def main() -> None:
    print(f"Arcilla c_u = {CU:.0f} kPa, γ = {GAMMA:.0f} kN/m³, D_f = {DF} m; N_c = π + 2 = {math.pi + 2:.4f}\n")
    print(f"  {'caso':26} {'s_c':>6} {'i_c':>6} {'q_ult D.3 [kPa]':>15} {'puerta φ=0 [kPa]':>16} {'diferencia':>10}")
    for nombre, B, L, e_B, H in CASOS:
        u = undrained(B, L, e_B, H)
        d = evaluate_bearing_ec7(B_m=B, L_m=L, D_f_m=DF, phi_deg=0.0, c_kPa=CU, gamma_kN_m3=GAMMA, e_B_m=e_B, H_kN=H, V_kN=1000.0 if H else 0.0)
        print(f"  {nombre:26} {u.sc:6.3f} {u.ic:6.3f} {u.q_ult:15.3f} {d.q_ult:16.3f} {u.q_ult - d.q_ult:10.2e}")
    print("\nResistencia de diseño R_d = q_ult(c_u/γ_cu)·A'/γ_R;v para la zapata 2,5 × 2,5 centrada:")
    print(f"  {'enfoque':8} {'γ_cu':>5} {'γ_R;v':>6} {'c_u,d [kPa]':>11} {'q_ult [kPa]':>11} {'R_k [kN]':>9} {'R_d [kN]':>9}")
    for da, gf in DA.items():
        u = undrained(2.5, 2.5, 0.0, 0.0, **gf)
        print(f"  {da:8} {gf['gamma_cu']:5.2f} {gf['gamma_Rv']:6.2f} {u.cu_d:11.2f} {u.q_ult:11.1f} {u.R_k:9.0f} {u.R_d:9.0f}")
    q = GAMMA * DF
    print(f"\nComprobación a mano C1: s_c = 1 + 0,2·B'/L' = 1,2; q_ult = 5,1416·75·1,2 + {q:.0f} = {(math.pi + 2) * CU * 1.2 + q:.2f} kPa.")
    print("DA1-C2 reduce la resistencia del material (c_u/1,4) y DA2 la resistencia global (/1,4): no dan el mismo R_d (2235 frente a 2186 kN) porque el término q = γ·D_f no lleva c_u: DA2 lo divide por 1,4 y DA1-C2 lo deja intacto.")


if __name__ == "__main__":
    main()
