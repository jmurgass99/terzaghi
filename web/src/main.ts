import van from "vanjs-core";
import type { SemanticStratum } from "./data-model.ts";
import { solveSoilColumnWasm } from "./solver/wasmSolver.ts";
import { fetchTerzaghiHealthApi } from "./solver/apiClient.ts";
import { createTerzaghiViewer3D } from "./viewer/getViewer3D.ts";
import { renderTransferFunctionChart, renderPyDeflectionChart } from "./ui/getWaveCharts.ts";

const { div, h2, h3, label, input, span, strong, canvas, button } = van.tags;

const vsUpper = van.state(175);
const bedrockVs = van.state(1100);
const divisions = van.state(5);
const pileForceKn = van.state(240);

const peakAmpText = van.state("0.00x");
const f0Text = van.state("0.00 Hz");
const maxYText = van.state("0.0 mm");
const sublayersText = van.state("10");
const apiStatus = van.state("Modo WASM local");

const viewerWrap = div({ class: "viewer-wrap" });
const tfCanvas = canvas({ class: "chart" });
const pyCanvas = canvas({ class: "chart" });
const viewer = createTerzaghiViewer3D(viewerWrap);

async function recompute() {
  const strata: SemanticStratum[] = [
    {
      id: "SAND-UPPER",
      thicknessM: 6.0,
      vsMps: vsUpper.val,
      densityKgM3: 1850,
      dampingRatio: 0.05,
      pUltKnM: 160,
      kPyKnM3: 11000,
    },
    {
      id: "CLAY-LOWER",
      thicknessM: 10.0,
      vsMps: 310,
      densityKgM3: 2020,
      dampingRatio: 0.04,
      pUltKnM: 280,
      kPyKnM3: 18500,
    },
  ];
  const res = await solveSoilColumnWasm(strata, divisions.val, bedrockVs.val, pileForceKn.val);
  peakAmpText.val = `${res.peakAmp.toFixed(2)}x`;
  f0Text.val = `${res.f0Hz.toFixed(2)} Hz`;
  const maxY = Math.max(...res.sublayers.map((s) => s.lateralDeflectionMm), 0);
  maxYText.val = `${maxY.toFixed(1)} mm`;
  sublayersText.val = `${res.sublayers.length}`;
  viewer.update(res);
  renderTransferFunctionChart(tfCanvas, res);
  renderPyDeflectionChart(pyCanvas, res);
}

van.derive(() => {
  void recompute();
});

const app = div(
  { class: "layout" },
  div(
    { class: "panel" },
    h2("Terzaghi SH 1D & p-y"),
    div(
      { class: "control-row" },
      label(() => `Velocidad de corte estrato 1 Vs = ${vsUpper.val} m/s`),
      input({
        type: "range",
        min: "100",
        max: "350",
        step: "5",
        value: vsUpper,
        oninput: (e: Event) => (vsUpper.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Vs Roca Basal = ${bedrockVs.val} m/s`),
      input({
        type: "range",
        min: "600",
        max: "2000",
        step: "50",
        value: bedrockVs,
        oninput: (e: Event) => (bedrockVs.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Subcapas por estrato (SoilColumnMapping) = ${divisions.val}`),
      input({
        type: "range",
        min: "2",
        max: "12",
        step: "1",
        value: divisions,
        oninput: (e: Event) => (divisions.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Carga lateral en cabeza H_0 = ${pileForceKn.val} kN`),
      input({
        type: "range",
        min: "50",
        max: "600",
        step: "10",
        value: pileForceKn,
        oninput: (e: Event) => (pileForceKn.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "kpi-grid" },
      div({ class: "kpi" }, span("Amplificación |H|_max"), strong(peakAmpText)),
      div({ class: "kpi" }, span("Frecuencia f_0"), strong(f0Text)),
      div({ class: "kpi" }, span("Deflexión pilote y_0"), strong(maxYText)),
      div({ class: "kpi" }, span("Subcapas activas"), strong(sublayersText))
    ),
    button(
      {
        onclick: async () => {
          const ok = await fetchTerzaghiHealthApi("http://localhost:8000");
          apiStatus.val = ok ? "FastAPI sincronizado OK" : "FastAPI offline (usando WASM local)";
        },
      },
      "Sincronizar con FastAPI"
    ),
    span({ style: "font-size:0.75rem;color:#94a3b8" }, apiStatus)
  ),
  viewerWrap,
  div(
    { class: "panel" },
    h3("Función de Transferencia |H(f)|"),
    tfCanvas,
    h3("Perfil de Deflexión Lateral p-y"),
    pyCanvas
  )
);

document.getElementById("app")?.appendChild(app);
