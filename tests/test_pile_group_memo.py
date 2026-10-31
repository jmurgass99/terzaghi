"""Tests para memoria de calculo pile group lateral — GJ-005."""
import pytest

from terzaghi.memos.pile_group_lateral import (
    PileGroupLateralInput,
    PileGroupLateralResult,
    render_pile_group_memo,
    _fm_mokwa_duncan,
)


class TestMokwaDuncanMemo:

    def _default_input(self) -> PileGroupLateralInput:
        return PileGroupLateralInput(
            n_rows=3, n_cols=3, D_m=0.6, s_m=1.8, P_single_kN=200.0,
        )

    def test_render_produce_output(self):
        """La memoria debe generar texto no vacio."""
        result = render_pile_group_memo(self._default_input())
        assert len(result.memo_text) > 100
        assert "MEMORIA DE CALCULO" in result.memo_text
        assert "Mokwa-Duncan" in result.memo_text

    def test_memo_contiene_pasos(self):
        """La memoria debe tener 4 pasos."""
        result = render_pile_group_memo(self._default_input())
        assert "PASO 1" in result.memo_text
        assert "PASO 2" in result.memo_text
        assert "PASO 3" in result.memo_text
        assert "PASO 4" in result.memo_text

    def test_valores_numericos_consistentes(self):
        """P_group debe ser la suma de P_per_row."""
        result = render_pile_group_memo(self._default_input())
        assert result.P_group_kN == pytest.approx(sum(result.P_per_row_kN), abs=0.1)

    def test_eficiencia_menor_igual_1(self):
        """Eficiencia no debe superar 1.0."""
        result = render_pile_group_memo(self._default_input())
        assert 0 < result.efficiency <= 1.0

    def test_leading_row_fm_es_1(self):
        """Fila delantera siempre tiene fm=1.0."""
        result = render_pile_group_memo(self._default_input())
        assert result.fm_per_row[0] == 1.0

    def test_trailing_rows_fm_capped(self):
        """Filas traseras con s/d=3 tienen fm <= 1.0 (saturado a 1.0)."""
        result = render_pile_group_memo(self._default_input())
        for fm in result.fm_per_row[1:]:
            assert fm <= 1.0

    def test_trailing_rows_fm_menor_con_sd_bajo(self):
        """Filas traseras con s/d bajo tienen fm < 1.0."""
        inp = PileGroupLateralInput(
            n_rows=3, n_cols=3, D_m=1.0, s_m=0.5, P_single_kN=200.0,
        )
        result = render_pile_group_memo(inp)
        # s/d = 0.5 → fm = 0.64 + 0.36*0.5 = 0.82
        for fm in result.fm_per_row[1:]:
            assert fm < 1.0

    def test_s_over_d(self):
        """s/D debe ser s_m / D_m."""
        result = render_pile_group_memo(self._default_input())
        assert result.s_over_d == pytest.approx(1.8 / 0.6, abs=0.01)

    def test_fm_mokwa_duncan_leading(self):
        """Row 1 siempre fm=1.0."""
        assert _fm_mokwa_duncan(1, 3.0) == 1.0

    def test_fm_mokwa_duncan_trailing_sd3(self):
        """s/d=3 → fm = min(0.64 + 0.36*3, 1.0) = 1.0 (saturado)."""
        fm = _fm_mokwa_duncan(2, 3.0)
        assert fm == pytest.approx(1.0, abs=0.01)

    def test_fm_mokwa_duncan_trailing_sd_low(self):
        """s/d=0.5 → fm = 0.64 + 0.36*0.5 = 0.82."""
        fm = _fm_mokwa_duncan(2, 0.5)
        assert fm == pytest.approx(0.82, abs=0.01)

    def test_p_group_con_grupo_grande(self):
        """Grupo 4x4 con s/d=5."""
        inp = PileGroupLateralInput(
            n_rows=4, n_cols=4, D_m=0.5, s_m=2.5, P_single_kN=150.0,
        )
        result = render_pile_group_memo(inp)
        assert result.P_group_kN > 0
        assert len(result.fm_per_row) == 4
        assert len(result.P_per_row_kN) == 4

    def test_input_invalido(self):
        with pytest.raises(ValueError):
            render_pile_group_memo(PileGroupLateralInput(
                n_rows=0, n_cols=3, D_m=0.6, s_m=1.8, P_single_kN=200.0,
            ))

    def test_una_fila(self):
        """Grupo de 1 fila: eficiencia = 1.0."""
        inp = PileGroupLateralInput(
            n_rows=1, n_cols=3, D_m=0.6, s_m=1.8, P_single_kN=200.0,
        )
        result = render_pile_group_memo(inp)
        assert result.efficiency == pytest.approx(1.0)
        assert result.fm_per_row == [1.0]
