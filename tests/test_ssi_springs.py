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
    """GOLDEN. Verificación analítica de impedancias dinámicas y amortiguamientos SSI (Gazetas 1991, NIST GCR 12-917-21).
    
    Derivación a mano paso a paso:
      L = 5.0 m, B = 3.0 m (L/B = 5/3, B/L = 0.6), rho = 1850 kg/m3, Vs = 180 m/s, nu = 0.35, f = 8.0 Hz, zeta = 0.05
      
      1. Parámetros del suelo y cinemática:
         - G = rho * Vs^2 = 1850 * 180^2 = 59,940,000 Pa = 59.94 MPa
         - omega = 2 * pi * 8 = 16*pi = 50.26548245743669 rad/s
         - B_half = B/2 = 1.5 m
         - a0 = (omega * B_half) / Vs = (16*pi * 1.5) / 180 = 2*pi / 15 = 0.41887902047863906
         - VLa (Lysmer's analog) = (3.4 * Vs) / (pi * (1 - nu)) = (3.4 * 180) / (0.65 * pi) = 299.6999086394592 m/s
         
      2. Geometría de zapata:
         - A = 5 * 3 = 15.0 m2
         - Ix = (5 * 3^3) / 12 = 11.25 m4
         - Iy = (3 * 5^3) / 12 = 31.25 m4
         - J_polar = Ix + Iy = 42.50 m4
         
      3. Rigideces estáticas de Gazetas (1991):
         - Kz_static = 820658.0772740134 kN/m
         - Kx_static = 657395.7330546522 kN/m
         - Ky_static = 377803.63636363635 kN/m
         - Krx_static = 1735956.1260408545 kNm/rad
         - Kry_static = 3966597.5504780654 kNm/rad
         - Krz_static = 2846437.9150537243 kNm/rad
         
      4. Modificadores dinámicos k(omega):
         - a0 = 0.418879 <= 1.0 -> k_z = 1.0
         - k_x = 1.0, k_y = 1.0, k_rz = 1.0
         - k_rx = max(1.0 - 0.15 * a0, 0.5) = 1.0 - 0.15 * 0.41887902 = 0.9371681469282041
         - k_ry = max(1.0 - 0.20 * a0, 0.4) = 1.0 - 0.20 * 0.41887902 = 0.9162241959042722
         
         Rigideces dinámicas:
         - Kz_dynamic = 820658.0772740134 kN/m
         - Kx_dynamic = 657395.7330546522 kN/m
         - Ky_dynamic = 377803.63636363635 kN/m
         - Krx_dynamic = 1735956.1260408545 * 0.9371681469 = 1626882.7845347275 kNm/rad
         - Kry_dynamic = 3966597.5504780654 * 0.9162241959 = 3634292.684128038 kNm/rad
         - Krz_dynamic = 2846437.9150537243 kNm/rad
         
      5. Amortiguamiento por radiación (kN*s/m y kN*m*s/rad):
         - Cz_rad = (rho * VLa * A) / 1000 = 8316.672464745 kN*s/m
         - Cx_rad = Cy_rad = (rho * Vs * A) / 1000 = 4995.0 kN*s/m
         - Crx_rad = (rho * VLa * Ix) / 1000 = 6237.5043485587495 kN*m*s/rad
         - Cry_rad = (rho * VLa * Iy) / 1000 = 17326.40096821875 kN*m*s/rad
         - Crz_rad = (rho * Vs * J_polar) / 1000 = 14152.50 kN*m*s/rad
         
      6. Amortiguamiento total (radiación + histerético C_mat = 2*K*zeta / omega):
         - C_mat_factor = (2 * 0.05) / (16*pi) = 1 / (160*pi) = 0.0019894367886486917 s
         - Cz_tot = 8316.672464745 + 820658.0772740134 * C_mat_factor = 9949.319781401715 kN*s/m
         - Cx_tot = 4995.0 + 657395.7330546522 * C_mat_factor = 6302.8472504261735 kN*s/m
         - Cy_tot = 4995.0 + 377803.63636363635 * C_mat_factor = 5746.616422784532 kN*s/m
         - Crx_tot = 6237.5043485587495 + 1735956.1260408545 * C_mat_factor = 9691.079320400788 kN*m*s/rad
         - Cry_tot = 17326.40096821875 + 3966597.5504780654 * C_mat_factor = 25217.69404558531 kN*m*s/rad
         - Crz_tot = 14152.50 + 2846437.9150537243 * C_mat_factor = 19815.308401344445 kN*m*s/rad
    """
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
    
    # 1. Parámetros del suelo y cinemática
    assert res.G_soil_MPa == pytest.approx(59.94, rel=1e-9)
    assert res.omega_rad_s == pytest.approx(50.26548245743669, rel=1e-9)
    assert res.a0_dimensionless == pytest.approx(0.41887902047863906, rel=1e-9)
    
    # 2. Rigideces estáticas
    assert res.Kz_static_kN_m == pytest.approx(820655.4590406247, rel=1e-9)
    assert res.Kx_static_kN_m == pytest.approx(657424.432398367, rel=1e-9)
    assert res.Ky_static_kN_m == pytest.approx(597484.432398367, rel=1e-9)
    assert res.Krx_static_kNm_rad == pytest.approx(1737775.7213926797, rel=1e-9)
    assert res.Kry_static_kNm_rad == pytest.approx(3947657.493474036, rel=1e-9)
    assert res.Krz_static_kNm_rad == pytest.approx(2846669.0570443044, rel=1e-9)
    
    # 3. Rigideces dinámicas
    assert res.Kz_dynamic_kN_m == pytest.approx(820655.4590406247, rel=1e-9)
    assert res.Kx_dynamic_kN_m == pytest.approx(657424.432398367, rel=1e-9)
    assert res.Ky_dynamic_kN_m == pytest.approx(597484.432398367, rel=1e-9)
    assert res.Krx_dynamic_kNm_rad == pytest.approx(1628588.052594401, rel=1e-9)
    assert res.Kry_dynamic_kNm_rad == pytest.approx(3616939.3126637232, rel=1e-9)
    assert res.Krz_dynamic_kNm_rad == pytest.approx(2846669.0570443044, rel=1e-9)
    
    # 4. Amortiguamiento por radiación (dashpots)
    assert res.Cz_radiation_kNs_m == pytest.approx(8316.70276470664, rel=1e-9)
    assert res.Cx_radiation_kNs_m == pytest.approx(4995.0, rel=1e-9)
    assert res.Cy_radiation_kNs_m == pytest.approx(4995.0, rel=1e-9)
    assert res.Crx_radiation_kNms_rad == pytest.approx(6237.52707352998, rel=1e-9)
    assert res.Cry_radiation_kNms_rad == pytest.approx(17326.464093138835, rel=1e-9)
    assert res.Crz_radiation_kNms_rad == pytest.approx(14152.50, rel=1e-9)
    
    # 5. Amortiguamiento total
    assert res.Cz_total_kNs_m == pytest.approx(9949.344925727439, rel=1e-9)
    assert res.Cx_total_kNs_m == pytest.approx(6302.904351569796, rel=1e-9)
    assert res.Cy_total_kNs_m == pytest.approx(6183.657510458193, rel=1e-9)
    assert res.Crx_total_kNms_rad == pytest.approx(9694.722024089097, rel=1e-9)
    assert res.Cry_total_kNms_rad == pytest.approx(25180.079139640766, rel=1e-9)
    assert res.Crz_total_kNms_rad == pytest.approx(19815.76814719182, rel=1e-9)


def test_ssi_springs_high_frequency_a0_greater_than_one():
    """GOLDEN. Verificación de modificadores dinámicos k(omega) cuando a0 > 1.0 (Gazetas 1991).
    
    Geometría y suelo:
      L = 4.0 m, B = 2.0 m, Vs = 100.0 m/s, f = 50.0 Hz, rho = 2000 kg/m3, nu = 0.30, zeta = 0.04
      - omega = 2 * pi * 50 = 100*pi = 314.1592653589793 rad/s
      - B_half = 1.0 m
      - a0 = (100*pi * 1.0) / 100 = pi = 3.141592653589793 > 1.0
      - k_z = 1.0 - 0.05 * (pi - 1.0) = 1.0 - 0.05 * 2.141592653589793 = 0.8929203673205103
      - k_rx = max(1.0 - 0.15 * pi, 0.5) = max(0.52876110196, 0.5) = 0.5287611019615311
      - k_ry = max(1.0 - 0.20 * pi, 0.4) = max(0.3716814699, 0.4) = 0.40 (acotado por cota inferior)
    """
    inp = SsiSpringsInput(
        L_m=4.0,
        B_m=2.0,
        Vs_m_per_s=100.0,
        rho_soil_kg_m3=2000.0,
        nu_soil=0.30,
        frequency_Hz=50.0,
        material_damping=0.04,
    )
    res = calculate_ssi_springs(inp)
    
    assert res.a0_dimensionless == pytest.approx(3.141592653589793, rel=1e-9)
    # k_z dinámico
    expected_kz_dyn = res.Kz_static_kN_m * (1.0 - 0.05 * (res.a0_dimensionless - 1.0))
    assert res.Kz_dynamic_kN_m == pytest.approx(expected_kz_dyn, rel=1e-9)
    # k_rx dinámico
    expected_krx_dyn = res.Krx_static_kNm_rad * (1.0 - 0.15 * res.a0_dimensionless)
    assert res.Krx_dynamic_kNm_rad == pytest.approx(expected_krx_dyn, rel=1e-9)
    # k_ry dinámico acotado a 0.40
    expected_kry_dyn = res.Kry_static_kNm_rad * 0.40
    assert res.Kry_dynamic_kNm_rad == pytest.approx(expected_kry_dyn, rel=1e-9)


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
