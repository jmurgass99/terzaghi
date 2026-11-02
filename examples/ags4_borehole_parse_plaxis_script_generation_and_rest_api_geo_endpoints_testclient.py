"""Datos y servicios: un fichero AGS4 con dos sondeos se convierte en estratigrafía y en un guion de PLAXIS 2D, y la API REST se consulta sin servidor con TestClient.

AGS4 (grupos PROJ, LOCA, GEOL, ISPT) → `Ags4Project` con sondeos, estratos clasificados arena/arcilla y SPT;
`generate_plaxis_python_script` escribe el guion de Remote Scripting (materiales Mohr-Coulomb, sondeos,
capas, malla). Después la API: /api/geo/health, /gazetas-springs, /liquefaction, /py/matlock, /tunnel-winkler,
/pile-group/lateral (y su 400) y /bearing-capacity, que todavía sirve la vía deprecada.

Ejecutar:  python examples/ags4_borehole_parse_plaxis_script_generation_and_rest_api_geo_endpoints_testclient.py
"""
import warnings

from terzaghi import generate_plaxis_python_script, parse_ags4_text

AGS = '''
"GROUP","PROJ"
"HEADING","PROJ_ID","PROJ_NAME"
"DATA","GEO-2026-014","Paso inferior Avenida del Puerto"

"GROUP","LOCA"
"HEADING","LOCA_ID","LOCA_NATE","LOCA_NATN","LOCA_GL","LOCA_FEND"
"DATA","S-1","431250.0","4582100.0","4.2","20.0"
"DATA","S-2","431310.0","4582140.0","4.0","18.0"

"GROUP","GEOL"
"HEADING","LOCA_ID","GEOL_TOP","GEOL_BASE","GEOL_DESC","GEOL_LEG"
"DATA","S-1","0.0","1.5","Made ground, gravelly SAND","FILL"
"DATA","S-1","1.5","7.0","Loose to medium dense fine SAND","SAND"
"DATA","S-1","7.0","14.0","Soft grey silty CLAY","CLAY"
"DATA","S-1","14.0","20.0","Dense SAND and gravel","SAND"
"DATA","S-2","0.0","6.5","Medium dense SAND","SAND"
"DATA","S-2","6.5","13.0","Soft CLAY","CLAY"
"DATA","S-2","13.0","18.0","Dense GRAVEL","GRAVEL"

"GROUP","ISPT"
"HEADING","LOCA_ID","ISPT_TOP","ISPT_NVAL"
"DATA","S-1","2.0","9"
"DATA","S-1","4.0","12"
"DATA","S-1","6.0","15"
"DATA","S-1","9.0","4"
"DATA","S-1","16.0","38"
"DATA","S-2","3.0","14"
"DATA","S-2","8.0","3"
"DATA","S-2","15.0","45"
'''


def main() -> None:
    proj = parse_ags4_text(AGS)
    print(f"Proyecto «{proj.project_name}» ({proj.project_number}), {len(proj.boreholes)} sondeos, estado {proj.status}, unidades {proj.units}")
    for bh in proj.boreholes:
        print(f"  {bh.hole_id}: X = {bh.x:.0f}, Y = {bh.y:.0f}, cota {bh.elevation} m, profundidad {bh.final_depth} m; SPT " + ", ".join(f"N = {t.n_value} a {t.depth} m" for t in bh.spt_tests))
        for s in bh.strata:
            print(f"     {s.top_depth:5.1f}–{s.base_depth:5.1f} m  {s.geology_code:6} → {s.soil_type:4}  γ = {s.unit_weight}, c = {s.cohesion}, φ = {s.friction_angle}, E = {s.elastic_modulus / 1e3:.0f} MPa   «{s.description}»")
    script = generate_plaxis_python_script(proj, model_dim="2D")
    lines = script.splitlines()
    print(f"\nGuion PLAXIS 2D: {len(lines)} líneas, {sum('soilmat' in l for l in lines)} materiales, {sum('g_i.borehole' in l for l in lines)} sondeos, {sum('soillayer' in l for l in lines)} capas. Primeras líneas útiles:")
    for l in lines[9:16]:
        print("   ", l)
    print("  Los parámetros de los materiales (γ, c, φ, E) son los por defecto por tipo arena/arcilla del lector, no los del informe: hay que sustituirlos antes de calcular.")
    try:
        from fastapi.testclient import TestClient

        from terzaghi.api import create_app
    except ImportError:
        print("\nFastAPI no instalado: `pip install terzaghi[api]` para la parte REST.")
        return
    client = TestClient(create_app())
    print(f"\nAPI REST (TestClient, sin servidor), versión {create_app().version}:")
    print(f"  GET /api/geo/health → {client.get('/api/geo/health').status_code} {client.get('/api/geo/health').json()}")
    r = client.post("/api/geo/gazetas-springs", json={"L_m": 4.0, "B_m": 2.0, "Vs_m_per_s": 200.0, "rho_soil_kg_m3": 2000.0, "nu_soil": 0.35}).json()
    print(f"  POST /gazetas-springs 4 × 2 m → K_z = {r['Kz_kN_per_m']:,.0f} kN/m, K_rx = {r['Krx_kNm_per_rad']:,.0f} kN·m/rad, G = {r['G_soil_MPa']:.0f} MPa")
    r = client.post("/api/geo/liquefaction", json={"depth_m": 6, "sigma_v_kPa": 130, "sigma_v_eff_kPa": 100, "N1_60_cs": 20, "a_max_g": 0.3, "Mw": 7.5}).json()
    print(f"  POST /liquefaction (z = 6, N = 20, 0,3 g, M 7,5) → CSR = {r['CSR']:.3f}, CRR = {r['CRR']:.4f}, MSF = {r['MSF']:.3f}, K_σ = {r['K_sigma']:.3f}, FS = {r['FS']:.3f}, is_safe = {r['is_safe']}")
    r = client.post("/api/geo/py/matlock", json={"z_m": 3.0, "D_m": 0.8, "su_kPa": 50.0}).json()
    print(f"  POST /py/matlock (z = 3, D = 0,8, s_u = 50) → {len(r['y_m'])} puntos, p_ult = {max(r['p_kN_per_m']):.1f} kN/m, y_máx = {max(r['y_m']) * 1e3:.0f} mm")
    r = client.post("/api/geo/tunnel-winkler", json={"R0_m": 3.0, "P0_kPa": 500.0, "E_soil_MPa": 120.0, "nu_soil": 0.25, "c_kPa": 150.0, "phi_deg": 30.0}).json()
    print(f"  POST /tunnel-winkler → P_cr = {r['Pcr_kPa']:.1f} kPa, equilibrio {r['equilibrium_status']} a {r['equilibrium_pressure_kPa']:.1f} kPa, k_Winkler = {r['k_winkler_static_kN_m3']:,.0f} kN/m³")
    r = client.post("/api/geo/pile-group/lateral", json={"s_over_D": 4.0, "rows": 3}).json()
    print(f"  POST /pile-group/lateral (s/D = 4, 3 filas) → η = {r['global_efficiency']:.3f}; con rows = 0 → {client.post('/api/geo/pile-group/lateral', json={'s_over_D': 4.0, 'rows': 0}).status_code} (validación Pydantic)")
    zap = {"B_m": 1.5, "L_m": 2.5, "D_f_m": 0.5, "phi_deg": 35.0, "c_kPa": 0.0, "gamma_kN_m3": 18.0, "code": "EU"}
    q_anexo_d = 903.5   # W00675, EN 1997-1 Anexo D
    print("  POST /bearing-capacity, zapata de W00675 (Anexo D publicado: 903,5 kPa):")
    for etiqueta, extra in (("EC7 Anexo D, method = chen_ec7", {"method": "chen_ec7"}),
                            ("EC7 con N_γ de Vesic, method = vesic", {"method": "vesic"}),
                            ("vía DEPRECADA, use_ec7_canonical = False", {"method": "vesic", "use_ec7_canonical": False})):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            r = client.post("/api/geo/bearing-capacity", json={**zap, **extra}).json()
        print(f"    {etiqueta:<42} q_ult = {r['q_ult_kPa']:6.1f} kPa ({r['q_ult_kPa'] / q_anexo_d - 1:+.1%}), q_adm = {r['q_adm_kPa']:.1f} kPa")
    print("\nEl lector AGS4 cubre PROJ/LOCA/GEOL/ISPT (no CPT ni laboratorio) y clasifica por la palabra CLAY en la descripción; el guion de PLAXIS necesita el servidor de Remote Scripting (puerto 10000) y la licencia correspondiente.")


if __name__ == "__main__":
    main()
