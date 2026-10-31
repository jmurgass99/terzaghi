# terzaghi

Análisis geotécnico para diseño estructural: capacidad portante (Terzaghi, Meyerhof, Vesic, Brinch Hansen y vía EN 1997-1 con inclinación y excentricidad), capacidad axial de pilotes en perfiles estratificados, curvas p-y (Matlock, Reese), eficiencia de grupos y p-multiplicadores (Mokwa-Duncan), monopilotes dinámicos, muelles de interacción suelo-estructura de Gazetas, consolidación (Terzaghi, Skempton-Bjerrum), licuefacción (Boulanger-Idriss), respuesta de sitio 1D, excavaciones, muros de gaviones, túneles, correlaciones, durabilidad (carbonatación, cloruros) e importación AGS4 con generación de scripts PLAXIS.

[![CI](https://github.com/jmurgass99/terzaghi/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/terzaghi/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Paquete independiente. Dependencias: `numpy`, `pydantic`, `forallpeople`. La capacidad portante canónica (geometría, suelo y fórmulas) va incluida en `terzaghi/_foundation`.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/terzaghi.git
```

Extras: `api` (REST), `memos` (memorias con handcalcs), `test`.

## Inicio rápido

### Capacidad portante por cuatro métodos

```python
from terzaghi.bearing_capacity import BearingCapacityInput, evaluate_bearing, evaluate_bearing_ec7

for method in ("terzaghi", "meyerhof", "vesic", "brinch_hansen"):
    r = evaluate_bearing(BearingCapacityInput(B_m=2.0, L_m=3.0, D_f_m=1.5, phi_deg=32.0,
                                              c_kPa=0.0, gamma_kN_m3=19.0, method=method), code="EU")
    print(method, round(r.q_ult_kPa), round(r.q_adm_kPa))

ec7 = evaluate_bearing_ec7(B_m=2.0, L_m=3.0, D_f_m=1.5, phi_deg=32.0, gamma_kN_m3=19.0, gamma_Rv=1.4)
print(ec7.q_ult, ec7.R_d)      # kPa y resistencia de diseño
```

### Pilote: capacidad axial y curvas p-y

```python
from terzaghi.piles.axial_capacity import Pile, SoilLayer, axial_capacity
from terzaghi.piles.py_curves import py_matlock_soft_clay

layers = [SoilLayer(top_m=0, bottom_m=8, kind="clay", Su_kPa=35),
          SoilLayer(top_m=8, bottom_m=25, kind="sand", phi_deg=34)]
r = axial_capacity(Pile(diameter_m=0.6, length_m=18.0, water_table_m=2.0), layers, FS=2.5)
print(r.Q_skin_kN, r.Q_base_kN, r.Q_allow_kN)      # 861, 1390, 901 kN

p, y = py_matlock_soft_clay(z_m=5.0, D_m=0.6, su_kPa=35.0)   # p [kN/m], y [m]
```

### Licuefacción y muelles de Gazetas

```python
from terzaghi.liquefaction import LiquefactionInput, evaluate_liquefaction
from terzaghi.gazetas_springs import GazetasInput, evaluate_gazetas

evaluate_liquefaction(LiquefactionInput(depth_m=6.0, sigma_v_kPa=114.0, sigma_v_eff_kPa=55.1,
                                        N1_60_cs=15, a_max_g=0.25, Mw=7.0))      # FS = 0.68
evaluate_gazetas(GazetasInput(L_m=3.0, B_m=2.0, Vs_m_per_s=180.0, nu_soil=0.35))   # K_z ≈ 530 000 kN/m
```

Los tres scripts de `examples/` ejecutan estos flujos con tablas comparativas.

## Módulos

| Módulo | Contenido |
|---|---|
| `bearing_capacity`, `bearing_inclination`, `_foundation/` | Capacidad portante multimétodo y EC7 |
| `piles/` | `axial_capacity`, `py_curves`, `group`, `mokwa_duncan`, `dynamic_py` |
| `gazetas_springs`, `ssi_springs` | Rigideces de interacción suelo-estructura |
| `consolidation`, `skempton_bjerrum`, `unsaturated` | Asientos y consolidación |
| `liquefaction/` (`boulanger_idriss`), `site_response/`, `wave_propagation_1d` | Sísmica geotécnica |
| `excavation`, `gabion_wall`, `gabion_wall_safety`, `tunnels` | Obras geotécnicas |
| `correlations`, `estratigrafias_catalogo`, `materials` | Correlaciones y catálogos |
| `durability/` | Carbonatación y cloruros |
| `ags4_plaxis` | Lectura AGS4 y script PLAXIS |
| `audit/`, `memos/`, `api/` | Auditoría de asiento diferencial, memorias, REST |

## Validación

Tests golden contra valores publicados de capacidad portante (903,5 kPa de la referencia frente a 903,47 calculados), fichas de consolidación y empujes de Rankine, Mononobe-Okabe (ficha W00678), asiento SSI de Gazetas y licuefacción Boulanger-Idriss 2014.

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte del toolkit estructural de código abierto **Loadpath**, de [Jesús Murgas](https://github.com/jmurgass99).
