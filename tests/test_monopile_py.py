"""Tests unitarios para curvas P-y dinámicas y cíclicas de monopilotes en Terzaghi."""

import pytest
from fastapi.testclient import TestClient
from terzaghi.piles.dynamic_py import (
    calculate_monopile_dynamic_py,
    MonopileDynamicPyInput,
)
from terzaghi.api.app import create_app

client = TestClient(create_app())


def test_monopile_dynamic_py_clay():
    """Prueba física de las curvas P-y en suelo arcilloso."""
    # Monopilote de D = 6.0m en arcilla, Vs = 160 m/s
    inp = MonopileDynamicPyInput(
        z_m=5.0,
        D_m=6.0,
        Vs_m_per_s=160.0,
        rho_soil_kg_m3=1900.0,
        soil_type="clay",
        su_kPa=80.0,
        gamma_kN_m3=18.0,
        eps_50=0.01,
        frequency_Hz=0.3,
        num_cycles=500,
        degradation_coef=0.05,
        dynamic_coef=0.20,
        n_points=30
    )
    res = calculate_monopile_dynamic_py(inp)
    
    assert res.z_m == 5.0
    assert res.D_m == 6.0
    
    # Reducción cíclica: 1 - 0.05 * log10(500) = 1 - 0.05 * 2.69897 = 1 - 0.1349 = 0.865
    # p_ult_cyclic = p_ult_static * 0.865
    assert res.p_ult_cyclic_kN_m == pytest.approx(res.p_ult_static_kN_m * (1.0 - 0.05 * 2.698970004))
    
    # Rigidez dinámica:
    # omega = 2 * pi * 0.3 = 1.8849
    # a0 = 1.8849 * 6.0 / 160 = 0.07068
    # stiffness_multiplier = 1 + 0.20 * a0^2 = 1 + 0.20 * 0.004996 = 1.00099
    assert res.stiffness_multiplier == pytest.approx(1.0 + 0.20 * (1.88495559 * 6.0 / 160.0) ** 2)
    
    # Validar curvas resultantes
    assert len(res.y_m) == 30
    assert len(res.p_static_kN_m) == 30
    assert len(res.p_dynamic_kN_m) == 30
    assert res.p_dynamic_kN_m[-1] == pytest.approx(res.p_ult_cyclic_kN_m)


def test_monopile_dynamic_py_sand():
    """Prueba física de las curvas P-y en suelo arenoso."""
    # Monopilote en arena
    inp = MonopileDynamicPyInput(
        z_m=3.0,
        D_m=5.0,
        Vs_m_per_s=180.0,
        rho_soil_kg_m3=1850.0,
        soil_type="sand",
        phi_deg=34.0,
        gamma_kN_m3=17.5,
        k_pH_kN_m3=22000.0,
        frequency_Hz=0.5,
        num_cycles=1000,
        degradation_coef=0.08,
        dynamic_coef=0.15,
        n_points=40
    )
    res = calculate_monopile_dynamic_py(inp)
    
    assert res.p_ult_static_kN_m > 0.0
    # Reducción cíclica: 1 - 0.08 * 3 = 0.76
    assert res.p_ult_cyclic_kN_m == pytest.approx(res.p_ult_static_kN_m * 0.76)
    assert len(res.y_m) == 40


def test_api_monopile_endpoint():
    """Prueba del endpoint FastAPI para curvas P-y dinámicas."""
    payload = {
        "z_m": 4.0,
        "D_m": 6.5,
        "Vs_m_per_s": 150.0,
        "soil_type": "sand",
        "phi_deg": 35.0,
        "frequency_Hz": 0.25,
        "num_cycles": 800,
        "degradation_coef": 0.06,
        "dynamic_coef": 0.25
    }
    response = client.post("/api/geo/monopile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "p_ult_static_kN_m" in data
    assert "p_ult_cyclic_kN_m" in data
    assert "y_m" in data
    assert "p_dynamic_kN_m" in data
