import assert from "node:assert/strict";
import { solveSoilColumnWasm } from "../solver/wasmSolver.ts";

const strata = [
  { id: "SAND-UPPER", thicknessM: 6.0, vsMps: 180, densityKgM3: 1850, dampingRatio: 0.05, pUltKnM: 160, kPyKnM3: 11000 },
  { id: "CLAY-LOWER", thicknessM: 10.0, vsMps: 310, densityKgM3: 2020, dampingRatio: 0.04, pUltKnM: 280, kPyKnM3: 18500 },
];

const res2 = await solveSoilColumnWasm(strata, 2, 1100, 240);
const res6 = await solveSoilColumnWasm(strata, 6, 1100, 240);

assert.equal(res2.sublayers.length, 4);
assert.equal(res6.sublayers.length, 12);
assert.equal(res6.mapping.stratumToSublayers.get("SAND-UPPER")?.length, 6);
assert.ok(res6.peakAmp > 1.5, "Site amplification peak must exceed 1.5x");
assert.ok(res6.sublayers[0].pySecantKnM2 > 0, "p-y secant stiffness must be positive");
console.log(
  `Terzaghi WASM test OK: |H|_max=${res6.peakAmp.toFixed(2)}x @ ${res6.f0Hz.toFixed(2)} Hz, k_py0=${res6.sublayers[0].pySecantKnM2.toFixed(1)} kN/m2`
);
