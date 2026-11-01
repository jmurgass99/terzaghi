"""FastAPI app para Terzaghi."""
from typing import Any, Literal


def create_router() -> Any:
    """Devuelve el APIRouter con los endpoints. Mountable en gateway."""
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field

    from ..bearing_capacity import BearingCapacityInput, evaluate_bearing, evaluate_bearing_ec7
    from ..liquefaction import LiquefactionInput, evaluate_liquefaction
    from ..materials import mander_confined_concrete
    from ..piles import (
        pile_group_efficiency_lateral,
        py_matlock_soft_clay,
        py_reese_sand,
    )
    from terzaghi._common.units import convert

    router = APIRouter()

    @router.get("/api/geo/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    class PYMatlockPayload(BaseModel):
        z_m: float = Field(..., gt=0)
        D_m: float = Field(..., gt=0)
        su_kPa: float = Field(..., gt=0)
        gamma_kN_m3: float = 17.0
        eps_50: float = 0.02

    @router.post("/api/geo/py/matlock", summary="Curvas p-y para arcillas saturadas según formulación de Matlock (1970)")
    def py_matlock(payload: PYMatlockPayload) -> dict[str, list]:
        p, y = py_matlock_soft_clay(**payload.model_dump())
        return {"p_kN_per_m": p.tolist(), "y_m": y.tolist()}

    class PYReesePayload(BaseModel):
        z_m: float = Field(..., gt=0)
        D_m: float = Field(..., gt=0)
        phi_deg: float = Field(..., gt=0, le=50)
        gamma_kN_m3: float = 18.0
        k_pH_kN_m3: float = 25_000.0

    @router.post("/api/geo/py/reese", summary="Curvas p-y para arenas según formulación de Reese, Cox & Koop (1974)")
    def py_reese(payload: PYReesePayload) -> dict[str, list]:
        p, y = py_reese_sand(**payload.model_dump())
        return {"p_kN_per_m": p.tolist(), "y_m": y.tolist()}

    class GroupPayload(BaseModel):
        s_over_D: float = Field(..., gt=0)
        rows: int = Field(..., ge=1)

    @router.post("/api/geo/pile-group/lateral", summary="Respuesta lateral de grupos de pilotes con factores p-multiplier")
    def pile_group(payload: GroupPayload):
        try:
            r = pile_group_efficiency_lateral(**payload.model_dump())
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {
            "global_efficiency": r.global_efficiency,
            "leading": r.p_multiplier_leading,
            "first_trailing": r.p_multiplier_first_trailing,
            "second_trailing": r.p_multiplier_second_trailing,
        }

    class LiquefactionPayload(BaseModel):
        depth_m: float
        sigma_v_kPa: float = Field(..., gt=0)
        sigma_v_eff_kPa: float = Field(..., gt=0)
        N1_60_cs: float = Field(..., ge=0)
        a_max_g: float = Field(..., gt=0)
        Mw: float = 7.5

    @router.post("/api/geo/liquefaction", summary="Evaluación de licuefacción cíclica según método simplificado NCEER / Youd")
    def liquefaction(payload: LiquefactionPayload):
        try:
            r = evaluate_liquefaction(LiquefactionInput(**payload.model_dump()))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return r.to_dict()

    class ManderPayload(BaseModel):
        fc: float = Field(..., gt=0)
        fyh: float = Field(..., gt=0)
        rho_x: float = Field(..., gt=0)
        rho_y: float = Field(..., gt=0)
        b_core_mm: float = Field(..., gt=0)
        h_core_mm: float = Field(..., gt=0)
        s_mm: float = Field(..., gt=0)

    @router.post("/api/geo/mander", summary="Modelo constitutivo de confinamiento de hormigón de Mander (1988)")
    def mander(payload: ManderPayload):
        try:
            r = mander_confined_concrete(**payload.model_dump())
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"fcc_MPa": r.fcc_MPa, "eps_cc": r.eps_cc, "eps_cu": r.eps_cu,
                "K_confinement": r.K_confinement}

    class BearingPayload(BaseModel):
        B_m: float = Field(..., gt=0)
        L_m: float = Field(..., gt=0)
        D_f_m: float = Field(..., ge=0)
        phi_deg: float = Field(..., ge=0, le=50)
        c_kPa: float = Field(0.0, ge=0)
        gamma_kN_m3: float = 18.0
        method: Literal["terzaghi", "meyerhof", "vesic", "brinch_hansen", "chen_ec7"] = "vesic"
        code: Literal["EU", "US", "CO", "AU", "SG"] = "EU"
        e_B_m: float = Field(0.0, ge=0)
        e_L_m: float = Field(0.0, ge=0)
        H_kN: float = Field(0.0, ge=0)
        V_kN: float = Field(0.0, ge=0)
        zw_m: float | None = None
        use_ec7_canonical: bool = True

    @router.post("/api/geo/bearing-capacity", summary="Capacidad de carga admisible y de hundimiento según EN 1997-1 Anexo D / Brinch Hansen / Vesic")
    def bearing_capacity(payload: BearingPayload):
        """Capacidad portante de zapata superficial vía implementación canónica EN 1997-1 Anexo D."""
        try:
            if not payload.use_ec7_canonical:
                legacy_method = "meyerhof" if payload.method == "chen_ec7" else payload.method
                r_leg = evaluate_bearing(
                    BearingCapacityInput(
                        B_m=payload.B_m,
                        L_m=payload.L_m,
                        D_f_m=payload.D_f_m,
                        phi_deg=payload.phi_deg,
                        c_kPa=payload.c_kPa,
                        gamma_kN_m3=payload.gamma_kN_m3,
                        method=legacy_method,  # type: ignore[arg-type]
                    ),
                    code=payload.code,
                )
                return {
                    "q_ult_kPa": r_leg.q_ult_kPa,
                    "q_ult_MPa": convert(r_leg.q_ult_kPa, "kPa", "MPa"),
                    "q_adm_kPa": r_leg.q_adm_kPa,
                    "Nc": r_leg.Nc, "Nq": r_leg.Nq, "Ngamma": r_leg.Ngamma,
                    "code_applied": r_leg.code_applied,
                }

            formula_map = {
                "terzaghi": "meyerhof",
                "meyerhof": "meyerhof",
                "vesic": "vesic",
                "brinch_hansen": "brinch_hansen",
                "chen_ec7": "chen_ec7",
            }
            r = evaluate_bearing_ec7(
                B_m=payload.B_m,
                L_m=payload.L_m,
                D_f_m=payload.D_f_m,
                phi_deg=payload.phi_deg,
                c_kPa=payload.c_kPa,
                gamma_kN_m3=payload.gamma_kN_m3,
                e_B_m=payload.e_B_m,
                e_L_m=payload.e_L_m,
                H_kN=payload.H_kN,
                V_kN=payload.V_kN,
                formula=formula_map[payload.method],
                zw_m=payload.zw_m,
            )
            if payload.code in ("EU", "SG"):
                q_adm = r.q_ult / 1.40
            elif payload.code == "US":
                q_adm = 0.50 * r.q_ult
            elif payload.code == "CO":
                q_adm = r.q_ult / 3.0
            else:
                q_adm = 0.45 * r.q_ult
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {
            "q_ult_kPa": r.q_ult,
            "q_ult_MPa": convert(r.q_ult, "kPa", "MPa"),
            "q_adm_kPa": q_adm,
            "Nc": r.Nc, "Nq": r.Nq, "Ngamma": r.Ngamma,
            "B_eff_m": r.B_eff,
            "L_eff_m": r.L_eff,
            "code_applied": payload.code,
        }

    class GazetasPayload(BaseModel):
        L_m: float = Field(..., gt=0)
        B_m: float = Field(..., gt=0)
        Vs_m_per_s: float = Field(200.0, gt=0)
        rho_soil_kg_m3: float = Field(1900.0, gt=0)
        nu_soil: float = Field(0.35, ge=0, le=0.5)

    @router.post("/api/geo/gazetas-springs", summary="Rigideces dinámicas e impedancias de cimentación según Gazetas (1991)")
    def gazetas(payload: GazetasPayload):
        """Resortes de impedancia de fundación superficial (Gazetas 1991)."""
        from ..gazetas_springs import GazetasInput, evaluate_gazetas
        try:
            r = evaluate_gazetas(GazetasInput(**payload.model_dump()))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {
            "Kz_kN_per_m": r.Kz_kN_per_m,
            "Kx_kN_per_m": r.Kx_kN_per_m,
            "Ky_kN_per_m": r.Ky_kN_per_m,
            "Krx_kNm_per_rad": r.Krx_kNm_per_rad,
            "Kry_kNm_per_rad": r.Kry_kNm_per_rad,
            "Krz_kNm_per_rad": r.Krz_kNm_per_rad,
            "G_soil_MPa": r.G_soil_MPa,
        }

    class GazetasSupportPayload(BaseModel):
        L_m: float = Field(..., gt=0)
        B_m: float = Field(..., gt=0)
        P_kN: float = Field(0.0, ge=0)
        Mx_kNm: float = Field(0.0)
        My_kNm: float = Field(0.0)
        Vs_m_per_s: float = Field(200.0, gt=0)
        rho_soil_kg_m3: float = Field(1900.0, gt=0)
        nu_soil: float = Field(0.35, ge=0, le=0.5)

    @router.post("/api/geo/gazetas-support", summary="Rigideces SSI de Gazetas con unidades y deformaciones elásticas P/k")
    def gazetas_support(payload: GazetasSupportPayload):
        """Apoyos elásticos Gazetas de 6 GDL con cálculo directo de asentamiento y giro."""
        from ..gazetas_springs import gazetas_elastic_support_and_settlement
        try:
            r = gazetas_elastic_support_and_settlement(**payload.model_dump())
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return r.to_dict()


    class SsiSpringsPayload(BaseModel):
        L_m: float = Field(..., gt=0)
        B_m: float = Field(..., gt=0)
        Vs_m_per_s: float = Field(..., gt=0)
        rho_soil_kg_m3: float = Field(1900.0, gt=0)
        nu_soil: float = Field(0.35, ge=0, le=0.5)
        frequency_Hz: float = Field(5.0, gt=0)
        material_damping: float = Field(0.05, ge=0, le=0.5)

    @router.post("/api/geo/ssi-springs", summary="Muelles desacoplados de interacción suelo-estructura (SSI)")
    def ssi_springs(payload: SsiSpringsPayload):
        """Resortes dinámicos y dashpots equivalentes de fundación superficial (Gazetas/Novak)."""
        from ..ssi_springs import SsiSpringsInput, calculate_ssi_springs
        try:
            r = calculate_ssi_springs(SsiSpringsInput(**payload.model_dump()))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return r.model_dump()

    class MonopileDynamicPyPayload(BaseModel):
        z_m: float = Field(..., ge=0.0)
        D_m: float = Field(..., gt=0.0)
        Vs_m_per_s: float = Field(..., gt=0.0)
        rho_soil_kg_m3: float = Field(1900.0, gt=0.0)
        soil_type: str = Field("clay")
        su_kPa: float = Field(100.0, ge=0.0)
        phi_deg: float = Field(32.0, ge=0.0, le=50.0)
        gamma_kN_m3: float = Field(18.0, gt=0.0)
        eps_50: float = Field(0.01, gt=0.0)
        k_pH_kN_m3: float = Field(25000.0, gt=0.0)
        frequency_Hz: float = Field(0.2, gt=0.0)
        num_cycles: int = Field(1000, ge=1)
        degradation_coef: float = Field(0.08, ge=0.0, le=0.3)
        dynamic_coef: float = Field(0.15, ge=0.0, le=0.5)
        n_points: int = Field(50, ge=10, le=200)

    @router.post("/api/geo/monopile", summary="Análisis lateral y capacidad de monopilotes offshore bajo viento y oleaje")
    def monopile_dynamic_py(payload: MonopileDynamicPyPayload):
        """Curvas P-y dinámicas y cíclicas para monopilotes eólicos de gran diámetro."""
        from ..piles.dynamic_py import MonopileDynamicPyInput, calculate_monopile_dynamic_py
        try:
            r = calculate_monopile_dynamic_py(MonopileDynamicPyInput(**payload.model_dump()))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return r.model_dump()

    class TunnelWinklerPayload(BaseModel):
        R0_m: float = Field(..., gt=0.0)
        P0_kPa: float = Field(..., gt=0.0)
        E_soil_MPa: float = Field(..., gt=0.0)
        nu_soil: float = Field(0.30, ge=0.0, le=0.5)
        c_kPa: float = Field(..., ge=0.0)
        phi_deg: float = Field(..., ge=0.0, le=50.0)
        E_liner_GPa: float = Field(30.0, gt=0.0)
        nu_liner: float = Field(0.20, ge=0.0, le=0.4)
        thickness_mm: float = Field(200.0, gt=0.0)
        unsupported_convergence_ratio: float = Field(0.30, ge=0.0, le=0.9)
        n_points: int = Field(50, ge=10, le=200)

    @router.post("/api/geo/tunnel-winkler", summary="Interacción suelo-estructura en revestimientos de túnel (modelo Winkler)")
    def tunnel_winkler(payload: TunnelWinklerPayload):
        """Análisis de convergencia-confinamiento y resortes Winkler elastoplásticos para túneles."""
        from ..tunnels import TunnelWinklerInput, calculate_tunnel_confinement
        try:
            r = calculate_tunnel_confinement(TunnelWinklerInput(**payload.model_dump()))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return r.model_dump()

    return router


def create_app() -> Any:
    """App FastAPI standalone."""
    from fastapi import FastAPI

    from .. import __version__

    app = FastAPI(title="Terzaghi API", version=__version__)
    app.include_router(create_router())
    return app
