"""Zapata sobre arena seca (EN 1997-1 Anexo D, ejemplo publicado W00675 §4.3 DA1-C1): los nueve valores intermedios y lo que da la vía deprecada.

Zapata 2,5 × 1,5 m a 0,5 m de profundidad, φ'_d = 35°, c' = 0, γ = 18 kN/m³, γ_R;v = 1,0. El
ejemplo resuelto publica N_q, N_c, N_γ, s_q, s_c, s_γ y los tres términos de q_ult (402,8 + 0 +
500,7 = 903,5 kPa). `evaluate_bearing_ec7` (puerta en metros hacia la ecuación del Anexo D con
N_γ = 2·(N_q − 1)·tan φ) los reproduce todos; la vía deprecada `evaluate_bearing` (factores de
forma 1 ± 0,1·B/L y 1 + 0,2·B/L, sin publicar) se desvía +2,6 % con Vesić y −17 % con Brinch
Hansen, y avisa con `DeprecationWarning`.

Ejecutar:  python examples/bearing_ec7_annex_d_pad_footing_w00675_nine_published_values_vs_deprecated_path.py
"""
import warnings

from terzaghi.bearing_capacity import BearingCapacityInput, evaluate_bearing, evaluate_bearing_ec7

DATOS = dict(B_m=1.5, L_m=2.5, D_f_m=0.5, phi_deg=35.0, c_kPa=0.0, gamma_kN_m3=18.0)
PUBLICADO = dict(Nq=33.3, Nc=46.1, Ngamma=45.2, sq=1.34, sc=1.35, sgamma=0.82,
                 q_ult_overburden=402.8, q_ult_cohesion=0.0, q_ult_self_weight=500.7, q_ult=903.5)


def main() -> None:
    r = evaluate_bearing_ec7(**DATOS)
    print("W00675 §4.3 DA1-C1 — zapata 2,5 × 1,5 m, d = 0,5 m, φ'_d = 35°, c' = 0, γ = 18 kN/m³, γ_R;v = 1,0\n")
    print(f"  {'magnitud':18} {'publicado':>10} {'terzaghi':>10} {'desvío':>8}")
    for k, pub in PUBLICADO.items():
        val = getattr(r, k)
        dev = f"{(val - pub) / pub * 100:+.3f} %" if pub else f"{val:+.1f}"
        print(f"  {k:18} {pub:10.2f} {val:10.3f} {dev:>8}")
    print(f"\n  B' = {r.B_eff:.2f} m, L' = {r.L_eff:.2f} m, A' = {r.A_eff:.3f} m²; R_k = q_ult·A' = {r.R_k:.1f} kN; R_d = R_k/γ_R;v = {r.R_d:.1f} kN "
          f"(fórmula {r.formula.value}, {r.drainage.value})")
    print("\nVía deprecada `evaluate_bearing` sobre los mismos datos (factores de forma sin publicar, ciega a e y H):")
    for method in ("vesic", "meyerhof", "brinch_hansen"):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            leg = evaluate_bearing(BearingCapacityInput(**DATOS, method=method), code="EU")
        aviso = "DeprecationWarning" if any(issubclass(x.category, DeprecationWarning) for x in w) else "sin aviso"
        print(f"  {method:14} q_ult = {leg.q_ult_kPa:8.2f} kPa ({(leg.q_ult_kPa / PUBLICADO['q_ult'] - 1) * 100:+6.2f} % frente a 903,5); N_γ = {leg.Ngamma:6.2f}; q_adm (γ_R;v = 1,4) = {leg.q_adm_kPa:7.1f} kPa  [{aviso}]")
    print("\nEl Anexo D usa N_γ = 2·(N_q − 1)·tan φ (Chen); Vesić da 2·(N_q + 1)·tan φ y Brinch Hansen 1,5·(N_q − 1)·tan φ: con φ = 35° son 45,2 / 48,0 / 33,9. "
          "La vía deprecada se conserva con sus números intactos para no romper llamadores; la puerta EC7 es la que hay que usar.")


if __name__ == "__main__":
    main()
