# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafBroadleafFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafBroadleafFactory | Category: factories_geo
# Prompt: A 3D model of a broad, ovate leaf rendered from a three-quarter perspective. The leaf features a wide elliptical blade with a smooth rounded contour, a thin stem (petiole) extending from the base, a subtle central vein, and a gently curved surface that gives the leaf a natural, slightly cupped appearance.

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
    # Set defaults on interface sockets
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


def make_random_mask_vein():
    ng = bpy.data.node_groups.new("nodegroup_random_mask_vein", 'GeometryNodeTree')
    ng.interface.new_socket('Coord', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Shape', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Density', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Random Scale Seed', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Coord': item.default_value = 0.0
            elif item.name == 'Shape': item.default_value = 0.5
            elif item.name == 'Density': item.default_value = 0.5
            elif item.name == 'Random Scale Seed': item.default_value = 0.5
    ng.interface.new_socket('Result', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    vein = ng.nodes.new('ShaderNodeTexVoronoi'); vein.voronoi_dimensions = '1D'
    ng.links.new(inp.outputs['Coord'], vein.inputs['W'])
    ng.links.new(inp.outputs['Density'], vein.inputs['Scale'])
    vein.inputs['Randomness'].default_value = 0.2

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Density'], mul.inputs[0])
    ng.links.new(inp.outputs['Random Scale Seed'], mul.inputs[1])

    vein_1 = ng.nodes.new('ShaderNodeTexVoronoi'); vein_1.voronoi_dimensions = '1D'
    ng.links.new(inp.outputs['Coord'], vein_1.inputs['W'])
    ng.links.new(mul.outputs[0], vein_1.inputs['Scale'])

    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(vein_1.outputs['Distance'], add.inputs[0])
    add.inputs[1].default_value = 0.35

    rnd = ng.nodes.new('ShaderNodeMath'); rnd.operation = 'ROUND'
    ng.links.new(add.outputs[0], rnd.inputs[0])

    add_1 = ng.nodes.new('ShaderNodeMath')
    ng.links.new(vein.outputs['Distance'], add_1.inputs[0])
    ng.links.new(rnd.outputs[0], add_1.inputs[1])

    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(add_1.outputs[0], mr1.inputs['Value'])
    mr1.inputs[2].default_value = 0.02
    mr1.inputs[3].default_value = 0.95
    mr1.inputs[4].default_value = 0.0

    mul_1 = ng.nodes.new('ShaderNodeMath'); mul_1.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Shape'], mul_1.inputs[0])
    ng.links.new(mr1.outputs['Result'], mul_1.inputs[1])

    mr2 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(mul_1.outputs[0], mr2.inputs['Value'])
    mr2.inputs[1].default_value = 0.001
    mr2.inputs[2].default_value = 0.005
    mr2.inputs[3].default_value = 1.0
    mr2.inputs[4].default_value = 0.0

    ng.links.new(mr2.outputs['Result'], out.inputs['Result'])
    return ng


def make_vein_coord_001():
    ng = bpy.data.node_groups.new("nodegroup_nodegroup_vein_coord_001", 'GeometryNodeTree')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Asymmetry', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Leaf Shape', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X Modulated': item.default_value = 0.5
            elif item.name == 'Y': item.default_value = 0.5
            elif item.name == 'Vein Asymmetry': item.default_value = 0.0
            elif item.name == 'Vein Angle': item.default_value = 2.0
            elif item.name == 'Leaf Shape': item.default_value = 0.0
    ng.interface.new_socket('Vein Coord', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    sign = ng.nodes.new('ShaderNodeMath'); sign.operation = 'SIGN'
    ng.links.new(inp.outputs['X Modulated'], sign.inputs[0])

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Vein Asymmetry'], mul.inputs[0])
    ng.links.new(sign.outputs[0], mul.inputs[1])

    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], mr.inputs['Value'])
    mr.inputs[1].default_value = -1.0

    vein_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(inp.outputs['X Modulated'], vein_shape.inputs['Value'])
    _assign_curve(vein_shape.mapping.curves[0],
                  [(0.0, 0.0), (0.0182, 0.05), (0.3364, 0.2386), (0.7227, 0.75), (1.0, 1.0)])

    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(vein_shape.outputs[0], mr1.inputs['Value'])
    mr1.inputs[4].default_value = 1.9

    mul_1 = ng.nodes.new('ShaderNodeMath'); mul_1.operation = 'MULTIPLY'
    ng.links.new(mr1.outputs['Result'], mul_1.inputs[0])
    ng.links.new(inp.outputs['Vein Angle'], mul_1.inputs[1])

    mul_2 = ng.nodes.new('ShaderNodeMath'); mul_2.operation = 'MULTIPLY'
    ng.links.new(mr.outputs['Result'], mul_2.inputs[0])
    ng.links.new(mul_1.outputs[0], mul_2.inputs[1])

    sub = ng.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
    ng.links.new(mul_2.outputs[0], sub.inputs[0])
    ng.links.new(inp.outputs['Y'], sub.inputs[1])

    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(mul.outputs[0], add.inputs[0])
    ng.links.new(sub.outputs[0], add.inputs[1])

    ng.links.new(add.outputs[0], out.inputs['Vein Coord'])
    return ng


def make_shape_with_jigsaw():
    ng = bpy.data.node_groups.new("nodegroup_nodegroup_shape_with_jigsaw", 'GeometryNodeTree')
    ng.interface.new_socket('Midrib Value', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Coord', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Leaf Shape', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Jigsaw Scale', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Jigsaw Depth', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Midrib Value': item.default_value = 1.0
            elif item.name == 'Vein Coord': item.default_value = 0.0
            elif item.name == 'Leaf Shape': item.default_value = 0.5
            elif item.name == 'Jigsaw Scale': item.default_value = 18.0
            elif item.name == 'Jigsaw Depth': item.default_value = 0.5
    ng.interface.new_socket('Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Midrib Value'], mr.inputs['Value'])
    mr.inputs[3].default_value = 1.0
    mr.inputs[4].default_value = 0.0

    jigsaw = ng.nodes.new('ShaderNodeTexVoronoi'); jigsaw.voronoi_dimensions = '1D'
    ng.links.new(inp.outputs['Vein Coord'], jigsaw.inputs['W'])
    ng.links.new(inp.outputs['Jigsaw Scale'], jigsaw.inputs['Scale'])

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Jigsaw Depth'], mul.inputs[0])
    mul.inputs[1].default_value = 0.05

    mul_add = ng.nodes.new('ShaderNodeMath'); mul_add.operation = 'MULTIPLY_ADD'; mul_add.use_clamp = True
    ng.links.new(jigsaw.outputs['Distance'], mul_add.inputs[0])
    ng.links.new(mul.outputs[0], mul_add.inputs[1])
    ng.links.new(inp.outputs['Leaf Shape'], mul_add.inputs[2])

    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(mul_add.outputs[0], mr1.inputs['Value'])
    mr1.inputs[1].default_value = 0.001
    mr1.inputs[2].default_value = 0.002
    mr1.inputs[3].default_value = 1.0
    mr1.inputs[4].default_value = 0.0

    mx = ng.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
    ng.links.new(mr.outputs['Result'], mx.inputs[0])
    ng.links.new(mr1.outputs['Result'], mx.inputs[1])

    ng.links.new(mx.outputs[0], out.inputs['Value'])
    return ng


def make_vein_coord(vein_curve_control_points, vein_curve_control_handles):
    ng = bpy.data.node_groups.new("nodegroup_nodegroup_vein_coord", 'GeometryNodeTree')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Asymmetry', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Leaf Shape', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X Modulated': item.default_value = 0.5
            elif item.name == 'Y': item.default_value = 0.5
            elif item.name == 'Vein Asymmetry': item.default_value = 0.0
            elif item.name == 'Vein Angle': item.default_value = 2.0
            elif item.name == 'Leaf Shape': item.default_value = 0.0
    ng.interface.new_socket('Vein Coord', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    sign = ng.nodes.new('ShaderNodeMath'); sign.operation = 'SIGN'
    ng.links.new(inp.outputs['X Modulated'], sign.inputs[0])

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Vein Asymmetry'], mul.inputs[0])
    ng.links.new(sign.outputs[0], mul.inputs[1])

    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], mr.inputs['Value'])
    mr.inputs[1].default_value = -1.0

    abs_n = ng.nodes.new('ShaderNodeMath'); abs_n.operation = 'ABSOLUTE'; abs_n.use_clamp = True
    ng.links.new(inp.outputs['X Modulated'], abs_n.inputs[0])

    div = ng.nodes.new('ShaderNodeMath'); div.operation = 'DIVIDE'; div.use_clamp = True
    ng.links.new(abs_n.outputs[0], div.inputs[0])
    ng.links.new(inp.outputs['Leaf Shape'], div.inputs[1])

    vein_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(div.outputs[0], vein_shape.inputs['Value'])
    _assign_curve(vein_shape.mapping.curves[0], vein_curve_control_points, vein_curve_control_handles)

    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(vein_shape.outputs[0], mr1.inputs['Value'])
    mr1.inputs[4].default_value = 1.9

    mul_1 = ng.nodes.new('ShaderNodeMath'); mul_1.operation = 'MULTIPLY'
    ng.links.new(mr1.outputs['Result'], mul_1.inputs[0])
    ng.links.new(inp.outputs['Vein Angle'], mul_1.inputs[1])

    mul_2 = ng.nodes.new('ShaderNodeMath'); mul_2.operation = 'MULTIPLY'
    ng.links.new(mr.outputs['Result'], mul_2.inputs[0])
    ng.links.new(mul_1.outputs[0], mul_2.inputs[1])

    sub = ng.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
    ng.links.new(mul_2.outputs[0], sub.inputs[0])
    ng.links.new(inp.outputs['Y'], sub.inputs[1])

    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(mul.outputs[0], add.inputs[0])
    ng.links.new(sub.outputs[0], add.inputs[1])

    ng.links.new(add.outputs[0], out.inputs['Vein Coord'])
    return ng


def make_shape(shape_curve_control_points):
    ng = bpy.data.node_groups.new("nodegroup_nodegroup_shape", 'GeometryNodeTree')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X Modulated': item.default_value = 0.0
            elif item.name == 'Y': item.default_value = 0.0
    ng.interface.new_socket('Leaf Shape', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(inp.outputs['X Modulated'], comb.inputs['X'])
    ng.links.new(inp.outputs['Y'], comb.inputs['Y'])

    clamp = ng.nodes.new('ShaderNodeClamp')
    ng.links.new(inp.outputs['Y'], clamp.inputs['Value'])
    clamp.inputs['Min'].default_value = -0.6
    clamp.inputs['Max'].default_value = 0.6

    comb_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(clamp.outputs[0], comb_1.inputs['Y'])

    sub = ng.nodes.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'
    ng.links.new(comb.outputs[0], sub.inputs[0])
    ng.links.new(comb_1.outputs[0], sub.inputs[1])

    length = ng.nodes.new('ShaderNodeVectorMath'); length.operation = 'LENGTH'
    ng.links.new(sub.outputs['Vector'], length.inputs[0])

    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], mr.inputs['Value'])
    mr.inputs[1].default_value = -0.6
    mr.inputs[2].default_value = 0.6

    leaf_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr.outputs['Result'], leaf_shape.inputs['Value'])
    _assign_curve(leaf_shape.mapping.curves[0], shape_curve_control_points)

    sub_1 = ng.nodes.new('ShaderNodeMath'); sub_1.operation = 'SUBTRACT'
    ng.links.new(length.outputs['Value'], sub_1.inputs[0])
    ng.links.new(leaf_shape.outputs[0], sub_1.inputs[1])

    ng.links.new(sub_1.outputs[0], out.inputs['Leaf Shape'])
    ng.links.new(leaf_shape.outputs[0], out.inputs['Value'])
    return ng


def make_midrib(midrib_curve_control_points):
    ng = bpy.data.node_groups.new("nodegroup_nodegroup_midrib", 'GeometryNodeTree')
    ng.interface.new_socket('X', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Midrib Length', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Midrib Width', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Stem Length', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X': item.default_value = 0.5
            elif item.name == 'Y': item.default_value = -0.6
            elif item.name == 'Midrib Length': item.default_value = 0.4
            elif item.name == 'Midrib Width': item.default_value = 1.0
            elif item.name == 'Stem Length': item.default_value = 0.8
    ng.interface.new_socket('X Modulated', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Midrib Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], mr.inputs['Value'])
    mr.inputs[1].default_value = -0.6
    mr.inputs[2].default_value = 0.6

    stem_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr.outputs['Result'], stem_shape.inputs['Value'])
    _assign_curve(stem_shape.mapping.curves[0], midrib_curve_control_points)

    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(stem_shape.outputs[0], mr1.inputs['Value'])
    mr1.inputs[3].default_value = -1.0

    sub = ng.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
    ng.links.new(mr1.outputs['Result'], sub.inputs[0])
    ng.links.new(inp.outputs['X'], sub.inputs[1])

    noise = ng.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 20.0

    # Blender 5.0: "Fac" renamed to "Factor"; use index 0
    mr5 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(noise.outputs[0], mr5.inputs['Value'])
    mr5.inputs[3].default_value = -1.0

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(mr5.outputs['Result'], mul.inputs[0])
    mul.inputs[1].default_value = 0.01

    mr2 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], mr2.inputs['Value'])
    mr2.inputs[1].default_value = -70.0
    ng.links.new(inp.outputs['Midrib Length'], mr2.inputs[2])
    ng.links.new(inp.outputs['Midrib Width'], mr2.inputs[3])
    mr2.inputs[4].default_value = 0.0

    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(mul.outputs[0], add.inputs[0])
    ng.links.new(mr2.outputs['Result'], add.inputs[1])

    abs_n = ng.nodes.new('ShaderNodeMath'); abs_n.operation = 'ABSOLUTE'
    ng.links.new(sub.outputs[0], abs_n.inputs[0])

    sub_1 = ng.nodes.new('ShaderNodeMath'); sub_1.operation = 'SUBTRACT'
    ng.links.new(add.outputs[0], sub_1.inputs[0])
    ng.links.new(abs_n.outputs[0], sub_1.inputs[1])

    abs_1 = ng.nodes.new('ShaderNodeMath'); abs_1.operation = 'ABSOLUTE'
    ng.links.new(inp.outputs['Y'], abs_1.inputs[0])

    mr3 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(abs_1.outputs[0], mr3.inputs['Value'])
    ng.links.new(inp.outputs['Stem Length'], mr3.inputs[2])
    mr3.inputs[3].default_value = 1.0
    mr3.inputs[4].default_value = 0.0

    smooth_min = ng.nodes.new('ShaderNodeMath'); smooth_min.operation = 'SMOOTH_MIN'
    ng.links.new(sub_1.outputs[0], smooth_min.inputs[0])
    ng.links.new(mr3.outputs['Result'], smooth_min.inputs[1])
    smooth_min.inputs[2].default_value = 0.06

    div = ng.nodes.new('ShaderNodeMath'); div.operation = 'DIVIDE'; div.use_clamp = True
    div.inputs[0].default_value = 1.0
    ng.links.new(smooth_min.outputs[0], div.inputs[1])

    mr4 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(div.outputs[0], mr4.inputs['Value'])
    mr4.inputs[1].default_value = 0.001
    mr4.inputs[2].default_value = 0.03
    mr4.inputs[3].default_value = 1.0
    mr4.inputs[4].default_value = 0.0

    ng.links.new(sub.outputs[0], out.inputs['X Modulated'])
    ng.links.new(mr4.outputs['Result'], out.inputs['Midrib Value'])
    return ng


def make_apply_vein_midrib(random_scale_seed=1.08):
    ng = bpy.data.node_groups.new("nodegroup_nodegroup_apply_vein_midrib", 'GeometryNodeTree')
    ng.interface.new_socket('Midrib Value', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Leaf Shape', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Density', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Coord - main', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Coord - 1', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Coord - 2', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Midrib Value': item.default_value = 0.5
            elif item.name == 'Leaf Shape': item.default_value = 1.0
            elif item.name == 'Vein Density': item.default_value = 6.0
    ng.interface.new_socket('Vein Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    mr = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Leaf Shape'], mr.inputs['Value'])
    mr.inputs[1].default_value = -0.3
    mr.inputs[2].default_value = 0.05
    mr.inputs[3].default_value = 0.015
    mr.inputs[4].default_value = 0.0

    # nodegroup (random_mask_vein) for Vein Coord - 2
    rmv_ng = make_random_mask_vein()
    nodegroup_node = ng.nodes.new('GeometryNodeGroup')
    nodegroup_node.node_tree = rmv_ng
    ng.links.new(inp.outputs['Vein Coord - 2'], nodegroup_node.inputs['Coord'])
    ng.links.new(mr.outputs['Result'], nodegroup_node.inputs['Shape'])
    ng.links.new(inp.outputs['Vein Density'], nodegroup_node.inputs['Density'])
    nodegroup_node.inputs['Random Scale Seed'].default_value = random_scale_seed * 2.7

    # nodegroup_1 (random_mask_vein) for Vein Coord - 1
    rmv_ng_1 = make_random_mask_vein()
    nodegroup_node_1 = ng.nodes.new('GeometryNodeGroup')
    nodegroup_node_1.node_tree = rmv_ng_1
    ng.links.new(inp.outputs['Vein Coord - 1'], nodegroup_node_1.inputs['Coord'])
    ng.links.new(mr.outputs['Result'], nodegroup_node_1.inputs['Shape'])
    ng.links.new(inp.outputs['Vein Density'], nodegroup_node_1.inputs['Density'])
    nodegroup_node_1.inputs['Random Scale Seed'].default_value = random_scale_seed

    # Vein voronoi on main coord
    vein = ng.nodes.new('ShaderNodeTexVoronoi'); vein.voronoi_dimensions = '1D'
    ng.links.new(inp.outputs['Vein Coord - main'], vein.inputs['W'])
    ng.links.new(inp.outputs['Vein Density'], vein.inputs['Scale'])
    vein.inputs['Randomness'].default_value = 0.2

    position = ng.nodes.new('GeometryNodeInputPosition')
    noise = ng.nodes.new('ShaderNodeTexNoise')
    ng.links.new(position.outputs[0], noise.inputs['Vector'])
    noise.inputs['Scale'].default_value = 20.0

    mr3 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(noise.outputs[0], mr3.inputs['Value'])
    mr3.inputs[3].default_value = -1.0

    mul_noise = ng.nodes.new('ShaderNodeMath'); mul_noise.operation = 'MULTIPLY'
    ng.links.new(mr3.outputs['Result'], mul_noise.inputs[0])
    mul_noise.inputs[1].default_value = 0.02

    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(vein.outputs['Distance'], add.inputs[0])
    ng.links.new(mul_noise.outputs[0], add.inputs[1])

    mr4 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(add.outputs[0], mr4.inputs['Value'])
    mr4.inputs[2].default_value = 0.03
    mr4.inputs[3].default_value = 1.0
    mr4.inputs[4].default_value = 0.0

    mul_1 = ng.nodes.new('ShaderNodeMath'); mul_1.operation = 'MULTIPLY'
    ng.links.new(mr.outputs['Result'], mul_1.inputs[0])
    ng.links.new(mr4.outputs['Result'], mul_1.inputs[1])

    mr5 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(mul_1.outputs[0], mr5.inputs['Value'])
    mr5.inputs[1].default_value = 0.001
    mr5.inputs[2].default_value = 0.01
    mr5.inputs[3].default_value = 1.0
    mr5.inputs[4].default_value = 0.0

    mul_2 = ng.nodes.new('ShaderNodeMath'); mul_2.operation = 'MULTIPLY'
    ng.links.new(nodegroup_node_1.outputs['Result'], mul_2.inputs[0])
    ng.links.new(mr5.outputs['Result'], mul_2.inputs[1])

    mul_3 = ng.nodes.new('ShaderNodeMath'); mul_3.operation = 'MULTIPLY'
    ng.links.new(nodegroup_node.outputs['Result'], mul_3.inputs[0])
    ng.links.new(mul_2.outputs[0], mul_3.inputs[1])

    mul_4 = ng.nodes.new('ShaderNodeMath'); mul_4.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Midrib Value'], mul_4.inputs[0])
    ng.links.new(mul_3.outputs[0], mul_4.inputs[1])

    ng.links.new(mul_4.outputs[0], out.inputs['Vein Value'])
    return ng


def make_sub_vein():
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

    abs_n = ng.nodes.new('ShaderNodeMath'); abs_n.operation = 'ABSOLUTE'
    ng.links.new(inp.outputs['X'], abs_n.inputs[0])

    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(abs_n.outputs[0], comb.inputs['X'])
    ng.links.new(inp.outputs['Y'], comb.inputs['Y'])

    vor = ng.nodes.new('ShaderNodeTexVoronoi')
    ng.links.new(comb.outputs[0], vor.inputs['Vector'])
    vor.inputs['Scale'].default_value = 30.0

    mr = ng.nodes.new('ShaderNodeMapRange'); mr.clamp = False
    ng.links.new(vor.outputs['Distance'], mr.inputs['Value'])
    mr.inputs[2].default_value = 0.1
    mr.inputs[4].default_value = 2.0

    vor_1 = ng.nodes.new('ShaderNodeTexVoronoi'); vor_1.feature = 'DISTANCE_TO_EDGE'
    ng.links.new(comb.outputs[0], vor_1.inputs['Vector'])
    vor_1.inputs['Scale'].default_value = 150.0

    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(vor_1.outputs['Distance'], mr1.inputs['Value'])
    mr1.inputs[2].default_value = 0.1

    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(mr.outputs['Result'], add.inputs[0])
    ng.links.new(mr1.outputs['Result'], add.inputs[1])

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(add.outputs[0], mul.inputs[0])
    mul.inputs[1].default_value = -1.0

    mr3 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(mr1.outputs['Result'], mr3.inputs['Value'])
    mr3.inputs[4].default_value = -1.0

    ng.links.new(mul.outputs[0], out.inputs['Value'])
    ng.links.new(mr3.outputs['Result'], out.inputs['Color Value'])
    return ng


def make_leaf_gen(**kwargs):
    ng = bpy.data.node_groups.new("nodegroup_nodegroup_leaf_gen", 'GeometryNodeTree')
    ng.interface.new_socket('Mesh', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Displancement scale', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Asymmetry', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Density', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Jigsaw Scale', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Jigsaw Depth', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Sub-vein Displacement', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Sub-vein Scale', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Wave Displacement', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Midrib Length', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Midrib Width', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Stem Length', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Displancement scale': item.default_value = 0.5
            elif item.name == 'Vein Asymmetry': item.default_value = 0.0
            elif item.name == 'Vein Density': item.default_value = 6.0
            elif item.name == 'Jigsaw Scale': item.default_value = 18.0
            elif item.name == 'Jigsaw Depth': item.default_value = 0.07
            elif item.name == 'Vein Angle': item.default_value = 1.0
            elif item.name == 'Sub-vein Displacement': item.default_value = 0.5
            elif item.name == 'Sub-vein Scale': item.default_value = 50.0
            elif item.name == 'Wave Displacement': item.default_value = 0.1
            elif item.name == 'Midrib Length': item.default_value = 0.4
            elif item.name == 'Midrib Width': item.default_value = 1.0
            elif item.name == 'Stem Length': item.default_value = 0.8
    ng.interface.new_socket('Mesh', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Attribute', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('X Modulated', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Coord', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    position = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], sep.inputs['Vector'])

    # Midrib sub-group
    midrib_ng = make_midrib(kwargs["midrib_curve_control_points"])
    midrib = ng.nodes.new('GeometryNodeGroup')
    midrib.node_tree = midrib_ng
    ng.links.new(sep.outputs['X'], midrib.inputs['X'])
    ng.links.new(sep.outputs['Y'], midrib.inputs['Y'])
    ng.links.new(inp.outputs['Midrib Length'], midrib.inputs['Midrib Length'])
    ng.links.new(inp.outputs['Midrib Width'], midrib.inputs['Midrib Width'])
    ng.links.new(inp.outputs['Stem Length'], midrib.inputs['Stem Length'])

    # Shape sub-group
    shape_ng = make_shape(kwargs["shape_curve_control_points"])
    shape = ng.nodes.new('GeometryNodeGroup')
    shape.node_tree = shape_ng
    ng.links.new(midrib.outputs['X Modulated'], shape.inputs['X Modulated'])
    ng.links.new(sep.outputs['Y'], shape.inputs['Y'])

    # Vein coord (main) with specific curve
    vc_ng = make_vein_coord(
        [(0.0, 0.0), (0.0182, 0.05), (0.3364, 0.2386), (0.6045, 0.4812), (0.7, 0.725), (0.8273, 0.8437), (1.0, 1.0)],
        ["AUTO", "AUTO", "AUTO", "VECTOR", "AUTO", "AUTO", "AUTO"])
    vc = ng.nodes.new('GeometryNodeGroup')
    vc.node_tree = vc_ng
    ng.links.new(midrib.outputs['X Modulated'], vc.inputs['X Modulated'])
    ng.links.new(sep.outputs['Y'], vc.inputs['Y'])
    ng.links.new(inp.outputs['Vein Asymmetry'], vc.inputs['Vein Asymmetry'])
    ng.links.new(inp.outputs['Vein Angle'], vc.inputs['Vein Angle'])
    ng.links.new(shape.outputs['Value'], vc.inputs['Leaf Shape'])

    # Vein coord 002
    vc2_ng = make_vein_coord(
        [(0.0, 0.0), (0.0182, 0.05), (0.3364, 0.2386), (0.8091, 0.7312), (1.0, 0.9937)],
        ["AUTO", "AUTO", "AUTO", "AUTO", "AUTO"])
    vc2 = ng.nodes.new('GeometryNodeGroup')
    vc2.node_tree = vc2_ng
    ng.links.new(midrib.outputs['X Modulated'], vc2.inputs['X Modulated'])
    ng.links.new(sep.outputs['Y'], vc2.inputs['Y'])
    ng.links.new(inp.outputs['Vein Asymmetry'], vc2.inputs['Vein Asymmetry'])
    ng.links.new(inp.outputs['Vein Angle'], vc2.inputs['Vein Angle'])
    ng.links.new(shape.outputs['Value'], vc2.inputs['Leaf Shape'])

    # Vein coord 003
    vc3_ng = make_vein_coord(
        [(0.0, 0.0), (0.0182, 0.05), (0.2909, 0.2199), (0.4182, 0.3063), (0.7045, 0.3), (1.0, 0.8562)],
        ["AUTO", "AUTO", "AUTO", "VECTOR", "AUTO", "AUTO"])
    vc3 = ng.nodes.new('GeometryNodeGroup')
    vc3.node_tree = vc3_ng
    ng.links.new(midrib.outputs['X Modulated'], vc3.inputs['X Modulated'])
    ng.links.new(sep.outputs['Y'], vc3.inputs['Y'])
    ng.links.new(inp.outputs['Vein Asymmetry'], vc3.inputs['Vein Asymmetry'])
    ng.links.new(inp.outputs['Vein Angle'], vc3.inputs['Vein Angle'])
    ng.links.new(shape.outputs['Value'], vc3.inputs['Leaf Shape'])

    # Apply vein midrib
    avm_ng = make_apply_vein_midrib(kwargs["vein_mask_random_seed"])
    avm = ng.nodes.new('GeometryNodeGroup')
    avm.node_tree = avm_ng
    ng.links.new(midrib.outputs['Midrib Value'], avm.inputs['Midrib Value'])
    ng.links.new(shape.outputs['Leaf Shape'], avm.inputs['Leaf Shape'])
    ng.links.new(inp.outputs['Vein Density'], avm.inputs['Vein Density'])
    ng.links.new(vc2.outputs['Vein Coord'], avm.inputs['Vein Coord - main'])
    ng.links.new(vc.outputs['Vein Coord'], avm.inputs['Vein Coord - 1'])
    ng.links.new(vc3.outputs['Vein Coord'], avm.inputs['Vein Coord - 2'])

    # Displacement from vein
    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Displancement scale'], mul.inputs[0])
    ng.links.new(avm.outputs['Vein Value'], mul.inputs[1])

    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(mul.outputs[0], comb.inputs['Z'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(inp.outputs['Mesh'], set_pos.inputs['Geometry'])
    ng.links.new(comb.outputs[0], set_pos.inputs['Offset'])

    # Shape with jigsaw
    swj_ng = make_shape_with_jigsaw()
    swj = ng.nodes.new('GeometryNodeGroup')
    swj.node_tree = swj_ng
    ng.links.new(midrib.outputs['Midrib Value'], swj.inputs['Midrib Value'])
    ng.links.new(vc2.outputs['Vein Coord'], swj.inputs['Vein Coord'])
    ng.links.new(shape.outputs['Leaf Shape'], swj.inputs['Leaf Shape'])
    ng.links.new(inp.outputs['Jigsaw Scale'], swj.inputs['Jigsaw Scale'])
    ng.links.new(inp.outputs['Jigsaw Depth'], swj.inputs['Jigsaw Depth'])

    # Compare (less than)
    less = ng.nodes.new('FunctionNodeCompare'); less.operation = 'LESS_THAN'
    ng.links.new(swj.outputs['Value'], less.inputs[0])
    less.inputs[1].default_value = 0.5

    # Delete geometry
    delete = ng.nodes.new('GeometryNodeDeleteGeometry')
    ng.links.new(set_pos.outputs[0], delete.inputs['Geometry'])
    ng.links.new(less.outputs[0], delete.inputs['Selection'])

    # CaptureAttribute (Blender 5.0: must add capture channel)
    capture = ng.nodes.new('GeometryNodeCaptureAttribute')
    capture.capture_items.new('FLOAT', 'Value')
    ng.links.new(delete.outputs[0], capture.inputs['Geometry'])
    ng.links.new(avm.outputs['Vein Value'], capture.inputs['Value'])

    # Leaf surface curvature offset
    position_1 = ng.nodes.new('GeometryNodeInputPosition')
    sep_1 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position_1.outputs[0], sep_1.inputs['Vector'])

    mr1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(sep_1.outputs['Y'], mr1.inputs['Value'])
    mr1.inputs[1].default_value = -0.6
    mr1.inputs[2].default_value = 0.6

    fc1 = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr1.outputs['Result'], fc1.inputs['Value'])
    _assign_curve(fc1.mapping.curves[0], [(0.0, 0.0), (0.5182, 1.0), (1.0, 1.0)])

    mr_ls = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(shape.outputs['Leaf Shape'], mr_ls.inputs['Value'])
    mr_ls.inputs[2].default_value = -1.0

    fc2 = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(mr_ls.outputs['Result'], fc2.inputs['Value'])
    _assign_curve(fc2.mapping.curves[0], [(0.0045, 0.0063), (0.0409, 0.0375), (0.4182, 0.05), (1.0, 0.0)])

    mul_1 = ng.nodes.new('ShaderNodeMath'); mul_1.operation = 'MULTIPLY'
    ng.links.new(fc1.outputs[0], mul_1.inputs[0])
    ng.links.new(fc2.outputs[0], mul_1.inputs[1])

    mul_2 = ng.nodes.new('ShaderNodeMath'); mul_2.operation = 'MULTIPLY'
    ng.links.new(mul_1.outputs[0], mul_2.inputs[0])
    mul_2.inputs[1].default_value = 0.7

    comb_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(mul_2.outputs[0], comb_1.inputs['Z'])

    set_pos_1 = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(capture.outputs['Geometry'], set_pos_1.inputs['Geometry'])
    ng.links.new(comb_1.outputs[0], set_pos_1.inputs['Offset'])

    # Vein coord 001 sub-group
    vc001_ng = make_vein_coord_001()
    vc001 = ng.nodes.new('GeometryNodeGroup')
    vc001.node_tree = vc001_ng
    ng.links.new(midrib.outputs['X Modulated'], vc001.inputs['X Modulated'])
    ng.links.new(sep.outputs['Y'], vc001.inputs['Y'])
    ng.links.new(inp.outputs['Vein Asymmetry'], vc001.inputs['Vein Asymmetry'])
    ng.links.new(inp.outputs['Vein Angle'], vc001.inputs['Vein Angle'])

    # Outputs
    ng.links.new(set_pos_1.outputs[0], out.inputs['Mesh'])
    ng.links.new(capture.outputs['Value'], out.inputs['Attribute'])
    ng.links.new(midrib.outputs['X Modulated'], out.inputs['X Modulated'])
    ng.links.new(vc001.outputs['Vein Coord'], out.inputs['Vein Coord'])
    ng.links.new(avm.outputs['Vein Value'], out.inputs['Vein Value'])
    return ng


def make_geo_leaf_broadleaf(**kwargs):
    """Build the top-level GeoNodes tree for broadleaf. Returns the node group."""

    ng = bpy.data.node_groups.new("geo_leaf_broadleaf", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Offset', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Coordinate', in_out='OUTPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('subvein offset', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('vein value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # Subdivide mesh (level 10)
    subdiv = ng.nodes.new('GeometryNodeSubdivideMesh')
    ng.links.new(inp.outputs['Geometry'], subdiv.inputs['Mesh'])
    subdiv.inputs['Level'].default_value = 10

    # Capture initial position (FLOAT_VECTOR)
    position = ng.nodes.new('GeometryNodeInputPosition')
    cap0 = ng.nodes.new('GeometryNodeCaptureAttribute')
    cap0.capture_items.new('VECTOR', 'Value')
    ng.links.new(subdiv.outputs[0], cap0.inputs['Geometry'])
    ng.links.new(position.outputs[0], cap0.inputs['Value'])

    # Leaf gen sub-group
    lg_ng = make_leaf_gen(**kwargs)
    lg = ng.nodes.new('GeometryNodeGroup')
    lg.node_tree = lg_ng
    ng.links.new(cap0.outputs['Geometry'], lg.inputs['Mesh'])
    lg.inputs['Displancement scale'].default_value = 0.005
    # Wire up parameter inputs as constants (set on the socket)
    lg.inputs['Vein Asymmetry'].default_value = kwargs["vein_asymmetry"]
    lg.inputs['Vein Density'].default_value = kwargs["vein_density"]
    lg.inputs['Jigsaw Scale'].default_value = kwargs["jigsaw_scale"]
    lg.inputs['Jigsaw Depth'].default_value = kwargs["jigsaw_depth"]
    lg.inputs['Vein Angle'].default_value = kwargs["vein_angle"]
    lg.inputs['Midrib Length'].default_value = kwargs["midrib_length"]
    lg.inputs['Midrib Width'].default_value = kwargs["midrib_length"]
    lg.inputs['Stem Length'].default_value = kwargs["stem_length"]

    # Sub-vein sub-group
    sv_ng = make_sub_vein()
    sv = ng.nodes.new('GeometryNodeGroup')
    sv.node_tree = sv_ng
    ng.links.new(lg.outputs['X Modulated'], sv.inputs['X'])
    ng.links.new(lg.outputs['Vein Coord'], sv.inputs['Y'])

    # Sub-vein displacement
    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(sv.outputs['Value'], mul.inputs[0])
    mul.inputs[1].default_value = 0.0002

    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(mul.outputs[0], comb.inputs['Z'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(lg.outputs['Mesh'], set_pos.inputs['Geometry'])
    ng.links.new(comb.outputs[0], set_pos.inputs['Offset'])

    # Capture sub-vein color value
    cap1 = ng.nodes.new('GeometryNodeCaptureAttribute')
    cap1.capture_items.new('FLOAT', 'Value')
    ng.links.new(set_pos.outputs[0], cap1.inputs['Geometry'])
    ng.links.new(sv.outputs['Color Value'], cap1.inputs['Value'])

    # Capture vein value
    cap2 = ng.nodes.new('GeometryNodeCaptureAttribute')
    cap2.capture_items.new('FLOAT', 'Value')
    ng.links.new(cap1.outputs['Geometry'], cap2.inputs['Geometry'])
    ng.links.new(lg.outputs['Vein Value'], cap2.inputs['Value'])

    # Apply wave sub-group
    aw_ng = make_apply_wave(kwargs["y_wave_control_points"], kwargs["x_wave_control_points"])
    aw = ng.nodes.new('GeometryNodeGroup')
    aw.node_tree = aw_ng
    ng.links.new(cap2.outputs['Geometry'], aw.inputs['Geometry'])
    aw.inputs['Wave Scale X'].default_value = 0.2
    aw.inputs['Wave Scale Y'].default_value = 1.0
    ng.links.new(lg.outputs['X Modulated'], aw.inputs['X Modulated'])

    # Move to origin sub-group
    mto_ng = make_move_to_origin()
    mto = ng.nodes.new('GeometryNodeGroup')
    mto.node_tree = mto_ng
    ng.links.new(aw.outputs['Geometry'], mto.inputs['Geometry'])

    # Wire outputs
    ng.links.new(mto.outputs['Geometry'], out.inputs['Geometry'])
    ng.links.new(lg.outputs['Attribute'], out.inputs['Offset'])
    ng.links.new(cap0.outputs['Value'], out.inputs['Coordinate'])
    ng.links.new(cap1.outputs['Value'], out.inputs['subvein offset'])
    ng.links.new(cap2.outputs['Value'], out.inputs['vein value'])
    return ng


# ===================================================================
# Factory class (preserved from original)
# ===================================================================

class AssetFactory:
    def __init__(self, factory_seed=None, coarse=False):
        self.factory_seed = int(factory_seed if factory_seed is not None else np.random.randint(1e9))
        self.coarse = coarse
    def __call__(self, i=0, **kwargs):
        with FixedSeed(int_hash((self.factory_seed, i))):
            return self.create_asset(i=i, **kwargs)


class LeafFactoryBroadleaf(AssetFactory):
    scale = 0.5

    def __init__(self, factory_seed, season="autumn", coarse=False):
        super(LeafFactoryBroadleaf, self).__init__(factory_seed, coarse=coarse)

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
        leaf_width_1 = uniform(0.2, 0.4)
        leaf_width_2 = uniform(0.1, leaf_width_1)

        leaf_offset_1 = uniform(0.49, 0.51)

        return {
            "midrib_length": uniform(0.0, 0.8),
            "midrib_width": uniform(0.5, 1.0),
            "stem_length": uniform(0.7, 0.9),
            "vein_asymmetry": uniform(0.0, 1.0),
            "vein_angle": uniform(0.4, 1.0),
            "vein_density": uniform(3.0, 8.0),
            "subvein_scale": uniform(10.0, 20.0),
            "jigsaw_scale": uniform(30.0, 70.0),
            "jigsaw_depth": uniform(0.0, 0.6),
            "vein_mask_random_seed": uniform(0.0, 100.0),
            "midrib_curve_control_points": [
                (0.0, 0.5),
                (0.25, leaf_offset_1),
                (0.75, 1.0 - leaf_offset_1),
                (1.0, 0.5),
            ],
            "shape_curve_control_points": [
                (0.0, 0.0),
                (uniform(0.2, 0.4), leaf_width_1),
                (uniform(0.6, 0.8), leaf_width_2),
                (1.0, 0.0),
            ],
            "vein_curve_control_points": [
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
        geo_ng = make_geo_leaf_broadleaf(**phenome)
        mod = obj.modifiers.new(name="geo_leaf_broadleaf", type='NODES')
        mod.node_group = geo_ng

        # Apply attributes by name (mirrors old surface.add_geomod attributes= logic)
        attr_names = ["offset", "coordinate", "subvein offset", "vein value"]
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
        obj.scale *= normal(1, 0.1) * self.scale
        apply_transform(obj)
        tag_object(obj, "leaf_broadleaf")

        return obj

def build(seed=0, season="autumn"):
    fac = LeafFactoryBroadleaf(seed, season)
    with FixedSeed(int_hash((seed, seed))):
        return fac.create_asset()

SEED = 0
build(SEED)
