"""Empujes de Rankine sobre un muro en voladizo de 9,65 m con dos estratos, sobrecarga uniforme y lineal (fichas W00664/W00677): descomposición de 268 kN/m y fuerza deslizante DA2 de 367 kN/m.

SOIL1 γ = 19,5, φ' = 30° (6 m) sobre SOIL2 γ = 20, φ' = 32° (2,65 m); q = 10 kPa uniforme y una carga
lineal S = 10 kN/m a 1,5 m del muro. K_a = tan²(45 − φ/2) (1/3 exacto a 30°); los empujes por estrato
(triangular propio, rectangular del estrato superior, sobrecargas) suman 267,99 kN/m y la fuerza
deslizante de diseño DA2 (γ_G = 1,35 permanentes, γ_Q = 1,5 variables) 366,9 kN/m (ficha 366,58 con K_a
truncado). También K_0 de Jaky con OCR y la errata de la ficha (q = 200 kPa es la presión admisible, no la
sobrecarga).

Ejecutar:  python examples/earth_pressure_rankine_multilayer_cantilever_wall_w00664_thrusts_and_da2_sliding_force.py
"""
from terzaghi._foundation.soil import SoilLayer, SoilType
from terzaghi.gabion_wall import DESIGN_APPROACHES, Ka_rankine, Kp_rankine

G1, PHI1, H1 = 19.5, 30.0, 6.0
G2, PHI2, H2 = 20.0, 32.0, 2.65
Q, S, A = 10.0, 10.0, 1.5
H_TOT = 9.65


def main() -> None:
    Ka1, Ka2 = Ka_rankine(PHI1), Ka_rankine(PHI2)
    print(f"K_a1 = tan²(45 − 15) = {Ka1:.5f} (= 1/3), K_a2 = tan²(29°) = {Ka2:.5f}; K_p1 = {Kp_rankine(PHI1):.3f} = 1/K_a1\n")
    filas = [("E_a1 = ½·K_a1·γ1·H1²  (triangular SOIL1)", 0.5 * Ka1 * G1 * H1 ** 2, H2 + H1 / 3, "G"),
             ("E_a2 = ½·K_a2·γ2·H2²  (triangular SOIL2)", 0.5 * Ka2 * G2 * H2 ** 2, H2 / 3, "G"),
             ("E_2' = K_a2·γ1·H1·H2  (rectangular, peso de SOIL1 sobre SOIL2)", Ka2 * G1 * H1 * H2, H2 / 2, "G"),
             ("E_S1 = K_a1·q·H1", Ka1 * Q * H1, H2 + H1 / 2, "Q"), ("E_S2 = K_a2·q·H2", Ka2 * Q * H2, H2 / 2, "Q"),
             ("E_s = 0,6·S (carga lineal, H ≥ 3a)", 0.6 * S, H_TOT - 1.17 * A - 1.0, "Q")]
    print(f"  {'componente':62} {'E [kN/m]':>8} {'brazo sobre base muro [m]':>25} {'tipo':>4}")
    for nombre, E, z, tipo in filas:
        print(f"  {nombre:62} {E:8.2f} {z:25.2f} {tipo:>4}")
    total = sum(E for _, E, _, _ in filas)
    perm = sum(E for _, E, _, t in filas if t == "G")
    var = total - perm
    print(f"  {'Σ':62} {total:8.2f}   (ficha W00664: 267,75 con K_a1 = 0,333)")
    gf = DESIGN_APPROACHES["DA2"]
    print(f"\nFuerza deslizante de diseño DA2: γ_G·E_perm + γ_Q·E_var = {gf['gG']}·{perm:.2f} + {gf['gQ']}·{var:.2f} = {gf['gG'] * perm + gf['gQ'] * var:.2f} kN/m (ficha W00677: 366,58)")
    print(f"Brazo de la carga lineal: H_total − 1,17·a = {H_TOT - 1.17 * A:.3f} m desde la base de la zapata (ficha 7,90)")
    print("\nErrata documentada: la ficha declara «q_k = 200 kPa»; con ese valor E_S1 = K_a·q·H1 = 400 kN/m, más que todo el empuje del suelo. Sus propios 19,98 y 8,14 kN/m solo salen con q = 10 kPa: los 200 kPa son la presión admisible del terreno (q_Rd = 200/1,4 = 142,9 kPa en su comprobación de hundimiento).")
    print("\nCoeficiente en reposo de Jaky con sobreconsolidación (K_0 = (1 − sin φ')·OCR^sin φ') para SOIL1:")
    for ocr in (1.0, 2.0, 4.0):
        capa = SoilLayer(thickness=H1, soil_type=SoilType.COHESIONLESS, friction_angle=PHI1, unit_weight=G1, OCR=ocr)
        print(f"  OCR = {ocr:.0f}: K_0 = {capa.K0():.3f}  (K_a = {capa.Ka_rankine():.3f}, K_p = {capa.Kp_rankine():.3f})")
    print("Un muro de sótano que no puede desplazarse recibe K_0 (hasta 1,5·K_a si OCR = 4), no K_a: Rankine activo exige que el muro ceda.")


if __name__ == "__main__":
    main()
