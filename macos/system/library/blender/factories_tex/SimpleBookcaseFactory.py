# [FL_INDEX: keywords="blender_factory, procedural_3d, SimpleBookcaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SimpleBookcaseFactory | Category: factories_tex
# Prompt: A 3D model of a compact bookcase rendered from a three-quarter perspective, featuring a rectangular enclosed box with two or three internal horizontal shelves, small visible mounting holes on the side panels, and a clean white appearance with an open front.

"""objects_blender_texture/shelves/SimpleBookcaseFactory.py

Texture-enabled conversion of the geometry-only
objects_blender/shelves/SimpleBookcaseFactory.py. Geometry is copied
verbatim from the source; materials are sampled in Phase 1 at module
level (raw SEED) to mirror `with FixedSeed(factory_seed)`
blocks, and passed through the geometry-nodes `SetMaterial` slots.

Material sources translated faithfully from:
                                                  -> make_grained_metal

The source factory simple_bookcase.py does NOT sample wear_tear, so this
textured script also skips wear_tear — there are no WEAR_DO_* gates.
"""


import os
import hashlib
import math
import random
import colorsys
from types import SimpleNamespace

import bpy
import numpy as np
from numpy.random import normal, randint, uniform

def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _mat_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _srgb_to_linear(c):
    if c < 0: return 0.0
    elif c < 0.04045: return c / 12.92
    else: return ((c + 0.055) / 1.055) ** 2.4

def _hex2rgba(hexval):
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0)

def _rgb2hsv(rgb):
    return colorsys.rgb_to_hsv(float(rgb[0]), float(rgb[1]), float(rgb[2]))

NATURAL_BASE_COLORS = [
    (0xC0C0C0, 1), (0x8C7853, 1), (0xBDBAAE, 1), (0xA9ACB6, 1), (0xB6AFA9, 1),
]

def _metal_natural_hsv():
    weights = np.array([w for _, w in NATURAL_BASE_COLORS], dtype=float)
    idx = int(np.random.choice(len(NATURAL_BASE_COLORS), p=weights / weights.sum()))
    hexval = NATURAL_BASE_COLORS[idx][0]
    h, s, v = _rgb2hsv(_hex2rgba(hexval)[:3])
    return (h + np.random.uniform(-0.1, 0.1),
            s + np.random.uniform(-0.1, 0.1),
            v * _mat_log_uniform(0.5, 0.2))

def metal_hsv():
    """py:metal_hsv with hex-based natural metals."""

    if np.random.uniform() < 0.2:
        return _metal_natural_hsv()
    return (float(np.random.uniform(0, 1)),
            float(np.random.uniform(0.3, 0.6)),
            _mat_log_uniform(0.02, 0.5))

def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
    """Set Principled BSDF inputs with Blender-version-tolerant socket names."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

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

# ----------------------------------------------------------------------------
# shader_shelves_white
#   and shader_shelves_white_sampler.
# ----------------------------------------------------------------------------
def make_shelves_white(name="ShelvesWhite") -> bpy.types.Material:
    # Sampler (mirrors shader_shelves_white_sampler)
    v = float(np.random.uniform(0.7, 1.0))
    rgb = (
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
    )
    roughness = float(np.random.uniform(0.7, 1.0))

    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    _set_principled(bsdf, Roughness=roughness)
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# shader_rough_plastic
# ----------------------------------------------------------------------------
def make_plastic_rough(name="PlasticRough", base_color=None) -> bpy.types.Material:
    if base_color is None:
        base_color = hsv2rgba((float(np.random.uniform(0, 1)),
                               float(np.random.uniform(0.5, 0.8)),
                               _mat_log_uniform(0.01, 0.5)))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

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

# ----------------------------------------------------------------------------
# make_brushed_metal — port of metal/brushed_metal.py.
# ----------------------------------------------------------------------------
def make_brushed_metal(name="BrushedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise2, "noise_dimensions"):
        try: noise2.noise_dimensions = "4D"
        except TypeError: pass
    noise2.inputs["Scale"].default_value = 100.0
    if "Detail" in noise2.inputs:    noise2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise2.inputs: noise2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise2.inputs:noise2.inputs["Distortion"].default_value = 0.1
    if "W" in noise2.inputs:         noise2.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(mapping_1.outputs["Vector"], noise2.inputs["Vector"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.4
    map_range.inputs[2].default_value = 0.6
    map_range.inputs[3].default_value = 0.8
    map_range.inputs[4].default_value = 1.2
    nt.links.new(_noise_fac_output(noise2), map_range.inputs[0])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    nt.links.new(map_range.outputs["Result"], hsv_node.inputs["Value"])

    map_range_r = nt.nodes.new("ShaderNodeMapRange")
    map_range_r.inputs[1].default_value = 0.4
    map_range_r.inputs[2].default_value = 0.6
    map_range_r.inputs[3].default_value = 0.2
    map_range_r.inputs[4].default_value = 0.3
    nt.links.new(_noise_fac_output(noise2), map_range_r.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(map_range_r.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# make_galvanized_metal — port of metal/galvanized_metal.py.
# ----------------------------------------------------------------------------
def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try: voronoi.voronoi_dimensions = "4D"
        except TypeError: voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "distance"):
        try: voronoi.distance = "MINKOWSKI"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 500.0
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[3].default_value = 0.1
    map_range.inputs[4].default_value = 0.5
    nt.links.new(voronoi.outputs[0], map_range.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# make_grained_metal — port of metal/grained_and_polished_metal.py.
# ----------------------------------------------------------------------------
def make_grained_metal(name="GrainedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

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
    mul3.inputs[1].default_value = 0.01
    nt.links.new(mul2.outputs[0], mul3.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# make_hammered_metal — port of metal/hammered_metal.py.
# ----------------------------------------------------------------------------
def make_hammered_metal(name="HammeredMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "feature"):
        try: voronoi.feature = "SMOOTH_F1"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 300.0
    if "Smoothness" in voronoi.inputs:
        voronoi.inputs["Smoothness"].default_value = 0.2
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

    pow_node = nt.nodes.new("ShaderNodeMath")
    pow_node.operation = "POWER"
    pow_node.inputs[1].default_value = 2.5
    dist_out = voronoi.outputs.get("Distance") or voronoi.outputs[0]
    nt.links.new(dist_out, pow_node.inputs[0])

    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = _mat_log_uniform(0.001, 0.003)
    nt.links.new(pow_node.outputs[0], mul.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv), "Roughness": 0.1},
    )
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# make_metal_basic — port of metal/metal_basic.py:shader_metal.
#   Noise-driven float curve roughness + Principled BSDF metal.
# ----------------------------------------------------------------------------
def make_metal_basic(name="MetalBasic", color_hsv=None) -> bpy.types.Material:
    if color_hsv is None:
        color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    fc = _build_float_curve(
        nt, _noise_fac_output(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0)),
           "Base Color": hsv2rgba(color_hsv)},
    )
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# get_shelf_material — local re-implementation of plywood.py:get_shelf_material.
#   For "white": np.random.choice([shader_shelves_white, shader_rough_plastic],
#                                 p=[0.6, 0.4])
#   For "metal": uniform choice across 5 metal shaders.
# Mirrors the call order / numpy.random consumption of the version.
# ----------------------------------------------------------------------------
_WHITE_CHOICES = (make_shelves_white, make_plastic_rough)
_WHITE_PROBS = (0.6, 0.4)

_METAL_CHOICES = (
    make_brushed_metal,
    make_galvanized_metal,
    make_grained_metal,
    make_hammered_metal,
    make_metal_basic,
)

def get_shelf_material(kind: str, name: str = None) -> bpy.types.Material:
    """Raw-bpy replica of plywood.get_shelf_material for 'white' / 'metal'."""

    if kind == "white":
        idx = int(np.random.choice(len(_WHITE_CHOICES), p=list(_WHITE_PROBS)))
        ctor = _WHITE_CHOICES[idx]
    elif kind == "metal":
        idx = int(np.random.choice(len(_METAL_CHOICES)))
        ctor = _METAL_CHOICES[idx]
    else:
        raise ValueError(f"Unsupported shelf material kind: {kind}")
    return ctor(name=name or kind.title())

# ── Basic helpers (copied verbatim from objects_blender/shelves boilerplate) ─

def int_hash(x, mod=(2**32 - 1)):
    m = hashlib.md5()
    for s in (x if isinstance(x, (tuple, list)) else [x]):
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % mod

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for blk in list(bpy.data.meshes):
        bpy.data.meshes.remove(blk)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    if o is not None:
        o.select_set(True)

# ── NodeWrangler (minimal) ─────────────────────────────────────────────────────

def ng_inputs(ng):
    return {s.name: s for s in ng.interface.items_tree if s.in_out == "INPUT"}

def ng_outputs(ng):
    return {s.name: s for s in ng.interface.items_tree if s.in_out == "OUTPUT"}

def _sock_type_for(v):
    if isinstance(v, bool): return "NodeSocketBool"
    if isinstance(v, int): return "NodeSocketInt"
    if isinstance(v, float): return "NodeSocketFloat"
    if isinstance(v, (tuple, list, np.ndarray)):
        n = len(v)
        if n == 3: return "NodeSocketVector"
        if n == 4: return "NodeSocketColor"
    if isinstance(v, bpy.types.Material):
        return "NodeSocketMaterial"
    return "NodeSocketFloat"

class NodeWrangler:
    def __init__(self, ng_or_mod):
        if isinstance(ng_or_mod, bpy.types.NodesModifier):
            self.modifier = ng_or_mod
            self.node_group = ng_or_mod.node_group
        else:
            self.modifier = None
            self.node_group = ng_or_mod
        self.nodes = self.node_group.nodes
        self.links = self.node_group.links

    def _group_io(self, bl_idname):
        for n in self.nodes:
            if n.bl_idname == bl_idname:
                return n
        return self.nodes.new(bl_idname)

    def expose_input(self, name, val=None, dtype=None):
        gi = self._group_io("NodeGroupInput")
        if name not in ng_inputs(self.node_group):
            sock_type = dtype if (isinstance(dtype, str) and dtype.startswith("NodeSocket")) else _sock_type_for(val)
            s = self.node_group.interface.new_socket(name=name, in_out="INPUT", socket_type=sock_type)
            if val is not None and hasattr(s, "default_value"):
                try:
                    s.default_value = val
                except Exception:
                    pass
        try:
            return gi.outputs[name]
        except Exception:
            idx = list(ng_inputs(self.node_group).keys()).index(name)
            return gi.outputs[idx]

    def _connect(self, sock, item):
        if isinstance(item, list):
            for sub in item:
                self._connect(sock, sub)
            return
        if isinstance(item, bpy.types.NodeSocket):
            try:
                self.links.new(item, sock)
            except Exception:
                pass
            return
        if hasattr(item, "outputs") and hasattr(item, "inputs"):
            out = None
            for s in item.outputs:
                if getattr(s, "enabled", True):
                    out = s
                    break
            if out is None and len(item.outputs):
                out = item.outputs[0]
            if out is not None:
                try:
                    self.links.new(out, sock)
                except Exception:
                    pass
            return
        try:
            sock.default_value = item
        except Exception:
            try:
                sock.default_value = tuple(item)
            except Exception:
                pass

    def _make_node(self, node_type):
        if isinstance(node_type, str) and node_type in bpy.data.node_groups:
            n = self.nodes.new("GeometryNodeGroup")
            n.node_tree = bpy.data.node_groups[node_type]
            return n
        return self.nodes.new(node_type)

    def new_node(self, node_type, input_args=None, attrs=None, input_kwargs=None,
                 label=None, expose_input=None, **_ignored):
        if expose_input:
            for spec in expose_input:
                if len(spec) == 3:
                    dtype, name, val = spec
                else:
                    dtype, name, val = None, spec[0], (spec[1] if len(spec) > 1 else None)
                self.expose_input(name, val=val, dtype=dtype)
        n = self._make_node(node_type)
        if label:
            n.label = label
        if attrs:
            for k, v in attrs.items():
                try:
                    setattr(n, k, v)
                except Exception:
                    try:
                        self._connect(n.inputs[k], v)
                    except Exception:
                        pass
        if input_args:
            for i, item in enumerate(input_args):
                if i < len(n.inputs):
                    self._connect(n.inputs[i], item)
        if input_kwargs:
            is_group_output = (n.bl_idname == "NodeGroupOutput")
            for k, item in input_kwargs.items():
                if is_group_output and isinstance(k, str) and k not in [s.name for s in n.inputs]:
                    if isinstance(item, bpy.types.NodeSocket):
                        st = getattr(item, "bl_idname", "NodeSocketFloat")
                    elif hasattr(item, "outputs") and len(getattr(item, "outputs", [])):
                        st = getattr(item.outputs[0], "bl_idname", "NodeSocketFloat")
                    else:
                        st = _sock_type_for(item)
                    st = {"NodeSocketFloatUnsigned": "NodeSocketFloat",
                          "NodeSocketVirtual": "NodeSocketFloat"}.get(st, st)
                    try:
                        self.node_group.interface.new_socket(name=k, in_out="OUTPUT", socket_type=st)
                    except Exception:
                        pass
                try:
                    sock = n.inputs[k]
                except Exception:
                    try:
                        idx = [s.name for s in n.inputs].index(k)
                        sock = n.inputs[idx]
                    except Exception:
                        continue
                self._connect(sock, item)
        return n

# ── to_nodegroup decorator + add_geomod ────────────────────────────────────────

def to_nodegroup(name=None, singleton=False, type="GeometryNodeTree"):
    def reg(fn):
        ng_name = name or fn.__name__
        def init(*args, **kwargs):
            if singleton and ng_name in bpy.data.node_groups:
                return bpy.data.node_groups[ng_name]
            ng = bpy.data.node_groups.new(ng_name, type)
            nw = NodeWrangler(ng)
            fn(nw, *args, **kwargs)
            return ng
        return init
    return reg

node_utils = SimpleNamespace(to_nodegroup=to_nodegroup)

def _ensure_geom_passthrough(ng):
    if "Geometry" not in ng_inputs(ng):
        try:
            s = ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
            try:
                ng.interface.move(s, 0)
            except Exception:
                pass
        except Exception:
            pass
    if "Geometry" not in ng_outputs(ng):
        try:
            ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        except Exception:
            pass
    for n in ng.nodes:
        if n.bl_idname == "NodeGroupOutput":
            n.is_active_output = True
    return ng

def add_geomod(obj, geo_func, name=None, apply=True, attributes=None, input_kwargs=None, **_ignored):
    fn_name = name or getattr(geo_func, "__name__", "GeometryNodes")
    mod = obj.modifiers.new(fn_name, "NODES")
    mod.node_group = bpy.data.node_groups.new(fn_name, "GeometryNodeTree")
    _ensure_geom_passthrough(mod.node_group)
    nw = NodeWrangler(mod)
    try:
        geo_func(nw, **(input_kwargs or {}))
    except Exception:
        pass
    _ensure_geom_passthrough(mod.node_group)
    if apply:
        _select_none()
        obj.select_set(True)
        _set_active(obj)
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception:
            pass
    return mod

surface = SimpleNamespace(add_geomod=add_geomod)

# ── Stubs: tagging / butil / AssetFactory ──────────────────────────────────────

tagging = SimpleNamespace(
    tag_system=SimpleNamespace(
        relabel_obj=lambda o: o,
        relabel_objects=lambda o: o,
    ),
    tag_object=lambda *a, **k: None,
    tag_nodegroup=lambda nw, geo, *a, **k: geo,
)
t = SimpleNamespace(
    shelf="shelf", cabinet="cabinet", door="door", drawer="drawer",
    Subpart=SimpleNamespace(SupportSurface="support_surface"),
)

def spawn_vert(name="vert"):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0)], [], [])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

butil = SimpleNamespace(spawn_vert=spawn_vert)

class AssetFactory:
    def __init__(self, factory_seed, coarse=False):
        self.factory_seed = int(factory_seed)
    def __call__(self, i=0, **kwargs):
        py_st, np_st = random.getstate(), np.random.get_state()
        random.seed(int_hash((self.factory_seed, i)))
        np.random.seed(int_hash((self.factory_seed, i)))
        try:
            try:
                return self.create_asset(i=i, **kwargs)
            except TypeError:
                return self.create_asset(**kwargs)
        finally:
            random.setstate(py_st)
            np.random.set_state(np_st)

def extract_nodegroup_geo(obj, *args, **kwargs):
    return [obj]

# ── Nodes class (from original factory) ───────────────────────────────────────
class Nodes:
    CombineXYZ = 'ShaderNodeCombineXYZ'
    Compare = 'FunctionNodeCompare'
    GroupInput = 'NodeGroupInput'
    GroupOutput = 'NodeGroupOutput'
    Index = 'GeometryNodeInputIndex'
    InputPosition = 'GeometryNodeInputPosition'
    JoinGeometry = 'GeometryNodeJoinGeometry'
    Math = 'ShaderNodeMath'
    MeshCube = 'GeometryNodeMeshCube'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    SetMaterial = 'GeometryNodeSetMaterial'
    SetPosition = 'GeometryNodeSetPosition'
    SubdivideMesh = 'GeometryNodeSubdivideMesh'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'

@node_utils.to_nodegroup("nodegroup_tagged_cube")
def nodegroup_tagged_cube(nw):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[("NodeSocketVector", "Size", (1.0, 1.0, 1.0))])
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": gi.outputs["Size"]})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Mesh": cube},
                attrs={"is_active_output": True})

# ── Factory-specific nodegroups + build ────────────────────────────────────────
@node_utils.to_nodegroup(
    "nodegroup_attach_gadget", singleton=False, type="GeometryNodeTree"
)
def nodegroup_attach_gadget(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "division_thickness", 0.5000),
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "attach_thickness", 0.5000),
            ("NodeSocketFloat", "attach_width", 0.5000),
            ("NodeSocketFloat", "attach_back_len", 0.5000),
            ("NodeSocketFloat", "attach_top_len", 0.5000),
            ("NodeSocketFloat", "depth", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["attach_width"], 1: 0.0000}
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["attach_top_len"], 1: 0.0000}
    )

    add_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["attach_thickness"], 1: 0.0000}
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add, "Y": add_1, "Z": add_2}
    )

    cube = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": combine_xyz,
            "Vertices X": 5,
            "Vertices Y": 5,
            "Vertices Z": 5,
        },
    )

    add_3 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["depth"], 1: 0.0000}
    )

    subtract = nw.new_node(
        Nodes.Math, input_kwargs={0: add_3, 1: add_1}, attrs={"operation": "SUBTRACT"}
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: subtract, 1: -0.5000},
        attrs={"operation": "MULTIPLY"},
    )

    subtract_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={
            0: group_input.outputs["height"],
            1: group_input.outputs["division_thickness"],
        },
        attrs={"operation": "SUBTRACT"},
    )

    combine_xyz_2 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": multiply, "Z": subtract_1}
    )

    transform = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_2}
    )

    add_4 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["attach_back_len"], 1: 0.0000}
    )

    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add, "Y": add_2, "Z": add_4}
    )

    cube_1 = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": combine_xyz_1,
            "Vertices X": 5,
            "Vertices Y": 5,
            "Vertices Z": 5,
        },
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_3, 1: -0.5000}, attrs={"operation": "MULTIPLY"}
    )

    multiply_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_4}, attrs={"operation": "MULTIPLY"}
    )

    subtract_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: subtract_1, 1: multiply_2},
        attrs={"operation": "SUBTRACT"},
    )

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": multiply_1, "Z": subtract_2}
    )

    transform_1 = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_3}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"attach1": transform, "attach2": transform_1},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_screw_head", singleton=False, type="GeometryNodeTree"
)
def nodegroup_screw_head(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "Depth", 0.0050),
            ("NodeSocketFloat", "Radius", 1.0000),
            ("NodeSocketFloat", "bottom_gap", 0.5000),
            ("NodeSocketFloat", "division_thickness", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "depth", 0.5000),
            ("NodeSocketFloat", "screw_gap", 0.5000),
        ],
    )

    cylinder = nw.new_node(
        "GeometryNodeMeshCylinder",
        input_kwargs={
            "Radius": group_input.outputs["Radius"],
            "Depth": group_input.outputs["Depth"],
        },
        attrs={"fill_type": "TRIANGLE_FAN"},
    )

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": cylinder.outputs["Mesh"],
            "Rotation": (0.0000, 1.5708, 0.0000),
        },
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["width"]},
        attrs={"operation": "MULTIPLY"},
    )

    multiply_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["depth"]},
        attrs={"operation": "MULTIPLY"},
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["screw_gap"], 1: 0.0000}
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_1, 1: add},
        attrs={"operation": "SUBTRACT"},
    )

    multiply_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["division_thickness"]},
        attrs={"operation": "MULTIPLY"},
    )

    subtract_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["height"], 1: multiply_2},
        attrs={"operation": "SUBTRACT"},
    )

    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply, "Y": subtract, "Z": subtract_1}
    )

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Translation": combine_xyz_1},
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: multiply_2, 1: group_input.outputs["bottom_gap"]}
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply, "Y": subtract, "Z": add_1}
    )

    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Translation": combine_xyz},
    )

    multiply_3 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: subtract, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_2 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply, "Y": multiply_3, "Z": subtract_1}
    )

    transform_3 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Translation": combine_xyz_2},
    )

    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: subtract_1, 1: add_1})

    multiply_4 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_2}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply, "Z": multiply_4}
    )

    transform_5 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Translation": combine_xyz_3},
    )

    combine_xyz_4 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply, "Y": multiply_3, "Z": add_1}
    )

    transform_6 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Translation": combine_xyz_4},
    )

    join_geometry_2 = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={
            "Geometry": [
                transform_2,
                transform_1,
                transform_3,
                transform_5,
                transform_6,
            ]
        },
    )

    transform_4 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": join_geometry_2, "Scale": (-1.0000, 1.0000, 1.0000)},
    )

    join_geometry_3 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_4, join_geometry_2]}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": join_geometry_3},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_back_board", singleton=False, type="GeometryNodeTree"
)
def nodegroup_back_board(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "width", 0.0000),
            ("NodeSocketFloat", "thickness", 0.5000),
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "depth", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: 0.0000}
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: 0.0000}
    )

    combine_xyz_4 = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={"X": group_input.outputs["width"], "Y": add, "Z": add_1},
    )

    cube_2 = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": combine_xyz_4,
            "Vertices X": 10,
            "Vertices Y": 10,
            "Vertices Z": 10,
        },
    )

    add_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["depth"], 1: 0.0000}
    )

    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: add, 1: -0.5000}, attrs={"operation": "MULTIPLY"}
    )

    multiply_add = nw.new_node(
        Nodes.Math,
        input_kwargs={0: add_2, 1: -0.5000, 2: multiply},
        attrs={"operation": "MULTIPLY_ADD"},
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_5 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": multiply_add, "Z": multiply_1}
    )

    transform_5 = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube_2, "Translation": combine_xyz_5}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_5},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_division_board", singleton=False, type="GeometryNodeTree"
)
def nodegroup_division_board(nw: NodeWrangler, tag_support=False):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "board_thickness", 0.0000),
            ("NodeSocketFloat", "depth", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
            ("NodeSocketFloat", "side_thickness", 0.5000),
        ],
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["side_thickness"], 1: 2.0000},
        attrs={"operation": "MULTIPLY"},
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["width"], 1: multiply},
        attrs={"operation": "SUBTRACT"},
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["depth"], 1: 0.0000}
    )

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={
            "X": subtract,
            "Y": add,
            "Z": group_input.outputs["board_thickness"],
        },
    )

    if tag_support:
        cube_1 = nw.new_node(
            nodegroup_tagged_cube().name, input_kwargs={"Size": combine_xyz_3}
        )
    else:
        cube_1 = nw.new_node(
            Nodes.MeshCube,
            input_kwargs={
                "Size": combine_xyz_3,
                "Vertices X": 10,
                "Vertices Y": 10,
                "Vertices Z": 10,
            },
        )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Mesh": cube_1},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_division_boards", singleton=False, type="GeometryNodeTree"
)
def nodegroup_division_boards(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "thickness", 0.5000),
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "gap", 0.5000),
            ("NodeSocketGeometry", "Geometry", None),
        ],
    )

    realize_instances_1 = nw.new_node(
        Nodes.RealizeInstances,
        input_kwargs={"Geometry": group_input.outputs["Geometry"]},
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["thickness"]},
        attrs={"operation": "MULTIPLY"},
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["gap"], 1: multiply}
    )

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": add})

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": realize_instances_1, "Translation": combine_xyz_1},
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["height"], 1: multiply},
        attrs={"operation": "SUBTRACT"},
    )

    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: subtract, 1: add})

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_1})

    transform_3 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": realize_instances_1, "Translation": combine_xyz_2},
    )

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": subtract})

    transform_4 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": realize_instances_1, "Translation": combine_xyz},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={
            "board1": transform_2,
            "board2": transform_3,
            "board3": transform_4,
        },
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_side_board", singleton=False, type="GeometryNodeTree"
)
def nodegroup_side_board(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "board_thickness", 0.5000),
            ("NodeSocketFloat", "depth", 0.5000),
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["board_thickness"], 1: 0.0000}
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["depth"], 1: 0.0000}
    )

    add_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: 0.0000}
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add, "Y": add_1, "Z": add_2}
    )

    cube = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": combine_xyz,
            "Vertices X": 10,
            "Vertices Y": 10,
            "Vertices Z": 10,
        },
    )

    add_3 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: 0.0000}
    )

    subtract = nw.new_node(
        Nodes.Math, input_kwargs={0: add_3, 1: add}, attrs={"operation": "SUBTRACT"}
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: subtract, 1: -0.5000},
        attrs={"operation": "MULTIPLY"},
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_2, 1: 0.5000}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply, "Z": multiply_1}
    )

    transform = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_1}
    )

    multiply_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: subtract, 1: 0.5000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_2 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply_2, "Z": multiply_1}
    )

    transform_1 = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_2}
    )

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [transform, transform_1]}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": join_geometry_1},
        attrs={"is_active_output": True},
    )

def geometry_nodes(nw: NodeWrangler, **kwargs):
    # Code generated using version 2.6.4 of the node_transpiler

    side_board_thickness = nw.new_node(Nodes.Value, label="side_board_thickness")
    side_board_thickness.outputs[0].default_value = kwargs["side_board_thickness"]

    shelf_depth = nw.new_node(Nodes.Value, label="shelf_depth")
    shelf_depth.outputs[0].default_value = kwargs["depth"]

    shelf_height = nw.new_node(Nodes.Value, label="shelf_height")
    shelf_height.outputs[0].default_value = kwargs["height"]

    shelf_width = nw.new_node(Nodes.Value, label="shelf_width")
    shelf_width.outputs[0].default_value = kwargs["width"]

    side_board = nw.new_node(
        nodegroup_side_board().name,
        input_kwargs={
            "board_thickness": side_board_thickness,
            "depth": shelf_depth,
            "height": shelf_height,
            "width": shelf_width,
        },
    )

    division_board_thickness = nw.new_node(
        Nodes.Value, label="division_board_thickness"
    )
    division_board_thickness.outputs[0].default_value = kwargs[
        "division_board_thickness"
    ]

    bottom_gap = nw.new_node(Nodes.Value, label="bottom_gap")
    bottom_gap.outputs[0].default_value = kwargs["bottom_gap"]

    division_board = nw.new_node(
        nodegroup_division_board(tag_support=kwargs["tag_support"]).name,
        input_kwargs={
            "board_thickness": division_board_thickness,
            "depth": shelf_depth,
            "width": shelf_width,
            "side_thickness": side_board_thickness,
        },
    )

    division_boards = nw.new_node(
        nodegroup_division_boards().name,
        input_kwargs={
            "thickness": division_board_thickness,
            "height": shelf_height,
            "gap": bottom_gap,
            "Geometry": division_board,
        },
    )

    backboard_thickness = nw.new_node(Nodes.Value, label="backboard_thickness")
    backboard_thickness.outputs[0].default_value = kwargs["backboard_thickness"]

    back_board = nw.new_node(
        nodegroup_back_board().name,
        input_kwargs={
            "width": shelf_width,
            "thickness": backboard_thickness,
            "height": shelf_height,
            "depth": shelf_depth,
        },
    )

    join_geometry = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={
            "Geometry": [
                side_board,
                division_boards.outputs["board1"],
                division_boards.outputs["board2"],
                back_board,
                division_boards.outputs["board3"],
            ]
        },
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry}
    )

    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": realize_instances,
            "Material": kwargs["frame_material"],
        },
    )

    screw_depth_head = nw.new_node(Nodes.Value, label="screw_depth_head")
    screw_depth_head.outputs[0].default_value = kwargs["screw_head_depth"]

    screw_head_radius = nw.new_node(Nodes.Value, label="screw_head_radius")
    screw_head_radius.outputs[0].default_value = kwargs["screw_head_radius"]

    screw_head_gap = nw.new_node(Nodes.Value, label="screw_head_gap")
    screw_head_gap.outputs[0].default_value = kwargs["screw_head_dist"]

    screw_head = nw.new_node(
        nodegroup_screw_head().name,
        input_kwargs={
            "Depth": screw_depth_head,
            "Radius": screw_head_radius,
            "bottom_gap": bottom_gap,
            "division_thickness": division_board_thickness,
            "width": shelf_width,
            "height": shelf_height,
            "depth": shelf_depth,
            "screw_gap": screw_head_gap,
        },
    )

    realize_instances_1 = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": screw_head}
    )

    set_material_1 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": realize_instances_1,
            "Material": kwargs["metal_material"],
        },
    )

    attach_thickness = nw.new_node(Nodes.Value, label="attach_thickness")
    attach_thickness.outputs[0].default_value = kwargs["attach_thickness"]

    attach_width = nw.new_node(Nodes.Value, label="attach_width")
    attach_width.outputs[0].default_value = kwargs["attach_width"]

    attach_back_length = nw.new_node(Nodes.Value, label="attach_back_length")
    attach_back_length.outputs[0].default_value = kwargs["attach_back_length"]

    attach_top_length = nw.new_node(Nodes.Value, label="attach_top_length")
    attach_top_length.outputs[0].default_value = kwargs["attach_top_length"]

    attach_gadget = nw.new_node(
        nodegroup_attach_gadget().name,
        input_kwargs={
            "division_thickness": division_board_thickness,
            "height": shelf_height,
            "attach_thickness": attach_thickness,
            "attach_width": attach_width,
            "attach_back_len": attach_back_length,
            "attach_top_len": attach_top_length,
            "depth": shelf_depth,
        },
    )

    join_geometry_2 = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={
            "Geometry": [
                attach_gadget.outputs["attach1"],
                attach_gadget.outputs["attach2"],
            ]
        },
    )

    realize_instances_2 = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_2}
    )

    set_material_2 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": realize_instances_2,
            "Material": kwargs["metal_material"],
        },
    )

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={"Geometry": [set_material, set_material_1, set_material_2]},
    )

    realize_instances_3 = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_1}
    )

    triangulate = nw.new_node(
        "GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances_3}
    )

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": triangulate, "Rotation": (0.0000, 0.0000, -1.5708)},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform},
        attrs={"is_active_output": True},
    )

class SimpleBookcaseBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(SimpleBookcaseBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = params

    def sample_params(self):
        return self.params.copy()

    def get_asset_params(self, i=0):
        params = self.sample_params()
        if params.get("depth", None) is None:
            params["depth"] = np.clip(normal(0.3, 0.05), 0.15, 0.45)
        if params.get("width", None) is None:
            params["width"] = np.clip(normal(0.5, 0.1), 0.25, 0.75)
        if params.get("height", None) is None:
            params["height"] = np.clip(normal(0.8, 0.1), 0.5, 1.0)
        params["side_board_thickness"] = uniform(0.005, 0.03)
        params["division_board_thickness"] = np.clip(normal(0.015, 0.005), 0.005, 0.025)
        params["bottom_gap"] = np.clip(normal(0.14, 0.05), 0.0, 0.2)
        params["backboard_thickness"] = uniform(0.01, 0.02)
        params["screw_head_depth"] = uniform(0.002, 0.008)
        params["screw_head_radius"] = uniform(0.003, 0.008)
        params["screw_head_dist"] = uniform(0.03, 0.1)
        params["attach_thickness"] = uniform(0.002, 0.005)
        params["attach_width"] = uniform(0.01, 0.04)
        params["attach_top_length"] = uniform(0.03, 0.1)
        params["attach_back_length"] = uniform(0.02, 0.05)
        # with FixedSeed(factory_seed) block — see spec).
        params["frame_material"] = MAT_FRAME
        params["metal_material"] = MAT_METAL
        params["tag_support"] = True
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
        surface.add_geomod(
            obj, geometry_nodes, apply=True, attributes=[], input_kwargs=obj_params
        )
        tagging.tag_system.relabel_obj(obj)

        return obj

class SimpleBookcaseFactory(SimpleBookcaseBaseFactory):
    def sample_params(self):
        params = dict()
        params["Dimensions"] = (
            uniform(0.25, 0.4),
            uniform(0.5, 0.7),
            uniform(0.7, 0.9),
        )
        params["depth"] = params["Dimensions"][0] - 0.015
        params["width"] = params["Dimensions"][1]
        params["height"] = params["Dimensions"][2]
        return params

#   Call order follows simple_bookcase.py get_asset_params():
#     1. frame_material = get_shelf_material("white")
#     2. metal_material = get_shelf_material("metal")
#   simple_bookcase does NOT sample wear_tear, so no gates here.
SEED = int(os.environ.get('SEED', 0))

# Scene cleanup
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)

seed_all(SEED)
MAT_FRAME = get_shelf_material("white", name="Frame")
MAT_METAL = get_shelf_material("metal", name="Metal")

def build(seed=SEED):
    seed = int(seed)
    derived = int_hash((seed, 0))
    random.seed(derived)
    np.random.seed(derived)
    fac = SimpleBookcaseFactory(seed)
    ph = None
    if hasattr(fac, 'create_placeholder'):
        try:
            ph = fac.create_placeholder(i=0)
        except Exception:
            try:
                ph = fac.create_placeholder()
            except Exception:
                pass
    if ph is None:
        try:
            ph = butil.spawn_vert()
        except Exception:
            ph = None
    result = None
    calls = []
    if ph is not None:
        calls += [dict(i=0, placeholder=ph, face_size=0.01), dict(i=0, placeholder=ph)]
    calls += [dict(i=0, face_size=0.01), dict(i=0), dict()]
    for kw in calls:
        try:
            result = fac.create_asset(**kw)
            break
        except TypeError:
            continue
    if result is None:
        result = fac.create_asset()
    if ph is not None and ph.name in bpy.data.objects:
        bpy.data.objects.remove(ph, do_unlink=True)
    if result is not None:
        fallback = MAT_FRAME if MAT_FRAME is not None else next((mat for mat in result.data.materials if mat is not None), None)
        if fallback is not None:
            for i in range(len(result.data.materials)):
                if result.data.materials[i] is None:
                    result.data.materials[i] = fallback
    return result

build(SEED)

