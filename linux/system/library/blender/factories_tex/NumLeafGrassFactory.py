# [FL_INDEX: keywords="blender_factory, procedural_3d, NumLeafGrassFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: NumLeafGrassFactory | Category: factories_tex
# Prompt: A 3D model of a small clover-like plant rendered from an elevated perspective, featuring a thin upright cylindrical stem topped with several small rounded leaflets arranged in a radial cluster, colored in dark green with a simple low-poly style.

import os, math, colorsys, random
import bpy
import bmesh
import numpy as np
from numpy.random import normal, uniform, randint

# ──────────────────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────────────────

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1,
                                   max(0, min(1, float(s))),
                                   max(0, min(1, float(v))))
    return (r, g, b, 1.0)

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac(node):
    """Get Fac/Factor output from a texture node (Blender 5.0 compat)."""

    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

# ──────────────────────────────────────────────────────────
#
# Shader structure:
#   - 3x Noise Texture 4D (color fac, roughness fac, translucent fac)
#   - MapRange (smoothstep) on first noise -> mix factor for two plant_green colors
#   - MixRGB to blend two plant_green colors
#   - TranslucentBSDF with that color
#   - MapRange (smoothstep) on second noise -> roughness
#   - PrincipledBSDF with that color + roughness
#   - MapRange (smoothstep) on third noise -> fac for MixShader
#   - MixShader(translucent, principled)
# ──────────────────────────────────────────────────────────

def _plant_green():
    return (
        float(uniform(0.25, 0.33)),
        float(normal(0.65, 0.03)),
        float(uniform(0.1, 0.45)),
    )

def _make_noise_4d(node_tree):
    """Create a Noise Texture 4D node with randomized inputs, matching simple_greenery's noise()."""

    noise = node_tree.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["W"].default_value = float(uniform(0, 100))
    noise.inputs["Scale"].default_value = float(normal(60, 25))
    noise.inputs["Detail"].default_value = float(uniform(0, 10))
    noise.inputs["Roughness"].default_value = float(uniform(0, 1))
    noise.inputs["Distortion"].default_value = float(uniform(0, 3))
    return noise

def make_simple_greenery(name="SimpleGreenery"):
    """Faithful translation of shader_simple_greenery to raw bpy node tree."""

    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new

    # --- Noise 1: color mix factor ---
    noise_color = _make_noise_4d(nt)

    # MapRange (smoothstep) for color factor
    mr_color = nt.nodes.new("ShaderNodeMapRange")
    mr_color.interpolation_type = "SMOOTHSTEP"
    mr_color.inputs["From Min"].default_value = 0.0
    mr_color.inputs["From Max"].default_value = 1.0
    mr_color.inputs["To Min"].default_value = 0.0
    mr_color.inputs["To Max"].default_value = float(uniform(0.1, 1))
    ln(_fac(noise_color), mr_color.inputs["Value"])

    # Two plant_green colors
    color1_hsv = _plant_green()
    color2_hsv = _plant_green()
    color1_rgba = _hsv2rgba(*color1_hsv)
    color2_rgba = _hsv2rgba(*color2_hsv)

    # MixRGB to blend the two greens
    mix_color = nt.nodes.new("ShaderNodeMix")
    mix_color.data_type = "RGBA"
    mix_color.inputs[0].default_value = 0.0  # placeholder; driven by map range
    ln(mr_color.outputs["Result"], mix_color.inputs[0])
    mix_color.inputs[6].default_value = color1_rgba
    mix_color.inputs[7].default_value = color2_rgba

    # TranslucentBSDF
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    ln(mix_color.outputs[2], translucent.inputs["Color"])

    # --- Noise 2: roughness ---
    noise_rough = _make_noise_4d(nt)

    # MapRange (smoothstep) for roughness
    mr_rough = nt.nodes.new("ShaderNodeMapRange")
    mr_rough.interpolation_type = "SMOOTHSTEP"
    mr_rough.inputs["From Min"].default_value = 0.0
    mr_rough.inputs["From Max"].default_value = 1.0
    mr_rough.inputs["To Min"].default_value = float(uniform(0.1, 0.8))
    mr_rough.inputs["To Max"].default_value = float(uniform(0.1, 0.8))
    ln(_fac(noise_rough), mr_rough.inputs["Value"])

    # PrincipledBSDF
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_color.outputs[2], principled.inputs["Base Color"])
    ln(mr_rough.outputs["Result"], principled.inputs["Roughness"])

    # --- Noise 3: translucent mix factor ---
    noise_trans = _make_noise_4d(nt)

    # MapRange (smoothstep) for translucent factor
    mr_trans = nt.nodes.new("ShaderNodeMapRange")
    mr_trans.interpolation_type = "SMOOTHSTEP"
    mr_trans.inputs["From Min"].default_value = 0.0
    mr_trans.inputs["From Max"].default_value = 1.0
    mr_trans.inputs["To Min"].default_value = float(uniform(0.6, 0.9))
    mr_trans.inputs["To Max"].default_value = 1.0
    ln(_fac(noise_trans), mr_trans.inputs["Value"])

    # MixShader: blend translucent and principled
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    ln(mr_trans.outputs["Result"], mix_shader.inputs["Fac"])
    ln(translucent.outputs["BSDF"], mix_shader.inputs[1])
    ln(principled.outputs["BSDF"], mix_shader.inputs[2])

    # Output
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_shader.outputs["Shader"], output.inputs["Surface"])

    return mat

# ══════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════

SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)

MAT_GREENERY = make_simple_greenery(name="NumLeafGrass_SimpleGreenery")
MAT_GREENERY.use_fake_user = True

# No wear_tear in source for this factory.

# ══════════════════════════════════════════════════════════
# Geometry (copied verbatim from objects_blender/small_plants/NumLeafGrassFactory.py)
# ══════════════════════════════════════════════════════════

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)

def _make_leaf(genome=None):
    g = dict(leaf_width=0.5, alpha=0.3, use_wave=True, x_offset=0,
             flip_leaf=False, z_scaling=0, width_rand=0.33)
    if genome:
        g.update(genome)

    bpy.ops.mesh.primitive_circle_add(
        enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_face_add()
    obj = bpy.context.active_object
    n = len(obj.data.vertices) // 2

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.vertices[0].select = True
    obj.data.vertices[-1].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide()

    a = np.linspace(0, np.pi, n)
    if g['flip_leaf']:
        a = a[::-1]
    x = (np.sin(a) * (g['leaf_width'] + np.random.randn() * g['width_rand'])
         + g['x_offset'])
    y = -np.cos(0.9 * (a - g['alpha']))
    z = x ** 2 * g['z_scaling']
    full_coords = np.concatenate([
        np.stack([x, y, z], 1),
        np.stack([-x[::-1], y[::-1], z], 1),
        np.array([[0, y[0], 0]]),
    ]).flatten()
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.vertices.foreach_set('co', full_coords)

    if g['use_wave']:
        bpy.ops.object.modifier_add(type='WAVE')
        bpy.context.object.modifiers['Wave'].height = np.random.randn() * 0.3
        bpy.context.object.modifiers['Wave'].width = 0.75 + np.random.randn() * 0.1
        bpy.context.object.modifiers['Wave'].speed = np.random.rand()

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    bpy.context.scene.cursor.location = obj.data.vertices[-1].co
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.location = (0, 0, 0)
    obj.scale *= 0.3
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj

def _make_leaf_heart(genome=None):
    g = dict(leaf_width=1.0, use_wave=True, z_scaling=0, width_rand=0.1)
    if genome:
        g.update(genome)

    bpy.ops.mesh.primitive_circle_add(
        enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_face_add()
    obj = bpy.context.active_object
    n = len(obj.data.vertices) // 2

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.vertices[0].select = True
    obj.data.vertices[-1].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide()

    a = np.linspace(0, np.pi, n)
    x = (16.0 * (np.sin(a - np.pi) ** 3)
         * (g['leaf_width'] + np.random.randn() * g['width_rand']))
    y = (13.0 * np.cos(a - np.pi)
         - 5 * np.cos(2 * (a - np.pi))
         - 2 * np.cos(3 * (a - np.pi)))
    x, y = x * 0.3, y * 0.3
    z = x ** 2 * g['z_scaling']
    full_coords = np.concatenate([
        np.stack([x, y, z], 1),
        np.stack([-x[::-1], y[::-1], z], 1),
        np.array([[0, y[0], 0]]),
    ]).flatten()
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.vertices.foreach_set('co', full_coords)

    if g['use_wave']:
        bpy.ops.object.modifier_add(type='WAVE')
        bpy.context.object.modifiers['Wave'].height = 0.8 * np.random.randn() * 0.8
        bpy.context.object.modifiers['Wave'].width = 3.5 + np.random.randn() * 1.0
        bpy.context.object.modifiers['Wave'].speed = 40 + np.random.uniform(-10, 20)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    bpy.context.scene.cursor.location = obj.data.vertices[-1].co
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.location = (0, 0, 0)
    obj.scale *= 0.2
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj

# --------------- GeoNodes builder functions ---------------

def build_stem_geometry_ng():
    ng = bpy.data.node_groups.new("stem_geometry", 'GeometryNodeTree')
    ng.interface.new_socket('Curve', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Mesh', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    sp = ng.nodes.new('GeometryNodeSplineParameter')
    mr = ng.nodes.new('ShaderNodeMapRange')
    mr.inputs[3].default_value = 1.0
    mr.inputs[4].default_value = 0.4

    scr = ng.nodes.new('GeometryNodeSetCurveRadius')
    cc = ng.nodes.new('GeometryNodeCurvePrimitiveCircle')
    cc.inputs['Resolution'].default_value = 12
    cc.inputs['Radius'].default_value = 0.03

    c2m = ng.nodes.new('GeometryNodeCurveToMesh')
    c2m.inputs['Fill Caps'].default_value = True

    ng.links.new(sp.outputs['Factor'], mr.inputs['Value'])
    ng.links.new(gi.outputs['Curve'], scr.inputs['Curve'])
    ng.links.new(mr.outputs['Result'], scr.inputs['Radius'])
    ng.links.new(scr.outputs['Curve'], c2m.inputs['Curve'])
    ng.links.new(cc.outputs['Curve'], c2m.inputs['Profile Curve'])
    if 'Scale' in c2m.inputs:
        ng.links.new(mr.outputs['Result'], c2m.inputs['Scale'])
    ng.links.new(c2m.outputs['Mesh'], go.inputs['Mesh'])
    return ng

def build_leaf_on_stem_ng(name, z_rotation, leaf_scale, leaf_obj):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Points', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Instances', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    eps = ng.nodes.new('GeometryNodeCurveEndpointSelection')
    eps.inputs['Start Size'].default_value = 0

    oi = ng.nodes.new('GeometryNodeObjectInfo')
    oi.inputs['Object'].default_value = leaf_obj

    ct = ng.nodes.new('GeometryNodeInputTangent')
    aev = ng.nodes.new('FunctionNodeAlignEulerToVector')
    aev.axis = 'Z'

    val = ng.nodes.new('ShaderNodeValue')
    val.outputs[0].default_value = leaf_scale

    iop = ng.nodes.new('GeometryNodeInstanceOnPoints')

    vec = ng.nodes.new('FunctionNodeInputVector')
    vec.vector = z_rotation

    ri = ng.nodes.new('GeometryNodeRotateInstances')

    ng.links.new(ct.outputs['Tangent'], aev.inputs['Vector'])
    ng.links.new(gi.outputs['Points'], iop.inputs['Points'])
    ng.links.new(eps.outputs['Selection'], iop.inputs['Selection'])
    ng.links.new(oi.outputs['Geometry'], iop.inputs['Instance'])
    ng.links.new(aev.outputs['Rotation'], iop.inputs['Rotation'])
    ng.links.new(val.outputs['Value'], iop.inputs['Scale'])
    ng.links.new(iop.outputs['Instances'], ri.inputs['Instances'])
    ng.links.new(vec.outputs['Vector'], ri.inputs['Rotation'])
    ng.links.new(ri.outputs['Instances'], go.inputs['Instances'])
    return ng

def build_main_ng(leaf_obj, leaf_num, leaf_scale_factor, stem_rotation):
    ng = bpy.data.node_groups.new("num_leaf_grass_main", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    mid_z = float(uniform(0.35, 0.65))
    mid_x = float(normal(0.0, stem_rotation))
    mid_y = float(normal(0.0, stem_rotation))
    top_x = float(normal(0.0, stem_rotation))
    top_y = float(normal(0.0, stem_rotation))

    vec_mid = ng.nodes.new('FunctionNodeInputVector')
    vec_mid.vector = (mid_x, mid_y, mid_z)
    vec_top = ng.nodes.new('FunctionNodeInputVector')
    vec_top.vector = (top_x, top_y, 1.0)

    qb = ng.nodes.new('GeometryNodeCurveQuadraticBezier')
    qb.inputs['Resolution'].default_value = 25
    qb.inputs['Start'].default_value = (0.0, 0.0, 0.0)
    ng.links.new(vec_mid.outputs['Vector'], qb.inputs['Middle'])
    ng.links.new(vec_top.outputs['Vector'], qb.inputs['End'])

    nt = ng.nodes.new('ShaderNodeTexNoise')
    nt.inputs['Scale'].default_value = 1.0
    nt.inputs['Roughness'].default_value = 0.2

    offset_vec = ng.nodes.new('FunctionNodeInputVector')
    offset_vec.vector = (-0.5, -0.5, -0.5)

    vm_add = ng.nodes.new('ShaderNodeVectorMath')
    vm_add.operation = 'ADD'
    ng.links.new(nt.outputs[0], vm_add.inputs[0])
    ng.links.new(offset_vec.outputs['Vector'], vm_add.inputs[1])

    sp = ng.nodes.new('GeometryNodeSplineParameter')
    vm_mul = ng.nodes.new('ShaderNodeVectorMath')
    vm_mul.operation = 'MULTIPLY'
    ng.links.new(vm_add.outputs['Vector'], vm_mul.inputs[0])
    ng.links.new(sp.outputs['Factor'], vm_mul.inputs[1])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(qb.outputs['Curve'], set_pos.inputs['Geometry'])
    ng.links.new(vm_mul.outputs['Vector'], set_pos.inputs['Offset'])

    stem_ng = build_stem_geometry_ng()
    stem_grp = ng.nodes.new('GeometryNodeGroup')
    stem_grp.node_tree = stem_ng
    ng.links.new(set_pos.outputs['Geometry'], stem_grp.inputs['Curve'])

    leaf_scale = float(uniform(0.15, 0.35)) * leaf_scale_factor
    leaf_groups = []
    rotation = 0.0
    for i in range(leaf_num):
        leaf_ng = build_leaf_on_stem_ng(
            f"leaf_on_stem_{i}", (0, 0, rotation), leaf_scale, leaf_obj)
        leaf_grp = ng.nodes.new('GeometryNodeGroup')
        leaf_grp.node_tree = leaf_ng
        ng.links.new(set_pos.outputs['Geometry'], leaf_grp.inputs['Points'])
        leaf_groups.append(leaf_grp)
        rotation += 6.28 / leaf_num

    jg = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(stem_grp.outputs['Mesh'], jg.inputs['Geometry'])
    for lg in leaf_groups:
        ng.links.new(lg.outputs['Instances'], jg.inputs['Geometry'])

    ri = ng.nodes.new('GeometryNodeRealizeInstances')
    ng.links.new(jg.outputs['Geometry'], ri.inputs['Geometry'])
    ng.links.new(ri.outputs['Geometry'], go.inputs['Geometry'])
    return ng

# --------------- main creation ---------------

def make_num_leaf_grass():
    bpy.ops.mesh.primitive_plane_add(
        size=1, enter_editmode=False, align='WORLD',
        location=(0, 0, 0), scale=(1, 1, 1))
    obj = bpy.context.active_object

    lf_seed = int(randint(0, 1000))
    leaf_num = int(np.random.choice([2, 3, 4], p=[0.2, 0.4, 0.4]))
    z_offset = float(normal(0, 0.05))

    if leaf_num == 2:
        leaf = _make_leaf(genome={'leaf_width': 0.95, 'width_rand': 0.1, 'z_scaling': z_offset})
        leaf_scale_factor = 2.0
    elif leaf_num == 3:
        leaf = _make_leaf_heart(genome={'leaf_width': 1.1, 'width_rand': 0.05, 'z_scaling': z_offset})
        leaf_scale_factor = 1.0
    else:
        leaf = _make_leaf_heart(genome={'leaf_width': 0.85, 'width_rand': 0.05, 'z_scaling': z_offset})
        leaf_scale_factor = 1.0

    main_ng = build_main_ng(leaf, leaf_num, leaf_scale_factor, stem_rotation=0.15)

    mod = obj.modifiers.new("NumLeafGrass", 'NODES')
    mod.node_group = main_ng
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    bpy.data.objects.remove(leaf, do_unlink=True)

    # --- Material assignment (single material for entire plant) ---
    obj.data.materials.clear()
    obj.data.materials.append(MAT_GREENERY)

    return obj

make_num_leaf_grass()

