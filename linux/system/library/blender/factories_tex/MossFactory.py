# [FL_INDEX: keywords="blender_factory, procedural_3d, MossFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MossFactory | Category: factories_tex
# Prompt: A 3D model of a small moss fragment rendered from a slightly elevated perspective, featuring a short curved wedge or crescent-shaped piece with a rounded top edge and flat base, colored in a muted olive-brown tone with subtle surface variation.

import os
import math
import random
import colorsys

import bpy
import numpy as np

SEED = int(os.environ.get("SEED", 0))

# ══════════════════════════════════════════════════════════════════════════════
# Green translucent plant shader: NoiseTexture -> HSV ColorRamp -> MixRGB (with
# ObjectInfo Random) -> Principled BSDF (subsurface) mixed with TranslucentBSDF.
# ══════════════════════════════════════════════════════════════════════════════

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def _hsv2rgba(h, s, v):
    h = float(h) % 1.0
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, float(v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _get_noise_fac(noise_node):
    return noise_node.outputs.get("Fac") or noise_node.outputs.get("Factor") or noise_node.outputs[0]

def _set_principled(bsdf, key, value):
    """Set a Principled BSDF input, tolerating Blender 4.x/5.x socket renames."""

    if key in bsdf.inputs:
        bsdf.inputs[key].default_value = value
        return
    # Subsurface Weight renamed from "Subsurface" in older versions
    fallbacks = {
        "Subsurface Weight": ("Subsurface",),
        "Subsurface": ("Subsurface Weight",),
    }
    for alt in fallbacks.get(key, ()):
        if alt in bsdf.inputs:
            bsdf.inputs[alt].default_value = value
            return

def make_moss_material(seed, name="MossMaterial"):
    """Faithful replication of MossFactory.shader_moss.

    Sampling order (raw SEED, mirrors MossFactory.__init__ then shader_moss):
      1. base_hue = U(0.2, 0.24)                # __init__
      2. base_hue_shift = U(-0.02, 0.02)        # create_asset call site
      3. h_perturb = U(-0.02, 0.02)             # shader_moss locals
      4. s_perturb = U(-0.1, 0.0)
      5. v_perturb = U(1.0, 1.5)
    """

    seed_all(seed)

    # Mirror MossFactory.__init__
    base_hue = float(np.random.uniform(0.2, 0.24))
    # Mirror MossFactory.create_asset shader_func call:
    #   shader_moss, (self.base_hue + U(-0.02, 0.02) % 1)
    base_hue = (base_hue + float(np.random.uniform(-0.02, 0.02))) % 1

    # Mirror shader_moss locals
    h_perturb = float(np.random.uniform(-0.02, 0.02))
    s_perturb = float(np.random.uniform(-0.1, 0.0))
    v_perturb = float(np.random.uniform(1.0, 1.5))

    def map_perturb(h, s, v):
        return _hsv2rgba(h + h_perturb, s + s_perturb, v / v_perturb)

    subsurface_ratio = 0.05
    roughness = 1.0
    mix_ratio = 0.2

    # Colors (bright moss, slightly shifted darker moss, black)
    color_a = map_perturb(base_hue, 0.8, 0.1)
    color_b = map_perturb(base_hue - 0.05, 0.8, 0.1)
    color_c = (0.0, 0.0, 0.0, 1.0)
    background = map_perturb(base_hue, 0.8, 0.02)

    mat = _new_mat(name)
    nt = mat.node_tree
    link = nt.links.new

    # NoiseTexture(Scale=5) -> Fac
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 5.0

    # Build color ramp (mode=HSV, 3 stops at 0, 0.5, 1)
    color_ramp = nt.nodes.new("ShaderNodeValToRGB")
    color_ramp.color_ramp.color_mode = "HSV"
    # default has 2 elements; add one more for total of 3
    color_ramp.color_ramp.elements.new(0.5)
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[0].color = color_a
    color_ramp.color_ramp.elements[1].position = 0.5
    color_ramp.color_ramp.elements[1].color = color_b
    color_ramp.color_ramp.elements[2].position = 1.0
    color_ramp.color_ramp.elements[2].color = color_c
    link(_get_noise_fac(noise), color_ramp.inputs["Fac"])

    # ObjectInfo -> Random output
    obj_info = nt.nodes.new("ShaderNodeObjectInfo")

    # MixRGB with Random as factor, ColorRamp as A, background as B
    mix_rgb = nt.nodes.new("ShaderNodeMix")
    mix_rgb.data_type = "RGBA"
    mix_rgb.blend_type = "MIX"
    link(obj_info.outputs["Random"], mix_rgb.inputs[0])
    link(color_ramp.outputs["Color"], mix_rgb.inputs[6])
    mix_rgb.inputs[7].default_value = background

    # Principled BSDF with subsurface
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    link(mix_rgb.outputs[2], principled.inputs["Base Color"])
    _set_principled(principled, "Subsurface Weight", subsurface_ratio)
    if "Subsurface Radius" in principled.inputs:
        principled.inputs["Subsurface Radius"].default_value = (0.01, 0.01, 0.01)
    # "Subsurface Color" only exists in Blender 3.x; 4.x merges it with Base Color.
    if "Subsurface Color" in principled.inputs:
        principled.inputs["Subsurface Color"].default_value = background
    principled.inputs["Roughness"].default_value = roughness

    # Translucent BSDF
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    link(mix_rgb.outputs[2], translucent.inputs["Color"])

    # Mix Shader (fac=mix_ratio, A=principled, B=translucent)
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    mix_shader.inputs["Fac"].default_value = mix_ratio
    link(principled.outputs["BSDF"], mix_shader.inputs[1])
    link(translucent.outputs["BSDF"], mix_shader.inputs[2])

    output = nt.nodes.new("ShaderNodeOutputMaterial")
    link(mix_shader.outputs["Shader"], output.inputs["Surface"])

    return mat

# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════

CATEG_MAT = make_moss_material(SEED, "MossFactory_Material")
CATEG_MAT.use_fake_user = True

# MossFactory does NOT use wear_tear — no scratches / edge wear applied.

# ══════════════════════════════════════════════════════════════════════════════
# Geometry — copied verbatim from objects_blender/particles/MossFactory.py
# ══════════════════════════════════════════════════════════════════════════════

random.seed(SEED)
np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.context.scene.cursor.location = (0, 0, 0)

from numpy.random import uniform as U

def build_moss_geonodes():
    """GeoNodes: BezierSegment + CurveCircle -> CurveToMesh."""

    end_z = U(0.04, 0.05)
    end_x = -0.04
    end_handle_x = end_x + U(-0.03, -0.02)
    end_handle_z = end_z + U(-0.01, 0.0)

    ng = bpy.data.node_groups.new("MossStrand", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')
    go.is_active_output = True

    bezier = ng.nodes.new('GeometryNodeCurvePrimitiveBezierSegment')
    bezier.inputs['Resolution'].default_value = 10
    bezier.inputs['Start'].default_value = (0, 0, 0)
    bezier.inputs['Start Handle'].default_value = (-0.03, 0, 0.02)
    bezier.inputs['End'].default_value = (end_x, 0, end_z)
    bezier.inputs['End Handle'].default_value = (end_handle_x, 0, end_handle_z)

    circle = ng.nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.inputs['Resolution'].default_value = 4
    circle.inputs['Radius'].default_value = 0.008

    c2m = ng.nodes.new('GeometryNodeCurveToMesh')
    ng.links.new(bezier.outputs['Curve'], c2m.inputs['Curve'])
    ng.links.new(circle.outputs['Curve'], c2m.inputs['Profile Curve'])
    ng.links.new(c2m.outputs['Mesh'], go.inputs['Geometry'])
    return ng

# Build
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "MossFactory"

mod = obj.modifiers.new("MossGeo", 'NODES')
mod.node_group = build_moss_geonodes()
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.modifier_apply(modifier=mod.name)

# Attach textured material
obj.data.materials.clear()
obj.data.materials.append(CATEG_MAT)

print(f"MossFactory built: {len(obj.data.vertices)} verts, "
      f"{len(obj.data.polygons)} faces, "
      f"{len(obj.data.materials)} material slots")

