# [FL_INDEX: keywords="blender_factory, procedural_3d, DoorCasingFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: DoorCasingFactory | Category: factories_tex
# Prompt: A clean white architectural door casing rendered as a 3D model, consisting of a rectangular frame surrounding an open doorway.

import os
import random

import bpy
import numpy as np

SEED = 0
random.seed(SEED)
SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

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

WOOD_COLORS = [
    0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170,
    0x3D2B1F, 0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43,
    0x4E3828, 0x4E3828, 0xC09A6B, 0x944536, 0x3F0110, 0x773C12,
    0x6E4E37, 0x5C4033, 0x5C4033, 0x3C3034, 0x96704C, 0x371B1A,
    0x483B32, 0x43141A, 0x471713, 0xC3B090, 0x6B4423, 0x674D46,
    0x5D2E1A, 0x331C1F, 0x7A5640, 0xB99984, 0x71543D, 0x8F4B28,
    0x491A00, 0x836446, 0x7F461B, 0x6A3208, 0x724115, 0xA0522B,
    0x832A0C, 0x371B1A, 0xC7A373, 0x483B32, 0x635147, 0x664228,
    0x5C5248,
]

def _srgb_to_linear(c):
    if c < 0: return 0.0
    elif c < 0.04045: return c / 12.92
    else: return ((c + 0.055) / 1.055) ** 2.4

def _hex2rgba_linear(hexval):
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0)

def _wood_base_color(seed):
    """Sample wood color"""

    rng = np.random.RandomState(((seed + 7) * 2654435761) & 0xFFFFFFFF)
    hexval = WOOD_COLORS[rng.randint(0, len(WOOD_COLORS))]
    r, g, b, _ = _hex2rgba_linear(hexval)
    h, s, v = _colorsys.rgb_to_hsv(r, g, b)
    # Variation in wood color
    h2 = (h + rng.uniform(-0.0, 0.05)) % 1.0
    s2 = max(0, min(1, s + rng.uniform(-0.3, 0.2)))
    v2 = max(0, min(1, v * float(np.exp(rng.uniform(np.log(0.2), np.log(20))))))
    return _colorsys.hsv_to_rgb(h2, s2, v2)

def make_mat(seed, name="WoodMaterial"):
    """Wood material with color"""

    r1, g1, b1 = _wood_base_color(seed)
    r2, g2, b2 = _wood_base_color(seed + 3)
    c1 = (r1, g1, b1, 1.0)
    c2 = (r2, g2, b2, 1.0)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(np.random.uniform(5, 20))
    noise.inputs["Detail"].default_value = 5.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = c1
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = c2
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.3, 0.6))
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

ELEM_MAT = make_mat(SEED, "DoorCasingFactory_Material")
np.random.seed(SEED)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)

def apply_tf(obj, loc=False):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if loc:
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    else:
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def add_mod(obj, mtype, apply=True, **kw):
    m = obj.modifiers.new("", mtype)
    for k, v in kw.items():
        setattr(m, k, v)
    bpy.context.view_layer.objects.active = obj
    if apply:
        bpy.ops.object.modifier_apply(modifier=m.name)
    return m

def read_edge_centers_and_dirs(obj):
    """Read edge centers and normalized directions using bmesh."""

    mesh = obj.data
    mesh.update()
    verts = np.zeros(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', verts)
    verts = verts.reshape(-1, 3)

    edges = np.zeros(len(mesh.edges) * 2, dtype=int)
    mesh.edges.foreach_get('vertices', edges)
    edges = edges.reshape(-1, 2)

    v0 = verts[edges[:, 0]]
    v1 = verts[edges[:, 1]]
    centers = (v0 + v1) / 2
    dirs = v1 - v0
    norms = np.linalg.norm(dirs, axis=1, keepdims=True)
    norms[norms < 1e-10] = 1
    dirs = dirs / norms
    return centers, dirs

def build_door_casing():
    clear_scene()

    # Simulate RoomConstants
    wall_thickness = np.random.uniform(0.2, 0.3)
    segment_margin = 1.4
    door_width_ratio = np.random.uniform(0.7, 0.8)
    door_width = (segment_margin - wall_thickness) * door_width_ratio
    door_size = np.random.uniform(2.0, 2.4)

    margin = door_size * np.random.uniform(0.05, 0.1)
    extrude = np.random.uniform(0.02, 0.08)
    bevel_all_sides = np.random.uniform() < 0.3

    w = door_width
    s = door_size

    # Outer box: new_cube at location (0,0,1) → z range [0, 2]
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    outer = bpy.context.active_object
    outer.location = (0, 0, 1)
    apply_tf(outer, loc=True)
    outer.scale = (w / 2 + margin, wall_thickness / 2 + extrude, s / 2 + margin / 2)
    apply_tf(outer)

    # Cutter: z range [0, s], wider than outer in Y to cut clean through
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    cutter = bpy.context.active_object
    cutter.location = (0, 0, 1 - 1e-3)
    apply_tf(cutter, loc=True)
    cutter.scale = (w / 2 - 1e-3, wall_thickness + extrude, s / 2)
    apply_tf(cutter)

    # Boolean difference
    bool_mod = outer.modifiers.new("bool", "BOOLEAN")
    bool_mod.operation = "DIFFERENCE"
    bool_mod.object = cutter
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

    # Edge-based bevel selection using edge center/direction analysis
    centers, dirs = read_edge_centers_and_dirs(outer)
    x, y, z = centers.T
    x_, y_, z_ = dirs.T

    if bevel_all_sides:
        selection = (np.abs(z_) > 0.5) | (np.abs(x_) > 0.5)
    else:
        selection = (
            ((np.abs(z_) > 0.5) & (np.abs(x) < w / 2 + margin / 2)) |
            ((np.abs(x_) > 0.5) & (z < s + margin / 2))
        )

    # Set bevel weight on selected edges (Blender 5.0 attribute API)
    mesh = outer.data
    attr_name = 'bevel_weight_edge'
    if attr_name not in mesh.attributes:
        mesh.attributes.new(attr_name, 'FLOAT', 'EDGE')
    mesh.attributes[attr_name].data.foreach_set('value', selection.astype(float))

    # Apply bevel with WEIGHT limit_method and custom profile preset
    preset = np.random.choice(["LINE", "SUPPORTS", "CORNICE", "CROWN", "STEPS"])
    mod = add_mod(outer, "BEVEL", apply=False,
                  width=extrude,
                  segments=np.random.randint(20, 30),
                  limit_method="WEIGHT",
                  profile_type="CUSTOM")

    # Apply preset to custom profile
    try:
        mod.custom_profile.preset = preset
    except Exception:
        pass

    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier=mod.name)

    outer.name = "DoorCasingFactory"
    # [auto-append] ensure material bound
    if outer is not None:
        if len(outer.data.materials) == 0:
            outer.data.materials.append(ELEM_MAT)
        elif outer.data.materials[0] is None:
            outer.data.materials[0] = ELEM_MAT
    return outer

casing = build_door_casing()

