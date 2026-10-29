# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafPineFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafPineFactory | Category: factories_geo
# Prompt: A 3D model of a pine needle cluster on a small branch rendered from a three-quarter perspective. The model features a short brown twig with numerous thin, elongated green pine needles radiating outward in pairs or bundles along the branch, creating a characteristic coniferous foliage appearance with a natural spread and slight droop.

import bpy
import numpy as np
import random
import hashlib
from types import SimpleNamespace
from numpy.random import normal, uniform, randint
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

def purge_empty_materials(obj):
    return obj

butil = SimpleNamespace(
    apply_transform=apply_transform,
    purge_empty_materials=purge_empty_materials,
)

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

# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory of this source tree.

# Authors: Yiming Zuo

from random import randint

import bpy
from numpy.random import normal, uniform

######## code for creating pine needles ########

def make_geometry_needle():
    """Build the geometry node group for creating a single pine needle cone (no material)."""

    ng = bpy.data.node_groups.new("geometry_needle", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    cone = ng.nodes.new('GeometryNodeMeshCone')
    cone.inputs['Vertices'].default_value = 4
    cone.inputs['Radius Top'].default_value = 0.01
    cone.inputs['Radius Bottom'].default_value = 0.02
    cone.inputs['Depth'].default_value = 1.0

    # Shape-only: skip SetMaterial, just output the cone mesh directly
    ng.links.new(cone.outputs['Mesh'], out.inputs['Geometry'])
    return ng


def make_needle(name="Needle"):
    if bpy.context.scene.objects.get(name):
        return bpy.context.scene.objects.get(name)

    bpy.ops.mesh.primitive_plane_add(
        size=2,
        enter_editmode=False,
        align="WORLD",
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )
    needle = bpy.context.active_object
    needle.name = name

    # Apply geometry_needle via direct modifier creation
    geo_ng = make_geometry_needle()
    mod = needle.modifiers.new(name="geometry_needle", type='NODES')
    mod.node_group = geo_ng

    bpy.ops.object.convert(target="MESH")

    return needle


######## code for creating pine twigs ########

def make_instance_needle():
    """Build nodegroup_instance_needle: instances needle objects on curve points."""

    ng_name = "nodegroup_instance_needle (no gc)"
    if ng_name in bpy.data.node_groups:
        return bpy.data.node_groups[ng_name]

    ng = bpy.data.node_groups.new(ng_name, 'GeometryNodeTree')
    ng.interface.new_socket('Curve', in_out='INPUT', socket_type='NodeSocketGeometry')
    s_nd = ng.interface.new_socket('Needle Density', in_out='INPUT', socket_type='NodeSocketFloat')
    s_nd.default_value = 0.9
    s_seed = ng.interface.new_socket('Seed', in_out='INPUT', socket_type='NodeSocketInt')
    s_seed.default_value = 0
    ng.interface.new_socket('Instance', in_out='INPUT', socket_type='NodeSocketGeometry')
    s_xam = ng.interface.new_socket('X Angle Mean', in_out='INPUT', socket_type='NodeSocketFloat')
    s_xam.default_value = 0.5
    s_xar = ng.interface.new_socket('X Angle Range', in_out='INPUT', socket_type='NodeSocketFloat')
    s_xar.default_value = 0.0
    ng.interface.new_socket('Instances', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    spline_parameter_1 = ng.nodes.new('GeometryNodeSplineParameter')

    greater_than = ng.nodes.new('FunctionNodeCompare')
    ng.links.new(spline_parameter_1.outputs['Factor'], greater_than.inputs[0])
    greater_than.inputs[1].default_value = 0.1

    random_value_3 = ng.nodes.new('FunctionNodeRandomValue')
    random_value_3.data_type = 'BOOLEAN'
    ng.links.new(inp.outputs['Needle Density'], random_value_3.inputs['Probability'])
    ng.links.new(inp.outputs['Seed'], random_value_3.inputs['Seed'])

    op_and = ng.nodes.new('FunctionNodeBooleanMath')
    ng.links.new(greater_than.outputs[0], op_and.inputs[0])
    ng.links.new(random_value_3.outputs[3], op_and.inputs[1])

    curve_tangent = ng.nodes.new('GeometryNodeInputTangent')

    align_euler_to_vector = ng.nodes.new('FunctionNodeAlignEulerToVector')
    align_euler_to_vector.axis = 'Y'
    ng.links.new(curve_tangent.outputs[0], align_euler_to_vector.inputs['Vector'])

    random_value = ng.nodes.new('FunctionNodeRandomValue')
    random_value.inputs[2].default_value = 0.6
    ng.links.new(inp.outputs['Seed'], random_value.inputs['Seed'])

    combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz.inputs['X'].default_value = 0.8
    combine_xyz.inputs['Y'].default_value = 0.8
    ng.links.new(random_value.outputs[1], combine_xyz.inputs['Z'])

    value_1 = ng.nodes.new('ShaderNodeValue')
    value_1.outputs[0].default_value = 0.3

    multiply = ng.nodes.new('ShaderNodeVectorMath')
    multiply.operation = 'MULTIPLY'
    ng.links.new(combine_xyz.outputs[0], multiply.inputs[0])
    ng.links.new(value_1.outputs[0], multiply.inputs[1])

    instance_on_points = ng.nodes.new('GeometryNodeInstanceOnPoints')
    ng.links.new(inp.outputs['Curve'], instance_on_points.inputs['Points'])
    ng.links.new(op_and.outputs[0], instance_on_points.inputs['Selection'])
    ng.links.new(inp.outputs['Instance'], instance_on_points.inputs['Instance'])
    ng.links.new(align_euler_to_vector.outputs[0], instance_on_points.inputs['Rotation'])
    ng.links.new(multiply.outputs['Vector'], instance_on_points.inputs['Scale'])

    add = ng.nodes.new('ShaderNodeMath')
    ng.links.new(inp.outputs['X Angle Mean'], add.inputs[0])
    ng.links.new(inp.outputs['X Angle Range'], add.inputs[1])

    subtract = ng.nodes.new('ShaderNodeMath')
    subtract.operation = 'SUBTRACT'
    ng.links.new(inp.outputs['X Angle Mean'], subtract.inputs[0])
    ng.links.new(inp.outputs['X Angle Range'], subtract.inputs[1])

    random_value_2 = ng.nodes.new('FunctionNodeRandomValue')
    ng.links.new(add.outputs[0], random_value_2.inputs[2])
    ng.links.new(subtract.outputs[0], random_value_2.inputs[3])
    ng.links.new(inp.outputs['Seed'], random_value_2.inputs['Seed'])

    radians = ng.nodes.new('ShaderNodeMath')
    radians.operation = 'RADIANS'
    ng.links.new(random_value_2.outputs[1], radians.inputs[0])

    random_value_1 = ng.nodes.new('FunctionNodeRandomValue')
    random_value_1.inputs[3].default_value = 360.0
    ng.links.new(inp.outputs['Seed'], random_value_1.inputs['Seed'])

    radians_1 = ng.nodes.new('ShaderNodeMath')
    radians_1.operation = 'RADIANS'
    ng.links.new(random_value_1.outputs[1], radians_1.inputs[0])

    combine_xyz_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(radians.outputs[0], combine_xyz_1.inputs['X'])
    ng.links.new(radians_1.outputs[0], combine_xyz_1.inputs['Y'])

    rotate_instances = ng.nodes.new('GeometryNodeRotateInstances')
    ng.links.new(instance_on_points.outputs[0], rotate_instances.inputs['Instances'])
    ng.links.new(combine_xyz_1.outputs[0], rotate_instances.inputs['Rotation'])

    ng.links.new(rotate_instances.outputs[0], out.inputs['Instances'])
    return ng


def make_needle5():
    """Build nodegroup_needle5: 5x instance_needle with different seeds."""

    ng_name = "nodegroup_needle5 (no gc)"
    if ng_name in bpy.data.node_groups:
        return bpy.data.node_groups[ng_name]

    ng = bpy.data.node_groups.new(ng_name, 'GeometryNodeTree')
    ng.interface.new_socket('Curve', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Instance', in_out='INPUT', socket_type='NodeSocketGeometry')
    s_xam = ng.interface.new_socket('X Angle Mean', in_out='INPUT', socket_type='NodeSocketFloat')
    s_xam.default_value = 0.5
    s_xar = ng.interface.new_socket('X Angle Range', in_out='INPUT', socket_type='NodeSocketFloat')
    s_xar.default_value = 0.0
    s_nd = ng.interface.new_socket('Needle Density', in_out='INPUT', socket_type='NodeSocketFloat')
    s_nd.default_value = 0.9
    s_seed = ng.interface.new_socket('Seed', in_out='INPUT', socket_type='NodeSocketInt')
    s_seed.default_value = 0
    ng.interface.new_socket('Instances', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    inst_needle_ng = make_instance_needle()

    # Create 5 instance_needle groups with seed, seed+1, seed+2, seed+3, seed+4
    # NOTE: In the original transpiled code, instanceneedle_1 (i=1) does NOT receive
    # the Instance input — this is faithful to the original node_transpiler output.
    instance_nodes = []
    for i in range(5):
        inst = ng.nodes.new('GeometryNodeGroup')
        inst.node_tree = inst_needle_ng
        ng.links.new(inp.outputs['Curve'], inst.inputs['Curve'])
        ng.links.new(inp.outputs['Needle Density'], inst.inputs['Needle Density'])
        if i != 1:  # instanceneedle_1 omits Instance (matches original)
            ng.links.new(inp.outputs['Instance'], inst.inputs['Instance'])
        ng.links.new(inp.outputs['X Angle Mean'], inst.inputs['X Angle Mean'])
        ng.links.new(inp.outputs['X Angle Range'], inst.inputs['X Angle Range'])

        if i == 0:
            ng.links.new(inp.outputs['Seed'], inst.inputs['Seed'])
        else:
            add_node = ng.nodes.new('ShaderNodeMath')
            ng.links.new(inp.outputs['Seed'], add_node.inputs[0])
            add_node.inputs[1].default_value = float(i)
            ng.links.new(add_node.outputs[0], inst.inputs['Seed'])

        instance_nodes.append(inst)

    join_geometry = ng.nodes.new('GeometryNodeJoinGeometry')
    # Join in reverse order (Blender JoinGeometry stacks from bottom)
    for inst in reversed(instance_nodes):
        ng.links.new(inst.outputs['Instances'], join_geometry.inputs['Geometry'])

    ng.links.new(join_geometry.outputs[0], out.inputs['Instances'])
    return ng


def make_pine_twig_nodegroup():
    """Build nodegroup_pine_twig: creates twig curve + needle instancing."""

    ng = bpy.data.node_groups.new("nodegroup_pine_twig", 'GeometryNodeTree')
    s_res = ng.interface.new_socket('Resolution', in_out='INPUT', socket_type='NodeSocketInt')
    s_res.default_value = 20
    s_my = ng.interface.new_socket('Middle Y', in_out='INPUT', socket_type='NodeSocketFloat')
    s_my.default_value = 0.0
    s_mz = ng.interface.new_socket('Middle Z', in_out='INPUT', socket_type='NodeSocketFloat')
    s_mz.default_value = 0.0
    s_nd = ng.interface.new_socket('Needle Density', in_out='INPUT', socket_type='NodeSocketFloat')
    s_nd.default_value = 0.9
    ng.interface.new_socket('Instance', in_out='INPUT', socket_type='NodeSocketGeometry')
    s_xam = ng.interface.new_socket('X Angle Mean', in_out='INPUT', socket_type='NodeSocketFloat')
    s_xam.default_value = 0.5
    s_xar = ng.interface.new_socket('X Angle Range', in_out='INPUT', socket_type='NodeSocketFloat')
    s_xar.default_value = 0.0
    s_seed = ng.interface.new_socket('Seed', in_out='INPUT', socket_type='NodeSocketInt')
    s_seed.default_value = 0
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # divide = Resolution / 30.0
    divide = ng.nodes.new('ShaderNodeMath')
    divide.operation = 'DIVIDE'
    ng.links.new(inp.outputs['Resolution'], divide.inputs[0])
    divide.inputs[1].default_value = 30.0

    # divide_1 = divide / 2.0
    divide_1 = ng.nodes.new('ShaderNodeMath')
    divide_1.operation = 'DIVIDE'
    ng.links.new(divide.outputs[0], divide_1.inputs[0])
    divide_1.inputs[1].default_value = 2.0

    # combine_xyz = (Middle Y, divide_1, Middle Z)
    combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(inp.outputs['Middle Y'], combine_xyz.inputs['X'])
    ng.links.new(divide_1.outputs[0], combine_xyz.inputs['Y'])
    ng.links.new(inp.outputs['Middle Z'], combine_xyz.inputs['Z'])

    # combine_xyz_1 = (0, divide, 0)
    combine_xyz_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(divide.outputs[0], combine_xyz_1.inputs['Y'])

    # QuadraticBezier
    quadratic_bezier = ng.nodes.new('GeometryNodeCurveQuadraticBezier')
    ng.links.new(inp.outputs['Resolution'], quadratic_bezier.inputs['Resolution'])
    _set_default(quadratic_bezier.inputs['Start'], (0.0, 0.0, 0.0))
    ng.links.new(combine_xyz.outputs[0], quadratic_bezier.inputs['Middle'])
    ng.links.new(combine_xyz_1.outputs[0], quadratic_bezier.inputs['End'])

    # Noise texture 4D
    noise_texture = ng.nodes.new('ShaderNodeTexNoise')
    noise_texture.noise_dimensions = '4D'
    noise_texture.inputs['W'].default_value = -1.7

    # value = 0.5
    value = ng.nodes.new('ShaderNodeValue')
    value.outputs[0].default_value = 0.5

    # subtract = Color - 0.5
    subtract = ng.nodes.new('ShaderNodeVectorMath')
    subtract.operation = 'SUBTRACT'
    ng.links.new(noise_texture.outputs['Color'], subtract.inputs[0])
    ng.links.new(value.outputs[0], subtract.inputs[1])

    # spline_parameter
    spline_parameter = ng.nodes.new('GeometryNodeSplineParameter')

    # multiply = Factor * 0.1
    multiply = ng.nodes.new('ShaderNodeMath')
    multiply.operation = 'MULTIPLY'
    ng.links.new(spline_parameter.outputs['Factor'], multiply.inputs[0])
    multiply.inputs[1].default_value = 0.1

    # multiply_1 = subtract * multiply (vector)
    multiply_1 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_1.operation = 'MULTIPLY'
    ng.links.new(subtract.outputs['Vector'], multiply_1.inputs[0])
    ng.links.new(multiply.outputs[0], multiply_1.inputs[1])

    # set_position = offset bezier by noise
    set_position = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(quadratic_bezier.outputs[0], set_position.inputs['Geometry'])
    ng.links.new(multiply_1.outputs['Vector'], set_position.inputs['Offset'])

    # map_range: Factor -> [1.0, 0.0]
    map_range = ng.nodes.new('ShaderNodeMapRange')
    ng.links.new(spline_parameter.outputs['Factor'], map_range.inputs['Value'])
    map_range.inputs[3].default_value = 1.0
    map_range.inputs[4].default_value = 0.0

    # power = 2.0 ^ map_range
    power = ng.nodes.new('ShaderNodeMath')
    power.operation = 'POWER'
    power.inputs[0].default_value = 2.0
    ng.links.new(map_range.outputs['Result'], power.inputs[1])

    # set_curve_radius
    set_curve_radius = ng.nodes.new('GeometryNodeSetCurveRadius')
    ng.links.new(set_position.outputs[0], set_curve_radius.inputs['Curve'])
    ng.links.new(power.outputs[0], set_curve_radius.inputs['Radius'])

    # curve_circle (profile)
    curve_circle = ng.nodes.new('GeometryNodeCurvePrimitiveCircle')
    curve_circle.inputs['Resolution'].default_value = 16
    curve_circle.inputs['Radius'].default_value = 0.01

    # curve_to_mesh (Blender 5.0: use named kwargs, Scale=power for radius)
    curve_to_mesh = ng.nodes.new('GeometryNodeCurveToMesh')
    ng.links.new(set_curve_radius.outputs[0], curve_to_mesh.inputs['Curve'])
    ng.links.new(curve_circle.outputs['Curve'], curve_to_mesh.inputs['Profile Curve'])
    ng.links.new(power.outputs[0], curve_to_mesh.inputs['Scale'])
    curve_to_mesh.inputs['Fill Caps'].default_value = True

    # Shape-only: skip SetMaterial for twig, pass mesh directly

    # needle5 sub-group
    needle5_ng = make_needle5()
    needle5 = ng.nodes.new('GeometryNodeGroup')
    needle5.node_tree = needle5_ng
    ng.links.new(set_position.outputs[0], needle5.inputs['Curve'])
    ng.links.new(inp.outputs['Instance'], needle5.inputs['Instance'])
    ng.links.new(inp.outputs['X Angle Mean'], needle5.inputs['X Angle Mean'])
    ng.links.new(inp.outputs['X Angle Range'], needle5.inputs['X Angle Range'])
    ng.links.new(inp.outputs['Needle Density'], needle5.inputs['Needle Density'])
    ng.links.new(inp.outputs['Seed'], needle5.inputs['Seed'])

    # join twig mesh + needle instances
    join_geometry = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(curve_to_mesh.outputs[0], join_geometry.inputs['Geometry'])
    ng.links.new(needle5.outputs['Instances'], join_geometry.inputs['Geometry'])

    # realize instances
    realize_instances = ng.nodes.new('GeometryNodeRealizeInstances')
    ng.links.new(join_geometry.outputs[0], realize_instances.inputs['Geometry'])

    # set shade smooth = False
    set_shade_smooth = ng.nodes.new('GeometryNodeSetShadeSmooth')
    ng.links.new(realize_instances.outputs[0], set_shade_smooth.inputs['Geometry'])
    set_shade_smooth.inputs['Shade Smooth'].default_value = False

    ng.links.new(set_shade_smooth.outputs[0], out.inputs['Geometry'])
    return ng


def make_geo_pine_twig(needle_name="Needle", length=30, middle_y=0.0, middle_z=0.0,
                       seed=0, x_angle_mean=-50.0, x_angle_range=10.0):
    """Build top-level GeoNodes tree: ObjectInfo -> pine_twig nodegroup."""

    ng = bpy.data.node_groups.new("geo_pine_twig", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = ng.nodes.new('NodeGroupInput')
    out = ng.nodes.new('NodeGroupOutput'); out.is_active_output = True

    # ObjectInfo node referencing the needle mesh
    object_info = ng.nodes.new('GeometryNodeObjectInfo')
    object_info.inputs['Object'].default_value = bpy.data.objects[needle_name]

    # Pine twig sub-group
    pine_twig_ng = make_pine_twig_nodegroup()
    pine_twig = ng.nodes.new('GeometryNodeGroup')
    pine_twig.node_tree = pine_twig_ng
    pine_twig.inputs['Resolution'].default_value = length
    pine_twig.inputs['Middle Y'].default_value = middle_y
    pine_twig.inputs['Middle Z'].default_value = middle_z
    ng.links.new(object_info.outputs['Geometry'], pine_twig.inputs['Instance'])
    pine_twig.inputs['X Angle Mean'].default_value = x_angle_mean
    pine_twig.inputs['X Angle Range'].default_value = x_angle_range
    pine_twig.inputs['Seed'].default_value = seed

    ng.links.new(pine_twig.outputs['Geometry'], out.inputs['Geometry'])
    return ng


def make_pine_twig_obj(**kwargs):
    """Create a plane, apply the pine twig GeoNodes, return the object."""

    bpy.ops.mesh.primitive_plane_add(
        size=2, enter_editmode=False, align="WORLD", location=(0, 0, 0), scale=(1, 1, 1)
    )
    twig = bpy.context.active_object
    twig.name = "Twig"

    # Build GeoNodes tree and assign as modifier (replaces surface.add_geomod)
    geo_ng = make_geo_pine_twig(**kwargs)
    mod = twig.modifiers.new(name="geo_pine_twig", type='NODES')
    mod.node_group = geo_ng

    return twig


class LeafFactoryPine(AssetFactory):
    scale = 0.7

    def __init__(self, factory_seed, season="autumn", coarse=False):
        super(LeafFactoryPine, self).__init__(factory_seed, coarse=coarse)
        self.needle = make_needle("Needle")
        self.needle.hide_viewport = True
        self.needle.hide_render = True

    def create_asset(self, **params):
        # with FixedSeed(self.factory_seed):
        seed = randint(0, 1e6)
        middle_y = normal(0.0, 0.1)
        middle_z = normal(0.0, 0.1)
        length = randint(25, 35)
        x_angle_mean = uniform(-40, -60)

        obj = make_pine_twig_obj(
            needle_name="Needle",
            length=length,
            middle_y=middle_y,
            middle_z=middle_z,
            seed=seed,
            x_angle_mean=x_angle_mean,
            x_angle_range=10.0,
        )

        bpy.ops.object.convert(target="MESH")

        obj = bpy.context.object
        obj.scale *= normal(1, 0.05) * self.scale
        butil.apply_transform(obj)
        butil.purge_empty_materials(obj)
        tag_object(obj, "leaf_pine")

        return obj

def build(seed=0, season="autumn"):
    fac = LeafFactoryPine(seed, season)
    with FixedSeed(int_hash((seed, seed))):
        return fac.create_asset()

SEED = 0
build(SEED)
