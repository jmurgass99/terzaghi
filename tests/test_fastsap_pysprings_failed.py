"""export_to_fastsap debe reportar fallos OAPI, no tragarlos en silencio."""
from __future__ import annotations

from geojm.integration.fastsap_pysprings import (
    PySpringNode, FastSAPPySpringsConfig, export_to_fastsap,
)


class _StubSap:
    def __init__(self, raise_on=()):
        self.calls = []
        raise_on = set(raise_on)
        outer = self

        class _PropLink:
            @staticmethod
            def SetMultiLinearPlastic(name, n, x, y, *a):
                outer.calls.append(name)
                if name in raise_on:
                    raise RuntimeError(f"OAPI error en {name}")
                return 0

        self.PropLink = _PropLink


def test_export_reports_failed_springs():
    nodes = (
        PySpringNode(z_m=1.0, D_m=0.6, su_kPa=50),   # -> PY_z1.00
        PySpringNode(z_m=3.0, D_m=0.6, su_kPa=60),   # -> PY_z3.00
    )
    sap = _StubSap(raise_on={"PY_z3.00"})
    cfg = FastSAPPySpringsConfig(nodes=nodes, code="EU")

    res = export_to_fastsap(cfg, client=sap, dry_run=False)

    assert res["applied"] == 1
    assert isinstance(res["failed"], dict)            # shape uniforme name->mensaje
    assert "OAPI error" in res["failed"]["PY_z3.00"]  # mensaje preservado
    assert "PY_z1.00" not in res["failed"]
