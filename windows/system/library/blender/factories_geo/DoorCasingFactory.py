# [FL_INDEX: keywords="blender_factory, procedural_3d, DoorCasingFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: DoorCasingFactory | Category: factories_geo
# Prompt: A clean white architectural door casing rendered as a 3D model, consisting of a rectangular frame surrounding an open doorway.

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
    """Wood: warm brown with noise grain pattern."""

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

ELEM_MAT = make_mat(SEED, "DoorCasingFactory_Material")
np.random.seed(SEED)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    bpy.context.scene.cursor.location = (0, 0, 0)

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
