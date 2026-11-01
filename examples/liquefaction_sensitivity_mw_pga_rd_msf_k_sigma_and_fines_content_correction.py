"""Sensibilidad del factor de seguridad frente a licuefacción: magnitud (MSF), PGA, profundidad (r_d y K_σ) y contenido de finos ((N₁)₆₀ → (N₁)₆₀cs).

Arena a 6 m con σ_v = 110 y σ'_v = 66 kPa y (N₁)₆₀ = 14. MSF = 1 + (MSF_máx − 1)·(8,64·e^(−M/4) − 1,325) vale
1 en M = 7,5 y hasta 1,4 en M = 6; K_σ = 1 − C_σ·ln(σ'_v/P_a) ≤ 1,1 favorece las capas someras; r_d baja
con z. La corrección por finos de Boulanger e Idriss, Δ(N₁)₆₀ = exp(1,63 + 9,7/(FC + 0,01) − (15,7/(FC + 0,01))²),
convierte 14 golpes en 19,6 con 35 % de finos y cambia el veredicto.

Ejecutar:  python examples/liquefaction_sensitivity_mw_pga_rd_msf_k_sigma_and_fines_content_correction.py
"""
import math

from terzaghi.liquefaction.boulanger_idriss import BoulangerIdrissInput, _crr_m75, _k_sigma_bi2014, _msf_bi2014, _rd_bi2014, evaluate_bi2014

Z, SV, SVE, N = 6.0, 110.0, 66.0, 14.0


def delta_n_fines(FC_pct: float) -> float:
    """Boulanger & Idriss (2014) ec. 2.23: incremento de (N₁)₆₀ por contenido de finos FC [%]."""
    f = FC_pct + 0.01
    return math.exp(1.63 + 9.7 / f - (15.7 / f) ** 2)


def main() -> None:
    print(f"Capa de referencia: z = {Z} m, σ_v = {SV}, σ'_v = {SVE} kPa, (N₁)₆₀cs = {N:.0f}\n")
    print(f"  {'M_w':>4} " + " ".join(f"a = {a:.2f} g" for a in (0.15, 0.20, 0.30, 0.40)) + f"   {'MSF':>6}")
    for M in (5.5, 6.0, 6.5, 7.0, 7.5, 8.0):
        fss = [evaluate_bi2014(BoulangerIdrissInput(Z, SV, SVE, N, a, M)).FS for a in (0.15, 0.20, 0.30, 0.40)]
        print(f"  {M:4.1f} " + " ".join(f"{fs:10.2f}" for fs in fss) + f"   {_msf_bi2014(M, N):6.3f}")
    print("  FS escala con 1/a_máx y con MSF: un M 6 y 0,3 g equivale en demanda a un M 7,5 y 0,26 g (0,3/1,173).\n")
    print(f"  {'z [m]':>5} {'σ′_v [kPa]':>10} {'r_d':>6} {'K_σ':>6} {'CSR (0,3 g, M 7)':>16} {'FS':>6}")
    for z in (2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0):
        sve = 18 * 1.5 + (19.5 - 9.81) * (z - 1.5)
        sv = 18 * 1.5 + 19.5 * (z - 1.5)
        r = evaluate_bi2014(BoulangerIdrissInput(z, sv, sve, N, 0.30, 7.0))
        print(f"  {z:5.1f} {sve:10.1f} {r.rd:6.3f} {r.K_sigma:6.3f} {r.CSR:16.3f} {r.FS:6.2f}")
    print("  Con el mismo N, la capa somera tiene K_σ > 1 y σ_v/σ'_v alto (CSR alto); en profundidad r_d y K_σ bajan y CSR también: el FS mínimo suele caer entre 4 y 10 m.\n")
    print(f"  {'FC [%]':>6} {'Δ(N₁)₆₀':>8} {'(N₁)₆₀cs':>8} {'CRR₇.₅':>7} {'FS (0,3 g, M 7)':>15}")
    for FC in (0.0, 5.0, 15.0, 25.0, 35.0, 50.0):
        dN = delta_n_fines(FC)
        r = evaluate_bi2014(BoulangerIdrissInput(Z, SV, SVE, N + dN, 0.30, 7.0))
        print(f"  {FC:6.0f} {dN:8.2f} {N + dN:8.2f} {_crr_m75(N + dN):7.3f} {r.FS:15.2f}")
    print(f"\n  Comprobaciones cerradas: MSF(7,5) = {_msf_bi2014(7.5, N):.5f}; K_σ(100 kPa) = {_k_sigma_bi2014(100.0, N):.5f}; r_d(6 m, 7,5) = {_rd_bi2014(6.0, 7.5):.4f}; CRR(20) = {_crr_m75(20.0):.4f} (paper 0,2059)")
    print("La corrección por finos sube el FS un 40 % (de 0,54 a 0,76 con 35 % de finos) y satura a partir del 35 %: el contenido de finos de laboratorio vale tanto como el golpeo. La curva CRR satura en (N₁)₆₀cs = 37 (el paper dice 37,5).")


if __name__ == "__main__":
    main()
