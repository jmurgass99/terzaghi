"""Tests Terzaghi-Peck excavation stability."""
import pytest

from geojm.excavation import ExcavationInput, check_excavation


def test_excavacion_segura():
    r = check_excavation(ExcavationInput(
        depth_m=3, width_m=5, length_m=10, su_kPa=80,
    ))
    assert r.FS_basal_heave > 1.5
    assert r.is_safe


def test_excavacion_profunda_falla():
    r = check_excavation(ExcavationInput(
        depth_m=15, width_m=5, length_m=10, su_kPa=30,
    ))
    assert r.FS_basal_heave < 1.5
    assert not r.is_safe


def test_NF_dentro_excavacion_uplift_finito():
    r = check_excavation(ExcavationInput(
        depth_m=5, width_m=5, length_m=5, su_kPa=80,
        water_table_depth_m=2,
    ))
    assert r.FS_uplift > 0
    assert r.FS_uplift != float("inf")


def test_input_invalido():
    with pytest.raises(ValueError):
        check_excavation(ExcavationInput(
            depth_m=0, width_m=5, length_m=10, su_kPa=50,
        ))
