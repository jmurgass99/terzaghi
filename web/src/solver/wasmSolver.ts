import type { SemanticStratum, TerzaghiColumnResult } from "../data-model.ts";
import { getSoilColumnMesh } from "../mesh/getMesh.ts";

// Binario WebAssembly compilado desde waveKernel.cpp
const WASM_B64 =
  "AGFzbQEAAAABEQJgBHx8fHwBfGAEfHx8fAF8AwMCAAEFAwEAAQcmAg5pbXBlZGFuY2VSYXRpbwAAEXB5U2VjYW50U3RpZmZuZXNzAAEKJgINACAAIAGiIAIgA6KjCxYAIAAgAaIgAqIgACABIAKiIAOioKML";

function decodeBase64(b64: string): Uint8Array {
  if (typeof Buffer !== "undefined") {
    return new Uint8Array(Buffer.from(b64, "base64"));
  }
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export interface WaveWasmExports {
  impedanceRatio: (rho1: number, vs1: number, rho2: number, vs2: number) => number;
  pySecantStiffness: (pUlt: number, kIni: number, z: number, y: number) => number;
}

let cachedExports: WaveWasmExports | null = null;

export async function initWaveWasm(): Promise<WaveWasmExports> {
  if (cachedExports) return cachedExports;
  const { instance } = await WebAssembly.instantiate(decodeBase64(WASM_B64));
  cachedExports = instance.exports as unknown as WaveWasmExports;
  return cachedExports;
}

export async function solveSoilColumnWasm(
  strata: SemanticStratum[],
  divisionsPerStratum: number,
  bedrockVs: number,
  pileHeadForceKn: number
): Promise<TerzaghiColumnResult> {
  const wasm = await initWaveWasm();
  const { sublayers, mapping } = getSoilColumnMesh(strata, divisionsPerStratum);
  const bedrockRho = 2450.0;
  const totalDepth = sublayers.reduce((acc, s) => acc + s.dzM, 0);

  for (const s of sublayers) {
    const st = strata.find((x) => x.id === s.stratumId) ?? strata[0];
    s.impedanceRatioToBedrock = wasm.impedanceRatio(s.densityKgM3, s.vsMps, bedrockRho, bedrockVs);
    const decay = Math.exp((-2.4 * s.zMidM) / Math.max(totalDepth, 1));
    const yEstM = Math.max(0.0005, (pileHeadForceKn / 12000) * decay);
    s.pySecantKnM2 = wasm.pySecantStiffness(st.pUltKnM, st.kPyKnM3, s.zMidM, yEstM);
    s.lateralDeflectionMm = (pileHeadForceKn * decay * 1000) / Math.max(s.pySecantKnM2 * s.dzM + 1500, 100);
  }

  // Función de transferencia multicapa |H(f)|
  const freqsHz: number[] = [];
  const transferAmp: number[] = [];
  let peakAmp = 1.0;
  let f0Hz = 1.0;

  for (let i = 1; i <= 80; i++) {
    const f = i * 0.25;
    const omega = 2 * Math.PI * f;
    let hMag = 1.0;
    for (const s of sublayers) {
      const kh = (omega * s.dzM) / s.vsMps;
      const denom = Math.sqrt(Math.pow(Math.cos(kh), 2) + Math.pow(s.dampingRatio * kh, 2));
      hMag *= 1.0 / Math.max(denom, 0.08);
    }
    // Ajuste por contraste de impedancia en roca basal
    const alphaBedrock = sublayers[sublayers.length - 1]?.impedanceRatioToBedrock ?? 0.3;
    const amp = Math.min(12.0, hMag / (1 + 0.35 * alphaBedrock));
    freqsHz.push(f);
    transferAmp.push(amp);
    if (amp > peakAmp) {
      peakAmp = amp;
      f0Hz = f;
    }
  }

  return { sublayers, mapping, freqsHz, transferAmp, peakAmp, f0Hz };
}
