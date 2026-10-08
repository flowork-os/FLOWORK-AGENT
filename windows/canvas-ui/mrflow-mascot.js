// =============================================================================
// MR. FLOW — STANDALONE 3D SOVEREIGN MASCOT ENGINE
// 100% Procedural Geometry & Real-Time Audio-Reactive Lip Sync
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================

import * as THREE from '/canvas/vendor/three/three.module.js';
import { OrbitControls } from '/canvas/vendor/three/addons/controls/OrbitControls.js';

let scene, camera, renderer, controls;
let faceRoot = null;
let proceduralMouth = null;
let mouthLight = null;
let holoRings = [];
let particles = null;
let animationFrameId = null;
let isRunning = false;
let isInitialized = false;

let audioCtx = null;
let analyser = null;
let audioSource = null;
let smoothVocalEnergy = 0.0;
const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };

export function initMrFlowMascot(canvas, stageWrap, audioEl) {
  if (!canvas || !stageWrap) return null;
  if (isInitialized && renderer) {
    startMascot();
    return { start: startMascot, stop: stopMascot, getEnergy: () => smoothVocalEnergy, getAnalyser: () => analyser, getAudioCtx: () => audioCtx };
  }

  const width = stageWrap.clientWidth || 700;
  const height = stageWrap.clientHeight || 550;

  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'default'
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
  } catch (err) {
    console.warn('[MR. FLOW Mascot] WebGL failed:', err);
    return null;
  }

  isInitialized = true;
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(34, width / height, 0.1, 100);
  camera.position.set(0, 0.04, 3.2);

  try {
    controls = new OrbitControls(camera, canvas);
    controls.enableZoom = false;
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.rotateSpeed = 0.6;
    controls.minPolarAngle = Math.PI / 2.6;
    controls.maxPolarAngle = Math.PI / 1.7;
    controls.minAzimuthAngle = -Math.PI / 3.5;
    controls.maxAzimuthAngle = Math.PI / 3.5;
  } catch (err) {
    console.warn('[MR. FLOW Mascot] OrbitControls warning:', err);
    controls = null;
  }

  // Lighting (Cybernetic Electric Cyan / Ultraviolet Rim)
  const ambientLight = new THREE.AmbientLight(0x071526, 3.2);
  scene.add(ambientLight);

  const keyLight = new THREE.DirectionalLight(0x00e5ff, 4.2);
  keyLight.position.set(3.0, 3.5, 3.5);
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x7f00ff, 3.8);
  rimLight.position.set(-3.2, -1.2, -2.8);
  scene.add(rimLight);

  const topSpot = new THREE.PointLight(0x38bdf8, 2.8, 12);
  topSpot.position.set(0, 3.5, 2.0);
  scene.add(topSpot);

  mouthLight = new THREE.PointLight(0x00f2fe, 1.5, 6);
  mouthLight.position.set(0, -0.22, 1.0);
  scene.add(mouthLight);

  // Holographic Concentric Rings
  createHoloRings();

  // Ambient Particles Field
  createParticles();

  // Procedural 3D Mesh
  createProceduralAvatar();

  // Mouse Gaze
  window.addEventListener('mousemove', (e) => {
    mouse.targetX = (e.clientX / window.innerHeight) * 2 - 1;
    mouse.targetY = -(e.clientY / window.innerHeight) * 2 + 1;
  });

  // Resize Observer
  const ro = new ResizeObserver(() => {
    if (!stageWrap || !renderer) return;
    const w = stageWrap.clientWidth || 700;
    const h = stageWrap.clientHeight || 550;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  });
  ro.observe(stageWrap);

  // Audio Analyzer Hook
  if (audioEl) {
    attachAudioAnalyzer(audioEl);
  }

  startMascot();
  return { start: startMascot, stop: stopMascot, getEnergy: () => smoothVocalEnergy, getAnalyser: () => analyser, getAudioCtx: () => audioCtx };
}

function createHoloRings() {
  const ringGeom = new THREE.TorusGeometry(0.72, 0.006, 16, 120);
  const ringMat1 = new THREE.MeshBasicMaterial({ color: 0x00e5ff, transparent: true, opacity: 0.5 });
  const ringMat2 = new THREE.MeshBasicMaterial({ color: 0x7f00ff, transparent: true, opacity: 0.4 });
  const ringMat3 = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.3 });

  const ring1 = new THREE.Mesh(ringGeom, ringMat1);
  ring1.userData = { speedZ: 0.005, speedX: 0.003, baseScale: 0.95 };
  scene.add(ring1);
  holoRings.push(ring1);

  const ring2 = new THREE.Mesh(ringGeom, ringMat2);
  ring2.userData = { speedZ: -0.007, speedX: -0.004, baseScale: 1.10 };
  ring2.rotation.x = Math.PI / 3;
  scene.add(ring2);
  holoRings.push(ring2);

  const ring3 = new THREE.Mesh(ringGeom, ringMat3);
  ring3.userData = { speedZ: 0.004, speedX: -0.005, baseScale: 1.25 };
  ring3.rotation.y = Math.PI / 4;
  scene.add(ring3);
  holoRings.push(ring3);
}

function createParticles() {
  const count = 260;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);

  for (let i = 0; i < count * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 8.5;
    positions[i + 1] = (Math.random() - 0.5) * 6.0;
    positions[i + 2] = (Math.random() - 0.5) * 4.0;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({
    color: 0x00f2fe,
    size: 0.024,
    transparent: true,
    opacity: 0.55
  });

  particles = new THREE.Points(geometry, material);
  scene.add(particles);
}

function createProceduralAvatar() {
  if (faceRoot) return;
  const group = new THREE.Group();

  // 1. Central Core: Metallic Obsidian Sphere
  const coreGeom = new THREE.SphereGeometry(0.52, 36, 28);
  const coreMat = new THREE.MeshStandardMaterial({
    color: 0x051833,
    emissive: 0x00172e,
    emissiveIntensity: 0.8,
    metalness: 0.88,
    roughness: 0.18
  });
  group.add(new THREE.Mesh(coreGeom, coreMat));

  // 2. Holographic Geometric Lattice
  const latticeGeom = new THREE.IcosahedronGeometry(0.536, 2);
  const latticeMat = new THREE.MeshBasicMaterial({
    color: 0x00e5ff,
    wireframe: true,
    transparent: true,
    opacity: 0.22
  });
  group.add(new THREE.Mesh(latticeGeom, latticeMat));

  // 3. Cybernetic Ocular Visor
  const visorGeom = new THREE.BoxGeometry(0.48, 0.12, 0.18);
  const visorMat = new THREE.MeshStandardMaterial({
    color: 0x00e5ff,
    emissive: 0x00f2fe,
    emissiveIntensity: 2.4,
    metalness: 0.9,
    roughness: 0.1
  });
  const visor = new THREE.Mesh(visorGeom, visorMat);
  visor.position.set(0, 0.06, 0.44);
  group.add(visor);

  // Visor Central Pupil
  const pupilGeom = new THREE.SphereGeometry(0.045, 16, 16);
  const pupilMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const pupil = new THREE.Mesh(pupilGeom, pupilMat);
  pupil.position.set(0, 0.06, 0.52);
  group.add(pupil);

  // 4. Ear Pods & Glowing Rings
  const podGeom = new THREE.CylinderGeometry(0.14, 0.14, 0.12, 24);
  const podMat = new THREE.MeshStandardMaterial({ color: 0x0b2240, metalness: 0.85, roughness: 0.2 });
  const ringGeom = new THREE.TorusGeometry(0.15, 0.012, 16, 32);
  const ringMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff, transparent: true, opacity: 0.85 });

  const leftPod = new THREE.Mesh(podGeom, podMat);
  leftPod.rotation.z = Math.PI / 2;
  leftPod.position.set(-0.53, 0.02, 0);
  const leftRing = new THREE.Mesh(ringGeom, ringMat);
  leftRing.rotation.y = Math.PI / 2;
  leftRing.position.set(-0.58, 0.02, 0);
  group.add(leftPod);
  group.add(leftRing);

  const rightPod = new THREE.Mesh(podGeom, podMat);
  rightPod.rotation.z = Math.PI / 2;
  rightPod.position.set(0.53, 0.02, 0);
  const rightRing = new THREE.Mesh(ringGeom, ringMat);
  rightRing.rotation.y = Math.PI / 2;
  rightRing.position.set(0.58, 0.02, 0);
  group.add(rightPod);
  group.add(rightRing);

  // 5. Talking Mouth Equalizer Bars (7 Audio-Reactive Bars)
  const mouthGroup = new THREE.Group();
  const barCount = 7;
  const barWidth = 0.035;
  const barGap = 0.014;
  const totalW = barCount * barWidth + (barCount - 1) * barGap;

  for (let i = 0; i < barCount; i++) {
    const barGeom = new THREE.BoxGeometry(barWidth, 0.07, 0.04);
    const barMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x00f2fe,
      emissiveIntensity: 2.0
    });
    const bar = new THREE.Mesh(barGeom, barMat);
    bar.position.x = -totalW / 2 + i * (barWidth + barGap) + barWidth / 2;
    bar.userData = { index: i, baseH: 0.07 };
    mouthGroup.add(bar);
  }
  mouthGroup.position.set(0, -0.17, 0.46);
  group.add(mouthGroup);
  proceduralMouth = mouthGroup;

  // 6. Magnetic Levitation Collar Halo
  const collarGeom = new THREE.TorusGeometry(0.30, 0.014, 16, 48);
  const collarMat = new THREE.MeshStandardMaterial({
    color: 0x00e5ff,
    emissive: 0x00f2fe,
    emissiveIntensity: 1.2,
    metalness: 0.8
  });
  const collar = new THREE.Mesh(collarGeom, collarMat);
  collar.rotation.x = Math.PI / 2;
  collar.position.set(0, -0.44, 0);
  group.add(collar);

  group.position.set(0, 0.08, 0);
  group.userData = { basePosY: 0.08, baseRotX: 0, baseRotY: 0 };

  scene.add(group);
  faceRoot = group;
}

export function attachAudioAnalyzer(audioEl) {
  if (!audioEl) return;
  try {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContextClass();
    }
    if (!analyser) {
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
    }
    if (!audioSource) {
      audioSource = audioCtx.createMediaElementSource(audioEl);
      audioSource.connect(analyser);
      analyser.connect(audioCtx.destination);
    }
  } catch (err) {
    console.warn('[MR. FLOW Mascot] AudioContext setup notice:', err.message);
  }
}

function updateAudioEnergy() {
  if (!analyser) {
    smoothVocalEnergy = 0.0;
    return;
  }
  const dataArray = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteFrequencyData(dataArray);

  let sum = 0;
  const minBin = 2;
  const maxBin = Math.min(48, dataArray.length);
  for (let i = minBin; i < maxBin; i++) {
    sum += dataArray[i];
  }
  const avg = sum / (maxBin - minBin);
  const targetEnergy = Math.min(1.0, avg / 120.0);
  smoothVocalEnergy += (targetEnergy - smoothVocalEnergy) * 0.35;
}

const clock = new THREE.Clock();

function render() {
  if (!isRunning) return;
  animationFrameId = requestAnimationFrame(render);
  const elapsedTime = clock.getElapsedTime();

  mouse.x += (mouse.targetX - mouse.x) * 0.05;
  mouse.y += (mouse.targetY - mouse.y) * 0.05;

  if (controls) controls.update();
  updateAudioEnergy();

  if (faceRoot) {
    const basePosY = faceRoot.userData.basePosY || 0;
    faceRoot.position.y = basePosY + Math.sin(elapsedTime * 1.5) * 0.035 + smoothVocalEnergy * 0.015;
    faceRoot.rotation.x = (faceRoot.userData.baseRotX || 0) + Math.sin(elapsedTime * 1.8) * 0.025 + smoothVocalEnergy * 0.06;
    const baseRotY = faceRoot.userData.baseRotY || 0;
    faceRoot.rotation.y = baseRotY + Math.sin(elapsedTime * 0.6) * 0.08 + mouse.x * 0.2;
    faceRoot.rotation.z = Math.sin(elapsedTime * 1.2) * 0.018;

    if (proceduralMouth) {
      const bars = proceduralMouth.children;
      for (let i = 0; i < bars.length; i++) {
        const bar = bars[i];
        const harmonic = Math.sin(elapsedTime * 15 + i) * 0.5 + 0.5;
        bar.scale.y = 1.0 + smoothVocalEnergy * 3.5 * (0.6 + harmonic * 0.8);
      }
    }

    if (mouthLight) {
      mouthLight.intensity = 1.0 + smoothVocalEnergy * 6.0;
    }
  }

  for (let i = 0; i < holoRings.length; i++) {
    const ring = holoRings[i];
    ring.rotation.z += ring.userData.speedZ;
    ring.rotation.x += ring.userData.speedX;
    ring.scale.setScalar(ring.userData.baseScale * (1.0 + smoothVocalEnergy * 0.25));
  }

  if (particles) {
    particles.rotation.y = elapsedTime * 0.035;
  }

  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
}

export function startMascot() {
  if (isRunning) return;
  isRunning = true;
  if (audioCtx && audioCtx.state === 'suspended') {
    try { audioCtx.resume(); } catch (_) {}
  }
  render();
}

export function stopMascot() {
  isRunning = false;
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
  if (audioCtx && audioCtx.state === 'running') {
    try { audioCtx.suspend(); } catch (_) {}
  }
}

export function destroyMascot() {
  stopMascot();
  if (renderer) {
    try { renderer.dispose(); } catch (_) {}
  }
  faceRoot = null;
  proceduralMouth = null;
  holoRings = [];
  particles = null;
  isInitialized = false;
}
