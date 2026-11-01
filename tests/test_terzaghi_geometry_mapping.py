"""Tests para SoilColumnMapping en Terzaghi."""
from terzaghi.geometry_mapping import SemanticStratum, build_soil_column_mesh


def test_soil_column_mapping_invariance():
    strata = [
        SemanticStratum("FILL-SAND", thickness_m=6.0, Vs_m_per_s=180.0, density_kg_m3=1850.0),
        SemanticStratum("STIFF-CLAY", thickness_m=10.0, Vs_m_per_s=310.0, density_kg_m3=2000.0),
    ]
    sub_2, map_2, sum_2 = build_soil_column_mesh(strata, divisions_per_stratum=2)
    sub_6, map_6, sum_6 = build_soil_column_mesh(strata, divisions_per_stratum=6)

    assert len(sub_2) == 4
    assert len(sub_6) == 12
    assert len(map_6.stratum_to_sublayers["FILL-SAND"]) == 6
    assert len(map_6.stratum_to_sublayers["STIFF-CLAY"]) == 6
    assert abs(sum_2["amplification_factor"] - sum_6["amplification_factor"]) < 1e-6
    assert sum_6["total_py_stiffness_kN_m"] > 100.0
