# [FL_INDEX: keywords="blender_factory, procedural_3d, LargeShelfFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LargeShelfFactory | Category: factories_geo
# Prompt: A 3D model of a tall freestanding bookshelf rendered from a three-quarter perspective, featuring a simple rectangular frame with multiple horizontal shelves evenly spaced from top to bottom, creating open storage tiers with a clean white appearance.

"""Texture-enabled conversion of objects_blender/shelves/LargeShelfFactory.py.

Geometry is copied verbatim from the geometry-only source. Materials are
faithful raw-bpy ports of the three shelf shaders from

    - shader_shelves_white         (simple diffuse white Principled BSDF)
    - shader_shelves_black_wood    (layered noise+voronoi wood grain,
                                    dark/gray/red color ramp, displacement)
    - shader_shelves_wood          (same topology as black_wood, with
                                    bright/mid/dark HSV color ramp)
    - *_z variants — same shader with z-axis mapping rather than y-axis

The original uses `Nodes.MusgraveTexture` which was removed in Blender 5.0;
we substitute `ShaderNodeTexNoise` with matched Scale/Detail inputs — the
closest shader-graph equivalent available in 5.0. All other node topology,
color-ramp positions, mix factors, and displacement scales are preserved

LargeShelfFactory does not use wear_tear (no finalize_assets override), so
scratch/edge-wear post-processing is intentionally omitted.

Material sampling is done in Phase 1 under the raw SEED, matching the spec's
"materials under raw factory_seed" convention. The 40/30/30 frame_material
mix (white / black_wood / wood) comes from
`large_shelf.py:LargeShelfBaseFactory.get_asset_params()`.
"""
# SEED-deterministic: all random calls seeded from SEED

import hashlib
import math
import random
import os
import colorsys
from types import SimpleNamespace

import bpy
import numpy as np
from numpy.random import normal, randint, uniform


# ============================================================================
# === Inlined material library — raw-bpy port of plywood.py shaders ==========
# ============================================================================
# Sources translated faithfully from:
#     - shader_shelves_white
#     - shader_shelves_black_wood  (+ _z variant = z_axis_texture=True)
#     - shader_shelves_wood        (+ _z variant)
#
# Sampler call order inside `LargeShelfBaseFactory.get_asset_params` is:
#   1. frame_material string (one of white/black_wood/wood, p=[0.4,0.3,0.3])
#   2. board_material string (copied from frame_material)
#   3. frame_material shader params (z_axis=True)
#   4. board_material shader params (z_axis=False)
# We mirror this call order exactly so numpy.random consumption matches.
# ============================================================================


def _seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)


def _hsv2rgba(hsv):
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
    """Set Principled BSDF inputs with Blender-version-tolerant socket names."""

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


# ---------------------------------------------------------------------------
# Samplers (mirror plywood.py:shader_shelves_*_sampler exactly)
# ---------------------------------------------------------------------------

def shader_shelves_white_sampler():
    params = {}
    v = uniform(0.7, 1.0)
    params["rgb"] = [
        v * (1.0 + normal(0, 0.005)),
        v * (1.0 + normal(0, 0.005)),
        v * (1.0 + normal(0, 0.005)),
    ]
    params["roughness"] = uniform(0.7, 1.0)
    return params


def shader_shelves_black_wood_sampler():
    params = {}
    params["wave_scale"] = uniform(1.0, 3.0)
    params["dark_scale"] = uniform(0.0, 0.01)
    params["gray_scale"] = uniform(0.01, 0.03)
    params["rgb"] = [uniform(0.015, 0.035), uniform(0.0, 0.01), uniform(0.0, 0.01)]
    params["roughness"] = uniform(0.75, 1.0)
    return params


def shader_shelves_wood_sampler():
    params = {}
    params["bright_hsv"] = [uniform(0.03, 0.09), uniform(0.5, 0.7), uniform(0.7, 1.0)]
    params["mid_hsv"]    = [uniform(0.02, 0.06), uniform(0.6, 1.0), uniform(0.3, 0.6)]
    params["dark_hsv"]   = [uniform(0.03, 0.05), uniform(0.6, 1.0), uniform(0.1, 0.3)]
    params["wave_scale"] = uniform(1.0, 3.0)
    params["roughness"]  = uniform(0.75, 1.0)
    return params


# ---------------------------------------------------------------------------
# Material constructors (raw-bpy ports of plywood.py shaders)
# ---------------------------------------------------------------------------

def make_shelves_white(name="WhitePlywood", params=None) -> bpy.types.Material:
    """Port of plywood.py:shader_shelves_white.

    Simple: just a Principled BSDF with rgb base color and roughness.
    """

    if params is None:
        params = shader_shelves_white_sampler()
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    base_color = (*params["rgb"], 1.0)
    _set_principled(bsdf, **{"Base Color": base_color,
                              "Roughness": params["roughness"]})
    _connect_output(nt, bsdf)
    return mat


def _build_plywood_grain(nt, wave_scale_tuple, mapping_scale):
    """Build the shared black_wood / wood grain sub-graph.

    Returns (colorramp_1_color_out, mix_2_color_out, mix_3_color_out).

    Faithful to plywood.py:shader_shelves_wood node topology. The only
    substitution is Blender 5.0 compatible: the `MusgraveTexture` node
    (removed in 5.0) is replaced with a stretched `NoiseTexture` using the
    """

    tex_coord_1 = nt.nodes.new("ShaderNodeTexCoord")
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = mapping_scale
    nt.links.new(tex_coord_1.outputs["Object"], mapping_1.inputs["Vector"])

    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise_1.inputs:
        noise_1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise_1.inputs:
        noise_1.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = 40.0
    # Feed voronoi vector from noise fac (matches plywood.py which uses
    # `noise_texture_1.outputs["Fac"]` as the Vector input).
    nt.links.new(_noise_fac_output(noise_1), voronoi.inputs["Vector"])

    # ColorRamp 1 — steep threshold on voronoi color
    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(voronoi.outputs["Color"] if "Color" in voronoi.outputs else voronoi.outputs[1],
                 cr1.inputs[0])
    cr1.color_ramp.elements[0].position = 0.0864
    cr1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr1.color_ramp.elements[1].position = 0.1091
    cr1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Second branch — wave-scale noise and musgrave-substitute
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = wave_scale_tuple
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # Substitute for ShaderNodeTexMusgrave (removed in Blender 5.0).
    # plywood.py uses: Scale=20, Detail=3, Vector=noise.outputs["Fac"].
    # A stretched NoiseTexture with the same Scale/Detail gives the closest
    # available 5.0 equivalent. Distortion=0 to keep it one-dimensional.
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave.inputs:
        musgrave.inputs["Detail"].default_value = 3.0
    if "Distortion" in musgrave.inputs:
        musgrave.inputs["Distortion"].default_value = 0.0
    nt.links.new(_noise_fac_output(noise), musgrave.inputs["Vector"])

    # Mix 1 — RGBA mix, Fac from default 0.5 (plywood.py passes no Fac, so
    # uses Mix default). A = musgrave fac, B = noise color.
    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    # inputs[0]=Factor (default 0.5), [6]=A, [7]=B for RGBA mix.
    nt.links.new(_noise_fac_output(musgrave), mix_1.inputs[6])
    # noise has both Fac (float) and Color outputs; plywood.py uses Color.
    noise_color_out = noise.outputs.get("Color") or noise.outputs[1]
    nt.links.new(noise_color_out, mix_1.inputs[7])

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    # mix_1.outputs[2] is the RGBA mix Result socket.
    nt.links.new(mix_1.outputs[2], cr2.inputs[0])
    cr2.color_ramp.elements[0].position = 0.0818
    cr2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr2.color_ramp.elements[1].position = 0.8500
    cr2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Mix 2 — Fac=0.6, A=cr1.Color, B=cr2.Color
    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"):
        mix_2.data_type = "RGBA"
    mix_2.inputs[0].default_value = 0.6
    nt.links.new(cr1.outputs["Color"], mix_2.inputs[6])
    nt.links.new(cr2.outputs["Color"], mix_2.inputs[7])

    # Mix 3 — Fac=0.004, same inputs as Mix 2 (used as displacement height)
    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"):
        mix_3.data_type = "RGBA"
    mix_3.inputs[0].default_value = 0.004
    nt.links.new(cr1.outputs["Color"], mix_3.inputs[6])
    nt.links.new(cr2.outputs["Color"], mix_3.inputs[7])

    return cr1, mix_2, mix_3


def make_shelves_black_wood(name="BlackPlywood", params=None,
                            z_axis_texture=False) -> bpy.types.Material:
    """Port of plywood.py:shader_shelves_black_wood (+ _z variant).

    Faithful re-creation with the Blender 5.0 Musgrave substitution.
    """

    if params is None:
        params = shader_shelves_black_wood_sampler()
    mat = _new_material(name)
    nt = mat.node_tree

    wave_scale_val = params.get("wave_scale", 2.0)
    if z_axis_texture:
        wave_scale_tuple = (wave_scale_val, wave_scale_val, 0.1)
        mapping_scale = (0.1, 0.1, 2.0)
    else:
        wave_scale_tuple = (wave_scale_val, 0.1, 0.1)
        mapping_scale = (0.1, 2.0, 2.0)

    cr1, mix_2, mix_3 = _build_plywood_grain(nt, wave_scale_tuple, mapping_scale)

    # Base color — 3-stop ramp (dark / gray / color)
    dark_scale = params.get("dark_scale", 0.005)
    gray_scale = params.get("gray_scale", 0.02)
    rgb = params.get("rgb", [0.02, 0.002, 0.002])

    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix_2.outputs[2], cr_base.inputs[0])
    # ColorRamp starts with 2 stops; add a third.
    cr_base.color_ramp.elements.new(0)
    cr_base.color_ramp.elements[0].position = 0.15
    cr_base.color_ramp.elements[0].color = (dark_scale, dark_scale, dark_scale, 1.0)
    cr_base.color_ramp.elements[1].position = 0.5
    cr_base.color_ramp.elements[1].color = (gray_scale, gray_scale, gray_scale, 1.0)
    cr_base.color_ramp.elements[2].position = 1.0
    cr_base.color_ramp.elements[2].color = (rgb[0], rgb[1], rgb[2], 1.0)

    # Displacement from mix_3
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(cr_base.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, **{"Roughness": params.get("roughness", 0.9)})
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_shelves_wood(name="BlondePlywood", params=None,
                      z_axis_texture=False) -> bpy.types.Material:
    """Port of plywood.py:shader_shelves_wood (+ _z variant).

    Same topology as black_wood but with bright/mid/dark HSV color ramp.
    """

    if params is None:
        params = shader_shelves_wood_sampler()
    mat = _new_material(name)
    nt = mat.node_tree

    wave_scale_val = params.get("wave_scale", 2.0)
    if z_axis_texture:
        wave_scale_tuple = (wave_scale_val, wave_scale_val, 0.1)
        mapping_scale = (0.1, 0.1, 2.0)
    else:
        wave_scale_tuple = (wave_scale_val, 0.1, 0.1)
        mapping_scale = (0.1, 2.0, 2.0)

    cr1, mix_2, mix_3 = _build_plywood_grain(nt, wave_scale_tuple, mapping_scale)

    bright_hsv = params.get("bright_hsv", [0.068, 0.665, 0.805])
    mid_hsv    = params.get("mid_hsv",    [0.042, 0.853, 0.447])
    dark_hsv   = params.get("dark_hsv",   [0.043, 0.882, 0.183])

    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix_2.outputs[2], cr_base.inputs[0])
    cr_base.color_ramp.elements.new(0)
    cr_base.color_ramp.elements[0].position = 0.02
    cr_base.color_ramp.elements[0].color = _hsv2rgba(dark_hsv)
    cr_base.color_ramp.elements[1].position = 0.11
    cr_base.color_ramp.elements[1].color = _hsv2rgba(mid_hsv)
    cr_base.color_ramp.elements[2].position = 0.8
    cr_base.color_ramp.elements[2].color = _hsv2rgba(bright_hsv)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(cr_base.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, **{"Roughness": params.get("roughness", 0.9)})
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_frame_material(kind: str, slot_name: str) -> bpy.types.Material:
    """Frame material uses *_z-axis variants per plywood.py:shader_shelves_*_z."""

    if kind == "white":
        return make_shelves_white(name=slot_name,
                                  params=shader_shelves_white_sampler())
    if kind == "black_wood":
        p = shader_shelves_black_wood_sampler()
        return make_shelves_black_wood(name=slot_name, params=p, z_axis_texture=True)
    if kind == "wood":
        p = shader_shelves_wood_sampler()
        return make_shelves_wood(name=slot_name, params=p, z_axis_texture=True)
    raise ValueError(f"unknown frame material kind: {kind!r}")


def make_board_material(kind: str, slot_name: str) -> bpy.types.Material:
    """Board material uses non-z variants per plywood.py:shader_shelves_*."""

    if kind == "white":
        return make_shelves_white(name=slot_name,
                                  params=shader_shelves_white_sampler())
    if kind == "black_wood":
        p = shader_shelves_black_wood_sampler()
        return make_shelves_black_wood(name=slot_name, params=p, z_axis_texture=False)
    if kind == "wood":
        p = shader_shelves_wood_sampler()
        return make_shelves_wood(name=slot_name, params=p, z_axis_texture=False)
    raise ValueError(f"unknown board material kind: {kind!r}")


# ============================================================================
# === End of inlined material library ========================================
# ============================================================================


# ── Basic helpers (copied verbatim from objects_blender/shelves header) ─────

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
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
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


# ── NodeWrangler (copied verbatim from objects_blender header) ──────────────

def ng_inputs(ng):
    return {s.name: s for s in ng.interface.items_tree if s.in_out == "INPUT"}


def ng_outputs(ng):
    return {s.name: s for s in ng.interface.items_tree if s.in_out == "OUTPUT"}


def _sock_type_for(v):
    if isinstance(v, bool):
        return "NodeSocketBool"
    if isinstance(v, int):
        return "NodeSocketInt"
    if isinstance(v, float):
        return "NodeSocketFloat"
    if isinstance(v, (tuple, list, np.ndarray)):
        n = len(v)
        if n == 3:
            return "NodeSocketVector"
        if n == 4:
            return "NodeSocketColor"
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


# ── to_nodegroup decorator + add_geomod ─────────────────────────────────────

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

# ── Stubs: tagging / butil / AssetFactory ──────────────────────────────────

tagging = SimpleNamespace(
    tag_system=SimpleNamespace(
        relabel_obj=lambda o: o,
        relabel_objects=lambda o: o,
    ),
    tag_object=lambda *a, **k: None,
    tag_nodegroup=lambda nw, geo, *a, **k: geo,
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


# ── Nodes class (from original factory) ────────────────────────────────────

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


# ── Factory-specific nodegroups + build (verbatim from objects_blender) ────

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
            ("NodeSocketFloat", "division_thickness", 0.5000),
            ("NodeSocketFloat", "width", 0.5000),
            ("NodeSocketFloat", "depth", 0.5000),
            ("NodeSocketFloat", "screw_width_gap", 0.5000),
            ("NodeSocketFloat", "screw_depth_gap", 0.0000),
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
        Nodes.Transform, input_kwargs={"Geometry": cylinder.outputs["Mesh"]}
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["width"]},
        attrs={"operation": "MULTIPLY"},
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply, 1: group_input.outputs["screw_width_gap"]},
        attrs={"operation": "SUBTRACT"},
    )

    multiply_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["depth"]},
        attrs={"operation": "MULTIPLY"},
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["screw_width_gap"], 1: 0.0000}
    )

    subtract_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_1, 1: add},
        attrs={"operation": "SUBTRACT"},
    )

    multiply_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: subtract_1, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    multiply_3 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["division_thickness"], 1: -0.5000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": multiply_2, "Z": multiply_3}
    )

    transform_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Translation": combine_xyz},
    )

    combine_xyz_4 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": subtract_1, "Z": multiply_3}
    )

    transform_6 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": transform, "Translation": combine_xyz_4},
    )

    join_geometry_2 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_1, transform_6]}
    )

    transform_4 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": join_geometry_2, "Scale": (-1.0000, 1.0000, 1.0000)},
    )

    join_geometry_3 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_4, join_geometry_2]}
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_3}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": realize_instances},
        attrs={"is_active_output": True},
    )


@node_utils.to_nodegroup(
    "nodegroup_division_board", singleton=False, type="GeometryNodeTree"
)
def nodegroup_division_board(nw: NodeWrangler, material, tag_support=False):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "thickness", 0.0000),
            ("NodeSocketFloat", "width", 0.0000),
            ("NodeSocketFloat", "depth", 0.0000),
            ("NodeSocketFloat", "z_translation", 0.0000),
            ("NodeSocketFloat", "x_translation", 0.0000),
            ("NodeSocketFloat", "screw_depth", 0.0000),
            ("NodeSocketFloat", "screw_radius", 0.0000),
            ("NodeSocketFloat", "screw_width_gap", 0.0000),
            ("NodeSocketFloat", "screw_depth_gap", 0.0000),
        ],
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={
            "X": group_input.outputs["width"],
            "Y": group_input.outputs["depth"],
            "Z": group_input.outputs["thickness"],
        },
    )

    if tag_support:
        cube = nw.new_node(
            nodegroup_tagged_cube().name, input_kwargs={"Size": combine_xyz}
        )
    else:
        cube = nw.new_node(
            Nodes.MeshCube,
            input_kwargs={
                "Size": combine_xyz,
                "Vertices X": 2,
                "Vertices Y": 2,
                "Vertices Z": 2,
            },
        )

    screw_head = nw.new_node(
        nodegroup_screw_head().name,
        input_kwargs={
            "Depth": group_input.outputs["screw_depth"],
            "Radius": group_input.outputs["screw_radius"],
            "division_thickness": group_input.outputs["thickness"],
            "width": group_input.outputs["width"],
            "depth": group_input.outputs["depth"],
            "screw_width_gap": group_input.outputs["screw_width_gap"],
            "screw_depth_gap": group_input.outputs["screw_depth_gap"],
        },
    )

    join_geometry = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [cube, screw_head]}
    )

    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={
            "X": group_input.outputs["x_translation"],
            "Z": group_input.outputs["z_translation"],
        },
    )

    transform = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz_1},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform},
        attrs={"is_active_output": True},
    )


@node_utils.to_nodegroup(
    "nodegroup_bottom_board", singleton=False, type="GeometryNodeTree"
)
def nodegroup_bottom_board(nw: NodeWrangler):
    # Code generated using version 2.6.4 of the node_transpiler

    group_input = nw.new_node(
        Nodes.GroupInput,
        expose_input=[
            ("NodeSocketFloat", "thickness", 0.0000),
            ("NodeSocketFloat", "depth", 0.5000),
            ("NodeSocketFloat", "y_gap", 0.5000),
            ("NodeSocketFloat", "x_translation", 0.0000),
            ("NodeSocketFloat", "height", 0.5000),
            ("NodeSocketFloat", "width", 0.0000),
        ],
    )

    add = nw.new_node(
        Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: 0.0000}
    )

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={
            "X": group_input.outputs["width"],
            "Y": group_input.outputs["thickness"],
            "Z": add,
        },
    )

    cube = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": combine_xyz,
            "Vertices X": 2,
            "Vertices Y": 2,
            "Vertices Z": 2,
        },
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: group_input.outputs["depth"]},
        attrs={"operation": "MULTIPLY"},
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply, 1: group_input.outputs["y_gap"]},
        attrs={"operation": "SUBTRACT"},
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: add}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={
            "X": group_input.outputs["x_translation"],
            "Y": subtract,
            "Z": multiply_1,
        },
    )

    transform = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_1}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform},
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
            "Vertices X": 2,
            "Vertices Y": 2,
            "Vertices Z": 2,
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
            ("NodeSocketFloat", "x_translation", 0.0000),
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
            "Vertices X": 2,
            "Vertices Y": 2,
            "Vertices Z": 2,
        },
    )

    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: add_2, 1: 0.5000}, attrs={"operation": "MULTIPLY"}
    )

    combine_xyz_1 = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={"X": group_input.outputs["x_translation"], "Z": multiply},
    )

    transform = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_1}
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform},
        attrs={"is_active_output": True},
    )


def geometry_nodes(nw: NodeWrangler, **kwargs):
    # Code generated using version 2.6.4 of the node_transpiler

    side_board_thickness = nw.new_node(Nodes.Value, label="side_board_thickness")
    side_board_thickness.outputs[0].default_value = kwargs["side_board_thickness"]

    shelf_depth = nw.new_node(Nodes.Value, label="shelf_depth")
    shelf_depth.outputs[0].default_value = kwargs["shelf_depth"]

    add = nw.new_node(Nodes.Math, input_kwargs={0: shelf_depth, 1: 0.0040})

    shelf_height = nw.new_node(Nodes.Value, label="shelf_height")
    shelf_height.outputs[0].default_value = kwargs["shelf_height"]

    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: shelf_height, 1: 0.0020})
    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: shelf_height, 1: -0.0010})
    side_boards = []

    for x in kwargs["side_board_x_translation"]:
        side_board_x_translation = nw.new_node(
            Nodes.Value, label="side_board_x_translation"
        )
        side_board_x_translation.outputs[0].default_value = x

        side_board = nw.new_node(
            nodegroup_side_board().name,
            input_kwargs={
                "board_thickness": side_board_thickness,
                "depth": add,
                "height": add_1,
                "x_translation": side_board_x_translation,
            },
        )
        side_boards.append(side_board)

    shelf_width = nw.new_node(Nodes.Value, label="shelf_width")
    shelf_width.outputs[0].default_value = kwargs["shelf_width"]

    backboard_thickness = nw.new_node(Nodes.Value, label="backboard_thickness")
    backboard_thickness.outputs[0].default_value = kwargs["backboard_thickness"]

    add_side = nw.new_node(
        Nodes.Math, input_kwargs={0: shelf_width, 1: kwargs["side_board_thickness"] * 2}
    )
    back_board = nw.new_node(
        nodegroup_back_board().name,
        input_kwargs={
            "width": add_side,
            "thickness": backboard_thickness,
            "height": add_2,
            "depth": shelf_depth,
        },
    )

    bottom_board_y_gap = nw.new_node(Nodes.Value, label="bottom_board_y_gap")
    bottom_board_y_gap.outputs[0].default_value = kwargs["bottom_board_y_gap"]

    bottom_board_height = nw.new_node(Nodes.Value, label="bottom_board_height")
    bottom_board_height.outputs[0].default_value = kwargs["bottom_board_height"]

    bottom_boards = []
    for i in range(len(kwargs["shelf_cell_width"])):
        bottom_gap_x_translation = nw.new_node(
            Nodes.Value, label="bottom_gap_x_translation"
        )
        bottom_gap_x_translation.outputs[0].default_value = kwargs[
            "bottom_gap_x_translation"
        ][i]

        shelf_cell_width = nw.new_node(Nodes.Value, label="shelf_cell_width")
        shelf_cell_width.outputs[0].default_value = kwargs["shelf_cell_width"][i]

        bottomboard = nw.new_node(
            nodegroup_bottom_board().name,
            input_kwargs={
                "thickness": side_board_thickness,
                "depth": shelf_depth,
                "y_gap": bottom_board_y_gap,
                "x_translation": bottom_gap_x_translation,
                "height": bottom_board_height,
                "width": shelf_cell_width,
            },
        )

        bottom_boards.append(bottomboard)

    join_geometry = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={"Geometry": [back_board] + side_boards + bottom_boards},
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

    division_board_thickness = nw.new_node(
        Nodes.Value, label="division_board_thickness"
    )
    division_board_thickness.outputs[0].default_value = kwargs[
        "division_board_thickness"
    ]

    division_boards = []
    for i in range(len(kwargs["shelf_cell_width"])):
        for j in range(len(kwargs["division_board_z_translation"])):
            division_board_z_translation = nw.new_node(
                Nodes.Value, label="division_board_z_translation"
            )
            division_board_z_translation.outputs[0].default_value = kwargs[
                "division_board_z_translation"
            ][j]

            division_board_x_translation = nw.new_node(
                Nodes.Value, label="division_board_x_translation"
            )
            division_board_x_translation.outputs[0].default_value = kwargs[
                "division_board_x_translation"
            ][i]

            shelf_cell_width = nw.new_node(Nodes.Value, label="shelf_cell_width")
            shelf_cell_width.outputs[0].default_value = kwargs["shelf_cell_width"][i]

            screw_depth_head = nw.new_node(Nodes.Value, label="screw_depth_head")
            screw_depth_head.outputs[0].default_value = kwargs["screw_depth_head"]

            screw_head_radius = nw.new_node(Nodes.Value, label="screw_head_radius")
            screw_head_radius.outputs[0].default_value = kwargs["screw_head_radius"]

            screw_width_gap = nw.new_node(Nodes.Value, label="screw_width_gap")
            screw_width_gap.outputs[0].default_value = kwargs["screw_width_gap"]

            screw_depth_gap = nw.new_node(Nodes.Value, label="screw_depth_gap")
            screw_depth_gap.outputs[0].default_value = kwargs["screw_depth_gap"]

            division_board = nw.new_node(
                nodegroup_division_board(
                    material=kwargs["board_material"],
                    tag_support=kwargs.get("tag_support", False),
                ).name,
                input_kwargs={
                    "thickness": division_board_thickness,
                    "width": shelf_cell_width,
                    "depth": shelf_depth,
                    "z_translation": division_board_z_translation,
                    "x_translation": division_board_x_translation,
                    "screw_depth": screw_depth_head,
                    "screw_radius": screw_head_radius,
                    "screw_width_gap": screw_width_gap,
                    "screw_depth_gap": screw_depth_gap,
                },
            )
            division_boards.append(division_board)

    attach_thickness = nw.new_node(Nodes.Value, label="attach_thickness")
    attach_thickness.outputs[0].default_value = kwargs["attach_thickness"]

    attach_length = nw.new_node(Nodes.Value, label="attach_length")
    attach_length.outputs[0].default_value = kwargs["attach_length"]

    attach_z_translation = nw.new_node(Nodes.Value, label="attach_z_translation")
    attach_z_translation.outputs[0].default_value = kwargs["attach_z_translation"]

    attach_gap = nw.new_node(Nodes.Value, label="attach_gap")
    attach_gap.outputs[0].default_value = kwargs["attach_gap"]

    attach_width = nw.new_node(Nodes.Value, label="attach_width")
    attach_width.outputs[0].default_value = kwargs["attach_width"]

    join_geometry_k = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": division_boards}
    )

    set_material_1 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": join_geometry_k,
            "Material": kwargs["board_material"],
        },
    )

    join_geometry_3 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [set_material, set_material_1]}
    )

    realize_instances_3 = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_3}
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


class LargeShelfBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(LargeShelfBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = {}

    def sample_params(self):
        return self.params.copy()

    def get_asset_params(self, i=0):
        params = self.sample_params()
        if params.get("shelf_depth", None) is None:
            params["shelf_depth"] = np.clip(normal(0.26, 0.03), 0.18, 0.36)
        if params.get("side_board_thickness", None) is None:
            params["side_board_thickness"] = np.clip(normal(0.02, 0.002), 0.015, 0.025)
        if params.get("back_board_thickness", None) is None:
            params["backboard_thickness"] = 0.01
        if params.get("bottom_board_y_gap", None) is None:
            params["bottom_board_y_gap"] = uniform(0.01, 0.05)
        if params.get("bottom_board_height", None) is None:
            params["bottom_board_height"] = np.clip(
                normal(0.083, 0.01), 0.05, 0.11
            ) * np.random.choice([1.0, 0.0], p=[0.8, 0.2])
        if params.get("division_board_thickness", None) is None:
            params["division_board_thickness"] = np.clip(
                normal(0.02, 0.002), 0.015, 0.025
            )
        if params.get("screw_depth_head", None) is None:
            params["screw_depth_head"] = uniform(0.001, 0.004)
        if params.get("screw_head_radius", None) is None:
            params["screw_head_radius"] = uniform(0.001, 0.004)
        if params.get("screw_width_gap", None) is None:
            params["screw_width_gap"] = uniform(0.0, 0.02)
        if params.get("screw_depth_gap", None) is None:
            params["screw_depth_gap"] = uniform(0.025, 0.06)
        if params.get("attach_length", None) is None:
            params["attach_length"] = uniform(0.05, 0.1)
        if params.get("attach_width", None) is None:
            params["attach_width"] = uniform(0.01, 0.025)
        if params.get("attach_thickness", None) is None:
            params["attach_thickness"] = uniform(0.002, 0.005)
        if params.get("attach_gap", None) is None:
            params["attach_gap"] = uniform(0.0, 0.05)
        if params.get("shelf_cell_width", None) is None:
            num_h_cells = randint(1, 4)
            shelf_cell_width = []
            for i in range(num_h_cells):
                shelf_cell_width.append(
                    np.random.choice([0.76, 0.36], p=[0.5, 0.5])
                    * np.clip(normal(1.0, 0.1), 0.75, 1.25)
                )
            params["shelf_cell_width"] = shelf_cell_width
        if params.get("shelf_cell_height", None) is None:
            num_v_cells = randint(3, 8)
            shelf_cell_height = []
            for i in range(num_v_cells):
                shelf_cell_height.append(0.3 * np.clip(normal(1.0, 0.1), 0.75, 1.25))
            params["shelf_cell_height"] = shelf_cell_height

        params = self.update_translation_params(params)
        # Materials are already bound at module level (MAT_FRAME / MAT_BOARD)
        # via Phase 1 sampling; we inject them here so the geometry_nodes
        # SetMaterial nodes receive real bpy.types.Material objects.
        params["frame_material"] = MAT_FRAME
        params["board_material"] = MAT_BOARD
        params["tag_support"] = True
        return params

    def update_translation_params(self, params):
        cell_widths = params["shelf_cell_width"]
        cell_heights = params["shelf_cell_height"]
        side_thickness = params["side_board_thickness"]
        div_thickness = params["division_board_thickness"]

        # get shelf_width and shelf_height
        width = (len(cell_widths) - 1) * side_thickness * 2 + (
            len(cell_widths) - 1
        ) * 0.001
        height = (len(cell_heights) + 1) * div_thickness + params["bottom_board_height"]
        for w in cell_widths:
            width += w
        for h in cell_heights:
            height += h

        params["shelf_width"] = width
        params["shelf_height"] = height
        params["attach_z_translation"] = height - div_thickness

        # get side_board_x_translation
        dist = -(width + side_thickness) / 2.0
        side_board_x_translation = [dist]

        for w in cell_widths:
            dist += side_thickness + w
            side_board_x_translation.append(dist)
            dist += side_thickness + 0.001
            side_board_x_translation.append(dist)
        side_board_x_translation = side_board_x_translation[:-1]

        # get division_board_z_translation
        dist = params["bottom_board_height"] + div_thickness / 2.0
        division_board_z_translation = [dist]
        for h in cell_heights:
            dist += h + div_thickness
            division_board_z_translation.append(dist)

        # get division_board_x_translation
        division_board_x_translation = []
        for i in range(len(cell_widths)):
            division_board_x_translation.append(
                (side_board_x_translation[2 * i] + side_board_x_translation[2 * i + 1])
                / 2.0
            )

        params["side_board_x_translation"] = side_board_x_translation
        params["division_board_x_translation"] = division_board_x_translation
        params["division_board_z_translation"] = division_board_z_translation
        params["bottom_gap_x_translation"] = division_board_x_translation

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
            obj, geometry_nodes, attributes=[], apply=True, input_kwargs=obj_params
        )

        if params.get("ret_params", False):
            return obj, obj_params

        tagging.tag_system.relabel_obj(obj)

        return obj


class LargeShelfFactory(LargeShelfBaseFactory):
    def sample_params(self):
        params = dict()
        params["Dimensions"] = (
            uniform(0.25, 0.35),
            uniform(0.3, 2.0),
            uniform(0.9, 2.0),
        )

        params["bottom_board_height"] = 0.083
        params["shelf_depth"] = params["Dimensions"][0] - 0.01
        num_h = int((params["Dimensions"][2] - 0.083) / 0.3)
        params["shelf_cell_height"] = [
            (params["Dimensions"][2] - 0.083) / num_h for _ in range(num_h)
        ]
        num_v = max(int(params["Dimensions"][1] / 0.5), 1)
        params["shelf_cell_width"] = [
            params["Dimensions"][1] / num_v for _ in range(num_v)
        ]
        return params


# ============================================================================
# === Phase 1 — Material sampling on raw SEED ===============================
# ============================================================================
# there); material kind strings are picked inside get_asset_params under the
# create_asset int_hash seed. For our conversion spec we standardise on the
# raw SEED for Phase 1 material construction (so all converted factories
# share the same phase-1 convention). The 40/30/30 white/black_wood/wood
# mix comes from large_shelf.py:1020-1024.
# ============================================================================

SEED = int(os.environ.get("SEED", 0))
_seed_all(SEED)

# Clear scene (fresh Blender state, matches objects_blender build block).
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)
bpy.context.scene.cursor.location = (0, 0, 0)

# Mirror sampling order in get_asset_params:
#   1) frame_material kind       (line 1020-1023)
#   2) board_material kind       (line 1024-1025, copies frame)
#   3) frame shader params       (via make_frame_material, _z variant)
#   4) board shader params       (via make_board_material, non-z variant)
_FRAME_KIND = np.random.choice(["white", "black_wood", "wood"], p=[0.4, 0.3, 0.3])
_BOARD_KIND = _FRAME_KIND  # large_shelf.py always copies frame -> board
MAT_FRAME = make_frame_material(_FRAME_KIND, slot_name="ShelfFrame")
MAT_BOARD = make_board_material(_BOARD_KIND, slot_name="ShelfBoard")

# LargeShelfFactory has no finalize_assets / wear_tear — no scratch/edge-wear


# ============================================================================
# === Build entry point — identical to objects_blender build() ==============
# ============================================================================

def build(seed=SEED):
    seed = int(seed)
    derived = int_hash((seed, 0))
    random.seed(derived)
    np.random.seed(derived)
    fac = LargeShelfFactory(seed)
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
