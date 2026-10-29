# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafFactory | Category: factories_geo
# Prompt: A 3D model of a narrow, elongated leaf rendered from a three-quarter perspective. The leaf features a slender blade with a pointed tip, a visible central midrib running along its length, smooth edges, and a slight natural curvature along the longitudinal axis giving it a subtle three-dimensional form.

import os
SEED = int(os.environ.get("SEED", "0"))
import bpy
import numpy as np
import random
import hashlib
from types import SimpleNamespace
from numpy.random import normal, uniform
from mathutils import Color

import random as _random, colorsys as _colorsys

def _seed_mat(seed):
    _s = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s); _random.seed(_s)

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
    """Leaf: season-dependent color variants with diffuse/glossy/translucent mix.
    Seasons: autumn (red/yellow/orange), spring/summer (saturated green), winter (desaturated brown/black)."""

    _seed_mat(seed)
    season = np.random.choice(['spring', 'summer', 'autumn', 'winter'], p=[0.25, 0.35, 0.25, 0.15])
    if season == 'autumn':
        base_hue = float(np.random.uniform(0.0, 0.20))
        sat = 0.85
        val = 0.9
        vein_val = 0.7
    elif season == 'winter':
        base_hue = float(np.random.uniform(0.0, 0.10))
        sat = float(np.random.uniform(0.2, 0.6))
        val = float(np.random.uniform(0.0, 0.1))
        vein_val = max(val - 0.05, 0.0)
    else:  # spring / summer
        base_hue = float(np.random.uniform(0.28, 0.32))
        sat = float(np.random.uniform(0.6, 0.7))
        val = float(np.random.uniform(0.1, 0.5))
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

CATEG_MAT = make_category_mat(SEED, "LeafFactory_Material")
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

def purge_empty_materials(obj):
    # shape-only conversion keeps this a no-op for stability
    return obj

butil = SimpleNamespace(
    apply_transform=apply_transform,
    purge_empty_materials=purge_empty_materials,
    select_none=_select_none,
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

# -- minimal tree mesh helpers used by leaf.py --
def _mesh_select_vtx_by_idx(obj, idx, deselect=False):
    if not isinstance(idx, list):
        idx = [idx]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    if deselect:
        bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    n = len(obj.data.vertices)
    for i in idx:
        obj.data.vertices[i % n].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    return idx

def _mesh_finalize_obj(obj):
    _select_none(); _set_active(obj)
    bpy.ops.object.convert(target='MESH')
    _select_none(); _set_active(obj)
    return obj

mesh = SimpleNamespace(select_vtx_by_idx=_mesh_select_vtx_by_idx, finalize_obj=_mesh_finalize_obj)

# -- minimal node_utils / NodeWrangler runtime --
def ng_inputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == 'INPUT'}

def ng_outputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == 'OUTPUT'}

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

def assign_curve(c, points, handles=None):
    for i, p in enumerate(points):
        if i < 2:
            c.points[i].location = p
        else:
            c.points.new(*p)
        if handles is not None:
            c.points[i].handle_type = handles[i]

def to_nodegroup(name=None, singleton=False, type='GeometryNodeTree'):
    def reg(fn):
        ng_name = name or fn.__name__
        if singleton:
            ng_name = ng_name + ' (no gc)'
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
    if isinstance(item, bpy.types.NodeSocket):
        return item
    if isinstance(item, tuple) and len(item) == 2 and hasattr(item[0], 'outputs'):
        node, sock = item
        return node.outputs[sock] if not isinstance(sock, int) else node.outputs[sock]
    if hasattr(item, 'outputs') and len(getattr(item, 'outputs', [])):
        # first enabled output if possible
        for s in item.outputs:
            if getattr(s, 'enabled', True):
                return s
        return item.outputs[0]
    return None

def _socket_type_for_output(out_socket):
    if out_socket is None:
        return 'NodeSocketFloat'
    t = getattr(out_socket, 'bl_idname', None)
    return t if isinstance(t, str) and t.startswith('NodeSocket') else 'NodeSocketFloat'

def _socket_type_for_val(val):
    if isinstance(val, bool):
        return 'NodeSocketBool'
    if isinstance(val, int):
        return 'NodeSocketInt'
    if isinstance(val, float):
        return 'NodeSocketFloat'
    if isinstance(val, (tuple, list, np.ndarray)):
        n = len(val)
        if n == 3:
            return 'NodeSocketVector'
        if n == 4:
            return 'NodeSocketColor'
    return 'NodeSocketFloat'

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
        return self.nodes.new(bl_idname)

    def _make_node(self, node_type):
        # custom node-group reference by name
        if isinstance(node_type, str) and node_type in bpy.data.node_groups and not node_type.startswith(('ShaderNode','GeometryNode','FunctionNode','CompositorNode','NodeGroup','NodeReroute')):
            n = self.nodes.new('GeometryNodeGroup' if self.node_group.bl_idname == 'GeometryNodeTree' else 'ShaderNodeGroup')
            n.node_tree = bpy.data.node_groups[node_type]
            return n
        if isinstance(node_type, str) and node_type in bpy.data.node_groups:
            # explicit nodegroup name may look arbitrary, prefer node group instance if not a registered node type
            try:
                n = self.nodes.new(node_type)
                return n
            except Exception:
                n = self.nodes.new('GeometryNodeGroup' if self.node_group.bl_idname == 'GeometryNodeTree' else 'ShaderNodeGroup')
                n.node_tree = bpy.data.node_groups[node_type]
                return n
        return self.nodes.new(node_type)

    def expose_input(self, name, val=None, attribute=None, dtype=None, use_namednode=False):
        gi = self._group_io('NodeGroupInput')
        if name not in ng_inputs(self.node_group):
            sock_type = dtype if isinstance(dtype, str) and dtype.startswith('NodeSocket') else _socket_type_for_val(val)
            iface_sock = self.node_group.interface.new_socket(name=name, in_out='INPUT', socket_type=sock_type)
            if val is not None and hasattr(iface_sock, 'default_value'):
                try:
                    iface_sock.default_value = val
                except Exception:
                    try:
                        iface_sock.default_value = tuple(val)
                    except Exception:
                        pass
            if self.modifier is not None and val is not None:
                try:
                    self.modifier[iface_sock.identifier] = val
                except Exception:
                    pass
        return gi.outputs[name]

    def connect_input(self, input_socket, input_item):
        if isinstance(input_item, list):
            for it in input_item:
                self.connect_input(input_socket, it)
            return
        out = _infer_output_socket(input_item)
        if out is not None:
            self.links.new(out, input_socket)
            return
        if hasattr(input_socket, 'default_value'):
            try:
                input_socket.default_value = input_item
            except Exception:
                if isinstance(input_item, np.ndarray):
                    input_socket.default_value = input_item.tolist()
                elif isinstance(input_item, (tuple, list)):
                    input_socket.default_value = tuple(input_item)
                else:
                    raise

    def new_node(self, node_type, input_args=None, attrs=None, input_kwargs=None, label=None, expose_input=None, compat_mode=True, strict=True):
        input_args = [] if input_args is None else list(input_args)
        input_kwargs = {} if input_kwargs is None else dict(input_kwargs)
        attrs = {} if attrs is None else dict(attrs)

        if node_type == getattr(Nodes, 'GroupInput', 'NodeGroupInput'):
            node = self._group_io('NodeGroupInput')
        elif node_type == getattr(Nodes, 'GroupOutput', 'NodeGroupOutput'):
            node = self._group_io('NodeGroupOutput')
            node.is_active_output = True
        else:
            node = self._make_node(node_type)

        if label is not None:
            node.label = label
            node.name = label

        if expose_input is not None:
            for dtype, name, val in expose_input:
                self.expose_input(name, val=val, dtype=dtype)

        for key, val in attrs.items():
            target = node
            if '.' in key:
                parts = key.split('.')
                for p in parts[:-1]:
                    target = getattr(target, p)
                setattr(target, parts[-1], val)
            else:
                setattr(target, key, val)

        items = list(enumerate(input_args)) + list(input_kwargs.items())
        for input_socket_name, input_item in items:
            if input_item is None:
                continue
            if node.bl_idname == 'NodeGroupOutput' and not isinstance(input_socket_name, int):
                if input_socket_name not in node.inputs:
                    out_sock = _infer_output_socket(input_item)
                    sock_type = _socket_type_for_output(out_sock) if out_sock is not None else _socket_type_for_val(input_item)
                    self.node_group.interface.new_socket(name=input_socket_name, in_out='OUTPUT', socket_type=sock_type)
            try:
                input_socket = node.inputs[input_socket_name]
            except Exception:
                input_socket = node.inputs[int(input_socket_name)]
            self.connect_input(input_socket, input_item)

        return node

class _SurfaceNS:
    def shaderfunc_to_material(self, shader_func, *args, name=None, **kwargs):
        name = name or shader_func.__name__
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
        mat.use_nodes = True
        if mat.node_tree is None:
            return mat
        for n in list(mat.node_tree.nodes):
            mat.node_tree.nodes.remove(n)
        nw = NodeWrangler(mat.node_tree)
        shader_func(nw, *args, **kwargs)
        return mat

    def add_material(self, objs, shader_func, *args, **kwargs):
        # shape-only: keep geometry and skip assigning material slots
        return None

    def add_geomod(self, objs, geo_func, name=None, apply=False, reuse=False, input_args=None, input_kwargs=None, attributes=None, show_viewport=True, selection=None, domains=None, input_attributes=None):
        if input_args is None:
            input_args = []
        if input_kwargs is None:
            input_kwargs = {}
        if attributes is None:
            attributes = []
        if not isinstance(objs, list):
            objs = [objs]
        if not objs:
            return None
        mod_last = None
        for obj in objs:
            mod = obj.modifiers.new(name=name or geo_func.__name__, type='NODES')
            if mod.node_group is None:
                mod.node_group = geometry_node_group_empty_new()
            mod.show_viewport = show_viewport
            nw = NodeWrangler(mod)
            geo_func(nw, *input_args, **input_kwargs)
            if attributes:
                try:
                    outs = [o for o in ng_outputs(mod.node_group).values() if getattr(o, 'socket_type', None) != 'NodeSocketGeometry']
                    for o, att_name in zip(outs, attributes):
                        if att_name:
                            mod[o.identifier + '_attribute_name'] = att_name
                except Exception:
                    pass
            mod_last = mod
            if apply:
                _select_none(); _set_active(obj)
                bpy.ops.object.modifier_apply(modifier=mod.name)
                _select_none()
        return mod_last

surface = _SurfaceNS()

class Nodes:
    pass

# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory of this source tree.

# Authors: Alejandro Newell, Yiming Zuo, Alexander Raistrick

C = bpy.context
D = bpy.data

class LeafFactory(AssetFactory):
    scale = 0.3

    def __init__(self, factory_seed, genome: dict = None, coarse=False):
        super(LeafFactory, self).__init__(factory_seed, coarse=coarse)
        self.genome = dict(
            leaf_width=0.5,
            alpha=0.3,
            use_wave=True,
            x_offset=0,
            flip_leaf=False,
            z_scaling=0,
            width_rand=0.33,
        )
        if genome:
            for k, g in genome.items():
                assert k in self.genome
                self.genome[k] = g

    def create_asset(self, **params) -> bpy.types.Object:
        # bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.mesh.primitive_circle_add(
            enter_editmode=False, align="WORLD", location=(0, 0, 0), scale=(1, 1, 1)
        )
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.edge_face_add()

        obj = bpy.context.active_object
        min_radius = 0.02
        radii_ref = [1]
        n = len(obj.data.vertices) // 2

        # define origin point
        mesh.select_vtx_by_idx(obj, [0, -1], deselect=True)
        bpy.ops.mesh.subdivide()

        a = np.linspace(0, np.pi, n)
        if self.genome["flip_leaf"]:
            a = a[::-1]
        x = (
            np.sin(a)
            * (
                self.genome["leaf_width"]
                + np.random.randn() * self.genome["width_rand"]
            )
            + self.genome["x_offset"]
        )
        y = -np.cos(0.9 * (a - self.genome["alpha"]))
        z = x**2 * self.genome["z_scaling"]

        full_coords = np.concatenate(
            [
                np.stack([x, y, z], 1),
                np.stack([-x[::-1], y[::-1], z], 1),
                np.array([[0, y[0], 0]]),
            ]
        ).flatten()
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.data.vertices.foreach_set("co", full_coords)

        if self.genome["use_wave"]:
            bpy.ops.object.modifier_add(type="WAVE")
            bpy.context.object.modifiers["Wave"].height = np.random.randn() * 0.3
            bpy.context.object.modifiers["Wave"].width = 0.75 + np.random.randn() * 0.1
            bpy.context.object.modifiers["Wave"].speed = np.random.rand()

        mesh.finalize_obj(obj)
        C.scene.cursor.location = obj.data.vertices[-1].co

        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

        obj.location = (0, 0, 0)
        obj.scale *= self.scale
        butil.apply_transform(obj)

        if obj is not None and len(obj.data.materials) == 0:
            obj.data.materials.append(CATEG_MAT)
        return obj

# SEED-deterministic: material via _seed_mat(SEED); geometry via FixedSeed(factory_seed) + FixedSeed(int_hash((seed,seed)))
def build(seed=0):
    fac = LeafFactory(seed)
    with FixedSeed(int_hash((seed, seed))):
        return fac.create_asset()

build(SEED)
