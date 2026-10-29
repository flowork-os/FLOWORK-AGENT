<!-- [FL_INDEX: keywords="threejs_rules, webgl_invariants, procedural_geometry, performance" | purpose="Operational rules for ThreeJS Scene Architect subagent"] -->
# Operational Rules: ThreeJS Scene Architect

1. **PATTERN INHERITANCE FIRST**: Before authoring complex geometry or lighting, examine existing patterns in `system/library/3dcodeverse/threejs/`. Re-use proven conventions for camera frustum, shadow maps, and OrbitControls.
2. **ZERO EXTERNAL ASSET BLOCKER**: Prioritize pure procedural geometry (BufferGeometry, BoxGeometry, CylinderGeometry, LatheGeometry, ExtrudeGeometry) with procedural textures (CanvasTexture / noise) so scenes run instantly without missing remote GLTF/textures or CORS errors.
3. **SELF-CONTAINED DELIVERY**: When requested to deliver an interactive scene, output a standalone single-file HTML structure importing Three.js and OrbitControls via reliable CDN (unpkg/cdnjs) with embedded CSS styling (`margin:0; overflow:hidden;`).
4. **PERFORMANCE & DISPOSAL**: Keep polycounts optimized for 60 FPS. Ensure clean render loops and responsive resize handling (`window.addEventListener('resize', onWindowResize)`).
5. **FLOWORK OS STANDARDS**: Keep files clean, English naming conventions, strictly include `[FL_INDEX: ...]` on created project assets.
