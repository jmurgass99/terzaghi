import * as THREE from "three";
import type { TerzaghiColumnResult } from "../data-model.ts";

export function createTerzaghiViewer3D(container: HTMLElement): {
  update: (res: TerzaghiColumnResult) => void;
} {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x070b11);

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 250);
  camera.position.set(14, 2, 18);
  camera.lookAt(0, -6, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  container.appendChild(renderer.domElement);

  const ambient = new THREE.AmbientLight(0xffffff, 0.7);
  const dir = new THREE.DirectionalLight(0xffffff, 0.9);
  dir.position.set(10, 15, 12);
  scene.add(ambient, dir);

  const group = new THREE.Group();
  scene.add(group);

  const resize = () => {
    const w = container.clientWidth || 640;
    const h = container.clientHeight || 480;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  };
  window.addEventListener("resize", resize);
  setTimeout(resize, 0);

  let phase = 0;
  const animate = () => {
    requestAnimationFrame(animate);
    phase += 0.04;
    group.children.forEach((child) => {
      if (child.userData.isSoilBlock) {
        const amp = child.userData.ampFactor || 0.2;
        child.position.x = Math.sin(phase - child.position.y * 0.35) * amp;
      }
    });
    renderer.render(scene, camera);
  };
  animate();

  return {
    update(res: TerzaghiColumnResult) {
      while (group.children.length > 0) group.remove(group.children[0]);

      for (const s of res.sublayers) {
        const ratio = Math.min(1, s.vsMps / 450);
        const color = new THREE.Color().setHSL(0.32 * ratio + 0.08, 0.72, 0.45);
        const geo = new THREE.BoxGeometry(4.5, s.dzM * 0.92, 4.5);
        const mat = new THREE.MeshStandardMaterial({ color, transparent: true, opacity: 0.72 });
        const block = new THREE.Mesh(geo, mat);
        block.position.set(0, -s.zMidM, 0);
        block.userData = { isSoilBlock: true, ampFactor: 0.35 * (1 - ratio * 0.6) };
        group.add(block);

        // Segmento de pilote deformado lateralmente
        const pileGeo = new THREE.CylinderGeometry(0.38, 0.38, s.dzM * 0.96, 16);
        const pileMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8 });
        const pileSeg = new THREE.Mesh(pileGeo, pileMat);
        pileSeg.position.set(3.4 + s.lateralDeflectionMm * 0.03, -s.zMidM, 0);
        group.add(pileSeg);
      }
    },
  };
}
