"""Vida útil del hormigón de una cimentación: iniciación de la corrosión por cloruros (2ª ley de Fick) según recubrimiento y difusividad, y frente de carbonatación según a/c, cenizas y humedad.

Cloruros: C(x,t) = C₀ + (C_s − C₀)·[1 − erf(x/(2√(Dt)))]; con C_s = 0,8 %, C₀ = 0, D = 10 mm²/año y umbral
0,4 % en peso de cemento, el tiempo hasta despasivar la armadura crece con el cuadrado del
recubrimiento. Carbonatación: d = K_c·√t con K_c = 4·(a/c/0,5)²·(1 + 0,01·%cv)·exp(−((HR − 60)/30)²) mm/√año,
máxima a humedad intermedia. Se tabulan ambos para recubrimientos de 30 a 70 mm.

Ejecutar:  python examples/durability_chloride_fick_time_to_corrosion_cover_sweep_and_carbonation_service_life.py
"""
from terzaghi.durability import ChlorideInput, carbonation_coefficient, carbonation_depth, concentration, time_to_depth, time_to_initiation


def main() -> None:
    base = dict(Cs_pct=0.80, C0_pct=0.0, C_crit_pct=0.40)
    print("Cloruros (ambiente marino, C_s = 0,8 %, C_crit = 0,4 % en peso de cemento): años hasta la iniciación según recubrimiento y difusividad")
    print(f"  {'recubr. [mm]':>12} " + " ".join(f"D = {D:4.1f} mm²/año" for D in (2.0, 5.0, 10.0, 20.0)))
    for c in (30.0, 40.0, 50.0, 60.0, 70.0):
        print(f"  {c:12.0f} " + " ".join(f"{time_to_initiation(ChlorideInput(D_mm2_per_year=D, cover_mm=c, **base)):17.1f}" for D in (2.0, 5.0, 10.0, 20.0)))
    inp = ChlorideInput(D_mm2_per_year=10.0, cover_mm=50.0, **base)
    t = time_to_initiation(inp)
    print(f"\n  Perfil a t = {t:.1f} años (D = 10, recubrimiento 50 mm): C(0) = {concentration(0.0, t, inp):.3f}, C(25 mm) = {concentration(25.0, t, inp):.3f}, C(50 mm) = {concentration(50.0, t, inp):.3f} (= umbral), C(100 mm) = {concentration(100.0, t, inp):.3f} %")
    print(f"  Doblar el recubrimiento multiplica el tiempo por {time_to_initiation(ChlorideInput(D_mm2_per_year=10.0, cover_mm=100.0, **base)) / t:.1f}; con umbral 0,6 % en vez de 0,4 %: {time_to_initiation(ChlorideInput(Cs_pct=0.8, C0_pct=0.0, D_mm2_per_year=10.0, cover_mm=50.0, C_crit_pct=0.6)):.1f} años; con C_crit ≥ C_s: {time_to_initiation(ChlorideInput(Cs_pct=0.8, C0_pct=0.0, D_mm2_per_year=10.0, cover_mm=50.0, C_crit_pct=0.9))}")
    print("\nCarbonatación: K_c [mm/√año] y vida útil hasta un recubrimiento de 30 y 50 mm")
    print(f"  {'a/c':>4} {'% cenizas':>9} {'HR [%]':>6} {'K_c':>6} {'d(50 años) [mm]':>15} {'t(30 mm) [años]':>15} {'t(50 mm) [años]':>15}")
    for wc, fa, rh in ((0.45, 0, 65), (0.55, 0, 65), (0.65, 0, 65), (0.50, 30, 65), (0.50, 0, 40), (0.50, 0, 60), (0.50, 0, 85), (0.50, 0, 95)):
        K = carbonation_coefficient(wc, fa, rh)
        print(f"  {wc:4.2f} {fa:9.0f} {rh:6.0f} {K:6.2f} {carbonation_depth(50.0, K):15.1f} {time_to_depth(30.0, K):15.0f} {time_to_depth(50.0, K):15.0f}")
    print("\nUn hormigón a/c 0,65 carbonata el doble de deprisa que uno a/c 0,45 (K ∝ (a/c)²) y la humedad del 60 % es la peor; saturado (95 %) casi no avanza. "
          "Los coeficientes (K_ref = 4 mm/√año, D en mm²/año) son valores de referencia del modelo, no de un ensayo: para una obra hay que medir D_app y C_s en testigos o usar los de la clase de exposición de EN 206 / fib MC.")


if __name__ == "__main__":
    main()
