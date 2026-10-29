# [FL_INDEX: keywords="blender_factory, procedural_3d, PalletFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PalletFactory | Category: factories_tex
# Prompt: A standard wooden shipping pallet rendered as a detailed 3D model, featuring a grid of dark brown wooden planks across the top surface running in one direction, supported below by perpendicular runner boards raised on short block feet that create forklift entry channels on all four sides.

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

ELEM_MAT = make_mat(SEED, "PalletFactory_Material")
np.random.seed(SEED)

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

def add_mod(obj, mtype, **kw):
    m = obj.modifiers.new("", mtype)
    for k, v in kw.items():
        setattr(m, k, v)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def join_objs(objs):
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def new_cube_at_origin():
    """Create a cube with corner at origin: size=2 cube [-1,1]^3 shifted by (1,1,1) -> [0,2]^3."""

    bpy.ops.mesh.primitive_cube_add(size=2.0)
    obj = bpy.context.active_object
    obj.location = (1, 1, 1)
    apply_tf(obj)
    return obj

def make_vertical(depth, width, tile_width, tile_slackness, thickness):
    """Planks along X direction (spanning depth, spaced along width)."""

    obj = new_cube_at_origin()
    obj.scale = (tile_width / 2, depth / 2, thickness / 2)
    apply_tf(obj)

    count = int(np.floor((width - tile_width) / tile_width / tile_slackness) / 2) * 2
    count = max(2, count)

    add_mod(obj, "ARRAY",
            use_relative_offset=False,
            use_constant_offset=True,
            constant_offset_displace=((width - tile_width) / count, 0, 0),
            count=count + 1)
    return obj

def make_horizontal(depth, width, tile_width, tile_slackness, thickness):
    """Planks along Y direction (spanning width, spaced along depth)."""

    obj = new_cube_at_origin()
    obj.scale = (width / 2, tile_width / 2, thickness / 2)
    apply_tf(obj)

    count = int(np.floor((depth - tile_width) / tile_width / tile_slackness) / 2) * 2
    count = max(2, count)

    add_mod(obj, "ARRAY",
            use_relative_offset=False,
            use_constant_offset=True,
            constant_offset_displace=(0, (depth - tile_width) / count, 0),
            count=count + 1)
    return obj

def make_support(depth, width, tile_width, height, thickness):
    """3x3 grid of support blocks."""

    obj = new_cube_at_origin()
    obj.scale = (tile_width / 2, tile_width / 2, height / 2 - 2 * thickness)
    apply_tf(obj)

    add_mod(obj, "ARRAY",
            use_relative_offset=False,
            use_constant_offset=True,
            constant_offset_displace=((width - tile_width) / 2, 0, 0),
            count=3)

    add_mod(obj, "ARRAY",
            use_relative_offset=False,
            use_constant_offset=True,
            constant_offset_displace=(0, (depth - tile_width) / 2, 0),
            count=3)
    return obj

def build_pallet():
    clear_scene()

    depth = np.random.uniform(1.2, 1.4)
    width = np.random.uniform(1.2, 1.4)
    thickness = np.random.uniform(0.01, 0.015)
    tile_width = np.random.uniform(0.06, 0.10)
    tile_slackness = np.random.uniform(1.5, 2.0)
    height = np.random.uniform(0.20, 0.25)

    parts = []

    # Bottom vertical deck at z=thickness
    v1 = make_vertical(depth, width, tile_width, tile_slackness, thickness)
    v1.location[2] = thickness
    apply_tf(v1)
    parts.append(v1)

    # Top vertical deck (clone) at z=height-thickness
    v2 = make_vertical(depth, width, tile_width, tile_slackness, thickness)
    v2.location[2] = height - thickness
    apply_tf(v2)
    parts.append(v2)

    # Bottom horizontal deck at z=0
    h1 = make_horizontal(depth, width, tile_width, tile_slackness, thickness)
    parts.append(h1)

    # Top horizontal deck at z=height-2*thickness
    h2 = make_horizontal(depth, width, tile_width, tile_slackness, thickness)
    h2.location[2] = height - 2 * thickness
    apply_tf(h2)
    parts.append(h2)

    # Support blocks at z=2*thickness
    sup = make_support(depth, width, tile_width, height, thickness)
    sup.location[2] = 2 * thickness
    apply_tf(sup)
    parts.append(sup)

    result = join_objs(parts)
    result.name = "PalletFactory"
    # [auto-append] ensure material bound
    if result is not None:
        if len(result.data.materials) == 0:
            result.data.materials.append(ELEM_MAT)
        elif result.data.materials[0] is None:
            result.data.materials[0] = ELEM_MAT
    return result

pallet = build_pallet()

