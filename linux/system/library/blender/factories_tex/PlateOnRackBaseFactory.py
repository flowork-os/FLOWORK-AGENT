# [FL_INDEX: keywords="blender_factory, procedural_3d, PlateOnRackBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PlateOnRackBaseFactory | Category: factories_tex
# Prompt: A 3D model of a round plate displayed on a wooden plate rack, rendered from a three-quarter perspective, featuring a large dark purple circular plate leaning upright against vertical wooden pegs that form a supporting stand.

"""Texture-enabled conversion of objects_blender/organizer/PlateOnRackBaseFactory.py.

Geometry is preserved verbatim from the source (GeoNodes pipeline via a small
inline NodeWrangler shim). Materials replace the stubbed
``shaderfunc_to_material`` with faithful raw-bpy ports of:
      (used for the rack base + rack rods + plate-rack connectors)
      (used for the plate on top of the rack)

Both shaders are wired into the existing Set Material nodes inside the
rack/plate GeoNodes trees via the ``shaderfunc_to_material`` dispatch, so
every part of the composite ends up with the correct shader *before* the
final object.join().

applies no wear_tear (scratches / edge_wear) to this asset -- therefore the
phase-1 wear_tear gates and apply_* helpers are intentionally omitted.
"""


import os
import math
import hashlib
import random
import colorsys
from types import SimpleNamespace

import bpy
import bmesh
import numpy as np
from numpy.random import uniform, randint

# ---            Inlined material library (raw-bpy shader ports)          ---

def seed_all(seed):
    np.random.seed(int(seed))
    random.seed(int(seed))

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

_WOOD_COLORS_HEX = [
    0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170, 0x3D2B1F,
    0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43, 0x4E3828, 0x4E3828,
    0xC09A6B, 0x944536, 0x3F0110, 0x773C12, 0x6E4E37, 0x5C4033, 0x5C4033,
    0x3C3034, 0x96704C, 0x371B1A, 0x483B32, 0x43141A, 0x471713, 0xC3B090,
    0x6B4423, 0x674D46, 0x5D2E1A, 0x331C1F, 0x7A5640, 0xB99984, 0x71543D,
    0x8F4B28, 0x491A00, 0x836446, 0x7F461B, 0x6A3208, 0x724115, 0xA0522B,
    0x832A0C, 0x371B1A, 0xC7A373, 0x483B32, 0x635147, 0x664228, 0x5C5248,
]

def _hex_to_rgb(hexval):
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (r, g, b)

def bark_hsv():
    hexval = _WOOD_COLORS_HEX[np.random.randint(0, len(_WOOD_COLORS_HEX))]
    r, g, b = _hex_to_rgb(hexval)
    return colorsys.rgb_to_hsv(r, g, b)

def wood_color():
    h, s, v = bark_hsv()
    return hsv2rgba((
        h + np.random.uniform(-0.0, 0.05),
        s + np.random.uniform(-0.3, 0.2),
        v * log_uniform(0.2, 20.0),
    ))

# --- low-level shader helpers (shared by make_wood / make_plastic_rough) ---
def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
    """Version-tolerant Principled BSDF input setter."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
    }
    for key, value in kw.items():
        for name in aliases.get(key, (key,)):
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = value
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

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

# --- shader_wood port -------------------------------------------------------
def make_wood(name="Wood"):

    """


    The original 2.6.4 transpiler output uses MusgraveTexture which was REMOVED
    in Blender 5.0. We substitute NoiseTexture (4D, matching the original noise
    dimension) with equivalent Scale/Detail/Distortion values, mirroring
    own substitution strategy in other porting passes. The full
    node topology (triple-mix procedural grain + anisotropic mapping + HSV
    tint + displacement + noise-driven roughness FloatCurve + Coat Weight)
    is preserved 1:1.
    """

    mat = _new_material(name)
    nt = mat.node_tree

    color = wood_color()
    w = float(np.random.uniform(0, 1))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    vec = tex_coord.outputs["Object"]

    # Mapping 2: strong anisotropic stretch in Y/Z for long grain
    mapping_2 = nt.nodes.new("ShaderNodeMapping")
    mapping_2.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(vec, mapping_2.inputs["Vector"])

    musgrave_2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(musgrave_2, "noise_dimensions"):
        try: musgrave_2.noise_dimensions = "4D"
        except TypeError: pass
    musgrave_2.inputs["Scale"].default_value = 10.0
    if "Detail" in musgrave_2.inputs:     musgrave_2.inputs["Detail"].default_value = 15.0
    if "Distortion" in musgrave_2.inputs: musgrave_2.inputs["Distortion"].default_value = 1.0
    if "W" in musgrave_2.inputs:          musgrave_2.inputs["W"].default_value = w
    nt.links.new(mapping_2.outputs["Vector"], musgrave_2.inputs["Vector"])

    map_range_2 = nt.nodes.new("ShaderNodeMapRange")
    map_range_2.inputs[3].default_value = 1.0
    map_range_2.inputs[4].default_value = -1.0
    nt.links.new(_noise_fac_output(musgrave_2), map_range_2.inputs[0])

    # Mapping 1: identity
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(vec, mapping_1.inputs["Vector"])

    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_1, "noise_dimensions"):
        try: noise_1.noise_dimensions = "4D"
        except TypeError: pass
    noise_1.inputs["Scale"].default_value = 0.5
    if "Detail" in noise_1.inputs:     noise_1.inputs["Detail"].default_value = 1.0
    if "Distortion" in noise_1.inputs: noise_1.inputs["Distortion"].default_value = 1.1
    if "W" in noise_1.inputs:          noise_1.inputs["W"].default_value = w
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])

    musgrave_1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(musgrave_1, "noise_dimensions"):
        try: musgrave_1.noise_dimensions = "4D"
        except TypeError: pass
    nt.links.new(_noise_fac_output(noise_1), musgrave_1.inputs["Scale"])
    if "Detail" in musgrave_1.inputs:     musgrave_1.inputs["Detail"].default_value = 15.0
    if "Distortion" in musgrave_1.inputs: musgrave_1.inputs["Distortion"].default_value = 2.4
    if "W" in musgrave_1.inputs:          musgrave_1.inputs["W"].default_value = w

    map_range_hi = nt.nodes.new("ShaderNodeMapRange")
    map_range_hi.inputs[3].default_value = -1.4
    map_range_hi.inputs[4].default_value = 1.5
    nt.links.new(_noise_fac_output(musgrave_1), map_range_hi.inputs[0])

    map_range_lo = nt.nodes.new("ShaderNodeMapRange")
    map_range_lo.inputs[3].default_value = 1.0
    map_range_lo.inputs[4].default_value = 0.5
    nt.links.new(map_range_hi.outputs["Result"], map_range_lo.inputs[0])

    # Mapping: fine grain
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (0.15, 1.0, 0.15)
    nt.links.new(vec, mapping.inputs["Vector"])

    noise_fine = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_fine, "noise_dimensions"):
        try: noise_fine.noise_dimensions = "4D"
        except TypeError: pass
    if "Detail" in noise_fine.inputs:     noise_fine.inputs["Detail"].default_value = 5.0
    if "Distortion" in noise_fine.inputs: noise_fine.inputs["Distortion"].default_value = 1.0
    if "W" in noise_fine.inputs:          noise_fine.inputs["W"].default_value = w
    nt.links.new(mapping.outputs["Vector"], noise_fine.inputs["Vector"])

    musgrave_fine = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(musgrave_fine, "noise_dimensions"):
        try: musgrave_fine.noise_dimensions = "4D"
        except TypeError: pass
    musgrave_fine.inputs["Scale"].default_value = 4.0
    if "Detail" in musgrave_fine.inputs:     musgrave_fine.inputs["Detail"].default_value = 10.0
    if "Distortion" in musgrave_fine.inputs: musgrave_fine.inputs["Distortion"].default_value = 0.0
    if "W" in musgrave_fine.inputs:          musgrave_fine.inputs["W"].default_value = w
    nt.links.new(_noise_fac_output(noise_fine), musgrave_fine.inputs["Vector"])

    # Mix A (RGBA): factor=noise_fine.Fac, A=noise_fine.Fac (as color), B=musgrave_fine
    mix_a = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_a, "data_type"):
        mix_a.data_type = "RGBA"
    nt.links.new(_noise_fac_output(noise_fine), mix_a.inputs[6])  # A color
    nt.links.new(_noise_fac_output(musgrave_fine), mix_a.inputs[7])  # B color

    # Mix 1 (RGBA Multiply, fac=0.9)
    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    mix_1.blend_type = "MULTIPLY"
    mix_1.inputs[0].default_value = 0.9
    nt.links.new(map_range_lo.outputs["Result"], mix_1.inputs[6])
    nt.links.new(mix_a.outputs[2], mix_1.inputs[7])

    # Mix 2 (RGBA Multiply, fac=0.95)
    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"):
        mix_2.data_type = "RGBA"
    mix_2.blend_type = "MULTIPLY"
    mix_2.inputs[0].default_value = 0.95
    nt.links.new(map_range_2.outputs["Result"], mix_2.inputs[6])
    nt.links.new(mix_1.outputs[2], mix_2.inputs[7])

    # HSV tint of base color (saturation=0.8, value=0.2)
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    # Mix 3 (RGBA) -- factor from mix_2 result; A=hsv tinted dark, B=base color
    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"):
        mix_3.data_type = "RGBA"
    nt.links.new(mix_2.outputs[2], mix_3.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix_3.inputs[6])
    mix_3.inputs[7].default_value = color

    # Displacement from mix_2 * tiny scalar
    mul_disp = nt.nodes.new("ShaderNodeMath")
    mul_disp.operation = "MULTIPLY"
    mul_disp.inputs[1].default_value = log_uniform(0.0002, 0.01)
    nt.links.new(mix_2.outputs[2], mul_disp.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])

    # Roughness: noise -> build_float_curve
    rough_noise = nt.nodes.new("ShaderNodeTexNoise")
    rough_noise.inputs["Scale"].default_value = log_uniform(40.0, 50.0)
    rough_low = float(np.random.uniform(0.0, 0.4))
    rough_high = rough_low + float(np.random.uniform(0.0, 0.8))
    rough_curve = _build_float_curve(
        nt, _noise_fac_output(rough_noise),
        [(0.0, rough_low), (1.0, rough_high)],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        **{"Coat Weight": float(np.clip(np.random.uniform(0, 1.4), 0, 1))},
    )
    nt.links.new(mix_3.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(rough_curve.outputs["Value"], bsdf.inputs["Roughness"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --- shader_rough_plastic port ----------------------------------------------
def make_plastic_rough(name="PlasticRough"):

    """


    Faithful 1:1 translation of the ``nodegroup_plastics`` internals:
        - TexCoord (Object) -> NoiseTexture 4D (scale = Scale * 2000)
        - roughness MapRange(0..1 -> 0.05..0.25) -> Principled BSDF Roughness
        - displacement: NoiseTexture.Fac * (roughness_mapped * 0.4) * 0.003
    Base color / roughness / seed sampled on the current numpy RNG state
    (mirroring the call site's ``if X is None: X = ...`` defaulting).
    """

    mat = _new_material(name)
    nt = mat.node_tree

    # Default sampling order mirrors shader_rough_plastic()
    roughness_input = float(np.random.uniform(0.0, 1.0))
    seed = float(np.random.uniform(-1000.0, 1000.0))
    base_color = hsv2rgba((
        np.random.uniform(0, 1),
        np.random.uniform(0.5, 0.8),
        log_uniform(0.01, 0.5),
    ))
    # shader_rough_plastic's top-level ``scale`` kw default = 1.0
    scale = 1.0

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try: noise.noise_dimensions = "4D"
        except TypeError: pass
    noise.inputs["Scale"].default_value = scale * 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = seed
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    # Roughness: MapRange(0.05 -> 0.25)
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # Displacement: noise.Fac * (roughness_mapped * 0.4) * 0.003
    mul_roughness_scale = nt.nodes.new("ShaderNodeMath")
    mul_roughness_scale.operation = "MULTIPLY"
    mul_roughness_scale.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul_roughness_scale.inputs[0])

    mul_noise = nt.nodes.new("ShaderNodeMath")
    mul_noise.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul_noise.inputs[0])
    nt.links.new(mul_roughness_scale.outputs[0], mul_noise.inputs[1])

    mul_final = nt.nodes.new("ShaderNodeMath")
    mul_final.operation = "MULTIPLY"
    mul_final.inputs[1].default_value = 0.003
    nt.links.new(mul_noise.outputs[0], mul_final.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_final.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ---                    Geometry (verbatim from source)                  ---

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

def _select_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    if o is not None: o.select_set(True)

def apply_transform(obj, loc=False, rot=True, scale=True):
    _select_none()
    _set_active(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)

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
    """Dispatch helper -- routes the two shader function references
    inside rack_geometry_nodes / plate_geometry_nodes to our raw-bpy ports.

    Returns a freshly-built Blender material so that each call inside a
    GeoNodes tree attaches a *distinct* material to the Set Material node (the
    rack gets wood, the plate gets plastic). Falls back to a blank material
    for any unexpected shader function.
    """

    shader_name = getattr(shader_func, '__name__', '')
    if shader_name == 'shader_wood':
        return make_wood(name or "PlateRack_Wood")
    if shader_name == 'shader_rough_plastic':
        return make_plastic_rough(name or "Plate_PlasticRough")
    # Fallback: blank material, surface missing. Should never hit this branch
    # for this factory -- logged for debugging only.
    mat_name = name or (shader_name or 'Material')
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
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
    JoinGeometry = 'GeometryNodeJoinGeometry'
    Math = 'ShaderNodeMath'
    MeshCube = 'GeometryNodeMeshCube'
    MeshLine = 'GeometryNodeMeshLine'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    SetMaterial = 'GeometryNodeSetMaterial'
    StoreNamedAttribute = 'GeometryNodeStoreNamedAttribute'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'

# --- shader function stubs used only as identifiers by the dispatcher above ---
def shader_wood(nw=None, *args, **kwargs):
    return None

def shader_rough_plastic(nw=None, *args, **kwargs):
    return None

@node_utils.to_nodegroup(
    "nodegroup_plate_rack_connect", singleton=False, type="GeometryNodeTree"
)
def nodegroup_plate_rack_connect(nw: NodeWrangler):
    # Code generated using version 2.6.5 of the node_transpiler

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
    # Code generated using version 2.6.5 of the node_transpiler

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
    # Code generated using version 2.6.5 of the node_transpiler

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
    # Code generated using version 2.6.5 of the node_transpiler

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
            "Material": shaderfunc_to_material(shader_wood, name="PlateRack_Wood"),
        },
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": set_material},
        attrs={"is_active_output": True},
    )

def plate_geometry_nodes(nw: NodeWrangler, **kwargs):
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
            "Material": shaderfunc_to_material(shader_rough_plastic, name="Plate_PlasticRough"),
        },
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": set_material},
        attrs={"is_active_output": True},
    )

class PlateRackBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params=None, coarse=False):
        super(PlateRackBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = {} if params is None else params

    def sample_params(self):
        return self.params.copy()

    def get_place_points(self, params):
        # compute the lowest point in the bezier curve
        xs = []
        for i in range(params["num_rack"] - 1):
            length = params["base_length"]
            step_dx = (length - 0.03) / (params["num_rack"] - 1)
            x = -length / 2.0 + 0.015 + (i + 0.5) * step_dx
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

class PlateBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params=None, coarse=False):
        super(PlateBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = {} if params is None else params

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

        return obj

class PlateOnRackBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params=None, coarse=False):
        super(PlateOnRackBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = {} if params is None else params

        self.rack_fac = PlateRackBaseFactory(factory_seed, params=self.params)
        self.plate_fac = PlateBaseFactory(factory_seed, params=self.params)

    def get_asset_params(self, i):
        if self.params.get("base_gap", None) is None:
            d = uniform(0.05, 0.08)
            self.rack_fac.params["base_gap"] = d
            self.plate_fac.params["radius"] = d + uniform(0.025, 0.06)

    def create_asset(self, i, **params):
        self.get_asset_params(i)
        rack, place_points = self.rack_fac.create_asset(i)
        plate = self.plate_fac.create_asset(i)

        plate.location = place_points[0]
        apply_transform(plate, loc=True)

        # Join rack + plate into a single mesh (matches geometry-only source).
        # Per-part materials are embedded inside each GeoNodes tree via
        # ``Set Material`` before this join -- the resulting joined mesh
        # keeps both slots (wood + plastic_rough).
        _select_none()
        for o in [rack, plate]:
            o.select_set(True)
        bpy.context.view_layer.objects.active = rack
        bpy.ops.object.join()
        return rack

# ---                  Phase 1 -- material sampling on SEED                ---
# ``shader_rough_plastic`` inside the GeoNodes builder functions (not via
# get_material_params / material_assignments registry), and its parent class
# does not override finalize_assets -- so there is no wear_tear sampling.
# Materials are built lazily inside ``rack_geometry_nodes`` /
# ``plate_geometry_nodes``, which the build() below invokes while the RNG
# state is deterministic under ``FixedSeed(int_hash((SEED, 0)))``. That
# same factory_seed when i=0 is the only instance rendered.
SEED = int(os.environ.get('SEED', 0))
seed_all(SEED)

def build(seed=SEED):
    fac = PlateOnRackBaseFactory(seed)
    with FixedSeed(int_hash((fac.factory_seed, 0))):
        result = fac.create_asset(i=0)
    obj = result if not isinstance(result, tuple) else result[0]
    obj.name = "PlateOnRackBaseFactory"
    fallback = next((mat for mat in obj.data.materials if mat is not None), None)
    if fallback is not None:
        for i in range(len(obj.data.materials)):
            if obj.data.materials[i] is None:
                obj.data.materials[i] = fallback
    return obj

obj = build(SEED)

