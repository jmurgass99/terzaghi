# GeoJm

Geotecnia + fundaciones — extiende `FoundationDesignJm` con P-y curves,
grupo de pilotes y materiales no lineales.

## Scope

- `geojm.piles.py_curves` — Matlock (arcilla blanda), Reese (arena)
- `geojm.piles.group` — eficiencia lateral por método del `p-multiplier`
- `geojm.materials.mander` — hormigón confinado Mander 1988

## Roadmap

- [ ] Integración con `fastsap` para inyectar springs T-Z + P-y vía OAPI
- [ ] Asentamientos diferenciales como `AuditRule` (gotcha #12 colateral)
- [ ] Geotecnia sísmica: propagación de ondas + licuación (IEG 3660)
