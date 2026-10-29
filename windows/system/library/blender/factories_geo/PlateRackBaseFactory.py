# [FL_INDEX: keywords="blender_factory, procedural_3d, PlateRackBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PlateRackBaseFactory | Category: factories_geo
# Prompt: A 3D model of a wooden plate rack rendered from a three-quarter perspective, featuring a rectangular base frame with horizontal crossbars and multiple vertical dowel pegs rising upward to hold plates in an upright position, with a dark wood-grain appearance.

# PlateRackBaseFactory — standalone Blender script (geometry + wood material).
# Dual-seed: SEED for material, int_hash((SEED,0)) for geometry. No wear_tear.
import os, math, random, colorsys, hashlib
import bpy
import numpy as np
from types import SimpleNamespace
from numpy.random import uniform, randint

C = bpy.context
D = bpy.data

# Blender 5.0 notes:
#   * ShaderNodeTexMusgrave is removed. The original shader chains several
#     MusgraveTexture nodes (fbm / hybrid_multifractal). We substitute
#     ShaderNodeTexNoise with tuned detail / dimension / distortion values so
#     the topology of the node tree — the map_range chains, the multi-mix
#     blend, the HSV tinting, the displacement output — is preserved
#     byte-for-byte. Shading response is visually equivalent grain.
#   * ShaderNodeMix uses inputs[0]=Factor, inputs[6]=A, inputs[7]=B,
#     outputs[2]=Result when data_type='RGBA'.
#   * Noise outputs[0] == 'Factor' (not 'Fac') — access by index for safety.
# ============================================================================


def seed_all(seed: int):
    np.random.seed(int(seed))
    random.seed(int(seed))


def _hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))


def _bark_hsv():
    _WOOD_COLORS_HEX = [
        0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170, 0x3D2B1F,
        0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43, 0x4E3828, 0x4E3828,
        0xC09A6B, 0x944536, 0x3F0110, 0x773C12, 0x6E4E37, 0x5C4033, 0x5C4033,
        0x3C3034, 0x96704C, 0x371B1A, 0x483B32, 0x43141A, 0x471713, 0xC3B090,
        0x6B4423, 0x674D46, 0x5D2E1A, 0x331C1F, 0x7A5640, 0xB99984, 0x71543D,
        0x8F4B28, 0x491A00, 0x836446, 0x7F461B, 0x6A3208, 0x724115, 0xA0522B,
        0x832A0C, 0x371B1A, 0xC7A373, 0x483B32, 0x635147, 0x664228, 0x5C5248,
    ]
    hexval = _WOOD_COLORS_HEX[np.random.randint(0, len(_WOOD_COLORS_HEX))]
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return colorsys.rgb_to_hsv(r, g, b)


def _get_wood_color():
    """Replica of materials/wood/wood.py:get_color."""

    h, s, v = _bark_hsv()
    return _hsv2rgba((
        h + float(np.random.uniform(-0.0, 0.05)),
        s + float(np.random.uniform(-0.3, 0.2)),
        v * _log_uniform(0.2, 20),
    ))


def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for n in names:
            if n in bsdf.inputs:
                bsdf.inputs[n].default_value = v
                break


def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]


def _build_float_curve(nt, value_socket, anchors):
    fc = nt.nodes.new("ShaderNodeFloatCurve")
    fc.mapping.use_clip = False
    curve = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
        curve.points[i].handle_type = "VECTOR"
    fc.mapping.update()
    nt.links.new(value_socket, fc.inputs["Value"])
    return fc


def _tex_noise(nt, scale=None, detail=None, distortion=None, dimension="3D", w=None):
    node = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(node, "noise_dimensions"):
        try:
            node.noise_dimensions = dimension
        except TypeError:
            pass
    if scale is not None and "Scale" in node.inputs:
        node.inputs["Scale"].default_value = float(scale)
    if detail is not None and "Detail" in node.inputs:
        node.inputs["Detail"].default_value = float(detail)
    if distortion is not None and "Distortion" in node.inputs:
        node.inputs["Distortion"].default_value = float(distortion)
    if w is not None and "W" in node.inputs:
        node.inputs["W"].default_value = float(w)
    return node


def _map_range(nt, src_socket, from_min=0.0, from_max=1.0, to_min=0.0, to_max=1.0):
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = float(from_min)
    mr.inputs[2].default_value = float(from_max)
    mr.inputs[3].default_value = float(to_min)
    mr.inputs[4].default_value = float(to_max)
    if src_socket is not None:
        nt.links.new(src_socket, mr.inputs[0])
    return mr


def _mix_rgba(nt, fac, a_socket, b_socket_or_color, blend_type="MIX"):
    mix = nt.nodes.new("ShaderNodeMix")
    try:
        mix.data_type = "RGBA"
    except Exception:
        pass
    if hasattr(mix, "blend_type"):
        try:
            mix.blend_type = blend_type
        except TypeError:
            pass
    # Factor
    if isinstance(fac, (int, float)):
        mix.inputs[0].default_value = float(fac)
    else:
        nt.links.new(fac, mix.inputs[0])
    # A (input index 6 for RGBA)
    if hasattr(a_socket, "default_value") or hasattr(a_socket, "node"):
        try:
            nt.links.new(a_socket, mix.inputs[6])
        except Exception:
            mix.inputs[6].default_value = a_socket
    else:
        mix.inputs[6].default_value = a_socket
    # B (input index 7 for RGBA)
    if isinstance(b_socket_or_color, (tuple, list)):
        mix.inputs[7].default_value = tuple(b_socket_or_color)
    else:
        try:
            nt.links.new(b_socket_or_color, mix.inputs[7])
        except Exception:
            mix.inputs[7].default_value = b_socket_or_color
    return mix


def make_wood(name="Wood", color=None, w=None) -> bpy.types.Material:
    """


    Preserves the original node topology 1:1:
      vec -> mapping_2 (scale 5,100,100) -> musgrave_2 -> map_range_2
      vec -> mapping_1 (default)         -> noise_1    -> musgrave_1 -> map_range -> map_range_1
      vec -> mapping   (scale .15,1,.15) -> noise      -> musgrave
      mix(noise, musgrave) -> mix_1(map_range_1, prev, MULTIPLY) ->
      mix_2(map_range_2, prev, MULTIPLY) -> HSV tint -> mix_3(HSV, color) -> BSDF
      mix_2 -> multiply by log_uniform(0.0002, 0.01) -> Displacement

    Blender 5.0 substitution: ShaderNodeTexMusgrave was removed; we use
    ShaderNodeTexNoise with the same scale/detail/distortion/dimension values.
    """

    if color is None:
        color = _get_wood_color()
    if w is None:
        w = float(np.random.uniform(0, 1))

    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    vec_out = tex_coord.outputs["Object"]

    # --- Stretched mapping for long-axis grain ---
    mapping_2 = nt.nodes.new("ShaderNodeMapping")
    mapping_2.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(vec_out, mapping_2.inputs["Vector"])

    # --- musgrave_texture_2 substitute (fbm-like stretched noise) ---
    musgrave_2 = _tex_noise(nt, scale=10.0, detail=15.0, distortion=0.0, dimension="4D", w=w)
    nt.links.new(mapping_2.outputs["Vector"], musgrave_2.inputs["Vector"])
    map_range_2 = _map_range(nt, _noise_fac_output(musgrave_2),
                             from_min=0.0, from_max=1.0, to_min=1.0, to_max=-1.0)

    # --- Default mapping for noise-driven musgrave_1 ---
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(vec_out, mapping_1.inputs["Vector"])

    noise_texture_1 = _tex_noise(nt, scale=0.5, detail=1.0, distortion=1.1, dimension="4D", w=w)
    nt.links.new(mapping_1.outputs["Vector"], noise_texture_1.inputs["Vector"])

    # musgrave_texture_1: Scale driven by noise_texture_1 Fac, hybrid_multifractal-ish
    musgrave_1 = _tex_noise(nt, detail=15.0, distortion=0.0, dimension="4D", w=w)
    nt.links.new(_noise_fac_output(noise_texture_1), musgrave_1.inputs["Scale"])

    map_range_mg1 = _map_range(nt, _noise_fac_output(musgrave_1),
                               from_min=0.0, from_max=1.0, to_min=-1.4, to_max=1.5)
    map_range_1 = _map_range(nt, map_range_mg1.outputs["Result"],
                             from_min=0.0, from_max=1.0, to_min=1.0, to_max=0.5)

    # --- Small-scale mapping for the third noise/musgrave pair ---
    mapping_small = nt.nodes.new("ShaderNodeMapping")
    mapping_small.inputs["Scale"].default_value = (0.15, 1.0, 0.15)
    nt.links.new(vec_out, mapping_small.inputs["Vector"])

    noise_texture = _tex_noise(nt, scale=5.0, detail=5.0, distortion=1.0, dimension="4D", w=w)
    nt.links.new(mapping_small.outputs["Vector"], noise_texture.inputs["Vector"])

    # musgrave_texture: Vector driven by noise_texture Fac
    musgrave_small = _tex_noise(nt, scale=4.0, detail=10.0, distortion=0.0, dimension="4D", w=w)
    nt.links.new(_noise_fac_output(noise_texture), musgrave_small.inputs["Vector"])

    # mix = Mix(fac=noise_texture.Fac, a=musgrave) [RGBA, default MIX]
    mix_noise = _mix_rgba(nt,
                          fac=_noise_fac_output(noise_texture),
                          a_socket=_noise_fac_output(musgrave_small),
                          b_socket_or_color=(0.0, 0.0, 0.0, 1.0),
                          blend_type="MIX")

    # mix_1 = MULTIPLY(fac=0.9, a=map_range_1.Result, b=mix.Result)
    mix_1 = _mix_rgba(nt,
                      fac=0.9,
                      a_socket=map_range_1.outputs["Result"],
                      b_socket_or_color=mix_noise.outputs[2],
                      blend_type="MULTIPLY")

    # mix_2 = MULTIPLY(fac=0.95, a=map_range_2.Result, b=mix_1.Result)
    mix_2 = _mix_rgba(nt,
                      fac=0.95,
                      a_socket=map_range_2.outputs["Result"],
                      b_socket_or_color=mix_1.outputs[2],
                      blend_type="MULTIPLY")

    # HSV tint node (Saturation 0.8, Value 0.2)
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    # mix_3 = Mix(fac=mix_2.Result, a=hsv_tinted, b=color)
    mix_3 = _mix_rgba(nt,
                      fac=mix_2.outputs[2],
                      a_socket=hsv_node.outputs["Color"],
                      b_socket_or_color=color,
                      blend_type="MIX")

    # Displacement chain: multiply mix_2 by log_uniform(0.0002, 0.01)
    mult_disp = nt.nodes.new("ShaderNodeMath")
    mult_disp.operation = "MULTIPLY"
    nt.links.new(mix_2.outputs[2], mult_disp.inputs[0])
    mult_disp.inputs[1].default_value = _log_uniform(0.0002, 0.01)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mult_disp.outputs[0], disp.inputs["Height"])

    # --- Roughness driven by NoiseTexture -> FloatCurve ---
    base_roughness = float(np.random.uniform(0.0, 0.4))
    roughness_noise = nt.nodes.new("ShaderNodeTexNoise")
    roughness_noise.inputs["Scale"].default_value = _log_uniform(40, 50)
    rough_curve = _build_float_curve(
        nt, _noise_fac_output(roughness_noise),
        [(0.0, base_roughness), (1.0, base_roughness + float(np.random.uniform(0.0, 0.8)))],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_3.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(rough_curve.outputs["Value"], bsdf.inputs["Roughness"])
    _set_principled(bsdf, **{"Coat Weight": float(np.clip(np.random.uniform(0, 1.4), 0, 1))})

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    nt.links.new(disp.outputs[0], out.inputs["Displacement"])
    return mat


# Phase 1: wood material on raw SEED; geometry on int_hash((SEED,0))
SEED = int(os.environ.get("SEED", "0"))
seed_all(SEED)
MAT_WOOD = make_wood(name="PlateRack_Wood")

# ---------------------------------------------------------------------------
# Geometry (shaderfunc_to_material override returns MAT_WOOD)
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
    return MAT_WOOD  # always returns the Phase-1 wood material

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
    JoinGeometry = 'GeometryNodeJoinGeometry'
    Math = 'ShaderNodeMath'
    MeshCube = 'GeometryNodeMeshCube'
    MeshLine = 'GeometryNodeMeshLine'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    SetMaterial = 'GeometryNodeSetMaterial'
    StoreNamedAttribute = 'GeometryNodeStoreNamedAttribute'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'

def shader_wood(nw=None, *args, **kwargs):
    return None

@node_utils.to_nodegroup(
    "nodegroup_plate_rack_connect", singleton=False, type="GeometryNodeTree"
)
def nodegroup_plate_rack_connect(nw: NodeWrangler):
    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "Radius", 1.0000),
            ("NodeSocketFloat", "Value1", 0.5000),
            ("NodeSocketFloat", "Value", 0.5000),
        ],
    )

    multiply_add = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["Value1"], 1: 2.0000, 2: -0.0020},
        attrs={"operation": "MULTIPLY_ADD"},
    )

    cylinder = nw.new_node(
        "GeometryNodeMeshCylinder",
        input_kwargs={"Radius": group_input.outputs["Radius"], "Depth": multiply_add},
    )

    store_named_attribute = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cylinder.outputs["Mesh"],
            "Name": "uv_map",
            3: cylinder.outputs["UV Map"],
        },
        attrs={"data_type": "FLOAT_VECTOR", "domain": "CORNER"},
    )

    multiply_add_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["Value"], 2: -uniform(0.02, 0.045)},
        attrs={"operation": "MULTIPLY_ADD"},
    )

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_add_1})

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": store_named_attribute,
            "Translation": combine_xyz,
            "Rotation": (1.5708, 0.0000, 0.0000),
        },
    )

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Scale": (-1.0000, 1.0000, 1.0000)},
    )

    join_geometry_2 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_2, transform]}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": join_geometry_2},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup("nodegroup_rack_cyn", singleton=False, type="GeometryNodeTree")
def nodegroup_rack_cyn(nw: NodeWrangler):
    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "Radius", 1.0000),
            ("NodeSocketFloat", "Value", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["Value"], 1: 0.0000}
    )

    cylinder = nw.new_node(
        "GeometryNodeMeshCylinder",
        input_kwargs={"Radius": group_input.outputs["Radius"], "Depth": add},
    )

    store_named_attribute = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cylinder.outputs["Mesh"],
            "Name": "uv_map",
            3: cylinder.outputs["UV Map"],
        },
        attrs={"data_type": "FLOAT_VECTOR", "domain": "CORNER"},
    )

    multiply_add = nw.new_node(
        Nodes.Math,
        input_kwargs={0: add, 2: 0.0010},
        attrs={"operation": "MULTIPLY_ADD"},
    )

    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_add})

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": store_named_attribute, "Translation": combine_xyz_4},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_2},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_rack_base", singleton=False, type="GeometryNodeTree"
)
def nodegroup_rack_base(nw: NodeWrangler):
    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketGeometry", "Instance", None),
            ("NodeSocketFloat", "Value1", 0.5000),
            ("NodeSocketFloat", "Value2", 0.5000),
            ("NodeSocketFloat", "Value3", 0.5000),
            ("NodeSocketInt", "Count", 10),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["Value1"], 1: 0.0000}
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["Value2"], 1: 0.0000}
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add, "Y": add_1, "Z": add_1}
    )

    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    store_named_attribute = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube.outputs["Mesh"],
            "Name": "uv_map",
            3: cube.outputs["UV Map"],
        },
        attrs={"data_type": "FLOAT_VECTOR", "domain": "CORNER"},
    )

    add_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["Value3"], 1: 0.0000}
    )

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_2})

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": store_named_attribute, "Translation": combine_xyz_1},
    )

    multiply_add = nw.new_node(
        Nodes.Math,
        input_kwargs={0: add, 2: -0.0150},
        attrs={"operation": "MULTIPLY_ADD"},
    )

    combine_xyz_2 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply_add, "Y": add_2}
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_add, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply, "Y": add_2}
    )

    mesh_line = nw.new_node(
        Nodes.MeshLine,
        input_kwargs={
            "Count": group_input.outputs["Count"],
            "Start Location": combine_xyz_2,
            "Offset": combine_xyz_3,
        },
        attrs={"mode": "END_POINTS"},
    )

    instance_on_points = nw.new_node(
        Nodes.InstanceOnPoints,
        input_kwargs={"Points": mesh_line, "Instance": group_input.outputs["Instance"]},
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": instance_on_points}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Base": transform, "Racks": realize_instances},
        attrs={"is_active_output": True},
    )

def rack_geometry_nodes(nw: NodeWrangler, **kwargs):
    rack_radius = nw.new_node(Nodes.Value, label="rack_radius")
    rack_radius.outputs[0].default_value = kwargs["rack_radius"]

    rack_height = nw.new_node(Nodes.Value, label="rack_height")
    rack_height.outputs[0].default_value = kwargs["rack_height"]

    rack_cyn = nw.new_node(
        nodegroup_rack_cyn().name,
        input_kwargs={"Radius": rack_radius, "Value": rack_height},
    )

    base_length = nw.new_node(Nodes.Value, label="base_length")
    base_length.outputs[0].default_value = kwargs["base_length"]

    base_width = nw.new_node(Nodes.Value, label="base_width")
    base_width.outputs[0].default_value = kwargs["base_width"]

    base_gap = nw.new_node(Nodes.Value, label="base_gap")
    base_gap.outputs[0].default_value = kwargs["base_gap"]

    integer = nw.new_node(Nodes.Integer)
    integer.integer = kwargs["num_rack"]

    rack_base = nw.new_node(
        nodegroup_rack_base().name,
        input_kwargs={
            "Instance": rack_cyn,
            "Value1": base_length,
            "Value2": base_width,
            "Value3": base_gap,
            "Count": integer,
        },
    )

    join_geometry = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={
            "Geometry": [rack_base.outputs["Base"], rack_base.outputs["Racks"]]
        },
    )

    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": join_geometry, "Scale": (1.0000, -1.0000, 1.0000)},
    )

    plate_rack_connect = nw.new_node(
        nodegroup_plate_rack_connect().name,
        input_kwargs={"Radius": rack_radius, "Value1": base_gap, "Value": base_length},
    )

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={"Geometry": [transform_1, join_geometry, plate_rack_connect]},
    )

    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: base_width}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply})

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": join_geometry_1, "Translation": combine_xyz},
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": transform}
    )

    triangulate = nw.new_node(
        "GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances}
    )

    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": triangulate,
            "Material": shaderfunc_to_material(shader_wood),
        },
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": set_material},
        attrs={"is_active_output": True},
    )

class PlateRackBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(PlateRackBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = params

    def sample_params(self):
        return self.params.copy()

    def get_place_points(self, params):
        xs = []
        for i in range(params["num_rack"] - 1):
            l = params["base_length"]
            d = (l - 0.03) / (params["num_rack"] - 1)
            x = -l / 2.0 + 0.015 + (i + 0.5) * d
            xs.append(x)

        y = 0
        z = params["base_width"]

        place_points = []
        for x in xs:
            place_points.append((x, y, z))

        return place_points

    def get_asset_params(self, i=0):
        params = self.sample_params()
        if params.get("num_rack", None) is None:
            params["num_rack"] = randint(3, 7)
        if params.get("rack_radius", None) is None:
            params["rack_radius"] = uniform(0.0025, 0.006)
        if params.get("rack_height", None) is None:
            params["rack_height"] = uniform(0.08, 0.15)
        if params.get("base_length", None) is None:
            params["base_length"] = (params["num_rack"] - 1) * uniform(
                0.03, 0.06
            ) + 0.03
        if params.get("base_gap", None) is None:
            params["base_gap"] = uniform(0.05, 0.08)
        if params.get("base_width", None) is None:
            params["base_width"] = uniform(0.015, 0.03)

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
            obj, rack_geometry_nodes, attributes=[], apply=True, input_kwargs=obj_params
        )

        place_points = self.get_place_points(obj_params)

        return obj, place_points

def build(seed=0):
    fac = PlateRackBaseFactory(seed)
    with FixedSeed(int_hash((fac.factory_seed, 0))):
        result = fac.create_asset(i=0)
    obj = result[0] if isinstance(result, tuple) else result
    obj.name = "PlateRackBaseFactory"
    # Ensure the wood material is actually bound to the mesh after geomod apply.
    # surface.shaderfunc_to_material returned MAT_WOOD, and the in-GeoNodes
    # SetMaterial should have assigned it; we defensively ensure it's slot 0
    # so texture renderers that check obj.data.materials see it.
    if obj is not None and obj.type == 'MESH':
        if len(obj.data.materials) == 0:
            obj.data.materials.append(MAT_WOOD)
        else:
            obj.data.materials[0] = MAT_WOOD
    return obj

obj = build(SEED)
