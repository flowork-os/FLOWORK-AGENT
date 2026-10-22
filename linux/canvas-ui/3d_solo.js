/**
 * ============================================================================
 * 🏛️ FLOWORK OS — 3D LUXURY EXECUTIVE OFFICE & BOARDROOM ENGINE
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 * ============================================================================
 * Key Architectural Highlights:
 * 1. Executive Penthouse Boardroom & Studio:
 *    - Polished Grigio Carnico obsidian marble floors with brass borders
 *    - Dark American Walnut acoustic slats & champagne gold architectural accents
 * 2. Panoramic Metropolitan High-Rise Skyline Windows:
 *    - Floor-to-ceiling glass observation walls overlooking glowing skyscrapers
 *    - Natural 3500K architectural daylight & warm downlights
 * 3. Executive Round Conference Table:
 *    - Solid American Walnut conference table with calfskin leather inlay
 *    - Central 3D holographic Flowork engineering projector
 * 4. Corporate Workstations & Ergonomic Executive Chairs:
 *    - Walnut desks, dual monitors, leather writing blotters, ergonomic swivel chairs
 * 5. Dedicated Specialist Auditor Workstation (Option C):
 *    - Walnut workstation pod with live adversarial code review display
 * 6. Authentic Chibi Robot Mascots Preserved 100%:
 *    - Grand Chief AI Overseer and full mascot avatar roster preserved intact
 */

import * as THREE from 'https://canvas.floworkos.com/canvas/vendor/three/three.module.js';

const PERSONA_PALETTE = [
  0x00f2fe, // Neon Cyan (Core Engine)
  0x38bdf8, // Electric Sky Blue
  0xa855f7, // Neon Purple
  0xf59e0b, // Amber Gold
  0x10b981, // Emerald Green
  0xec4899, // Hot Pink
  0xef4444, // Coral Red
  0x06b6d4, // Cyan Teal
  0x8b5cf6, // Deep Violet
  0xf97316, // Orange Flame
  0x14b8a6, // Bright Mint
  0x6366f1  // Indigo
];

class SovereignOffice3D {
  constructor(canvasElement, containerElement) {
    this.canvas = canvasElement;
    this.container = containerElement || canvasElement.parentElement;
    this.agents = [];
    this.workstationsGroup = null;
    this.environmentGroup = null;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2(-999, -999);
    this.hoveredAgent = null;
    this.selectedAgent = null;
    this.clock = new THREE.Clock();
    this.isRunning = true;

    // Active Office Mode
    this.currentMode = 'office';

    // Camera targets: Overview of Modern Corporate Tech Office (Elevated Overview of 3-Wide Grid)
    this.camTarget = new THREE.Vector3(0, 1.20, 1.10);
    this.camPosTarget = new THREE.Vector3(0, 6.20, 11.80);
    this.agentRoster = [];

    this.floorMesh = null;
    this.selectionRing = null;
    this.navTargetMarker = null;
    this.activeKeys = new Set();
    this.boardCanvas = null;
    this.boardTexture = null;

    // Follow-Cam distances for smooth zooming
    this.camFollowDist = 6.5;
    this.camFollowHeight = 4.8;

    // WebGL Optimization: Shared Resources & State
    this.sharedMaterials = null;
    this.sharedGeometries = null;
    this.accentMatCache = null;
    this.orbitalMatCache = null;
    this.logoTextures = null;
    this.faceTextureCache = null;
    this.isInteractionsAttached = false;

    // Dynamic Roster Watcher
    this._rosterWatcherInterval = null;
    this._lastRosterFingerprint = null;
    this.wallClockSecondHand = null;
    this.serverLeds = [];

    window.office3DInstance = this;
    this.init();
  }

  init() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x111722);
    this.scene.fog = null;

    const aspect = (this.container && this.container.clientHeight > 0) ? (this.container.clientWidth / this.container.clientHeight) : 1.77;
    this.camera = new THREE.PerspectiveCamera(48, aspect, 0.5, 350);
    this.camera.position.copy(this.camPosTarget);
    this.camera.lookAt(this.camTarget);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);

    let isSoftwareRenderer = false;
    try {
      const gl = this.renderer.getContext();
      const dbg = gl.getExtension('WEBGL_debug_renderer_info');
      if (dbg) {
        const rName = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) || '';
        if (/llvmpipe|swiftshader|software/i.test(rName)) {
          isSoftwareRenderer = true;
          window.isLowPowerMode = true;
        }
      }
    } catch (_) {}
    this.isSoftwareRenderer = isSoftwareRenderer;

    const maxPixelRatio = (this.isSoftwareRenderer || window.isLowPowerMode) ? 1.0 : 1.5;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, maxPixelRatio));
    this.renderer.shadowMap.enabled = false;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25;

    this.lastCalmRender = 0;
    this.isInteracting = false;
    this.interactTimeout = null;

    this.initSharedResources();

    // Environment Group (Office Interior)
    this.environmentGroup = new THREE.Group();
    this.environmentGroup.name = 'OfficeEnvironment';
    this.scene.add(this.environmentGroup);

    // Compatibility references
    this.groupEnvironmentGroup = this.environmentGroup;
    this.soloEnvironmentGroup = this.environmentGroup;
    this.soloForegroundGroup = new THREE.Group();
    this.scene.add(this.soloForegroundGroup);

    this.buildLighting();
    this.buildModernCorporateOffice();

    // Workstations & Agents Container
    this.workstationsGroup = new THREE.Group();
    this.workstationsGroup.name = 'WorkstationsGroup';
    this.scene.add(this.workstationsGroup);

    this.initForegroundRenderer();
    this.loadPersonas();
    this.startRosterWatcher();
    this.setupInteractions();

    window.addEventListener('flowork:auth-synced', (e) => {
      this.syncUserIdentity(e.detail);
    });

    this.rafId = null;
    this.isPaused = false;
    this.animate = this.animate.bind(this);
    this.resume();
  }
  initSharedResources() {
    this.sharedMaterials = {
      // Executive Corporate Office Materials & Luxury Architectural Finishes
      walnutWoodMat: new THREE.MeshStandardMaterial({
        color: 0x241711, // Rich dark American Walnut
        roughness: 0.52,
        metalness: 0.12,
      }),
      oakWoodMat: new THREE.MeshStandardMaterial({
        color: 0x6e4726, // Warm natural executive oak
        roughness: 0.48,
        metalness: 0.10,
      }),
      executiveLeatherMat: new THREE.MeshStandardMaterial({
        color: 0x0f141c, // Premium deep charcoal perforated calfskin leather
        roughness: 0.38,
        metalness: 0.22,
      }),
      brushedBrassMat: new THREE.MeshStandardMaterial({
        color: 0xd4af37, // Polished brushed Champagne gold brass
        metalness: 0.88,
        roughness: 0.22,
      }),
      matteGraphiteMat: new THREE.MeshStandardMaterial({
        color: 0x1f2937, // Modern architectural slate graphite steel
        metalness: 0.78,
        roughness: 0.28,
      }),
      corporateDeskMat: new THREE.MeshStandardMaterial({
        color: 0x1a2130, // Sleek executive laminate with subtle bevel
        roughness: 0.25,
        metalness: 0.65,
      }),
      frostedLampMat: new THREE.MeshStandardMaterial({
        color: 0xffedd5,
        emissive: 0xffa040,
        emissiveIntensity: 1.8,
        roughness: 0.25,
        metalness: 0.10,
        transparent: true,
        opacity: 0.94,
      }),
      // Architectural Materials
      alienHullMat: new THREE.MeshStandardMaterial({
        color: 0x131a28, // Architectural dark corporate slate
        roughness: 0.35,
        metalness: 0.65,
      }),
      alienRibMat: new THREE.MeshStandardMaterial({
        color: 0x1e2738, // Reinforced architectural steel column
        roughness: 0.40,
        metalness: 0.60,
      }),
      plasmaCyanMat: new THREE.MeshBasicMaterial({
        color: 0x00f2fe,
      }),
      plasmaPurpleMat: new THREE.MeshBasicMaterial({
        color: 0xa855f7,
      }),
      thrusterFlameMat: new THREE.MeshBasicMaterial({
        color: 0x00f2fe,
        transparent: true,
        opacity: 0.88,
      }),
      thrusterCoreMat: new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.95,
      }),
      holoScreenFrameMat: new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.25,
        metalness: 0.80,
      }),
      warpCoreMat: new THREE.MeshBasicMaterial({
        color: 0x00f2fe,
        wireframe: true,
        transparent: true,
        opacity: 0.75,
      }),
      nebulaMatViolet: new THREE.MeshBasicMaterial({
        color: 0x7f00ff,
        transparent: true,
        opacity: 0.22,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
      nebulaMatCyan: new THREE.MeshBasicMaterial({
        color: 0x00f2fe,
        transparent: true,
        opacity: 0.18,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),

      bossArmorMat: new THREE.MeshStandardMaterial({
        color: 0x09090b,
        roughness: 0.22,
        metalness: 0.85,
      }),
      agentArmorMat: new THREE.MeshStandardMaterial({
        color: 0x111827,
        roughness: 0.35,
        metalness: 0.65,
      }),
      agentSuitMat: new THREE.MeshStandardMaterial({
        color: 0xf1f5f9, // Crisp Executive Platinum White Cyber Suit
        roughness: 0.22,
        metalness: 0.45,
      }),
      visorGlassMat: new THREE.MeshStandardMaterial({
        color: 0x030814,
        metalness: 0.2,
        roughness: 0.45,
      }),
      purpleAccentMat: new THREE.MeshStandardMaterial({
        color: 0x7f00ff,
        emissive: 0x7f00ff,
        emissiveIntensity: 1.4,
        metalness: 0.8,
        roughness: 0.2,
      }),
      bossCrownMat: new THREE.MeshStandardMaterial({
        color: 0xf59e0b,
        metalness: 0.85,
        roughness: 0.2,
        emissive: 0x78350f,
        emissiveIntensity: 0.4,
      }),
      bossCapeMat: new THREE.MeshStandardMaterial({
        color: 0x451a03,
        roughness: 0.6,
        metalness: 0.3,
      }),
      bossEpauletMat: new THREE.MeshStandardMaterial({
        color: 0xf59e0b,
        metalness: 0.85,
        roughness: 0.2,
      }),

      // Workstation shared materials
      deskLegMat: new THREE.MeshStandardMaterial({
        color: 0x64748b,
        metalness: 0.7,
      }),
      monitorFrameMat: new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        metalness: 0.6,
      }),
      chairMat: new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        roughness: 0.5,
      }),
      kbMat: new THREE.MeshStandardMaterial({
        color: 0x334155,
        roughness: 0.6,
      }),
      mousePadMat: new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        roughness: 0.8,
      }),
      mouseMat: new THREE.MeshStandardMaterial({
        color: 0x64748b,
        roughness: 0.4,
      }),

      // Architecture & Skyline
      buildingMat: new THREE.MeshStandardMaterial({
        color: 0x0a0e17,
        roughness: 0.6,
        metalness: 0.4,
      }),
      dotMatAmber: new THREE.MeshBasicMaterial({ color: 0xf59e0b }),
      dotMatCyan: new THREE.MeshBasicMaterial({ color: 0x00f2fe }),
    };

    this.accentMatCache = new Map();
    this.orbitalMatCache = new Map();
    this.logoTextures = new Map();
    this.faceTextureCache = new Map();

    this.sharedGeometries = {
      // Crown
      // Alien Holo-Terminals & Starship Geometries
      holoMainScreen: new THREE.PlaneGeometry(1.05, 0.58),
      holoSideScreen: new THREE.PlaneGeometry(0.68, 0.48),
      holoHudRibbon: new THREE.PlaneGeometry(1.25, 0.18),
      holoKeyboard: new THREE.PlaneGeometry(0.64, 0.28),
      pylonPedestal: new THREE.CylinderGeometry(0.32, 0.46, 0.65, 16),
      antiGravBase: new THREE.TorusGeometry(0.52, 0.035, 12, 28),
      antiGravCore: new THREE.CylinderGeometry(0.48, 0.48, 0.08, 24),
      thrusterCone: new THREE.ConeGeometry(0.045, 0.18, 12),
      thrusterInner: new THREE.ConeGeometry(0.022, 0.12, 10),
      warpGyroRingA: new THREE.TorusGeometry(2.2, 0.065, 12, 40),
      warpGyroRingB: new THREE.TorusGeometry(2.8, 0.065, 12, 40),

      crownBase: new THREE.CylinderGeometry(0.18, 0.17, 0.05, 16, 1, true),
      crownSpike: new THREE.ConeGeometry(0.04, 0.11, 4),

      // Agent Chibi Body Parts
      agentHelmet: new THREE.SphereGeometry(0.20, 24, 20),
      agentVisor: new THREE.SphereGeometry(0.205, 24, 18, -Math.PI * 0.44, Math.PI * 0.88, Math.PI * 0.22, Math.PI * 0.56),
      visorRim: new THREE.TorusGeometry(0.14, 0.007, 12, 28, Math.PI * 1.3),
      faceMesh: new THREE.PlaneGeometry(0.22, 0.22),
      eye: new THREE.TorusGeometry(0.028, 0.006, 10, 16, Math.PI),
      crestPlate: new THREE.CylinderGeometry(0.062, 0.062, 0.010, 20),
      crestRim: new THREE.TorusGeometry(0.064, 0.005, 10, 24),
      fSpine: new THREE.BoxGeometry(0.018, 0.062, 0.012),
      fTop: new THREE.BoxGeometry(0.040, 0.015, 0.012),
      fMid: new THREE.BoxGeometry(0.028, 0.013, 0.012),
      pod: new THREE.CylinderGeometry(0.055, 0.055, 0.045, 16),
      podRing: new THREE.TorusGeometry(0.058, 0.006, 10, 16),
      ant: new THREE.CylinderGeometry(0.005, 0.008, 0.14, 8),
      antTip: new THREE.SphereGeometry(0.012, 10, 10),
      collar: new THREE.TorusGeometry(0.12, 0.010, 12, 24),
      torso: new THREE.CylinderGeometry(0.17, 0.13, 0.44, 20),
      coreRing: new THREE.TorusGeometry(0.055, 0.008, 10, 20),
      cFSpine: new THREE.BoxGeometry(0.03, 0.12, 0.02),
      cFTop: new THREE.BoxGeometry(0.07, 0.028, 0.02),
      cFMid: new THREE.BoxGeometry(0.05, 0.024, 0.02),
      jacketEmblem: new THREE.PlaneGeometry(0.20, 0.20),
      bossCape: new THREE.BoxGeometry(0.44, 0.65, 0.04),
      bossEpaulet: new THREE.BoxGeometry(0.12, 0.035, 0.14),
      orbitalRing: new THREE.TorusGeometry(0.32, 0.005, 10, 36),
      shoulder: new THREE.SphereGeometry(0.055, 14, 14),
      bicep: new THREE.CylinderGeometry(0.038, 0.034, 0.26, 12),
      hand: new THREE.SphereGeometry(0.045, 12, 12),
      thigh: new THREE.CylinderGeometry(0.042, 0.038, 0.24, 12),
      boot: new THREE.BoxGeometry(0.085, 0.12, 0.14),
      thrusterRing: new THREE.TorusGeometry(0.032, 0.007, 10, 16),

      // Workstation Desk Equipment
      kb: new THREE.BoxGeometry(0.52, 0.015, 0.18),
      mousePad: new THREE.BoxGeometry(0.22, 0.005, 0.24),
      mouse: new THREE.BoxGeometry(0.08, 0.02, 0.12),
      standFoot: new THREE.BoxGeometry(0.24, 0.014, 0.18),
      standPole: new THREE.CylinderGeometry(0.02, 0.02, 0.28),
      screenFrame: new THREE.BoxGeometry(0.85, 0.48, 0.025),
      screenDisplay: new THREE.PlaneGeometry(0.80, 0.43),
      seat: new THREE.BoxGeometry(0.52, 0.06, 0.50),
      back: new THREE.BoxGeometry(0.50, 0.56, 0.05),
      stem: new THREE.CylinderGeometry(0.035, 0.035, 0.48),
      starBase: new THREE.CylinderGeometry(0.28, 0.28, 0.04, 10),

      // Architectural slats & window dots
      northSlat: new THREE.BoxGeometry(0.18, 9.5, 0.08),
      sideSlat: new THREE.BoxGeometry(0.08, 7.5, 0.16),
      windowDot: new THREE.BoxGeometry(0.05, 0.4, 0.4),
    };
  }

  getAccentMat(color, isBoss = false) {
    const key = isBoss ? 'boss' : String(color);
    if (!this.accentMatCache.has(key)) {
      this.accentMatCache.set(key, new THREE.MeshStandardMaterial({
        color: isBoss ? 0xf59e0b : color,
        emissive: isBoss ? 0xd97706 : color,
        emissiveIntensity: 1.5,
        metalness: 0.8,
        roughness: 0.2,
      }));
    }
    return this.accentMatCache.get(key);
  }

  getOrbitalMat(color, isBoss = false) {
    const key = isBoss ? 'boss' : String(color);
    if (!this.orbitalMatCache.has(key)) {
      this.orbitalMatCache.set(key, new THREE.MeshBasicMaterial({
        color: isBoss ? 0xf59e0b : color,
        transparent: true,
        opacity: 0.35,
      }));
    }
    return this.orbitalMatCache.get(key);
  }

  getFaceTexture(data) {
    const isBoss = !!data.isBoss;
    const key = isBoss ? 'boss' : String(data.color);
    if (this.faceTextureCache && this.faceTextureCache.has(key)) {
      return this.faceTextureCache.get(key);
    }
    const faceCanvas = isBoss ? this.createBossFaceCanvas() : this.createFloworkLogoCanvas(data.color);
    const faceTexture = new THREE.CanvasTexture(faceCanvas);
    if (this.faceTextureCache) {
      this.faceTextureCache.set(key, faceTexture);
    }
    return faceTexture;
  }

  buildLighting() {
    // 🏢 MODERN CORPORATE OFFICE LIGHTING (Warm, Bright, Natural)
    // 1. Warm Ambient Hemisphere Light (Warm white ceiling + soft cool floor bounce)
    const hemiLight = new THREE.HemisphereLight(0xfff6eb, 0x1e293b, 1.45);
    this.scene.add(hemiLight);

    // 2. Natural Sunbeam Light flooding through the West Panoramic Windows
    const sunLight = new THREE.DirectionalLight(0xfff5dd, 1.85);
    sunLight.position.set(-18, 22, 6);
    sunLight.target.position.set(0, 0, 2);
    this.scene.add(sunLight);
    this.scene.add(sunLight.target);

    // 3. Interior Fill Light (Soft warm office fill from camera direction)
    const fillLight = new THREE.DirectionalLight(0xffeed9, 1.15);
    fillLight.position.set(10, 16, 16);
    fillLight.target.position.set(0, 1, 0);
    this.scene.add(fillLight);
    this.scene.add(fillLight.target);

    // 4. Executive Command Desk Spotlight (Focus on Mr. Flow's desk)
    const execSpot = new THREE.SpotLight(0xfffaec, 2.8, 16, Math.PI / 4.2, 0.5, 1.2);
    execSpot.position.set(0, 5.8, -1.0);
    execSpot.target.position.set(0, 0.8, -2.8);
    this.scene.add(execSpot);
    this.scene.add(execSpot.target);

    // 5. Overhead Workstation Downlights
    [-2.85, 2.85].forEach(colX => {
      [0.0, 3.2, 6.4].forEach(rowZ => {
        const podLight = new THREE.PointLight(0xfffaed, 1.4, 8, 1.8);
        podLight.position.set(colX, 4.8, rowZ);
        this.scene.add(podLight);
      });
    });
  }
  initForegroundRenderer() {
    const layout = document.querySelector('.canvas-layout');
    let fgCanvas = document.getElementById('office-3d-canvas-fg');
    if (!fgCanvas && layout) {
      fgCanvas = document.createElement('canvas');
      fgCanvas.id = 'office-3d-canvas-fg';
      fgCanvas.className = 'office-3d-canvas-fg';
      layout.appendChild(fgCanvas);
    }
    this.canvasFg = fgCanvas;

    if (this.canvasFg) {
      this.rendererFg = new THREE.WebGLRenderer({
        canvas: this.canvasFg,
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance',
      });
      this.rendererFg.setClearColor(0x000000, 0);
      this.rendererFg.toneMapping = this.renderer.toneMapping;
      this.rendererFg.toneMappingExposure = this.renderer.toneMappingExposure;
      this.syncCanvasFgSize();

      if (this.boundOnPointerMove) this.canvasFg.addEventListener('pointermove', this.boundOnPointerMove);
      if (this.boundOnPointerDown) this.canvasFg.addEventListener('pointerdown', this.boundOnPointerDown);
      if (this.boundOnContextMenu) this.canvasFg.addEventListener('contextmenu', this.boundOnContextMenu);
    }
  }

  syncCanvasFgSize() {
    if (!this.canvas || !this.canvasFg) return;
    const rect = this.canvas.getBoundingClientRect();
    const layout = document.querySelector('.canvas-layout');
    const lRect = layout ? layout.getBoundingClientRect() : { top: 0, left: 0 };
    this.canvasFg.style.position = 'absolute';
    this.canvasFg.style.top = (rect.top - lRect.top) + 'px';
    this.canvasFg.style.left = (rect.left - lRect.left) + 'px';
    this.canvasFg.style.width = rect.width + 'px';
    this.canvasFg.style.height = rect.height + 'px';
    if (this.rendererFg) {
      this.rendererFg.setSize(rect.width, rect.height, false);
      const maxPixelRatio = (this.isSoftwareRenderer || window.isLowPowerMode || (typeof navigator !== 'undefined' && navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4)) ? 1.0 : 1.5;
      this.rendererFg.setPixelRatio(Math.min(window.devicePixelRatio || 1, maxPixelRatio));
    }
  }

  initCotWall() {
    this.cotWallCanvas = document.createElement('canvas');
    this.cotWallCanvas.width = 1920;
    this.cotWallCanvas.height = 960;
    this.cotWallTexture = new THREE.CanvasTexture(this.cotWallCanvas);
    this.cotWallTexture.minFilter = THREE.LinearFilter;
    this.cotWallTexture.magFilter = THREE.LinearFilter;

    this.cotWallState = {
      phase: 'STANDBY // READY',
      userPrompt: 'Awaiting instruction prompt from user...',
      assistantResponse: 'Sovereign Core on standby. Enter a prompt in the chat console below and Mr. Flow will execute immediately.',
      keywords: ['fl_soul', 'fl_brain', 'exit_code_0', 'zero_trust'],
      cotLines: [
        'SYSTEM READY: Flowork Sovereign Core Engine online.',
        'TERRITORY: Workspace verified. Multi-OS portability armed.',
        'MEMORY VAULT: Connected to .fl_brain (1 File 1 Solusi).',
        'IRON DOCTRINE: Anti-Overclaim & Radical Honesty strictly guarded.',
        'MASCOT CORE: Mr. Flow presiding at Executive Luxury Suite.',
        'Awaiting task submission from bottom chat console...'
      ]
    };

    this.drawCotWall(this.cotWallState);
  }

  drawCotWall(data = {}) {
    if (!this.cotWallCanvas) return;
    if (!this.cotWallState) {
      this.cotWallState = {};
    }

    // Merge incoming telemetry into persistent wall state
    if (data.phase) this.cotWallState.phase = data.phase;
    if (data.userPrompt !== undefined) this.cotWallState.userPrompt = data.userPrompt;
    if (data.assistantResponse !== undefined) this.cotWallState.assistantResponse = data.assistantResponse;
    if (data.response !== undefined) this.cotWallState.assistantResponse = data.response;
    if (data.keywords && Array.isArray(data.keywords)) this.cotWallState.keywords = data.keywords;
    if (data.cotLines && Array.isArray(data.cotLines)) this.cotWallState.cotLines = data.cotLines;
    else if (data.reason) {
      if (!this.cotWallState.cotLines) this.cotWallState.cotLines = [];
      if (!this.cotWallState.cotLines.includes(data.reason)) {
        this.cotWallState.cotLines.push(data.reason);
        if (this.cotWallState.cotLines.length > 20) {
          this.cotWallState.cotLines.shift();
        }
      }
    }

    const state = this.cotWallState;
    const ctx = this.cotWallCanvas.getContext('2d');
    const w = this.cotWallCanvas.width;
    const h = this.cotWallCanvas.height;

    // Rich luxury dark obsidian tech background
    ctx.fillStyle = '#050a14';
    ctx.fillRect(0, 0, w, h);

    // Fine holographic grid lines
    ctx.strokeStyle = 'rgba(0, 242, 254, 0.07)';
    ctx.lineWidth = 1;
    for (let x = 40; x < w; x += 60) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 40; y < h; y += 60) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // 1. TOP HEADER BAR
    ctx.fillStyle = 'rgba(14, 165, 233, 0.15)';
    ctx.fillRect(24, 20, w - 48, 64);
    ctx.strokeStyle = '#00f2fe';
    ctx.lineWidth = 2.5;
    ctx.strokeRect(24, 20, w - 48, 64);

    ctx.font = 'bold 28px "Inter", "Segoe UI", monospace';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'left';
    ctx.fillText('⚡ FLOWORK SOVEREIGN COGNITIVE ENGINE', 48, 62);

    const phase = state.phase || 'COGNITIVE REASONING STREAM';
    ctx.font = 'bold 20px monospace';
    ctx.fillStyle = phase.includes('EXIT CODE 0') || phase.includes('COMPLETED') ? '#22c55e' : '#38bdf8';
    ctx.textAlign = 'right';
    ctx.fillText(`● [${phase}]`, w - 48, 62);

    // 2. SUBHEADER: ACTIVE SPECIALIST & USER INSTRUCTION
    ctx.textAlign = 'left';
    ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
    ctx.fillRect(24, 94, w - 48, 54);
    ctx.strokeStyle = 'rgba(168, 85, 247, 0.4)';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(24, 94, w - 48, 54);

    const agentName = (this.activeAgentName || 'MR. FLOW').toUpperCase();
    ctx.font = 'bold 18px monospace';
    ctx.fillStyle = '#a855f7';
    ctx.fillText(`SPECIALIST: ${agentName}`, 48, 128);

    // User prompt summary in center/right of subheader
    const promptTxt = state.userPrompt ? `👤 PROMPT: "${state.userPrompt.length > 70 ? state.userPrompt.slice(0, 68) + '…' : state.userPrompt}"` : '👤 PROMPT: (Standing by)';
    ctx.font = '18px monospace';
    ctx.fillStyle = '#e0f2fe';
    ctx.fillText(promptTxt, 440, 128);

    const keywords = Array.isArray(state.keywords) && state.keywords.length > 0
      ? state.keywords.slice(0, 4).map(k => `#${k}`).join(' ')
      : '#fl_brain #exit_code_0';
    ctx.textAlign = 'right';
    ctx.fillStyle = '#f59e0b';
    ctx.fillText(keywords, w - 48, 128);
    ctx.textAlign = 'left';

    // 3. DUAL-WING SCI-FI COMMAND LAYOUT
    // Left Wing (x: 24 to 760): Chain of Thought (CoT) & Reasoning Stream
    // Center (x: 760 to 1160): Unobstructed silhouette behind Mr. Flow
    // Right Wing (x: 1160 to 1896): Live Assistant Response Stream & Dialogue

    const wingW = 730;
    const wingH = 690;
    const wingY = 160;

    // Helper for word wrapping text
    const renderWrapText = (text, startX, startY, maxWidth, lineHeight, maxLines = 14, color = '#e2e8f0', font = '19px "JetBrains Mono", monospace') => {
      if (!text) return startY;
      ctx.font = font;
      ctx.fillStyle = color;
      const paragraphs = text.split('\n');
      let currentY = startY;
      let totalLinesRendered = 0;

      for (let p = 0; p < paragraphs.length; p++) {
        const words = paragraphs[p].split(' ');
        let currentLine = '';
        for (let n = 0; n < words.length; n++) {
          const testLine = currentLine + words[n] + ' ';
          const metrics = ctx.measureText(testLine);
          if (metrics.width > maxWidth && n > 0) {
            ctx.fillText(currentLine, startX, currentY);
            currentLine = words[n] + ' ';
            currentY += lineHeight;
            totalLinesRendered++;
            if (totalLinesRendered >= maxLines) {
              ctx.fillText(currentLine.trim() + '…', startX, currentY);
              return currentY;
            }
          } else {
            currentLine = testLine;
          }
        }
        if (currentLine.trim().length > 0) {
          ctx.fillText(currentLine, startX, currentY);
          currentY += lineHeight;
          totalLinesRendered++;
          if (totalLinesRendered >= maxLines) return currentY;
        }
      }
      return currentY;
    };

    // --- LEFT WING: CHAIN OF THOUGHT & REASONING TERMINAL ---
    ctx.fillStyle = 'rgba(3, 7, 18, 0.94)';
    ctx.fillRect(24, wingY, wingW, wingH);
    ctx.strokeStyle = 'rgba(0, 242, 254, 0.35)';
    ctx.lineWidth = 2;
    ctx.strokeRect(24, wingY, wingW, wingH);

    // Left Wing Header
    ctx.fillStyle = 'rgba(0, 242, 254, 0.12)';
    ctx.fillRect(24, wingY, wingW, 46);
    ctx.font = 'bold 19px monospace';
    ctx.fillStyle = '#00f2fe';
    ctx.fillText('🧠 CHAIN OF THOUGHT (CoT) & TELEMETRY', 44, wingY + 30);

    const cotList = Array.isArray(state.cotLines) && state.cotLines.length > 0
      ? state.cotLines
      : ['Standing by for user task submission...'];

    let cotY = wingY + 80;
    const visibleCot = cotList.slice(-13);
    visibleCot.forEach((line, idx) => {
      ctx.font = '17px "JetBrains Mono", monospace';
      ctx.fillStyle = '#64748b';
      ctx.fillText(String(idx + 1).padStart(2, '0') + ' | ', 44, cotY);

      if (line.includes('EXIT CODE 0') || line.includes('SUCCESS') || line.includes('PASS')) {
        ctx.fillStyle = '#22c55e';
      } else if (line.includes('WARN') || line.includes('CIRCUIT') || line.includes('ATTENTION')) {
        ctx.fillStyle = '#f59e0b';
      } else if (line.includes('TOOL') || line.includes('EXEC') || line.includes('RUN_COMMAND')) {
        ctx.fillStyle = '#38bdf8';
      } else if (line.includes('THINK') || line.includes('REASON') || line.includes('SYNTH')) {
        ctx.fillStyle = '#a855f7';
      } else if (line.startsWith('USER:')) {
        ctx.fillStyle = '#38bdf8';
      } else {
        ctx.fillStyle = '#cbd5e1';
      }

      const truncatedLine = line.length > 56 ? line.slice(0, 53) + '…' : line;
      ctx.fillText(truncatedLine, 98, cotY);
      cotY += 44;
    });

    // --- RIGHT WING: LIVE ASSISTANT RESPONSE STREAM ---
    const rightWingX = w - wingW - 24;
    ctx.fillStyle = 'rgba(3, 7, 18, 0.94)';
    ctx.fillRect(rightWingX, wingY, wingW, wingH);
    ctx.strokeStyle = 'rgba(168, 85, 247, 0.35)';
    ctx.lineWidth = 2;
    ctx.strokeRect(rightWingX, wingY, wingW, wingH);

    // Right Wing Header
    ctx.fillStyle = 'rgba(168, 85, 247, 0.12)';
    ctx.fillRect(rightWingX, wingY, wingW, 46);
    ctx.font = 'bold 19px monospace';
    ctx.fillStyle = '#c084fc';
    ctx.fillText('💬 MR. FLOW LIVE RESPONSE STREAM', rightWingX + 20, wingY + 30);

    const responseText = state.assistantResponse || 'Awaiting prompt. Responses stream directly here in ultra-low latency...';
    renderWrapText(responseText, rightWingX + 20, wingY + 84, wingW - 40, 36, 15, '#f8fafc', '20px "Inter", "Segoe UI", sans-serif');

    // --- CENTER GAUGE & HOLOGRAPHIC CONDUIT (Behind Mr. Flow) ---
    const centerX = w / 2;
    ctx.strokeStyle = 'rgba(0, 242, 254, 0.18)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(centerX, wingY + wingH / 2, 90, 0, Math.PI * 2);
    ctx.stroke();

    ctx.strokeStyle = 'rgba(168, 85, 247, 0.22)';
    ctx.beginPath();
    ctx.arc(centerX, wingY + wingH / 2, 120, 0, Math.PI * 2);
    ctx.stroke();

    ctx.font = 'bold 15px monospace';
    ctx.fillStyle = 'rgba(0, 242, 254, 0.6)';
    ctx.textAlign = 'center';
    ctx.fillText('SOVEREIGN CORE', centerX, wingY + wingH / 2 - 10);
    ctx.fillStyle = 'rgba(168, 85, 247, 0.8)';
    ctx.fillText('MR. FLOW v2.0', centerX, wingY + wingH / 2 + 15);
    ctx.textAlign = 'left';

    // 4. FOOTER STATUS BAR
    ctx.fillStyle = 'rgba(15, 23, 42, 0.96)';
    ctx.fillRect(24, 868, w - 48, 54);
    ctx.font = 'bold 16px monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText('MEMORY: .fl_brain • CIRCUIT BREAKER: 0/3 SECURE • SCRATCH: .FL_BIN/scratch/', 48, 902);
    ctx.fillStyle = '#22c55e';
    ctx.textAlign = 'right';
    ctx.fillText('● SYSTEM 60 FPS • ZERO LATENCY STREAMING', w - 48, 902);

    if (this.cotWallTexture) {
      this.cotWallTexture.needsUpdate = true;
    }
  }

  initAgentThoughtHUD() {
    this.thoughtCanvas = document.createElement('canvas');
    this.thoughtCanvas.width = 900;
    this.thoughtCanvas.height = 240;
    this.thoughtSpriteTexture = new THREE.CanvasTexture(this.thoughtCanvas);
    this.thoughtSpriteTexture.minFilter = THREE.LinearFilter;
    this.thoughtSpriteTexture.magFilter = THREE.LinearFilter;

    const spriteMat = new THREE.SpriteMaterial({
      map: this.thoughtSpriteTexture,
      transparent: true,
      depthTest: true,
    });
    this.agentThoughtSprite = new THREE.Sprite(spriteMat);
    this.agentThoughtSprite.scale.set(2.0, 0.48, 1);

    this.drawAgentThoughtHUD({
      reason: 'Sovereign Core Ready. Awaiting user prompt...',
      keywords: 'fl_soul, fl_brain, exit_code_0'
    });
  }

  drawAgentThoughtHUD(data = {}) {
    if (!this.thoughtCanvas) return;
    const ctx = this.thoughtCanvas.getContext('2d');
    const w = this.thoughtCanvas.width;
    const h = this.thoughtCanvas.height;

    ctx.clearRect(0, 0, w, h);

    // Glowing Pill Container
    ctx.fillStyle = 'rgba(7, 13, 24, 0.92)';
    ctx.strokeStyle = '#00f2fe';
    ctx.lineWidth = 4;
    ctx.shadowColor = '#00f2fe';
    ctx.shadowBlur = 16;
    ctx.beginPath();
    ctx.roundRect(10, 10, w - 20, h - 20, 24);
    ctx.fill();
    ctx.stroke();

    ctx.shadowBlur = 0; // reset shadow

    // Top Row: REASON
    ctx.font = 'bold 28px "Inter", "Segoe UI", sans-serif';
    ctx.fillStyle = '#38bdf8';
    ctx.textAlign = 'left';
    ctx.fillText('🧠 REASON:', 35, 68);
    const reasonLabelWidth = ctx.measureText('🧠 REASON:').width;

    ctx.font = '500 24px "Inter", "Segoe UI", sans-serif';
    ctx.fillStyle = '#ffffff';
    const reasonText = (data.reason || 'Sovereign Core Ready').slice(0, 48);
    ctx.fillText(reasonText, 50 + reasonLabelWidth, 68);

    // Divider Line
    ctx.strokeStyle = 'rgba(0, 242, 254, 0.25)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(35, 108);
    ctx.lineTo(w - 35, 108);
    ctx.stroke();

    // Bottom Row: KEYWORDS
    ctx.font = 'bold 24px "Inter", "Segoe UI", monospace';
    ctx.fillStyle = '#f59e0b';
    ctx.fillText('🏷️ KEYWORDS:', 35, 168);
    const kwLabelWidth = ctx.measureText('🏷️ KEYWORDS:').width;

    ctx.font = '500 22px monospace';
    ctx.fillStyle = '#34d399';
    const kwText = typeof data.keywords === 'string'
      ? data.keywords
      : (Array.isArray(data.keywords) ? data.keywords.join(', ') : 'fl_soul, fl_brain, exit_code_0');
    ctx.fillText(kwText.slice(0, 48), 50 + kwLabelWidth, 168);

    // Live status pulsing dot
    ctx.fillStyle = '#22c55e';
    ctx.beginPath();
    ctx.arc(w - 45, 58, 10, 0, Math.PI * 2);
    ctx.fill();

    if (this.thoughtSpriteTexture) {
      this.thoughtSpriteTexture.needsUpdate = true;
    }
  }

  updateAgentReasoning(data = {}) {
    this.drawAgentThoughtHUD(data);
    this.drawCotWall(data);
  }

  buildSoloExecutiveChair() {
    const chairGroup = new THREE.Group();
    chairGroup.name = 'SoloExecutiveChair';
    chairGroup.position.set(0, 0, 0.16); // Positioned directly behind Mr. Flow

    const chromeMat = new THREE.MeshStandardMaterial({
      color: 0xd1d5db,
      metalness: 0.95,
      roughness: 0.15,
    });
    const leatherMat = new THREE.MeshStandardMaterial({
      color: 0x070b14,
      roughness: 0.40,
      metalness: 0.25,
    });
    const pipingMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe });

    // 1. Chrome 5-star Caster Base on Floor
    const centerHub = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.14, 0.06, 16), chromeMat);
    centerHub.position.y = 0.06;
    chairGroup.add(centerHub);

    for (let i = 0; i < 5; i++) {
      const angle = (i * Math.PI * 2) / 5;
      const legMesh = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.04, 0.38), chromeMat);
      legMesh.position.set(Math.sin(angle) * 0.18, 0.05, Math.cos(angle) * 0.18);
      legMesh.rotation.y = angle;
      chairGroup.add(legMesh);

      // Mini caster wheel at end of leg
      const caster = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.03, 8), chromeMat);
      caster.rotation.z = Math.PI / 2;
      caster.position.set(Math.sin(angle) * 0.36, 0.03, Math.cos(angle) * 0.36);
      chairGroup.add(caster);
    }

    // 2. Heavy-Duty Chrome Hydraulic Cylinder Column
    const cylinder = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.045, 0.38, 16), chromeMat);
    cylinder.position.y = 0.24;
    chairGroup.add(cylinder);

    // 3. Ergonomic Contoured Seat Cushion
    const seatCushion = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.10, 0.64), leatherMat);
    seatCushion.position.set(0, 0.44, 0.02);
    chairGroup.add(seatCushion);

    // Glowing cyan piping under seat rim
    const seatRim = new THREE.Mesh(new THREE.BoxGeometry(0.73, 0.02, 0.65), pipingMat);
    seatRim.position.set(0, 0.42, 0.02);
    chairGroup.add(seatRim);

    // 4. Ergonomic High-Back Executive Backrest
    const backGroup = new THREE.Group();
    backGroup.position.set(0, 0.95, -0.26);
    backGroup.rotation.x = -0.06; // Slight executive recline angle

    // Main backrest cushion
    const backCushion = new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.96, 0.08), leatherMat);
    backGroup.add(backCushion);

    // Left and right side contour bolsters
    [-0.31, 0.31].forEach(bx => {
      const bolster = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.92, 0.12), leatherMat);
      bolster.position.set(bx, 0, 0.03);
      backGroup.add(bolster);
    });

    // Executive Headrest
    const headrest = new THREE.Mesh(new THREE.BoxGeometry(0.44, 0.22, 0.09), leatherMat);
    headrest.position.set(0, 0.58, 0.02);
    backGroup.add(headrest);

    // Chrome spine / mounting bracket behind backrest
    const spineMesh = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.05, 0.04), chromeMat);
    spineMesh.position.set(0, 0.08, -0.05);
    backGroup.add(spineMesh);

    // Flowork Sovereign Crest on Headrest
    const headrestEmblem = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.12, 0.02), pipingMat);
    headrestEmblem.position.set(0, 0.58, 0.07);
    backGroup.add(headrestEmblem);

    chairGroup.add(backGroup);

    // 5. Polished Chrome & Leather Armrests
    [-0.38, 0.38].forEach(ax => {
      const armSupport = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.24, 0.05), chromeMat);
      armSupport.position.set(ax, 0.58, 0.05);
      chairGroup.add(armSupport);

      const armPad = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.04, 0.40), leatherMat);
      armPad.position.set(ax, 0.70, 0.06);
      chairGroup.add(armPad);
    });

    return chairGroup;
  }

  buildModernCorporateOffice() {
    const officeGroup = new THREE.Group();
    officeGroup.name = 'ModernCorporateOffice';

    // 1. REALISTIC OFFICE PARQUET FLOOR (Warm European Oak / Honey Walnut)
    const floorGeo = new THREE.PlaneGeometry(32, 28);
    const floorCanvas = document.createElement('canvas');
    floorCanvas.width = 1024;
    floorCanvas.height = 1024;
    const fCtx = floorCanvas.getContext('2d');

    // Base tone: rich honey-warm oak
    fCtx.fillStyle = '#6b4728';
    fCtx.fillRect(0, 0, 1024, 1024);

    // Procedural Wood Parquet Planks
    const plankW = 128;
    const plankH = 32;
    const tones = ['#754f2e', '#6e4827', '#7b5331', '#664223', '#7f5835'];

    for (let y = 0; y < 1024; y += plankH) {
      const offsetX = (Math.floor(y / plankH) % 2 === 0) ? 0 : (plankW / 2);
      for (let x = -plankW; x < 1024 + plankW; x += plankW) {
        const tone = tones[Math.abs(Math.floor(Math.sin(x * 12.3 + y * 7.9) * 10)) % tones.length];
        fCtx.fillStyle = tone;
        fCtx.fillRect(x + offsetX + 1, y + 1, plankW - 2, plankH - 2);

        // Subtle wood grain lines
        fCtx.strokeStyle = 'rgba(0, 0, 0, 0.08)';
        fCtx.lineWidth = 1;
        fCtx.beginPath();
        fCtx.moveTo(x + offsetX + 2, y + 10);
        fCtx.lineTo(x + offsetX + plankW - 2, y + 12);
        fCtx.stroke();
        fCtx.beginPath();
        fCtx.moveTo(x + offsetX + 2, y + 22);
        fCtx.lineTo(x + offsetX + plankW - 2, y + 20);
        fCtx.stroke();
      }
    }

    // Modern Brass Perimeter Inlay Runner
    fCtx.strokeStyle = 'rgba(212, 175, 55, 0.45)';
    fCtx.lineWidth = 6;
    fCtx.strokeRect(40, 40, 944, 944);

    const floorTex = new THREE.CanvasTexture(floorCanvas);
    floorTex.wrapS = THREE.RepeatWrapping;
    floorTex.wrapT = THREE.RepeatWrapping;
    floorTex.repeat.set(2, 2);

    const floorMat = new THREE.MeshStandardMaterial({
      map: floorTex,
      roughness: 0.38,
      metalness: 0.12,
    });
    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
    floorMesh.rotation.x = -Math.PI / 2;
    floorMesh.position.set(0, 0, 3.0);
    floorMesh.userData = { isFloor: true };
    this.floorMesh = floorMesh;
    officeGroup.add(floorMesh);

    // Dynamic Navigation Markers
    const ringGeo = new THREE.RingGeometry(0.55, 0.76, 32);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe, side: THREE.DoubleSide, transparent: true, opacity: 0.88, depthWrite: false });
    this.selectionRing = new THREE.Mesh(ringGeo, ringMat);
    this.selectionRing.rotation.x = -Math.PI / 2;
    this.selectionRing.position.y = 0.02;
    this.selectionRing.visible = false;
    officeGroup.add(this.selectionRing);

    // 2. NORTH WALL (Executive Walnut Slat Wall, Logo, Sprint Board, Clock)
    const wallGeo = new THREE.BoxGeometry(32, 6.4, 0.4);
    const wallMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.65, metalness: 0.15 });
    const backWall = new THREE.Mesh(wallGeo, wallMat);
    backWall.position.set(0, 3.2, -5.8);
    officeGroup.add(backWall);

    // Real 3D Warm Oak Acoustic Wood Slats
    const slatMat = new THREE.MeshStandardMaterial({ color: 0xb45309, roughness: 0.42, metalness: 0.08 });
    for (let sx = -15.2; sx <= 15.2; sx += 0.48) {
      if (sx > -4.5 && sx < 4.5) continue; // Leave center space for 3D corporate logo plaque
      const slat = new THREE.Mesh(new THREE.BoxGeometry(0.20, 6.0, 0.10), slatMat);
      slat.position.set(sx, 3.2, -5.62);
      officeGroup.add(slat);
    }

    // Center Illuminated Corporate Signage Plaque
    const plaqueBackdrop = new THREE.Mesh(
      new THREE.BoxGeometry(8.6, 2.4, 0.12),
      new THREE.MeshStandardMaterial({ color: 0x0c1322, roughness: 0.4, metalness: 0.6 })
    );
    plaqueBackdrop.position.set(0, 4.4, -5.65);
    officeGroup.add(plaqueBackdrop);

    // Sign Face Canvas (High Resolution Flowork Headquarters Branding)
    const signCanvas = document.createElement('canvas');
    signCanvas.width = 1024;
    signCanvas.height = 256;
    const sCtx = signCanvas.getContext('2d');
    sCtx.fillStyle = '#080e1a';
    sCtx.fillRect(0, 0, 1024, 256);

    // Subtle neon border
    sCtx.strokeStyle = '#00f2fe';
    sCtx.lineWidth = 4;
    sCtx.strokeRect(8, 8, 1008, 240);

    // Title
    sCtx.font = '900 68px system-ui, -apple-system, sans-serif';
    sCtx.fillStyle = '#ffffff';
    sCtx.textAlign = 'center';
    sCtx.fillText('⚡ FLOWORK OS ⚡', 512, 105);

    // Subtitle
    sCtx.font = '700 24px monospace';
    sCtx.fillStyle = '#38bdf8';
    sCtx.letterSpacing = '4px';
    sCtx.fillText('AUTONOMOUS AGENT HEADQUARTERS // ZERO-TRUST LAB', 512, 168);

    sCtx.font = '600 16px monospace';
    sCtx.fillStyle = '#10b981';
    sCtx.fillText('STATUS: ONLINE • ALL ENGINES ARMED • VERIFIED EXIT CODE 0', 512, 212);

    const signTex = new THREE.CanvasTexture(signCanvas);
    const signMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(8.4, 2.2),
      new THREE.MeshBasicMaterial({ map: signTex })
    );
    signMesh.position.set(0, 4.4, -5.58);
    officeGroup.add(signMesh);

    // LED Backlight Glow Rim around Plaque
    const plaqueGlow = new THREE.PointLight(0x00f2fe, 2.4, 8, 1.8);
    plaqueGlow.position.set(0, 4.4, -5.3);
    officeGroup.add(plaqueGlow);

    // Frosted Glass Agile Kanban Sprint Whiteboard (Left of center at X = -7.4)
    const boardGroup = new THREE.Group();
    boardGroup.position.set(-7.4, 3.2, -5.62);

    const boardFrame = new THREE.Mesh(
      new THREE.BoxGeometry(5.4, 2.8, 0.08),
      new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.8, roughness: 0.2 })
    );
    boardGroup.add(boardFrame);

    // Whiteboard Canvas
    const wbCanvas = document.createElement('canvas');
    wbCanvas.width = 1024;
    wbCanvas.height = 512;
    const wbCtx = wbCanvas.getContext('2d');

    // Translucent frosted glass look
    wbCtx.fillStyle = 'rgba(241, 245, 249, 0.94)';
    wbCtx.fillRect(0, 0, 1024, 512);

    // Header
    wbCtx.fillStyle = '#0f172a';
    wbCtx.font = 'bold 28px sans-serif';
    wbCtx.fillText('📋 SPRINT ARCHITECTURE & ACTIVE WORKFLOWS', 30, 48);

    // Columns
    const cols = [
      { name: 'BACKLOG', x: 30, color: '#64748b' },
      { name: 'IN PROGRESS', x: 275, color: '#0284c7' },
      { name: 'CODE REVIEW (@LOCK)', x: 520, color: '#d97706' },
      { name: 'EXIT CODE 0 (DONE)', x: 765, color: '#059669' }
    ];

    cols.forEach(c => {
      wbCtx.fillStyle = c.color;
      wbCtx.font = 'bold 18px monospace';
      wbCtx.fillText(c.name, c.x, 90);
      wbCtx.strokeStyle = 'rgba(100, 116, 139, 0.3)';
      wbCtx.lineWidth = 2;
      wbCtx.beginPath(); wbCtx.moveTo(c.x, 102); wbCtx.lineTo(c.x + 210, 102); wbCtx.stroke();
    });

    // Sticky Notes
    const stickyNotes = [
      { text: 'Nano-Modular Core', col: 0, y: 125, bg: '#fef08a' },
      { text: 'Agnostic Manifest', col: 0, y: 220, bg: '#bae6fd' },
      { text: 'Live Trajectory DAG', col: 1, y: 125, bg: '#fed7aa' },
      { text: 'Chibi 3D Mascots', col: 1, y: 220, bg: '#bbf7d0' },
      { text: 'Anti-Zombie IPC', col: 2, y: 125, bg: '#fbcfe8' },
      { text: 'Security Gate Lock', col: 2, y: 220, bg: '#fef08a' },
      { text: 'Axum Port Routing', col: 3, y: 125, bg: '#bbf7d0' },
      { text: 'Multi-OS Binaries', col: 3, y: 220, bg: '#bae6fd' },
      { text: 'Exit Code 0 Verified', col: 3, y: 315, bg: '#bbf7d0' },
    ];

    stickyNotes.forEach(sn => {
      const sx = cols[sn.col].x + 5;
      const sy = sn.y;
      wbCtx.fillStyle = sn.bg;
      wbCtx.shadowColor = 'rgba(0,0,0,0.15)';
      wbCtx.shadowBlur = 6;
      wbCtx.fillRect(sx, sy, 200, 75);
      wbCtx.shadowColor = 'transparent';
      wbCtx.fillStyle = '#0f172a';
      wbCtx.font = 'bold 14px sans-serif';
      wbCtx.fillText(sn.text, sx + 12, sy + 35);
      wbCtx.font = '11px monospace';
      wbCtx.fillStyle = '#475569';
      wbCtx.fillText('✓ Autonomous Task', sx + 12, sy + 55);
    });

    const wbTex = new THREE.CanvasTexture(wbCanvas);
    const wbMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(5.2, 2.6),
      new THREE.MeshBasicMaterial({ map: wbTex })
    );
    wbMesh.position.z = 0.05;
    boardGroup.add(wbMesh);
    officeGroup.add(boardGroup);

    // Architectural Office Wall Clock (Right of center at X = 7.4, Y = 4.4)
    const clockGroup = new THREE.Group();
    clockGroup.position.set(7.4, 4.4, -5.62);

    const clockFrame = new THREE.Mesh(
      new THREE.CylinderGeometry(0.55, 0.55, 0.08, 32),
      new THREE.MeshStandardMaterial({ color: 0xd4af37, metalness: 0.85, roughness: 0.2 })
    );
    clockFrame.rotation.x = Math.PI / 2;
    clockGroup.add(clockFrame);

    // Clock Face
    const cCanvas = document.createElement('canvas');
    cCanvas.width = 256; cCanvas.height = 256;
    const cCtx = cCanvas.getContext('2d');
    cCtx.fillStyle = '#ffffff';
    cCtx.beginPath(); cCtx.arc(128, 128, 120, 0, Math.PI * 2); cCtx.fill();
    cCtx.strokeStyle = '#0f172a'; cCtx.lineWidth = 6; cCtx.stroke();
    for (let h = 0; h < 12; h++) {
      const rad = (h / 12) * Math.PI * 2;
      cCtx.strokeStyle = '#0f172a';
      cCtx.lineWidth = (h % 3 === 0) ? 6 : 3;
      cCtx.beginPath();
      cCtx.moveTo(128 + Math.sin(rad) * 95, 128 - Math.cos(rad) * 95);
      cCtx.lineTo(128 + Math.sin(rad) * 112, 128 - Math.cos(rad) * 112);
      cCtx.stroke();
    }
    const cTex = new THREE.CanvasTexture(cCanvas);
    const clockFace = new THREE.Mesh(new THREE.CircleGeometry(0.50, 32), new THREE.MeshBasicMaterial({ map: cTex }));
    clockFace.position.z = 0.045;
    clockGroup.add(clockFace);

    // Clock Hands
    const hourHand = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.26, 0.01), new THREE.MeshBasicMaterial({ color: 0x0f172a }));
    hourHand.position.set(0, 0.10, 0.05);
    hourHand.rotation.z = -Math.PI / 3;
    clockGroup.add(hourHand);

    const minHand = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.38, 0.01), new THREE.MeshBasicMaterial({ color: 0x0f172a }));
    minHand.position.set(0, 0.16, 0.055);
    minHand.rotation.z = Math.PI / 4;
    clockGroup.add(minHand);

    const secHand = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.42, 0.01), new THREE.MeshBasicMaterial({ color: 0xef4444 }));
    secHand.position.set(0, 0.18, 0.06);
    clockGroup.add(secHand);
    this.wallClockSecondHand = secHand;

    officeGroup.add(clockGroup);

    // Warm Architectural Cove Lighting along top of back wall
    const coveLight = new THREE.Mesh(
      new THREE.BoxGeometry(32, 0.08, 0.12),
      new THREE.MeshBasicMaterial({ color: 0xffedd5 })
    );
    coveLight.position.set(0, 6.35, -5.60);
    officeGroup.add(coveLight);

    // 3. WEST WALL: FLOOR-TO-CEILING PANORAMIC CITY SKYLINE WINDOWS
    const westWallGroup = new THREE.Group();
    westWallGroup.position.set(-15.8, 0, 3.0);

    // Floor-to-ceiling glass panel
    const winGlassMat = new THREE.MeshStandardMaterial({
      color: 0x0d1e38,
      transparent: true,
      opacity: 0.32,
      roughness: 0.06,
      metalness: 0.92,
      side: THREE.DoubleSide
    });
    const winGlass = new THREE.Mesh(new THREE.PlaneGeometry(28, 6.4), winGlassMat);
    winGlass.rotation.y = Math.PI / 2;
    winGlass.position.set(0, 3.2, 0);
    westWallGroup.add(winGlass);

    // Architectural Window Mullions (Matte black aluminum steel frame)
    const mullionMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.85, roughness: 0.25 });
    for (let mz = -13; mz <= 13; mz += 3.5) {
      const mullion = new THREE.Mesh(new THREE.BoxGeometry(0.18, 6.4, 0.14), mullionMat);
      mullion.position.set(0, 3.2, mz);
      westWallGroup.add(mullion);
    }
    // Horizontal Transom Bars
    [1.8, 4.2].forEach(ty => {
      const transom = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.12, 28), mullionMat);
      transom.position.set(0, ty, 0);
      westWallGroup.add(transom);
    });

    // Metropolitan High-Rise Skyline Backdrop Canvas
    const skyCanvas = document.createElement('canvas');
    skyCanvas.width = 1024;
    skyCanvas.height = 512;
    const skyCtx = skyCanvas.getContext('2d');

    // Daylight to Golden Hour Atmospheric Horizon Gradient
    const skyGrad = skyCtx.createLinearGradient(0, 0, 0, 512);
    skyGrad.addColorStop(0, '#0f2b5c');
    skyGrad.addColorStop(0.45, '#1e40af');
    skyGrad.addColorStop(0.75, '#f59e0b');
    skyGrad.addColorStop(1, '#ffedd5');
    skyCtx.fillStyle = skyGrad;
    skyCtx.fillRect(0, 0, 1024, 512);

    // Skyscraper Silhouettes with Lit Window Grids
    const towers = [
      { x: 30, w: 90, h: 360, col: '#0a101d' },
      { x: 135, w: 120, h: 440, col: '#060b14' },
      { x: 270, w: 80, h: 320, col: '#0f172a' },
      { x: 365, w: 130, h: 490, col: '#050912' },
      { x: 510, w: 95, h: 380, col: '#090e18' },
      { x: 620, w: 140, h: 460, col: '#060c16' },
      { x: 775, w: 105, h: 350, col: '#0e1626' },
      { x: 895, w: 115, h: 420, col: '#070d19' },
    ];

    towers.forEach(t => {
      skyCtx.fillStyle = t.col;
      skyCtx.fillRect(t.x, 512 - t.h, t.w, t.h);

      // Lit Office Window Dots
      for (let wy = 512 - t.h + 20; wy < 490; wy += 18) {
        for (let wx = t.x + 10; wx < t.x + t.w - 10; wx += 14) {
          if ((wx * 13 + wy * 17) % 7 !== 0) {
            skyCtx.fillStyle = ((wx + wy) % 5 === 0) ? '#fef08a' : '#93c5fd';
            skyCtx.fillRect(wx, wy, 6, 9);
          }
        }
      }

      // Tower Antenna Beacons
      skyCtx.strokeStyle = '#475569';
      skyCtx.lineWidth = 2;
      skyCtx.beginPath();
      skyCtx.moveTo(t.x + t.w / 2, 512 - t.h);
      skyCtx.lineTo(t.x + t.w / 2, 512 - t.h - 35);
      skyCtx.stroke();
      skyCtx.fillStyle = '#ef4444';
      skyCtx.fillRect(t.x + t.w / 2 - 2, 512 - t.h - 37, 4, 4);
    });

    const skyTex = new THREE.CanvasTexture(skyCanvas);
    const skyBackdrop = new THREE.Mesh(
      new THREE.PlaneGeometry(36, 12),
      new THREE.MeshBasicMaterial({ map: skyTex, side: THREE.DoubleSide })
    );
    skyBackdrop.rotation.y = Math.PI / 2;
    skyBackdrop.position.set(-6.5, 4.0, 0);
    westWallGroup.add(skyBackdrop);

    officeGroup.add(westWallGroup);

    // 4. EAST WALL (Bookshelf Credenza, Server Hardware, Coffee & Pantry Station)
    const eastWallGroup = new THREE.Group();
    eastWallGroup.position.set(15.8, 0, 3.0);

    const eastWall = new THREE.Mesh(
      new THREE.BoxGeometry(0.4, 6.4, 28),
      new THREE.MeshStandardMaterial({ color: 0x18202e, roughness: 0.65, metalness: 0.15 })
    );
    eastWall.position.set(0, 3.2, 0);
    eastWallGroup.add(eastWall);

    // Modern Modular Walnut Bookshelf Credenza (Z = -4.0 to 1.0)
    const shelfGroup = new THREE.Group();
    shelfGroup.position.set(-0.45, 0, -2.0);

    const shelfFrameMat = this.sharedMaterials ? this.sharedMaterials.walnutWoodMat : new THREE.MeshStandardMaterial({ color: 0x241711, roughness: 0.5 });
    const shelfBack = new THREE.Mesh(new THREE.BoxGeometry(0.12, 4.4, 5.0), shelfFrameMat);
    shelfBack.position.set(0.15, 2.2, 0);
    shelfGroup.add(shelfBack);

    // Shelves
    [0.1, 1.1, 2.1, 3.1, 4.1].forEach(sy => {
      const shelfPlank = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.06, 5.0), shelfFrameMat);
      shelfPlank.position.set(-0.2, sy, 0);
      shelfGroup.add(shelfPlank);
    });

    // Books, Binders & Server Hardware on shelves
    const bookColors = [0x38bdf8, 0xf59e0b, 0x10b981, 0xa855f7, 0xef4444, 0x475569];
    for (let sz = -2.1; sz <= 2.1; sz += 0.8) {
      const bookStack = new THREE.Mesh(
        new THREE.BoxGeometry(0.35, 0.45, 0.60),
        new THREE.MeshStandardMaterial({ color: bookColors[Math.abs(Math.floor(sz * 5)) % bookColors.length], roughness: 0.4 })
      );
      bookStack.position.set(-0.18, 1.35, sz);
      shelfGroup.add(bookStack);
    }

    // 2U Server Chassis Units with live blinking status LEDs
    [-0.8, 0.8].forEach(srvZ => {
      const srvChassis = new THREE.Mesh(
        new THREE.BoxGeometry(0.45, 0.28, 0.85),
        new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9, roughness: 0.2 })
      );
      srvChassis.position.set(-0.2, 2.30, srvZ);
      shelfGroup.add(srvChassis);

      // Blinking LEDs
      const ledMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
      const ledMesh = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.04, 0.12), ledMat);
      ledMesh.position.set(-0.44, 2.30, srvZ);
      shelfGroup.add(ledMesh);
      this.serverLeds.push(ledMesh);
    });

    eastWallGroup.add(shelfGroup);

    // Refreshment Pantry / Coffee Corner Station (Z = 5.0 to 8.5)
    const pantryGroup = new THREE.Group();
    pantryGroup.position.set(-0.6, 0, 6.5);

    // White Quartz Counter
    const counterMat = new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.15, metalness: 0.2 });
    const counterTop = new THREE.Mesh(new THREE.BoxGeometry(0.85, 0.08, 3.2), counterMat);
    counterTop.position.set(0, 0.95, 0);
    pantryGroup.add(counterTop);

    // Walnut Cabinet Base
    const cabinetBase = new THREE.Mesh(new THREE.BoxGeometry(0.80, 0.91, 3.1), shelfFrameMat);
    cabinetBase.position.set(0, 0.455, 0);
    pantryGroup.add(cabinetBase);

    // Espresso Machine
    const espressoGroup = new THREE.Group();
    espressoGroup.position.set(0, 0.99, -0.6);
    const espBody = new THREE.Mesh(
      new THREE.BoxGeometry(0.42, 0.42, 0.48),
      new THREE.MeshStandardMaterial({ color: 0xd4af37, metalness: 0.85, roughness: 0.2 })
    );
    espBody.position.y = 0.21;
    espressoGroup.add(espBody);
    pantryGroup.add(espressoGroup);

    // Coffee Mugs
    const mugMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, roughness: 0.3 });
    [-0.15, 0.15].forEach(mx => {
      const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.045, 0.12, 16), mugMat);
      mug.position.set(mx, 1.05, 0.1);
      pantryGroup.add(mug);
    });

    // Office Water Cooler with blue water bottle
    const coolerGroup = new THREE.Group();
    coolerGroup.position.set(0, 0, 1.2);
    const coolerBody = new THREE.Mesh(
      new THREE.BoxGeometry(0.38, 1.05, 0.38),
      new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.25 })
    );
    coolerBody.position.y = 0.525;
    coolerGroup.add(coolerBody);

    const waterBottle = new THREE.Mesh(
      new THREE.CylinderGeometry(0.14, 0.14, 0.48, 16),
      new THREE.MeshStandardMaterial({ color: 0x0284c7, transparent: true, opacity: 0.65, roughness: 0.1 })
    );
    waterBottle.position.y = 1.25;
    coolerGroup.add(waterBottle);
    pantryGroup.add(coolerGroup);

    eastWallGroup.add(pantryGroup);
    officeGroup.add(eastWallGroup);

    // 5. CEILING WITH RECESSED LINEAR LED LIGHT TROFFERS
    const ceilingGeo = new THREE.PlaneGeometry(32, 28);
    const ceilingMat = new THREE.MeshStandardMaterial({ color: 0x1e2634, roughness: 0.6, metalness: 0.2, side: THREE.DoubleSide });
    const ceiling = new THREE.Mesh(ceilingGeo, ceilingMat);
    ceiling.rotation.x = Math.PI / 2;
    ceiling.position.set(0, 6.4, 3.0);
    officeGroup.add(ceiling);

    // Recessed 4000K LED Troffer Panels
    [-6.5, 0, 6.5].forEach(tx => {
      [-1.5, 3.5, 8.5].forEach(tz => {
        const troffer = new THREE.Mesh(
          new THREE.PlaneGeometry(3.2, 0.45),
          new THREE.MeshBasicMaterial({ color: 0xfffcf0, side: THREE.DoubleSide })
        );
        troffer.rotation.x = Math.PI / 2;
        troffer.position.set(tx, 6.38, tz);
        officeGroup.add(troffer);
      });
    });

    // 6. LUSH INDOOR OFFICE PLANTS (Monstera Deliciosa & Snake Plants)
    const plantLocations = [
      { x: -11.5, z: -4.5, type: 'monstera' },
      { x: 11.5, z: -4.5, type: 'monstera' },
      { x: -11.5, z: 12.0, type: 'ficus' },
      { x: 11.5, z: 12.0, type: 'ficus' },
      { x: -2.8, z: 5.5, type: 'snake' },
      { x: 2.8, z: 5.5, type: 'snake' }
    ];

    plantLocations.forEach(p => {
      const potGroup = new THREE.Group();
      potGroup.position.set(p.x, 0, p.z);

      // Ceramic Cylinder Pot
      const potMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.25, metalness: 0.1 });
      const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.26, 0.65, 24), potMat);
      pot.position.y = 0.325;
      potGroup.add(pot);

      // Soil
      const soil = new THREE.Mesh(
        new THREE.CylinderGeometry(0.30, 0.30, 0.05, 24),
        new THREE.MeshStandardMaterial({ color: 0x271911, roughness: 0.9 })
      );
      soil.position.y = 0.63;
      potGroup.add(soil);

      // Leaves
      const leafMat = new THREE.MeshStandardMaterial({
        color: 0x166534, // Vibrant natural Monstera green
        roughness: 0.35,
        metalness: 0.05,
        side: THREE.DoubleSide
      });

      for (let l = 0; l < 8; l++) {
        const lAngle = (l / 8) * Math.PI * 2;
        const leafStem = new THREE.Mesh(
          new THREE.CylinderGeometry(0.015, 0.02, 0.65, 8),
          new THREE.MeshStandardMaterial({ color: 0x15803d })
        );
        leafStem.position.set(Math.sin(lAngle) * 0.12, 0.85, Math.cos(lAngle) * 0.12);
        leafStem.rotation.x = Math.cos(lAngle) * 0.45;
        leafStem.rotation.z = -Math.sin(lAngle) * 0.45;

        const leafBlade = new THREE.Mesh(new THREE.SphereGeometry(0.24, 8, 8), leafMat);
        leafBlade.scale.set(1.0, 0.12, 1.6);
        leafBlade.position.y = 0.35;
        leafStem.add(leafBlade);
        potGroup.add(leafStem);
      }

      officeGroup.add(potGroup);
    });

    this.environmentGroup.add(officeGroup);
  }

  async loadPersonas() {
    try {
      let agents = [];
      // 1. Fetch from /api/agents or /api/personas
      try {
        let res = await fetch('/api/agents');
        if (!res.ok) res = await fetch('/api/personas');
        if (res.ok) {
          const data = await res.json();
          const list = data && (Array.isArray(data.agents) ? data.agents : (Array.isArray(data.personas) ? data.personas : null));
          if (list && list.length > 0) agents = list;
        }
      } catch (_) {}

      // 2. Fetch from /api/subagents to capture disk-based subagents
      try {
        let res2 = await fetch('/api/subagents');
        if (res2.ok) {
          const data2 = await res2.json();
          if (data2 && Array.isArray(data2.subagents)) {
            data2.subagents.forEach(sa => {
              if (sa && sa.id && !agents.some(a => a.id === sa.id)) {
                agents.push(sa);
              }
            });
          }
        }
      } catch (_) {}

      if (!agents.length && window.AVAILABLE_PERSONAS && window.AVAILABLE_PERSONAS.length > 0) {
        agents = window.AVAILABLE_PERSONAS;
      }

      if (!agents.length) {
        agents = [
          { id: 'leader', name: 'Swarm Leader', role: 'Swarm Leader & Group Mode Orchestrator', icon: '👑', is_default: false },
          { id: 'mr.flow', name: 'Mr. Flow', role: 'Sovereign Solo Executive Agent', icon: '⚡', is_default: true },
          { id: 'security-auditor', name: 'Security Auditor', role: 'Offensive & Defensive Security Specialist', icon: '🛡️' },
          { id: 'quality-control', name: 'Quality Control', role: 'Logic, QA & Invariant Validator', icon: '🧪' },
          { id: 'backend-engineer', name: 'Backend Engineer', role: 'Backend & Systems Specialist', icon: '⚙️' },
          { id: 'frontend-engineer', name: 'Frontend Engineer', role: 'UI/UX & Canvas Architecture Specialist', icon: '🎨' }
        ];
      }

      const cleanRoster = agents.filter(p => p && p.id && p.id.toLowerCase() !== 'default');
      window.AVAILABLE_PERSONAS = cleanRoster;
      this.syncPersonas(cleanRoster);

      // Record fingerprint
      this._lastRosterFingerprint = cleanRoster.map(a => `${a.id}:${a.name || ''}:${a.role || ''}`).sort().join('||');
    } catch (err) {
      console.warn('[Office 3D] Failed to fetch agents:', err);
    }
  }

  startRosterWatcher() {
    if (this._rosterWatcherInterval) clearInterval(this._rosterWatcherInterval);
    // Poll disk & backend every 3 seconds for added or removed agents
    this._rosterWatcherInterval = setInterval(async () => {
      if (document.hidden || !this.isRunning) return;
      await this.checkRosterChanges();
    }, 3000);

    // Event hooks for instant UI reactivity
    if (!this._boundRosterEvents) {
      this._boundRosterEvents = true;
      window.addEventListener('flowork:subagent-updated', () => this.checkRosterChanges());
      window.addEventListener('flowork:agents-changed', () => this.checkRosterChanges());
      window.addEventListener('focus', () => this.checkRosterChanges());
      window.syncOffice3DAgents = (list) => {
        if (Array.isArray(list) && list.length > 0) {
          this.syncPersonas(list);
        } else {
          this.checkRosterChanges();
        }
      };
    }
  }

  async checkRosterChanges() {
    try {
      let agents = [];
      try {
        let res = await fetch('/api/agents');
        if (!res.ok) res = await fetch('/api/personas');
        if (res.ok) {
          const data = await res.json();
          const list = data && (Array.isArray(data.agents) ? data.agents : (Array.isArray(data.personas) ? data.personas : null));
          if (list && list.length > 0) agents = list;
        }
      } catch (_) {}

      try {
        let res2 = await fetch('/api/subagents');
        if (res2.ok) {
          const data2 = await res2.json();
          if (data2 && Array.isArray(data2.subagents)) {
            data2.subagents.forEach(sa => {
              if (sa && sa.id && !agents.some(a => a.id === sa.id)) {
                agents.push(sa);
              }
            });
          }
        }
      } catch (_) {}

      if (!agents.length) return;
      const clean = agents.filter(p => p && p.id && p.id.toLowerCase() !== 'default');
      const currentFingerprint = clean.map(a => `${a.id}:${a.name || ''}:${a.role || ''}`).sort().join('||');

      if (!this._lastRosterFingerprint || this._lastRosterFingerprint !== currentFingerprint) {
        if (this._lastRosterFingerprint) {
          console.log('[Office 3D] ⚡ Dynamic Agent update detected! Auto-syncing 3D Office...');
        }
        window.AVAILABLE_PERSONAS = clean;
        this.syncPersonas(clean);
        this._lastRosterFingerprint = currentFingerprint;
      }
    } catch (_) {}
  }

  getAgentRegistry() {
    try {
      const raw = localStorage.getItem('xflow_office_agents');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (_) {}
    return null;
  }

  saveAgentRegistry(roster) {
    try {
      const cleanData = roster.map((a) => ({
        id: a.id,
        name: a.name,
        role: a.role,
        sessionId: a.sessionId,
        persona: a.persona,
        icon: a.icon,
        model: a.model,
        provider: a.provider || 'google',
        account: a.account || 'combo',
        state: 'idle',
      }));
      localStorage.setItem('xflow_office_agents', JSON.stringify(cleanData));
    } catch (_) {}
  }

  syncPersonas(personaList) {
    if (!personaList || !Array.isArray(personaList) || personaList.length === 0) {
      personaList = (window.AVAILABLE_PERSONAS && Array.isArray(window.AVAILABLE_PERSONAS) && window.AVAILABLE_PERSONAS.length > 0)
        ? window.AVAILABLE_PERSONAS
        : [
            { id: 'mr.flow', name: 'Mr. Flow', role: 'Sovereign Solo Executive Agent', icon: '⚡', is_default: true }
          ];
    }

    const cleanList = personaList.filter(p => p && p.id && p.id.toLowerCase() !== 'default');

    // Sort: Mr. Flow strictly at index 0 (Executive Desk), followed by Swarm Leader, then specialists
    const sorted = [...cleanList].sort((a, b) => {
      const aCore = a.id === 'mr.flow' || a.id === 'mrflow' || a.is_default;
      const bCore = b.id === 'mr.flow' || b.id === 'mrflow' || b.is_default;
      if (aCore) return -1;
      if (bCore) return 1;
      const aLeader = a.id === 'leader';
      const bLeader = b.id === 'leader';
      if (aLeader) return -1;
      if (bLeader) return 1;
      return (a.name || a.id).localeCompare(b.name || b.id);
    });

    const existingStates = new Map();
    if (this.agents && this.agents.length > 0) {
      this.agents.forEach(ag => {
        if (ag.data && ag.data.persona) {
          existingStates.set(ag.data.persona, ag.data.state);
        }
      });
    }

    // Build Roster with Procedural Modern Office Desks
    const newRoster = sorted.map((p, idx) => {
      const isCore = p.id === 'mr.flow' || p.id === 'mrflow' || p.is_default;
      const color = PERSONA_PALETTE[idx % PERSONA_PALETTE.length];
      const agentId = 'agent-' + p.id;
      const existingState = existingStates.get(p.id) || 'idle';

      let deskPos, deskFacingAngle;
      if (idx === 0) {
        // Executive Command Station (Mr. Flow) centered on executive dais at front of room
        deskPos = new THREE.Vector3(0, 0.22, -3.6);
        deskFacingAngle = 0; // Faces forward into the room
      } else {
        // Specialist Team Workstations: 3 Desks across (3 baris), widens horizontally ("melebar") when team grows!
        const specialistsCount = sorted.length - 1;
        const cols = Math.max(3, Math.ceil(specialistsCount / 3));
        const teamIdx = idx - 1;
        const row = Math.floor(teamIdx / cols);
        const colInRow = teamIdx % cols;
        const startOfRow = row * cols;
        const countInThisRow = Math.min(cols, specialistsCount - startOfRow);

        // Symmetric horizontal layout across office floor
        const xSpacing = Math.min(4.90, 25.0 / Math.max(1, cols - 1));
        let col = colInRow;
        // If this row has 2 desks in a 3-column layout, distribute them symmetrically to left and right wings
        if (cols === 3 && countInThisRow === 2) {
          col = colInRow === 0 ? 0 : 2;
        }
        const xPos = (col - (cols - 1) / 2) * xSpacing;
        const zPos = -0.50 + (row * 2.70);
        deskPos = new THREE.Vector3(xPos, 0, zPos);
        // Slightly angled toward room center
        deskFacingAngle = -xPos * 0.016;
      }

      return {
        id: agentId,
        name: p.name || p.id,
        role: p.role || p.description || 'Specialist Autonomous Agent',
        sessionId: 'session-' + p.id,
        persona: p.id,
        icon: p.icon || (isCore ? '⚡' : '🤖'),
        model: localStorage.getItem('xflow_chat_model') || 'gemini-3.8-flash-high',
        provider: 'sovereign',
        account: 'combo',
        color: isCore ? 0x00f2fe : color,
        isBoss: p.id === 'leader',
        isTrainer: isCore,
        deskPos,
        deskFacingAngle,
        standbyPos: deskPos.clone(),
        standbyFacingAngle: deskFacingAngle,
        steppedPos: deskPos.clone(),
        state: existingState,
        typingPhase: idx * 1.3,
      };
    });

    this.agentRoster = newRoster;
    this.saveAgentRegistry(this.agentRoster);
    this._lastRosterFingerprint = cleanList.map(a => `${a.id}:${a.name || ''}:${a.role || ''}`).sort().join('||');
    this.rebuildOfficeEntities();

    if (typeof window.renderOfficeAgentDock === 'function') {
      window.renderOfficeAgentDock();
    }
  }

  syncUserIdentity(user) {
    if (!user) return;
    const emojiMatch = (user.badge || '').match(/^(\p{Emoji})/u);
    const bossIcon = emojiMatch ? emojiMatch[1] : ((user.role === 'SUPER_ADMIN' || (user.level && user.level >= 90)) ? '👑' : '👤');
    const bossName = user.name || user.username || 'Commander';
    const bossRole = user.rank || user.level_name || (user.role ? `${user.role} • LV ${user.level || 1}` : '👑 Sovereign Master & Supreme Leader');

    if (Array.isArray(this.agentRoster)) {
      const boss = this.agentRoster.find(a => a.isBoss);
      if (boss) {
        boss.name = bossName;
        boss.role = bossRole;
        boss.icon = bossIcon;
      }
    }
    if (Array.isArray(this.agents)) {
      const bossAgent = this.agents.find(a => a.data && a.data.isBoss);
      if (bossAgent) {
        bossAgent.data.name = bossName;
        bossAgent.data.role = bossRole;
        bossAgent.data.icon = bossIcon;
        if (bossAgent.badgeTexture && bossAgent.badgeCtx) {
          this.drawBadge(bossAgent.badgeCtx, bossAgent.data);
          bossAgent.badgeTexture.needsUpdate = true;
        }
      }
    }
    if (typeof window.renderOfficeAgentDock === 'function') {
      window.renderOfficeAgentDock();
    }
  }

  rebuildOfficeEntities() {
    if (!this.workstationsGroup) return;

    // Safely dispose old agent resources
    if (this.agents && this.agents.length > 0) {
      this.agents.forEach((ag) => {
        if (ag.badgeSprite && ag.badgeSprite.material) {
          if (ag.badgeSprite.material.map) {
            try { ag.badgeSprite.material.map.dispose(); } catch (_) {}
          }
          try { ag.badgeSprite.material.dispose(); } catch (_) {}
        }
        if (ag.screens && ag.screens.length > 0) {
          ag.screens.forEach((s) => {
            if (s.material) {
              if (s.material.map) try { s.material.map.dispose(); } catch (_) {}
              try { s.material.dispose(); } catch (_) {}
            }
          });
        }
      });
    }

    while (this.workstationsGroup.children.length > 0) {
      const obj = this.workstationsGroup.children[0];
      this.workstationsGroup.remove(obj);
    }
    this.agents = [];

    // Instantiate Workstation and Mascot for EVERY agent in this.agentRoster
    this.agentRoster.forEach((data, index) => {
      // 1. Workstation Desk, Chair, Monitors, Accessories
      const equip = this.buildDeskEquipment(data, index, this.agentRoster.length);
      equip.slotGroup.visible = true;

      // 2. Official Chibi Robot Mascot Rig (100% Authentic Mascot)
      const agentRig = this.buildCompactAgentRig(data);
      agentRig.group.visible = true;

      this.agents.push({
        data,
        group: agentRig.group,
        torso: agentRig.torso,
        head: agentRig.head,
        visorRim: agentRig.visorRim,
        lEye: agentRig.lEye,
        rEye: agentRig.rEye,
        faceMesh: agentRig.faceMesh,
        armL: agentRig.armL,
        armR: agentRig.armR,
        lBicep: agentRig.lBicep,
        rBicep: agentRig.rBicep,
        lSh: agentRig.lSh,
        rSh: agentRig.rSh,
        legL: agentRig.legL,
        legR: agentRig.legR,
        badgeSprite: agentRig.badgeSprite,
        badgeCanvas: agentRig.badgeCanvas,
        bossCape: agentRig.bossCape,
        epauletL: agentRig.epauletL,
        epauletR: agentRig.epauletR,
        coreRing: agentRig.coreRing,
        chestF: agentRig.chestF,
        thrusterFlames: [agentRig.flameL, agentRig.flameR],
        screens: equip.screens,
        chairGroup: equip.chairGroup,
        slotGroup: equip.slotGroup,
        currentPos: data.deskPos.clone(),
        targetPos: data.deskPos.clone(),
        currentRotY: data.deskFacingAngle,
        targetRotY: data.deskFacingAngle,
        isTransitioning: false,
        transitionProgress: 1.0,
        wanderState: {
          status: 'desk', // 'desk' | 'walking' | 'resting' | 'returning_to_desk'
          destPos: data.deskPos.clone(),
          timer: 3.5 + index * 2.5,
          walkPhase: index * 1.5,
        },
      });

      this.workstationsGroup.add(agentRig.group);
    });

    // Auto-load custom outfits & styles from system/subagent/<id>/style.json
    this.loadAllAgentStyles();
  }
  updateAgentStyle(agentId, styleData) {
    if (!agentId || !styleData) return;
    const cleanId = String(agentId).toLowerCase().replace(/^agent-/, '');

    // Locate target agent in roster/scene
    const agent = this.agents.find(a => {
      if (!a.data) return false;
      const persona = (a.data.persona || '').toLowerCase();
      const id = (a.data.id || '').toLowerCase().replace(/^agent-/, '');
      return persona === cleanId || id === cleanId || (cleanId === 'leader' && a.data.isBoss) || (cleanId === 'mr.flow' && a.data.isTrainer);
    });

    if (!agent) {
      console.warn(`[Office 3D Style] Agent not found in scene for style update: ${agentId}`);
      return;
    }

    agent.data.styleData = styleData;

    // 1. Primary Suit Color (Torso, Biceps)
    const primaryColor = styleData.suit?.primary_color || '#00f2fe';
    const primaryThreeColor = new THREE.Color(primaryColor);
    const suitMat = new THREE.MeshStandardMaterial({
      color: primaryThreeColor,
      roughness: (styleData.suit?.material?.roughness) ?? 0.25,
      metalness: (styleData.suit?.material?.metalness) ?? 0.5,
    });
    if (agent.torso) agent.torso.material = suitMat;
    if (agent.lBicep) agent.lBicep.material = suitMat;
    if (agent.rBicep) agent.rBicep.material = suitMat;

    // 2. Secondary Color (Shoulders)
    const secondaryColor = styleData.suit?.secondary_color || '#7f00ff';
    const secondaryThreeColor = new THREE.Color(secondaryColor);
    const secondaryMat = new THREE.MeshStandardMaterial({
      color: secondaryThreeColor,
      roughness: 0.3,
      metalness: 0.6,
    });
    if (agent.lSh) agent.lSh.material = secondaryMat;
    if (agent.rSh) agent.rSh.material = secondaryMat;

    // 3. Head: Visor Rim & Eye Luminescence (Sacred Head Lock preserved)
    const visorGlow = styleData.head?.visor_glow_color || primaryColor;
    const glowThreeColor = new THREE.Color(visorGlow);
    const glowMat = new THREE.MeshStandardMaterial({
      color: glowThreeColor,
      emissive: glowThreeColor,
      emissiveIntensity: 1.8,
      metalness: 0.8,
      roughness: 0.2,
    });
    if (agent.visorRim) agent.visorRim.material = glowMat;
    if (agent.lEye) agent.lEye.material = glowMat;
    if (agent.rEye) agent.rEye.material = glowMat;

    // 4. Accessories: Cape
    const hasCape = styleData.accessories?.cape === true || styleData.accessories?.cape === 'true';
    if (agent.bossCape) {
      agent.bossCape.visible = hasCape;
      if (hasCape) {
        agent.bossCape.material = new THREE.MeshStandardMaterial({
          color: primaryThreeColor,
          roughness: 0.6,
          metalness: 0.25,
        });
      }
    }

    // 5. Accessories: Epaulets
    const hasEpaulets = styleData.accessories?.shoulders === 'epaulets';
    if (agent.epauletL) agent.epauletL.visible = hasEpaulets;
    if (agent.epauletR) agent.epauletR.visible = hasEpaulets;

    // 6. Thruster Plasma Flame
    const thrusterColor = styleData.limbs?.thruster_plasma_color || primaryColor;
    const thrusterThreeColor = new THREE.Color(thrusterColor);
    if (agent.thrusterFlames && Array.isArray(agent.thrusterFlames)) {
      const flameMat = new THREE.MeshBasicMaterial({
        color: thrusterThreeColor,
        transparent: true,
        opacity: 0.85,
      });
      agent.thrusterFlames.forEach(f => {
        if (f) f.material = flameMat;
      });
    }

    // 7. Chest Core
    const badgeType = styleData.accessories?.chest_badge || 'arc_reactor';
    if (agent.coreRing) {
      agent.coreRing.visible = (badgeType !== 'none');
      if (agent.coreRing.visible) agent.coreRing.material = glowMat;
    }
    if (agent.chestF) {
      agent.chestF.visible = (badgeType === 'flowork_f');
    }

    console.log(`[Office 3D Style] ✓ Outfit successfully applied to agent '${agentId}':`, styleData.preset_name || 'Custom');
  }

  async loadAllAgentStyles() {
    if (!this.agents || !this.agents.length) return;
    for (const agent of this.agents) {
      if (!agent.data) continue;
      const subagentId = agent.data.persona || (agent.data.id ? agent.data.id.replace(/^agent-/, '') : null);
      if (!subagentId) continue;
      try {
        const res = await fetch(`/api/subagents/${encodeURIComponent(subagentId)}/style`);
        if (res.ok) {
          const json = await res.json();
          if (json.status === 'ok' && json.style_data) {
            this.updateAgentStyle(subagentId, json.style_data);
          }
        }
      } catch (e) {
        // Silently skip if style API unreachable or offline
      }
    }
  }

  setSessionMode(mode) {
    this.currentMode = 'office';
    console.log('[Office 3D] 🏢 Sovereign Modern Corporate Office Active');

    if (this.environmentGroup) this.environmentGroup.visible = true;
    if (this.workstationsGroup) this.workstationsGroup.visible = true;

    if (window.AVAILABLE_PERSONAS) {
      this.syncPersonas(window.AVAILABLE_PERSONAS);
    } else {
      this.loadPersonas();
    }

    const tabSymbol = document.getElementById('tab-office-symbol');
    const tabLabel = document.getElementById('tab-office-label');
    if (tabSymbol) tabSymbol.textContent = '🏢';
    if (tabLabel) tabLabel.textContent = 'Office';
  }

  buildDeskEquipment(data, index = 0, total = 1) {
    // 🏢 DYNAMIC OFFICE WORKSTATION POD
    const slotGroup = new THREE.Group();
    slotGroup.position.copy(data.deskPos);
    slotGroup.rotation.y = data.deskFacingAngle;

    const isWorking = data.state === 'working';
    const isCore = !!data.isTrainer || data.id === 'agent-mr.flow' || data.persona === 'mr.flow';
    const screens = [];

    const walnutMat = this.sharedMaterials ? this.sharedMaterials.walnutWoodMat : new THREE.MeshStandardMaterial({ color: 0x241711, roughness: 0.5 });
    const oakMat = this.sharedMaterials ? this.sharedMaterials.oakWoodMat : new THREE.MeshStandardMaterial({ color: 0x78502d, roughness: 0.45 });
    const leatherMat = this.sharedMaterials ? this.sharedMaterials.executiveLeatherMat : new THREE.MeshStandardMaterial({ color: 0x0f141c, roughness: 0.38 });
    const graphiteMat = this.sharedMaterials ? this.sharedMaterials.matteGraphiteMat : new THREE.MeshStandardMaterial({ color: 0x1f2937, metalness: 0.8 });
    const brassMat = this.sharedMaterials ? this.sharedMaterials.brushedBrassMat : new THREE.MeshStandardMaterial({ color: 0xd4af37, metalness: 0.88 });

    // 1. DESK (Executive Desk for index 0, Modern Team Desk for specialists)
    const deskGroup = new THREE.Group();
    deskGroup.position.set(0, 0, 0.65);

    const isExec = (index === 0);
    const deskW = isExec ? 2.10 : 1.55;
    const deskD = isExec ? 0.95 : 0.82;
    const deskTopMat = isExec ? walnutMat : oakMat;

    // Desktop
    const deskTop = new THREE.Mesh(new THREE.BoxGeometry(deskW, 0.055, deskD), deskTopMat);
    deskTop.position.y = 0.74;
    deskGroup.add(deskTop);

    if (isExec) {
      // Sleek Executive Walnut Dais with Brushed Brass Accent
      const dais = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.20, 2.6), walnutMat);
      dais.position.set(0, -0.10, 0.20);
      deskGroup.add(dais);
      const daisTrim = new THREE.Mesh(new THREE.BoxGeometry(3.64, 0.04, 2.64), brassMat);
      daisTrim.position.set(0, -0.01, 0.20);
      deskGroup.add(daisTrim);
    }

    // Leather Writing Blotter
    const blotterW = isExec ? 1.10 : 0.85;
    const blotterD = isExec ? 0.60 : 0.50;
    const blotter = new THREE.Mesh(new THREE.BoxGeometry(blotterW, 0.012, blotterD), leatherMat);
    blotter.position.set(0, 0.77, -0.05);
    deskGroup.add(blotter);

    // Brass Front Edge Trim
    const frontTrim = new THREE.Mesh(new THREE.BoxGeometry(deskW + 0.01, 0.018, 0.018), brassMat);
    frontTrim.position.set(0, 0.74, -deskD / 2);
    deskGroup.add(frontTrim);

    // Modesty Panel
    const modestyPanel = new THREE.Mesh(
      new THREE.BoxGeometry(deskW - 0.25, 0.45, 0.025),
      graphiteMat
    );
    modestyPanel.position.set(0, 0.48, deskD / 2 - 0.05);
    deskGroup.add(modestyPanel);

    // Metal Legs
    [-deskW / 2 + 0.12, deskW / 2 - 0.12].forEach(lx => {
      const leg = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.74, deskD - 0.12), graphiteMat);
      leg.position.set(lx, 0.37, 0);
      deskGroup.add(leg);
    });

    slotGroup.add(deskGroup);

    // 2. MONITORS (Triple Curved for Executive Desk, Dual Widescreen for Specialists)
    if (isExec) {
      // Center Tactical Screen
      const centerCanvas = this.createHoloDisplayCanvas('MAIN_TACTICAL', data);
      const centerTex = new THREE.CanvasTexture(centerCanvas);
      const centerMat = new THREE.MeshBasicMaterial({ map: centerTex, side: THREE.DoubleSide });
      const centerScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 0.48), centerMat);
      centerScreen.position.set(0, 1.15, 0.90);
      centerScreen.rotation.y = Math.PI;
      slotGroup.add(centerScreen);
      screens.push(centerScreen);

      // Left Screen (Neural Radar Diagnostics)
      const leftCanvas = this.createHoloDisplayCanvas('RADAR_DIAGNOSTICS', data);
      const leftTex = new THREE.CanvasTexture(leftCanvas);
      const leftMat = new THREE.MeshBasicMaterial({ map: leftTex, side: THREE.DoubleSide });
      const leftScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.68, 0.42), leftMat);
      leftScreen.position.set(-0.76, 1.15, 0.82);
      leftScreen.rotation.y = Math.PI - 0.38;
      slotGroup.add(leftScreen);
      screens.push(leftScreen);

      // Right Screen (Synapse Heuristics Code)
      const rightCanvas = this.createHoloDisplayCanvas('SYNAPSE_CODE', data);
      const rightTex = new THREE.CanvasTexture(rightCanvas);
      const rightMat = new THREE.MeshBasicMaterial({ map: rightTex, side: THREE.DoubleSide });
      const rightScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.68, 0.42), rightMat);
      rightScreen.position.set(0.76, 1.15, 0.82);
      rightScreen.rotation.y = Math.PI + 0.38;
      slotGroup.add(rightScreen);
      screens.push(rightScreen);

      // Monitor Stand
      const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.40, 12), graphiteMat);
      stand.position.set(0, 0.94, 0.90);
      slotGroup.add(stand);

    } else {
      // Dual Widescreen Monitors side-by-side mounted on dual-arm
      // Left Monitor: Live IDE Code Editor
      const codeCanvas = this.createHoloDisplayCanvas('SYNAPSE_CODE', data);
      const codeTex = new THREE.CanvasTexture(codeCanvas);
      const codeMat = new THREE.MeshBasicMaterial({ map: codeTex, side: THREE.DoubleSide });
      const codeScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.64, 0.40), codeMat);
      codeScreen.position.set(-0.35, 1.12, 0.88);
      codeScreen.rotation.y = Math.PI - 0.15;
      slotGroup.add(codeScreen);
      screens.push(codeScreen);

      // Right Monitor: Real-time Telemetry Dashboard
      const dashCanvas = this.createHoloDisplayCanvas('MAIN_TACTICAL', data);
      const dashTex = new THREE.CanvasTexture(dashCanvas);
      const dashMat = new THREE.MeshBasicMaterial({ map: dashTex, side: THREE.DoubleSide });
      const dashScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.64, 0.40), dashMat);
      dashScreen.position.set(0.35, 1.12, 0.88);
      dashScreen.rotation.y = Math.PI + 0.15;
      slotGroup.add(dashScreen);
      screens.push(dashScreen);

      // Dual Monitor Stand Mount
      const mount = new THREE.Mesh(new THREE.BoxGeometry(0.60, 0.04, 0.04), graphiteMat);
      mount.position.set(0, 1.05, 0.90);
      const mountStem = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.35, 12), graphiteMat);
      mountStem.position.set(0, 0.92, 0.90);
      slotGroup.add(mount, mountStem);
    }

    // 3. KEYBOARD & MOUSE ON DESK
    const kbCanvas = this.createHoloKeyboardCanvas(data.color);
    const kbTex = new THREE.CanvasTexture(kbCanvas);
    const kbMat = new THREE.MeshBasicMaterial({ map: kbTex, transparent: true, opacity: 0.95, side: THREE.DoubleSide });
    const kbMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.52, 0.22), kbMat);
    kbMesh.rotation.x = -Math.PI / 2;
    kbMesh.position.set(-0.06, 0.776, 0.60);
    slotGroup.add(kbMesh);

    // Mouse & Pad
    const mousePad = new THREE.Mesh(
      new THREE.PlaneGeometry(0.24, 0.22),
      new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.8 })
    );
    mousePad.rotation.x = -Math.PI / 2;
    mousePad.position.set(0.35, 0.774, 0.60);
    const mouseMesh = new THREE.Mesh(
      new THREE.BoxGeometry(0.07, 0.03, 0.11),
      new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.3 })
    );
    mouseMesh.position.set(0.35, 0.79, 0.60);
    slotGroup.add(mousePad, mouseMesh);

    // Ceramic Coffee Mug with Flowork Logo
    const mug = new THREE.Mesh(
      new THREE.CylinderGeometry(0.045, 0.04, 0.10, 16),
      new THREE.MeshStandardMaterial({ color: isExec ? 0xd4af37 : 0x38bdf8, roughness: 0.3 })
    );
    mug.position.set(-deskW / 2 + 0.18, 0.79, 0.62);
    slotGroup.add(mug);

    // 4. ERGONOMIC OFFICE CHAIR (Placed behind desk at (0, 0, 0))
    const chairGroup = new THREE.Group();
    chairGroup.position.set(0, 0, 0);

    // 5-Star Caster Base
    const baseCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.26, 0.03, 16), graphiteMat);
    baseCyl.position.y = 0.05;
    chairGroup.add(baseCyl);

    for (let sp = 0; sp < 5; sp++) {
      const spAng = (sp / 5) * Math.PI * 2;
      const spoke = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.02, 0.26), graphiteMat);
      spoke.position.set(Math.sin(spAng) * 0.14, 0.04, Math.cos(spAng) * 0.14);
      spoke.rotation.y = spAng;
      chairGroup.add(spoke);

      // Caster Wheel
      const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.02, 8), graphiteMat);
      wheel.rotation.z = Math.PI / 2;
      wheel.position.set(Math.sin(spAng) * 0.26, 0.025, Math.cos(spAng) * 0.26);
      chairGroup.add(wheel);
    }

    // Chrome Gas Lift Stem
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.35, 12), brassMat);
    stem.position.y = 0.22;
    chairGroup.add(stem);

    // Mesh / Leather Seat Cushion
    const seatMat = isExec ? leatherMat : (this.sharedMaterials ? this.sharedMaterials.corporateDeskMat : graphiteMat);
    const seat = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.065, 0.46), seatMat);
    seat.position.y = 0.42;
    chairGroup.add(seat);

    // High Backrest with Ergonomic Curve & Headrest
    const backRest = new THREE.Mesh(new THREE.BoxGeometry(0.44, 0.55, 0.05), seatMat);
    backRest.position.set(0, 0.70, -0.21);
    chairGroup.add(backRest);

    if (isExec) {
      // Executive Headrest
      const headRest = new THREE.Mesh(new THREE.BoxGeometry(0.30, 0.14, 0.06), leatherMat);
      headRest.position.set(0, 1.05, -0.22);
      chairGroup.add(headRest);
    }

    // Armrests
    [-0.26, 0.26].forEach(ax => {
      const arm = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.18, 0.28), graphiteMat);
      arm.position.set(ax, 0.54, 0);
      chairGroup.add(arm);
    });

    slotGroup.add(chairGroup);

    // Workstation is ALWAYS visible
    slotGroup.visible = true;
    this.workstationsGroup.add(slotGroup);

    return {
      screens,
      slotGroup,
      chairGroup,
    };
  }

  createHoloDisplayCanvas(type, data) {
    const canvas = document.createElement('canvas');
    canvas.width = type === 'MAIN_TACTICAL' ? 640 : (type === 'STATUS_RIBBON' ? 640 : 400);
    canvas.height = type === 'STATUS_RIBBON' ? 96 : 320;
    const ctx = canvas.getContext('2d');
    const colorHex = (typeof data.color === 'number')
      ? ('#' + data.color.toString(16).padStart(6, '0'))
      : (data.color || '#00f2fe');

    // Translucent dark cyber glass background
    ctx.fillStyle = 'rgba(10, 16, 28, 0.94)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Glowing border
    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 4;
    ctx.strokeRect(4, 4, canvas.width - 8, canvas.height - 8);

    // Inner fine grid lines
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.12)';
    ctx.lineWidth = 1;
    for (let x = 20; x < canvas.width; x += 30) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }
    for (let y = 20; y < canvas.height; y += 30) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
    }

    if (type === 'MAIN_TACTICAL') {
      // Header Banner
      ctx.fillStyle = 'rgba(0, 242, 254, 0.18)';
      ctx.fillRect(8, 8, canvas.width - 16, 42);
      ctx.font = 'bold 20px monospace';
      ctx.fillStyle = '#ffffff';
      ctx.fillText(`⚡ ${data.name ? data.name.toUpperCase() : 'AGENT'} // WORKSTATION`, 20, 36);

      // Neural frequency wave
      ctx.strokeStyle = colorHex;
      ctx.lineWidth = 3;
      ctx.beginPath();
      for (let x = 20; x < canvas.width - 20; x += 10) {
        const y = 140 + Math.sin(x * 0.05 + (data.typingPhase || 0)) * 30 * Math.cos(x * 0.02);
        if (x === 20) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Telemetry Data Readout Lines
      ctx.font = '14px monospace';
      ctx.fillStyle = '#38bdf8';
      ctx.fillText('STATUS: ONLINE • RUNTIME: HIGH-PRIORITY • EXIT CODE 0', 20, 210);
      ctx.fillText(`ROLE: ${data.role || 'Autonomous Specialist Agent'}`, 20, 240);
      ctx.fillText('PROTOCOL: FLOWORK_LIFECYCLE • ZERO-TRUST VERIFIED', 20, 270);

      // Corner status led
      ctx.fillStyle = '#22c55e';
      ctx.beginPath();
      ctx.arc(canvas.width - 30, 28, 8, 0, Math.PI * 2);
      ctx.fill();

    } else if (type === 'RADAR_DIAGNOSTICS') {
      // Tactical Radar Sweep HUD
      ctx.font = 'bold 16px monospace';
      ctx.fillStyle = '#00f2fe';
      ctx.fillText('📡 SYSTEM RADAR', 20, 32);

      const cx = canvas.width / 2;
      const cy = 175;
      [35, 70, 105].forEach(r => {
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.35)';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + 80, cy - 60);
      ctx.strokeStyle = '#00f2fe';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      ctx.font = '13px monospace';
      ctx.fillStyle = '#a855f7';
      ctx.fillText('SYSTEM INTEGRITY: 100%', 20, 300);

    } else if (type === 'SYNAPSE_CODE') {
      // Hex Matrix Code & Logic Stream
      ctx.font = 'bold 16px monospace';
      ctx.fillStyle = '#a855f7';
      ctx.fillText('💾 CORE HEURISTICS', 20, 32);

      const hexLines = [
        '0x7F00FF // EXEC LTO FAT',
        '0x00F2FE // FLOWORK MESH',
        'WAITPID: 0 DEFECTS REAPED',
        'THREAD[AXUM]: PORT 19890',
        'LIFECYCLE: STANDBY_ARMED',
        'MEM_BUFFER: OPTIMAL 0B_LEAK',
        'STATE: QUANTUM_ALIGNED'
      ];
      ctx.font = '12px monospace';
      ctx.fillStyle = '#38bdf8';
      hexLines.forEach((line, i) => {
        ctx.fillText(line, 20, 75 + i * 32);
      });

    } else if (type === 'STATUS_RIBBON') {
      ctx.font = 'bold 18px monospace';
      ctx.fillStyle = '#00f2fe';
      ctx.fillText(`⚡ FLOWORK OFFICE // ${data.name || 'AGENT'} STATION`, 20, 42);
      ctx.font = '14px monospace';
      ctx.fillStyle = '#fbbf24';
      ctx.fillText('STATUS: ATTENTIVE STANDBY • EXIT CODE 0 VERIFIED', 20, 75);
    }

    return canvas;
  }

  createHoloKeyboardCanvas(color) {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 220;
    const ctx = canvas.getContext('2d');
    const colorHex = (typeof color === 'number')
      ? ('#' + color.toString(16).padStart(6, '0'))
      : (color || '#00f2fe');

    // Translucent dark glass keyboard base
    ctx.fillStyle = 'rgba(15, 23, 42, 0.90)';
    if (typeof ctx.roundRect === 'function') {
      ctx.roundRect(8, 8, 496, 204, 16);
    } else {
      ctx.rect(8, 8, 496, 204);
    }
    ctx.fill();

    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Floating keys grid (Ergonomic Keyboard Layout)
    ctx.fillStyle = 'rgba(30, 41, 59, 0.95)';
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
    ctx.lineWidth = 1;
    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 12; col++) {
        const kx = 24 + col * 38;
        const ky = 24 + row * 44;
        ctx.fillRect(kx, ky, 32, 34);
        ctx.strokeRect(kx, ky, 32, 34);
      }
    }
    return canvas;
  }
  createFloworkLogoCanvas(agentColor) {
    const colorHex = (typeof agentColor === 'number')
      ? ('#' + agentColor.toString(16).padStart(6, '0'))
      : (agentColor || '#00f2fe');

    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');

    // 1. Dark Cyber Glass Surface
    const bgGrad = ctx.createRadialGradient(256, 256, 30, 256, 256, 270);
    bgGrad.addColorStop(0, '#0f172a');
    bgGrad.addColorStop(0.65, '#080c14');
    bgGrad.addColorStop(1, '#020408');
    ctx.fillStyle = bgGrad;
    ctx.beginPath();
    ctx.roundRect(16, 16, 480, 480, 72);
    ctx.fill();

    // 2. Glowing Neon Border Frame (Agent Color Accent)
    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 10;
    ctx.shadowColor = colorHex;
    ctx.shadowBlur = 24;
    ctx.beginPath();
    ctx.roundRect(24, 24, 464, 464, 64);
    ctx.stroke();

    // Subtle outer pulse ring
    ctx.strokeStyle = '#7f00ff';
    ctx.lineWidth = 3;
    ctx.shadowBlur = 10;
    ctx.setLineDash([12, 10]);
    ctx.beginPath();
    ctx.arc(256, 256, 215, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);

    // 3. Flowork Neon Gradient for the Iconic "F" Monogram
    const flowGrad = ctx.createLinearGradient(140, 120, 380, 390);
    flowGrad.addColorStop(0, '#00f2fe');   // Bright Electric Cyan
    flowGrad.addColorStop(0.55, '#38bdf8'); // Sky Blue
    flowGrad.addColorStop(1, '#818cf8');   // Purple/Indigo

    ctx.fillStyle = flowGrad;
    ctx.shadowColor = '#00f2fe';
    ctx.shadowBlur = 28;

    // Geometric "F" Bars (Exact coordinates from Flowork logo SVG)
    // Vertical stem: x=152, y=120, w=64, h=272, rx=18
    ctx.beginPath();
    ctx.roundRect(152, 120, 64, 272, 18);
    ctx.fill();

    // Top horizontal bar: x=152, y=120, w=208, h=64, rx=18
    ctx.beginPath();
    ctx.roundRect(152, 120, 208, 64, 18);
    ctx.fill();

    // Middle horizontal bar: x=152, y=234, w=176, h=60, rx=16
    ctx.beginPath();
    ctx.roundRect(152, 234, 176, 60, 16);
    ctx.fill();

    // 4. Flow Accent: Sweeping streak curve and satellite node
    ctx.strokeStyle = '#00f2fe';
    ctx.lineWidth = 12;
    ctx.lineCap = 'round';
    ctx.shadowColor = '#00f2fe';
    ctx.shadowBlur = 20;
    ctx.beginPath();
    ctx.moveTo(330, 200);
    ctx.quadraticCurveTo(395, 216, 435, 176);
    ctx.stroke();

    // Satellite Orbit Node
    ctx.fillStyle = '#00f2fe';
    ctx.beginPath();
    ctx.arc(435, 176, 16, 0, Math.PI * 2);
    ctx.fill();

    // Inner bright core dot
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(435, 176, 6, 0, Math.PI * 2);
    ctx.fill();

    return canvas;
  }

  createBossFaceCanvas() {
    // 👑 Boss / Sovereign Master Custom Face (NO "F" LOGO!)
    // High-tech luxury golden cyber visor with glowing eyes and imperial crest
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');

    // 1. Dark Cyber Glass Surface with Imperial Gold gradient
    const bgGrad = ctx.createRadialGradient(256, 256, 30, 256, 256, 270);
    bgGrad.addColorStop(0, '#1c1917');
    bgGrad.addColorStop(0.65, '#0c0a09');
    bgGrad.addColorStop(1, '#000000');
    ctx.fillStyle = bgGrad;
    ctx.beginPath();
    ctx.roundRect(16, 16, 480, 480, 72);
    ctx.fill();

    // 2. Imperial Gold Outer Border Frame
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 12;
    ctx.shadowColor = '#fbbf24';
    ctx.shadowBlur = 32;
    ctx.beginPath();
    ctx.roundRect(24, 24, 464, 464, 64);
    ctx.stroke();

    // Subtle golden pulse orbit ring
    ctx.strokeStyle = '#d97706';
    ctx.lineWidth = 3;
    ctx.shadowBlur = 12;
    ctx.setLineDash([14, 10]);
    ctx.beginPath();
    ctx.arc(256, 256, 215, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);

    // 3. Cybernetic Boss Eyes / Holographic Visor (Sleek predatory twin horizontal optics)
    const visorGrad = ctx.createLinearGradient(120, 240, 392, 272);
    visorGrad.addColorStop(0, '#fbbf24');
    visorGrad.addColorStop(0.5, '#ffffff');
    visorGrad.addColorStop(1, '#f59e0b');

    ctx.fillStyle = visorGrad;
    ctx.shadowColor = '#f59e0b';
    ctx.shadowBlur = 36;

    // Left Optic Visor Slit
    ctx.beginPath();
    ctx.roundRect(110, 246, 120, 32, 10);
    ctx.fill();

    // Right Optic Visor Slit
    ctx.beginPath();
    ctx.roundRect(282, 246, 120, 32, 10);
    ctx.fill();

    // Twin Core Laser Dots (Pupils)
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = '#ffffff';
    ctx.shadowBlur = 20;
    ctx.beginPath();
    ctx.arc(170, 262, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(342, 262, 7, 0, Math.PI * 2);
    ctx.fill();

    // 4. Imperial Master Crest / Crown Monogram on Forehead
    ctx.strokeStyle = '#fbbf24';
    ctx.fillStyle = '#f59e0b';
    ctx.lineWidth = 6;
    ctx.shadowColor = '#f59e0b';
    ctx.shadowBlur = 24;
    ctx.beginPath();
    ctx.moveTo(180, 160);
    ctx.lineTo(210, 115);
    ctx.lineTo(256, 145);
    ctx.lineTo(302, 115);
    ctx.lineTo(332, 160);
    ctx.closePath();
    ctx.stroke();
    ctx.fill();

    // Crown jewels / dots
    ctx.fillStyle = '#ffffff';
    [210, 256, 302].forEach(cx => {
      ctx.beginPath();
      ctx.arc(cx, cx === 256 ? 142 : 115, 5, 0, Math.PI * 2);
      ctx.fill();
    });

    // 5. Tech circuitry traces under visor
    ctx.strokeStyle = 'rgba(251, 191, 36, 0.4)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(130, 310);
    ctx.lineTo(190, 360);
    ctx.lineTo(240, 360);
    ctx.moveTo(382, 310);
    ctx.lineTo(322, 360);
    ctx.lineTo(272, 360);
    ctx.stroke();

    return canvas;
  }

  createBossCrownMesh() {
    // 3D Imperial Low-Poly Gold Crown resting atop Boss helmet
    const crownGroup = new THREE.Group();
    const goldMat = this.sharedMaterials.bossCrownMat;

    // Circular base band
    const baseMesh = new THREE.Mesh(this.sharedGeometries.crownBase, goldMat);
    crownGroup.add(baseMesh);

    // 5 Crown spikes
    for (let i = 0; i < 5; i++) {
      const angle = (i / 5) * Math.PI * 2;
      const spike = new THREE.Mesh(this.sharedGeometries.crownSpike, goldMat);
      spike.position.set(Math.cos(angle) * 0.165, 0.065, Math.sin(angle) * 0.165);
      spike.rotation.y = -angle;
      crownGroup.add(spike);
    }
    crownGroup.position.set(0, 0.185, 0);
    return crownGroup;
  }

  buildCompactAgentRig(data) {
    // -------------------------------------------------------------
    // Compact Official Chibi Mr. Flow Character Model (~0.62x scale)
    // Height: ~1.15 units. Perfectly balanced for workstations & floor.
    // -------------------------------------------------------------
    const isBoss = !!data.isBoss;
    const agentGroup = new THREE.Group();
    agentGroup.position.copy(data.state === 'working' ? data.deskPos : data.standbyPos);
    agentGroup.rotation.y = data.state === 'working' ? data.deskFacingAngle : data.standbyFacingAngle;
    agentGroup.userData = { agentData: data };

    const armorMat = isBoss ? this.sharedMaterials.bossArmorMat : this.sharedMaterials.agentArmorMat;
    const accentMat = this.getAccentMat(data.color, isBoss);
    const purpleAccentMat = this.sharedMaterials.purpleAccentMat;
    const visorGlassMat = this.sharedMaterials.visorGlassMat;

    // 1. HEAD & HELMET
    const head = new THREE.Group();
    head.position.y = 1.22;

    // Chibi Cyber Helmet Shell (Rounded Sphere)
    const helmet = new THREE.Mesh(this.sharedGeometries.agentHelmet, armorMat);
    helmet.scale.set(1.0, 0.96, 0.92);
    head.add(helmet);

    // Glossy Curved Face Visor Plate
    const visor = new THREE.Mesh(this.sharedGeometries.agentVisor, visorGlassMat);
    visor.scale.set(1.01, 0.97, 0.93);
    head.add(visor);

    // Glowing Visor Rim
    const visorRim = new THREE.Mesh(this.sharedGeometries.visorRim, accentMat);
    visorRim.rotation.z = Math.PI * 0.85;
    visorRim.position.set(0, -0.02, 0.18);
    head.add(visorRim);

    // Face screen texture (Canvas for logo / visor telemetry)
    const faceTexture = this.getFaceTexture(data);
    const faceMat = new THREE.MeshBasicMaterial({
      map: faceTexture,
      transparent: true,
      opacity: 0.92,
    });
    const faceMesh = new THREE.Mesh(this.sharedGeometries.faceMesh, faceMat);
    faceMesh.position.set(0, 0, 0.19);
    head.add(faceMesh);

    // Expressive Digital Eyes (^ _ ^) for AI Agents
    let lEye = null;
    let rEye = null;
    if (!isBoss) {
      lEye = new THREE.Mesh(this.sharedGeometries.eye, accentMat);
      lEye.position.set(-0.068, 0.015, 0.195);
      head.add(lEye);

      rEye = new THREE.Mesh(this.sharedGeometries.eye, accentMat);
      rEye.position.set(0.068, 0.015, 0.195);
      head.add(rEye);
    }

    // Forehead Crest: Boss Crown (Grand Chief only)
    if (isBoss) {
      const crown = this.createBossCrownMesh();
      crown.position.set(0, 0.16, 0);
      head.add(crown);
    }

    // Ear Pods & Antennas
    const lPod = new THREE.Mesh(this.sharedGeometries.pod, armorMat);
    lPod.rotation.z = Math.PI / 2;
    lPod.position.set(-0.20, 0, 0);
    const lRing = new THREE.Mesh(this.sharedGeometries.podRing, accentMat);
    lRing.rotation.y = Math.PI / 2;
    lRing.position.set(-0.225, 0, 0);
    head.add(lPod, lRing);

    const rPod = new THREE.Mesh(this.sharedGeometries.pod, armorMat);
    rPod.rotation.z = Math.PI / 2;
    rPod.position.set(0.20, 0, 0);
    const rRing = new THREE.Mesh(this.sharedGeometries.podRing, purpleAccentMat);
    rRing.rotation.y = Math.PI / 2;
    rRing.position.set(0.225, 0, 0);
    head.add(rPod, rRing);

    // Mini Antennas
    const lAnt = new THREE.Mesh(this.sharedGeometries.ant, armorMat);
    lAnt.position.set(-0.18, 0.13, -0.02);
    lAnt.rotation.z = Math.PI / 7;
    const lTip = new THREE.Mesh(this.sharedGeometries.antTip, accentMat);
    lTip.position.y = 0.07;
    lAnt.add(lTip);
    head.add(lAnt);

    const rAnt = new THREE.Mesh(this.sharedGeometries.ant, armorMat);
    rAnt.position.set(0.18, 0.13, -0.02);
    rAnt.rotation.z = -Math.PI / 7;
    const rTip = new THREE.Mesh(this.sharedGeometries.antTip, purpleAccentMat);
    rTip.position.y = 0.07;
    rAnt.add(rTip);
    head.add(rAnt);

    agentGroup.add(head);

    // Magnetic Collar Ring
    const collar = new THREE.Mesh(this.sharedGeometries.collar, accentMat);
    collar.rotation.x = Math.PI / 2;
    collar.position.set(0, 1.05, 0);
    agentGroup.add(collar);

    // 2. TORSO / JACKET CAPSULE (Baju Agent with high contrast)
    const suitMat = (this.sharedMaterials && this.sharedMaterials.agentSuitMat) ? this.sharedMaterials.agentSuitMat : armorMat;
    const torso = new THREE.Mesh(this.sharedGeometries.torso, suitMat);
    torso.position.y = 0.80;
    agentGroup.add(torso);

    // Chest Arc Reactor Core
    const coreRing = new THREE.Mesh(this.sharedGeometries.coreRing, accentMat);
    coreRing.position.set(0, 0.85, 0.155);
    agentGroup.add(coreRing);

    // Mini 'F' inside Chest Reactor
    const chestF = new THREE.Group();
    chestF.position.set(0, 0.85, 0.16);
    chestF.scale.set(0.3, 0.3, 0.3);
    const cFSpine = new THREE.Mesh(this.sharedGeometries.cFSpine, accentMat);
    cFSpine.position.set(-0.025, 0, 0);
    const cFTop = new THREE.Mesh(this.sharedGeometries.cFTop, accentMat);
    cFTop.position.set(0.015, 0.045, 0);
    const cFMid = new THREE.Mesh(this.sharedGeometries.cFMid, purpleAccentMat);
    cFMid.position.set(0.01, -0.01, 0);
    chestF.add(cFSpine, cFTop, cFMid);
    agentGroup.add(chestF);

    // Back Jacket Emblem
    const jacketMat = new THREE.MeshBasicMaterial({ map: faceTexture, transparent: true });
    const jacketEmblem = new THREE.Mesh(this.sharedGeometries.jacketEmblem, jacketMat);
    jacketEmblem.position.set(0, 0.80, -0.145);
    jacketEmblem.rotation.y = Math.PI;
    agentGroup.add(jacketEmblem);

    // Imperial Boss Cape & Epaulets
    const bossCape = new THREE.Mesh(this.sharedGeometries.bossCape, this.sharedMaterials.bossCapeMat.clone());
    bossCape.position.set(0, 0.74, -0.16);
    bossCape.rotation.x = 0.08;
    bossCape.visible = isBoss;
    agentGroup.add(bossCape);

    const epauletL = new THREE.Mesh(this.sharedGeometries.bossEpaulet, this.sharedMaterials.bossEpauletMat.clone());
    epauletL.position.set(-0.25, 1.02, 0);
    const epauletR = new THREE.Mesh(this.sharedGeometries.bossEpaulet, this.sharedMaterials.bossEpauletMat.clone());
    epauletR.position.set(0.25, 1.02, 0);
    epauletL.visible = isBoss;
    epauletR.visible = isBoss;
    agentGroup.add(epauletL, epauletR);

    // Miniature Concentric Orbital Ring
    const orbitalRing = new THREE.Mesh(
      this.sharedGeometries.orbitalRing,
      this.getOrbitalMat(data.color, isBoss)
    );
    orbitalRing.position.set(0, 0.80, 0);
    orbitalRing.rotation.x = Math.PI / 4;
    agentGroup.add(orbitalRing);

    // 3. LIMBS: ARMS
    const armL = new THREE.Group();
    armL.position.set(-0.26, 0.82, 0);
    const lSh = new THREE.Mesh(this.sharedGeometries.shoulder, accentMat);
    const lBicep = new THREE.Mesh(this.sharedGeometries.bicep, suitMat);
    lBicep.position.y = -0.14;
    const lHand = new THREE.Mesh(this.sharedGeometries.hand, armorMat);
    lHand.position.y = -0.28;
    armL.add(lSh, lBicep, lHand);
    agentGroup.add(armL);

    const armR = new THREE.Group();
    armR.position.set(0.26, 0.82, 0);
    const rSh = new THREE.Mesh(this.sharedGeometries.shoulder, purpleAccentMat);
    const rBicep = new THREE.Mesh(this.sharedGeometries.bicep, suitMat);
    rBicep.position.y = -0.14;
    const rHand = new THREE.Mesh(this.sharedGeometries.hand, accentMat);
    rHand.position.y = -0.28;
    armR.add(rSh, rBicep, rHand);
    agentGroup.add(armR);

    // 4. LIMBS: LEGS & HOVER BOOTS
    const legL = new THREE.Group();
    legL.position.set(-0.12, 0.35, 0);
    const lThigh = new THREE.Mesh(this.sharedGeometries.thigh, armorMat);
    lThigh.position.y = -0.10;
    const lBoot = new THREE.Mesh(this.sharedGeometries.boot, armorMat);
    lBoot.position.set(0, -0.25, 0.02);
    const lThrust = new THREE.Mesh(this.sharedGeometries.thrusterRing, accentMat);
    lThrust.rotation.x = Math.PI / 2;
    lThrust.position.set(0, -0.31, 0.02);
    legL.add(lThigh, lBoot, lThrust);
    agentGroup.add(legL);

    const legR = new THREE.Group();
    legR.position.set(0.12, 0.35, 0);
    const rThigh = new THREE.Mesh(this.sharedGeometries.thigh, armorMat);
    rThigh.position.y = -0.10;
    const rBoot = new THREE.Mesh(this.sharedGeometries.boot, armorMat);
    rBoot.position.set(0, -0.25, 0.02);
    const rThrust = new THREE.Mesh(this.sharedGeometries.thrusterRing, accentMat);
    rThrust.rotation.x = Math.PI / 2;
    rThrust.position.set(0, -0.31, 0.02);
    legR.add(rThigh, rBoot, rThrust);
    agentGroup.add(legR);

    // 3D Ion Thruster Exhaust Plumes (Pulsing plasma cones under boots)
    const flameMat = this.sharedMaterials.thrusterFlameMat;
    const flameL = new THREE.Mesh(this.sharedGeometries.thrusterCone, flameMat);
    flameL.rotation.x = Math.PI; // Point down
    flameL.position.set(0, -0.38, 0.02);
    legL.add(flameL);

    const flameR = new THREE.Mesh(this.sharedGeometries.thrusterCone, flameMat);
    flameR.rotation.x = Math.PI; // Point down
    flameR.position.set(0, -0.38, 0.02);
    legR.add(flameR);

    agentGroup.userData.thrusterFlames = [flameL, flameR];

    // 5. FLOATING HOLOGRAM BADGE
    const badgeCanvas = document.createElement('canvas');
    badgeCanvas.width = 512;
    badgeCanvas.height = 160;
    const bCtx = badgeCanvas.getContext('2d');
    this.drawBadge(bCtx, data);

    const badgeTexture = new THREE.CanvasTexture(badgeCanvas);
    const badgeMat = new THREE.SpriteMaterial({ map: badgeTexture, transparent: true });
    const badgeSprite = new THREE.Sprite(badgeMat);
    badgeSprite.scale.set(1.5, 0.46, 1);
    badgeSprite.position.set(0, 1.76, 0);
    agentGroup.add(badgeSprite);

    return {
      group: agentGroup,
      torso,
      head,
      visorRim,
      lEye,
      rEye,
      faceMesh,
      armL,
      armR,
      lBicep,
      rBicep,
      lSh,
      rSh,
      legL,
      legR,
      flameL,
      flameR,
      badgeSprite,
      badgeCanvas,
      bossCape,
      epauletL,
      epauletR,
      coreRing,
      chestF,
      orbitalRing,
    };
  }

  drawBadge(ctx, data) {
    ctx.clearRect(0, 0, 512, 160);

    const isBoss = !!data.isBoss;
    const isToolRunning = !!data.activeTool && !!data.activeTool.name;
    const isThinking = !!data.isThinking;
    const isWorking = data.state === 'working' || isToolRunning;

    // Rounded background capsule
    ctx.fillStyle = isBoss
      ? 'rgba(28, 25, 23, 0.94)'
      : (isToolRunning
        ? 'rgba(32, 12, 24, 0.96)'
        : (isThinking
          ? 'rgba(24, 15, 38, 0.95)'
          : (isWorking ? 'rgba(10, 28, 20, 0.95)' : 'rgba(15, 23, 42, 0.88)')));
    ctx.beginPath();
    ctx.roundRect(10, 10, 492, 140, 20);
    ctx.fill();

    // Border glowing stroke
    ctx.lineWidth = isBoss ? 5 : (isToolRunning ? 6 : 4);
    ctx.strokeStyle = isBoss
      ? '#f59e0b'
      : (isToolRunning
        ? '#f43f5e'
        : (isThinking ? '#a855f7' : (isWorking ? '#10b981' : '#475569')));
    ctx.stroke();

    // 1. Agent Icon + Name & Authority Title
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.font = '900 28px "Inter", "Segoe UI", sans-serif';
    ctx.fillStyle = isBoss ? '#fbbf24' : '#ffffff';
    const titlePrefix = isBoss ? '👑 ' : (data.icon || '🤖 ') + ' ';
    ctx.fillText(`${titlePrefix}${data.name}`, 24, 22);

    // 2. Status Indicator Pill
    let statusText = '⚪ IDLE';
    let statusColor = '#94a3b8';
    if (isBoss) {
      statusText = '👑 SUPREME LEADER';
      statusColor = '#fbbf24';
    } else if (isToolRunning) {
      statusText = `⚡ TOOL: ${String(data.activeTool.name).toUpperCase()}`;
      statusColor = '#fb7185';
    } else if (data.isTrainer) {
      statusText = isThinking ? '⚡ REASONING / TRAINER' : '⚡ CHIEF ORCHESTRATOR';
      statusColor = '#00f2fe';
    } else if (isThinking) {
      statusText = '🧠 REASONING & ANALYSIS';
      statusColor = '#c084fc';
    } else if (isWorking) {
      statusText = '🟢 EXECUTING TASK';
      statusColor = '#34d399';
    }

    ctx.font = '700 20px "Inter", "Segoe UI", sans-serif';
    ctx.fillStyle = statusColor;
    ctx.fillText(statusText, 24, 64);

    // 3. Dynamic Tool / Thought Reason (SEDANG BERFIKIR APA / TOOL ACTION)
    let thoughtText = '';
    let thoughtIcon = '💭';
    if (isToolRunning) {
      thoughtIcon = '🔧';
      thoughtText = data.activeTool.action || `Running tool: ${data.activeTool.name}`;
    } else if (isBoss) {
      thoughtText = data.thinkingReason || '👑 Directing Autonomous Sovereign Swarm Architecture';
    } else if (data.thinkingReason) {
      thoughtText = data.thinkingReason;
    } else if (isWorking) {
      thoughtText = 'Executing precision operations with verified Exit Code 0';
    } else {
      thoughtText = data.role || 'Standby for multi-agent dispatch command';
    }

    // Truncate cleanly for crisp canvas display
    const cleanThought = thoughtText.replace(/\s+/g, ' ').trim();
    const displayThought = cleanThought.length > 46 ? cleanThought.slice(0, 44) + '…' : cleanThought;

    // Thought bubble icon & text bar
    ctx.font = '600 20px "Inter", "Segoe UI", sans-serif';
    ctx.fillStyle = isToolRunning ? '#fda4af' : (isThinking ? '#fde047' : '#94a3b8');
    ctx.fillText(`${thoughtIcon} ${displayThought}`, 24, 106);
  }

  pickRandomOfficeDestination(ag) {
    const spots = [
      // Central hallway promenade
      { x: (Math.random() - 0.5) * 1.8, z: -1.0 + Math.random() * 8.0 },
      { x: (Math.random() - 0.5) * 1.6, z: 0.5 + Math.random() * 6.5 },
      // Whiteboard sprint inspection
      { x: -7.2 + (Math.random() - 0.5) * 2.0, z: -3.2 + (Math.random() - 0.5) * 1.0 },
      // Panoramic Skyline Windows viewing
      { x: -12.5 + (Math.random() - 0.5) * 1.5, z: 1.0 + Math.random() * 4.5 },
      // Coffee & Espresso refreshment corner
      { x: 12.0 + (Math.random() - 0.5) * 1.5, z: 4.5 + (Math.random() - 0.5) * 1.5 },
      // IT Server Rack telemetry check
      { x: 12.0 + (Math.random() - 0.5) * 1.5, z: -2.2 + (Math.random() - 0.5) * 1.5 },
      // Front of North Wall headquarters plaque
      { x: (Math.random() - 0.5) * 3.5, z: -3.6 },
    ];
    const picked = spots[Math.floor(Math.random() * spots.length)];
    ag.wanderState.destPos.set(picked.x, 0, picked.z);
  }

  mountCameraHUDControls() {
    const pane = document.getElementById('office-pane-3d');
    if (!pane) return;
    let hud = pane.querySelector('#office-viewport-controls');
    if (!hud) {
      hud = document.createElement('div');
      hud.className = 'office-viewport-controls';
      hud.id = 'office-viewport-controls';
      hud.innerHTML = `
        <button type="button" class="office-view-btn" id="btn-office-zoom-in" title="Zoom In (+)">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
          <span>Zoom In</span>
        </button>
        <button type="button" class="office-view-btn" id="btn-office-zoom-out" title="Zoom Out (-)">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
          <span>Zoom Out</span>
        </button>
        <button type="button" class="office-view-btn" id="btn-office-reset-view" title="Reset View (R)">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
          <span>Reset View</span>
        </button>
      `;
      pane.appendChild(hud);
    }

    const btnIn = hud.querySelector('#btn-office-zoom-in');
    if (btnIn && !btnIn._hasBound) {
      btnIn._hasBound = true;
      btnIn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.zoomIn();
      });
    }
    const btnOut = hud.querySelector('#btn-office-zoom-out');
    if (btnOut && !btnOut._hasBound) {
      btnOut._hasBound = true;
      btnOut.addEventListener('click', (e) => {
        e.stopPropagation();
        this.zoomOut();
      });
    }
    const btnReset = hud.querySelector('#btn-office-reset-view');
    if (btnReset && !btnReset._hasBound) {
      btnReset._hasBound = true;
      btnReset.addEventListener('click', (e) => {
        e.stopPropagation();
        this.resetCamera();
      });
    }
  }

  setupInteractions() {
    let isDragging = false;
    let dragMode = null; // 'orbit' | 'pan'
    let dragStartX = 0;
    let dragStartY = 0;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const wakeUpInteractions = () => {
      this.isInteracting = true;
      if (this.interactTimeout) clearTimeout(this.interactTimeout);
      this.interactTimeout = setTimeout(() => {
        this.isInteracting = false;
      }, 1500);
    };
    this.wakeUpInteractions = wakeUpInteractions;

    const onPointerMove = (e) => {
      if (this.isPaused || !this.isRunning) return;
      if (!isDragging && e.target !== this.canvas && e.target !== this.container) return;

      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      wakeUpInteractions();

      if (isDragging) {
        const deltaX = e.clientX - prevMouseX;
        const deltaY = e.clientY - prevMouseY;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;

        if (dragMode === 'pan') {
          const panSpeed = 0.016 * Math.max(0.4, (this.camPosTarget.y / 8));
          const right = new THREE.Vector3();
          this.camera.getWorldDirection(right);
          const forward = new THREE.Vector3(right.x, 0, right.z).normalize();
          right.cross(this.camera.up).normalize();

          const moveX = -deltaX * panSpeed;
          const moveZ = -deltaY * panSpeed;
          const shiftX = right.x * moveX + forward.x * moveZ;
          const shiftZ = right.z * moveX + forward.z * moveZ;

          this.camPosTarget.x = Math.max(-20, Math.min(20, this.camPosTarget.x + shiftX));
          this.camPosTarget.z = Math.max(-16, Math.min(20, this.camPosTarget.z + shiftZ));
          this.camTarget.x = Math.max(-18, Math.min(18, this.camTarget.x + shiftX));
          this.camTarget.z = Math.max(-14, Math.min(14, this.camTarget.z + shiftZ));
          this.canvas.style.cursor = 'grabbing';
          return;
        }

        if (dragMode === 'orbit') {
          const angle = -deltaX * 0.005;
          const curX = this.camPosTarget.x - this.camTarget.x;
          const curZ = this.camPosTarget.z - this.camTarget.z;
          this.camPosTarget.x = this.camTarget.x + (curX * Math.cos(angle) - curZ * Math.sin(angle));
          this.camPosTarget.z = this.camTarget.z + (curX * Math.sin(angle) + curZ * Math.cos(angle));
          this.camPosTarget.y = Math.max(3.0, Math.min(18.0, this.camPosTarget.y + deltaY * 0.02));
          this.canvas.style.cursor = 'grabbing';
          return;
        }
      }

      // Raycast hover check over agent avatars
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const hitCandidates = this.agents.map((ag) => ag.group);
      const intersects = this.raycaster.intersectObjects(hitCandidates, true);
      if (intersects.length > 0) {
        const hitAgent = this.findAgentFromObject(intersects[0].object);
        if (hitAgent) {
          this.canvas.style.cursor = 'pointer';
          this.hoveredAgent = hitAgent;
          return;
        }
      }

      this.canvas.style.cursor = 'grab';
      this.hoveredAgent = null;
    };

    const onPointerDown = (e) => {
      if (this.isPaused || !this.isRunning) return;
      wakeUpInteractions();

      dragStartX = e.clientX;
      dragStartY = e.clientY;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
      isDragging = true;
      this.canvas.classList.add('is-dragging');

      // Pan mode: Right-click, Middle-click, or Shift + Left-click
      if (e.button === 1 || e.button === 2 || (e.button === 0 && e.shiftKey)) {
        dragMode = 'pan';
        return;
      }

      // Orbit mode: Normal Left-click
      if (e.button === 0) {
        dragMode = 'orbit';
      }
    };

    const onPointerUp = (e) => {
      wakeUpInteractions();
      this.canvas.classList.remove('is-dragging');

      if (isDragging) {
        const dist = Math.hypot(e.clientX - dragStartX, e.clientY - dragStartY);
        if (dist < 8 && e.button === 0 && !e.shiftKey) {
          // Click without drag: check if clicked on an agent or desk to focus camera!
          const rect = this.canvas.getBoundingClientRect();
          this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
          this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
          this.raycaster.setFromCamera(this.mouse, this.camera);

          const hitCandidates = this.agents.map((ag) => ag.group);
          const intersects = this.raycaster.intersectObjects(hitCandidates, true);
          if (intersects.length > 0) {
            const hitAgent = this.findAgentFromObject(intersects[0].object);
            if (hitAgent) {
              const now = performance.now();
              const isDoubleClick = (this._lastAgentClickTime && (now - this._lastAgentClickTime < 380) && this._lastClickedAgent === hitAgent);
              this._lastAgentClickTime = now;
              this._lastClickedAgent = hitAgent;

              this.selectAgent(hitAgent);
              // Smoothly glide camera down to this agent's workstation
              this.camTarget.set(hitAgent.data.deskPos.x, 1.10, hitAgent.data.deskPos.z);
              this.camPosTarget.set(hitAgent.data.deskPos.x, 2.40, hitAgent.data.deskPos.z + 3.20);

              if (isDoubleClick) {
                if (typeof window.openAgentStudio === 'function') {
                  window.openAgentStudio(hitAgent.data.id || hitAgent.data.persona);
                }
              }
            }
          } else if (this.floorMesh) {
            const floorHits = this.raycaster.intersectObject(this.floorMesh, false);
            if (floorHits.length > 0) {
              // Clicked empty floor: reset camera to overview & hide HUD!
              this.resetCamera();
              this.hideHoloHud();
            }
          }
        }
        isDragging = false;
        dragMode = null;
        this.canvas.style.cursor = 'grab';
      }
    };

    const onWheel = (e) => {
      if (this.isPaused || !this.isRunning) return;
      e.preventDefault();
      wakeUpInteractions();
      this.zoom(Math.sign(e.deltaY));
    };

    const onContextMenu = (e) => {
      e.preventDefault(); // Prevent browser context menu so right-drag pan works smoothly
    };

    this.boundOnResize = () => {
      if (!this.container || !this.renderer || !this.camera) return;
      const w = this.container.clientWidth;
      const h = this.container.clientHeight;
      if (w === 0 || h === 0) return;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    };

    this.boundOnVisibilityChange = () => {
      if (document.hidden) {
        this.pause();
      } else {
        const isOfficeActive = document.getElementById('view-office') && document.getElementById('view-office').classList.contains('active');
        if (isOfficeActive) {
          this.resume();
          this.checkRosterChanges();
        }
      }
    };

    this.interactionListeners = {
      onPointerMove,
      onPointerDown,
      onPointerUp,
      onWheel,
      onContextMenu,
    };

    this.attachInteractionListeners();
    this.mountCameraHUDControls();

    const onKeyDown = (e) => {
      if (this.isPaused || !this.isRunning) return;
      if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable)) return;
      if (e.key === '+' || e.key === '=') {
        this.zoomIn();
      } else if (e.key === '-' || e.key === '_') {
        this.zoomOut();
      } else if (e.key === 'r' || e.key === 'R' || e.key === 'Home') {
        this.resetCamera();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    this.boundOnKeyDown = onKeyDown;

    window.addEventListener('resize', this.boundOnResize);
    document.addEventListener('visibilitychange', this.boundOnVisibilityChange);
  }

  attachInteractionListeners() {
    if (this.isInteractionsAttached || !this.canvas || !this.interactionListeners) return;
    this.canvas.addEventListener('pointermove', this.interactionListeners.onPointerMove);
    this.canvas.addEventListener('pointerdown', this.interactionListeners.onPointerDown);
    window.addEventListener('pointerup', this.interactionListeners.onPointerUp);
    this.canvas.addEventListener('wheel', this.interactionListeners.onWheel, { passive: false });
    this.canvas.addEventListener('contextmenu', this.interactionListeners.onContextMenu);
    this.isInteractionsAttached = true;
  }

  detachInteractionListeners() {
    if (!this.isInteractionsAttached || !this.canvas || !this.interactionListeners) return;
    this.canvas.removeEventListener('pointermove', this.interactionListeners.onPointerMove);
    this.canvas.removeEventListener('pointerdown', this.interactionListeners.onPointerDown);
    window.removeEventListener('pointerup', this.interactionListeners.onPointerUp);
    this.canvas.removeEventListener('wheel', this.interactionListeners.onWheel);
    this.canvas.removeEventListener('contextmenu', this.interactionListeners.onContextMenu);
    this.isInteractionsAttached = false;
  }

  findAgentFromObject(object) {
    let curr = object;
    while (curr) {
      if (curr.userData && curr.userData.agentData) {
        const id = curr.userData.agentData.id;
        return this.agents.find((a) => a.data.id === id);
      }
      curr = curr.parent;
    }
    return null;
  }

  selectAgent(agentWrapper, isInitialBoot = false) {
    if (!agentWrapper) return;
    this.selectedAgent = agentWrapper;
    this.trackingAgent = agentWrapper;

    // Trigger cyber energetic reaction animation (wave & eye pulse)
    agentWrapper.clickReactionTimer = 1.2;

    if (this.selectionRing) {
      this.selectionRing.visible = true;
      if (this.selectionRing.material) {
        this.selectionRing.material.color.setHex(agentWrapper.data.color || 0x00f2fe);
      }
      this.selectionRing.position.set(agentWrapper.data.deskPos.x, 0.02, agentWrapper.data.deskPos.z);
    }

    if (!isInitialBoot && agentWrapper.data && agentWrapper.data.deskPos) {
      this.camTarget.set(agentWrapper.data.deskPos.x, 1.10, agentWrapper.data.deskPos.z);
      this.camPosTarget.set(agentWrapper.data.deskPos.x, 2.40, agentWrapper.data.deskPos.z + 3.20);
      this.showHoloHud(agentWrapper);
    }

    if (typeof window.highlightOfficeDockItem === 'function') {
      window.highlightOfficeDockItem(agentWrapper.data.id);
    }

    if (typeof window.onOfficeAgentSelected === 'function') {
      window.onOfficeAgentSelected(agentWrapper.data);
    }
  }

  showHoloHud(agentWrapper) {
    if (!agentWrapper || !agentWrapper.data) return;
    const hud = document.getElementById('agent-holo-hud');
    if (!hud) return;

    const data = agentWrapper.data;
    const titleEl = hud.querySelector('#agent-holo-title');
    const roleEl = hud.querySelector('#agent-holo-role');
    const iconEl = hud.querySelector('#agent-holo-icon');

    if (titleEl) titleEl.textContent = data.name || data.persona || 'Agent';
    if (roleEl) roleEl.textContent = data.role || 'Autonomous Specialist';
    if (iconEl) iconEl.textContent = data.icon || (data.persona === 'leader' ? '👑' : '⚡');

    if (!hud._boundActions) {
      hud._boundActions = true;
      hud.querySelector('#btn-agent-holo-close')?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.hideHoloHud();
      });

      hud.querySelector('#btn-agent-holo-studio')?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.hideHoloHud();
        if (this.selectedAgent && typeof window.openAgentStudio === 'function') {
          window.openAgentStudio(this.selectedAgent.data.id || this.selectedAgent.data.persona);
        }
      });
    }

    hud.style.display = 'block';
    this.updateHoloHudPosition();
  }

  hideHoloHud() {
    const hud = document.getElementById('agent-holo-hud');
    if (hud) hud.style.display = 'none';
  }

  updateHoloHudPosition() {
    const hud = document.getElementById('agent-holo-hud');
    if (!hud || hud.style.display === 'none' || !this.selectedAgent || !this.camera || !this.canvas) return;

    const pos = new THREE.Vector3();
    pos.copy(this.selectedAgent.group.position);
    pos.y += 1.45;
    pos.project(this.camera);

    if (pos.z < 1.0) {
      const rect = this.canvas.getBoundingClientRect();
      const sx = ((pos.x + 1) / 2) * rect.width + rect.left;
      const sy = ((-pos.y + 1) / 2) * rect.height + rect.top;
      hud.style.position = 'fixed';
      hud.style.left = `${sx}px`;
      hud.style.top = `${sy}px`;
    } else {
      hud.style.display = 'none';
    }
  }

  selectAgentById(agentId, isInitialBoot = false) {
    let ag = this.agents.find((a) =>
      a.data.id === agentId ||
      a.data.sessionId === agentId ||
      a.data.persona === agentId ||
      ('agent-' + a.data.persona) === agentId ||
      ('session-' + a.data.persona) === agentId
    );

    if (ag) {
      this.selectAgent(ag, isInitialBoot);
      return ag;
    }

    if (this.agents.length > 0) {
      this.selectAgent(this.agents[0], isInitialBoot);
      return this.agents[0];
    }
    return null;
  }

  resetCamera() {
    this.isLockView = false;
    this.trackingAgent = null;
    this.camTarget.set(0, 1.20, 1.10);
    this.camPosTarget.set(0, 6.20, 11.80);
    if (this.camera) {
      this.camera.fov = 50;
      this.camera.updateProjectionMatrix();
    }
  }

  zoomIn(amount = 1.0) {
    this.zoom(-amount);
  }

  zoomOut(amount = 1.0) {
    this.zoom(amount);
  }

  zoom(directionFactor) {
    const zoomSpeed = 0.85;
    const dir = new THREE.Vector3().subVectors(this.camPosTarget, this.camTarget).normalize();
    const curDist = this.camPosTarget.distanceTo(this.camTarget);
    const newDist = Math.max(3.2, Math.min(26.0, curDist + directionFactor * zoomSpeed * 1.5));
    this.camPosTarget.copy(this.camTarget).addScaledVector(dir, newDist);
  }

  setAgentState(agentId, newState) {
    if (!agentId) return;
    const target = String(agentId).trim().toLowerCase();
    const ag = this.agents.find((a) => {
      const p = (a.data.persona || '').toLowerCase();
      const aid = (a.data.id || '').toLowerCase();
      const sid = (a.data.sessionId || '').toLowerCase();
      return (
        aid === target ||
        sid === target ||
        p === target ||
        ('agent-' + p) === target ||
        ('session-' + p) === target ||
        ((target === 'default' || target === 'mrflow' || target === 'agent-default') && (p === 'default' || aid === 'agent-default')) ||
        (p && target.includes(p)) ||
        (aid && target.includes(aid))
      );
    });

    if (ag) {
      ag.data.state = newState;
      ag.group.visible = true;
      if (ag.slotGroup) ag.slotGroup.visible = true;

      // Update badge
      if (ag.badgeCanvas) {
        this.drawBadge(ag.badgeCanvas.getContext('2d'), ag.data);
      }
      if (ag.badgeSprite && ag.badgeSprite.material && ag.badgeSprite.material.map) {
        ag.badgeSprite.material.map.needsUpdate = true;
      }

      // Brighten monitors when working
      if (ag.screens && ag.screens.length > 0) {
        ag.screens.forEach((s) => {
          if (s.material) {
            s.material.opacity = (newState === 'working') ? 0.98 : 0.65;
          }
        });
      }

      if (typeof window.updateOfficeDockAgentState === 'function') {
        window.updateOfficeDockAgentState(ag.data.id, newState);
      }
    }
  }

  setAgentThinkingReason(agentId, reasonText, isThinking = true) {
    if (!agentId) return;
    const target = String(agentId).trim().toLowerCase();
    const ag = this.agents.find((a) => {
      const p = (a.data.persona || '').toLowerCase();
      const aid = (a.data.id || '').toLowerCase();
      const sid = (a.data.sessionId || '').toLowerCase();
      return (
        aid === target ||
        sid === target ||
        p === target ||
        ('agent-' + p) === target ||
        ('session-' + p) === target ||
        ((target === 'default' || target === 'mrflow' || target === 'agent-default') && (p === 'default' || aid === 'agent-default')) ||
        (p && target.includes(p)) ||
        (aid && target.includes(aid))
      );
    });

    if (ag) {
      ag.data.thinkingReason = reasonText || '';
      ag.data.isThinking = !!isThinking;
      if (ag.badgeCanvas) {
        this.drawBadge(ag.badgeCanvas.getContext('2d'), ag.data);
      }
      if (ag.badgeSprite && ag.badgeSprite.material && ag.badgeSprite.material.map) {
        ag.badgeSprite.material.map.needsUpdate = true;
      }
    }
  }

  setAgentActiveTool(agentId, toolName, toolAction, isRunning = true) {
    if (!agentId) return;
    const target = String(agentId).trim().toLowerCase();
    const ag = this.agents.find((a) => {
      const p = (a.data.persona || '').toLowerCase();
      const aid = (a.data.id || '').toLowerCase();
      const sid = (a.data.sessionId || '').toLowerCase();
      return (
        aid === target ||
        sid === target ||
        p === target ||
        ('agent-' + p) === target ||
        ('session-' + p) === target ||
        ((target === 'default' || target === 'mrflow' || target === 'agent-default') && (p === 'default' || aid === 'agent-default')) ||
        (p && target.includes(p)) ||
        (aid && target.includes(aid))
      );
    });

    if (ag) {
      if (isRunning && toolName) {
        ag.data.activeTool = { name: toolName, action: toolAction || '' };
        ag.data.state = 'working';
        if (ag.wanderState && ag.wanderState.status !== 'desk') {
          ag.wanderState.status = 'returning_to_desk';
        }
      } else {
        ag.data.activeTool = null;
      }
      if (ag.badgeCanvas) {
        this.drawBadge(ag.badgeCanvas.getContext('2d'), ag.data);
      }
      if (ag.badgeSprite && ag.badgeSprite.material && ag.badgeSprite.material.map) {
        ag.badgeSprite.material.map.needsUpdate = true;
      }
    }
  }

  setSoloSpecialist(personaId) {
    this.soloSpecialistId = personaId;
    localStorage.setItem('xflow_chat_persona', personaId);
    if (window.AVAILABLE_PERSONAS) {
      this.syncPersonas(window.AVAILABLE_PERSONAS);
    }
  }

  updateAgentConfig(agentId, { model, provider, account, persona, name, role, icon, state }) {
    const ag = this.agents.find(a =>
      a.data.id === agentId ||
      a.data.sessionId === agentId ||
      a.data.persona === agentId ||
      ('agent-' + a.data.persona) === agentId ||
      ('session-' + a.data.persona) === agentId
    );
    if (ag) {
      if (model) ag.data.model = model;
      if (provider) ag.data.provider = provider;
      if (account) ag.data.account = account;
      if (persona) ag.data.persona = persona;
      if (name) ag.data.name = name;
      if (role) ag.data.role = role;
      if (icon) ag.data.icon = icon;
      if (state) this.setAgentState(agentId, state);

      this.drawBadge(ag.badgeCanvas.getContext('2d'), ag.data);
      ag.badgeSprite.material.map.needsUpdate = true;
      this.saveAgentRegistry(this.agents.map(a => a.data));
    }
  }

  animate() {
    if (!this.isRunning || this.isPaused) return;

    if (document.hidden) {
      this.pause();
      return;
    }
    const isOfficeActive = document.getElementById('view-office') && document.getElementById('view-office').classList.contains('active');
    if (!isOfficeActive) {
      this.pause();
      return;
    }
    if (this.container && (this.container.clientWidth === 0 || this.container.clientHeight === 0)) {
      this.pause();
      return;
    }

    const id = requestAnimationFrame(this.animate);
    this.rafId = id;
    this.animFrameId = id;

    const minFrameInterval = (this.isSoftwareRenderer || window.isLowPowerMode) ? 42.0 : 32.5;
    const now = performance.now();
    if (this.lastFrameTime && (now - this.lastFrameTime < minFrameInterval)) {
      return;
    }
    this.lastFrameTime = now;

    const delta = this.clock.getDelta();
    const time = this.clock.getElapsedTime();

    // Smooth Camera Damping (LERP)
    this.camera.position.lerp(this.camPosTarget, 0.06);
    this.camera.lookAt(this.camTarget);

    // Wall Clock Second Hand Sweeping
    if (this.wallClockSecondHand) {
      this.wallClockSecondHand.rotation.z = -time * 1.05;
    }

    // Blinking Server LEDs
    if (this.serverLeds && this.serverLeds.length > 0) {
      this.serverLeds.forEach((led, i) => {
        led.visible = Math.sin(time * 6.0 + i * 2.0) > -0.2;
      });
    }

    // Animate Each Agent (Typing at desk when working, autonomous wandering when idle!)
    this.agents.forEach((ag, idx) => {
      if (!ag.wanderState) {
        ag.wanderState = {
          status: 'desk', // 'desk' | 'walking' | 'resting' | 'returning_to_desk'
          destPos: ag.data.deskPos.clone(),
          timer: 3.5 + (idx * 2.5),
          walkPhase: idx * 1.5,
        };
      }

      const isToolRunning = ag.data && !!ag.data.activeTool && !!ag.data.activeTool.name;
      const isWorking = ag.data && (ag.data.state === 'working' || ag.data.isThinking || isToolRunning);
      const phase = time * 2.0 + (ag.data.typingPhase || 0);

      if (isWorking) {
        // PRIORITY 1: WORKING -> If agent was wandering, sprint back to desk immediately!
        if (ag.wanderState.status !== 'desk') {
          const dx = ag.data.deskPos.x - ag.group.position.x;
          const dz = ag.data.deskPos.z - ag.group.position.z;
          const dist = Math.hypot(dx, dz);
          if (dist > 0.08) {
            const moveAng = Math.atan2(dx, dz);
            ag.group.rotation.y = THREE.MathUtils.lerp(ag.group.rotation.y, moveAng, 0.22);
            const step = Math.min(dist, 2.8 * delta);
            ag.group.position.x += Math.sin(moveAng) * step;
            ag.group.position.z += Math.cos(moveAng) * step;
            ag.wanderState.walkPhase += delta * 14.0;
            ag.legL.rotation.x = Math.sin(ag.wanderState.walkPhase) * 0.60;
            ag.legR.rotation.x = -Math.sin(ag.wanderState.walkPhase) * 0.60;
            ag.armL.rotation.x = -Math.sin(ag.wanderState.walkPhase) * 0.45;
            ag.armR.rotation.x = Math.sin(ag.wanderState.walkPhase) * 0.45;
            ag.group.position.y = Math.abs(Math.sin(ag.wanderState.walkPhase)) * 0.06;
          } else {
            // Arrived at desk! Sit down
            ag.wanderState.status = 'desk';
            ag.group.position.copy(ag.data.deskPos);
            ag.group.rotation.y = ag.data.deskFacingAngle;
            ag.legL.rotation.set(0, 0, 0);
            ag.legR.rotation.set(0, 0, 0);
          }
        } else {
          // At desk working: Active typing bursts on keyboard
          ag.group.position.copy(ag.data.deskPos);
          ag.group.rotation.y = ag.data.deskFacingAngle;
          const burstRate = isToolRunning ? 26.0 : 16.0;
          const burstAmp = isToolRunning ? 0.16 : 0.12;
          const burst = Math.sin(time * burstRate);
          ag.armL.rotation.set(-1.15 + burst * burstAmp, 0.18, -0.08);
          ag.armR.rotation.set(-1.15 - burst * burstAmp, -0.18, 0.08);
          ag.head.rotation.set(0.10 + Math.sin(phase * 1.5) * 0.04, Math.sin(phase) * 0.14, 0);
          ag.group.position.y = Math.sin(phase * 2.0) * 0.01;
          ag.legL.rotation.set(0, 0, 0);
          ag.legR.rotation.set(0, 0, 0);

          if (ag.faceMesh && ag.faceMesh.material) {
            ag.faceMesh.material.opacity = (isToolRunning ? 1.0 : 0.95) + Math.sin(time * 8.0) * 0.05;
          }
        }
      } else {
        // IDLE: Autonomous wandering tak terarah di area kantor!
        const ws = ag.wanderState;

        if (ws.status === 'desk') {
          // Sitting comfortably at desk
          ag.group.position.copy(ag.data.deskPos);
          ag.group.rotation.y = ag.data.deskFacingAngle;
          const breath = Math.sin(time * 1.8 + idx);
          ag.group.position.y = breath * 0.015;
          ag.armL.rotation.set(-0.35 + breath * 0.03, 0.12, -0.12);
          ag.armR.rotation.set(-0.35 + breath * 0.03, -0.12, 0.12);
          ag.head.rotation.set(0.04 + breath * 0.02, Math.sin(time * 0.5 + idx) * 0.12, 0);
          ag.legL.rotation.set(0, 0, 0);
          ag.legR.rotation.set(0, 0, 0);

          if (ag.faceMesh && ag.faceMesh.material) {
            ag.faceMesh.material.opacity = 0.85 + breath * 0.08;
          }

          ws.timer -= delta;
          if (ws.timer <= 0) {
            // Get up and stroll!
            this.pickRandomOfficeDestination(ag);
            ws.status = 'walking';
          }
        } else if (ws.status === 'walking') {
          // Walking to chosen spot
          const dx = ws.destPos.x - ag.group.position.x;
          const dz = ws.destPos.z - ag.group.position.z;
          const dist = Math.hypot(dx, dz);
          if (dist > 0.12) {
            const moveAng = Math.atan2(dx, dz);
            ag.group.rotation.y = THREE.MathUtils.lerp(ag.group.rotation.y, moveAng, 0.14);
            const step = Math.min(dist, 1.25 * delta);
            ag.group.position.x += Math.sin(moveAng) * step;
            ag.group.position.z += Math.cos(moveAng) * step;
            ws.walkPhase += delta * 8.5;

            // Leg & arm walking swing
            ag.legL.rotation.x = Math.sin(ws.walkPhase) * 0.50;
            ag.legR.rotation.x = -Math.sin(ws.walkPhase) * 0.50;
            ag.armL.rotation.x = -Math.sin(ws.walkPhase) * 0.35;
            ag.armR.rotation.x = Math.sin(ws.walkPhase) * 0.35;
            ag.group.position.y = Math.abs(Math.sin(ws.walkPhase)) * 0.05;
            ag.head.rotation.set(0.04, Math.sin(ws.walkPhase * 0.5) * 0.12, 0);
          } else {
            // Arrived! Rest & inspect surroundings
            ws.status = 'resting';
            ws.timer = 5.0 + Math.random() * 8.0;
            ag.legL.rotation.set(0, 0, 0);
            ag.legR.rotation.set(0, 0, 0);
            ag.armL.rotation.set(-0.15, 0.10, -0.05);
            ag.armR.rotation.set(-0.15, -0.10, 0.05);
          }
        } else if (ws.status === 'resting') {
          // Standing casually at the spot, looking around
          const breath = Math.sin(time * 1.8 + idx);
          ag.group.position.y = breath * 0.015;
          ag.head.rotation.set(0.04 + breath * 0.02, Math.sin(time * 0.7 + idx) * 0.28, 0);
          ag.armL.rotation.set(-0.15 + breath * 0.02, 0.10, -0.05);
          ag.armR.rotation.set(-0.15 + breath * 0.02, -0.10, 0.05);
          ag.legL.rotation.set(0, 0, 0);
          ag.legR.rotation.set(0, 0, 0);

          ws.timer -= delta;
          if (ws.timer <= 0) {
            // 45% chance: walk to another spot in the office
            // 55% chance: walk back to desk to rest
            if (Math.random() < 0.45) {
              this.pickRandomOfficeDestination(ag);
              ws.status = 'walking';
            } else {
              ws.destPos.copy(ag.data.deskPos);
              ws.status = 'returning_to_desk';
            }
          }
        } else if (ws.status === 'returning_to_desk') {
          // Walking casually back to desk
          const dx = ag.data.deskPos.x - ag.group.position.x;
          const dz = ag.data.deskPos.z - ag.group.position.z;
          const dist = Math.hypot(dx, dz);
          if (dist > 0.08) {
            const moveAng = Math.atan2(dx, dz);
            ag.group.rotation.y = THREE.MathUtils.lerp(ag.group.rotation.y, moveAng, 0.14);
            const step = Math.min(dist, 1.25 * delta);
            ag.group.position.x += Math.sin(moveAng) * step;
            ag.group.position.z += Math.cos(moveAng) * step;
            ws.walkPhase += delta * 8.5;

            ag.legL.rotation.x = Math.sin(ws.walkPhase) * 0.50;
            ag.legR.rotation.x = -Math.sin(ws.walkPhase) * 0.50;
            ag.armL.rotation.x = -Math.sin(ws.walkPhase) * 0.35;
            ag.armR.rotation.x = Math.sin(ws.walkPhase) * 0.35;
            ag.group.position.y = Math.abs(Math.sin(ws.walkPhase)) * 0.05;
            ag.head.rotation.set(0.04, Math.sin(ws.walkPhase * 0.5) * 0.12, 0);
          } else {
            // Returned to desk chair! Sit down
            ws.status = 'desk';
            ag.group.position.copy(ag.data.deskPos);
            ag.group.rotation.y = ag.data.deskFacingAngle;
            ag.legL.rotation.set(0, 0, 0);
            ag.legR.rotation.set(0, 0, 0);
            ws.timer = 8.0 + Math.random() * 16.0; // Rest at desk for 8-24 seconds
          }
        }
      }

      // Click reaction animation (Energetic cyber wave / salute)
      if (ag.clickReactionTimer && ag.clickReactionTimer > 0) {
        ag.clickReactionTimer -= delta;
        const wave = Math.sin((1.2 - ag.clickReactionTimer) * 14.0);
        ag.armR.rotation.set(-2.1 + wave * 0.45, 0.15, 0.35);
        ag.head.rotation.set(-0.12, Math.sin(time * 8.0) * 0.10, 0);
        if (ag.faceMesh && ag.faceMesh.material) {
          ag.faceMesh.material.opacity = 1.0;
        }
      }

      // Billboard overhead badge toward camera
      if (ag.badgeSprite) {
        ag.badgeSprite.visible = true;
      }
    });

    this.renderer.render(this.scene, this.camera);
    this.updateHoloHudPosition();
  }

  pause() {
    this.isPaused = true;
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  resume() {
    if (!this.isRunning) return;
    this.isPaused = false;
    this.clock.start();
    if (!this.rafId) {
      this.rafId = requestAnimationFrame(this.animate);
    }
  }

  destroy() {
    this.isRunning = false;
    this.pause();
    if (this._rosterWatcherInterval) {
      clearInterval(this._rosterWatcherInterval);
      this._rosterWatcherInterval = null;
    }
    this.detachInteractionListeners();
    window.removeEventListener('resize', this.boundOnResize);
    document.removeEventListener('visibilitychange', this.boundOnVisibilityChange);
  }
}

window.SovereignOffice3D = SovereignOffice3D;
window.Office3D = SovereignOffice3D;

// Bridge helper to set all specialist agents to working/typing state during auditor council sessions
window.setSpecialistAuditorWorking = function(isWorking, reason) {
  const office = window.office3DInstance || window.Flowork3DSolo || window._sovereignOffice3DInstance;
  if (!office || !Array.isArray(office.agents)) return;
  office.agents.forEach(ag => {
    if (ag.data && !ag.data.isBoss && !ag.data.isTrainer) {
      const state = isWorking ? 'working' : 'idle';
      office.setAgentState(ag.data.id, state);
      if (typeof office.setAgentThinkingReason === 'function') {
        office.setAgentThinkingReason(ag.data.id, isWorking ? (reason || 'Auditing Flowork OS') : '', isWorking);
      }
    }
  });
};

window.setOfficeAgentThinking = function(agentId, reasonText, isThinking = true) {
  const office = window.office3DInstance || window.Flowork3DSolo || window._sovereignOffice3DInstance;
  if (office && typeof office.setAgentThinkingReason === 'function') {
    office.setAgentThinkingReason(agentId, reasonText, isThinking);
  }
};

window.setOfficeAgentTool = function(agentId, toolName, toolAction, isRunning = true) {
  const office = window.office3DInstance || window.Flowork3DSolo || window._sovereignOffice3DInstance;
  if (office && typeof office.setAgentActiveTool === 'function') {
    office.setAgentActiveTool(agentId, toolName, toolAction, isRunning);
  }
};

export default SovereignOffice3D;
