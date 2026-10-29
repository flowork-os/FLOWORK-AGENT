# [FL_INDEX: keywords="blender_factory, procedural_3d, PlantBananaTreeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PlantBananaTreeFactory | Category: factories_tex
# Prompt: A 3D model of a young banana plant rendered from a side perspective. The plant features a single large elongated oval leaf with a prominent midrib and fine parallel venation on the green upper surface, mounted on a long slender petiole stem rising from the ground.

import os
import math
import random
import colorsys

import bmesh
import bpy
import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
# Inlined materials for PlantBananaTreeFactory
#
#         - shader_leaf_material()              (whole-plant shader, uses
#                                                 `vein` attribute to switch
#                                                 between stem and leaf path)
#         - nodegroup_nodegroup_leaf_shader()   (diffuse/glossy/translucent mix)
#         - shader_stem_material()              (plant stem shader)
#
# The leaf shader output color is:
#   mix_1 = mix( vein_attr, leaf_path_color, stem_color )
# where `vein_attr` is a float geometry attribute set to 1 on the stem curve
# and 0 on the leaf blade. In the original plant geometry the stem curve also
# receives a separate shader_stem_material through SetMaterial before joining,
# so the baked-mesh version keeps TWO separate part materials:
#
#   MAT_LEAF_BLADE : full shader_leaf_material with vein=0 (leaf path)
#   MAT_STEM       : shader_stem_material
#
# All other nodes (NoiseTexture, SeparateRGB, MapRange, HueSaturation, the
# MixRGB "mix" that picks between two slightly different main_leaf_hsv values,
# and the diffuse+glossy+translucent MixShader leaf_shader group) are replicated
# verbatim in raw bpy node-tree code for the leaf material.
#
# Natural / no wear_tear.
# ══════════════════════════════════════════════════════════════════════════════

def seed_all(seed):
    np.random.seed(int(seed))
    random.seed(int(seed))

def _hsv2rgba(h, s, v):
    h = float(h) % 1.0
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, float(v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _noise_factor_output(noise_node):
    """Blender 4.x names this 'Fac', Blender 5.x renames it to 'Factor'."""

    out = noise_node.outputs.get("Fac") or noise_node.outputs.get("Factor")
    return out if out is not None else noise_node.outputs[0]

def _build_leaf_shader_group(name="nodegroup_leaf_shader"):
    """Faithful replica of tropic_plant_utils.nodegroup_nodegroup_leaf_shader.

    Input: Color (NodeSocketColor)
    Output: Shader
    Structure:
        DiffuseBSDF(Color) --+
                             MixShader(Fac=0.2) -> mix_shader
        GlossyBSDF(Color, R=0.3) -+
        mix_shader ----------------+
                                    MixShader(Fac=0.3) -> mix_shader_1 -> out
        TranslucentBSDF(Color) ----+
    """

    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    ng = bpy.data.node_groups.new(name, "ShaderNodeTree")
    ng.interface.new_socket(name="Color", in_out="INPUT", socket_type="NodeSocketColor")
    ng.interface.new_socket(name="Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")

    diffuse = ng.nodes.new("ShaderNodeBsdfDiffuse")
    glossy = ng.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Roughness"].default_value = 0.3
    translucent = ng.nodes.new("ShaderNodeBsdfTranslucent")

    mix1 = ng.nodes.new("ShaderNodeMixShader")
    mix1.inputs[0].default_value = 0.2  # Fac
    mix2 = ng.nodes.new("ShaderNodeMixShader")
    mix2.inputs[0].default_value = 0.3  # Fac

    link = ng.links.new
    link(gi.outputs["Color"], diffuse.inputs["Color"])
    link(gi.outputs["Color"], glossy.inputs["Color"])
    link(gi.outputs["Color"], translucent.inputs["Color"])
    link(diffuse.outputs["BSDF"], mix1.inputs[1])
    link(glossy.outputs["BSDF"], mix1.inputs[2])
    link(mix1.outputs["Shader"], mix2.inputs[1])
    link(translucent.outputs["BSDF"], mix2.inputs[2])
    link(mix2.outputs["Shader"], go.inputs["Shader"])
    return ng

def _build_shader_leaf_material(name, *, stem_color_hsv, main_leaf_hsv,
                                 main_leaf_hsv_2, force_vein):
    """Replicate shader_leaf_material from leaf_banana_tree.py.

    force_vein:
        0.0 -> render the leaf path  (used for MAT_LEAF_BLADE)
        1.0 -> render the stem color (used for MAT_STEM)

    All sampled RNG values (main_leaf_hsv, main_leaf_hsv_2) must be drawn in
    the same numpy.random call order as the original so seeds stay
    aligned:
        main_leaf_hsv       = (U(0.26,0.37), U(0.8,1.0), U(0.15,0.55))
        main_leaf_hsv_2     = (main_leaf_hsv[0] + N(0, 0.02),) + main_leaf_hsv[1:]
    Caller samples them once per SEED and passes them into both materials so
    stem and leaf stay colour-coordinated.
    """

    mat = _new_mat(name)
    nt = mat.node_tree
    link = nt.links.new

    # --- Texture coordinate + noise (procedural leaf variation) ---
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.8
    noise.inputs["Detail"].default_value = 10.0
    noise.inputs["Roughness"].default_value = 0.7
    link(tex_coord.outputs["Object"], noise.inputs["Vector"])

    # SeparateRGB on noise Color → channels drive hue / value variation
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    sep.mode = "RGB"
    link(noise.outputs["Color"], sep.inputs[0])

    # MapRange #1: noise.G in [0.4, 0.7] -> hue offset in [0.48, 0.52]
    mr_hue = nt.nodes.new("ShaderNodeMapRange")
    mr_hue.inputs[1].default_value = 0.4
    mr_hue.inputs[2].default_value = 0.7
    mr_hue.inputs[3].default_value = 0.48
    mr_hue.inputs[4].default_value = 0.52
    link(sep.outputs["Green"], mr_hue.inputs["Value"])

    # MapRange #2: noise.B in [0.4, 0.7] -> value multiplier in [0.8, 1.2]
    mr_val = nt.nodes.new("ShaderNodeMapRange")
    mr_val.inputs[1].default_value = 0.4
    mr_val.inputs[2].default_value = 0.7
    mr_val.inputs[3].default_value = 0.8
    mr_val.inputs[4].default_value = 1.2
    link(sep.outputs["Blue"], mr_val.inputs["Value"])

    # subvein offset attribute drives mr_sub (min=-0.94 .. max=1.0 -> black/white)
    # Our baked geometry has no 'subvein offset' attribute so Blender will
    # default the attribute Color to black (0,0,0). The MapRange will then
    # produce a constant value, baking the "mix between main_leaf_hsv and
    # main_leaf_hsv_2" toward Color1. We still build the full node network so
    # the shader structure matches 1:1.
    attr_subvein = nt.nodes.new("ShaderNodeAttribute")
    attr_subvein.attribute_name = "subvein offset"

    mr_sub = nt.nodes.new("ShaderNodeMapRange")
    mr_sub.inputs[1].default_value = 0.0    # From Min default
    mr_sub.inputs[2].default_value = -0.94  # From Max (sets idx 2=-0.94)
    mr_sub.inputs[3].default_value = 0.0    # To Min default
    mr_sub.inputs[4].default_value = 1.0    # To Max default
    link(attr_subvein.outputs["Color"], mr_sub.inputs["Value"])

    # HueSaturationValue on main_leaf_hsv color, Value = 2.0 (brighter)
    hsv_main = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_main.inputs["Hue"].default_value = 0.5
    hsv_main.inputs["Saturation"].default_value = 1.0
    hsv_main.inputs["Value"].default_value = 2.0
    hsv_main.inputs["Fac"].default_value = 1.0
    hsv_main.inputs["Color"].default_value = _hsv2rgba(*main_leaf_hsv)

    # MixRGB: blend between the two slightly different main_leaf_hsv variants
    # using subvein MapRange as Fac. In Blender 5.x ShaderNodeMixRGB still
    # exists (legacy) and is what the transpiler emits — keep it for parity.
    mix_leaf = nt.nodes.new("ShaderNodeMix")
    mix_leaf.data_type = "RGBA"
    mix_leaf.blend_type = "MIX"
    link(mr_sub.outputs["Result"], mix_leaf.inputs[0])
    link(hsv_main.outputs["Color"], mix_leaf.inputs[6])
    mix_leaf.inputs[7].default_value = _hsv2rgba(*main_leaf_hsv_2)

    # Second HueSaturationValue: hue shift from mr_hue, value from mr_val
    hsv_detail = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_detail.inputs["Saturation"].default_value = 1.0
    hsv_detail.inputs["Fac"].default_value = 1.0
    link(mr_hue.outputs["Result"], hsv_detail.inputs["Hue"])
    link(mr_val.outputs["Result"], hsv_detail.inputs["Value"])
    link(mix_leaf.outputs[2], hsv_detail.inputs["Color"])

    # mix_1: attribute "vein" chooses between stem color (Color1) and leaf
    # path (Color2). We replace the attribute with a constant Fac because
    # our baked mesh has no vein attribute.
    mix_vein = nt.nodes.new("ShaderNodeMix")
    mix_vein.data_type = "RGBA"
    mix_vein.blend_type = "MIX"
    mix_vein.inputs[0].default_value = float(force_vein)
    mix_vein.inputs[6].default_value = _hsv2rgba(*stem_color_hsv)
    link(hsv_detail.outputs["Color"], mix_vein.inputs[7])

    # leaf_shader nodegroup (diffuse + glossy + translucent MixShader)
    group_node = nt.nodes.new("ShaderNodeGroup")
    group_node.node_tree = _build_leaf_shader_group()
    link(mix_vein.outputs[2], group_node.inputs["Color"])

    output = nt.nodes.new("ShaderNodeOutputMaterial")
    link(group_node.outputs["Shader"], output.inputs["Surface"])
    return mat

def _build_shader_stem_material(name, *, stem_color_hsv):
    """Replicate tropic_plant_utils.shader_stem_material."""

    mat = _new_mat(name)
    nt = mat.node_tree
    link = nt.links.new

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = _hsv2rgba(*stem_color_hsv)

    output = nt.nodes.new("ShaderNodeOutputMaterial")
    link(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat

# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#
# PlantBananaTreeFactory.__init__ creates LeafBananaTreeFactory(factory_seed)
# but neither __init__ touches numpy RNG. All material randomness happens
# inside shader_leaf_material() which is called from create_asset() under
# the int_hash((factory_seed, i)) geometry seed. The spec still instructs us
# to sample materials on the raw factory seed before build() — that is the
# cleanest convention across textured factories. The material state is
# captured in MAT_LEAF_BLADE / MAT_STEM; build() re-seeds numpy for geometry
# via sample_params and is unaffected.
#
# Call order inside shader_leaf_material (numpy.random only):
#     main_leaf_hsv    = (uniform(0.26, 0.37),
#                         uniform(0.8, 1.0),
#                         uniform(0.15, 0.55))
#     main_leaf_hsv_2  = (main_leaf_hsv[0] + normal(0.0, 0.02),) + main_leaf_hsv[1:]
#
# stem_color_hsv is sampled in update_params (also numpy.random under the
# SEED so the two materials agree):
#     stem_color_hsv   = (uniform(0.25, 0.32),
#                         uniform(0.8, 1.0),
#                         uniform(0.8, 1.0))

SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)

# stem_color_hsv first so the call order for shader_leaf_material below can
# mirror exactly.
STEM_COLOR_HSV = (
    float(np.random.uniform(0.25, 0.32)),
    float(np.random.uniform(0.8, 1.0)),
    float(np.random.uniform(0.8, 1.0)),
)
MAIN_LEAF_HSV = (
    float(np.random.uniform(0.26, 0.37)),
    float(np.random.uniform(0.8, 1.0)),
    float(np.random.uniform(0.15, 0.55)),
)
MAIN_LEAF_HSV_2 = (
    MAIN_LEAF_HSV[0] + float(np.random.normal(0.0, 0.02)),
    MAIN_LEAF_HSV[1],
    MAIN_LEAF_HSV[2],
)

MAT_LEAF_BLADE = _build_shader_leaf_material(
    "PlantBananaTreeFactory_LeafBlade",
    stem_color_hsv=STEM_COLOR_HSV,
    main_leaf_hsv=MAIN_LEAF_HSV,
    main_leaf_hsv_2=MAIN_LEAF_HSV_2,
    force_vein=0.0,  # leaf path of mix_1
)
MAT_LEAF_BLADE.use_fake_user = True

MAT_STEM = _build_shader_stem_material(
    "PlantBananaTreeFactory_Stem",
    stem_color_hsv=STEM_COLOR_HSV,
)
MAT_STEM.use_fake_user = True

# PlantBananaTreeFactory does NOT use wear_tear — natural plant.

# ══════════════════════════════════════════════════════════════════════════════
# Geometry — copied VERBATIM from objects_blender/tropic_plants/PlantBananaTreeFactory.py
# (only modification: material append on stem_obj and leaf before join_objs)
# ══════════════════════════════════════════════════════════════════════════════

# ── parse seed ────────────────────────────────────────────────────────────────
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
        # Keep the leaf_shader nodegroup we just built for the materials.
        if ng.name == "nodegroup_leaf_shader":
            continue
        bpy.data.node_groups.remove(ng)
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

def catmull_rom_1d(ts_ctrl, vals, ts_out):
    v = np.array(vals, dtype=float)
    t = np.array(ts_ctrl, dtype=float)
    v_ext = np.concatenate([[2*v[0]-v[1]], v, [2*v[-1]-v[-2]]])
    result = np.zeros(len(ts_out))
    for k, tq in enumerate(ts_out):
        seg = int(np.searchsorted(t, tq, side='right')) - 1
        seg = max(0, min(seg, len(t) - 2))
        t0, t1 = t[seg], t[seg + 1]
        dt = t1 - t0
        if dt < 1e-10:
            result[k] = v[seg]
            continue
        u = (tq - t0) / dt
        u2, u3 = u*u, u*u*u
        p0, p1, p2, p3 = v_ext[seg], v_ext[seg+1], v_ext[seg+2], v_ext[seg+3]
        result[k] = 0.5 * ((2*p1) + (-p0+p2)*u + (2*p0-5*p1+4*p2-p3)*u2 +
                            (-p0+3*p1-3*p2+p3)*u3)
    return result

# ── Parameters ────────────────────────────────────────────────────────────────

def sample_params(rng):
    contour_mode = rng.choice(["oval", "pear"])
    if contour_mode == "oval":
        contour_pts = [0.13, 0.275, 0.35, 0.365, 0.32, 0.21]
    else:
        contour_pts = [0.30, 0.46, 0.46, 0.43, 0.37, 0.23]

    leaf_width = float(rng.uniform(0.6, 0.95))

    h_mode = rng.choice(["flat", "w", "s"], p=[0.4, 0.3, 0.3])
    if h_mode == "flat":
        h_wave_pts = [float(rng.normal(0.0, 0.03)) for _ in range(5)]
    elif h_mode == "s":
        h_wave_pts = [
            -0.1 + float(rng.normal(0.0, 0.02)),
            0.0 + float(rng.normal(0.0, 0.02)),
            0.08 + float(rng.normal(0.0, 0.02)),
            0.0 + float(rng.normal(0.0, 0.02)),
            -0.05 + float(rng.normal(0.0, 0.01)),
        ]
    else:  # w
        h_wave_pts = [
            -0.08 + float(rng.normal(0.0, 0.02)),
            0.07 + float(rng.normal(0.0, 0.02)),
            -0.08 + float(rng.normal(0.0, 0.02)),
            0.08 + float(rng.normal(0.0, 0.02)),
            -0.05 + float(rng.normal(0, 0.02)),
        ]
    h_wave_scale = float(rng.uniform(0.02, 0.2))

    w_mode = rng.choice(["fold", "wing"], p=[0.2, 0.8])
    if w_mode == "fold":
        w_wave_pts = [
            -0.28 + float(rng.normal(0.0, 0.02)),
            -0.2 + float(rng.normal(0.0, 0.02)),
            -0.13 + float(rng.normal(0.0, 0.01)),
            -0.06 + float(rng.normal(0.0, 0.01)),
        ]
        w_wave_scale = float(rng.uniform(0.1, 0.3))
    else:  # wing
        w_wave_pts = [
            0.0 + float(rng.normal(0.0, 0.02)),
            0.06 + float(rng.normal(0.0, 0.02)),
            0.07 + float(rng.normal(0.0, 0.01)),
            0.04 + float(rng.normal(0.0, 0.01)),
        ]
        w_wave_scale = float(rng.uniform(0.0, 0.3))

    leaf_x_curvature = float(rng.uniform(0.0, 0.25))
    jigsaw_depth = float(rng.choice([0, 1]) * rng.uniform(0.8, 1.7))

    return {
        "contour_pts": contour_pts,
        "leaf_width": leaf_width,
        "h_wave_pts": h_wave_pts,
        "h_wave_scale": h_wave_scale,
        "w_wave_pts": w_wave_pts,
        "w_wave_scale": w_wave_scale,
        "leaf_x_curvature": leaf_x_curvature,
        "jigsaw_depth": jigsaw_depth,
    }

# ── Leaf Blade ────────────────────────────────────────────────────────────────

def build_leaf_blade(rng, params):
    """

    Build the banana leaf blade as a high-resolution quad-strip mesh
    with lateral vein grooves, midrib depression, and edge undulation.
    Leaf base at Y=0, tip at Y=leaf_length (extends upward from stem tip).
    """

    contour_pts = params["contour_pts"]
    leaf_width = params["leaf_width"]
    h_wave_pts = params["h_wave_pts"]
    h_wave_scale = params["h_wave_scale"]
    w_wave_pts = params["w_wave_pts"]
    w_wave_scale = params["w_wave_scale"]
    leaf_x_curvature = params["leaf_x_curvature"]
    jigsaw_depth = params["jigsaw_depth"]

    leaf_length = 1.8  # slightly longer blade for better proportions
    nx = 128  # high res along length for sharp vein detail
    ny = 20   # smooth cross-section

    # Lateral vein parameters (visible horizontal stripes across leaf)
    n_veins = int(rng.integers(28, 42))
    vein_depth = float(rng.uniform(0.0015, 0.0035))
    # Midrib channel
    midrib_depth = float(rng.uniform(0.002, 0.005))
    midrib_sigma = float(rng.uniform(0.03, 0.06))
    # Edge undulation
    edge_wave_freq = float(rng.uniform(8, 15))
    edge_wave_amp = float(rng.uniform(0.002, 0.005))

    # Contour t-positions's FloatCurve
    # Taper to 0 at both base (t=0) and tip (t=1) — pointed ends
    contour_t = np.array([0.0, 0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0])
    contour_v = np.array([0.0] + list(contour_pts) + [0.0])
    t_rows = np.linspace(0.0, 1.0, nx + 1)
    half_widths = catmull_rom_1d(contour_t, contour_v, t_rows) * leaf_width
    half_widths = np.clip(half_widths, 0.0, None)

    # Height wave — 7 knots to match 5 wave points + 2 zero endpoints
    h_t = np.array([0.0, 0.125, 0.3, 0.5, 0.7, 0.875, 1.0])
    h_v = np.array([0.0] + list(h_wave_pts) + [0.0])
    z_h = catmull_rom_1d(h_t, h_v, t_rows) * h_wave_scale * leaf_length

    w_t = np.array([0.0, 0.33, 0.67, 1.0])
    w_v = np.array(w_wave_pts[:4])
    abs_xf_samples = np.linspace(0.0, 1.0, ny + 1)
    z_w_profile = catmull_rom_1d(w_t, w_v, abs_xf_samples) * w_wave_scale * leaf_length

    bm = bmesh.new()
    grid = {}

    for i, t in enumerate(t_rows):
        hw = half_widths[i]
        z_long = z_h[i]
        y_pos = t * leaf_length  # base at Y=0, tip at Y=leaf_length
        x_lean = leaf_x_curvature * t * leaf_length * 0.1
        # Gentle parabolic droop toward tip
        z_droop = -leaf_x_curvature * (t ** 2) * leaf_length * 0.8

        # Lateral vein pattern at this Y position
        vein_phase = t * n_veins * 2.0 * math.pi
        vein_primary = math.cos(vein_phase)
        vein_sub = math.cos(vein_phase * 3.17 + 0.7)

        # Fade veins near base and tip
        tip_factor = min(t / 0.12, 1.0) * min((1.0 - t) / 0.05, 1.0)
        tip_factor = max(0.0, min(1.0, tip_factor))

        for j in range(2 * ny + 1):
            xf = (j / ny) - 1.0
            x_abs = abs(xf)
            x = xf * hw
            j_idx = min(int(x_abs * ny), ny)
            z_cross = z_w_profile[j_idx]
            z = z_long + z_cross + x_lean + z_droop

            # Lateral vein ridges and grooves
            edge_factor = max(0.0, 1.0 - 0.5 * x_abs)
            vein_z = (vein_primary + vein_sub * 0.25) * vein_depth
            z += vein_z * edge_factor * tip_factor

            # Midrib depression
            midrib_z = -midrib_depth * math.exp(-(xf ** 2) / (2.0 * midrib_sigma ** 2))
            z += midrib_z * tip_factor

            # Edge undulation
            if x_abs > 0.55:
                edge_t = (x_abs - 0.55) / 0.45
                edge_z = edge_wave_amp * math.sin(t * edge_wave_freq * 2.0 * math.pi)
                z += edge_z * edge_t * tip_factor

            v = bm.verts.new((x, y_pos, z))
            grid[(i, j)] = v

    for i in range(nx):
        for j in range(2 * ny):
            v0 = grid[(i, j)]
            v1 = grid[(i, j+1)]
            v2 = grid[(i+1, j+1)]
            v3 = grid[(i+1, j)]
            bm.faces.new([v0, v1, v2, v3])

    mesh = bpy.data.meshes.new("leaf_blade")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("leaf_blade", mesh)
    bpy.context.collection.objects.link(obj)

    if jigsaw_depth > 0.1:
        tex = bpy.data.textures.new("jigsaw", type="STUCCI")
        tex.noise_scale = 0.05
        d = obj.modifiers.new("jig", "DISPLACE")
        d.texture = tex
        d.texture_coords = 'LOCAL'
        d.direction = 'Y'
        d.strength = jigsaw_depth * 0.02
        d.mid_level = 0.5
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=d.name)

    apply_tf(obj)
    return obj

# ── Stem ──────────────────────────────────────────────────────────────────────

def build_stem(rng, stem_length=2.0, stem_radius=0.015):
    """Curved tapered stem: thin and elegant, from (0,0,0) upward."""

    n_segs = 32   # smoother curve
    n_sides = 12  # rounder cross-section
    y_curv = float(rng.uniform(-1.0, 1.0))   # stronger curve
    x_curv = float(rng.uniform(-0.3, 0.3))  # allow bidirectional

    bm = bmesh.new()
    rings = []
    for i in range(n_segs + 1):
        t = i / n_segs
        z = t * stem_length
        x = x_curv * t * t * stem_length * 0.15
        y = y_curv * t * t * stem_length * 0.15

        r = stem_radius * (1.0 - 0.5 * t)  # stronger taper to fine tip

        up = np.array([0.0, 0.0, 1.0])
        d = np.array([x_curv * 2 * t * 0.15, y_curv * 2 * t * 0.15, 1.0])
        d /= (np.linalg.norm(d) + 1e-8)
        right = np.cross(d, up)
        if np.linalg.norm(right) < 1e-8:
            right = np.array([1.0, 0.0, 0.0])
        right /= np.linalg.norm(right)
        fwd = np.cross(right, d)

        ring = []
        for j in range(n_sides):
            theta = 2 * math.pi * j / n_sides
            offset = r * (math.cos(theta) * right + math.sin(theta) * fwd)
            ring.append(bm.verts.new(tuple(np.array([x, y, z]) + offset)))
        rings.append(ring)

    for i in range(n_segs):
        for j in range(n_sides):
            j2 = (j + 1) % n_sides
            bm.faces.new([rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]])

    bot = bm.verts.new((0, 0, 0))
    for j in range(n_sides):
        bm.faces.new([bot, rings[0][(j+1)%n_sides], rings[0][j]])

    mesh = bpy.data.meshes.new("stem")
    bm.to_mesh(mesh)
    bm.free()
    stem_obj = bpy.data.objects.new("stem", mesh)
    bpy.context.collection.objects.link(stem_obj)
    apply_tf(stem_obj)
    # Tip position accounts for stem curvature
    tip_x = x_curv * 1.0 * stem_length * 0.15
    tip_y = y_curv * 1.0 * stem_length * 0.15
    return stem_obj, (tip_x, tip_y, stem_length)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    rng = np.random.default_rng(SEED)
    np.random.seed(SEED)
    clear_scene()

    params = sample_params(rng)
    parts = []

    stem_length = float(rng.uniform(2.0, 3.0))  # longer stem (~60% of total)
    stem_obj, tip_pos = build_stem(rng, stem_length)
    # Assign stem shader BEFORE any join().
    stem_obj.data.materials.clear()
    stem_obj.data.materials.append(MAT_STEM)
    parts.append(stem_obj)

    # Build leaf and position at stem tip (base at tip, extends upward)
    leaf = build_leaf_blade(rng, params)
    s = float(rng.uniform(0.8, 1.3))
    leaf.scale = (s, s, s)
    tilt = float(rng.uniform(0.2, 0.5))  # 11-29° tilt from vertical
    leaf.rotation_euler.x = math.pi * 0.5 - tilt
    leaf.rotation_euler.z = float(rng.uniform(-0.4, 0.4))
    leaf.location = tip_pos
    apply_tf(leaf)
    # Assign leaf-blade shader BEFORE join().
    leaf.data.materials.clear()
    leaf.data.materials.append(MAT_LEAF_BLADE)
    parts.append(leaf)

    result = join_objs(parts)
    result.name = "PlantBananaTreeFactory"
    apply_tf(result)

    d = result.dimensions
    return result

if __name__ == "__main__":
    main()

