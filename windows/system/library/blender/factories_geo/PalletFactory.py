# [FL_INDEX: keywords="blender_factory, procedural_3d, PalletFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PalletFactory | Category: factories_geo
# Prompt: A standard wooden shipping pallet rendered as a detailed 3D model, featuring a grid of dark brown wooden planks across the top surface running in one direction, supported below by perpendicular runner boards raised on short block feet that create forklift entry channels on all four sides.

import os
import random
import colorsys

import bpy
import numpy as np

SEED = int(os.environ.get("SEED", "0"))
np.random.seed(SEED)

def _seed_mat(seed):
    _s = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s); random.seed(_s)

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h)%1, max(0,min(1,float(s))), max(0,min(1,float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear()
    return m

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def make_mat(seed, name="WoodMaterial"):
    _seed_mat(seed)
    base_hue = float(np.random.uniform(0.04, 0.1))
    c1 = _hsv2rgba(base_hue, np.random.uniform(0.4, 0.8), np.random.uniform(0.15, 0.5))
    c2 = _hsv2rgba(base_hue + float(np.random.uniform(-0.02, 0.02)), np.random.uniform(0.3, 0.6), np.random.uniform(0.3, 0.7))
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
    bpy.context.scene.cursor.location = (0, 0, 0)

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
