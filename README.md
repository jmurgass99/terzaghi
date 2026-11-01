# terzaghi — geotecnia y cimentaciones en Python: EN 1997-1 Anexo D, pilotes, consolidación, licuefacción, muelles de Gazetas, muros, túneles

**Español** · [English](README.en.md) · [Português](README.pt.md) · [Italiano](README.it.md)

Capacidad portante de zapatas por la ecuación completa del Anexo D de EN 1997-1 (área efectiva, inclinación de carga, factores parciales DA1/DA2, cláusula no drenada), pilotes (métodos α y β, curvas p-y de Matlock y Reese, grupos, monopilotes cíclicos), consolidación con drenes verticales (Terzaghi, Barron, Hansbo, Carrillo), licuefacción por SPT de Boulanger e Idriss (2014), respuesta de sitio 1D, muelles estáticos y dinámicos de Gazetas, muros de gaviones y empujes (Rankine, Coulomb, Mononobe-Okabe), excavaciones, túneles por convergencia-confinamiento, durabilidad del hormigón, hormigón confinado de Mander, lectura de AGS4 con salida a PLAXIS y una API REST. Dependencias: `numpy`, `pydantic`, `forallpeople`.

[![CI](https://github.com/jmurgass99/terzaghi/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/terzaghi/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Qué problema resuelve

Las fórmulas de geotecnia son cortas pero están llenas de decisiones escondidas: qué autor de N_γ, si la excentricidad recorta la base, qué factores parciales lleva cada enfoque de diseño, si r_d lleva senos o no, qué p-multiplicador usa cada fila de pilotes. `terzaghi` las implementa como funciones pequeñas con los coeficientes a la vista y los números anclados a ejemplos publicados y a fichas resueltas de un máster (W00675 y W00672 de capacidad portante, W00254 y W00255 de precarga, W00664 y W00677 de empujes, W00704 y W00678 de Mononobe-Okabe, las ecuaciones numeradas de Boulanger e Idriss 2014), de modo que cada resultado se pueda seguir a mano. Cuando una fórmula del paquete no está en una fuente, lo dice en el código y en este README.

**Úsalo cuando**

- necesites la capacidad portante de una zapata con la ecuación completa del Anexo D (área efectiva, i_q/i_c/i_γ, s_q/s_c/s_γ publicados, DA1-C1/C2 y DA2) o la cláusula no drenada D.3, y quieras ver los nueve valores intermedios;
- hagas un anteproyecto de pilotes: capacidad axial en perfil estratificado, curvas p-y para los muelles de SAP2000 o ETABS, eficiencia de grupo y monopilotes con degradación cíclica;
- calcules plazos de precarga con y sin drenes verticales, asientos corregidos por Skempton-Bjerrum o distorsiones angulares entre zapatas;
- evalúes licuefacción capa a capa con el procedimiento SPT de Boulanger e Idriss (2014), la amplificación de un estrato blando o los muelles de interacción suelo-estructura de una zapata;
- comprobes un muro de gaviones o un muro en voladizo por los tres estados límite de EN 1997-1 con empuje estático o sísmico, el fondo de una excavación en arcilla o el sostenimiento de un túnel circular.

**No lo uses para**

- estabilidad de taludes y círculos críticos: el muro de gaviones acepta los datos de un círculo pero no lo busca (eso es `slipcircle`);
- respuesta de sitio con varios estratos: el producto de 1/cos(k·h) por capa es exacto para una capa sobre base rígida y falla con varias (ver Limitaciones);
- grupos de pilotes con la memoria `memos.pile_group_lateral`: su fórmula no reduce nada para s/D ≥ 1; usa `piles.group` (Brown 1988);
- flotación del fondo de excavaciones: `check_excavation` no conoce el espesor del tapón ni la carga del acuífero;
- pérdidas, costes o decisiones de proyecto: todo son comprobaciones de anteproyecto con parámetros característicos que el usuario aporta.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/terzaghi.git
```

Extras: `api` (FastAPI + TestClient), `memos` (memorias con handcalcs), `test`. Para desarrollo: `git clone`, `pip install -e ".[test,api,memos]"`, `pytest -q` (37 ficheros de tests; `tests/test_examples.py` ejecuta los 30 ejemplos como subprocesos). En Windows, si la consola no es UTF-8, ejecuta los ejemplos con `python -X utf8 examples/<nombre>.py`.

## Capacidades

| Capacidad | Módulos | Norma o referencia | Casos de uso |
|---|---|---|---|
| Cimentación superficial: ecuación del Anexo D (drenada y no drenada) con área efectiva de Meyerhof, factores de forma e inclinación, N_γ de Chen, Vesić, Meyerhof y Brinch Hansen, factores parciales DA1-C1/C2 y DA2; perfil de suelo con nivel freático (σ_v, u, σ'_v, K_0, K_a, K_p); puerta `evaluate_bearing_ec7` en metros y vía deprecada con aviso | `bearing_capacity`, `_foundation.bearing_capacity`, `_foundation.soil`, `_foundation.geometry` | EN 1997-1:2004 Anexo D y Anexo A; Vesić (1973); Meyerhof (1963); Brinch Hansen (1970); fichas W00675 y W00672 | [5 casos](#1-cimentación-superficial-en-1997-1-anexo-d) |
| Pilotes: capacidad axial α (API RP 2A) y β en perfil estratificado con nivel freático; curvas p-y de Matlock (arcilla blanda) y Reese (arena) y su exportación a enlaces multilineales de SAP2000; p-multiplicadores de Brown (1988), tabla y bloque pasivo de Mokwa-Duncan, memoria handcalcs; curvas p-y cíclicas y dinámicas para monopilotes | `piles.axial_capacity`, `piles.py_curves`, `piles.group`, `piles.mokwa_duncan`, `piles.dynamic_py`, `memos.pile_group_lateral`, `integration.fastsap_pysprings` | API RP 2A-WSD §6.4; Matlock (1970); Reese, Cox y Koop (1974); Brown et al. (1988); Mokwa y Duncan (2001); DNV-RP-C212 (parámetros) | [5 casos](#2-pilotes) |
| Asientos, consolidación y correlaciones: Terzaghi 1D (dos ramas), drenes verticales de Barron y Hansbo (remoldeo y resistencia del dren), Carrillo; corrección de Skempton-Bjerrum y auditoría de distorsión angular (Anexo H); correlaciones SPT/CPT (N_60, C_N, φ' de Hatanaka-Uchida, E_s de Bowles, S_u del cono); catálogo de estratigrafías; suelos no saturados (van Genuchten, Bishop) | `consolidation`, `skempton_bjerrum`, `audit.differential_settlement`, `correlations`, `estratigrafias_catalogo`, `unsaturated` | Terzaghi (1943); Barron (1948); Hansbo (1981); Carrillo (1942); Bjerrum (1972); EN 1997-1 Anexo H; Skempton (1986); Hatanaka y Uchida (1996); Bowles (1997); van Genuchten (1980); fichas W00254 y W00255 | [5 casos](#3-asientos-consolidación-y-correlaciones) |
| Empujes, muros y excavaciones: muro de gaviones escalonado por DA1-a/DA1-b/DA2 (hundimiento con B', deslizamiento, vuelco, cursos, círculo global), Rankine multicapa con sobrecargas, K_0 de Jaky con OCR, Coulomb y Mononobe-Okabe con auditoría ASD, estabilidad del fondo de excavación (Terzaghi-Peck) | `gabion_wall`, `gabion_wall_safety`, `excavation`, `_foundation.soil` | EN 1997-1 §9 y Anexo A; EN 1998-5 Anexo E; Coulomb; Mononobe-Okabe; Terzaghi y Peck; ejemplo de Hanif; fichas W00664, W00677, W00676, W00704 y W00678 | [5 casos](#4-empujes-muros-y-excavaciones) |
| Licuefacción, respuesta de sitio y SSI: Boulanger e Idriss (2014) por capas con capas sin ensayo declaradas (CSR, CRR, MSF, K_σ, r_d, corrección por finos); propagación SH 1D de una capa sobre roca con espectro en superficie; muelles estáticos de Gazetas (seis rigideces, asiento y giro) e impedancias dinámicas con radiación y amortiguamiento material | `liquefaction`, `liquefaction.boulanger_idriss`, `site_response`, `gazetas_springs`, `ssi_springs` | Boulanger e Idriss (2014) ec. 2, 6–8, 11, 34, 72; Kramer (1996); Gazetas (1991); NIST GCR 12-917-21 | [5 casos](#5-licuefacción-respuesta-de-sitio-y-ssi) |
| Túneles, durabilidad, materiales y datos: convergencia-confinamiento con Mohr-Coulomb (P_cr, radio plástico, curva del sostenimiento, equilibrio, muelles de Winkler); cloruros por Fick y carbonatación; hormigón confinado de Mander; lector AGS4 y generador de guion PLAXIS; API REST con FastAPI | `tunnels`, `durability`, `materials.mander`, `ags4_plaxis`, `api` | Duncan Fama (1993) / Hoek (CCM); EN 206, fib MC (modelos paramétricos); Mander, Priestley y Park (1988); AGS4; PLAXIS Remote Scripting | [5 casos](#6-túneles-durabilidad-materiales-y-datos) |

Los 30 scripts de `examples/` se ejecutaron en un entorno limpio antes de publicarse; su salida está en `examples/output/` y es la que se reproduce aquí.

## Casos de uso

### 1. Cimentación superficial (EN 1997-1 Anexo D)

#### Zapata sobre arena seca (ejemplo publicado W00675 §4.3 DA1-C1): los nueve valores intermedios y lo que da la vía deprecada

<details><summary>Salida real de <code>python examples/bearing_ec7_annex_d_pad_footing_w00675_nine_published_values_vs_deprecated_path.py</code></summary>

```text
W00675 §4.3 DA1-C1 — zapata 2,5 × 1,5 m, d = 0,5 m, φ'_d = 35°, c' = 0, γ = 18 kN/m³, γ_R;v = 1,0

  magnitud            publicado   terzaghi   desvío
  Nq                      33.30     33.296 -0.012 %
  Nc                      46.10     46.124 +0.051 %
  Ngamma                  45.20     45.228 +0.062 %
  sq                       1.34      1.344 +0.309 %
  sc                       1.35      1.355 +0.356 %
  sgamma                   0.82      0.820 +0.000 %
  q_ult_overburden       402.80    402.793 -0.002 %
  q_ult_cohesion           0.00      0.000     +0.0
  q_ult_self_weight      500.70    500.673 -0.005 %
  q_ult                  903.50    903.466 -0.004 %

  B' = 1.50 m, L' = 2.50 m, A' = 3.750 m²; R_k = q_ult·A' = 3388.0 kN; R_d = R_k/γ_R;v = 3388.0 kN (fórmula chen_ec7, drained)

Vía deprecada `evaluate_bearing` sobre los mismos datos (factores de forma sin publicar, ciega a e y H):
  vesic          q_ult =   927.13 kPa ( +2.62 % frente a 903,5); N_γ =  48.03; q_adm (γ_R;v = 1,4) =   662.2 kPa  [DeprecationWarning]
  meyerhof       q_ult =   789.11 kPa (-12.66 % frente a 903,5); N_γ =  37.15; q_adm (γ_R;v = 1,4) =   563.6 kPa  [DeprecationWarning]
  brinch_hansen  q_ult =   748.10 kPa (-17.20 % frente a 903,5); N_γ =  33.92; q_adm (γ_R;v = 1,4) =   534.4 kPa  [DeprecationWarning]

El Anexo D usa N_γ = 2·(N_q − 1)·tan φ (Chen); Vesić da 2·(N_q + 1)·tan φ y Brinch Hansen 1,5·(N_q − 1)·tan φ: con φ = 35° son 45,2 / 48,0 / 33,9. La vía deprecada se conserva con sus números intactos para no romper llamadores; la puerta EC7 es la que hay que usar.
```

</details>

#### Carga excéntrica e inclinada: área efectiva de Meyerhof, factores i_q/i_c/i_γ y los 41 % que se pierde la vía deprecada

<details><summary>Salida real de <code>python examples/bearing_ec7_eccentric_and_inclined_load_effective_area_and_blind_legacy_41pct.py</code></summary>

```text
Zapata 2,5 × 2,5 m, D_f = 1,5 m, arena φ' = 32°, γ = 19 kN/m³ (EN 1997-1 Anexo D, N_γ de Chen):

  caso                           B′ [m] L′ [m] A′ [m²]    i_q    i_γ q_ult [kPa]  R_k [kN] legacy/EC7
  S1 centrada, vertical            2.50   2.50   6.250  1.000  1.000     1471.33      9196      0.933
  S3 e_B = 0,30 m                  1.90   2.50   4.750  1.000  1.000     1312.76      6236      1.045
  S4 H/V = 150/1000 kN             2.50   2.50   6.250  0.784  0.666     1098.87      6868      1.249
  S5 e_B = 0,30 m + H/V            1.90   2.50   4.750  0.775  0.659      972.53      4620      1.411
  S5b e_B = e_L = 0,30 m + H/V     1.90   1.90   3.610  0.784  0.666     1025.20      3701      1.339

  La vía deprecada devuelve 1372.43 kPa en los cinco casos (no tiene e ni H): en S5 es un 41.1 % más que el Anexo D.
  Exponente m para carga paralela a B': m = (2 + B'/L')/(1 + B'/L') = 1.568; i_q = (1 − H/V)^m = 0.775 (c' = 0)

  H > 0 con V = 0 → ValueError: inclination_factors: H=150 kN>0 con V=0 kN<=0. La inclinación de carga drenada (Vesic / EN 1997-1 Anexo D) exi…

Con la excentricidad el área efectiva cae un 24 % y q_ult un 11 %; la inclinación quita otro 25 %: los dos efectos se multiplican y ninguno es despreciable para una zapata de pilar con viento o sismo.
```

</details>

#### Factores N_q, N_c y N_γ para φ' = 20–40° según el autor (Brinch Hansen, Meyerhof, Vesić, Chen/EC7) y la errata de la ficha W00675

<details><summary>Salida real de <code>python examples/bearing_capacity_factors_ngamma_authors_table_phi_20_to_40_and_w00675_errata.py</code></summary>

```text
  φ [°]      N_q      N_c N_γ Hansen N_γ Meyerhof  N_γ Vesić N_γ Chen/EC7
      0    1.000    5.142       0.00         0.00       0.00         0.00
     20    6.399   14.835       2.95         2.87       5.39         3.93
     25   10.662   20.721       6.76         6.77      10.88         9.01
     28   14.720   25.803      10.94        11.19      16.72        14.59
     30   18.401   30.140      15.07        15.67      22.40        20.09
     32   23.177   35.490      20.79        22.02      30.21        27.72
     35   33.296   46.124      33.92        37.15      48.03        45.23
     40   64.195   75.313      79.54        93.69     109.41       106.05

Contraste con la tabla publicada (Das, Principles of Foundation Engineering; 2 decimales):
  φ = 20°: ΔN_q = -0.001, ΔN_c = +0.005, ΔN_γ Vesić = -0.004, Meyerhof = +0.001, Hansen = -0.002
  φ = 30°: ΔN_q = +0.001, ΔN_c = -0.000, ΔN_γ Vesić = +0.002, Meyerhof = -0.002, Hansen = -0.000
  φ = 40°: ΔN_q = -0.005, ΔN_c = +0.003, ΔN_γ Vesić = +0.001, Meyerhof = +0.001, Hansen = +0.001

Ficha W00675 (tabla rotulada «Hansen, EN 1997-1 Annex D»): N_γ impreso frente a cada autor
  φ = 25°: impreso  10.88 | Vesić  10.88 | Anexo D   9.01 | Hansen   6.76 → coincide con vesic
  φ = 28°: impreso  16.72 | Vesić  16.72 | Anexo D  14.59 | Hansen  10.94 → coincide con vesic
  φ = 30°: impreso  22.40 | Vesić  22.40 | Anexo D  20.09 | Hansen  15.07 → coincide con vesic
  φ = 32°: impreso  30.22 | Vesić  30.21 | Anexo D  27.72 | Hansen  20.79 → coincide con vesic
  φ = 35°: impreso  48.03 | Vesić  48.03 | Anexo D  45.23 | Hansen  33.92 → coincide con vesic

Comprobación cerrada φ = 30°: N_q = e^(π·tan 30°)·tan²60° = 18.4011222 (tabla 18,40); N_c = (N_q − 1)/tan 30° = 30.1396 (tabla 30,14); con φ = 0, N_c = π + 2 = 5.1416.
Elegir el autor de N_γ cambia el término de peso propio hasta un 40 % (Hansen frente a Vesić a 35°); el Anexo D fija el de Chen y los anexos nacionales pueden decir otra cosa.
```

</details>

#### Arcilla no drenada: cláusula D.3 frente a la puerta drenada con φ = 0 y la resistencia de diseño por DA1-C1, DA1-C2 y DA2

<details><summary>Salida real de <code>python examples/bearing_undrained_clay_annex_d3_vs_drained_gate_phi_zero_and_design_approaches.py</code></summary>

```text
Arcilla c_u = 75 kPa, γ = 18 kN/m³, D_f = 1.5 m; N_c = π + 2 = 5.1416

  caso                          s_c    i_c q_ult D.3 [kPa] puerta φ=0 [kPa] diferencia
  C1 2,5 × 2,5 centrada       1.200  1.000         489.743          489.743   0.00e+00
  C2 2,0 × 4,0 centrada       1.100  1.000         451.181          451.181   0.00e+00
  C3 2,5 × 2,5, e_B = 0,30    1.152  1.000         471.234          471.234   0.00e+00
  C4 2,5 × 2,5, H = 150 kN    1.200  0.912         449.166          449.166   0.00e+00

Resistencia de diseño R_d = q_ult(c_u/γ_cu)·A'/γ_R;v para la zapata 2,5 × 2,5 centrada:
  enfoque   γ_cu  γ_R;v c_u,d [kPa] q_ult [kPa]  R_k [kN]  R_d [kN]
  DA1-C1    1.00   1.00       75.00       489.7      3061      3061
  DA1-C2    1.40   1.00       53.57       357.5      2235      2235
  DA2       1.00   1.40       75.00       489.7      3061      2186

Comprobación a mano C1: s_c = 1 + 0,2·B'/L' = 1,2; q_ult = 5,1416·75·1,2 + 27 = 489.74 kPa.
DA1-C2 reduce la resistencia del material (c_u/1,4) y DA2 la resistencia global (/1,4): no dan el mismo R_d (2235 frente a 2186 kN) porque el término q = γ·D_f no lleva c_u: DA2 lo divide por 1,4 y DA1-C2 lo deja intacto.
```

</details>

#### Zapata corrida con nivel freático en la base (W00675 GT2): tensiones del perfil, γ' bajo el agua y q_ult = 822 kPa

<details><summary>Salida real de <code>python examples/bearing_strip_footing_water_table_soil_profile_stresses_w00675_gt2_822kpa.py</code></summary>

```text
Perfil: arena φ' = 28.0°, c' = 10.0 kPa, γ = 18.0 / γ_sat = 19.81 kN/m³, nivel freático a 1.5 m (base de la zapata)
  z [m] σ_v [kPa]  u [kPa] σ′_v [kPa]
    0.0      0.00     0.00       0.00
    1.0     18.00     0.00      18.00
    1.5     27.00     0.00      27.00
    2.5     46.81     9.81      37.00
    4.0     76.53    24.53      52.00
    6.0    116.14    44.15      72.00
  K_0 (Jaky) = 1 − sin φ' = 0.531; K_a = 0.361; K_p = 2.770

Factores de Vesić a 28.0°: N_q = 14.720, N_c = 25.803, N_γ = 16.717
A mano (ficha W00675 GT2): q_ult = 10.0·25.80 + 27·14.72 + ½·10.00·2.0·16.72 = 258.03 + 397.44 + 167.17 = 822.6 kPa (ficha: 822)
`drained_bearing_capacity` (L = 200 m, γ' en el término de peso, q = γ·D_f aparte): q_ult = 825.3 kPa; s_q = 1.0047, s_c = 1.0050, s_γ = 0.9970
Sin nivel freático (γ = 18 en los dos términos): 958.6 kPa → el agua en la base quita un 14 % (solo afecta al término de peso propio).
Con N_γ del Anexo D (Chen, 2·(N_q − 1)·tan φ = 14.590): 804.1 kPa, un 2.6 % menos que con Vesić.

La puerta `evaluate_bearing_ec7` no tiene nivel freático: si hay agua en la base, pásale γ' sabiendo que también lo usará en la sobrecarga (conservador); para separar los dos pesos usa `drained_bearing_capacity` directamente.
```

</details>

### 2. Pilotes

#### Pilote hincado en arcilla blanda sobre arena: capacidad axial α (API RP 2A) y β, reparto por capas y barrido de longitud

<details><summary>Salida real de <code>python examples/pile_axial_alpha_beta_api_rp2a_layered_clay_over_sand_per_layer_and_length_sweep.py</code></summary>

```text
Pilote D = 0.6 m, nivel freático a 2.0 m, FS = 2.5; capas: arcilla blanda 0–8 (S_u 30), arcilla media 8–14 (S_u 60), arena densa 14–30 (φ' 34°)

  L [m] capa de punta Q_fuste [kN] Q_punta [kN] Q_ult [kN] Q_adm [kN]          fuste por capa [kN]
   10.0 clay (8–14 m)          422          153        575        230                [287, 135, 0]
   14.0 clay (8–14 m)          729          153        882        353                [287, 442, 0]
   16.0 sand (14–30 m)          845         1204       2049        820              [287, 442, 116]
   18.0 sand (14–30 m)          976         1357       2333        933              [287, 442, 247]
   22.0 sand (14–30 m)         1286         1663       2949       1180              [287, 442, 557]
   26.0 sand (14–30 m)         1659         1969       3628       1451              [287, 442, 930]

Detalle de la adhesión α en la arcilla (σ'_v a media capa, ψ = S_u/σ'_v):
  0–8 m: σ'_v(4 m) = 48.4 kPa, ψ = 0.620, α = 0.635, f_s = 19.0 kPa
  8–14 m: σ'_v(11 m) = 101.7 kPa, ψ = 0.590, α = 0.651, f_s = 39.1 kPa
  Arena a 18 m: σ'_v = 163.0 kPa; K = 1 − sin 34° = 0.441; δ = 0,8·34° = 27,2°; f_s = K·tan δ·σ'_v = 36.9 kPa

Empotrar 2 m en la arena multiplica la punta por 7.9 (9·S_u = 540 kPa frente a N_q·σ'_v con N_q acotado a 120) y la capacidad total por 2.32.
Con FS = 2,5 sobre la suma; en proyecto conviene factores distintos para fuste (más fiable) y punta, y comprobar la hinca con el registro de golpes.
```

</details>

#### Curvas p-y de Matlock y Reese a varias profundidades y su exportación como muelles multilineales para SAP2000

<details><summary>Salida real de <code>python examples/pile_py_curves_matlock_clay_reese_sand_depth_family_and_sap_link_export_dry_run.py</code></summary>

```text
Pilote D = 0.6 m. Arcilla blanda s_u = 40.0 kPa (γ' = 7.19 kN/m³, ε_50 = 0,02); arena φ' = 32.0°, γ = 18.0 kN/m³, k_pH = 25 MN/m³

  z [m] Matlock p_ult [kN/m] factor N_p y_50 [mm] p(10 mm) [kN/m] | Reese p_ult [kN/m] k_ini [MN/m²] p(10 mm) [kN/m]
    1.0                 96.3       4.01      30.0            33.3 |               32.0            25            30.8
    3.0                144.9       6.04      30.0            50.2 |               95.9            75            92.4
    6.0                216.0       9.00      30.0            74.8 |              191.7           150           184.9
   10.0                216.0       9.00      30.0            74.8 |              319.5           250           308.2
  En arcilla p_ult crece con z hasta N_p = 9 (aquí desde z ≈ 6 m); en arena crece linealmente con z y la hipérbola llega a p_ult solo asintóticamente.

Exportación en seco: 4 muelles, dry_run = True; nombres ['PY_z1.00', 'PY_z3.00', 'PY_z6.00', 'PY_z10.00']
  PY_z1.00: (0.0 mm, 0.0), (34.3 mm, 50.3), (68.6 mm, 63.4), (102.9 mm, 72.6) … (240.0 mm, 96.3 kN/m)
  PY_z3.00: (0.0 mm, 0.0), (34.3 mm, 75.8), (68.6 mm, 95.5), (102.9 mm, 109.3) … (240.0 mm, 144.9 kN/m)
  PY_z6.00: (0.0 mm, 0.0), (34.3 mm, 112.9), (68.6 mm, 142.3), (102.9 mm, 162.9) … (240.0 mm, 216.0 kN/m)
  PY_z10.00: (0.0 mm, 0.0), (4.3 mm, 45.8), (8.6 mm, 84.6), (12.9 mm, 116.4) … (30.0 mm, 172.8 kN/m)

  Arena a 10 m: el exportador satura en 172.8 kN/m (fórmula 1,5·γ·z·φ/30·D, sin referencia) frente a 319.5 kN/m de `py_reese_sand`: razón 1.85. Para muelles de arena en SAP conviene muestrear `py_reese_sand` directamente.
  Nodo sin s_u ni φ → ValueError: PySpringNode z=2.0 m: sin su_kPa ni phi_deg; no se fabrica una resistencia (ante… (antes se fabricaba una arena de 30°)
```

</details>

#### Eficiencia lateral de un grupo 3 × 3: las tres convenciones de p-multiplicadores del paquete no dicen lo mismo

<details><summary>Salida real de <code>python examples/pile_group_p_multipliers_three_conventions_brown_mokwa_duncan_table_and_memo.py</code></summary>

```text
Grupo 3 × 3, D = 0.6 m, P_single = 200 kN (capacidad lateral de un pilote aislado)

   s/D Brown 1988 (f_1, f_2, f_3)  η_Brown tabla M-D (f_1, f_2, f_3)  η_tabla memo f_m filas 2–3  η_memo  P_grupo [kN] Brown / tabla / memo
   2.0            (0.8, 0.4, 0.3)    0.500           (1.0, 0.7, 0.5)    0.733              1.000   1.000      900 /   1320 /   1800
   3.0            (0.8, 0.4, 0.3)    0.500           (1.0, 0.7, 0.5)    0.733              1.000   1.000      900 /   1320 /   1800
   4.0           (0.9, 0.62, 0.5)    0.675           (1.0, 0.7, 0.5)    0.733              1.000   1.000     1215 /   1320 /   1800
   5.0           (1.0, 0.85, 0.7)    0.850           (1.0, 0.7, 0.5)    0.733              1.000   1.000     1530 /   1320 /   1800
   6.0           (1.0, 0.85, 0.7)    0.850           (1.0, 0.7, 0.5)    0.733              1.000   1.000     1530 /   1320 /   1800

Memoria handcalcs para s/D = 3 (primeras líneas):
    PASO 2: p-multipliers por fila (Mokwa-Duncan)
    ----------------------------------------
      Fila leading (row 1): fm = 1.0
      Filas traseras: fm = min(0.64 + 0.36*(s/d), 1.0)
      fm = min(0.64 + 0.36*3.000, 1.0)
      fm = min(1.7200, 1.0) = 1.0000
    
      Fila 1 (leading): fm = 1.0000

Lectura: Brown (1988) es el único de los tres que depende de la separación y coincide con los p-multiplicadores que piden las guías (FHWA, AASHTO) para 3 ≤ s/D ≤ 5. La tabla de `mokwa_duncan` es fija por fila y la fórmula de la memoria satura a 1 desde s/D = 1: la memoria documenta el procedimiento, pero su número no reduce la capacidad del grupo. Para proyecto, usar `pile_group_efficiency_lateral` y revisar la memoria a mano.
```

</details>

#### Grupo con encepado empotrado (Mokwa y Duncan 2001): cuña pasiva del bloque frente a pilotes individuales, barriendo separación y empotramiento

<details><summary>Salida real de <code>python examples/pile_group_lateral_passive_block_vs_individual_mokwa_duncan_spacing_embedment_sweep.py</code></summary>

```text
Grupo 3 × 3, D = 0.6 m, arena φ' = 30.0° (K_p = 3.00), γ = 18.0 kN/m³, L = 12 m

=== c = 0 kPa ===
  s [m] H_emb [m] B_f [m] p_m medio bloque [kN] individuales [kN] H_grupo [kN]  gobierna
    1.2       3.0    3.00     0.733         729               962          729  bloque
    1.2       4.5    3.00     0.733        1640              2165         1640  bloque
    1.2       6.0    3.00     0.733        2916              3849         2916  bloque
    1.8       3.0    4.20     0.733        1021               962          962  pilotes
    1.8       4.5    4.20     0.733        2296              2165         2165  pilotes
    1.8       6.0    4.20     0.733        4082              3849         3849  pilotes
    3.0       3.0    6.60     0.733        1604               962          962  pilotes
    3.0       4.5    6.60     0.733        3609              2165         2165  pilotes
    3.0       6.0    6.60     0.733        6415              3849         3849  pilotes

=== c = 20 kPa ===
  s [m] H_emb [m] B_f [m] p_m medio bloque [kN] individuales [kN] H_grupo [kN]  gobierna
    1.2       3.0    3.00     0.733        1353              2138         1353  bloque
    1.2       4.5    3.00     0.733        2576              3208         2576  bloque
    1.2       6.0    3.00     0.733        4163              4277         4163  bloque
    1.8       3.0    4.20     0.733        1894              2138         1894  bloque
    1.8       4.5    4.20     0.733        3606              3208         3208  pilotes
    1.8       6.0    4.20     0.733        5828              4277         4277  pilotes
    3.0       3.0    6.60     0.733        2976              2138         2138  pilotes
    3.0       4.5    6.60     0.733        5666              3208         3208  pilotes
    3.0       6.0    6.60     0.733        9159              4277         4277  pilotes

Comprobación a mano (s = 1,8, H = 4,5, c = 0): B_f = 0,6 + 2·1,8 = 4,2 m; bloque = ½·3.00·18·4,5²·4,2 = 2296 kN (2296); individual = ½·K_p·γ·H²·D = 328 kN × 9 × p_m = 0.733 → 2165 kN
El bloque crece con la anchura del grupo (B_f) y los individuales con el número de pilotes y el empotramiento: la cohesión favorece más a los pilotes (9·c·D·H) que al bloque. El modelo es el de anteproyecto de Mokwa-Duncan; con encepado flexible o pilotes largos hace falta un análisis p-y completo.
```

</details>

#### Monopilote eólico de 7 m: curvas p-y cíclicas con degradación por ciclos y factor dinámico a_0

<details><summary>Salida real de <code>python examples/monopile_offshore_dynamic_py_cyclic_degradation_cycles_and_frequency_a0.py</code></summary>

```text
=== clay — D = 7 m, z = 6 m, V_s = 180 m/s {'su_kPa': 90.0} ===
  N ciclos f [Hz]    a_0 p_ult est. [kN/m] p_ult cíclico [kN/m] reducción mult. rigidez p_din(y = 50 mm) [kN/m]
         1   0.20  0.049              2937                 2937      0.0%        1.0004                    1068
         1   1.00  0.244              2937                 2937      0.0%        1.0090                    1078
       100   0.20  0.049              2937                 2467     16.0%        1.0004                     897
       100   1.00  0.244              2937                 2467     16.0%        1.0090                     905
      1000   0.20  0.049              2937                 2232     24.0%        1.0004                     812
      1000   1.00  0.244              2937                 2232     24.0%        1.0090                     819
     10000   0.20  0.049              2937                 1997     32.0%        1.0004                     726
     10000   1.00  0.244              2937                 1997     32.0%        1.0090                     733

=== sand — D = 7 m, z = 6 m, V_s = 180 m/s {'phi_deg': 35.0, 'k_pH_kN_m3': 30000.0} ===
  N ciclos f [Hz]    a_0 p_ult est. [kN/m] p_ult cíclico [kN/m] reducción mult. rigidez p_din(y = 50 mm) [kN/m]
         1   0.20  0.049              2867                 2867      0.0%        1.0004                    2165
         1   1.00  0.244              2867                 2867      0.0%        1.0090                    2183
       100   0.20  0.049              2867                 2409     16.0%        1.0004                    1818
       100   1.00  0.244              2867                 2409     16.0%        1.0090                    1834
      1000   0.20  0.049              2867                 2179     24.0%        1.0004                    1645
      1000   1.00  0.244              2867                 2179     24.0%        1.0090                    1659
     10000   0.20  0.049              2867                 1950     32.0%        1.0004                    1472
     10000   1.00  0.244              2867                 1950     32.0%        1.0090                    1485

Arcilla, N = 1000: reducción = 1 − 0,08·log₁₀(1000) = 0.76; a_0 = 2π·0,2·7/180 = 0.0489, multiplicador 1 + 0,15·a_0² = 1.0004: p_ult cíclico 2232 kN/m, y_50 = 2,5·ε_50·D = 175 mm
A frecuencias de rotor (0,2–1 Hz) a_0 < 0,25 y la rigidez dinámica apenas sube; lo que manda es la degradación cíclica: 10⁴ ciclos quitan un tercio de p_ult. DNV-RP-C212 pide curvas cíclicas calibradas con ensayos; estos coeficientes son de anteproyecto.
```

</details>

### 3. Asientos, consolidación y correlaciones

#### Consolidación 1D de Terzaghi para una precarga (ficha W00255): T_v del 90 %, 14,1 años y drenaje simple frente a doble

<details><summary>Salida real de <code>python examples/consolidation_terzaghi_1d_precarga_w00255_t90_double_drainage_and_degree_vs_time.py</code></summary>

```text
Arcilla H = 10 m, c_v = 1.5 m²/año (ficha W00255 «Precarga», UPC)

T_v(U = 90 %) = −(4/π²)·ln(0,1·π²/8) = 0.84809 (ficha 0,848); comprobación U_v(0.848) = 0.9000
Drenaje doble (d = H/2 = 5 m): t_90 = T_v·d²/c_v = 14.13 años (ficha 14,1)
Drenaje simple (d = H = 10 m): t_90 = 56.5 años (×4)

  U [%]     T_v t doble [años] t simple [años]
     30  0.0707           1.18             4.7
     50  0.1963           3.27            13.1
     60  0.2827           4.71            18.8
     70  0.4028           6.71            26.9
     80  0.5672           9.45            37.8
     90  0.8481          14.13            56.5
     95  1.1290          18.82            75.3

  t [años] T_v doble U doble [%] T_v simple U simple [%]
       1.0    0.0600        27.6     0.0150         13.8
       2.0    0.1200        39.1     0.0300         19.5
       5.0    0.3000        61.3     0.0750         30.9
      10.0    0.6000        81.6     0.1500         43.7
      14.1    0.8460        89.9     0.2115         51.9
      20.0    1.2000        95.8     0.3000         61.3

Las dos ramas se cruzan en U = 0,60 (T_v = 0.2827): raíz 0.6000 frente a exponencial 0.5965 (salto < 0,5 %, inherente a la aproximación clásica).
Catorce años es inasumible para una obra: de ahí los drenes verticales del caso siguiente, que reducen el camino de drenaje a decenas de centímetros.
```

</details>

#### Drenes verticales: Barron, Hansbo (remoldeo y resistencia del dren) y Carrillo, con las fichas W00255 y W00254 (El Prat)

<details><summary>Salida real de <code>python examples/consolidation_vertical_drains_barron_hansbo_carrillo_el_prat_w00254_spacing_sweep.py</code></summary>

```text
W00255 — malla triangular l = 1,5 m, d_w = 0,066 m, c_h = 3 m²/año:
  D = 1,05·l = 1.575 m; n = D/d_w = 23.86 (ficha 23,9); F(n) = ln n − 0,75 = 2.4224 (2,42); T_h(90 %) = 0.6972 (0,696); t_90 = T_h·D²/c_h = 0.577 años = 6.9 meses (ficha 0,575)
  Sin drenes: 14.1 años → los drenes dividen el plazo por 25

  l [m]      malla  D [m]      n   F(n) t_90 Barron [meses] t_90 Hansbo s=2,kh/ks=3 [meses] + q_w = 100 m³/año [meses]
   1.00 triangular  1.050   15.9  2.017                 2.6                             4.3                        5.2
   1.00     square  1.130   17.1  2.090                 3.1                             5.1                        6.2
   1.25 triangular  1.312   19.9  2.240                 4.4                             7.2                        8.6
   1.25     square  1.412   21.4  2.313                 5.3                             8.5                       10.1
   1.50 triangular  1.575   23.9  2.422                 6.9                            10.9                       12.9
   1.50     square  1.695   25.7  2.496                 8.3                            12.8                       15.2
   2.00 triangular  2.100   31.8  2.710                13.8                            20.8                       24.4
   2.00     square  2.260   34.2  2.783                16.4                            24.5                       28.7
   2.50 triangular  2.625   39.8  2.933                23.3                            34.3                       39.9
   2.50     square  2.825   42.8  3.007                27.6                            40.4                       46.9

W00254 — El Prat: l = 2,0 m triangular, c_h = 1,5 m²/año, t = 8 meses:
  D = 2.10 m, n = 31.8, F(n) = 2.710; T_h = c_h·t/D² = 0.2268 (ficha 0,227); U_h = 1 − e^(−8T_h/F) = 0.488 (ficha 0,49)
  Vertical a los 8 meses (c_v = 1,5, d = 5 m): U_v = 0.226; combinada (Carrillo) 1 − (1 − U_v)(1 − U_h) = 0.604

El remoldeo (s = 2, k_h/k_s = 3) alarga el plazo un 60 %; la resistencia del dren con q_w = 100 m³/año añade otro 15–20 % en un estrato de 10 m. A igual separación la malla cuadrada tarda un 20 % más que la triangular (D = 1,13·l frente a 1,05·l, y el tiempo va con D²).
```

</details>

#### Asiento corregido por Skempton-Bjerrum y auditoría de distorsión angular entre zapatas (Anexo H)

<details><summary>Salida real de <code>python examples/settlement_skempton_bjerrum_mu_correction_and_differential_distortion_audit_annex_h.py</code></summary>

```text
μ de Skempton-Bjerrum (tabla simplificada de Bjerrum 1972 para zapata circular; interpolación bilineal):
   H/B A = 0.00 A = 0.25 A = 0.50 A = 0.75 A = 1.00
  0.25    0.750    0.800    0.850    0.925    1.000
  0.50    0.500    0.600    0.700    0.850    1.000
  1.00    0.400    0.500    0.600    0.800    1.000
  2.00    0.367    0.475    0.583    0.792    1.000
  4.00    0.300    0.425    0.550    0.775    1.000
  10.00    0.250    0.375    0.500    0.750    1.000

Zapata B = 3 m sobre 6 m de arcilla (H/B = 2): S_oed = 85 mm
  sobreconsolidada (A = 0,3)         μ = 0.497 → S = 42.2 mm
  ligeramente SC (A = 0,6)           μ = 0.667 → S = 56.7 mm
  normalmente consolidada (A = 1,0)  μ = 1.000 → S = 85.0 mm

Pórtico con cuatro zapatas (asientos 22/38/61/30 mm, luces 5–6 m):
  par    δ [mm]  L [m]      δ/L  1/(δ/L)  veredicto
  Z1-Z2      16   6.00  0.00267      375  WARNING
  Z1-Z3      39  12.00  0.00325      308  WARNING
  Z1-Z4       8   7.81  0.00102      976  OK (< 1/500)
  Z2-Z3      23   6.00  0.00383      261  ERROR
  Z2-Z4       8   5.00  0.00160      625  OK (< 1/500)
  Z3-Z4      31   7.81  0.00397      252  ERROR

  Hallazgos del auditor: 4 (2 ERROR, 2 WARNING)
   - Distorsion angular 0.00267 > 1/500 entre Z1 y Z2 — posible dano no-estructural (EN 1997-1 Annex H)
   - Distorsion angular 0.00325 > 1/500 entre Z1 y Z3 — posible dano no-estructural (EN 1997-1 Annex H)
   - Distorsion angular 0.00383 > 1/300 entre Z2 y Z3 — dano estructural probable (EN 1997-1 Annex H)
   - Distorsion angular 0.00397 > 1/300 entre Z3 y Z4 — dano estructural probable (EN 1997-1 Annex H)

La tabla de μ es una simplificación de la figura de Bjerrum (cinco columnas de H/B); para un informe conviene leer la curva original. Los límites 1/500 y 1/300 son los orientativos del Anexo H para pórticos: estructuras de fábrica o con acabados frágiles piden menos.
```

</details>

#### De los ensayos de campo a parámetros: N_60, C_N, φ' de Hatanaka-Uchida, E_s de Bowles, q_c ↔ N y S_u del cono

<details><summary>Salida real de <code>python examples/correlations_spt_cpt_n60_overburden_phi_hatanaka_es_bowles_su_from_qc_field_table.py</code></summary>

```text
Sondeo: γ = 18.5 kN/m³, nivel freático a 2.0 m, martillo con ER = 75 %

  z [m] suelo N campo σ′_v [kPa]   N_60   C_N (N_1)_60  φ′ [°] E_s [MPa] q_c CPT [MPa] q_c de N [MPa] N de q_c S_u [kPa]
    1.5  sand       8       27.8   10.0  1.90     19.0    37.1      12.0           3.2            5.0      6.4       nan
    3.0  sand      14       45.7   17.5  1.48     25.9    40.0      15.8           6.1            8.8     12.2       nan
    6.0  sand      22       71.8   27.5  1.18     32.5    42.4      20.8          10.5           13.8     21.0       nan
    9.0  sand      31       97.8   38.8  1.01     39.2    44.6      26.4          15.8           19.4     31.6       nan
   12.0  clay      27      123.9   33.8  0.90     30.3     nan      15.5           2.4            6.8     12.0     145.2

  C_N = √(100/σ'_v) acotado a 2: a 1,5 m (σ'_v = 28 kPa) multiplica N por 1,9; a 12 m lo divide. φ' de Hatanaka-Uchida solo vale en arenas; en la arcilla de 12 m el dato útil es S_u del cono (N_k = 15 es un valor medio, 10–20 según la arcilla).
  q_c ≈ 0,5·N_60 en arena es una correlación de orden de magnitud (k varía 0,3–0,7 con el tamaño de grano): aquí el CPT real queda en 0,32–0,41·N_60, por debajo del 0,5 de la correlación (arena fina o limosa), y en la arcilla la relación no aplica.

Estas correlaciones sirven para el anteproyecto y para contrastar un ensayo con otro; los parámetros de proyecto salen del laboratorio o de ensayos in situ interpretados con su propia sobrecarga.
```

</details>

#### Catálogo de estratigrafías tipo (Santiago, Bogotá, Lima, Andes) y resistencia de suelos no saturados con van Genuchten y Bishop

<details><summary>Salida real de <code>python examples/stratigraphy_catalog_latin_america_profiles_and_unsaturated_van_genuchten_bishop_suction.py</code></summary>

```text
Perfiles del catálogo: santiago_grava, bogota_lacustre, lima_grava, andes_volcanico

  santiago_grava:
    estrato                        z [m] γ [kN/m³] φ′ [°] c′ [kPa] E_s [MPa]  N_60
    Relleno                      0.0–2.0      17.0     28        0        15     8
    Grava 1a depositacion        2.0–8.0      22.0     42        0       120    50
    Grava 2a depositacion       8.0–20.0      23.0     45        5       200    60

  bogota_lacustre:
    estrato                        z [m] γ [kN/m³] φ′ [°] c′ [kPa] E_s [MPa]  N_60
    Costra desecada              0.0–3.0      16.0      0       30         8     4
    Arcilla blanda              3.0–25.0      13.0      0       25         4     2
    Arcilla preconsolidada     25.0–50.0      16.0      0       80        20     8

  lima_grava:
    estrato                        z [m] γ [kN/m³] φ′ [°] c′ [kPa] E_s [MPa]  N_60
    Suelo superficial            0.0–1.5      17.0     30        5        20    10
    Grava aluvial               1.5–30.0      21.0     40        0       150    50

  andes_volcanico:
    estrato                        z [m] γ [kN/m³] φ′ [°] c′ [kPa] E_s [MPa]  N_60
    Ceniza volcanica             0.0–5.0      14.0     32       10        25    12
    Toba consolidada            5.0–20.0      19.0     38       50       100    40

Zapata a 2 m en Bogotá cae en «Costra desecada» (φ' = 0, c = 30 kPa): q_ult no drenado ≈ (π + 2)·c_u·1,2 + γ·D = 217 kPa para zapata cuadrada; la arcilla blanda de debajo (c_u = 25 kPa, E_s = 4 MPa, 22 m) es la que manda en el asiento.

Relleno limo-arenoso compactado: van Genuchten θ_r = 0.06, θ_s = 0.42, α = 0.8 1/m, n = 1.8 (m = 1 − 1/n = 0.444); c' = 5 kPa, φ' = 32°, σ = 60 kPa, u_a = 0
   ψ [m] u_w [kPa]      θ  S_e = χ χ·(u_a − u_w) [kPa]  τ [kPa] τ/τ_sat
     0.0      -0.0  0.420    1.000                 0.0     42.5    1.00
     0.2      -2.0  0.414    0.984                 1.9     43.7    1.03
     0.5      -4.9  0.393    0.925                 4.5     45.3    1.07
     1.0      -9.8  0.347    0.796                 7.8     47.4    1.11
     2.0     -19.6  0.271    0.586                11.5     49.7    1.17
     5.0     -49.1  0.175    0.318                15.6     52.3    1.23
    10.0     -98.1  0.128    0.188                18.4     54.0    1.27

Con 2 m de succión la resistencia sube un 17 % y con 10 m un 27 %: χ cae con la succión pero en este rango (n = 1,8) el producto χ·s sigue creciendo; con n mayor (arenas uniformes) χ cae antes y el producto tiene máximo. Esa resistencia desaparece al saturarse el relleno (lluvia, rotura de una conducción): no se cuenta en proyecto salvo que se garantice el drenaje.
```

</details>

### 4. Empujes, muros y excavaciones

#### Muro de gaviones de 5 m (ejemplo de Hanif, DA1-a, no drenado): hundimiento, deslizamiento, vuelco, cursos y círculo global

<details><summary>Salida real de <code>python examples/gabion_wall_hanif_example_da1a_undrained_uls_1_2_3_internal_courses_and_global_circle.py</code></summary>

```text
Muro H = 5 m, B = 3.0 m; K_a = (1 − sin 34°)/(1 + sin 34°) = 0.283 (ejemplo 0,28); W = 230 kN/m (230); M_estab = 431.2 kN·m/m
Empuje activo característico S_A = ½·K_a·γ'·H² + K_a·q·H = 60.7 kN/m (γ' = γ − γ_w en no drenado); q_f = 5,14·c_u = 514 kPa
Factores parciales DA1a: {'gG': 1.35, 'gQ': 1.5, 'gphi': 1.0, 'gcu': 1.0, 'gRh': 1.0, 'gRb': 1.0}

  verificación                         E_d       R_d FS = R_d/E_d unidades  ok   ejemplo Hanif
  ULS-1 Capacidad portante           356.4    1334.6         3.74     kN/m  True  3,3 (con B completa)
  ULS-2 Deslizamiento                 68.0     185.8         2.73     kN/m  True  3,08
  ULS-3 Vuelco                       113.3     533.2         4.71   kN*m/m  True  3,83

Estabilidad interna (deslizamiento de cada curso sobre el inferior, ULS-6):
  ULS-6 Curso 1 (deslizamiento)    H =    7.8 kN/m  R_d =   20.9 kN/m  FS =  2.69  ok
  ULS-6 Curso 2 (deslizamiento)    H =   18.5 kN/m  R_d =   52.4 kN/m  FS =  2.83  ok
  ULS-6 Curso 3 (deslizamiento)    H =   32.1 kN/m  R_d =   94.2 kN/m  FS =  2.94  ok
  ULS-6 Curso 4 (deslizamiento)    H =   48.6 kN/m  R_d =  146.6 kN/m  FS =  3.02  ok
  ULS-6 Curso 5 (deslizamiento)    H =   68.0 kN/m  R_d =  209.4 kN/m  FS =  3.08  ok

Círculo global no drenado (r = 7.0 m, arco 13.4 m, bloque 372 kN/m con brazo 1.8 m): M_R = c_u·L_a·r = 9407, M_A = 670 kN·m/m → FS = 14.03
`verify_full` devuelve 9 comprobaciones (3 externas + 5 cursos + 1 global).

W, K_a y q_f coinciden con el ejemplo; los FS no son comparables uno a uno (3,7/2,7/4,7 frente a 3,3/3,08/3,83) porque el paquete aplica los factores parciales DA1-a a las acciones (γ_G = 1,35) y usa B' = B − 2e en el hundimiento, mientras el ejemplo compara valores característicos con B completa. Los datos del círculo global son de entrada (radio, arco, peso, brazo): el paquete no busca el círculo crítico; para eso está `slipcircle`.
```

</details>

#### El mismo muro por DA1-a, DA1-b y DA2, drenado y no drenado, y cuántos cursos hacen falta según la altura

<details><summary>Salida real de <code>python examples/gabion_wall_design_approaches_da1a_da1b_da2_drained_vs_undrained_and_height_sweep.py</code></summary>

```text
Factores parciales por enfoque de diseño (EN 1997-1 Anexo A, muros):
  DA1a  γ_G = 1.35, γ_Q = 1.50, γ_φ = 1.00, γ_cu = 1.00, γ_Rh = 1.00, γ_Rb = 1.00
  DA1b  γ_G = 1.00, γ_Q = 1.30, γ_φ = 1.00, γ_cu = 1.40, γ_Rh = 1.00, γ_Rb = 1.25
  DA2   γ_G = 1.35, γ_Q = 1.50, γ_φ = 1.00, γ_cu = 1.00, γ_Rh = 1.10, γ_Rb = 1.00

Muro de 5 cursos (H = 5 m, B = 3 m): FS = R_d/E_d por verificación
  enfoque  condición   S_A [kN/m] ULS-1 hund. ULS-2 desl. ULS-3 vuelco
  DA1a     no drenada        60.7        3.74        2.73         4.71
  DA1a     drenada           95.4       11.49        2.42         3.32
  DA1b     no drenada        60.7        2.89        2.64         5.08
  DA1b     drenada           95.4       12.40        2.42         3.59
  DA2      no drenada        60.7        3.74        2.48         4.71
  DA2      drenada           95.4       11.49        2.20         3.32

Cursos necesarios según la altura (DA1-a, no drenado): se quitan cursos por arriba
  H [m]                 anchos [m] W [kN/m]  ULS-1  ULS-2  ULS-3 curso crítico ULS-6  gobierna
      5  (1.0, 1.5, 2.0, 2.5, 3.0)      230   3.74   2.73   4.71 ULS-6 Curso 1 FS 2.69  ULS-2
      4       (1.5, 2.0, 2.5, 3.0)      207   4.20   3.83   6.89 ULS-6 Curso 4 FS 3.88  ULS-2
      3            (2.0, 2.5, 3.0)      172   5.25   5.79  10.73 ULS-6 Curso 3 FS 4.90  ULS-1
      2                 (2.5, 3.0)      126   7.63  10.06  18.82 ULS-6 Curso 2 FS 6.24  ULS-1

En las dos condiciones gobierna el deslizamiento (FS 2,2–2,7). En drenado el empuje es un 57 % mayor (γ en vez de γ − γ_w) y el deslizamiento baja a 2,4 (fricción N·tan φ'), mientras el hundimiento se dispara con N_q y N_γ de φ' = 34°. DA1-b castiga el hundimiento no drenado (c_u/1,4 y γ_Rb = 1,25: de 3,74 a 2,89) y DA2 el deslizamiento (γ_Rh = 1,1): hay que comprobar las dos combinaciones de DA1, no elegir una.
```

</details>

#### Empujes de Rankine sobre un muro en voladizo de 9,65 m con dos estratos y sobrecargas (fichas W00664/W00677): 268 kN/m y fuerza deslizante DA2

<details><summary>Salida real de <code>python examples/earth_pressure_rankine_multilayer_cantilever_wall_w00664_thrusts_and_da2_sliding_force.py</code></summary>

```text
K_a1 = tan²(45 − 15) = 0.33333 (= 1/3), K_a2 = tan²(29°) = 0.30726; K_p1 = 3.000 = 1/K_a1

  componente                                                     E [kN/m] brazo sobre base muro [m] tipo
  E_a1 = ½·K_a1·γ1·H1²  (triangular SOIL1)                         117.00                      4.65    G
  E_a2 = ½·K_a2·γ2·H2²  (triangular SOIL2)                          21.58                      0.88    G
  E_2' = K_a2·γ1·H1·H2  (rectangular, peso de SOIL1 sobre SOIL2)    95.27                      1.32    G
  E_S1 = K_a1·q·H1                                                  20.00                      5.65    Q
  E_S2 = K_a2·q·H2                                                   8.14                      1.32    Q
  E_s = 0,6·S (carga lineal, H ≥ 3a)                                 6.00                      6.90    Q
  Σ                                                                267.99   (ficha W00664: 267,75 con K_a1 = 0,333)

Fuerza deslizante de diseño DA2: γ_G·E_perm + γ_Q·E_var = 1.35·233.84 + 1.5·34.14 = 366.90 kN/m (ficha W00677: 366,58)
Brazo de la carga lineal: H_total − 1,17·a = 7.895 m desde la base de la zapata (ficha 7,90)

Errata documentada: la ficha declara «q_k = 200 kPa»; con ese valor E_S1 = K_a·q·H1 = 400 kN/m, más que todo el empuje del suelo. Sus propios 19,98 y 8,14 kN/m solo salen con q = 10 kPa: los 200 kPa son la presión admisible del terreno (q_Rd = 200/1,4 = 142,9 kPa en su comprobación de hundimiento).

Coeficiente en reposo de Jaky con sobreconsolidación (K_0 = (1 − sin φ')·OCR^sin φ') para SOIL1:
  OCR = 1: K_0 = 0.500  (K_a = 0.333, K_p = 3.000)
  OCR = 2: K_0 = 0.707  (K_a = 0.333, K_p = 3.000)
  OCR = 4: K_0 = 1.000  (K_a = 0.333, K_p = 3.000)
Un muro de sótano que no puede desplazarse recibe K_0 (hasta 1,5·K_a si OCR = 4), no K_a: Rankine activo exige que el muro ceda.
```

</details>

#### Empuje sísmico de Mononobe-Okabe (ficha W00704: K_ae = 0,471), Coulomb estático y auditoría de vuelco, deslizamiento y presiones

<details><summary>Salida real de <code>python examples/retaining_wall_mononobe_okabe_w00704_kae_0471_coulomb_ka_and_asd_safety_audit.py</code></summary>

```text
φ_d = atan(tan 36°/1,25) = 30.17°, δ_d = 16.23°; Coulomb: K_a = 0.2982 (ficha 0,298), P_a = ½·K_a·γ·H² = 96.6 kN/m (96,6)

   k_h   k_v  ψ [°]   K_ae ΔK = K_ae − K_a E_d = ½·K_ae·γ·H²·(1 ∓ k_v) [kN/m] ΔP_ae [kN/m] h_e [m]
   0.0   0.0   0.00 0.2982          0.0000                               96.6          0.0    2.00
   0.1   0.0   5.71 0.3649          0.0667                              118.2         21.6    2.18
   0.2   0.0  11.31 0.4495          0.1512                              145.6         49.0    2.34
   0.2   0.1  12.53 0.4715          0.1732                              137.5         40.9    2.30
   0.2  -0.1  10.30 0.4325          0.1342                              154.1         57.5    2.37
   0.3   0.0  16.70 0.5609          0.2626                              181.7         85.1    2.47
  Convención: ψ = atan(k_h/(1 − k_v)); la fila k_v = −0,1 es la rama «1 + k_v» de la ficha W00678 (K = 0,433; imprime 0,446 por errata, su propio E_d = 154,7 implica 0,434).
  El incremento sísmico ΔP_ae se aplica a H/2 (EC8 Anexo E) y el estático a H/3: la resultante sube a h_e.

Auditoría estático: muro W = 304 kN/m (x_cg = 1.6 m, B = 3.5 m), P_h = 92.8, P_v = 27.0 kN/m
  vuelco FS = 3.13 (ok ≥ 2,0); deslizamiento FS = 1.96 (ok ≥ 1,5); e = 0.556 m (< B/6), q_máx = 184 kPa (ok ≤ 250) → COMPLETAMENTE SEGURO
Auditoría sísmico k_h = 0,2, k_v = 0,1: muro W = 304 kN/m (x_cg = 1.6 m, B = 3.5 m), P_h = 132.0, P_v = 38.4 kN/m
  vuelco FS = 2.35 (ok ≥ 2,0); deslizamiento FS = 1.43 (NO ≥ 1,5); e = 0.708 m (> B/6, base parcialmente despegada), q_máx = 219 kPa (ok ≤ 250) → INSUFICIENTE SEGURIDAD

El sismo sube el empuje un 42 % (K_ae/K_a = 1,58 menos el factor 1 − k_v) y eleva la resultante; el muro pasa en estático y se queda sin margen de deslizamiento en sísmico: en EC8 los FS clásicos se sustituyen por factores parciales, pero la lectura es la misma.
```

</details>

#### Fondo de una excavación en arcilla blanda (Terzaghi-Peck): número de estabilidad según la profundidad y qué significa el FS de flotación

<details><summary>Salida real de <code>python examples/excavation_basal_heave_terzaghi_soft_clay_depth_sweep_and_uplift_semantics.py</code></summary>

```text
Arcilla c_u = 40 kPa, γ = 18 kN/m³, sobrecarga 10 kPa, excavación 5 × 10 m (FS mínimo 1,5)

  H [m] N_b = (γH + q)/c_u FS fondo = 5,14·c_u/(γH + q) Skempton N_c(H/B, B/L) FS con N_c Skempton  veredicto
    2.0               1.15                         4.47                   5.94                5.17  ok
    4.0               2.05                         2.51                   6.38                3.11  ok
    6.0               2.95                         1.74                   6.82                2.31  ok
    8.0               3.85                         1.34                   7.26                1.89  NO
   10.0               4.75                         1.08                   7.70                1.62  NO
   12.0               5.65                         0.91                   8.14                1.44  NO

  Profundidad máxima con FS = 1,5 y N_c = 5,14: H = (5,14·c_u/1,5 − q)/γ = 7.06 m; con N_c de Skempton (5·(1 + 0,2·B/L)·(1 + 0,2·H/B) ≤ 7,5·(1 + 0,2·B/L)) se llega más hondo.

Flotación: el paquete calcula FS_uplift = γ·H/(γ_w·h_w) con h_w = H − z_NF
  H = 6 m, NF a 2 m → h_w = 4 m: FS_uplift (paquete) = 2.75; con un tapón de arcilla de t = 3 m bajo el fondo y acuífero confinado, FS real = γ·t/(γ_w·(h_w + t)) = 0.79
  H = 6 m, NF a 4 m → h_w = 2 m: FS_uplift (paquete) = 5.50; con un tapón de arcilla de t = 3 m bajo el fondo y acuífero confinado, FS real = γ·t/(γ_w·(h_w + t)) = 1.10
  H = 10 m, NF a 2 m → h_w = 8 m: FS_uplift (paquete) = 2.29; con un tapón de arcilla de t = 3 m bajo el fondo y acuífero confinado, FS real = γ·t/(γ_w·(h_w + t)) = 0.50
  El valor del paquete compara el peso de la columna EXCAVADA con la presión del agua: es un indicador de que hay agua por encima del fondo, no el equilibrio del tapón. Para el tapón hace falta su espesor y la carga piezométrica del acuífero inferior; el paquete no los tiene como entrada.

Con c_u = 40 kPa la excavación no pasa de unos 7 m con FS = 1,5 (N_c = 5,14); más allá hacen falta pantallas empotradas bajo el fondo, mejora del terreno o rebajar el nivel freático.
```

</details>

### 5. Licuefacción, respuesta de sitio y SSI

#### Licuefacción por SPT (Boulanger e Idriss 2014) en un perfil con nivel freático: FS capa a capa, capas sin ensayo declaradas y la vía legacy igualada

<details><summary>Salida real de <code>python examples/liquefaction_boulanger_idriss_2014_spt_profile_fs_by_layer_and_legacy_path_now_identical.py</code></summary>

```text
M_w = 7.0, a_máx = 0.3 g; nivel freático a 1.5 m
  estado: EVALUADO PARCIALMENTE (Boulanger & Idriss 2014): 5 de 6 capas. 1 sin N1_60cs y por tanto SIN evaluar — la ausencia de estrato licuable NO esta establecida para el perfil completo.

  z [m]    σ_v   σ′_v (N₁)₆₀cs    r_d    CSR  CRR₇.₅    MSF    K_σ     FS  estado
    2.0   36.8   31.8        9  0.987  0.222   0.111  1.030  1.100   0.57  LICUABLE
    4.0   75.8   51.2       12  0.961  0.277   0.132  1.041  1.066   0.53  LICUABLE
    6.0  114.8   70.6        —      —      —       —      —      —      —  NO EVALUADA (sin N1_60cs)
    8.0  153.8   90.0       16  0.898  0.299   0.165  1.061  1.012   0.59  LICUABLE
   11.0  212.2  119.1       22  0.844  0.294   0.233  1.102  0.975   0.85  LICUABLE
   15.0  290.2  157.8       30  0.771  0.277   0.485  1.176  0.908   1.87  no licuable

  FS mínimo = 0.53; estrato licuable: True; capas sin evaluar: 1

Vía simple `evaluate_liquefaction` (la que usa /api/geo/liquefaction) frente a `evaluate_bi2014`, mismas capas:
  z [m] FS legacy  FS B&I diferencia   (hasta la 1.0: +13 % a 5 m, +29 % a 10 m)
    2.0    0.5677  0.5677    0.0e+00
    4.0    0.5309  0.5309    1.1e-16
    8.0    0.5916  0.5916    0.0e+00
   11.0    0.8528  0.8528    0.0e+00
   15.0    1.8705  1.8705    0.0e+00

Las cuatro capas evaluadas hasta 11 m licúan (FS 0,53–0,85) y solo la arena densa de 15 m queda a salvo; la de 6 m no se evalúa porque no trae N, y el informe lo dice en vez de rellenar 15. `is_safe` de la vía simple exige FS ≥ 1,2 (margen de proyecto); `is_liquefiable` del módulo B&I compara con 1,0.
```

</details>

#### Sensibilidad del FS: magnitud (MSF), PGA, profundidad (r_d y K_σ) y contenido de finos

<details><summary>Salida real de <code>python examples/liquefaction_sensitivity_mw_pga_rd_msf_k_sigma_and_fines_content_correction.py</code></summary>

```text
Capa de referencia: z = 6.0 m, σ_v = 110.0, σ'_v = 66.0 kPa, (N₁)₆₀cs = 14

   M_w a = 0.15 g a = 0.20 g a = 0.30 g a = 0.40 g      MSF
   5.5       1.35       1.01       0.67       0.51    1.247
   6.0       1.24       0.93       0.62       0.47    1.173
   6.5       1.15       0.87       0.58       0.43    1.108
   7.0       1.07       0.80       0.54       0.40    1.051
   7.5       1.00       0.75       0.50       0.38    1.000
   8.0       0.94       0.70       0.47       0.35    0.955
  FS escala con 1/a_máx y con MSF: un M 6 y 0,3 g equivale en demanda a un M 7,5 y 0,26 g (0,3/1,173).

  z [m] σ′_v [kPa]    r_d    K_σ CSR (0,3 g, M 7)     FS
    2.0       31.8  0.987  1.100            0.222   0.77
    4.0       51.2  0.961  1.071            0.277   0.60
    6.0       70.6  0.931  1.037            0.295   0.55
    8.0       90.0  0.898  1.011            0.299   0.53
   12.0      128.7  0.826  0.973            0.290   0.52
   16.0      167.5  0.754  0.945            0.272   0.54
   20.0      206.3  0.687  0.923            0.252   0.57
  Con el mismo N, la capa somera tiene K_σ > 1 y σ_v/σ'_v alto (CSR alto); en profundidad r_d y K_σ bajan y CSR también: el FS mínimo suele caer entre 4 y 10 m.

  FC [%]  Δ(N₁)₆₀ (N₁)₆₀cs  CRR₇.₅ FS (0,3 g, M 7)
       0     0.00    14.00   0.148            0.54
       5     0.00    14.00   0.148            0.54
      15     3.26    17.26   0.176            0.65
      25     5.07    19.07   0.195            0.73
      35     5.51    19.51   0.200            0.76
      50     5.61    19.61   0.201            0.76

  Comprobaciones cerradas: MSF(7,5) = 1.00000; K_σ(100 kPa) = 1.00000; r_d(6 m, 7,5) = 0.9491; CRR(20) = 0.2059 (paper 0,2059)
La corrección por finos sube el FS un 40 % (de 0,54 a 0,76 con 35 % de finos) y satura a partir del 35 %: el contenido de finos de laboratorio vale tanto como el golpeo. La curva CRR satura en (N₁)₆₀cs = 37 (el paper dice 37,5).
```

</details>

#### Respuesta de sitio 1D: estrato blando sobre roca, función de transferencia, f₀ = V_s/4H, amplificación y espectro en superficie

<details><summary>Salida real de <code>python examples/site_response_1d_soft_clay_over_bedrock_transfer_function_f0_amplification_and_surface_spectrum.py</code></summary>

```text
Estrato 30 m, V_s = 200 m/s, ξ = 5 %: f₀ = V_s/(4H) = 1.667 Hz (T₀ = 0.60 s); |H(f₀)| teórico ≈ 2/(πξ) = 12.7

Función de transferencia evaluada a mano: pico |H| = 12.73 en f = 1.666 Hz; |H| en 3·f₀ = 4.21, en 5·f₀ = 1.98; |H(0,5 Hz)| = 1.12

Ruido blanco filtrado (PGA roca 0.86 m/s²): PGA superficie 1.60 m/s², amplificación 1.85, f_pico = 1.650 Hz (-1.0 % frente a f₀), γ_máx ≈ 0.202 %
Seno en f₀ (0,5 m/s²): amplificación 12.72, la cota 2/(πξ) de la capa sobre base rígida; con ruido de banda ancha la amplificación de la PGA es mucho menor (1,8) porque solo la banda en torno a f₀ se amplifica

Espectro de respuesta en superficie (ξ = 5 %) del caso de ruido:
  T=0.10s T=0.20s T=0.30s T=0.50s T=0.60s T=0.80s T=1.00s T=2.00s
   0.313g  0.612g  0.259g  0.577g  0.787g  0.274g  0.148g  0.057g

Dos capas (arcilla 10 m V_s 150 + arena 20 m V_s 300): f_pico = 3.750 Hz frente a 1/(4·ΣH/V_s) = 1.875 Hz; amplificación 17.53; γ_máx por capa [0.246, 0.222] %

El producto de 1/cos(k·h) por capa es exacto para la capa única sobre base rígida, pero con dos capas el pico sale al doble del periodo esperado del perfil y la amplificación se dispara: faltan los cocientes de impedancia entre capas (Kramer cap. 7). Para un estudio de sitio multicapa hace falta la matriz de transferencia completa o un análisis no lineal con degradación G/G_máx; aquí la capa única es lo que se puede usar.
```

</details>

#### Muelles estáticos de Gazetas para una zapata 4 × 2 m: seis rigideces en forma cerrada, asiento y giro, y la asimetría de balanceo de la fuente

<details><summary>Salida real de <code>python examples/ssi_gazetas_static_springs_footing_4x2_closed_form_settlement_rotation_and_square_asymmetry.py</code></summary>

```text
Zapata 4.0 × 2.0 m, G = ρV_s² = 80 MPa, ν = 0.35; I_x = 2.667 m⁴, I_y = 10.667 m⁴

  rigidez         a mano        paquete    unidad
  K_z          810185.6       810185.6      kN/m
  K_x          656865.3       656865.3      kN/m
  K_y          576865.3       576865.3      kN/m
  K_rx         809387.6       809387.6  kN·m/rad
  K_ry        2418098.2      2418098.2  kN·m/rad
  K_t         1480642.1      1480642.1  kN·m/rad

Apoyo elástico con P = 1620,4 kN, M_x = 400, M_y = 900 kN·m: asiento P/K_z = 2.000 mm; giros M/K_r = 0.494 y 0.372 mrad; unidades declaradas: kN/m, kNm/rad
  Giro × semilado: δ_borde ≈ θ_x·B/2 = 0.494 mm y θ_y·L/2 = 0.744 mm, a sumar o restar al asiento uniforme.

Zapata cuadrada: K_x = K_y exacto y K_rx/K_ry = (2,4 + 0,5)/3,0 según los coeficientes publicados
  B = L = 1.5 m: K_x/K_y = 1.000000; K_rx/K_ry = 0.9667 (= 0.9667, un 3,3 % de asimetría de la fuente)
  B = L = 3.0 m: K_x/K_y = 1.000000; K_rx/K_ry = 0.9667 (= 0.9667, un 3,3 % de asimetría de la fuente)
  B = L = 6.0 m: K_x/K_y = 1.000000; K_rx/K_ry = 0.9667 (= 0.9667, un 3,3 % de asimetría de la fuente)

Estas son rigideces estáticas de semiespacio homogéneo sin empotramiento: con la zapata enterrada Gazetas multiplica por factores de empotramiento (no incluidos) y con estratos finos hay que usar el V_s medio del bulbo. En la corrección K_x − K_y el paquete emplea la longitud total L donde Gazetas escribe la semilongitud; el término es del orden del 3 % de K y está pendiente de contrastar.
```

</details>

#### Impedancias dinámicas de una zapata 5 × 3 m: rigideces con la frecuencia, radiación de Lysmer y amortiguamiento material de 1 a 20 Hz

<details><summary>Salida real de <code>python examples/ssi_dynamic_impedances_radiation_damping_frequency_sweep_and_material_damping_dashpots.py</code></summary>

```text
Zapata 5.0 × 3.0 m, V_s = 180.0 m/s, ρ = 1850.0 kg/m³, ν = 0.35; V_La = 3,4·V_s/(π(1 − ν)) = 299.7 m/s; ξ_material = 5%

Rigideces estáticas: K_z = 820,655 kN/m, K_x = 657,424, K_y = 597,484, K_rx = 1,737,776 kN·m/rad, K_ry = 3,947,657, K_t = 2,846,669
Radiación (no depende de f): C_z = ρ·V_La·A = 8,317 kN·s/m, C_x = ρ·V_s·A = 4,995, C_rx = ρ·V_La·I_x = 6,238 kN·m·s/rad, C_ry = 17,326, C_t = 14,152

  f [Hz]    a_0 K_z,din/K_z K_rx,din/K_rx K_ry,din/K_ry C_z total [kN·s/m]  ξ_eq,z   C_rx total  ξ_eq,rx C_mat/C_rad (z)
     1.0  0.052       1.000         0.992         0.990             21,378    0.08       33,895     0.06           1.570
     2.0  0.105       1.000         0.984         0.979             14,847    0.11       20,066     0.07           0.785
     4.0  0.209       1.000         0.969         0.958             11,582    0.18       13,152     0.10           0.393
     6.0  0.314       1.000         0.953         0.937             10,494    0.24       10,847     0.12           0.262
     8.0  0.419       1.000         0.937         0.916              9,949    0.30        9,695     0.15           0.196
    12.0  0.628       1.000         0.906         0.874              9,405    0.43        8,542     0.20           0.131
    16.0  0.838       1.000         0.874         0.832              9,133    0.56        7,966     0.26           0.098
    20.0  1.047       0.998         0.843         0.791              8,970    0.69        7,620     0.33           0.079

A 1 Hz (periodos de edificio) manda el amortiguamiento material, 1,6 veces la radiación, porque C_mat = 2Kξ/ω crece al bajar ω; a 2 Hz van parejos y desde 4 Hz domina la radiación. El ξ_eq vertical pasa del 50 % hacia 15 Hz: por eso las cimentaciones superficiales en suelo firme apenas vibran verticalmente a frecuencias de maquinaria.
Los factores k(a_0) y los dashpots de radiación son los de la tabla de Gazetas para cimentación superficial SIN los coeficientes c̄(a_0) de baja frecuencia (que reducen el amortiguamiento de balanceo a a_0 < 1): del lado optimista en rocking a frecuencias bajas.
```

</details>

### 6. Túneles, durabilidad, materiales y datos

#### Convergencia-confinamiento de un túnel circular: curva del terreno, curva del sostenimiento, equilibrio estable frente a colapso y muelles de Winkler

<details><summary>Salida real de <code>python examples/tunnel_convergence_confinement_grc_scc_equilibrium_stable_vs_collapse_and_winkler_springs.py</code></summary>

```text
=== Túnel en roca competente (R₀ = 3 m, P₀ = 500 kPa, anillo 200 mm) ===
  k_p = 3.00, σ_cm = 2c·cos φ/(1 − sin φ) = 519.6 kPa → P_cr = (2P₀ − σ_cm)/(k_p + 1) = 120.1 kPa (paquete 120.1)
  Convergencia libre máxima u(P_i = 0) = 21.1 mm (0.70 % de R₀); radio plástico a P_i = 0: R_p = 3.63 m (1.21·R₀)
  Anillo: K_s = E·t/(R₀²(1 − ν²)) = 694.4 kPa/mm, activado en u = 6.3 mm
  Equilibrio: STABLE — p_eq = 284.2 kPa (56.8 % de P₀) en u = 6.74 mm
  Winkler elastoplástico: k = E/(R₀(1 + ν)) = 32,000 kN/m³, p_y = σ_cm = 519.6 kPa, u_y = 16.24 mm
  Curva de reacción del terreno (P_i, u):
    (500 kPa, 0.00 mm)  (415 kPa, 2.65 mm)  (331 kPa, 5.30 mm)  (246 kPa, 7.94 mm)  (161 kPa, 10.59 mm)  (0 kPa, 21.11 mm)

=== Suelo blando (R₀ = 4 m, P₀ = 1200 kPa, E = 25 MPa, anillo 100 mm al 80 % de convergencia) ===
  k_p = 2.46, σ_cm = 2c·cos φ/(1 − sin φ) = 157.0 kPa → P_cr = (2P₀ − σ_cm)/(k_p + 1) = 647.5 kPa (paquete 647.5)
  Convergencia libre máxima u(P_i = 0) = 1856.3 mm (46.41 % de R₀); radio plástico a P_i = 0: R_p = 15.17 m (3.79·R₀)
  Anillo: K_s = E·t/(R₀²(1 − ν²)) = 32.6 kPa/mm, activado en u = 1485.1 mm
  Equilibrio: UNSTABLE_COLLAPSE — p_eq = 0.0 kPa (0.0 % de P₀) en u = 1856.32 mm
  Winkler elastoplástico: k = E/(R₀(1 + ν)) = 4,630 kN/m³, p_y = σ_cm = 157.0 kPa, u_y = 33.91 mm
  Curva de reacción del terreno (P_i, u):
    (1200 kPa, 0.00 mm)  (1015 kPa, 39.88 mm)  (800 kPa, 86.40 mm)  (585 kPa, 147.99 mm)  (400 kPa, 258.86 mm)  (0 kPa, 1856.32 mm)

Comprobación: desplazamiento al final de la rama elástica u(P_cr) = (1 + ν)/E·(P₀ − P_cr)·R₀ = 11.87 mm; el anillo de 200 mm toma el 57 % de P₀ porque llega tarde (30 %) y la roca ya ha relajado.
La rama plástica es la simplificada ((P₀ − P_cr)(R_p/R₀)² + (P_cr − P_i)) y no la de Hoek con (1 − 2ν): orden de magnitud para anteproyecto; el colapso se declara si la convergencia libre supera el 10 % de R₀, si el anillo no equilibra o si supera su tensión de aro (ε_y = 0,0015).
```

</details>

#### Cuándo y con qué espesor sostener: barrido de la convergencia previa a la instalación y del espesor del anillo

<details><summary>Salida real de <code>python examples/tunnel_support_installation_delay_and_liner_thickness_sweep_equilibrium_pressure.py</code></summary>

```text
R₀ = 4 m, P₀ = 800 kPa: P_cr = 408 kPa, convergencia libre 274.4 mm (6.86 % de R₀), R_p(P_i = 0) = 10.60 m

Anillo de 250 mm según el momento de instalación:
  conv. previa u_activación [mm] p_eq [kPa] p_eq/P₀ u_eq [mm] capacidad aro [kPa]  estado
           10%              27.4      472.3   0.590      28.4                2812  STABLE
           20%              54.9      300.1   0.375      55.5                2812  STABLE
           30%              82.3      204.6   0.256      82.7                2812  STABLE
           50%             137.2       97.7   0.122     137.4                2812  STABLE
           70%             192.1       43.6   0.055     192.2                2812  STABLE
           90%             246.9       11.6   0.015     247.0                2812  STABLE

Instalación al 30 % según el espesor del anillo:
  t [mm] K_s [kPa/mm] p_eq [kPa] u_eq [mm] capacidad aro [kPa]    uso  estado
     100        195.3      202.8      83.4                1125   0.18  STABLE
     150        293.0      203.8      83.0                1688   0.12  STABLE
     200        390.6      204.3      82.8                2250   0.09  STABLE
     250        488.3      204.6      82.7                2812   0.07  STABLE
     300        585.9      204.8      82.7                3375   0.06  STABLE
     400        781.2      205.1      82.6                4500   0.05  STABLE

Retrasar el anillo del 10 al 50 % de la convergencia baja la presión que recibe de 472 a 98 kPa a costa de 110 mm más de convergencia: es el principio del NATM. A partir de 100 mm el anillo es tan rígido frente al terreno (K_s ≫ pendiente de la curva de reacción) que p_eq apenas depende del espesor: el equilibrio lo fija el momento de instalación, y el uso de la capacidad de aro se queda por debajo de 0,2. Un anillo rígido instalado muy pronto en terreno peor puede superar su capacidad de aro (uso > 1) y el paquete lo marca como colapso aunque el terreno sea estable.
```

</details>

#### Vida útil del hormigón: iniciación por cloruros (Fick) según recubrimiento y difusividad, y frente de carbonatación según a/c, cenizas y humedad

<details><summary>Salida real de <code>python examples/durability_chloride_fick_time_to_corrosion_cover_sweep_and_carbonation_service_life.py</code></summary>

```text
Cloruros (ambiente marino, C_s = 0,8 %, C_crit = 0,4 % en peso de cemento): años hasta la iniciación según recubrimiento y difusividad
  recubr. [mm] D =  2.0 mm²/año D =  5.0 mm²/año D = 10.0 mm²/año D = 20.0 mm²/año
            30             494.6             197.8              98.9              49.5
            40             879.2             351.7             175.8              87.9
            50            1373.8             549.5             274.8             137.4
            60            1978.3             791.3             395.7             197.8
            70            2692.7            1077.1             538.5             269.3

  Perfil a t = 274.8 años (D = 10, recubrimiento 50 mm): C(0) = 0.800, C(25 mm) = 0.589, C(50 mm) = 0.400 (= umbral), C(100 mm) = 0.142 %
  Doblar el recubrimiento multiplica el tiempo por 4.0; con umbral 0,6 % en vez de 0,4 %: 1231.2 años; con C_crit ≥ C_s: inf

Carbonatación: K_c [mm/√año] y vida útil hasta un recubrimiento de 30 y 50 mm
   a/c % cenizas HR [%]    K_c d(50 años) [mm] t(30 mm) [años] t(50 mm) [años]
  0.45         0     65   3.15            22.3              91             252
  0.55         0     65   4.71            33.3              41             113
  0.65         0     65   6.57            46.5              21              58
  0.50        30     65   5.06            35.8              35              98
  0.50         0     40   2.56            18.1             137             380
  0.50         0     60   4.00            28.3              56             156
  0.50         0     85   2.00            14.1             226             627
  0.50         0     95   1.03             7.3             856            2377

Un hormigón a/c 0,65 carbonata el doble de deprisa que uno a/c 0,45 (K ∝ (a/c)²) y la humedad del 60 % es la peor; saturado (95 %) casi no avanza. Los coeficientes (K_ref = 4 mm/√año, D en mm²/año) son valores de referencia del modelo, no de un ensayo: para una obra hay que medir D_app y C_s en testigos o usar los de la clase de exposición de EN 206 / fib MC.
```

</details>

#### Hormigón confinado de Mander para el núcleo de un pilar: K, ε_cc, ε_cu, curva σ-ε y el límite sin confinar, listos para una sección de fibras

<details><summary>Salida real de <code>python examples/mander_confined_concrete_column_core_k_fcc_curve_and_unconfined_limit_for_etabs_fiber.py</code></summary>

```text
Núcleo 400 × 400 mm, f'c = 30 MPa, f_yh = 420 MPa, ε_su = 0,10, E_c = 5000√f'c = 27.4 GPa

  ρ_x = ρ_y s [mm]    k_e f_l [MPa]      K f′cc [MPa]    ε_cc    ε_cu     r σ(ε_cu)/f′cc
     0.0025     75  0.795      0.83  1.181       35.4  0.0038  0.0123  1.51         0.76
     0.0025    100  0.742      0.78  1.170       35.1  0.0037  0.0124  1.53         0.74
     0.0025    150  0.643      0.68  1.148       34.4  0.0035  0.0125  1.57         0.70
     0.0050     75  0.795      1.67  1.341       40.2  0.0054  0.0186  1.37         0.81
     0.0050    100  0.742      1.56  1.321       39.6  0.0052  0.0188  1.38         0.79
     0.0050    150  0.643      1.35  1.282       38.5  0.0048  0.0193  1.41         0.75
     0.0100     75  0.795      3.34  1.617       48.5  0.0082  0.0282  1.28         0.86
     0.0100    100  0.742      3.12  1.583       47.5  0.0078  0.0288  1.28         0.84
     0.0100    150  0.643      2.70  1.518       45.5  0.0072  0.0298  1.30         0.81
     0.0150     75  0.795      5.01  1.849       55.5  0.0105  0.0358  1.24         0.88
     0.0150    100  0.742      4.68  1.806       54.2  0.0101  0.0366  1.24         0.87
     0.0150    150  0.643      4.05  1.721       51.6  0.0092  0.0382  1.26         0.84
     0.0200     75  0.795      6.68  2.050       61.5  0.0125  0.0422  1.22         0.89
     0.0200    100  0.742      6.24  2.000       60.0  0.0120  0.0432  1.22         0.88
     0.0200    150  0.643      5.40  1.899       57.0  0.0110  0.0453  1.23         0.85

Caso ρ = 1 %, s = 100 mm: K = 1.5834 (a mano 1,584), f'cc = 47.5 MPa, ε_cc = 0.0078, ε_cu = 0.0288
  Curva σ-ε (ε, σ [MPa]) para la tabla de material no lineal:
    (0.0000, 0.0)  (0.0030, 40.5)  (0.0059, 47.0)  (0.0089, 47.4)  (0.0119, 46.5)  (0.0149, 45.2)  (0.0198, 43.1)  (0.0248, 41.3)  (0.0288, 40.0)

Límite sin confinar (ρ → 0): K = 1.0000, f'cc = 30.00 MPa, ε_cc = 0.0020, ε_cu = 0.0040; σ a 0,004 = 22.7 MPa (rama descendente, no cero)

Hasta la 1.0 el paquete daba K = 2,58 (f'cc = 77 MPa) por un «1 +» de más en la fórmula y una rama descendente casi vertical (r = 5/(K − 1)): un modelo así sobreestimaba la resistencia del pilar un 60 %. El k_e implementado omite el divisor (1 − ρ_cc) de Mander (efecto < 3 %) y promedia con f_l,mín en secciones rectangulares (lado seguro).
```

</details>

#### Un fichero AGS4 con dos sondeos → estratigrafía y guion de PLAXIS 2D, y la API REST consultada con TestClient

<details><summary>Salida real de <code>python examples/ags4_borehole_parse_plaxis_script_generation_and_rest_api_geo_endpoints_testclient.py</code></summary>

```text
C:\Users\jesus\AppData\Local\Temp\jmv\terzaghi\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
Proyecto «Paso inferior Avenida del Puerto» (GEO-2026-014), 2 sondeos, estado CALCULADO, unidades SI_m_kN_kPa_deg
  S-1: X = 431250, Y = 4582100, cota 4.2 m, profundidad 20.0 m; SPT N = 9 a 2.0 m, N = 12 a 4.0 m, N = 15 a 6.0 m, N = 4 a 9.0 m, N = 38 a 16.0 m
       0.0–  1.5 m  gravelly SAND → sand  γ = 19.5, c = 1.0, φ = 33.0, E = 35 MPa   «Made ground»
       1.5–  7.0 m  SAND   → sand  γ = 19.5, c = 1.0, φ = 33.0, E = 35 MPa   «Loose to medium dense fine SAND»
       7.0– 14.0 m  CLAY   → clay  γ = 17.5, c = 25.0, φ = 22.0, E = 15 MPa   «Soft grey silty CLAY»
      14.0– 20.0 m  SAND   → sand  γ = 19.5, c = 1.0, φ = 33.0, E = 35 MPa   «Dense SAND and gravel»
  S-2: X = 431310, Y = 4582140, cota 4.0 m, profundidad 18.0 m; SPT N = 14 a 3.0 m, N = 3 a 8.0 m, N = 45 a 15.0 m
       0.0–  6.5 m  SAND   → sand  γ = 19.5, c = 1.0, φ = 33.0, E = 35 MPa   «Medium dense SAND»
       6.5– 13.0 m  CLAY   → clay  γ = 17.5, c = 25.0, φ = 22.0, E = 15 MPa   «Soft CLAY»
      13.0– 18.0 m  GRAVEL → sand  γ = 19.5, c = 1.0, φ = 33.0, E = 35 MPa   «Dense GRAVEL»

Guion PLAXIS 2D: 82 líneas, 4 materiales, 2 sondeos, 7 capas. Primeras líneas útiles:
    # Connect to PLAXIS 2D Input Server
    s_i, g_i = new_server(host='localhost', port=10000)
    g_i.new()
    # Project: Paso inferior Avenida del Puerto (GEO-2026-014)
    
    # 1. Define Mohr-Coulomb soil materials
    # Material: Mat_gravelly_SAND (Made ground)
  Los parámetros de los materiales (γ, c, φ, E) son los por defecto por tipo arena/arcilla del lector, no los del informe: hay que sustituirlos antes de calcular.

API REST (TestClient, sin servidor), versión 1.1.0:
  GET /api/geo/health → 200 {'status': 'ok'}
  POST /gazetas-springs 4 × 2 m → K_z = 810,186 kN/m, K_rx = 809,388 kN·m/rad, G = 80 MPa
  POST /liquefaction (z = 6, N = 20, 0,3 g, M 7,5) → CSR = 0.241, CRR = 0.2059, MSF = 1.000, K_σ = 1.000, FS = 0.856, is_safe = False
  POST /py/matlock (z = 3, D = 0,8, s_u = 50) → 50 puntos, p_ult = 235.8 kN/m, y_máx = 640 mm
  POST /tunnel-winkler → P_cr = 120.1 kPa, equilibrio STABLE a 284.2 kPa, k_Winkler = 32,000 kN/m³
  POST /pile-group/lateral (s/D = 4, 3 filas) → η = 0.675; con rows = 0 → 422 (validación Pydantic)
  POST /bearing-capacity (W00675) → q_ult = 927.1 kPa, q_adm = 662.2 kPa: es la vía DEPRECADA (factores de forma sin publicar, +2,6 % frente a los 903,5 del Anexo D); la puerta EC7 no tiene endpoint todavía.

El lector AGS4 cubre PROJ/LOCA/GEOL/ISPT (no CPT ni laboratorio) y clasifica por la palabra CLAY en la descripción; el guion de PLAXIS necesita el servidor de Remote Scripting (puerto 10000) y la licencia correspondiente.
```

</details>

## Verificación

- Capacidad portante: los nueve valores publicados del ejemplo W00675 §4.3 (N_q, N_c, N_γ, s_q, s_c, s_γ y los tres términos; q_ult = 903,5 kPa a −0,004 %), la tabla de factores de Das y las tablas de las fichas W00675 y W00672 con sus erratas documentadas; la puerta drenada con φ = 0 coincide bit a bit con la cláusula no drenada D.3 (`tests/test_golden_bearing_fichas.py`, `test_golden_bearing_capacity_published.py`, `test_consolidacion_bearing_canonica.py`).
- Consolidación anclada a las fichas W00255 (T_v,90 = 0,848, 14,1 años, F(n) = 2,42, 0,575 años con drenes) y W00254 (U_h = 0,49 a los 8 meses); empujes de Rankine a W00664/W00677 (267,99 y 366,9 kN/m) y Mononobe-Okabe a W00704 (K_ae = 0,471) y W00678 (0,433, errata 0,446 documentada) en `test_golden_consolidation_fichas.py`, `test_golden_empujes_rankine_fichas.py`, `test_gabion_wall_safety.py`, `test_golden_mononobe_W00678.py`.
- Licuefacción: CRR, MSF, K_σ y r_d contra las ecuaciones numeradas de Boulanger e Idriss (2014) con desarrollo escrito (`test_golden_liquefaction_bi2014.py`); Gazetas contra la derivación cerrada de las seis rigideces y el asiento P/K_z = 2,000 mm (`test_golden_gazetas_ssi_settlement.py`); muro de gaviones contra el ejemplo de Hanif (`test_gabion_wall.py`).
- Correcciones de la 1.1.0 con test propio: K de Mander igual a la ec. 7 de la fuente (1,584 para el caso de referencia) y rama descendente de Popovics; la vía legacy de licuefacción coincide con B&I 2014 y la función de perfil es importable (`test_mander_published_confined_strength.py`, `test_liquefaction_legacy_matches_bi2014.py`).
- `tests/test_examples.py` ejecuta los 30 ejemplos como subprocesos en ubuntu y windows × Python 3.11–3.13; cada ejemplo imprime la comprobación a mano junto al número del paquete.

## Limitaciones

- `evaluate_bearing_ec7` no tiene nivel freático: usa un único γ en la sobrecarga y en el peso propio (pásale γ' si hay agua en la base, conservador) y no admite factores de profundidad d_q/d_c ni inclinación del terreno o de la base. La vía `evaluate_bearing` está deprecada (factores de forma sin publicar, ciega a e y H: hasta +41 % del lado inseguro) y es la que todavía sirve el endpoint `/api/geo/bearing-capacity`.
- Tres convenciones de p-multiplicadores conviven: `piles.group` (Brown 1988, depende de s/D), la tabla fija de `piles.mokwa_duncan` y la fórmula f_m = 0,64 + 0,36·s/D de `memos.pile_group_lateral`, que satura a 1 desde s/D = 1 y no reduce nada en los casos reales. La curva de arena de `integration.fastsap_pysprings.build_py_curve` no es la de Reese (sin referencia; da aproximadamente la mitad): muestrea `py_reese_sand` para los muelles. Los coeficientes cíclico (λ = 0,08) y dinámico (β = 0,15) de `piles.dynamic_py` son paramétricos, no de norma.
- `site_response.propagate_1d` multiplica 1/cos(k·h) por capa: exacto para una capa sobre base rígida, pero con dos capas el pico sale al doble del periodo del perfil y la amplificación se dispara (faltan los cocientes de impedancia); el módulo `wave_propagation_1d` del raíz es un duplicado más antiguo.
- `check_excavation` calcula el FS de flotación con la profundidad de excavación, no con el espesor del tapón ni la carga piezométrica del acuífero: es un indicador, no la comprobación. El levantamiento de fondo usa N_c = 5,14 sin los factores de forma y profundidad de Skempton (lado seguro).
- Gazetas: rigideces estáticas de semiespacio sin factores de empotramiento; en zapata cuadrada K_rx/K_ry = 0,967 por los coeficientes publicados (declarado, no corregido); la corrección K_x − K_y se aplica con la longitud total donde la fuente usa la semilongitud (término del orden del 3 %, pendiente de contrastar). Los dashpots de radiación de `ssi_springs` no llevan los coeficientes c̄(a_0) de baja frecuencia: amortiguamiento de balanceo optimista a a_0 < 1.
- `tunnels`: rama plástica simplificada (sin el término (1 − 2ν) de Hoek); cuando P_cr se acerca a P₀ la convergencia libre y el radio plástico crecen sin límite físico y solo el estado («colapso») tiene sentido. La tabla μ de Skempton-Bjerrum es una simplificación de la figura de Bjerrum; los coeficientes de durabilidad (K_ref = 4 mm/√año, D) son de referencia y no sustituyen a los testigos.
- Mander: k_e omite el divisor (1 − ρ_cc) de la fuente y la sección rectangular se trata con f_l,mín (lado seguro). El lector AGS4 cubre PROJ/LOCA/GEOL/ISPT y clasifica por la palabra CLAY; los parámetros del guion de PLAXIS son valores por defecto por tipo de suelo.

## Normas y referencias

- EN 1997-1:2004 Anexo A (factores parciales DA1/DA2), Anexo D (capacidad portante drenada y no drenada), Anexo H (asientos admisibles), §9 (empujes); EN 1998-5 Anexo E (Mononobe-Okabe); API RP 2A-WSD §6.4 (α, β); DNV-RP-C212 (monopilotes, como marco).
- Vesić (1973); Meyerhof (1963); Brinch Hansen (1970); Chen (1975); Das, *Principles of Foundation Engineering* (tablas de factores).
- Matlock (1970); Reese, Cox y Koop (1974); Brown, Morrison y Reese (1988); Mokwa y Duncan (2001).
- Terzaghi (1943); Barron (1948); Hansbo (1981); Carrillo (1942); Skempton y Bjerrum (1957); Bjerrum (1972); Skempton (1986); Hatanaka y Uchida (1996); Bowles (1997); Robertson y Wride (1998); van Genuchten (1980); Bishop (1959).
- Boulanger, R. W. e Idriss, I. M. (2014), *CPT and SPT Based Liquefaction Triggering Procedures*, UCD/CGM-14/01; Kramer (1996), *Geotechnical Earthquake Engineering*; Gazetas (1991), *Formulas and Charts for Impedances of Surface and Embedded Foundations*; NIST GCR 12-917-21.
- Duncan Fama (1993) y Hoek (convergencia-confinamiento); Mander, Priestley y Park (1988); EN 206 y fib Model Code (durabilidad, como marco); AGS4 v4.x; PLAXIS Remote Scripting.
- UPC, Máster en Ingeniería Estructural y de la Construcción: fichas W00254, W00255, W00664, W00672, W00675, W00676, W00677, W00678 y W00704; ejemplo de muro de gaviones de M. Hanif.

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte de **Loadpath**, la colección de librerías estructurales de código abierto de [Jesús Murgas](https://github.com/jmurgass99).
