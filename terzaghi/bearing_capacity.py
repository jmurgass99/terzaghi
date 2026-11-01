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
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from math import exp, pi, radians, tan
from typing import Any, Literal

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
    zw_m: float | None = None,
    gamma_sat_kN_m3: float | None = None,
) -> Any:
    """Capacidad portante drenada — DELEGA en la implementación canónica (EN 1997-1 Anexo D).

    Cuando ``zw_m`` (profundidad del nivel freático desde la superficie en metros)
    se especifica, calcula automáticamente la presión efectiva de sobrecarga ``q'``
    en el nivel de desplante ``D_f_m`` y el peso específico efectivo ``gamma_eff``
    en la cuña de rotura bajo la base (entre ``D_f_m`` y ``D_f_m + B_eff``).
    """
    if _canonical_drained_bearing_capacity is None:
        raise ImportError(
            "terzaghi.bearing_capacity.evaluate_bearing_ec7 delega en la "
            "implementación canónica de FoundationDesignJm, que no se pudo "
            f"importar: {_CANONICAL_IMPORT_ERROR}. Instala el paquete "
            "'foundationcalc' del workspace."
        ) from _CANONICAL_IMPORT_ERROR

    if zw_m is None:
        return _canonical_drained_bearing_capacity(
            foundation=_CanonicalFoundation(
                length=L_m * 1000.0,            # m -> mm
                width=B_m * 1000.0,             # m -> mm
                thickness=thickness_m * 1000.0,  # m -> mm
                embedment_depth=D_f_m * 1000.0,  # m -> mm
            ),
            soil=_CanonicalSoilLayer(
                thickness=10.0,
                friction_angle=phi_deg,
                cohesion=c_kPa,
                unit_weight=gamma_kN_m3,
            ),
            e_x=e_L_m,
            e_y=e_B_m,
            H_load=H_kN,
            V_load=V_kN,
            gamma_Rv=gamma_Rv,
            gamma_phi=gamma_phi,
            gamma_c=gamma_c,
            formula=_CanonicalFormula(formula),
        )

    gamma_w = 9.81
    gamma_sat = gamma_sat_kN_m3 if gamma_sat_kN_m3 is not None else gamma_kN_m3
    gamma_sub = max(gamma_sat - gamma_w, 1.0)

    # 1. Presión vertical efectiva q' al nivel de desplante D_f_m
    if zw_m <= 0.0:
        q_eff = gamma_sub * D_f_m
    elif zw_m < D_f_m:
        q_eff = gamma_kN_m3 * zw_m + gamma_sub * (D_f_m - zw_m)
    else:
        q_eff = gamma_kN_m3 * D_f_m

    # 2. Peso específico efectivo en la cuña bajo la base (profundidad B' bajo D_f_m)
    B_eff_est = max(min(B_m - 2.0 * abs(e_B_m), L_m - 2.0 * abs(e_L_m)), 1e-6)
    if zw_m <= D_f_m:
        gamma_wedge = gamma_sub
    elif zw_m < D_f_m + B_eff_est:
        frac = (zw_m - D_f_m) / B_eff_est
        gamma_wedge = gamma_sub + frac * (gamma_kN_m3 - gamma_sub)
    else:
        gamma_wedge = gamma_kN_m3

    return _canonical_drained_bearing_capacity(
        foundation=_CanonicalFoundation(
            length=L_m * 1000.0,
            width=B_m * 1000.0,
            thickness=thickness_m * 1000.0,
            embedment_depth=D_f_m * 1000.0,
        ),
        soil=_CanonicalSoilLayer(
            thickness=10.0,
            friction_angle=phi_deg,
            cohesion=c_kPa,
            unit_weight=gamma_wedge,
        ),
        e_x=e_L_m,
        e_y=e_B_m,
        H_load=H_kN,
        V_load=V_kN,
        overburden_pressure=q_eff,
        gamma_Rv=gamma_Rv,
        gamma_phi=gamma_phi,
        gamma_c=gamma_c,
        formula=_CanonicalFormula(formula),
    )


def evaluate_bearing(inp: BearingCapacityInput, code: str = "EU"
                      ) -> BearingCapacityResult:
    """DEPRECADO — usa :func:`evaluate_bearing_ec7`."""
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
