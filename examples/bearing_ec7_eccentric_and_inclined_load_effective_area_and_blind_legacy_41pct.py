"""Zapata cuadrada con carga excéntrica e inclinada (EN 1997-1 Anexo D): área efectiva de Meyerhof, factores i_q/i_c/i_γ y los 41 % que se pierde la vía deprecada.

Zapata 2,5 × 2,5 m a 1,5 m en arena φ' = 32°, γ = 19 kN/m³. Cuatro estados: centrada y vertical
(S1), excéntrica e_B = 0,30 m (S3), inclinada H/V = 150/1000 kN (S4) y ambas (S5). La ecuación
del Anexo D recorta la base a B' = B − 2e y multiplica por i_q = (1 − H/(V + A'c'cot φ))^m con
m = (2 + B'/L')/(1 + B'/L'); la vía deprecada no tiene esos parámetros y devuelve el mismo número
en los cuatro casos: en S5 queda un 41 % por encima, del lado inseguro. Con H > 0 y V ≤ 0 la
puerta se niega a calcular (gobierna el deslizamiento, no el hundimiento).

Ejecutar:  python examples/bearing_ec7_eccentric_and_inclined_load_effective_area_and_blind_legacy_41pct.py
"""
import warnings

from terzaghi.bearing_capacity import BearingCapacityInput, evaluate_bearing, evaluate_bearing_ec7

BASE = dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0, gamma_kN_m3=19.0)
CASOS = [("S1 centrada, vertical", {}), ("S3 e_B = 0,30 m", dict(e_B_m=0.30)),
         ("S4 H/V = 150/1000 kN", dict(H_kN=150.0, V_kN=1000.0)),
         ("S5 e_B = 0,30 m + H/V", dict(e_B_m=0.30, H_kN=150.0, V_kN=1000.0)),
         ("S5b e_B = e_L = 0,30 m + H/V", dict(e_B_m=0.30, e_L_m=0.30, H_kN=150.0, V_kN=1000.0))]


def main() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        legacy = evaluate_bearing(BearingCapacityInput(**BASE, method="vesic"), code="EU").q_ult_kPa
    print("Zapata 2,5 × 2,5 m, D_f = 1,5 m, arena φ' = 32°, γ = 19 kN/m³ (EN 1997-1 Anexo D, N_γ de Chen):\n")
    print(f"  {'caso':30} {'B′ [m]':>6} {'L′ [m]':>6} {'A′ [m²]':>7} {'i_q':>6} {'i_γ':>6} {'q_ult [kPa]':>11} {'R_k [kN]':>9} {'legacy/EC7':>10}")
    for nombre, extra in CASOS:
        r = evaluate_bearing_ec7(**BASE, **extra)
        print(f"  {nombre:30} {r.B_eff:6.2f} {r.L_eff:6.2f} {r.A_eff:7.3f} {r.iq:6.3f} {r.igamma:6.3f} {r.q_ult:11.2f} {r.R_k:9.0f} {legacy / r.q_ult:10.3f}")
    r5 = evaluate_bearing_ec7(**BASE, e_B_m=0.30, H_kN=150.0, V_kN=1000.0)
    print(f"\n  La vía deprecada devuelve {legacy:.2f} kPa en los cinco casos (no tiene e ni H): en S5 es un {(legacy / r5.q_ult - 1) * 100:.1f} % más que el Anexo D.")
    print(f"  Exponente m para carga paralela a B': m = (2 + B'/L')/(1 + B'/L') = {(2 + r5.B_eff / r5.L_eff) / (1 + r5.B_eff / r5.L_eff):.3f}; i_q = (1 − H/V)^m = {(1 - 150 / 1000) ** ((2 + r5.B_eff / r5.L_eff) / (1 + r5.B_eff / r5.L_eff)):.3f} (c' = 0)")
    try:
        evaluate_bearing_ec7(**BASE, H_kN=150.0, V_kN=0.0)
    except ValueError as exc:
        print(f"\n  H > 0 con V = 0 → ValueError: {str(exc)[:110]}…")
    print("\nCon la excentricidad el área efectiva cae un 24 % y q_ult un 11 %; la inclinación quita otro 25 %: los dos efectos se multiplican y ninguno es despreciable para una zapata de pilar con viento o sismo.")


if __name__ == "__main__":
    main()
