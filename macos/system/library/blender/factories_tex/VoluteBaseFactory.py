# [FL_INDEX: keywords="blender_factory, procedural_3d, VoluteBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: VoluteBaseFactory | Category: factories_tex
# Prompt: A 3D model of a volute shell rendered from a three-quarter perspective, featuring a smooth rounded globular coiled form with a large inflated body whorl and a low spire, spiraling inward to a small opening, displayed with a clean white untextured surface and a rounded overall silhouette.

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

# ── helpers ───────────────────────────────────────────────────────────────────




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

# ── snail spiral core ────────────────────────────────────────────────────────

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

# ── main factory ──────────────────────────────────────────────────────────────

def build_volute():
    """

    Volute shell: wide spiral, fast shrink, few loops.
    Matches SnailBaseFactory.volute_make.
    """

    freq = 256

    shrink = float(np.random.uniform(0.5, 0.6))
    scale = solve_scale(shrink, freq)
    lateral = solve_lateral(float(np.random.uniform(0.4, 0.5)), freq, scale)
    longitude = solve_longitude(float(np.random.uniform(0.6, 0.7)), freq, scale)
    loop = int(np.random.randint(4, 5))

    obj = snail_make(lateral, longitude, freq, scale, loop)
    return obj

def build_volute_base_factory():
    np.random.seed(SEED)
    random.seed(SEED)
    clear_scene()

    # Consume the same random state as SnailBaseFactory.__init__
    # SnailBaseFactory.__init__ calls:
    # 1. np.random.choice(self.makers) -- 1 random call
    # 2. uniform(0, 0.3) or uniform(0.7, 1.0) -- ratio, 2 random calls
    # 3. log_uniform(0.2, 1) -- z_scale, 1 call
    # 4. log_uniform(2, 20) -- distortion, 1 call
    # But VoluteBaseFactory overrides maker to volute_make,
    # so we still need to consume the SnailBase init random state.
    # FixedSeed(factory_seed) resets to the seed, then the random calls happen.

    # Actually, for standalone we just need the geometry to match.
    # The SnailBaseFactory.__init__ with FixedSeed(factory_seed) does:
    #   np.random.choice(self.makers) → consume 1 call
    #   ratio = uniform(0, 0.3) or uniform(0.7, 1.0) → consume 2-3 calls
    #   z_scale = log_uniform(0.2, 1) → 1 call
    #   distortion = log_uniform(2, 20) → 1 call
    # But VoluteBaseFactory.__init__ calls super().__init__ first,
    # which does these calls, then overrides self.maker.
    # Then create_asset calls self.maker() = self.volute_make()
    # which calls self.snail_make() with specific params.

    # For standalone, we skip the init random calls and just seed properly
    # for the volute_make geometry.

    obj = build_volute()
    obj = finalize_snail(obj)
    return obj

result = build_volute_base_factory()

result.name = "VoluteBaseFactory"
print(f"VoluteBaseFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces")

