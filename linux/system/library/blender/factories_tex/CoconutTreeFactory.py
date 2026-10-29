# [FL_INDEX: keywords="blender_factory, procedural_3d, CoconutTreeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CoconutTreeFactory | Category: factories_tex
# Prompt: A 3D model of a coconut palm tree rendered from a side perspective. The tree features a tall, curved trunk with a ringed, ridged surface, a rough fibrous crown base where fronds emerge, and multiple long feathery pinnate fronds spreading outward at the top.

"""Standalone CoconutTreeFactory with textures/materials.

    * shader_trunk           -> palm trunk (voronoi cracks + horizontal wave
                                banding from old frond scars)
    * shader_top_core        -> crown/top-core bulge at the trunk tip
                                (Voronoi + Wave, dark/bright color ramp)
    * shader_leaf_material   -> palm frond green (from leaf_palm_tree.py)
    * shader_coconut_green_shader -> green unripe coconut husks

Coconut trees are natural, never worn or weathered — NO wear_tear applied.

Per-part material assignment:
    trunk   slot 0  shader_trunk
    crown   slot 1  shader_top_core
    frond   slot 2  shader_leaf_material
    coconut slot 3  shader_coconut_green_shader
"""


import colorsys
import math
import os
import random

import bmesh
import bpy
import numpy as np

# ── parse seed ────────────────────────────────────────────────────────────────

SEED = int(os.environ.get("SEED", 0))
random.seed(SEED)
np.random.seed(SEED)

# ── helpers ───────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def _hsv_to_rgba(h, s, v):
    h = float(h) % 1.0
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, min(1.0, float(v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _fac_output(node):
    """Return the Fac/Factor output (Blender 5.0 renamed it)."""

    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

# ── Materials ─────────────────────────────────────────────────────────────────

def create_trunk_material():
    """Palm trunk shader — mirrors shader_trunk in coconut_tree.py.

    Uses Voronoi (4D) + Wave (Z bands) combined through a ColorRamp from a
    brownish HSV palette, plus a secondary cheby Voronoi colorramp for fine
    dark speckling. Output roughness is driven by the fine Voronoi distance.
    """

    d_hsv = (
        float(np.random.uniform(0.02, 0.05)),
        float(np.random.uniform(0.01, 0.05)) if np.random.randint(0, 2) == 1
        else float(np.random.uniform(0.5, 0.8)),
        float(np.random.uniform(0.03, 0.09)),
    )
    b_hsv = d_hsv[:-1] + (float(np.random.uniform(0.1, 0.3)),)
    d_rgba = _hsv_to_rgba(*d_hsv)
    b_rgba = _hsv_to_rgba(*b_hsv)

    mat = bpy.data.materials.new("CoconutTrunk")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (900, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (600, 0)
    links.new(bsdf.outputs[0], output.inputs[0])

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-1000, 0)

    # Primary Voronoi (vertical bark cracks) + Wave Z bands (frond scars)
    voronoi_1 = nodes.new("ShaderNodeTexVoronoi")
    voronoi_1.location = (-750, 250)
    voronoi_1.voronoi_dimensions = "4D"
    voronoi_1.inputs["Scale"].default_value = 20.0
    links.new(tex_coord.outputs["Object"], voronoi_1.inputs["Vector"])

    wave = nodes.new("ShaderNodeTexWave")
    wave.location = (-750, 0)
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = float(np.random.uniform(1.0, 3.0))
    wave.inputs["Distortion"].default_value = 5.0
    # Detail Scale in 4.x corresponds to "Detail Scale" socket
    try:
        wave.inputs["Detail Scale"].default_value = 3.0
    except KeyError:
        pass
    links.new(tex_coord.outputs["Object"], wave.inputs["Vector"])

    mix_1 = nodes.new("ShaderNodeMix")
    mix_1.location = (-450, 150)
    mix_1.data_type = "RGBA"
    mix_1.inputs[0].default_value = 0.5
    links.new(voronoi_1.outputs["Distance"], mix_1.inputs[6])
    links.new(wave.outputs["Color"], mix_1.inputs[7])

    ramp_main = nodes.new("ShaderNodeValToRGB")
    ramp_main.location = (-180, 150)
    ramp_main.color_ramp.elements[0].position = 0.4682
    ramp_main.color_ramp.elements[0].color = d_rgba
    ramp_main.color_ramp.elements[1].position = 0.5591
    ramp_main.color_ramp.elements[1].color = b_rgba
    links.new(mix_1.outputs[2], ramp_main.inputs["Fac"])

    # Fine chebychev voronoi dark-speckle overlay
    voronoi_fine = nodes.new("ShaderNodeTexVoronoi")
    voronoi_fine.location = (-750, -250)
    voronoi_fine.voronoi_dimensions = "4D"
    voronoi_fine.distance = "CHEBYCHEV"
    voronoi_fine.inputs["Scale"].default_value = 100.0
    voronoi_fine.inputs["Randomness"].default_value = 1.0
    # Scale up coordinates for fine pattern
    mapping_fine = nodes.new("ShaderNodeMapping")
    mapping_fine.location = (-950, -250)
    mapping_fine.inputs["Scale"].default_value = (10.0, 10.0, 0.2)
    links.new(tex_coord.outputs["Object"], mapping_fine.inputs["Vector"])
    links.new(mapping_fine.outputs["Vector"], voronoi_fine.inputs["Vector"])

    ramp_fine = nodes.new("ShaderNodeValToRGB")
    ramp_fine.location = (-450, -250)
    ramp_fine.color_ramp.elements[0].position = 0.2818
    ramp_fine.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp_fine.color_ramp.elements[1].position = 0.3045
    ramp_fine.color_ramp.elements[1].color = (0.5284, 0.5034, 0.4327, 1.0)
    links.new(voronoi_fine.outputs["Distance"], ramp_fine.inputs["Fac"])

    mix_2 = nodes.new("ShaderNodeMix")
    mix_2.location = (150, 0)
    mix_2.data_type = "RGBA"
    mix_2.inputs[0].default_value = float(np.random.uniform(0.1, 0.3))
    links.new(ramp_main.outputs["Color"], mix_2.inputs[6])
    links.new(ramp_fine.outputs["Color"], mix_2.inputs[7])

    links.new(mix_2.outputs[2], bsdf.inputs["Base Color"])
    links.new(voronoi_fine.outputs["Distance"], bsdf.inputs["Roughness"])

    # Subtle bump from the primary voronoi for micro-bark relief
    bump = nodes.new("ShaderNodeBump")
    bump.location = (350, -200)
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.01
    links.new(voronoi_1.outputs["Distance"], bump.inputs["Height"])
    links.new(bump.outputs[0], bsdf.inputs["Normal"])

    return mat

def create_crown_material():
    """Top-core bulge shader — mirrors shader_top_core in coconut_tree.py.

    Voronoi (very fine) + Wave (distorted) blended, mapped through a dark/bright
    ColorRamp with HSV sampling identical to shader_top_core.
    """

    d_hsv = (
        float(np.random.uniform(0.02, 0.05)),
        float(np.random.uniform(0.3, 0.6)),
        float(np.random.uniform(0.01, 0.05)),
    )
    b_hsv = d_hsv[:1] + (
        float(np.random.uniform(0.6, 0.9)),
        float(np.random.uniform(0.3, 0.6)),
    )
    d_rgba = _hsv_to_rgba(*d_hsv)
    b_rgba = _hsv_to_rgba(*b_hsv)

    mat = bpy.data.materials.new("CoconutCrown")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (700, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (450, 0)
    links.new(bsdf.outputs[0], output.inputs[0])

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-900, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-700, 150)
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 0.1)
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.location = (-450, 200)
    voronoi.inputs["Scale"].default_value = float(np.random.uniform(100.0, 400.0))
    links.new(mapping.outputs["Vector"], voronoi.inputs["Vector"])

    wave = nodes.new("ShaderNodeTexWave")
    wave.location = (-450, -100)
    wave.inputs["Scale"].default_value = 2.0
    wave.inputs["Distortion"].default_value = 5.0
    try:
        wave.inputs["Detail"].default_value = 10.0
    except KeyError:
        pass
    links.new(tex_coord.outputs["Object"], wave.inputs["Vector"])

    mix = nodes.new("ShaderNodeMix")
    mix.location = (-150, 50)
    mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.4
    links.new(voronoi.outputs["Distance"], mix.inputs[6])
    links.new(wave.outputs["Color"], mix.inputs[7])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (100, 50)
    ramp.color_ramp.elements[0].position = 0.2409
    ramp.color_ramp.elements[0].color = d_rgba
    ramp.color_ramp.elements[1].position = 0.6045
    ramp.color_ramp.elements[1].color = b_rgba
    links.new(mix.outputs[2], ramp.inputs["Fac"])

    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(ramp.outputs["Alpha"], bsdf.inputs["Roughness"])

    return mat

def create_frond_material():
    """Palm frond shader — mirrors shader_leaf_material in leaf_palm_tree.py.

    Samples main_leaf_hsv (green) and modulates via an object-space noise
    texture through a HSV-interpolated ColorRamp. Principled+Translucent mix
    at 0.7 matches leaf_v2 for back-lit translucency.
    """

    main_hsv = (
        float(np.random.uniform(0.3, 0.36)),
        float(np.random.uniform(0.8, 1.0)),
        float(np.random.uniform(0.25, 0.45)),
    )
    # Slightly darker secondary shade for shaded areas
    sec_hsv = (main_hsv[0] + float(np.random.normal(0.0, 0.005)),
               main_hsv[1],
               main_hsv[2] * 0.7)
    main_rgba = _hsv_to_rgba(*main_hsv)
    sec_rgba = _hsv_to_rgba(*sec_hsv)

    mat = bpy.data.materials.new("CoconutFrond")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (800, 0)

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-550, 100)
    noise.inputs["Scale"].default_value = float(np.random.uniform(4.0, 8.0))
    noise.inputs["Detail"].default_value = 10.0
    noise.inputs["Roughness"].default_value = 0.7
    links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-300, 100)
    ramp.color_ramp.color_mode = "HSV"
    ramp.color_ramp.hue_interpolation = "NEAR"
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = sec_rgba
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = main_rgba
    links.new(_fac_output(noise), ramp.inputs["Fac"])

    # Principled for direct lit side
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (150, 250)
    bsdf.inputs["Roughness"].default_value = 0.55
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    # Translucent for back-lit glow
    translucent = nodes.new("ShaderNodeBsdfTranslucent")
    translucent.location = (150, -50)
    links.new(ramp.outputs["Color"], translucent.inputs["Color"])

    mix_shader = nodes.new("ShaderNodeMixShader")
    mix_shader.location = (500, 100)
    mix_shader.inputs["Fac"].default_value = 0.7
    links.new(translucent.outputs[0], mix_shader.inputs[1])
    links.new(bsdf.outputs[0], mix_shader.inputs[2])
    links.new(mix_shader.outputs[0], output.inputs["Surface"])

    return mat

def create_coconut_material():
    """Green coconut husk shader — mirrors shader_coconut_green_shader.

    Noise-driven HSV modulation over a two-stop green ColorRamp (0.0908,
    0.2664, 0.013 → 0.2462, 0.4125, 0.0044). Principled BSDF with modest
    roughness (~0.45) matches the source.
    """

    mat = bpy.data.materials.new("CoconutHusk")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (800, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (550, 0)
    bsdf.inputs["Roughness"].default_value = 0.4455
    try:
        bsdf.inputs["Specular IOR Level"].default_value = 0.4773
    except KeyError:
        pass
    links.new(bsdf.outputs[0], output.inputs[0])

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-900, 0)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-650, 100)
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 10.0
    noise.inputs["Roughness"].default_value = 0.7
    links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-350, 100)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.0908, 0.2664, 0.013, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.2462, 0.4125, 0.0044, 1.0)
    # insert a middle stop at 0.5 for extra range
    mid = ramp.color_ramp.elements.new(0.5)
    mid.color = (0.15, 0.33, 0.008, 1.0)
    links.new(_fac_output(noise), ramp.inputs["Fac"])

    # Hue shift from noise for per-coconut variation
    hsv = nodes.new("ShaderNodeHueSaturation")
    hsv.location = (50, 100)
    hsv.inputs["Hue"].default_value = 0.5
    hsv.inputs["Saturation"].default_value = 1.0
    hsv.inputs["Value"].default_value = 1.0
    links.new(ramp.outputs["Color"], hsv.inputs["Color"])
    links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])

    # Subtle husk-fiber bump
    bump = nodes.new("ShaderNodeBump")
    bump.location = (300, -150)
    bump.inputs["Strength"].default_value = 0.2
    bump.inputs["Distance"].default_value = 0.003
    links.new(_fac_output(noise), bump.inputs["Height"])
    links.new(bump.outputs[0], bsdf.inputs["Normal"])

    return mat

# the geometry RNG stream identical to the no-texture CoconutTreeFactory we
# build materials first, then re-seed before geometry.

clear_scene()
random.seed(SEED)
np.random.seed(SEED)

TRUNK_MATERIAL = create_trunk_material()
TRUNK_MATERIAL.use_fake_user = True
CROWN_MATERIAL = create_crown_material()
CROWN_MATERIAL.use_fake_user = True
FROND_MATERIAL = create_frond_material()
FROND_MATERIAL.use_fake_user = True
COCONUT_MATERIAL = create_coconut_material()
COCONUT_MATERIAL.use_fake_user = True

# ── Geometry (VERBATIM from objects_blender/tropic_plants/CoconutTreeFactory) ─

def build_trunk(rng, trunk_height=8.0, base_r=0.25, tip_r=0.12, n_rings=36):
    """Curved tapered trunk with horizontal ring bumps (bark texture)."""

    lean_x = float(rng.uniform(-0.15, 0.15))
    lean_y = float(rng.uniform(-0.15, 0.15))
    n_sides = 16

    bm = bmesh.new()
    rings = []
    cx, cy = 0.0, 0.0
    accum_ax, accum_ay = 0.0, 0.0

    for i in range(n_rings + 1):
        t = i / n_rings
        r = base_r + (tip_r - base_r) * t
        # Horizontal ring bumps (old frond scars)
        ring_bump = 0.012 * math.sin(i * 2.8) * (1 - 0.4 * t)
        r += ring_bump

        accum_ax += lean_x / n_rings
        accum_ay += lean_y / n_rings
        cz = t * trunk_height
        cx += accum_ax * trunk_height / n_rings
        cy += accum_ay * trunk_height / n_rings

        ring = []
        for j in range(n_sides):
            theta = 2 * math.pi * j / n_sides
            ring.append(bm.verts.new((cx + r * math.cos(theta),
                                      cy + r * math.sin(theta), cz)))
        rings.append(ring)

    for i in range(n_rings):
        for j in range(n_sides):
            j2 = (j + 1) % n_sides
            bm.faces.new([rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]])

    # Bottom cap
    bot = bm.verts.new((0, 0, 0))
    for j in range(n_sides):
        bm.faces.new([bot, rings[0][(j + 1) % n_sides], rings[0][j]])

    mesh = bpy.data.meshes.new("trunk")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("trunk", mesh)
    bpy.context.collection.objects.link(obj)

    # Additional subtle bark displacement
    tex = bpy.data.textures.new("bark", type="STUCCI")
    tex.noise_scale = 0.12
    disp = obj.modifiers.new("bark", "DISPLACE")
    disp.texture = tex
    disp.strength = base_r * 0.04
    disp.mid_level = 0.5
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=disp.name)

    apply_tf(obj)
    tip_pos = np.array([cx, cy, trunk_height])
    return obj, tip_pos

def build_crown(tip_pos, radius=0.18, z_scale=1.2):
    """UV sphere at trunk tip — the bulge where fronds and coconuts attach."""

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=12, ring_count=8, radius=radius,
        location=tuple(tip_pos))
    crown = bpy.context.active_object
    crown.scale.z = z_scale
    apply_tf(crown)
    return crown

def build_frond(rng, frond_length=3.5, x_curvature=0.5):
    """

    Build one coconut palm frond at origin, spine along +Y axis.
    Central spine with many narrow paired leaflets — matches LeafPalmTreeFactory style.
    All geometry in a single bmesh for efficiency.
    Returns single mesh object.
    """

    n_spine = 24
    spine_r_base = float(rng.uniform(0.010, 0.016))
    leaflet_max_len = frond_length * float(rng.uniform(0.14, 0.22))
    leaflet_w = float(rng.uniform(0.030, 0.055))
    n_leaflets_per_side = int(rng.integers(30, 45))

    # Spine centerline: initial upward arc then strong gravity droop
    spine_pts = np.zeros((n_spine, 3))
    for i in range(n_spine):
        t = i / (n_spine - 1)
        spine_pts[i] = [
            0.0,
            frond_length * t,
            frond_length * (0.08 * math.sin(t * math.pi * 0.35)
                            - x_curvature * t * t * 0.55)
        ]

    # Tangents via gradient
    tangents = np.gradient(spine_pts, axis=0)
    for i in range(n_spine):
        n = np.linalg.norm(tangents[i])
        if n > 1e-8:
            tangents[i] /= n

    bm = bmesh.new()

    # ── Spine tube ──
    n_sides = 5
    prev_ring = None
    for i in range(n_spine):
        td = tangents[i]
        up = np.array([0.0, 0.0, 1.0])
        if abs(td[2]) > 0.9:
            up = np.array([1.0, 0.0, 0.0])
        right = np.cross(td, up)
        right /= (np.linalg.norm(right) + 1e-8)
        fwd = np.cross(right, td)
        r = spine_r_base * (1 - 0.6 * i / (n_spine - 1))

        ring = []
        for j in range(n_sides):
            theta = 2 * math.pi * j / n_sides
            v = bm.verts.new(tuple(
                spine_pts[i] + r * (math.cos(theta) * right + math.sin(theta) * fwd)))
            ring.append(v)

        if prev_ring is not None:
            for j in range(n_sides):
                j2 = (j + 1) % n_sides
                bm.faces.new([prev_ring[j], prev_ring[j2], ring[j2], ring[j]])
        prev_ring = ring

    # ── Leaflets on both sides ──
    for side in [-1, 1]:
        for k in range(n_leaflets_per_side):
            t = 0.06 + 0.88 * (k + 0.5) / n_leaflets_per_side

            # Interpolate spine position
            si = t * (n_spine - 1)
            idx = min(int(si), n_spine - 2)
            frac = si - idx
            pos = spine_pts[idx] * (1 - frac) + spine_pts[idx + 1] * frac
            td = tangents[idx] * (1 - frac) + tangents[min(idx + 1, n_spine - 1)] * frac
            n = np.linalg.norm(td)
            if n > 1e-8:
                td /= n

            up = np.array([0.0, 0.0, 1.0])
            if abs(td[2]) > 0.9:
                up = np.array([1.0, 0.0, 0.0])
            perp = np.cross(td, up)
            perp /= (np.linalg.norm(perp) + 1e-8)

            # Envelope: bell curve, peaks around 40-60%
            envelope = math.sin(t * math.pi) ** 0.7
            ll = leaflet_max_len * envelope   # leaflet length (perp to spine)
            lw = leaflet_w * envelope         # leaflet width (along spine)
            droop_f = float(rng.uniform(0.15, 0.35))

            if ll < 0.008:
                continue

            # Build leaflet as quad strip within this bmesh
            # Width direction: mix of tangent + vertical so leaflets are
            # visible from any horizontal viewing angle
            w_dir = 0.3 * td + 0.7 * np.array([0.0, 0.0, 1.0])
            w_dir /= (np.linalg.norm(w_dir) + 1e-8)

            n_l = 5
            top_vs = []
            bot_vs = []
            for li in range(n_l):
                lt = li / (n_l - 1)
                hw = lw * (1 - lt * 0.75) * 0.5   # taper toward tip
                droop = -droop_f * lt * lt * ll
                center = pos + side * perp * (ll * lt)
                p_top = center + w_dir * hw + np.array([0, 0, droop])
                p_bot = center - w_dir * hw + np.array([0, 0, droop])
                top_vs.append(bm.verts.new(tuple(p_top)))
                bot_vs.append(bm.verts.new(tuple(p_bot)))

            for li in range(n_l - 1):
                if li == n_l - 2:   # triangular tip
                    bm.faces.new([top_vs[li], top_vs[li + 1], bot_vs[li]])
                else:
                    bm.faces.new([top_vs[li], top_vs[li + 1],
                                  bot_vs[li + 1], bot_vs[li]])

    mesh = bpy.data.meshes.new("frond")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("frond", mesh)
    bpy.context.collection.objects.link(obj)
    apply_tf(obj)
    return obj

def build_coconuts(rng, tip_pos, crown_r, n=5):
    """Dense cluster of coconuts around the lower part of the crown."""

    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n + float(rng.uniform(-0.3, 0.3))
        r_offset = crown_r * float(rng.uniform(0.6, 1.0))
        cx = tip_pos[0] + r_offset * math.cos(a)
        cy = tip_pos[1] + r_offset * math.sin(a)
        cz = tip_pos[2] - float(rng.uniform(0.05, 0.22))
        coco_r = float(rng.uniform(0.08, 0.13))
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=10, ring_count=6, radius=coco_r,
            location=(cx, cy, cz))
        coco = bpy.context.active_object
        coco.scale.z = float(rng.uniform(1.1, 1.4))
        coco.rotation_euler.x = float(rng.uniform(-0.3, 0.3))
        coco.rotation_euler.y = float(rng.uniform(-0.3, 0.3))
        apply_tf(coco)
        # Subtle surface texture
        tex = bpy.data.textures.new("coco_t", type="STUCCI")
        tex.noise_scale = 0.03
        disp = coco.modifiers.new("d", "DISPLACE")
        disp.texture = tex
        disp.strength = 0.012
        disp.mid_level = 0.5
        bpy.context.view_layer.objects.active = coco
        bpy.ops.object.modifier_apply(modifier=disp.name)
        apply_tf(coco)
        parts.append(coco)
    return parts

# ── Main ──────────────────────────────────────────────────────────────────────

def assign_material(obj, material):
    """Append a material slot and set all faces to it."""

    obj.data.materials.append(material)
    slot_index = len(obj.data.materials) - 1
    for poly in obj.data.polygons:
        poly.material_index = slot_index
    return slot_index

def main():
    # Re-seed for geometry (mirrors objects_blender/CoconutTreeFactory)
    rng = np.random.default_rng(SEED)
    np.random.seed(SEED)

    trunk_h = float(rng.uniform(6.0, 12.0))
    base_r = float(rng.uniform(0.20, 0.35))
    tip_r = float(rng.uniform(0.10, 0.18))
    n_fronds = int(rng.integers(10, 18))
    frond_len = float(rng.uniform(2.5, 4.5))
    x_curvature = float(rng.uniform(0.3, 0.8))
    crown_r = float(rng.uniform(0.15, 0.22))
    crown_z_scale = float(rng.uniform(0.8, 1.5))
    n_coconuts = int(rng.integers(4, 8))

    parts = []

    # Trunk
    trunk, tip_pos = build_trunk(rng, trunk_h, base_r, tip_r)
    assign_material(trunk, TRUNK_MATERIAL)
    parts.append(trunk)

    # Crown sphere at trunk tip
    crown = build_crown(tip_pos, crown_r, crown_z_scale)
    assign_material(crown, CROWN_MATERIAL)
    parts.append(crown)

    # Fronds around crown at golden angle intervals
    golden = 2.39996
    for i in range(n_fronds):
        fl = frond_len * float(rng.uniform(0.85, 1.15))
        xc = x_curvature * float(rng.uniform(0.8, 1.2))
        frond = build_frond(rng, fl, xc)

        az = i * golden + float(rng.uniform(-0.15, 0.15))
        # Tilt: 0=horizontal, positive=upward; mostly horizontal so droop is visible
        tilt = float(rng.uniform(-0.05, 0.25))

        # Orient: rotate frond from +Y axis to radial direction around crown
        # Euler XYZ: first X-rotate (tilt up), then Z-rotate (azimuth)
        frond.rotation_euler = (tilt, 0, az)
        frond.location = tuple(tip_pos)
        apply_tf(frond)
        assign_material(frond, FROND_MATERIAL)
        parts.append(frond)

    # Coconuts clustered around crown
    coco_parts = build_coconuts(rng, tip_pos, crown_r, n_coconuts)
    for coco in coco_parts:
        assign_material(coco, COCONUT_MATERIAL)
    parts.extend(coco_parts)

    if not parts:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 0))
        return bpy.context.active_object

    # Join: pre-compute per-object face counts so we can re-assign material
    # indices to the joined result's four slots (trunk/crown/frond/coconut)
    # After join, Blender appends the child's material slots into the active
    # object in order, deduplicating by identity — since each group shares a
    # single material instance, slots remain 4 total.
    #
    # Easier & robust: record a (start, count, material) tuple before joining.
    face_groups = []
    cursor = 0
    # The active object at join-time is parts[0] (trunk); parts are appended in
    # the order their faces appear in the joined mesh.
    for p in parts:
        nfaces = len(p.data.polygons)
        # Look up which material (identity) this part currently uses
        mat = p.data.materials[p.data.polygons[0].material_index] if nfaces else None
        face_groups.append((cursor, nfaces, mat))
        cursor += nfaces

    result = join_objs(parts)
    result.name = "CoconutTreeFactory"
    apply_tf(result)

    # Ensure the joined result has all 4 materials in a known order
    result.data.materials.clear()
    mat_to_slot = {}
    for mat in (TRUNK_MATERIAL, CROWN_MATERIAL, FROND_MATERIAL, COCONUT_MATERIAL):
        result.data.materials.append(mat)
        mat_to_slot[mat.name] = len(result.data.materials) - 1

    # Re-assign per-face material indices based on pre-join grouping
    for start, nfaces, mat in face_groups:
        if mat is None:
            continue
        slot = mat_to_slot.get(mat.name, 0)
        for f in range(start, start + nfaces):
            if f < len(result.data.polygons):
                result.data.polygons[f].material_index = slot

    # Shade: trunk/crown/coconuts smooth-ish, fronds flat would look odd;
    # keep the original script's implicit shading (flat default).
    return result

if __name__ == "__main__":
    main()

