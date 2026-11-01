"""Empuje sísmico de Mononobe-Okabe sobre un muro de 6 m (ficha W00704: K_ae = 0,471), Coulomb estático (K_a = 0,298) y auditoría de vuelco, deslizamiento y presiones de contacto.

Arena densa γ = 18 kN/m³, φ = 36°, δ = 20°; valores de diseño EC8 con γ_φ = 1,25: φ_d = 30,2°, δ_d = 16,2°;
k_h = 0,2, k_v = 0,1. Coulomb da K_a = 0,298 y P_a = 96,6 kN/m; Mononobe-Okabe (Coulomb en un campo
rotado ψ = atan(k_h/(1 − k_v)) = 12,5°) da K_ae = 0,471 y la rama con 1 + k_v (W00678, ψ = 10,3°) 0,433,
donde la ficha imprime 0,446 por errata. Después `audit_retaining_wall_safety` comprueba un muro de
gaviones de 6 m y 3,5 m de base con los límites clásicos ASD (vuelco ≥ 2, deslizamiento ≥ 1,5) en
estático y en sísmico.

Ejecutar:  python examples/retaining_wall_mononobe_okabe_w00704_kae_0471_coulomb_ka_and_asd_safety_audit.py
"""
import math

from terzaghi.gabion_wall_safety import active_thrust_coulomb, audit_retaining_wall_safety, mononobe_okabe_seismic_coefficient

GAMMA, H = 18.0, 6.0
PHI_D, DELTA_D = math.degrees(math.atan(math.tan(math.radians(36)) / 1.25)), math.degrees(math.atan(math.tan(math.radians(20)) / 1.25))


def main() -> None:
    Pa = active_thrust_coulomb(GAMMA, H, PHI_D, delta_deg=DELTA_D)
    Ka = 2 * Pa / (GAMMA * H ** 2)
    print(f"φ_d = atan(tan 36°/1,25) = {PHI_D:.2f}°, δ_d = {DELTA_D:.2f}°; Coulomb: K_a = {Ka:.4f} (ficha 0,298), P_a = ½·K_a·γ·H² = {Pa:.1f} kN/m (96,6)\n")
    print(f"  {'k_h':>4} {'k_v':>5} {'ψ [°]':>6} {'K_ae':>6} {'ΔK = K_ae − K_a':>15} {'E_d = ½·K_ae·γ·H²·(1 ∓ k_v) [kN/m]':>34} {'ΔP_ae [kN/m]':>12} {'h_e [m]':>7}")
    for kh, kv in ((0.0, 0.0), (0.1, 0.0), (0.2, 0.0), (0.2, 0.1), (0.2, -0.1), (0.3, 0.0)):
        Kae = mononobe_okabe_seismic_coefficient(PHI_D, kh, kv, delta_deg=DELTA_D)
        psi = math.degrees(math.atan(kh / (1 - kv)))
        Ed = 0.5 * Kae * GAMMA * H ** 2 * (1 - kv)
        dP = Ed - Pa
        he = (Pa * H / 3 + dP * H / 2) / Ed if dP > 0 else H / 3
        print(f"  {kh:4.1f} {kv:5.1f} {psi:6.2f} {Kae:6.4f} {Kae - Ka:15.4f} {Ed:34.1f} {dP:12.1f} {he:7.2f}")
    print("  Convención: ψ = atan(k_h/(1 − k_v)); la fila k_v = −0,1 es la rama «1 + k_v» de la ficha W00678 (K = 0,433; imprime 0,446 por errata, su propio E_d = 154,7 implica 0,434).")
    print("  El incremento sísmico ΔP_ae se aplica a H/2 (EC8 Anexo E) y el estático a H/3: la resultante sube a h_e.\n")
    W, xcg, B = 6.0 * 2.2 * 23.0, 1.6, 3.5
    for caso, kh, kv in (("estático", 0.0, 0.0), ("sísmico k_h = 0,2, k_v = 0,1", 0.2, 0.1)):
        Kae = mononobe_okabe_seismic_coefficient(PHI_D, kh, kv, delta_deg=DELTA_D)
        E = 0.5 * Kae * GAMMA * H ** 2 * (1 - kv)
        Ph, Pv = E * math.cos(math.radians(DELTA_D)), E * math.sin(math.radians(DELTA_D))
        a = audit_retaining_wall_safety(W_wall_kN=W, x_cg_m=xcg, H_m=H, Pa_kN=Ph, Pv_kN=Pv, B_base_m=B, friction_coefficient=0.55, q_allowable_kPa=250.0)
        print(f"Auditoría {caso}: muro W = {W:.0f} kN/m (x_cg = {xcg} m, B = {B} m), P_h = {Ph:.1f}, P_v = {Pv:.1f} kN/m")
        print(f"  vuelco FS = {a['FS_overturning']:.2f} ({'ok' if a['ok_overturning'] else 'NO'} ≥ 2,0); deslizamiento FS = {a['FS_sliding']:.2f} ({'ok' if a['ok_sliding'] else 'NO'} ≥ 1,5); e = {a['eccentricity_m']:.3f} m ({'< B/6' if a['eccentricity_m'] <= B / 6 else '> B/6, base parcialmente despegada'}), q_máx = {a['q_max_kPa']:.0f} kPa ({'ok' if a['ok_bearing'] else 'NO'} ≤ 250) → {a['safety_status']}")
    print("\nEl sismo sube el empuje un 42 % (K_ae/K_a = 1,58 menos el factor 1 − k_v) y eleva la resultante; el muro pasa en estático y se queda sin margen de deslizamiento en sísmico: en EC8 los FS clásicos se sustituyen por factores parciales, pero la lectura es la misma.")


if __name__ == "__main__":
    main()
