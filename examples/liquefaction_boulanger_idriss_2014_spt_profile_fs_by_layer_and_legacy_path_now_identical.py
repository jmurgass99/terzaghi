"""Licuefacción por SPT (Boulanger e Idriss 2014) en un perfil de arena con nivel freático: CSR, CRR, MSF, K_σ y FS capa a capa, capas sin ensayo declaradas y la vía legacy igualada.

Perfil de arena γ = 18 (seca) / 19,5 kN/m³ (saturada), nivel freático a 1,5 m, (N₁)₆₀cs medidos a seis
profundidades (una sin ensayo), sismo M_w = 7,0 con a_máx = 0,30 g. `evaluate_spt_profile_liquefaction`
calcula σ_v y σ'_v aportados, r_d = exp(α(z) + β(z)·M), CSR = 0,65·(a_máx/g)·(σ_v/σ'_v)·r_d,
CRR_7,5 de la ec. 34, MSF y K_σ, y marca la capa sin N como «NO EVALUADA» en vez de inventar un valor.
La vía simple `evaluate_liquefaction` (y la API) daba hasta la 1.0 un FS un 13–29 % mayor por un r_d sin
senos y un K_σ con raíz en vez de logaritmo; ahora coincide bit a bit.

Ejecutar:  python examples/liquefaction_boulanger_idriss_2014_spt_profile_fs_by_layer_and_legacy_path_now_identical.py
"""
from terzaghi.liquefaction import LiquefactionInput, evaluate_liquefaction, evaluate_spt_profile_liquefaction
from terzaghi.liquefaction.boulanger_idriss import BoulangerIdrissInput, evaluate_bi2014

G_DRY, G_SAT, WT = 18.0, 19.5, 1.5
CAPAS = [(2.0, 9.0), (4.0, 12.0), (6.0, None), (8.0, 16.0), (11.0, 22.0), (15.0, 30.0)]  # (z, (N1)60cs)
A_MAX, MW = 0.30, 7.0


def stresses(z):
    sv = G_DRY * min(z, WT) + G_SAT * max(z - WT, 0.0)
    return sv, sv - 9.81 * max(z - WT, 0.0)


def main() -> None:
    layers = []
    for z, N in CAPAS:
        sv, sve = stresses(z)
        d = {"depth_m": z, "sigma_v_kPa": sv, "sigma_v_eff_kPa": sve}
        if N is not None:
            d["N1_60cs"] = N
        layers.append(d)
    res = evaluate_spt_profile_liquefaction(layers, a_max_g=A_MAX, Mw=MW)
    print(f"M_w = {MW}, a_máx = {A_MAX} g; nivel freático a {WT} m\n  estado: {res.status}\n")
    print(f"  {'z [m]':>5} {'σ_v':>6} {'σ′_v':>6} {'(N₁)₆₀cs':>8} {'r_d':>6} {'CSR':>6} {'CRR₇.₅':>7} {'MSF':>6} {'K_σ':>6} {'FS':>6}  estado")
    for L in res.layers:
        if L["FS"] is None:
            print(f"  {L['depth_m']:5.1f} {L['sigma_v_kPa']:6.1f} {L['sigma_v_eff_kPa']:6.1f} {'—':>8} {'—':>6} {'—':>6} {'—':>7} {'—':>6} {'—':>6} {'—':>6}  {L['status']}")
            continue
        r = evaluate_bi2014(BoulangerIdrissInput(L["depth_m"], L["sigma_v_kPa"], L["sigma_v_eff_kPa"], L["N1_60cs"], A_MAX, MW))
        print(f"  {L['depth_m']:5.1f} {L['sigma_v_kPa']:6.1f} {L['sigma_v_eff_kPa']:6.1f} {L['N1_60cs']:8.0f} {r.rd:6.3f} {L['CSR']:6.3f} {L['CRR']:7.3f} {L['MSF']:6.3f} {L['K_sigma']:6.3f} {L['FS']:6.2f}  {'LICUABLE' if L['is_liquefiable'] else 'no licuable'}")
    print(f"\n  FS mínimo = {res.min_FS:.2f}; estrato licuable: {res.has_liquefiable_stratum}; capas sin evaluar: {res.n_layers_not_evaluated}")
    print("\nVía simple `evaluate_liquefaction` (la que usa /api/geo/liquefaction) frente a `evaluate_bi2014`, mismas capas:")
    print(f"  {'z [m]':>5} {'FS legacy':>9} {'FS B&I':>7} {'diferencia':>10}   (hasta la 1.0: +13 % a 5 m, +29 % a 10 m)")
    for z, N in CAPAS:
        if N is None:
            continue
        sv, sve = stresses(z)
        a = evaluate_liquefaction(LiquefactionInput(z, sv, sve, N, A_MAX, MW))
        b = evaluate_bi2014(BoulangerIdrissInput(z, sv, sve, N, A_MAX, MW))
        print(f"  {z:5.1f} {a.FS:9.4f} {b.FS:7.4f} {a.FS - b.FS:10.1e}")
    print("\nLas cuatro capas evaluadas hasta 11 m licúan (FS 0,53–0,85) y solo la arena densa de 15 m queda a salvo; la de 6 m no se evalúa porque no trae N, y el informe lo dice en vez de rellenar 15. "
          "`is_safe` de la vía simple exige FS ≥ 1,2 (margen de proyecto); `is_liquefiable` del módulo B&I compara con 1,0.")


if __name__ == "__main__":
    main()
