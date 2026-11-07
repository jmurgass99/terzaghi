# terzaghi

**Español** · [English](README.en.md)

Geotecnia y cimentaciones en Python: capacidad portante de EN 1997-1, pilotes, consolidación, licuefacción, muelles de Gazetas, muros y túneles.

[![CI](https://github.com/jmurgass99/terzaghi/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/terzaghi/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

## Qué hace

- Capacidad portante de zapatas con la ecuación completa del Anexo D de EN 1997-1 (área efectiva, inclinación de carga, factores parciales DA1/DA2).
- Pilotes: métodos α y β, curvas p-y de Matlock y Reese, grupos y monopilotes cíclicos.
- Consolidación con drenes verticales (Terzaghi, Barron, Hansbo, Carrillo).
- Licuefacción por SPT (Boulanger e Idriss, 2014) y respuesta de sitio 1D.
- Muelles estáticos y dinámicos de Gazetas, muros de gaviones y empujes (Rankine, Coulomb, Mononobe-Okabe), excavaciones y túneles.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/terzaghi.git
```

Extras opcionales: `api`, `memos`. Requiere Python 3.11 o superior.

## Ejemplo

Factores de capacidad portante de Vesić para φ' = 28°:

```python
from terzaghi._foundation.bearing_capacity import BearingCapacityFormula, bearing_capacity_factors

Nq, Nc, Ngamma = bearing_capacity_factors(28.0, BearingCapacityFormula.VESIC)
print(round(Nq, 2), round(Nc, 2), round(Ngamma, 2))   # 14.72 25.8 16.72
```

Más casos en [`examples/`](examples).

## Qué no hace

- Estabilidad de taludes (círculos críticos): para eso está [slipcircle](https://github.com/jmurgass99/slipcircle).
- Respuesta de sitio con varios estratos: el producto por capa es exacto para una capa sobre base rígida y falla con varias.
- Grupos de pilotes con la memoria `memos.pile_group_lateral`: no reduce nada para s/D ≥ 1; usa `piles.group` (Brown 1988).
- Flotación del fondo de excavaciones: `check_excavation` no conoce el espesor del tapón ni la carga del acuífero.

El detalle está en [docs/LIMITACIONES.md](docs/LIMITACIONES.md).

## Pruebas

```bash
pip install -e ".[test]"
pytest -q
```

## Licencia

MIT. Ver [LICENSE](LICENSE). Autor: [Jesús Murgas](https://github.com/jmurgass99).
