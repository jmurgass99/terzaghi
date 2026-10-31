"""Capacidad portante de una zapata por cuatro métodos y valor de diseño según EC7.

Zapata 2,0 x 3,0 m a 1,5 m de profundidad en arena (φ' = 32°, c' = 0) y en
arcilla drenada (φ' = 24°, c' = 15 kPa). Se comparan los factores N_c, N_q, N_γ
y la capacidad última de Terzaghi, Meyerhof, Vesic y Brinch Hansen, y después
se obtiene la resistencia de diseño con la vía EN 1997-1 (factores parciales
γ_φ y γ_Rv del enfoque de diseño elegido, aquí DA2: γ_Rv = 1,4).

Ejecutar:  python examples/01_bearing_capacity_methods.py
"""
from dataclasses import asdict

from terzaghi.bearing_capacity import BearingCapacityInput, evaluate_bearing, evaluate_bearing_ec7

CASES = {
    "arena densa (φ' = 32°, c' = 0)": dict(phi_deg=32.0, c_kPa=0.0, gamma_kN_m3=19.0),
    "arcilla drenada (φ' = 24°, c' = 15 kPa)": dict(phi_deg=24.0, c_kPa=15.0, gamma_kN_m3=18.0),
}
GEOM = dict(B_m=2.0, L_m=3.0, D_f_m=1.5)


def main() -> None:
    for title, soil in CASES.items():
        print(f"{title}, zapata 2,0 x 3,0 m, D_f = 1,5 m")
        print(f"  {'método':<14} {'N_c':>7} {'N_q':>7} {'N_γ':>7} {'q_ult [kPa]':>12} {'q_adm [kPa]':>12}")
        for method in ("terzaghi", "meyerhof", "vesic", "brinch_hansen"):
            r = evaluate_bearing(BearingCapacityInput(method=method, **GEOM, **soil), code="EU")
            print(f"  {method:<14} {r.Nc:7.2f} {r.Nq:7.2f} {r.Ngamma:7.2f} {r.q_ult_kPa:12.0f} {r.q_adm_kPa:12.0f}")

        ec7 = evaluate_bearing_ec7(**GEOM, **soil, gamma_Rv=1.4, gamma_phi=1.0, formula="chen_ec7")
        print("  EN 1997-1 (DA2, γ_Rv = 1,4):")
        data = ec7.model_dump() if hasattr(ec7, "model_dump") else (asdict(ec7) if hasattr(ec7, "__dataclass_fields__") else dict(vars(ec7)))
        for k, v in data.items():
            if isinstance(v, (int, float, str, bool)):
                print(f"    {k:<26} {round(v, 2) if isinstance(v, float) else v}")
        print()


if __name__ == "__main__":
    main()
