"""Pilote hincado en arcilla blanda sobre arena: capacidad axial por los métodos α (API RP 2A) y β, reparto por capas y barrido de longitud.

Pilote de 0,6 m con nivel freático a 2 m en tres capas: arcilla blanda 0–8 m (S_u = 30 kPa, γ = 17),
arcilla media 8–14 m (S_u = 60 kPa, γ = 18) y arena densa 14–30 m (φ' = 34°, γ = 19). Fuste: f_s = α·S_u
con α = 0,5·ψ^−0,5 (ψ = S_u/σ'_v ≤ 1) ó 0,5·ψ^−0,25, acotado a 1; en arena f_s = K·tan δ·σ'_v con
K = 1 − sin φ y δ = 0,8·φ. Punta: 9·S_u en arcilla o N_q·σ'_v (N_q ≤ 120) en arena. Se recorre la
longitud 10, 14, 16, 18, 22 y 26 m para ver el salto al empotrar la punta en la arena y cuánto
aporta cada capa.

Ejecutar:  python examples/pile_axial_alpha_beta_api_rp2a_layered_clay_over_sand_per_layer_and_length_sweep.py
"""
import math

from terzaghi.piles.axial_capacity import Pile, SoilLayer, _sigma_v_eff, api_alpha, axial_capacity

LAYERS = [SoilLayer(0.0, 8.0, "clay", gamma_kN_m3=17.0, Su_kPa=30.0), SoilLayer(8.0, 14.0, "clay", gamma_kN_m3=18.0, Su_kPa=60.0),
          SoilLayer(14.0, 30.0, "sand", gamma_kN_m3=19.0, phi_deg=34.0)]
D, WT, FS = 0.6, 2.0, 2.5


def main() -> None:
    print(f"Pilote D = {D} m, nivel freático a {WT} m, FS = {FS}; capas: arcilla blanda 0–8 (S_u 30), arcilla media 8–14 (S_u 60), arena densa 14–30 (φ' 34°)\n")
    print(f"  {'L [m]':>5} {'capa de punta':>13} {'Q_fuste [kN]':>12} {'Q_punta [kN]':>12} {'Q_ult [kN]':>10} {'Q_adm [kN]':>10} {'fuste por capa [kN]':>28}")
    for L in (10.0, 14.0, 16.0, 18.0, 22.0, 26.0):
        p = Pile(diameter_m=D, length_m=L, water_table_m=WT)
        r = axial_capacity(p, LAYERS, FS=FS)
        base = next((lay for lay in LAYERS if lay.top_m <= L <= lay.bottom_m), LAYERS[-1])
        print(f"  {L:5.1f} {base.kind + f' ({base.top_m:.0f}–{base.bottom_m:.0f} m)':>13} {r.Q_skin_kN:12.0f} {r.Q_base_kN:12.0f} {r.Q_ult_kN:10.0f} {r.Q_allow_kN:10.0f} {str([round(x) for x in r.per_layer_skin_kN]):>28}")
    print("\nDetalle de la adhesión α en la arcilla (σ'_v a media capa, ψ = S_u/σ'_v):")
    for lay in LAYERS[:2]:
        z = 0.5 * (lay.top_m + lay.bottom_m)
        sv = _sigma_v_eff(z, LAYERS, WT)
        a = api_alpha(lay.Su_kPa, sv)
        print(f"  {lay.top_m:.0f}–{lay.bottom_m:.0f} m: σ'_v({z:.0f} m) = {sv:.1f} kPa, ψ = {lay.Su_kPa / sv:.3f}, α = {a:.3f}, f_s = {a * lay.Su_kPa:.1f} kPa")
    sv18 = _sigma_v_eff(18.0, LAYERS, WT)
    K = 1 - math.sin(math.radians(34.0))
    print(f"  Arena a 18 m: σ'_v = {sv18:.1f} kPa; K = 1 − sin 34° = {K:.3f}; δ = 0,8·34° = 27,2°; f_s = K·tan δ·σ'_v = {K * math.tan(math.radians(27.2)) * sv18:.1f} kPa")
    r14 = axial_capacity(Pile(D, 14.0, WT), LAYERS, FS); r16 = axial_capacity(Pile(D, 16.0, WT), LAYERS, FS)
    print(f"\nEmpotrar 2 m en la arena multiplica la punta por {r16.Q_base_kN / r14.Q_base_kN:.1f} (9·S_u = 540 kPa frente a N_q·σ'_v con N_q acotado a 120) y la capacidad total por {r16.Q_ult_kN / r14.Q_ult_kN:.2f}.")
    print("Con FS = 2,5 sobre la suma; en proyecto conviene factores distintos para fuste (más fiable) y punta, y comprobar la hinca con el registro de golpes.")


if __name__ == "__main__":
    main()
