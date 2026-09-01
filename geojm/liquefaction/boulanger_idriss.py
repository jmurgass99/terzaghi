"""
Evaluacion de potencial de licuacion — Boulanger & Idriss (2014).

Formulacion simplificada con las ecuaciones explicitas del paper:

    CRR_M7.5 = exp(N1_60cs/14.1 + (N1_60cs/126)^2
                    - (N1_60cs/23.6)^3 + (N1_60cs/25.4)^4 - 2.8)

    CSR = 0.65 * (amax/g) * (sigma_v / sigma'_v) * rd

    rd = exp(alpha(z) + beta(z)*M)       (B&I 2014)

    FS_liq = (CRR / CSR) * MSF * K_sigma

    MSF = 6.9*exp(-M/4) - 0.058  (<=1.8)

    K_sigma = 1 - C_sigma * ln(sigma'_v / Pa)
    C_sigma = 1 / (18.9 - 2.55*sqrt(N1_60cs))
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, sqrt
from typing import Any


@dataclass(frozen=True)
class BoulangerIdrissInput:
    """Datos de entrada para evaluacion B&I 2014."""
    depth_m: float
    sigma_v_kPa: float         # esfuerzo vertical total
    sigma_v_eff_kPa: float     # esfuerzo vertical efectivo
    N1_60cs: float             # SPT corregido + finos-equivalente
    a_max_g: float             # PGA (g)
    Mw: float = 7.5            # magnitud de momento


@dataclass(frozen=True)
class BoulangerIdrissResult:
    """Resultados de la evaluacion B&I 2014."""
    CSR: float
    CRR: float
    MSF: float
    K_sigma: float
    rd: float
    FS: float
    is_liquefiable: bool       # FS < 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "CSR": self.CSR, "CRR": self.CRR,
            "MSF": self.MSF, "K_sigma": self.K_sigma,
            "rd": self.rd, "FS": self.FS,
            "is_liquefiable": self.is_liquefiable,
        }


def _rd_bi2014(depth_m: float, Mw: float) -> float:
    """Factor de reduccion por profundidad — Boulanger & Idriss 2014.

    rd = exp(alpha(z) + beta(z)*M)
    alpha(z) = -1.012 - 1.126*sin(z/11.73 + 5.133)
    beta(z) = 0.106 + 0.118*sin(z/11.28 + 5.142)
    Aplicable para z <= 34m; mas alla se satura.
    """
    from math import sin as _sin
    z = min(depth_m, 34.0)
    alpha = -1.012 - 1.126 * _sin(z / 11.73 + 5.133)
    beta = 0.106 + 0.118 * _sin(z / 11.28 + 5.142)
    return exp(alpha + beta * Mw)


def _crr_m75(N1_60cs: float) -> float:
    """CRR a Mw=7.5 — Boulanger & Idriss 2014.

    CRR = exp(N/14.1 + (N/126)^2 - (N/23.6)^3 + (N/25.4)^4 - 2.8)
    """
    N = min(N1_60cs, 37.0)
    return exp(
        N / 14.1
        + (N / 126.0) ** 2
        - (N / 23.6) ** 3
        + (N / 25.4) ** 4
        - 2.8
    )


def _msf_bi2014(Mw: float, N1_60cs: float = 14.0) -> float:
    """Magnitude Scaling Factor — Boulanger & Idriss 2014 completo.

    MSFmax = 1.09 + (N1_60cs/31.5)^2  (<=2.2)
    MSF = 1 + (MSFmax - 1) * (8.64*exp(-Mw/4) - 1.325)
    Saturado a [1.0, MSFmax].
    """
    MSFmax = min(1.09 + (min(N1_60cs, 37.0) / 31.5) ** 2, 2.2)
    msf = 1.0 + (MSFmax - 1.0) * (8.64 * exp(-Mw / 4.0) - 1.325)
    return min(msf, MSFmax)


def _k_sigma_bi2014(sigma_v_eff_kPa: float, N1_60cs: float) -> float:
    """Factor de correccion por presion de confinamiento.

    K_sigma = 1 - C_sigma * ln(sigma'_v / Pa)
    C_sigma = 1 / (18.9 - 2.55 * sqrt(N1_60cs))
    Pa = 100 kPa (presion atmosferica)
    """
    Pa = 100.0  # kPa
    N_capped = min(N1_60cs, 37.0)
    denom = 18.9 - 2.55 * sqrt(N_capped)
    if denom <= 0:
        C_sigma = 0.3
    else:
        C_sigma = min(1.0 / denom, 0.3)

    ratio = sigma_v_eff_kPa / Pa
    if ratio <= 0:
        return 1.0
    K_sig = 1.0 - C_sigma * log(ratio)
    return max(min(K_sig, 1.1), 0.5)


def evaluate_bi2014(inp: BoulangerIdrissInput) -> BoulangerIdrissResult:
    """Evalua el factor de seguridad contra licuacion — B&I 2014.

    Returns:
        BoulangerIdrissResult con FS, CSR, CRR, MSF, K_sigma, rd.
    """
    if inp.sigma_v_eff_kPa <= 0:
        raise ValueError("sigma_v_eff_kPa debe ser > 0")
    if inp.a_max_g <= 0:
        raise ValueError("a_max_g debe ser > 0")

    rd = _rd_bi2014(inp.depth_m, inp.Mw)
    CSR = 0.65 * (inp.a_max_g) * (inp.sigma_v_kPa / inp.sigma_v_eff_kPa) * rd
    CRR = _crr_m75(inp.N1_60cs)
    MSF = _msf_bi2014(inp.Mw, inp.N1_60cs)
    K_sigma = _k_sigma_bi2014(inp.sigma_v_eff_kPa, inp.N1_60cs)

    FS = (CRR / max(CSR, 1e-9)) * MSF * K_sigma

    return BoulangerIdrissResult(
        CSR=CSR,
        CRR=CRR,
        MSF=MSF,
        K_sigma=K_sigma,
        rd=rd,
        FS=FS,
        is_liquefiable=FS < 1.0,
    )


@dataclass(frozen=True)

class ProfileLiquefactionResult:
    evaluated: bool
    status: str
    layers: list[dict[str, Any]]
    min_FS: float | None
    has_liquefiable_stratum: bool
    n_layers_not_evaluated: int = 0
    """Capas descartadas por no traer N1_60cs.

    Si es > 0, ``has_liquefiable_stratum=False`` significa "ninguna de las capas
    EVALUADAS lo es", no que el perfil este libre de licuacion.
    """

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluated": self.evaluated,
            "status": self.status,
            "layers": self.layers,
            "min_FS": self.min_FS,
            "has_liquefiable_stratum": self.has_liquefiable_stratum,
            "n_layers_not_evaluated": self.n_layers_not_evaluated,
        }


def evaluate_spt_profile_liquefaction(
    spt_layers: list[dict[str, Any]] | None,
    a_max_g: float = 0.30,
    Mw: float = 7.5,
) -> ProfileLiquefactionResult:
    """Evalúa licuación multicapa con Boulanger & Idriss (2014) o reporta no evaluación si no hay datos SPT."""
    if not spt_layers:
        return ProfileLiquefactionResult(
            evaluated=False,
            status="NO EVALUADO (sin datos de SPT)",
            layers=[],
            min_FS=None,
            has_liquefiable_stratum=False,
        )

    layer_results: list[dict[str, Any]] = []
    min_fs = float("inf")
    any_liq = False

    n_sin_ensayo = 0

    for ly in spt_layers:
        depth = float(ly["depth_m"])
        sv = float(ly["sigma_v_kPa"])
        sveff = float(ly["sigma_v_eff_kPa"])

        # DEFECTO CORREGIDO: aqui habia un `.get(..., 15.0)`. Si una capa no
        # traia el ensayo SPT se INVENTABA N1_60cs = 15.0 y se calculaba un
        # factor de seguridad sobre un dato fabricado. Y 15 no es un valor
        # neutro: cae justo en la frontera licuable / no licuable, asi que el
        # resultado salia plausible en cualquier direccion. Ademas era el UNICO
        # parametro que se rellenaba en silencio —depth_m, sigma_v_kPa y
        # sigma_v_eff_kPa si lanzaban KeyError— y precisamente el que gobierna
        # la resistencia. Todo ello en el modulo cuyo titular es el reporte
        # defensivo "NO EVALUADO (sin datos de SPT)".
        raw_n160 = ly.get("N1_60cs", ly.get("N1_60_cs"))
        if raw_n160 is None:
            n_sin_ensayo += 1
            layer_results.append({
                "depth_m": depth,
                "N1_60cs": None,
                "sigma_v_kPa": sv,
                "sigma_v_eff_kPa": sveff,
                "CSR": None,
                "CRR": None,
                "MSF": None,
                "K_sigma": None,
                "FS": None,
                "is_liquefiable": None,
                "status": "NO EVALUADA (sin N1_60cs)",
            })
            continue
        n160 = float(raw_n160)

        res = evaluate_bi2014(
            BoulangerIdrissInput(
                depth_m=depth,
                sigma_v_kPa=sv,
                sigma_v_eff_kPa=sveff,
                N1_60cs=n160,
                a_max_g=a_max_g,
                Mw=Mw,
            )
        )
        layer_results.append({
            "depth_m": depth,
            "N1_60cs": n160,
            "sigma_v_kPa": sv,
            "sigma_v_eff_kPa": sveff,
            "CSR": res.CSR,
            "CRR": res.CRR,
            "MSF": res.MSF,
            "K_sigma": res.K_sigma,
            "FS": res.FS,
            "is_liquefiable": res.is_liquefiable,
            "status": "EVALUADA",
        })
        if res.FS < min_fs:
            min_fs = res.FS
        if res.is_liquefiable:
            any_liq = True

    n_evaluadas = len(layer_results) - n_sin_ensayo

    if n_evaluadas == 0:
        return ProfileLiquefactionResult(
            evaluated=False,
            status=(
                f"NO EVALUADO (ninguna de las {n_sin_ensayo} capas trae N1_60cs)"
            ),
            layers=layer_results,
            min_FS=None,
            has_liquefiable_stratum=False,
            n_layers_not_evaluated=n_sin_ensayo,
        )

    if n_sin_ensayo:
        status = (
            f"EVALUADO PARCIALMENTE (Boulanger & Idriss 2014): "
            f"{n_evaluadas} de {len(layer_results)} capas. "
            f"{n_sin_ensayo} sin N1_60cs y por tanto SIN evaluar — la ausencia "
            f"de estrato licuable NO esta establecida para el perfil completo."
        )
    else:
        status = "EVALUADO (Boulanger & Idriss 2014)"

    return ProfileLiquefactionResult(
        evaluated=True,
        status=status,
        layers=layer_results,
        min_FS=min_fs,
        has_liquefiable_stratum=any_liq,
        n_layers_not_evaluated=n_sin_ensayo,
    )


__all__ = [
    "BoulangerIdrissInput",
    "BoulangerIdrissResult",
    "ProfileLiquefactionResult",
    "evaluate_bi2014",
    "evaluate_spt_profile_liquefaction",
]

