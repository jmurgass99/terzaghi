"""La licuacion ya no se calcula sobre un ensayo inventado.

DEFECTO CORREGIDO
-----------------
`evaluate_spt_profile_liquefaction` hacia

    n160 = float(ly.get("N1_60cs", ly.get("N1_60_cs", 15.0)))

de modo que una capa sin ensayo SPT se evaluaba igualmente, con N1_60cs = 15.0
FABRICADO, y producia un factor de seguridad de aspecto perfectamente normal.

Tres agravantes:

  1. N = 15 no es un valor neutro: cae justo en la frontera licuable / no
     licuable, asi que el resultado inventado salia creible en cualquier
     direccion.
  2. Era el UNICO parametro que se rellenaba en silencio. `depth_m`,
     `sigma_v_kPa` y `sigma_v_eff_kPa` lanzaban KeyError. Y es precisamente el
     que gobierna la RESISTENCIA.
  3. Todo esto en el modulo cuyo titular es el reporte defensivo
     "NO EVALUADO (sin datos de SPT)", que solo cubria el caso de lista vacia.

Ahora una capa sin ensayo NO se evalua, se marca como tal, y queda fuera del
min_FS. Y si hay capas sin evaluar, el resultado dice explicitamente que la
ausencia de estrato licuable no esta establecida para el perfil completo: un
`has_liquefiable_stratum=False` parcial no puede leerse como un perfil limpio.
"""
from __future__ import annotations

import pytest

from terzaghi.liquefaction.boulanger_idriss import evaluate_spt_profile_liquefaction

CAPA_OK = {
    "depth_m": 5.0, "sigma_v_kPa": 95.0, "sigma_v_eff_kPa": 65.0,
    "N1_60cs": 12.0,
}
CAPA_SIN_ENSAYO = {
    "depth_m": 8.0, "sigma_v_kPa": 150.0, "sigma_v_eff_kPa": 95.0,
}


def test_una_capa_sin_ensayo_no_se_evalua_con_un_numero_inventado():
    """EL TEST QUE SOSTIENE LA CORRECCION."""
    res = evaluate_spt_profile_liquefaction([CAPA_SIN_ENSAYO], a_max_g=0.30)

    capa = res.layers[0]
    assert capa["N1_60cs"] is None, (
        "se ha vuelto a inventar un N1_60cs para una capa sin ensayo"
    )
    assert capa["FS"] is None
    assert capa["CRR"] is None
    assert capa["is_liquefiable"] is None
    assert "NO EVALUADA" in capa["status"]

    # Con todas las capas sin ensayo, el perfil entero queda sin evaluar.
    assert res.evaluated is False
    assert res.min_FS is None
    assert res.n_layers_not_evaluated == 1


def test_perfil_mixto_evalua_lo_que_puede_y_declara_lo_que_no():
    res = evaluate_spt_profile_liquefaction(
        [CAPA_OK, CAPA_SIN_ENSAYO], a_max_g=0.30,
    )

    assert res.evaluated is True
    assert res.n_layers_not_evaluated == 1
    assert "PARCIALMENTE" in res.status
    assert "NO esta establecida" in res.status

    evaluadas = [c for c in res.layers if c["FS"] is not None]
    assert len(evaluadas) == 1
    # El min_FS sale SOLO de las capas evaluadas.
    assert res.min_FS == pytest.approx(evaluadas[0]["FS"])


def test_la_capa_sin_ensayo_no_arrastra_el_min_FS():
    """Con el defecto, la capa fabricada participaba en el min_FS y podia
    bajarlo o subirlo. Ahora no participa: el min_FS de un perfil mixto es
    identico al del perfil con solo las capas que si tienen ensayo."""
    solo_buena = evaluate_spt_profile_liquefaction([CAPA_OK], a_max_g=0.30)
    mixto = evaluate_spt_profile_liquefaction(
        [CAPA_OK, CAPA_SIN_ENSAYO], a_max_g=0.30,
    )
    assert mixto.min_FS == pytest.approx(solo_buena.min_FS, rel=1e-12)


def test_se_acepta_el_alias_N1_60_cs():
    """El codigo admitia dos grafias; la correccion no puede haber roto una."""
    capa = dict(CAPA_SIN_ENSAYO, N1_60_cs=12.0)
    res = evaluate_spt_profile_liquefaction([capa], a_max_g=0.30)
    assert res.evaluated is True
    assert res.n_layers_not_evaluated == 0
    assert res.layers[0]["N1_60cs"] == pytest.approx(12.0)


def test_sin_capas_sigue_dando_el_no_evaluado_de_siempre():
    """La rama que ya existia y era correcta no se toca."""
    res = evaluate_spt_profile_liquefaction([])
    assert res.evaluated is False
    assert "NO EVALUADO" in res.status
    assert res.min_FS is None


def test_los_demas_parametros_siguen_siendo_obligatorios():
    """No se rellena ninguno en silencio: sin sigma_v_eff no hay evaluacion
    posible y debe fallar ruidosamente, como ya hacia."""
    with pytest.raises(KeyError):
        evaluate_spt_profile_liquefaction([{"depth_m": 5.0, "N1_60cs": 12.0}])
