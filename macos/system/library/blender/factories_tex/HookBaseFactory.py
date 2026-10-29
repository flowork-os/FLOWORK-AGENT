# [FL_INDEX: keywords="blender_factory, procedural_3d, HookBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: HookBaseFactory | Category: factories_tex
# Prompt: A 3D model of a wall-mounted hook rack rendered from a three-quarter perspective, featuring a flat rectangular backplate panel with a dark border frame and curved hook feet extending from the bottom edge for hanging items.

"""Standalone textured HookBaseFactory -- geometry + materials in one file.

  - Hook curves use shader_brushed_metal   (metal/brushed_metal.py)
  - Mounting board uses  shader_rough_plastic (plastic/plastic_rough.py)
Both materials are constructed inside the hook geometry-nodes tree by the
source via `SetMaterial` nodes -- we replicate that topology.

No wear_tear: hook.py has no `finalize_assets` override and is not listed in
composition/material_assignments.py.

Geometry code is copied verbatim from objects_blender/organizer/HookBaseFactory.py.

Run: [SEED=0] blender --background --python HookBaseFactory.py
"""


SEED = 0

import os
import math
import random
import hashlib
import colorsys
from types import SimpleNamespace

import bpy
import numpy as np
from numpy.random import uniform, randint

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

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def metal_hsv():
    
    if np.random.uniform() < 0.2:
        return (np.random.uniform(0, 1),
                np.random.uniform(0.0, 0.2),
                log_uniform(0.05, 0.3))
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            log_uniform(0.02, 0.5))

def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
    }
    for k, v in kw.items():
        for name in aliases.get(k, (k,)):
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

def make_brushed_metal(name="BrushedMetal", base_color_hsv=None):

    """


    Original shader:
      - TextureCoord.Object -> Mapping(scale=(0.2,0.2,5)) -> Noise2 (4D, scale=100,
        detail=15, rough=0.4, distortion=0.1)
      - Second chain: TextureCoord.Object -> Noise1 (4D, scale=0.1, detail=15,
        rough=0.0) -> Mix(0.2, RGBA) with Mapping(scale=(1,1,20)) -> Noise3
        (vector in=mix, scale=100, detail=15, rough=0.6, distortion=0.1)
      - Mix DARKEN between Noise2.Fac and Noise3.Fac -> map_range(0.4->0.8, 0.6->1.2)
        -> HueSaturation(value) of base color; Mix -> map_range(0.4->0.2, 0.6->0.3)
        -> Principled Roughness
      - Principled BSDF Metallic=1, Specular IOR Level=0
    """

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    seed_val = float(np.random.uniform(-1000.0, 1000.0))

    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # mapping_1: scale (0.2, 0.2, 5.0) -- brush direction along Z
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    def _make_noise(scale, detail, roughness, distortion, vector_socket, seed_w):
        n = nt.nodes.new("ShaderNodeTexNoise")
        if hasattr(n, "noise_dimensions"):
            try: n.noise_dimensions = "4D"
            except TypeError: pass
        n.inputs["Scale"].default_value = float(scale)
        if "Detail" in n.inputs:
            n.inputs["Detail"].default_value = float(detail)
        if "Roughness" in n.inputs:
            n.inputs["Roughness"].default_value = float(roughness)
        if "Distortion" in n.inputs:
            n.inputs["Distortion"].default_value = float(distortion)
        if "W" in n.inputs:
            n.inputs["W"].default_value = float(seed_w)
        if vector_socket is not None:
            nt.links.new(vector_socket, n.inputs["Vector"])
        return n

    # noise_texture_2: vector=mapping_1, scale=100, detail=15, rough=0.4, distortion=0.1
    noise2 = _make_noise(100.0, 15.0, 0.4, 0.1, mapping_1.outputs["Vector"], seed_val)

    # Second branch: mapping (scale=(1,1,20)) in RGBA mix with noise_texture_1
    mapping_b = nt.nodes.new("ShaderNodeMapping")
    mapping_b.inputs["Scale"].default_value = (1.0, 1.0, 20.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_b.inputs["Vector"])

    # noise_texture_1: vector=TexCoord.Object, scale=0.1, detail=15, rough=0.0
    noise1 = _make_noise(0.1, 15.0, 0.0, 0.0, tex_coord.outputs["Object"], seed_val)

    # Mix(Fac=0.2, RGBA): A=mapping_b (Vector as color), B=noise1.Color -> Result
    mix_ab = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_ab, "data_type"):
        mix_ab.data_type = "RGBA"
    mix_ab.inputs[0].default_value = 0.2
    nt.links.new(mapping_b.outputs["Vector"], mix_ab.inputs[6])
    # noise1.Color -- may be named "Color" or only Factor; prefer Color
    n1_color = noise1.outputs.get("Color") or noise1.outputs[0]
    nt.links.new(n1_color, mix_ab.inputs[7])

    # noise_texture: vector=mix_ab.Result(2), scale=100, detail=15, rough=0.6, distortion=0.1
    noise3 = _make_noise(100.0, 15.0, 0.6, 0.1, mix_ab.outputs[2], seed_val)

    # mix_1 DARKEN RGBA(Fac=1.0): A=noise2.Fac, B=noise3.Fac
    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    if hasattr(mix_1, "blend_type"):
        try: mix_1.blend_type = "DARKEN"
        except TypeError: pass
    mix_1.inputs[0].default_value = 1.0
    nt.links.new(_noise_fac_output(noise2), mix_1.inputs[6])
    nt.links.new(_noise_fac_output(noise3), mix_1.inputs[7])

    # map_range color->value (use RGBA result output [2])
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.4
    map_range.inputs[2].default_value = 0.6
    map_range.inputs[3].default_value = 0.8
    map_range.inputs[4].default_value = 1.2
    nt.links.new(mix_1.outputs[2], map_range.inputs[0])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    nt.links.new(map_range.outputs["Result"], hsv_node.inputs["Value"])

    map_range_r = nt.nodes.new("ShaderNodeMapRange")
    map_range_r.inputs[1].default_value = 0.4
    map_range_r.inputs[2].default_value = 0.6
    map_range_r.inputs[3].default_value = 0.2
    map_range_r.inputs[4].default_value = 0.3
    nt.links.new(mix_1.outputs[2], map_range_r.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(map_range_r.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_plastic_rough(name="PlasticRough", base_color=None):

    """


    Original shader:
      - Principled BSDF.BaseColor from param
      - map_range(Value=roughness_input, 3=0.05, 4=0.25) -> BSDF.Roughness
      - TextureCoord.Object -> Noise (4D, scale=2000, detail=15, distortion=2)
      - Displacement chain: mul(map_range,0.4)*noise.Fac*0.003 -> Displacement
    """

    if base_color is None:
        # hsv2rgba(uniform(0,1), uniform(0.5,0.8), log_uniform(0.01, 0.5))
        base_color = hsv2rgba((np.random.uniform(0, 1),
                               np.random.uniform(0.5, 0.8),
                               log_uniform(0.01, 0.5)))
    roughness_input = float(np.random.uniform(0.0, 1.0))
    seed_val = float(np.random.uniform(-1000.0, 1000.0))

    mat = _new_material(name)
    nt = mat.node_tree

    # map_range(roughness_input, 3=0.05, 4=0.25) -> Roughness
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # TextureCoord + 4D noise
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try: noise.noise_dimensions = "4D"
        except TypeError: pass
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed_val
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    # Displacement chain: map_range.Result * 0.4 * noise.Fac * 0.003
    mul1 = nt.nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul1.inputs[0])

    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul2.inputs[0])
    nt.links.new(mul1.outputs[0], mul2.inputs[1])

    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    mul3.inputs[1].default_value = 0.003
    nt.links.new(mul2.outputs[0], mul3.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# Minimal NodeWrangler / AssetFactory stubs (copied verbatim from the geometry
# source objects_blender/organizer/HookBaseFactory.py) so we can reuse the
# hook_geometry_nodes() function without any imports.

C = bpy.context
D = bpy.data

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    if o is not None:
        o.select_set(True)

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
        if i < 2:
            c.points[i].location = p
        else:
            c.points.new(*p)
        if handles is not None:
            c.points[i].handle_type = handles[i]

node_utils = SimpleNamespace(assign_curve=assign_curve)

def _infer_output_socket(item):
    if isinstance(item, bpy.types.NodeSocket):
        return item
    if isinstance(item, tuple) and len(item) == 2 and hasattr(item[0], 'outputs'):
        node, sock = item
        try: return node.outputs[sock]
        except Exception: return node.outputs[int(sock)]
    if hasattr(item, 'outputs'):
        for s in item.outputs:
            if getattr(s, 'enabled', True):
                return s
        if len(item.outputs):
            return item.outputs[0]
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
            if n.bl_idname == bl_idname:
                return n
        n = self.nodes.new(bl_idname)
        if bl_idname == 'NodeGroupOutput':
            n.is_active_output = True
        return n

    def expose_input(self, name, val=None, attribute=None, dtype=None, use_namednode=False):
        gi = self._group_io('NodeGroupInput')
        if name not in ng_inputs(self.node_group):
            socket_type = dtype if isinstance(dtype, str) and dtype.startswith('NodeSocket') else _socket_type_for_val(val)
            if val is None and name == 'Geometry':
                socket_type = 'NodeSocketGeometry'
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
            for it in item:
                self.connect_input(sock, it)
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
        if isinstance(node_type, str) and node_type in bpy.data.node_groups and not node_type.startswith(
                ('ShaderNode', 'GeometryNode', 'FunctionNode', 'CompositorNode', 'NodeGroup')):
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

    def new_node(self, node_type, input_args=None, attrs=None, input_kwargs=None,
                 label=None, expose_input=None, compat_mode=True, strict=True):
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
            node.label = label
            node.name = label
        if expose_input is not None:
            for dtype, name, val in expose_input:
                self.expose_input(name, val=val, dtype=dtype)
        for k, v in attrs.items():
            t = node
            if '.' in k:
                parts = k.split('.')
                for p in parts[:-1]:
                    t = getattr(t, p)
                setattr(t, parts[-1], v)
            else:
                setattr(node, k, v)
        for k, v in list(enumerate(input_args)) + list(input_kwargs.items()):
            if v is None:
                continue
            if node.bl_idname == 'NodeGroupOutput' and not isinstance(k, int) and k not in node.inputs:
                out_sock = _infer_output_socket(v)
                self.node_group.interface.new_socket(
                    name=k, in_out='OUTPUT', socket_type=_socket_type_for_out(out_sock))
            try:
                sock = node.inputs[k]
            except Exception:
                sock = node.inputs[int(k)]
            self.connect_input(sock, v)
        return node

def add_geomod(objs, geo_func, name=None, apply=False, input_args=None, input_kwargs=None,
               attributes=None, **_ignored):
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
            if mod.node_group is None:
                mod.node_group = geometry_node_group_empty_new()
            nw = NodeWrangler(mod)
            geo_func(nw, *input_args, **input_kwargs)
            ng = mod.node_group
            ng.name = name or geo_func.__name__
        else:
            mod.node_group = ng
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
    CurveBezierSegment = 'GeometryNodeCurvePrimitiveBezierSegment'
    CurveCircle = 'GeometryNodeCurvePrimitiveCircle'
    CurveLine = 'GeometryNodeCurvePrimitiveLine'
    CurveToMesh = 'GeometryNodeCurveToMesh'
    FloatCurve = 'ShaderNodeFloatCurve'
    GroupOutput = 'NodeGroupOutput'
    InstanceOnPoints = 'GeometryNodeInstanceOnPoints'
    Integer = 'FunctionNodeInputInt'
    JoinGeometry = 'GeometryNodeJoinGeometry'
    Math = 'ShaderNodeMath'
    MergeByDistance = 'GeometryNodeMergeByDistance'
    MeshCube = 'GeometryNodeMeshCube'
    MeshLine = 'GeometryNodeMeshLine'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    ScaleInstances = 'GeometryNodeScaleInstances'
    SetCurveRadius = 'GeometryNodeSetCurveRadius'
    SetMaterial = 'GeometryNodeSetMaterial'
    SplineParameter = 'GeometryNodeSplineParameter'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'
    Vector = 'FunctionNodeInputVector'

# Geometry -- copied verbatim from objects_blender/organizer/HookBaseFactory.py.
# The only difference: the SetMaterial nodes receive real pre-built materials
# (MAT_HOOK_METAL, MAT_BOARD_PLASTIC) passed in via kwargs instead of stubs.

def hook_geometry_nodes(nw, **kwargs):
    # Code generated using version 2.6.5 of the node_transpiler

    hook_num = nw.new_node(Nodes.Integer, label="hook_num")
    hook_num.integer = kwargs["num_hook"]

    add = nw.new_node(Nodes.Math, input_kwargs={0: hook_num, 1: -1.0000})

    hook_gap = nw.new_node(Nodes.Value, label="hook_gap")
    hook_gap.outputs[0].default_value = kwargs["hook_gap"]

    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: hook_gap, 1: add}, attrs={"operation": "MULTIPLY"}
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: multiply}, attrs={"operation": "MULTIPLY"}
    )

    multiply_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_1, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_2})

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_1})

    mesh_line = nw.new_node(
        Nodes.MeshLine,
        input_kwargs={
            "Count": add,
            "Start Location": combine_xyz_2,
            "Offset": combine_xyz_1,
        },
        attrs={"mode": "END_POINTS"},
    )

    bezier_segment = nw.new_node(
        Nodes.CurveBezierSegment,
        input_kwargs={
            "Start": (0.0000, 0.0000, 0.0000),
            "Start Handle": (0.0000, 0.0000, kwargs["init_handle"]),
            "End Handle": kwargs["curve_handle"],
            "End": kwargs["curve_end_point"],
        },
    )

    curve_line = nw.new_node(Nodes.CurveLine)

    join_geometry_3 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [bezier_segment, curve_line]}
    )

    spline_parameter = nw.new_node(Nodes.SplineParameter)

    float_curve = nw.new_node(
        Nodes.FloatCurve, input_kwargs={"Factor": spline_parameter.outputs["Factor"]}
    )
    node_utils.assign_curve(
        float_curve.mapping.curves[0], [(0.0000, 0.8), (0.5, 0.8), (1.0000, 0.8)]
    )

    raduis = nw.new_node(Nodes.Value, label="raduis")
    raduis.outputs[0].default_value = kwargs["hook_radius"]

    multiply_3 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: float_curve, 1: raduis},
        attrs={"operation": "MULTIPLY"},
    )

    set_curve_radius = nw.new_node(
        Nodes.SetCurveRadius,
        input_kwargs={"Curve": join_geometry_3, "Radius": multiply_3},
    )

    curve_circle = nw.new_node(
        Nodes.CurveCircle,
        input_kwargs={
            "Resolution": kwargs["hook_resolution"],
            "Point 1": (1.0000, 0.0000, 0.0000),
            "Point 3": (-1.0000, 0.0000, 0.0000),
        },
        attrs={"mode": "POINTS"},
    )

    hook_reshape = nw.new_node(Nodes.Vector, label="hook_reshape")
    hook_reshape.vector = (1.0000, 1.0000, 1.0000)

    transform_geometry_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": curve_circle.outputs["Curve"], "Scale": hook_reshape},
    )

    # Blender 5.0: SetCurveRadius ignored by CurveToMesh -- pass via Scale input
    curve_to_mesh = nw.new_node(
        Nodes.CurveToMesh,
        input_kwargs={
            "Curve": set_curve_radius,
            "Profile Curve": transform_geometry_2,
            "Fill Caps": True,
            "Scale": multiply_3,
        },
    )

    hook_size = nw.new_node(Nodes.Value, label="hook_size")
    hook_size.outputs[0].default_value = kwargs["hook_size"]

    transform_geometry = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": curve_to_mesh, "Scale": hook_size}
    )

    realize_instances_1 = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": transform_geometry}
    )

    merge_by_distance_1 = nw.new_node(
        Nodes.MergeByDistance, input_kwargs={"Geometry": realize_instances_1}
    )

    instance_on_points = nw.new_node(
        Nodes.InstanceOnPoints,
        input_kwargs={"Points": mesh_line, "Instance": merge_by_distance_1},
    )

    scale_instances = nw.new_node(
        Nodes.ScaleInstances, input_kwargs={"Instances": instance_on_points}
    )

    # Real material injection: hook curves -> brushed metal
    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": scale_instances,
            "Material": kwargs["mat_hook_metal"],
        },
    )

    board_side_gap = nw.new_node(Nodes.Value, label="board_side_gap")
    board_side_gap.outputs[0].default_value = kwargs["board_side_gap"]

    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: board_side_gap})

    board_thickness = nw.new_node(Nodes.Value, label="board_thickness")
    board_thickness.outputs[0].default_value = kwargs["board_thickness"]

    board_height = nw.new_node(Nodes.Value, label="board_height")
    board_height.outputs[0].default_value = kwargs["board_height"]

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={"X": add_1, "Y": board_thickness, "Z": board_height},
    )

    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    multiply_4 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: board_thickness, 1: -0.5000},
        attrs={"operation": "MULTIPLY"},
    )

    multiply_5 = nw.new_node(
        Nodes.Math, input_kwargs={0: board_height}, attrs={"operation": "MULTIPLY"}
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: hook_size, 1: multiply_5},
        attrs={"operation": "SUBTRACT"},
    )

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": multiply_4, "Z": subtract}
    )

    transform_geometry_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": cube.outputs["Mesh"], "Translation": combine_xyz_3},
    )

    # Real material injection: mounting board -> rough plastic
    set_material_1 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": transform_geometry_1,
            "Material": kwargs["mat_board_plastic"],
        },
    )

    join_geometry_2 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [set_material, set_material_1]}
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_2}
    )

    triangulate = nw.new_node(
        "GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances}
    )

    transform_geometry_3 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": triangulate, "Rotation": (0.0000, 0.0000, -1.5708)},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_geometry_3},
        attrs={"is_active_output": True},
    )

class HookBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params=None, coarse=False):
        super(HookBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = dict(params) if params else {}

    def sample_params(self):
        return self.params.copy()

    def get_asset_params(self, i=0):
        params = self.sample_params()
        if params.get("num_hook", None) is None:
            params["num_hook"] = randint(3, 6)
        if params.get("hook_size", None) is None:
            params["hook_size"] = uniform(0.05, 0.1)
        if params.get("hook_radius", None) is None:
            params["hook_radius"] = uniform(0.002, 0.004) / params["hook_size"]
        else:
            params["hook_radius"] = params["hook_radius"] / params["hook_size"]

        if params.get("hook_resolution", None) is None:
            params["hook_resolution"] = np.random.choice([4, 32], p=[0.5, 0.5])

        if params.get("hook_gap", None) is None:
            params["hook_gap"] = uniform(0.04, 0.08)
        if params.get("board_height", None) is None:
            params["board_height"] = params["hook_size"] + uniform(-0.02, 0.01)
        if params.get("board_thickness", None) is None:
            params["board_thickness"] = uniform(0.005, 0.015)
        if params.get("board_side_gap", None) is None:
            params["board_side_gap"] = uniform(0.03, 0.05)

        params["init_handle"] = uniform(-0.15, -0.25)
        params["curve_handle"] = (0, uniform(0.15, 0.35), uniform(-0.15, -0.35))
        params["curve_end_point"] = (0, uniform(0.35, 0.55), uniform(-0.05, 0.15))

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
        # Inject the pre-built materials captured in Phase 1
        obj_params["mat_hook_metal"] = MAT_HOOK_METAL
        obj_params["mat_board_plastic"] = MAT_BOARD_PLASTIC

        add_geomod(
            obj, hook_geometry_nodes, attributes=[], apply=True, input_kwargs=obj_params
        )

        return obj

# hook.py constructs shader_brushed_metal and shader_rough_plastic with no
# explicit args, so they both use their default argument sampling
# (metal_hsv / hsv+log_uniform). Call order matches hook_geometry_nodes:
# brushed_metal is the first SetMaterial node built, then rough_plastic.
seed_all(SEED)

MAT_HOOK_METAL = make_brushed_metal(name="HookBrushedMetal")
MAT_BOARD_PLASTIC = make_plastic_rough(name="HookBoardPlastic")

# No wear_tear: hook.py has no finalize_assets override.

def build(seed=SEED):
    fac = HookBaseFactory(seed)
    with FixedSeed(int_hash((fac.factory_seed, 0))):
        obj = fac.create_asset(i=0)
    obj.name = "HookBaseFactory"
    for i in range(len(obj.data.materials)):
        if obj.data.materials[i] is None:
            obj.data.materials[i] = MAT_BOARD_PLASTIC
    return obj

build(SEED)

