# [FL_INDEX: keywords="blender_factory, procedural_3d, SingleCabinetFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SingleCabinetFactory | Category: factories_geo
# Prompt: A 3D model of a tall single-door cabinet rendered from a three-quarter perspective, featuring a narrow, upright rectangular body with a single front door panel, a small door handle, and a uniform dark wood-toned appearance.

import os
import bpy
import bmesh
import math
import random
import colorsys
import hashlib
import numpy as np
from numpy.random import normal, randint, uniform

# ============================================================================
# Sources translated faithfully from:
# Upstream single_cabinet.py rolls frame_material from
# ["white","black_wood","wood"] with p=[0.5,0.2,0.3] in get_material_params(),
# then door panels roll glass via
#   lower = choice([frame, glass], p=[0.7,0.3])
#   upper = choice([lower, glass], p=[0.6,0.4])
# This script replicates that material sampling order under the raw SEED and
# stores the resulting shaders in module-level MAT_* variables.
# ============================================================================


def seed_all(seed: int) -> None:
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


def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    """Set Principled BSDF inputs with Blender-version-tolerant names."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
    }
    for key, val in kw.items():
        names = aliases.get(key, (key,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = val
                break


def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]


def _connect_output(nt, surface_out, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(surface_out, out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out


# ----------------------------------------------------------------------------
# shader_shelves_white — faithful port of shelf_shaders.py:21
# ----------------------------------------------------------------------------
def make_shelves_white(name="ShelvesWhite"):
    v = float(uniform(0.7, 1.0))
    rgb = [
        v * (1.0 + float(normal(0, 0.005))),
        v * (1.0 + float(normal(0, 0.005))),
        v * (1.0 + float(normal(0, 0.005))),
    ]
    base_color = (rgb[0], rgb[1], rgb[2], 1.0)
    roughness = float(uniform(0.7, 1.0))

    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color, "Roughness": roughness})
    _connect_output(nt, bsdf.outputs[0])
    return mat


# ----------------------------------------------------------------------------
# Common "wood/black_wood" node graph builder — faithful port of
# shader_shelves_black_wood / shader_shelves_wood (they share the same node
# topology; only the final ColorRamp palette differs). z_axis_texture swaps
# the mapping/wave-scale axes between x-stretched and xy-stretched layouts.
# Blender 5.0 no longer ships MusgraveTexture, so the one "musgrave" node in
# the original shader is substituted with a stretched NoiseTexture chain; all
# other nodes (TexCoord/Mapping/Noise/Voronoi/ColorRamp/Mix/Displacement) are
# preserved node-for-node.
# ----------------------------------------------------------------------------
def _build_wood_grain_graph(nt, wave_scale_value, z_axis_texture, ramp_palette):
    tex_coord_1 = nt.nodes.new("ShaderNodeTexCoord")

    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    if z_axis_texture:
        mapping_1.inputs["Scale"].default_value = (0.1, 0.1, 2.0)
    else:
        mapping_1.inputs["Scale"].default_value = (0.1, 2.0, 2.0)
    nt.links.new(tex_coord_1.outputs["Object"], mapping_1.inputs["Vector"])

    noise_texture_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_texture_1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise_texture_1.inputs:
        noise_texture_1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise_texture_1.inputs:
        noise_texture_1.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping_1.outputs["Vector"], noise_texture_1.inputs["Vector"])

    voronoi_texture = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi_texture, "voronoi_dimensions"):
        try:
            voronoi_texture.voronoi_dimensions = "3D"
        except TypeError:
            pass
    voronoi_texture.inputs["Scale"].default_value = 40.0
    nt.links.new(_noise_fac_output(noise_texture_1), voronoi_texture.inputs["Vector"])

    colorramp_1 = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = colorramp_1.inputs.get("Fac") or colorramp_1.inputs[0]
    color_out = voronoi_texture.outputs.get("Color") or voronoi_texture.outputs[1]
    nt.links.new(color_out, fac_in)
    colorramp_1.color_ramp.elements[0].position = 0.0864
    colorramp_1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = 0.1091
    colorramp_1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    if z_axis_texture:
        wave_scale_vec = (wave_scale_value, wave_scale_value, 0.1)
    else:
        wave_scale_vec = (wave_scale_value, 0.1, 0.1)

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = wave_scale_vec
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise_texture = nt.nodes.new("ShaderNodeTexNoise")
    noise_texture.inputs["Scale"].default_value = 3.0
    if "Detail" in noise_texture.inputs:
        noise_texture.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise_texture.inputs:
        noise_texture.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise_texture.inputs["Vector"])

    # Musgrave substitute: stretched NoiseTexture (Blender 5.0 drop-in)
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave.inputs:
        musgrave.inputs["Detail"].default_value = 3.0
    nt.links.new(_noise_fac_output(noise_texture), musgrave.inputs["Vector"])

    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    mix_1.inputs[0].default_value = 0.5
    nt.links.new(_noise_fac_output(musgrave), mix_1.inputs[6])
    nt.links.new(
        noise_texture.outputs.get("Color") or noise_texture.outputs[1],
        mix_1.inputs[7],
    )

    colorramp_2 = nt.nodes.new("ShaderNodeValToRGB")
    fac_in_2 = colorramp_2.inputs.get("Fac") or colorramp_2.inputs[0]
    nt.links.new(mix_1.outputs[2], fac_in_2)
    colorramp_2.color_ramp.elements[0].position = 0.0818
    colorramp_2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_2.color_ramp.elements[1].position = 0.85
    colorramp_2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"):
        mix_2.data_type = "RGBA"
    mix_2.inputs[0].default_value = 0.6
    nt.links.new(colorramp_1.outputs["Color"], mix_2.inputs[6])
    nt.links.new(colorramp_2.outputs["Color"], mix_2.inputs[7])

    colorramp_final = nt.nodes.new("ShaderNodeValToRGB")
    fac_in_f = colorramp_final.inputs.get("Fac") or colorramp_final.inputs[0]
    nt.links.new(mix_2.outputs[2], fac_in_f)
    # 3 stops (wood shelves shader uses 3 elements)
    elems = colorramp_final.color_ramp.elements
    while len(elems) < 3:
        elems.new(0.5)
    stops = ramp_palette
    for i, (pos, color) in enumerate(stops):
        elems[i].position = pos
        elems[i].color = color

    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"):
        mix_3.data_type = "RGBA"
    mix_3.inputs[0].default_value = 0.004
    nt.links.new(colorramp_1.outputs["Color"], mix_3.inputs[6])
    nt.links.new(colorramp_2.outputs["Color"], mix_3.inputs[7])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    return colorramp_final.outputs["Color"], disp.outputs[0]


def make_shelves_black_wood(name="ShelvesBlackWood", z_axis_texture=False):
    wave_scale = float(uniform(1.0, 3.0))
    dark_scale = float(uniform(0.0, 0.01))
    gray_scale = float(uniform(0.01, 0.03))
    rgb = [float(uniform(0.015, 0.035)), float(uniform(0.0, 0.01)), float(uniform(0.0, 0.01))]
    roughness = float(uniform(0.75, 1.0))

    palette = [
        (0.15, (dark_scale, dark_scale, dark_scale, 1.0)),
        (0.5, (gray_scale, gray_scale, gray_scale, 1.0)),
        (1.0, (rgb[0], rgb[1], rgb[2], 1.0)),
    ]

    mat = _new_material(name)
    nt = mat.node_tree
    color_socket, disp_socket = _build_wood_grain_graph(nt, wave_scale, z_axis_texture, palette)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    nt.links.new(color_socket, bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf.outputs[0], displacement=disp_socket)
    return mat


def make_shelves_black_wood_z(name="ShelvesBlackWoodZ"):
    return make_shelves_black_wood(name=name, z_axis_texture=True)


def make_shelves_wood(name="ShelvesWood", z_axis_texture=False):
    bright_hsv = [float(uniform(0.03, 0.09)), float(uniform(0.5, 0.7)), float(uniform(0.7, 1.0))]
    mid_hsv = [float(uniform(0.02, 0.06)), float(uniform(0.6, 1.0)), float(uniform(0.3, 0.6))]
    dark_hsv = [float(uniform(0.03, 0.05)), float(uniform(0.6, 1.0)), float(uniform(0.1, 0.3))]
    wave_scale = float(uniform(1.0, 3.0))
    roughness = float(uniform(0.75, 1.0))

    palette = [
        (0.02, hsv2rgba(dark_hsv)),
        (0.11, hsv2rgba(mid_hsv)),
        (0.8, hsv2rgba(bright_hsv)),
    ]

    mat = _new_material(name)
    nt = mat.node_tree
    color_socket, disp_socket = _build_wood_grain_graph(nt, wave_scale, z_axis_texture, palette)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    nt.links.new(color_socket, bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf.outputs[0], displacement=disp_socket)
    return mat


def make_shelves_wood_z(name="ShelvesWoodZ"):
    return make_shelves_wood(name=name, z_axis_texture=True)


# ----------------------------------------------------------------------------
# shader_glass — faithful port of ceramic/glass.py:15 (object surface variant,
# is_window=False so no LightPath/TransparentBSDF branch).
# ----------------------------------------------------------------------------
def _glass_color_roll():
    if float(uniform(0.0, 1.0)) < 0.5:
        return (1.0, 1.0, 1.0, 1.0)
    hue = float(uniform(0.0, 1.0))
    sat = float(uniform(0.05, 0.25))
    return hsv2rgba((hue, sat, 1.0))


def make_glass(name="Glass"):
    color = _glass_color_roll()
    mat = _new_material(name)
    nt = mat.node_tree
    glass_bsdf = nt.nodes.new("ShaderNodeBsdfGlass")
    glass_bsdf.inputs["Roughness"].default_value = 0.02
    glass_bsdf.inputs["IOR"].default_value = 1.5
    if "Color" in glass_bsdf.inputs:
        glass_bsdf.inputs["Color"].default_value = color
    _connect_output(nt, glass_bsdf.outputs[0])
    return mat


# ----------------------------------------------------------------------------
# Material dispatch — maps upstream frame_material name to shader constructor.
# single_cabinet.py uses the _z (z-axis texture) variants for the cabinet body
# and the non-_z variants for door panels, mirroring
# doors.py:get_material_func() and large_shelf.py:get_material_func().
# ----------------------------------------------------------------------------
def make_frame_material(name_key, slot_name):
    if name_key == "white":
        return make_shelves_white(name=slot_name)
    if name_key == "black_wood":
        return make_shelves_black_wood_z(name=slot_name)
    if name_key == "wood":
        return make_shelves_wood_z(name=slot_name)
    return make_shelves_white(name=slot_name)


def make_panel_material(name_key, slot_name):
    if name_key == "white":
        return make_shelves_white(name=slot_name)
    if name_key == "black_wood":
        return make_shelves_black_wood_z(name=slot_name)
    if name_key == "wood":
        return make_shelves_wood_z(name=slot_name)
    if name_key == "glass":
        return make_glass(name=slot_name)
    return make_shelves_white(name=slot_name)


# applied here.

SCRATCH_LABEL = "scratch"  # kept for potential downstream reference
EDGE_WEAR_LABEL = "wear_tear"


# ── Seed & scene cleanup ──
SEED = int(os.environ.get("SEED", "0"))
random.seed(SEED)
np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)


# ============================================================================
# Phase 1 — Material sampling on raw SEED (mirrors single_cabinet.py
# __init__ / get_material_params() under FixedSeed(factory_seed)).
#
# Sampling order:
#   1. frame_material name roll (3-way choice)
#   2. large_shelf frame shader build (z-axis variant for the cabinet body)
#   3. cabinet-door panel_material rolls:
#        - has_mid_ramp flag (used both here and for geometry; geometry code
#          will re-roll its own copy under the separate geometry seed, so we
#          snapshot+restore RNG around this roll so the geometry sequence is
#          unchanged)
#        - lower_mat = choice([frame_material, glass], p=[0.7,0.3])
#        - upper_mat = choice([lower_mat, glass], p=[0.6,0.4])
#   4. door frame shader build (shared with body frame — we reuse MAT_FRAME
#      for both to keep slot counts tight)
#   5. panel shader materials (lower / upper)
#   6. hinge-attach material (same frame shader)
#   7. wear_tear 50/50 gates
#
# The geometry phase uses its own Phase-2 seed derived from md5 below, so
# this block does not need to preserve RNG state for geometry.
# ============================================================================
seed_all(SEED)

_FRAME_NAMES = ["white", "black_wood", "wood"]
_FRAME_PROBS = [0.5, 0.2, 0.3]
_frame_name = str(np.random.choice(_FRAME_NAMES, p=_FRAME_PROBS))

MAT_FRAME = make_frame_material(_frame_name, "CabinetFrame")

# Door panel material rolls — mirror CabinetDoorBaseFactory.get_asset_params.
# has_mid_ramp is also rolled for the geometry, but geometry re-seeds under
# the separate Phase-2 hash so we roll an independent copy here for the
# material sampling only.
_has_mid_ramp_mat_side = bool(np.random.choice([True, False], p=[0.6, 0.4]))
if _has_mid_ramp_mat_side:
    _lower_key = str(np.random.choice([_frame_name, "glass"], p=[0.7, 0.3]))
    _upper_key = str(np.random.choice([_lower_key, "glass"], p=[0.6, 0.4]))
else:
    _lower_key = _frame_name
    _upper_key = _frame_name

MAT_PANEL_LOWER = make_panel_material(_lower_key, "CabinetPanelLower")
MAT_PANEL_UPPER = make_panel_material(_upper_key, "CabinetPanelUpper")
MAT_HINGE = make_frame_material(_frame_name, "CabinetHinge")



# ============================================================================
# === Original geometry code copied verbatim from objects_blender/shelves/
#     SingleCabinetFactory.py. The only modifications are:
#       - per-part material bindings before the final join
#       - final join uses bpy.ops.object.join() (preserves material slots)
#         in place of the bmesh.from_mesh path (which drops slots)
# ============================================================================

def apply_transform(obj, loc=False, rot=True, scale=True):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    obj.select_set(False)
    return obj

# --- Node system ---

def to_nodegroup(name):
    def reg(fn):
        def init_fn(*args, **kw):
            ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
            fn(NodeWrangler(ng), *args, **kw)
            return ng
        return init_fn
    return reg

def _infer_output_socket(item):
    if isinstance(item, bpy.types.NodeSocket): return item
    if outputs := getattr(item, 'outputs', None):
        return next((s for s in outputs if getattr(s, 'enabled', True)), outputs[0])

class NodeWrangler:
    def __init__(self, node_group_or_mod):
        ng = self.node_group = node_group_or_mod.node_group if isinstance(node_group_or_mod, bpy.types.NodesModifier) else node_group_or_mod
        self.nodes, self.links = ng.nodes, ng.links

    def expose_input(self, name, val=None, dtype=None):
        gi = next((n for n in self.nodes if n.bl_idname == 'NodeGroupInput'), None) or self.nodes.new('NodeGroupInput')
        inames = [s.name for s in self.node_group.interface.items_tree if s.in_out == 'INPUT']
        if name not in inames:
            self.node_group.interface.new_socket(name=name, in_out='INPUT', socket_type=dtype or 'NodeSocketFloat')
            inames.append(name)
        try: return gi.outputs[name]
        except Exception: return gi.outputs[inames.index(name)]

    def connect_input(self, sock, item):
        for sub in (item if isinstance(item, list) else [item]):
            out = _infer_output_socket(sub)
            if out is not None:
                try: self.links.new(out, sock)
                except Exception: pass
            elif not isinstance(item, list):
                try: sock.default_value = sub
                except Exception:
                    try: sock.default_value = tuple(sub)
                    except Exception: pass

    def new_node(self, node_type, input_kwargs=None, attrs=None, expose_input=None):
        if expose_input:
            for dtype, name, val in expose_input:
                self.expose_input(name, val=val, dtype=dtype)
        ng_ref = bpy.data.node_groups.get(node_type)
        if ng_ref is not None:
            n = self.nodes.new('GeometryNodeGroup'); n.node_tree = ng_ref
        else:
            n = self.nodes.new(node_type)
        if attrs:
            for k, v in attrs.items():
                try: setattr(n, k, v)
                except Exception: pass
        if input_kwargs:
            is_go = (n.bl_idname == 'NodeGroupOutput')
            for k, item in input_kwargs.items():
                if is_go and isinstance(k, str) and k not in [s.name for s in n.inputs]:
                    out_sock = _infer_output_socket(item)
                    st = getattr(out_sock, 'bl_idname', 'NodeSocketFloat') if out_sock else 'NodeSocketFloat'
                    st = {'NodeSocketFloatUnsigned': 'NodeSocketFloat', 'NodeSocketVirtual': 'NodeSocketFloat'}.get(st, st)
                    try: self.node_group.interface.new_socket(name=k, in_out='OUTPUT', socket_type=st)
                    except Exception: pass
                try: self.connect_input(n.inputs[k], item)
                except Exception:
                    try:
                        self.connect_input(n.inputs[[s.name for s in n.inputs].index(k)], item)
                    except Exception: pass
        return n

    def val(self, v):
        n = self.new_node('ShaderNodeValue'); n.outputs[0].default_value = v; return n

def make_geo_object(geo_func, kwargs):
    bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    ng = bpy.data.node_groups.new('Geometry Nodes', 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    mod = obj.modifiers.new(geo_func.__name__, 'NODES')
    mod.node_group = ng
    geo_func(NodeWrangler(mod), **kwargs)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)
    return obj

# --- Node type constants ---

class Nodes:
    BooleanMath = 'FunctionNodeBooleanMath'
    CombineXYZ = 'ShaderNodeCombineXYZ'
    ConvexHull = 'GeometryNodeConvexHull'
    CurveCircle = 'GeometryNodeCurvePrimitiveCircle'
    CurveLine = 'GeometryNodeCurvePrimitiveLine'
    CurveToMesh = 'GeometryNodeCurveToMesh'
    EndpointSelection = 'GeometryNodeCurveEndpointSelection'
    FlipFaces = 'GeometryNodeFlipFaces'
    GroupInput = 'NodeGroupInput'
    GroupOutput = 'NodeGroupOutput'
    Index = 'GeometryNodeInputIndex'
    JoinGeometry = 'GeometryNodeJoinGeometry'
    Math = 'ShaderNodeMath'
    MergeByDistance = 'GeometryNodeMergeByDistance'
    MeshCube = 'GeometryNodeMeshCube'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    SetPosition = 'GeometryNodeSetPosition'
    Transform = 'GeometryNodeTransform'

# =====================================================================
# Shelf nodegroup functions
# =====================================================================

@to_nodegroup("nodegroup_screw_head")
def nodegroup_screw_head(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "Depth", 0.0050),
        ("NodeSocketFloat", "Radius", 1.0000),
        ("NodeSocketFloat", "division_thickness", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
        ("NodeSocketFloat", "depth", 0.5000),
        ("NodeSocketFloat", "screw_width_gap", 0.5000),
        ("NodeSocketFloat", "screw_depth_gap", 0.0000),
    ])

    cylinder = nw.new_node("GeometryNodeMeshCylinder",
        input_kwargs={"Radius": group_input.outputs["Radius"], "Depth": group_input.outputs["Depth"]},
        attrs={"fill_type": "TRIANGLE_FAN"})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["width"]}, attrs={"operation": "MULTIPLY"})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: group_input.outputs["screw_width_gap"]}, attrs={"operation": "SUBTRACT"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["depth"]}, attrs={"operation": "MULTIPLY"})
    subtract_1 = nw.new_node(Nodes.Math, input_kwargs={0: multiply_1, 1: group_input.outputs["screw_width_gap"]}, attrs={"operation": "SUBTRACT"})
    multiply_2 = nw.new_node(Nodes.Math, input_kwargs={0: subtract_1, 1: -1.0000}, attrs={"operation": "MULTIPLY"})
    multiply_3 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["division_thickness"], 1: -0.5000}, attrs={"operation": "MULTIPLY"})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": multiply_2, "Z": multiply_3})

    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cylinder.outputs["Mesh"], "Translation": combine_xyz})

    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": subtract_1, "Z": multiply_3})

    transform_6 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cylinder.outputs["Mesh"], "Translation": combine_xyz_4})

    join_geometry_2 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_1, transform_6]})

    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry_2, "Scale": (-1.0000, 1.0000, 1.0000)})

    join_geometry_3 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_4, join_geometry_2]})

    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_3})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": realize_instances})

@to_nodegroup("nodegroup_division_board")
def nodegroup_division_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "thickness", 0.0000),
        ("NodeSocketFloat", "width", 0.0000),
        ("NodeSocketFloat", "depth", 0.0000),
        ("NodeSocketFloat", "z_translation", 0.0000),
        ("NodeSocketFloat", "x_translation", 0.0000),
        ("NodeSocketFloat", "screw_depth", 0.0000),
        ("NodeSocketFloat", "screw_radius", 0.0000),
        ("NodeSocketFloat", "screw_width_gap", 0.0000),
        ("NodeSocketFloat", "screw_depth_gap", 0.0000),
    ])

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": group_input.outputs["width"], "Y": group_input.outputs["depth"], "Z": group_input.outputs["thickness"]})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    screw_head = nw.new_node(nodegroup_screw_head().name, input_kwargs={
        "Depth": group_input.outputs["screw_depth"], "Radius": group_input.outputs["screw_radius"],
        "division_thickness": group_input.outputs["thickness"], "width": group_input.outputs["width"],
        "depth": group_input.outputs["depth"], "screw_width_gap": group_input.outputs["screw_width_gap"],
        "screw_depth_gap": group_input.outputs["screw_depth_gap"]})

    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [cube, screw_head]})
    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": group_input.outputs["x_translation"], "Z": group_input.outputs["z_translation"]})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform})

@to_nodegroup("nodegroup_bottom_board")
def nodegroup_bottom_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "thickness", 0.0000),
        ("NodeSocketFloat", "depth", 0.5000),
        ("NodeSocketFloat", "y_gap", 0.5000),
        ("NodeSocketFloat", "x_translation", 0.0000),
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "width", 0.0000),
    ])

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": group_input.outputs["width"], "Y": group_input.outputs["thickness"], "Z": group_input.outputs["height"]})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["depth"]}, attrs={"operation": "MULTIPLY"})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: group_input.outputs["y_gap"]}, attrs={"operation": "SUBTRACT"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"]}, attrs={"operation": "MULTIPLY"})
    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": group_input.outputs["x_translation"], "Y": subtract, "Z": multiply_1})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform})

@to_nodegroup("nodegroup_back_board")
def nodegroup_back_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "width", 0.0000),
        ("NodeSocketFloat", "thickness", 0.5000),
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "depth", 0.5000),
    ])

    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": group_input.outputs["width"], "Y": group_input.outputs["thickness"], "Z": group_input.outputs["height"]})

    cube_2 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_4})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: -0.5000}, attrs={"operation": "MULTIPLY"})
    multiply_add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["depth"], 1: -0.5000, 2: multiply}, attrs={"operation": "MULTIPLY_ADD"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"]}, attrs={"operation": "MULTIPLY"})

    combine_xyz_5 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": multiply_add, "Z": multiply_1})

    transform_5 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_2, "Translation": combine_xyz_5})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_5})

@to_nodegroup("nodegroup_side_board")
def nodegroup_side_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "board_thickness", 0.5000),
        ("NodeSocketFloat", "depth", 0.5000),
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "x_translation", 0.0000),
    ])

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": group_input.outputs["board_thickness"], "Y": group_input.outputs["depth"], "Z": group_input.outputs["height"]})

    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: 0.5000}, attrs={"operation": "MULTIPLY"})
    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": group_input.outputs["x_translation"], "Z": multiply})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform})

def geometry_nodes(nw: NodeWrangler, **kwargs):
    side_board_thickness = nw.val(kwargs["side_board_thickness"])
    shelf_depth = nw.val(kwargs["shelf_depth"])

    add = nw.new_node(Nodes.Math, input_kwargs={0: shelf_depth, 1: 0.0040})

    shelf_height = nw.val(kwargs["shelf_height"])

    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: shelf_height, 1: 0.0020})
    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: shelf_height, 1: -0.0010})
    _sb = nodegroup_side_board().name
    side_boards = [
        nw.new_node(_sb, input_kwargs={"board_thickness": side_board_thickness, "depth": add, "height": add_1, "x_translation": nw.val(x)})
        for x in kwargs["side_board_x_translation"]
    ]

    shelf_width = nw.val(kwargs["shelf_width"])
    backboard_thickness = nw.val(kwargs["backboard_thickness"])
    add_side = nw.new_node(Nodes.Math, input_kwargs={0: shelf_width, 1: kwargs["side_board_thickness"] * 2})
    back_board = nw.new_node(nodegroup_back_board().name, input_kwargs={
        "width": add_side, "thickness": backboard_thickness, "height": add_2, "depth": shelf_depth})

    bottom_board_y_gap = nw.val(kwargs["bottom_board_y_gap"])
    bottom_board_height = nw.val(kwargs["bottom_board_height"])
    _bb = nodegroup_bottom_board().name
    bottom_boards = [
        nw.new_node(_bb, input_kwargs={"thickness": side_board_thickness, "depth": shelf_depth,
            "y_gap": bottom_board_y_gap, "x_translation": nw.val(kwargs["bottom_gap_x_translation"][i]),
            "height": bottom_board_height, "width": nw.val(kwargs["shelf_cell_width"][i])})
        for i in range(len(kwargs["shelf_cell_width"]))
    ]

    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [back_board] + side_boards + bottom_boards})
    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry})

    division_board_thickness = nw.val(kwargs["division_board_thickness"])
    screw_depth_head = nw.val(kwargs["screw_depth_head"])
    screw_head_radius = nw.val(kwargs["screw_head_radius"])
    screw_width_gap = nw.val(kwargs["screw_width_gap"])
    screw_depth_gap = nw.val(kwargs["screw_depth_gap"])
    _db = nodegroup_division_board().name
    division_boards = [
        nw.new_node(_db, input_kwargs={"thickness": division_board_thickness,
            "width": nw.val(kwargs["shelf_cell_width"][i]), "depth": shelf_depth,
            "z_translation": nw.val(kwargs["division_board_z_translation"][j]),
            "x_translation": nw.val(kwargs["division_board_x_translation"][i]),
            "screw_depth": screw_depth_head, "screw_radius": screw_head_radius,
            "screw_width_gap": screw_width_gap, "screw_depth_gap": screw_depth_gap})
        for i in range(len(kwargs["shelf_cell_width"]))
        for j in range(len(kwargs["division_board_z_translation"]))
    ]

    join_geometry_k = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": division_boards})

    join_geometry_3 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [realize_instances, join_geometry_k]})

    realize_instances_3 = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_3})

    triangulate = nw.new_node("GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances_3})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": triangulate, "Rotation": (0.0000, 0.0000, -1.5708)})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform})

# =====================================================================
# Door nodegroup functions
# =====================================================================

@to_nodegroup("nodegroup_node_group")
def nodegroup_node_group(nw: NodeWrangler):
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": (0.0120, 0.00060, 0.0400)})

    cylinder = nw.new_node("GeometryNodeMeshCylinder", input_kwargs={"Vertices": 16, "Radius": 0.0100, "Depth": 0.00050})
    transform = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": cylinder.outputs["Mesh"], "Translation": (0.0050, 0.0000, 0.0000), "Rotation": (1.5708, 0.0000, 0.0000)})

    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": (0.0200, 0.0006, 0.0120)})

    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": (0.0080, 0.0000, 0.0000)})

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [cube, transform, transform_1]})

    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "attach_height", 0.1000),
        ("NodeSocketFloat", "door_width", 0.5000),
    ])

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["door_width"]}, attrs={"operation": "MULTIPLY"})

    subtract = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: 0.0181}, attrs={"operation": "SUBTRACT"})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Z": group_input.outputs["attach_height"]})

    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry_1, "Translation": combine_xyz})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_2})

@to_nodegroup("nodegroup_knob_handle")
def nodegroup_knob_handle(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "Radius", 0.0100),
        ("NodeSocketFloat", "thickness_1", 0.5000),
        ("NodeSocketFloat", "thickness_2", 0.5000),
        ("NodeSocketFloat", "length", 0.5000),
        ("NodeSocketFloat", "knob_mid_height", 0.0000),
        ("NodeSocketFloat", "edge_width", 0.5000),
        ("NodeSocketFloat", "door_width", 0.5000),
    ])

    add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["thickness_2"], 1: group_input.outputs["thickness_1"]})
    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: add, 1: group_input.outputs["length"]})
    cylinder = nw.new_node("GeometryNodeMeshCylinder",
        input_kwargs={"Vertices": 16, "Radius": group_input.outputs["Radius"], "Depth": add_1})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["door_width"], 1: group_input.outputs["edge_width"]}, attrs={"operation": "SUBTRACT"})
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: subtract, 1: -0.5000}, attrs={"operation": "MULTIPLY"})
    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: -0.005})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: add_1}, attrs={"operation": "MULTIPLY"})

    combine_xyz_6 = nw.new_node(Nodes.CombineXYZ, input_kwargs={
        "X": add_2, "Y": multiply_1, "Z": group_input.outputs["knob_mid_height"]})

    transform_6 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": cylinder.outputs["Mesh"], "Translation": combine_xyz_6, "Rotation": (1.5708, 0.0000, 0.0000)})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_6})

@to_nodegroup("nodegroup_mid_board")
def nodegroup_mid_board(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "thickness", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
    ])

    add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: -0.0001})
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"]}, attrs={"operation": "MULTIPLY"})

    multiply_k = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: 0.5000}, attrs={"operation": "MULTIPLY"})
    add_k = nw.new_node(Nodes.Math, input_kwargs={0: multiply_k, 1: 0.004})
    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: -0.0001})
    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add, "Y": group_input.outputs["thickness"], "Z": add_2})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_3})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: multiply}, attrs={"operation": "MULTIPLY"})
    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_k, "Z": multiply_1})
    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_4})
    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_3})
    multiply_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: 1.5000}, attrs={"operation": "MULTIPLY"})

    combine_xyz_8 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_k, "Z": multiply_2})

    transform_7 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_8})

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform_4, transform_7]})

    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": realize_instances, "mid_height": multiply})

@to_nodegroup("nodegroup_mid_board_001")
def nodegroup_mid_board_001(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "thickness", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
    ])

    add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["width"], 1: -0.0001})
    multiply_k = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["thickness"], 1: 0.5000}, attrs={"operation": "MULTIPLY"})
    add_k = nw.new_node(Nodes.Math, input_kwargs={0: multiply_k, 1: 0.004})
    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"], 1: -0.0001})
    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add, "Y": group_input.outputs["thickness"], "Z": add_2})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_3})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["height"]}, attrs={"operation": "MULTIPLY"})

    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_k, "Z": multiply_1})

    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_4})

    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": transform_4})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": realize_instances, "mid_height": group_input.outputs["height"]})

@to_nodegroup("nodegroup_double_rampled_edge")
def nodegroup_double_rampled_edge(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "thickness_2", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
        ("NodeSocketFloat", "thickness_1", 0.5000),
        ("NodeSocketFloat", "ramp_angle", 0.5000),
    ])

    height = group_input.outputs["height"]
    width = group_input.outputs["width"]
    ramp_angle = group_input.outputs["ramp_angle"]
    thickness_2 = group_input.outputs["thickness_2"]
    thickness_1 = group_input.outputs["thickness_1"]

    combine_xyz_10 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": height})
    curve_line = nw.new_node(Nodes.CurveLine, input_kwargs={"End": combine_xyz_10})
    curve_circle = nw.new_node(Nodes.CurveCircle, input_kwargs={"Resolution": 2, "Radius": 0.0100})
    endpoint_selection = nw.new_node(Nodes.EndpointSelection, input_kwargs={"End Size": 0})

    tangent = nw.new_node(Nodes.Math, input_kwargs={0: ramp_angle}, attrs={"operation": "TANGENT"})
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: tangent, 1: thickness_2}, attrs={"operation": "MULTIPLY"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: 2.0000, 1: multiply}, attrs={"operation": "MULTIPLY"})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: width, 1: multiply_1}, attrs={"operation": "SUBTRACT"})
    multiply_2 = nw.new_node(Nodes.Math, input_kwargs={0: subtract}, attrs={"operation": "MULTIPLY"})
    multiply_3 = nw.new_node(Nodes.Math, input_kwargs={0: multiply_2, 1: -1.0000}, attrs={"operation": "MULTIPLY"})
    combine_xyz_7 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_3, "Y": thickness_1})
    set_position = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": curve_circle.outputs["Curve"], "Selection": endpoint_selection, "Position": combine_xyz_7})

    endpoint_selection_1 = nw.new_node(Nodes.EndpointSelection, input_kwargs={"Start Size": 0})
    add_5 = nw.new_node(Nodes.Math, input_kwargs={0: thickness_1, 1: thickness_2})
    combine_xyz_8 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_3, "Y": add_5})
    set_position_1 = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": set_position, "Selection": endpoint_selection_1, "Position": combine_xyz_8})

    index = nw.new_node(Nodes.Index)
    less_than = nw.new_node(Nodes.Math, input_kwargs={0: index, 1: 1.0100}, attrs={"operation": "LESS_THAN"})
    greater_than = nw.new_node(Nodes.Math, input_kwargs={0: index, 1: 0.9900}, attrs={"operation": "GREATER_THAN"})
    op_and = nw.new_node(Nodes.BooleanMath, input_kwargs={0: less_than, 1: greater_than})
    multiply_4 = nw.new_node(Nodes.Math, input_kwargs={0: width}, attrs={"operation": "MULTIPLY"})
    multiply_5 = nw.new_node(Nodes.Math, input_kwargs={0: multiply_4, 1: -1.0000}, attrs={"operation": "MULTIPLY"})

    combine_xyz_9 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_5, "Y": thickness_1})

    set_position_2 = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": set_position_1, "Selection": op_and, "Position": combine_xyz_9})
    curve_to_mesh = nw.new_node(Nodes.CurveToMesh,
        input_kwargs={"Curve": curve_line, "Profile Curve": set_position_2, "Fill Caps": True})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": width, "Y": thickness_1, "Z": height})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})
    multiply_6 = nw.new_node(Nodes.Math, input_kwargs={0: thickness_1}, attrs={"operation": "MULTIPLY"})
    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": multiply_6})
    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_2})

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": thickness_2, "Z": height})
    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_1})
    multiply_7 = nw.new_node(Nodes.Math, input_kwargs={0: thickness_2}, attrs={"operation": "MULTIPLY"})
    add_6 = nw.new_node(Nodes.Math, input_kwargs={0: thickness_1, 1: multiply_7})
    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": add_6})
    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_3})
    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform, transform_1]})

    multiply_8 = nw.new_node(Nodes.Math, input_kwargs={0: height}, attrs={"operation": "MULTIPLY"})
    combine_xyz_11 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_8})
    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz_11})

    combine_xyz_12 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": height})
    curve_line_1 = nw.new_node(Nodes.CurveLine, input_kwargs={"End": combine_xyz_12})
    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": set_position_2, "Scale": (-1.0000, 1.0000, 1.0000)})
    curve_to_mesh_1 = nw.new_node(Nodes.CurveToMesh,
        input_kwargs={"Curve": curve_line_1, "Profile Curve": transform_2, "Fill Caps": True})

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [curve_to_mesh, transform_4, curve_to_mesh_1]})

    merge_by_distance = nw.new_node(Nodes.MergeByDistance, input_kwargs={"Geometry": join_geometry_1, "Distance": 0.0001})

    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": merge_by_distance})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": realize_instances})

@to_nodegroup("nodegroup_ramped_edge")
def nodegroup_ramped_edge(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "height", 0.5000),
        ("NodeSocketFloat", "thickness_2", 0.5000),
        ("NodeSocketFloat", "width", 0.5000),
        ("NodeSocketFloat", "thickness_1", 0.5000),
        ("NodeSocketFloat", "ramp_angle", 0.5000),
    ])

    height = group_input.outputs["height"]
    width = group_input.outputs["width"]
    ramp_angle = group_input.outputs["ramp_angle"]
    thickness_2 = group_input.outputs["thickness_2"]
    thickness_1 = group_input.outputs["thickness_1"]

    combine_xyz_10 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": height})
    curve_line = nw.new_node(Nodes.CurveLine, input_kwargs={"End": combine_xyz_10})
    curve_circle = nw.new_node(Nodes.CurveCircle, input_kwargs={"Resolution": 2, "Radius": 0.0100})
    endpoint_selection = nw.new_node(Nodes.EndpointSelection, input_kwargs={"End Size": 0})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: width}, attrs={"operation": "MULTIPLY"})
    tangent = nw.new_node(Nodes.Math, input_kwargs={0: ramp_angle}, attrs={"operation": "TANGENT"})
    multiply_1 = nw.new_node(Nodes.Math, input_kwargs={0: tangent, 1: thickness_2}, attrs={"operation": "MULTIPLY"})
    subtract = nw.new_node(Nodes.Math, input_kwargs={0: width, 1: multiply_1}, attrs={"operation": "SUBTRACT"})
    subtract_1 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: subtract}, attrs={"operation": "SUBTRACT"})
    combine_xyz_7 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract_1, "Y": thickness_1})
    set_position = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": curve_circle.outputs["Curve"], "Selection": endpoint_selection, "Position": combine_xyz_7})

    endpoint_selection_1 = nw.new_node(Nodes.EndpointSelection, input_kwargs={"Start Size": 0})
    add_5 = nw.new_node(Nodes.Math, input_kwargs={0: thickness_1, 1: thickness_2})
    combine_xyz_8 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract_1, "Y": add_5})
    set_position_1 = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": set_position, "Selection": endpoint_selection_1, "Position": combine_xyz_8})

    index = nw.new_node(Nodes.Index)
    less_than = nw.new_node(Nodes.Math, input_kwargs={0: index, 1: 1.0100}, attrs={"operation": "LESS_THAN"})
    greater_than = nw.new_node(Nodes.Math, input_kwargs={0: index, 1: 0.9900}, attrs={"operation": "GREATER_THAN"})
    op_and = nw.new_node(Nodes.BooleanMath, input_kwargs={0: less_than, 1: greater_than})
    multiply_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: -1.0000}, attrs={"operation": "MULTIPLY"})
    combine_xyz_9 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_2, "Y": thickness_1})
    set_position_2 = nw.new_node(Nodes.SetPosition,
        input_kwargs={"Geometry": set_position_1, "Selection": op_and, "Position": combine_xyz_9})
    curve_to_mesh = nw.new_node(Nodes.CurveToMesh,
        input_kwargs={"Curve": curve_line, "Profile Curve": set_position_2, "Fill Caps": True})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": width, "Y": thickness_1, "Z": height})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})
    multiply_3 = nw.new_node(Nodes.Math, input_kwargs={0: thickness_1}, attrs={"operation": "MULTIPLY"})
    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": multiply_3})
    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": combine_xyz_2})

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": subtract, "Y": thickness_2, "Z": height})
    cube_1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz_1})
    multiply_4 = nw.new_node(Nodes.Math, input_kwargs={0: multiply_1}, attrs={"operation": "MULTIPLY"})
    multiply_5 = nw.new_node(Nodes.Math, input_kwargs={0: thickness_2}, attrs={"operation": "MULTIPLY"})
    add_6 = nw.new_node(Nodes.Math, input_kwargs={0: thickness_1, 1: multiply_5})
    combine_xyz_3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_4, "Y": add_6})
    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube_1, "Translation": combine_xyz_3})
    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [transform, transform_1]})

    multiply_6 = nw.new_node(Nodes.Math, input_kwargs={0: height}, attrs={"operation": "MULTIPLY"})
    combine_xyz_11 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_6})
    transform_4 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz_11})
    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [curve_to_mesh, transform_4]})
    merge_by_distance = nw.new_node(Nodes.MergeByDistance, input_kwargs={"Geometry": join_geometry_1, "Distance": 0.0001})
    realize_instances = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": merge_by_distance})

    multiply_7 = nw.new_node(Nodes.Math, input_kwargs={0: width, 1: -0.5000}, attrs={"operation": "MULTIPLY"})
    combine_xyz_4 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_7})

    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": realize_instances, "Translation": combine_xyz_4})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_2})

@to_nodegroup("nodegroup_panel_edge_frame")
def nodegroup_panel_edge_frame(nw: NodeWrangler):
    group_input = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketGeometry", "vertical_edge", None),
        ("NodeSocketFloat", "door_width", 0.5000),
        ("NodeSocketFloat", "door_height", 0.0000),
        ("NodeSocketGeometry", "horizontal_edge", None),
    ])

    multiply_add = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["door_width"], 2: 0.0010}, attrs={"operation": "MULTIPLY_ADD"})
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: multiply_add, 1: -1.0000}, attrs={"operation": "MULTIPLY"})
    transform_7 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": group_input.outputs["horizontal_edge"], "Translation": (0.0000, -0.0001, 0.0000), "Scale": (0.9999, 1.0000, 1.0000)})

    add = nw.new_node(Nodes.Math, input_kwargs={0: multiply_add, 1: -0.0001})
    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: group_input.outputs["door_height"], 1: 0.0001})
    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add, "Z": add_1})
    transform_3 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": transform_7, "Translation": combine_xyz_2, "Rotation": (0.0000, -1.5708, 0.0000)})

    add_2 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: 0.0001})
    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add_2})
    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": transform_7, "Translation": combine_xyz_1, "Rotation": (0.0000, 1.5708, 0.0000)})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_add})
    transform = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": group_input.outputs["vertical_edge"], "Translation": combine_xyz})

    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": transform, "Scale": (-1.0000, 1.0000, 1.0000)})

    convex_hull_final = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform})
    convex_hull_final1 = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform_1})
    convex_hull_final2 = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform_2})
    convex_hull_final3 = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform_3})

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={
        "Geometry": [convex_hull_final, convex_hull_final1, convex_hull_final2, convex_hull_final3]})

    flip_faces = nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": join_geometry_1})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Value": multiply, "Geometry": flip_faces})

def geometry_door_nodes(nw: NodeWrangler, **kwargs):
    door_height = nw.val(kwargs["door_height"])
    door_edge_thickness_2 = nw.val(kwargs["edge_thickness_2"])
    door_edge_width = nw.val(kwargs["edge_width"])
    door_edge_thickness_1 = nw.val(kwargs["edge_thickness_1"])
    door_edge_ramp_angle = nw.val(kwargs["edge_ramp_angle"])

    _re = nodegroup_ramped_edge().name
    re_kwargs = {"thickness_2": door_edge_thickness_2, "width": door_edge_width, "thickness_1": door_edge_thickness_1, "ramp_angle": door_edge_ramp_angle}
    ramped_edge = nw.new_node(_re, input_kwargs={"height": door_height, **re_kwargs})
    door_width = nw.val(kwargs["door_width"])
    ramped_edge_1 = nw.new_node(_re, input_kwargs={"height": door_width, **re_kwargs})
    panel_edge_frame = nw.new_node(nodegroup_panel_edge_frame().name, input_kwargs={
        "vertical_edge": ramped_edge, "door_width": door_width, "door_height": door_height, "horizontal_edge": ramped_edge_1})

    add = nw.new_node(Nodes.Math, input_kwargs={0: panel_edge_frame.outputs["Value"], 1: 0.0001})
    mid_board_thickness = nw.val(kwargs["board_thickness"])

    if kwargs["has_mid_ramp"]:
        mid_board = nw.new_node(nodegroup_mid_board().name,
            input_kwargs={"height": door_height, "thickness": mid_board_thickness, "width": door_width})
    else:
        mid_board = nw.new_node(nodegroup_mid_board_001().name,
            input_kwargs={"height": door_height, "thickness": mid_board_thickness, "width": door_width})

    combine_xyz_5 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add, "Y": -0.0001, "Z": mid_board.outputs["mid_height"]})

    frame = [panel_edge_frame.outputs["Geometry"]]
    if kwargs["has_mid_ramp"]:
        double_rampled_edge = nw.new_node(nodegroup_double_rampled_edge().name,
            input_kwargs={"height": door_width, **re_kwargs})
        transform_5 = nw.new_node(Nodes.Transform, input_kwargs={
            "Geometry": double_rampled_edge, "Translation": combine_xyz_5, "Rotation": (0.0000, 1.5708, 0.0000)})
        convex_hull_midboard = nw.new_node(Nodes.ConvexHull, input_kwargs={"Geometry": transform_5})
        frame.append(nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": convex_hull_midboard}))

    join_geometry_1 = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": frame})

    knob_raduis = nw.val(kwargs["knob_R"])
    know_length = nw.val(kwargs["knob_length"])
    multiply = nw.new_node(Nodes.Math, input_kwargs={0: door_height}, attrs={"operation": "MULTIPLY"})

    knob_handle = nw.new_node(nodegroup_knob_handle().name, input_kwargs={
        "Radius": knob_raduis, "thickness_1": door_edge_thickness_1, "thickness_2": door_edge_thickness_2,
        "length": know_length, "knob_mid_height": multiply, "edge_width": door_edge_width, "door_width": door_width})

    knob_flip_faces = nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": knob_handle})

    _ng = nodegroup_node_group().name
    attach_gadgets = [
        nw.new_node(_ng, input_kwargs={"attach_height": nw.val(h), "door_width": door_width})
        for h in kwargs["attach_height"]
    ]

    flip_faces_middle = nw.new_node(Nodes.FlipFaces, input_kwargs={"Mesh": mid_board.outputs["Geometry"]})

    geos = [join_geometry_1, knob_flip_faces, flip_faces_middle] + attach_gadgets
    join_geometry = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": geos})

    multiply = nw.new_node(Nodes.Math, input_kwargs={0: door_width, 1: -0.5000}, attrs={"operation": "MULTIPLY"})

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply})

    transform = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": join_geometry, "Translation": combine_xyz})

    realize_instances_1 = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": transform})

    triangulate = nw.new_node("GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances_1})
    transform_1 = nw.new_node(Nodes.Transform, input_kwargs={
        "Geometry": triangulate, "Scale": (-1.0 if kwargs["door_left_hinge"] else 1.0, 1.0000, 1.0000)})

    transform_2 = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": transform_1, "Rotation": (0.0000, 0.0000, -1.5708)})

    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform_2})

# =====================================================================
# Parameter helpers
# =====================================================================

def update_translation_params(params):
    cell_widths = params["shelf_cell_width"]
    cell_heights = params["shelf_cell_height"]
    side_thickness = params["side_board_thickness"]
    div_thickness = params["division_board_thickness"]

    width = (len(cell_widths) - 1) * side_thickness * 2 + (len(cell_widths) - 1) * 0.001 + sum(cell_widths)
    height = (len(cell_heights) + 1) * div_thickness + params["bottom_board_height"] + sum(cell_heights)

    params["shelf_width"] = width
    params["shelf_height"] = height

    dist = -(width + side_thickness) / 2.0
    side_board_x_translation = [dist]
    for w in cell_widths:
        dist += side_thickness + w
        side_board_x_translation.append(dist)
        dist += side_thickness + 0.001
        side_board_x_translation.append(dist)
    side_board_x_translation = side_board_x_translation[:-1]

    d = params["bottom_board_height"] + div_thickness / 2.0
    division_board_z_translation = [d := d + h + div_thickness for h in [-div_thickness] + cell_heights]

    division_board_x_translation = [
        (side_board_x_translation[2 * i] + side_board_x_translation[2 * i + 1]) / 2.0
        for i in range(len(cell_widths))
    ]

    params["side_board_x_translation"] = side_board_x_translation
    params["division_board_x_translation"] = division_board_x_translation
    params["division_board_z_translation"] = division_board_z_translation
    params["bottom_gap_x_translation"] = division_board_x_translation
    return params


def _join_with_materials(parts):
    """Join objects into a newly linked object while preserving material slots."""

    parts = [p for p in parts if p is not None]
    if len(parts) == 0:
        return None
    if len(parts) == 1:
        return parts[0]

    materials = []
    material_index = {}

    def mapped_slot(mat):
        if mat is None:
            return 0
        key = mat.name
        if key not in material_index:
            material_index[key] = len(materials)
            materials.append(mat)
        return material_index[key]

    dg = bpy.context.evaluated_depsgraph_get()
    combined = bmesh.new()
    for p in parts:
        slot_map = [mapped_slot(mat) for mat in p.data.materials]
        eo = p.evaluated_get(dg)
        me = eo.to_mesh()
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(p.matrix_world)
        for face in tmp.faces:
            src = face.material_index
            face.material_index = slot_map[src] if src < len(slot_map) else 0
        tmp_me = bpy.data.meshes.new("_tmp")
        tmp.to_mesh(tmp_me)
        tmp.free()
        combined.from_mesh(tmp_me)
        bpy.data.meshes.remove(tmp_me)
        eo.to_mesh_clear()

    new_mesh = bpy.data.meshes.new("SingleCabinetFactory")
    combined.to_mesh(new_mesh)
    combined.free()
    joined = bpy.data.objects.new("SingleCabinetFactory", new_mesh)
    bpy.context.scene.collection.objects.link(joined)
    for mat in materials:
        joined.data.materials.append(mat)
    for p in parts:
        bpy.data.objects.remove(p, do_unlink=True)
    joined.location = (0, 0, 0)
    joined.rotation_euler = (0, 0, 0)
    joined.scale = (1, 1, 1)
    return joined


# =====================================================================
# Build — SingleCabinetFactory
#
# RNG sequence reproduces upstream exactly:
#   Phase 1: FixedSeed(factory_seed)
#     - SingleCabinetFactory.sample_params() consumes 3 uniforms (Dimensions)
#   Phase 2: FixedSeed(int_hash((factory_seed, 0)))
#     - get_material_params() temporarily re-seeds with factory_seed for 1 choice
#     - LargeShelfBaseFactory.get_asset_params() fills defaults for keys not set
#       by SingleCabinetFactory.sample_params() (side_board_thickness, gaps, screws,
#       attach_*; shelf_depth/cell_width/cell_height/bottom_board_height are skipped)
#     - get_door_params() may consume 1 RNG iff len(division_board_z_translation) > 5
#     - CabinetDoorBaseFactory.get_asset_params() rolls right door params
#     - Left door reuses all params (no RNG)
# =====================================================================

def build(seed=SEED):
    seed = int(seed)

    # ----- Phase 1: FixedSeed(factory_seed) for SingleCabinetFactory.sample_params -----
    py_st0, np_st0 = random.getstate(), np.random.get_state()
    random.seed(seed); np.random.seed(seed)
    dim_x = float(uniform(0.25, 0.35))
    dim_y = float(uniform(0.3, 0.7))
    dim_z = float(uniform(0.9, 1.8))
    random.setstate(py_st0); np.random.set_state(np_st0)

    # SingleCabinetFactory.sample_params: Dim-constrained shelf params
    bottom_board_height = 0.083
    shelf_depth = dim_x - 0.01
    num_h = max(1, int((dim_z - bottom_board_height) / 0.3))
    shelf_cell_height = [(dim_z - bottom_board_height) / num_h for _ in range(num_h)]
    shelf_cell_width = [dim_y]

    # ----- Phase 2: FixedSeed(int_hash((factory_seed, 0))) for create_asset -----
    derived = abs(int(hashlib.md5(f"{seed}0".encode()).hexdigest(), 16)) % (2**32 - 1)
    random.seed(derived); np.random.seed(derived)

    # get_material_params(): inner FixedSeed(factory_seed) consumes 1 RNG, then restores
    py_st1, np_st1 = random.getstate(), np.random.get_state()
    random.seed(seed); np.random.seed(seed)
    np.random.choice(3, p=[0.5, 0.2, 0.3])  # frame_material — value captured in Phase 1 at module level
    random.setstate(py_st1); np.random.set_state(np_st1)

    # LargeShelfBaseFactory.get_asset_params: roll defaults for keys not already set
    # (shelf_depth, shelf_cell_width, shelf_cell_height, bottom_board_height already set → skipped upstream)
    side_board_thickness = float(np.clip(normal(0.02, 0.002), 0.015, 0.025))
    backboard_thickness = 0.01
    bottom_board_y_gap = float(uniform(0.01, 0.05))
    division_board_thickness = float(np.clip(normal(0.02, 0.002), 0.015, 0.025))
    screw_depth_head = float(uniform(0.001, 0.004))
    screw_head_radius = float(uniform(0.001, 0.004))
    screw_width_gap = float(uniform(0.0, 0.02))
    screw_depth_gap = float(uniform(0.025, 0.06))
    # attach_length/width/thickness/gap consumed by upstream get_asset_params; geometry_nodes does not use them
    uniform(0.05, 0.1); uniform(0.01, 0.025); uniform(0.002, 0.005); uniform(0.0, 0.05)

    shelf_params = {
        "shelf_cell_width": shelf_cell_width,
        "shelf_cell_height": shelf_cell_height,
        "shelf_depth": shelf_depth,
        "side_board_thickness": side_board_thickness,
        "backboard_thickness": backboard_thickness,
        "bottom_board_y_gap": bottom_board_y_gap,
        "bottom_board_height": bottom_board_height,
        "division_board_thickness": division_board_thickness,
        "screw_depth_head": screw_depth_head,
        "screw_head_radius": screw_head_radius,
        "screw_width_gap": screw_width_gap,
        "screw_depth_gap": screw_depth_gap,
    }
    update_translation_params(shelf_params)

    shelf = make_geo_object(geometry_nodes, shelf_params)
    # Cabinet frame (body) — bound to the frame shader.
    shelf.data.materials.append(MAT_FRAME)

    # ----- Door dimensions from shelf -----
    shelf_width_total = shelf_params["shelf_width"] + side_board_thickness * 2
    if shelf_width_total < 0.55:
        door_width, num_door = shelf_width_total, 1
    else:
        door_width, num_door = shelf_width_total / 2.0 - 0.0005, 2

    div_zs = shelf_params["division_board_z_translation"]
    door_height = div_zs[-1] - div_zs[0] + division_board_thickness
    if len(div_zs) > 5 and bool(np.random.choice([True, False], p=[0.5, 0.5])):
        door_height = div_zs[3] - div_zs[0] + division_board_thickness

    # ----- CabinetDoorBaseFactory.get_asset_params (right door) -----
    edge_thickness_1 = float(uniform(0.01, 0.018))
    edge_width = float(uniform(0.03, 0.05))
    edge_thickness_2 = float(uniform(0.005, 0.008))
    edge_ramp_angle = float(uniform(0.6, 0.8))
    knob_R = float(uniform(0.003, 0.006))
    knob_length = float(uniform(0.018, 0.035))
    attach_gap_door = float(uniform(0.05, 0.15))
    door_attach_height = [attach_gap_door, door_height - attach_gap_door]
    has_mid_ramp = bool(np.random.choice([True, False], p=[0.6, 0.4]))
    if has_mid_ramp:
        # panel_material rolls (shader materials themselves are bound via
        # MAT_PANEL_LOWER/MAT_PANEL_UPPER above under the raw SEED; these
        # rolls only advance the geometry-phase RNG to match upstream)
        np.random.choice(2, p=[0.7, 0.3])
        np.random.choice(2, p=[0.6, 0.4])

    door_params = {
        "door_width": door_width,
        "door_height": door_height,
        "edge_thickness_1": edge_thickness_1,
        "edge_width": edge_width,
        "edge_thickness_2": edge_thickness_2,
        "edge_ramp_angle": edge_ramp_angle,
        "board_thickness": edge_thickness_1 - 0.005,
        "knob_R": knob_R,
        "knob_length": knob_length,
        "attach_height": door_attach_height,
        "has_mid_ramp": has_mid_ramp,
        "door_left_hinge": False,
    }
    right_door = make_geo_object(geometry_door_nodes, door_params)
    # Door frame + panel are represented as one mesh inside geometry_door_nodes;
    # the panel material rolled separately. We follow the same convention: the
    # door mesh gets MAT_FRAME, and we allocate a secondary slot for
    # face index selection stays on slot 0. (MAT_PANEL_UPPER only shows up on
    # multi-ramp doors but we still register it for parity.)
    right_door.data.materials.append(MAT_FRAME)
    right_door.data.materials.append(MAT_PANEL_LOWER)
    if has_mid_ramp:
        right_door.data.materials.append(MAT_PANEL_UPPER)
    door_params["door_left_hinge"] = True
    left_door = make_geo_object(geometry_door_nodes, door_params)
    left_door.data.materials.append(MAT_FRAME)
    left_door.data.materials.append(MAT_PANEL_LOWER)
    if has_mid_ramp:
        left_door.data.materials.append(MAT_PANEL_UPPER)

    # ----- Position doors at hinges (matches single_cabinet.get_cabinet_params) -----
    sd = shelf_depth / 2.0
    sw = shelf_params["shelf_width"] / 2.0
    bbh = bottom_board_height
    if num_door == 1:
        hinges = [(sd + 0.0025, -shelf_width_total / 2.0, bbh)]
        attach_pos = [(sd, -sw, bbh + z) for z in door_attach_height]
    else:
        hinges = [(sd + 0.008, -shelf_width_total / 2.0, bbh),
                  (sd + 0.008,  shelf_width_total / 2.0, bbh)]
        attach_pos = [(sd, -sw, bbh + z) for z in door_attach_height] + \
                     [(sd,  sw, bbh + z) for z in door_attach_height]

    for door, hp in zip([right_door, left_door], hinges):
        door.location = (float(hp[0]), float(hp[1]), float(hp[2]))
        apply_transform(door, loc=True, rot=True, scale=True)

    # ----- Hinge attach geometry (faithful to single_cabinet.geometry_cabinet_nodes) -----
    attach_objs = []
    for pos in attach_pos:
        center_x, center_y, center_z = float(pos[0]), float(pos[1]), float(pos[2])
        bpy.ops.mesh.primitive_cube_add(size=1, location=(center_x - 0.027, center_y, center_z))
        cube_a = bpy.context.active_object
        cube_a.scale = (0.02 / 2, 0.0006 / 2, 0.045 / 2)
        apply_transform(cube_a, loc=False, scale=True)
        cube_a.data.materials.append(MAT_HINGE)
        attach_objs.append(cube_a)

        bpy.ops.mesh.primitive_cube_add(size=1, location=(center_x - 0.017, center_y, center_z))
        cube_b = bpy.context.active_object
        cube_b.scale = (0.034 / 2, 0.0005 / 2, 0.02 / 2)
        apply_transform(cube_b, loc=False, scale=True)
        cube_b.data.materials.append(MAT_HINGE)
        attach_objs.append(cube_b)

    # ----- Join shelf + doors + hinge attaches (material-preserving) -----
    # For num_door==1, upstream geometry_cabinet_nodes builds left_door for RNG
    # fidelity but does not include it in the output; we drop it before joining.
    door_components = [right_door] if num_door == 1 else [right_door, left_door]
    if num_door == 1 and left_door is not None:
        bpy.data.objects.remove(left_door, do_unlink=True)
        left_door = None

    join_components = [shelf] + door_components + attach_objs
    obj = _join_with_materials(join_components)

    if obj is not None:
        obj.name = "SingleCabinetFactory"
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_smooth()
        obj.select_set(False)
        obj.data.update()

    return obj


build(SEED)
