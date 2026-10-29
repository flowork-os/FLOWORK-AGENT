# [FL_INDEX: keywords="blender_factory, procedural_3d, CabinetDoorBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CabinetDoorBaseFactory | Category: factories_geo
# Prompt: A 3D model of a tall, narrow cabinet door panel rendered from a three-quarter perspective, featuring a flat rectangular slab with a light wood-grain appearance and subtle vertical edge detailing along its front face.

"""CabinetDoorBaseFactory (textured).

Texture-enabled rewrite of `objects_blender/shelves/CabinetDoorBaseFactory.py`.
Geometry is copied verbatim from the source file; materials are assigned per
part (frame / panel[s]) using hand-crafted raw-bpy shaders translated from

``CabinetDoorBaseFactory.get_asset_params`` which runs under
``FixedSeed(int_hash((factory_seed, i)))``). The factory has NO
``finalize_assets`` method, so no wear_tear is applied.

Shader slot → registry mapping:
    frame_material  ∈ {white, black_wood_z, wood}   (plywood.py)
    panel_material  ∈ {frame_color, glass}          (plywood.py + glass.py)
        - white       -> shader_shelves_white
        - black_wood  -> shader_shelves_black_wood_z
        - wood        -> shader_shelves_wood_z
        - glass       -> shader_glass
"""
# SEED-deterministic: all random calls seeded from SEED

import colorsys
import hashlib
import math
import os
import random
from types import SimpleNamespace

import bpy
import numpy as np
from numpy.random import normal, randint, uniform


# ============================================================================
#     shaders). Translated faithfully from:
#           black_wood, black_wood_z, wood, wood_z})
# ============================================================================

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


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
# shader_shelves_black_wood / _z  (plywood.py:72, 509)
# shader_shelves_wood       / _z  (plywood.py:246, 513)
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


def _build_shelves_wood_common_trunk(nt, z_axis_texture, wave_scale):
    """Shared trunk for shader_shelves_black_wood and shader_shelves_wood.
    Returns (mix_2_factor, cr1_color, cr2_color) — the factor for the final
    color ramp plus the two branch colors used for the displacement mix.
    Faithful translation of plywood.py lines 75-165."""
    # --- branch 1: voronoi / grain lines --------------------------------
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

    # --- branch 2: wave / grain-body -------------------------------------
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

    # Musgrave substitute: stretched NoiseTexture driven off the previous
    # noise. Blender 5.0 removed ShaderNodeTexMusgrave; NoiseTexture with
    # scale 20 / detail 3 is the visual analogue used in KitchenCabinet.
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave.inputs:     musgrave.inputs["Detail"].default_value = 3.0
    if "Distortion" in musgrave.inputs: musgrave.inputs["Distortion"].default_value = 0.0
    nt.links.new(_noise_fac_output(noise), musgrave.inputs["Vector"])

    # mix_1 = Mix(RGBA, factor=default 0.5, A=musgrave, B=noise.Color)
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

    # mix_2: combine branch1 + branch2 with factor 0.6
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

    mix2_factor, cr1_color, cr2_color = _build_shelves_wood_common_trunk(
        nt, z_axis_texture, params["wave_scale"]
    )

    # --- final 3-stop ramp: dark / gray / rgb ---------------------------
    cr_final = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr_final.inputs.get("Fac") or cr_final.inputs[0]
    nt.links.new(mix2_factor, fac_in)
    cr_final.color_ramp.elements.new(0.5)
    dark = params["dark_scale"]; gray = params["gray_scale"]
    color_scale = (*params["rgb"], 1.0)
    cr_final.color_ramp.elements[0].position = 0.15
    cr_final.color_ramp.elements[0].color = (dark, dark, dark, 1.0)
    cr_final.color_ramp.elements[1].position = 0.5
    cr_final.color_ramp.elements[1].color = (gray, gray, gray, 1.0)
    cr_final.color_ramp.elements[2].position = 1.0
    cr_final.color_ramp.elements[2].color = color_scale

    # --- displacement: mix_3(cr1, cr2, factor=0.004) -> Displacement ---
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


def make_shelves_wood(name="ShelvesWood", params=None, z_axis_texture=False):
    """shader_shelves_wood (+ _z variant) — blond plywood."""

    if params is None:
        params = _sample_wood_params()
    mat = _new_material(name)
    nt = mat.node_tree

    mix2_factor, cr1_color, cr2_color = _build_shelves_wood_common_trunk(
        nt, z_axis_texture, params["wave_scale"]
    )

    cr_final = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr_final.inputs.get("Fac") or cr_final.inputs[0]
    nt.links.new(mix2_factor, fac_in)
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
# shader_glass  (ceramic/glass.py:15) + get_glass_color
# ----------------------------------------------------------------------------
def _get_glass_color():
    if np.random.uniform(0, 1) < 0.5:
        return (1.0, 1.0, 1.0, 1.0)
    h = float(np.random.uniform(0, 1))
    s = float(np.random.uniform(0.05, 0.25))
    return hsv2rgba([h, s, 1.0])


def make_glass(name="Glass", color=None):
    """shader_glass: GlassBSDF, IOR=1.5, Roughness=0.02. Uses a tinted
    material.diffuse_color (surface.shaderfunc_to_material). We preserve
    the glass BSDF and also set the material diffuse_color for preview."""

    if color is None:
        color = _get_glass_color()
    mat = _new_material(name)
    nt = mat.node_tree
    glass = nt.nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["Roughness"].default_value = 0.02
    glass.inputs["IOR"].default_value = 1.5
    # via surface.shaderfunc_to_material passing color into the material's
    # diffuse_color property (used as viewport / preview color).
    try:
        mat.diffuse_color = color
    except Exception:
        pass
    _connect_output(nt, glass)
    return mat


def _get_door_material(key):
    """Mirror doors.py get_material_func dispatch (frame branches use
    non-z variants; panel branches use _z variants for wood shaders)."""

    if key == "white":
        return make_shelves_white("PanelWhite")
    if key == "black_wood":
        return make_shelves_black_wood_z("PanelBlackWoodZ")
    if key == "wood":
        return make_shelves_wood_z("PanelWoodZ")
    if key == "glass":
        return make_glass("PanelGlass")
    return make_shelves_white("PanelFallback")


def _get_frame_material(key):
    """Frame branch uses the non-z variants per doors.py:1219."""

    if key == "white":
        return make_shelves_white("FrameWhite")
    if key == "black_wood":
        return make_shelves_black_wood("FrameBlackWood")
    if key == "wood":
        return make_shelves_wood("FrameWood")
    return make_shelves_white("FrameFallback")


# ============================================================================
# === Geometry runtime stubs (copied verbatim from
#     objects_blender/shelves/CabinetDoorBaseFactory.py) ====================
# ============================================================================

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

# Material stubs present in the original geometry file are replaced by the
# real shader makers defined at the top of this script. The get_material_func
# method of the factory class below uses _get_frame_material / _get_door_material
# directly, so these shader stubs are unused.

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
    CombineXYZ = 'ShaderNodeCombineXYZ'
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
    RealizeInstances = 'GeometryNodeRealizeInstances'
    SetMaterial = 'GeometryNodeSetMaterial'
    SetPosition = 'GeometryNodeSetPosition'
    SubdivideMesh = 'GeometryNodeSubdivideMesh'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'


# ── Factory-specific nodegroups + build ────────────────────────────────────────

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
            "Vertices": 64,
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
            "Vertices X": 5,
            "Vertices Y": 5,
            "Vertices Z": 5,
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
        input_kwargs={
            "Geometry": transform_4,
            "Material": kwargs["material"][0],
        },
    )

    combine_xyz_7 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": add, "Y": add_1, "Z": add_2}
    )

    cube_1 = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": combine_xyz_7,
            "Vertices X": 5,
            "Vertices Y": 5,
            "Vertices Z": 5,
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
        input_kwargs={
            "Geometry": transform_7,
            "Material": kwargs["material"][1],
        },
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
            "Vertices X": 5,
            "Vertices Y": 5,
            "Vertices Z": 5,
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
        input_kwargs={
            "Geometry": transform_4,
            "Material": kwargs["material"][0],
        },
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

    # transform_1 = nw.new_node(Nodes.FlipFaces, input_kwargs={'Mesh': transform_1})

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
            nodegroup_mid_board(material=kwargs["panel_material"]).name,
            input_kwargs={
                "height": door_height,
                "thickness": mid_board_thickness,
                "width": door_width,
            },
        )
    else:
        mid_board = nw.new_node(
            nodegroup_mid_board_001(material=kwargs["panel_material"]).name,
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
        frame.append(transform_5)

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

    join_geometry_1 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": frame + [knob_handle]}
    )

    set_material_3 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": join_geometry_1,
            "Material": kwargs["frame_material"],
        },
    )

    geos = [set_material_3, mid_board.outputs["Geometry"]]
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

    if kwargs["door_left_hinge"]:
        transform_1 = nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": transform_1})

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
        self.params = {}

    def get_asset_params(self, i=0):
        params = self.params.copy()
        if params.get("door_height", None) is None:
            params["door_height"] = uniform(0.7, 2.2)
        if params.get("door_width", None) is None:
            params["door_width"] = uniform(0.3, 0.4)
        if params.get("edge_thickness_1", None) is None:
            params["edge_thickness_1"] = uniform(0.01, 0.018)
        if params.get("edge_width", None) is None:
            params["edge_width"] = uniform(0.03, 0.05)
        if params.get("edge_thickness_2", None) is None:
            params["edge_thickness_2"] = uniform(0.005, 0.008)
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
                ["white", "black_wood", "wood"], p=[0.5, 0.2, 0.3]
            )
        if params.get("panel_material", None) is None:
            if params["has_mid_ramp"]:
                lower_mat = np.random.choice(
                    [params["frame_material"], "glass"], p=[0.7, 0.3]
                )
                upper_mat = np.random.choice([lower_mat, "glass"], p=[0.6, 0.4])
                params["panel_material"] = [lower_mat, upper_mat]
            else:
                params["panel_material"] = [params["frame_material"]]

        params = self.get_material_func(params)
        return params

    def get_material_func(self, params, randomness=True):
        # Frame uses the non-z wood shader variants, panels use the _z variants
        # for wood shaders and plain glass for the "glass" panel choice.
        params["frame_material"] = _get_frame_material(params["frame_material"])

        materials = []
        if not isinstance(params["panel_material"], list):
            params["panel_material"] = [params["panel_material"]]
        for mat_key in params["panel_material"]:
            materials.append(_get_door_material(mat_key))
        # nodegroup_mid_board uses material[0] and material[1]; if only one
        # panel material is sampled (has_mid_ramp=False path is handled by
        # original code makes the list 2-long for the has_mid_ramp path via
        # get_asset_params). Pad to length 2 defensively so material[1] exists
        # for the has_mid_ramp=True nodegroup path.
        if len(materials) < 2:
            materials = materials + [materials[0]]
        params["panel_material"] = materials
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
            obj, geometry_door_nodes, apply=True, attributes=[], input_kwargs=obj_params
        )
        tagging.tag_system.relabel_obj(obj)

        if params.get("ret_params", False):
            return obj, obj_params

        return obj

def build(seed=0):
    seed = int(seed)
    derived = int_hash((seed, 0))
    random.seed(derived)
    np.random.seed(derived)
    fac = CabinetDoorBaseFactory(seed)
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

SEED = int(os.environ.get("SEED", "0"))
build(SEED)
