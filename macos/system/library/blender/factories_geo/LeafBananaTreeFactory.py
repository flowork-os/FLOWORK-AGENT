# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafBananaTreeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafBananaTreeFactory | Category: factories_geo
# Prompt: A 3D model of a single banana tree leaf rendered from a slightly elevated perspective. The leaf features a large, broad elliptical blade with a prominent central midrib, fine parallel lateral veins running across the bright green upper surface, and a dark underside.

"""LeafBananaTreeFactory — textured standalone.
Geometry: copied verbatim from
    objects_blender/tropic_plants/LeafBananaTreeFactory.py
"""


import os
import math
import random
import colorsys

import bpy
import bmesh
import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
# Seeding
# ══════════════════════════════════════════════════════════════════════════════

SEED = int(os.environ.get("SEED", "0"))


def seed_all(seed):
    np.random.seed(int(seed))
    random.seed(int(seed))


def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0,
                                  max(0.0, min(1.0, float(s))),
                                  max(0.0, min(1.0, float(v))))
    return (r, g, b, 1.0)


def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def _noise_fac(noise_node):
    # Blender 5.0 renamed "Fac" -> "Factor"; fall back to first output.
    return (noise_node.outputs.get("Fac")
            or noise_node.outputs.get("Factor")
            or noise_node.outputs[0])


# ══════════════════════════════════════════════════════════════════════════════
# Leaf-shader NodeGroup (ShaderNodeTree)
#     mirrors tropic_plant_utils.nodegroup_nodegroup_leaf_shader
#     inputs : Color
#     body   : diffuse + glossy(0.3)  ── mix(0.2) ──  translucent  ── mix(0.3)
# ══════════════════════════════════════════════════════════════════════════════

def _build_leaf_shader_nodegroup():
    name = "nodegroup_nodegroup_leaf_shader"
    group = bpy.data.node_groups.get(name)
    if group is not None:
        return group

    group = bpy.data.node_groups.new(name, "ShaderNodeTree")

    group.interface.new_socket("Color", in_out="INPUT", socket_type="NodeSocketColor")
    group.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")

    nodes = group.nodes
    link = group.links.new

    grp_in = nodes.new("NodeGroupInput")
    grp_out = nodes.new("NodeGroupOutput")

    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    glossy = nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Roughness"].default_value = 0.3

    translucent = nodes.new("ShaderNodeBsdfTranslucent")

    link(grp_in.outputs["Color"], diffuse.inputs["Color"])
    link(grp_in.outputs["Color"], glossy.inputs["Color"])
    link(grp_in.outputs["Color"], translucent.inputs["Color"])

    mix_diffuse_glossy = nodes.new("ShaderNodeMixShader")
    mix_diffuse_glossy.inputs["Fac"].default_value = 0.2
    link(diffuse.outputs["BSDF"], mix_diffuse_glossy.inputs[1])
    link(glossy.outputs["BSDF"], mix_diffuse_glossy.inputs[2])

    mix_translucent = nodes.new("ShaderNodeMixShader")
    mix_translucent.inputs["Fac"].default_value = 0.3
    link(mix_diffuse_glossy.outputs["Shader"], mix_translucent.inputs[1])
    link(translucent.outputs["BSDF"], mix_translucent.inputs[2])

    link(mix_translucent.outputs["Shader"], grp_out.inputs["Shader"])
    return group


# ══════════════════════════════════════════════════════════════════════════════
# shader_leaf_material (faithful port of leaf_banana_tree.shader_leaf_material)
# ══════════════════════════════════════════════════════════════════════════════

def make_leaf_material(seed, name="LeafBananaTree_Material"):
    """Replicates the leaf material shader.
    numpy.random consumption order for raw-seed reproduction (must match
    for raw-seed reproduction):
      1. main_leaf_hsv   = (U(0.26,0.37), U(0.8,1.0), U(0.15,0.55))
      2. main_leaf_hsv_2 = (main_leaf_hsv[0] + N(0, 0.02), s, v)
      3. colorramp[1].position = U(0.3, 0.5)   (inside nodegroup_apply_wave in
         geometry path; NOT consumed here — the outer shader does not touch it)
      4. stem_color_hsv  = (U(0.25,0.32), U(0.8,1.0), U(0.8,1.0))   (from
         factory.update_params; fed in as parameter)
    We follow the factory-level call order: update_params first (=> stem_color
    + leaf wave params we ignore for shader), then shader_leaf_material.
    Here, since we only need shader colours, we re-sample stem_color before
    main_leaf_hsv to match the factory order.
    """

    seed_all(seed)

    # (only the entries that come before shader sampling matter for rng state).
    _ = np.random.choice(["flat", "w", "s"], p=[0.4, 0.3, 0.3])        # h-mode
    _ = [float(np.random.normal(0, 0.03)) for _ in range(6)]           # h-wave
    _ = np.random.choice(["fold", "wing"], p=[0.2, 0.8])               # w-mode
    _ = [float(np.random.normal(0, 0.02)) for _ in range(4)]           # w-wave pts
    _ = float(np.random.uniform(0.0, 0.3))                             # w-wave scale
    _ = np.random.choice(["wavy", "flat"], p=[1.0, 0.0])               # e-mode
    _ = [float(np.random.normal(0, 0.01)) for _ in range(9)]           # e-wave
    _ = np.random.choice(["oval", "pear"], p=[0.5, 0.5])               # contour mode
    _ = np.random.choice([0, 1], p=[0.4, 0.6])                         # jigsaw
    if _ != 0:
        _ = float(np.random.uniform(0.8, 1.7))                         # jigsaw depth
    _ = float(np.random.uniform(0.5, 0.85))                            # leaf_width
    _ = float(np.random.uniform(0.02, 0.2))                            # h_wave_scale
    _ = float(np.random.uniform(0.05, 0.25))                           # w_wave_scale (ignored — resampled if w_mode=fold, but we skip)
    _ = float(np.random.uniform(0.0, 0.1))                             # leaf_x_curvature
    stem_color_hsv = (float(np.random.uniform(0.25, 0.32)),
                      float(np.random.uniform(0.8, 1.0)),
                      float(np.random.uniform(0.8, 1.0)))

    # shader_leaf_material internal sampling:
    main_leaf_hsv = (float(np.random.uniform(0.26, 0.37)),
                     float(np.random.uniform(0.8, 1.0)),
                     float(np.random.uniform(0.15, 0.55)))
    main_leaf_hsv_2 = (main_leaf_hsv[0] + float(np.random.normal(0.0, 0.02)),
                       main_leaf_hsv[1], main_leaf_hsv[2])

    main_rgba   = _hsv2rgba(*main_leaf_hsv)
    main_rgba_2 = _hsv2rgba(*main_leaf_hsv_2)
    stem_rgba   = _hsv2rgba(*stem_color_hsv)

    # ── Build node tree ───────────────────────────────────────────────────────
    leaf_shader_group = _build_leaf_shader_nodegroup()

    mat = _new_mat(name)
    nt = mat.node_tree
    link = nt.links.new

    # are written by the geomod. Our standalone geometry does not write them, so
    # attribute lookups return (0,0,0,1). The shader still constructs them so
    # the shader graph stays faithful.
    attr_vein = nt.nodes.new("ShaderNodeAttribute")
    attr_vein.attribute_name = "vein"

    attr_subvein = nt.nodes.new("ShaderNodeAttribute")
    attr_subvein.attribute_name = "subvein offset"

    # Texture coordinate -> noise
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.8
    noise.inputs["Detail"].default_value = 10.0
    noise.inputs["Roughness"].default_value = 0.7
    link(tex_coord.outputs["Object"], noise.inputs["Vector"])

    # Separate noise color -> G drives hue map, B drives value map
    sep_rgb = nt.nodes.new("ShaderNodeSeparateColor")
    sep_rgb.mode = "RGB"
    link(noise.outputs["Color"], sep_rgb.inputs[0])

    map_range_hue = nt.nodes.new("ShaderNodeMapRange")
    map_range_hue.inputs[1].default_value = 0.4   # From Min
    map_range_hue.inputs[2].default_value = 0.7   # From Max
    map_range_hue.inputs[3].default_value = 0.48  # To Min
    map_range_hue.inputs[4].default_value = 0.52  # To Max
    link(sep_rgb.outputs[1], map_range_hue.inputs["Value"])  # G

    map_range_val = nt.nodes.new("ShaderNodeMapRange")
    map_range_val.inputs[1].default_value = 0.4
    map_range_val.inputs[2].default_value = 0.7
    map_range_val.inputs[3].default_value = 0.8
    map_range_val.inputs[4].default_value = 1.2
    link(sep_rgb.outputs[2], map_range_val.inputs["Value"])  # B

    # subvein offset -> MapRange(To Max = -0.94)
    map_range_subvein = nt.nodes.new("ShaderNodeMapRange")
    map_range_subvein.inputs[1].default_value = 0.0   # From Min
    map_range_subvein.inputs[2].default_value = 1.0   # From Max
    map_range_subvein.inputs[3].default_value = 0.0   # To Min
    map_range_subvein.inputs[4].default_value = -0.94  # To Max
    link(attr_subvein.outputs["Color"], map_range_subvein.inputs["Value"])

    # HueSaturation (Value=2.0, Color=main_leaf_rgba)
    hsv_main = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_main.inputs["Value"].default_value = 2.0
    hsv_main.inputs["Color"].default_value = main_rgba

    # MixRGB (Fac=subvein, Color1=hsv_main, Color2=main_rgba_2)
    mix_subvein = nt.nodes.new("ShaderNodeMixRGB")
    mix_subvein.blend_type = "MIX"
    link(map_range_subvein.outputs["Result"], mix_subvein.inputs["Fac"])
    link(hsv_main.outputs["Color"], mix_subvein.inputs["Color1"])
    mix_subvein.inputs["Color2"].default_value = main_rgba_2

    # HueSaturation(Hue=map_range_hue, Value=map_range_val, Color=mix_subvein)
    hsv_driven = nt.nodes.new("ShaderNodeHueSaturation")
    link(map_range_hue.outputs["Result"], hsv_driven.inputs["Hue"])
    link(map_range_val.outputs["Result"], hsv_driven.inputs["Value"])
    link(mix_subvein.outputs["Color"], hsv_driven.inputs["Color"])

    # MixRGB (Fac=attr_vein, Color1=stem_rgba, Color2=hsv_driven)
    mix_vein = nt.nodes.new("ShaderNodeMixRGB")
    mix_vein.blend_type = "MIX"
    link(attr_vein.outputs["Color"], mix_vein.inputs["Fac"])
    mix_vein.inputs["Color1"].default_value = stem_rgba
    link(hsv_driven.outputs["Color"], mix_vein.inputs["Color2"])

    # Wrap in the leaf shader nodegroup
    grp = nt.nodes.new("ShaderNodeGroup")
    grp.node_tree = leaf_shader_group
    link(mix_vein.outputs["Color"], grp.inputs["Color"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    link(grp.outputs["Shader"], out.inputs["Surface"])

    # Banana leaves are thin blades — make the shader two-sided so the
    # translucent contribution is visible from both faces.
    mat.use_backface_culling = False
    return mat


# ══════════════════════════════════════════════════════════════════════════════
# Phase 1 — Material sampling on raw SEED
# ══════════════════════════════════════════════════════════════════════════════

MAT_LEAF = make_leaf_material(SEED, "LeafBananaTree_Material")
MAT_LEAF.use_fake_user = True

# LeafBananaTreeFactory does NOT go through wear_tear (natural foliage).


# ══════════════════════════════════════════════════════════════════════════════
# Geometry — copied verbatim from objects_blender/tropic_plants/LeafBananaTreeFactory.py
# ══════════════════════════════════════════════════════════════════════════════

random.seed(SEED)
np.random.seed(SEED)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):    bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):   bpy.data.curves.remove(c)
    # Do NOT remove node_groups — that would wipe the material's leaf shader group.
    bpy.context.scene.cursor.location = (0, 0, 0)


def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def catmull_rom_eval(ctrl_pts, x):
    """Smooth Catmull-Rom spline through control points.
    ctrl_pts: sorted list of (t, value) tuples.
    Much smoother than piecewise-linear; matches Blender FloatCurve AUTO handles.
    """

    if x <= ctrl_pts[0][0]:  return ctrl_pts[0][1]
    if x >= ctrl_pts[-1][0]: return ctrl_pts[-1][1]

    ts = [p[0] for p in ctrl_pts]
    vs = [p[1] for p in ctrl_pts]
    # Ghost points for zero-derivative boundary condition
    vs_ext = [2*vs[0] - vs[1]] + list(vs) + [2*vs[-1] - vs[-2]]

    seg = 0
    for i in range(len(ts) - 1):
        if ts[i] <= x < ts[i + 1]:
            seg = i
            break
    if x == ts[-1]:
        seg = len(ts) - 2

    dt = ts[seg + 1] - ts[seg]
    if dt < 1e-10:
        return vs[seg]
    u  = (x - ts[seg]) / dt
    u2, u3 = u*u, u*u*u

    p0, p1, p2, p3 = vs_ext[seg], vs_ext[seg+1], vs_ext[seg+2], vs_ext[seg+3]
    return 0.5 * ((2*p1) + (-p0+p2)*u + (2*p0-5*p1+4*p2-p3)*u2
                             + (-p0+3*p1-3*p2+p3)*u3)


def sample_params(rng):
    """Sample leaf parameters matching LeafBananaTreeFactory.update_params."""


    mode = rng.choice(["oval", "pear"])
    if mode == "oval":
        contour_pts = [0.13, 0.275, 0.35, 0.365, 0.32, 0.21]
    else:
        contour_pts = [0.30, 0.46, 0.46, 0.43, 0.37, 0.23]

    leaf_width = float(rng.uniform(0.5, 0.85))

    h_mode = rng.choice(["flat", "w", "s"], p=[0.4, 0.3, 0.3])
    if h_mode == "flat":
        h_wave_pts = [float(rng.normal(0.0, 0.03)) for _ in range(5)]
    elif h_mode == "s":
        h_wave_pts = [
            -0.10 + float(rng.normal(0, 0.02)),
             0.00 + float(rng.normal(0, 0.02)),
             0.08 + float(rng.normal(0, 0.02)),
             0.00 + float(rng.normal(0, 0.02)),
            -0.05 + float(rng.normal(0, 0.01)),
        ]
    else:  # w
        h_wave_pts = [
            -0.08 + float(rng.normal(0, 0.02)),
             0.07 + float(rng.normal(0, 0.02)),
            -0.08 + float(rng.normal(0, 0.02)),
             0.08 + float(rng.normal(0, 0.02)),
            -0.05 + float(rng.normal(0, 0.02)),
        ]
    h_wave_scale = float(rng.uniform(0.02, 0.2))

    w_mode = rng.choice(["fold", "wing"], p=[0.2, 0.8])
    if w_mode == "fold":
        w_wave_pts = [
            -0.28 + float(rng.normal(0, 0.02)),
            -0.20 + float(rng.normal(0, 0.02)),
            -0.13 + float(rng.normal(0, 0.01)),
            -0.06 + float(rng.normal(0, 0.01)),
        ]
        w_wave_scale = float(rng.uniform(0.1, 0.3))
    else:  # wing
        w_wave_pts = [
             0.00 + float(rng.normal(0, 0.02)),
             0.06 + float(rng.normal(0, 0.02)),
             0.07 + float(rng.normal(0, 0.01)),
             0.04 + float(rng.normal(0, 0.01)),
        ]
        w_wave_scale = float(rng.uniform(0.0, 0.3))

    leaf_x_curvature = float(rng.uniform(0.0, 0.1))

    return {
        "contour_pts":      contour_pts,
        "leaf_width":       leaf_width,
        "h_wave_pts":       h_wave_pts,
        "h_wave_scale":     h_wave_scale,
        "w_wave_pts":       w_wave_pts,
        "w_wave_scale":     w_wave_scale,
        "leaf_x_curvature": leaf_x_curvature,
    }


def build_leaf_blade(rng, params):
    contour_pts      = params["contour_pts"]
    leaf_width       = params["leaf_width"]
    h_wave_pts       = params["h_wave_pts"]
    h_wave_scale     = params["h_wave_scale"]
    w_wave_pts       = params["w_wave_pts"]
    w_wave_scale     = params["w_wave_scale"]
    leaf_x_curvature = params["leaf_x_curvature"]

    BLADE_HALF = 0.6
    ny = 160
    nx = 80

    Y_rows = np.linspace(-BLADE_HALF, BLADE_HALF, ny + 1)
    t_rows = np.linspace(0.0, 1.0,          ny + 1)

    contour_ctrl = [
        (0.00, 0.0),
        (0.10, contour_pts[0]),
        (0.25, contour_pts[1]),
        (0.40, contour_pts[2]),
        (0.55, contour_pts[3]),
        (0.70, contour_pts[4]),
        (0.85, contour_pts[5]),
        (1.00, 0.0),
    ]
    hw_rows  = np.array([catmull_rom_eval(contour_ctrl, t) * leaf_width for t in t_rows])
    hw_rows  = np.maximum(hw_rows, 0.0)
    max_hw   = float(np.max(hw_rows))
    if max_hw < 1e-6: max_hw = 1.0

    h_ctrl = [(0.0, 0.5)] + [((i+1) * 0.2, h_wave_pts[i] + 0.5) for i in range(5)]

    def wn(): return float(rng.normal(0.0, 0.02))
    w_ctrl = [
        (0.00, w_wave_pts[0] + 0.5 + wn()),
        (0.10, w_wave_pts[1] + 0.5 + wn()),
        (0.25, w_wave_pts[2] + 0.5 + wn()),
        (0.40, w_wave_pts[3] + 0.5 + wn()),
        (0.50, 0.5),
        (0.60, w_wave_pts[3] + 0.5 + wn()),
        (0.75, w_wave_pts[2] + 0.5 + wn()),
        (0.90, w_wave_pts[1] + 0.5 + wn()),
        (1.00, w_wave_pts[0] + 0.5 + wn()),
    ]

    TIP_THRESH = max_hw * 0.04

    bm = bmesh.new()
    verts_by_row = []

    for i in range(ny + 1):
        Y = float(Y_rows[i])
        t = float(t_rows[i])
        hw = float(hw_rows[i])

        h_raw = catmull_rom_eval(h_ctrl, t)
        z_h   = (h_raw - 0.5) * 2.0 * h_wave_scale

        if hw < TIP_THRESH:
            verts_by_row.append([bm.verts.new((0.0, Y, z_h))])
        else:
            row = []
            for j in range(2 * nx + 1):
                u   = (j / nx) - 1.0
                X   = u * hw
                w_t = max(0.0, min(1.0, (-X + max_hw) / (2.0 * max_hw)))
                w_raw = catmull_rom_eval(w_ctrl, w_t)
                z_w   = (w_raw - 0.5) * 2.0 * w_wave_scale
                row.append(bm.verts.new((X, Y, z_h + z_w)))
            verts_by_row.append(row)

    for i in range(ny):
        ra = verts_by_row[i]
        rb = verts_by_row[i + 1]

        if len(ra) == 1 and len(rb) == 1:
            pass
        elif len(ra) == 1:
            vt = ra[0]
            for j in range(len(rb) - 1):
                bm.faces.new([vt, rb[j], rb[j + 1]])
        elif len(rb) == 1:
            vt = rb[0]
            for j in range(len(ra) - 1):
                bm.faces.new([ra[j], ra[j + 1], vt])
        else:
            for j in range(len(ra) - 1):
                bm.faces.new([ra[j], ra[j+1], rb[j+1], rb[j]])

    mesh = bpy.data.meshes.new("leaf_blade")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("leaf_blade", mesh)
    bpy.context.scene.collection.objects.link(obj)

    for v in obj.data.vertices:
        v.co.y += BLADE_HALF

    to_max = -leaf_x_curvature
    for v in obj.data.vertices:
        Yv, Zv = v.co.y, v.co.z
        a      = Yv * to_max
        v.co.y = Yv * math.cos(a) - Zv * math.sin(a)
        v.co.z = Yv * math.sin(a) + Zv * math.cos(a)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

    apply_tf(obj)
    return obj


def main():
    rng = np.random.default_rng(SEED)
    np.random.seed(SEED)
    clear_scene()

    params = sample_params(rng)
    leaf   = build_leaf_blade(rng, params)
    leaf.name = "LeafBananaTreeFactory"

    # Attach the textured leaf material
    leaf.data.materials.clear()
    leaf.data.materials.append(MAT_LEAF)

    print(f"LeafBananaTreeFactory built: {len(leaf.data.vertices)} verts, "
          f"{len(leaf.data.polygons)} faces, "
          f"{len(leaf.data.materials)} material slots")


if __name__ == "__main__":
    main()
