"""Licuefacción por SPT (Boulanger-Idriss) y muelles de interacción suelo-estructura (Gazetas).

1. Perfil de arena saturada con (N1)60cs conocido: factor de seguridad frente a
   licuefacción a varias profundidades para un sismo de Mw 7,0 y PGA 0,25 g.
2. Zapata 3 x 2 m sobre suelo con V_s = 180 m/s: rigideces estáticas de
   Gazetas (vertical, horizontal, rotación) para modelar el apoyo.

Ejecutar:  python examples/03_liquefaction_and_ssi_springs.py
"""
from dataclasses import asdict

from terzaghi.gazetas_springs import GazetasInput, evaluate_gazetas
from terzaghi.liquefaction import LiquefactionInput, evaluate_liquefaction

GAMMA, GAMMA_W = 19.0, 9.81


def main() -> None:
    print("Licuefacción (Mw = 7,0, a_max = 0,25 g, nivel freático en superficie, FS umbral 1,2):")
    print(f"  {'z [m]':>5} {'σ_v':>7} {'σ_v\'':>7} {'(N1)60cs':>9} | resultado")
    for z, n160 in ((2.0, 8), (4.0, 12), (6.0, 15), (8.0, 20), (10.0, 28)):
        sv = GAMMA * z
        sve = sv - GAMMA_W * z
        r = evaluate_liquefaction(LiquefactionInput(depth_m=z, sigma_v_kPa=sv, sigma_v_eff_kPa=sve,
                                                    N1_60_cs=n160, a_max_g=0.25, Mw=7.0))
        nums = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in asdict(r).items()}
        print(f"  {z:5.1f} {sv:7.1f} {sve:7.1f} {n160:9d} | {nums}")

    print("\nMuelles de Gazetas para zapata 3,0 x 2,0 m, V_s = 180 m/s, ν = 0,35:")
    g = evaluate_gazetas(GazetasInput(L_m=3.0, B_m=2.0, Vs_m_per_s=180.0, nu_soil=0.35))
    for k, v in asdict(g).items():
        print(f"  {k:<22} {v if not isinstance(v, float) else f'{v:,.0f}'}")


if __name__ == "__main__":
    main()
