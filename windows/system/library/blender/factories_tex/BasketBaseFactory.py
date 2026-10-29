# [FL_INDEX: keywords="blender_factory, procedural_3d, BasketBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BasketBaseFactory | Category: factories_tex
# Prompt: A 3D model of a rectangular open-top storage basket rendered from a three-quarter perspective, featuring gently sloped sides, a flat bottom, and rectangular cutout handles on opposite sides, with a smooth mint-green surface coloring.

import os
import math
import random
import colorsys
import hashlib
from types import SimpleNamespace

import bpy
import numpy as np
from numpy.random import uniform

C = bpy.context
D = bpy.data

class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
        self.py_state = None
        self.np_state = None
    def __enter__(self):
        self.py_state = random.getstate(); self.np_state = np.random.get_state()
        random.seed(self.seed); np.random.seed(self.seed)
    def __exit__(self, *_):
        random.setstate(self.py_state); np.random.set_state(self.np_state)

def md5_hash(x):
    if isinstance(x, (tuple, list)):
        m = hashlib.md5(); [m.update(str(s).encode('utf-8')) for s in x]; return m
    return hashlib.md5(str(x).encode('utf-8'))

def int_hash(x, max=(2**32 - 1)):
    return abs(int(md5_hash(x).hexdigest(), 16)) % max

def seed_all(seed):
    np.random.seed(int(seed)); random.seed(int(seed))

# Shader helpers (used by the plastic_rough re-implementation)

def hsv2rgba(h, s, v):
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
    }
    for key, val in kw.items():
        names = aliases.get(key, (key,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = val
                break

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

# Faithful re-implementation of
# The source wraps the BSDF + 4D noise displacement in a
# `nodegroup_plastics` group. We inline the full node graph directly into the
# material's own node tree rather than via a group, which is semantically
# equivalent.

def make_plastic_rough(name="PlasticRough", base_color=None, roughness=None,
                       seed=None, scale=1.0):
    # numpy.random consumption order mirrors shader_rough_plastic():
    #   roughness  <- uniform(0.0, 1.0)
    #   seed       <- uniform(-1000.0, 1000.0)
    #   base_color <- hsv2rgba(uniform(0,1), uniform(0.5,0.8), log_uniform(0.01,0.5))
    if roughness is None:
        roughness = float(np.random.uniform(0.0, 1.0))
    if seed is None:
        seed = float(np.random.uniform(-1000.0, 1000.0))
    if base_color is None:
        base_color = hsv2rgba(
            float(np.random.uniform(0, 1)),
            float(np.random.uniform(0.5, 0.8)),
            log_uniform(0.01, 0.5),
        )

    mat = _new_material(name)
    nt = mat.node_tree
    link = nt.links.new

    # Roughness map_range: 0..1 -> 0.05..0.25 (see source MapRange [3]/[4])
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = float(roughness)
    map_range.inputs[1].default_value = 0.0
    map_range.inputs[2].default_value = 1.0
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    link(map_range.outputs["Result"], bsdf.inputs["Roughness"])

    # Texture coordinate -> 4D noise (Blender 5.0 preserves 4D mode)
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Scale * 2000 (multiplies the user "Scale" by 2000 for noise)
    scale_mul = nt.nodes.new("ShaderNodeMath")
    scale_mul.operation = "MULTIPLY"
    scale_mul.inputs[0].default_value = float(scale)
    scale_mul.inputs[1].default_value = 2000.0

    noise = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise.noise_dimensions = "4D"
    except Exception:
        pass
    link(tex_coord.outputs["Object"], noise.inputs["Vector"])
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = float(seed)
    link(scale_mul.outputs[0], noise.inputs["Scale"])
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0

    # Displacement chain: noise.Fac * (map_range.Result * 0.4) * 0.003
    mul_rough = nt.nodes.new("ShaderNodeMath")
    mul_rough.operation = "MULTIPLY"
    mul_rough.inputs[1].default_value = 0.4
    link(map_range.outputs["Result"], mul_rough.inputs[0])

    mul_noise = nt.nodes.new("ShaderNodeMath")
    mul_noise.operation = "MULTIPLY"
    link(_noise_fac_output(noise), mul_noise.inputs[0])
    link(mul_rough.outputs[0], mul_noise.inputs[1])

    mul_small = nt.nodes.new("ShaderNodeMath")
    mul_small.operation = "MULTIPLY"
    mul_small.inputs[1].default_value = 0.003
    link(mul_noise.outputs[0], mul_small.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    link(mul_small.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# Geometry: copied verbatim from objects_blender/organizer/BasketBaseFactory.py
# except `shader_rough_plastic` is wired to return the material we build in
# so that after the geometry nodes modifier is applied, MAT_PLASTIC is the
# sole material slot.

def _select_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    if o is not None: o.select_set(True)

def geometry_node_group_empty_new():
    group = bpy.data.node_groups.new('Geometry Nodes', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = group.nodes.new('NodeGroupInput')
    out = group.nodes.new('NodeGroupOutput')
    out.is_active_output = True
    try:
        group.links.new(inp.outputs['Geometry'], out.inputs['Geometry'])
    except Exception:
        pass
    return group

def ng_inputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == 'INPUT'}

def ng_outputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == 'OUTPUT'}

def assign_curve(c, points, handles=None):
    for i, p in enumerate(points):
        if i < 2: c.points[i].location = p
        else: c.points.new(*p)
        if handles is not None: c.points[i].handle_type = handles[i]

def to_nodegroup(name=None, singleton=False, type='GeometryNodeTree'):
    def reg(fn):
        ng_name = name or fn.__name__
        if singleton: ng_name += ' (no gc)'
        def init_fn(*args, **kwargs):
            if singleton and ng_name in bpy.data.node_groups:
                return bpy.data.node_groups[ng_name]
            ng = bpy.data.node_groups.new(ng_name, type)
            nw = NodeWrangler(ng)
            fn(nw, *args, **kwargs)
            return ng
        return init_fn
    return reg

node_utils = SimpleNamespace(to_nodegroup=to_nodegroup, assign_curve=assign_curve)

def _infer_output_socket(item):
    if isinstance(item, bpy.types.NodeSocket): return item
    if isinstance(item, tuple) and len(item) == 2 and hasattr(item[0], 'outputs'):
        n, s = item
        try: return n.outputs[s]
        except Exception: return n.outputs[int(s)]
    if hasattr(item, 'outputs'):
        for s in item.outputs:
            if getattr(s, 'enabled', True): return s
        if len(item.outputs): return item.outputs[0]
    return None

def _socket_type_for_val(v):
    if isinstance(v, bool): return 'NodeSocketBool'
    if isinstance(v, int): return 'NodeSocketInt'
    if isinstance(v, float): return 'NodeSocketFloat'
    if isinstance(v, (tuple, list, np.ndarray)):
        if len(v) == 3: return 'NodeSocketVector'
        if len(v) == 4: return 'NodeSocketColor'
    return 'NodeSocketFloat'

def _socket_type_for_out(sock):
    if sock is None: return 'NodeSocketFloat'
    sid = getattr(sock, 'bl_idname', None)
    return sid if isinstance(sid, str) and sid.startswith('NodeSocket') else 'NodeSocketFloat'

class NodeWrangler:
    def __init__(self, node_group_or_mod):
        if isinstance(node_group_or_mod, bpy.types.NodesModifier):
            self.modifier = node_group_or_mod
            self.node_group = self.modifier.node_group
        else:
            self.modifier = None
            self.node_group = node_group_or_mod
        self.nodes = self.node_group.nodes
        self.links = self.node_group.links

    def _group_io(self, bl_idname):
        for n in self.nodes:
            if n.bl_idname == bl_idname: return n
        n = self.nodes.new(bl_idname)
        if bl_idname == 'NodeGroupOutput': n.is_active_output = True
        return n

    def expose_input(self, name, val=None, attribute=None, dtype=None, use_namednode=False):
        gi = self._group_io('NodeGroupInput')
        if name not in ng_inputs(self.node_group):
            socket_type = dtype if isinstance(dtype, str) and dtype.startswith('NodeSocket') else _socket_type_for_val(val)
            if val is None and name == 'Geometry': socket_type = 'NodeSocketGeometry'
            iface = self.node_group.interface.new_socket(name=name, in_out='INPUT', socket_type=socket_type)
            if val is not None and hasattr(iface, 'default_value'):
                try: iface.default_value = val
                except Exception:
                    try: iface.default_value = tuple(val)
                    except Exception: pass
            if self.modifier is not None and val is not None:
                try: self.modifier[iface.identifier] = val
                except Exception: pass
        return gi.outputs[name]

    def connect_input(self, sock, item):
        if isinstance(item, list):
            for it in item: self.connect_input(sock, it)
            return
        out = _infer_output_socket(item)
        if out is not None:
            self.links.new(out, sock)
            return
        if hasattr(sock, 'default_value'):
            try: sock.default_value = item
            except Exception:
                try: sock.default_value = tuple(item)
                except Exception: pass

    def _make_node(self, node_type):
        if isinstance(node_type, str) and node_type in bpy.data.node_groups and not node_type.startswith(('ShaderNode','GeometryNode','FunctionNode','CompositorNode','NodeGroup')):
            n = self.nodes.new('GeometryNodeGroup' if self.node_group.bl_idname == 'GeometryNodeTree' else 'ShaderNodeGroup')
            n.node_tree = bpy.data.node_groups[node_type]
            return n
        if isinstance(node_type, str) and node_type in bpy.data.node_groups:
            try: return self.nodes.new(node_type)
            except Exception:
                n = self.nodes.new('GeometryNodeGroup' if self.node_group.bl_idname == 'GeometryNodeTree' else 'ShaderNodeGroup')
                n.node_tree = bpy.data.node_groups[node_type]
                return n
        return self.nodes.new(node_type)

    def new_node(self, node_type, input_args=None, attrs=None, input_kwargs=None, label=None, expose_input=None, compat_mode=True, strict=True):
        input_args = [] if input_args is None else list(input_args)
        attrs = {} if attrs is None else dict(attrs)
        input_kwargs = {} if input_kwargs is None else dict(input_kwargs)
        if node_type == getattr(Nodes, 'GroupInput', 'NodeGroupInput'):
            node = self._group_io('NodeGroupInput')
        elif node_type == getattr(Nodes, 'GroupOutput', 'NodeGroupOutput'):
            node = self._group_io('NodeGroupOutput')
        else:
            node = self._make_node(node_type)
        if label is not None:
            node.label = label; node.name = label
        if expose_input is not None:
            for dtype, name, val in expose_input:
                self.expose_input(name, val=val, dtype=dtype)
        for k, v in attrs.items():
            t = node
            if '.' in k:
                parts = k.split('.')
                for p in parts[:-1]: t = getattr(t, p)
                setattr(t, parts[-1], v)
            else:
                setattr(node, k, v)
        for k, v in list(enumerate(input_args)) + list(input_kwargs.items()):
            if v is None: continue
            if node.bl_idname == 'NodeGroupOutput' and not isinstance(k, int) and k not in node.inputs:
                out_sock = _infer_output_socket(v)
                self.node_group.interface.new_socket(name=k, in_out='OUTPUT', socket_type=_socket_type_for_out(out_sock))
            try: sock = node.inputs[k]
            except Exception: sock = node.inputs[int(k)]
            self.connect_input(sock, v)
        return node

def shaderfunc_to_material(shader_func, *args, name=None, **kwargs):
    mat_name = name or getattr(shader_func, '__name__', 'Material')
    mat = bpy.data.materials.get(mat_name)
    if mat is None: mat = bpy.data.materials.new(name=mat_name)
    return mat

def add_geomod(objs, geo_func, name=None, apply=False, input_args=None, input_kwargs=None, attributes=None, **_ignored):
    if input_args is None: input_args = []
    if input_kwargs is None: input_kwargs = {}
    if attributes is None: attributes = []
    if not isinstance(objs, list): objs = [objs]
    if not objs: return None
    ng = None
    mod_last = None
    for obj in objs:
        mod = obj.modifiers.new(name=name or geo_func.__name__, type='NODES')
        if ng is None:
            if mod.node_group is None: mod.node_group = geometry_node_group_empty_new()
            nw = NodeWrangler(mod)
            geo_func(nw, *input_args, **input_kwargs)
            ng = mod.node_group
            ng.name = name or geo_func.__name__
        else:
            mod.node_group = ng
        if attributes:
            try:
                outs = [o for o in ng_outputs(mod.node_group).values() if getattr(o, 'socket_type', None) != 'NodeSocketGeometry']
                for o, att in zip(outs, attributes):
                    if att: mod[o.identifier + '_attribute_name'] = att
            except Exception:
                pass
        if apply:
            _select_none()
            _set_active(obj)
            bpy.ops.object.modifier_apply(modifier=mod.name)
        mod_last = mod
    return mod_last

class AssetFactory:
    def __init__(self, factory_seed=None, coarse=False):
        self.factory_seed = int(factory_seed if factory_seed is not None else np.random.randint(1e9))
        self.coarse = coarse
    def __call__(self, i=0, **kwargs):
        with FixedSeed(int_hash((self.factory_seed, i))):
            return self.create_asset(i=i, **kwargs)

class Nodes:
    CombineXYZ = 'ShaderNodeCombineXYZ'
    GroupInput = 'NodeGroupInput'
    GroupOutput = 'NodeGroupOutput'
    InstanceOnPoints = 'GeometryNodeInstanceOnPoints'
    Integer = 'FunctionNodeInputInt'
    Math = 'ShaderNodeMath'
    MeshBoolean = 'GeometryNodeMeshBoolean'
    MeshCube = 'GeometryNodeMeshCube'
    MeshGrid = 'GeometryNodeMeshGrid'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    SetMaterial = 'GeometryNodeSetMaterial'
    StoreNamedAttribute = 'GeometryNodeStoreNamedAttribute'
    SubdivideMesh = 'GeometryNodeSubdivideMesh'
    SubdivisionSurface = 'GeometryNodeSubdivisionSurface'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'

# The original stub returned None; we redirect it to the real material sampled
# in Phase 1, but `shaderfunc_to_material` inside geometry_nodes() still does
# the lookup-by-name that the GeoNodes SetMaterial node expects.
def shader_rough_plastic(nw=None, *args, **kwargs):
    return None

@node_utils.to_nodegroup("nodegroup_holes", singleton=False, type="GeometryNodeTree")
def nodegroup_holes(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "Value1", 0.5000),
            ("NodeSocketFloat", "Value2", 0.5000),
            ("NodeSocketFloat", "Value3", 0.5000),
            ("NodeSocketFloat", "Value4", 0.5000),
            ("NodeSocketFloat", "Value5", 0.5000),
            ("NodeSocketFloat", "Value6", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["Value3"], 1: 0.0000}
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["Value1"], 1: add},
        attrs={"operation": "SUBTRACT"},
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["Value6"], 1: 0.0000}
    )

    subtract_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1, 1: add}, attrs={"operation": "SUBTRACT"}
    )

    add_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["Value4"], 1: 0.0000}
    )

    add_3 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_2, 1: group_input.outputs["Value2"]}
    )

    divide = nw.new_node(
        Nodes.Math, input_kwargs={0: subtract, 1: add_3}, attrs={"operation": "DIVIDE"}
    )

    divide_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: subtract_1, 1: add_3},
        attrs={"operation": "DIVIDE"},
    )

    grid = nw.new_node(
        Nodes.MeshGrid,
        input_kwargs={
            "Size X": subtract,
            "Size Y": subtract_1,
            "Vertices X": divide,
            "Vertices Y": divide_1,
        },
    )

    store_named_attribute = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": grid.outputs["Mesh"],
            "Name": "uv_map",
            3: grid.outputs["UV Map"],
        },
        attrs={"domain": "CORNER", "data_type": "FLOAT_VECTOR"},
    )

    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": store_named_attribute,
            "Rotation": (0.0000, 1.5708, 0.0000),
        },
    )

    add_4 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["Value5"], 1: 0.0000}
    )

    add_5 = nw.new_node(Nodes.Math, input_kwargs={0: add_4, 1: 0.1})

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add_5, "Y": add_2, "Z": add_2}
    )

    cube_2 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_3})

    store_named_attribute_1 = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube_2.outputs["Mesh"],
            "Name": "uv_map",
            3: cube_2.outputs["UV Map"],
        },
        attrs={"domain": "CORNER", "data_type": "FLOAT_VECTOR"},
    )

    instance_on_points = nw.new_node(
        Nodes.InstanceOnPoints,
        input_kwargs={"Points": transform_1, "Instance": store_named_attribute_1},
    )

    subtract_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_4, 1: add}, attrs={"operation": "SUBTRACT"}
    )

    divide_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: subtract_2, 1: add_3},
        attrs={"operation": "DIVIDE"},
    )

    grid_1 = nw.new_node(
        Nodes.MeshGrid,
        input_kwargs={
            "Size X": subtract_2,
            "Size Y": subtract,
            "Vertices X": divide_2,
            "Vertices Y": divide,
        },
    )

    store_named_attribute_2 = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": grid_1.outputs["Mesh"],
            "Name": "uv_map",
            3: grid_1.outputs["UV Map"],
        },
        attrs={"domain": "CORNER", "data_type": "FLOAT_VECTOR"},
    )

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": store_named_attribute_2,
            "Rotation": (1.5708, 0.0000, 0.0000),
        },
    )

    add_6 = nw.new_node(Nodes.Math, input_kwargs={0: add_1, 1: 0.1})

    combine_xyz_4 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add_2, "Y": add_6, "Z": add_2}
    )

    cube_3 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_4})

    store_named_attribute_3 = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube_3.outputs["Mesh"],
            "Name": "uv_map",
            3: cube_3.outputs["UV Map"],
        },
        attrs={"domain": "CORNER", "data_type": "FLOAT_VECTOR"},
    )

    instance_on_points_1 = nw.new_node(
        Nodes.InstanceOnPoints,
        input_kwargs={"Points": transform_2, "Instance": store_named_attribute_3},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={
            "Instances1": instance_on_points,
            "Instances2": instance_on_points_1,
        },
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_handle_hole", singleton=False, type="GeometryNodeTree"
)
def nodegroup_handle_hole(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "X", 0.0000),
            ("NodeSocketFloat", "Z", 0.0000),
            ("NodeSocketFloat", "Value", 0.5000),
            ("NodeSocketFloat", "Value2", 0.5000),
            ("NodeSocketInt", "Level", 0),
        ],
    )

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={
            "X": group_input.outputs["X"],
            "Y": 1.0000,
            "Z": group_input.outputs["Z"],
        },
    )

    cube_2 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_3})

    store_named_attribute = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube_2.outputs["Mesh"],
            "Name": "uv_map",
            3: cube_2.outputs["UV Map"],
        },
        attrs={"domain": "CORNER", "data_type": "FLOAT_VECTOR"},
    )

    subdivide_mesh_2 = nw.new_node(
        Nodes.SubdivideMesh, input_kwargs={"Mesh": store_named_attribute}
    )

    subdivision_surface_2 = nw.new_node(
        Nodes.SubdivisionSurface,
        input_kwargs={"Mesh": subdivide_mesh_2, "Level": group_input.outputs["Level"]},
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["Value"]},
        attrs={"operation": "MULTIPLY"},
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply, 1: group_input.outputs["Value2"]},
        attrs={"operation": "SUBTRACT"},
    )

    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": subtract})

    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": subdivision_surface_2, "Translation": combine_xyz_4},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_1},
        attrs={"is_active_output": True},
    )

def geometry_nodes(nw: NodeWrangler, **kwargs):
    # Code generated using version 2.6.4 of the node_transpiler

    depth = nw.new_node(Nodes.Value, label="depth")
    depth.outputs[0].default_value = kwargs["depth"]

    width = nw.new_node(Nodes.Value, label="width")
    width.outputs[0].default_value = kwargs["width"]

    height = nw.new_node(Nodes.Value, label="height")
    height.outputs[0].default_value = kwargs["height"]

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": depth, "Y": width, "Z": height}
    )

    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    store_named_attribute = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube.outputs["Mesh"],
            "Name": "uv_map",
            3: cube.outputs["UV Map"],
        },
        attrs={"domain": "CORNER", "data_type": "FLOAT_VECTOR"},
    )

    subdivide_mesh = nw.new_node(
        Nodes.SubdivideMesh, input_kwargs={"Mesh": store_named_attribute, "Level": 2}
    )

    sub_level = nw.new_node(Nodes.Integer, label="sub_level")
    sub_level.integer = kwargs["frame_sub_level"]

    subdivision_surface = nw.new_node(
        Nodes.SubdivisionSurface,
        input_kwargs={"Mesh": subdivide_mesh, "Level": sub_level},
    )

    differences = []

    if kwargs["has_handle"]:
        hole_depth = nw.new_node(Nodes.Value, label="hole_depth")
        hole_depth.outputs[0].default_value = kwargs["handle_depth"]

        hole_height = nw.new_node(Nodes.Value, label="hole_height")
        hole_height.outputs[0].default_value = kwargs["handle_height"]

        hole_dist = nw.new_node(Nodes.Value, label="hole_dist")
        hole_dist.outputs[0].default_value = kwargs["handle_dist_to_top"]

        handle_level = nw.new_node(Nodes.Integer, label="handle_level")
        handle_level.integer = kwargs["handle_sub_level"]
        handle_hole = nw.new_node(
            nodegroup_handle_hole().name,
            input_kwargs={
                "X": hole_depth,
                "Z": hole_height,
                "Value": height,
                "Value2": hole_dist,
                "Level": handle_level,
            },
        )
        differences.append(handle_hole)

    thickness = nw.new_node(Nodes.Value, label="thickness")
    thickness.outputs[0].default_value = kwargs["thickness"]

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: depth, 1: thickness},
        attrs={"operation": "SUBTRACT"},
    )

    subtract_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: width, 1: thickness},
        attrs={"operation": "SUBTRACT"},
    )

    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": subtract_1, "Z": height}
    )

    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_1})

    store_named_attribute_1 = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube_1.outputs["Mesh"],
            "Name": "uv_map",
            3: cube_1.outputs["UV Map"],
        },
        attrs={"domain": "CORNER", "data_type": "FLOAT_VECTOR"},
    )

    subdivide_mesh_1 = nw.new_node(
        Nodes.SubdivideMesh, input_kwargs={"Mesh": store_named_attribute_1, "Level": 2}
    )

    subdivision_surface_1 = nw.new_node(
        Nodes.SubdivisionSurface,
        input_kwargs={"Mesh": subdivide_mesh_1, "Level": sub_level},
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: thickness, 1: 0.2500},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply})

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": subdivision_surface_1, "Translation": combine_xyz_2},
    )

    if kwargs["has_holes"]:
        gap_size = nw.new_node(Nodes.Value, label="gap_size")
        gap_size.outputs[0].default_value = kwargs["hole_gap_size"]

        hole_edge_gap = nw.new_node(Nodes.Value, label="hole_edge_gap")
        hole_edge_gap.outputs[0].default_value = kwargs["hole_edge_gap"]

        hole_size = nw.new_node(Nodes.Value, label="hole_size")
        hole_size.outputs[0].default_value = kwargs["hole_size"]
        holes = nw.new_node(
            nodegroup_holes().name,
            input_kwargs={
                "Value1": height,
                "Value2": gap_size,
                "Value3": hole_edge_gap,
                "Value4": hole_size,
                "Value5": depth,
                "Value6": width,
            },
        )
        differences.extend([holes.outputs["Instances1"], holes.outputs["Instances2"]])

    difference = nw.new_node(
        Nodes.MeshBoolean,
        input_kwargs={
            "Mesh 1": subdivision_surface,
            "Mesh 2": [transform] + differences,
        },
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": difference.outputs["Mesh"]}
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: height}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_1})

    transform_geometry = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": realize_instances, "Translation": combine_xyz_3},
    )

    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": transform_geometry,
            "Material": MAT_PLASTIC,
        },
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": set_material},
        attrs={"is_active_output": True},
    )

class BasketBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(BasketBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = params

    def sample_params(self):
        return self.params.copy()

    def get_asset_params(self, i=0):
        params = self.sample_params()
        if params.get("depth", None) is None:
            params["depth"] = uniform(0.15, 0.4)
        if params.get("width", None) is None:
            params["width"] = uniform(0.2, 0.6)
        if params.get("height", None) is None:
            params["height"] = uniform(0.06, 0.24)
        if params.get("frame_sub_level", None) is None:
            params["frame_sub_level"] = np.random.choice([0, 3], p=[0.5, 0.5])
        if params.get("thickness", None) is None:
            params["thickness"] = uniform(0.001, 0.005)

        if params.get("has_handle", None) is None:
            params["has_handle"] = np.random.choice([True, False], p=[0.8, 0.2])
        if params.get("handle_sub_level", None) is None:
            params["handle_sub_level"] = np.random.choice([0, 1, 2], p=[0.2, 0.4, 0.4])
        if params.get("handle_depth", None) is None:
            params["handle_depth"] = params["depth"] * uniform(0.2, 0.4)
        if params.get("handle_height", None) is None:
            params["handle_height"] = params["height"] * uniform(0.1, 0.25)
        if params.get("handle_dist_to_top", None) is None:
            params["handle_dist_to_top"] = params["handle_height"] * 0.5 + params[
                "height"
            ] * uniform(0.08, 0.15)

        if params.get("has_holes", None) is None:
            if params["height"] < 0.12:
                params["has_holes"] = False
            else:
                params["has_holes"] = np.random.choice([True, False], p=[0.5, 0.5])
        if params.get("hole_size", None) is None:
            params["hole_size"] = uniform(0.005, 0.01)
        if params.get("hole_gap_size", None) is None:
            params["hole_gap_size"] = params["hole_size"] * uniform(0.8, 1.1)
        if params.get("hole_edge_gap", None) is None:
            params["hole_edge_gap"] = uniform(0.04, 0.06)

        return params

    def create_asset(self, i=0, **params):
        bpy.ops.mesh.primitive_plane_add(
            size=1,
            enter_editmode=False,
            align="WORLD",
            location=(0, 0, 0),
            scale=(1, 1, 1),
        )
        obj = bpy.context.active_object

        obj_params = self.get_asset_params(i)
        add_geomod(
            obj, geometry_nodes, attributes=[], apply=True, input_kwargs=obj_params
        )

        # After the GeoNodes modifier is applied, the SetMaterial node placed
        # MAT_PLASTIC into the mesh's material slots. Ensure the mesh's slot 0
        # is exactly MAT_PLASTIC so the renderer picks it up cleanly (even if
        # no slot was auto-created on apply).
        if obj.data is not None:
            if len(obj.data.materials) == 0:
                obj.data.materials.append(MAT_PLASTIC)
            else:
                obj.data.materials[0] = MAT_PLASTIC

        return obj

SEED = int(os.environ.get('SEED', 0))
seed_all(SEED)

# geometry_nodes (basket.py line 436). No material_assignments registry lookup,
# no clear=True, no alternative shader. Not finalized via wear_tear.
MAT_PLASTIC = make_plastic_rough(name="BasketPlasticRough")
MAT_PLASTIC.use_fake_user = True

# AssetFactory.__call__)
def build(seed=0):
    fac = BasketBaseFactory(seed)
    with FixedSeed(int_hash((fac.factory_seed, 0))):
        obj = fac.create_asset(i=0)
    obj.name = "BasketBaseFactory"
    return obj

obj = build(SEED)

