# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafMapleFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafMapleFactory | Category: factories_tex
# Prompt: A 3D model of a maple leaf rendered from a three-quarter perspective. The leaf features a palmate shape with multiple pointed lobes radiating from a central point, serrated edges along each lobe with sharp teeth, a long petiole stem, and a gently undulating three-dimensional surface with visible veins extending into each lobe.

import os
SEED = int(os.environ.get('SEED', 0))
import bpy
import numpy as np
import random
import hashlib
from numpy.random import normal, uniform
from mathutils import Color

C = bpy.context
D = bpy.data

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

def make_category_mat(seed, name="LeafMaterial"):
    """Leaf: color from colors.plant_green/yellow/red distribution.
    80% plant_green, 10% plant_yellow, 10% plant_red."""

    t = float(np.random.uniform(0.0, 1.0))
    if t < 0.8:
        base_hue = float(np.random.uniform(0.25, 0.33))
        sat = float(np.clip(np.random.normal(0.65, 0.03), 0, 1))
        val = float(np.random.uniform(0.1, 0.45))
    elif t < 0.9:
        base_hue = float(np.random.normal(0.15, 0.005)) % 1.0
        sat = float(np.clip(np.random.normal(0.95, 0.02), 0, 1))
        val = float(np.clip(np.random.normal(0.9, 0.02), 0, 1))
    else:
        base_hue = float(np.random.normal(0.0, 0.05)) % 1.0
        sat = float(np.clip(np.random.normal(0.9, 0.03), 0, 1))
        val = float(np.clip(np.random.normal(0.6, 0.05), 0, 1))
    vein_val = max(val - 0.1, 0.05)
    base_c = _hsv2rgba(base_hue, sat, val)
    vein_c = _hsv2rgba(base_hue + float(np.random.uniform(-0.03, 0.03)),
                        sat * 0.7, vein_val)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(np.random.uniform(5, 20))
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.color_mode = "HSV"
    cr.color_ramp.hue_interpolation = "NEAR"
    ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = vein_c
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = base_c
    # 20% glossy + 30% translucent + 50% diffuse (matches leaf_shader mix weights)
    glossy = nt.nodes.new("ShaderNodeBsdfGlossy"); glossy.inputs["Roughness"].default_value = 0.3
    ln(cr.outputs["Color"], glossy.inputs["Color"])
    trans = nt.nodes.new("ShaderNodeBsdfTranslucent"); ln(cr.outputs["Color"], trans.inputs["Color"])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.5
    mix1 = nt.nodes.new("ShaderNodeMixShader"); mix1.inputs["Fac"].default_value = 0.2
    ln(bsdf.outputs["BSDF"], mix1.inputs[1]); ln(glossy.outputs["BSDF"], mix1.inputs[2])
    mix2 = nt.nodes.new("ShaderNodeMixShader"); mix2.inputs["Fac"].default_value = 0.3
    ln(mix1.outputs["Shader"], mix2.inputs[1]); ln(trans.outputs["BSDF"], mix2.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial"); ln(mix2.outputs["Shader"], out.inputs["Surface"])
    return mat

CATEG_MAT = make_category_mat(SEED, "LeafFactoryMaple_Material")
CATEG_MAT.use_fake_user = True

class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
        self.py_state = None
        self.np_state = None
    def __enter__(self):
        self.py_state = random.getstate()
        self.np_state = np.random.get_state()
        random.seed(self.seed)
        np.random.seed(self.seed)
    def __exit__(self, *_):
        random.setstate(self.py_state)
        np.random.set_state(self.np_state)

def md5_hash(x):
    if isinstance(x, (tuple, list)):
        m = hashlib.md5()
        for s in x:
            m.update(str(s).encode('utf-8'))
        return m
    return hashlib.md5(str(x).encode('utf-8'))

def int_hash(x, max=(2**32 - 1)):
    return abs(int(md5_hash(x).hexdigest(), 16)) % max

def hsv2rgba(hsv, *args):
    if len(args) > 0:
        hsv = (hsv, *args)
    c = Color()
    c.hsv = (float(hsv[0]) % 1.0, float(hsv[1]), float(hsv[2]))
    return np.array([c.r, c.g, c.b, 1.0])

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)

def apply_transform(obj):
    _select_none(); _set_active(obj)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    _select_none()

def tag_object(obj, tag):
    return obj

# ---------------------------------------------------------------------------
# Helper: assign curve control points
# ---------------------------------------------------------------------------
def _assign_curve(curve_mapping_curve, points, handles=None):
    for i, p in enumerate(points):
        if i < 2:
            curve_mapping_curve.points[i].location = p
        else:
            curve_mapping_curve.points.new(*p)
        if handles is not None:
            curve_mapping_curve.points[i].handle_type = handles[i]

# ---------------------------------------------------------------------------
# Helper: set default value on a socket, handling ndarray/tuple conversion
# ---------------------------------------------------------------------------
def _set_default(socket, value):
    if value is None:
        return
    try:
        socket.default_value = value
    except Exception:
        if isinstance(value, np.ndarray):
            socket.default_value = value.tolist()
        elif isinstance(value, (tuple, list)):
            socket.default_value = tuple(value)
        else:
            raise

def deg2rad(deg):
    return deg / 180.0 * np.pi

# Node-group builder functions (direct bpy API, no NodeWrangler)

def make_vein():
    """nodegroup_vein: per-midrib vein pattern using 1D Voronoi."""

    ng = bpy.data.node_groups.new("nodegroup_vein", 'GeometryNodeTree')
    ng.interface.new_socket('Vector', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Length', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Start', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Anneal', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Phase Offset', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Vector':
                item.default_value = (0.0, 0.0, 0.0)
            elif item.name == 'Anneal':
                item.default_value = 0.4
    ng.interface.new_socket('Result', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # abs(X Modulated)
    absolute = ng.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'
    ng.links.new(inp.outputs['X Modulated'], absolute.inputs[0])

    # separate Vector
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(inp.outputs['Vector'], sep.inputs['Vector'])

    # combine (abs, Y, Z)
    comb1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(absolute.outputs[0], comb1.inputs['X'])
    ng.links.new(sep.outputs['Y'], comb1.inputs['Y'])
    ng.links.new(sep.outputs['Z'], comb1.inputs['Z'])

    # vector rotate comb1 by Angle around Z
    vrot = ng.nodes.new('ShaderNodeVectorRotate'); vrot.rotation_type = 'Z_AXIS'
    ng.links.new(comb1.outputs[0], vrot.inputs['Vector'])
    ng.links.new(inp.outputs['Angle'], vrot.inputs['Angle'])

    # separate rotated
    sep3 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(vrot.outputs[0], sep3.inputs['Vector'])

    # separate unrotated (comb1)
    sep1 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(comb1.outputs[0], sep1.inputs['Vector'])

    # map_range_1: sep1.X -> [0, 0.3] -> [0, 1]
    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(sep1.outputs['X'], mr1.inputs['Value'])
    mr1.inputs[2].default_value = 0.3

    # float curve
    fc = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr1.outputs['Result'], fc.inputs['Value'])
    _assign_curve(fc.mapping.curves[0], [(0.0, 0.0), (0.5932, 0.1969), (1.0, 1.0)])

    # multiply float_curve * 0.2
    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(fc.outputs[0], mul.inputs[0])
    mul.inputs[1].default_value = 0.2

    # add sep3.X + mul
    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(sep3.outputs['X'], add.inputs[0])
    ng.links.new(mul.outputs[0], add.inputs[1])

    # sign(X Modulated)
    sign = ng.nodes.new('ShaderNodeMath'); sign.operation = 'SIGN'
    ng.links.new(inp.outputs['X Modulated'], sign.inputs[0])

    # sign * 0.1
    mul1 = ng.nodes.new('ShaderNodeMath'); mul1.operation = 'MULTIPLY'
    ng.links.new(sign.outputs[0], mul1.inputs[0])
    mul1.inputs[1].default_value = 0.1

    # add_1 = add + mul1
    add1 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(add.outputs[0], add1.inputs[0])
    ng.links.new(mul1.outputs[0], add1.inputs[1])

    # add_2 = add_1 + Phase Offset
    add2 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(add1.outputs[0], add2.inputs[0])
    ng.links.new(inp.outputs['Phase Offset'], add2.inputs[1])

    # voronoi 1D
    vor = ng.nodes.new('ShaderNodeTexVoronoi'); vor.voronoi_dimensions = '1D'
    ng.links.new(add2.outputs[0], vor.inputs['W'])
    vor.inputs['Scale'].default_value = 8.0
    vor.inputs['Randomness'].default_value = 0.7125

    # length of rotated vector
    length = ng.nodes.new('ShaderNodeVectorMath'); length.operation = 'LENGTH'
    ng.links.new(vrot.outputs[0], length.inputs[0])

    # multiply_2 = 0.05 * length, clamped
    mul2 = ng.nodes.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'; mul2.use_clamp = True
    mul2.inputs[0].default_value = 0.05
    ng.links.new(length.outputs['Value'], mul2.inputs[1])

    # subtract = 0.08 - mul2, clamped
    sub = ng.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; sub.use_clamp = True
    sub.inputs[0].default_value = 0.08
    ng.links.new(mul2.outputs[0], sub.inputs[1])

    # map_range: vor.Distance -> [0, sub] -> [1, 0]
    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(vor.outputs['Distance'], mr.inputs['Value'])
    ng.links.new(sub.outputs[0], mr.inputs[2])
    mr.inputs[3].default_value = 1.0
    mr.inputs[4].default_value = 0.0

    # abs(X Modulated) again
    abs1 = ng.nodes.new('ShaderNodeMath'); abs1.operation = 'ABSOLUTE'
    ng.links.new(inp.outputs['X Modulated'], abs1.inputs[0])

    # subtract_1 = sep1.Y - 0.0
    sub1 = ng.nodes.new('ShaderNodeMath'); sub1.operation = 'SUBTRACT'
    ng.links.new(sep1.outputs['Y'], sub1.inputs[0])
    sub1.inputs[1].default_value = 0.0

    # multiply_3 = sub1 * Anneal
    mul3 = ng.nodes.new('ShaderNodeMath'); mul3.operation = 'MULTIPLY'
    ng.links.new(sub1.outputs[0], mul3.inputs[0])
    ng.links.new(inp.outputs['Anneal'], mul3.inputs[1])

    # less_than = abs1 < mul3
    lt = ng.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
    ng.links.new(abs1.outputs[0], lt.inputs[0])
    ng.links.new(mul3.outputs[0], lt.inputs[1])

    # multiply_4 = mr.Result * lt
    mul4 = ng.nodes.new('ShaderNodeMath'); mul4.operation = 'MULTIPLY'
    ng.links.new(mr.outputs['Result'], mul4.inputs[0])
    ng.links.new(lt.outputs[0], mul4.inputs[1])

    # less_than_1 = add < Start
    lt1 = ng.nodes.new('ShaderNodeMath'); lt1.operation = 'LESS_THAN'
    ng.links.new(add.outputs[0], lt1.inputs[0])
    ng.links.new(inp.outputs['Start'], lt1.inputs[1])

    # multiply_5 = mul4 * lt1
    mul5 = ng.nodes.new('ShaderNodeMath'); mul5.operation = 'MULTIPLY'
    ng.links.new(mul4.outputs[0], mul5.inputs[0])
    ng.links.new(lt1.outputs[0], mul5.inputs[1])

    ng.links.new(mul5.outputs[0], out.inputs['Result'])
    return ng

def make_nodegroup_sub_vein():
    """nodegroup_nodegroup_sub_vein: sub-vein pattern using Voronoi textures."""

    ng = bpy.data.node_groups.new("nodegroup_nodegroup_sub_vein", 'GeometryNodeTree')
    ng.interface.new_socket('X', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X': item.default_value = 0.5
            elif item.name == 'Y': item.default_value = 0.0
    ng.interface.new_socket('Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Color Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # abs(X)
    abs_n = ng.nodes.new('ShaderNodeMath'); abs_n.operation = 'ABSOLUTE'
    ng.links.new(inp.outputs['X'], abs_n.inputs[0])

    # combine (abs, Y)
    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(abs_n.outputs[0], comb.inputs['X'])
    ng.links.new(inp.outputs['Y'], comb.inputs['Y'])

    # noise texture
    noise = ng.nodes.new('ShaderNodeTexNoise')
    ng.links.new(comb.outputs[0], noise.inputs['Vector'])

    # mix rgb
    mix = ng.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['Fac'].default_value = 0.9
    ng.links.new(noise.outputs['Color'], mix.inputs['Color1'])
    ng.links.new(comb.outputs[0], mix.inputs['Color2'])

    # voronoi scale=30
    vor = ng.nodes.new('ShaderNodeTexVoronoi')
    ng.links.new(mix.outputs[0], vor.inputs['Vector'])
    vor.inputs['Scale'].default_value = 30.0

    # map_range: vor.Distance -> [0, 0.1] -> [0, 2.0], no clamp
    mr = ng.nodes.new('ShaderNodeMapRange'); mr.clamp = False
    ng.links.new(vor.outputs['Distance'], mr.inputs['Value'])
    mr.inputs[2].default_value = 0.1
    mr.inputs[4].default_value = 2.0

    # voronoi_1: DISTANCE_TO_EDGE, scale=150
    vor1 = ng.nodes.new('ShaderNodeTexVoronoi'); vor1.feature = 'DISTANCE_TO_EDGE'
    ng.links.new(mix.outputs[0], vor1.inputs['Vector'])
    vor1.inputs['Scale'].default_value = 150.0

    # map_range_1: vor1.Distance -> [0, 0.1] -> [0, 1]
    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(vor1.outputs['Distance'], mr1.inputs['Value'])
    mr1.inputs[2].default_value = 0.1

    # add = mr.Result + mr1.Result
    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(mr.outputs['Result'], add.inputs[0])
    ng.links.new(mr1.outputs['Result'], add.inputs[1])

    # multiply = add * -1.0
    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(add.outputs[0], mul.inputs[0])
    mul.inputs[1].default_value = -1.0

    # map_range_3: mr1.Result -> [0, 1] -> [0, -1.0]
    mr3 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(mr1.outputs['Result'], mr3.inputs['Value'])
    mr3.inputs[4].default_value = -1.0

    ng.links.new(mul.outputs[0], out.inputs['Value'])
    ng.links.new(mr3.outputs['Result'], out.inputs['Color Value'])
    return ng

def make_node_group_002():
    """nodegroup_node_group_002: displacement from leaf shape (position length)."""

    ng = bpy.data.node_groups.new("nodegroup_node_group_002", 'GeometryNodeTree')
    ng.interface.new_socket('Shape', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and item.name == 'Shape':
            item.default_value = 0.5
    ng.interface.new_socket('Result', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    position = ng.nodes.new('GeometryNodeInputPosition')

    length = ng.nodes.new('ShaderNodeVectorMath'); length.operation = 'LENGTH'
    ng.links.new(position.outputs[0], length.inputs[0])

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(length.outputs['Value'], mul.inputs[0])
    ng.links.new(inp.outputs['Shape'], mul.inputs[1])

    mr = ng.nodes.new('ShaderNodeMapRange'); mr.clamp = False
    ng.links.new(mul.outputs[0], mr.inputs['Value'])
    mr.inputs[1].default_value = -1.0
    mr.inputs[2].default_value = 0.0
    mr.inputs[3].default_value = -0.1
    mr.inputs[4].default_value = 0.1

    ng.links.new(mr.outputs['Result'], out.inputs['Result'])
    return ng

def make_midrib():
    """nodegroup_midrib: midrib vein structure with rotation and sub-vein."""

    ng = bpy.data.node_groups.new("nodegroup_midrib", 'GeometryNodeTree')
    ng.interface.new_socket('Vector', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('vein Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('vein Length', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('vein Start', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Anneal', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Phase Offset', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Angle': item.default_value = 0.8238
            elif item.name == 'vein Angle': item.default_value = 0.7854
            elif item.name == 'vein Length': item.default_value = 0.2
            elif item.name == 'vein Start': item.default_value = -0.2
            elif item.name == 'Anneal': item.default_value = 0.4
    ng.interface.new_socket('Result', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vector', in_out='OUTPUT', socket_type='NodeSocketVector')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # Vector rotate by Angle around Z
    vrot1 = ng.nodes.new('ShaderNodeVectorRotate'); vrot1.rotation_type = 'Z_AXIS'
    ng.links.new(inp.outputs['Vector'], vrot1.inputs['Vector'])
    ng.links.new(inp.outputs['Angle'], vrot1.inputs['Angle'])

    # separate rotated
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(vrot1.outputs[0], sep.inputs['Vector'])

    # map range: Y -> [0, 1]
    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(sep.outputs['Y'], mr1.inputs['Value'])

    # float curve (midrib wobble)
    fc = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr1.outputs['Result'], fc.inputs['Value'])
    _assign_curve(fc.mapping.curves[0], [
        (0.0, 0.5), (0.1432, 0.5406), (0.2591, 0.5062), (0.3705, 0.5406),
        (0.4591, 0.425), (0.5932, 0.4562), (0.7432, 0.3562), (0.8727, 0.5062), (1.0, 0.5),
    ])

    # value = 0.1
    val = ng.nodes.new('ShaderNodeValue')
    val.outputs[0].default_value = 0.1

    # multiply = fc * value
    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(fc.outputs[0], mul.inputs[0])
    ng.links.new(val.outputs[0], mul.inputs[1])

    # add = sep.X + mul
    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(sep.outputs['X'], add.inputs[0])
    ng.links.new(mul.outputs[0], add.inputs[1])

    # multiply_1 = value * value (default inputs[1] = 0.5)
    mul1 = ng.nodes.new('ShaderNodeMath'); mul1.operation = 'MULTIPLY'
    ng.links.new(val.outputs[0], mul1.inputs[0])
    # inputs[1] defaults to 0.5

    # subtract = add - mul1
    sub = ng.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
    ng.links.new(add.outputs[0], sub.inputs[0])
    ng.links.new(mul1.outputs[0], sub.inputs[1])

    # Create vein sub-group
    vein_ng = make_vein()
    vein = ng.nodes.new('GeometryNodeGroup')
    vein.node_tree = vein_ng
    ng.links.new(vrot1.outputs[0], vein.inputs['Vector'])
    ng.links.new(inp.outputs['vein Angle'], vein.inputs['Angle'])
    ng.links.new(inp.outputs['vein Length'], vein.inputs['Length'])
    ng.links.new(inp.outputs['vein Start'], vein.inputs['Start'])
    ng.links.new(sub.outputs[0], vein.inputs['X Modulated'])
    ng.links.new(inp.outputs['Anneal'], vein.inputs['Anneal'])
    ng.links.new(inp.outputs['Phase Offset'], vein.inputs['Phase Offset'])

    # abs(subtract)
    abs_n = ng.nodes.new('ShaderNodeMath'); abs_n.operation = 'ABSOLUTE'
    ng.links.new(sub.outputs[0], abs_n.inputs[0])

    # noise texture on rotated vector
    noise = ng.nodes.new('ShaderNodeTexNoise')
    ng.links.new(vrot1.outputs[0], noise.inputs['Vector'])
    noise.inputs['Scale'].default_value = 10.0

    # subtract_1 = noise.outputs[0] - 0.5 (default inputs[1])
    # Blender 5.0: use outputs[0] instead of "Factor"/"Fac"
    sub1 = ng.nodes.new('ShaderNodeMath'); sub1.operation = 'SUBTRACT'
    ng.links.new(noise.outputs[0], sub1.inputs[0])

    # multiply_2 = sub1 * 0.01
    mul2 = ng.nodes.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
    ng.links.new(sub1.outputs[0], mul2.inputs[0])
    mul2.inputs[1].default_value = 0.01

    # add_1 = abs + mul2
    add1 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(abs_n.outputs[0], add1.inputs[0])
    ng.links.new(mul2.outputs[0], add1.inputs[1])

    # map_range: add1 -> [0, 0.01] -> [1, 0]
    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(add1.outputs[0], mr.inputs['Value'])
    mr.inputs[2].default_value = 0.01
    mr.inputs[3].default_value = 1.0
    mr.inputs[4].default_value = 0.0

    # greater_than: sep.Y > 0
    gt = ng.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'
    ng.links.new(sep.outputs['Y'], gt.inputs[0])
    gt.inputs[1].default_value = 0.0

    # multiply_3 = mr.Result * gt
    mul3 = ng.nodes.new('ShaderNodeMath'); mul3.operation = 'MULTIPLY'
    ng.links.new(mr.outputs['Result'], mul3.inputs[0])
    ng.links.new(gt.outputs[0], mul3.inputs[1])

    # maximum = max(vein, mul3)
    mx = ng.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
    ng.links.new(vein.outputs['Result'], mx.inputs[0])
    ng.links.new(mul3.outputs[0], mx.inputs[1])

    ng.links.new(mx.outputs[0], out.inputs['Result'])
    ng.links.new(vrot1.outputs[0], out.inputs['Vector'])
    return ng

def make_valid_area():
    """nodegroup_valid_area: maps sign of value to 0/1 range."""

    ng = bpy.data.node_groups.new("nodegroup_valid_area", 'GeometryNodeTree')
    ng.interface.new_socket('Value', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and item.name == 'Value':
            item.default_value = 0.5
    ng.interface.new_socket('Result', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    sign = ng.nodes.new('ShaderNodeMath'); sign.operation = 'SIGN'
    ng.links.new(inp.outputs['Value'], sign.inputs[0])

    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(sign.outputs[0], mr.inputs['Value'])
    mr.inputs[1].default_value = -1.0
    mr.inputs[3].default_value = 1.0
    mr.inputs[4].default_value = 0.0

    ng.links.new(mr.outputs['Result'], out.inputs['Result'])
    return ng

def make_maple_shape():
    """nodegroup_maple_shape: radial gradient shape with complex float curve."""

    ng = bpy.data.node_groups.new("nodegroup_maple_shape", 'GeometryNodeTree')
    ng.interface.new_socket('Coordinate', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Multiplier', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Noise Level', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Multiplier': item.default_value = 1.96
            elif item.name == 'Noise Level': item.default_value = 0.02
    ng.interface.new_socket('Shape', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Displacement', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # multiply coord * (0.9, 1.0, 0.0)
    vmul = ng.nodes.new('ShaderNodeVectorMath'); vmul.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Coordinate'], vmul.inputs[0])
    vmul.inputs[1].default_value = (0.9, 1.0, 0.0)

    # length
    length = ng.nodes.new('ShaderNodeVectorMath'); length.operation = 'LENGTH'
    ng.links.new(vmul.outputs['Vector'], length.inputs[0])

    # gradient texture (RADIAL)
    grad = ng.nodes.new('ShaderNodeTexGradient'); grad.gradient_type = 'RADIAL'
    ng.links.new(inp.outputs['Coordinate'], grad.inputs['Vector'])

    # pingpong(grad.Factor)
    # Blender 5.0: use outputs[0] for gradient texture factor
    pp = ng.nodes.new('ShaderNodeMath'); pp.operation = 'PINGPONG'
    ng.links.new(grad.outputs[0], pp.inputs[0])

    # multiply_1 = pp * Multiplier
    mul1 = ng.nodes.new('ShaderNodeMath'); mul1.operation = 'MULTIPLY'
    ng.links.new(pp.outputs[0], mul1.inputs[0])
    ng.links.new(inp.outputs['Multiplier'], mul1.inputs[1])

    # float_curve (main maple shape, 27 control points)
    fc = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mul1.outputs[0], fc.inputs['Value'])
    _assign_curve(fc.mapping.curves[0], [
        (0.0, 0.0), (0.1156, 0.075), (0.2109, 0.2719), (0.2602, 0.2344),
        (0.3633, 0.2625), (0.4171, 0.5545), (0.4336, 0.5344), (0.4568, 0.7094),
        (0.4749, 0.6012), (0.4882, 0.6636), (0.5352, 0.4594), (0.5484, 0.4375),
        (0.5648, 0.4469), (0.6366, 0.7331), (0.6719, 0.6562), (0.7149, 0.8225),
        (0.768, 0.6344), (0.7928, 0.6853), (0.8156, 0.5125), (0.8297, 0.4906),
        (0.85, 0.5125), (0.8988, 0.747), (0.9297, 0.6937), (0.9648, 0.8937),
        (0.9797, 0.8656), (0.9883, 0.8938), (1.0, 1.0),
    ], handles=[
        "AUTO", "AUTO", "VECTOR", "AUTO", "AUTO", "VECTOR", "AUTO", "VECTOR",
        "AUTO", "VECTOR", "AUTO", "AUTO", "AUTO", "VECTOR", "AUTO", "VECTOR",
        "AUTO", "VECTOR", "AUTO", "AUTO", "AUTO", "VECTOR", "AUTO", "VECTOR",
        "AUTO", "VECTOR", "AUTO",
    ])

    # subtract = length - fc
    sub = ng.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
    ng.links.new(length.outputs['Value'], sub.inputs[0])
    ng.links.new(fc.outputs[0], sub.inputs[1])

    # subtract_1 = sub - 0.06
    sub1 = ng.nodes.new('ShaderNodeMath'); sub1.operation = 'SUBTRACT'
    ng.links.new(sub.outputs[0], sub1.inputs[0])
    sub1.inputs[1].default_value = 0.06

    # float_curve_1 (displacement shape, 20 control points)
    fc1 = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mul1.outputs[0], fc1.inputs['Value'])
    _assign_curve(fc1.mapping.curves[0], [
        (0.0, 0.0), (0.1156, 0.075), (0.2109, 0.2719), (0.2602, 0.2344),
        (0.3633, 0.2625), (0.4336, 0.5344), (0.4568, 0.7094), (0.4749, 0.6012),
        (0.5352, 0.4594), (0.5484, 0.4375), (0.5648, 0.4469), (0.6719, 0.6562),
        (0.7149, 0.8225), (0.768, 0.6344), (0.8156, 0.5125), (0.8297, 0.4906),
        (0.85, 0.5125), (0.9297, 0.6937), (0.9883, 0.8938), (1.0, 1.0),
    ], handles=[
        "AUTO", "AUTO", "VECTOR", "AUTO", "AUTO", "AUTO", "VECTOR", "AUTO",
        "AUTO", "AUTO", "AUTO", "AUTO", "VECTOR", "AUTO", "AUTO", "AUTO",
        "AUTO", "AUTO", "VECTOR", "AUTO",
    ])

    # subtract_2 = length - fc1
    sub2 = ng.nodes.new('ShaderNodeMath'); sub2.operation = 'SUBTRACT'
    ng.links.new(length.outputs['Value'], sub2.inputs[0])
    ng.links.new(fc1.outputs[0], sub2.inputs[1])

    # subtract_3 = sub2 - 0.06
    sub3 = ng.nodes.new('ShaderNodeMath'); sub3.operation = 'SUBTRACT'
    ng.links.new(sub2.outputs[0], sub3.inputs[0])
    sub3.inputs[1].default_value = 0.06

    ng.links.new(sub1.outputs[0], out.inputs['Shape'])
    ng.links.new(sub3.outputs[0], out.inputs['Displacement'])
    return ng

def make_maple_stem(stem_curve_control_points):
    """nodegroup_maple_stem: stem shape with curve and noise."""

    ng = bpy.data.node_groups.new("nodegroup_maple_stem", 'GeometryNodeTree')
    ng.interface.new_socket('Coordinate', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Length', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Value', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Length': item.default_value = 0.64
            elif item.name == 'Value': item.default_value = 0.005
    ng.interface.new_socket('Stem', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Stem Raw', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # add = Coordinate + (0, 0.08, 0)
    vadd = ng.nodes.new('ShaderNodeVectorMath')
    ng.links.new(inp.outputs['Coordinate'], vadd.inputs[0])
    vadd.inputs[1].default_value = (0.0, 0.08, 0.0)

    # separate
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(vadd.outputs['Vector'], sep.inputs['Vector'])

    # map_range_2: Y -> [-1, 0] -> [0, 1]
    mr2 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(sep.outputs['Y'], mr2.inputs['Value'])
    mr2.inputs[1].default_value = -1.0
    mr2.inputs[2].default_value = 0.0

    # float curve
    fc1 = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr2.outputs['Result'], fc1.inputs['Value'])
    _assign_curve(fc1.mapping.curves[0], stem_curve_control_points)

    # map_range_3: fc1 -> [0, 1] -> [-1, 1]
    mr3 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(fc1.outputs[0], mr3.inputs['Value'])
    mr3.inputs[3].default_value = -1.0

    # add_1 = mr3.Result + X
    add1 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(mr3.outputs['Result'], add1.inputs[0])
    ng.links.new(sep.outputs['X'], add1.inputs[1])

    # absolute
    abs_n = ng.nodes.new('ShaderNodeMath'); abs_n.operation = 'ABSOLUTE'
    ng.links.new(add1.outputs[0], abs_n.inputs[0])

    # map_range: Y -> [-1.72, -0.35] -> [0.03, 0.008] SMOOTHSTEP
    mr = ng.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
    ng.links.new(sep.outputs['Y'], mr.inputs['Value'])
    mr.inputs[1].default_value = -1.72
    mr.inputs[2].default_value = -0.35
    mr.inputs[3].default_value = 0.03
    mr.inputs[4].default_value = 0.008

    # subtract = abs - mr.Result
    sub = ng.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
    ng.links.new(abs_n.outputs[0], sub.inputs[0])
    ng.links.new(mr.outputs['Result'], sub.inputs[1])

    # add_2 = Y + Length
    add2 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(sep.outputs['Y'], add2.inputs[0])
    ng.links.new(inp.outputs['Length'], add2.inputs[1])

    # abs(add_2)
    abs1 = ng.nodes.new('ShaderNodeMath'); abs1.operation = 'ABSOLUTE'
    ng.links.new(add2.outputs[0], abs1.inputs[0])

    # subtract_1 = abs1 - Length
    sub1 = ng.nodes.new('ShaderNodeMath'); sub1.operation = 'SUBTRACT'
    ng.links.new(abs1.outputs[0], sub1.inputs[0])
    ng.links.new(inp.outputs['Length'], sub1.inputs[1])

    # smooth_max(sub, sub1, 0.02)
    smx = ng.nodes.new('ShaderNodeMath'); smx.operation = 'SMOOTH_MAX'
    ng.links.new(sub.outputs[0], smx.inputs[0])
    ng.links.new(sub1.outputs[0], smx.inputs[1])
    smx.inputs[2].default_value = 0.02

    # subtract_2 = smooth_max - Value
    sub2 = ng.nodes.new('ShaderNodeMath'); sub2.operation = 'SUBTRACT'
    ng.links.new(smx.outputs[0], sub2.inputs[0])
    ng.links.new(inp.outputs['Value'], sub2.inputs[1])

    ng.links.new(sub2.outputs[0], out.inputs['Stem'])
    ng.links.new(abs_n.outputs[0], out.inputs['Stem Raw'])
    return ng

def make_move_to_origin():
    """nodegroup_move_to_origin: centers geometry by shifting Y min to 0 and Z max to 0."""

    ng = bpy.data.node_groups.new("nodegroup_move_to_origin", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    position = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], sep.inputs['Vector'])

    # Y stats
    stats_y = ng.nodes.new('GeometryNodeAttributeStatistic')
    ng.links.new(inp.outputs['Geometry'], stats_y.inputs['Geometry'])
    ng.links.new(sep.outputs['Y'], stats_y.inputs[2])

    sub_y = ng.nodes.new('ShaderNodeMath'); sub_y.operation = 'SUBTRACT'
    sub_y.inputs[0].default_value = 0.0
    ng.links.new(stats_y.outputs['Min'], sub_y.inputs[1])

    # Z stats
    stats_z = ng.nodes.new('GeometryNodeAttributeStatistic')
    ng.links.new(inp.outputs['Geometry'], stats_z.inputs['Geometry'])
    ng.links.new(sep.outputs['Z'], stats_z.inputs[2])

    sub_z = ng.nodes.new('ShaderNodeMath'); sub_z.operation = 'SUBTRACT'
    sub_z.inputs[0].default_value = 0.0
    ng.links.new(stats_z.outputs['Max'], sub_z.inputs[1])

    combine = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(sub_y.outputs[0], combine.inputs['Y'])
    ng.links.new(sub_z.outputs[0], combine.inputs['Z'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(inp.outputs['Geometry'], set_pos.inputs['Geometry'])
    ng.links.new(combine.outputs[0], set_pos.inputs['Offset'])

    ng.links.new(set_pos.outputs[0], out.inputs['Geometry'])
    return ng

def make_apply_wave(y_wave_control_points, x_wave_control_points):
    """nodegroup_apply_wave: applies Y and X wave displacement."""

    ng = bpy.data.node_groups.new("nodegroup_apply_wave", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Wave Scale Y', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Wave Scale X', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Wave Scale Y': item.default_value = 1.0
            elif item.name == 'Wave Scale X': item.default_value = 1.0
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # Y wave branch
    position = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], sep.inputs['Vector'])

    position_1 = ng.nodes.new('GeometryNodeInputPosition')
    sep_1 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position_1.outputs[0], sep_1.inputs['Vector'])

    attr_stat = ng.nodes.new('GeometryNodeAttributeStatistic')
    ng.links.new(inp.outputs['Geometry'], attr_stat.inputs['Geometry'])
    ng.links.new(sep_1.outputs['Y'], attr_stat.inputs[2])

    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(sep.outputs['Y'], mr.inputs['Value'])
    ng.links.new(attr_stat.outputs['Min'], mr.inputs[1])
    ng.links.new(attr_stat.outputs['Max'], mr.inputs[2])

    fc = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr.outputs['Result'], fc.inputs['Value'])
    _assign_curve(fc.mapping.curves[0], y_wave_control_points)

    mr2 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(fc.outputs[0], mr2.inputs['Value'])
    mr2.inputs[3].default_value = -1.0

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(mr2.outputs['Result'], mul.inputs[0])
    ng.links.new(inp.outputs['Wave Scale Y'], mul.inputs[1])

    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(mul.outputs[0], comb.inputs['Z'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(inp.outputs['Geometry'], set_pos.inputs['Geometry'])
    ng.links.new(comb.outputs[0], set_pos.inputs['Offset'])

    # X wave branch
    attr_stat_1 = ng.nodes.new('GeometryNodeAttributeStatistic')
    ng.links.new(inp.outputs['Geometry'], attr_stat_1.inputs['Geometry'])
    ng.links.new(inp.outputs['X Modulated'], attr_stat_1.inputs[2])

    mr7 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['X Modulated'], mr7.inputs['Value'])
    ng.links.new(attr_stat_1.outputs['Min'], mr7.inputs[1])
    ng.links.new(attr_stat_1.outputs['Max'], mr7.inputs[2])

    fc2 = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr7.outputs['Result'], fc2.inputs['Value'])
    _assign_curve(fc2.mapping.curves[0], x_wave_control_points)
    fc2.mapping.curves[0].points[2].handle_type = "VECTOR"

    mr4 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(fc2.outputs[0], mr4.inputs['Value'])
    mr4.inputs[3].default_value = -1.0

    mul_1 = ng.nodes.new('ShaderNodeMath'); mul_1.operation = 'MULTIPLY'
    ng.links.new(mr4.outputs['Result'], mul_1.inputs[0])
    ng.links.new(inp.outputs['Wave Scale X'], mul_1.inputs[1])

    comb_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(mul_1.outputs[0], comb_1.inputs['Z'])

    set_pos_1 = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(set_pos.outputs[0], set_pos_1.inputs['Geometry'])
    ng.links.new(comb_1.outputs[0], set_pos_1.inputs['Offset'])

    ng.links.new(set_pos_1.outputs[0], out.inputs['Geometry'])
    return ng

def make_geo_leaf_maple(**kwargs):
    """Build the top-level GeoNodes tree for maple leaf. Returns the node group."""

    ng = bpy.data.node_groups.new("geo_leaf_maple", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Vein', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # subdivide_mesh (level 11)
    subdiv = ng.nodes.new('GeometryNodeSubdivideMesh')
    ng.links.new(inp.outputs['Geometry'], subdiv.inputs['Mesh'])
    subdiv.inputs['Level'].default_value = 11

    # position
    position = ng.nodes.new('GeometryNodeInputPosition')

    # maple stem sub-group
    stem_ng = make_maple_stem(kwargs["stem_curve_control_points"])
    maplestem = ng.nodes.new('GeometryNodeGroup')
    maplestem.node_tree = stem_ng
    ng.links.new(position.outputs[0], maplestem.inputs['Coordinate'])
    maplestem.inputs['Length'].default_value = 0.32
    maplestem.inputs['Value'].default_value = 0.005

    # vector rotate by angle (Z axis)
    vrot1 = ng.nodes.new('ShaderNodeVectorRotate'); vrot1.rotation_type = 'Z_AXIS'
    ng.links.new(position.outputs[0], vrot1.inputs['Vector'])
    vrot1.inputs['Angle'].default_value = deg2rad(kwargs["angle"])

    # vector rotate by -pi/2 (Z axis)
    vrot = ng.nodes.new('ShaderNodeVectorRotate'); vrot.rotation_type = 'Z_AXIS'
    ng.links.new(vrot1.outputs[0], vrot.inputs['Vector'])
    vrot.inputs['Angle'].default_value = -1.5708

    # maple shape sub-group
    shape_ng = make_maple_shape()
    mapleshape = ng.nodes.new('GeometryNodeGroup')
    mapleshape.node_tree = shape_ng
    ng.links.new(vrot.outputs[0], mapleshape.inputs['Coordinate'])
    mapleshape.inputs['Multiplier'].default_value = kwargs["multiplier"]
    mapleshape.inputs['Noise Level'].default_value = 0.04

    # smooth_min(stem, shape, 0)
    smin = ng.nodes.new('ShaderNodeMath'); smin.operation = 'SMOOTH_MIN'
    ng.links.new(maplestem.outputs['Stem'], smin.inputs[0])
    ng.links.new(mapleshape.outputs['Shape'], smin.inputs[1])
    smin.inputs[2].default_value = 0.0

    # compare (stem_length): smooth_min >= 0 (default: A >= B=0)
    cmp = ng.nodes.new('FunctionNodeCompare')
    ng.links.new(smin.outputs[0], cmp.inputs[0])

    # delete geometry
    delete = ng.nodes.new('GeometryNodeDeleteGeometry')
    ng.links.new(subdiv.outputs[0], delete.inputs['Geometry'])
    ng.links.new(cmp.outputs[0], delete.inputs['Selection'])

    # valid area for shape
    va_ng = make_valid_area()
    validarea = ng.nodes.new('GeometryNodeGroup')
    validarea.node_tree = va_ng
    ng.links.new(mapleshape.outputs['Shape'], validarea.inputs['Value'])

    # midrib instances (6 total, each with make_midrib())
    midrib_ng0 = make_midrib()
    midrib0 = ng.nodes.new('GeometryNodeGroup'); midrib0.node_tree = midrib_ng0
    ng.links.new(vrot1.outputs[0], midrib0.inputs['Vector'])
    midrib0.inputs['Angle'].default_value = 1.693
    midrib0.inputs['vein Length'].default_value = 0.12
    midrib0.inputs['vein Start'].default_value = -0.12
    midrib0.inputs['Phase Offset'].default_value = kwargs["_phase_offsets"][0]

    midrib_ng1 = make_midrib()
    midrib1 = ng.nodes.new('GeometryNodeGroup'); midrib1.node_tree = midrib_ng1
    ng.links.new(vrot1.outputs[0], midrib1.inputs['Vector'])
    midrib1.inputs['Angle'].default_value = -1.7279
    midrib1.inputs['vein Length'].default_value = 0.12
    midrib1.inputs['vein Start'].default_value = -0.12
    midrib1.inputs['Phase Offset'].default_value = kwargs["_phase_offsets"][1]

    # maximum(midrib0, midrib1)
    mx0 = ng.nodes.new('ShaderNodeMath'); mx0.operation = 'MAXIMUM'
    ng.links.new(midrib0.outputs['Result'], mx0.inputs[0])
    ng.links.new(midrib1.outputs['Result'], mx0.inputs[1])

    midrib_ng2 = make_midrib()
    midrib2 = ng.nodes.new('GeometryNodeGroup'); midrib2.node_tree = midrib_ng2
    ng.links.new(vrot1.outputs[0], midrib2.inputs['Vector'])
    midrib2.inputs['Angle'].default_value = 0.8901
    midrib2.inputs['vein Length'].default_value = 0.2
    midrib2.inputs['vein Start'].default_value = 0.0
    midrib2.inputs['Phase Offset'].default_value = kwargs["_phase_offsets"][2]

    midrib_ng3 = make_midrib()
    midrib3 = ng.nodes.new('GeometryNodeGroup'); midrib3.node_tree = midrib_ng3
    ng.links.new(vrot1.outputs[0], midrib3.inputs['Vector'])
    midrib3.inputs['Angle'].default_value = -0.9041
    midrib3.inputs['vein Start'].default_value = 0.0
    midrib3.inputs['Phase Offset'].default_value = kwargs["_phase_offsets"][3]

    mx1 = ng.nodes.new('ShaderNodeMath'); mx1.operation = 'MAXIMUM'
    ng.links.new(midrib2.outputs['Result'], mx1.inputs[0])
    ng.links.new(midrib3.outputs['Result'], mx1.inputs[1])

    mx2 = ng.nodes.new('ShaderNodeMath'); mx2.operation = 'MAXIMUM'
    ng.links.new(mx0.outputs[0], mx2.inputs[0])
    ng.links.new(mx1.outputs[0], mx2.inputs[1])

    midrib_ng4 = make_midrib()
    midrib4 = ng.nodes.new('GeometryNodeGroup'); midrib4.node_tree = midrib_ng4
    ng.links.new(vrot1.outputs[0], midrib4.inputs['Vector'])
    midrib4.inputs['Angle'].default_value = 0.0
    midrib4.inputs['vein Length'].default_value = 1.64
    midrib4.inputs['vein Start'].default_value = -0.12
    midrib4.inputs['Phase Offset'].default_value = kwargs["_phase_offsets"][4]

    midrib_ng5 = make_midrib()
    midrib5 = ng.nodes.new('GeometryNodeGroup'); midrib5.node_tree = midrib_ng5
    ng.links.new(vrot1.outputs[0], midrib5.inputs['Vector'])
    midrib5.inputs['Angle'].default_value = 3.1416
    midrib5.inputs['vein Angle'].default_value = 0.761
    midrib5.inputs['vein Length'].default_value = -10.56
    midrib5.inputs['vein Start'].default_value = 0.02
    midrib5.inputs['Anneal'].default_value = 10.0
    midrib5.inputs['Phase Offset'].default_value = kwargs["_phase_offsets"][5]

    mx3 = ng.nodes.new('ShaderNodeMath'); mx3.operation = 'MAXIMUM'
    ng.links.new(midrib4.outputs['Result'], mx3.inputs[0])
    ng.links.new(midrib5.outputs['Result'], mx3.inputs[1])

    mx4 = ng.nodes.new('ShaderNodeMath'); mx4.operation = 'MAXIMUM'
    ng.links.new(mx2.outputs[0], mx4.inputs[0])
    ng.links.new(mx3.outputs[0], mx4.inputs[1])

    # separate position for sub_vein
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], sep.inputs['Vector'])

    # sub_vein sub-group
    sv_ng = make_nodegroup_sub_vein()
    sub_vein = ng.nodes.new('GeometryNodeGroup')
    sub_vein.node_tree = sv_ng
    ng.links.new(sep.outputs['X'], sub_vein.inputs['X'])
    ng.links.new(sep.outputs['Y'], sub_vein.inputs['Y'])

    # map_range: sub_vein Color Value -> [0, -0.94] -> [1, 0]
    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(sub_vein.outputs['Color Value'], mr.inputs['Value'])
    mr.inputs[2].default_value = -0.94
    mr.inputs[3].default_value = 1.0
    mr.inputs[4].default_value = 0.0

    # max(mx4, mr.Result)
    mx5 = ng.nodes.new('ShaderNodeMath'); mx5.operation = 'MAXIMUM'
    ng.links.new(mx4.outputs[0], mx5.inputs[0])
    ng.links.new(mr.outputs['Result'], mx5.inputs[1])

    # subtract = 1.0 - mx5
    sub_n = ng.nodes.new('ShaderNodeMath'); sub_n.operation = 'SUBTRACT'
    sub_n.inputs[0].default_value = 1.0
    ng.links.new(mx5.outputs[0], sub_n.inputs[1])

    # multiply = validarea * sub_n
    mul_n = ng.nodes.new('ShaderNodeMath'); mul_n.operation = 'MULTIPLY'
    ng.links.new(validarea.outputs['Result'], mul_n.inputs[0])
    ng.links.new(sub_n.outputs[0], mul_n.inputs[1])

    # CaptureAttribute (Blender 5.0: must add capture channel)
    capture = ng.nodes.new('GeometryNodeCaptureAttribute')
    capture.capture_items.new('FLOAT', 'Value')
    ng.links.new(delete.outputs[0], capture.inputs['Geometry'])
    ng.links.new(mul_n.outputs[0], capture.inputs['Value'])

    # sub_vein displacement path
    # multiply_1 = sub_vein.Value * -0.03
    mul1 = ng.nodes.new('ShaderNodeMath'); mul1.operation = 'MULTIPLY'
    ng.links.new(sub_vein.outputs['Value'], mul1.inputs[0])
    mul1.inputs[1].default_value = -0.03

    # max(mx4, mul1)
    mx6 = ng.nodes.new('ShaderNodeMath'); mx6.operation = 'MAXIMUM'
    ng.links.new(mx4.outputs[0], mx6.inputs[0])
    ng.links.new(mul1.outputs[0], mx6.inputs[1])

    # multiply_2 = mx6 * 0.015
    mul2 = ng.nodes.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
    ng.links.new(mx6.outputs[0], mul2.inputs[0])
    mul2.inputs[1].default_value = 0.015

    # multiply_3 = mul2 * -1.0
    mul3 = ng.nodes.new('ShaderNodeMath'); mul3.operation = 'MULTIPLY'
    ng.links.new(mul2.outputs[0], mul3.inputs[0])
    mul3.inputs[1].default_value = -1.0

    # multiply_4 = mul3 * validarea
    mul4 = ng.nodes.new('ShaderNodeMath'); mul4.operation = 'MULTIPLY'
    ng.links.new(mul3.outputs[0], mul4.inputs[0])
    ng.links.new(validarea.outputs['Result'], mul4.inputs[1])

    # valid area for stem
    va_ng2 = make_valid_area()
    validarea1 = ng.nodes.new('GeometryNodeGroup')
    validarea1.node_tree = va_ng2
    ng.links.new(maplestem.outputs['Stem'], validarea1.inputs['Value'])

    # subtract_1 = Stem Raw - 0.01
    sub1 = ng.nodes.new('ShaderNodeMath'); sub1.operation = 'SUBTRACT'
    ng.links.new(maplestem.outputs['Stem Raw'], sub1.inputs[0])
    sub1.inputs[1].default_value = 0.01

    # multiply_5 = validarea1 * sub1
    mul5 = ng.nodes.new('ShaderNodeMath'); mul5.operation = 'MULTIPLY'
    ng.links.new(validarea1.outputs['Result'], mul5.inputs[0])
    ng.links.new(sub1.outputs[0], mul5.inputs[1])

    # add = mul4 + mul5
    add_n = ng.nodes.new('ShaderNodeMath')
    ng.links.new(mul4.outputs[0], add_n.inputs[0])
    ng.links.new(mul5.outputs[0], add_n.inputs[1])

    # multiply_6 = add * 0.5 (default inputs[1])
    mul6 = ng.nodes.new('ShaderNodeMath'); mul6.operation = 'MULTIPLY'
    ng.links.new(add_n.outputs[0], mul6.inputs[0])

    # nodegroup_002 sub-group
    ng002 = make_node_group_002()
    grp002 = ng.nodes.new('GeometryNodeGroup')
    grp002.node_tree = ng002
    ng.links.new(mapleshape.outputs['Displacement'], grp002.inputs['Shape'])

    # add_1 = mul6 + grp002
    add1 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(mul6.outputs[0], add1.inputs[0])
    ng.links.new(grp002.outputs['Result'], add1.inputs[1])

    # combine Z = add1
    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(add1.outputs[0], comb.inputs['Z'])

    # set_position on captured geometry
    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(capture.outputs['Geometry'], set_pos.inputs['Geometry'])
    ng.links.new(comb.outputs[0], set_pos.inputs['Offset'])

    # separate vrot1 for X Modulated
    sep1 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(vrot1.outputs[0], sep1.inputs['Vector'])

    # move_to_origin sub-group
    mto_ng = make_move_to_origin()
    mto = ng.nodes.new('GeometryNodeGroup')
    mto.node_tree = mto_ng
    ng.links.new(set_pos.outputs[0], mto.inputs['Geometry'])

    # apply_wave sub-group
    aw_ng = make_apply_wave(kwargs["y_wave_control_points"], kwargs["x_wave_control_points"])
    aw = ng.nodes.new('GeometryNodeGroup')
    aw.node_tree = aw_ng
    ng.links.new(mto.outputs['Geometry'], aw.inputs['Geometry'])
    aw.inputs['Wave Scale X'].default_value = 0.5
    aw.inputs['Wave Scale Y'].default_value = 1.0
    ng.links.new(sep1.outputs['X'], aw.inputs['X Modulated'])

    # Wire outputs
    ng.links.new(aw.outputs['Geometry'], out.inputs['Geometry'])
    ng.links.new(capture.outputs['Value'], out.inputs['Vein'])
    return ng

# Factory class (preserved from original)

class AssetFactory:
    def __init__(self, factory_seed=None, coarse=False):
        self.factory_seed = int(factory_seed if factory_seed is not None else np.random.randint(1e9))
        self.coarse = coarse
    def __call__(self, i=0, **kwargs):
        with FixedSeed(int_hash((self.factory_seed, i))):
            return self.create_asset(i=i, **kwargs)

class LeafFactoryMaple(AssetFactory):
    scale = 0.5

    def __init__(self, factory_seed, season="autumn", coarse=False):
        super().__init__(factory_seed, coarse=coarse)

        with FixedSeed(factory_seed):
            self.genome = self.sample_geo_genome()

            t = uniform(0.0, 1.0)

            if season == "autumn":
                hsvcol_blade = [uniform(0.0, 0.20), 0.85, 0.9]
                hsvcol_vein = np.copy(hsvcol_blade)
                hsvcol_vein[2] = 0.7

            elif season == "summer" or season == "spring":
                hsvcol_blade = [uniform(0.28, 0.32), uniform(0.6, 0.7), 0.9]
                hsvcol_vein = np.copy(hsvcol_blade)
                hsvcol_blade[2] = uniform(0.1, 0.5)
                hsvcol_vein[2] = uniform(0.1, 0.5)

            elif season == "winter":
                hsvcol_blade = [
                    uniform(0.0, 0.10),
                    uniform(0.2, 0.6),
                    uniform(0.0, 0.1),
                ]
                hsvcol_vein = [uniform(0.0, 0.10), uniform(0.2, 0.6), uniform(0.0, 0.1)]

            else:
                raise NotImplementedError

            self.blade_color = hsvcol_blade
            self.vein_color = hsvcol_vein

            self.color_randomness = uniform(0.05, 0.10)

    @staticmethod
    def sample_geo_genome():
        return {
            "midrib_length": uniform(0.0, 0.8),
            "midrib_width": uniform(0.5, 1.0),
            "stem_length": uniform(0.7, 0.9),
            "vein_asymmetry": uniform(0.0, 1.0),
            "vein_angle": uniform(0.2, 2.0),
            "vein_density": uniform(5.0, 20.0),
            "subvein_scale": uniform(10.0, 20.0),
            "jigsaw_scale": uniform(5.0, 20.0),
            "jigsaw_depth": uniform(0.0, 2.0),
            "midrib_shape_control_points": [
                (0.0, 0.5),
                (0.25, uniform(0.48, 0.52)),
                (0.75, uniform(0.48, 0.52)),
                (1.0, 0.5),
            ],
            "leaf_shape_control_points": [
                (0.0, 0.0),
                (uniform(0.2, 0.4), uniform(0.1, 0.4)),
                (uniform(0.6, 0.8), uniform(0.1, 0.4)),
                (1.0, 0.0),
            ],
            "vein_shape_control_points": [
                (0.0, 0.0),
                (0.25, uniform(0.1, 0.4)),
                (0.75, uniform(0.6, 0.9)),
                (1.0, 1.0),
            ],
        }

    def create_asset(self, **params):
        bpy.ops.mesh.primitive_plane_add(
            size=4,
            enter_editmode=False,
            align="WORLD",
            location=(0, 0, 0),
            scale=(1, 1, 1),
        )
        obj = bpy.context.active_object

        phenome = self.genome.copy()

        phenome["y_wave_control_points"] = [
            (0.0, 0.5),
            (uniform(0.25, 0.75), uniform(0.50, 0.60)),
            (1.0, 0.5),
        ]
        x_wave_val = np.random.uniform(0.50, 0.58)
        phenome["x_wave_control_points"] = [
            (0.0, 0.5),
            (0.4, x_wave_val),
            (0.5, 0.5),
            (0.6, x_wave_val),
            (1.0, 0.5),
        ]

        phenome["stem_curve_control_points"] = [
            (0.0, 0.5),
            (uniform(0.2, 0.3), uniform(0.45, 0.55)),
            (uniform(0.7, 0.8), uniform(0.45, 0.55)),
            (1.0, 0.5),
        ]
        phenome["shape_curve_control_points"] = [
            (0.0, 0.0),
            (0.523, 0.1156),
            (0.5805, 0.7469),
            (0.7742, 0.7719),
            (0.9461, 0.7531),
            (1.0, 0.0),
        ]
        phenome["vein_length"] = uniform(0.4, 0.5)
        phenome["angle"] = uniform(-15.0, 15.0)
        phenome["multiplier"] = uniform(1.92, 2.00)

        phenome["scale_vein"] = uniform(70.0, 90.0)
        phenome["scale_wave"] = uniform(4.0, 6.0)
        phenome["scale_margin"] = uniform(5.5, 7.5)

        # Pre-sample the 6 phase offsets (to match original RNG sequence)
        phenome["_phase_offsets"] = [uniform(0, 100) for _ in range(6)]

        material_kwargs = phenome.copy()
        material_kwargs["color_base"] = np.copy(self.blade_color)
        material_kwargs["color_base"][0] += np.random.normal(0.0, 0.02)
        material_kwargs["color_base"][1] += np.random.normal(0.0, self.color_randomness)
        material_kwargs["color_base"][2] += np.random.normal(0.0, self.color_randomness)
        material_kwargs["color_base"] = hsv2rgba(material_kwargs["color_base"])

        material_kwargs["color_vein"] = np.copy(self.vein_color)
        material_kwargs["color_vein"][0] += np.random.normal(0.0, 0.02)
        material_kwargs["color_vein"][1] += np.random.normal(0.0, self.color_randomness)
        material_kwargs["color_vein"][2] += np.random.normal(0.0, self.color_randomness)
        material_kwargs["color_vein"] = hsv2rgba(material_kwargs["color_vein"])

        # Build GeoNodes tree and assign as modifier (replaces surface.add_geomod)
        geo_ng = make_geo_leaf_maple(**phenome)
        mod = obj.modifiers.new(name="geo_leaf_maple", type='NODES')
        mod.node_group = geo_ng

        # Apply attributes by name (mirrors old surface.add_geomod attributes=["vein"])
        out_items = [item for item in geo_ng.interface.items_tree
                     if getattr(item, 'in_out', None) == 'OUTPUT'
                     and getattr(item, 'socket_type', None) != 'NodeSocketGeometry']
        attr_names = ["vein"]
        for item, att_name in zip(out_items, attr_names):
            if att_name:
                try:
                    mod[item.identifier + '_attribute_name'] = att_name
                except Exception:
                    pass

        # Material: shape-only, skip material assignment
        # surface.add_material(obj, shader_material, reuse=False, input_kwargs=material_kwargs)

        bpy.ops.object.convert(target="MESH")

        obj = bpy.context.object
        obj.scale *= normal(1, 0.1) * self.scale
        apply_transform(obj)
        tag_object(obj, "leaf_maple")

        if obj is not None and len(obj.data.materials) == 0:
            obj.data.materials.append(CATEG_MAT)
        return obj

def build(seed=0, season="autumn"):
    fac = LeafFactoryMaple(seed, season)
    with FixedSeed(int_hash((seed, seed))):
        return fac.create_asset()

SEED = int(os.environ.get("SEED", 0))
build(SEED)

