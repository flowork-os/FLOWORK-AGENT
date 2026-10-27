/**
 * ============================================================================
 * ⚡ FLOWORK OS — MR. FLOW SCI-FI HOLOGRAPHIC LABORATORY (SOLO MODE ENGINE)
 * Module: mrflow_solo_lab.js
 * 
 * Strict Architecture Guarantee:
 * - 100% White-Labeled: Sovereign Flowork OS branding (Zero third-party trademarks).
 * - 100% Isolated from 3d_solo.js (Team/Group mode remains untouched).
 * - Clean Cyber Holographic Lab for Solo Agent (Mr. Flow).
 * - Zero Particle Noise / Snow: Removed for optimal visual ergonomics and focus.
 * - Arc Reactor Floor dais with rotating tick rings & neon runes.
 * - 3D Gyroscopic Arc Reactor Rings rotating on X, Y, Z axes around Mr. Flow.
 * - Floating Curved Holographic HUD Screens:
 *     * Screen 1: Live Audio & Neural Core Equalizer (32 dynamic dancing bars).
 *     * Screen 2: Real-time Sovereign Diagnostics & Telemetry Stream (hex code, metrics).
 *     * Screen 3: 3D Holographic Wireframe Core Matrix with laser sweep.
 * - Mr. Flow Levitation / Hover Physics with ion thruster glow & cyber gestures.
 * 
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 * ============================================================================
 */

import * as THREE from '/canvas/vendor/three/three.module.js';

export class MrFlowSoloLab {
  constructor(scene, customThree) {
    this.THREE = customThree || THREE || window.THREE;
    this.scene = scene;
    this.group = new this.THREE.Group();
    this.group.name = 'MrFlowSoloLab';
    this.group.visible = false;

    // Component References
    this.floorGroup = null;
    this.gyroGroup = null;
    this.screensGroup = null;
    this.lightsGroup = null;
    this.coreMatrix = null;
    this.laserPlane = null;
    this.thrusterPlumes = [];

    // Canvas Textures & State
    this.eqCanvas = null;
    this.eqCtx = null;
    this.eqTexture = null;
    this.eqBars = new Float32Array(32);
    this.eqPeakBars = new Float32Array(32);

    this.telemetryCanvas = null;
    this.telemetryCtx = null;
    this.telemetryTexture = null;
    this.hexLines = [];
    this.lastCanvasUpdate = 0;

    // Active Agent Reference
    this.activeAgent = null;
    this.originalStandbyPos = null;
    this.originalStandbyRotY = 0;

    // Build the Laboratory (Clean: Zero Snow / Flying Particles)
    this.init();
    if (this.scene) {
      this.scene.add(this.group);
    }
  }

  init() {
    this.buildArcReactorFloor();
    this.buildGyroscopicRings();
    this.buildCurvedHoloScreens();
    this.buildCoreMatrix();
    this.buildHoloLighting();
    this.buildThrusterPlumes();
    this.initTelemetryData();
  }

  // ==========================================================================
  // 1. ARC REACTOR HOLOGRAPHIC FLOOR DAIS
  // ==========================================================================
  buildArcReactorFloor() {
    this.floorGroup = new this.THREE.Group();
    this.floorGroup.name = 'MrFlowFloorDais';

    // A. Dark Cyber Platform Base
    const baseGeo = new this.THREE.CylinderGeometry(4.2, 4.4, 0.04, 48);
    const baseMat = new this.THREE.MeshStandardMaterial({
      color: 0x050a14,
      roughness: 0.25,
      metalness: 0.92
    });
    const baseMesh = new this.THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.y = -0.02;
    this.floorGroup.add(baseMesh);

    // B. Outer Bezel Glow Ring (Cyan)
    const outerRingGeo = new this.THREE.RingGeometry(3.92, 4.02, 64);
    const outerRingMat = new this.THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      side: this.THREE.DoubleSide,
      transparent: true,
      opacity: 0.75,
      blending: this.THREE.AdditiveBlending
    });
    const outerRing = new this.THREE.Mesh(outerRingGeo, outerRingMat);
    outerRing.rotation.x = -Math.PI / 2;
    outerRing.position.y = 0.005;
    this.floorGroup.add(outerRing);

    // C. Segmented Rotating Tick Marks Ring
    this.tickRingGroup = new this.THREE.Group();
    this.tickRingGroup.position.y = 0.008;
    const tickCount = 48;
    const tickMat = new this.THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.85,
      blending: this.THREE.AdditiveBlending
    });
    for (let i = 0; i < tickCount; i++) {
      const angle = (i / tickCount) * Math.PI * 2;
      const isMajor = (i % 4 === 0);
      const len = isMajor ? 0.28 : 0.14;
      const w = isMajor ? 0.03 : 0.015;
      const tickGeo = new this.THREE.PlaneGeometry(w, len);
      const tick = new this.THREE.Mesh(tickGeo, tickMat);
      const r = 3.70;
      tick.position.set(Math.cos(angle) * r, 0, Math.sin(angle) * r);
      tick.rotation.x = -Math.PI / 2;
      tick.rotation.z = -angle;
      this.tickRingGroup.add(tick);
    }
    this.floorGroup.add(this.tickRingGroup);

    // D. Mid Neon Violet Circuit Ring
    const midRingGeo = new this.THREE.RingGeometry(2.55, 2.62, 48);
    const midRingMat = new this.THREE.MeshBasicMaterial({
      color: 0x8b5cf6,
      side: this.THREE.DoubleSide,
      transparent: true,
      opacity: 0.8,
      blending: this.THREE.AdditiveBlending
    });
    this.midRing = new this.THREE.Mesh(midRingGeo, midRingMat);
    this.midRing.rotation.x = -Math.PI / 2;
    this.midRing.position.y = 0.010;
    this.floorGroup.add(this.midRing);

    // E. Inner Pulse Ring (Cyan)
    const innerRingGeo = new this.THREE.RingGeometry(1.42, 1.48, 48);
    const innerRingMat = new this.THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      side: this.THREE.DoubleSide,
      transparent: true,
      opacity: 0.9,
      blending: this.THREE.AdditiveBlending
    });
    this.innerRing = new this.THREE.Mesh(innerRingGeo, innerRingMat);
    this.innerRing.rotation.x = -Math.PI / 2;
    this.innerRing.position.y = 0.012;
    this.floorGroup.add(this.innerRing);

    // F. Center Arc Reactor Aperture Core
    const coreApertureCanvas = document.createElement('canvas');
    coreApertureCanvas.width = 512;
    coreApertureCanvas.height = 512;
    const cctx = coreApertureCanvas.getContext('2d');
    
    // Draw Arc Reactor Aperture Texture
    const cx = 256, cy = 256;
    const grad = cctx.createRadialGradient(cx, cy, 20, cx, cy, 250);
    grad.addColorStop(0, 'rgba(0, 240, 255, 0.95)');
    grad.addColorStop(0.3, 'rgba(0, 168, 255, 0.7)');
    grad.addColorStop(0.7, 'rgba(112, 0, 255, 0.4)');
    grad.addColorStop(1, 'rgba(5, 10, 20, 0.0)');
    cctx.fillStyle = grad;
    cctx.fillRect(0, 0, 512, 512);

    // Radiating power vanes
    cctx.strokeStyle = '#00f0ff';
    cctx.lineWidth = 4;
    for (let a = 0; a < 12; a++) {
      const ang = (a / 12) * Math.PI * 2;
      cctx.beginPath();
      cctx.moveTo(cx + Math.cos(ang) * 45, cy + Math.sin(ang) * 45);
      cctx.lineTo(cx + Math.cos(ang) * 230, cy + Math.sin(ang) * 230);
      cctx.stroke();
    }
    // Concentric coil rings
    cctx.strokeStyle = '#a855f7';
    cctx.lineWidth = 3;
    cctx.beginPath();
    cctx.arc(cx, cy, 95, 0, Math.PI * 2);
    cctx.stroke();
    cctx.beginPath();
    cctx.arc(cx, cy, 165, 0, Math.PI * 2);
    cctx.stroke();

    const coreTexture = new this.THREE.CanvasTexture(coreApertureCanvas);
    const coreDiscGeo = new this.THREE.CircleGeometry(0.92, 32);
    const coreDiscMat = new this.THREE.MeshBasicMaterial({
      map: coreTexture,
      transparent: true,
      opacity: 0.95,
      blending: this.THREE.AdditiveBlending,
      side: this.THREE.DoubleSide
    });
    this.coreDisc = new this.THREE.Mesh(coreDiscGeo, coreDiscMat);
    this.coreDisc.rotation.x = -Math.PI / 2;
    this.coreDisc.position.y = 0.015;
    this.floorGroup.add(this.coreDisc);

    // G. 8 Radiating Floor Circuit Inlays
    const lineMat = new this.THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.65,
      blending: this.THREE.AdditiveBlending
    });
    for (let i = 0; i < 8; i++) {
      const ang = (i / 8) * Math.PI * 2;
      const rayGeo = new this.THREE.PlaneGeometry(0.025, 2.8);
      const ray = new this.THREE.Mesh(rayGeo, lineMat);
      ray.position.set(Math.cos(ang) * 2.35, 0.007, Math.sin(ang) * 2.35);
      ray.rotation.x = -Math.PI / 2;
      ray.rotation.z = -ang + Math.PI / 2;
      this.floorGroup.add(ray);
    }

    this.group.add(this.floorGroup);
  }

  // ==========================================================================
  // 2. 3D GYROSCOPIC ARC REACTOR RINGS (GIMBAL AROUND MR. FLOW)
  // ==========================================================================
  buildGyroscopicRings() {
    this.gyroGroup = new this.THREE.Group();
    this.gyroGroup.name = 'MrFlowGyroscopicRings';
    this.gyroGroup.position.set(0, 1.15, 0);

    // Ring A: Inner Ring (Cyan)
    const ringAGeo = new this.THREE.TorusGeometry(1.42, 0.010, 16, 64);
    const ringAMat = new this.THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.85,
      blending: this.THREE.AdditiveBlending
    });
    this.gyroRingA = new this.THREE.Mesh(ringAGeo, ringAMat);
    this.gyroRingA.rotation.x = 0.45;
    this.gyroGroup.add(this.gyroRingA);

    // Ring B: Middle Ring (Neon Violet)
    const ringBGeo = new this.THREE.TorusGeometry(1.70, 0.011, 16, 64);
    const ringBMat = new this.THREE.MeshBasicMaterial({
      color: 0xa855f7,
      transparent: true,
      opacity: 0.80,
      blending: this.THREE.AdditiveBlending
    });
    this.gyroRingB = new this.THREE.Mesh(ringBGeo, ringBMat);
    this.gyroRingB.rotation.y = -0.55;
    this.gyroGroup.add(this.gyroRingB);

    // Ring C: Outer Ring (Electric Sky Blue)
    const ringCGeo = new this.THREE.TorusGeometry(1.98, 0.013, 16, 64);
    const ringCMat = new this.THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.70,
      blending: this.THREE.AdditiveBlending
    });
    this.gyroRingC = new this.THREE.Mesh(ringCGeo, ringCMat);
    this.gyroRingC.rotation.z = 0.35;
    this.gyroGroup.add(this.gyroRingC);

    // Orbiting Quantum Energy Satellites (Glowing Nodes)
    this.orbitalNodes = [];
    const nodeGeo = new this.THREE.SphereGeometry(0.038, 12, 12);
    const nodeMatCyan = new this.THREE.MeshBasicMaterial({ color: 0x00ffff, blending: this.THREE.AdditiveBlending });
    const nodeMatGold = new this.THREE.MeshBasicMaterial({ color: 0xfbbf24, blending: this.THREE.AdditiveBlending });
    const nodeMatPurple = new this.THREE.MeshBasicMaterial({ color: 0xc084fc, blending: this.THREE.AdditiveBlending });

    const nodesData = [
      { ring: this.gyroRingA, radius: 1.42, speed: 1.8, mat: nodeMatCyan, phase: 0 },
      { ring: this.gyroRingA, radius: 1.42, speed: 1.8, mat: nodeMatCyan, phase: Math.PI },
      { ring: this.gyroRingB, radius: 1.70, speed: -1.3, mat: nodeMatPurple, phase: 0.8 },
      { ring: this.gyroRingB, radius: 1.70, speed: -1.3, mat: nodeMatPurple, phase: 0.8 + Math.PI },
      { ring: this.gyroRingC, radius: 1.98, speed: 0.9, mat: nodeMatGold, phase: 2.1 },
      { ring: this.gyroRingC, radius: 1.98, speed: 0.9, mat: nodeMatGold, phase: 2.1 + Math.PI }
    ];

    nodesData.forEach(nd => {
      const nodeMesh = new this.THREE.Mesh(nodeGeo, nd.mat);
      nd.ring.add(nodeMesh);
      this.orbitalNodes.push({ mesh: nodeMesh, ...nd });
    });

    this.group.add(this.gyroGroup);
  }

  // ==========================================================================
  // 3. FLOATING CURVED HOLOGRAPHIC HUD SCREENS
  // ==========================================================================
  buildCurvedHoloScreens() {
    this.screensGroup = new this.THREE.Group();
    this.screensGroup.name = 'MrFlowCurvedHoloScreens';

    // A. SCREEN 1 (LEFT FLANK): AUDIO & NEURAL CORE EQUALIZER
    this.eqCanvas = document.createElement('canvas');
    this.eqCanvas.width = 512;
    this.eqCanvas.height = 256;
    this.eqCtx = this.eqCanvas.getContext('2d');
    this.eqTexture = new this.THREE.CanvasTexture(this.eqCanvas);
    this.eqTexture.minFilter = this.THREE.LinearFilter;
    this.eqTexture.magFilter = this.THREE.LinearFilter;

    // Curved cylinder segment facing Mr. Flow
    const eqRadius = 1.88;
    const eqHeight = 1.05;
    const eqArc = Math.PI / 3.4; // ~53 degrees
    const eqCenterAngle = -Math.PI * 0.38; // Left-front
    const eqStartAngle = eqCenterAngle - eqArc / 2;

    const eqGeo = new this.THREE.CylinderGeometry(
      eqRadius, eqRadius, eqHeight, 32, 1, true,
      eqStartAngle, eqArc
    );
    const eqMat = new this.THREE.MeshBasicMaterial({
      map: this.eqTexture,
      transparent: true,
      opacity: 0.92,
      blending: this.THREE.AdditiveBlending,
      side: this.THREE.DoubleSide,
      depthWrite: false
    });
    this.eqScreenMesh = new this.THREE.Mesh(eqGeo, eqMat);
    this.eqScreenMesh.position.set(0, 1.25, 0);
    this.screensGroup.add(this.eqScreenMesh);

    // B. SCREEN 2 (RIGHT FLANK): SOVEREIGN MATRIX TELEMETRY & DIAGNOSTICS
    this.telemetryCanvas = document.createElement('canvas');
    this.telemetryCanvas.width = 512;
    this.telemetryCanvas.height = 256;
    this.telemetryCtx = this.telemetryCanvas.getContext('2d');
    this.telemetryTexture = new this.THREE.CanvasTexture(this.telemetryCanvas);
    this.telemetryTexture.minFilter = this.THREE.LinearFilter;
    this.telemetryTexture.magFilter = this.THREE.LinearFilter;

    const telemRadius = 1.88;
    const telemHeight = 1.05;
    const telemArc = Math.PI / 3.4;
    const telemCenterAngle = Math.PI * 0.38; // Right-front
    const telemStartAngle = telemCenterAngle - telemArc / 2;

    const telemGeo = new this.THREE.CylinderGeometry(
      telemRadius, telemRadius, telemHeight, 32, 1, true,
      telemStartAngle, telemArc
    );
    const telemMat = new this.THREE.MeshBasicMaterial({
      map: this.telemetryTexture,
      transparent: true,
      opacity: 0.92,
      blending: this.THREE.AdditiveBlending,
      side: this.THREE.DoubleSide,
      depthWrite: false
    });
    this.telemScreenMesh = new this.THREE.Mesh(telemGeo, telemMat);
    this.telemScreenMesh.position.set(0, 1.25, 0);
    this.screensGroup.add(this.telemScreenMesh);

    this.group.add(this.screensGroup);
  }

  // ==========================================================================
  // 4. UPPER-CENTER REVOLVING 3D HOLOGRAPHIC CORE MATRIX
  // ==========================================================================
  buildCoreMatrix() {
    this.coreMatrix = new this.THREE.Group();
    this.coreMatrix.name = 'MrFlowCoreMatrix';
    this.coreMatrix.position.set(0, 2.30, -0.75);

    // A. 3D Wireframe Icosahedron
    const icoGeo = new this.THREE.IcosahedronGeometry(0.36, 1);
    const icoMat = new this.THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      wireframe: true,
      transparent: true,
      opacity: 0.75,
      blending: this.THREE.AdditiveBlending
    });
    this.icoMesh = new this.THREE.Mesh(icoGeo, icoMat);
    this.coreMatrix.add(this.icoMesh);

    // B. Inner Pulsing Core Sphere
    const coreSphereGeo = new this.THREE.SphereGeometry(0.16, 16, 16);
    const coreSphereMat = new this.THREE.MeshBasicMaterial({
      color: 0x8b5cf6,
      transparent: true,
      opacity: 0.85,
      blending: this.THREE.AdditiveBlending
    });
    this.coreSphere = new this.THREE.Mesh(coreSphereGeo, coreSphereMat);
    this.coreMatrix.add(this.coreSphere);

    // C. Revolving Reticle Ring
    const reticleGeo = new this.THREE.RingGeometry(0.48, 0.51, 32);
    const reticleMat = new this.THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.85,
      side: this.THREE.DoubleSide,
      blending: this.THREE.AdditiveBlending
    });
    this.coreReticleA = new this.THREE.Mesh(reticleGeo, reticleMat);
    this.coreMatrix.add(this.coreReticleA);

    this.coreReticleB = new this.THREE.Mesh(reticleGeo, reticleMat);
    this.coreReticleB.rotation.x = Math.PI / 2;
    this.coreMatrix.add(this.coreReticleB);

    // D. Vertical Scanning Laser Sweep Plane
    const laserGeo = new this.THREE.RingGeometry(0.05, 0.45, 24);
    const laserMat = new this.THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.55,
      side: this.THREE.DoubleSide,
      blending: this.THREE.AdditiveBlending
    });
    this.laserPlane = new this.THREE.Mesh(laserGeo, laserMat);
    this.laserPlane.rotation.x = Math.PI / 2;
    this.coreMatrix.add(this.laserPlane);

    this.group.add(this.coreMatrix);
  }

  // ==========================================================================
  // 5. DEDICATED SCI-FI HOLOGRAPHIC LIGHTING
  // ==========================================================================
  buildHoloLighting() {
    this.lightsGroup = new this.THREE.Group();
    this.lightsGroup.name = 'MrFlowHoloLighting';

    // Core Uplight (Floods upward from floor arc reactor)
    const floorLight = new this.THREE.PointLight(0x00f0ff, 3.2, 7.5, 1.2);
    floorLight.position.set(0, 0.25, 0);
    this.lightsGroup.add(floorLight);

    // Overhead Violet Rim Light (Dramatic sci-fi rim lighting on Mr. Flow)
    const topLight = new this.THREE.PointLight(0x8b5cf6, 2.2, 6.0, 1.2);
    topLight.position.set(0, 3.10, 0);
    this.lightsGroup.add(topLight);

    // Front Holographic Screen Illuminators
    const screenLightL = new this.THREE.PointLight(0x00e5ff, 1.4, 4.5, 1.4);
    screenLightL.position.set(-1.4, 1.4, 1.0);
    this.lightsGroup.add(screenLightL);

    const screenLightR = new this.THREE.PointLight(0xa855f7, 1.4, 4.5, 1.4);
    screenLightR.position.set(1.4, 1.4, 1.0);
    this.lightsGroup.add(screenLightR);

    this.group.add(this.lightsGroup);
  }

  // ==========================================================================
  // 6. ION THRUSTER ENERGY PLUMES (UNDER MR. FLOW BOOTS)
  // ==========================================================================
  buildThrusterPlumes() {
    this.thrusterGroup = new this.THREE.Group();
    this.thrusterGroup.name = 'MrFlowIonThrusterPlumes';

    const discGeo = new this.THREE.RingGeometry(0.02, 0.14, 24);
    const discMat = new this.THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      side: this.THREE.DoubleSide,
      transparent: true,
      opacity: 0.90,
      blending: this.THREE.AdditiveBlending
    });

    // Left Thruster Disc
    this.thrusterDiscL = new this.THREE.Mesh(discGeo, discMat);
    this.thrusterDiscL.rotation.x = -Math.PI / 2;
    this.thrusterDiscL.position.set(-0.16, 0.72, 0.0);
    this.thrusterGroup.add(this.thrusterDiscL);

    // Right Thruster Disc
    this.thrusterDiscR = new this.THREE.Mesh(discGeo, discMat);
    this.thrusterDiscR.rotation.x = -Math.PI / 2;
    this.thrusterDiscR.position.set(0.16, 0.72, 0.0);
    this.thrusterGroup.add(this.thrusterDiscR);

    this.group.add(this.thrusterGroup);
  }

  // ==========================================================================
  // 7. TELEMETRY STREAM SEED DATA
  // ==========================================================================
  initTelemetryData() {
    this.hexLines = [
      '0x7FFF94A2  48 89 E5 48 83 EC 20  CALL_CORE_INIT',
      '0x7FFF94B4  BA 01 00 00 00 BE 00  EXIT_CODE_0_OK',
      '0x7FFF94C6  E8 D5 FE FF FF 48 89  LOCK_PROTECTED',
      '0x7FFF94D8  8B 45 F8 89 C7 E8 BF  BRAIN_RECALL_ON',
      '0x7FFF94EA  48 83 C4 20 5D C3 90  CIRCUIT_0_CALL',
      '0x7FFF94FC  66 2E 0F 1F 84 00 00  SOVEREIGN_LV99'
    ];
  }

  // ==========================================================================
  // 8. DYNAMIC EQUALIZER CANVAS RENDERER
  // ==========================================================================
  drawEqualizerCanvas(time, isWorking, isThinking) {
    if (!this.eqCtx) return;
    const ctx = this.eqCtx;
    const w = 512, h = 256;

    ctx.clearRect(0, 0, w, h);

    // Semi-transparent Cyber Card Background
    ctx.fillStyle = 'rgba(4, 9, 20, 0.82)';
    ctx.fillRect(0, 0, w, h);

    // Neon Frame Borders & Corner Brackets
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.45)';
    ctx.lineWidth = 2;
    ctx.strokeRect(6, 6, w - 12, h - 12);

    // Corner accents
    ctx.fillStyle = '#00f0ff';
    ctx.fillRect(6, 6, 16, 3);
    ctx.fillRect(6, 6, 3, 16);
    ctx.fillRect(w - 22, 6, 16, 3);
    ctx.fillRect(w - 9, 6, 3, 16);
    ctx.fillRect(6, h - 9, 16, 3);
    ctx.fillRect(6, h - 22, 3, 16);
    ctx.fillRect(w - 22, h - 9, 16, 3);
    ctx.fillRect(w - 9, h - 22, 3, 16);

    // Title Bar (White Labeled: Mr. Flow Neural Core)
    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 13px monospace';
    ctx.fillText('◈ MR. FLOW NEURAL CORE EQUALIZER ◈', 20, 28);

    ctx.fillStyle = isWorking ? '#f59e0b' : '#10b981';
    ctx.font = '11px monospace';
    ctx.fillText(isWorking ? '● ACTIVE PROCESSING' : '● QUANTUM STANDBY', w - 180, 28);

    // 32-Band Spectrum Bars
    const barCount = 32;
    const barWidth = 11;
    const gap = 3.6;
    const startX = 20;
    const maxBarHeight = 135;
    const baseY = 205;

    const baseMult = (isWorking || isThinking) ? 1.6 : 0.85;
    const speedMult = (isWorking || isThinking) ? 14.0 : 6.0;

    for (let i = 0; i < barCount; i++) {
      // Dynamic frequency wave calculation
      const waveA = Math.sin(time * speedMult + i * 0.42);
      const waveB = Math.cos(time * (speedMult * 0.6) + i * 0.78);
      const rawTarget = Math.abs(waveA * 0.65 + waveB * 0.35) * baseMult;
      const targetHeight = Math.min(maxBarHeight, Math.max(12, rawTarget * maxBarHeight));

      // Smooth bar interpolation
      this.eqBars[i] += (targetHeight - this.eqBars[i]) * 0.28;

      // Peak hold dots
      if (this.eqBars[i] > this.eqPeakBars[i]) {
        this.eqPeakBars[i] = this.eqBars[i];
      } else {
        this.eqPeakBars[i] = Math.max(0, this.eqPeakBars[i] - 1.2);
      }

      const bx = startX + i * (barWidth + gap);
      const bh = this.eqBars[i];
      const by = baseY - bh;

      // Vertical Gradient (Cyan -> Violet -> Hot Pink)
      const barGrad = ctx.createLinearGradient(0, baseY, 0, by);
      barGrad.addColorStop(0, '#00f0ff');
      barGrad.addColorStop(0.65, '#8b5cf6');
      barGrad.addColorStop(1, '#ec4899');

      ctx.fillStyle = barGrad;
      ctx.fillRect(bx, by, barWidth, bh);

      // Peak dot
      ctx.fillStyle = '#fef08a';
      ctx.fillRect(bx, baseY - this.eqPeakBars[i] - 3, barWidth, 2);
    }

    // Oscilloscope Bottom Wave Line
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let x = 20; x < w - 20; x += 4) {
      const oscY = 228 + Math.sin(x * 0.06 + time * 8.0) * (isWorking ? 8.0 : 4.0);
      if (x === 20) ctx.moveTo(x, oscY);
      else ctx.lineTo(x, oscY);
    }
    ctx.stroke();

    // Footer Readout
    ctx.fillStyle = 'rgba(255, 255, 255, 0.75)';
    ctx.font = '10px monospace';
    ctx.fillText('IN: -12.4 dB  |  FREQ: 432 Hz  |  NEURAL SYNC: 99.8%  |  FL_BRAIN: CONNECTED', 20, 246);

    this.eqTexture.needsUpdate = true;
  }

  // ==========================================================================
  // 9. DYNAMIC TELEMETRY CANVAS RENDERER
  // ==========================================================================
  drawTelemetryCanvas(time, isWorking) {
    if (!this.telemetryCtx) return;
    const ctx = this.telemetryCtx;
    const w = 512, h = 256;

    ctx.clearRect(0, 0, w, h);

    // Semi-transparent Cyber Card Background
    ctx.fillStyle = 'rgba(4, 9, 20, 0.82)';
    ctx.fillRect(0, 0, w, h);

    // Neon Frame Borders & Corner Brackets
    ctx.strokeStyle = 'rgba(168, 85, 247, 0.45)';
    ctx.lineWidth = 2;
    ctx.strokeRect(6, 6, w - 12, h - 12);

    // Corner accents (Violet)
    ctx.fillStyle = '#a855f7';
    ctx.fillRect(6, 6, 16, 3);
    ctx.fillRect(6, 6, 3, 16);
    ctx.fillRect(w - 22, 6, 16, 3);
    ctx.fillRect(w - 9, 6, 3, 16);
    ctx.fillRect(6, h - 9, 16, 3);
    ctx.fillRect(6, h - 22, 3, 16);
    ctx.fillRect(w - 22, h - 9, 16, 3);
    ctx.fillRect(w - 9, h - 22, 3, 16);

    // Title Bar
    ctx.fillStyle = '#c084fc';
    ctx.font = 'bold 13px monospace';
    ctx.fillText('◈ SOVEREIGN MATRIX TELEMETRY & DIAGNOSTICS ◈', 20, 28);

    // Status Cards & Badges
    ctx.font = '11px monospace';
    
    // Line 1: Security
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('[SECURITY LEVEL]', 20, 56);
    ctx.fillStyle = '#4ade80';
    ctx.fillText('LV99 SUPER ADMIN (SOVEREIGN)', 160, 56);

    // Line 2: Circuit Breaker
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('[CIRCUIT BREAKER]', 20, 76);
    ctx.fillStyle = '#facc15';
    ctx.fillText('ARMED (0/500 CALLS MONITORING)', 160, 76);

    // Line 3: Radical Truth Verification
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('[EXIT CODE]', 20, 96);
    ctx.fillStyle = '#4ade80';
    ctx.fillText('EXIT CODE 0 (VERIFIED & LOCKED)', 160, 96);

    // Line 4: Memory Vault
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('[KUBAH INGATAN]', 20, 116);
    ctx.fillStyle = '#a78bfa';
    ctx.fillText('/dr.floworks-skl/.fl_brain (RECALL ACTIVE)', 160, 116);

    // Separator line
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.beginPath();
    ctx.moveTo(20, 130);
    ctx.lineTo(w - 20, 130);
    ctx.stroke();

    // Rolling Hex Code Stream
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px monospace';
    ctx.fillText('HEX MEMORY STREAM & REGISTERS:', 20, 148);

    ctx.fillStyle = '#38bdf8';
    const hexOffset = Math.floor(time * 2.5) % this.hexLines.length;
    for (let l = 0; l < 4; l++) {
      const idx = (hexOffset + l) % this.hexLines.length;
      ctx.fillText(this.hexLines[idx], 20, 168 + l * 17);
    }

    // Circular Radial Gauges (Right Side)
    const gx1 = 440, gy1 = 76, gr1 = 28;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(gx1, gy1, gr1, 0, Math.PI * 2);
    ctx.stroke();

    // Gauge 1: Neural Core Load Arc
    const coreLoad = 0.65 + Math.sin(time * 3.0) * 0.18;
    ctx.strokeStyle = '#00f0ff';
    ctx.beginPath();
    ctx.arc(gx1, gy1, gr1, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * coreLoad);
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`${Math.round(coreLoad * 100)}%`, gx1, gy1 + 3);
    ctx.fillStyle = '#38bdf8';
    ctx.font = '9px monospace';
    ctx.fillText('CORE', gx1, gy1 + 14);

    // Gauge 2: Quantum Memory Load Arc
    const gx2 = 440, gy2 = 175, gr2 = 28;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(gx2, gy2, gr2, 0, Math.PI * 2);
    ctx.stroke();

    const memLoad = 0.42 + Math.sin(time * 1.5) * 0.08;
    ctx.strokeStyle = '#a855f7';
    ctx.beginPath();
    ctx.arc(gx2, gy2, gr2, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * memLoad);
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 10px monospace';
    ctx.fillText(`${Math.round(memLoad * 100)}%`, gx2, gy2 + 3);
    ctx.fillStyle = '#c084fc';
    ctx.font = '9px monospace';
    ctx.fillText('MEM', gx2, gy2 + 14);
    ctx.textAlign = 'left';

    this.telemetryTexture.needsUpdate = true;
  }

  // ==========================================================================
  // 10. LIFECYCLE: ACTIVATE SOLO MR. FLOW MODE
  // ==========================================================================
  activate(soloAgent) {
    this.group.visible = true;
    this.activeAgent = soloAgent || null;

    if (this.activeAgent && this.activeAgent.group) {
      // Save original desk position before levitating
      this.originalStandbyPos = this.activeAgent.data ? this.activeAgent.data.deskPos.clone() : new this.THREE.Vector3(0, 0.22, -3.6);
      this.originalStandbyRotY = this.activeAgent.data ? this.activeAgent.data.deskFacingAngle : 0;

      // Position Mr. Flow at Center of Arc Reactor Hover Dais
      this.activeAgent.group.position.set(0, 1.15, 0);
      this.activeAgent.group.rotation.set(0, 0, 0);

      // Hide Desk and Chair pods
      if (this.activeAgent.slotGroup) {
        this.activeAgent.slotGroup.visible = false;
      }
    }
  }

  // ==========================================================================
  // 11. LIFECYCLE: DEACTIVATE (SWITCH BACK TO TEAM MODE)
  // ==========================================================================
  deactivate() {
    this.group.visible = false;

    if (this.activeAgent && this.activeAgent.group) {
      // Restore desk visibility and posture
      if (this.activeAgent.slotGroup) {
        this.activeAgent.slotGroup.visible = true;
      }
      if (this.originalStandbyPos) {
        this.activeAgent.group.position.copy(this.originalStandbyPos);
        this.activeAgent.group.rotation.set(0, this.originalStandbyRotY, 0);
      }
      // Reset limbs
      if (this.activeAgent.legL) this.activeAgent.legL.rotation.set(0, 0, 0);
      if (this.activeAgent.legR) this.activeAgent.legR.rotation.set(0, 0, 0);
      if (this.activeAgent.armL) this.activeAgent.armL.rotation.set(0, 0, 0);
      if (this.activeAgent.armR) this.activeAgent.armR.rotation.set(0, 0, 0);
      if (this.activeAgent.head) this.activeAgent.head.rotation.set(0, 0, 0);
    }
    this.activeAgent = null;
  }

  // ==========================================================================
  // 12. MAIN ANIMATION LOOP STEP
  // ==========================================================================
  update(delta, time, soloAgent) {
    if (!this.group.visible) return;

    if (soloAgent) {
      this.activeAgent = soloAgent;
    }

    // A. Animate Arc Reactor Floor Rings
    if (this.tickRingGroup) {
      this.tickRingGroup.rotation.y = -time * 0.12;
    }
    if (this.midRing) {
      this.midRing.rotation.z = time * 0.18;
    }
    if (this.innerRing) {
      this.innerRing.rotation.z = -time * 0.28;
    }
    if (this.coreDisc) {
      this.coreDisc.rotation.z = time * 0.45;
      const pulse = 0.85 + Math.sin(time * 3.0) * 0.15;
      this.coreDisc.material.opacity = pulse;
    }

    // B. Animate 3D Gyroscopic Rings (Nested Gimbal Rotation)
    if (this.gyroRingA) {
      this.gyroRingA.rotation.x += delta * 0.55;
      this.gyroRingA.rotation.y += delta * 0.70;
    }
    if (this.gyroRingB) {
      this.gyroRingB.rotation.y += delta * -0.45;
      this.gyroRingB.rotation.z += delta * 0.60;
    }
    if (this.gyroRingC) {
      this.gyroRingC.rotation.x += delta * -0.35;
      this.gyroRingC.rotation.z += delta * -0.50;
    }

    // Update Orbital Nodes
    if (this.orbitalNodes && this.orbitalNodes.length > 0) {
      this.orbitalNodes.forEach(nd => {
        const a = time * nd.speed + nd.phase;
        nd.mesh.position.set(Math.cos(a) * nd.radius, Math.sin(a) * nd.radius, 0);
      });
    }

    // C. Animate 3D Holographic Core Matrix
    if (this.icoMesh) {
      this.icoMesh.rotation.x = time * 0.65;
      this.icoMesh.rotation.y = time * 0.85;
    }
    if (this.coreSphere) {
      const corePulse = 1.0 + Math.sin(time * 5.0) * 0.25;
      this.coreSphere.scale.set(corePulse, corePulse, corePulse);
    }
    if (this.coreReticleA) {
      this.coreReticleA.rotation.z = time * 0.90;
    }
    if (this.coreReticleB) {
      this.coreReticleB.rotation.y = -time * 0.75;
    }
    if (this.laserPlane) {
      // Laser scan sweeps up and down
      this.laserPlane.position.y = Math.sin(time * 2.8) * 0.28;
    }

    // D. Dynamic Canvas Textures (Throttled to ~25fps for maximum WebGL efficiency)
    const now = performance.now();
    const isWorking = Boolean(
      this.activeAgent && this.activeAgent.data && 
      (this.activeAgent.data.state === 'working' || this.activeAgent.data.isThinking || 
       (this.activeAgent.data.activeTool && this.activeAgent.data.activeTool.name))
    );
    const isThinking = Boolean(this.activeAgent && this.activeAgent.data && this.activeAgent.data.isThinking);

    if (now - this.lastCanvasUpdate > 38) {
      this.lastCanvasUpdate = now;
      this.drawEqualizerCanvas(time, isWorking, isThinking);
      this.drawTelemetryCanvas(time, isWorking);
    }

    // E. MR. FLOW HOVER & LEVITATION PHYSICS
    if (this.activeAgent && this.activeAgent.group) {
      const ag = this.activeAgent;

      // Base Levitation Height & Smooth Sinusoidal Bobbing
      const hoverHeight = 1.15 + Math.sin(time * 2.2) * 0.055;
      ag.group.position.set(0, hoverHeight, 0);

      // Subtle Banking Roll & Pitch
      ag.group.rotation.z = Math.sin(time * 1.5) * 0.022;
      ag.group.rotation.x = Math.sin(time * 1.8) * 0.018;

      // Scanning gaze
      const gazeYaw = Math.sin(time * 0.4) * 0.14;
      ag.group.rotation.y = gazeYaw;

      // Leg Posture in Flight Levitation
      if (ag.legL) ag.legL.rotation.x = 0.18 + Math.sin(time * 2.2) * 0.03;
      if (ag.legR) ag.legR.rotation.x = 0.22 - Math.sin(time * 2.2) * 0.03;

      // Ion Thruster Discs under boots
      if (this.thrusterDiscL && this.thrusterDiscR) {
        const thrusterScale = 1.0 + Math.sin(time * 18.0) * 0.22;
        this.thrusterDiscL.scale.set(thrusterScale, thrusterScale, 1.0);
        this.thrusterDiscR.scale.set(thrusterScale, thrusterScale, 1.0);
        this.thrusterDiscL.position.y = hoverHeight - 0.44;
        this.thrusterDiscR.position.y = hoverHeight - 0.44;
      }

      // Authentic Thruster Flame scaling on Agent Rig
      if (ag.thrusterFlames && ag.thrusterFlames.length > 0) {
        ag.thrusterFlames.forEach(fl => {
          if (fl) {
            fl.visible = true;
            const fScale = 1.1 + Math.sin(time * 20.0) * 0.35;
            fl.scale.set(fScale, fScale * 1.3, fScale);
          }
        });
      }

      // Arm Gestures: Idle vs Active Holographic Interaction
      if (isWorking || isThinking) {
        // High-Speed Cyber Gesture: Manipulating Hologram Screens
        const typeRate = 16.0;
        const typeAmp = 0.20;
        const burstL = Math.sin(time * typeRate);
        const burstR = Math.sin(time * typeRate + 1.2);

        if (ag.armL) ag.armL.rotation.set(-1.05 + burstL * typeAmp, 0.30, -0.12);
        if (ag.armR) ag.armR.rotation.set(-1.05 - burstR * typeAmp, -0.30, 0.12);
        if (ag.head) ag.head.rotation.set(0.10 + Math.sin(time * 8.0) * 0.05, Math.sin(time * 4.0) * 0.22, 0);
      } else {
        // Sci-Fi Standby: Hands held slightly forward interacting with air interface
        const breath = Math.sin(time * 1.8);
        if (ag.armL) ag.armL.rotation.set(-0.62 + breath * 0.04, 0.22, -0.10);
        if (ag.armR) ag.armR.rotation.set(-0.62 + breath * 0.04, -0.22, 0.10);
        if (ag.head) ag.head.rotation.set(0.04, Math.sin(time * 0.6) * 0.20, 0);
      }

      // Arc Reactor Chest Ring on Mr. Flow pulses brightly
      if (ag.coreRing && ag.coreRing.material) {
        ag.coreRing.material.opacity = 0.90 + Math.sin(time * 10.0) * 0.15;
      }
    }
  }

  // ==========================================================================
  // 13. DISPOSE
  // ==========================================================================
  dispose() {
    if (this.group && this.group.parent) {
      this.group.parent.remove(this.group);
    }
    if (this.eqTexture) this.eqTexture.dispose();
    if (this.telemetryTexture) this.telemetryTexture.dispose();
  }
}

// Global Attachment & Compatibility
if (typeof window !== 'undefined') {
  window.MrFlowSoloLab = MrFlowSoloLab;
}

export default MrFlowSoloLab;
