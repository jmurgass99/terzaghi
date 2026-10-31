"""Tests para IDEAS_20 grupos A/B/C en Terzaghi."""
import pytest


def test_van_genuchten_y_bishop():
    from terzaghi.unsaturated import (
        VanGenuchtenParams, theta_of_psi, chi_bishop, shear_strength_unsat,
    )
    p = VanGenuchtenParams()
    assert theta_of_psi(0, p) == pytest.approx(p.theta_s)
    t = theta_of_psi(2, p)
    assert p.theta_r < t < p.theta_s
    chi = chi_bishop(2, p)
    assert 0 < chi < 1
    tau = shear_strength_unsat(100, 0, -10, 2, 0, 30, p)
    assert tau > 0


def test_van_genuchten_decay():
    from terzaghi.unsaturated import VanGenuchtenParams, theta_of_psi
    p = VanGenuchtenParams()
    assert theta_of_psi(0.5, p) > theta_of_psi(5.0, p)


def test_mokwa_duncan():
    from terzaghi.piles.mokwa_duncan import MokwaDuncanInput, analyze, p_multiplier
    assert p_multiplier(1) == 1.0
    assert p_multiplier(5) == 0.4
    res = analyze(MokwaDuncanInput(
        n_rows=3, n_cols=3, D_m=0.6, s_m=2.0, L_pile_m=10, H_emb_m=5,
        phi_deg=30, c_kPa=20, code="EU",
    ))
    assert res.H_group_total_kN > 0
    assert 0 < res.p_multiplier_avg <= 1.0


def test_estratigrafias_catalogo():
    from terzaghi.estratigrafias_catalogo import list_profiles, get_profile
    profs = list_profiles()
    assert "santiago_grava" in profs
    assert "bogota_lacustre" in profs
    sg = get_profile("santiago_grava")
    assert len(sg) >= 2
    with pytest.raises(KeyError):
        get_profile("inexistente")


def test_fastsap_pysprings_dry_run():
    from terzaghi.integration.fastsap_pysprings import (
        PySpringNode, FastSAPPySpringsConfig, build_py_curve, export_to_fastsap,
    )
    nodes = (
        PySpringNode(z_m=1.0, D_m=0.6, su_kPa=50),
        PySpringNode(z_m=3.0, D_m=0.6, phi_deg=32),
    )
    cfg = FastSAPPySpringsConfig(nodes=nodes, code="EU")
    res = export_to_fastsap(cfg, dry_run=True)
    assert res["dry_run"] is True
    assert res["applied"] == 2
    curve = build_py_curve(nodes[0])
    assert len(curve) == 12


def test_fastsap_pysprings_mock_client():
    from unittest.mock import MagicMock
    from terzaghi.integration.fastsap_pysprings import (
        PySpringNode, FastSAPPySpringsConfig, export_to_fastsap,
    )
    mock = MagicMock()
    cfg = FastSAPPySpringsConfig(nodes=(PySpringNode(z_m=1, D_m=0.5, su_kPa=40),))
    res = export_to_fastsap(cfg, client=mock, dry_run=False)
    assert res["dry_run"] is False
