"""Tests for AGS4 geotechnical parser and PLAXIS 2D/3D remote scripting generator."""
from __future__ import annotations

import pytest

from geojm.ags4_plaxis import (
    Ags4Project,
    generate_plaxis_python_script,
    parse_ags4_text,
)

SAMPLE_AGS4_DATA = """
"GROUP","PROJ"
"HEADING","PROJ_ID","PROJ_NAME"
"DATA","PJ101","Puente Metropolitano Sur"

"GROUP","LOCA"
"HEADING","LOCA_ID","LOCA_NATE","LOCA_NATN","LOCA_GL","LOCA_FEND"
"DATA","BH01","500000.0","4500000.0","25.0","18.0"

"GROUP","GEOL"
"HEADING","LOCA_ID","GEOL_TOP","GEOL_BASE","GEOL_DESC","GEOL_LEG"
"DATA","BH01","0.0","4.5","Dense coarse SAND with fine gravel","SAND"
"DATA","BH01","4.5","14.0","Stiff silty CLAY medium plasticity","CLAY"

"GROUP","ISPT"
"HEADING","LOCA_ID","ISPT_TOP","ISPT_NVAL"
"DATA","BH01","1.5","28"
"DATA","BH01","3.0","34"
"DATA","BH01","6.0","18"
"""


def test_parse_ags4_text() -> None:
    proj = parse_ags4_text(SAMPLE_AGS4_DATA)
    assert proj.status == "CALCULADO"
    assert proj.project_name == "Puente Metropolitano Sur"
    assert len(proj.boreholes) == 1

    bh = proj.boreholes[0]
    assert bh.hole_id == "BH01"
    assert bh.elevation == 25.0
    assert len(bh.strata) == 2
    assert bh.strata[0].geology_code == "SAND"
    assert bh.strata[0].soil_type == "sand"
    assert bh.strata[1].soil_type == "clay"
    assert len(bh.spt_tests) == 3
    assert bh.spt_tests[0].n_value == 28


def test_generate_plaxis_python_script() -> None:
    proj = parse_ags4_text(SAMPLE_AGS4_DATA)
    script_2d = generate_plaxis_python_script(proj, model_dim="2D")
    assert "new_server(host='localhost'" in script_2d
    assert "bh_BH01 = g_i.borehole" in script_2d
    assert "Mat_SAND" in script_2d
    assert "Mat_CLAY" in script_2d
    assert "g_i.mesh()" in script_2d

    script_3d = generate_plaxis_python_script(proj, model_dim="3D")
    assert "g_i.borehole(500000.0, 4500000.0)" in script_3d
