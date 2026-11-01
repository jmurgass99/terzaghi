"""Factores de capacidad portante N_q, N_c y N_γ para φ' = 20–40° según el autor de N_γ (Brinch Hansen, Meyerhof, Vesić, Chen/EC7) y la errata de la ficha W00675.

N_q = e^(π·tan φ)·tan²(45° + φ/2) y N_c = (N_q − 1)·cot φ son comunes a todos los autores
(Reissner-Prandtl); N_γ no: Brinch Hansen 1,5·(N_q − 1)·tan φ, Meyerhof (N_q − 1)·tan(1,4φ),
Vesić 2·(N_q + 1)·tan φ y Chen/EN 1997-1 Anexo D 2·(N_q − 1)·tan φ. La tabla se contrasta con
los valores publicados (Das, 2 decimales) y se muestra la errata de la ficha W00675: rotula su
tabla «Hansen, EN 1997-1 Annex D» pero los N_γ impresos (30,22 a 32°) son los de Vesić.

Ejecutar:  python examples/bearing_capacity_factors_ngamma_authors_table_phi_20_to_40_and_w00675_errata.py
"""
import math

from terzaghi._foundation.bearing_capacity import BearingCapacityFormula, bearing_capacity_factors

PUBLICADO_DAS = {20: (6.40, 14.83, 5.39, 2.87, 2.95), 30: (18.40, 30.14, 22.40, 15.67, 15.07), 40: (64.20, 75.31, 109.41, 93.69, 79.54)}  # Nq, Nc, Nγ Vesić, Meyerhof, Hansen
W00675 = {25: 10.88, 28: 16.72, 30: 22.40, 32: 30.22, 35: 48.03}  # N_γ impresos, rotulados «Hansen / Annex D»


def main() -> None:
    F = BearingCapacityFormula
    print(f"  {'φ [°]':>5} {'N_q':>8} {'N_c':>8} {'N_γ Hansen':>10} {'N_γ Meyerhof':>12} {'N_γ Vesić':>10} {'N_γ Chen/EC7':>12}")
    for phi in (0, 20, 25, 28, 30, 32, 35, 40):
        Nq, Nc, _ = bearing_capacity_factors(phi, F.CHEN_EC7)
        ng = {f: bearing_capacity_factors(phi, f)[2] for f in F}
        print(f"  {phi:5d} {Nq:8.3f} {Nc:8.3f} {ng[F.BRINCH_HANSEN]:10.2f} {ng[F.MEYERHOF]:12.2f} {ng[F.VESIC]:10.2f} {ng[F.CHEN_EC7]:12.2f}")
    print("\nContraste con la tabla publicada (Das, Principles of Foundation Engineering; 2 decimales):")
    for phi, (Nq_p, Nc_p, Ngv_p, Ngm_p, Ngh_p) in PUBLICADO_DAS.items():
        Nq, Nc, Ngv = bearing_capacity_factors(phi, F.VESIC)
        Ngm = bearing_capacity_factors(phi, F.MEYERHOF)[2]
        Ngh = bearing_capacity_factors(phi, F.BRINCH_HANSEN)[2]
        print(f"  φ = {phi}°: ΔN_q = {Nq - Nq_p:+.3f}, ΔN_c = {Nc - Nc_p:+.3f}, ΔN_γ Vesić = {Ngv - Ngv_p:+.3f}, Meyerhof = {Ngm - Ngm_p:+.3f}, Hansen = {Ngh - Ngh_p:+.3f}")
    print("\nFicha W00675 (tabla rotulada «Hansen, EN 1997-1 Annex D»): N_γ impreso frente a cada autor")
    for phi, ng_f in W00675.items():
        ng = {f: bearing_capacity_factors(phi, f)[2] for f in F}
        mejor = min(F, key=lambda f: abs(ng[f] - ng_f))
        print(f"  φ = {phi}°: impreso {ng_f:6.2f} | Vesić {ng[F.VESIC]:6.2f} | Anexo D {ng[F.CHEN_EC7]:6.2f} | Hansen {ng[F.BRINCH_HANSEN]:6.2f} → coincide con {mejor.value}")
    Nq30 = math.exp(math.pi * math.tan(math.radians(30))) * math.tan(math.radians(60)) ** 2
    print(f"\nComprobación cerrada φ = 30°: N_q = e^(π·tan 30°)·tan²60° = {Nq30:.7f} (tabla 18,40); N_c = (N_q − 1)/tan 30° = {(Nq30 - 1) / math.tan(math.radians(30)):.4f} (tabla 30,14); con φ = 0, N_c = π + 2 = {math.pi + 2:.4f}.")
    print("Elegir el autor de N_γ cambia el término de peso propio hasta un 40 % (Hansen frente a Vesić a 35°); el Anexo D fija el de Chen y los anexos nacionales pueden decir otra cosa.")


if __name__ == "__main__":
    main()
