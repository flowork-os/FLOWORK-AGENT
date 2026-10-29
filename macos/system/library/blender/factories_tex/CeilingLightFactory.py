# [FL_INDEX: keywords="blender_factory, procedural_3d, CeilingLightFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CeilingLightFactory | Category: factories_tex
# Prompt: A 3D model of a flush-mount ceiling light rendered from a slightly angled overhead perspective, featuring a flat cylindrical disc shape with a smooth white diffuser surface on top and a thin side profile, emitting a soft glow from its underside that illuminates the surrounding area.

import os
SEED = int(os.environ.get('SEED', 0))
import math
import random

import bmesh
import bpy
import numpy as np

SEED = int(os.environ.get("SEED", 0))
random.seed(SEED)
np.random.seed(SEED)

# ── scene helpers ─────────────────────────────────────────────────────────────

import os as _os, random as _random, colorsys as _colorsys


def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h)%1, max(0,min(1,float(s))), max(0,min(1,float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear()
    return m

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def make_category_mat(seed, name="LampMaterial"):
    """Port of shader_lamp_bulb_nonemissive: glass-like dome shader.
    LightPath-conditional mix of TransparentBSDF (camera rays) and
    TranslucentBSDF (non-camera rays). Base color from WhiteNoise mixed with tan."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    # ObjectInfo -> WhiteNoise -> Mix(0.9, noise_color, tan)
    obj_info = nt.nodes.new("ShaderNodeObjectInfo")
    white_noise = nt.nodes.new("ShaderNodeTexWhiteNoise")
    white_noise.noise_dimensions = "4D"
    ln(obj_info.outputs["Random"], white_noise.inputs["Vector"])

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.9
    ln(white_noise.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (0.5, 0.4444, 0.3669, 1.0)
    color_out = mix.outputs[2]

    # Transparent BSDF (camera ray branch) — glass-like pass-through
    transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
    ln(color_out, transparent.inputs["Color"])

    # Translucent BSDF (non-camera ray branch) — diffuse glow
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    ln(color_out, translucent.inputs["Color"])

    # LightPath -> MixShader (Fac=Is Camera Ray; slot1=Transparent, slot2=Translucent)
    light_path = nt.nodes.new("ShaderNodeLightPath")
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    ln(light_path.outputs["Is Camera Ray"], mix_shader.inputs["Fac"])
    ln(transparent.outputs["BSDF"], mix_shader.inputs[1])
    ln(translucent.outputs["BSDF"], mix_shader.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_shader.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_metal_mat(seed, name="LampMetal", dark=False):
    """Port of shader_black: simple Principled BSDF with teal/gray HSV color.
    hsv2rgba(U(0.45,0.55), U(0,0.1), U(0,1)) — not a warm brushed-metal."""

    hue = float(np.random.uniform(0.45, 0.55))
    sat = float(np.random.uniform(0.0, 0.1))
    val = float(np.random.uniform(0.0, 1.0))
    base_color = _hsv2rgba(hue, sat, val)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = base_color
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(principled.outputs["BSDF"], out.inputs["Surface"])
    return mat

LAMPSHADE_MAT = make_category_mat(SEED, "CeilingLightFactory_Lampshade")
LAMPSHADE_MAT.use_fake_user = True
CATEG_MAT = LAMPSHADE_MAT  # backward-compat alias

_saved_state = np.random.get_state()
METAL_BLACK_MAT = make_metal_mat(SEED, "CeilingLightBlackMetal", dark=True)
METAL_MAT       = make_metal_mat(SEED, "CeilingLightMetal", dark=False)
METAL_BLACK_MAT.use_fake_user = True
METAL_MAT.use_fake_user = True
np.random.set_state(_saved_state)

# --- wear_tear probability gates (mirror finalize_assets) ---
# Sampled here (module level) AFTER material sampling and BEFORE build(),
WEAR_DO_SCRATCH  = (np.random.uniform() <= 0.5)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= 0.5)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)

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

# ── parameter sampling ────────────────────────────────────────────────────────

def clip_gaussian(mean, std, lo, hi):
    return float(np.clip(np.random.normal(mean, std), lo, hi))

def sample_parameters():
    radius = clip_gaussian(0.12, 0.04, 0.1, 0.25)
    thickness = float(np.random.uniform(0.005, 0.05))
    inner_radius = radius * float(np.random.uniform(0.4, 0.9))
    height = 0.7 * clip_gaussian(0.09, 0.03, 0.07, 0.15)
    inner_height = height * float(np.random.uniform(0.5, 1.1))
    curvature = float(np.random.uniform(0.1, 0.5))
    return {
        "Radius": radius,
        "Thickness": thickness,
        "InnerRadius": inner_radius,
        "Height": height,
        "InnerHeight": inner_height,
        "Curvature": curvature,
    }

# ── outer cylindrical shell ───────────────────────────────────────────────────

def build_outer_shell(radius, height, thickness):
    """

    Thin-walled cylinder, open at bottom, closed at top.
    Hanging downward: top at z=0, bottom at z=-height.
    Matches curve_line (down) → curve_to_mesh → extrude Thickness + flip_faces.
    """

    bm = bmesh.new()
    n_sides = 512

    outer_top = []
    outer_bot = []
    inner_top = []
    inner_bot = []

    for j in range(n_sides):
        theta = 2 * math.pi * j / n_sides
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        outer_top.append(bm.verts.new((radius * cos_t, radius * sin_t, 0)))
        outer_bot.append(bm.verts.new((radius * cos_t, radius * sin_t, -height)))
        inner_top.append(bm.verts.new(((radius - thickness) * cos_t,
                                        (radius - thickness) * sin_t, 0)))
        inner_bot.append(bm.verts.new(((radius - thickness) * cos_t,
                                        (radius - thickness) * sin_t, -height)))

    # Outer wall
    for j in range(n_sides):
        j2 = (j + 1) % n_sides
        bm.faces.new([outer_top[j], outer_top[j2], outer_bot[j2], outer_bot[j]])

    # Inner wall (flipped normal)
    for j in range(n_sides):
        j2 = (j + 1) % n_sides
        bm.faces.new([inner_top[j], inner_bot[j], inner_bot[j2], inner_top[j2]])

    # Top annular face
    for j in range(n_sides):
        j2 = (j + 1) % n_sides
        bm.faces.new([outer_top[j], inner_top[j], inner_top[j2], outer_top[j2]])

    mesh = bpy.data.meshes.new("shell")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("shell", mesh)
    bpy.context.collection.objects.link(obj)
    apply_tf(obj)
    return obj

# ── top cap disc ──────────────────────────────────────────────────────────────

def build_top_cap(radius):
    """Flat circle disc at z=0 (ceiling face). Matches mesh_circle NGON."""

    bpy.ops.mesh.primitive_circle_add(
        vertices=512, radius=radius, fill_type="NGON", location=(0, 0, 0)
    )
    cap = bpy.context.active_object
    apply_tf(cap)
    return cap

# ── inner diffuser dome ───────────────────────────────────────────────────────

def build_inner_dome(inner_radius, inner_height, curvature):
    """

    Lower hemisphere of an icosphere of InnerRadius, scaled Z by Curvature,
    translated to z=-InnerHeight.
    Matches separate_geometry_1 (Z < 0) + transform (scale Z=Curvature, translate -InnerHeight).
    """

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=5, radius=inner_radius, location=(0, 0, 0)
    )
    sphere = bpy.context.active_object
    apply_tf(sphere)

    # Keep only lower hemisphere (Z <= 0)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    mesh = sphere.data
    # Mark vertices in upper hemisphere for deletion
    for v in mesh.vertices:
        v.select = v.co.z > 0.001
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply scale Z = curvature, translate to -inner_height
    sphere.scale.z = curvature
    sphere.location.z = -inner_height
    apply_tf(sphere)
    return sphere

# ── inner cylinder ────────────────────────────────────────────────────────────

def build_inner_cylinder(inner_radius, inner_height):
    """

    Short cylinder from z=0 to z=-inner_height at inner_radius.
    Matches curve_line_1 → curve_to_mesh_1 (inner tube with Fill Caps).
    """

    cyl_depth = inner_height - 0.001
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, radius=inner_radius, depth=cyl_depth,
        location=(0, 0, -0.001 - cyl_depth * 0.5)
    )
    cyl = bpy.context.active_object
    apply_tf(cyl)
    return cyl

# ── main ──────────────────────────────────────────────────────────────────────

# --- helpers required by wear_tear block (not already in this factory) ---
def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _noise_fac_output(noise_node):
    """Blender 5.0 renamed Fac->Factor on some nodes; fall back to first output."""

    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _set_principled(bsdf, **kw):
    """Set Principled BSDF inputs with Blender-version-tolerant socket names."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
        "Sheen Tint": ("Sheen Tint",),
        "Subsurface Color": ("Subsurface Color",),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

# wear_tear post-processing
# Faithful raw-bpy translations of:
# Both follow the same pattern: walk obj.data.materials, find existing
# MaterialOutput / BSDF, inject a procedural wear graph, reconnect.
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"

def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)

def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    if in0 is not None:
        if hasattr(in0, "default_value") or hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "default_value") or hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    return n

def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    if in0 is not None:
        if hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    if scale is not None:
        # SCALE op uses inputs[3] (Scale) on VectorMath
        for inp in n.inputs:
            if inp.name == "Scale":
                inp.default_value = scale
                break
    return n

def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = value
    return n

def _color_ramp(nt, fac_socket, stops):
    """stops = [(position, (r,g,b,a)), ...]"""

    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(fac_socket, fac_in)
    elements = cr.color_ramp.elements
    for i, (pos, color) in enumerate(stops):
        if i < len(elements):
            elements[i].position = pos
            elements[i].color = color
        else:
            e = elements.new(pos)
            e.color = color
    return cr

def _noise_tex(nt, vector_socket, scale, detail=2.0, distortion=0.0, roughness=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_socket is not None:
        nt.links.new(vector_socket, n.inputs["Vector"])
    if isinstance(scale, (int, float)):
        n.inputs["Scale"].default_value = float(scale)
    else:
        nt.links.new(scale, n.inputs["Scale"])
    if "Detail" in n.inputs:
        n.inputs["Detail"].default_value = detail
    if "Distortion" in n.inputs:
        n.inputs["Distortion"].default_value = distortion
    if "Roughness" in n.inputs:
        n.inputs["Roughness"].default_value = roughness
    return n

def get_scratch_params():
    """Replica of wear_tear/scratches.py:get_scratch_params."""

    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=log_uniform(5, 80),
        scratch_mask_ratio=log_uniform(0.01, 0.9),
        scratch_mask_noise=log_uniform(5, 40),
        scratch_depth=log_uniform(0.1, 1.0),
    )

def _build_scratch_graph(nt, params):
    """Build the scratch displacement node graph and return the Displacement output socket.

    Faithful translation of wear_tear/scratches.py:scratch_shader.
    """

    n_angle1 = _value_node(nt, params["angle1"])
    n_angle2 = _value_node(nt, params["angle2"])
    n_scale = _value_node(nt, params["scratch_scale"])
    n_mask_ratio = _value_node(nt, params["scratch_mask_ratio"])
    n_mask_noise = _value_node(nt, params["scratch_mask_noise"])
    n_depth = _value_node(nt, params["scratch_depth"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # First scratch direction
    cxyz1 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle1.outputs[0], cxyz1.inputs["Y"])
    map1 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map1, "vector_type"):
        try: map1.vector_type = "TEXTURE"
        except TypeError: pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    # Second scratch direction
    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map2, "vector_type"):
        try: map2.vector_type = "TEXTURE"
        except TypeError: pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    # Mask noise
    map3 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map3, "vector_type"):
        try: map3.vector_type = "TEXTURE"
        except TypeError: pass
    map3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.1920)
    nt.links.new(tex_coord.outputs["Object"], map3.inputs["Vector"])
    noise3 = _noise_tex(nt, map3.outputs["Vector"], n_mask_noise.outputs[0], detail=1.0)
    cr_mask = _color_ramp(nt, _noise_fac_output(noise3),
                          [(0.4109, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))])
    mul_mask = _math(nt, "MULTIPLY", n_mask_ratio.outputs[0], cr_mask.outputs["Color"])
    add_combined = _math(nt, "ADD", add.outputs[0], mul_mask.outputs[0], clamp=True)

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.7
    map_range.inputs[2].default_value = 0.72
    map_range.inputs[4].default_value = 0.9
    nt.links.new(add_combined.outputs[0], map_range.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(map_range.outputs["Result"], disp.inputs["Height"])
    nt.links.new(n_depth.outputs[0], disp.inputs["Scale"])

    return disp.outputs[0]

def apply_scratches(obj, **params):
    """Faithful raw-bpy port of wear_tear/scratches.py:Scratches.apply_over."""

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
            continue   # idempotency: already applied
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        try:
            disp_out = _build_scratch_graph(nt, params)
            nt.links.new(disp_out, mat_out.inputs["Displacement"])
            # Mark idempotency
            disp_out.node.label = SCRATCH_LABEL
        except Exception as e:
            print(f"  [scratches] failed on {mat.name}: {type(e).__name__}: {e}")

def get_edge_wear_params():
    """Replica of wear_tear/edge_wear.py:get_edge_wear_params."""

    return dict(
        worn_off_opacity=float(np.random.uniform(0, 0.01)),
        worn_off_radius=float(np.random.uniform(0.005, 0.01)),
        scratch_radius=float(np.random.uniform(0.01, 0.03)),
        worn_off_mask_randomness=float(np.random.uniform(2.5, 3.0)),
        edge_base_color_hue=float(np.random.uniform(0.0, 1.0)),
        edge_base_color_whiteness=float(np.random.uniform(0.1, 0.6)),
        scratch_mask_randomness=float(np.random.choice(
            [np.random.uniform(0.1, 5.0), np.random.uniform(1.0, 10.0)])),
        scratch_density=float(np.random.uniform(1.5, 10.0)),
        scratch_opacity=float(np.random.uniform(0.5, 1.0)),
    )

def _build_edge_wear_graph(nt, original_bsdf_node, original_displacement_node, params):
    """Faithful raw-bpy port of edge_wear.py:shader_edge_tear_free_node_group.

    Returns (final_bsdf_socket, final_displacement_socket).
    """

    p = params
    n_scratch_opacity = _value_node(nt, p["scratch_opacity"])
    n_scratch_mask_randomness = _value_node(nt, p["scratch_mask_randomness"])
    n_scratch_radius = _value_node(nt, p["scratch_radius"])
    n_worn_opacity = _value_node(nt, p["worn_off_opacity"])
    n_worn_radius = _value_node(nt, p["worn_off_radius"])
    n_worn_mask_randomness = _value_node(nt, p["worn_off_mask_randomness"])
    n_edge_whiteness = _value_node(nt, p["edge_base_color_whiteness"])
    n_edge_hue = _value_node(nt, p["edge_base_color_hue"])
    n_scratch_density = _value_node(nt, p["scratch_density"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    # Scratch mask noise
    noise_a = _noise_tex(nt, mapping.outputs["Vector"], n_scratch_mask_randomness.outputs[0], detail=1.0)
    cr_a = _color_ramp(nt, _noise_fac_output(noise_a),
                       [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    # Bevel edge detection (scratch radius)
    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.samples = 20
    nt.links.new(n_scratch_radius.outputs[0], bevel.inputs["Radius"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub = _vmath(nt, "SUBTRACT", bevel.outputs[0], geo.outputs["Normal"])
    abs_a = _math(nt, "ABSOLUTE", sub.outputs["Vector"])
    cr_b = _color_ramp(nt, abs_a.outputs[0],
                       [(0.0691, (0, 0, 0, 1)), (0.1564, (1, 1, 1, 1))])

    mul_a = _math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"], clamp=True)
    mul_a1 = _math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0], clamp=True)

    # Bevel edge detection (worn-off radius)
    bevel2 = nt.nodes.new("ShaderNodeBevel")
    bevel2.samples = 20
    nt.links.new(n_worn_radius.outputs[0], bevel2.inputs["Radius"])
    sub2 = _vmath(nt, "SUBTRACT", bevel2.outputs[0], geo.outputs["Normal"])
    abs_b = _math(nt, "ABSOLUTE", sub2.outputs["Vector"])

    noise_b = _noise_tex(nt, mapping.outputs["Vector"], n_worn_mask_randomness.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac_output(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
    cr_d = _color_ramp(nt, mul_b1.outputs[0],
                       [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])

    # Edge color HSV
    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    if hasattr(combine_color, "mode"):
        try: combine_color.mode = "HSV"
        except TypeError: pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_result"):
        try: mix.clamp_result = True
        except TypeError: pass
    if hasattr(mix, "clamp_factor"):
        try: mix.clamp_factor = False
        except TypeError: pass
    nt.links.new(n_edge_whiteness.outputs[0], mix.inputs[0])
    nt.links.new(combine_color.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

    # Worn-edge BSDFs (Principled)
    bsdf_worn1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn1.inputs["Base Color"])
    _set_principled(bsdf_worn1, Metallic=0.3745, Roughness=0.1436,
                    **{"Specular IOR Level": 0.0})

    # Mix the original BSDF with the worn version
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cr_d.outputs["Color"], mix_shader.inputs["Fac"])
    nt.links.new(original_bsdf_node.outputs[0], mix_shader.inputs[1])
    nt.links.new(bsdf_worn1.outputs[0], mix_shader.inputs[2])

    # Scratch density via voronoi distance-to-edge (two perpendicular)
    map_h = nt.nodes.new("ShaderNodeMapping")
    map_h.inputs["Scale"].default_value = (10.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_h.inputs["Vector"])
    vor_h = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_h, "feature"):
        try: vor_h.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])

    # Scale density by 2 for vertical
    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_v, "feature"):
        try: vor_v.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_v.outputs["Vector"], vor_v.inputs["Vector"])
    nt.links.new(scale_v.outputs[0], vor_v.inputs["Scale"])

    dist_h = vor_h.outputs.get("Distance") or vor_h.outputs[0]
    dist_v = vor_v.outputs.get("Distance") or vor_v.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_e = _color_ramp(nt, mul_dist.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_e = _math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"], clamp=True)
    mul_f = _math(nt, "MULTIPLY", mul_a.outputs[0], mul_e.outputs[0], clamp=True)

    bsdf_worn2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn2.inputs["Base Color"])
    _set_principled(bsdf_worn2, Metallic=0.3855, Roughness=0.0,
                    **{"Specular IOR Level": 0.0})

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_a1.outputs[0], mix_shader_2.inputs["Fac"])
    nt.links.new(mix_shader.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(bsdf_worn2.outputs[0], mix_shader_2.inputs[2])

    # Displacement
    scale_disp = _vmath(nt, "SCALE", in0=mul_f.outputs[0], scale=2.0)
    if original_displacement_node is None:
        total_displacement = scale_disp.outputs[0]
    else:
        add_disp = _math(nt, "ADD", original_displacement_node.outputs[0],
                         scale_disp.outputs[0], clamp=True)
        total_displacement = add_disp.outputs[0]

    return mix_shader_2.outputs[0], total_displacement

def apply_edge_wear(obj, **params):
    """Faithful raw-bpy port of wear_tear/edge_wear.py:EdgeWear.apply_over."""

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
            continue   # idempotency
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        # Find original BSDF feeding Surface
        surface_links = mat_out.inputs["Surface"].links
        if not surface_links:
            continue
        original_bsdf = surface_links[0].from_node
        # Find original displacement (if any)
        disp_links = mat_out.inputs["Displacement"].links
        original_disp = disp_links[0].from_node if disp_links else None
        try:
            final_bsdf_socket, final_disp_socket = _build_edge_wear_graph(
                nt, original_bsdf, original_disp, params)
            # Reconnect
            nt.links.new(final_bsdf_socket, mat_out.inputs["Surface"])
            nt.links.new(final_disp_socket, mat_out.inputs["Displacement"])
            # Mark idempotency on the new mix_shader
            final_bsdf_socket.node.label = EDGE_WEAR_LABEL
        except Exception as e:
            print(f"  [edge_wear] failed on {mat.name}: {type(e).__name__}: {e}")

def apply_wear_tear(obj):
    """

    Two independent 50% probability gates: scratches and edge_wear.
    """

    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    scratch_p, edge_p = WEAR_TEAR_PROB
    if np.random.uniform() <= scratch_p:
        apply_scratches(obj)
    if np.random.uniform() <= edge_p:
        apply_edge_wear(obj)

def build_ceiling_light():
    np.random.seed(SEED)
    clear_scene()

    p = sample_parameters()

    parts = []

    # 1. Outer cylindrical shell → metal casing
    shell = build_outer_shell(p["Radius"], p["Height"], p["Thickness"])
    shell.data.materials.append(METAL_MAT)
    parts.append(shell)

    # 2. Top cap at z=0 (ceiling attachment) → metal
    cap = build_top_cap(p["Radius"])
    cap.data.materials.append(METAL_MAT)
    parts.append(cap)

    # 3. Inner diffuser dome → lampshade (translucent diffuser)
    dome = build_inner_dome(p["InnerRadius"], p["InnerHeight"], p["Curvature"])
    dome.data.materials.append(LAMPSHADE_MAT)
    parts.append(dome)

    # 4. Inner cylindrical wall → lampshade (continues the diffuser surface)
    inner_cyl = build_inner_cylinder(p["InnerRadius"], p["InnerHeight"])
    inner_cyl.data.materials.append(LAMPSHADE_MAT)
    parts.append(inner_cyl)

    result = join_objs(parts)
    # Mount: position so top is at z=0 (attaches to ceiling)
    apply_tf(result)
    # Per-part materials were appended before join; slots preserved automatically.
    if result is not None and len(result.data.materials) == 0:
        result.data.materials.append(LAMPSHADE_MAT)
    # --- wear_tear application ---
    if result is not None and WEAR_DO_SCRATCH:
        apply_scratches(result)
    if result is not None and WEAR_DO_EDGEWEAR:
        apply_edge_wear(result)
    return result

light = build_ceiling_light()
light.name = "CeilingLightFactory"

