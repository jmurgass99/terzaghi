"""De los ensayos de campo a parámetros: corrección del SPT por energía y sobrecarga, φ' de Hatanaka-Uchida, E_s de Bowles, q_c ↔ N y S_u del cono.

Registro de un sondeo con N de campo (martillo al 75 % de energía) y q_c del CPT a cinco profundidades.
N_60 = N·(ER/60); (N_1)_60 = N_60·C_N con C_N = √(100/σ'_v) ≤ 2 (Liao-Whitman); φ' = √(15,4·(N_1)_60) + 20
(Hatanaka y Uchida 1996); E_s = 0,5·N_60 + 7 MPa en arena y 0,4·N_60 + 2 en arcilla (Bowles); q_c ≈ 0,5·N_60
MPa en arena (Robertson y Wride); S_u = (q_c − σ_v)/N_k con N_k = 15.

Ejecutar:  python examples/correlations_spt_cpt_n60_overburden_phi_hatanaka_es_bowles_su_from_qc_field_table.py
"""
from terzaghi.correlations import Es_from_N, N60_corrected, N_from_qc, SoilSample, Su_from_qc, phi_from_N, qc_from_N

GAMMA, WT = 18.5, 2.0
SONDEO = [SoilSample(1.5, N_SPT=8, qc_MPa=3.2), SoilSample(3.0, N_SPT=14, qc_MPa=6.1), SoilSample(6.0, N_SPT=22, qc_MPa=10.5),
          SoilSample(9.0, N_SPT=31, qc_MPa=15.8), SoilSample(12.0, N_SPT=27, qc_MPa=2.4, fs_kPa=60.0)]
TIPO = {1.5: "sand", 3.0: "sand", 6.0: "sand", 9.0: "sand", 12.0: "clay"}


def sigma(z):
    sv = GAMMA * z
    u = 9.81 * max(z - WT, 0.0)
    return sv, sv - u


def main() -> None:
    print(f"Sondeo: γ = {GAMMA} kN/m³, nivel freático a {WT} m, martillo con ER = 75 %\n")
    print(f"  {'z [m]':>5} {'suelo':>5} {'N campo':>7} {'σ′_v [kPa]':>10} {'N_60':>6} {'C_N':>5} {'(N_1)_60':>8} {'φ′ [°]':>7} {'E_s [MPa]':>9} {'q_c CPT [MPa]':>13} {'q_c de N [MPa]':>14} {'N de q_c':>8} {'S_u [kPa]':>9}")
    for s in SONDEO:
        sv, sve = sigma(s.depth_m)
        tipo = TIPO[s.depth_m]
        N60 = N60_corrected(s.N_SPT, energy_ratio=0.75)
        N160 = N60_corrected(s.N_SPT, energy_ratio=0.75, overburden_kPa=sve)
        CN = N160 / N60
        phi = phi_from_N(N160) if tipo == "sand" else float("nan")
        su = Su_from_qc(s.qc_MPa, sigma_v_kPa=sv) if tipo == "clay" else float("nan")
        print(f"  {s.depth_m:5.1f} {tipo:>5} {s.N_SPT:7d} {sve:10.1f} {N60:6.1f} {CN:5.2f} {N160:8.1f} {phi:7.1f} {Es_from_N(N60, tipo):9.1f} {s.qc_MPa:13.1f} {qc_from_N(N60, tipo):14.1f} {N_from_qc(s.qc_MPa, tipo):8.1f} {su:9.1f}")
    print("\n  C_N = √(100/σ'_v) acotado a 2: a 1,5 m (σ'_v = 28 kPa) multiplica N por 1,9; a 12 m lo divide. φ' de Hatanaka-Uchida solo vale en arenas; en la arcilla de 12 m el dato útil es S_u del cono (N_k = 15 es un valor medio, 10–20 según la arcilla).")
    print("  q_c ≈ 0,5·N_60 en arena es una correlación de orden de magnitud (k varía 0,3–0,7 con el tamaño de grano): aquí el CPT real queda en 0,32–0,41·N_60, por debajo del 0,5 de la correlación (arena fina o limosa), y en la arcilla la relación no aplica.")
    print("\nEstas correlaciones sirven para el anteproyecto y para contrastar un ensayo con otro; los parámetros de proyecto salen del laboratorio o de ensayos in situ interpretados con su propia sobrecarga.")


if __name__ == "__main__":
    main()
