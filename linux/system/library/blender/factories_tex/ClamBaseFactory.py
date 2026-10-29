# [FL_INDEX: keywords="blender_factory, procedural_3d, ClamBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: ClamBaseFactory | Category: factories_tex
# Prompt: A 3D model of a clam shell rendered from a three-quarter perspective, featuring two smooth, rounded oval valve halves hinged together and partially open, with a convex bowl-shaped lower valve and a slightly angled upper valve, displayed with a clean white untextured surface.

import os
import math
import random

import bmesh
import bpy
import numpy as np
from scipy.interpolate import interp1d

SEED = int(os.environ.get("SEED", 0))
random.seed(SEED)
np.random.seed(SEED)

# ── helpers ───────────────────────────────────────────────────────────────────

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

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def write_co(obj, arr):
    obj.data.vertices.foreach_set("co", arr.reshape(-1))
    obj.data.update()

def log_uniform(low, high):
    return float(np.exp(np.random.uniform(np.log(low), np.log(high))))

# ── shell geometry ────────────────────────────────────────────────────────────

def build_filled_disc(n_verts=1024):
    bpy.ops.mesh.primitive_circle_add(vertices=n_verts, location=(1, 0, 0))
    obj = bpy.context.active_object
    apply_tf(obj)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.fill_grid()
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj

def build_ellipse(obj, viewpoint=(0.0, 0.0, 1.0), softness=0.3):
    viewpoint = np.array(viewpoint)
    co = read_co(obj)

    x, y, z = co.T
    r = np.sqrt((x - 1) ** 2 + y ** 2 + z ** 2)
    t = 1.0 - softness + softness * r ** 4

    displacement = (1.0 - t)[:, np.newaxis] * (viewpoint[np.newaxis, :] - co)
    co += displacement
    write_co(obj, co)
    return obj

def shape_by_angles(obj, angles, scales):
    co = read_co(obj)
    x, y, z = co.T
    vert_angles = np.arctan2(y, x)

    f = interp1d(angles, scales, kind='quadratic', bounds_error=False, fill_value=0)
    vert_scales = f(vert_angles)

    co *= vert_scales[:, np.newaxis]
    write_co(obj, co)
    return obj

def deep_clone(obj):
    mesh_copy = obj.data.copy()
    clone = bpy.data.objects.new(obj.name + "_clone", mesh_copy)
    bpy.context.collection.objects.link(clone)
    return clone

# ── clam maker ───────────────────────────────────────────────────────────────

def clam_make():
    """

    Build one clam shell half.
    Matches ShellBaseFactory.clam_make.
    """

    obj = build_filled_disc(1024)
    build_ellipse(obj, viewpoint=(0, 0, 1), softness=0.5)

    obj.scale = (1, 1.2, 1)
    apply_tf(obj)

    s = float(np.random.uniform(0.6, 0.7))
    angles = [
        -float(np.random.uniform(0.4, 0.5)),
        -float(np.random.uniform(0.3, 0.35)),
        float(np.random.uniform(-0.25, 0.25)),
        float(np.random.uniform(0.3, 0.35)),
        float(np.random.uniform(0.4, 0.5)),
    ]
    scales = [0, s, 1, s, 0]
    shape_by_angles(obj, np.array(angles) * np.pi, scales)

    # No radial grooves for clam
    # No hinge for clam
    return obj

# ── main factory ──────────────────────────────────────────────────────────────

def create_shell_asset(maker_fn):
    upper = maker_fn()
    apply_tf(upper)

    dim = float(np.sqrt(upper.dimensions[0] * upper.dimensions[1] + 0.01))
    s = 1.0 / dim
    upper.scale = (s, s, s)
    upper.location[2] += 0.005
    apply_tf(upper)

    lower = deep_clone(upper)
    lower.scale = (1, 1, -1)
    apply_tf(lower)

    base = float(np.random.uniform(0, np.pi / 4))
    lower.rotation_euler[1] = -base
    upper.rotation_euler[1] = -base - float(np.random.uniform(np.pi / 6, np.pi / 3))

    # Match join_objects([lower, upper]): active = lower (first arg)
    bpy.ops.object.select_all(action="DESELECT")
    lower.select_set(True)
    upper.select_set(True)
    bpy.context.view_layer.objects.active = lower
    bpy.ops.object.join()

    result = bpy.context.active_object
    # Match join_objects: reset transform to identity (no apply)
    result.location = (0, 0, 0)
    result.rotation_euler = (0, 0, 0)
    result.scale = (1, 1, 1)
    return result

def build_clam_base_factory():
    np.random.seed(SEED)
    random.seed(SEED)
    clear_scene()

    result = create_shell_asset(clam_make)
    return result

result = build_clam_base_factory()

result.name = "ClamBaseFactory"
print(f"ClamBaseFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces")

