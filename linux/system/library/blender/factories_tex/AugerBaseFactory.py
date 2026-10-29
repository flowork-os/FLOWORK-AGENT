# [FL_INDEX: keywords="blender_factory, procedural_3d, AugerBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: AugerBaseFactory | Category: factories_tex
# Prompt: A 3D model of an auger shell rendered from a three-quarter perspective, featuring an elongated, tapered conical shape with a series of progressively smaller rounded whorls spiraling from a wide aperture to a pointed tip, displayed with a smooth white untextured surface.

import os
SEED = int(os.environ.get('SEED', 0))
import math
import random

import bpy
import mathutils
import numpy as np

SEED = int(os.environ.get("SEED", 0))
random.seed(SEED)
np.random.seed(SEED)

# -- helpers -------------------------------------------------------------------

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for e in list(bpy.data.objects):
        bpy.data.objects.remove(e)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def log_uniform(low, high):
    return float(np.exp(np.random.uniform(np.log(low), np.log(high))))

# -- snail spiral core --------------------------------------------------------

def build_cross_section(n=40, affine=1.0, spike=0.0, concave=2.2):
    """

    Build superellipse cross-section polygon.
    |cos(t)|^concave + |sin(t)|^concave defines the radius envelope.
    """

    perturb = 1.0 / (5 * n)
    angles = (np.arange(n) / n + np.random.uniform(-perturb, perturb, n)) * 2 * np.pi
    radius = np.abs(np.cos(angles)) ** concave + np.abs(np.sin(angles)) ** concave
    radius *= 1.0 + np.random.uniform(0, spike, n) * (np.random.uniform(0, 1, n) < 0.2)

    vertices = np.stack([
        np.cos(angles) * radius,
        np.sin(angles) * radius * affine,
        np.zeros_like(angles),
    ]).T

    edges = np.stack([np.arange(n), np.roll(np.arange(n), -1)]).T

    mesh = bpy.data.meshes.new("cross_section")
    mesh.from_pydata(vertices.tolist(), edges.tolist(), [])
    mesh.update()

    obj = bpy.data.objects.new("cross_section", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Small random rotation around Z
    obj.rotation_euler = (0, 0, float(np.random.uniform(0, np.pi / 12)))
    apply_tf(obj)

    return obj

def solve_scale(shrink, freq):
    return shrink ** (1.0 / freq)

def solve_lateral(ratio, freq, scale):
    indices = np.arange(freq)
    denom = (np.sin(2 * np.pi / freq * indices) * scale ** indices).sum()
    return ratio / denom

def solve_longitude(ratio, freq, scale):
    return ratio * (1 + scale ** freq) / freq

def snail_make(lateral=0.15, longitudinal=0.04, freq=28, scale=0.99,
               loop=8, affine=1.0, spike=0.0):
    """

    Core spiral shell generator matching SnailBaseFactory.snail_make.
    Uses ARRAY modifier with object offset to create spiral.
    """

    n = 40
    resolution = loop * freq
    concave = float(np.random.uniform(1.9, 2.1))

    # 1. Build cross-section
    obj = build_cross_section(n, affine, spike, concave)

    # 2. Create empty for object offset
    bpy.ops.object.empty_add(location=(0, 0, 0))
    empty = bpy.context.active_object
    empty.location = (longitudinal * np.random.choice([-1, 1]), 0, 0)
    empty.rotation_euler = (2 * np.pi / freq, 0, 0)
    empty.scale = (scale, scale, scale)

    # 3. Apply ARRAY modifier
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    mod = obj.modifiers.new("Array", 'ARRAY')
    mod.use_relative_offset = False
    mod.use_constant_offset = True
    mod.constant_offset_displace = (0, 0, lateral)
    mod.use_object_offset = True
    mod.offset_object = empty
    mod.count = resolution
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # 4. Delete the empty
    bpy.ops.object.select_all(action="DESELECT")
    empty.select_set(True)
    bpy.context.view_layer.objects.active = empty
    bpy.ops.object.delete()

    # 5. Bridge edge loops to create surface
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj

def finalize_snail(obj):
    """

    Post-process: normalize scale, random rotation, center, affine perturb.
    Matches SnailBaseFactory.create_asset.
    """

    apply_tf(obj)

    # Normalize to max dimension = 1
    dims = obj.dimensions
    max_dim = max(dims)
    if max_dim > 1e-6:
        s = 1.0 / max_dim
        obj.scale = (s, s, s)
    apply_tf(obj)

    # Random rotation (full random Euler)
    obj.rotation_euler = tuple(np.random.uniform(0, 2 * np.pi, 3))
    apply_tf(obj)

    # Center the object
    bb = np.array([list(obj.matrix_world @ mathutils.Vector(c)) for c in obj.bound_box])
    ctr = (bb.min(axis=0) + bb.max(axis=0)) / 2.0
    obj.location = (-ctr[0], -ctr[1], -ctr[2])
    obj.location[2] += obj.dimensions[2] * 0.4
    apply_tf(obj)

    # Affine perturbation
    co = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)

    offsets = np.zeros_like(co)
    for axis in range(3):
        weights = np.random.uniform(-0.1, 0.1, 3)
        offsets[:, axis] = co @ weights
    co += offsets

    obj.data.vertices.foreach_set("co", co.reshape(-1))
    obj.data.update()

    return obj

# -- main factory --------------------------------------------------------------

def build_auger():
    """

    Auger shell: tight narrow spiral, slow shrink, many loops, elongated cross-section.
    Matches SnailBaseFactory.auger_make.
    """

    freq = 256

    shrink = float(np.random.uniform(0.7, 0.8))
    scale = solve_scale(shrink, freq)
    lateral = solve_lateral(float(np.random.uniform(0.1, 0.15)), freq, scale)
    longitude = solve_longitude(float(np.random.uniform(0.9, 1.0)), freq, scale)
    loop = int(np.random.randint(8, 12))
    affine = float(np.random.uniform(0.5, 0.6))

    obj = snail_make(lateral, longitude, freq, scale, loop, affine=affine)
    return obj

def build_auger_base_factory():
    np.random.seed(SEED)
    random.seed(SEED)
    clear_scene()

    obj = build_auger()
    obj = finalize_snail(obj)
    return obj

result = build_auger_base_factory()
result.name = "AugerBaseFactory"
print(f"AugerBaseFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces")
