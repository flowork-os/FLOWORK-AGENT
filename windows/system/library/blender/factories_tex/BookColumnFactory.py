# [FL_INDEX: keywords="blender_factory, procedural_3d, BookColumnFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BookColumnFactory | Category: factories_tex
# Prompt: A 3D model of a vertical column of books standing upright and leaning against each other, rendered from a slightly elevated three-quarter perspective. The book column features multiple books of varying heights and thicknesses arranged side by side in an upright position, with visible front covers, spines, and page edges forming a compact row.

"""BookColumnFactory -- standalone Blender script with materials.

Geometry: copied from objects_blender/table_decorations/BookColumnFactory.py
Materials:
    Uses Voronoi + Noise + ColorRamp to create varied abstract book-cover designs.
Wear & tear:
"""


import os
import random
import colorsys
import math

import bmesh
import bpy
import numpy as np

# ── Seed ──────────────────────────────────────────────────────────────────────

SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)
random.seed(SEED)

# ── Helpers ───────────────────────────────────────────────────────────────────

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def hsv2rgba(h, s, v):
    h = h - math.floor(h)
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, min(1.0, float(v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

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

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_tf(obj, loc=False):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

# --- Material helpers ---

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
        "Transmission Weight": ("Transmission Weight", "Transmission"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

def _noise_fac(node):
    if "Fac" in node.outputs:
        return node.outputs["Fac"]
    if "Factor" in node.outputs:
        return node.outputs["Factor"]
    return node.outputs[0]

def _color_ramp(nt, fac_socket, stops):
    cr = nt.nodes.new("ShaderNodeValToRGB")
    for i, (pos, color) in enumerate(stops):
        if i < 2:
            cr.color_ramp.elements[i].position = pos
            cr.color_ramp.elements[i].color = color
        else:
            elem = cr.color_ramp.elements.new(pos)
            elem.color = color
    nt.links.new(fac_socket, cr.inputs["Fac"])
    return cr

def _noise_tex(nt, vector_socket, scale_socket=None, scale_val=None, detail=5.0):
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Detail"].default_value = detail
    if scale_socket is not None:
        nt.links.new(scale_socket, noise.inputs["Scale"])
    elif scale_val is not None:
        noise.inputs["Scale"].default_value = scale_val
    if vector_socket is not None:
        nt.links.new(vector_socket, noise.inputs["Vector"])
    return noise

def _value_node(nt, val):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = val
    return n

def _math(nt, op, a, b=None, clamp=False):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    if clamp:
        m.use_clamp = True
    if isinstance(a, bpy.types.NodeSocket):
        nt.links.new(a, m.inputs[0])
    elif a is not None:
        m.inputs[0].default_value = a
    if isinstance(b, bpy.types.NodeSocket):
        nt.links.new(b, m.inputs[1])
    elif b is not None:
        m.inputs[1].default_value = b
    return m

def _vmath(nt, op, a=None, b=None, in0=None, scale=None):
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = op
    if a is not None and isinstance(a, bpy.types.NodeSocket):
        nt.links.new(a, vm.inputs[0])
    if b is not None and isinstance(b, bpy.types.NodeSocket):
        nt.links.new(b, vm.inputs[1])
    if in0 is not None and isinstance(in0, bpy.types.NodeSocket):
        nt.links.new(in0, vm.inputs[0])
    if scale is not None:
        vm.inputs["Scale"].default_value = scale
    return vm

def _find_node(nt, bl_idname):
    for n in nt.nodes:
        if n.bl_idname == bl_idname:
            return n
    return None

# --- Paper material (plaster) ---

def make_paper_material(seed, name="PaperMaterial"):
    _s = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s)
    random.seed(_s)

    plaster_colored = np.random.uniform() < 0.4
    hue = float(np.random.uniform(0, 1))
    front_value = log_uniform(0.5, 1.0)
    back_value = front_value * float(np.random.uniform(0.6, 1))
    if plaster_colored:
        front_color = hsv2rgba(hue, float(np.random.uniform(0.3, 0.5)), front_value)
        back_color = hsv2rgba(
            hue + float(np.random.uniform(-0.1, 0.1)),
            float(np.random.uniform(0.3, 0.5)),
            back_value,
        )
    else:
        front_color = hsv2rgba(hue, 0, front_value)
        back_color = hsv2rgba(hue + float(np.random.uniform(-0.1, 0.1)), 0, back_value)

    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new

    # UV Map
    uv = nt.nodes.new("ShaderNodeUVMap")

    # Musgrave-like texture (use Noise with high detail as substitute in Blender 5.0)
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Detail"].default_value = log_uniform(15, 30)
    musgrave.inputs["Roughness"].default_value = 0.0
    musgrave.inputs["Scale"].default_value = 5.0
    ln(uv.outputs["UV"], musgrave.inputs["Vector"])

    # Noise texture
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Detail"].default_value = log_uniform(15, 30)
    noise.inputs["Distortion"].default_value = log_uniform(4, 8)
    noise.inputs["Scale"].default_value = 5.0
    ln(uv.outputs["UV"], noise.inputs["Vector"])

    # ColorRamp on noise
    mid_pos = float(np.random.uniform(0.3, 0.5))
    noise_ramp = _color_ramp(nt, _noise_fac(noise),
                             [(0.0, (0, 0, 0, 1)), (mid_pos, (1, 1, 1, 1))])

    # Mix (DIFFERENCE)
    mix_diff = nt.nodes.new("ShaderNodeMix")
    mix_diff.data_type = "RGBA"
    try:
        mix_diff.blend_type = "DARKEN"
    except Exception:
        pass
    mix_diff.inputs[0].default_value = 1.0
    ln(_noise_fac(musgrave), mix_diff.inputs[6])
    ln(noise_ramp.outputs["Color"], mix_diff.inputs[7])

    # ColorRamp for base color
    low_pos = float(np.random.uniform(0.2, 0.3))
    base_ramp = _color_ramp(nt, mix_diff.outputs[2],
                            [(low_pos, back_color), (1.0, front_color)])

    # Displacement
    disp_musgrave = nt.nodes.new("ShaderNodeTexNoise")
    disp_musgrave.inputs["Scale"].default_value = float(np.random.uniform(1e3, 2e3))
    disp_musgrave.inputs["Detail"].default_value = 5.0

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Scale"].default_value = log_uniform(0.0001, 0.0003)
    disp.inputs["Midlevel"].default_value = 0.0
    ln(_noise_fac(disp_musgrave), disp.inputs["Height"])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(base_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.7, 0.8))

    # Output
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    ln(disp.outputs["Displacement"], out.inputs["Displacement"])

    return mat

# --- Cover material (text/art book cover) ---

def make_cover_material(seed, name="CoverMaterial"):
    _s = ((seed + 2) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s)
    random.seed(_s)

    # Pick two contrasting colors
    hue1 = float(np.random.uniform(0, 1))
    hue2 = (hue1 + float(np.random.uniform(0.15, 0.5))) % 1.0
    sat1 = float(np.random.uniform(0.3, 0.8))
    sat2 = float(np.random.uniform(0.3, 0.8))
    val1 = float(np.random.uniform(0.3, 0.8))
    val2 = float(np.random.uniform(0.3, 0.8))
    color1 = hsv2rgba(hue1, sat1, val1)
    color2 = hsv2rgba(hue2, sat2, val2)

    # Background color
    bg_hue = float(np.random.uniform(0, 1))
    bg_val = float(np.random.uniform(0.1, 0.9))
    bg_sat = float(np.random.uniform(0.0, 0.6))
    bg_color = hsv2rgba(bg_hue, bg_sat, bg_val)

    pattern = np.random.choice(["voronoi_mix", "stripes", "noise_blocks"])

    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new

    # Texture coordinates (Object-based for consistency across faces)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    ln(tc.outputs["Object"], mapping.inputs["Vector"])

    if pattern == "voronoi_mix":
        # Voronoi + Noise mix for abstract art-like cover
        voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
        voronoi.inputs["Scale"].default_value = float(np.random.uniform(3, 12))
        ln(mapping.outputs["Vector"], voronoi.inputs["Vector"])

        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = float(np.random.uniform(5, 20))
        noise.inputs["Detail"].default_value = float(np.random.uniform(3, 8))
        noise.inputs["Distortion"].default_value = float(np.random.uniform(0, 3))
        ln(mapping.outputs["Vector"], noise.inputs["Vector"])

        # Mix voronoi distance with noise
        mix_factor = nt.nodes.new("ShaderNodeMix")
        mix_factor.data_type = "FLOAT"
        mix_factor.inputs[0].default_value = float(np.random.uniform(0.3, 0.7))
        vor_dist = voronoi.outputs.get("Distance") or voronoi.outputs[0]
        ln(vor_dist, mix_factor.inputs[2])
        ln(_noise_fac(noise), mix_factor.inputs[3])

        ramp = _color_ramp(nt, mix_factor.outputs[0],
                           [(0.0, bg_color),
                            (float(np.random.uniform(0.3, 0.5)), color1),
                            (1.0, color2)])
        color_out = ramp.outputs["Color"]

    elif pattern == "stripes":
        # Stripe pattern with noise distortion
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ln(mapping.outputs["Vector"], sep.inputs[0])

        stripe_axis = int(np.random.choice([0, 1]))
        scale_val = float(np.random.uniform(4, 15))

        mul = _math(nt, "MULTIPLY", sep.outputs[stripe_axis], scale_val)
        sine = _math(nt, "SINE", mul.outputs[0])

        # Add noise distortion
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = float(np.random.uniform(8, 25))
        noise.inputs["Detail"].default_value = 4.0
        ln(mapping.outputs["Vector"], noise.inputs["Vector"])

        add = _math(nt, "ADD", sine.outputs[0], _noise_fac(noise))

        ramp = _color_ramp(nt, add.outputs[0],
                           [(0.0, color1),
                            (0.5, bg_color),
                            (1.0, color2)])
        ramp.color_ramp.interpolation = "EASE"
        color_out = ramp.outputs["Color"]

    else:  # noise_blocks
        # Block pattern using Brick texture
        brick = nt.nodes.new("ShaderNodeTexBrick")
        brick.inputs["Scale"].default_value = float(np.random.uniform(3, 10))
        brick.inputs["Color1"].default_value = color1
        brick.inputs["Color2"].default_value = color2
        brick.inputs["Mortar"].default_value = bg_color
        brick.inputs["Mortar Size"].default_value = float(np.random.uniform(0.01, 0.05))
        ln(mapping.outputs["Vector"], brick.inputs["Vector"])

        # Mix with noise for variation
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = float(np.random.uniform(10, 30))
        noise.inputs["Detail"].default_value = 5.0
        ln(mapping.outputs["Vector"], noise.inputs["Vector"])

        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs[0].default_value = float(np.random.uniform(0.05, 0.2))
        ln(brick.outputs["Color"], mix.inputs[6])
        ln(noise.outputs["Color"], mix.inputs[7])
        color_out = mix.outputs[2]

    # Subtle roughness variation
    rough_noise = nt.nodes.new("ShaderNodeTexNoise")
    rough_noise.inputs["Scale"].default_value = 50.0
    rough_noise.inputs["Detail"].default_value = 3.0

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(color_out, bsdf.inputs["Base Color"])
    ln(_noise_fac(rough_noise), bsdf.inputs["Roughness"])
    _set_principled(bsdf,
                    Metallic=float(np.random.uniform(0, 0.3)),
                    **{"Specular IOR Level": float(np.random.uniform(0.1, 0.4))})

    # Output
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat

# --- Wear & tear ---

SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"

def get_scratch_params():
    return dict(
        angle1=float(np.random.uniform(10, 80)),
        angle2=float(np.random.uniform(-80, -10)),
        scratch_scale=log_uniform(5, 80),
        scratch_mask_ratio=log_uniform(0.01, 0.9),
        scratch_mask_noise=log_uniform(5, 40),
        scratch_depth=log_uniform(0.1, 1.0),
    )

def _build_scratch_graph(nt, params):
    ln = nt.links.new
    n_angle1 = _value_node(nt, params["angle1"])
    n_angle2 = _value_node(nt, params["angle2"])
    n_scale = _value_node(nt, params["scratch_scale"])
    n_mask_ratio = _value_node(nt, params["scratch_mask_ratio"])
    n_mask_noise = _value_node(nt, params["scratch_mask_noise"])
    n_depth = _value_node(nt, params["scratch_depth"])

    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Direction 1
    comb1 = nt.nodes.new("ShaderNodeCombineXYZ")
    ln(n_angle1.outputs[0], comb1.inputs["Y"])
    map1 = nt.nodes.new("ShaderNodeMapping")
    map1.vector_type = "TEXTURE"
    map1.inputs["Scale"].default_value = (25, 1, 1)
    ln(tc.outputs["Object"], map1.inputs["Vector"])
    ln(comb1.outputs[0], map1.inputs["Rotation"])
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.inputs["Detail"].default_value = 15.0
    noise1.inputs["Roughness"].default_value = 0.0
    noise1.inputs["Distortion"].default_value = 22.8
    ln(map1.outputs["Vector"], noise1.inputs["Vector"])
    ln(n_scale.outputs[0], noise1.inputs["Scale"])

    # Direction 2
    comb2 = nt.nodes.new("ShaderNodeCombineXYZ")
    ln(n_angle2.outputs[0], comb2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    map2.vector_type = "TEXTURE"
    map2.inputs["Scale"].default_value = (25, 1, 1)
    ln(tc.outputs["Object"], map2.inputs["Vector"])
    ln(comb2.outputs[0], map2.inputs["Rotation"])
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.inputs["Detail"].default_value = 15.0
    noise2.inputs["Roughness"].default_value = 0.0
    noise2.inputs["Distortion"].default_value = 22.8
    ln(map2.outputs["Vector"], noise2.inputs["Vector"])
    ln(n_scale.outputs[0], noise2.inputs["Scale"])

    add = _math(nt, "ADD", _noise_fac(noise1), _noise_fac(noise2))

    # Mask noise
    map3 = nt.nodes.new("ShaderNodeMapping")
    map3.vector_type = "TEXTURE"
    map3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.1920)
    ln(tc.outputs["Object"], map3.inputs["Vector"])
    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    noise3.inputs["Detail"].default_value = 1.0
    ln(map3.outputs["Vector"], noise3.inputs["Vector"])
    ln(n_mask_noise.outputs[0], noise3.inputs["Scale"])

    cr = _color_ramp(nt, _noise_fac(noise3),
                     [(0.4109, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))])

    mul = _math(nt, "MULTIPLY", n_mask_ratio.outputs[0], cr.outputs["Color"])
    add2 = _math(nt, "ADD", add.outputs[0], mul.outputs[0], clamp=True)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.7
    mr.inputs["From Max"].default_value = 0.72
    mr.inputs["To Max"].default_value = 0.9
    ln(add2.outputs[0], mr.inputs["Value"])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    ln(mr.outputs["Result"], disp.inputs["Height"])
    ln(n_depth.outputs[0], disp.inputs["Scale"])

    return disp.outputs[0]

def apply_scratches(obj, **params):
    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_scratch_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == SCRATCH_LABEL for n in nt.nodes):
            continue
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        try:
            disp_out = _build_scratch_graph(nt, params)
            nt.links.new(disp_out, mat_out.inputs["Displacement"])
            disp_out.node.label = SCRATCH_LABEL
        except Exception as exc:
            print(f"  [scratches] failed on {mat.name}: {type(exc).__name__}: {exc}")

def get_edge_wear_params():
    return dict(
        worn_off_opacity=float(np.random.uniform(0, 0.01)),
        worn_off_radius=float(np.random.uniform(0.005, 0.01)),
        scratch_radius=float(np.random.uniform(0.01, 0.03)),
        worn_off_mask_randomness=float(np.random.uniform(2.5, 3.0)),
        edge_base_color_hue=float(np.random.uniform(0, 1)),
        edge_base_color_whiteness=float(np.random.uniform(0.1, 0.6)),
        scratch_mask_randomness=float(np.random.choice(
            [np.random.uniform(0.1, 5.0), np.random.uniform(1.0, 10.0)])),
        scratch_density=float(np.random.uniform(1.5, 10.0)),
        scratch_opacity=float(np.random.uniform(0.5, 1.0)),
    )

def _build_edge_wear_graph(nt, original_bsdf_node, original_disp_node, params):
    ln = nt.links.new
    p = params
    n_scratch_opacity = _value_node(nt, p["scratch_opacity"])
    n_scratch_mask_rand = _value_node(nt, p["scratch_mask_randomness"])
    n_scratch_radius = _value_node(nt, p["scratch_radius"])
    n_worn_opacity = _value_node(nt, p["worn_off_opacity"])
    n_worn_radius = _value_node(nt, p["worn_off_radius"])
    n_worn_mask_rand = _value_node(nt, p["worn_off_mask_randomness"])
    n_edge_whiteness = _value_node(nt, p["edge_base_color_whiteness"])
    n_edge_hue = _value_node(nt, p["edge_base_color_hue"])
    n_scratch_density = _value_node(nt, p["scratch_density"])

    tc = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    ln(tc.outputs["Object"], mapping.inputs["Vector"])

    noise_a = _noise_tex(nt, mapping.outputs["Vector"],
                         n_scratch_mask_rand.outputs[0], detail=1.0)
    cr_a = _color_ramp(nt, _noise_fac(noise_a),
                       [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.samples = 20
    ln(n_scratch_radius.outputs[0], bevel.inputs["Radius"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub = _vmath(nt, "SUBTRACT", bevel.outputs[0], geo.outputs["Normal"])
    abs_a = _math(nt, "ABSOLUTE", sub.outputs["Vector"])
    cr_b = _color_ramp(nt, abs_a.outputs[0],
                       [(0.0691, (0, 0, 0, 1)), (0.1564, (1, 1, 1, 1))])

    mul_a = _math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"], clamp=True)
    mul_a1 = _math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0], clamp=True)

    bevel2 = nt.nodes.new("ShaderNodeBevel")
    bevel2.samples = 20
    ln(n_worn_radius.outputs[0], bevel2.inputs["Radius"])
    sub2 = _vmath(nt, "SUBTRACT", bevel2.outputs[0], geo.outputs["Normal"])
    abs_b = _math(nt, "ABSOLUTE", sub2.outputs["Vector"])

    noise_b = _noise_tex(nt, mapping.outputs["Vector"],
                         n_worn_mask_rand.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
    cr_d = _color_ramp(nt, mul_b1.outputs[0],
                       [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])

    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    if hasattr(combine_color, "mode"):
        try:
            combine_color.mode = "HSV"
        except TypeError:
            pass
    ln(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_result"):
        try:
            mix.clamp_result = True
        except TypeError:
            pass
    if hasattr(mix, "clamp_factor"):
        try:
            mix.clamp_factor = False
        except TypeError:
            pass
    ln(n_edge_whiteness.outputs[0], mix.inputs[0])
    ln(combine_color.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

    bsdf_worn1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix.outputs[2], bsdf_worn1.inputs["Base Color"])
    _set_principled(bsdf_worn1, Metallic=0.3745, Roughness=0.1436,
                    **{"Specular IOR Level": 0.0})

    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    ln(cr_d.outputs["Color"], mix_shader.inputs["Fac"])
    ln(original_bsdf_node.outputs[0], mix_shader.inputs[1])
    ln(bsdf_worn1.outputs[0], mix_shader.inputs[2])

    map_h = nt.nodes.new("ShaderNodeMapping")
    map_h.inputs["Scale"].default_value = (10, 1, 1)
    ln(tc.outputs["Object"], map_h.inputs["Vector"])
    vor_h = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        vor_h.feature = "DISTANCE_TO_EDGE"
    except Exception:
        pass
    ln(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    ln(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1, 10, 1)
    ln(tc.outputs["Object"], map_v.inputs["Vector"])

    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        vor_v.feature = "DISTANCE_TO_EDGE"
    except Exception:
        pass
    ln(map_v.outputs["Vector"], vor_v.inputs["Vector"])
    ln(scale_v.outputs[0], vor_v.inputs["Scale"])

    dist_h = vor_h.outputs.get("Distance") or vor_h.outputs[0]
    dist_v = vor_v.outputs.get("Distance") or vor_v.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_e = _color_ramp(nt, mul_dist.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_e = _math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"], clamp=True)
    mul_f = _math(nt, "MULTIPLY", mul_a.outputs[0], mul_e.outputs[0], clamp=True)

    bsdf_worn2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix.outputs[2], bsdf_worn2.inputs["Base Color"])
    _set_principled(bsdf_worn2, Metallic=0.3855, Roughness=0.0,
                    **{"Specular IOR Level": 0.0})

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    ln(mul_a1.outputs[0], mix_shader_2.inputs["Fac"])
    ln(mix_shader.outputs[0], mix_shader_2.inputs[1])
    ln(bsdf_worn2.outputs[0], mix_shader_2.inputs[2])

    scale_disp = _vmath(nt, "SCALE", in0=mul_f.outputs[0], scale=2.0)
    if original_disp_node is None:
        total_disp = scale_disp.outputs[0]
    else:
        add_disp = _math(nt, "ADD", original_disp_node.outputs[0],
                         scale_disp.outputs[0], clamp=True)
        total_disp = add_disp.outputs[0]

    return mix_shader_2.outputs[0], total_disp

def apply_edge_wear(obj, **params):
    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_edge_wear_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == EDGE_WEAR_LABEL for n in nt.nodes):
            continue
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        surface_links = mat_out.inputs["Surface"].links
        if not surface_links:
            continue
        original_bsdf = surface_links[0].from_node
        disp_links = mat_out.inputs["Displacement"].links
        original_disp = disp_links[0].from_node if disp_links else None
        try:
            final_bsdf_socket, final_disp_socket = _build_edge_wear_graph(
                nt, original_bsdf, original_disp, params)
            nt.links.new(final_bsdf_socket, mat_out.inputs["Surface"])
            nt.links.new(final_disp_socket, mat_out.inputs["Displacement"])
            final_bsdf_socket.node.label = EDGE_WEAR_LABEL
        except Exception as exc:
            print(f"  [edge_wear] failed on {mat.name}: {type(exc).__name__}: {exc}")

# --- Material and wear-tear decisions are made inside make_book_column() ---
# --- after clear_scene() to avoid StructRNA removal. ---

# --- Geometry (from objects_blender/table_decorations/BookColumnFactory.py) ---

def make_paper(width, height, depth):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    paper = bpy.context.active_object
    paper.location = (width / 2, height / 2, depth / 2)
    paper.scale = (width / 2 - 1e-4, height / 2, depth / 2 - 1e-4)
    apply_tf(paper, loc=True)
    return paper

def make_paperback(width, height, depth, paper_mat, cover_mat):
    paper = make_paper(width, height, depth)

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.location = (width / 2, height / 2, depth / 2)
    obj.scale = (width / 2, height / 2, depth / 2)
    apply_tf(obj, loc=True)

    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(obj.data)
    geom = []
    for e in bm.edges:
        u, v = e.verts
        if u.co[0] > 0 and v.co[0] > 0 and u.co[2] != v.co[2]:
            geom.append(e)
    bmesh.ops.delete(bm, geom=geom, context="EDGES")
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Assign materials
    paper.data.materials.append(paper_mat)
    obj.data.materials.append(cover_mat)

    return join_objs([paper, obj])

def make_hardcover(width, height, depth, margin, offset, thickness, paper_mat, cover_mat):
    paper = make_paper(width, height, depth)

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    count = 8
    mod = obj.modifiers.new("ARRAY", "ARRAY")
    mod.count = count
    mod.relative_offset_displace = (0, 0, 1)
    mod.use_merge_vertices = True
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    obj.location = (1, 1, 1)
    apply_tf(obj, loc=True)

    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(obj.data)
    geom = []
    for v in bm.verts:
        if v.co[0] > 0 and 0 < v.co[2] < count * 2:
            geom.append(v)
    bmesh.ops.delete(bm, geom=geom, context="VERTS")
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    obj.location = (0, -margin, 0)
    obj.scale = ((width + margin) / 2, height / 2 + margin, depth / 2 / count)
    apply_tf(obj, loc=True)

    x, y, z = read_co(obj).T
    ratio = np.minimum(z / depth, 1 - z / depth)
    x -= 4 * ratio * (1 - ratio) * offset
    obj.data.vertices.foreach_set("co", np.stack([x, y, z]).T.reshape(-1))
    obj.data.update()

    mod = obj.modifiers.new("SOLIDIFY", "SOLIDIFY")
    mod.thickness = thickness
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Assign materials
    paper.data.materials.append(paper_mat)
    obj.data.materials.append(cover_mat)

    return join_objs([paper, obj])

def make_book(paper_mat, cover_mat):
    rel_scale = log_uniform(1, 1.5)
    skewness = log_uniform(1.3, 1.8)
    is_paperback = np.random.uniform() < 0.5
    margin = float(np.random.uniform(0.005, 0.01))
    offset = 0 if np.random.uniform() < 0.5 else log_uniform(0.002, 0.008)
    thickness = float(np.random.uniform(0.002, 0.003))

    unit = 0.0127
    width = int(log_uniform(0.08, 0.15) * rel_scale / unit) * unit
    height = int(width * skewness / unit) * unit
    depth = float(np.random.uniform(0.01, 0.02)) * rel_scale

    if is_paperback:
        return make_paperback(width, height, depth, paper_mat, cover_mat)
    else:
        return make_hardcover(width, height, depth, margin, offset, thickness, paper_mat, cover_mat)

def make_book_column():
    np.random.seed(SEED)
    random.seed(SEED)

    n_styles_local = np.random.randint(1, 4)
    style_seeds_local = [np.random.randint(0, 100000) for _ in range(n_styles_local)]

    n_books = np.random.randint(10, 20)
    max_angle = float(np.random.uniform(0, np.pi / 9)) if np.random.uniform() < 0.7 else 0

    # Create materials for each book style (after clear_scene)
    paper_mats = []
    cover_mats = []
    for i, ss in enumerate(style_seeds_local):
        paper_mats.append(make_paper_material(ss, f"PaperMaterial_{i}"))
        cover_mats.append(make_cover_material(ss, f"CoverMaterial_{i}"))

    # Wear-tear decisions
    wear_do_scratch = np.random.uniform() <= 0.5
    wear_do_edgewear = np.random.uniform() <= 0.5

    books = []
    for i in range(n_books):
        style_idx = np.random.randint(0, len(style_seeds_local))
        style_seed = style_seeds_local[style_idx]
        saved_state = np.random.get_state()

        paper_mat = paper_mats[style_idx]
        cover_mat = cover_mats[style_idx]

        np.random.seed(style_seed + i * 1000)
        obj = make_book(paper_mat, cover_mat)
        np.random.set_state(saved_state)

        co = read_co(obj)
        obj.location = (-co[:, 0].max(), -co[:, 1].min(), -co[:, 2].min())
        apply_tf(obj, loc=True)

        if np.random.uniform() < 0.5:
            obj.rotation_euler = (np.pi / 2 - float(np.random.uniform(0, max_angle)), 0, np.pi / 2)
        else:
            co = read_co(obj)
            obj.location = (0, 0, -co[:, 2].max())
            apply_tf(obj, loc=True)
            co = read_co(obj)
            obj.location = (-co[:, 0].max(), -co[:, 1].min(), -co[:, 2].min() + co[:, 2].max())
            apply_tf(obj, loc=True)
            obj.rotation_euler = (np.pi / 2 + float(np.random.uniform(0, max_angle)), 0, np.pi / 2)
        apply_tf(obj)

        if i > 0:
            obj.location = (10, 0, 0)
            apply_tf(obj, loc=True)
            prev_max_x = read_co(books[-1])[:, 0].max()
            curr_min_x = read_co(obj)[:, 0].min()
            obj.location = (prev_max_x - curr_min_x, 0, 0)
            apply_tf(obj, loc=True)

        books.append(obj)

    result = join_objs(books)
    co = read_co(result)
    result.location = (-co[:, 0].min(), 0, 0)
    apply_tf(result, loc=True)

    result.name = "BookColumnFactory"

    # Apply wear & tear
    if wear_do_scratch:
        apply_scratches(result)
    if wear_do_edgewear:
        apply_edge_wear(result)

    return result

# --- Main ---

clear_scene()
obj = make_book_column()

print(f"BookColumnFactory: {len(obj.data.vertices)} verts, "
      f"{len(obj.data.polygons)} faces, "
      f"{len(obj.data.materials)} material slots")

