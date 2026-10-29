# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafPalmPlantFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafPalmPlantFactory | Category: factories_geo
# Prompt: A 3D model of a single fan palm leaf rendered from a slightly elevated perspective. The leaf features a broad, palmate blade with narrow radiating segments spreading from a central point, mounted on a thin upright petiole stem.

"""
LeafPalmPlantFactory (textured) — geometry copied verbatim from
objects_blender/tropic_plants/LeafPalmPlantFactory.py, materials hand-crafted
(shader_leaf_material + shader_stem_material + nodegroup_nodegroup_leaf_shader).

Natural object — no wear_tear.

Two materials:
  MAT_LEAF  : palm leaf shader (HSV-driven blade colour + noise variation,
              diffuse/glossy/translucent mix replicating nodegroup_leaf_shader)
  MAT_STEM  : simple principled BSDF with HSV stem colour
"""


import os
SEED = int(os.environ.get("SEED", "0"))

import math
import random
import colorsys
import bmesh
import bpy
import numpy as np


# ── material helpers ─────────────────────────────────────────────────────────

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


def _fac(node):
    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]


def _set_specular(bsdf, value):
    key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[key].default_value = float(value)


# ── shader: palm leaf ────────────────────────────────────────────────────────
# Port of shader_leaf_material; vertex attributes replaced by procedural noise.

def make_leaf_material(name="LeafPalm_Leaf"):
    # Mirrors the numpy.random consumption order of shader_leaf_material.
    main_leaf_hsv = (float(np.random.uniform(0.30, 0.36)),
                     float(np.random.uniform(0.60, 0.70)),
                     float(np.random.uniform(0.20, 0.30)))
    hue_jitter = float(np.random.normal(0.0, 0.005))
    main_leaf_hsv_2 = ((main_leaf_hsv[0] + hue_jitter) % 1.0,
                       main_leaf_hsv[1], main_leaf_hsv[2])
    stem_color_hsv = (main_leaf_hsv[0], main_leaf_hsv[1],
                      max(0.0, main_leaf_hsv[2] - float(np.random.uniform(0.05, 0.15))))

    base_color_a = _hsv2rgba(*main_leaf_hsv)
    base_color_b = _hsv2rgba(*main_leaf_hsv_2)
    vein_color   = _hsv2rgba(*stem_color_hsv)

    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new

    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Primary noise ≈ subvein offset attribute: drives base↔variant blend (mix).
    noise_subvein = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Object"], noise_subvein.inputs["Vector"])
    noise_subvein.inputs["Scale"].default_value = 6.8
    noise_subvein.inputs["Detail"].default_value = 10.0
    noise_subvein.inputs["Roughness"].default_value = 0.7

    # Secondary noise ≈ "vein" attribute: drives stem-colour vein mask.
    noise_vein = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Object"], noise_vein.inputs["Vector"])
    noise_vein.inputs["Scale"].default_value = 18.0
    noise_vein.inputs["Detail"].default_value = 6.0
    noise_vein.inputs["Roughness"].default_value = 0.55

    # MapRange: G  -> Hue in [0.48, 0.52]
    # ShaderNodeSeparateRGB was removed in Blender 4.x+ -> use SeparateColor (RGB mode).
    sep_sub = nt.nodes.new("ShaderNodeSeparateColor")
    try:
        sep_sub.mode = "RGB"
    except Exception:
        pass
    ln(noise_subvein.outputs["Color"], sep_sub.inputs["Color"])

    mr_hue = nt.nodes.new("ShaderNodeMapRange")
    mr_hue.inputs["From Min"].default_value = 0.4
    mr_hue.inputs["From Max"].default_value = 0.7
    mr_hue.inputs["To Min"].default_value = 0.48
    mr_hue.inputs["To Max"].default_value = 0.52
    # SeparateColor outputs: "Red"/"Green"/"Blue" in 4.x+ (RGB mode).
    ln(sep_sub.outputs[1], mr_hue.inputs["Value"])

    # MapRange: B  -> Value in [0.8, 1.2]
    mr_val = nt.nodes.new("ShaderNodeMapRange")
    mr_val.inputs["From Min"].default_value = 0.4
    mr_val.inputs["From Max"].default_value = 0.7
    mr_val.inputs["To Min"].default_value = 0.8
    mr_val.inputs["To Max"].default_value = 1.2
    ln(sep_sub.outputs[2], mr_val.inputs["Value"])

    # MapRange on "subvein offset": 0..1 -> 0..-0.94  (fac for base mix)
    mr_subvein = nt.nodes.new("ShaderNodeMapRange")
    mr_subvein.inputs["From Min"].default_value = 0.0
    mr_subvein.inputs["From Max"].default_value = 1.0
    mr_subvein.inputs["To Min"].default_value = 0.0
    mr_subvein.inputs["To Max"].default_value = -0.94
    ln(_fac(noise_subvein), mr_subvein.inputs["Value"])

    # HSV node #1: value = 2.0, color = base_color_a
    hsv_boost = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_boost.inputs["Value"].default_value = 2.0
    hsv_boost.inputs["Color"].default_value = base_color_a

    # Mix base_a (via hsv_boost) with base_b using (subvein-0.94) as fac
    mix_bases = nt.nodes.new("ShaderNodeMixRGB")
    ln(mr_subvein.outputs["Result"], mix_bases.inputs["Fac"])
    ln(hsv_boost.outputs["Color"], mix_bases.inputs["Color1"])
    mix_bases.inputs["Color2"].default_value = base_color_b

    # HSV node #2: hue/value modulated by MapRange results
    hsv_mod = nt.nodes.new("ShaderNodeHueSaturation")
    ln(mr_hue.outputs["Result"], hsv_mod.inputs["Hue"])
    ln(mr_val.outputs["Result"], hsv_mod.inputs["Value"])
    ln(mix_bases.outputs["Color"], hsv_mod.inputs["Color"])

    # Vein mix: use noise_vein (≈ "vein" attribute) as fac between stem and leaf
    mix_vein = nt.nodes.new("ShaderNodeMixRGB")
    ln(_fac(noise_vein), mix_vein.inputs["Fac"])
    mix_vein.inputs["Color1"].default_value = vein_color
    ln(hsv_mod.outputs["Color"], mix_vein.inputs["Color2"])

    # nodegroup_nodegroup_leaf_shader: Diffuse + 20% Glossy(0.3) + 30% Translucent
    diffuse = nt.nodes.new("ShaderNodeBsdfDiffuse")
    ln(mix_vein.outputs["Color"], diffuse.inputs["Color"])

    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Roughness"].default_value = 0.3
    ln(mix_vein.outputs["Color"], glossy.inputs["Color"])

    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    ln(mix_vein.outputs["Color"], translucent.inputs["Color"])

    mix_shader_a = nt.nodes.new("ShaderNodeMixShader")
    mix_shader_a.inputs["Fac"].default_value = 0.2
    ln(diffuse.outputs["BSDF"], mix_shader_a.inputs[1])
    ln(glossy.outputs["BSDF"], mix_shader_a.inputs[2])

    mix_shader_b = nt.nodes.new("ShaderNodeMixShader")
    mix_shader_b.inputs["Fac"].default_value = 0.3
    ln(mix_shader_a.outputs["Shader"], mix_shader_b.inputs[1])
    ln(translucent.outputs["BSDF"], mix_shader_b.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_shader_b.outputs["Shader"], out.inputs["Surface"])
    return mat


# ── shader: stem ─────────────────────────────────────────────────────────────

def make_stem_material(name="LeafPalm_Stem"):
    stem_hsv = (float(np.random.uniform(0.25, 0.32)),
                float(np.random.uniform(0.60, 0.90)),
                float(np.random.uniform(0.20, 0.60)))
    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = _hsv2rgba(*stem_hsv)
    bsdf.inputs["Roughness"].default_value = 0.7
    _set_specular(bsdf, 0.1)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


seed_all(SEED)
MAT_LEAF = make_leaf_material("LeafPalmPlantFactory_Leaf")
MAT_LEAF.use_fake_user = True
MAT_STEM = make_stem_material("LeafPalmPlantFactory_Stem")
MAT_STEM.use_fake_user = True

# Natural asset: no wear_tear gates.


# Geometry (verbatim from objects_blender; only material.append calls added)
random.seed(SEED); np.random.seed(SEED)


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

# ── parameters ────────────────────────────────────────────────────────────────

def sample_params(rng):
    h_mode = rng.choice(["flat", "s"], p=[0.7, 0.3])
    if h_mode == "flat":
        h_wave_pts = [float(rng.normal(0.0, 0.03)) for _ in range(5)]
    else:
        h_wave_pts = [
            -0.5 + float(rng.normal(0.0, 0.01)),
             0.0 + float(rng.normal(0.0, 0.01)),
             0.05 + float(rng.normal(0.0, 0.01)),
             0.0 + float(rng.normal(0.0, 0.01)),
            -0.05 + float(rng.normal(0.0, 0.01)),
        ]
    return {
        "h_wave_pts":       h_wave_pts,
        "h_wave_scale":     float(rng.uniform(0.01, 0.15)),
        "leaf_x_curvature": float(rng.uniform(0.0, 0.5)),
        "leaf_width_scale": float(rng.uniform(0.15, 0.20)),
        "n_resolution":     int(rng.integers(24, 34)),
        "leaf_scale":       float(rng.uniform(0.85, 1.25)),
        "stem_length":      float(rng.uniform(1.5, 2.2)),
        "stem_x_curv":      float(rng.uniform(-0.1, 0.4)),
        "stem_y_curv":      float(rng.uniform(-0.15, 0.15)),
        "plant_z_rotate":   float(rng.uniform(-0.4, 0.4)),
        "plant_scale":      float(rng.uniform(0.8, 1.3)),
    }

# ── stem ──────────────────────────────────────────────────────────────────────

def build_stem(rng, params):
    """Curved stem tube via cumulative arc integration.
    Returns (obj, tip_pos, tip_tangent, tip_radius).
    tip_pos is the exact centrepoint of the top ring.
    """

    stem_length = params["stem_length"]
    stem_x_curv = params["stem_x_curv"]
    stem_y_curv = params["stem_y_curv"]
    stem_radius  = float(rng.uniform(0.03, 0.06))

    n_segs   = 40
    n_sides  = 8
    step_len = stem_length / n_segs

    dx = stem_x_curv / n_segs
    dy = stem_y_curv / n_segs

    pos       = np.zeros(3)
    direction = np.array([0.0, 0.0, 1.0])
    centerline = [pos.copy()]
    tangents   = [direction.copy()]

    for _ in range(n_segs):
        cy, sy = math.cos(dx), math.sin(dx)
        d = direction.copy()
        direction = np.array([d[0], d[1]*cy - d[2]*sy, d[1]*sy + d[2]*cy])
        cz, sz = math.cos(dy), math.sin(dy)
        d = direction.copy()
        direction = np.array([d[0]*cz + d[2]*sz, d[1], -d[0]*sz + d[2]*cz])
        direction /= np.linalg.norm(direction)
        pos = pos + direction * step_len
        centerline.append(pos.copy())
        tangents.append(direction.copy())

    bm = bmesh.new()
    rings = []
    n_tube_rings = n_segs - 6
    for i in range(n_tube_rings + 1):
        c, tang = centerline[i], tangents[i]
        t    = i / n_segs
        t_s  = t*t*(3 - 2*t)
        r    = stem_radius * (0.8 - 0.4*t_s)
        if t > 0.55:
            alpha = (1.0 - t) / 0.45
            r *= alpha * alpha * alpha

        ref  = np.array([0.0, 1.0, 0.0]) if abs(tang[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        rght = np.cross(tang, ref); rght /= np.linalg.norm(rght)
        fwd  = np.cross(tang, rght)

        ring = []
        for j in range(n_sides):
            a      = 2*math.pi*j/n_sides
            offset = r*(math.cos(a)*rght + math.sin(a)*fwd)
            ring.append(bm.verts.new(tuple(c + offset)))
        rings.append(ring)

    for i in range(n_tube_rings):
        for j in range(n_sides):
            j2 = (j+1) % n_sides
            bm.faces.new([rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]])

    bot = bm.verts.new(tuple(centerline[0]))
    for j in range(n_sides):
        bm.faces.new([bot, rings[0][(j+1) % n_sides], rings[0][j]])

    mesh = bpy.data.meshes.new("stem")
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new("stem", mesh)
    bpy.context.scene.collection.objects.link(obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    apply_tf(obj)

    tip_r = stem_radius * (0.8 - 0.4 * 1.0)
    return obj, centerline[-1], tangents[-1], tip_r

# ── palm fan ──────────────────────────────────────────────────────────────────

def build_fan(rng, params, r_fan=0.04):
    h_wave_pts       = params["h_wave_pts"]
    h_wave_scale     = params["h_wave_scale"]
    leaf_x_curvature = params["leaf_x_curvature"]
    leaf_width_scale = params["leaf_width_scale"]
    n_resolution     = params["n_resolution"]
    leaf_scale       = params["leaf_scale"]

    n_leaves     = n_resolution // 2 - 1
    angular_step = 2.0 * math.pi / n_resolution

    BLADE_LEN = 1.2
    ny = 60
    nx = 14

    t_rows = np.linspace(0.0, 1.0, ny + 1)

    contour_ctrl = [
        (0.00, 0.0),
        (0.10, 0.08),
        (0.25, 0.24),
        (0.40, 0.34),
        (0.55, 0.3625),
        (0.70, 0.30),
        (0.85, 0.20),
        (1.00, 0.0),
    ]
    hw_rows = np.array([catmull_rom_eval(contour_ctrl, t) * leaf_width_scale
                        for t in t_rows])
    hw_rows = np.maximum(hw_rows, 0.0)
    max_hw  = float(np.max(hw_rows))
    if max_hw < 1e-6: max_hw = 1.0

    h_ctrl = [(0.0, 0.5)] + [((i+1)*0.2, h_wave_pts[i] + 0.5) for i in range(5)]
    z_h_base = np.array([(catmull_rom_eval(h_ctrl, t) - 0.5)*2.0*h_wave_scale
                          for t in t_rows])

    TIP_THRESH = max_hw * 0.04
    to_max = leaf_x_curvature

    fy_ctrl  = [(0.0, 0.0), (0.5182, 1.0), (1.0, 1.0)]
    fy_rows  = np.array([catmull_rom_eval(fy_ctrl, t) for t in t_rows])
    fc_x_ctrl = [(0.0045, 0.0063), (0.0409, 0.0375), (0.4182, 0.05), (1.0, 0.0)]

    bm = bmesh.new()

    for li in range(n_leaves):
        theta = (li + 1) * angular_step

        leaf_y = np.array([ math.cos(theta), 0.0, -math.sin(theta)])
        leaf_x = np.array([ math.sin(theta), 0.0,  math.cos(theta)])
        leaf_z = np.array([0.0,              1.0,  0.0             ])

        fan_offset = np.array([-r_fan * math.cos(theta), 0.0, r_fan * math.sin(theta)])

        scale = float(rng.uniform(0.9, 1.1)) * leaf_scale

        verts_by_row = []
        for i in range(ny + 1):
            t   = float(t_rows[i])
            hw  = float(hw_rows[i]) * scale
            z_h = float(z_h_base[i]) * scale
            Y_l = t * BLADE_LEN * scale

            a     = Y_l * to_max
            cos_a = math.cos(a); sin_a = math.sin(a)
            new_Y = Y_l * cos_a - z_h * sin_a
            new_Z = Y_l * sin_a + z_h * cos_a

            fy = float(fy_rows[i]) * scale

            if hw < TIP_THRESH:
                wp = fan_offset + new_Y * leaf_y + new_Z * leaf_z
                verts_by_row.append([bm.verts.new(tuple(wp))])
            else:
                row = []
                for j in range(2*nx + 1):
                    u   = (j / nx) - 1.0
                    Xl  = u * hw
                    s_dome = hw * (1.0 - abs(u))
                    z_inner = 0.7 * fy * catmull_rom_eval(fc_x_ctrl, s_dome)
                    wp = fan_offset + Xl * leaf_x + new_Y * leaf_y + (new_Z + z_inner) * leaf_z
                    row.append(bm.verts.new(tuple(wp)))
                verts_by_row.append(row)

        for i in range(ny):
            ra, rb = verts_by_row[i], verts_by_row[i+1]
            if len(ra) == 1 and len(rb) == 1:
                pass
            elif len(ra) == 1:
                vt = ra[0]
                for j in range(len(rb)-1):
                    bm.faces.new([vt, rb[j], rb[j+1]])
            elif len(rb) == 1:
                vt = rb[0]
                for j in range(len(ra)-1):
                    bm.faces.new([ra[j], ra[j+1], vt])
            else:
                for j in range(len(ra)-1):
                    bm.faces.new([ra[j], ra[j+1], rb[j+1], rb[j]])

    mesh = bpy.data.meshes.new("fan")
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new("fan", mesh)
    bpy.context.scene.collection.objects.link(obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    apply_tf(obj)
    return obj

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    rng = np.random.default_rng(SEED)
    np.random.seed(SEED)
    clear_scene()

    params = sample_params(rng)

    stem, tip_pos, tip_tangent, tip_r = build_stem(rng, params)
    fan = build_fan(rng, params)

    fan_origin = tip_pos + tip_tangent * 0.04
    fan.location = tuple(fan_origin)
    apply_tf(fan)

    # Per-part material assignment BEFORE join (spec rule).
    stem.data.materials.clear()
    stem.data.materials.append(MAT_STEM)
    fan.data.materials.clear()
    fan.data.materials.append(MAT_LEAF)

    result = join_objs([stem, fan])
    result.rotation_euler.x = params["leaf_x_curvature"]
    result.rotation_euler.z = params["plant_z_rotate"]
    s = params["plant_scale"]
    result.scale = (s, s, s)
    apply_tf(result)
    result.name = "LeafPalmPlantFactory"

    return result

if __name__ == "__main__":
    main()
