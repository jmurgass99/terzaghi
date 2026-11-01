"""Zapata corrida con nivel freático en la base (W00675 GT2): tensiones del perfil con `SoilProfile`, γ' bajo el agua y q_ult = 822 kPa con N_γ de Vesić.

Zapata corrida B = 2 m a D_f = 1,5 m en arena φ' = 28°, c' = 10 kPa, γ = 18 kN/m³ sobre la base y
γ_sat = 19,8 (γ' = 10) por debajo. La ficha compone q_ult = c·N_c + q·N_q + ½·γ'·B·N_γ = 822,6 kPa
(factores de Vesić; corrida ⇒ factores de forma 1). `SoilProfile` da σ_v, u y σ'_v a cualquier cota
partiendo el estrato en el nivel freático; `drained_bearing_capacity` admite la sobrecarga q = γ·D_f
y el γ' del estrato de apoyo por separado (`overburden_pressure`), que es lo que la puerta
`evaluate_bearing_ec7` no permite: ésta usa un único γ para los dos términos.

Ejecutar:  python examples/bearing_strip_footing_water_table_soil_profile_stresses_w00675_gt2_822kpa.py
"""
from terzaghi._foundation.bearing_capacity import BearingCapacityFormula, bearing_capacity_factors, drained_bearing_capacity
from terzaghi._foundation.geometry import RectangularFoundation
from terzaghi._foundation.soil import SoilLayer, SoilProfile, SoilType

B, DF, PHI, C = 2.0, 1.5, 28.0, 10.0
GAMMA, GAMMA_SAT = 18.0, 19.81


def main() -> None:
    perfil = SoilProfile(layers=[SoilLayer(name="arena", thickness=12.0, soil_type=SoilType.COHESIONLESS, friction_angle=PHI, cohesion=C,
                                           unit_weight=GAMMA, saturated_unit_weight=GAMMA_SAT, OCR=1.0)], water_table_depth=DF)
    print(f"Perfil: arena φ' = {PHI}°, c' = {C} kPa, γ = {GAMMA} / γ_sat = {GAMMA_SAT} kN/m³, nivel freático a {DF} m (base de la zapata)")
    print(f"  {'z [m]':>5} {'σ_v [kPa]':>9} {'u [kPa]':>8} {'σ′_v [kPa]':>10}")
    for z in (0.0, 1.0, 1.5, 2.5, 4.0, 6.0):
        print(f"  {z:5.1f} {perfil.total_stress_at(z):9.2f} {perfil.pore_pressure_at(z):8.2f} {perfil.effective_stress_at(z):10.2f}")
    capa = perfil.layer_at(2.0)
    print(f"  K_0 (Jaky) = 1 − sin φ' = {capa.K0():.3f}; K_a = {capa.Ka_rankine():.3f}; K_p = {capa.Kp_rankine():.3f}\n")
    Nq, Nc, Ng = bearing_capacity_factors(PHI, BearingCapacityFormula.VESIC)
    q = GAMMA * DF
    g_sub = GAMMA_SAT - perfil.gamma_w
    mano = C * Nc + q * Nq + 0.5 * g_sub * B * Ng
    print(f"Factores de Vesić a {PHI}°: N_q = {Nq:.3f}, N_c = {Nc:.3f}, N_γ = {Ng:.3f}")
    print(f"A mano (ficha W00675 GT2): q_ult = {C}·{Nc:.2f} + {q:.0f}·{Nq:.2f} + ½·{g_sub:.2f}·{B}·{Ng:.2f} = {C * Nc:.2f} + {q * Nq:.2f} + {0.5 * g_sub * B * Ng:.2f} = {mano:.1f} kPa (ficha: 822)")
    r = drained_bearing_capacity(RectangularFoundation(length=200_000.0, width=B * 1000, thickness=500.0, embedment_depth=DF * 1000),
                                 SoilLayer(thickness=10.0, friction_angle=PHI, cohesion=C, unit_weight=g_sub),
                                 overburden_pressure=q, formula=BearingCapacityFormula.VESIC)
    print(f"`drained_bearing_capacity` (L = 200 m, γ' en el término de peso, q = γ·D_f aparte): q_ult = {r.q_ult:.1f} kPa; s_q = {r.sq:.4f}, s_c = {r.sc:.4f}, s_γ = {r.sgamma:.4f}")
    r_seco = drained_bearing_capacity(RectangularFoundation(length=200_000.0, width=B * 1000, thickness=500.0, embedment_depth=DF * 1000),
                                      SoilLayer(thickness=10.0, friction_angle=PHI, cohesion=C, unit_weight=GAMMA), formula=BearingCapacityFormula.VESIC)
    print(f"Sin nivel freático (γ = 18 en los dos términos): {r_seco.q_ult:.1f} kPa → el agua en la base quita un {(1 - r.q_ult / r_seco.q_ult) * 100:.0f} % (solo afecta al término de peso propio).")
    r_ec7 = drained_bearing_capacity(RectangularFoundation(length=200_000.0, width=B * 1000, thickness=500.0, embedment_depth=DF * 1000),
                                     SoilLayer(thickness=10.0, friction_angle=PHI, cohesion=C, unit_weight=g_sub), overburden_pressure=q)
    print(f"Con N_γ del Anexo D (Chen, 2·(N_q − 1)·tan φ = {r_ec7.Ngamma:.3f}): {r_ec7.q_ult:.1f} kPa, un {(1 - r_ec7.q_ult / r.q_ult) * 100:.1f} % menos que con Vesić.")
    print("\nLa puerta `evaluate_bearing_ec7` no tiene nivel freático: si hay agua en la base, pásale γ' sabiendo que también lo usará en la sobrecarga (conservador); para separar los dos pesos usa `drained_bearing_capacity` directamente.")


if __name__ == "__main__":
    main()
