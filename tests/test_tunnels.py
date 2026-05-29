"""Tests unitarios para el análisis de convergencia-confinamiento y resortes Winkler en GeoJm."""

import pytest
from fastapi.testclient import TestClient
from geojm.tunnels import (
    calculate_tunnel_confinement,
    TunnelWinklerInput,
)
from geojm.api.app import create_app

client = TestClient(create_app())


def test_tunnel_confinement_stable():
    """Túnel en terreno competente que alcanza el equilibrio con el revestimiento (STABLE)."""
    # R0 = 3.0 m, P0 = 500 kPa, E = 120 MPa, nu = 0.25, c = 150 kPa, phi = 30°
    # Concreto: 30 GPa, 200 mm de espesor, activado al 30% de convergencia libre
    inp = TunnelWinklerInput(
        R0_m=3.0,
        P0_kPa=500.0,
        E_soil_MPa=120.0,
        nu_soil=0.25,
        c_kPa=150.0,
        phi_deg=30.0,
        E_liner_GPa=30.0,
        nu_liner=0.20,
        thickness_mm=200.0,
        unsupported_convergence_ratio=0.30,
        n_points=40
    )
    res = calculate_tunnel_confinement(inp)
    
    # 1. Pcr_kPa check
    # phi = 30° -> kp = (1 + sin(30)) / (1 - sin(30)) = 1.5 / 0.5 = 3.0
    # sigma_cm = 2 * c * cos(30) / (1 - sin(30)) = 2 * 150 * 0.8660 / 0.5 = 519.615 kPa
    # Pcr = (2 * P0 - sigma_cm) / (kp + 1) = (2 * 500 - 519.615) / 4.0 = 480.385 / 4.0 = 120.096 kPa
    assert res.Pcr_kPa == pytest.approx(120.096, abs=1e-2)
    
    # 2. Soporte
    # K_support = E_liner * t / [ R0^2 * (1 - nu^2) ] = 30e9 * 0.2 / [ 9.0 * 0.96 ] = 6e9 / 8.64 = 6.944e8 Pa/m = 694.4 kPa/mm
    assert res.K_support_kPa_mm == pytest.approx(694.444, abs=1e-1)
    
    # 3. Punto de equilibrio y estatus
    assert res.equilibrium_status == "STABLE"
    assert 0.0 < res.equilibrium_pressure_kPa < 500.0
    assert res.equilibrium_displacement_mm > res.liner_activation_displacement_mm
    
    # 4. Resortes Winkler
    # k_winkler = E / (R0 * (1 + nu)) = 120,000 kPa / (3 * 1.25) = 120,000 / 3.75 = 32,000 kN/m3
    assert res.k_winkler_static_kN_m3 == pytest.approx(32000.0)
    assert res.p_yield_kPa == pytest.approx(519.61524, abs=1e-2)
    assert res.u_yield_mm == pytest.approx(519.61524 / 32000.0 * 1000.0)


def test_tunnel_confinement_collapse():
    """Túnel en terreno extremadamente débil bajo mucha presión que colapsa (UNSTABLE_COLLAPSE)."""
    inp = TunnelWinklerInput(
        R0_m=4.0,
        P0_kPa=1200.0,      # Mucha presión
        E_soil_MPa=15.0,     # Suelo muy blando
        nu_soil=0.35,
        c_kPa=10.0,         # Cohesión bajísima
        phi_deg=15.0,        # Fricción baja
        E_liner_GPa=5.0,     # Soporte muy flexible
        nu_liner=0.20,
        thickness_mm=50.0,
        unsupported_convergence_ratio=0.80,
        n_points=30
    )
    res = calculate_tunnel_confinement(inp)
    assert res.equilibrium_status == "UNSTABLE_COLLAPSE"
    assert res.equilibrium_pressure_kPa == 0.0
    assert res.equilibrium_displacement_mm == res.max_convergence_unsupported_mm


def test_api_tunnel_winkler_endpoint():
    """Prueba del endpoint de la API para análisis de túneles Winkler."""
    payload = {
        "R0_m": 3.0,
        "P0_kPa": 600.0,
        "E_soil_MPa": 150.0,
        "nu_soil": 0.25,
        "c_kPa": 100.0,
        "phi_deg": 28.0,
        "E_liner_GPa": 25.0,
        "nu_liner": 0.20,
        "thickness_mm": 150.0,
        "unsupported_convergence_ratio": 0.40
    }
    response = client.post("/api/geo/tunnel-winkler", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Pcr_kPa" in data
    assert "equilibrium_status" in data
    assert "radial_displacement_mm" in data
    assert "pi_support_pressure_kPa" in data
