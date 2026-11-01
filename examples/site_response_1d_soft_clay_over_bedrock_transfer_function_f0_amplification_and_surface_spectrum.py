"""Respuesta de sitio 1D (ondas SH, lineal equivalente): estrato blando sobre roca, función de transferencia, f₀ = V_s/4H, amplificación y espectro en superficie.

Estrato de 30 m con V_s = 200 m/s y ξ = 5 % sobre roca (V_s = 1500 m/s). La función de transferencia
roca-superficie es |H(f)| = 1/|cos(ωH/V_s*)| con V_s* = V_s(1 + iξ): resonancia en f₀ = V_s/(4H) = 1,67 Hz
con |H| ≈ 2/(πξ) = 12,7. Se propaga un ruido blanco filtrado (20 s, dt = 0,01) y un seno en f₀, se
compara la frecuencia pico con la teórica y se da el espectro de respuesta en superficie. Después un
perfil de dos capas (arcilla 10 m V_s 150 sobre arena 20 m V_s 300). El modelo multiplica 1/cos(kh) de
cada capa: exacto para una capa sobre base rígida, aproximado (sin cocientes de impedancia) con varias.

Ejecutar:  python examples/site_response_1d_soft_clay_over_bedrock_transfer_function_f0_amplification_and_surface_spectrum.py
"""
import numpy as np

from terzaghi.site_response import SoilLayer1D, propagate_1d

DT, T_TOT = 0.01, 20.0


def ruido(seed=7):
    rng = np.random.default_rng(seed)
    a = rng.normal(scale=0.5, size=int(T_TOT / DT))
    return np.convolve(a, np.ones(5) / 5, mode="same")


def main() -> None:
    capa = [SoilLayer1D(thickness_m=30.0, Vs_m_s=200.0, density_kg_m3=1900.0, damping_ratio=0.05)]
    f0 = 200.0 / (4 * 30.0)
    print(f"Estrato 30 m, V_s = 200 m/s, ξ = 5 %: f₀ = V_s/(4H) = {f0:.3f} Hz (T₀ = {1 / f0:.2f} s); |H(f₀)| teórico ≈ 2/(πξ) = {2 / (np.pi * 0.05):.1f}\n")
    f = np.linspace(0.05, 8.0, 1600)
    H = 1 / np.cos(2 * np.pi * f * 30.0 / (200.0 * (1 + 0.05j)))
    i0 = int(np.argmax(np.abs(H)))
    print(f"Función de transferencia evaluada a mano: pico |H| = {abs(H[i0]):.2f} en f = {f[i0]:.3f} Hz; |H| en 3·f₀ = {abs(H[int(np.argmin(abs(f - 3 * f0)))]):.2f}, en 5·f₀ = {abs(H[int(np.argmin(abs(f - 5 * f0)))]):.2f}; |H(0,5 Hz)| = {abs(H[int(np.argmin(abs(f - 0.5)))]):.2f}")
    a_in = ruido()
    r = propagate_1d(a_in, DT, capa)
    print(f"\nRuido blanco filtrado (PGA roca {np.max(np.abs(a_in)):.2f} m/s²): PGA superficie {np.max(np.abs(r.surface_accel)):.2f} m/s², amplificación {r.amplification_factor:.2f}, f_pico = {r.peak_freq_Hz:.3f} Hz ({(r.peak_freq_Hz / f0 - 1) * 100:+.1f} % frente a f₀), γ_máx ≈ {r.gamma_max_profile[0] * 100:.3f} %")
    t = np.arange(0, T_TOT, DT)
    r_sin = propagate_1d(0.5 * np.sin(2 * np.pi * f0 * t), DT, capa)
    print(f"Seno en f₀ (0,5 m/s²): amplificación {r_sin.amplification_factor:.2f}, la cota 2/(πξ) de la capa sobre base rígida; con ruido de banda ancha la amplificación de la PGA es mucho menor (1,8) porque solo la banda en torno a f₀ se amplifica")
    print("\nEspectro de respuesta en superficie (ξ = 5 %) del caso de ruido:")
    print("  " + " ".join(f"T={T:.2f}s" for T in (0.1, 0.2, 0.3, 0.5, 0.6, 0.8, 1.0, 2.0)))
    print("  " + " ".join(f"{np.interp(T, r.response_spectrum_T, r.response_spectrum_Sa):6.3f}g" for T in (0.1, 0.2, 0.3, 0.5, 0.6, 0.8, 1.0, 2.0)))
    perfil2 = [SoilLayer1D(10.0, 150.0, 1700.0, 0.07), SoilLayer1D(20.0, 300.0, 2000.0, 0.04)]
    r2 = propagate_1d(a_in, DT, perfil2)
    Hs = sum(h.thickness_m / h.Vs_m_s for h in perfil2)
    print(f"\nDos capas (arcilla 10 m V_s 150 + arena 20 m V_s 300): f_pico = {r2.peak_freq_Hz:.3f} Hz frente a 1/(4·ΣH/V_s) = {1 / (4 * Hs):.3f} Hz; amplificación {r2.amplification_factor:.2f}; γ_máx por capa {np.round(r2.gamma_max_profile * 100, 3).tolist()} %")
    print("\nEl producto de 1/cos(k·h) por capa es exacto para la capa única sobre base rígida, pero con dos capas el pico sale al doble del periodo esperado del perfil y la amplificación se dispara: faltan los cocientes de impedancia entre capas (Kramer cap. 7). "
          "Para un estudio de sitio multicapa hace falta la matriz de transferencia completa o un análisis no lineal con degradación G/G_máx; aquí la capa única es lo que se puede usar.")


if __name__ == "__main__":
    main()
