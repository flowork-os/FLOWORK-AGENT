# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafGinkoFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafGinkoFactory | Category: factories_geo
# Prompt: A 3D model of a ginkgo leaf rendered from a three-quarter perspective. The leaf features a distinctive fan-shaped blade with a wavy or scalloped outer edge, a characteristic central notch dividing the fan into two lobes, a long thin petiole stem, and a slightly curved surface with a pale yellow-green coloration.

import bpy
import numpy as np
import random
import hashlib
from numpy.random import normal, uniform
from mathutils import Color

C = bpy.context
D = bpy.data

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

class AssetFactory:
    def __init__(self, factory_seed=None, coarse=False):
        self.factory_seed = int(factory_seed if factory_seed is not None else np.random.randint(1e9))
        self.coarse = coarse
    def __call__(self, i=0, **kwargs):
        with FixedSeed(int_hash((self.factory_seed, i))):
            return self.create_asset(i=i, **kwargs)

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

# ===================================================================
# Node-group builder functions (direct bpy API, no NodeWrangler)
# ===================================================================

def make_move_to_origin():
    ng = bpy.data.node_groups.new("nodegroup_move_to_origin", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    position = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], sep.inputs['Vector'])

    stats = ng.nodes.new('GeometryNodeAttributeStatistic')
    ng.links.new(inp.outputs['Geometry'], stats.inputs['Geometry'])
    ng.links.new(sep.outputs['Y'], stats.inputs[2])

    sub = ng.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
    sub.inputs[0].default_value = 0.0
    ng.links.new(stats.outputs['Min'], sub.inputs[1])

    combine = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(sub.outputs[0], combine.inputs['Y'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(inp.outputs['Geometry'], set_pos.inputs['Geometry'])
    ng.links.new(combine.outputs[0], set_pos.inputs['Offset'])

    ng.links.new(set_pos.outputs[0], out.inputs['Geometry'])
    return ng


def make_apply_wave(y_wave_control_points, x_wave_control_points):
    ng = bpy.data.node_groups.new("nodegroup_apply_wave", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Wave Scale Y', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Wave Scale X', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and item.name == 'Wave Scale Y':
            item.default_value = 1.0
        if getattr(item, 'in_out', None) == 'INPUT' and item.name == 'Wave Scale X':
            item.default_value = 1.0

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

    map_range = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(sep.outputs['Y'], map_range.inputs['Value'])
    ng.links.new(attr_stat.outputs['Min'], map_range.inputs[1])
    ng.links.new(attr_stat.outputs['Max'], map_range.inputs[2])

    fc = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(map_range.outputs['Result'], fc.inputs['Value'])
    _assign_curve(fc.mapping.curves[0], y_wave_control_points)

    map_range_2 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(fc.outputs[0], map_range_2.inputs['Value'])
    map_range_2.inputs[3].default_value = -1.0

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(map_range_2.outputs['Result'], mul.inputs[0])
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

    map_range_7 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['X Modulated'], map_range_7.inputs['Value'])
    ng.links.new(attr_stat_1.outputs['Min'], map_range_7.inputs[1])
    ng.links.new(attr_stat_1.outputs['Max'], map_range_7.inputs[2])

    fc2 = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(map_range_7.outputs['Result'], fc2.inputs['Value'])
    _assign_curve(fc2.mapping.curves[0], x_wave_control_points)
    fc2.mapping.curves[0].points[2].handle_type = "VECTOR"

    map_range_4 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(fc2.outputs[0], map_range_4.inputs['Value'])
    map_range_4.inputs[3].default_value = -1.0

    mul_1 = ng.nodes.new('ShaderNodeMath'); mul_1.operation = 'MULTIPLY'
    ng.links.new(map_range_4.outputs['Result'], mul_1.inputs[0])
    ng.links.new(inp.outputs['Wave Scale X'], mul_1.inputs[1])

    comb_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(mul_1.outputs[0], comb_1.inputs['Z'])

    set_pos_1 = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(set_pos.outputs[0], set_pos_1.inputs['Geometry'])
    ng.links.new(comb_1.outputs[0], set_pos_1.inputs['Offset'])

    ng.links.new(set_pos_1.outputs[0], out.inputs['Geometry'])
    return ng


# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory of this source tree.

# Authors: Yiming Zuo


def make_ginko_stem(stem_curve_control_points):
    """nodegroup_ginko_stem: given a coordinate, computes stem SDF value."""

    ng = bpy.data.node_groups.new("nodegroup_ginko_stem", 'GeometryNodeTree')
    ng.interface.new_socket('Coordinate', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Length', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Value', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Coordinate':
                item.default_value = (0.0, 0.0, 0.0)
            elif item.name == 'Length':
                item.default_value = 0.64
            elif item.name == 'Value':
                item.default_value = 0.005
    ng.interface.new_socket('Stem', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Stem Raw', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # add = Coordinate + (0, 0.03, 0)
    add = ng.nodes.new('ShaderNodeVectorMath')
    ng.links.new(inp.outputs['Coordinate'], add.inputs[0])
    _set_default(add.inputs[1], (0.0, 0.03, 0.0))

    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(add.outputs['Vector'], sep.inputs['Vector'])

    # map_range_2: Y from [-1, 0] -> [0, 1]
    mr2 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(sep.outputs['Y'], mr2.inputs['Value'])
    mr2.inputs[1].default_value = -1.0
    mr2.inputs[2].default_value = 0.0

    # float curve on the mapped Y
    fc1 = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr2.outputs['Result'], fc1.inputs['Value'])
    _assign_curve(fc1.mapping.curves[0], stem_curve_control_points)

    # map_range_3: float_curve from [0,1] -> [-1, 1]
    mr3 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(fc1.outputs[0], mr3.inputs['Value'])
    mr3.inputs[3].default_value = -1.0

    # add_1 = map_range_3.Result + X
    add_1 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(mr3.outputs['Result'], add_1.inputs[0])
    ng.links.new(sep.outputs['X'], add_1.inputs[1])

    # absolute
    absolute = ng.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'
    ng.links.new(add_1.outputs[0], absolute.inputs[0])

    # map_range: Y from [-1.72, -0.35] -> [0.03, 0.008] SMOOTHSTEP
    mr = ng.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
    ng.links.new(sep.outputs['Y'], mr.inputs['Value'])
    mr.inputs[1].default_value = -1.72
    mr.inputs[2].default_value = -0.35
    mr.inputs[3].default_value = 0.03
    mr.inputs[4].default_value = 0.008

    # subtract = absolute - map_range.Result
    subtract = ng.nodes.new('ShaderNodeMath'); subtract.operation = 'SUBTRACT'
    ng.links.new(absolute.outputs[0], subtract.inputs[0])
    ng.links.new(mr.outputs['Result'], subtract.inputs[1])

    # add_2 = Y + Length
    add_2 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(sep.outputs['Y'], add_2.inputs[0])
    ng.links.new(inp.outputs['Length'], add_2.inputs[1])

    # absolute_1 = abs(add_2)
    absolute_1 = ng.nodes.new('ShaderNodeMath'); absolute_1.operation = 'ABSOLUTE'
    ng.links.new(add_2.outputs[0], absolute_1.inputs[0])

    # subtract_1 = absolute_1 - Length
    subtract_1 = ng.nodes.new('ShaderNodeMath'); subtract_1.operation = 'SUBTRACT'
    ng.links.new(absolute_1.outputs[0], subtract_1.inputs[0])
    ng.links.new(inp.outputs['Length'], subtract_1.inputs[1])

    # smooth_max(subtract, subtract_1, 0.02)
    smooth_max = ng.nodes.new('ShaderNodeMath'); smooth_max.operation = 'SMOOTH_MAX'
    ng.links.new(subtract.outputs[0], smooth_max.inputs[0])
    ng.links.new(subtract_1.outputs[0], smooth_max.inputs[1])
    smooth_max.inputs[2].default_value = 0.02

    # subtract_2 = smooth_max - Value
    subtract_2 = ng.nodes.new('ShaderNodeMath'); subtract_2.operation = 'SUBTRACT'
    ng.links.new(smooth_max.outputs[0], subtract_2.inputs[0])
    ng.links.new(inp.outputs['Value'], subtract_2.inputs[1])

    ng.links.new(subtract_2.outputs[0], out.inputs['Stem'])
    ng.links.new(absolute.outputs[0], out.inputs['Stem Raw'])
    return ng


def make_ginko_vein():
    """nodegroup_ginko_vein: computes vein and wave displacement from coordinate."""

    ng = bpy.data.node_groups.new("nodegroup_ginko_vein", 'GeometryNodeTree')
    ng.interface.new_socket('Vector', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Scale Vein', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Scale Wave', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Vector':
                item.default_value = (0.0, 0.0, 0.0)
            elif item.name == 'Scale Vein':
                item.default_value = 80.0
            elif item.name == 'Scale Wave':
                item.default_value = 5.0
    ng.interface.new_socket('Vein', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Wave', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # subtract = Vector - (-0.18, 0, 0)
    subtract = ng.nodes.new('ShaderNodeVectorMath'); subtract.operation = 'SUBTRACT'
    ng.links.new(inp.outputs['Vector'], subtract.inputs[0])
    _set_default(subtract.inputs[1], (-0.18, 0.0, 0.0))

    # noise_texture_1 on subtract.Vector
    noise_1 = ng.nodes.new('ShaderNodeTexNoise')
    ng.links.new(subtract.outputs['Vector'], noise_1.inputs['Vector'])

    # gradient_texture_1 RADIAL on subtract.Vector
    grad_1 = ng.nodes.new('ShaderNodeTexGradient'); grad_1.gradient_type = 'RADIAL'
    ng.links.new(subtract.outputs['Vector'], grad_1.inputs['Vector'])

    # pingpong(gradient_1.Factor)
    pingpong = ng.nodes.new('ShaderNodeMath'); pingpong.operation = 'PINGPONG'
    ng.links.new(grad_1.outputs['Factor'], pingpong.inputs[0])

    # length of subtract.Vector
    length = ng.nodes.new('ShaderNodeVectorMath'); length.operation = 'LENGTH'
    ng.links.new(subtract.outputs['Vector'], length.inputs[0])

    # subtract_1 = pingpong - 0.5 (default input[1] = 0.5)
    subtract_1 = ng.nodes.new('ShaderNodeMath'); subtract_1.operation = 'SUBTRACT'
    ng.links.new(pingpong.outputs[0], subtract_1.inputs[0])

    # multiply = subtract_1 * -0.44
    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(subtract_1.outputs[0], multiply.inputs[0])
    multiply.inputs[1].default_value = -0.44

    # multiply_1 = length * multiply
    multiply_1 = ng.nodes.new('ShaderNodeMath'); multiply_1.operation = 'MULTIPLY'
    ng.links.new(length.outputs['Value'], multiply_1.inputs[0])
    ng.links.new(multiply.outputs[0], multiply_1.inputs[1])

    # add = pingpong + multiply_1
    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(pingpong.outputs[0], add.inputs[0])
    ng.links.new(multiply_1.outputs[0], add.inputs[1])

    # multiply_add = noise_1.Factor * 0.005 + add
    # Blender 5.0: noise output[0] = "Factor"
    multiply_add = ng.nodes.new('ShaderNodeMath'); multiply_add.operation = 'MULTIPLY_ADD'
    ng.links.new(noise_1.outputs[0], multiply_add.inputs[0])
    multiply_add.inputs[1].default_value = 0.005
    ng.links.new(add.outputs[0], multiply_add.inputs[2])

    # combine_xyz_2 = (multiply_add, 0, 0)
    combine_2 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(multiply_add.outputs[0], combine_2.inputs['X'])

    # wave_texture_1 on combine_2
    wave_1 = ng.nodes.new('ShaderNodeTexWave')
    ng.links.new(combine_2.outputs[0], wave_1.inputs['Vector'])
    ng.links.new(inp.outputs['Scale Vein'], wave_1.inputs['Scale'])
    wave_1.inputs['Distortion'].default_value = 0.6
    wave_1.inputs['Detail'].default_value = 3.0
    wave_1.inputs['Detail Scale'].default_value = 5.0
    wave_1.inputs['Detail Roughness'].default_value = 1.0
    wave_1.inputs['Phase Offset'].default_value = -4.62

    # multiply_2 = wave_1.Color * length.Value
    # wave_texture outputs: [0]=Color, [1]=Fac/Factor
    multiply_2 = ng.nodes.new('ShaderNodeMath'); multiply_2.operation = 'MULTIPLY'
    ng.links.new(wave_1.outputs['Color'], multiply_2.inputs[0])
    ng.links.new(length.outputs['Value'], multiply_2.inputs[1])

    # map_range_1: multiply_2 from [0.15, -0.32] -> [0.0, -0.02]
    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(multiply_2.outputs[0], mr1.inputs['Value'])
    mr1.inputs[1].default_value = 0.15
    mr1.inputs[2].default_value = -0.32
    mr1.inputs[4].default_value = -0.02

    # multiply_add_1 = noise_1.Factor * 0.03 + add
    multiply_add_1 = ng.nodes.new('ShaderNodeMath'); multiply_add_1.operation = 'MULTIPLY_ADD'
    ng.links.new(noise_1.outputs[0], multiply_add_1.inputs[0])
    multiply_add_1.inputs[1].default_value = 0.03
    ng.links.new(add.outputs[0], multiply_add_1.inputs[2])

    # combine_xyz_3 = (multiply_add_1, 0, 0)
    combine_3 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(multiply_add_1.outputs[0], combine_3.inputs['X'])

    # wave_texture_2
    wave_2 = ng.nodes.new('ShaderNodeTexWave')
    ng.links.new(combine_3.outputs[0], wave_2.inputs['Vector'])
    ng.links.new(inp.outputs['Scale Wave'], wave_2.inputs['Scale'])
    wave_2.inputs['Distortion'].default_value = -0.42
    wave_2.inputs['Detail'].default_value = 10.0
    wave_2.inputs['Detail Roughness'].default_value = 1.0
    wave_2.inputs['Phase Offset'].default_value = -4.62

    # multiply_3 = wave_2.Factor * length
    multiply_3 = ng.nodes.new('ShaderNodeMath'); multiply_3.operation = 'MULTIPLY'
    ng.links.new(wave_2.outputs['Factor'], multiply_3.inputs[0])
    ng.links.new(length.outputs['Value'], multiply_3.inputs[1])

    ng.links.new(mr1.outputs['Result'], out.inputs['Vein'])
    ng.links.new(multiply_3.outputs[0], out.inputs['Wave'])
    return ng


def make_ginko_shape(shape_curve_control_points):
    """nodegroup_ginko_shape: fan-shaped SDF from radial + wave textures."""

    ng = bpy.data.node_groups.new("nodegroup_ginko_shape", 'GeometryNodeTree')
    ng.interface.new_socket('Coordinate', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Multiplier', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Scale Margin', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Coordinate':
                item.default_value = (0.0, 0.0, 0.0)
            elif item.name == 'Multiplier':
                item.default_value = 1.980
            elif item.name == 'Scale Margin':
                item.default_value = 6.6
    ng.interface.new_socket('Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # multiply = Coordinate * (0.9, 1.0, 0.0)
    multiply = ng.nodes.new('ShaderNodeVectorMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Coordinate'], multiply.inputs[0])
    _set_default(multiply.inputs[1], (0.9, 1.0, 0.0))

    # length of multiply
    length = ng.nodes.new('ShaderNodeVectorMath'); length.operation = 'LENGTH'
    ng.links.new(multiply.outputs['Vector'], length.inputs[0])

    # gradient_texture RADIAL on Coordinate
    grad = ng.nodes.new('ShaderNodeTexGradient'); grad.gradient_type = 'RADIAL'
    ng.links.new(inp.outputs['Coordinate'], grad.inputs['Vector'])

    # pingpong(gradient.Factor)
    pingpong = ng.nodes.new('ShaderNodeMath'); pingpong.operation = 'PINGPONG'
    ng.links.new(grad.outputs['Factor'], pingpong.inputs[0])

    # multiply_1 = pingpong * Multiplier
    multiply_1 = ng.nodes.new('ShaderNodeMath'); multiply_1.operation = 'MULTIPLY'
    ng.links.new(pingpong.outputs[0], multiply_1.inputs[0])
    ng.links.new(inp.outputs['Multiplier'], multiply_1.inputs[1])

    # noise_texture 1D on gradient.Factor
    noise = ng.nodes.new('ShaderNodeTexNoise'); noise.noise_dimensions = '1D'
    ng.links.new(grad.outputs['Factor'], noise.inputs['W'])

    # multiply_2 = noise.Factor * 0.3
    multiply_2 = ng.nodes.new('ShaderNodeMath'); multiply_2.operation = 'MULTIPLY'
    ng.links.new(noise.outputs[0], multiply_2.inputs[0])
    multiply_2.inputs[1].default_value = 0.3

    # add = multiply_1 + multiply_2
    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(multiply_1.outputs[0], add.inputs[0])
    ng.links.new(multiply_2.outputs[0], add.inputs[1])

    # combine_xyz_1 = (add, 0, 0)
    combine_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(add.outputs[0], combine_1.inputs['X'])

    # wave_texture
    wave = ng.nodes.new('ShaderNodeTexWave')
    ng.links.new(combine_1.outputs[0], wave.inputs['Vector'])
    ng.links.new(inp.outputs['Scale Margin'], wave.inputs['Scale'])
    wave.inputs['Distortion'].default_value = 5.82
    wave.inputs['Detail'].default_value = 1.52
    wave.inputs['Detail Roughness'].default_value = 1.0

    # multiply_3 = wave.Factor * 0.02
    multiply_3 = ng.nodes.new('ShaderNodeMath'); multiply_3.operation = 'MULTIPLY'
    ng.links.new(wave.outputs['Factor'], multiply_3.inputs[0])
    multiply_3.inputs[1].default_value = 0.02

    # float_curve on multiply_1
    fc = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(multiply_1.outputs[0], fc.inputs['Value'])
    _assign_curve(fc.mapping.curves[0], shape_curve_control_points)

    # add_1 = multiply_3 + float_curve
    add_1 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(multiply_3.outputs[0], add_1.inputs[0])
    ng.links.new(fc.outputs[0], add_1.inputs[1])

    # subtract = length - add_1
    subtract = ng.nodes.new('ShaderNodeMath'); subtract.operation = 'SUBTRACT'
    ng.links.new(length.outputs['Value'], subtract.inputs[0])
    ng.links.new(add_1.outputs[0], subtract.inputs[1])

    ng.links.new(subtract.outputs[0], out.inputs['Value'])
    return ng


def make_valid_area():
    """nodegroup_valid_area: sign -> map_range to convert negative->1, positive->0."""

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


def make_ginko(stem_curve_control_points, shape_curve_control_points):
    """nodegroup_ginko: main compound group - subdivide, shape, vein, stem, delete, displace."""

    ng = bpy.data.node_groups.new("nodegroup_ginko", 'GeometryNodeTree')
    ng.interface.new_socket('Mesh', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Vein Length', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Width', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Displacenment', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Multiplier', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Scale Vein', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Scale Wave', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Scale Margin', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Level', in_out='INPUT', socket_type='NodeSocketInt')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Vein Length': item.default_value = 0.64
            elif item.name == 'Vein Width': item.default_value = 0.005
            elif item.name == 'Angle': item.default_value = -1.7617
            elif item.name == 'Displacenment': item.default_value = 0.5
            elif item.name == 'Multiplier': item.default_value = 1.980
            elif item.name == 'Scale Vein': item.default_value = 80.0
            elif item.name == 'Scale Wave': item.default_value = 5.0
            elif item.name == 'Scale Margin': item.default_value = 6.6
            elif item.name == 'Level': item.default_value = 9
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Vein', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Shape', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Wave', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # Subdivide mesh
    subdiv = ng.nodes.new('GeometryNodeSubdivideMesh')
    ng.links.new(inp.outputs['Mesh'], subdiv.inputs['Mesh'])
    ng.links.new(inp.outputs['Level'], subdiv.inputs['Level'])

    # Position + VectorRotate Z_AXIS
    position = ng.nodes.new('GeometryNodeInputPosition')

    vec_rotate = ng.nodes.new('ShaderNodeVectorRotate'); vec_rotate.rotation_type = 'Z_AXIS'
    ng.links.new(position.outputs[0], vec_rotate.inputs['Vector'])
    ng.links.new(inp.outputs['Angle'], vec_rotate.inputs['Angle'])

    # GinkoShape sub-group
    shape_ng = make_ginko_shape(shape_curve_control_points)
    ginkoshape = ng.nodes.new('GeometryNodeGroup')
    ginkoshape.node_tree = shape_ng
    ng.links.new(vec_rotate.outputs['Vector'], ginkoshape.inputs['Coordinate'])
    ng.links.new(inp.outputs['Multiplier'], ginkoshape.inputs['Multiplier'])
    ng.links.new(inp.outputs['Scale Margin'], ginkoshape.inputs['Scale Margin'])

    # ValidArea on ginkoshape
    va_ng = make_valid_area()
    validarea = ng.nodes.new('GeometryNodeGroup')
    validarea.node_tree = va_ng
    ng.links.new(ginkoshape.outputs['Value'], validarea.inputs['Value'])

    # GinkoVein sub-group
    vein_ng = make_ginko_vein()
    ginkovein = ng.nodes.new('GeometryNodeGroup')
    ginkovein.node_tree = vein_ng
    ng.links.new(vec_rotate.outputs['Vector'], ginkovein.inputs['Vector'])
    ng.links.new(inp.outputs['Scale Vein'], ginkovein.inputs['Scale Vein'])
    ng.links.new(inp.outputs['Scale Wave'], ginkovein.inputs['Scale Wave'])

    # multiply = validarea * ginkovein.Vein
    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(validarea.outputs['Result'], multiply.inputs[0])
    ng.links.new(ginkovein.outputs['Vein'], multiply.inputs[1])

    # map_range_4: ginkoshape from [-1, 0] -> [-5, 0] (no clamp)
    mr4 = ng.nodes.new('ShaderNodeMapRange'); mr4.clamp = False
    ng.links.new(ginkoshape.outputs['Value'], mr4.inputs['Value'])
    mr4.inputs[1].default_value = -1.0
    mr4.inputs[2].default_value = 0.0
    mr4.inputs[3].default_value = -5.0
    mr4.inputs[4].default_value = 0.0

    # multiply_1 = multiply * map_range_4.Result (clamped)
    multiply_1 = ng.nodes.new('ShaderNodeMath'); multiply_1.operation = 'MULTIPLY'; multiply_1.use_clamp = True
    ng.links.new(multiply.outputs[0], multiply_1.inputs[0])
    ng.links.new(mr4.outputs['Result'], multiply_1.inputs[1])

    # clamp multiply_1 to [0, 0.01]
    clamp = ng.nodes.new('ShaderNodeClamp')
    ng.links.new(multiply_1.outputs[0], clamp.inputs['Value'])
    clamp.inputs['Max'].default_value = 0.01

    # CaptureAttribute 1: capture clamp on subdivided geometry
    cap1 = ng.nodes.new('GeometryNodeCaptureAttribute')
    cap1.capture_items.new('FLOAT', 'Value')
    ng.links.new(subdiv.outputs[0], cap1.inputs['Geometry'])
    ng.links.new(clamp.outputs[0], cap1.inputs['Value'])

    # CaptureAttribute 2: capture ginkoshape on cap1 geometry
    cap2 = ng.nodes.new('GeometryNodeCaptureAttribute')
    cap2.capture_items.new('FLOAT', 'Value')
    ng.links.new(cap1.outputs['Geometry'], cap2.inputs['Geometry'])
    ng.links.new(ginkoshape.outputs['Value'], cap2.inputs['Value'])

    # GinkoStem sub-group
    stem_ng = make_ginko_stem(stem_curve_control_points)
    ginkostem = ng.nodes.new('GeometryNodeGroup')
    ginkostem.node_tree = stem_ng
    ng.links.new(position.outputs[0], ginkostem.inputs['Coordinate'])
    ng.links.new(inp.outputs['Vein Length'], ginkostem.inputs['Length'])
    ng.links.new(inp.outputs['Vein Width'], ginkostem.inputs['Value'])

    # smooth_min(ginkoshape, stem.Stem, 0.1)
    smooth_min = ng.nodes.new('ShaderNodeMath'); smooth_min.operation = 'SMOOTH_MIN'
    ng.links.new(ginkoshape.outputs['Value'], smooth_min.inputs[0])
    ng.links.new(ginkostem.outputs['Stem'], smooth_min.inputs[1])
    smooth_min.inputs[2].default_value = 0.1

    # multiply_2 = smooth_min * -1
    multiply_2 = ng.nodes.new('ShaderNodeMath'); multiply_2.operation = 'MULTIPLY'
    ng.links.new(smooth_min.outputs[0], multiply_2.inputs[0])
    multiply_2.inputs[1].default_value = -1.0

    # stem_length = compare (multiply_2 < 0)
    stem_length = ng.nodes.new('FunctionNodeCompare'); stem_length.operation = 'LESS_THAN'
    ng.links.new(multiply_2.outputs[0], stem_length.inputs[0])
    stem_length.inputs[1].default_value = 0.0

    # delete_geometry
    delete = ng.nodes.new('GeometryNodeDeleteGeometry')
    ng.links.new(cap2.outputs['Geometry'], delete.inputs['Geometry'])
    ng.links.new(stem_length.outputs[0], delete.inputs['Selection'])

    # ValidArea on stem.Stem
    va_ng_1 = make_valid_area()
    validarea_1 = ng.nodes.new('GeometryNodeGroup')
    validarea_1.node_tree = va_ng_1
    ng.links.new(ginkostem.outputs['Stem'], validarea_1.inputs['Value'])

    # multiply_3 = validarea_1 * stem.Stem Raw
    multiply_3 = ng.nodes.new('ShaderNodeMath'); multiply_3.operation = 'MULTIPLY'
    ng.links.new(validarea_1.outputs['Result'], multiply_3.inputs[0])
    ng.links.new(ginkostem.outputs['Stem Raw'], multiply_3.inputs[1])

    # add = multiply_3 + clamp
    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(multiply_3.outputs[0], add.inputs[0])
    ng.links.new(clamp.outputs[0], add.inputs[1])

    # multiply_4 = add * Displacenment
    multiply_4 = ng.nodes.new('ShaderNodeMath'); multiply_4.operation = 'MULTIPLY'
    ng.links.new(add.outputs[0], multiply_4.inputs[0])
    ng.links.new(inp.outputs['Displacenment'], multiply_4.inputs[1])

    # combine_xyz Z = multiply_4
    combine = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(multiply_4.outputs[0], combine.inputs['Z'])

    # set_position on delete with offset
    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(delete.outputs[0], set_pos.inputs['Geometry'])
    ng.links.new(combine.outputs[0], set_pos.inputs['Offset'])

    # ValidArea on ginkoshape (for wave output)
    va_ng_2 = make_valid_area()
    validarea_2 = ng.nodes.new('GeometryNodeGroup')
    validarea_2.node_tree = va_ng_2
    ng.links.new(ginkoshape.outputs['Value'], validarea_2.inputs['Value'])

    # multiply_5 = validarea_2 * ginkovein.Wave
    multiply_5 = ng.nodes.new('ShaderNodeMath'); multiply_5.operation = 'MULTIPLY'
    ng.links.new(validarea_2.outputs['Result'], multiply_5.inputs[0])
    ng.links.new(ginkovein.outputs['Wave'], multiply_5.inputs[1])

    # Wire outputs
    ng.links.new(set_pos.outputs[0], out.inputs['Geometry'])
    ng.links.new(cap1.outputs['Value'], out.inputs['Vein'])
    ng.links.new(cap2.outputs['Value'], out.inputs['Shape'])
    ng.links.new(multiply_5.outputs[0], out.inputs['Wave'])
    return ng


def make_geo_leaf_ginko(**kwargs):
    """Build the top-level GeoNodes tree for ginko leaf. Returns the node group."""

    ng = bpy.data.node_groups.new("geo_leaf_ginko", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Vein', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Shape', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # nodegroup_ginko sub-group
    ginko_ng = make_ginko(
        stem_curve_control_points=kwargs["stem_curve_control_points"],
        shape_curve_control_points=kwargs["shape_curve_control_points"],
    )
    nodegroup = ng.nodes.new('GeometryNodeGroup')
    nodegroup.node_tree = ginko_ng
    ng.links.new(inp.outputs['Geometry'], nodegroup.inputs['Mesh'])
    nodegroup.inputs['Vein Length'].default_value = kwargs["vein_length"]
    nodegroup.inputs['Angle'].default_value = deg2rad(kwargs["angle"])
    nodegroup.inputs['Multiplier'].default_value = kwargs["multiplier"]
    nodegroup.inputs['Scale Vein'].default_value = kwargs["scale_vein"]
    nodegroup.inputs['Scale Wave'].default_value = kwargs["scale_wave"]
    nodegroup.inputs['Scale Margin'].default_value = kwargs["scale_margin"]

    # map_range on Wave: [0,1] -> [0, 0.04]
    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(nodegroup.outputs['Wave'], mr.inputs['Value'])
    mr.inputs[4].default_value = 0.04

    # combine_xyz Z = map_range.Result
    combine = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(mr.outputs['Result'], combine.inputs['Z'])

    # set_position
    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(nodegroup.outputs['Geometry'], set_pos.inputs['Geometry'])
    ng.links.new(combine.outputs[0], set_pos.inputs['Offset'])

    # apply_wave sub-group
    position = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], sep.inputs['Vector'])

    aw_ng = make_apply_wave(
        kwargs["y_wave_control_points"],
        kwargs["x_wave_control_points"],
    )
    apply_wave = ng.nodes.new('GeometryNodeGroup')
    apply_wave.node_tree = aw_ng
    ng.links.new(set_pos.outputs[0], apply_wave.inputs['Geometry'])
    apply_wave.inputs['Wave Scale X'].default_value = 0.0
    apply_wave.inputs['Wave Scale Y'].default_value = 1.0
    ng.links.new(sep.outputs['X'], apply_wave.inputs['X Modulated'])

    # move_to_origin sub-group
    mto_ng = make_move_to_origin()
    mto = ng.nodes.new('GeometryNodeGroup')
    mto.node_tree = mto_ng
    ng.links.new(apply_wave.outputs['Geometry'], mto.inputs['Geometry'])

    # Wire outputs
    ng.links.new(mto.outputs['Geometry'], out.inputs['Geometry'])
    ng.links.new(nodegroup.outputs['Vein'], out.inputs['Vein'])
    ng.links.new(nodegroup.outputs['Shape'], out.inputs['Shape'])
    return ng


# ===================================================================
# Factory class (preserved from original)
# ===================================================================

class LeafFactoryGinko(AssetFactory):
    scale = 0.3

    def __init__(self, factory_seed, season="autumn", coarse=False):
        super(LeafFactoryGinko, self).__init__(factory_seed, coarse=coarse)

        with FixedSeed(factory_seed):
            self.genome = self.sample_geo_genome()

            t = uniform(0.0, 1.0)

            if season == "autumn":
                self.blade_color = [uniform(0.125, 0.2), 0.95, 0.6]
            elif season == "summer" or season == "spring":
                self.blade_color = [uniform(0.25, 0.3), 0.95, 0.6]
            elif season == "winter":
                self.blade_color = [uniform(0.125, 0.2), 0.95, 0.6]
            else:
                raise NotImplementedError

            self.color_randomness = 0.05

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
            size=2,
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
        phenome["angle"] = uniform(-110.0, -70.0)
        phenome["multiplier"] = uniform(1.90, 1.98)

        phenome["scale_vein"] = uniform(70.0, 90.0)
        phenome["scale_wave"] = uniform(4.0, 6.0)
        phenome["scale_margin"] = uniform(5.5, 7.5)

        material_kwargs = phenome.copy()
        material_kwargs["color_base"] = np.copy(self.blade_color)
        material_kwargs["color_base"][0] += np.random.normal(0.0, 0.02)
        material_kwargs["color_base"][1] += np.random.normal(0.0, self.color_randomness)
        material_kwargs["color_base"][2] += np.random.normal(0.0, self.color_randomness)
        material_kwargs["color_base"] = hsv2rgba(material_kwargs["color_base"])

        material_kwargs["color_vein"] = hsv2rgba(np.copy(self.blade_color))

        # Build GeoNodes tree and assign as modifier (replaces surface.add_geomod)
        geo_ng = make_geo_leaf_ginko(**phenome)
        mod = obj.modifiers.new(name="geo_leaf_ginko", type='NODES')
        mod.node_group = geo_ng

        # Apply attributes by name (mirrors old surface.add_geomod attributes= logic)
        attr_names = ["vein", "shape"]
        out_items = [item for item in geo_ng.interface.items_tree
                     if getattr(item, 'in_out', None) == 'OUTPUT'
                     and getattr(item, 'socket_type', None) != 'NodeSocketGeometry']
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
        obj.scale *= normal(1, 0.2) * self.scale
        apply_transform(obj)
        tag_object(obj, "leaf_ginko")

        return obj

def build(seed=0, season="autumn"):
    fac = LeafFactoryGinko(seed, season)
    with FixedSeed(int_hash((seed, seed))):
        return fac.create_asset()

SEED = 0
build(SEED)
