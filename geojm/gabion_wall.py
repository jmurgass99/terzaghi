# -*- coding: utf-8 -*-
"""
Muro de gaviones (gravedad) — diseno por estados limite ultimos (EN 1997-1).

Verifica un muro de gaviones escalonado (capas de ancho creciente hacia la base)
frente a las tres comprobaciones externas ULS de EN 1997-1, en condicion drenada
o no drenada, con los factores parciales de los Design Approaches (DA1-a/b, DA2):

  ULS-1  Capacidad portante : E_d (presion de contacto) <= R_d (q_f del terreno)
  ULS-2  Deslizamiento      : H (empuje activo horiz.) <= H_ult
  ULS-3  Vuelco             : M_vuelco <= M_estabilizador

Referencias: EN 1997-1 (Eurocodigo 7); Craig's Soil Mechanics cap. 11; metodo
de Mohammad Hanif "Design of Gabion Retaining Structure". Validado contra ese
ejemplo (DA1-a, no drenado): Ka=0.28, W=230 kN, q_f=514 kPa, FS portante~3.3,
deslizamiento~3.08, vuelco~3.83.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Literal

_GAMMA_W = 9.81  # kN/m3

# Factores parciales EN 1997-1 por Design Approach (G, Q, phi, cu, Rh deslizam., Rb base)
DESIGN_APPROACHES: Dict[str, Dict[str, float]] = {
    "DA1a": {"gG": 1.35, "gQ": 1.50, "gphi": 1.00, "gcu": 1.00, "gRh": 1.00, "gRb": 1.00},
    "DA1b": {"gG": 1.00, "gQ": 1.30, "gphi": 1.00, "gcu": 1.40, "gRh": 1.00, "gRb": 1.25},
    "DA2":  {"gG": 1.35, "gQ": 1.50, "gphi": 1.00, "gcu": 1.00, "gRh": 1.10, "gRb": 1.00},
}


@dataclass(frozen=True)
class GabionLayer:
    width_m: float          # ancho de la capa (crece hacia la base)
    height_m: float = 1.0


@dataclass(frozen=True)
class GabionSoil:
    gamma_s: float = 19.0       # peso especifico del relleno retenido (kN/m3)
    phi_deg: float = 34.0       # angulo de friccion (drenado)
    c_kPa: float = 0.0          # cohesion efectiva
    cu_kPa: float = 100.0       # resistencia no drenada
    surcharge_kPa: float = 20.0  # sobrecarga en superficie


@dataclass
class GabionCheck:
    name: str
    E_d: float
    R_d: float
    FS: float
    ok: bool
    units: str = ""


def Ka_rankine(phi_deg: float) -> float:
    """Coeficiente de empuje activo de Rankine: (1-sin) / (1+sin)."""
    s = math.sin(math.radians(phi_deg))
    return (1.0 - s) / (1.0 + s)


@dataclass
class GabionWall:
    layers: List[GabionLayer]
    soil: GabionSoil = field(default_factory=GabionSoil)
    gamma_gab: float = 23.0          # peso especifico del gavion relleno (kN/m3)
    design_approach: Literal["DA1a", "DA1b", "DA2"] = "DA1a"
    drained: bool = False            # False = no drenado (cu); True = drenado (c', phi')

    # --- geometria ---
    @property
    def H(self) -> float:
        return sum(l.height_m for l in self.layers)

    @property
    def B(self) -> float:
        return max(l.width_m for l in self.layers)

    @property
    def gf(self) -> Dict[str, float]:
        return DESIGN_APPROACHES[self.design_approach]

    # --- acciones ---
    def active_thrust(self) -> float:
        """Empuje activo total S_A (kN/m), caracteristico. Suelo + sobrecarga.

        No drenado: usa peso sumergido (gamma_s - gamma_w). Drenado: gamma_s.
        """
        Ka = Ka_rankine(self.soil.phi_deg)
        gamma_eff = (self.soil.gamma_s - _GAMMA_W) if not self.drained else self.soil.gamma_s
        S_soil = 0.5 * Ka * gamma_eff * self.H ** 2
        S_surch = Ka * self.soil.surcharge_kPa * self.H
        return S_soil + S_surch

    def weight_and_moment(self):
        """Peso total Gk (kN/m), momento estabilizador respecto a la puntera y
        brazo medio. Capas alineadas por el trasdos (lado del terreno); la
        puntera esta al frente, a distancia B."""
        W_total = 0.0
        M_stab = 0.0
        for l in self.layers:
            Wi = l.width_m * l.height_m * self.gamma_gab
            arm = self.B - l.width_m / 2.0   # brazo desde la puntera (trasdos alineado)
            W_total += Wi
            M_stab += Wi * arm
        return W_total, M_stab

    # --- ULS-1: capacidad portante ---
    def bearing_check(self) -> GabionCheck:
        gf = self.gf
        Ka = Ka_rankine(self.soil.phi_deg)
        phi = math.radians(self.soil.phi_deg)
        SA = self.active_thrust()
        W, M_stab = self.weight_and_moment()
        # Carga vertical de diseno (peso + componente vertical del empuje).
        N_rd = W * gf["gG"] + SA * math.sin(phi) * gf["gG"]
        # Momento neto y excentricidad respecto al centro de la base.
        M_net = (M_stab + SA * math.sin(phi) * self.B - SA * math.cos(phi) * (self.H / 3.0)) * gf["gG"]
        e = abs(self.B / 2.0 - M_net / N_rd) if N_rd else 0.0
        Beff = max(self.B - 2.0 * e, 1e-6)
        # Capacidad del terreno.
        if not self.drained:
            # Gavion apoyado en superficie: sobrecarga en la base de cimentacion ~0.
            qf = 5.14 * self.soil.cu_kPa / gf["gcu"]   # Nc=5.14, sc=1 (B/L~0)
        else:
            Nq = (1 + math.sin(phi)) / (1 - math.sin(phi)) * math.exp(math.pi * math.tan(phi))
            Nc = (Nq - 1) / math.tan(phi)
            Ng = 2 * (Nq - 1) * math.tan(phi)
            q0 = self.soil.surcharge_kPa
            qf = (Nq * q0 + 0.5 * self.soil.gamma_s * Beff * Ng + Nc * self.soil.c_kPa)
        R_d = qf * Beff / gf["gRb"]                   # resistencia (kN/m) — uses Beff, not full B
        E_d_force = N_rd                              # fuerza vertical actuante (kN/m)
        FS = R_d / E_d_force if E_d_force else float("inf")
        return GabionCheck("ULS-1 Capacidad portante", E_d_force, R_d, FS, FS >= 1.0, "kN/m")

    # --- ULS-2: deslizamiento ---
    def sliding_check(self) -> GabionCheck:
        gf = self.gf
        phi = math.radians(self.soil.phi_deg)
        SA = self.active_thrust()
        W, _ = self.weight_and_moment()
        H = SA * math.cos(phi) * gf["gG"]            # empuje horizontal de diseno
        if not self.drained:
            alpha = max(1.16 - self.soil.cu_kPa / 185.0, 0.3)   # factor de adhesion
            R_d = alpha * (self.soil.cu_kPa / gf["gcu"]) * self.B / gf["gRh"]
        else:
            N = W * gf["gG"] + SA * math.sin(phi) * gf["gG"]
            R_d = (N * math.tan(phi) + self.soil.c_kPa * self.B) / gf["gRh"]
        FS = R_d / H if H else float("inf")
        return GabionCheck("ULS-2 Deslizamiento", H, R_d, FS, FS >= 1.0, "kN/m")

    # --- ULS-3: vuelco ---
    def overturning_check(self) -> GabionCheck:
        gf = self.gf
        phi = math.radians(self.soil.phi_deg)
        SA = self.active_thrust()
        W, M_stab = self.weight_and_moment()
        # Estabilizador: peso + componente vertical del empuje (brazo = B).
        R_d = (M_stab + SA * math.sin(phi) * self.B) / gf["gRb"]
        # Volcador: componente horizontal del empuje (brazo = H/3).
        E_d = SA * math.cos(phi) * (self.H / 3.0) * gf["gG"]
        FS = R_d / E_d if E_d else float("inf")
        return GabionCheck("ULS-3 Vuelco", E_d, R_d, FS, FS >= 1.0, "kN*m/m")

    # --- ULS-6: estabilidad interna por capa (curso a curso) ---
    def internal_stability(self) -> List[GabionCheck]:
        """FS de deslizamiento de cada curso sobre el inferior (de arriba abajo).

        Para cada capa i, el empuje activo acumulado por encima desliza sobre la
        junta; la resistencia es el peso de las capas superiores por friccion del
        gavion. Sigue el metodo del ejemplo (ULS-6a)."""
        gf = self.gf
        Ka = Ka_rankine(self.soil.phi_deg)
        gamma_eff = (self.soil.gamma_s - _GAMMA_W) if not self.drained else self.soil.gamma_s
        phi = math.radians(self.soil.phi_deg)
        checks: List[GabionCheck] = []
        # Altura acumulada desde arriba hasta la base de cada capa.
        h_top = 0.0
        W_above = 0.0
        for i, lay in enumerate(self.layers):
            h_base = h_top + lay.height_m            # profundidad de la junta inferior
            W_above += lay.width_m * lay.height_m * self.gamma_gab
            # Empuje activo sobre el bloque por encima de esta junta.
            SA = 0.5 * Ka * gamma_eff * h_base ** 2 + Ka * self.soil.surcharge_kPa * h_base
            H = SA * math.cos(phi) * gf["gG"]
            R_d = (W_above * gf["gG"] * math.tan(phi)) / gf["gRh"]
            FS = R_d / H if H else float("inf")
            checks.append(GabionCheck(f"ULS-6 Curso {i + 1} (deslizamiento)", H, R_d, FS, FS >= 1.0, "kN/m"))
            h_top = h_base
        return checks

    # --- ULS-4: estabilidad global (circular) ---
    def global_stability_undrained(self, r_m: float, La_m: float, W_kN: float, d_m: float) -> GabionCheck:
        """FS de estabilidad global, condicion no drenada (momento sobre circulo).

        F = M_R / M_A = (cu · La · r) / (W · d).  Parametros del circulo de falla
        critico (radio r, longitud de arco La, peso del bloque W, brazo d)."""
        cu = self.soil.cu_kPa / self.gf["gcu"]
        M_R = cu * La_m * r_m
        M_A = W_kN * d_m
        FS = M_R / M_A if M_A else float("inf")
        return GabionCheck("ULS-4 Estabilidad global", M_A, M_R, FS, FS >= 1.0, "kN*m/m")

    def verify_all(self) -> List[GabionCheck]:
        """Las tres verificaciones EXTERNAS (ULS-1/2/3)."""
        return [self.bearing_check(), self.sliding_check(), self.overturning_check()]

    def verify_full(self, global_circle: dict | None = None) -> List[GabionCheck]:
        """Externas + internas por capa (+ global si se dan datos del circulo)."""
        out = self.verify_all() + self.internal_stability()
        if global_circle:
            out.append(self.global_stability_undrained(**global_circle))
        return out


__all__ = [
    "GabionLayer", "GabionSoil", "GabionWall", "GabionCheck",
    "Ka_rankine", "DESIGN_APPROACHES",
]
