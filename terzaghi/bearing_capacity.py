"""
Capacidad portante de zapatas.

ESTADO: este módulo está DEPRECADO como calculadora. La implementación
CANÓNICA de capacidad portante de cimentación superficial del monorepo es
``foundationcalc.analysis.bearing_capacity``; aquí se DELEGA en ella a
través de :func:`evaluate_bearing_ec7`.

Por qué la canónica es esa y no ésta (medido, no opinado)
---------------------------------------------------------
Sobre el ejemplo resuelto PUBLICADO W00675 §4.3 DA1-C1 ("Examples of
geotechnical design according to Eurocode 7", UPC MEEC; transcrito en
``packages/FoundationDesignJm/docs/theory/04_eurocode7_examples.md``), que
publica los NUEVE valores intermedios de una zapata de 2.5 × 1.5 m:

    foundationcalc.analysis   903.47 kPa   →   −0.004 %  (publicado 903.5)
    evaluate_bearing (vesic)      927.13 kPa   →   +2.62 %
    evaluate_bearing (brinch_h.)  748.10 kPa   →  −17.20 %

Los factores de forma de :func:`evaluate_bearing`
(S_c = 1+0.2·B/L, S_q = 1+0.1·B/L, S_γ = 1−0.1·B/L) NO corresponden a ningún
juego publicado — ya estaba documentado en la NOTA 2 de
``tests/test_golden_bearing_capacity_published.py``. Los de la canónica sí son
los del Anexo D de EN 1997-1.

Además :func:`evaluate_bearing` es CIEGO a la excentricidad y a la inclinación
de carga (no tiene esos parámetros), y siempre del lado INSEGURO: sobre una
zapata cuadrada de 2.5 m con e_B = 0.30 m y H/V = 150/1000 kN devuelve un
q_ult un **+41.1 %** por encima de la canónica.

:func:`evaluate_bearing` se conserva con sus valores INTACTOS (sólo emite
``DeprecationWarning``) para no romper a los llamadores existentes. El módulo
``terzaghi.bearing_inclination`` queda igualmente superado por la canónica, que
sí cablea excentricidad e inclinación dentro de la misma ecuación.

Modelos que implementa el camino legacy:
    Terzaghi (1943)        — ver NOTA 1 del golden: NO son los factores de
                             Terzaghi, coinciden exactamente con Meyerhof
    Meyerhof (1963)
    Vesic (1973)
    Brinch Hansen (1970)

Códigos cubiertos (factores parciales) por el camino legacy:
    EU/SG: EN 1997-1 §6.5.2 + Annex D (γ_R,v = 1.4 R3, γ_φ = 1.25, γ_c = 1.4)
    US:    ACI 318 / AASHTO LRFD §10.6 (φ = 0.45 a 0.55)
    CO:    NSR-10 §H.4.7 (FS ≥ 3 estático, FS ≥ 2 sísmico)
    AU:    AS 5100.3 / Foundation Code AS 2159 (φ = 0.40–0.70 según método)
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from math import exp, pi, radians, tan
from typing import Any, Literal

# --- Delegación a la implementación CANÓNICA ------------------------------
# Import a nivel de módulo: se comprobó que NO crea ciclo (FoundationDesignJm
# sólo importa terzaghi de forma perezosa, dentro de funciones, en
# ``foundationcalc/integration/terzaghi_bridge.py``, y no lo declara como
# dependencia).
# Si el import fallara NO se silencia: se guarda la excepción y se relanza en
# la llamada, para no convertir una dependencia ausente en un cero silencioso.
try:  # pragma: no cover - depende del entorno instalado
    from ._foundation.bearing_capacity import (
        BearingCapacityFormula as _CanonicalFormula,
    )
    from ._foundation.bearing_capacity import (
        drained_bearing_capacity as _canonical_drained_bearing_capacity,
    )
    from ._foundation.geometry import (
        RectangularFoundation as _CanonicalFoundation,
    )
    from ._foundation.soil import SoilLayer as _CanonicalSoilLayer

    _CANONICAL_IMPORT_ERROR: ImportError | None = None
except ImportError as _exc:  # pragma: no cover - depende del entorno instalado
    _CanonicalFormula = None  # type: ignore[assignment]
    _canonical_drained_bearing_capacity = None  # type: ignore[assignment]
    _CanonicalFoundation = None  # type: ignore[assignment]
    _CanonicalSoilLayer = None  # type: ignore[assignment]
    _CANONICAL_IMPORT_ERROR = _exc


@dataclass(frozen=True)
class BearingCapacityInput:
    B_m: float                          # ancho zapata
    L_m: float                          # largo
    D_f_m: float                        # profundidad desplante
    phi_deg: float                      # ángulo fricción
    c_kPa: float = 0.0                  # cohesión
    gamma_kN_m3: float = 18.0
    method: Literal["terzaghi", "meyerhof", "vesic", "brinch_hansen"] = "vesic"


@dataclass(frozen=True)
class BearingCapacityResult:
    q_ult_kPa: float                    # capacidad última
    q_adm_kPa: float                    # con FS o γ_R aplicado
    Nc: float
    Nq: float
    Ngamma: float
    code_applied: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "q_ult_kPa": self.q_ult_kPa, "q_adm_kPa": self.q_adm_kPa,
            "Nc": self.Nc, "Nq": self.Nq, "Ngamma": self.Ngamma,
            "code_applied": self.code_applied,
        }


def _bearing_factors(phi_deg: float, method: str
                       ) -> tuple[float, float, float]:
    phi = radians(phi_deg)
    Nq = exp(pi * tan(phi)) * (tan(pi / 4 + phi / 2)) ** 2
    Nc = (Nq - 1) / max(tan(phi), 1e-9) if phi_deg > 0 else 5.14
    if method == "terzaghi":
        Ngamma = (Nq - 1) * tan(1.4 * phi)
    elif method == "meyerhof":
        Ngamma = (Nq - 1) * tan(1.4 * phi)
    elif method == "vesic":
        Ngamma = 2 * (Nq + 1) * tan(phi)
    elif method == "brinch_hansen":
        Ngamma = 1.5 * (Nq - 1) * tan(phi)
    else:
        raise ValueError(f"método '{method}' no soportado")
    return Nc, Nq, Ngamma


def evaluate_bearing_ec7(
    *,
    B_m: float,
    L_m: float,
    D_f_m: float,
    phi_deg: float,
    c_kPa: float = 0.0,
    gamma_kN_m3: float = 18.0,
    e_B_m: float = 0.0,
    e_L_m: float = 0.0,
    H_kN: float = 0.0,
    V_kN: float = 0.0,
    thickness_m: float = 0.30,
    formula: str = "chen_ec7",
    gamma_Rv: float = 1.0,
    gamma_phi: float = 1.0,
    gamma_c: float = 1.0,
) -> Any:
    """Capacidad portante drenada — DELEGA en la implementación canónica.

    Puerta de Terzaghi hacia
    ``foundationcalc.analysis.bearing_capacity.drained_bearing_capacity``
    (EN 1997-1:2004 Anexo D). Devuelve **el objeto de la canónica sin
    envolver**: no se reimplementa ni se copia ninguna fórmula aquí, de modo
    que cualquier corrección en la canónica llega a Terzaghi sin tocar este
    fichero.

    Lo único que aporta esta función es la **conversión de unidades**: Terzaghi
    habla en metros y la canónica en MILÍMETROS. Ese es exactamente el error
    silencioso (factor ~1000, sin excepción) que se evita centralizándolo.

    ALCANCE — cláusula DRENADA (EN 1997-1 Anexo D.4). Para suelo cohesivo se
    pasa ``phi_deg=0`` y ``c_kPa=c_u``. Se MIDIÓ que en ese caso esta vía
    coincide **bit a bit** (diferencia 0.00e+00 kPa) con la cláusula no drenada
    D.3 de la canónica (``undrained_bearing_capacity``), con y sin
    excentricidad y con y sin inclinación — lo fija
    ``test_gate_phi_cero_coincide_bit_a_bit_con_la_clausula_no_drenada``.
    Coinciden porque en D.4 con φ=0 resulta N_q = 1, s_q = 1 e i_q = 1, de modo
    que el término de sobrecarga se reduce al ``+ q`` de D.3, y ambos usan el
    mismo N_c = π+2, s_c = 1+0.2·B/L e i_c.

    NO cubierto por esta puerta: nivel freático (NINGUNA de las cinco
    implementaciones del monorepo lo cablea dentro de la ecuación; la única
    con un enganche real de peso sumergido es el parámetro ``gamma_sub`` de
    ``fastsap.codes.bearing_capacity``, que ningún llamador usa). Si hay NF,
    pasa ``gamma_kN_m3`` = γ' del estrato de apoyo a sabiendas de que el
    término de sobrecarga usará ese mismo γ'.

    Frente a :func:`evaluate_bearing`, esta vía SÍ cubre:
      - área efectiva por excentricidad (Meyerhof): B' = B − 2·e_B, L' = L − 2·e_L
      - factores de inclinación de carga i_c/i_q/i_γ (Vesic / EN 1997-1 Anexo D)
      - factores de forma PUBLICADOS del Anexo D
      - factores parciales de material (γ_φ, γ_c) y de resistencia (γ_R,v)

    Args:
        B_m, L_m: ancho y largo de la zapata (m).
        D_f_m: profundidad de desplante (m).
        phi_deg, c_kPa, gamma_kN_m3: parámetros del suelo (grados, kPa, kN/m³).
        e_B_m, e_L_m: excentricidades en dirección B y L (m).
        H_kN, V_kN: cortante horizontal y axil vertical de diseño (kN). Con
            H_kN > 0 hace falta V_kN > 0: la canónica rechaza la combinación
            H>0 / V<=0 en vez de aprobarla en silencio.
        thickness_m: canto de la zapata (m); no interviene en q_ult.
        formula: autor de N_γ ("chen_ec7", "vesic", "meyerhof",
            "brinch_hansen"). El defecto es el del Anexo D.
        gamma_Rv, gamma_phi, gamma_c: factores parciales del Design Approach.

    Returns:
        ``foundationcalc.analysis.bearing_capacity.BearingCapacityResult``
        — con ``.q_ult``, los tres términos, N_c/N_q/N_γ, factores de forma e
        inclinación y las dimensiones efectivas.

    Raises:
        ImportError: si FoundationDesignJm no está instalado (se relanza el
            error original en vez de devolver un cero silencioso).
    """
    if _canonical_drained_bearing_capacity is None:
        raise ImportError(
            "terzaghi.bearing_capacity.evaluate_bearing_ec7 delega en la "
            "implementación canónica de FoundationDesignJm, que no se pudo "
            f"importar: {_CANONICAL_IMPORT_ERROR}. Instala el paquete "
            "'foundationcalc' del workspace."
        ) from _CANONICAL_IMPORT_ERROR

    return _canonical_drained_bearing_capacity(
        foundation=_CanonicalFoundation(
            length=L_m * 1000.0,            # m -> mm
            width=B_m * 1000.0,             # m -> mm
            thickness=thickness_m * 1000.0,  # m -> mm
            embedment_depth=D_f_m * 1000.0,  # m -> mm
        ),
        soil=_CanonicalSoilLayer(
            # ``thickness`` NO interviene en q_ult (la canónica sólo usa la capa
            # de apoyo); se fija a un literal para que no parezca un parámetro
            # de cálculo. El validador de la canónica exige > 0.
            thickness=10.0,
            friction_angle=phi_deg,
            cohesion=c_kPa,
            unit_weight=gamma_kN_m3,
        ),
        e_x=e_L_m,   # e_x recorta L (eje largo) en la canónica
        e_y=e_B_m,   # e_y recorta B (eje corto)
        H_load=H_kN,
        V_load=V_kN,
        gamma_Rv=gamma_Rv,
        gamma_phi=gamma_phi,
        gamma_c=gamma_c,
        formula=_CanonicalFormula(formula),
    )


def evaluate_bearing(inp: BearingCapacityInput, code: str = "EU"
                      ) -> BearingCapacityResult:
    """DEPRECADO — usa :func:`evaluate_bearing_ec7`.

    Calcula q_ult y aplica el factor parcial/FS del código, con factores de
    forma NO publicados y sin excentricidad ni inclinación. Sus valores se
    mantienen intactos por compatibilidad; ver el docstring del módulo para la
    medición que motivó la deprecación.
    """
    warnings.warn(
        "terzaghi.bearing_capacity.evaluate_bearing está deprecada: sus factores "
        "de forma no corresponden a ningún juego publicado y es ciega a la "
        "excentricidad y a la inclinación de carga (hasta +41 % del lado "
        "INSEGURO). Usa terzaghi.bearing_capacity.evaluate_bearing_ec7, que "
        "delega en la canónica foundationcalc.analysis.bearing_capacity "
        "(EN 1997-1 Anexo D).",
        DeprecationWarning,
        stacklevel=2,
    )
    Nc, Nq, Ngamma = _bearing_factors(inp.phi_deg, inp.method)

    # Factores de forma simplificados (Meyerhof / Vesic)
    sB_L = inp.B_m / inp.L_m if inp.L_m > 0 else 1.0
    Sc = 1 + 0.2 * sB_L
    Sq = 1 + 0.1 * sB_L
    Sgamma = 1 - 0.1 * sB_L

    q = inp.gamma_kN_m3 * inp.D_f_m  # sobrecarga
    q_ult = (
        inp.c_kPa * Nc * Sc
        + q * Nq * Sq
        + 0.5 * inp.gamma_kN_m3 * inp.B_m * Ngamma * Sgamma
    )

    # Aplicar factor por código
    if code in ("EU", "SG"):
        q_adm = q_ult / 1.40        # γ_R,v = 1.4 (R3 EC7)
    elif code == "US":
        q_adm = 0.50 * q_ult         # φ ≈ 0.50 (AASHTO LRFD)
    elif code == "CO":
        q_adm = q_ult / 3.0          # FS = 3 (NSR-10 estático)
    elif code == "AU":
        q_adm = 0.45 * q_ult         # AS 2159 método Brinch Hansen
    else:
        raise ValueError(f"código '{code}' no soportado")

    return BearingCapacityResult(
        q_ult_kPa=q_ult, q_adm_kPa=q_adm,
        Nc=Nc, Nq=Nq, Ngamma=Ngamma, code_applied=code,
    )


__all__ = [
    "BearingCapacityInput",
    "BearingCapacityResult",
    "evaluate_bearing",       # DEPRECADO
    "evaluate_bearing_ec7",   # delega en la canónica
]
