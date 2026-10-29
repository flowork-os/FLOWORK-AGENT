# [FL_INDEX: keywords="blender_factory, procedural_3d, CabinetDoorIkeaFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CabinetDoorIkeaFactory | Category: factories_tex
# Prompt: A 3D model of a sleek, tall IKEA-style cabinet door panel rendered from a three-quarter perspective, featuring a thin, dark-colored rectangular slab with a smooth flat surface and clean sharp edges.

"""CabinetDoorIkeaFactory (textured).

Texture-enabled rewrite of `objects_blender/shelves/CabinetDoorIkeaFactory.py`.
Geometry is copied verbatim from the source file; materials are assigned per
part (frame / board / metal attach gadgets) via hand-crafted raw-bpy shaders
translated faithfully from the material library.

``CabinetDoorIkeaFactory`` (inherits ``CabinetDoorBaseFactory`` defined in the
same file, NOT ``doors.py``). The Ikea variant samples a single
``frame_material`` uniformly from {"white", "black_wood", "wood", "glass",
"metal"} and sets ``board_material = [frame_material]``; both slots are then
resolved by ``plywood.get_shelf_material`` which in turn picks one of several
material shaders per bucket:

    white       -> 60% shader_shelves_white    , 40% shader_rough_plastic
    black_wood  -> 60% shader_shelves_black_wood, 40% shader_wood
    wood        -> 60% shader_shelves_wood     , 40% shader_wood
    glass       -> shader_glass
    metal       -> uniform over {brushed, galvanized, grained, hammered,
                                  metal_basic}

In addition, the geometry graph calls ``get_shelf_material("metal")`` for the
two hinge attach gadgets (regardless of ``frame_material``).

``CabinetDoorIkeaFactory.__init__`` does NOT sample materials — the sampling
happens inside ``get_asset_params`` which is itself called under
``FixedSeed(int_hash((factory_seed, i)))``. We therefore let the geometry
pipeline perform material sampling at build() time ('s
exact RNG consumption order) rather than lifting it into a Phase 1 block.

Neither ``CabinetDoorBaseFactory`` nor ``CabinetDoorIkeaFactory`` defines
``finalize_assets`` (no ``apply_scratches``/``apply_edge_wear`` calls), so
wear_tear is NOT applied — matching the source exactly.
"""


import colorsys
import hashlib
import math
import os
import random
from types import SimpleNamespace

import bpy
import numpy as np
from numpy.random import normal, randint, uniform

# ── Basic helpers ──────────────────────────────────────────────────────────────

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

# Sources translated faithfully from:
#                                                 shader_shelves_black_wood,
#                                                 shader_shelves_wood,
#                                                 get_shelf_material)

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

WOOD_COLORS = [
    0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170,
    0x3D2B1F, 0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43,
    0x4E3828, 0x4E3828, 0xC09A6B, 0x944536, 0x3F0110, 0x773C12,
    0x6E4E37, 0x5C4033, 0x5C4033, 0x3C3034, 0x96704C, 0x371B1A,
    0x483B32, 0x43141A, 0x471713, 0xC3B090, 0x6B4423, 0x674D46,
    0x5D2E1A, 0x331C1F, 0x7A5640, 0xB99984, 0x71543D, 0x8F4B28,
    0x491A00, 0x836446, 0x7F461B, 0x6A3208, 0x724115, 0xA0522B,
    0x832A0C, 0x371B1A, 0xC7A373, 0x483B32, 0x635147, 0x664228,
    0x5C5248,
]

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
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            _mat_log_uniform(0.02, 0.5))

def bark_hsv():
    """py:bark_hsv with sRGB-to-linear + full palette."""

    hexval = WOOD_COLORS[np.random.randint(0, len(WOOD_COLORS))]
    return _rgb2hsv(_hex2rgba(hexval)[:3])

def _new_material(name):
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
    for key, value in kw.items():
        names = aliases.get(key, (key,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = value
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
# Shelves-specific shaders (plywood.py)
# ----------------------------------------------------------------------------
def _shelves_wood_body(nt, wave_scale, z_axis_texture):
    """Shared trunk for shader_shelves_black_wood / shader_shelves_wood.
    Returns (base_color_fac, disp_fac) — the factor sockets feeding the
    final BaseColor ramp and the Displacement mix, respectively.
    Matches plywood.py lines 75-165 / 249-361 verbatim except MusgraveTexture
    (removed in 5.0) is replaced by a stretched NoiseTexture."""

    tex_coord_1 = nt.nodes.new("ShaderNodeTexCoord")
    if z_axis_texture:
        wave_vec = (wave_scale, wave_scale, 0.1)
        map1_scale = (0.1, 0.1, 2.0)
    else:
        wave_vec = (wave_scale, 0.1, 0.1)
        map1_scale = (0.1, 2.0, 2.0)

    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = map1_scale
    nt.links.new(tex_coord_1.outputs["Object"], mapping_1.inputs["Vector"])

    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise_1.inputs:     noise_1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise_1.inputs: noise_1.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = 40.0
    nt.links.new(_noise_fac_output(noise_1), voronoi.inputs["Vector"])

    colorramp_1 = nt.nodes.new("ShaderNodeValToRGB")
    cr1_in = colorramp_1.inputs.get("Fac") or colorramp_1.inputs[0]
    vor_col = voronoi.outputs.get("Color") or voronoi.outputs[0]
    nt.links.new(vor_col, cr1_in)
    colorramp_1.color_ramp.elements[0].position = 0.0864
    colorramp_1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = 0.1091
    colorramp_1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = wave_vec
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # Musgrave substitute — stretched NoiseTexture (Musgrave removed in 5.0)
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave.inputs: musgrave.inputs["Detail"].default_value = 3.0
    nt.links.new(_noise_fac_output(noise), musgrave.inputs["Vector"])

    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"): mix_1.data_type = "RGBA"
    nt.links.new(_noise_fac_output(musgrave), mix_1.inputs[6])
    noise_col = noise.outputs.get("Color") or noise.outputs[0]
    nt.links.new(noise_col, mix_1.inputs[7])

    colorramp_2 = nt.nodes.new("ShaderNodeValToRGB")
    cr2_in = colorramp_2.inputs.get("Fac") or colorramp_2.inputs[0]
    nt.links.new(mix_1.outputs[2], cr2_in)
    colorramp_2.color_ramp.elements[0].position = 0.0818
    colorramp_2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_2.color_ramp.elements[1].position = 0.85
    colorramp_2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"): mix_2.data_type = "RGBA"
    mix_2.inputs[0].default_value = 0.6
    nt.links.new(colorramp_1.outputs["Color"], mix_2.inputs[6])
    nt.links.new(colorramp_2.outputs["Color"], mix_2.inputs[7])

    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"): mix_3.data_type = "RGBA"
    mix_3.inputs[0].default_value = 0.004
    nt.links.new(colorramp_1.outputs["Color"], mix_3.inputs[6])
    nt.links.new(colorramp_2.outputs["Color"], mix_3.inputs[7])

    return mix_2.outputs[2], mix_3.outputs[2]

def make_shelves_white(name="ShelvesWhite"):
    v = float(np.random.uniform(0.7, 1.0))
    rgb = (
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
        1.0,
    )
    roughness = float(np.random.uniform(0.7, 1.0))

    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    bsdf.inputs["Base Color"].default_value = rgb
    _connect_output(nt, bsdf)
    return mat

def make_shelves_black_wood(name="ShelvesBlackWood", z_axis_texture=False):
    wave_scale = float(np.random.uniform(1.0, 3.0))
    dark_scale = float(np.random.uniform(0.0, 0.01))
    gray_scale = float(np.random.uniform(0.01, 0.03))
    rgb = (float(np.random.uniform(0.015, 0.035)),
           float(np.random.uniform(0.0, 0.01)),
           float(np.random.uniform(0.0, 0.01)))
    roughness = float(np.random.uniform(0.75, 1.0))

    mat = _new_material(name)
    nt = mat.node_tree
    base_fac, disp_fac = _shelves_wood_body(nt, wave_scale, z_axis_texture)

    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    cr_in = cr_base.inputs.get("Fac") or cr_base.inputs[0]
    nt.links.new(base_fac, cr_in)
    elements = cr_base.color_ramp.elements
    elements[0].position = 0.15
    elements[0].color = (dark_scale, dark_scale, dark_scale, 1.0)
    e_mid = elements.new(0.5)
    e_mid.color = (gray_scale, gray_scale, gray_scale, 1.0)
    elements[-1].position = 1.0
    elements[-1].color = (rgb[0], rgb[1], rgb[2], 1.0)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(disp_fac, disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    nt.links.new(cr_base.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_shelves_wood(name="ShelvesWood", z_axis_texture=False):
    bright_hsv = (float(np.random.uniform(0.03, 0.09)),
                  float(np.random.uniform(0.5, 0.7)),
                  float(np.random.uniform(0.7, 1.0)))
    mid_hsv = (float(np.random.uniform(0.02, 0.06)),
               float(np.random.uniform(0.6, 1.0)),
               float(np.random.uniform(0.3, 0.6)))
    dark_hsv = (float(np.random.uniform(0.03, 0.05)),
                float(np.random.uniform(0.6, 1.0)),
                float(np.random.uniform(0.1, 0.3)))
    wave_scale = float(np.random.uniform(1.0, 3.0))
    roughness = float(np.random.uniform(0.75, 1.0))

    mat = _new_material(name)
    nt = mat.node_tree
    base_fac, disp_fac = _shelves_wood_body(nt, wave_scale, z_axis_texture)

    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    cr_in = cr_base.inputs.get("Fac") or cr_base.inputs[0]
    nt.links.new(base_fac, cr_in)
    elements = cr_base.color_ramp.elements
    elements[0].position = 0.02
    elements[0].color = hsv2rgba(dark_hsv)
    e_mid = elements.new(0.11)
    e_mid.color = hsv2rgba(mid_hsv)
    elements[-1].position = 0.8
    elements[-1].color = hsv2rgba(bright_hsv)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(disp_fac, disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    nt.links.new(cr_base.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# Wood (bark-color variant, from materials/wood/wood.py)
# ----------------------------------------------------------------------------
def make_wood(name="Wood", color=None):
    if color is None:
        h, s, v = bark_hsv()
        color = hsv2rgba((h + float(np.random.uniform(-0.0, 0.05)),
                          max(0.0, s + float(np.random.uniform(-0.3, 0.2))),
                          v * _mat_log_uniform(0.2, 20)))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 10.0
    if "Detail" in grain.inputs:     grain.inputs["Detail"].default_value = 15.0
    if "Distortion" in grain.inputs: grain.inputs["Distortion"].default_value = 0.5
    nt.links.new(mapping.outputs["Vector"], grain.inputs["Vector"])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    nt.links.new(_noise_fac_output(grain), mix.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = color

    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = _mat_log_uniform(40, 50)
    base_rough = float(np.random.uniform(0.0, 0.4))
    fc = _build_float_curve(nt, _noise_fac_output(noise_r),
                            [(0, base_rough),
                             (1, base_rough + float(np.random.uniform(0.0, 0.8)))])

    mul_disp = nt.nodes.new("ShaderNodeMath")
    mul_disp.operation = "MULTIPLY"
    mul_disp.inputs[1].default_value = _mat_log_uniform(0.0002, 0.01)
    nt.links.new(_noise_fac_output(grain), mul_disp.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    **{"Coat Weight": float(np.clip(np.random.uniform(0, 1.4), 0, 1))})
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# Rough plastic (materials/plastic/plastic_rough.py)
# ----------------------------------------------------------------------------
def make_plastic_rough(name="PlasticRough", base_color=None):
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
# Metal family (materials/metal/*.py)
# ----------------------------------------------------------------------------
def make_metal_basic(name="MetalBasic", color_hsv=None):
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    fc = _build_float_curve(
        nt,
        _noise_fac_output(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0))})
    bsdf.inputs["Base Color"].default_value = hsv2rgba(color_hsv or metal_hsv())
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_brushed_metal(name="BrushedMetal", base_color_hsv=None):
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
    if "Distortion" in noise2.inputs: noise2.inputs["Distortion"].default_value = 0.1
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

def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None):
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
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": 0.0,
                       "Base Color": hsv2rgba(base_color_hsv)})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_grained_metal(name="GrainedMetal", base_color_hsv=None):
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
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": 0.0,
                       "Base Color": hsv2rgba(base_color_hsv)})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_hammered_metal(name="HammeredMetal", base_color_hsv=None):
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
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": 0.0,
                       "Base Color": hsv2rgba(base_color_hsv),
                       "Roughness": 0.1})
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# Glass (materials/ceramic/glass.py)
# ----------------------------------------------------------------------------
def make_glass(name="Glass"):
    mat = _new_material(name)
    nt = mat.node_tree
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    if "Roughness" in glass.inputs:
        glass.inputs["Roughness"].default_value = 0.02
    if "IOR" in glass.inputs:
        glass.inputs["IOR"].default_value = 1.5
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0
        if "Transmission Weight" in glass.inputs:
            glass.inputs["Transmission Weight"].default_value = 1.0
        elif "Transmission" in glass.inputs:
            glass.inputs["Transmission"].default_value = 1.0
    # Replicate plywood.get_shelf_material -> shader_glass -> get_glass_color(clear=False).
    if np.random.uniform() < 0.5:
        color = (1.0, 1.0, 1.0, 1.0)
    else:
        color = hsv2rgba((float(np.random.uniform(0, 1)),
                          float(np.random.uniform(0.05, 0.25)),
                          1.0))
    if "Color" in glass.inputs:
        glass.inputs["Base Color"].default_value = color
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(glass.outputs[0], out.inputs["Surface"])
    return mat

# ----------------------------------------------------------------------------
# Dispatch — replicates plywood.get_shelf_material(name)
# RNG consumption per bucket must match the source order: one
# np.random.choice() for the inner shader pick (except glass which consumes
# none, and metal which consumes one uniform 5-way choice).
# ----------------------------------------------------------------------------
def get_shelf_material(name, slot_name=None, **kwargs):
    slot_name = slot_name or str(name).title()
    if name == "white":
        if int(np.random.choice(2, p=[0.6, 0.4])) == 0:
            return make_shelves_white(name=slot_name)
        return make_plastic_rough(name=slot_name)
    if name == "black_wood":
        if int(np.random.choice(2, p=[0.6, 0.4])) == 0:
            return make_shelves_black_wood(name=slot_name)
        return make_wood(name=slot_name)
    if name == "wood":
        if int(np.random.choice(2, p=[0.6, 0.4])) == 0:
            return make_shelves_wood(name=slot_name)
        return make_wood(name=slot_name)
    if name == "glass":
        return make_glass(name=slot_name)
    if name == "metal":
        metal_ctors = [make_brushed_metal, make_galvanized_metal,
                       make_grained_metal, make_hammered_metal, make_metal_basic]
        ctor = metal_ctors[int(np.random.choice(5))]
        return ctor(name=slot_name)
    # Fallback path matches plywood.get_shelf_material's default case.
    ctors = [make_shelves_white, make_plastic_rough,
             make_shelves_black_wood, make_wood, make_shelves_wood]
    ctor = ctors[int(np.random.choice(5, p=[0.3, 0.2, 0.3, 0.1, 0.1]))]
    return ctor(name=slot_name)

# Shader function aliases (kept around so any other geometry nodegroups that
# reference the bare shader names by identity can still import them; in the
# current factory only ``get_shelf_material`` is invoked).
shader_shelves_white = make_shelves_white
shader_shelves_black_wood = make_shelves_black_wood
shader_shelves_wood = make_shelves_wood
shader_shelves_black_wood_z = lambda *a, **k: make_shelves_black_wood(*a, z_axis_texture=True, **k)
shader_shelves_wood_z = lambda *a, **k: make_shelves_wood(*a, z_axis_texture=True, **k)
shader_glass = make_glass
# Geometry graphs below never actually call these — they call get_shelf_material
# or reference the materials that were pre-resolved in get_asset_params.
shader_shelves_black_metallic = make_metal_basic
shader_shelves_white_metallic = make_metal_basic
shader_marble = make_shelves_white

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
    BooleanMath = 'FunctionNodeBooleanMath'
    BoundingBox = 'GeometryNodeBoundBox'
    CombineXYZ = 'ShaderNodeCombineXYZ'
    Compare = 'FunctionNodeCompare'
    ConvexHull = 'GeometryNodeConvexHull'
    CurveCircle = 'GeometryNodeCurvePrimitiveCircle'
    CurveLine = 'GeometryNodeCurvePrimitiveLine'
    CurveToMesh = 'GeometryNodeCurveToMesh'
    EndpointSelection = 'GeometryNodeCurveEndpointSelection'
    FlipFaces = 'GeometryNodeFlipFaces'
    GroupInput = 'NodeGroupInput'
    GroupOutput = 'NodeGroupOutput'
    Index = 'GeometryNodeInputIndex'
    InputPosition = 'GeometryNodeInputPosition'
    JoinGeometry = 'GeometryNodeJoinGeometry'
    Math = 'ShaderNodeMath'
    MergeByDistance = 'GeometryNodeMergeByDistance'
    MeshCube = 'GeometryNodeMeshCube'
    ObjectInfo = 'GeometryNodeObjectInfo'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    SeparateXYZ = 'ShaderNodeSeparateXYZ'
    SetMaterial = 'GeometryNodeSetMaterial'
    SetPosition = 'GeometryNodeSetPosition'
    SubdivideMesh = 'GeometryNodeSubdivideMesh'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'
    Vector = 'FunctionNodeInputVector'
    VectorMath = 'ShaderNodeVectorMath'

# ── Factory-specific nodegroups + build ────────────────────────────────────────

# - Beining Han: primary author
# - Abhishek Joshi: Updates for sim
# - Max Gonzalez Saez-Diez: Updates for sim

import bpy
import numpy as np
from numpy.random import uniform

@node_utils.to_nodegroup(
    "nodegroup_node_group", singleton=False, type="GeometryNodeTree"
)
def nodegroup_node_group(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": (0.0120, 0.00060, 0.0400)})

    cylinder = nw.new_node(
        "GeometryNodeMeshCylinder",
        input_kwargs={"Vertices": 16, "Radius": 0.0100, "Depth": 0.00050},
    )

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": cylinder.outputs["Mesh"],
            "Translation": (0.0050, 0.0000, 0.0000),
            "Rotation": (1.5708, 0.0000, 0.0000),
        },
    )

    cube_1 = nw.new_node(
        Nodes.MeshCube, input_kwargs={"Size": (0.0200, 0.0006, 0.0120)}
    )

    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": cube_1, "Translation": (0.0080, 0.0000, 0.0000)},
    )

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [cube, transform, transform_1]}
    )

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "attach_height", 0.1000),
            ("NodeSocketFloat", "door_width", 0.5000),
        ],
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["door_width"]},
        attrs={"operation": "MULTIPLY"},
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply, 1: 0.0181},
        attrs={"operation": "SUBTRACT"},
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={"X": subtract, "Z": group_input.outputs["attach_height"]},
    )

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": join_geometry_1, "Translation": combine_xyz},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_2},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_knob_handle", singleton=False, type="GeometryNodeTree"
)
def nodegroup_knob_handle(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "Radius", 0.0100),
            ("NodeSocketFloat", "thickness_1", 0.5000),
            ("NodeSocketFloat", "thickness_2", 0.5000),
            ("NodeSocketFloat", "length", 0.5000),
            ("NodeSocketFloat", "knob_mid_height", 0.0000),
            ("NodeSocketFloat", "edge_width", 0.5000),
            ("NodeSocketFloat", "door_width", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math,
        input_kwargs={
            0: group_input.outputs["thickness_2"],
            1: group_input.outputs["thickness_1"],
        },
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add, 1: group_input.outputs["length"]}
    )

    cylinder = nw.new_node(
        "GeometryNodeMeshCylinder",
        input_kwargs={
            "Vertices": 16,
            "Radius": group_input.outputs["Radius"],
            "Depth": add_1,
        },
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={
            0: group_input.outputs["door_width"],
            1: group_input.outputs["edge_width"],
        },
        attrs={"operation": "SUBTRACT"},
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: subtract, 1: -0.5000},
        attrs={"operation": "MULTIPLY"},
    )

    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: -0.005})

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_6 = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={
            "X": add_2,
            "Y": multiply_1,
            "Z": group_input.outputs["knob_mid_height"],
        },
    )

    transform_6 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": cylinder.outputs["Mesh"],
            "Translation": combine_xyz_6,
            "Rotation": (1.5708, 0.0000, 0.0000),
        },
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_6},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_mid_board", singleton=False, type="GeometryNodeTree"
)
def nodegroup_mid_board(nw: NodeWrangler, **kwargs):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "thickness", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: -0.0001}
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: 0.0000}
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["height"]},
        attrs={"operation": "MULTIPLY"},
    )

    multiply_k = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1, 1: 0.5000}, attrs={"operation": "MULTIPLY"}
    )

    add_k = nw.new_node(Nodes.Math, input_kwargs={0: multiply_k, 1: 0.004})

    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: -0.0001})

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add, "Y": add_1, "Z": add_2}
    )

    cube = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": combine_xyz_3,
            "Vertices X": 2,
            "Vertices Y": 2,
            "Vertices Z": 2,
        },
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: multiply}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_4 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": add_k, "Z": multiply_1}
    )

    transform_4 = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_4}
    )

    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={"Geometry": transform_4, "Material": kwargs["material"][0]},
    )

    combine_xyz_7 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add, "Y": add_1, "Z": add_2}
    )

    cube_1 = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": combine_xyz_7,
            "Vertices X": 2,
            "Vertices Y": 2,
            "Vertices Z": 2,
        },
    )

    multiply_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply, 1: 1.5000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_8 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": add_k, "Z": multiply_2}
    )

    transform_7 = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_8}
    )

    set_material_1 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={"Geometry": transform_7, "Material": kwargs["material"][1]},
    )

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [set_material, set_material_1]}
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_1}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": realize_instances, "mid_height": multiply},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_mid_board_001", singleton=False, type="GeometryNodeTree"
)
def nodegroup_mid_board_001(nw: NodeWrangler, **kwargs):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "thickness", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: -0.0001}
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: 0.0000}
    )

    multiply_k = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1, 1: 0.5000}, attrs={"operation": "MULTIPLY"}
    )

    add_k = nw.new_node(Nodes.Math, input_kwargs={0: multiply_k, 1: 0.004})

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["height"], 1: 1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: -0.0001})

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add, "Y": add_1, "Z": add_2}
    )

    cube = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": combine_xyz_3,
            "Vertices X": 2,
            "Vertices Y": 2,
            "Vertices Z": 2,
        },
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: multiply}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_4 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": add_k, "Z": multiply_1}
    )

    transform_4 = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_4}
    )

    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={"Geometry": transform_4, "Material": kwargs["material"][0]},
    )

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": set_material}
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_1}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": realize_instances, "mid_height": multiply},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_double_rampled_edge", singleton=False, type="GeometryNodeTree"
)
def nodegroup_double_rampled_edge(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "thickness_2", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
            ("NodeSocketFloat", "thickness_1", 0.5000),
            ("NodeSocketFloat", "ramp_angle", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: 0.0000}
    )

    combine_xyz_10 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": add})

    curve_line = nw.new_node(Nodes.CurveLine, input_kwargs={"End": combine_xyz_10})

    curve_circle = nw.new_node(
        Nodes.CurveCircle, input_kwargs={"Resolution": 3, "Radius": 0.0100}
    )

    endpoint_selection = nw.new_node(
        Nodes.EndpointSelection, input_kwargs={"End Size": 0}
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: 0.0000}
    )

    add_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["ramp_angle"], 1: 0.0000}
    )

    tangent = nw.new_node(
        Nodes.Math, input_kwargs={0: add_2}, attrs={"operation": "TANGENT"}
    )

    add_3 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["thickness_2"], 1: 0.0000}
    )

    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: tangent, 1: add_3}, attrs={"operation": "MULTIPLY"}
    )

    multiply_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: 2.0000, 1: multiply},
        attrs={"operation": "MULTIPLY"},
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: add_1, 1: multiply_1},
        attrs={"operation": "SUBTRACT"},
    )

    multiply_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: subtract}, attrs={"operation": "MULTIPLY"}
    )

    multiply_3 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_2, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    add_4 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["thickness_1"], 1: 0.0000}
    )

    combine_xyz_7 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply_3, "Y": add_4}
    )

    set_position = nw.new_node(
        Nodes.SetPosition,
        input_kwargs={
            "Geometry": curve_circle.outputs["Curve"],
            "Selection": endpoint_selection,
            "Position": combine_xyz_7,
        },
    )

    endpoint_selection_1 = nw.new_node(
        Nodes.EndpointSelection, input_kwargs={"Start Size": 0}
    )

    add_5 = nw.new_node(Nodes.Math, input_kwargs={0: add_4, 1: add_3})

    combine_xyz_8 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply_3, "Y": add_5}
    )

    set_position_1 = nw.new_node(
        Nodes.SetPosition,
        input_kwargs={
            "Geometry": set_position,
            "Selection": endpoint_selection_1,
            "Position": combine_xyz_8,
        },
    )

    index = nw.new_node(Nodes.Index)

    less_than = nw.new_node(
        Nodes.Math, input_kwargs={0: index, 1: 1.0100}, attrs={"operation": "LESS_THAN"}
    )

    greater_than = nw.new_node(
        Nodes.Math,
        input_kwargs={0: index, 1: 0.9900},
        attrs={"operation": "GREATER_THAN"},
    )

    op_and = nw.new_node(
        Nodes.BooleanMath, input_kwargs={0: less_than, 1: greater_than}
    )

    multiply_4 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1}, attrs={"operation": "MULTIPLY"}
    )

    multiply_5 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_4, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_9 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply_5, "Y": add_4}
    )

    set_position_2 = nw.new_node(
        Nodes.SetPosition,
        input_kwargs={
            "Geometry": set_position_1,
            "Selection": op_and,
            "Position": combine_xyz_9,
        },
    )

    curve_to_mesh = nw.new_node(
        Nodes.CurveToMesh,
        input_kwargs={
            "Curve": curve_line,
            "Profile Curve": set_position_2,
            "Fill Caps": True,
        },
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add_1, "Y": add_4, "Z": add}
    )

    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    multiply_6 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_4}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": multiply_6})

    transform = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_2}
    )

    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": add_3, "Z": add}
    )

    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_1})

    multiply_7 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_3}, attrs={"operation": "MULTIPLY"}
    )

    add_6 = nw.new_node(Nodes.Math, input_kwargs={0: add_4, 1: multiply_7})

    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_6})

    transform_1 = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_3}
    )

    join_geometry = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [transform, transform_1]}
    )

    multiply_8 = nw.new_node(
        Nodes.Math, input_kwargs={0: add}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_11 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_8})

    transform_4 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz_11},
    )

    combine_xyz_12 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": add})

    curve_line_1 = nw.new_node(Nodes.CurveLine, input_kwargs={"End": combine_xyz_12})

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": set_position_2, "Scale": (-1.0000, 1.0000, 1.0000)},
    )

    curve_to_mesh_1 = nw.new_node(
        Nodes.CurveToMesh,
        input_kwargs={
            "Curve": curve_line_1,
            "Profile Curve": transform_2,
            "Fill Caps": True,
        },
    )

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={"Geometry": [curve_to_mesh, transform_4, curve_to_mesh_1]},
    )

    merge_by_distance = nw.new_node(
        Nodes.MergeByDistance,
        input_kwargs={"Geometry": join_geometry_1, "Distance": 0.0001},
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": merge_by_distance}
    )

    subdivide_mesh = nw.new_node(
        Nodes.SubdivideMesh, input_kwargs={"Mesh": realize_instances, "Level": 4}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": subdivide_mesh},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_ramped_edge", singleton=False, type="GeometryNodeTree"
)
def nodegroup_ramped_edge(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "thickness_2", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
            ("NodeSocketFloat", "thickness_1", 0.5000),
            ("NodeSocketFloat", "ramp_angle", 0.5000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: 0.0000}
    )

    combine_xyz_10 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": add})

    curve_line = nw.new_node(Nodes.CurveLine, input_kwargs={"End": combine_xyz_10})

    curve_circle = nw.new_node(
        Nodes.CurveCircle, input_kwargs={"Resolution": 3, "Radius": 0.0100}
    )

    endpoint_selection = nw.new_node(
        Nodes.EndpointSelection, input_kwargs={"End Size": 0}
    )

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: 0.0000}
    )

    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1}, attrs={"operation": "MULTIPLY"}
    )

    add_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["ramp_angle"], 1: 0.0000}
    )

    tangent = nw.new_node(
        Nodes.Math, input_kwargs={0: add_2}, attrs={"operation": "TANGENT"}
    )

    add_3 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["thickness_2"], 1: 0.0000}
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: tangent, 1: add_3}, attrs={"operation": "MULTIPLY"}
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: add_1, 1: multiply_1},
        attrs={"operation": "SUBTRACT"},
    )

    subtract_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply, 1: subtract},
        attrs={"operation": "SUBTRACT"},
    )

    add_4 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["thickness_1"], 1: 0.0000}
    )

    combine_xyz_7 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": subtract_1, "Y": add_4}
    )

    set_position = nw.new_node(
        Nodes.SetPosition,
        input_kwargs={
            "Geometry": curve_circle.outputs["Curve"],
            "Selection": endpoint_selection,
            "Position": combine_xyz_7,
        },
    )

    endpoint_selection_1 = nw.new_node(
        Nodes.EndpointSelection, input_kwargs={"Start Size": 0}
    )

    add_5 = nw.new_node(Nodes.Math, input_kwargs={0: add_4, 1: add_3})

    combine_xyz_8 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": subtract_1, "Y": add_5}
    )

    set_position_1 = nw.new_node(
        Nodes.SetPosition,
        input_kwargs={
            "Geometry": set_position,
            "Selection": endpoint_selection_1,
            "Position": combine_xyz_8,
        },
    )

    index = nw.new_node(Nodes.Index)

    less_than = nw.new_node(
        Nodes.Math, input_kwargs={0: index, 1: 1.0100}, attrs={"operation": "LESS_THAN"}
    )

    greater_than = nw.new_node(
        Nodes.Math,
        input_kwargs={0: index, 1: 0.9900},
        attrs={"operation": "GREATER_THAN"},
    )

    op_and = nw.new_node(
        Nodes.BooleanMath, input_kwargs={0: less_than, 1: greater_than}
    )

    multiply_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_9 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply_2, "Y": add_4}
    )

    set_position_2 = nw.new_node(
        Nodes.SetPosition,
        input_kwargs={
            "Geometry": set_position_1,
            "Selection": op_and,
            "Position": combine_xyz_9,
        },
    )

    curve_to_mesh = nw.new_node(
        Nodes.CurveToMesh,
        input_kwargs={
            "Curve": curve_line,
            "Profile Curve": set_position_2,
            "Fill Caps": True,
        },
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add_1, "Y": add_4, "Z": add}
    )

    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    multiply_3 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_4}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": multiply_3})

    transform = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_2}
    )

    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": add_3, "Z": add}
    )

    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_1})

    multiply_4 = nw.new_node(
        Nodes.Math, input_kwargs={0: multiply_1}, attrs={"operation": "MULTIPLY"}
    )

    multiply_5 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_3}, attrs={"operation": "MULTIPLY"}
    )

    add_6 = nw.new_node(Nodes.Math, input_kwargs={0: add_4, 1: multiply_5})

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply_4, "Y": add_6}
    )

    transform_1 = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_3}
    )

    join_geometry = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [transform, transform_1]}
    )

    multiply_6 = nw.new_node(
        Nodes.Math, input_kwargs={0: add}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_11 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_6})

    transform_4 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz_11},
    )

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [curve_to_mesh, transform_4]}
    )

    merge_by_distance = nw.new_node(
        Nodes.MergeByDistance,
        input_kwargs={"Geometry": join_geometry_1, "Distance": 0.0001},
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": merge_by_distance}
    )

    subdivide_mesh = nw.new_node(
        Nodes.SubdivideMesh, input_kwargs={"Mesh": realize_instances, "Level": 4}
    )

    multiply_7 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1, 1: -0.5000}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_7})

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": subdivide_mesh, "Translation": combine_xyz_4},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_2},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_panel_edge_frame", singleton=False, type="GeometryNodeTree"
)
def nodegroup_panel_edge_frame(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketGeometry", "vertical_edge", None),
            ("NodeSocketFloat", "door_width", 0.5000),
            ("NodeSocketFloat", "door_height", 0.0000),
            ("NodeSocketGeometry", "horizontal_edge", None),
        ],
    )

    multiply_add = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["door_width"], 2: 0.0010},
        attrs={"operation": "MULTIPLY_ADD"},
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_add, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    transform_7 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": group_input.outputs["horizontal_edge"],
            "Translation": (0.0000, -0.0001, 0.0000),
            "Scale": (0.9999, 1.0000, 1.0000),
        },
    )

    multiply_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_add, 1: 1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    add = nw.new_node(Nodes.Math, input_kwargs={0: multiply_1, 1: -0.0001})

    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["door_height"], 1: 0.0001}
    )

    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add, "Z": add_1})

    transform_3 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": transform_7,
            "Translation": combine_xyz_2,
            "Rotation": (0.0000, -1.5708, 0.0000),
        },
    )

    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: 0.0001})

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add_2})

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": transform_7,
            "Translation": combine_xyz_1,
            "Rotation": (0.0000, 1.5708, 0.0000),
        },
    )

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_add})

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": group_input.outputs["vertical_edge"],
            "Translation": combine_xyz,
        },
    )

    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Scale": (-1.0000, 1.0000, 1.0000)},
    )

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={"Geometry": [transform_3, transform_2, transform_1, transform]},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Value": multiply, "Geometry": join_geometry_1},
        attrs={"is_active_output": True},
    )

def geometry_door_nodes(nw: NodeWrangler, **kwargs):
    # Code generated using version 2.6.4 of the node_transpiler

    door_height = nw.new_node(Nodes.Value, label="door_height")
    door_height.outputs[0].default_value = kwargs["door_height"]

    door_edge_thickness_2 = nw.new_node(Nodes.Value, label="door_edge_thickness_2")
    door_edge_thickness_2.outputs[0].default_value = kwargs["edge_thickness_2"]

    door_edge_width = nw.new_node(Nodes.Value, label="door_edge_width")
    door_edge_width.outputs[0].default_value = kwargs["edge_width"]

    door_edge_thickness_1 = nw.new_node(Nodes.Value, label="door_edge_thickness_1")
    door_edge_thickness_1.outputs[0].default_value = kwargs["edge_thickness_1"]

    door_edge_ramp_angle = nw.new_node(Nodes.Value, label="door_edge_ramp_angle")
    door_edge_ramp_angle.outputs[0].default_value = kwargs["edge_ramp_angle"]

    ramped_edge = nw.new_node(
        nodegroup_ramped_edge().name,
        input_kwargs={
            "height": door_height,
            "thickness_2": door_edge_thickness_2,
            "width": door_edge_width,
            "thickness_1": door_edge_thickness_1,
            "ramp_angle": door_edge_ramp_angle,
        },
    )

    door_width = nw.new_node(Nodes.Value, label="door_width")
    door_width.outputs[0].default_value = kwargs["door_width"]

    ramped_edge_1 = nw.new_node(
        nodegroup_ramped_edge().name,
        input_kwargs={
            "height": door_width,
            "thickness_2": door_edge_thickness_2,
            "width": door_edge_width,
            "thickness_1": door_edge_thickness_1,
            "ramp_angle": door_edge_ramp_angle,
        },
    )

    panel_edge_frame = nw.new_node(
        nodegroup_panel_edge_frame().name,
        input_kwargs={
            "vertical_edge": ramped_edge,
            "door_width": door_width,
            "door_height": door_height,
            "horizontal_edge": ramped_edge_1,
        },
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: panel_edge_frame.outputs["Value"], 1: 0.0001}
    )

    mid_board_thickness = nw.new_node(Nodes.Value, label="mid_board_thickness")
    mid_board_thickness.outputs[0].default_value = kwargs["board_thickness"]

    if kwargs["has_mid_ramp"]:
        mid_board = nw.new_node(
            nodegroup_mid_board(material=kwargs["board_material"]).name,
            input_kwargs={
                "height": door_height,
                "thickness": mid_board_thickness,
                "width": door_width,
            },
        )
    else:
        mid_board = nw.new_node(
            nodegroup_mid_board_001(material=kwargs["board_material"]).name,
            input_kwargs={
                "height": door_height,
                "thickness": mid_board_thickness,
                "width": door_width,
            },
        )

    combine_xyz_5 = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={"X": add, "Y": -0.0001, "Z": mid_board.outputs["mid_height"]},
    )

    frame = [panel_edge_frame.outputs["Geometry"]]
    if kwargs["has_mid_ramp"]:
        double_rampled_edge = nw.new_node(
            nodegroup_double_rampled_edge().name,
            input_kwargs={
                "height": door_width,
                "thickness_2": door_edge_thickness_2,
                "width": door_edge_width,
                "thickness_1": door_edge_thickness_1,
                "ramp_angle": door_edge_ramp_angle,
            },
        )

        transform_5 = nw.new_node(
            Nodes.Transform,
            input_kwargs={
                "Geometry": double_rampled_edge,
                "Translation": combine_xyz_5,
                "Rotation": (0.0000, 1.5708, 0.0000),
            },
        )

        convex_hull_midboard = nw.new_node(
            Nodes.ConvexHull, input_kwargs={"Geometry": transform_5}
        )

        flip_faces_midboard = nw.new_node(
            Nodes.FlipFaces, input_kwargs={"Mesh": convex_hull_midboard}
        )

        frame.append(flip_faces_midboard)

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": frame})

    set_material_2 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": join_geometry_1,
            "Material": kwargs["frame_material"],
        },
    )

    knob_raduis = nw.new_node(Nodes.Value, label="knob_raduis")
    knob_raduis.outputs[0].default_value = kwargs["knob_R"]

    know_length = nw.new_node(Nodes.Value, label="know_length")
    know_length.outputs[0].default_value = kwargs["knob_length"]

    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: door_height}, attrs={"operation": "MULTIPLY"}
    )

    knob_handle = nw.new_node(
        nodegroup_knob_handle().name,
        input_kwargs={
            "Radius": knob_raduis,
            "thickness_1": door_edge_thickness_1,
            "thickness_2": door_edge_thickness_2,
            "length": know_length,
            "knob_mid_height": multiply,
            "edge_width": door_edge_width,
            "door_width": door_width,
        },
    )

    knob_flip_faces = nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": knob_handle})

    set_material_3 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": knob_flip_faces,
            "Material": kwargs["frame_material"],
        },
    )

    attach_gadgets = []

    for h in kwargs["attach_height"]:
        attach_height = nw.new_node(Nodes.Value, label="attach_height")
        attach_height.outputs[0].default_value = h

        attach = nw.new_node(
            nodegroup_node_group().name,
            input_kwargs={"attach_height": attach_height, "door_width": door_width},
        )

        set_material_1 = nw.new_node(
            Nodes.SetMaterial,
            input_kwargs={"Geometry": attach, "Material": get_shelf_material("metal")},
        )
        attach_gadgets.append(set_material_1)

    flip_faces_middle = nw.new_node(
        Nodes.FlipFaces, input_kwargs={"Mesh": mid_board.outputs["Geometry"]}
    )

    geos = [
        set_material_2,
        set_material_3,
        flip_faces_middle,
    ] + attach_gadgets
    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": geos})

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: door_width, 1: -0.5000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply})

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz},
    )

    realize_instances_1 = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": transform}
    )

    triangulate = nw.new_node(
        "GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances_1}
    )

    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": triangulate,
            "Scale": (-1.0 if kwargs["door_left_hinge"] else 1.0, 1.0000, 1.0000),
        },
    )

    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform_1, "Rotation": (0.0000, 0.0000, -1.5708)},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_2},
        attrs={"is_active_output": True},
    )

class CabinetDoorBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(CabinetDoorBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = params

    def get_asset_params(self, i=0):
        params = self.params.copy()
        if params.get("door_height", None) is None:
            params["door_height"] = uniform(0.7, 2.2)
        if params.get("door_width", None) is None:
            params["door_width"] = uniform(0.3, 0.4)
        if params.get("edge_thickness_1", None) is None:
            params["edge_thickness_1"] = uniform(0.01, 0.02)
        if params.get("edge_width", None) is None:
            params["edge_width"] = uniform(0.03, 0.05)
        if params.get("edge_thickness_2", None) is None:
            params["edge_thickness_2"] = uniform(0.005, 0.01)
        if params.get("edge_ramp_angle", None) is None:
            params["edge_ramp_angle"] = uniform(0.6, 0.8)
        params["board_thickness"] = params["edge_thickness_1"] - 0.005
        if params.get("knob_R", None) is None:
            params["knob_R"] = uniform(0.003, 0.006)
        if params.get("knob_length", None) is None:
            params["knob_length"] = uniform(0.018, 0.035)
        if params.get("attach_height", None) is None:
            gap = uniform(0.05, 0.15)
            params["attach_height"] = [gap, params["door_height"] - gap]
        if params.get("has_mid_ramp", None) is None:
            params["has_mid_ramp"] = np.random.choice([True, False], p=[0.6, 0.4])
        if params.get("door_left_hinge", None) is None:
            params["door_left_hinge"] = False

        if params.get("frame_material", None) is None:
            params["frame_material"] = np.random.choice(
                ["white", "black_wood", "wood", "glass", "metal"]
            )
        if params.get("board_material", None) is None:
            if params["has_mid_ramp"]:
                lower_mat = np.random.choice(
                    [params["frame_material"], "glass"], p=[0.6, 0.4]
                )
                upper_mat = np.random.choice([lower_mat, "glass"], p=[0.6, 0.4])
                params["board_material"] = [lower_mat, upper_mat]
            else:
                params["board_material"] = [params["frame_material"]]

        params = self.get_material_func(params)
        return params

    def get_material_func(self, params, randomness=True):
        params["frame_material"] = get_shelf_material(params["frame_material"])
        materials = []
        if not isinstance(params["board_material"], list):
            params["board_material"] = [params["board_material"]]
        for mat in params["board_material"]:
            materials.append(get_shelf_material(mat))
        params["board_material"] = materials

        return params

    def create_asset(self, sample_params=True, i=0, **params):
        bpy.ops.mesh.primitive_plane_add(
            size=1,
            enter_editmode=False,
            align="WORLD",
            location=(0, 0, 0),
            scale=(1, 1, 1),
        )
        obj = bpy.context.active_object

        if sample_params:
            obj_params = self.get_asset_params(i)
        else:
            obj_params = self.params

        surface.add_geomod(
            obj,
            geometry_door_nodes,
            apply=True,
            attributes=[],
            input_kwargs=obj_params,
        )

        if params.get("ret_params", False):
            return obj, obj_params

        return obj

class CabinetDoorIkeaFactory(CabinetDoorBaseFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(CabinetDoorIkeaFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = {
            "edge_thickness_1": 0.012,
            "edge_thickness_2": 0.008,
            "board_thickness": 0.006,
            "edge_width": 0.02,
            "edge_ramp_angle": 0.5,
            "knob_R": 0.004,
            "knob_length": 0.03,
            "has_mid_ramp": False,
            "attach_height": 0.08,
        }

    def get_asset_params(self, i=0):
        params = self.params.copy()
        if params.get("door_height", None) is None:
            params["door_height"] = uniform(0.7, 2.2)
        if params.get("door_width", None) is None:
            params["door_width"] = uniform(0.3, 0.4)
        if params.get("door_left_hinge", None) is None:
            params["door_left_hinge"] = False

        params["attach_height"] = [
            params["door_height"] - params["attach_height"],
            params["attach_height"],
        ]

        if params.get("frame_material", None) is None:
            params["frame_material"] = np.random.choice(
                ["white", "black_wood", "wood", "glass", "metal"]
            )
        if params.get("board_material", None) is None:
            params["board_material"] = [params["frame_material"]]

        params = self.get_material_func(params)
        return params

def build(seed=0):
    seed = int(seed)
    derived = int_hash((seed, 0))
    random.seed(derived)
    np.random.seed(derived)
    fac = CabinetDoorIkeaFactory(seed)
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
        fallback = next((mat for mat in result.data.materials if mat is not None), None)
        if fallback is not None:
            for i in range(len(result.data.materials)):
                if result.data.materials[i] is None:
                    result.data.materials[i] = fallback
    return result

SEED = int(os.environ.get('SEED', 0))
build(SEED)

