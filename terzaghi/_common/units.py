"""Conversión de unidades para ingeniería estructural — sin dependencias.

API mínima por diseño: una función ``convert(value, from_unit, to_unit)``
basada en una tabla de factores. No hay tipo ``Quantity`` ni álgebra de
unidades (eso sería otro proyecto); esto cubre el 95% de la necesidad real
de los módulos: pasar kN↔N, MPa↔psi, m↔ft, kN·m↔N·mm.

Ejemplo:
    >>> convert(1.0, "kN", "N")
    1000.0
    >>> round(convert(250.0, "MPa", "psi"), 1)
    36259.4
"""
from __future__ import annotations

import re
from typing import Any, Dict, Tuple

# Cada dimensión mapea unidad → factor hacia la unidad base de esa dimensión.
# Base: fuerza=N, esfuerzo=Pa, longitud=m, momento=N·m, masa=kg, ángulo=rad.
_DIMENSIONS: Dict[str, Dict[str, float]] = {
    "force": {
        "N": 1.0,
        "kN": 1.0e3,
        "MN": 1.0e6,
        "lbf": 4.4482216153,
        "kip": 4448.2216153,
        # Fuerzas de las etiquetas eUnits de CSI (kgf_*, Ton_*): kilogramo-fuerza y
        # tonelada-fuerza (2026-09-07). `lb` (masa) sigue siendo masa: CSI llama
        # "lb" a la libra-FUERZA y el adaptador la mapea a lbf.
        "kgf": 9.80665,
        "tonf": 9806.65,
    },
    "stress": {
        "Pa": 1.0,
        "kPa": 1.0e3,
        "MPa": 1.0e6,
        "GPa": 1.0e9,
        "psi": 6894.757293168,
        "ksi": 6894757.293168,
    },
    "length": {
        "m": 1.0,
        "dm": 0.1,
        "cm": 0.01,
        "mm": 1.0e-3,
        "km": 1.0e3,
        "ft": 0.3048,
        "in": 0.0254,
    },
    "moment": {
        "N*m": 1.0,
        "Nm": 1.0,
        "kN*m": 1.0e3,
        "kNm": 1.0e3,
        "N*mm": 1.0e-3,
        "Nmm": 1.0e-3,
        "lbf*ft": 1.3558179483,
        # Momentos de TODAS las etiquetas eUnits de CSI (fuerza x longitud). Medido
        # el 2026-09-07: el modelo real estaba en lb_in_F y faltaba lbf*in.
        "lbf*in": 4.4482216153 * 0.0254,
        "kip*in": 4448.2216153 * 0.0254,
        "kip*ft": 4448.2216153 * 0.3048,
        "kN*cm": 1.0e3 * 0.01,
        "kgf*m": 9.80665,
        "kgf*cm": 9.80665 * 0.01,
        "kgf*mm": 9.80665 * 1.0e-3,
        "tonf*m": 9806.65,
        "tonf*cm": 9806.65 * 0.01,
        "tonf*mm": 9806.65 * 1.0e-3,
        "kN*mm": 1.0,
        "N*cm": 0.01,
    },
    # Carga repartida (base N/m). Antes no existia ninguna dimension para
    # esto, asi que `kN/m` no se podia ni nombrar y una carga lineal viajaba
    # sin unidad.
    "line_load": {
        "N/m": 1.0,
        "kN/m": 1.0e3,
        "MN/m": 1.0e6,
        "N/mm": 1.0e3,
        "kN/mm": 1.0e6,
        "N/cm": 1.0e2,
        "kgf/m": 9.80665,
        "kgf/cm": 9.80665 * 1.0e2,
        "tonf/m": 9806.65,
        "lbf/ft": 4.4482216153 / 0.3048,
        "lbf/in": 4.4482216153 / 0.0254,
        "kip/ft": 4448.2216153 / 0.3048,
        "kip/in": 4448.2216153 / 0.0254,
    },
    "mass": {
        "kg": 1.0,
        "g": 1.0e-3,
        "t": 1.0e3,
        "lb": 0.45359237,
    },
}

# Índice inverso: unidad → (dimensión, factor_a_base). Construido una vez.
_UNIT_INDEX: Dict[str, Tuple[str, float]] = {}
for _dim, _table in _DIMENSIONS.items():
    for _unit, _factor in _table.items():
        _UNIT_INDEX[_unit] = (_dim, _factor)

#: Separadores que las exportaciones de CAD/BIM y las tablas CSI usan para el
#: producto fuerza x longitud. Son cosméticos: `kN-m`, `kN·m` y `kN.m` son la
#: misma unidad que `kN*m`. Antes solo se reconocía `*` (y las formas pegadas
#: como `kNm`), así que un momento escrito con guion no se entendía y el
#: pipeline se cortaba —o alguien lo rodeaba suponiendo la unidad—.
#:
#: Los alias se DERIVAN de las unidades canónicas, no se listan a mano: así no
#: pueden quedar desincronizados, y normalizar el separador nunca puede
#: fabricar una unidad que no exista.
_SEPARADORES_EQUIVALENTES: Tuple[str, ...] = ("-", "·", ".")

for _unidad, _valor in list(_UNIT_INDEX.items()):
    if "*" in _unidad:
        for _sep in _SEPARADORES_EQUIVALENTES:
            _UNIT_INDEX.setdefault(_unidad.replace("*", _sep), _valor)


#: Una coma con EXACTAMENTE tres digitos detras y nada mas: '1,234', '12,345'.
#: Puede ser mil doscientos treinta y cuatro o uno coma dos tres cuatro, y no hay
#: forma de saberlo sin el locale.
_RE_COMA_MILES = re.compile(r"[+-]?\d{1,3},\d{3}")


def to_float(raw: Any, *, decimal_sep: "str | None" = None) -> "float | None":
    """Celda de una tabla OAPI a ``float``, o ``None`` si no hay número.

    **Ausente devuelve ``None``, nunca ``0.0``.** Un cero es una medida: dice que
    la reacción vale cero. ``None`` dice que la tabla no la dio. Son cosas
    distintas y el llamante tiene que poder distinguirlas (regla 7).

    Las tablas de ETABS pueden traer **coma decimal** según el locale de la
    máquina: ``'-1,111E-08'``, ``'81,25'`` — observado contra ETABS vivo. Sin
    entender la coma, un número perfectamente válido se pierde en silencio.

    **Y donde no se puede saber, no se adivina: se lanza.** Una coma puede ser el
    decimal o el separador de miles, y confundirlos es un error de 1000× que no
    deja rastro. La regla:

        '81,25'    -> 81.25      dos decimales: no puede ser separador de miles
        '1,2345'   -> 1.2345     cuatro: tampoco
        '1,234'    -> ValueError tres digitos detras: mil doscientos o uno coma dos
        '1,234.5'  -> ValueError los dos separadores a la vez
        '1.234,5'  -> ValueError idem

    ``decimal_sep`` (``','`` o ``'.'``) quita la ambigüedad: quien conoce el
    locale lo declara y la función deja de tener que decidir.

    MEDIDO al escribir esto: ``'1,234'`` salía ``1.234``. Es el mismo defecto que
    esta función viene a cerrar, en la otra dirección.

    Esta es la implementación CANÓNICA. Había tres en `fastsap`
    (`csi/normalizer.py`, `etabs/client.py`, `smoke_e2e_etabs.py`) y no hacían lo
    mismo: una devolvía ``0.0`` para lo ausente —fabricando una reacción nula que
    después dimensionaba zapatas— y otra no entendía la coma, así que descartaba
    valores reales. Sólo la tercera era correcta, y vivía en un módulo de humo.

    Raises:
        ValueError: si la cadena es ambigua y no se declaró ``decimal_sep``, o si
            ``decimal_sep`` no es ``','`` ni ``'.'``.
    """
    if decimal_sep is not None and decimal_sep not in (",", "."):
        raise ValueError(f"decimal_sep debe ser ',' o '.', no {decimal_sep!r}")
    if raw is None:
        return None
    if isinstance(raw, bool):           # bool es int en Python; aqui no es un numero
        return None
    if not isinstance(raw, str):
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    texto = raw.strip()
    if not texto:
        return None

    tiene_coma, tiene_punto = "," in texto, "." in texto

    if decimal_sep is not None:
        miles = "." if decimal_sep == "," else ","
        try:
            return float(texto.replace(miles, "").replace(decimal_sep, "."))
        except ValueError:
            return None

    if tiene_coma and tiene_punto:
        raise ValueError(
            f"{texto!r} es ambiguo: lleva coma y punto y no se declaro cual es el "
            "separador decimal. Pasa decimal_sep=',' o '.'; adivinar aqui es un "
            "error de 1000x que no deja rastro")

    if tiene_coma and _RE_COMA_MILES.fullmatch(texto):
        raise ValueError(
            f"{texto!r} es ambiguo: una coma con tres digitos detras puede ser el "
            "separador de miles (1234) o el decimal (1.234). Pasa decimal_sep")

    try:
        return float(texto.replace(",", ".") if tiene_coma else texto)
    except ValueError:
        return None


def known_units() -> Dict[str, list]:
    """Devuelve {dimensión: [unidades]} para descubribilidad."""
    return {dim: sorted(table) for dim, table in _DIMENSIONS.items()}


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convierte ``value`` de ``from_unit`` a ``to_unit``.

    Raises:
        ValueError: si una unidad es desconocida o las dimensiones no coinciden.
    """
    if from_unit not in _UNIT_INDEX:
        raise ValueError(f"unknown unit: {from_unit!r}")
    if to_unit not in _UNIT_INDEX:
        raise ValueError(f"unknown unit: {to_unit!r}")
    dim_from, factor_from = _UNIT_INDEX[from_unit]
    dim_to, factor_to = _UNIT_INDEX[to_unit]
    if dim_from != dim_to:
        raise ValueError(
            f"incompatible units: {from_unit!r} ({dim_from}) -> "
            f"{to_unit!r} ({dim_to})"
        )
    return value * factor_from / factor_to


def conversion_factor(from_unit: str, to_unit: str) -> float:
    """Devuelve el factor multiplicativo para convertir de from_unit a to_unit.

    value_in_to_unit = value_in_from_unit * conversion_factor(from_unit, to_unit)
    """
    if from_unit not in _UNIT_INDEX:
        raise ValueError(f"unknown unit: {from_unit!r}")
    if to_unit not in _UNIT_INDEX:
        raise ValueError(f"unknown unit: {to_unit!r}")
    dim_from, factor_from = _UNIT_INDEX[from_unit]
    dim_to, factor_to = _UNIT_INDEX[to_unit]
    if dim_from != dim_to:
        raise ValueError(
            f"incompatible units: {from_unit!r} ({dim_from}) -> "
            f"{to_unit!r} ({dim_to})"
        )
    return factor_from / factor_to


def ensure_unit(value: float, current_unit: str, target_unit: str) -> float:
    """Valida compatibilidad dimensional y convierte el valor a la unidad destino.

    Si las unidades son idénticas, retorna float(value) directamente.
    """
    if current_unit == target_unit:
        return float(value)
    return convert(value, current_unit, target_unit)


def assert_compatible_units(
    current_unit: str,
    target_unit: str,
    expected_dimension: str | None = None,
) -> None:
    """Verifica compatibilidad dimensional entre dos unidades y opcionalmente con una dimensión esperada.

    Raises:
        ValueError: si alguna unidad es desconocida, si sus dimensiones difieren,
                    o si no corresponden a expected_dimension.
    """
    if current_unit not in _UNIT_INDEX:
        raise ValueError(f"Unidad de origen desconocida: {current_unit!r}")
    if target_unit not in _UNIT_INDEX:
        raise ValueError(f"Unidad de destino desconocida: {target_unit!r}")
    dim_cur = _UNIT_INDEX[current_unit][0]
    dim_tgt = _UNIT_INDEX[target_unit][0]
    if dim_cur != dim_tgt:
        raise ValueError(
            f"Incompatibilidad dimensional: {current_unit!r} ({dim_cur}) vs "
            f"{target_unit!r} ({dim_tgt})"
        )
    if expected_dimension is not None and dim_cur != expected_dimension:
        raise ValueError(
            f"Dimensión inesperada para {current_unit!r}: esperada "
            f"{expected_dimension!r}, encontrada {dim_cur!r}"
        )


#: Mapeo exhaustivo de códigos eUnits de CSI (1 a 16) a sus unidades canónicas.
CSI_UNITS_METADATA: Dict[str, Dict[str, str]] = {
    "lb_in_F": {"force": "lbf", "length": "in", "moment": "lbf*in", "stress": "psi", "temp": "F"},
    "lb_ft_F": {"force": "lbf", "length": "ft", "moment": "lbf*ft", "stress": "psi", "temp": "F"},
    "kip_in_F": {"force": "kip", "length": "in", "moment": "kip*in", "stress": "ksi", "temp": "F"},
    "kip_ft_F": {"force": "kip", "length": "ft", "moment": "kip*ft", "stress": "ksi", "temp": "F"},
    "kN_mm_C": {"force": "kN", "length": "mm", "moment": "kN*mm", "stress": "MPa", "temp": "C"},
    "kN_m_C": {"force": "kN", "length": "m", "moment": "kN*m", "stress": "kPa", "temp": "C"},
    "kgf_mm_C": {"force": "kgf", "length": "mm", "moment": "kgf*mm", "stress": "MPa", "temp": "C"},
    "kgf_m_C": {"force": "kgf", "length": "m", "moment": "kgf*m", "stress": "kPa", "temp": "C"},
    "N_mm_C": {"force": "N", "length": "mm", "moment": "N*mm", "stress": "MPa", "temp": "C"},
    "N_m_C": {"force": "N", "length": "m", "moment": "N*m", "stress": "Pa", "temp": "C"},
    "Ton_mm_C": {"force": "tonf", "length": "mm", "moment": "tonf*mm", "stress": "MPa", "temp": "C"},
    "Ton_m_C": {"force": "tonf", "length": "m", "moment": "tonf*m", "stress": "kPa", "temp": "C"},
    "kN_cm_C": {"force": "kN", "length": "cm", "moment": "kN*cm", "stress": "kPa", "temp": "C"},
    "kgf_cm_C": {"force": "kgf", "length": "cm", "moment": "kgf*cm", "stress": "kPa", "temp": "C"},
    "N_cm_C": {"force": "N", "length": "cm", "moment": "N*cm", "stress": "kPa", "temp": "C"},
    "Ton_cm_C": {"force": "tonf", "length": "cm", "moment": "tonf*cm", "stress": "kPa", "temp": "C"},
}

_CSI_EUNITS_CODE_TO_LABEL: Dict[int, str] = {
    1: "lb_in_F", 2: "lb_ft_F", 3: "kip_in_F", 4: "kip_ft_F",
    5: "kN_mm_C", 6: "kN_m_C", 7: "kgf_mm_C", 8: "kgf_m_C",
    9: "N_mm_C", 10: "N_m_C", 11: "Ton_mm_C", 12: "Ton_m_C",
    13: "kN_cm_C", 14: "kgf_cm_C", 15: "N_cm_C", 16: "Ton_cm_C",
}


def csi_units_for_code(code_or_label: int | str) -> Dict[str, str]:
    """Resuelve un código eUnits (int o str) a su diccionario de unidades canónicas."""
    if isinstance(code_or_label, int) or (isinstance(code_or_label, str) and code_or_label.isdigit()):
        c = int(code_or_label)
        if c not in _CSI_EUNITS_CODE_TO_LABEL:
            raise ValueError(f"Código eUnits desconocido: {c}")
        label = _CSI_EUNITS_CODE_TO_LABEL[c]
    else:
        label = str(code_or_label).replace("eUnits.", "").strip()
        if label not in CSI_UNITS_METADATA:
            raise ValueError(f"Etiqueta de unidades CSI desconocida: {label!r}")
    return dict(CSI_UNITS_METADATA[label])


def unit_dimension(unit: str) -> str:
    """Devuelve la dimensión física de la unidad ('force', 'moment', 'length', etc.)."""
    if unit not in _UNIT_INDEX:
        raise ValueError(f"unknown unit: {unit!r}")
    return _UNIT_INDEX[unit][0]


def normalize_forces_df(
    df: Any,
    target_force_unit: str = "N",
    target_moment_unit: str = "N*m",
    default_force_unit: str | None = None,
    default_moment_unit: str | None = None,
    strict: bool = True,
) -> Any:
    """[ESTADO: EXPERIMENTAL] Normaliza columnas de fuerzas y momentos en un DataFrame a unidades objetivo.

    MEDIDO (F13): **no tiene ningún llamante de producción**, solo tests. Y con
    `strict=False` deja los kN sin escalar hacia N: 1000x de subestimación en
    silencio, que es lo que fija
    `tests/test_la_unidad_ausente_no_se_supone.py`. Un conversor de unidades
    exportado en `__all__`, sin llamante y con un modo que se equivoca por mil
    no es API estable: el primero que lo use no tendrá cómo saberlo.

    Quien necesite convertir una magnitud suelta use :func:`convert`, y quien
    necesite leer un número de una tabla use :func:`to_float`; esas dos sí son
    de producción. `tools/lint_experimental.py` falla si esta gana un llamante.

    Columnas de fuerza evaluadas: 'P', 'V2', 'V3', 'V_major', 'V_minor', 'N_Ed', 'V_Ed', 'Fx', 'Fy', 'Fz', 'P_N'.
    Columnas de momento evaluadas: 'M2', 'M3', 'T', 'M_major', 'M_minor', 'M_Ed', 'Mx', 'My', 'Mz', 'M_Nm'.

    Determina la unidad actual por columna desde:
      1. df.attrs['units'][col] o df.attrs['units']['force'|'moment']
      2. df.attrs['force_unit'] / df.attrs['moment_unit']
      3. default_force_unit / default_moment_unit

    `strict` es True POR OMISION, y eso es deliberado: si la unidad no consta por
    ninguna de las tres vias, la funcion LANZA en vez de devolver el numero sin tocar.
    Con el permisivo por omision, una tabla en kN salia con el mismo numero tratado como
    N --1000x de subestimacion, en silencio--, y bastaba con que nadie hubiera declarado
    la unidad. El permisivo sigue disponible pidiendolo (`strict=False`): lo que cambia
    es que ahora es una decision declarada y no un descuido.
    """
    if hasattr(df, "copy"):
        out = df.copy()
    else:
        out = df

    attrs_units = getattr(out, "attrs", {}).get("units", {}) if hasattr(out, "attrs") else {}
    if not isinstance(attrs_units, dict):
        attrs_units = {}

    force_cols = {"P", "V2", "V3", "V_major", "V_minor", "N_Ed", "V_Ed", "Fx", "Fy", "Fz", "P_N"}
    moment_cols = {"M2", "M3", "T", "M_major", "M_minor", "M_Ed", "Mx", "My", "Mz", "M_Nm"}

    updated_units = dict(attrs_units)

    cols = getattr(out, "columns", [])
    for col in cols:
        col_str = str(col)
        if col_str in force_cols:
            cur_unit = (
                attrs_units.get(col_str)
                or attrs_units.get("force")
                or getattr(out, "attrs", {}).get("force_unit")
                or default_force_unit
            )
            if cur_unit is None:
                if strict:
                    raise ValueError(f"Falta unidad para la columna de fuerza {col_str!r}")
                cur_unit = target_force_unit

            dim = unit_dimension(cur_unit)
            if dim != "force":
                raise ValueError(f"La unidad {cur_unit!r} para {col_str} tiene dimensión {dim!r}, no 'force'")

            factor = conversion_factor(cur_unit, target_force_unit)
            if factor != 1.0:
                out[col] = out[col] * factor
            updated_units[col_str] = target_force_unit

        elif col_str in moment_cols:
            cur_unit = (
                attrs_units.get(col_str)
                or attrs_units.get("moment")
                or getattr(out, "attrs", {}).get("moment_unit")
                or default_moment_unit
            )
            if cur_unit is None:
                if strict:
                    raise ValueError(f"Falta unidad para la columna de momento {col_str!r}")
                cur_unit = target_moment_unit

            dim = unit_dimension(cur_unit)
            if dim != "moment":
                raise ValueError(f"La unidad {cur_unit!r} para {col_str} tiene dimensión {dim!r}, no 'moment'")

            factor = conversion_factor(cur_unit, target_moment_unit)
            if factor != 1.0:
                out[col] = out[col] * factor
            updated_units[col_str] = target_moment_unit

    if hasattr(out, "attrs"):
        out.attrs["units"] = updated_units
        out.attrs["force_unit"] = target_force_unit
        out.attrs["moment_unit"] = target_moment_unit

    return out


# --- Integración OPCIONAL con forallpeople (reporte dinámico Mathcad-Style) ---
#
# `forallpeople` NO es dependencia del núcleo: se resuelve de forma PEREZOSA la
# primera vez que se accede a una de estas unidades, mediante el `__getattr__`
# de módulo (PEP 562), que también atiende a `from ... import kN`.
#
# Antes se importaba en el cuerpo del módulo sin declararlo en el pyproject, de
# modo que `import terzaghi._common` reventaba en cualquier entorno que no
# arrastrase el grupo dev de la raíz, y eso afecta a los 26+ paquetes que
# dependen del núcleo y al empaquetado de escritorio (fase 1E.3, 2026-09-07).
#
# Consumidores actuales: `fastsap.memos.*` (concrete_design, steel_ltb_memo,
# seismic_transient_memo, bearing_capacity_memo), que declaran el extra `memos`.

#: Unidades expuestas perezosamente desde forallpeople.
FORALLPEOPLE_UNITS: Tuple[str, ...] = (
    "m", "N", "Pa", "kN", "MN", "kPa", "MPa", "GPa", "mm", "cm", "cm2", "m2", "kNm", "Nmm",
)

_si_units: Dict[str, object] | None = None


def _load_forallpeople() -> Dict[str, object]:
    """Carga forallpeople una sola vez y construye las unidades derivadas."""
    global _si_units
    if _si_units is not None:
        return _si_units
    try:
        import forallpeople as si
    except ImportError as exc:                                    # pragma: no cover
        raise ImportError(
            "Las unidades simbólicas de terzaghi._common.units requieren `forallpeople`, "
            "que es una dependencia OPCIONAL del núcleo. Instálala con `uv sync --all-packages` "
            "(grupo dev del workspace) o añade el extra que la declare. La conversión numérica "
            "`convert()` no la necesita y sigue disponible."
        ) from exc
    try:
        si.environment("structural")
    except Exception:                                             # pragma: no cover
        pass  # el entorno ya estaba inicializado o no existe: las unidades base siguen sirviendo
    m = getattr(si, "m", None)
    N = getattr(si, "N", None)
    kN = getattr(si, "kN", None)
    mm = m / 1000 if m else None
    cm = m / 100 if m else None
    _si_units = {
        "m": m, "N": N, "Pa": getattr(si, "Pa", None), "kN": kN, "MN": getattr(si, "MN", None),
        "kPa": getattr(si, "kPa", None), "MPa": getattr(si, "MPa", None), "GPa": getattr(si, "GPa", None),
        "mm": mm, "cm": cm,
        "cm2": cm ** 2 if cm else None,
        "m2": m ** 2 if m else None,
        "kNm": kN * m if (kN and m) else None,
        "Nmm": N * mm if (N and mm) else None,
    }
    return _si_units


def __getattr__(name: str) -> object:
    """PEP 562: resuelve las unidades simbólicas al primer acceso."""
    if name in FORALLPEOPLE_UNITS:
        return _load_forallpeople()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals()) + list(FORALLPEOPLE_UNITS))

