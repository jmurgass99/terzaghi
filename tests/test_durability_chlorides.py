"""Suite 2.1 — Difusión de cloruros por la 2ª ley de Fick.

Valores de referencia cerrados (no round-trip):
  C(x=0,t)  = Cs           (erf(0)=0)
  C(x,t→∞)  → Cs           (arg→0)
  C(x→∞,t)  → C0           (erf→1)
"""
import math

import pytest

from terzaghi.durability.chlorides import ChlorideInput, concentration, time_to_initiation


@pytest.fixture
def inp():
    # Caso típico marino: Cs=0.8% peso cemento, D=10 mm²/año, recubrimiento 50 mm
    return ChlorideInput(
        Cs_pct=0.80, C0_pct=0.0, D_mm2_per_year=10.0,
        cover_mm=50.0, C_crit_pct=0.40,
    )


def test_surface_equals_Cs(inp):
    # En la superficie x=0 → C = Cs exactamente
    assert concentration(0.0, 25.0, inp) == pytest.approx(inp.Cs_pct, rel=1e-12)


def test_long_time_tends_to_Cs(inp):
    # t muy grande → toda la sección tiende a Cs
    assert concentration(50.0, 1e9, inp) == pytest.approx(inp.Cs_pct, rel=1e-3)


def test_deep_tends_to_C0(inp):
    # x muy grande respecto al frente difusivo → C → C0
    assert concentration(1e6, 25.0, inp) == pytest.approx(inp.C0_pct, abs=1e-9)


def test_monotonic_decreasing_in_x(inp):
    c10 = concentration(10.0, 25.0, inp)
    c30 = concentration(30.0, 25.0, inp)
    c50 = concentration(50.0, 25.0, inp)
    assert c10 > c30 > c50


def test_time_to_initiation_consistency(inp):
    # En t = t_init la concentración en el recubrimiento debe igualar C_crit
    t = time_to_initiation(inp)
    assert t > 0
    c_at_cover = concentration(inp.cover_mm, t, inp)
    assert c_at_cover == pytest.approx(inp.C_crit_pct, rel=1e-4)


def test_time_scales_with_cover_squared(inp):
    # t_init ∝ x²  (ley de Fick): doblar recubrimiento → ×4 el tiempo
    t1 = time_to_initiation(inp)
    inp2 = ChlorideInput(
        Cs_pct=inp.Cs_pct, C0_pct=inp.C0_pct, D_mm2_per_year=inp.D_mm2_per_year,
        cover_mm=2 * inp.cover_mm, C_crit_pct=inp.C_crit_pct,
    )
    t2 = time_to_initiation(inp2)
    assert t2 / t1 == pytest.approx(4.0, rel=1e-4)


def test_no_initiation_when_crit_above_Cs(inp):
    # Si el umbral crítico es mayor que Cs, nunca se inicia la corrosión
    bad = ChlorideInput(Cs_pct=0.3, C0_pct=0.0, D_mm2_per_year=10.0,
                        cover_mm=50.0, C_crit_pct=0.4)
    assert time_to_initiation(bad) == math.inf
