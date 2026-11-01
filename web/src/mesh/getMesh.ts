import type { SemanticStratum, SoilColumnMapping, Sublayer1D } from "../data-model.ts";

export function getSoilColumnMesh(
  strata: SemanticStratum[],
  divisionsPerStratum: number
): { sublayers: Sublayer1D[]; mapping: SoilColumnMapping } {
  const div = Math.max(1, Math.floor(divisionsPerStratum));
  const stratumToSublayers = new Map<string, number[]>();
  const sublayerToStratum = new Map<number, string>();
  const depthToPySprings = new Map<string, number[]>();
  const sublayers: Sublayer1D[] = [];

  let zCursor = 0;
  for (const st of strata) {
    const dz = st.thicknessM / div;
    const indices: number[] = [];
    for (let i = 0; i < div; i++) {
      const idx = sublayers.length;
      const zMid = zCursor + 0.5 * dz;
      sublayers.push({
        index: idx,
        stratumId: st.id,
        zMidM: zMid,
        dzM: dz,
        vsMps: st.vsMps,
        densityKgM3: st.densityKgM3,
        dampingRatio: st.dampingRatio,
        impedanceRatioToBedrock: 1.0,
        pySecantKnM2: 0.0,
        lateralDeflectionMm: 0.0,
      });
      indices.push(idx);
      sublayerToStratum.set(idx, st.id);
      zCursor += dz;
    }
    stratumToSublayers.set(st.id, indices);
  }

  depthToPySprings.set(
    "PILE-LAT-1",
    sublayers.map((s) => s.index)
  );

  return {
    sublayers,
    mapping: { stratumToSublayers, sublayerToStratum, depthToPySprings },
  };
}
