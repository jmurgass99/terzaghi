# Changelog

## 1.1.0 — 2026-11-01

Correcciones encontradas al ejecutar los casos de uso del README.

- `materials.mander_confined_concrete`: la resistencia confinada llevaba un «1,0 +» de más en la ec. 7 de Mander et al. (1988): K salía exactamente 1,0 por encima de la fuente (2,58 en vez de 1,58 para 1 % de cuantía y f'c = 30 MPa; f'cc = 77 MPa donde Mander da 47). El exponente de Popovics pasa de 5/(K − 1) a r = E_c/(E_c − E_sec) con E_c = 5000·√f'c: la rama descendente deja de ser casi vertical y el hormigón sin confinar ya no cae a cero tras el pico.
- `liquefaction.evaluate_liquefaction` (y el endpoint `/api/geo/liquefaction`): r_d omitía los senos de α(z) y β(z) (0,74 en vez de 0,96 a 5 m) y K_σ usaba √(σ'/100) en vez de ln(σ'/P_a) (0,89 en vez de 1,0 a 100 kPa). El FS salía un 13–29 % por encima del de `evaluate_bi2014`, del lado inseguro. Ahora ambas vías comparten las funciones de Boulanger & Idriss (2014).
- `terzaghi.liquefaction` exportaba `evaluate_spt_profile_liquefaction` en `__all__` sin importarla (ImportError). Se exportan también `evaluate_bi2014`, `BoulangerIdrissInput`, `BoulangerIdrissResult` y `ProfileLiquefactionResult`.
- Versión única: `pyproject.toml` decía 1.0.0, `__version__` 0.2.0 y la API 0.1.0; ahora 1.1.0 en los tres sitios.
- `piles.mokwa_duncan`: eliminada una asignación muerta de K_p (sin cambio numérico).
- Documentado, sin corregir: `memos.pile_group_lateral` usa f_m = 0,64 + 0,36·s/D saturado a 1 (no reduce nada para s/D ≥ 1); `excavation.check_excavation` calcula el FS de flotación con la profundidad de excavación en vez del espesor del tapón; `integration.fastsap_pysprings.build_py_curve` usa en arena una fórmula sin referencia (≈ la mitad de `py_reese_sand`); la corrección K_x − K_y de Gazetas se aplica con la longitud total (Gazetas usa la semilongitud; término del orden del 3 % de K).
- 30 casos de uso ejecutados en `examples/` (cimentación superficial EC7; pilotes; asientos, consolidación y correlaciones; empujes, muros y excavaciones; licuefacción, respuesta de sitio y SSI; túneles, durabilidad, Mander, AGS4 y API), con su salida en `examples/output/`; `tests/test_examples.py` los ejecuta en CI. README reescrito.

## 1.0.0

Versión publicada como repositorio independiente (origen: GeoJm del monorepo Structural JM).
