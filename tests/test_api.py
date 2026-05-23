"""Test API GeoJm."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from geojm.api import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_health(client):
    assert client.get("/health").status_code == 200


def test_py_matlock(client):
    r = client.post("/api/geo/py/matlock", json={
        "z_m": 3, "D_m": 0.8, "su_kPa": 50,
    })
    assert r.status_code == 200
    assert len(r.json()["p_kN_per_m"]) > 5


def test_pile_group(client):
    r = client.post("/api/geo/pile-group/lateral", json={
        "s_over_D": 5, "rows": 3,
    })
    assert r.status_code == 200
    assert 0 < r.json()["global_efficiency"] <= 1


def test_liquefaction(client):
    r = client.post("/api/geo/liquefaction", json={
        "depth_m": 5, "sigma_v_kPa": 90, "sigma_v_eff_kPa": 60,
        "N1_60_cs": 15, "a_max_g": 0.3, "Mw": 7.5,
    })
    assert r.status_code == 200
    assert "FS" in r.json()
