# [FL_INDEX: keywords="blender_factory, procedural_3d, CabinetDrawerBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CabinetDrawerBaseFactory | Category: factories_tex
# Prompt: A 3D model of an open cabinet drawer box rendered from a three-quarter perspective, featuring a rectangular tray-like form with a tall back panel and shorter side walls, all displaying a rich dark wood-grain appearance.

"""CabinetDrawerBaseFactory (textured).

Texture-enabled rewrite of `objects_blender/shelves/CabinetDrawerBaseFactory.py`.
Geometry is copied verbatim from the source file; materials are assigned to
the drawer body via a hand-crafted raw-bpy shader library translated from

reference:
                                                 — get_shelf_material(name)

The factory samples materials inside `create_asset` (via
`get_asset_params` -> `get_material_func` -> `get_shelf_material`), not
`int_hash((factory_seed, i))`, so material sampling happens under the
int_hash-derived seed, not the raw seed. We therefore do NOT sample materials
at module level — instead we override the `get_shelf_material` stub below
with a real implementation that samples & builds materials inline during

wear_tear: the factory has NO `finalize_assets` method and does
NOT apply `scratches`/`edge_wear`. Per spec, wear_tear is therefore NOT
included here.
"""


import os
import bpy
import bmesh
import math
import random
import hashlib
import colorsys
import numpy as np
from numpy.random import uniform
from contextlib import contextmanager

# ----------------------------------------------------------------------------
#     shader_shelves_white           -> make_shelves_white
#     shader_shelves_black_wood(_z)  -> make_shelves_black_wood(_z)
#     shader_shelves_wood      (_z)  -> make_shelves_wood      (_z)
# Shader call logic matches `get_shelf_material(name)` in plywood.py.

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
        for name in names:
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

# ----------------------------------------------------------------------------
# shader_shelves_white  (plywood.py:26)
# ----------------------------------------------------------------------------
def _sample_white_params():
    v = np.random.uniform(0.7, 1.0)
    return dict(
        rgb=[v * (1.0 + np.random.normal(0, 0.005)),
             v * (1.0 + np.random.normal(0, 0.005)),
             v * (1.0 + np.random.normal(0, 0.005))],
        roughness=float(np.random.uniform(0.7, 1.0)),
    )

def make_shelves_white(name="ShelvesWhite", params=None):
    if params is None:
        params = _sample_white_params()
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        **{"Base Color": (*params["rgb"], 1.0),
           "Roughness": params["roughness"]},
    )
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# shader_shelves_black_wood  (plywood.py:72)
# ----------------------------------------------------------------------------
def _sample_black_wood_params():
    return dict(
        wave_scale=float(np.random.uniform(1.0, 3.0)),
        dark_scale=float(np.random.uniform(0.0, 0.01)),
        gray_scale=float(np.random.uniform(0.01, 0.03)),
        rgb=[float(np.random.uniform(0.015, 0.035)),
             float(np.random.uniform(0.0, 0.01)),
             float(np.random.uniform(0.0, 0.01))],
        roughness=float(np.random.uniform(0.75, 1.0)),
    )

def _build_shelves_wood_common_trunk(nt, z_axis_texture, wave_scale):
    """Shared trunk for shader_shelves_black_wood and shader_shelves_wood.
    Faithfully replicates plywood.py lines 75-165.
    Returns (mix_2_out, colorramp_1_out, colorramp_2_out)."""

    tex_coord_1 = nt.nodes.new("ShaderNodeTexCoord")
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    if z_axis_texture:
        mapping_1.inputs["Scale"].default_value = (0.1, 0.1, 2.0)
    else:
        mapping_1.inputs["Scale"].default_value = (0.1, 2.0, 2.0)
    nt.links.new(tex_coord_1.outputs["Object"], mapping_1.inputs["Vector"])

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise1.inputs:     noise1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise1.inputs: noise1.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping_1.outputs["Vector"], noise1.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = 40.0
    nt.links.new(_noise_fac_output(noise1), voronoi.inputs["Vector"])

    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    fac_in1 = cr1.inputs.get("Fac") or cr1.inputs[0]
    vor_color = voronoi.outputs.get("Color") or voronoi.outputs[0]
    nt.links.new(vor_color, fac_in1)
    cr1.color_ramp.elements[0].position = 0.0864
    cr1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr1.color_ramp.elements[1].position = 0.1091
    cr1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    if z_axis_texture:
        mapping.inputs["Scale"].default_value = (wave_scale, wave_scale, 0.1)
    else:
        mapping.inputs["Scale"].default_value = (wave_scale, 0.1, 0.1)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # Musgrave substitute: Blender 5.0 removed ShaderNodeTexMusgrave; use a
    # NoiseTexture with high detail as a visually-close replacement.
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave.inputs:     musgrave.inputs["Detail"].default_value = 3.0
    if "Distortion" in musgrave.inputs: musgrave.inputs["Distortion"].default_value = 0.0
    nt.links.new(_noise_fac_output(noise), musgrave.inputs["Vector"])

    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    nt.links.new(_noise_fac_output(musgrave), mix_1.inputs[6])
    noise_color = noise.outputs.get("Color") or noise.outputs[0]
    nt.links.new(noise_color, mix_1.inputs[7])

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    fac_in2 = cr2.inputs.get("Fac") or cr2.inputs[0]
    nt.links.new(mix_1.outputs[2], fac_in2)
    cr2.color_ramp.elements[0].position = 0.0818
    cr2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr2.color_ramp.elements[1].position = 0.8500
    cr2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"):
        mix_2.data_type = "RGBA"
    mix_2.inputs[0].default_value = 0.6
    cr1_color = cr1.outputs.get("Color") or cr1.outputs[0]
    cr2_color = cr2.outputs.get("Color") or cr2.outputs[0]
    nt.links.new(cr1_color, mix_2.inputs[6])
    nt.links.new(cr2_color, mix_2.inputs[7])

    return mix_2.outputs[2], cr1_color, cr2_color

def make_shelves_black_wood(name="ShelvesBlackWood", params=None, z_axis_texture=False):
    if params is None:
        params = _sample_black_wood_params()
    mat = _new_material(name)
    nt = mat.node_tree

    mix2_out, cr1_color, cr2_color = _build_shelves_wood_common_trunk(
        nt, z_axis_texture, params["wave_scale"]
    )

    cr_final = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr_final.inputs.get("Fac") or cr_final.inputs[0]
    nt.links.new(mix2_out, fac_in)
    cr_final.color_ramp.elements.new(0.5)
    dark = params["dark_scale"]; gray = params["gray_scale"]
    color_scale = (*params["rgb"], 1.0)
    cr_final.color_ramp.elements[0].position = 0.15
    cr_final.color_ramp.elements[0].color = (dark, dark, dark, 1.0)
    cr_final.color_ramp.elements[1].position = 0.5
    cr_final.color_ramp.elements[1].color = (gray, gray, gray, 1.0)
    cr_final.color_ramp.elements[2].position = 1.0
    cr_final.color_ramp.elements[2].color = color_scale

    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"):
        mix_3.data_type = "RGBA"
    mix_3.inputs[0].default_value = 0.004
    nt.links.new(cr1_color, mix_3.inputs[6])
    nt.links.new(cr2_color, mix_3.inputs[7])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=params["roughness"])
    cr_final_color = cr_final.outputs.get("Color") or cr_final.outputs[0]
    nt.links.new(cr_final_color, bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_shelves_black_wood_z(name="ShelvesBlackWoodZ", params=None):
    return make_shelves_black_wood(name=name, params=params, z_axis_texture=True)

# ----------------------------------------------------------------------------
# shader_shelves_wood  (plywood.py:246, blond wood)
# ----------------------------------------------------------------------------
def _sample_wood_params():
    return dict(
        bright_hsv=[float(np.random.uniform(0.03, 0.09)),
                    float(np.random.uniform(0.5, 0.7)),
                    float(np.random.uniform(0.7, 1.0))],
        mid_hsv=[float(np.random.uniform(0.02, 0.06)),
                 float(np.random.uniform(0.6, 1.0)),
                 float(np.random.uniform(0.3, 0.6))],
        dark_hsv=[float(np.random.uniform(0.03, 0.05)),
                  float(np.random.uniform(0.6, 1.0)),
                  float(np.random.uniform(0.1, 0.3))],
        wave_scale=float(np.random.uniform(1.0, 3.0)),
        roughness=float(np.random.uniform(0.75, 1.0)),
    )

def make_shelves_wood(name="ShelvesWood", params=None, z_axis_texture=False):
    if params is None:
        params = _sample_wood_params()
    mat = _new_material(name)
    nt = mat.node_tree

    mix2_out, cr1_color, cr2_color = _build_shelves_wood_common_trunk(
        nt, z_axis_texture, params["wave_scale"]
    )

    cr_final = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr_final.inputs.get("Fac") or cr_final.inputs[0]
    nt.links.new(mix2_out, fac_in)
    cr_final.color_ramp.elements.new(0.5)
    cr_final.color_ramp.elements[0].position = 0.02
    cr_final.color_ramp.elements[0].color = hsv2rgba(params["dark_hsv"])
    cr_final.color_ramp.elements[1].position = 0.11
    cr_final.color_ramp.elements[1].color = hsv2rgba(params["mid_hsv"])
    cr_final.color_ramp.elements[2].position = 0.8
    cr_final.color_ramp.elements[2].color = hsv2rgba(params["bright_hsv"])

    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"):
        mix_3.data_type = "RGBA"
    mix_3.inputs[0].default_value = 0.004
    nt.links.new(cr1_color, mix_3.inputs[6])
    nt.links.new(cr2_color, mix_3.inputs[7])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=params["roughness"])
    cr_final_color = cr_final.outputs.get("Color") or cr_final.outputs[0]
    nt.links.new(cr_final_color, bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_shelves_wood_z(name="ShelvesWoodZ", params=None):
    return make_shelves_wood(name=name, params=params, z_axis_texture=True)

# ----------------------------------------------------------------------------
# Simple procedural metal shader — stand-in for
# get_shelf_material("metal") which in chooses between 5 metal
# shader functions (brushed / galvanized / grained / hammered / basic). We
# implement a single simple brushed-metal lookalike so "metal" knob samples
# produce a visible metallic material if the knob is ever geometrically
# distinguished. The drawer geometry_nodes does NOT actually bind knob
# material to its own SetMaterial node — the entire joined mesh uses
# drawer_material — but we still honour the RNG consumption order so seed
# ----------------------------------------------------------------------------
def _sample_metal_params():
    # Mirror 1 RNG draw from np.random.choice over the 5-shader list.
    # The individual metal samplers consume more draws but we approximate with
    # a single uniform draw here to keep it predictable; this only affects
    # knob_material which is geometrically unused.
    return dict(
        hue=float(np.random.uniform(0.55, 0.65)),
        metallic=float(np.random.uniform(0.75, 1.0)),
        roughness=float(np.random.uniform(0.1, 0.5)),
    )

def make_metal_basic(name="Metal", params=None):
    if params is None:
        params = _sample_metal_params()
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    gray = 0.65
    _set_principled(
        bsdf,
        **{"Base Color": (gray, gray, gray, 1.0),
           "Metallic": params["metallic"],
           "Roughness": params["roughness"]},
    )
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# CabinetDrawerBaseFactory material resolver — mirrors
# to the keys actually sampled by CabinetDrawerBaseFactory
# ("white"/"black_wood"/"wood"/"metal"). Each path consumes exactly one
# np.random.choice draw for the shader-func selection and then whatever
# order so the geometry (sampled next) stays reproducible.
# ----------------------------------------------------------------------------
def _resolve_shelf_material(key, slot_name=None):
    # The drawer body and the knob use (potentially) distinct RNG draws; give
    # each a unique readable name to aid debugging.
    slot_name = slot_name or str(key)
    if key == "white":
        # get_shelf_material("white") picks between 2 shaders w/ p=[0.6, 0.4];
        # we always use shader_shelves_white (the "primary" option) but still
        # consume the choice draw.
        _ = np.random.choice([0, 1], p=[0.6, 0.4])
        p = _sample_white_params()
        return make_shelves_white(slot_name, params=p)
    if key == "black_wood":
        _ = np.random.choice([0, 1], p=[0.6, 0.4])
        p = _sample_black_wood_params()
        return make_shelves_black_wood(slot_name, params=p)
    if key == "wood":
        _ = np.random.choice([0, 1], p=[0.6, 0.4])
        p = _sample_wood_params()
        return make_shelves_wood(slot_name, params=p)
    if key == "metal":
        # np.random.choice over 5 shader functions (uniform); consume the draw.
        _ = np.random.choice(5)
        p = _sample_metal_params()
        return make_metal_basic(slot_name, params=p)
    # Fallback
    p = _sample_white_params()
    return make_shelves_white(slot_name, params=p)

# ── Scene cleanup ──
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)

# --- Original geometry code (copied verbatim from
#     objects_blender/shelves/CabinetDrawerBaseFactory.py) ===================
# The only change: the local `get_shelf_material(*args, **kwargs)` stub is
# replaced with `_resolve_shelf_material` which returns an actual bpy
# Material. Material RNG draws now happen inside `get_asset_params` exactly
# where performs them.

from types import SimpleNamespace

C = bpy.context
D = bpy.data

def int_hash(x, mod=(2**32 - 1)):
    m = hashlib.md5()
    for s in (x if isinstance(x, (tuple, list)) else [x]):
        m.update(str(s).encode('utf-8'))
    return abs(int(m.hexdigest(), 16)) % mod

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    if o is not None:
        o.select_set(True)

class SelectObjects:
    def __init__(self, objs, active=0):
        self.objs = objs if isinstance(objs, (list, tuple)) else [objs]
        self.active = active
        self.prev_sel = None
        self.prev_active = None
    def __enter__(self):
        self.prev_sel = list(bpy.context.selected_objects)
        self.prev_active = bpy.context.view_layer.objects.active
        _select_none()
        for o in self.objs:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if self.objs:
            _set_active(self.objs[self.active])
        return self
    def __exit__(self, *_):
        _select_none()
        for o in self.prev_sel or []:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if self.prev_active is not None and self.prev_active.name in bpy.data.objects:
            _set_active(self.prev_active)

def apply_transform(obj, loc=False, rot=True, scale=True):
    with SelectObjects(obj):
        bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    return obj

def delete(obj):
    if obj is None:
        return
    objs = obj if isinstance(obj, (list, tuple)) else [obj]
    for o in objs:
        if o is None or o.name not in bpy.data.objects:
            continue
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass

def deep_clone_obj(obj, keep_modifiers=False, keep_materials=True):
    o = obj.copy()
    if obj.data:
        o.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(o)
    if not keep_modifiers:
        for m in list(o.modifiers):
            try:
                o.modifiers.remove(m)
            except Exception:
                pass
    if not keep_materials and getattr(o.data, 'materials', None):
        o.data.materials.clear()
    for ch in obj.children:
        ch2 = deep_clone_obj(ch, keep_modifiers=keep_modifiers, keep_materials=keep_materials)
        ch2.parent = o
    return o

def join_objects(objs):
    objs = [o for o in objs if o is not None and o.name in bpy.data.objects and o.type == 'MESH']
    if not objs:
        return None
    if len(objs) == 1:
        return objs[0]
    import bmesh as _bm
    dg = bpy.context.evaluated_depsgraph_get()
    combined = _bm.new()
    for o in objs:
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        tmp = _bm.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)
        tmp_me = bpy.data.meshes.new("_tmp")
        tmp.to_mesh(tmp_me)
        tmp.free()
        combined.from_mesh(tmp_me)
        bpy.data.meshes.remove(tmp_me)
        eo.to_mesh_clear()
    new_me = bpy.data.meshes.new("joined")
    combined.to_mesh(new_me)
    combined.free()
    result = bpy.data.objects.new("joined", new_me)
    bpy.context.collection.objects.link(result)
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    return result

def modify_mesh(obj, type, apply=True, name=None, return_mod=False, ng_inputs=None, show_viewport=None, **kwargs):
    name = name or f'modify_mesh({type})'
    if show_viewport is None:
        show_viewport = not apply
    mod = obj.modifiers.new(name=name, type=type)
    mod.show_viewport = show_viewport
    for k, v in kwargs.items():
        try:
            setattr(mod, k, v)
        except Exception:
            pass
    if ng_inputs is not None and type == 'NODES' and 'node_group' in kwargs:
        set_geomod_inputs(mod, ng_inputs)
    if apply:
        with SelectObjects(obj):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass
    return (obj, None if apply else mod) if return_mod else obj

# minimal node_utils / NodeWrangler runtime

def ng_inputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == 'INPUT'}

def ng_outputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == 'OUTPUT'}

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

node_utils = SimpleNamespace(to_nodegroup=to_nodegroup)

def _infer_output_socket(item):
    if isinstance(item, bpy.types.NodeSocket):
        return item
    if isinstance(item, tuple) and len(item) == 2 and hasattr(item[0], 'outputs'):
        node, sock = item
        return node.outputs[sock] if not isinstance(sock, int) else node.outputs[sock]
    if hasattr(item, 'outputs') and len(getattr(item, 'outputs', [])):
        for s in item.outputs:
            if getattr(s, 'enabled', True):
                return s
        return item.outputs[0]
    return None

def _socket_type_for_val(v):
    if isinstance(v, bool): return 'NodeSocketBool'
    if isinstance(v, int): return 'NodeSocketInt'
    if isinstance(v, float): return 'NodeSocketFloat'
    if isinstance(v, (tuple, list, np.ndarray)):
        n = len(v)
        if n == 3: return 'NodeSocketVector'
        if n == 4: return 'NodeSocketColor'
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
        if isinstance(node_type, str) and node_type in bpy.data.node_groups:
            try:
                return self.nodes.new(node_type)
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
                    pass
        try:
            return gi.outputs[name]
        except Exception:
            idx = list(ng_inputs(self.node_group).keys()).index(name)
            return gi.outputs[idx]

    def connect_input(self, sock, item):
        if isinstance(item, list):
            for sub in item:
                out = _infer_output_socket(sub)
                if out is not None:
                    try:
                        self.links.new(out, sock)
                    except Exception:
                        pass
            return
        out = _infer_output_socket(item)
        if out is not None:
            try:
                self.links.new(out, sock)
            except Exception:
                pass
        else:
            try:
                sock.default_value = item
            except Exception:
                try:
                    sock.default_value = tuple(item)
                except Exception:
                    pass

    def new_node(self, node_type, input_args=None, attrs=None, input_kwargs=None, label=None, expose_input=None, compat_mode=True, strict=True):
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
                    pass
        if input_args:
            for i, item in enumerate(input_args):
                if i < len(n.inputs):
                    self.connect_input(n.inputs[i], item)
        if input_kwargs:
            is_group_output = (n.bl_idname == 'NodeGroupOutput')
            for k, item in input_kwargs.items():
                if is_group_output and isinstance(k, str) and k not in [s.name for s in n.inputs]:
                    out_sock = _infer_output_socket(item)
                    if out_sock is not None:
                        st = out_sock.bl_idname if hasattr(out_sock, 'bl_idname') else 'NodeSocketFloat'
                        st = {'NodeSocketFloatUnsigned': 'NodeSocketFloat', 'NodeSocketVirtual': 'NodeSocketFloat'}.get(st, st)
                    else:
                        st = 'NodeSocketGeometry' if k.lower() in ('geometry', 'mesh') else 'NodeSocketFloat'
                    try:
                        self.node_group.interface.new_socket(name=k, in_out='OUTPUT', socket_type=st)
                    except Exception:
                        pass
                try:
                    self.connect_input(n.inputs[k], item)
                except Exception:
                    try:
                        idx = [s.name for s in n.inputs].index(k)
                        self.connect_input(n.inputs[idx], item)
                    except Exception:
                        pass
        return n

    def uniform(self, a, b):
        return float(np.random.uniform(float(a), float(b)))

class _SurfaceNS:

    def add_geomod(self, objs, geo_func, name=None, apply=False, reuse=False, input_args=None, input_kwargs=None, attributes=None, show_viewport=True, selection=None, domains=None, input_attributes=None):
        if not isinstance(objs, (list, tuple)):
            objs = [objs]
        out_mods = []
        for obj in objs:
            mod = obj.modifiers.new(name or getattr(geo_func, '__name__', 'GeometryNodes'), 'NODES')
            mod.show_viewport = show_viewport
            mod.node_group = bpy.data.node_groups.new(name or 'Geometry Nodes', 'GeometryNodeTree')
            try:
                if 'Geometry' not in ng_inputs(mod.node_group):
                    mod.node_group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
                if 'Geometry' not in ng_outputs(mod.node_group):
                    mod.node_group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
            except Exception:
                pass
            nw = NodeWrangler(mod)
            try:
                if input_args or input_kwargs:
                    geo_func(nw, *(input_args or []), **(input_kwargs or {}))
                else:
                    geo_func(nw)
            except (TypeError, KeyError):
                try:
                    geo_func(nw, *(input_args or []), **(input_kwargs or {}))
                except Exception:
                    gi = mod.node_group.nodes.new('NodeGroupInput')
                    go = mod.node_group.nodes.new('NodeGroupOutput')
                    go.is_active_output = True
                    mod.node_group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
                    mod.node_group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
                    try:
                        mod.node_group.links.new(gi.outputs['Geometry'], go.inputs['Geometry'])
                    except Exception:
                        pass
            except Exception:
                pass
            out_mods.append(mod)
            if apply:
                with SelectObjects(obj):
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    except Exception:
                        pass
        return out_mods[0] if len(out_mods) == 1 else out_mods

surface = _SurfaceNS()

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

butil = SimpleNamespace(
    apply_transform=apply_transform,
    modify_mesh=modify_mesh,
    delete=delete,
    join_objects=join_objects,
    select_none=_select_none,
)

butil.copy = deep_clone_obj

def spawn_vert(name='vert'):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0,0,0)], [], [])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj
butil.spawn_vert = spawn_vert

_orig_butil_modify_mesh = butil.modify_mesh
def _ensure_nodegroup_geom_passthrough(ng):
    if ng is None:
        return ng
    try:
        if 'Geometry' not in ng_inputs(ng):
            ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    except Exception:
        pass
    try:
        if 'Geometry' not in ng_outputs(ng):
            ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    except Exception:
        pass
    try:
        gi = next((n for n in ng.nodes if n.bl_idname == 'NodeGroupInput'), None) or ng.nodes.new('NodeGroupInput')
        go = next((n for n in ng.nodes if n.bl_idname == 'NodeGroupOutput'), None) or ng.nodes.new('NodeGroupOutput')
        go.is_active_output = True
        has_geom_link = False
        for l in ng.links:
            try:
                if l.from_node == gi and l.to_node == go:
                    has_geom_link = True
                    break
            except Exception:
                pass
        if not has_geom_link and len(gi.outputs) and len(go.inputs):
            try:
                ng.links.new(gi.outputs[0], go.inputs[0])
            except Exception:
                pass
    except Exception:
        pass
    return ng
def _safe_butil_modify_mesh(obj, type, *args, **kwargs):
    if type == 'NODES':
        ng = kwargs.get('node_group')
        if ng is not None:
            _ensure_nodegroup_geom_passthrough(ng)
    out = _orig_butil_modify_mesh(obj, type, *args, **kwargs)
    try:
        if type == 'NODES':
            mod = obj.modifiers[-1] if len(obj.modifiers) else None
            if mod and getattr(mod, 'node_group', None):
                _ensure_nodegroup_geom_passthrough(mod.node_group)
    except Exception:
        pass
    return out
butil.modify_mesh = _safe_butil_modify_mesh
_orig_surface_add_geomod = surface.add_geomod
def _safe_surface_add_geomod(*args, **kwargs):
    requested_apply = bool(kwargs.get('apply', False))
    if requested_apply:
        kwargs = dict(kwargs)
        kwargs['apply'] = False
    mods = _orig_surface_add_geomod(*args, **kwargs)
    mod_list = mods if isinstance(mods, (list, tuple)) else [mods]
    objs = args[0] if args else None
    obj_list = objs if isinstance(objs, (list, tuple)) else ([objs] if objs is not None else [])
    for mod in mod_list:
        try:
            ng = mod.node_group
            if 'Geometry' not in ng_inputs(ng):
                ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
            if 'Geometry' not in ng_outputs(ng):
                ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
            gi = next((n for n in ng.nodes if n.bl_idname == 'NodeGroupInput'), None) or ng.nodes.new('NodeGroupInput')
            go = next((n for n in ng.nodes if n.bl_idname == 'NodeGroupOutput'), None) or ng.nodes.new('NodeGroupOutput')
            go.is_active_output = True
            if len(go.inputs) and len(gi.outputs) and not go.inputs[0].is_linked:
                try:
                    ng.links.new(gi.outputs[0], go.inputs[0])
                except Exception:
                    pass
        except Exception:
            pass
    if requested_apply:
        for obj, mod in zip(obj_list, mod_list):
            try:
                with SelectObjects(obj):
                    bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass
    return mods
surface.add_geomod = _safe_surface_add_geomod

_orig_selectobjects_exit = SelectObjects.__exit__
def _safe_selectobjects_exit(self, *args):
    _select_none()
    for o in self.prev_sel or []:
        try:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        except ReferenceError:
            pass
    try:
        if self.prev_active is not None and self.prev_active.name in bpy.data.objects:
            _set_active(self.prev_active)
    except ReferenceError:
        pass
SelectObjects.__exit__ = _safe_selectobjects_exit

_orig_make_node = NodeWrangler._make_node
def _safe_make_node(self, node_type):
    if isinstance(node_type, str) and node_type.startswith('nodegroup_'):
        ng = bpy.data.node_groups.get(node_type)
        if ng is None:
            ng = bpy.data.node_groups.new(node_type, 'GeometryNodeTree')
            _ensure_nodegroup_geom_passthrough(ng)
        n = self.nodes.new('GeometryNodeGroup' if self.node_group.bl_idname == 'GeometryNodeTree' else 'ShaderNodeGroup')
        n.node_tree = ng
        return n
    try:
        return _orig_make_node(self, node_type)
    except Exception:
        raise
NodeWrangler._make_node = _safe_make_node

# --- Real material resolver (replaces the `return None` stub in the
#     objects_blender source). Called from inside CabinetDrawerBaseFactory's
#     get_material_func, which is invoked during get_asset_params under the
_MAT_SLOT_COUNTER = {'n': 0}
def get_shelf_material(name, **kwargs):
    _MAT_SLOT_COUNTER['n'] += 1
    slot_name = f"Drawer{_MAT_SLOT_COUNTER['n']}_{name}"
    return _resolve_shelf_material(name, slot_name=slot_name)

tagging = SimpleNamespace(tag_system=SimpleNamespace(relabel_obj=lambda o: o, relabel_objects=lambda o: o), tag_object=lambda *a, **k: None, tag_nodegroup=lambda nw, geo, *a, **k: geo)
t = SimpleNamespace(shelf='shelf', cabinet='cabinet', door='door', drawer='drawer', Subpart=SimpleNamespace(SupportSurface='support_surface'))

def copy(obj, keep_materials=True):
    return deep_clone_obj(obj, keep_modifiers=True, keep_materials=keep_materials)
butil.copy = copy

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
    StoreNamedAttribute = 'GeometryNodeStoreNamedAttribute'
    SubdivideMesh = 'GeometryNodeSubdivideMesh'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'

# ---- CabinetDrawerBaseFactory nodegroups ----

@node_utils.to_nodegroup(
    "nodegroup_kallax_drawer_frame", singleton=False, type="GeometryNodeTree"
)
def nodegroup_kallax_drawer_frame(nw: NodeWrangler):
    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "depth", 0.5000),
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "thickness", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
        ],
    )
    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: 0.0000}
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
        input_kwargs={"Size": combine_xyz, "Vertices X": 4, "Vertices Y": 4, "Vertices Z": 4},
    )
    store_named_attribute_1 = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube.outputs["Mesh"],
            "Name": "uv_map",
            3: cube.outputs["UV Map"],
        },
        attrs={"data_type": "FLOAT_VECTOR", "domain": "CORNER"},
    )
    add_3 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: 0.0000}
    )
    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: add_3}, attrs={"operation": "MULTIPLY"}
    )
    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1, 1: -0.5000}, attrs={"operation": "MULTIPLY"}
    )
    add_4 = nw.new_node(Nodes.Math, input_kwargs={0: multiply_1, 1: -0.0001})
    multiply_add = nw.new_node(
        Nodes.Math,
        input_kwargs={0: add_2, 2: 0.0100},
        attrs={"operation": "MULTIPLY_ADD"},
    )
    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": multiply, "Y": add_4, "Z": multiply_add}
    )
    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": store_named_attribute_1, "Translation": combine_xyz_1},
    )
    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Scale": (-1.0000, 1.0000, 1.0000)},
    )
    add_5 = nw.new_node(Nodes.Math, input_kwargs={0: add, 1: -0.0001})
    add_6 = nw.new_node(Nodes.Math, input_kwargs={0: add_3, 1: add_5})
    combine_xyz_2 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add_6, "Y": add_1, "Z": add}
    )
    cube_1 = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={"Size": combine_xyz_2, "Vertices X": 4, "Vertices Y": 4, "Vertices Z": 4},
    )
    store_named_attribute_2 = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube_1.outputs["Mesh"],
            "Name": "uv_map",
            3: cube_1.outputs["UV Map"],
        },
        attrs={"data_type": "FLOAT_VECTOR", "domain": "CORNER"},
    )
    multiply_add_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: add_1, 1: -0.5000, 2: -0.0001},
        attrs={"operation": "MULTIPLY_ADD"},
    )
    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": multiply_add_1, "Z": 0.0100}
    )
    transform_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": store_named_attribute_2, "Translation": combine_xyz_3},
    )
    combine_xyz_4 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add_3, "Y": add, "Z": add_2}
    )
    cube_2 = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={"Size": combine_xyz_4, "Vertices X": 4, "Vertices Y": 4, "Vertices Z": 4},
    )
    store_named_attribute = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube_2.outputs["Mesh"],
            "Name": "uv_map",
            3: cube_2.outputs["UV Map"],
        },
        attrs={"data_type": "FLOAT_VECTOR", "domain": "CORNER"},
    )
    multiply_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: add}, attrs={"operation": "MULTIPLY"}
    )
    multiply_add_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: add_1, 1: -1.0000, 2: multiply_2},
        attrs={"operation": "MULTIPLY_ADD"},
    )
    multiply_add_3 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: add_2, 2: 0.0100},
        attrs={"operation": "MULTIPLY_ADD"},
    )
    combine_xyz_5 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": multiply_add_2, "Z": multiply_add_3}
    )
    transform_3 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": store_named_attribute, "Translation": combine_xyz_5},
    )
    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={"Geometry": [transform_1, transform, transform_2, transform_3]},
    )
    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": join_geometry_1},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_door_knob", singleton=False, type="GeometryNodeTree"
)
def nodegroup_door_knob(nw: NodeWrangler):
    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "Radius", 0.0040),
            ("NodeSocketFloat", "length", 0.5000),
            ("NodeSocketFloat", "z", 0.5000),
        ],
    )
    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["length"], 1: 0.0000}
    )
    cylinder = nw.new_node(
        "GeometryNodeMeshCylinder",
        input_kwargs={
            "Vertices": 64,
            "Radius": group_input.outputs["Radius"],
            "Depth": add,
        },
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
    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: add}, attrs={"operation": "MULTIPLY"}
    )
    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: 0.0001})
    add_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["z"], 1: 0.0000}
    )
    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_2}, attrs={"operation": "MULTIPLY"}
    )
    combine_xyz_2 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": add_1, "Z": multiply_1}
    )
    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": store_named_attribute,
            "Translation": combine_xyz_2,
            "Rotation": (1.5708, 0.0000, 0.0000),
        },
    )
    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_1},
        attrs={"is_active_output": True},
    )

@node_utils.to_nodegroup(
    "nodegroup_drawer_door_board", singleton=False, type="GeometryNodeTree"
)
def nodegroup_drawer_door_board(nw: NodeWrangler):
    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "thickness", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
            ("NodeSocketFloat", "height", 0.5000),
        ],
    )
    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: 0.0000}
    )
    add_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: 0.0000}
    )
    add_2 = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: 0.0000}
    )
    combine_xyz = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add, "Y": add_1, "Z": add_2}
    )
    cube = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={"Size": combine_xyz, "Vertices X": 5, "Vertices Y": 5, "Vertices Z": 5},
    )
    store_named_attribute = nw.new_node(
        Nodes.StoreNamedAttribute,
        input_kwargs={
            "Geometry": cube.outputs["Mesh"],
            "Name": "uv_map",
            3: cube.outputs["UV Map"],
        },
        attrs={"data_type": "FLOAT_VECTOR", "domain": "CORNER"},
    )
    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: add_1, 1: -0.5000}, attrs={"operation": "MULTIPLY"}
    )
    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add_2}, attrs={"operation": "MULTIPLY"}
    )
    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": multiply, "Z": multiply_1}
    )
    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": store_named_attribute, "Translation": combine_xyz_1},
    )
    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform},
        attrs={"is_active_output": True},
    )

def geometry_nodes(nw: NodeWrangler, **kwargs):
    door_thickness = nw.new_node(Nodes.Value, label="door_thickness")
    door_thickness.outputs[0].default_value = kwargs["drawer_board_thickness"]

    drawer_board_width = nw.new_node(Nodes.Value, label="drawer_board_width")
    drawer_board_width.outputs[0].default_value = kwargs["drawer_board_width"]

    drawer_board_height = nw.new_node(Nodes.Value, label="drawer_board_height")
    drawer_board_height.outputs[0].default_value = kwargs["drawer_board_height"]

    drawer_door_board = nw.new_node(
        nodegroup_drawer_door_board().name,
        input_kwargs={
            "thickness": door_thickness,
            "width": drawer_board_width,
            "height": drawer_board_height,
        },
    )

    knob_radius = nw.new_node(Nodes.Value, label="knob_radius")
    knob_radius.outputs[0].default_value = kwargs["knob_radius"]

    knob_length = nw.new_node(Nodes.Value, label="knob_length")
    knob_length.outputs[0].default_value = kwargs["knob_length"]

    door_knob = nw.new_node(
        nodegroup_door_knob().name,
        input_kwargs={
            "Radius": knob_radius,
            "length": knob_length,
            "z": drawer_board_height,
        },
    )

    drawer_depth = nw.new_node(Nodes.Value, label="drawer_depth")
    drawer_depth.outputs[0].default_value = (
        kwargs["drawer_depth"] - kwargs["drawer_board_thickness"]
    )

    drawer_side_height = nw.new_node(Nodes.Value, label="drawer_side_height")
    drawer_side_height.outputs[0].default_value = kwargs["drawer_side_height"]

    drawer_width = nw.new_node(Nodes.Value, label="drawer_width")
    drawer_width.outputs[0].default_value = kwargs["drawer_width"]

    kallax_drawer_frame = nw.new_node(
        nodegroup_kallax_drawer_frame().name,
        input_kwargs={
            "depth": drawer_depth,
            "height": drawer_side_height,
            "thickness": door_thickness,
            "width": drawer_width,
        },
    )

    side_tilt_width = nw.new_node(Nodes.Value, label="side_tilt_width")
    side_tilt_width.outputs[0].default_value = kwargs["side_tilt_width"]

    join_geometry = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={"Geometry": [door_knob, drawer_door_board, kallax_drawer_frame]},
    )

    set_material_2 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": join_geometry,
            "Material": kwargs["drawer_material"],
        },
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": set_material_2}
    )

    triangulate = nw.new_node(
        "GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances}
    )

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": triangulate, "Rotation": (0.0000, 0.0000, -1.5708)},
    )

    group_output_1 = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform},
        attrs={"is_active_output": True},
    )

class CabinetDrawerBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(CabinetDrawerBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = {}

    def get_asset_params(self, i=0):
        params = self.params.copy()
        if params.get("drawer_board_thickness", None) is None:
            params["drawer_board_thickness"] = uniform(0.005, 0.01)
        if params.get("drawer_board_width", None) is None:
            params["drawer_board_width"] = uniform(0.3, 0.7)
        if params.get("drawer_board_height", None) is None:
            params["drawer_board_height"] = uniform(0.25, 0.4)
        if params.get("drawer_depth", None) is None:
            params["drawer_depth"] = uniform(0.3, 0.4)
        if params.get("drawer_side_height", None) is None:
            params["drawer_side_height"] = uniform(0.05, 0.2)
        if params.get("drawer_width", None) is None:
            params["drawer_width"] = params["drawer_board_width"] - uniform(0.015, 0.025)
        if params.get("side_tilt_width", None) is None:
            params["side_tilt_width"] = uniform(0.02, 0.03)
        if params.get("knob_radius", None) is None:
            params["knob_radius"] = uniform(0.003, 0.006)
        if params.get("knob_length", None) is None:
            params["knob_length"] = uniform(0.018, 0.035)

        if params.get("drawer_material", None) is None:
            params["drawer_material"] = np.random.choice(
                ["white", "black_wood", "wood"], p=[0.5, 0.2, 0.3]
            )
        if params.get("knob_material", None) is None:
            params["knob_material"] = np.random.choice(
                [params["drawer_material"], "metal"], p=[0.5, 0.5]
            )

        params = self.get_material_func(params)
        return params

    def get_material_func(self, params, randomness=True):
        params["drawer_material"] = get_shelf_material(params["drawer_material"])
        params["knob_material"] = get_shelf_material(params["knob_material"])
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

        if params.get("ret_params", False):
            return obj, obj_params

        return obj

def build(seed=0):
    seed = int(seed)
    derived = int_hash((seed, 0))
    random.seed(derived)
    np.random.seed(derived)
    fac = CabinetDrawerBaseFactory(seed)
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

