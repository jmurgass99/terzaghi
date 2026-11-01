"""Eficiencia lateral de un grupo de pilotes 3 × 3: las tres convenciones de p-multiplicadores que conviven en el paquete (Brown 1988, tabla de Mokwa-Duncan y memoria handcalcs) no dicen lo mismo.

Grupo 3 × 3 de pilotes de 0,6 m con separación 1,8 m (s/D = 3) y 3,0 m (s/D = 5), P_single = 200 kN.
`piles.group` interpola Brown et al. (1988) entre s/D = 3 (0,80/0,40/0,30) y 5 (1,00/0,85/0,70);
`piles.mokwa_duncan.p_multiplier` usa una tabla por fila (1,0/0,7/0,5/0,4) independiente de s/D; la
memoria `memos.pile_group_lateral` aplica f_m = 0,64 + 0,36·s/D saturado a 1, que para cualquier
s/D ≥ 1 no reduce nada. Se imprimen las tres para el mismo grupo y se dice cuál usar.

Ejecutar:  python examples/pile_group_p_multipliers_three_conventions_brown_mokwa_duncan_table_and_memo.py
"""
from terzaghi.memos.pile_group_lateral import PileGroupLateralInput, render_pile_group_memo
from terzaghi.piles import pile_group_efficiency_lateral
from terzaghi.piles.mokwa_duncan import p_multiplier

D, P1, ROWS, COLS = 0.6, 200.0, 3, 3


def main() -> None:
    print(f"Grupo {ROWS} × {COLS}, D = {D} m, P_single = {P1:.0f} kN (capacidad lateral de un pilote aislado)\n")
    print(f"  {'s/D':>4} {'Brown 1988 (f_1, f_2, f_3)':>26} {'η_Brown':>8} {'tabla M-D (f_1, f_2, f_3)':>25} {'η_tabla':>8} {'memo f_m filas 2–3':>18} {'η_memo':>7} {'P_grupo [kN] Brown / tabla / memo':>34}")
    for s_over_D in (2.0, 3.0, 4.0, 5.0, 6.0):
        b = pile_group_efficiency_lateral(s_over_D, rows=ROWS)
        fb = (b.p_multiplier_leading, b.p_multiplier_first_trailing, b.p_multiplier_second_trailing)
        ft = tuple(p_multiplier(i + 1) for i in range(ROWS))
        eta_t = sum(ft) / ROWS
        memo = render_pile_group_memo(PileGroupLateralInput(ROWS, COLS, D, s_over_D * D, P1))
        print(f"  {s_over_D:4.1f} {str(tuple(round(x, 2) for x in fb)):>26} {b.global_efficiency:8.3f} {str(ft):>25} {eta_t:8.3f} {memo.fm_per_row[1]:18.3f} {memo.efficiency:7.3f} "
              f"{b.global_efficiency * ROWS * COLS * P1:8.0f} / {eta_t * ROWS * COLS * P1:6.0f} / {memo.P_group_kN:6.0f}")
    memo3 = render_pile_group_memo(PileGroupLateralInput(ROWS, COLS, D, 3 * D, P1))
    print("\nMemoria handcalcs para s/D = 3 (primeras líneas):")
    for line in memo3.memo_text.splitlines()[14:22]:
        print("   ", line)
    print("\nLectura: Brown (1988) es el único de los tres que depende de la separación y coincide con los p-multiplicadores que piden las guías (FHWA, AASHTO) para 3 ≤ s/D ≤ 5. "
          "La tabla de `mokwa_duncan` es fija por fila y la fórmula de la memoria satura a 1 desde s/D = 1: la memoria documenta el procedimiento, pero su número no reduce la capacidad del grupo. "
          "Para proyecto, usar `pile_group_efficiency_lateral` y revisar la memoria a mano.")


if __name__ == "__main__":
    main()
