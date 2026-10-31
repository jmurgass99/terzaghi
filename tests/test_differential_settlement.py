"""Tests para asentamientos diferenciales — GJ-002."""
import pytest

from terzaghi.audit.differential_settlement import (
    check_differential_settlement,
    Finding,
)


class TestDifferentialSettlement:
    """Caso: 3 zapatas, una con asentamiento excesivo."""

    def _foundations(self):
        return [
            {"name": "Z1", "settlement_mm": 5.0, "x": 0.0, "y": 0.0},
            {"name": "Z2", "settlement_mm": 6.0, "x": 6.0, "y": 0.0},
            {"name": "Z3", "settlement_mm": 30.0, "x": 12.0, "y": 0.0},
        ]

    def test_encuentra_findings(self):
        findings = check_differential_settlement(self._foundations())
        assert len(findings) > 0

    def test_z3_genera_error(self):
        """Z3 tiene 30mm vs Z2 con 6mm a 6m → delta/L = 24/(1000*6) = 0.004 > 1/300."""
        findings = check_differential_settlement(self._foundations())
        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) >= 1
        # Debe involucrar Z3
        z3_involved = any(
            f.footing_a == "Z3" or f.footing_b == "Z3" for f in errors
        )
        assert z3_involved

    def test_z1_z2_ok_o_warning(self):
        """Z1-Z2: delta=1mm, L=6m → 1/(6000) = 0.000167 < 1/500, sin finding."""
        findings = check_differential_settlement(self._foundations())
        z1_z2 = [
            f for f in findings
            if {f.footing_a, f.footing_b} == {"Z1", "Z2"}
        ]
        # No deberia haber finding entre Z1 y Z2
        assert len(z1_z2) == 0

    def test_distorsion_warning_rango(self):
        """Caso intermedio: delta/L entre 1/500 y 1/300 → WARNING."""
        foundations = [
            {"name": "A", "settlement_mm": 0.0, "x": 0.0, "y": 0.0},
            {"name": "B", "settlement_mm": 8.0, "x": 5.0, "y": 0.0},
            # delta=8mm, L=5m → 8/(5000) = 0.0016 → entre 1/500=0.002 y 1/300=0.0033
        ]
        # Hmm, 0.0016 < 1/500=0.002, ajustemos
        foundations[1]["settlement_mm"] = 12.0
        # delta=12mm, L=5m → 12/5000 = 0.0024 → > 1/500=0.002 y < 1/300=0.00333
        findings = check_differential_settlement(foundations)
        assert len(findings) == 1
        assert findings[0].severity == "WARNING"

    def test_una_sola_zapata_sin_findings(self):
        findings = check_differential_settlement(
            [{"name": "Z1", "settlement_mm": 50.0, "x": 0, "y": 0}]
        )
        assert findings == []

    def test_lista_vacia(self):
        assert check_differential_settlement([]) == []

    def test_finding_to_dict(self):
        findings = check_differential_settlement(self._foundations())
        for f in findings:
            d = f.to_dict()
            assert "severity" in d
            assert "angular_distortion" in d
