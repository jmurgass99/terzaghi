"""Asiento de consolidación corregido por Skempton-Bjerrum (μ según A y H/B) y auditoría de asientos diferenciales entre zapatas con los límites del Anexo H de EN 1997-1.

El asiento edométrico S_oed se multiplica por μ(A, H/B): arcillas sobreconsolidadas (A ≈ 0–0,5) asientan
menos que lo que dice el edómetro; normalmente consolidadas (A ≈ 1) igual. Después, cuatro zapatas de
un pórtico con asientos distintos: la distorsión angular δ/L se compara con 1/500 (aviso, daño no
estructural) y 1/300 (error, daño estructural) para cada par.

Ejecutar:  python examples/settlement_skempton_bjerrum_mu_correction_and_differential_distortion_audit_annex_h.py
"""
from terzaghi.audit.differential_settlement import check_differential_settlement
from terzaghi.skempton_bjerrum import SkemptonBjerrumInput, differential_settlement_ratio, skempton_bjerrum


def main() -> None:
    print("μ de Skempton-Bjerrum (tabla simplificada de Bjerrum 1972 para zapata circular; interpolación bilineal):")
    print(f"  {'H/B':>4} " + " ".join(f"A = {A:4.2f}" for A in (0.0, 0.25, 0.5, 0.75, 1.0)))
    for hb in (0.25, 0.5, 1.0, 2.0, 4.0, 10.0):
        print(f"  {hb:4.2f} " + " ".join(f"{skempton_bjerrum(SkemptonBjerrumInput(100.0, A, hb)).mu:8.3f}" for A in (0.0, 0.25, 0.5, 0.75, 1.0)))
    S_oed = 85.0
    print(f"\nZapata B = 3 m sobre 6 m de arcilla (H/B = 2): S_oed = {S_oed:.0f} mm")
    for nombre, A in (("sobreconsolidada (A = 0,3)", 0.3), ("ligeramente SC (A = 0,6)", 0.6), ("normalmente consolidada (A = 1,0)", 1.0)):
        r = skempton_bjerrum(SkemptonBjerrumInput(S_oed, A, 2.0, code="EU"))
        print(f"  {nombre:34} μ = {r.mu:.3f} → S = {r.settlement_corrected_mm:.1f} mm")
    zapatas = [{"name": "Z1", "settlement_mm": 22.0, "x": 0.0, "y": 0.0}, {"name": "Z2", "settlement_mm": 38.0, "x": 6.0, "y": 0.0},
               {"name": "Z3", "settlement_mm": 61.0, "x": 12.0, "y": 0.0}, {"name": "Z4", "settlement_mm": 30.0, "x": 6.0, "y": 5.0}]
    print("\nPórtico con cuatro zapatas (asientos 22/38/61/30 mm, luces 5–6 m):")
    print(f"  {'par':6} {'δ [mm]':>6} {'L [m]':>6} {'δ/L':>8} {'1/(δ/L)':>8}  veredicto")
    hallazgos = {(f.footing_a, f.footing_b): f for f in check_differential_settlement(zapatas)}
    for i in range(len(zapatas)):
        for j in range(i + 1, len(zapatas)):
            a, b = zapatas[i], zapatas[j]
            L = ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5
            ratio = differential_settlement_ratio(a["settlement_mm"], b["settlement_mm"], L)
            f = hallazgos.get((a["name"], b["name"]))
            print(f"  {a['name']}-{b['name']:3} {abs(a['settlement_mm'] - b['settlement_mm']):6.0f} {L:6.2f} {ratio:8.5f} {1 / ratio if ratio else float('inf'):8.0f}  {f.severity if f else 'OK (< 1/500)'}")
    print(f"\n  Hallazgos del auditor: {len(hallazgos)} ({sum(f.severity == 'ERROR' for f in hallazgos.values())} ERROR, {sum(f.severity == 'WARNING' for f in hallazgos.values())} WARNING)")
    for f in hallazgos.values():
        print(f"   - {f.message}")
    print("\nLa tabla de μ es una simplificación de la figura de Bjerrum (cinco columnas de H/B); para un informe conviene leer la curva original. Los límites 1/500 y 1/300 son los orientativos del Anexo H para pórticos: estructuras de fábrica o con acabados frágiles piden menos.")


if __name__ == "__main__":
    main()
