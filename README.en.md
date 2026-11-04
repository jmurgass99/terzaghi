# terzaghi

[Español](README.md) · **English**

Geotechnics and foundations in Python: EN 1997-1 bearing capacity, piles, consolidation, liquefaction, Gazetas springs, walls and tunnels.

[![CI](https://github.com/jmurgass99/terzaghi/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/terzaghi/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What it does

- Bearing capacity of footings with the full EN 1997-1 Annex D equation (effective area, load inclination, DA1/DA2 partial factors).
- Piles: α and β methods, Matlock and Reese p-y curves, groups and cyclic monopiles.
- Consolidation with vertical drains (Terzaghi, Barron, Hansbo, Carrillo).
- SPT liquefaction (Boulanger and Idriss, 2014) and 1D site response.
- Static and dynamic Gazetas springs, gabion walls and earth pressures (Rankine, Coulomb, Mononobe-Okabe), excavations and tunnels.

## Install

```bash
pip install git+https://github.com/jmurgass99/terzaghi.git
```

Optional extras: `api`, `memos`. Requires Python 3.11 or later.

## Example

Vesić bearing capacity factors for φ' = 28°:

```python
from terzaghi._foundation.bearing_capacity import BearingCapacityFormula, bearing_capacity_factors

Nq, Nc, Ngamma = bearing_capacity_factors(28.0, BearingCapacityFormula.VESIC)
print(round(Nq, 2), round(Nc, 2), round(Ngamma, 2))   # 14.72 25.8 16.72
```

More cases in [`examples/`](examples).

## What it does not do

- Slope stability (critical circles): use [slipcircle](https://github.com/jmurgass99/slipcircle) for that.
- Site response with several layers: the per-layer product is exact for one layer over rigid base and fails with several.
- Pile groups with the `memos.pile_group_lateral` memo: it reduces nothing for s/D ≥ 1; use `piles.group` (Brown 1988).
- Excavation base heave: `check_excavation` does not know the plug thickness or the aquifer load.

Details are in [docs/LIMITACIONES.md](docs/LIMITACIONES.md) (in Spanish).

## Tests

```bash
pip install -e ".[test]"
pytest -q
```

## License

MIT. See [LICENSE](LICENSE). Author: [Jesús Murgas](https://github.com/jmurgass99).
