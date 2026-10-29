# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafV2Factory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafV2Factory | Category: factories_geo
# Prompt: A 3D model of a serrated leaf rendered from a three-quarter perspective. The leaf features an elongated ovate blade with prominent toothed or serrated edges creating a jagged sawtooth margin along both sides, a pointed tip, a short petiole stem, and a gently curved surface with a visible central midrib.

import bpy
import numpy as np
import random
import hashlib
import logging
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

def wrap_gaussian(mean, std, low=0, high=1):
    x = np.random.normal(mean, std)
    if x < low:
        x = high - (low - x) % (high - low)
    elif x > high:
        x = low + (x - high) % (high - low)
    return x

class _ColorsNS:
    @staticmethod
    def hsv2rgba(hsv):
        return hsv2rgba(hsv)
    @staticmethod
    def plant_green():
        return (uniform(0.25, 0.33), normal(0.65, 0.03), uniform(0.1, 0.45))
    @staticmethod
    def plant_red():
        return (wrap_gaussian(0.0, 0.05), normal(0.9, 0.03), normal(0.6, 0.05))
    @staticmethod
    def plant_yellow():
        return (wrap_gaussian(0.15, 0.005), normal(0.95, 0.02), normal(0.9, 0.02))

colors = _ColorsNS()

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

class AssetFactory:
    def __init__(self, factory_seed=None, coarse=False):
        self.factory_seed = int(factory_seed if factory_seed is not None else np.random.randint(1e9))
        self.coarse = coarse
    def __call__(self, i=0, **kwargs):
        with FixedSeed(int_hash((self.factory_seed, i))):
            return self.create_asset(i=i, **kwargs)


# ===================================================================
# Node-group builder functions (direct bpy API, no NodeWrangler)
# ===================================================================

# -- Shader node groups (ShaderNodeTree) used by shader_leaf_new --

def make_shader_sub_vein():
    ng = bpy.data.node_groups.new("shader_nodegroup_sub_vein", 'ShaderNodeTree')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X Modulated': item.default_value = 0.5
            elif item.name == 'Y': item.default_value = 0.0
    ng.interface.new_socket('Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    absolute = ng.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'; absolute.use_clamp = True
    ng.links.new(inp.outputs['X Modulated'], absolute.inputs[0])

    combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(absolute.outputs[0], combine_xyz.inputs['X'])
    ng.links.new(inp.outputs['Y'], combine_xyz.inputs['Y'])

    voronoi_texture = ng.nodes.new('ShaderNodeTexVoronoi')
    voronoi_texture.feature = 'DISTANCE_TO_EDGE'
    ng.links.new(combine_xyz.outputs[0], voronoi_texture.inputs['Vector'])
    voronoi_texture.inputs['Scale'].default_value = 30.0
    voronoi_texture.inputs['Randomness'].default_value = 0.754

    map_range = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(voronoi_texture.outputs['Distance'], map_range.inputs['Value'])
    map_range.inputs[2].default_value = 0.1
    map_range.inputs[4].default_value = 3.0

    voronoi_texture_1 = ng.nodes.new('ShaderNodeTexVoronoi')
    voronoi_texture_1.feature = 'DISTANCE_TO_EDGE'
    ng.links.new(combine_xyz.outputs[0], voronoi_texture_1.inputs['Vector'])
    voronoi_texture_1.inputs['Scale'].default_value = 10.0
    voronoi_texture_1.inputs['Randomness'].default_value = 0.754

    map_range_1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(voronoi_texture_1.outputs['Distance'], map_range_1.inputs['Value'])
    map_range_1.inputs[2].default_value = 0.1
    map_range_1.inputs[4].default_value = 3.0

    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(map_range.outputs['Result'], multiply.inputs[0])
    ng.links.new(map_range_1.outputs['Result'], multiply.inputs[1])

    ng.links.new(multiply.outputs[0], out.inputs['Value'])
    return ng


def make_shader_midrib(midrib_curve_control_points):
    ng = bpy.data.node_groups.new("shader_nodegroup_midrib", 'ShaderNodeTree')
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

    map_range_6 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], map_range_6.inputs['Value'])
    map_range_6.inputs[1].default_value = -0.6
    map_range_6.inputs[2].default_value = 0.6

    stem_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(map_range_6.outputs['Result'], stem_shape.inputs['Value'])
    _assign_curve(stem_shape.mapping.curves[0], midrib_curve_control_points)

    map_range_7 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(stem_shape.outputs[0], map_range_7.inputs['Value'])
    map_range_7.inputs[3].default_value = -1.0

    subtract = ng.nodes.new('ShaderNodeMath'); subtract.operation = 'SUBTRACT'
    ng.links.new(map_range_7.outputs['Result'], subtract.inputs[0])
    ng.links.new(inp.outputs['X'], subtract.inputs[1])

    map_range_8 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], map_range_8.inputs['Value'])
    map_range_8.inputs[1].default_value = -70.0
    ng.links.new(inp.outputs['Midrib Length'], map_range_8.inputs[2])
    ng.links.new(inp.outputs['Midrib Width'], map_range_8.inputs[3])
    map_range_8.inputs[4].default_value = 0.0

    absolute = ng.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'
    ng.links.new(subtract.outputs[0], absolute.inputs[0])

    subtract_1 = ng.nodes.new('ShaderNodeMath'); subtract_1.operation = 'SUBTRACT'
    ng.links.new(map_range_8.outputs['Result'], subtract_1.inputs[0])
    ng.links.new(absolute.outputs[0], subtract_1.inputs[1])

    absolute_1 = ng.nodes.new('ShaderNodeMath'); absolute_1.operation = 'ABSOLUTE'
    ng.links.new(inp.outputs['Y'], absolute_1.inputs[0])

    map_range_9 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(absolute_1.outputs[0], map_range_9.inputs['Value'])
    ng.links.new(inp.outputs['Stem Length'], map_range_9.inputs[2])
    map_range_9.inputs[3].default_value = 1.0
    map_range_9.inputs[4].default_value = 0.0

    smooth_min = ng.nodes.new('ShaderNodeMath'); smooth_min.operation = 'SMOOTH_MIN'
    ng.links.new(subtract_1.outputs[0], smooth_min.inputs[0])
    ng.links.new(map_range_9.outputs['Result'], smooth_min.inputs[1])
    smooth_min.inputs[2].default_value = 0.06

    divide = ng.nodes.new('ShaderNodeMath'); divide.operation = 'DIVIDE'; divide.use_clamp = True
    ng.links.new(map_range_8.outputs['Result'], divide.inputs[0])
    ng.links.new(smooth_min.outputs[0], divide.inputs[1])

    map_range_11 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(divide.outputs[0], map_range_11.inputs['Value'])
    map_range_11.inputs[1].default_value = 0.001
    map_range_11.inputs[2].default_value = 0.03
    map_range_11.inputs[3].default_value = 1.0
    map_range_11.inputs[4].default_value = 0.0

    ng.links.new(subtract.outputs[0], out.inputs['X Modulated'])
    ng.links.new(map_range_11.outputs['Result'], out.inputs['Midrib Value'])
    return ng


def make_shader_vein_coord(vein_curve_control_points):
    ng = bpy.data.node_groups.new("shader_nodegroup_vein_coord", 'ShaderNodeTree')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Asymmetry', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X Modulated': item.default_value = 0.5
            elif item.name == 'Y': item.default_value = 0.5
            elif item.name == 'Vein Asymmetry': item.default_value = 0.0
            elif item.name == 'Vein Angle': item.default_value = 2.0
    ng.interface.new_socket('Vein Coord', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    sign = ng.nodes.new('ShaderNodeMath'); sign.operation = 'SIGN'
    ng.links.new(inp.outputs['X Modulated'], sign.inputs[0])

    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(sign.outputs[0], multiply.inputs[0])
    ng.links.new(inp.outputs['Vein Asymmetry'], multiply.inputs[1])

    map_range_13 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], map_range_13.inputs['Value'])
    map_range_13.inputs[1].default_value = -1.0

    absolute = ng.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'; absolute.use_clamp = True
    ng.links.new(inp.outputs['X Modulated'], absolute.inputs[0])

    vein_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(absolute.outputs[0], vein_shape.inputs['Value'])
    _assign_curve(vein_shape.mapping.curves[0], vein_curve_control_points)

    map_range_4 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(vein_shape.outputs[0], map_range_4.inputs['Value'])
    map_range_4.inputs[2].default_value = 0.9
    map_range_4.inputs[4].default_value = 1.9

    multiply_1 = ng.nodes.new('ShaderNodeMath'); multiply_1.operation = 'MULTIPLY'
    ng.links.new(map_range_4.outputs['Result'], multiply_1.inputs[0])
    ng.links.new(inp.outputs['Vein Angle'], multiply_1.inputs[1])

    multiply_2 = ng.nodes.new('ShaderNodeMath'); multiply_2.operation = 'MULTIPLY'
    ng.links.new(map_range_13.outputs['Result'], multiply_2.inputs[0])
    ng.links.new(multiply_1.outputs[0], multiply_2.inputs[1])

    subtract = ng.nodes.new('ShaderNodeMath'); subtract.operation = 'SUBTRACT'
    ng.links.new(multiply_2.outputs[0], subtract.inputs[0])
    ng.links.new(inp.outputs['Y'], subtract.inputs[1])

    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(multiply.outputs[0], add.inputs[0])
    ng.links.new(subtract.outputs[0], add.inputs[1])

    ng.links.new(add.outputs[0], out.inputs['Vein Coord'])
    return ng


def make_shader_shape(shape_curve_control_points):
    ng = bpy.data.node_groups.new("shader_nodegroup_shape", 'ShaderNodeTree')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X Modulated': item.default_value = 0.0
            elif item.name == 'Y': item.default_value = 0.0
    ng.interface.new_socket('Leaf Shape', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    combine_xyz_2 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(inp.outputs['X Modulated'], combine_xyz_2.inputs['X'])
    ng.links.new(inp.outputs['Y'], combine_xyz_2.inputs['Y'])

    clamp = ng.nodes.new('ShaderNodeClamp')
    ng.links.new(inp.outputs['Y'], clamp.inputs['Value'])
    clamp.inputs['Min'].default_value = -0.6
    clamp.inputs['Max'].default_value = 0.6

    combine_xyz_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(clamp.outputs[0], combine_xyz_1.inputs['Y'])

    subtract = ng.nodes.new('ShaderNodeVectorMath'); subtract.operation = 'SUBTRACT'
    ng.links.new(combine_xyz_2.outputs[0], subtract.inputs[0])
    ng.links.new(combine_xyz_1.outputs[0], subtract.inputs[1])

    length = ng.nodes.new('ShaderNodeVectorMath'); length.operation = 'LENGTH'
    ng.links.new(subtract.outputs['Vector'], length.inputs[0])

    map_range_1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], map_range_1.inputs['Value'])
    map_range_1.inputs[1].default_value = -0.6
    map_range_1.inputs[2].default_value = 0.6

    leaf_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(map_range_1.outputs['Result'], leaf_shape.inputs['Value'])
    _assign_curve(leaf_shape.mapping.curves[0], shape_curve_control_points)

    subtract_1 = ng.nodes.new('ShaderNodeMath'); subtract_1.operation = 'SUBTRACT'
    ng.links.new(length.outputs['Value'], subtract_1.inputs[0])
    ng.links.new(leaf_shape.outputs[0], subtract_1.inputs[1])

    ng.links.new(subtract_1.outputs[0], out.inputs['Leaf Shape'])
    return ng


def make_shader_apply_vein_midrib():
    ng = bpy.data.node_groups.new("shader_nodegroup_apply_vein_midrib", 'ShaderNodeTree')
    ng.interface.new_socket('Vein Coord', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Midrib Value', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Leaf Shape', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Density', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Vein Coord': item.default_value = 0.0
            elif item.name == 'Midrib Value': item.default_value = 0.5
            elif item.name == 'Leaf Shape': item.default_value = 1.0
            elif item.name == 'Vein Density': item.default_value = 6.0
    ng.interface.new_socket('Vein Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    map_range_5 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Leaf Shape'], map_range_5.inputs['Value'])
    map_range_5.inputs[1].default_value = -0.3
    map_range_5.inputs[2].default_value = 0.0
    map_range_5.inputs[3].default_value = 0.015
    map_range_5.inputs[4].default_value = 0.0

    vein = ng.nodes.new('ShaderNodeTexVoronoi'); vein.voronoi_dimensions = '1D'
    ng.links.new(inp.outputs['Vein Coord'], vein.inputs['W'])
    ng.links.new(inp.outputs['Vein Density'], vein.inputs['Scale'])
    vein.inputs['Randomness'].default_value = 0.2

    map_range_3 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(vein.outputs['Distance'], map_range_3.inputs['Value'])
    map_range_3.inputs[1].default_value = 0.001
    map_range_3.inputs[2].default_value = 0.05
    map_range_3.inputs[3].default_value = 1.0
    map_range_3.inputs[4].default_value = 0.0

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(map_range_5.outputs['Result'], mul.inputs[0])
    ng.links.new(map_range_3.outputs['Result'], mul.inputs[1])

    map_range_10 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(mul.outputs[0], map_range_10.inputs['Value'])
    map_range_10.inputs[1].default_value = 0.001
    map_range_10.inputs[2].default_value = 0.01
    map_range_10.inputs[3].default_value = 1.0
    map_range_10.inputs[4].default_value = 0.0

    multiply_1 = ng.nodes.new('ShaderNodeMath'); multiply_1.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Midrib Value'], multiply_1.inputs[0])
    ng.links.new(map_range_10.outputs['Result'], multiply_1.inputs[1])

    ng.links.new(multiply_1.outputs[0], out.inputs['Vein Value'])
    return ng


def make_shader_leaf_gen(midrib_curve_control_points, vein_curve_control_points, shape_curve_control_points):
    ng = bpy.data.node_groups.new("shader_nodegroup_leaf_gen", 'ShaderNodeTree')
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
            if item.name == 'Displancement scale': item.default_value = 0.01
            elif item.name == 'Vein Asymmetry': item.default_value = 0.8
            elif item.name == 'Vein Density': item.default_value = 10.0
            elif item.name == 'Jigsaw Scale': item.default_value = 18.0
            elif item.name == 'Jigsaw Depth': item.default_value = 1.0
            elif item.name == 'Vein Angle': item.default_value = 1.0
            elif item.name == 'Sub-vein Displacement': item.default_value = 0.5
            elif item.name == 'Sub-vein Scale': item.default_value = 20.0
            elif item.name == 'Wave Displacement': item.default_value = 0.05
            elif item.name == 'Midrib Length': item.default_value = 0.4
            elif item.name == 'Midrib Width': item.default_value = 1.0
            elif item.name == 'Stem Length': item.default_value = 0.8
    ng.interface.new_socket('Vein Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Sub Vein Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    coordinate = ng.nodes.new('ShaderNodeAttribute')
    coordinate.attribute_name = "coordinate"

    separate_xyz = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(coordinate.outputs['Vector'], separate_xyz.inputs['Vector'])

    # Midrib sub-group
    midrib_ng = make_shader_midrib(midrib_curve_control_points)
    midrib = ng.nodes.new('ShaderNodeGroup')
    midrib.node_tree = midrib_ng
    ng.links.new(separate_xyz.outputs['X'], midrib.inputs['X'])
    ng.links.new(separate_xyz.outputs['Y'], midrib.inputs['Y'])
    ng.links.new(inp.outputs['Midrib Length'], midrib.inputs['Midrib Length'])
    ng.links.new(inp.outputs['Midrib Width'], midrib.inputs['Midrib Width'])
    ng.links.new(inp.outputs['Stem Length'], midrib.inputs['Stem Length'])

    # Vein coord sub-group
    vc_ng = make_shader_vein_coord(vein_curve_control_points)
    veincoord = ng.nodes.new('ShaderNodeGroup')
    veincoord.node_tree = vc_ng
    ng.links.new(midrib.outputs['X Modulated'], veincoord.inputs['X Modulated'])
    ng.links.new(separate_xyz.outputs['Y'], veincoord.inputs['Y'])
    ng.links.new(inp.outputs['Vein Asymmetry'], veincoord.inputs['Vein Asymmetry'])
    ng.links.new(inp.outputs['Vein Angle'], veincoord.inputs['Vein Angle'])

    # Shape sub-group
    shape_ng = make_shader_shape(shape_curve_control_points)
    shape = ng.nodes.new('ShaderNodeGroup')
    shape.node_tree = shape_ng
    ng.links.new(midrib.outputs['X Modulated'], shape.inputs['X Modulated'])
    ng.links.new(separate_xyz.outputs['Y'], shape.inputs['Y'])

    # Apply vein midrib sub-group
    avm_ng = make_shader_apply_vein_midrib()
    applyveinmidrib = ng.nodes.new('ShaderNodeGroup')
    applyveinmidrib.node_tree = avm_ng
    ng.links.new(veincoord.outputs['Vein Coord'], applyveinmidrib.inputs['Vein Coord'])
    ng.links.new(midrib.outputs['Midrib Value'], applyveinmidrib.inputs['Midrib Value'])
    ng.links.new(shape.outputs['Leaf Shape'], applyveinmidrib.inputs['Leaf Shape'])
    ng.links.new(inp.outputs['Vein Density'], applyveinmidrib.inputs['Vein Density'])

    # Sub-vein sub-group
    sv_ng = make_shader_sub_vein()
    subvein = ng.nodes.new('ShaderNodeGroup')
    subvein.node_tree = sv_ng
    ng.links.new(midrib.outputs['X Modulated'], subvein.inputs['X Modulated'])
    ng.links.new(veincoord.outputs['Vein Coord'], subvein.inputs['Y'])

    ng.links.new(applyveinmidrib.outputs['Vein Value'], out.inputs['Vein Value'])
    ng.links.new(subvein.outputs['Value'], out.inputs['Sub Vein Value'])
    return ng


def make_shader_blight():
    ng = bpy.data.node_groups.new("nodegroup_blight", 'ShaderNodeTree')
    ng.interface.new_socket('Coordinate', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Leaf Color', in_out='INPUT', socket_type='NodeSocketColor')
    ng.interface.new_socket('Blight Color', in_out='INPUT', socket_type='NodeSocketColor')
    ng.interface.new_socket('Random Seed', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Offset', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Coordinate': item.default_value = (0.0, 0.0, 0.0)
            elif item.name == 'Leaf Color': item.default_value = (0.5, 0.5, 0.5, 1.0)
            elif item.name == 'Blight Color': item.default_value = (0.5, 0.3992, 0.035, 1.0)
            elif item.name == 'Random Seed': item.default_value = 18.3
            elif item.name == 'Offset': item.default_value = 0.5
    ng.interface.new_socket('Color', in_out='OUTPUT', socket_type='NodeSocketColor')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # MusgraveTexture replaced by NoiseTexture in Blender 4.4+
    musgrave_texture = ng.nodes.new('ShaderNodeTexNoise')
    musgrave_texture.noise_dimensions = '4D'
    ng.links.new(inp.outputs['Coordinate'], musgrave_texture.inputs['Vector'])
    ng.links.new(inp.outputs['Random Seed'], musgrave_texture.inputs['W'])
    musgrave_texture.inputs['Scale'].default_value = 4.0
    musgrave_texture.inputs['Detail'].default_value = 10.0
    # Dimension, Lacunarity, Offset not all available on NoiseTexture; use what's available
    try:
        musgrave_texture.inputs['Lacunarity'].default_value = 5.0
    except Exception:
        pass

    map_range_1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(musgrave_texture.outputs[0], map_range_1.inputs['Value'])
    map_range_1.inputs[4].default_value = 0.8

    mix_4 = ng.nodes.new('ShaderNodeMixRGB')
    ng.links.new(map_range_1.outputs['Result'], mix_4.inputs['Fac'])
    ng.links.new(inp.outputs['Leaf Color'], mix_4.inputs['Color1'])
    ng.links.new(inp.outputs['Blight Color'], mix_4.inputs['Color2'])

    ng.links.new(mix_4.outputs[0], out.inputs['Color'])
    return ng


def make_shader_dotted_blight():
    ng = bpy.data.node_groups.new("nodegroup_dotted_blight", 'ShaderNodeTree')
    ng.interface.new_socket('Coord', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Leaf Color', in_out='INPUT', socket_type='NodeSocketColor')
    ng.interface.new_socket('Blight Color', in_out='INPUT', socket_type='NodeSocketColor')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Coord': item.default_value = (0.0, 0.0, 0.0)
            elif item.name == 'Leaf Color': item.default_value = (0.5, 0.5, 0.5, 1.0)
            elif item.name == 'Blight Color': item.default_value = (0.4969, 0.2831, 0.0273, 1.0)
    ng.interface.new_socket('Color', in_out='OUTPUT', socket_type='NodeSocketColor')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    voronoi_texture = ng.nodes.new('ShaderNodeTexVoronoi')
    voronoi_texture.voronoi_dimensions = '2D'
    ng.links.new(inp.outputs['Coord'], voronoi_texture.inputs['Vector'])
    voronoi_texture.inputs['Scale'].default_value = 20.0

    map_range = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(voronoi_texture.outputs['Distance'], map_range.inputs['Value'])
    map_range.inputs[2].default_value = 0.15
    map_range.inputs[3].default_value = 1.0
    map_range.inputs[4].default_value = 0.0

    mix_5 = ng.nodes.new('ShaderNodeMixRGB')
    ng.links.new(map_range.outputs['Result'], mix_5.inputs['Fac'])
    ng.links.new(inp.outputs['Blight Color'], mix_5.inputs['Color1'])
    mix_5.inputs['Color2'].default_value = (0.0, 0.0, 0.0, 1.0)

    mix_3 = ng.nodes.new('ShaderNodeMixRGB')
    ng.links.new(map_range.outputs['Result'], mix_3.inputs['Fac'])
    ng.links.new(inp.outputs['Leaf Color'], mix_3.inputs['Color1'])
    ng.links.new(mix_5.outputs[0], mix_3.inputs['Color2'])

    ng.links.new(mix_3.outputs[0], out.inputs['Color'])
    return ng


# -- Geometry node groups (GeometryNodeTree) --

def make_shape_with_jigsaw():
    ng = bpy.data.node_groups.new("nodegroup_shape_with_jigsaw", 'GeometryNodeTree')
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

    map_range_12 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Midrib Value'], map_range_12.inputs['Value'])
    map_range_12.inputs[3].default_value = 1.0
    map_range_12.inputs[4].default_value = 0.0

    jigsaw = ng.nodes.new('ShaderNodeTexVoronoi'); jigsaw.voronoi_dimensions = '1D'
    ng.links.new(inp.outputs['Vein Coord'], jigsaw.inputs['W'])
    ng.links.new(inp.outputs['Jigsaw Scale'], jigsaw.inputs['Scale'])

    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Jigsaw Depth'], multiply.inputs[0])
    multiply.inputs[1].default_value = 0.05

    multiply_add = ng.nodes.new('ShaderNodeMath'); multiply_add.operation = 'MULTIPLY_ADD'; multiply_add.use_clamp = True
    ng.links.new(jigsaw.outputs['Distance'], multiply_add.inputs[0])
    ng.links.new(multiply.outputs[0], multiply_add.inputs[1])
    ng.links.new(inp.outputs['Leaf Shape'], multiply_add.inputs[2])

    map_range = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(multiply_add.outputs[0], map_range.inputs['Value'])
    map_range.inputs[1].default_value = 0.001
    map_range.inputs[2].default_value = 0.002
    map_range.inputs[3].default_value = 1.0
    map_range.inputs[4].default_value = 0.0

    maximum = ng.nodes.new('ShaderNodeMath'); maximum.operation = 'MAXIMUM'
    ng.links.new(map_range_12.outputs['Result'], maximum.inputs[0])
    ng.links.new(map_range.outputs['Result'], maximum.inputs[1])

    ng.links.new(maximum.outputs[0], out.inputs['Value'])
    return ng


def make_shape(shape_curve_control_points):
    ng = bpy.data.node_groups.new("nodegroup_shape", 'GeometryNodeTree')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X Modulated': item.default_value = 0.0
            elif item.name == 'Y': item.default_value = 0.0
    ng.interface.new_socket('Leaf Shape', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    combine_xyz_2 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(inp.outputs['X Modulated'], combine_xyz_2.inputs['X'])
    ng.links.new(inp.outputs['Y'], combine_xyz_2.inputs['Y'])

    clamp = ng.nodes.new('ShaderNodeClamp')
    ng.links.new(inp.outputs['Y'], clamp.inputs['Value'])
    clamp.inputs['Min'].default_value = -0.6
    clamp.inputs['Max'].default_value = 0.6

    combine_xyz_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(clamp.outputs[0], combine_xyz_1.inputs['Y'])

    subtract = ng.nodes.new('ShaderNodeVectorMath'); subtract.operation = 'SUBTRACT'
    ng.links.new(combine_xyz_2.outputs[0], subtract.inputs[0])
    ng.links.new(combine_xyz_1.outputs[0], subtract.inputs[1])

    length = ng.nodes.new('ShaderNodeVectorMath'); length.operation = 'LENGTH'
    ng.links.new(subtract.outputs['Vector'], length.inputs[0])

    map_range_1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], map_range_1.inputs['Value'])
    map_range_1.inputs[1].default_value = -0.6
    map_range_1.inputs[2].default_value = 0.6

    leaf_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(map_range_1.outputs['Result'], leaf_shape.inputs['Value'])
    _assign_curve(leaf_shape.mapping.curves[0], shape_curve_control_points)

    subtract_1 = ng.nodes.new('ShaderNodeMath'); subtract_1.operation = 'SUBTRACT'
    ng.links.new(length.outputs['Value'], subtract_1.inputs[0])
    ng.links.new(leaf_shape.outputs[0], subtract_1.inputs[1])

    ng.links.new(subtract_1.outputs[0], out.inputs['Leaf Shape'])
    return ng


def make_midrib(midrib_curve_control_points):
    ng = bpy.data.node_groups.new("nodegroup_midrib", 'GeometryNodeTree')
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

    map_range_6 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], map_range_6.inputs['Value'])
    map_range_6.inputs[1].default_value = -0.6
    map_range_6.inputs[2].default_value = 0.6

    stem_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(map_range_6.outputs['Result'], stem_shape.inputs['Value'])
    _assign_curve(stem_shape.mapping.curves[0], midrib_curve_control_points)

    map_range_7 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(stem_shape.outputs[0], map_range_7.inputs['Value'])
    map_range_7.inputs[3].default_value = -1.0

    subtract = ng.nodes.new('ShaderNodeMath'); subtract.operation = 'SUBTRACT'
    ng.links.new(map_range_7.outputs['Result'], subtract.inputs[0])
    ng.links.new(inp.outputs['X'], subtract.inputs[1])

    map_range_8 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], map_range_8.inputs['Value'])
    map_range_8.inputs[1].default_value = -70.0
    ng.links.new(inp.outputs['Midrib Length'], map_range_8.inputs[2])
    ng.links.new(inp.outputs['Midrib Width'], map_range_8.inputs[3])
    map_range_8.inputs[4].default_value = 0.0

    absolute = ng.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'
    ng.links.new(subtract.outputs[0], absolute.inputs[0])

    subtract_1 = ng.nodes.new('ShaderNodeMath'); subtract_1.operation = 'SUBTRACT'
    ng.links.new(map_range_8.outputs['Result'], subtract_1.inputs[0])
    ng.links.new(absolute.outputs[0], subtract_1.inputs[1])

    absolute_1 = ng.nodes.new('ShaderNodeMath'); absolute_1.operation = 'ABSOLUTE'
    ng.links.new(inp.outputs['Y'], absolute_1.inputs[0])

    map_range_9 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(absolute_1.outputs[0], map_range_9.inputs['Value'])
    ng.links.new(inp.outputs['Stem Length'], map_range_9.inputs[2])
    map_range_9.inputs[3].default_value = 1.0
    map_range_9.inputs[4].default_value = 0.0

    smooth_min = ng.nodes.new('ShaderNodeMath'); smooth_min.operation = 'SMOOTH_MIN'
    ng.links.new(subtract_1.outputs[0], smooth_min.inputs[0])
    ng.links.new(map_range_9.outputs['Result'], smooth_min.inputs[1])
    smooth_min.inputs[2].default_value = 0.06

    divide = ng.nodes.new('ShaderNodeMath'); divide.operation = 'DIVIDE'; divide.use_clamp = True
    ng.links.new(map_range_8.outputs['Result'], divide.inputs[0])
    ng.links.new(smooth_min.outputs[0], divide.inputs[1])

    map_range_11 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(divide.outputs[0], map_range_11.inputs['Value'])
    map_range_11.inputs[1].default_value = 0.001
    map_range_11.inputs[2].default_value = 0.03
    map_range_11.inputs[3].default_value = 1.0
    map_range_11.inputs[4].default_value = 0.0

    ng.links.new(subtract.outputs[0], out.inputs['X Modulated'])
    ng.links.new(map_range_11.outputs['Result'], out.inputs['Midrib Value'])
    return ng


def make_vein_coord(vein_curve_control_points):
    ng = bpy.data.node_groups.new("nodegroup_vein_coord", 'GeometryNodeTree')
    ng.interface.new_socket('X Modulated', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Asymmetry', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X Modulated': item.default_value = 0.5
            elif item.name == 'Y': item.default_value = 0.5
            elif item.name == 'Vein Asymmetry': item.default_value = 0.0
            elif item.name == 'Vein Angle': item.default_value = 2.0
    ng.interface.new_socket('Vein Coord', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    sign = ng.nodes.new('ShaderNodeMath'); sign.operation = 'SIGN'
    ng.links.new(inp.outputs['X Modulated'], sign.inputs[0])

    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(sign.outputs[0], multiply.inputs[0])
    ng.links.new(inp.outputs['Vein Asymmetry'], multiply.inputs[1])

    map_range_13 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Y'], map_range_13.inputs['Value'])
    map_range_13.inputs[1].default_value = -1.0

    absolute = ng.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'; absolute.use_clamp = True
    ng.links.new(inp.outputs['X Modulated'], absolute.inputs[0])

    vein_shape = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(absolute.outputs[0], vein_shape.inputs['Value'])
    _assign_curve(vein_shape.mapping.curves[0], vein_curve_control_points)

    map_range_4 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(vein_shape.outputs[0], map_range_4.inputs['Value'])
    map_range_4.inputs[2].default_value = 0.9
    map_range_4.inputs[4].default_value = 1.9

    multiply_1 = ng.nodes.new('ShaderNodeMath'); multiply_1.operation = 'MULTIPLY'
    ng.links.new(map_range_4.outputs['Result'], multiply_1.inputs[0])
    ng.links.new(inp.outputs['Vein Angle'], multiply_1.inputs[1])

    multiply_2 = ng.nodes.new('ShaderNodeMath'); multiply_2.operation = 'MULTIPLY'
    ng.links.new(map_range_13.outputs['Result'], multiply_2.inputs[0])
    ng.links.new(multiply_1.outputs[0], multiply_2.inputs[1])

    subtract = ng.nodes.new('ShaderNodeMath'); subtract.operation = 'SUBTRACT'
    ng.links.new(multiply_2.outputs[0], subtract.inputs[0])
    ng.links.new(inp.outputs['Y'], subtract.inputs[1])

    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(multiply.outputs[0], add.inputs[0])
    ng.links.new(subtract.outputs[0], add.inputs[1])

    ng.links.new(add.outputs[0], out.inputs['Vein Coord'])
    return ng


def make_apply_vein_midrib():
    ng = bpy.data.node_groups.new("nodegroup_apply_vein_midrib", 'GeometryNodeTree')
    ng.interface.new_socket('Vein Coord', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Midrib Value', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Leaf Shape', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Vein Density', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Vein Coord': item.default_value = 0.0
            elif item.name == 'Midrib Value': item.default_value = 0.5
            elif item.name == 'Leaf Shape': item.default_value = 1.0
            elif item.name == 'Vein Density': item.default_value = 6.0
    ng.interface.new_socket('Vein Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    map_range_5 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['Leaf Shape'], map_range_5.inputs['Value'])
    map_range_5.inputs[1].default_value = -0.3
    map_range_5.inputs[2].default_value = 0.0
    map_range_5.inputs[3].default_value = 0.015
    map_range_5.inputs[4].default_value = 0.0

    vein = ng.nodes.new('ShaderNodeTexVoronoi'); vein.voronoi_dimensions = '1D'
    ng.links.new(inp.outputs['Vein Coord'], vein.inputs['W'])
    ng.links.new(inp.outputs['Vein Density'], vein.inputs['Scale'])
    vein.inputs['Randomness'].default_value = 0.2

    map_range_3 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(vein.outputs['Distance'], map_range_3.inputs['Value'])
    map_range_3.inputs[1].default_value = 0.001
    map_range_3.inputs[2].default_value = 0.05
    map_range_3.inputs[3].default_value = 1.0
    map_range_3.inputs[4].default_value = 0.0

    mul = ng.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ng.links.new(map_range_5.outputs['Result'], mul.inputs[0])
    ng.links.new(map_range_3.outputs['Result'], mul.inputs[1])

    map_range_10 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(mul.outputs[0], map_range_10.inputs['Value'])
    map_range_10.inputs[1].default_value = 0.001
    map_range_10.inputs[2].default_value = 0.01
    map_range_10.inputs[3].default_value = 1.0
    map_range_10.inputs[4].default_value = 0.0

    multiply_1 = ng.nodes.new('ShaderNodeMath'); multiply_1.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Midrib Value'], multiply_1.inputs[0])
    ng.links.new(map_range_10.outputs['Result'], multiply_1.inputs[1])

    ng.links.new(multiply_1.outputs[0], out.inputs['Vein Value'])
    return ng


def make_leaf_gen(midrib_curve_control_points, vein_curve_control_points, shape_curve_control_points):
    ng = bpy.data.node_groups.new("nodegroup_leaf_gen", 'GeometryNodeTree')
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
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    position = ng.nodes.new('GeometryNodeInputPosition')
    separate_xyz = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], separate_xyz.inputs['Vector'])

    # Midrib sub-group
    midrib_ng = make_midrib(midrib_curve_control_points)
    midrib = ng.nodes.new('GeometryNodeGroup')
    midrib.node_tree = midrib_ng
    ng.links.new(separate_xyz.outputs['X'], midrib.inputs['X'])
    ng.links.new(separate_xyz.outputs['Y'], midrib.inputs['Y'])
    ng.links.new(inp.outputs['Midrib Length'], midrib.inputs['Midrib Length'])
    ng.links.new(inp.outputs['Midrib Width'], midrib.inputs['Midrib Width'])
    ng.links.new(inp.outputs['Stem Length'], midrib.inputs['Stem Length'])

    # Vein coord sub-group
    vc_ng = make_vein_coord(vein_curve_control_points)
    veincoord = ng.nodes.new('GeometryNodeGroup')
    veincoord.node_tree = vc_ng
    ng.links.new(midrib.outputs['X Modulated'], veincoord.inputs['X Modulated'])
    ng.links.new(separate_xyz.outputs['Y'], veincoord.inputs['Y'])
    ng.links.new(inp.outputs['Vein Asymmetry'], veincoord.inputs['Vein Asymmetry'])
    ng.links.new(inp.outputs['Vein Angle'], veincoord.inputs['Vein Angle'])

    # Shape sub-group
    shape_ng = make_shape(shape_curve_control_points)
    shape = ng.nodes.new('GeometryNodeGroup')
    shape.node_tree = shape_ng
    ng.links.new(midrib.outputs['X Modulated'], shape.inputs['X Modulated'])
    ng.links.new(separate_xyz.outputs['Y'], shape.inputs['Y'])

    # Apply vein midrib sub-group
    avm_ng = make_apply_vein_midrib()
    applyveinmidrib = ng.nodes.new('GeometryNodeGroup')
    applyveinmidrib.node_tree = avm_ng
    ng.links.new(veincoord.outputs['Vein Coord'], applyveinmidrib.inputs['Vein Coord'])
    ng.links.new(midrib.outputs['Midrib Value'], applyveinmidrib.inputs['Midrib Value'])
    ng.links.new(shape.outputs['Leaf Shape'], applyveinmidrib.inputs['Leaf Shape'])
    ng.links.new(inp.outputs['Vein Density'], applyveinmidrib.inputs['Vein Density'])

    # Displacement from vein
    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(inp.outputs['Displancement scale'], multiply.inputs[0])
    ng.links.new(applyveinmidrib.outputs['Vein Value'], multiply.inputs[1])

    combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(multiply.outputs[0], combine_xyz.inputs['Z'])

    set_position = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(inp.outputs['Mesh'], set_position.inputs['Geometry'])
    ng.links.new(combine_xyz.outputs[0], set_position.inputs['Offset'])

    # Shape with jigsaw
    swj_ng = make_shape_with_jigsaw()
    shapewithjigsaw = ng.nodes.new('GeometryNodeGroup')
    shapewithjigsaw.node_tree = swj_ng
    ng.links.new(midrib.outputs['Midrib Value'], shapewithjigsaw.inputs['Midrib Value'])
    ng.links.new(veincoord.outputs['Vein Coord'], shapewithjigsaw.inputs['Vein Coord'])
    ng.links.new(shape.outputs['Leaf Shape'], shapewithjigsaw.inputs['Leaf Shape'])
    ng.links.new(inp.outputs['Jigsaw Scale'], shapewithjigsaw.inputs['Jigsaw Scale'])
    ng.links.new(inp.outputs['Jigsaw Depth'], shapewithjigsaw.inputs['Jigsaw Depth'])

    # Compare (less than)
    less_than = ng.nodes.new('FunctionNodeCompare'); less_than.operation = 'LESS_THAN'
    ng.links.new(shapewithjigsaw.outputs['Value'], less_than.inputs[0])
    less_than.inputs[1].default_value = 0.5

    # Delete geometry
    delete_geometry = ng.nodes.new('GeometryNodeDeleteGeometry')
    ng.links.new(set_position.outputs[0], delete_geometry.inputs['Geometry'])
    ng.links.new(less_than.outputs[0], delete_geometry.inputs['Selection'])

    # CaptureAttribute (Blender 5.0: must add capture channel)
    capture_attribute = ng.nodes.new('GeometryNodeCaptureAttribute')
    capture_attribute.capture_items.new('FLOAT', 'Value')
    ng.links.new(delete_geometry.outputs[0], capture_attribute.inputs['Geometry'])
    ng.links.new(applyveinmidrib.outputs['Vein Value'], capture_attribute.inputs['Value'])

    # Wire outputs
    ng.links.new(capture_attribute.outputs['Geometry'], out.inputs['Mesh'])
    ng.links.new(capture_attribute.outputs['Value'], out.inputs['Attribute'])
    ng.links.new(midrib.outputs['X Modulated'], out.inputs['X Modulated'])
    ng.links.new(veincoord.outputs['Vein Coord'], out.inputs['Vein Coord'])
    return ng


def make_sub_vein():
    ng = bpy.data.node_groups.new("nodegroup_sub_vein", 'GeometryNodeTree')
    ng.interface.new_socket('X', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Y', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'X': item.default_value = 0.5
            elif item.name == 'Y': item.default_value = 0.0
    ng.interface.new_socket('Value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    absolute = ng.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'; absolute.use_clamp = True
    ng.links.new(inp.outputs['X'], absolute.inputs[0])

    combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(absolute.outputs[0], combine_xyz.inputs['X'])
    ng.links.new(inp.outputs['Y'], combine_xyz.inputs['Y'])

    voronoi_texture = ng.nodes.new('ShaderNodeTexVoronoi')
    voronoi_texture.feature = 'DISTANCE_TO_EDGE'
    ng.links.new(combine_xyz.outputs[0], voronoi_texture.inputs['Vector'])
    voronoi_texture.inputs['Scale'].default_value = 30.0
    voronoi_texture.inputs['Randomness'].default_value = 0.754

    map_range = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(voronoi_texture.outputs['Distance'], map_range.inputs['Value'])
    map_range.inputs[2].default_value = 0.1

    voronoi_texture_1 = ng.nodes.new('ShaderNodeTexVoronoi')
    voronoi_texture_1.feature = 'DISTANCE_TO_EDGE'
    ng.links.new(combine_xyz.outputs[0], voronoi_texture_1.inputs['Vector'])
    voronoi_texture_1.inputs['Scale'].default_value = 10.0
    voronoi_texture_1.inputs['Randomness'].default_value = 0.754

    map_range_1 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(voronoi_texture_1.outputs['Distance'], map_range_1.inputs['Value'])
    map_range_1.inputs[2].default_value = 0.1

    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(map_range.outputs['Result'], multiply.inputs[0])
    ng.links.new(map_range_1.outputs['Result'], multiply.inputs[1])

    ng.links.new(multiply.outputs[0], out.inputs['Value'])
    return ng


def make_add_noise():
    ng = bpy.data.node_groups.new("nodegroup_add_noise", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Displacement', in_out='INPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Scale', in_out='INPUT', socket_type='NodeSocketFloat')
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT':
            if item.name == 'Displacement': item.default_value = 0.05
            elif item.name == 'Scale': item.default_value = 10.0
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    position_1 = ng.nodes.new('GeometryNodeInputPosition')

    noise_texture = ng.nodes.new('ShaderNodeTexNoise')
    ng.links.new(position_1.outputs[0], noise_texture.inputs['Vector'])
    ng.links.new(inp.outputs['Scale'], noise_texture.inputs['Scale'])

    # Blender 5.0: "Fac" renamed to "Factor"; use index 0
    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(noise_texture.outputs[0], multiply.inputs[0])
    ng.links.new(inp.outputs['Displacement'], multiply.inputs[1])

    combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(multiply.outputs[0], combine_xyz.inputs['Z'])

    set_position = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(inp.outputs['Geometry'], set_position.inputs['Geometry'])
    ng.links.new(combine_xyz.outputs[0], set_position.inputs['Offset'])

    ng.links.new(set_position.outputs[0], out.inputs['Geometry'])
    return ng


def make_apply_wave(y_wave_control_points, x_wave_control_points):
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
    separate_xyz = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], separate_xyz.inputs['Vector'])

    position_1 = ng.nodes.new('GeometryNodeInputPosition')
    separate_xyz_1 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position_1.outputs[0], separate_xyz_1.inputs['Vector'])

    attribute_statistic = ng.nodes.new('GeometryNodeAttributeStatistic')
    ng.links.new(inp.outputs['Geometry'], attribute_statistic.inputs['Geometry'])
    ng.links.new(separate_xyz_1.outputs['Y'], attribute_statistic.inputs[2])

    map_range = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(separate_xyz.outputs['Y'], map_range.inputs['Value'])
    ng.links.new(attribute_statistic.outputs['Min'], map_range.inputs[1])
    ng.links.new(attribute_statistic.outputs['Max'], map_range.inputs[2])

    float_curves = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(map_range.outputs['Result'], float_curves.inputs['Value'])
    _assign_curve(float_curves.mapping.curves[0], y_wave_control_points)

    map_range_2 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(float_curves.outputs[0], map_range_2.inputs['Value'])
    map_range_2.inputs[3].default_value = -1.0

    multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    ng.links.new(map_range_2.outputs['Result'], multiply.inputs[0])
    ng.links.new(inp.outputs['Wave Scale Y'], multiply.inputs[1])

    combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(multiply.outputs[0], combine_xyz.inputs['Z'])

    set_position = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(inp.outputs['Geometry'], set_position.inputs['Geometry'])
    ng.links.new(combine_xyz.outputs[0], set_position.inputs['Offset'])

    # X wave branch
    attribute_statistic_1 = ng.nodes.new('GeometryNodeAttributeStatistic')
    ng.links.new(inp.outputs['Geometry'], attribute_statistic_1.inputs['Geometry'])
    ng.links.new(inp.outputs['X Modulated'], attribute_statistic_1.inputs[2])

    map_range_7 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(inp.outputs['X Modulated'], map_range_7.inputs['Value'])
    ng.links.new(attribute_statistic_1.outputs['Min'], map_range_7.inputs[1])
    ng.links.new(attribute_statistic_1.outputs['Max'], map_range_7.inputs[2])

    float_curves_2 = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(map_range_7.outputs['Result'], float_curves_2.inputs['Value'])
    _assign_curve(float_curves_2.mapping.curves[0], x_wave_control_points)
    float_curves_2.mapping.curves[0].points[2].handle_type = "VECTOR"

    map_range_4 = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(float_curves_2.outputs[0], map_range_4.inputs['Value'])
    map_range_4.inputs[3].default_value = -1.0

    multiply_1 = ng.nodes.new('ShaderNodeMath'); multiply_1.operation = 'MULTIPLY'
    ng.links.new(map_range_4.outputs['Result'], multiply_1.inputs[0])
    ng.links.new(inp.outputs['Wave Scale X'], multiply_1.inputs[1])

    combine_xyz_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(multiply_1.outputs[0], combine_xyz_1.inputs['Z'])

    set_position_1 = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(set_position.outputs[0], set_position_1.inputs['Geometry'])
    ng.links.new(combine_xyz_1.outputs[0], set_position_1.inputs['Offset'])

    ng.links.new(set_position_1.outputs[0], out.inputs['Geometry'])
    return ng


def make_move_to_origin():
    ng = bpy.data.node_groups.new("nodegroup_move_to_origin", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    position = ng.nodes.new('GeometryNodeInputPosition')
    separate_xyz = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], separate_xyz.inputs['Vector'])

    attribute_statistic = ng.nodes.new('GeometryNodeAttributeStatistic')
    ng.links.new(inp.outputs['Geometry'], attribute_statistic.inputs['Geometry'])
    ng.links.new(separate_xyz.outputs['Y'], attribute_statistic.inputs[2])

    subtract = ng.nodes.new('ShaderNodeMath'); subtract.operation = 'SUBTRACT'
    subtract.inputs[0].default_value = 0.0
    ng.links.new(attribute_statistic.outputs['Min'], subtract.inputs[1])

    combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(subtract.outputs[0], combine_xyz.inputs['Y'])

    set_position = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(inp.outputs['Geometry'], set_position.inputs['Geometry'])
    ng.links.new(combine_xyz.outputs[0], set_position.inputs['Offset'])

    ng.links.new(set_position.outputs[0], out.inputs['Geometry'])
    return ng


# ===================================================================
# Top-level GeoNodes tree builder
# ===================================================================

def make_geo_leaf_v2(**kwargs):
    """Build the top-level GeoNodes tree for leaf v2. Returns the node group."""

    ng = bpy.data.node_groups.new("geo_leaf_v2", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Attribute', in_out='OUTPUT', socket_type='NodeSocketFloat')
    ng.interface.new_socket('Coordinate', in_out='OUTPUT', socket_type='NodeSocketVector')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # Subdivide mesh (level 10)
    subdivide_mesh = ng.nodes.new('GeometryNodeSubdivideMesh')
    ng.links.new(inp.outputs['Geometry'], subdivide_mesh.inputs['Mesh'])
    subdivide_mesh.inputs['Level'].default_value = 10

    # Capture initial position (FLOAT_VECTOR) -- Blender 5.0
    position = ng.nodes.new('GeometryNodeInputPosition')
    capture_attribute = ng.nodes.new('GeometryNodeCaptureAttribute')
    capture_attribute.capture_items.new('VECTOR', 'Value')
    ng.links.new(subdivide_mesh.outputs[0], capture_attribute.inputs['Geometry'])
    ng.links.new(position.outputs[0], capture_attribute.inputs['Value'])

    # Leaf gen sub-group
    lg_ng = make_leaf_gen(
        kwargs["midrib_shape_control_points"],
        kwargs["vein_shape_control_points"],
        kwargs["leaf_shape_control_points"],
    )
    leafgen = ng.nodes.new('GeometryNodeGroup')
    leafgen.node_tree = lg_ng
    ng.links.new(capture_attribute.outputs['Geometry'], leafgen.inputs['Mesh'])
    leafgen.inputs['Displancement scale'].default_value = 0.005
    leafgen.inputs['Vein Asymmetry'].default_value = kwargs["vein_asymmetry"]
    leafgen.inputs['Vein Density'].default_value = kwargs["vein_density"]
    leafgen.inputs['Jigsaw Scale'].default_value = kwargs["jigsaw_scale"]
    leafgen.inputs['Jigsaw Depth'].default_value = kwargs["jigsaw_depth"]
    leafgen.inputs['Vein Angle'].default_value = kwargs["vein_angle"]
    leafgen.inputs['Midrib Length'].default_value = kwargs["midrib_length"]
    leafgen.inputs['Midrib Width'].default_value = kwargs["midrib_width"]
    leafgen.inputs['Stem Length'].default_value = kwargs["stem_length"]

    # Sub-vein sub-group
    sv_ng = make_sub_vein()
    subvein = ng.nodes.new('GeometryNodeGroup')
    subvein.node_tree = sv_ng
    ng.links.new(leafgen.outputs['X Modulated'], subvein.inputs['X'])
    ng.links.new(leafgen.outputs['Vein Coord'], subvein.inputs['Y'])

    # Sub-vein displacement -- DISABLED to match original (segfault workaround)
    # multiply = ng.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    # ng.links.new(subvein.outputs['Value'], multiply.inputs[0])
    # multiply.inputs[1].default_value = 0.001
    # combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    # ng.links.new(multiply.outputs[0], combine_xyz.inputs['Z'])
    # set_position = ng.nodes.new('GeometryNodeSetPosition')
    # ng.links.new(leafgen.outputs['Mesh'], set_position.inputs['Geometry'])
    # ng.links.new(combine_xyz.outputs[0], set_position.inputs['Offset'])

    logging.warning("Disabling set_position to avoid LeafV2 segfault")
    # Connect leafgen mesh directly (bypassing sub-vein set_position)
    leaf_mesh_out = leafgen.outputs['Mesh']

    # Apply wave sub-group
    aw_ng = make_apply_wave(kwargs["y_wave_control_points"], kwargs["x_wave_control_points"])
    applywave = ng.nodes.new('GeometryNodeGroup')
    applywave.node_tree = aw_ng
    ng.links.new(leaf_mesh_out, applywave.inputs['Geometry'])
    applywave.inputs['Wave Scale X'].default_value = 0.15
    applywave.inputs['Wave Scale Y'].default_value = 1.5
    ng.links.new(leafgen.outputs['X Modulated'], applywave.inputs['X Modulated'])

    # Move to origin sub-group
    mto_ng = make_move_to_origin()
    movetoorigin = ng.nodes.new('GeometryNodeGroup')
    movetoorigin.node_tree = mto_ng
    ng.links.new(applywave.outputs['Geometry'], movetoorigin.inputs['Geometry'])

    # Wire outputs
    ng.links.new(movetoorigin.outputs['Geometry'], out.inputs['Geometry'])
    ng.links.new(leafgen.outputs['Attribute'], out.inputs['Attribute'])
    ng.links.new(capture_attribute.outputs['Value'], out.inputs['Coordinate'])
    return ng


# ===================================================================
# Factory class
# ===================================================================

class LeafFactoryV2(AssetFactory):
    scale = 0.5

    def __init__(self, factory_seed, coarse=False):
        super(LeafFactoryV2, self).__init__(factory_seed, coarse=coarse)

        with FixedSeed(factory_seed):
            self.genome = self.sample_geo_genome()

            t = uniform(0.0, 1.0)

            if t < 0.8:
                self.blade_color_hsv = colors.plant_green()
            elif t < 0.9:
                self.blade_color_hsv = colors.plant_yellow()
            else:
                self.blade_color_hsv = colors.plant_red()

            self.blight_color_hsv = colors.plant_yellow()
            self.vein_color_mix_factor = uniform(0.2, 0.6)

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
            (np.random.uniform(0.25, 0.75), np.random.uniform(0.50, 0.60)),
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
        material_kwargs["blade_color"] = list(colors.hsv2rgba(self.blade_color_hsv))
        material_kwargs["blade_color"][0] += np.random.normal(0.0, 0.03)
        material_kwargs["blade_color"][1] += np.random.normal(0.0, 0.03)
        material_kwargs["blade_color"][2] += np.random.normal(0.0, 0.03)

        material_kwargs["blight_color"] = colors.hsv2rgba(self.blight_color_hsv)

        material_kwargs["vein_color_mix_factor"] = self.vein_color_mix_factor
        material_kwargs["blight_weight"] = np.random.binomial(1, 0.1)
        material_kwargs["dotted_blight_weight"] = np.random.binomial(1, 0.1)
        material_kwargs["blight_random_seed"] = np.random.uniform(0.0, 100.0)
        material_kwargs["blight_area_factor"] = np.random.uniform(0.2, 0.8)

        # Build GeoNodes tree and assign as modifier (replaces surface.add_geomod)
        geo_ng = make_geo_leaf_v2(**phenome)
        mod = obj.modifiers.new(name="geo_leaf_v2", type='NODES')
        mod.node_group = geo_ng

        # Apply attributes by name (mirrors old surface.add_geomod attributes= logic)
        attr_names = ["offset", "coordinate"]
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
        # surface.add_material(obj, shader_leaf_new, reuse=False, input_kwargs=material_kwargs)

        bpy.ops.object.convert(target="MESH")

        obj = bpy.context.object
        obj.scale *= normal(1, 0.05) * self.scale
        apply_transform(obj)
        tag_object(obj, "leaf")

        return obj

def build(seed=0, season="autumn"):
    fac = LeafFactoryV2(seed, season)
    with FixedSeed(int_hash((seed, seed))):
        return fac.create_asset()

SEED = 0
build(SEED)
