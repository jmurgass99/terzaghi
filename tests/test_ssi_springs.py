"""Tests unitarios para el cálculo de resortes dinámicos SSI Gazetas/Novak en GeoJm."""

import pytest
from fastapi.testclient import TestClient
from geojm.ssi_springs import (
    calculate_ssi_springs,
    SsiSpringsInput,
)
from geojm.api.app import create_app

client = TestClient(create_app())


def test_ssi_springs_calculus():
    """Verifica las ecuaciones físicas del módulo de resortes dinámicos y dashpots SSI."""
    # Zapata 5.0m x 3.0m, Vs = 180m/s, densidad = 1850 kg/m3, nu = 0.35, frecuencia = 8 Hz, damping = 0.05
    inp = SsiSpringsInput(
        L_m=5.0,
        B_m=3.0,
        Vs_m_per_s=180.0,
        rho_soil_kg_m3=1850.0,
        nu_soil=0.35,
        frequency_Hz=8.0,
        material_damping=0.05,
    )
    res = calculate_ssi_springs(inp)
    
    # 1. G = rho * Vs^2 = 1850 * 180^2 = 59,940,000 Pa = 59.94 MPa
    assert res.G_soil_MPa == pytest.approx(59.94)
    
    # 2. omega = 2 * pi * 8 = 50.265 rad/s
    assert res.omega_rad_s == pytest.approx(2.0 * 3.14159265 * 8.0)
    
    # 3. a0 = omega * (B/2) / Vs = 50.265 * 1.5 / 180 = 0.4188
    assert res.a0_dimensionless == pytest.approx(res.omega_rad_s * 1.5 / 180.0)
    
    # 4. Rigideces estáticas y dinámicas
    assert res.Kz_static_kN_m > 0.0
    assert res.Kz_dynamic_kN_m > 0.0
    assert res.Kx_static_kN_m > 0.0
    assert res.Kx_dynamic_kN_m > 0.0
    assert res.Ky_static_kN_m > 0.0
    assert res.Ky_dynamic_kN_m > 0.0
    assert res.Krx_static_kNm_rad > 0.0
    assert res.Krx_dynamic_kNm_rad > 0.0
    assert res.Kry_static_kNm_rad > 0.0
    assert res.Kry_dynamic_kNm_rad > 0.0
    assert res.Krz_static_kNm_rad > 0.0
    assert res.Krz_dynamic_kNm_rad > 0.0
    
    # 5. Amortiguamiento por radiación y total
    assert res.Cz_radiation_kNs_m > 0.0
    assert res.Cz_total_kNs_m > res.Cz_radiation_kNs_m
    assert res.Cx_total_kNs_m > res.Cx_radiation_kNs_m
    assert res.Cy_total_kNs_m > res.Cy_radiation_kNs_m
    assert res.Crx_total_kNms_rad > res.Crx_radiation_kNms_rad
    assert res.Cry_total_kNms_rad > res.Cry_radiation_kNms_rad
    assert res.Crz_total_kNms_rad > res.Crz_radiation_kNms_rad


def test_ssi_springs_invalid_dimensions():
    """L_m debe ser mayor o igual a B_m."""
    inp = SsiSpringsInput(
        L_m=2.0,
        B_m=4.0,  # L < B
        Vs_m_per_s=150.0,
        rho_soil_kg_m3=1900.0,
        nu_soil=0.3,
        frequency_Hz=5.0,
        material_damping=0.05,
    )
    with pytest.raises(ValueError, match="L_m debe ser mayor o igual a B_m"):
        calculate_ssi_springs(inp)


def test_api_ssi_springs_endpoint():
    """Verifica el endpoint FastAPI de resortes dinámicos SSI."""
    payload = {
        "L_m": 6.0,
        "B_m": 4.0,
        "Vs_m_per_s": 200.0,
        "rho_soil_kg_m3": 1900.0,
        "nu_soil": 0.33,
        "frequency_Hz": 6.0,
        "material_damping": 0.05
    }
    response = client.post("/api/geo/ssi-springs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Kz_static_kN_m" in data
    assert "Kz_dynamic_kN_m" in data
    assert "Cz_total_kNs_m" in data
    assert "Cz_radiation_kNs_m" in data
    assert data["omega_rad_s"] == pytest.approx(2.0 * 3.14159265 * 6.0, rel=1e-3)
