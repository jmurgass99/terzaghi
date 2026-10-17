"""AGS4 / DIGGS Geotechnical Data Interchange & PLAXIS 2D/3D Remote Scripting — GeoJm.

Implements digital geotechnical data standard ingestion and numerical modeling automation:
  1. **AGS4 (Association of Geotechnical and Geoenvironmental Specialists v4.x)**:
     - Parses ``.ags`` text files containing geotechnical ground investigation data:
       ``PROJ`` (Project), ``LOCA`` (Borehole coordinates and depth), ``GEOL`` (Stratigraphy,
       top/base depths, soil classification), and ``ISPT`` (SPT blow counts and depths).
  2. **PLAXIS 2D/3D Remote Scripting Generator**:
     - Automatically generates executable Python scripts compatible with Bentley PLAXIS
       Input Server (``s_i`` / ``g_i``) to create boreholes (``g_i.borehole(...)``), define
       soil stratigraphy, instantiate constitutive materials (Mohr-Coulomb / Hardening Soil),
       and configure calculation phases without manual UI entry.

All public dataclasses declare ``units`` explicitly and avoid unit-suffixed field names.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import io
import re
from typing import Any, Sequence


@dataclass(frozen=True)
class Ags4Stratum:
    """Individual geological stratum in an AGS4 borehole (GEOL group)."""

    top_depth: float
    base_depth: float
    geology_code: str
    description: str
    soil_type: str = "sand"
    unit_weight: float = 19.0  # kN/m3
    cohesion: float = 5.0      # kPa
    friction_angle: float = 30.0  # deg
    elastic_modulus: float = 25000.0  # kPa
    units: str = "SI_m_kN_kPa_deg"


@dataclass(frozen=True)
class Ags4SptTest:
    """Standard Penetration Test record in an AGS4 borehole (ISPT group)."""

    depth: float
    n_value: int
    blow_type: str = "SPT"
    units: str = "SI_m"


@dataclass(frozen=True)
class Ags4Borehole:
    """Borehole record containing coordinates, stratigraphy, and SPT tests (LOCA group)."""

    hole_id: str
    x: float
    y: float
    elevation: float
    final_depth: float
    strata: list[Ags4Stratum] = field(default_factory=list)
    spt_tests: list[Ags4SptTest] = field(default_factory=list)
    units: str = "SI_m"


@dataclass(frozen=True)
class Ags4Project:
    """Complete geotechnical investigation project parsed from AGS4 data."""

    project_name: str
    project_number: str
    boreholes: list[Ags4Borehole] = field(default_factory=list)
    status: str = "CALCULADO"
    units: str = "SI_m_kN_kPa_deg"


def parse_ags4_text(content: str) -> Ags4Project:
    """Parse an AGS4 formatted text buffer into a structured ``Ags4Project``."""
    proj_name = "Geotechnical Site Investigation"
    proj_num = "GEO-001"
    boreholes_map: dict[str, dict[str, Any]] = {}
    geol_rows: list[dict[str, str]] = []
    ispt_rows: list[dict[str, str]] = []

    current_group: str | None = None
    headers: list[str] = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = [p.strip().strip('"') for p in line.split(",")]
        record_type = parts[0].upper() if parts else ""

        if record_type == '"GROUP"' or record_type == "GROUP":
            current_group = parts[1].upper() if len(parts) > 1 else None
            headers = []
        elif record_type == '"HEADING"' or record_type == "HEADING":
            headers = [h.upper() for h in parts[1:]]
        elif record_type == '"DATA"' or record_type == "DATA":
            if not current_group or not headers:
                continue
            values = parts[1:]
            row = dict(zip(headers, values))

            if current_group == "PROJ":
                proj_name = row.get("PROJ_NAME") or proj_name
                proj_num = row.get("PROJ_ID") or proj_num
            elif current_group == "LOCA":
                hole_id = row.get("LOCA_ID", "BH1")
                try:
                    x = float(row.get("LOCA_NATE", 0.0))
                    y = float(row.get("LOCA_NATN", 0.0))
                    z = float(row.get("LOCA_GL", 0.0))
                    fend = float(row.get("LOCA_FEND", 10.0))
                except ValueError:
                    x, y, z, fend = 0.0, 0.0, 0.0, 10.0
                boreholes_map[hole_id] = {
                    "id": hole_id,
                    "x": x,
                    "y": y,
                    "z": z,
                    "fend": fend,
                    "strata": [],
                    "spt": [],
                }
            elif current_group == "GEOL":
                geol_rows.append(row)
            elif current_group == "ISPT":
                ispt_rows.append(row)

    # Attach strata to boreholes
    for g in geol_rows:
        hid = g.get("LOCA_ID", "")
        if hid not in boreholes_map:
            boreholes_map[hid] = {"id": hid, "x": 0.0, "y": 0.0, "z": 0.0, "fend": 10.0, "strata": [], "spt": []}
        try:
            top = float(g.get("GEOL_TOP", 0.0))
            base = float(g.get("GEOL_BASE", top + 2.0))
        except ValueError:
            top, base = 0.0, 2.0
        code = g.get("GEOL_LEG", "SOIL")
        desc = g.get("GEOL_DESC", "Stratum")

        if stype == "clay":
            gamma = 17.5
            c_kpa = 25.0
            phi_deg = 22.0
            e_kpa = 15000.0
        else:
            gamma = 19.5
            c_kpa = 1.0
            phi_deg = 33.0
            e_kpa = 35000.0


        boreholes_map[hid]["strata"].append(
            Ags4Stratum(
                top_depth=round(top, 3),
                base_depth=round(base, 3),
                geology_code=code,
                description=desc,
                soil_type=stype,
                unit_weight=gamma,
                cohesion=c_kpa,
                friction_angle=phi_deg,
                elastic_modulus=e_kpa,
            )
        )

    # Attach SPT tests
    for s in ispt_rows:
        hid = s.get("LOCA_ID", "")
        if hid in boreholes_map:
            try:
                dp = float(s.get("ISPT_TOP", 0.0))
                n_val = int(float(s.get("ISPT_NVAL", 10)))
            except ValueError:
                dp, n_val = 0.0, 10
            boreholes_map[hid]["spt"].append(Ags4SptTest(depth=dp, n_value=n_val))

    bh_list: list[Ags4Borehole] = []
    for d in boreholes_map.values():
        bh_list.append(
            Ags4Borehole(
                hole_id=d["id"],
                x=d["x"],
                y=d["y"],
                elevation=d["z"],
                final_depth=d["fend"],
                strata=d["strata"],
                spt_tests=d["spt"],
            )
        )

    return Ags4Project(
        project_name=proj_name,
        project_number=proj_num,
        boreholes=bh_list,
        status="CALCULADO",
    )


def generate_plaxis_python_script(
    project: Ags4Project,
    model_dim: str = "2D",
    host: str = "localhost",
    port: int = 10000,
) -> str:
    """Generate an executable PLAXIS Remote Scripting Python code string."""
    lines = [
        '"""PLAXIS Python Remote Scripting automation script generated by GeoJm."""',
        "from __future__ import annotations",
        "import sys",
        "try:",
        "    from plxscripting.easy import new_server",
        "except ImportError:",
        "    print('PLAXIS scripting module not installed.')",
        "    sys.exit(0)",
        "",
        f"# Connect to PLAXIS {model_dim} Input Server",
        f"s_i, g_i = new_server(host='{host}', port={port})",
        f"g_i.new()",
        f"# Project: {project.project_name} ({project.project_number})",
        "",
        "# 1. Define Mohr-Coulomb soil materials",
    ]

    defined_materials = set()
    for bh in project.boreholes:
        for st in bh.strata:
            mat_name = f"Mat_{st.geology_code}".replace(" ", "_")
            if mat_name not in defined_materials:
                defined_materials.add(mat_name)
                lines.append(f"# Material: {mat_name} ({st.description})")
                lines.append(f"mat_{mat_name} = g_i.soilmat()")
                lines.append(f"mat_{mat_name}.MaterialName = '{mat_name}'")
                lines.append(f"mat_{mat_name}.SoilModel = 2  # Mohr-Coulomb")
                lines.append(f"mat_{mat_name}.gammaUnsat = {st.unit_weight}")
                lines.append(f"mat_{mat_name}.gammaSat = {st.unit_weight + 1.5}")
                lines.append(f"mat_{mat_name}.Eref = {st.elastic_modulus}")
                lines.append(f"mat_{mat_name}.cref = {st.cohesion}")
                lines.append(f"mat_{mat_name}.phi = {st.friction_angle}")
                lines.append("")

    lines.append("# 2. Instantiate Boreholes and Soil Layers")
    for bh in project.boreholes:
        lines.append(f"# Borehole {bh.hole_id} at X={bh.x}, Y={bh.y}, GL={bh.elevation}")
        if model_dim.upper() == "2D":
            lines.append(f"bh_{bh.hole_id} = g_i.borehole({bh.x})")
        else:
            lines.append(f"bh_{bh.hole_id} = g_i.borehole({bh.x}, {bh.y})")
        lines.append(f"bh_{bh.hole_id}.Head = {bh.elevation}")

        for idx, st in enumerate(bh.strata):
            top_y = bh.elevation - st.top_depth
            base_y = bh.elevation - st.base_depth
            lines.append(f"g_i.soillayer(bh_{bh.hole_id}, {top_y}, {base_y})")
            mat_name = f"Mat_{st.geology_code}".replace(" ", "_")
            lines.append(f"bh_{bh.hole_id}.SoilLayers[{idx}].Material = mat_{mat_name}")
        lines.append("")

    lines.append("# 3. Mesh generation and Initial Conditions")
    lines.append("g_i.mesh()")
    lines.append("g_i.calculate()")
    lines.append("print('PLAXIS model generation and calculation completed.')")

    return "\n".join(lines)


__all__ = [
    "Ags4Borehole",
    "Ags4Project",
    "Ags4SptTest",
    "Ags4Stratum",
    "generate_plaxis_python_script",
    "parse_ags4_text",
]
