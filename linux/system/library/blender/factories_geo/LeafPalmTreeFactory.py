# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafPalmTreeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafPalmTreeFactory | Category: factories_geo
# Prompt: A 3D model of a single pinnate palm frond rendered from a front perspective. The frond features a long arching rachis with many narrow, pointed leaflets arranged symmetrically along both sides, tapering toward the tip, with a dark base stalk.

import os
SEED = int(os.environ.get("SEED", "0"))

import math, random, colorsys
import bmesh, bpy
import numpy as np

#   main_leaf_hsv = (uniform(0.3,0.36), uniform(0.8,1.0), uniform(0.25,0.45))
#   h2 = main_leaf_hsv[0] + normal(0.0, 0.005)  -> main_leaf_hsv_2
#   stem_color_hsv = main_leaf_hsv[:2] + (main_leaf_hsv[2] - uniform(0.05, 0.15),)
# These are applied inside a DiffuseBSDF+Glossy(mix=0.2)+Translucent(mix=0.3)
# shader, modulated by:
#   - noise (scale=6.8, detail=10.0, roughness=0.7) -> SeparateRGB ->
#     MapRange G [0.4,0.7]->[0.48,0.52] (hue), B [0.4,0.7]->[0.8,1.2] (value)
#   - "subvein offset" attribute (voronoi DISTANCE_TO_EDGE, scale=50 on leaf
#     local (|X|, Y)) -> MapRange [0,-0.94]->[0,1] -> MixRGB(hsv_main, hsv_2)
#   - "vein" attribute (main-vein/midrib voronoi scale~6 on leaf coord) ->
#     MixRGB(stem_color, modulated color)
# The standalone leaflet geometry does not carry leaf-local UV attributes, so
# we reproduce the shader structure on object-space coordinates with a
# Z-projected voronoi (used in the reference geometry-only script) and add the
# missing stem-color midrib mix.  The numpy.random call order matches

np.random.seed(SEED)
random.seed(SEED)

_MAIN_LEAF_H = float(np.random.uniform(0.30, 0.36))
_MAIN_LEAF_S = float(np.random.uniform(0.8, 1.0))
_MAIN_LEAF_V = float(np.random.uniform(0.25, 0.45))
_MAIN_LEAF_H2 = _MAIN_LEAF_H + float(np.random.normal(0.0, 0.005))
_STEM_COLOR_V_DELTA = float(np.random.uniform(0.05, 0.15))
_STEM_COLOR_HSV = (_MAIN_LEAF_H, _MAIN_LEAF_S, _MAIN_LEAF_V - _STEM_COLOR_V_DELTA)
_STEM_MAT_H = float(np.random.uniform(0.25, 0.32))
_STEM_MAT_S = float(np.random.uniform(0.6, 0.9))
_STEM_MAT_V = float(np.random.uniform(0.2, 0.6))


def _hsv_to_rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(
        float(h) % 1.0, max(0.0, min(1.0, float(s))), max(0.0, min(1.0, float(v)))
    )
    return (r, g, b, 1.0)


def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m


def make_palm_leaf_material(name="PalmLeafMaterial"):
    mat = _new_mat(name)
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links

    output_node = nodes.new("ShaderNodeOutputMaterial")
    tex_coord = nodes.new("ShaderNodeTexCoord")

    # --- leaf-body noise (hue+value modulation) ---
    noise_body = nodes.new("ShaderNodeTexNoise")
    noise_body.inputs["Scale"].default_value = 6.8
    noise_body.inputs["Detail"].default_value = 10.0
    noise_body.inputs["Roughness"].default_value = 0.7
    links.new(tex_coord.outputs["Object"], noise_body.inputs["Vector"])

    noise_color_out = noise_body.outputs.get("Color") or noise_body.outputs[1]
    separate_rgb = nodes.new("ShaderNodeSeparateColor")
    separate_rgb.mode = "RGB"
    links.new(noise_color_out, separate_rgb.inputs["Color"])

    map_range_hue = nodes.new("ShaderNodeMapRange")
    map_range_hue.inputs["From Min"].default_value = 0.4
    map_range_hue.inputs["From Max"].default_value = 0.7
    map_range_hue.inputs["To Min"].default_value = 0.48
    map_range_hue.inputs["To Max"].default_value = 0.52
    links.new(separate_rgb.outputs["Green"], map_range_hue.inputs["Value"])

    map_range_value = nodes.new("ShaderNodeMapRange")
    map_range_value.inputs["From Min"].default_value = 0.4
    map_range_value.inputs["From Max"].default_value = 0.7
    map_range_value.inputs["To Min"].default_value = 0.8
    map_range_value.inputs["To Max"].default_value = 1.2
    links.new(separate_rgb.outputs["Blue"], map_range_value.inputs["Value"])

    # --- sub-vein stripes (object-space voronoi stand-in for attribute) ---
    sep_xyz = nodes.new("ShaderNodeSeparateXYZ")
    links.new(tex_coord.outputs["Object"], sep_xyz.inputs["Vector"])

    comb_for_subvein = nodes.new("ShaderNodeCombineXYZ")
    comb_for_subvein.inputs["X"].default_value = 0.0
    comb_for_subvein.inputs["Z"].default_value = 0.0
    links.new(sep_xyz.outputs["Z"], comb_for_subvein.inputs["Y"])

    subvein_voronoi = nodes.new("ShaderNodeTexVoronoi")
    subvein_voronoi.voronoi_dimensions = "3D"
    subvein_voronoi.feature = "DISTANCE_TO_EDGE"
    subvein_voronoi.inputs["Scale"].default_value = 50.0
    links.new(comb_for_subvein.outputs["Vector"], subvein_voronoi.inputs["Vector"])

    map_range_subvein_dist = nodes.new("ShaderNodeMapRange")
    map_range_subvein_dist.inputs["From Min"].default_value = 0.0
    map_range_subvein_dist.inputs["From Max"].default_value = 0.1
    map_range_subvein_dist.inputs["To Min"].default_value = 0.0
    map_range_subvein_dist.inputs["To Max"].default_value = 1.0
    links.new(subvein_voronoi.outputs["Distance"], map_range_subvein_dist.inputs["Value"])

    neg_subvein = nodes.new("ShaderNodeMath")
    neg_subvein.operation = "MULTIPLY"
    neg_subvein.inputs[1].default_value = -1.0
    links.new(map_range_subvein_dist.outputs["Result"], neg_subvein.inputs[0])

    map_range_subvein = nodes.new("ShaderNodeMapRange")
    map_range_subvein.inputs["From Min"].default_value = 0.0
    map_range_subvein.inputs["From Max"].default_value = -0.94
    map_range_subvein.inputs["To Min"].default_value = 0.0
    map_range_subvein.inputs["To Max"].default_value = 1.0
    links.new(neg_subvein.outputs[0], map_range_subvein.inputs["Value"])

    # --- main leaf HSV with brightness=2.0 ---
    hsv_main = nodes.new("ShaderNodeHueSaturation")
    hsv_main.inputs["Value"].default_value = 2.0
    hsv_main.inputs["Color"].default_value = _hsv_to_rgba(_MAIN_LEAF_H, _MAIN_LEAF_S, _MAIN_LEAF_V)

    rgb_main_2 = nodes.new("ShaderNodeRGB")
    rgb_main_2.outputs[0].default_value = _hsv_to_rgba(_MAIN_LEAF_H2, _MAIN_LEAF_S, _MAIN_LEAF_V)

    mix_subvein_rgb = nodes.new("ShaderNodeMixRGB")
    mix_subvein_rgb.inputs["Fac"].default_value = 0.0
    links.new(map_range_subvein.outputs["Result"], mix_subvein_rgb.inputs["Fac"])
    links.new(hsv_main.outputs["Color"], mix_subvein_rgb.inputs["Color1"])
    links.new(rgb_main_2.outputs["Color"], mix_subvein_rgb.inputs["Color2"])

    # --- noise-driven hue/value shift ---
    hsv_modulated = nodes.new("ShaderNodeHueSaturation")
    links.new(map_range_hue.outputs["Result"], hsv_modulated.inputs["Hue"])
    links.new(map_range_value.outputs["Result"], hsv_modulated.inputs["Value"])
    links.new(mix_subvein_rgb.outputs["Color"], hsv_modulated.inputs["Color"])

    # --- main vein / midrib mix using a second voronoi stand-in for the
    # On the standalone mesh we do not have leaf-local X; use object X/Z.
    comb_for_midrib = nodes.new("ShaderNodeCombineXYZ")
    comb_for_midrib.inputs["Y"].default_value = 0.0
    links.new(sep_xyz.outputs["X"], comb_for_midrib.inputs["X"])
    links.new(sep_xyz.outputs["Z"], comb_for_midrib.inputs["Z"])

    midrib_voronoi = nodes.new("ShaderNodeTexVoronoi")
    midrib_voronoi.voronoi_dimensions = "3D"
    midrib_voronoi.feature = "DISTANCE_TO_EDGE"
    midrib_voronoi.inputs["Scale"].default_value = 6.0
    links.new(comb_for_midrib.outputs["Vector"], midrib_voronoi.inputs["Vector"])

    midrib_fac = nodes.new("ShaderNodeMapRange")
    midrib_fac.inputs["From Min"].default_value = 0.0
    midrib_fac.inputs["From Max"].default_value = 0.015
    midrib_fac.inputs["To Min"].default_value = 1.0
    midrib_fac.inputs["To Max"].default_value = 0.0
    links.new(midrib_voronoi.outputs["Distance"], midrib_fac.inputs["Value"])

    rgb_stem_color = nodes.new("ShaderNodeRGB")
    rgb_stem_color.outputs[0].default_value = _hsv_to_rgba(*_STEM_COLOR_HSV)

    mix_midrib_rgb = nodes.new("ShaderNodeMixRGB")
    links.new(midrib_fac.outputs["Result"], mix_midrib_rgb.inputs["Fac"])
    links.new(rgb_stem_color.outputs["Color"], mix_midrib_rgb.inputs["Color1"])
    links.new(hsv_modulated.outputs["Color"], mix_midrib_rgb.inputs["Color2"])

    # --- nodegroup_leaf_shader body: Diffuse + Glossy(0.3) mix@0.2, then
    # Translucent mix@0.3 ---
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    links.new(mix_midrib_rgb.outputs["Color"], diffuse.inputs["Color"])

    glossy = nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Roughness"].default_value = 0.3
    links.new(mix_midrib_rgb.outputs["Color"], glossy.inputs["Color"])

    mix_diffuse_glossy = nodes.new("ShaderNodeMixShader")
    mix_diffuse_glossy.inputs["Fac"].default_value = 0.2
    links.new(diffuse.outputs["BSDF"], mix_diffuse_glossy.inputs[1])
    links.new(glossy.outputs["BSDF"], mix_diffuse_glossy.inputs[2])

    translucent = nodes.new("ShaderNodeBsdfTranslucent")
    links.new(mix_midrib_rgb.outputs["Color"], translucent.inputs["Color"])

    mix_translucent = nodes.new("ShaderNodeMixShader")
    mix_translucent.inputs["Fac"].default_value = 0.3
    links.new(mix_diffuse_glossy.outputs["Shader"], mix_translucent.inputs[1])
    links.new(translucent.outputs["BSDF"], mix_translucent.inputs[2])

    links.new(mix_translucent.outputs["Shader"], output_node.inputs["Surface"])
    return mat


def make_palm_stem_material(name="PalmStemMaterial"):
    mat = _new_mat(name)
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links

    output_node = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = _hsv_to_rgba(
        _STEM_MAT_H, _STEM_MAT_S, _STEM_MAT_V
    )
    links.new(principled.outputs["BSDF"], output_node.inputs["Surface"])
    return mat


MAT_LEAF = make_palm_leaf_material("PalmLeafMaterial")
MAT_STEM = make_palm_stem_material("PalmStemMaterial")
MAT_LEAF.use_fake_user = True
MAT_STEM.use_fake_user = True

# ═════════════════════════════════════════════════════════════════════════════
# Geometry — copied verbatim from objects_blender/tropic_plants/LeafPalmTreeFactory.py
# Only deltas:
#   (1) SEED now comes from the env var at module top (see above).
#   (2) build() is wrapped around the original main() body and attaches
#       MAT_STEM / MAT_LEAF to the stem and leaflet objects before join.
#   (3) The inlined create_palm_leaf_material() from the geometry-only script
#       is removed; it is replaced by the Phase 1 shader above.
# ═════════════════════════════════════════════════════════════════════════════

# ── helpers ───────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete()
    for m in list(bpy.data.meshes):    bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):   bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups): bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def catmull_rom_eval(ctrl_pts, x):
    if x <= ctrl_pts[0][0]:  return ctrl_pts[0][1]
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

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]], dtype=float)

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]], dtype=float)

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]], dtype=float)

# ── Stem ──────────────────────────────────────────────────────────────────────

def compute_stem_centerline(leaf_x_curvature, stem_x_curv, n_pts, stem_length=2.0):
    """Stem centerline via VectorRotate around Y and X axes.

    Original: CurveLine from (0,0,stem_length) to (0,0,0), then:
      1. VectorRotate Y, center=(0,0,stem_length), angle=leaf_x_curv*(1-factor)
      2. VectorRotate X, center=(0,0,0), angle=stem_x_curv*(1-factor)
    factor: 0 at tip (z=stem_length), 1 at base (z=0).
    """

    pts = []
    for i in range(n_pts):
        t = i / max(n_pts - 1, 1)  # 0=tip(top), 1=base(bottom)

        # Straight line: tip at (0,0,stem_length), base at (0,0,0)
        p = np.array([0.0, 0.0, stem_length * (1.0 - t)])

        # VectorRotate around Y, center=(0,0,stem_length)
        angle_y = leaf_x_curvature * (1.0 - t)
        center = np.array([0.0, 0.0, stem_length])
        rel = p - center
        cy, sy = math.cos(angle_y), math.sin(angle_y)
        p = center + np.array([rel[0]*cy + rel[2]*sy, rel[1], -rel[0]*sy + rel[2]*cy])

        # VectorRotate around X, center=(0,0,0)
        angle_x = stem_x_curv * (1.0 - t)
        cx, sx = math.cos(angle_x), math.sin(angle_x)
        p = np.array([p[0], p[1]*cx - p[2]*sx, p[1]*sx + p[2]*cx])

        pts.append(p)

    # Tangents via finite differences
    tangents = []
    for i in range(n_pts):
        if i == 0:
            tang = pts[1] - pts[0]
        elif i == n_pts - 1:
            tang = pts[-1] - pts[-2]
        else:
            tang = pts[i+1] - pts[i-1]
        tl = np.linalg.norm(tang)
        tangents.append(tang / tl if tl > 1e-8 else np.array([0.0, 0.0, -1.0]))

    return pts, tangents

def build_stem_tube(pts, tangents, stem_radius, r_taper_start):
    """Stem tube mesh with radius taper.
    Smoothstep from r_taper_start (at tip) to 0.8 (at base).
    """

    n_sides = 8; n = len(pts)
    bm = bmesh.new()
    rings = []

    for i in range(n):
        t = i / max(n - 1, 1)  # 0=tip, 1=base
        t_s = t * t * (3 - 2*t)
        r_scale = r_taper_start + (0.8 - r_taper_start) * t_s
        r = stem_radius * r_scale

        tang = tangents[i]
        up = np.array([0.0, 1.0, 0.0]) if abs(tang[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        right = np.cross(tang, up)
        right /= (np.linalg.norm(right) + 1e-8)
        fwd = np.cross(tang, right)

        ring = []
        for j in range(n_sides):
            a = 2*math.pi*j/n_sides
            offset = r * (math.cos(a)*right + math.sin(a)*fwd)
            ring.append(bm.verts.new(tuple(pts[i] + offset)))
        rings.append(ring)

    for i in range(n - 1):
        for j in range(n_sides):
            j2 = (j+1) % n_sides
            bm.faces.new([rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]])

    # Caps
    top = bm.verts.new(tuple(pts[0]))
    for j in range(n_sides):
        bm.faces.new([top, rings[0][j], rings[0][(j+1)%n_sides]])
    bot = bm.verts.new(tuple(pts[-1]))
    for j in range(n_sides):
        bm.faces.new([bot, rings[-1][(j+1)%n_sides], rings[-1][j]])

    mesh = bpy.data.meshes.new("stem")
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new("stem", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    apply_tf(obj)
    return obj

# ── Leaflet ───────────────────────────────────────────────────────────────────

def compute_frame(tangent):
    """Orthonormal frame: Z=tangent, Y≈world Y (projected ⊥ Z)."""

    Z = tangent / (np.linalg.norm(tangent) + 1e-8)
    world_y = np.array([0.0, 1.0, 0.0])
    Y = world_y - np.dot(world_y, Z) * Z
    yl = np.linalg.norm(Y)
    if yl < 1e-6:
        Y = np.array([0.0, 0.0, 1.0]) - np.dot(np.array([0.,0.,1.]), Z) * Z
        yl = np.linalg.norm(Y)
    Y /= yl
    X = np.cross(Y, Z)
    X /= (np.linalg.norm(X) + 1e-8)
    return X, Y, Z

def build_leaflet_into_bm(bm_out, stem_pos, R_frame, scale, side,
                           to_max, leaf_width_scale, stem_length_param):
    """Build one leaflet directly into bm_out.

    Uses the same pipeline as palm plant: contour + inner-leaf dome + leaf_rotate_x.
    Wave Scale X = 0, Wave Scale Y = 0 (no wave displacement for palm tree).
    """

    BLADE_HALF = 0.6  # hardcoded in original (clamp to [-0.6, 0.6])
    ny = 40; nx = 10  # rows along length, half-width columns

    t_rows = np.linspace(0.0, 1.0, ny + 1)
    Y_rows = np.linspace(-BLADE_HALF, BLADE_HALF, ny + 1)

    # Default contour from nodegroup_shape (7-point control)
    contour_ctrl = [
        (0.0, 0.0), (0.15, 0.25), (0.3818, 0.35), (0.6273, 0.3625),
        (0.7802, 0.2957), (0.8955, 0.2), (1.0, 0.0),
    ]
    hw_rows = np.array([catmull_rom_eval(contour_ctrl, t) * leaf_width_scale
                        for t in t_rows])
    hw_rows = np.maximum(hw_rows, 0.0)
    max_hw = max(float(np.max(hw_rows)), 1e-6)

    # Inner-leaf dome (from nodegroup_leaf_gen)
    fy_ctrl  = [(0.0, 0.0), (0.5182, 1.0), (1.0, 1.0)]
    fc_x_ctrl = [(0.0045, 0.0063), (0.0409, 0.0375), (0.4182, 0.05), (1.0, 0.0)]
    fy_rows = np.array([catmull_rom_eval(fy_ctrl, t) for t in t_rows])

    TIP_THRESH = max_hw * 0.04

    verts_by_row = []
    for i in range(ny + 1):
        hw = float(hw_rows[i]); fy = float(fy_rows[i])

        # move_to_origin: Y += BLADE_HALF → Y ∈ [0, 2*BLADE_HALF]
        Y_shifted = float(Y_rows[i]) + BLADE_HALF

        # leaf_rotate_x: angle = Y_shifted * to_max
        a = Y_shifted * to_max
        cos_a, sin_a = math.cos(a), math.sin(a)

        if hw < TIP_THRESH:
            ly = Y_shifted * cos_a
            lz = Y_shifted * sin_a
            local = np.array([0.0, side * ly, lz]) * scale
            wp = stem_pos + R_frame @ local
            verts_by_row.append([bm_out.verts.new(tuple(wp))])
        else:
            row = []
            for j in range(2*nx + 1):
                u = (j / nx) - 1.0
                lx = u * hw

                s_dome = hw * (1.0 - abs(u))
                z_inner = 0.7 * fy * catmull_rom_eval(fc_x_ctrl, s_dome)

                ly = Y_shifted * cos_a - z_inner * sin_a
                lz = Y_shifted * sin_a + z_inner * cos_a

                local = np.array([lx, side * ly, lz]) * scale
                wp = stem_pos + R_frame @ local
                row.append(bm_out.verts.new(tuple(wp)))
            verts_by_row.append(row)

    for i in range(ny):
        ra, rb = verts_by_row[i], verts_by_row[i + 1]
        if len(ra) == 1 and len(rb) == 1:
            pass
        elif len(ra) == 1:
            vt = ra[0]
            for j in range(len(rb) - 1):
                bm_out.faces.new([vt, rb[j], rb[j + 1]])
        elif len(rb) == 1:
            vt = rb[0]
            for j in range(len(ra) - 1):
                bm_out.faces.new([ra[j], ra[j + 1], vt])
        else:
            for j in range(len(ra) - 1):
                bm_out.faces.new([ra[j], ra[j + 1], rb[j + 1], rb[j]])

# ── Main build() ──────────────────────────────────────────────────────────────

def build(seed=SEED):
    rng = np.random.default_rng(seed)
    np.random.seed(seed)
    clear_scene()

    # Parameters (matching LeafPalmTreeFactory.update_params)
    leaf_x_curvature = float(rng.uniform(0.0, 0.8))
    leaf_instance_curvature_ratio = float(rng.uniform(0.3, 0.6))
    leaf_instance_width = float(rng.uniform(0.07, 0.15))
    num_leaf_samples = min(int(int(rng.integers(6, 10)) / leaf_instance_width), 120)
    stem_x_curv = float(rng.normal(0.0, 0.15))
    stem_length = 2.0
    stem_radius = float(rng.uniform(0.03, 0.06))
    r_taper_start = float(rng.uniform(0.1, 0.3))
    stem_length_param = float(rng.uniform(0.55, 0.65))  # Stem Length for leaflets

    # Rotation/scale curve parameters (sampled once, shared by both sides)
    scale_gap = float(rng.uniform(0.2, 0.5))
    rotation_gap = float(rng.uniform(0.2, 0.6))
    rotation_scale = float(rng.uniform(0.6, 1.2))
    in_out_scale = float(rng.normal(0.0, 0.7))

    plant_z_rotate = float(rng.uniform(-0.4, 0.4))
    ps = float(rng.uniform(0.8, 1.5))

    to_max = leaf_x_curvature * leaf_instance_curvature_ratio

    # Stem centerline
    n_stem_pts = num_leaf_samples + 2
    stem_pts, stem_tangents = compute_stem_centerline(
        leaf_x_curvature, stem_x_curv, n_stem_pts, stem_length)

    # Build stem tube
    stem_obj = build_stem_tube(stem_pts, stem_tangents, stem_radius, r_taper_start)
    stem_obj.data.materials.append(MAT_STEM)

    # Build all leaflets into one bmesh
    bm = bmesh.new()

    for side in [-1, 1]:
        for k in range(num_leaf_samples):
            t = k / max(num_leaf_samples - 1, 1)
            idx = min(int(t * (n_stem_pts - 1)), n_stem_pts - 1)

            # Scale: FloatCurve * 0.5 (Math MULTIPLY default) * random(0.7, 1.0)
            scale_t = catmull_rom_eval(
                [(0.0, 1.0 - scale_gap), (0.3, 1.0 - scale_gap/2.0),
                 (0.6, 1.0 - scale_gap/5.0), (1.0, 1.0)], t)
            rand_scale = float(rng.uniform(0.7, 1.0))
            total_scale = scale_t * 0.50 * rand_scale

            # Rotation up/down: FloatCurve(t) * rotation_scale * side
            rot_t = catmull_rom_eval(
                [(0.0, 1.0 - rotation_gap), (0.7, 1.0 - rotation_gap/2.0),
                 (1.0, 1.0)], t)
            angle_z = rot_t * rotation_scale * side

            # Rotation in/out: (FloatCurve(t) - 0.5) * in_out_scale
            inout_t = catmull_rom_eval(
                [(0.0, 0.0), (0.5136, 0.2188), (1.0, 0.8813)], t)
            angle_x = (inout_t - 0.5) * in_out_scale

            # Random rotation per instance
            rand_rx = float(rng.uniform(-0.3, 0.3))
            rand_ry = float(rng.uniform(-0.3, 0.3))

            # Compute instance frame: Z=tangent, Y≈world Y, mirror Y for side
            tangent = stem_tangents[idx]
            X_inst, Y_inst, Z_inst = compute_frame(tangent)
            R_base = np.column_stack([X_inst, Y_inst, Z_inst])

            # Local rotations: updown(Z) → inout(X) → random(X,Y)
            R_local = rot_z(angle_z) @ rot_x(angle_x) @ rot_x(rand_rx) @ rot_y(rand_ry)
            R_frame = R_base @ R_local

            build_leaflet_into_bm(bm, stem_pts[idx], R_frame, total_scale, side,
                                  to_max, leaf_instance_width, stem_length_param)

    # Create leaflet mesh object
    mesh = bpy.data.meshes.new("leaflets")
    bm.to_mesh(mesh); bm.free()
    leaf_obj = bpy.data.objects.new("leaflets", mesh)
    bpy.context.scene.collection.objects.link(leaf_obj)
    bpy.ops.object.select_all(action="DESELECT")
    leaf_obj.select_set(True); bpy.context.view_layer.objects.active = leaf_obj
    bpy.ops.object.shade_smooth()
    apply_tf(leaf_obj)
    leaf_obj.data.materials.append(MAT_LEAF)

    # Join stem + leaflets
    result = join_objs([stem_obj, leaf_obj])

    # Final transform (matching original: plant_z_rotate + plant_scale)
    result.rotation_euler.z = plant_z_rotate
    result.scale = (ps, ps, ps)
    apply_tf(result)
    result.name = "LeafPalmTreeFactory"
    return result


build(SEED)
