# [FL_INDEX: keywords="blender_factory, procedural_3d, SnakePlantFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SnakePlantFactory | Category: factories_tex
# Prompt: A 3D model of a snake plant (Sansevieria) rendered from an elevated perspective, featuring several tall upright sword-shaped leaves with pointed tips growing from a common base, each leaf displaying characteristic horizontal banded patterns in light cream and muted green.

import os
import math
import random
import colorsys

import bpy
import numpy as np
from numpy.random import normal, randint, uniform

# ── helpers ──────────────────────────────────────────────────────────────────

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def _fac(node):
    """Return the 'Fac' or 'Factor' output of a texture node (Blender 5.0 compat)."""

    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

def hsv2rgba(hsv_list):
    """Replicate hsv2rgba: mathutils.Color with HSV assignment."""

    from mathutils import Color
    c = Color()
    h = float(hsv_list[0]) % 1.0
    s = max(0.0, min(1.0, float(hsv_list[1])))
    v = max(0.0, min(1.0, float(hsv_list[2])))
    c.hsv = (h, s, v)
    return (c.r, c.g, c.b, 1.0)

# ── shader: snake_plant material ─────────────────────────────────────────────

def make_snake_plant_material(name="SnakePlantMaterial"):
#     shader_snake_plant() into raw bpy node-tree code."""


    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    ln = nt.links.new

    # --- Random band presence (40% chance of no bands, 60% chance of bands) ---
    stripe_factor = 2.0 * float(np.random.choice([0, 1], p=(0.4, 0.6)))

    # multiply_0: 0.001 * stripe_factor
    multiply_0 = nt.nodes.new("ShaderNodeMath")
    multiply_0.operation = "MULTIPLY"
    multiply_0.inputs[0].default_value = 0.001
    multiply_0.inputs[1].default_value = stripe_factor

    # colorramp_1: edge/tip masking
    colorramp_1 = nt.nodes.new("ShaderNodeValToRGB")
    ln(multiply_0.outputs[0], colorramp_1.inputs["Fac"])
    edge_pos = float(np.random.uniform(0.34, 0.42))
    colorramp_1.color_ramp.elements[0].position = edge_pos
    colorramp_1.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = edge_pos + 0.02
    colorramp_1.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    # texture_coordinate_1
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # mapping_1: Object coords
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    # noise_texture: distortion noise
    noise_tex = nt.nodes.new("ShaderNodeTexNoise")
    ln(mapping_1.outputs["Vector"], noise_tex.inputs["Vector"])
    noise_tex.inputs["Scale"].default_value = float(np.random.uniform(0.2, 1.0))
    noise_tex.inputs["Roughness"].default_value = 1.0

    # multiply_1: noise Fac * (1, 1, 0.6) (VectorMath MULTIPLY)
    multiply_1 = nt.nodes.new("ShaderNodeVectorMath")
    multiply_1.operation = "MULTIPLY"
    ln(_fac(noise_tex), multiply_1.inputs[0])
    multiply_1.inputs[1].default_value = (1.0, 1.0, 0.6)

    # add: multiply_1 + mapping_1 (VectorMath ADD)
    add_vec = nt.nodes.new("ShaderNodeVectorMath")
    add_vec.operation = "ADD"
    ln(multiply_1.outputs["Vector"], add_vec.inputs[0])
    ln(mapping_1.outputs["Vector"], add_vec.inputs[1])

    # wave_texture: Z-direction bands
    wave_tex = nt.nodes.new("ShaderNodeTexWave")
    wave_tex.bands_direction = "Z"
    ln(add_vec.outputs["Vector"], wave_tex.inputs["Vector"])
    wave_tex.inputs["Scale"].default_value = float(np.random.uniform(1.0, 2.5))
    wave_tex.inputs["Distortion"].default_value = float(np.random.uniform(2.0, 4.5))
    wave_tex.inputs["Detail Scale"].default_value = float(np.random.uniform(2.0, 8.0))
    wave_tex.inputs["Detail Roughness"].default_value = 2.0

    # greater_than: wave Fac > w
    wave_threshold = float(np.random.uniform(0.2, 0.7))
    greater_than = nt.nodes.new("ShaderNodeMath")
    greater_than.operation = "GREATER_THAN"
    ln(_fac(wave_tex), greater_than.inputs[0])
    greater_than.inputs[1].default_value = wave_threshold

    # mapping_2: Object coords scaled (7, 7, 0.05)
    mapping_2 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], mapping_2.inputs["Vector"])
    mapping_2.inputs["Scale"].default_value = (7.0, 7.0, 0.05)

    # noise_texture_1: fine detail noise
    noise_tex_1 = nt.nodes.new("ShaderNodeTexNoise")
    ln(mapping_2.outputs["Vector"], noise_tex_1.inputs["Vector"])
    noise_tex_1.inputs["Scale"].default_value = float(np.random.uniform(20.0, 40.0))

    # multiply_2: greater_than * noise_tex_1 Fac
    multiply_2 = nt.nodes.new("ShaderNodeMath")
    multiply_2.operation = "MULTIPLY"
    ln(greater_than.outputs[0], multiply_2.inputs[0])
    ln(_fac(noise_tex_1), multiply_2.inputs[1])

    # colorramp_8: band masking
    colorramp_8 = nt.nodes.new("ShaderNodeValToRGB")
    ln(multiply_2.outputs[0], colorramp_8.inputs["Fac"])
    colorramp_8.color_ramp.elements[0].position = 0.2318
    colorramp_8.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_8.color_ramp.elements[1].position = float(np.random.uniform(0.55, 0.75))
    colorramp_8.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # colorramp_4: wave-based gradient
    band_base = 0.6 + (wave_threshold - 0.2) * 0.6
    colorramp_4 = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(wave_tex), colorramp_4.inputs["Fac"])
    colorramp_4.color_ramp.elements[0].position = band_base
    colorramp_4.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_4.color_ramp.elements[1].position = float(np.minimum(1.0, band_base + np.random.uniform(0.02, 0.15)))
    colorramp_4.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # mix_1: ADD blend of colorramp_8 and colorramp_4
    # Blender 5.0: ShaderNodeMix with data_type='RGBA'
    mix_1 = nt.nodes.new("ShaderNodeMix")
    mix_1.data_type = "RGBA"
    mix_1.blend_type = "ADD"
    mix_1.inputs[0].default_value = float(np.random.uniform(0.8, 1.0))
    ln(colorramp_8.outputs["Color"], mix_1.inputs[6])   # A
    ln(colorramp_4.outputs["Color"], mix_1.inputs[7])   # B

    # colorramp_3: main color gradient (green HSV-based)
    hsv_base = [float(np.random.uniform(0.28, 0.36)),
                float(np.random.uniform(0.35, 0.80)),
                float(np.random.uniform(0.20, 0.45))]
    color_light = hsv2rgba(hsv_base)

    hsv_dark = list(hsv_base)
    hsv_dark[2] = float(np.random.uniform(0.03, 0.07))
    hsv_dark[1] = float(np.random.uniform(0.5, 0.8))
    hsv_dark[0] += float(np.random.normal(0, 0.015))
    color_dark = hsv2rgba(hsv_dark)

    colorramp_3 = nt.nodes.new("ShaderNodeValToRGB")
    ln(mix_1.outputs[2], colorramp_3.inputs["Fac"])   # outputs[2] = Result for RGBA mix
    colorramp_3.color_ramp.elements[0].position = 0.0
    colorramp_3.color_ramp.elements[0].color = color_light
    colorramp_3.color_ramp.elements[1].position = 1.0
    colorramp_3.color_ramp.elements[1].color = color_dark

    # mix: blend between tip/edge color and main body color
    # Blender 5.0: ShaderNodeMix RGBA
    tip_color_hsv = (float(np.random.uniform(0.16, 0.23)),
                     float(np.random.uniform(0.8, 0.95)),
                     float(np.random.uniform(0.35, 0.8)))
    tip_color = colorsys.hsv_to_rgb(*tip_color_hsv)

    mix_final = nt.nodes.new("ShaderNodeMix")
    mix_final.data_type = "RGBA"
    mix_final.blend_type = "MIX"
    ln(colorramp_1.outputs["Color"], mix_final.inputs[0])   # Factor
    mix_final.inputs[6].default_value = (*tip_color, 1.0)   # Color1 (A)
    ln(colorramp_3.outputs["Color"], mix_final.inputs[7])   # Color2 (B)

    # principled_bsdf
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_final.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(8.0, 15.0))
    # Coat Roughness = 0 (Blender 4.x+ has this input)
    coat_rough = bsdf.inputs.get("Coat Roughness")
    if coat_rough is not None:
        coat_rough.default_value = 0.0

    # material_output
    mat_out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], mat_out.inputs["Surface"])

    return mat

# ── Phase 1: Material sampling on raw SEED ───────────────────────────────────

SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)

MAT_SNAKE_PLANT = make_snake_plant_material("SnakePlantMaterial")
MAT_SNAKE_PLANT.use_fake_user = True

# ── Geometry (verbatim from objects_blender/small_plants/SnakePlantFactory.py) ─

np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)

# --------------- helpers ---------------
def assign_curve(fc_node, points):
    """Set control points on a ShaderNodeFloatCurve node."""

    curve = fc_node.mapping.curves[0]
    for i, (x, y) in enumerate(points):
        if i < len(curve.points):
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
    fc_node.mapping.update()

def check_vicinity(param, petal_params):
    """Check if a new petal would overlap existing ones."""

    for p in petal_params:
        r1 = max(param[0] * np.sin(param[1]), 0.2)
        r2 = max(p[0] * np.sin(p[1]), 0.2)
        dist = np.linalg.norm([param[2] - p[2], param[3] - p[3]])
        if r1 + r2 > dist:
            return True
    return False

# --------------- build geometry nodes ---------------
def build_snake_plant_ng(num_petals):
    """Build the complete snake plant geometry nodes tree.

    Each petal pipeline (inlined):
      QuadraticBezier -> X-rotation curl -> CaptureAttribute(spline factor)
      -> CaptureAttribute(normal) -> width profile -> SetPosition -> CurveToMesh
      -> ExtrudeMesh(EDGES, normal, width) -> Z-twist -> ExtrudeMesh(FACES, thickness)
#       -> SubdivisionSurface -> SetShadeSmooth -> 3x Transform (scale/rotate/translate)
    All petals -> JoinGeometry
    """
    # Generate non-overlapping petal placement params
    """
    """

    petal_params = []
    c = 0
    while c < 50 and len(petal_params) < num_petals:
        c += 1
        scale = uniform(0.7, 1.0)
        x_rotation = normal(0, 0.15)
        x, y = uniform(-0.7, 0.7), uniform(-0.7, 0.7)
        param = (scale, x_rotation, x, y)
        if check_vicinity(param, petal_params):
            continue
        petal_params.append(param)

    # Create node group
    ng = bpy.data.node_groups.new('SnakePlantGeometry', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    petal_finals = []

    for param in petal_params:
        p_scale = param[0]
        p_x_rot = param[1]
        p_x, p_y = param[2], param[3]
        p_z_rot = uniform(0, 6.28)
        p_z2_rot = uniform(0, 6.28)

        # ===== SETUP: QuadraticBezier + X rotation curl + CaptureAttribute =====

        qb = ng.nodes.new('GeometryNodeCurveQuadraticBezier')
        qb.inputs[0].default_value = 25                                       # Resolution
        qb.inputs[1].default_value = (0.0, 0.0, 0.0)                          # Start
        qb.inputs[2].default_value = (0.0, 0.0, 1.0)                          # Middle
        qb.inputs[3].default_value = (uniform(-0.2, 0.2), 0.2, 2.0)           # End

        # X petal rotation: curl based on spline parameter
        pos_x = ng.nodes.new('GeometryNodeInputPosition')
        sp_x = ng.nodes.new('GeometryNodeSplineParameter')
        mul_xr = ng.nodes.new('ShaderNodeMath')
        mul_xr.operation = 'MULTIPLY'
        mul_xr.inputs[0].default_value = 0.5
        ng.links.new(sp_x.outputs[0], mul_xr.inputs[1])         # Factor

        vr_x = ng.nodes.new('ShaderNodeVectorRotate')
        vr_x.rotation_type = 'X_AXIS'
        ng.links.new(pos_x.outputs[0], vr_x.inputs[0])          # Vector
        ng.links.new(mul_xr.outputs[0], vr_x.inputs[3])         # Angle

        sp_xr = ng.nodes.new('GeometryNodeSetPosition')
        ng.links.new(qb.outputs[0], sp_xr.inputs[0])            # Geometry
        ng.links.new(vr_x.outputs[0], sp_xr.inputs[3])          # Offset

        # CaptureAttribute: store spline parameter factor
        sp_cap = ng.nodes.new('GeometryNodeSplineParameter')
        ca_sp = ng.nodes.new('GeometryNodeCaptureAttribute')
        ca_sp.capture_items.new('FLOAT', 'Value')
        ng.links.new(sp_xr.outputs[0], ca_sp.inputs[0])         # Geometry
        ng.links.new(sp_cap.outputs[0], ca_sp.inputs[1])         # Value (Factor)

        # ===== EDGE EXTRUSION: capture normal + width profile + CurveToMesh + extrude =====

        inp_norm = ng.nodes.new('GeometryNodeInputNormal')
        ca_n = ng.nodes.new('GeometryNodeCaptureAttribute')
        ca_n.capture_items.new('VECTOR', 'Normal')
        ng.links.new(ca_sp.outputs[0], ca_n.inputs[0])           # Geometry
        ng.links.new(inp_norm.outputs[0], ca_n.inputs[1])        # Normal vector

        # Width profile FloatCurve
        init_w = uniform(0.15, 0.3)
        fc_w = ng.nodes.new('ShaderNodeFloatCurve')
        ng.links.new(ca_sp.outputs[1], fc_w.inputs[1])           # spline factor -> Value
        assign_curve(fc_w, [
            (0.0, init_w),
            (0.25, init_w + uniform(0.0, 0.1)),
            (0.50, init_w + uniform(0.02, 0.18)),
            (0.75, init_w + uniform(0.02, 0.1)),
            (1.0, 0.0),
        ])

        cxyz_w = ng.nodes.new('ShaderNodeCombineXYZ')
        ng.links.new(fc_w.outputs[0], cxyz_w.inputs[0])         # X = width

        sp_w = ng.nodes.new('GeometryNodeSetPosition')
        ng.links.new(ca_n.outputs[0], sp_w.inputs[0])            # Geometry
        ng.links.new(cxyz_w.outputs[0], sp_w.inputs[3])          # Offset

        c2m = ng.nodes.new('GeometryNodeCurveToMesh')
        ng.links.new(sp_w.outputs[0], c2m.inputs[0])             # Curve

        ext_e = ng.nodes.new('GeometryNodeExtrudeMesh')
        ext_e.mode = 'EDGES'
        ng.links.new(c2m.outputs[0], ext_e.inputs[0])            # Mesh
        ng.links.new(ca_n.outputs[1], ext_e.inputs[2])           # Offset (captured normal)
        ng.links.new(fc_w.outputs[0], ext_e.inputs[3])           # Offset Scale (width)

        # ===== FACE EXTRUSION: Z twist + thickness =====

        # Z petal rotation (twist)
        pos_z = ng.nodes.new('GeometryNodeInputPosition')
        fc_twist = ng.nodes.new('ShaderNodeFloatCurve')
        ng.links.new(ca_sp.outputs[1], fc_twist.inputs[1])       # spline factor -> Value
        assign_curve(fc_twist, [
            (0.0, 0.0),
            (0.25, 0.25 + uniform(-0.1, 0.1)),
            (0.50, 0.5 + uniform(-0.15, 0.15)),
            (0.75, 0.75),
            (1.0, 1.0),
        ])

        mul_twist = ng.nodes.new('ShaderNodeMath')
        mul_twist.operation = 'MULTIPLY'
        mul_twist.inputs[1].default_value = uniform(0.8, 2.0)
        ng.links.new(fc_twist.outputs[0], mul_twist.inputs[0])

        vr_z = ng.nodes.new('ShaderNodeVectorRotate')
        vr_z.rotation_type = 'Z_AXIS'
        ng.links.new(pos_z.outputs[0], vr_z.inputs[0])           # Vector
        ng.links.new(mul_twist.outputs[0], vr_z.inputs[3])       # Angle

        sp_tw = ng.nodes.new('GeometryNodeSetPosition')
        ng.links.new(ext_e.outputs[0], sp_tw.inputs[0])          # Mesh
        ng.links.new(vr_z.outputs[0], sp_tw.inputs[3])           # Offset

        # Petal thickness: MapRange [0.2 -> 0.04] * random thickness
        mr_th = ng.nodes.new('ShaderNodeMapRange')
        mr_th.inputs[3].default_value = 0.2                       # To Min
        mr_th.inputs[4].default_value = 0.04                      # To Max
        ng.links.new(ca_sp.outputs[1], mr_th.inputs[0])           # spline factor

        val_th = ng.nodes.new('ShaderNodeValue')
        val_th.outputs[0].default_value = uniform(0.1, 0.35)

        mul_th = ng.nodes.new('ShaderNodeMath')
        mul_th.operation = 'MULTIPLY'
        ng.links.new(mr_th.outputs[0], mul_th.inputs[0])
        ng.links.new(val_th.outputs[0], mul_th.inputs[1])

        ext_f = ng.nodes.new('GeometryNodeExtrudeMesh')
        ext_f.mode = 'FACES'
        ng.links.new(sp_tw.outputs[0], ext_f.inputs[0])           # Mesh
        ng.links.new(mul_th.outputs[0], ext_f.inputs[3])           # Offset Scale
        ext_f.inputs[4].default_value = False                      # Individual = False

        # ===== POST-PROCESSING: SubdivisionSurface + SetShadeSmooth =====

        subdiv = ng.nodes.new('GeometryNodeSubdivisionSurface')
        subdiv.inputs[1].default_value = 2
        ng.links.new(ext_f.outputs[0], subdiv.inputs[0])

        smooth = ng.nodes.new('GeometryNodeSetShadeSmooth')
        ng.links.new(subdiv.outputs[0], smooth.inputs[0])

        # ===== TRANSFORMS: scale+z_rot -> x_rot -> z2_rot+translate =====

        tf1 = ng.nodes.new('GeometryNodeTransform')
        tf1.inputs[4].default_value = (p_scale, p_scale, p_scale)  # Scale
        tf1.inputs[3].default_value = (0.0, 0.0, p_z_rot)          # Rotation
        ng.links.new(smooth.outputs[0], tf1.inputs[0])

        tf2 = ng.nodes.new('GeometryNodeTransform')
        tf2.inputs[3].default_value = (p_x_rot, 0.0, 0.0)          # Rotation
        ng.links.new(tf1.outputs[0], tf2.inputs[0])

        tf3 = ng.nodes.new('GeometryNodeTransform')
        tf3.inputs[3].default_value = (0.0, 0.0, p_z2_rot)          # Rotation
        tf3.inputs[2].default_value = (p_x, p_y, 0.0)               # Translation
        ng.links.new(tf2.outputs[0], tf3.inputs[0])

        petal_finals.append(tf3)

    # Join all petals
    join = ng.nodes.new('GeometryNodeJoinGeometry')
    for pf in petal_finals:
        ng.links.new(pf.outputs[0], join.inputs[0])

    ng.links.new(join.outputs[0], go.inputs[0])
    return ng

# --------------- make_snake_plant ---------------
def make_snake_plant():
    bpy.ops.mesh.primitive_plane_add(
        size=1, enter_editmode=False, align='WORLD',
        location=(0, 0, 0), scale=(1, 1, 1),
    )
    obj = bpy.context.active_object

    petal_num = randint(4, 8)
    tree = build_snake_plant_ng(petal_num)

    mod = obj.modifiers.new('SnakePlant', 'NODES')
    mod.node_group = tree

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    obj.scale = (0.2, 0.2, 0.2)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # --- Append material (clear any leftover empty slots first) ---
    obj.data.materials.clear()
    obj.data.materials.append(MAT_SNAKE_PLANT)

    obj.name = "SnakePlantFactory"
    return obj

make_snake_plant()

