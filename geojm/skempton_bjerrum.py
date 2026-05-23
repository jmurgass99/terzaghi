"""
Asentamiento por consolidación con corrección Skempton-Bjerrum (idea #12).

S_real = mu * S_oed, donde mu depende de A (parámetro Skempton, [0..1])
y de la geometría H/B. Se tabula según Bjerrum 1972.

Para soporte multi-code:
- EU (EC 7): permitir factor μ explícito
- USA (ACI/AASHTO): igual
- NSR-10 / AS / SG: igual
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SkemptonBjerrumInput:
    S_oedometer_mm: float
    A_pore: float             # parámetro Skempton A
    H_over_B: float           # H del estrato/2*B
    code: str = "EU"


@dataclass(frozen=True)
class SkemptonResult:
    mu: float
    settlement_corrected_mm: float
    code: str


def _interp_mu(A: float, hb: float) -> float:
    """Interpolación bilineal de tabla Bjerrum 1972 (clay overconsolidated
    a normally consolidated). Tabla aproximada simplificada."""
    # Tabla μ para A en [0, 0.5, 1.0] y H/B en [0, 0.5, 1, 4, infinito]
    # Fuente: Bjerrum 1972 - circular footing
    table = {
        0.0: {0.0: 1.0, 0.5: 0.5, 1.0: 0.4, 4.0: 0.3, 10.0: 0.25},
        0.5: {0.0: 1.0, 0.5: 0.7, 1.0: 0.6, 4.0: 0.55, 10.0: 0.5},
        1.0: {0.0: 1.0, 0.5: 1.0, 1.0: 1.0, 4.0: 1.0, 10.0: 1.0},
    }
    A_clamp = max(0.0, min(1.0, A))
    hb_clamp = max(0.0, min(10.0, hb))
    # Encuentra A bounds
    A_keys = sorted(table.keys())
    if A_clamp <= A_keys[0]:
        Alo, Ahi = A_keys[0], A_keys[0]
    elif A_clamp >= A_keys[-1]:
        Alo, Ahi = A_keys[-1], A_keys[-1]
    else:
        for i in range(len(A_keys) - 1):
            if A_keys[i] <= A_clamp <= A_keys[i + 1]:
                Alo, Ahi = A_keys[i], A_keys[i + 1]
                break

    def interp_h(rowA):
        hb_keys = sorted(rowA.keys())
        if hb_clamp <= hb_keys[0]:
            return rowA[hb_keys[0]]
        if hb_clamp >= hb_keys[-1]:
            return rowA[hb_keys[-1]]
        for i in range(len(hb_keys) - 1):
            if hb_keys[i] <= hb_clamp <= hb_keys[i + 1]:
                lo, hi = hb_keys[i], hb_keys[i + 1]
                t = (hb_clamp - lo) / (hi - lo)
                return rowA[lo] * (1 - t) + rowA[hi] * t
        return rowA[hb_keys[-1]]

    mu_lo = interp_h(table[Alo])
    mu_hi = interp_h(table[Ahi])
    if Ahi == Alo:
        return mu_lo
    t = (A_clamp - Alo) / (Ahi - Alo)
    return mu_lo * (1 - t) + mu_hi * t


def skempton_bjerrum(inp: SkemptonBjerrumInput) -> SkemptonResult:
    if inp.S_oedometer_mm < 0:
        raise ValueError("S_oedometer >= 0")
    c = inp.code.upper()
    if c not in ("EU", "EUROCODE", "USA", "ASCE", "NSR", "CO", "AS", "AU", "SG", "SS"):
        raise ValueError(f"Código desconocido: {inp.code}")
    mu = _interp_mu(inp.A_pore, inp.H_over_B)
    return SkemptonResult(mu=mu, settlement_corrected_mm=mu * inp.S_oedometer_mm,
                          code=inp.code)


def differential_settlement_ratio(s1_mm: float, s2_mm: float, span_m: float) -> float:
    """Distorsión angular delta/L (rad) entre dos puntos."""
    if span_m <= 0:
        raise ValueError("span_m > 0")
    return abs(s1_mm - s2_mm) / 1000.0 / span_m
