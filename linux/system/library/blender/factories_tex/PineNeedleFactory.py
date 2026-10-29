# [FL_INDEX: keywords="blender_factory, procedural_3d, PineNeedleFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PineNeedleFactory | Category: factories_tex
# Prompt: A 3D model of a single pine needle rendered from above, featuring an extremely thin, elongated strand with a gentle arc-like curvature and a subtle brownish-tan coloring, appearing as a fine hair-like filament against the background.

import os
import math
import random
import colorsys

import bpy
import numpy as np

SEED = int(os.environ.get("SEED", 0))

# ══════════════════════════════════════════════════════════════════════════════
# Inlined pine needle shader
# ObjectInfo(Random) -> ColorRamp(2 stops, each a fresh pine_needle_hsv sample)
# -> Principled BSDF (defaults) -> Material Output.
#   H = wrap_gaussian(0.05, 0.02)  (narrow warm-yellow/green hue)
#   S = uniform(0.5, 0.93)
#   V = uniform(0.045, 0.4)        (dark — pine needles are low value)
# ══════════════════════════════════════════════════════════════════════════════

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def _wrap_gaussian(mean, std, low=0.0, high=1.0):
    x = float(np.random.normal(mean, std))
    if x < low:
        x = high - (low - x) % (high - low)
    elif x > high:
        x = low + (x - high) % (high - low)
    return x

def _pine_needle_hsv():
    return (
        _wrap_gaussian(0.05, 0.02),
        float(np.random.uniform(0.5, 0.93)),
        float(np.random.uniform(0.045, 0.4)),
    )

def _hsv2rgba(hsv):
    h = float(hsv[0]) % 1.0
    s = max(0.0, min(1.0, float(hsv[1])))
    v = max(0.0, float(hsv[2]))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def make_pine_needle_material(seed, name="PineNeedleMaterial"):
    """Faithful replication of PineNeedleFactory.shader_material.

      1. pine_needle_hsv() for ColorRamp stop 0 -> 3 samples
         (wrap_gaussian normal + 2 uniforms)
      2. pine_needle_hsv() for ColorRamp stop 1 -> 3 samples
    """

    seed_all(seed)

    stop0_rgba = _hsv2rgba(_pine_needle_hsv())
    stop1_rgba = _hsv2rgba(_pine_needle_hsv())

    mat = _new_mat(name)
    nt = mat.node_tree
    link = nt.links.new

    # ObjectInfo -> Random output drives the color ramp factor so each
    # instance of the pine needle gets a deterministic (but varied) colour.
    obj_info = nt.nodes.new("ShaderNodeObjectInfo")

    color_ramp = nt.nodes.new("ShaderNodeValToRGB")
    # uses the default RGB (linear) interpolation mode.
    color_ramp.color_ramp.color_mode = "RGB"
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[0].color = stop0_rgba
    color_ramp.color_ramp.elements[1].position = 1.0
    color_ramp.color_ramp.elements[1].color = stop1_rgba
    link(obj_info.outputs["Random"], color_ramp.inputs["Fac"])

    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    link(color_ramp.outputs["Color"], principled.inputs["Base Color"])

    output = nt.nodes.new("ShaderNodeOutputMaterial")
    link(principled.outputs["BSDF"], output.inputs["Surface"])

    return mat

# ══════════════════════════════════════════════════════════════════════════════
# and finalize_assets, which both run inside the factory-level FixedSeed)
# ══════════════════════════════════════════════════════════════════════════════

CATEG_MAT = make_pine_needle_material(SEED, "PineNeedleFactory_Material")
CATEG_MAT.use_fake_user = True

# PineNeedleFactory does NOT use wear_tear — no scratches / edge wear applied.

# ══════════════════════════════════════════════════════════════════════════════
# Geometry — copied verbatim from objects_blender/particles/PineNeedleFactory.py
# ══════════════════════════════════════════════════════════════════════════════

random.seed(SEED)
np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.context.scene.cursor.location = (0, 0, 0)

from numpy.random import normal as N

def build_pine_needle_geonodes(scale, bend, radius):
    """GeoNodes: VectorMath(SCALE)*3 -> QuadraticBezier -> CurveToMesh(CurveCircle)."""

    ng = bpy.data.node_groups.new("PineNeedle", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')
    go.is_active_output = True

    # Scale vectors for start(-x), middle(+y bend), end(+x)
    v_start = ng.nodes.new('ShaderNodeVectorMath')
    v_start.operation = 'SCALE'
    v_start.inputs[0].default_value = (-1, 0, 0)
    v_start.inputs['Scale'].default_value = scale

    v_mid = ng.nodes.new('ShaderNodeVectorMath')
    v_mid.operation = 'SCALE'
    v_mid.inputs[0].default_value = (0, 1, 0)
    v_mid.inputs['Scale'].default_value = bend

    v_end = ng.nodes.new('ShaderNodeVectorMath')
    v_end.operation = 'SCALE'
    v_end.inputs[0].default_value = (1, 0, 0)
    v_end.inputs['Scale'].default_value = scale

    qb = ng.nodes.new('GeometryNodeCurveQuadraticBezier')
    qb.inputs['Resolution'].default_value = 5
    ng.links.new(v_start.outputs['Vector'], qb.inputs['Start'])
    ng.links.new(v_mid.outputs['Vector'], qb.inputs['Middle'])
    ng.links.new(v_end.outputs['Vector'], qb.inputs['End'])

    circle = ng.nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.inputs['Resolution'].default_value = 6
    circle.inputs['Radius'].default_value = radius

    c2m = ng.nodes.new('GeometryNodeCurveToMesh')
    ng.links.new(qb.outputs['Curve'], c2m.inputs['Curve'])
    ng.links.new(circle.outputs['Curve'], c2m.inputs['Profile Curve'])
    ng.links.new(c2m.outputs['Mesh'], go.inputs['Geometry'])
    return ng

# Sample random params
s = N(1, 0.2)
scale_val = 0.04 * s
bend_val = 0.03 * s * N(1, 0.2)
radius_val = 0.001 * s * N(1, 0.2)

# Build
mesh = bpy.data.meshes.new("spawn")
mesh.from_pydata([(0, 0, 0)], [], [])
obj = bpy.data.objects.new("PineNeedleFactory", mesh)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

mod = obj.modifiers.new("PineGeo", 'NODES')
mod.node_group = build_pine_needle_geonodes(scale_val, bend_val, radius_val)
bpy.ops.object.modifier_apply(modifier=mod.name)

# Attach textured material
obj.data.materials.clear()
obj.data.materials.append(CATEG_MAT)

print(f"PineNeedleFactory built: {len(obj.data.vertices)} verts, "
      f"{len(obj.data.polygons)} faces, "
      f"{len(obj.data.materials)} material slots")

