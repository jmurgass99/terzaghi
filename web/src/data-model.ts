export interface SemanticStratum {
  id: string;
  thicknessM: number;
  vsMps: number;
  densityKgM3: number;
  dampingRatio: number;
  pUltKnM: number;
  kPyKnM3: number;
}

export interface SoilColumnMapping {
  stratumToSublayers: Map<string, number[]>;
  sublayerToStratum: Map<number, string>;
  depthToPySprings: Map<string, number[]>;
}

export interface Sublayer1D {
  index: number;
  stratumId: string;
  zMidM: number;
  dzM: number;
  vsMps: number;
  densityKgM3: number;
  dampingRatio: number;
  impedanceRatioToBedrock: number;
  pySecantKnM2: number;
  lateralDeflectionMm: number;
}

export interface TerzaghiColumnResult {
  sublayers: Sublayer1D[];
  mapping: SoilColumnMapping;
  freqsHz: number[];
  transferAmp: number[];
  peakAmp: number;
  f0Hz: number;
}
