"""Tests for terzaghi engineering, normative, and API improvements."""
from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from terzaghi.api.app import create_app
from terzaghi.bearing_capacity import evaluate_bearing_ec7
from terzaghi.excavation import ExcavationInput, check_excavation
from terzaghi.integration.fastsap_pysprings import PySpringNode, build_py_curve
from terzaghi.memos.pile_group_lateral import (
    PileGroupLateralInput,
    fm_brown_1988,
    render_pile_group_memo,
)
from terzaghi.site_response.wave_propagation_1d import (
    SoilLayer1D,
    propagate_1d,
    transfer_function_multilayer_kramer,
)
from terzaghi.wave_propagation_1d import SoilLayer, propagate_sh_wave


def test_evaluate_bearing_ec7_water_table_reduces_q_ult() -> None:
    base = dict(B_m=2.0, L_m=3.0, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0, gamma_kN_m3=19.0)
    r_dry = evaluate_bearing_ec7(**base)
    r_zw_base = evaluate_bearing_ec7(**base, zw_m=1.5)
    r_zw_surface = evaluate_bearing_ec7(**base, zw_m=0.0)
    assert r_dry.q_ult > r_zw_base.q_ult > r_zw_surface.q_ult


def test_api_bearing_capacity_routes_to_ec7_canonical() -> None:
    client = TestClient(create_app())
    r_centered = client.post(
        "/api/geo/bearing-capacity",
        json={
            "B_m": 2.5,
            "L_m": 2.5,
            "D_f_m": 1.5,
            "phi_deg": 32.0,
            "c_kPa": 0.0,
            "gamma_kN_m3": 19.0,
            "method": "chen_ec7",
            "code": "EU",
        },
    )
    assert r_centered.status_code == 200
    d_centered = r_centered.json()

    r_ecc_inc = client.post(
        "/api/geo/bearing-capacity",
        json={
            "B_m": 2.5,
            "L_m": 2.5,
            "D_f_m": 1.5,
            "phi_deg": 32.0,
            "c_kPa": 0.0,
            "gamma_kN_m3": 19.0,
            "method": "chen_ec7",
            "code": "EU",
            "e_B_m": 0.30,
            "H_kN": 150.0,
            "V_kN": 1000.0,
        },
    )
    assert r_ecc_inc.status_code == 200
    d_ecc = r_ecc_inc.json()
    assert d_ecc["q_ult_kPa"] < d_centered["q_ult_kPa"]
    assert d_ecc["B_eff_m"] == pytest.approx(1.90)


def test_multilayer_kramer_impedance_recursion() -> None:
    dt = 0.005
    t = np.arange(0.0, 5.0, dt)
    accel = 0.1 * np.sin(2.0 * np.pi * 2.0 * t)
    profile_1d = [
        SoilLayer1D(thickness_m=10.0, Vs_m_s=150.0, density_kg_m3=1800.0, damping_ratio=0.05),
        SoilLayer1D(thickness_m=15.0, Vs_m_s=300.0, density_kg_m3=2000.0, damping_ratio=0.04),
    ]
    res_kramer = propagate_1d(
        accel,
        dt,
        profile_1d,
        bedrock_Vs=1500.0,
        bedrock_density=2500.0,
        use_impedance_recursion=True,
        input_motion_type="outcrop",
    )
    assert res_kramer.amplification_factor > 1.0
    assert len(res_kramer.gamma_max_profile) == 2

    omegas = np.array([0.0, 2.0 * np.pi * 1.5])
    H_out, _ = transfer_function_multilayer_kramer(omegas, profile_1d, input_motion_type="outcrop")
    H_in, _ = transfer_function_multilayer_kramer(omegas, profile_1d, input_motion_type="within")
    assert H_out[0] == pytest.approx(1.0)
    assert H_in[0] == pytest.approx(1.0)
    assert not np.isclose(abs(H_out[1]), abs(H_in[1]))

    profile_sh = [SoilLayer(thickness_m=10.0, Vs_m_per_s=150.0, damping_ratio=0.05)]
    res_sh = propagate_sh_wave(accel, dt, profile_sh, use_impedance_recursion=True)
    assert res_sh.amplification_factor > 1.0


def test_excavation_plug_uplift_and_piping() -> None:
    r = check_excavation(
        ExcavationInput(
            depth_m=6.0,
            width_m=8.0,
            length_m=12.0,
            su_kPa=90.0,
            gamma_kN_m3=19.0,
            water_table_depth_m=2.0,
            plug_thickness_m=3.0,
            hydraulic_gradient_i=0.45,
        )
    )
    # h_w at bottom of plug = (6 + 3) - 2 = 7 m -> u = 9.81 * 7 = 68.67 kPa
    # W_plug = 19 * 3 = 57 kPa -> FS_uplift = 57 / 68.67 = 0.830
    assert r.FS_uplift == pytest.approx((19.0 * 3.0) / (9.81 * 7.0), rel=1e-4)
    assert r.FS_piping is not None
    assert r.FS_piping == pytest.approx(((19.0 - 9.81) / 9.81) / 0.45, rel=1e-4)
    assert not r.is_safe


def test_fastsap_pysprings_reese_sand_option() -> None:
    node = PySpringNode(z_m=3.0, D_m=0.6, phi_deg=32.0, gamma_kN_m3=18.0)
    pts_legacy = build_py_curve(node, n=12, sand_model="legacy")
    pts_reese = build_py_curve(node, n=12, sand_model="reese_1974")
    assert len(pts_reese) == 12
    assert pts_reese[-1][1] != pytest.approx(pts_legacy[-1][1])
    assert pts_reese[-1][1] > pts_legacy[-1][1]


def test_pile_group_memo_brown_1988_method() -> None:
    inp = PileGroupLateralInput(
        n_rows=3,
        n_cols=3,
        D_m=0.6,
        s_m=1.8,  # s/D = 3.0
        P_single_kN=200.0,
        method="brown_1988",
    )
    res = render_pile_group_memo(inp)
    assert res.fm_per_row == [0.80, 0.40, 0.30]
    assert res.efficiency == pytest.approx(0.50)
    assert "Brown et al. (1988)" in res.memo_text
    assert fm_brown_1988(2, 4.0) == pytest.approx(0.625)
