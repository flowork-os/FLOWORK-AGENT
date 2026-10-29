# [FL_INDEX: keywords="blender_factory, procedural_3d, PalmTreeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PalmTreeFactory | Category: factories_geo
# Prompt: A 3D model of a palm tree rendered from a side perspective. The tree features a tall straight trunk with a horizontally ridged surface and a bulging mid-section covered in clustered brown fibrous stubs, topped by a crown of spreading fan-shaped fronds.

# SEED-deterministic: all random calls seeded from SEED

import os
import math
import random
import colorsys

import bmesh
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler


# ──────────────────────────────────────────────────────────────────────────────
# Seed infrastructure
# ──────────────────────────────────────────────────────────────────────────────

SEED = int(os.environ.get("SEED", "0"))


def _seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)


def _hsv2rgba(hsv):
    r, g, b = colorsys.hsv_to_rgb(float(hsv[0]) % 1.0,
                                  max(0.0, min(1.0, float(hsv[1]))),
                                  max(0.0, min(1.0, float(hsv[2]))))
    return (r, g, b, 1.0)


def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def _fac_output(node):
    """Return the first usable 'factor' socket across Blender 4.x / 5.x."""

    return (node.outputs.get("Fac")
            or node.outputs.get("Factor")
            or node.outputs[0])


def _set_specular(bsdf, value):
    key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[key].default_value = float(value)


# ──────────────────────────────────────────────────────────────────────────────
# Shader translations (raw bpy node trees)
# ──────────────────────────────────────────────────────────────────────────────

def make_trunk_material(name="PalmTrunkMaterial"):
    """Faithful port of palm_tree.shader_trunk.

    voronoi (distance, 4D)  ─┐
    wave (Z-bands)           ├ mix -> colorramp (dark_hsv/bright_hsv)
                             │
    voronoi (scale 100, Chebychev, randomness 10) ─ colorramp (crack mask)
                                                  ─ mix -> base color
    roughness <- voronoi_texture.distance ; specular 0.
    """

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    voronoi_dist = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        voronoi_dist.voronoi_dimensions = "4D"
    except (TypeError, AttributeError):
        voronoi_dist.voronoi_dimensions = "3D"
    voronoi_dist.inputs["Scale"].default_value = 20.0
    ln(mapping.outputs["Vector"], voronoi_dist.inputs["Vector"])

    # Wave texture (Z bands)
    wave = nt.nodes.new("ShaderNodeTexWave")
    try:
        wave.bands_direction = "Z"
    except (TypeError, AttributeError):
        pass
    wave.inputs["Scale"].default_value = float(np.random.uniform(1.0, 3.0))
    wave.inputs["Distortion"].default_value = 5.0
    if "Detail Scale" in wave.inputs:
        wave.inputs["Detail Scale"].default_value = 3.0
    ln(mapping.outputs["Vector"], wave.inputs["Vector"])

    # mix_1 = voronoi.Distance <mix> wave.Color (MixRGB default factor 0.5)
    mix_1 = nt.nodes.new("ShaderNodeMix")
    mix_1.data_type = "RGBA"
    mix_1.inputs[0].default_value = 0.5
    ln(voronoi_dist.outputs["Distance"], mix_1.inputs[6])
    ln(wave.outputs["Color"], mix_1.inputs[7])

    # Base-colour ramp
    d_hsv = (
        float(np.random.uniform(0.02, 0.05)),
        float(np.random.uniform(0.01, 0.05)) if np.random.randint(0, 2) == 1
        else float(np.random.uniform(0.5, 0.8)),
        float(np.random.uniform(0.03, 0.09)),
    )
    b_hsv = d_hsv[:-1] + (float(np.random.uniform(0.1, 0.3)),)

    ramp_base = nt.nodes.new("ShaderNodeValToRGB")
    ramp_base.color_ramp.elements[0].position = 0.4682
    ramp_base.color_ramp.elements[0].color = _hsv2rgba(d_hsv)
    ramp_base.color_ramp.elements[1].position = 0.5591
    ramp_base.color_ramp.elements[1].color = _hsv2rgba(b_hsv)
    ln(mix_1.outputs[2], ramp_base.inputs["Fac"])

    # Crack pattern: second mapping (10, 10, 0.2) -> voronoi (Chebychev) -> ramp
    mapping_cracks = nt.nodes.new("ShaderNodeMapping")
    mapping_cracks.inputs["Scale"].default_value = (10.0, 10.0, 0.2)
    ln(tex_coord.outputs["Object"], mapping_cracks.inputs["Vector"])

    voronoi_cracks = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        voronoi_cracks.voronoi_dimensions = "4D"
    except (TypeError, AttributeError):
        voronoi_cracks.voronoi_dimensions = "3D"
    voronoi_cracks.distance = "CHEBYCHEV"
    voronoi_cracks.inputs["Scale"].default_value = 100.0
    voronoi_cracks.inputs["Randomness"].default_value = 10.0
    ln(mapping_cracks.outputs["Vector"], voronoi_cracks.inputs["Vector"])

    ramp_cracks = nt.nodes.new("ShaderNodeValToRGB")
    ramp_cracks.color_ramp.elements[0].position = 0.2818
    ramp_cracks.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp_cracks.color_ramp.elements[1].position = 0.3045
    ramp_cracks.color_ramp.elements[1].color = (0.5284, 0.5034, 0.4327, 1.0)
    ln(voronoi_cracks.outputs["Distance"], ramp_cracks.inputs["Fac"])

    crack_mix_fac = float(np.random.uniform(0.1, 0.3))
    mix_final = nt.nodes.new("ShaderNodeMix")
    mix_final.data_type = "RGBA"
    mix_final.inputs[0].default_value = crack_mix_fac
    ln(ramp_base.outputs["Color"], mix_final.inputs[6])
    ln(ramp_cracks.outputs["Color"], mix_final.inputs[7])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_final.outputs[2], bsdf.inputs["Base Color"])
    ln(voronoi_cracks.outputs["Distance"], bsdf.inputs["Roughness"])
    _set_specular(bsdf, 0.0)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_top_core_material(name="PalmTopCoreMaterial"):
    """Faithful port of palm_tree.shader_top_core."""

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 0.1)
    ln(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = float(np.random.uniform(100.0, 400.0))
    ln(mapping.outputs["Vector"], voronoi.inputs["Vector"])

    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 2.0
    wave.inputs["Distortion"].default_value = 5.0
    if "Detail Scale" in wave.inputs:
        wave.inputs["Detail Scale"].default_value = 10.0
    ln(mapping_1.outputs["Vector"], wave.inputs["Vector"])

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.4
    ln(voronoi.outputs["Distance"], mix.inputs[6])
    ln(wave.outputs["Color"], mix.inputs[7])

    d_hsv = (
        float(np.random.uniform(0.02, 0.05)),
        float(np.random.uniform(0.3, 0.6)),
        float(np.random.uniform(0.01, 0.05)),
    )
    b_hsv = (
        d_hsv[0],
        float(np.random.uniform(0.6, 0.9)),
        float(np.random.uniform(0.3, 0.6)),
    )

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.2409
    ramp.color_ramp.elements[0].color = _hsv2rgba(d_hsv)
    ramp.color_ramp.elements[1].position = 0.6045
    ramp.color_ramp.elements[1].color = _hsv2rgba(b_hsv)
    ln(mix.outputs[2], ramp.inputs["Fac"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    ln(ramp.outputs["Alpha"], bsdf.inputs["Roughness"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_leaf_material(name="PalmLeafMaterial"):
    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Noise in place of the upstream vein / subvein attributes.
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.8
    noise.inputs["Detail"].default_value = 10.0
    noise.inputs["Roughness"].default_value = 0.7
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])

    # Blender 5.0 removed ShaderNodeSeparateRGB; use SeparateColor in RGB mode.
    try:
        sep_rgb = nt.nodes.new("ShaderNodeSeparateColor")
        try:
            sep_rgb.mode = "RGB"
        except (TypeError, AttributeError):
            pass
        green_out = sep_rgb.outputs["Green"]
        blue_out = sep_rgb.outputs["Blue"]
    except RuntimeError:
        sep_rgb = nt.nodes.new("ShaderNodeSeparateRGB")
        green_out = sep_rgb.outputs["G"]
        blue_out = sep_rgb.outputs["B"]
    ln(noise.outputs["Color"], sep_rgb.inputs[0])

    # MapRange on G channel -> hue wobble (0.48..0.52)
    map_hue = nt.nodes.new("ShaderNodeMapRange")
    map_hue.inputs["From Min"].default_value = 0.4
    map_hue.inputs["From Max"].default_value = 0.7
    map_hue.inputs["To Min"].default_value = 0.48
    map_hue.inputs["To Max"].default_value = 0.52
    ln(green_out, map_hue.inputs["Value"])

    # MapRange on B channel -> value wobble (0.8..1.2)
    map_val = nt.nodes.new("ShaderNodeMapRange")
    map_val.inputs["From Min"].default_value = 0.4
    map_val.inputs["From Max"].default_value = 0.7
    map_val.inputs["To Min"].default_value = 0.8
    map_val.inputs["To Max"].default_value = 1.2
    ln(blue_out, map_val.inputs["Value"])

    # subvein-offset replacement: second noise -> map range (default From 0..1, To 0..-0.94)
    noise_subvein = nt.nodes.new("ShaderNodeTexNoise")
    noise_subvein.inputs["Scale"].default_value = 12.0
    ln(tex_coord.outputs["Object"], noise_subvein.inputs["Vector"])

    map_subvein = nt.nodes.new("ShaderNodeMapRange")
    map_subvein.inputs["From Min"].default_value = 0.0
    map_subvein.inputs["From Max"].default_value = 1.0
    map_subvein.inputs["To Min"].default_value = 0.0
    map_subvein.inputs["To Max"].default_value = -0.94
    ln(_fac_output(noise_subvein), map_subvein.inputs["Value"])

    main_leaf_hsv = (
        float(np.random.uniform(0.3, 0.36)),
        float(np.random.uniform(0.6, 0.7)),
        float(np.random.uniform(0.2, 0.3)),
    )

    hue_sat_val = nt.nodes.new("ShaderNodeHueSaturation")
    hue_sat_val.inputs["Value"].default_value = 2.0
    hue_sat_val.inputs["Color"].default_value = _hsv2rgba(main_leaf_hsv)

    # main_leaf_hsv_2 = same hsv with tiny hue jitter
    main_leaf_hsv_2 = (main_leaf_hsv[0] + float(np.random.normal(0.0, 0.005)),
                       main_leaf_hsv[1], main_leaf_hsv[2])

    mix_subvein = nt.nodes.new("ShaderNodeMix")
    mix_subvein.data_type = "RGBA"
    ln(map_subvein.outputs["Result"], mix_subvein.inputs[0])
    ln(hue_sat_val.outputs["Color"], mix_subvein.inputs[6])
    mix_subvein.inputs[7].default_value = _hsv2rgba(main_leaf_hsv_2)

    hue_sat_val_2 = nt.nodes.new("ShaderNodeHueSaturation")
    ln(map_hue.outputs["Result"], hue_sat_val_2.inputs["Hue"])
    ln(map_val.outputs["Result"], hue_sat_val_2.inputs["Value"])
    ln(mix_subvein.outputs[2], hue_sat_val_2.inputs["Color"])

    # stem_color (darker) mixed by "vein" mask — replaced by another noise mask
    stem_color_hsv = main_leaf_hsv[:-1] + (
        main_leaf_hsv[-1] - float(np.random.uniform(0.05, 0.15)),)

    noise_vein = nt.nodes.new("ShaderNodeTexNoise")
    noise_vein.inputs["Scale"].default_value = 18.0
    noise_vein.inputs["Detail"].default_value = 8.0
    ln(tex_coord.outputs["Object"], noise_vein.inputs["Vector"])

    mix_vein = nt.nodes.new("ShaderNodeMix")
    mix_vein.data_type = "RGBA"
    ln(_fac_output(noise_vein), mix_vein.inputs[0])
    mix_vein.inputs[6].default_value = _hsv2rgba(stem_color_hsv)
    ln(hue_sat_val_2.outputs["Color"], mix_vein.inputs[7])

    # ── leaf_shader group: Diffuse + Glossy (0.2 mix) then Translucent (0.3)
    diffuse = nt.nodes.new("ShaderNodeBsdfDiffuse")
    ln(mix_vein.outputs[2], diffuse.inputs["Color"])

    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Roughness"].default_value = 0.3
    ln(mix_vein.outputs[2], glossy.inputs["Color"])

    mix_shader_1 = nt.nodes.new("ShaderNodeMixShader")
    mix_shader_1.inputs["Fac"].default_value = 0.2
    ln(diffuse.outputs[0], mix_shader_1.inputs[1])
    ln(glossy.outputs[0], mix_shader_1.inputs[2])

    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    ln(mix_vein.outputs[2], translucent.inputs["Color"])

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    mix_shader_2.inputs["Fac"].default_value = 0.3
    ln(mix_shader_1.outputs[0], mix_shader_2.inputs[1])
    ln(translucent.outputs[0], mix_shader_2.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_shader_2.outputs[0], out.inputs["Surface"])
    return mat


def make_stem_material(name="PalmStemMaterial"):
    """Faithful port of tropic_plant_utils.shader_stem_material."""

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    stem_color_hsv = (float(np.random.uniform(0.25, 0.32)),
                      float(np.random.uniform(0.6, 0.9)),
                      float(np.random.uniform(0.2, 0.6)))

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = _hsv2rgba(stem_color_hsv)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ──────────────────────────────────────────────────────────────────────────────
# Phase 1 — material sampling on raw SEED (natural palm, no wear_tear)
# ──────────────────────────────────────────────────────────────────────────────
_seed_all(SEED)

# trunk/leaf shaders are sampled inside create_asset when
# surface.shaderfunc_to_material(...) is called. To keep the texture script
# self-contained we sample materials here in Phase 1 — this drains np.random
# called under FixedSeed(factory_seed). The geometry then re-seeds via
# ``np.random.default_rng(SEED)`` inside ``main()``.
#
#   set_material_1 (crown core)          -> shader_trunk
#   set_material   (trunk tube)          -> shader_trunk
#   truncated stem nodegroup material    -> shader_top_core
#   leaf material (on leaf mesh)  -> shader_leaf_material
#   stem material (on stem mesh)  -> shader_stem_material
#
# two material data-blocks but the shader sampling call sequence is identical).
# shader_trunk drains 7 uniforms + 1 randint per call — keep both calls so the

MAT_TRUNK = make_trunk_material("PalmTree_Trunk")
_ = make_trunk_material("PalmTree_TrunkDup")  # drain RNG to mirror second call
bpy.data.materials.remove(_, do_unlink=True)
MAT_TOP_CORE = make_top_core_material("PalmTree_TopCore")
MAT_LEAF = make_leaf_material("PalmTree_Leaf")
MAT_STEM = make_stem_material("PalmTree_Stem")

MAT_TRUNK.use_fake_user = True
MAT_TOP_CORE.use_fake_user = True
MAT_LEAF.use_fake_user = True
MAT_STEM.use_fake_user = True


# ──────────────────────────────────────────────────────────────────────────────
# Geometry helpers (verbatim from objects_blender/tropic_plants/PalmTreeFactory)
# ──────────────────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)


def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def join_objs(objs):
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def mesh_from_bm(bm, name="mesh"):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def quadratic_bezier(start, mid, end, n_pts):
    pts = np.zeros((n_pts, 3))
    for i in range(n_pts):
        t = i / max(n_pts - 1, 1)
        s = 1 - t
        pts[i] = s*s*np.array(start) + 2*s*t*np.array(mid) + t*t*np.array(end)
    return pts


def catmull_rom_eval(ctrl_pts, x):
    if x <= ctrl_pts[0][0]: return ctrl_pts[0][1]
    if x >= ctrl_pts[-1][0]: return ctrl_pts[-1][1]
    ts = [p[0] for p in ctrl_pts]; vs = [p[1] for p in ctrl_pts]
    vs_ext = [2*vs[0]-vs[1]] + list(vs) + [2*vs[-1]-vs[-2]]
    seg = len(ts) - 2
    for i in range(len(ts)-1):
        if ts[i] <= x < ts[i+1]: seg = i; break
    dt = ts[seg+1] - ts[seg]
    if dt < 1e-10: return vs[seg]
    u = (x - ts[seg]) / dt; u2, u3 = u*u, u*u*u
    p0,p1,p2,p3 = vs_ext[seg],vs_ext[seg+1],vs_ext[seg+2],vs_ext[seg+3]
    return 0.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u2+(-p0+3*p1-3*p2+p3)*u3)


def compute_tangents(pts):
    n = len(pts)
    tangents = np.zeros_like(pts)
    for i in range(n):
        if i == 0: t = pts[1] - pts[0]
        elif i == n-1: t = pts[-1] - pts[-2]
        else: t = pts[i+1] - pts[i-1]
        tl = np.linalg.norm(t)
        tangents[i] = t / tl if tl > 1e-8 else np.array([0, 0, 1])
    return tangents


def _safe_normalize(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-8 else np.array([1.0, 0.0, 0.0])


# ── Trunk ─────────────────────────────────────────────────────────────────────

def build_trunk(rng, trunk_height, trunk_radius, top_xy):
    top_x, top_y = top_xy
    mid_x = top_x / float(rng.uniform(1.0, 2.0))
    mid_y = top_y / float(rng.uniform(1.0, 2.0))
    mid_z = float(rng.uniform(1.5, 3.0))

    n_curve = 200
    centerline = quadratic_bezier(
        [0, 0, 0], [mid_x, mid_y, mid_z], [top_x, top_y, trunk_height], n_curve)
    tangents = compute_tangents(centerline)

    ring_mod_scale = float(rng.uniform(0.15, 0.35))
    ring_curve_pts = [(0.0, 0.0969), (0.5864, 0.1406), (1.0, 0.2906)]

    n_sides = 32
    bm = bmesh.new()
    rings = []

    for i in range(n_curve):
        factor = i / max(n_curve - 1, 1)
        base_taper = 1.0 + (0.2 - 1.0) * factor
        base_bulge = 0.15 * max(0, 1.0 - factor * 5.0)
        frac1 = (factor * 8000.0) % 1.0
        frac2 = (factor * 3000.0) % 1.0
        ring_bump = (catmull_rom_eval(ring_curve_pts, frac1) * 0.6
                     + catmull_rom_eval(ring_curve_pts, frac2) * 0.4) * ring_mod_scale * 0.6
        noise = float(rng.uniform(0.002, 0.008))
        r = ((base_taper + base_bulge) * (1.0 + ring_bump) + noise) * trunk_radius

        tang = tangents[i]
        up = np.array([0, 1, 0]) if abs(tang[1]) < 0.9 else np.array([1, 0, 0])
        right = np.cross(tang, up); right /= (np.linalg.norm(right) + 1e-8)
        fwd = np.cross(right, tang)

        ring = []
        for j in range(n_sides):
            theta = 2 * math.pi * j / n_sides
            offset = r * (math.cos(theta) * right + math.sin(theta) * fwd)
            ring.append(bm.verts.new(tuple(centerline[i] + offset)))
        rings.append(ring)

    for i in range(n_curve - 1):
        for j in range(n_sides):
            j2 = (j + 1) % n_sides
            bm.faces.new([rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]])

    bot = bm.verts.new((0, 0, 0))
    for j in range(n_sides):
        bm.faces.new([bot, rings[0][(j+1)%n_sides], rings[0][j]])

    tip = centerline[-1]
    top_v = bm.verts.new(tuple(tip))
    for j in range(n_sides):
        bm.faces.new([top_v, rings[-1][j], rings[-1][(j+1)%n_sides]])

    bm.normal_update()
    trunk_obj = mesh_from_bm(bm, "trunk")
    apply_tf(trunk_obj)
    return trunk_obj, tuple(tip), centerline, tangents


# ── Crown: UV sphere vertex instancing (matching original GeoNodes) ───────────

def build_crown(rng, tip_pos):
    """Build crown by simulating original GeoNodes UV sphere instancing.

    Returns (crown_stems_obj, crown_leaves_obj) so per-part materials can be
    assigned before the final join. The geometry is unchanged from the
    objects_blender source — only the single bmesh is split into two.
    """

    tip = np.array(tip_pos)

    sphere_r = float(rng.uniform(0.15, 0.22))
    z_scale = float(rng.uniform(0.5, 0.8))
    segments = int(rng.integers(5, 8))
    n_rings = int(rng.integers(7, 10))

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=n_rings, radius=sphere_r, location=tip_pos)
    core = bpy.context.active_object
    core.scale.z = z_scale
    apply_tf(core)
    core.name = "crown_core"

    verts_info = []
    idx = 0

    verts_info.append({
        'pos': tip + np.array([0.0, 0.0, sphere_r * z_scale]),
        'normal': np.array([0.0, 0.0, 1.0]),
        'idx': idx,
    })
    idx += 1

    for ri in range(1, n_rings):
        lat = math.pi / 2 - math.pi * ri / n_rings
        for si in range(segments):
            lon = 2 * math.pi * si / segments
            cx = math.cos(lat) * math.cos(lon)
            cy = math.cos(lat) * math.sin(lon)
            cz = math.sin(lat)

            pos = tip + np.array([cx * sphere_r, cy * sphere_r,
                                  cz * sphere_r * z_scale])

            nx, ny, nz = cx, cy, cz / (z_scale * z_scale)
            n_len = math.sqrt(nx**2 + ny**2 + nz**2)
            if n_len > 1e-8:
                normal = np.array([nx / n_len, ny / n_len, nz / n_len])
            else:
                normal = np.array([0.0, 0.0, 1.0])

            verts_info.append({
                'pos': pos,
                'normal': normal,
                'idx': idx,
            })
            idx += 1

    verts_info.append({
        'pos': tip + np.array([0.0, 0.0, -sphere_r * z_scale]),
        'normal': np.array([0.0, 0.0, -1.0]),
        'idx': idx,
    })

    threshold = n_rings - 3
    remaining = [v for v in verts_info
                 if v['idx'] / segments <= threshold and v['normal'][2] >= -0.05]

    target_count = int(rng.integers(18, 26))
    surviving = []
    for v in remaining:
        nz = v['normal'][2]
        v['extra_droop'] = max(0.0, 0.5 - nz) * 0.4
        height_bonus = max(0.0, nz) * 0.2
        v['scale'] = float(rng.uniform(0.7, 1.0)) + height_bonus
        surviving.append(v)

    if len(surviving) > target_count:
        perm = rng.permutation(len(surviving))
        surviving = [surviving[int(i)] for i in perm[:target_count]]

    lxc = float(rng.uniform(0.12, 0.28))
    stem_len_base = float(rng.uniform(1.0, 1.6))
    leaf_width_scale = float(rng.uniform(0.15, 0.20))
    blade_hw_base = leaf_width_scale * 0.3625 * 2.2
    leaf_scale = float(rng.uniform(0.85, 1.25))
    plant_scale = float(rng.uniform(0.8, 1.3))
    tree_scale = leaf_scale * plant_scale
    fold_height_base = float(rng.uniform(0.03, 0.06))
    n_fingers = int(rng.integers(10, 15))
    blade_len_base = 1.3
    n_blade_pts = 14
    n_cross = 6
    n_stem_segs = 8
    n_stem_sides = 6
    stem_r_base = 0.022

    contour_ctrl = [
        (0.0, 0.15), (0.05, 0.40), (0.12, 0.70), (0.25, 0.90),
        (0.40, 1.0), (0.60, 0.85), (0.80, 0.50), (0.92, 0.20), (1.0, 0.0),
    ]

    bm_stems = bmesh.new()
    bm_leaves = bmesh.new()

    for leaf_info in surviving:
        sd = np.array(leaf_info['normal'], dtype=float)
        inst_scale = leaf_info['scale'] * tree_scale
        fi = leaf_info['idx']
        extra_droop = leaf_info.get('extra_droop', 0.0)

        if sd[2] > 0.5:
            horiz = np.array([sd[0], sd[1], 0.0])
            h_len = np.linalg.norm(horiz)
            if h_len < 0.1:
                horiz = np.array([float(rng.normal()), float(rng.normal()), 0.0])
            horiz = _safe_normalize(horiz)
            tilt = (sd[2] - 0.5) * 1.2
            sd = _safe_normalize(sd + horiz * tilt)

        sl = stem_len_base * inst_scale
        bl = blade_len_base * inst_scale
        hw = blade_hw_base * inst_scale
        fh = fold_height_base * inst_scale
        sr = stem_r_base * inst_scale

        s_up = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(sd, s_up)) > 0.99:
            s_up = np.array([0.0, 1.0, 0.0])
        s_right = _safe_normalize(np.cross(sd, s_up))
        s_fwd = np.cross(s_right, sd)

        stem_y_curv = float(rng.uniform(-0.1, 0.1))
        stem_start = leaf_info['pos']

        stem_rings = []
        for ssi in range(n_stem_segs + 1):
            t = ssi / n_stem_segs
            center = (stem_start + sd * (sl * t)
                      + s_fwd * (stem_y_curv * sl * math.sin(math.pi * t)))
            center[2] -= extra_droop * sl * t * t * 0.5
            r = sr * max(0.3, 1.0 - 0.5 * t)
            ring = []
            for j in range(n_stem_sides):
                theta = 2 * math.pi * j / n_stem_sides
                offset = r * (math.cos(theta) * s_right + math.sin(theta) * s_fwd)
                ring.append(bm_stems.verts.new(tuple(center + offset)))
            stem_rings.append(ring)

        for ssi in range(n_stem_segs):
            for j in range(n_stem_sides):
                j2 = (j + 1) % n_stem_sides
                bm_stems.faces.new([stem_rings[ssi][j], stem_rings[ssi][j2],
                                    stem_rings[ssi + 1][j2], stem_rings[ssi + 1][j]])

        fan_origin = stem_start + sd * sl

        world_down = np.array([0.0, 0.0, -1.0])
        f_down = world_down - np.dot(world_down, sd) * sd
        f_down_len = np.linalg.norm(f_down)
        if f_down_len < 0.05:
            f_down = np.array([1.0, 0.0, 0.0])
        else:
            f_down /= f_down_len
        f_right = _safe_normalize(np.cross(sd, f_down))

        distribute_rot = (fi % segments) / segments * 2.0 * math.pi - math.pi / 2
        rand_rz = float(rng.uniform(-0.3, 0.3))
        fan_rot = distribute_rot + rand_rz

        cos_fr = math.cos(fan_rot)
        sin_fr = math.sin(fan_rot)
        fr_r = f_right * cos_fr - f_down * sin_fr

        rand_rx = float(rng.uniform(-0.08, 0.08))
        fr_r = _safe_normalize(fr_r + sd * rand_rx * 0.2)
        fr_r = _safe_normalize(fr_r - np.dot(fr_r, sd) * sd)

        rand_tilt = float(rng.uniform(-0.06, 0.06))
        fr_d = _safe_normalize(f_down + sd * rand_tilt * 0.2)
        fr_d = _safe_normalize(fr_d - np.dot(fr_d, sd) * sd)

        fan_span = math.pi * 0.94
        fan_start = (math.pi - fan_span) / 2
        for k in range(n_fingers):
            theta_k = fan_start + fan_span * (k + 0.5) / n_fingers
            blade_dir = fr_r * math.cos(theta_k) + fr_d * math.sin(theta_k)
            width_dir = _safe_normalize(np.cross(blade_dir, sd))
            dome_dir = sd

            center_frac = abs(theta_k - math.pi / 2) / (math.pi / 2)
            blen = bl * (1.0 - 0.12 * center_frac)

            rows = []
            for bi in range(n_blade_pts + 1):
                bt = bi / n_blade_pts
                hw_i = catmull_rom_eval(contour_ctrl, bt) * hw
                pos = fan_origin + blade_dir * (blen * bt)

                droop_mag = (lxc + extra_droop) * bt * bt * blen
                gravity_droop = (0.12 + extra_droop * 0.5) * bt * bt * bt * blen
                pos = pos - sd * droop_mag
                pos[2] -= gravity_droop

                if hw_i < 0.001:
                    rows.append([bm_leaves.verts.new(tuple(pos))])
                else:
                    dome_t = min(1.0, bt * 2.0) if bt < 0.5 else 1.0
                    fh_i = fh * dome_t
                    twist_angle = bt * 0.3 * (1.0 if k % 2 == 0 else -1.0)
                    cos_tw = math.cos(twist_angle)
                    sin_tw = math.sin(twist_angle)
                    tw_width = width_dir * cos_tw + dome_dir * sin_tw
                    tw_dome = -width_dir * sin_tw + dome_dir * cos_tw
                    row = []
                    for ci in range(n_cross):
                        u = ci / (n_cross - 1)
                        wx = (u - 0.5) * 2.0 * hw_i
                        wz = fh_i * (1.0 - 4.0 * (u - 0.5) ** 2)
                        vpos = pos + tw_width * wx + tw_dome * wz
                        row.append(bm_leaves.verts.new(tuple(vpos)))
                    rows.append(row)

            for bi in range(n_blade_pts):
                ra, rb = rows[bi], rows[bi + 1]
                na, nb = len(ra), len(rb)
                if na == 1 and nb == 1:
                    pass
                elif na == 1:
                    for ci in range(nb - 1):
                        bm_leaves.faces.new([ra[0], rb[ci], rb[ci + 1]])
                elif nb == 1:
                    for ci in range(na - 1):
                        bm_leaves.faces.new([ra[ci], ra[ci + 1], rb[0]])
                else:
                    mn = min(na, nb)
                    for ci in range(mn - 1):
                        bm_leaves.faces.new([ra[ci], ra[ci + 1], rb[ci + 1], rb[ci]])

    bm_stems.normal_update()
    bm_leaves.normal_update()
    stems_obj = mesh_from_bm(bm_stems, "crown_stems")
    leaves_obj = mesh_from_bm(bm_leaves, "crown_leaves")

    bpy.data.objects.remove(core, do_unlink=True)
    return stems_obj, leaves_obj


# ── Truncated Stems (Dead Leaf Sheaths) ───────────────────────────────────────

def build_single_sheath(rng, scale=1.0):
    length = 0.22 * scale
    n_pts = 16
    n_cross = 12

    z_contour_ctrl = [
        (0.0, 0.41), (0.18, 0.475), (0.38, 0.51),
        (0.59, 0.52), (0.72, 0.51), (0.86, 0.48), (1.0, 0.375),
    ]
    z_contour_scale = float(rng.uniform(0.35, 0.60))
    curv_ctrl = [(0.0, 0.07), (0.25, 0.23), (0.50, 0.26), (0.98, 0.27)]
    curv_scale = 0.25

    bm = bmesh.new()
    rings = []

    for i in range(n_pts):
        t = i / max(n_pts - 1, 1)
        z = length * t
        curv = catmull_rom_eval(curv_ctrl, t) * curv_scale
        x = curv * z / length
        ctr = np.array([x, 0, z])
        r = catmull_rom_eval(z_contour_ctrl, t) * z_contour_scale * scale
        ring = []
        for j in range(n_cross):
            theta = 2 * math.pi * j / n_cross
            ring.append(bm.verts.new((ctr[0] + r*1.3*math.cos(theta),
                                      ctr[1] + r*0.7*math.sin(theta), ctr[2])))
        rings.append(ring)

    for i in range(n_pts - 1):
        for j in range(n_cross):
            j2 = (j + 1) % n_cross
            bm.faces.new([rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]])

    bot = bm.verts.new((0, 0, 0))
    for j in range(n_cross):
        bm.faces.new([bot, rings[0][(j+1)%n_cross], rings[0][j]])

    top_center = (catmull_rom_eval(curv_ctrl, 1.0) * curv_scale, 0, length)
    top_v = bm.verts.new(top_center)
    for j in range(n_cross):
        bm.faces.new([top_v, rings[-1][j], rings[-1][(j+1)%n_cross]])

    return mesh_from_bm(bm, "sheath")


def build_truncated_stems(rng, trunk_obj, trunk_height):
    _ = rng.uniform(0, 1)

    mesh = trunk_obj.data
    mesh.update()

    face_data = []
    for p in mesh.polygons:
        center = Vector(p.center)
        z_frac = center.z / trunk_height if trunk_height > 0 else 0
        if 0.40 < z_frac < 0.98:
            face_data.append((center, Vector(p.normal), z_frac))

    if not face_data:
        return []

    step = max(1, int(rng.integers(4, 8)))
    selected = face_data[::step]

    sheaths = []
    for center, normal, z_frac in selected:
        s = float(rng.uniform(0.8, 1.5))
        sheath = build_single_sheath(rng, scale=s)

        n = normal.normalized()
        if n.length < 1e-6:
            continue

        z_axis = Vector((0, 0, 1))
        rot_align = z_axis.rotation_difference(n).to_matrix().to_4x4()
        rot_tilt = Euler((-0.96, 0.0, math.pi/2)).to_matrix().to_4x4()

        rand_rx = float(rng.uniform(-0.2, 0.2))
        rand_ry = float(rng.uniform(-0.5, 0.5))
        rand_rz = float(rng.uniform(-0.2, 0.2))
        rot_rand = Euler((rand_rx, rand_ry, rand_rz)).to_matrix().to_4x4()

        sheath.matrix_world = Matrix.Translation(center) @ rot_align @ rot_tilt @ rot_rand
        apply_tf(sheath)
        sheaths.append(sheath)

    return sheaths


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point (geometry re-seeds; materials were captured in Phase 1)
# ──────────────────────────────────────────────────────────────────────────────

def main():
    rng = np.random.default_rng(SEED)
    np.random.seed(SEED)
    clear_scene()

    trunk_height = 5.0
    trunk_radius = float(rng.uniform(0.2, 0.3))
    top_x = float(np.clip(rng.normal(0.0, 0.5), -0.8, 0.8))
    top_y = float(np.clip(rng.normal(0.0, 0.5), -0.8, 0.8))

    trunk_obj, tip_pos, _, _ = build_trunk(
        rng, trunk_height, trunk_radius, (top_x, top_y))

    crown_stems, crown_leaves = build_crown(rng, tip_pos)

    sheaths = build_truncated_stems(rng, trunk_obj, trunk_height)

    # Per-part material assignment BEFORE join (hard requirement from spec).
    trunk_obj.data.materials.append(MAT_TRUNK)
    if crown_stems is not None:
        crown_stems.data.materials.append(MAT_STEM)
    if crown_leaves is not None:
        crown_leaves.data.materials.append(MAT_LEAF)
    for s in sheaths:
        s.data.materials.append(MAT_TOP_CORE)

    all_parts = [trunk_obj, crown_stems, crown_leaves] + sheaths
    all_parts = [p for p in all_parts if p is not None]

    if not all_parts:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 0))
        return bpy.context.active_object

    result = join_objs(all_parts)
    result.name = "PalmTreeFactory"

    result.scale = (2, 2, 2)
    apply_tf(result)

    bpy.ops.object.select_all(action="DESELECT")
    result.select_set(True)
    bpy.context.view_layer.objects.active = result
    try:
        bpy.ops.object.shade_auto_smooth()
    except (AttributeError, RuntimeError):
        bpy.ops.object.shade_smooth()
        if hasattr(result.data, 'use_auto_smooth'):
            result.data.use_auto_smooth = True
            result.data.auto_smooth_angle = math.radians(40)

    return result


if __name__ == "__main__":
    main()
