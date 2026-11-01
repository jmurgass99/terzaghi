"""Capacidad lateral de un grupo de pilotes con encepado empotrado (Mokwa y Duncan 2001): cuña pasiva del bloque frente a suma de pilotes individuales, barriendo separación y empotramiento.

Grupo 3 × 3 de pilotes de 0,6 m, encepado empotrado H_emb = 3–6 m en arena φ' = 30°, γ = 18 kN/m³,
con y sin cohesión (c = 0 y 20 kPa). `mokwa_duncan.analyze` calcula el empuje pasivo de Rankine del
bloque B_f × H_emb (½·K_p·γ·H² + 2·c·√K_p·H) y la suma de pilotes individuales con p-multiplicadores
medios por fila, y se queda con el menor: H_grupo = min(bloque, individuales). Con separaciones
cortas gobierna el bloque; con separaciones largas y empotramientos cortos gobiernan los pilotes.

Ejecutar:  python examples/pile_group_lateral_passive_block_vs_individual_mokwa_duncan_spacing_embedment_sweep.py
"""
import math

from terzaghi.piles.mokwa_duncan import MokwaDuncanInput, analyze

D, PHI, GAMMA = 0.6, 30.0, 18.0


def main() -> None:
    Kp = math.tan(math.radians(45 + PHI / 2)) ** 2
    print(f"Grupo 3 × 3, D = {D} m, arena φ' = {PHI}° (K_p = {Kp:.2f}), γ = {GAMMA} kN/m³, L = 12 m\n")
    for c in (0.0, 20.0):
        print(f"=== c = {c:.0f} kPa ===")
        print(f"  {'s [m]':>5} {'H_emb [m]':>9} {'B_f [m]':>7} {'p_m medio':>9} {'bloque [kN]':>11} {'individuales [kN]':>17} {'H_grupo [kN]':>12}  gobierna")
        for s in (1.2, 1.8, 3.0):
            for H in (3.0, 4.5, 6.0):
                r = analyze(MokwaDuncanInput(n_rows=3, n_cols=3, D_m=D, s_m=s, L_pile_m=12.0, H_emb_m=H, phi_deg=PHI, c_kPa=c, gamma_kN_m3=GAMMA))
                Bf = D + 2 * s
                print(f"  {s:5.1f} {H:9.1f} {Bf:7.2f} {r.p_multiplier_avg:9.3f} {r.H_block_kN:11.0f} {r.H_individual_kN:17.0f} {r.H_group_total_kN:12.0f}  {'bloque' if r.H_block_kN <= r.H_individual_kN else 'pilotes'}")
        print()
    r = analyze(MokwaDuncanInput(3, 3, D, 1.8, 12.0, 4.5, PHI, 0.0, GAMMA))
    print(f"Comprobación a mano (s = 1,8, H = 4,5, c = 0): B_f = 0,6 + 2·1,8 = 4,2 m; bloque = ½·{Kp:.2f}·18·4,5²·4,2 = {0.5 * Kp * GAMMA * 4.5 ** 2 * 4.2:.0f} kN ({r.H_block_kN:.0f}); "
          f"individual = ½·K_p·γ·H²·D = {0.5 * Kp * GAMMA * 4.5 ** 2 * D:.0f} kN × 9 × p_m = {r.p_multiplier_avg:.3f} → {r.H_individual_kN:.0f} kN")
    print("El bloque crece con la anchura del grupo (B_f) y los individuales con el número de pilotes y el empotramiento: la cohesión favorece más a los pilotes (9·c·D·H) que al bloque. "
          "El modelo es el de anteproyecto de Mokwa-Duncan; con encepado flexible o pilotes largos hace falta un análisis p-y completo.")


if __name__ == "__main__":
    main()
