"""CONSOLIDACION de capacidad portante de cimentacion superficial.

El monorepo tenia CINCO implementaciones de la misma pregunta fisica:

  1. ``terzaghi.bearing_capacity.evaluate_bearing``                  (legacy, aqui)
  2. ``foundationcalc.analysis.bearing_capacity``             <-- CANONICA
  3. ``fastsap.codes.bearing_capacity.bearing_capacity``
  4. ``foundationcalc.services.bearing.bearing_capacity_multilayer``
  5. ``fastsap.memos.bearing_capacity_memo``

POR QUE LA CANONICA ES LA DE FoundationDesignJm
-----------------------------------------------
NO por antiguedad ni por numero de tests, sino por un ORACULO PUBLICADO
INDEPENDIENTE y por cobertura fisica:

(a) ORACULO PUBLICADO. El ejemplo resuelto W00675 §4.3 (ver FUENTE abajo)
    publica los NUEVE valores intermedios de una zapata rectangular
    (N_q, N_c, N_gamma, s_q, s_c, s_gamma y los tres terminos de q_ult).
    ``foundationcalc.analysis`` los reproduce TODOS con error <= 0.36 %
    y la suma con -0.004 %. Las otras implementaciones, sobre ese MISMO caso
    publicado, dan -17.20 % / -10.38 % / +2.62 % / +15.25 %.
    Los factores de forma de ``terzaghi.evaluate_bearing``
    (s_c = 1+0.2B/L, s_q = 1+0.1B/L, s_gamma = 1-0.1B/L) NO corresponden a
    ningun juego publicado -- ya estaba documentado en la NOTA 2 de
    ``test_golden_bearing_capacity_published.py``. Los de la canonica SI son
    los del Anexo D de EN 1997-1.

(b) COBERTURA FISICA. Solo la canonica cubre area efectiva por excentricidad
    (Meyerhof), factores de inclinacion de carga (Vesic / EN 1997-1 Anexo D),
    ecuacion no drenada separada (D.3) y factores parciales de material.
    ``evaluate_bearing`` no cubre ninguno de los cuatro.

FUENTE DEL GOLDEN
-----------------
  W00675 — "Examples of geotechnical design according to Eurocode 7"
  (UPC MEEC, Foundation Structures), ejemplo resuelto §4.3 "Pad footing on
  dry sand (Limit State GEO)", columna DA1-C1.
  Transcrito en el monorepo en
  ``packages/FoundationDesignJm/docs/theory/04_eurocode7_examples.md`` §4.3.
  Clausula de norma: EN 1997-1:2004 Anexo D (D.4, condiciones drenadas).

  Datos publicados: L x B = 2.5 x 1.5 m, d = 0.5 m, phi'_d = 35 deg,
                    c' = 0 kPa, gamma = 18 kN/m3, gamma_R,v = 1.0.
  Valores publicados (los NUEVE, mas la suma):
      N_q = 33.3   N_c = 46.1   N_gamma = 45.2
      s_q = 1.34   s_c = 1.35   s_gamma = 0.82
      q_ult,overburden  = 402.8 kPa
      q_ult,cohesion    =   0   kPa
      q_ult,self-weight = 500.7 kPa
      SUMA q_ult        = 903.5 kPa

  NO es un valor capturado de ninguna implementacion: es la tabla del ejemplo
  resuelto. Las tolerancias de abajo son la resolucion con que el ejemplo
  publica cada cifra (3-4 cifras significativas), no margenes ajustados para
  que pase.

DIVERGENCIA MEDIDA QUE SE ASEVERA (no se promedia ni se elige la que gusta)
--------------------------------------------------------------------------
Sobre el lote comun, ``evaluate_bearing`` (legacy) frente a la canonica:

    caso                                   legacy    canonica   legacy/canon
    S1 cuadrada, centrada                 1372.43     1471.33      0.9328
    S3 cuadrada + exc e=0.30 m            1372.43     1312.76      1.0455
    S4 cuadrada + incl H=150/V=1000       1372.43     1098.87      1.2490
    S5 cuadrada + exc 0.30 + incl         1372.43      972.53      1.4112  <--
    C4 arcilla + incl H=150/V=1000         492.30      449.17      1.0960

El legacy NO reacciona a la excentricidad ni a la inclinacion (devuelve el
mismo numero en S1, S3, S4 y S5), asi que su error crece con la carga real y
SIEMPRE del lado INSEGURO: +41.12 % en S5. Ese 41 % es el mismo orden de
magnitud que motivo esta consolidacion.
"""

from __future__ import annotations

import pytest

from terzaghi.bearing_capacity import BearingCapacityInput, evaluate_bearing

foundationcalc = pytest.importorskip(
    "foundationcalc",
    reason="la canonica vive en FoundationDesignJm; sin el paquete no hay que consolidar",
)

from foundationcalc.analysis.bearing_capacity import (  # noqa: E402
    BearingCapacityFormula,
    drained_bearing_capacity,
    undrained_bearing_capacity,
)
from foundationcalc.core.geometry import RectangularFoundation  # noqa: E402
from foundationcalc.core.soil import SoilLayer  # noqa: E402

from terzaghi.bearing_capacity import evaluate_bearing_ec7  # noqa: E402


# --- Ejemplo publicado W00675 §4.3 DA1-C1 ---------------------------------
W00675_4_3_DA1C1_DATOS = dict(
    B_m=1.5, L_m=2.5, D_f_m=0.5, phi_deg=35.0, c_kPa=0.0, gamma_kN_m3=18.0,
)
W00675_4_3_DA1C1_PUBLICADO = dict(
    Nq=33.3, Nc=46.1, Ngamma=45.2,
    sq=1.34, sc=1.35, sgamma=0.82,
    q_overburden=402.8, q_cohesion=0.0, q_self_weight=500.7,
    q_ult=903.5,
)


def _canonica_directa(B_m, L_m, D_f_m, phi_deg, c_kPa, gamma_kN_m3,
                      e_B_m=0.0, e_L_m=0.0, H_kN=0.0, V_kN=0.0):
    """Llama a la canonica SIN pasar por Terzaghi (oraculo del test de delegacion).

    OJO: la geometria de FoundationDesignJm va en MILIMETROS.
    """
    return drained_bearing_capacity(
        foundation=RectangularFoundation(
            length=L_m * 1000.0, width=B_m * 1000.0,
            thickness=300.0, embedment_depth=D_f_m * 1000.0,
        ),
        soil=SoilLayer(
            thickness=10.0, friction_angle=phi_deg,
            cohesion=c_kPa, unit_weight=gamma_kN_m3,
        ),
        e_x=e_L_m, e_y=e_B_m, H_load=H_kN, V_load=V_kN,
        formula=BearingCapacityFormula.CHEN_EC7,
    )


# (tag, kwargs) — lote comun de consistencia cruzada
LOTE = [
    ("S1", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0, gamma_kN_m3=19.0)),
    ("S2", dict(B_m=2.0, L_m=4.0, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0, gamma_kN_m3=19.0)),
    ("S3", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0, gamma_kN_m3=19.0,
                e_B_m=0.30)),
    ("S4", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0, gamma_kN_m3=19.0,
                H_kN=150.0, V_kN=1000.0)),
    ("S5", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0, gamma_kN_m3=19.0,
                e_B_m=0.30, H_kN=150.0, V_kN=1000.0)),
    ("S7", dict(B_m=2.0, L_m=2.0, D_f_m=3.0, phi_deg=32.0, c_kPa=0.0, gamma_kN_m3=19.0)),
    ("C1", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=0.0, c_kPa=75.0, gamma_kN_m3=18.0)),
    ("C2", dict(B_m=2.0, L_m=4.0, D_f_m=1.5, phi_deg=0.0, c_kPa=75.0, gamma_kN_m3=18.0)),
    ("C3", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=0.0, c_kPa=75.0, gamma_kN_m3=18.0,
                e_B_m=0.30)),
    ("C4", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=0.0, c_kPa=75.0, gamma_kN_m3=18.0,
                H_kN=150.0, V_kN=1000.0)),
]


# ==========================================================================
# 1. GOLDEN PUBLICADO — fija la canonica contra el ejemplo resuelto W00675
# ==========================================================================
def test_golden_w00675_pad_footing_da1c1_nueve_valores_publicados() -> None:
    """Los NUEVE valores intermedios publicados del ejemplo W00675 §4.3 DA1-C1.

    Se accede a la canonica A TRAVES de la puerta de Terzaghi: si la delegacion
    se rompiera, este golden cae con ella.

    Tolerancias = resolucion de la cifra publicada:
      N_q, N_c, N_gamma  -> publicados con 1 decimal   -> abs = 5e-2
      s_q, s_c, s_gamma  -> publicados con 2 decimales -> abs = 5e-3
      terminos de q_ult  -> publicados con 1 decimal   -> abs = 5e-2
    """
    r = evaluate_bearing_ec7(**W00675_4_3_DA1C1_DATOS)
    p = W00675_4_3_DA1C1_PUBLICADO

    assert r.Nq == pytest.approx(p["Nq"], abs=5e-2)
    assert r.Nc == pytest.approx(p["Nc"], abs=5e-2)
    assert r.Ngamma == pytest.approx(p["Ngamma"], abs=5e-2)

    assert r.sq == pytest.approx(p["sq"], abs=5e-3)
    assert r.sc == pytest.approx(p["sc"], abs=5e-3)
    assert r.sgamma == pytest.approx(p["sgamma"], abs=5e-3)

    assert r.q_ult_overburden == pytest.approx(p["q_overburden"], abs=5e-2)
    assert r.q_ult_cohesion == pytest.approx(p["q_cohesion"], abs=5e-2)
    assert r.q_ult_self_weight == pytest.approx(p["q_self_weight"], abs=5e-2)

    assert r.q_ult == pytest.approx(p["q_ult"], abs=5e-2)


def test_golden_w00675_suma_de_terminos_es_la_publicada() -> None:
    """La suma de los tres terminos publicados es el q_ult publicado.

    Comprueba la ARITMETICA de la fuente (402.8 + 0 + 500.7 = 903.5) y que la
    canonica no compensa un termino con otro para acertar el total.
    """
    p = W00675_4_3_DA1C1_PUBLICADO
    assert (p["q_overburden"] + p["q_cohesion"] + p["q_self_weight"]
            == pytest.approx(p["q_ult"], abs=1e-9))

    r = evaluate_bearing_ec7(**W00675_4_3_DA1C1_DATOS)
    assert (r.q_ult_overburden + r.q_ult_cohesion + r.q_ult_self_weight
            == pytest.approx(r.q_ult, rel=1e-12))


def test_golden_w00675_el_legacy_NO_reproduce_el_ejemplo_publicado() -> None:
    """EVIDENCIA de por que la canonica no es la de Terzaghi.

    Sobre el MISMO caso publicado, ``evaluate_bearing`` se desvia +2.6 % con
    sus factores de forma no publicados; forzando N_gamma de Brinch Hansen la
    desviacion llega a -17 %. La canonica acierta a -0.004 %.
    """
    pub = W00675_4_3_DA1C1_PUBLICADO["q_ult"]

    legacy_vesic = evaluate_bearing(
        BearingCapacityInput(**W00675_4_3_DA1C1_DATOS, method="vesic"),
        code="EU").q_ult_kPa
    legacy_bh = evaluate_bearing(
        BearingCapacityInput(**W00675_4_3_DA1C1_DATOS, method="brinch_hansen"),
        code="EU").q_ult_kPa
    canonica = evaluate_bearing_ec7(**W00675_4_3_DA1C1_DATOS).q_ult

    assert legacy_vesic == pytest.approx(927.13, abs=5e-2)
    assert legacy_bh == pytest.approx(748.10, abs=5e-2)

    err_legacy_vesic = (legacy_vesic - pub) / pub
    err_legacy_bh = (legacy_bh - pub) / pub
    err_canonica = (canonica - pub) / pub

    assert err_legacy_vesic == pytest.approx(+0.0262, abs=5e-4)
    assert err_legacy_bh == pytest.approx(-0.1720, abs=5e-4)
    # La canonica cae dentro del redondeo del propio ejemplo publicado.
    assert abs(err_canonica) < 1e-4
    assert abs(err_canonica) < abs(err_legacy_vesic) / 100.0


# ==========================================================================
# 2. CONSISTENCIA CRUZADA — la delegacion PRESERVA valores (no es copia)
# ==========================================================================
@pytest.mark.parametrize("tag,kw", LOTE, ids=[t for t, _ in LOTE])
def test_delegacion_preserva_valores_bit_a_bit_sobre_el_lote(tag: str, kw: dict) -> None:
    """``evaluate_bearing_ec7`` devuelve EXACTAMENTE lo que devuelve la canonica.

    Igualdad relativa 1e-12 sobre los tres terminos y sobre q_ult: si Terzaghi
    hubiese COPIADO la formula en vez de delegar, el menor detalle de orden de
    operaciones rompe esta tolerancia.
    """
    via_terzaghi = evaluate_bearing_ec7(**kw)
    directo = _canonica_directa(**kw)

    assert via_terzaghi.q_ult == pytest.approx(directo.q_ult, rel=1e-12)
    assert via_terzaghi.q_ult_overburden == pytest.approx(directo.q_ult_overburden, rel=1e-12)
    assert via_terzaghi.q_ult_cohesion == pytest.approx(directo.q_ult_cohesion, rel=1e-12)
    assert via_terzaghi.q_ult_self_weight == pytest.approx(directo.q_ult_self_weight, rel=1e-12)
    assert via_terzaghi.Nq == pytest.approx(directo.Nq, rel=1e-12)
    assert via_terzaghi.Nc == pytest.approx(directo.Nc, rel=1e-12)
    assert via_terzaghi.Ngamma == pytest.approx(directo.Ngamma, rel=1e-12)
    assert via_terzaghi.B_eff == pytest.approx(directo.B_eff, rel=1e-12)
    assert via_terzaghi.L_eff == pytest.approx(directo.L_eff, rel=1e-12)


def test_delegacion_es_delegacion_y_no_copia(monkeypatch: pytest.MonkeyPatch) -> None:
    """PRUEBA ESTRUCTURAL de que se delega: si se parchea la canonica, el
    resultado que devuelve Terzaghi cambia.

    Una reimplementacion copiada seguiria devolviendo el valor original y este
    test fallaria. Es la diferencia entre "delegar" y "duplicar".
    """
    import terzaghi.bearing_capacity as gbc

    centinela = object()

    def _canonica_falsa(**kwargs):
        return centinela

    monkeypatch.setattr(gbc, "_canonical_drained_bearing_capacity", _canonica_falsa)
    assert evaluate_bearing_ec7(**W00675_4_3_DA1C1_DATOS) is centinela


def test_delegacion_transporta_excentricidad_e_inclinacion() -> None:
    """La puerta de Terzaghi no se limita a los parametros del legacy: pasa e y H.

    Si ``evaluate_bearing_ec7`` ignorara e_B_m/H_kN (como hace el legacy),
    S1, S3, S4 y S5 devolverian el mismo numero. Deben ser cuatro distintos y
    estrictamente decrecientes: cada efecto quita capacidad.
    """
    base = dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0,
                gamma_kN_m3=19.0)
    s1 = evaluate_bearing_ec7(**base).q_ult
    s3 = evaluate_bearing_ec7(**base, e_B_m=0.30).q_ult
    s4 = evaluate_bearing_ec7(**base, H_kN=150.0, V_kN=1000.0).q_ult
    s5 = evaluate_bearing_ec7(**base, e_B_m=0.30, H_kN=150.0, V_kN=1000.0).q_ult

    assert s1 > s3 > s5
    assert s1 > s4 > s5
    assert len({round(v, 6) for v in (s1, s3, s4, s5)}) == 4


CASOS_COHESIVOS = [
    ("C1", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, cu_kPa=75.0, gamma_kN_m3=18.0)),
    ("C2", dict(B_m=2.0, L_m=4.0, D_f_m=1.5, cu_kPa=75.0, gamma_kN_m3=18.0)),
    ("C3", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, cu_kPa=75.0, gamma_kN_m3=18.0,
                e_B_m=0.30)),
    ("C4", dict(B_m=2.5, L_m=2.5, D_f_m=1.5, cu_kPa=75.0, gamma_kN_m3=18.0,
                H_kN=150.0, V_kN=1000.0)),
]


@pytest.mark.parametrize("tag,kw", CASOS_COHESIVOS,
                         ids=[t for t, _ in CASOS_COHESIVOS])
def test_gate_phi_cero_coincide_bit_a_bit_con_la_clausula_no_drenada(
    tag: str, kw: dict
) -> None:
    """La puerta expone la clausula DRENADA (D.4). Para suelo cohesivo se usa
    con phi=0 y c=c_u: hay que demostrar que eso NO enruta por la clausula
    equivocada de la misma norma.

    MEDIDO: coincide bit a bit (diferencia 0.00e+00 kPa) con
    ``undrained_bearing_capacity`` (EN 1997-1 Anexo D.3) en los cuatro casos
    cohesivos del lote, con y sin excentricidad, con y sin inclinacion.

    Coinciden porque en D.4 con phi=0 salen N_q=1, s_q=1 e i_q=1, de modo que
    el termino de sobrecarga se reduce al "+ q" de D.3, y ambas ramas comparten
    N_c = pi+2, s_c = 1+0.2 B/L e i_c.

    Si la canonica cambiara una de las dos ramas sin la otra, este test lo
    detecta: es la garantia de que la puerta de Terzaghi no esconde el mismo
    patron de "parametro declarado y nunca leido" que se documenta en el
    informe para ``foundationcalc/services/bearing.py``.
    """
    cu = kw["cu_kPa"]
    drenada = evaluate_bearing_ec7(
        B_m=kw["B_m"], L_m=kw["L_m"], D_f_m=kw["D_f_m"],
        phi_deg=0.0, c_kPa=cu, gamma_kN_m3=kw["gamma_kN_m3"],
        e_B_m=kw.get("e_B_m", 0.0), H_kN=kw.get("H_kN", 0.0),
        V_kN=kw.get("V_kN", 0.0),
    ).q_ult

    no_drenada = undrained_bearing_capacity(
        foundation=RectangularFoundation(
            length=kw["L_m"] * 1000.0, width=kw["B_m"] * 1000.0,
            thickness=300.0, embedment_depth=kw["D_f_m"] * 1000.0,
        ),
        soil=SoilLayer(
            thickness=10.0, friction_angle=0.0, cohesion=0.0,
            undrained_shear_strength=cu, unit_weight=kw["gamma_kN_m3"],
        ),
        e_y=kw.get("e_B_m", 0.0), H_load=kw.get("H_kN", 0.0),
    ).q_ult

    assert drenada == no_drenada, (
        f"{tag}: la puerta drenada con phi=0 ({drenada!r}) deberia coincidir "
        f"exactamente con la clausula no drenada D.3 ({no_drenada!r})"
    )


# ==========================================================================
# 3. LA DIVERGENCIA MEDIDA — se ASEVERA, no se promedia
# ==========================================================================
def test_divergencia_legacy_vs_canonica_llega_al_41_por_ciento() -> None:
    """HALLAZGO: el legacy sobreestima q_ult un 41.1 % en el caso S5.

    S5 = zapata cuadrada 2.5x2.5 m, D_f = 1.5 m, arena phi'=32, gamma=19,
    con excentricidad e_B = 0.30 m Y carga inclinada H=150 / V=1000 kN.

    El legacy ignora AMBOS efectos, asi que devuelve el mismo numero que en el
    caso centrado (S1). La razon legacy/canonica se aseveran a la resolucion
    con que se midieron.
    """
    base = dict(B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0,
                gamma_kN_m3=19.0)

    legacy = evaluate_bearing(
        BearingCapacityInput(**base, method="vesic"), code="EU").q_ult_kPa
    canonica_s5 = evaluate_bearing_ec7(
        **base, e_B_m=0.30, H_kN=150.0, V_kN=1000.0).q_ult

    assert legacy == pytest.approx(1372.4301, abs=5e-4)
    assert canonica_s5 == pytest.approx(972.5271, abs=5e-4)
    assert legacy / canonica_s5 == pytest.approx(1.4112, abs=5e-4)


def test_legacy_es_ciego_a_la_excentricidad_y_a_la_inclinacion() -> None:
    """El legacy devuelve EXACTAMENTE el mismo q_ult con y sin e, con y sin H.

    No es una aproximacion: no tiene los parametros. Se fija para que nadie
    "arregle" el 41 % tocando tolerancias en vez de la cobertura fisica.
    """
    sig = ("B_m", "L_m", "D_f_m", "phi_deg", "c_kPa", "gamma_kN_m3", "method")
    assert set(BearingCapacityInput.__dataclass_fields__) == set(sig)
    for ausente in ("e_B_m", "e_L_m", "H_kN", "V_kN", "water_table_m"):
        assert ausente not in BearingCapacityInput.__dataclass_fields__


@pytest.mark.parametrize("tag,kw", LOTE, ids=[t for t, _ in LOTE])
def test_legacy_es_inseguro_siempre_que_hay_excentricidad_o_inclinacion(
    tag: str, kw: dict
) -> None:
    """Con e != 0 o H != 0 el legacy SIEMPRE queda por encima de la canonica.

    Del lado inseguro, nunca del conservador. Es la propiedad que hace que la
    divergencia importe: no es ruido simetrico.
    """
    tiene_e_o_H = bool(kw.get("e_B_m") or kw.get("e_L_m") or kw.get("H_kN"))
    if not tiene_e_o_H:
        pytest.skip("caso centrado y vertical: la comparacion vive en otro test")

    legacy_kw = {k: v for k, v in kw.items()
                 if k in ("B_m", "L_m", "D_f_m", "phi_deg", "c_kPa", "gamma_kN_m3")}
    legacy = evaluate_bearing(
        BearingCapacityInput(**legacy_kw, method="vesic"), code="EU").q_ult_kPa
    canonica = evaluate_bearing_ec7(**kw).q_ult

    assert legacy > canonica, (
        f"{tag}: se esperaba legacy INSEGURO (mayor) frente a la canonica; "
        f"legacy={legacy:.4f} canonica={canonica:.4f}"
    )


# ==========================================================================
# 4. LA PUERTA VIEJA AVISA
# ==========================================================================
def test_evaluate_bearing_legacy_emite_deprecationwarning() -> None:
    """``evaluate_bearing`` sigue funcionando (no se rompe a nadie) pero avisa
    y NOMBRA la canonica a la que hay que migrar."""
    inp = BearingCapacityInput(
        B_m=2.5, L_m=2.5, D_f_m=1.5, phi_deg=32.0, c_kPa=0.0,
        gamma_kN_m3=19.0, method="vesic",
    )
    with pytest.warns(DeprecationWarning) as capturado:
        r = evaluate_bearing(inp, code="EU")

    assert r.q_ult_kPa == pytest.approx(1372.4301, abs=5e-4)
    mensaje = str(capturado[0].message)
    assert "evaluate_bearing_ec7" in mensaje
    assert "foundationcalc" in mensaje


def test_el_legacy_no_cambia_de_valor_al_quedar_deprecado() -> None:
    """Deprecar NO es cambiar numeros: los valores del legacy siguen siendo los
    que fijaron los goldens y caracterizaciones existentes."""
    inp = BearingCapacityInput(
        B_m=2.0, L_m=2000.0, D_f_m=1.5, phi_deg=35.0, c_kPa=0.0,
        gamma_kN_m3=18.0, method="vesic",
    )
    with pytest.warns(DeprecationWarning):
        r = evaluate_bearing(inp, code="EU")
    # Mismo valor que test_golden_bearing_capacity_published.py fija hoy.
    assert r.q_ult_kPa == pytest.approx(1763.5157, abs=1e-3)
    assert r.q_adm_kPa == pytest.approx(1259.6540, abs=1e-3)
