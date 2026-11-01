import type { TerzaghiColumnResult } from "../data-model.ts";

export function renderTransferFunctionChart(canvas: HTMLCanvasElement, res: TerzaghiColumnResult): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = (canvas.width = canvas.clientWidth || 360);
  const h = (canvas.height = canvas.clientHeight || 205);
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "rgba(148,163,184,0.25)";
  ctx.strokeRect(36, 16, w - 52, h - 38);

  const maxF = Math.max(...res.freqsHz, 1);
  const maxA = Math.max(...res.transferAmp, 2);

  ctx.strokeStyle = "#10b981";
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  res.freqsHz.forEach((f, idx) => {
    const x = 36 + (f / maxF) * (w - 52);
    const y = h - 22 - (res.transferAmp[idx] / maxA) * (h - 42);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "11px Inter, sans-serif";
  ctx.fillText(`|H(f)| Kramer SH 1D — Pico = ${res.peakAmp.toFixed(2)}x @ ${res.f0Hz.toFixed(2)} Hz`, 42, 30);
}

export function renderPyDeflectionChart(canvas: HTMLCanvasElement, res: TerzaghiColumnResult): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = (canvas.width = canvas.clientWidth || 360);
  const h = (canvas.height = canvas.clientHeight || 205);
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "rgba(148,163,184,0.25)";
  ctx.strokeRect(36, 16, w - 52, h - 38);

  const maxZ = Math.max(...res.sublayers.map((s) => s.zMidM + 0.5 * s.dzM), 1);
  const maxY = Math.max(...res.sublayers.map((s) => s.lateralDeflectionMm), 0.1);

  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  res.sublayers.forEach((s, idx) => {
    const x = 36 + (s.lateralDeflectionMm / maxY) * (w - 56);
    const y = 16 + (s.zMidM / maxZ) * (h - 38);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "11px Inter, sans-serif";
  ctx.fillText(`Deflexión lateral pilote y(z) (máx = ${maxY.toFixed(1)} mm)`, 42, h - 8);
}
