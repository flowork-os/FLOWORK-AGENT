# [FL_INDEX: keywords="blender_factory, procedural_3d, PlateBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PlateBaseFactory | Category: factories_geo
# Prompt: A 3D model of a round dinner plate rendered from a three-quarter perspective, featuring a flat circular disc shape with a slight thickness, smooth edges, and a uniform dark green surface coloring.

# PlateBaseFactory — standalone Blender script (geometry + rough_plastic material).
# Dual-seed: SEED for material, int_hash((SEED,0)) for geometry. No wear_tear.
import os, math, random, hashlib, colorsys
import bpy
import numpy as np
from types import SimpleNamespace
from numpy.random import uniform

C = bpy.context
D = bpy.data

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


def weighted_sample(reg):
    classes, w = zip(*reg)
    w = np.array(w, dtype=float)
    return classes[int(np.random.choice(len(classes), p=w / w.sum()))]


def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    """Set Principled BSDF inputs with 3.x/4.x/5.0 socket-name tolerance."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
    }
    for k, v in kw.items():
        for name in aliases.get(k, (k,)):
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break


def _noise_fac_output(noise_node):
    """Blender 5.0 renamed Fac → Factor on NoiseTexture; fall back to index 0."""

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


def make_plastic_rough(name="PlasticRough", base_color=None):
    """
    :shader_rough_plastic (and its nodegroup_plastics inner group).

      - TexCoord.Object → NoiseTexture 4D (Scale = 1.0 * 2000, Detail 15, Distortion 2, W = seed)
      - MapRange on sampled roughness ∈ U(0,1) → [0.05, 0.25] → Principled BSDF Roughness
      - noise.Fac × (roughness * 0.4) × 0.003 → Displacement height
      - Principled BSDF Base Color from hsv2rgba(hue, sat 0.5-0.8, val log-uniform 0.01-0.5)
    """

    if base_color is None:
        base_color = hsv2rgba((
            float(np.random.uniform(0, 1)),
            float(np.random.uniform(0.5, 0.8)),
            log_uniform(0.01, 0.5),
        ))

    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Noise — 4D for stable per-factory seed decorrelation
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try:
            noise.noise_dimensions = "4D"
        except TypeError:
            pass
    # scale = Scale_input (1.0) * 2000.0 from nodegroup_plastics
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = float(np.random.uniform(-1000.0, 1000.0))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    # roughness ∈ U(0,1) → MapRange to [0.05, 0.25]
    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[1].default_value = 0.0
    map_range.inputs[2].default_value = 1.0
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # Displacement chain: (map_range.Result * 0.4) * noise.Fac * 0.003
    mul_mapped_times_point4 = nt.nodes.new("ShaderNodeMath")
    mul_mapped_times_point4.operation = "MULTIPLY"
    mul_mapped_times_point4.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul_mapped_times_point4.inputs[0])

    mul_noise_times_mapped = nt.nodes.new("ShaderNodeMath")
    mul_noise_times_mapped.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul_noise_times_mapped.inputs[0])
    nt.links.new(mul_mapped_times_point4.outputs[0], mul_noise_times_mapped.inputs[1])

    mul_scale_point003 = nt.nodes.new("ShaderNodeMath")
    mul_scale_point003.operation = "MULTIPLY"
    mul_scale_point003.inputs[1].default_value = 0.003
    nt.links.new(mul_noise_times_mapped.outputs[0], mul_scale_point003.inputs[0])

    displacement = nt.nodes.new("ShaderNodeDisplacement")
    displacement.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_scale_point003.outputs[0], displacement.inputs["Height"])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])

    _connect_output(nt, bsdf, displacement=displacement.outputs[0])
    return mat


# Registry (single-entry, mirrors the hard-coded shader in plate_rack.py)
plate_surface_registry = [(make_plastic_rough, 1.0)]
REGISTRY = {"plate_surface": plate_surface_registry}


def get_material(key, name=None):
    ctor = weighted_sample(REGISTRY[key])
    return ctor(name=name or key.title())


# ---------------------------------------------------------------------------
# Geometry (shaderfunc_to_material returns MAT_PLATE from Phase 1)
# ---------------------------------------------------------------------------

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
    # Override of the geometry-only stub: return the real Phase-1 plastic_rough
    # material so the SetMaterial node in plate_geometry_nodes binds it directly.
    return MAT_PLATE

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
    GroupOutput = 'NodeGroupOutput'
    Math = 'ShaderNodeMath'
    SetMaterial = 'GeometryNodeSetMaterial'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'

def shader_rough_plastic(nw=None, *args, **kwargs):
    return None

def plate_geometry_nodes(nw, **kwargs):
    # Code generated using version 2.6.5 of the node_transpiler

    radius = nw.new_node(Nodes.Value, label="radius")
    radius.outputs[0].default_value = kwargs["radius"]

    thickness = nw.new_node(Nodes.Value, label="thickness")
    thickness.outputs[0].default_value = kwargs["thickness"]

    cylinder = nw.new_node(
        "GeometryNodeMeshCylinder",
        input_kwargs={"Vertices": 64, "Radius": radius, "Depth": thickness},
    )

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": radius})

    transform_geometry = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": cylinder.outputs["Mesh"],
            "Translation": combine_xyz,
            "Rotation": (0.0000, 1.5708, 0.0000),
        },
    )

    triangulate = nw.new_node(
        "GeometryNodeTriangulate", input_kwargs={"Mesh": transform_geometry}
    )

    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": triangulate,
            "Material": shaderfunc_to_material(shader_rough_plastic),
        },
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": set_material},
        attrs={"is_active_output": True},
    )

class PlateBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(PlateBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = params

    def sample_params(self):
        return self.params.copy()

    def get_asset_params(self, i=0):
        params = self.sample_params()
        if params.get("radius", None) is None:
            params["radius"] = uniform(0.15, 0.25)
        if params.get("thickness", None) is None:
            params["thickness"] = uniform(0.01, 0.025)

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
            obj,
            plate_geometry_nodes,
            attributes=[],
            apply=True,
            input_kwargs=obj_params,
        )

        # Ensure the slot binding survives modifier apply (SetMaterial inside
        # the geo-node tree is baked in; we re-assert on the object slot so
        # downstream renderers see MAT_PLATE in obj.data.materials[0]).
        if obj.data is not None:
            if len(obj.data.materials) == 0:
                obj.data.materials.append(MAT_PLATE)
            else:
                obj.data.materials[0] = MAT_PLATE

        return obj


# Phase 1: material on raw SEED; geometry on int_hash((SEED,0))
SEED = int(os.environ.get("SEED", "0"))
seed_all(SEED)
MAT_PLATE = get_material("plate_surface", "PlateSurface")


def build(seed=SEED):
    fac = PlateBaseFactory(seed)
    with FixedSeed(int_hash((fac.factory_seed, 0))):
        obj = fac.create_asset(i=0)
    obj.name = "PlateBaseFactory"
    return obj


obj = build(SEED)
