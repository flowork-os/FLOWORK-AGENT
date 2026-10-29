# [FL_INDEX: keywords="blender_factory, procedural_3d, KitchenSpaceFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: KitchenSpaceFactory | Category: factories_tex
# Prompt: A 3D model of a full kitchen cabinet arrangement rendered from a three-quarter perspective, featuring an upper wall cabinet unit with open compartments mounted above a lower base cabinet run with a light-colored countertop surface, closed door panels, and a visible backsplash area between the two tiers.

"""KitchenSpaceFactory (textured).

Texture-enabled rewrite of `objects_blender/shelves/KitchenSpaceFactory.py`.
Geometry is copied verbatim from the source file (the Level-2 inlined
KitchenCabinet infrastructure + KitchenSpaceFactory composer); materials
are assigned per part (frame / board / countertop) using hand-crafted
raw-bpy shaders translated from:

Material sampling mirrors the order executed by when
`KitchenSpaceFactory.create_asset` composes KitchenCabinet sub-factories:

    KitchenCabinetBaseFactory.get_material_params():
        1. key = np.random.choice(["white", "black_wood", "wood"], p=[0.4, 0.3, 0.3])
        2. frame_material = shader_shelves_{white, black_wood_z, wood_z}
        3. board_material = shader_shelves_{white, black_wood, wood}
    geometry_nodes_add_cabinet_top:
        4. countertop_material = shader_marble   (deterministic; no random draws)

In each KitchenCabinetFactory sub-instance created by the
KitchenSpaceFactory uses the same factory_seed, and its
`get_material_params()` wraps the sampling inside `FixedSeed(factory_seed)`
— so every bottom/top/mid cabinet ends up with the same plywood pair.
We replicate that by sampling once at module load (Phase 1, raw SEED)
and reusing the resulting MAT_FRAME/MAT_BOARD on every cabinet part.

`finalize_assets` is NOT defined on KitchenSpaceFactory, KitchenCabinetFactory,
or any shelves base class — does not apply wear_tear to this
factory, so this script deliberately skips the wear_tear scratch / edge_wear
and `kitchen_cabinet.py` contain no `finalize_assets` method and no
`wear_tear` / `scratches` / `edge_wear` import.)
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
    Returns (mix_2_out, colorramp_1_out, colorramp_2_out). Faithfully
    replicates plywood.py lines 75-165."""
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

    # "Musgrave" substitute: Blender 5.0 removed ShaderNodeTexMusgrave; use
    # a high-detail NoiseTexture driven off the previous noise's Fac output.
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
    """shader_shelves_black_wood (+ _z variant)."""

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
    """shader_shelves_wood (+ _z variant) — blond plywood."""

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
# Kitchen-cabinet material sampler — mirrors
# Returns (frame_material, board_material). The two shaders share the same
# "key" but the frame uses the Z-axis-tuned variant (matching plywood.py's
# shader_shelves_*_z wrappers).
# ----------------------------------------------------------------------------
def sample_kitchen_cabinet_materials():
    key = np.random.choice(["white", "black_wood", "wood"], p=[0.4, 0.3, 0.3])
    if key == "white":
        p = _sample_white_params()
        frame_mat = make_shelves_white("KSFrame", params=p)
        board_mat = make_shelves_white("KSBoard", params=p)
    elif key == "black_wood":
        p = _sample_black_wood_params()
        frame_mat = make_shelves_black_wood_z("KSFrame", params=p)
        board_mat = make_shelves_black_wood("KSBoard", params=p)
    else:  # "wood"
        p = _sample_wood_params()
        frame_mat = make_shelves_wood_z("KSFrame", params=p)
        board_mat = make_shelves_wood("KSBoard", params=p)
    return frame_mat, board_mat

# ----------------------------------------------------------------------------
# shader_marble  (ceramic/marble.py:12)
# Faithful raw-bpy translation of the NodeWrangler version. Used for the
# ----------------------------------------------------------------------------
def make_marble(name="MarbleCountertop"):
    mat = _new_material(name)
    nt = mat.node_tree

    texture_coordinate = nt.nodes.new("ShaderNodeTexCoord")

    # Vector Math, operation=SCALE, vector=tex_coord.Object
    scale_vmath = nt.nodes.new("ShaderNodeVectorMath")
    scale_vmath.operation = "SCALE"
    nt.links.new(texture_coordinate.outputs["Object"], scale_vmath.inputs[0])

    vector_rotate = nt.nodes.new("ShaderNodeVectorRotate")
    if hasattr(vector_rotate, "rotation_type"):
        try: vector_rotate.rotation_type = "EULER_XYZ"
        except TypeError: pass
    nt.links.new(scale_vmath.outputs["Vector"], vector_rotate.inputs["Vector"])

    seed = nt.nodes.new("ShaderNodeValue")
    seed.label = "seed"
    seed.outputs[0].default_value = 0.0

    scale_1 = nt.nodes.new("ShaderNodeValue")
    scale_1.label = "scale"
    scale_1.outputs[0].default_value = 3.0

    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(scale_1.outputs[0], add.inputs[0])
    add.inputs[1].default_value = 1.0

    def _make_noise(is_4d=True):
        n = nt.nodes.new("ShaderNodeTexNoise")
        if is_4d and hasattr(n, "noise_dimensions"):
            try: n.noise_dimensions = "4D"
            except TypeError: pass
        return n

    noise_texture_2 = _make_noise(is_4d=True)
    nt.links.new(vector_rotate.outputs["Vector"], noise_texture_2.inputs["Vector"])
    if "W" in noise_texture_2.inputs:
        nt.links.new(seed.outputs[0], noise_texture_2.inputs["W"])
    nt.links.new(add.outputs[0], noise_texture_2.inputs["Scale"])
    if "Detail" in noise_texture_2.inputs:
        noise_texture_2.inputs["Detail"].default_value = 15.0

    map_range = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(_noise_fac_output(noise_texture_2), map_range.inputs[0])
    map_range.inputs[1].default_value = 0.48
    map_range.inputs[2].default_value = 0.60

    noise_texture = _make_noise(is_4d=True)
    nt.links.new(vector_rotate.outputs["Vector"], noise_texture.inputs["Vector"])
    if "W" in noise_texture.inputs:
        nt.links.new(seed.outputs[0], noise_texture.inputs["W"])
    nt.links.new(scale_1.outputs[0], noise_texture.inputs["Scale"])
    if "Detail" in noise_texture.inputs:
        noise_texture.inputs["Detail"].default_value = 15.0

    noise_texture_3 = _make_noise(is_4d=False)
    nt.links.new(_noise_fac_output(noise_texture), noise_texture_3.inputs["Vector"])
    noise_texture_3.inputs["Scale"].default_value = 8.0
    if "Detail" in noise_texture_3.inputs:
        noise_texture_3.inputs["Detail"].default_value = 15.0

    voronoi_texture = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi_texture, "feature"):
        try: voronoi_texture.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    if hasattr(voronoi_texture, "voronoi_dimensions"):
        try: voronoi_texture.voronoi_dimensions = "4D"
        except TypeError:
            try: voronoi_texture.voronoi_dimensions = "3D"
            except TypeError: pass
    nt.links.new(_noise_fac_output(noise_texture_3), voronoi_texture.inputs["Vector"])
    if "W" in voronoi_texture.inputs:
        voronoi_texture.inputs["W"].default_value = 1.64
    voronoi_texture.inputs["Scale"].default_value = 3.0

    colorramp_1 = nt.nodes.new("ShaderNodeValToRGB")
    fac_in1 = colorramp_1.inputs.get("Fac") or colorramp_1.inputs[0]
    dist_out = voronoi_texture.outputs.get("Distance") or voronoi_texture.outputs[0]
    nt.links.new(dist_out, fac_in1)
    colorramp_1.color_ramp.elements[0].position = 0.0
    colorramp_1.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = 0.03
    colorramp_1.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    multiply = nt.nodes.new("ShaderNodeMath")
    multiply.operation = "MULTIPLY"
    nt.links.new(map_range.outputs["Result"], multiply.inputs[0])
    cr1_color = colorramp_1.outputs.get("Color") or colorramp_1.outputs[0]
    nt.links.new(cr1_color, multiply.inputs[1])

    noise_texture_1 = _make_noise(is_4d=True)
    nt.links.new(_noise_fac_output(noise_texture), noise_texture_1.inputs["Vector"])
    if "W" in noise_texture_1.inputs:
        nt.links.new(seed.outputs[0], noise_texture_1.inputs["W"])
    noise_texture_1.inputs["Scale"].default_value = 8.0
    if "Detail" in noise_texture_1.inputs:
        noise_texture_1.inputs["Detail"].default_value = 15.0

    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    mix_1.inputs[0].default_value = 0.8
    nt.links.new(_noise_fac_output(noise_texture), mix_1.inputs[6])
    nt.links.new(_noise_fac_output(noise_texture_1), mix_1.inputs[7])

    colorramp = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = colorramp.inputs.get("Fac") or colorramp.inputs[0]
    nt.links.new(mix_1.outputs[2], fac_in)
    colorramp.color_ramp.elements[0].position = 0.3
    colorramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    colorramp.color_ramp.elements[1].position = 0.9
    colorramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    mix_final = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_final, "data_type"):
        mix_final.data_type = "RGBA"
    nt.links.new(multiply.outputs[0], mix_final.inputs[0])
    cramp_color = colorramp.outputs.get("Color") or colorramp.outputs[0]
    nt.links.new(cramp_color, mix_final.inputs[6])
    mix_final.inputs[7].default_value = (0.0376, 0.0179, 0.0033, 1.0)

    displacement = nt.nodes.new("ShaderNodeDisplacement")
    displacement.inputs["Midlevel"].default_value = 0.0
    displacement.inputs["Scale"].default_value = 0.02
    nt.links.new(multiply.outputs[0], displacement.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        **{"Specular IOR Level": 0.6, "Roughness": 0.1},
    )
    # NOTE: shader_marble hooks mix_1.outputs[2] into Base Color,
    # not mix_final. Faithfully preserved here.
    nt.links.new(mix_1.outputs[2], bsdf.inputs["Base Color"])

    _connect_output(nt, bsdf, displacement=displacement.outputs[0])
    return mat

# ── Scene cleanup ──
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)

#   Mirrors the order executed by while composing kitchen cabinets:
#     1. KitchenCabinetBaseFactory.get_material_params() samples a style key
#        then resolves frame_material + board_material shaders.
#     2. geometry_nodes_add_cabinet_top creates shader_marble for the top
#        slab (deterministic — no random draws).
#   wear_tear is NOT applied: neither kitchen_space.py nor kitchen_cabinet.py
#   defines finalize_assets or references wear_tear / scratches / edge_wear.
SEED = int(os.environ.get('SEED', 0))
seed_all(SEED)
MAT_FRAME, MAT_BOARD = sample_kitchen_cabinet_materials()
MAT_COUNTERTOP = make_marble("KSCountertop")

# --- Original geometry code (copied verbatim from objects_blender/shelves/
#     KitchenSpaceFactory.py), with per-part material bindings inserted at
#     the end of each build_* function and on the countertop slab. ===========

# -----------------------------------------------------------------------------
# Seeding + small utilities
# -----------------------------------------------------------------------------

def int_hash(x, mod=(2**32 - 1)):
    m = hashlib.md5()
    for s in (x if isinstance(x, (tuple, list)) else [x]):
        m.update(str(s).encode('utf-8'))
    return abs(int(m.hexdigest(), 16)) % mod

@contextmanager
def FixedSeed(seed):
    py_state, np_state = random.getstate(), np.random.get_state()
    random.seed(int(seed))
    np.random.seed(int(seed))
    try:
        yield
    finally:
        random.setstate(py_state)
        np.random.set_state(np_state)

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def apply_transform(obj, loc=False, rot=True, scale=True):
    _select_none()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    obj.select_set(False)
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

def join_objects(objs):
    """Merge mesh objects into a newly linked object, preserving material slots."""

    objs = [o for o in objs if o is not None and o.name in bpy.data.objects and o.type == 'MESH']
    if not objs:
        return None
    if len(objs) == 1:
        return objs[0]

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
    for o in objs:
        slot_map = [mapped_slot(mat) for mat in o.data.materials]
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)
        for face in tmp.faces:
            src = face.material_index
            face.material_index = slot_map[src] if src < len(slot_map) else 0
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
    for mat in materials:
        result.data.materials.append(mat)
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    return result

def new_bbox(x0, x1, y0, y1, z0, z1):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.scale = ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2)
    obj.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    apply_transform(obj, loc=True)
    return obj

# -----------------------------------------------------------------------------
# bmesh primitive helpers
# -----------------------------------------------------------------------------

def _add_box(bm, sx, sy, sz, cx, cy, cz):
    """Add an axis-aligned box to an existing bmesh."""

    if sx <= 0 or sy <= 0 or sz <= 0:
        return
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    verts = [
        bm.verts.new((cx - hx, cy - hy, cz - hz)),
        bm.verts.new((cx + hx, cy - hy, cz - hz)),
        bm.verts.new((cx + hx, cy + hy, cz - hz)),
        bm.verts.new((cx - hx, cy + hy, cz - hz)),
        bm.verts.new((cx - hx, cy - hy, cz + hz)),
        bm.verts.new((cx + hx, cy - hy, cz + hz)),
        bm.verts.new((cx + hx, cy + hy, cz + hz)),
        bm.verts.new((cx - hx, cy + hy, cz + hz)),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    for f in faces:
        try:
            bm.faces.new([verts[i] for i in f])
        except ValueError:
            pass

def _add_cylinder(bm, radius, depth, cx, cy, cz, segments=32, axis='Z'):
    if radius <= 0 or depth <= 0:
        return
    half = depth / 2.0
    ring_lo = []
    ring_hi = []
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        c, s = math.cos(theta), math.sin(theta)
        if axis == 'Z':
            lo = (cx + radius * c, cy + radius * s, cz - half)
            hi = (cx + radius * c, cy + radius * s, cz + half)
        elif axis == 'Y':
            lo = (cx + radius * c, cy - half, cz + radius * s)
            hi = (cx + radius * c, cy + half, cz + radius * s)
        else:
            lo = (cx - half, cy + radius * c, cz + radius * s)
            hi = (cx + half, cy + radius * c, cz + radius * s)
        ring_lo.append(bm.verts.new(lo))
        ring_hi.append(bm.verts.new(hi))
    for i in range(segments):
        j = (i + 1) % segments
        try:
            bm.faces.new([ring_lo[i], ring_lo[j], ring_hi[j], ring_hi[i]])
        except ValueError:
            pass
    try:
        bm.faces.new(list(reversed(ring_lo)))
    except ValueError:
        pass
    try:
        bm.faces.new(ring_hi)
    except ValueError:
        pass

def _finalize_bmesh_obj(bm, name):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    return obj

# -----------------------------------------------------------------------------
# AssetFactory base
# -----------------------------------------------------------------------------

class AssetFactory:
    _build_fn = None

    def __init__(self, factory_seed, coarse=False):
        self.factory_seed = int(factory_seed)

    def get_asset_params(self, i=0):
        return {}

    def create_asset(self, i=0, **kwargs):
        if self._build_fn is None:
            raise NotImplementedError
        obj_params = self.get_asset_params(i)
        obj = self._build_fn(obj_params)
        if kwargs.get("ret_params", False):
            return obj, obj_params
        return obj

    def __call__(self, i=0, **kwargs):
        py_state, np_state = random.getstate(), np.random.get_state()
        derived = int_hash((self.factory_seed, i))
        random.seed(derived)
        np.random.seed(derived)
        try:
            return self.create_asset(i=i, **kwargs)
        finally:
            random.setstate(py_state)
            np.random.set_state(np_state)

# Shelf frame (LargeShelfBaseFactory)

def build_shelf_frame(params):
    bm = bmesh.new()

    shelf_depth = params["shelf_depth"]
    shelf_width = params["shelf_width"]
    shelf_height = params["shelf_height"]
    side_thickness = params["side_board_thickness"]
    back_thickness = params["backboard_thickness"]
    div_thickness = params["division_board_thickness"]
    bottom_height = params["bottom_board_height"]
    y_gap = params["bottom_board_y_gap"]
    cell_widths = params["shelf_cell_width"]

    depth_ext = shelf_depth + 0.004
    side_height = shelf_height + 0.002
    for sx in params["side_board_x_translation"]:
        _add_box(bm, side_thickness, depth_ext, side_height,
                 sx, 0.0, side_height / 2.0)

    back_width = shelf_width + 2 * side_thickness
    back_height = shelf_height - 0.001
    _add_box(bm, back_width, back_thickness, back_height,
             0.0, -(shelf_depth + back_thickness) / 2.0, back_height / 2.0)

    for i, cell_w in enumerate(cell_widths):
        cx = params["bottom_gap_x_translation"][i]
        _add_box(bm, cell_w, side_thickness, bottom_height,
                 cx, shelf_depth / 2.0 - y_gap, bottom_height / 2.0)

    sw_depth = params["screw_depth_head"]
    sw_radius = params["screw_head_radius"]
    sw_gap = params["screw_width_gap"]
    for i, cell_w in enumerate(cell_widths):
        cx = params["division_board_x_translation"][i]
        for z in params["division_board_z_translation"]:
            _add_box(bm, cell_w, shelf_depth, div_thickness,
                     cx, 0.0, z)
            sz = z - div_thickness / 2.0
            for sx_sign in (-1, 1):
                for sy_sign in (-1, 1):
                    sx = cx + sx_sign * (cell_w / 2.0 - sw_gap)
                    sy = sy_sign * (shelf_depth / 2.0 - sw_gap)
                    _add_cylinder(bm, sw_radius, sw_depth, sx, sy, sz,
                                  segments=16, axis='Z')

    obj = _finalize_bmesh_obj(bm, "cabinet_frame")
    obj.rotation_euler = (0.0, 0.0, -math.pi / 2.0)
    apply_transform(obj, rot=True)
    # Frame uses frame_material (Z-axis tuned variant mirrors plywood.shader_shelves_*_z)
    obj.data.materials.append(MAT_FRAME)
    return obj

class LargeShelfBaseFactory(AssetFactory):
    _build_fn = staticmethod(build_shelf_frame)

    def __init__(self, factory_seed, coarse=False):
        super().__init__(factory_seed, coarse=coarse)
        self.params = {}

    def sample_params(self):
        return self.params.copy()

    def get_asset_params(self, i=0):
        params = self.sample_params()
        if params.get("shelf_depth", None) is None:
            params["shelf_depth"] = np.clip(np.random.normal(0.26, 0.03), 0.18, 0.36)
        if params.get("side_board_thickness", None) is None:
            params["side_board_thickness"] = np.clip(np.random.normal(0.02, 0.002), 0.015, 0.025)
        if params.get("back_board_thickness", None) is None:
            params["backboard_thickness"] = 0.01
        if params.get("bottom_board_y_gap", None) is None:
            params["bottom_board_y_gap"] = uniform(0.01, 0.05)
        if params.get("bottom_board_height", None) is None:
            params["bottom_board_height"] = np.clip(
                np.random.normal(0.083, 0.01), 0.05, 0.11
            ) * np.random.choice([1.0, 0.0], p=[0.8, 0.2])
        if params.get("division_board_thickness", None) is None:
            params["division_board_thickness"] = np.clip(
                np.random.normal(0.02, 0.002), 0.015, 0.025
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
            num_h_cells = np.random.randint(1, 4)
            params["shelf_cell_width"] = [
                np.random.choice([0.76, 0.36], p=[0.5, 0.5])
                * np.clip(np.random.normal(1.0, 0.1), 0.75, 1.25)
                for _ in range(num_h_cells)
            ]
        if params.get("shelf_cell_height", None) is None:
            num_v_cells = np.random.randint(3, 8)
            params["shelf_cell_height"] = [
                0.3 * np.clip(np.random.normal(1.0, 0.1), 0.75, 1.25)
                for _ in range(num_v_cells)
            ]
        params = self.update_translation_params(params)
        # Preserve the dead random draw the original made for materials so
        # the RNG sequence stays in sync with downstream factories.
        if params.get("frame_material", None) is None:
            np.random.choice(["white", "black_wood", "wood"], p=[0.4, 0.3, 0.3])
        params["tag_support"] = True
        return params

    def update_translation_params(self, params):
        cell_widths = params["shelf_cell_width"]
        cell_heights = params["shelf_cell_height"]
        side_thickness = params["side_board_thickness"]
        div_thickness = params["division_board_thickness"]

        width = (len(cell_widths) - 1) * side_thickness * 2 + (len(cell_widths) - 1) * 0.001
        height = (len(cell_heights) + 1) * div_thickness + params["bottom_board_height"]
        for w in cell_widths:
            width += w
        for h in cell_heights:
            height += h

        params["shelf_width"] = width
        params["shelf_height"] = height
        params["attach_z_translation"] = height - div_thickness

        dist = -(width + side_thickness) / 2.0
        side_board_x_translation = [dist]
        for w in cell_widths:
            dist += side_thickness + w
            side_board_x_translation.append(dist)
            dist += side_thickness + 0.001
            side_board_x_translation.append(dist)
        side_board_x_translation = side_board_x_translation[:-1]

        dist = params["bottom_board_height"] + div_thickness / 2.0
        division_board_z_translation = [dist]
        for h in cell_heights:
            dist += h + div_thickness
            division_board_z_translation.append(dist)

        division_board_x_translation = []
        for i in range(len(cell_widths)):
            division_board_x_translation.append(
                (side_board_x_translation[2 * i] + side_board_x_translation[2 * i + 1]) / 2.0
            )

        params["side_board_x_translation"] = side_board_x_translation
        params["division_board_x_translation"] = division_board_x_translation
        params["division_board_z_translation"] = division_board_z_translation
        params["bottom_gap_x_translation"] = division_board_x_translation

        return params

# Door (CabinetDoorBaseFactory)

def build_door(params):
    bm = bmesh.new()

    door_width = params["door_width"]
    door_height = params["door_height"]
    edge_width = params["edge_width"]
    t1 = params["edge_thickness_1"]
    t2 = params["edge_thickness_2"]
    board_thickness = max(params["board_thickness"], 0.002)
    has_mid_ramp = params["has_mid_ramp"]
    knob_r = params["knob_R"]
    knob_len = params["knob_length"]
    left_hinge = params["door_left_hinge"]

    total_t = t1 + t2
    xc = -door_width / 2.0

    _add_box(bm, edge_width, total_t, door_height,
             -door_width + edge_width / 2.0, total_t / 2.0, door_height / 2.0)
    _add_box(bm, edge_width, total_t, door_height,
             -edge_width / 2.0, total_t / 2.0, door_height / 2.0)
    _add_box(bm, door_width, total_t, edge_width,
             xc, total_t / 2.0, door_height - edge_width / 2.0)
    _add_box(bm, door_width, total_t, edge_width,
             xc, total_t / 2.0, edge_width / 2.0)

    panel_w = door_width - 0.0001
    panel_h = door_height - 0.0001
    panel_y = t1 / 2.0 + 0.004
    if has_mid_ramp:
        half_h = door_height / 2.0 - 0.0001
        _add_box(bm, panel_w, t1, half_h,
                 xc, panel_y, door_height / 4.0)
        _add_box(bm, panel_w, t1, half_h,
                 xc, panel_y, door_height * 3.0 / 4.0)
        _add_box(bm, door_width, total_t, edge_width,
                 xc, total_t / 2.0, door_height / 2.0)
    else:
        _add_box(bm, panel_w, t1, panel_h,
                 xc, panel_y, door_height / 2.0)

    knob_cyl_len = t1 + t2 + knob_len
    knob_x = -door_width + edge_width / 2.0 - 0.005
    knob_y = knob_cyl_len / 2.0
    knob_z = door_height / 2.0
    _add_cylinder(bm, knob_r, knob_cyl_len, knob_x, knob_y, knob_z,
                  segments=32, axis='Y')

    if left_hinge:
        for v in bm.verts:
            v.co.x = -v.co.x
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))

    obj = _finalize_bmesh_obj(bm, "cabinet_door")
    obj.rotation_euler = (0.0, 0.0, -math.pi / 2.0)
    apply_transform(obj, rot=True)
    # Doors use board_material (non-Z variant), mirroring plywood.shader_shelves_*
    obj.data.materials.append(MAT_BOARD)
    return obj

class CabinetDoorBaseFactory(AssetFactory):
    _build_fn = staticmethod(build_door)

    def __init__(self, factory_seed, coarse=False):
        super().__init__(factory_seed, coarse=coarse)
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
        # Preserve the dead random draws for material selection so the RNG
        # sequence stays in sync with the original factory.
        if params.get("frame_material", None) is None:
            np.random.choice(["white", "black_wood", "wood"], p=[0.5, 0.2, 0.3])
            if params["has_mid_ramp"]:
                np.random.choice(["white", "glass"], p=[0.7, 0.3])
                np.random.choice(["white", "glass"], p=[0.6, 0.4])
        return params

# Drawer (CabinetDrawerBaseFactory)

def build_drawer(params):
    bm = bmesh.new()

    board_t = params["drawer_board_thickness"]
    board_w = params["drawer_board_width"]
    board_h = params["drawer_board_height"]
    drawer_depth = params["drawer_depth"]
    drawer_width = params["drawer_width"]
    side_h = params["drawer_side_height"]
    knob_r = params["knob_radius"]
    knob_len = params["knob_length"]

    _add_box(bm, board_w, board_t, board_h,
             0.0, -board_t / 2.0, board_h / 2.0)

    inner_depth = drawer_depth - board_t
    body_y = -inner_depth / 2.0 - 0.0001
    body_z = side_h / 2.0 + 0.01

    _add_box(bm, board_t, inner_depth, side_h,
             -drawer_width / 2.0, body_y, body_z)
    _add_box(bm, board_t, inner_depth, side_h,
             drawer_width / 2.0, body_y, body_z)
    _add_box(bm, drawer_width + board_t - 0.0001, inner_depth, board_t,
             0.0, body_y, 0.01)
    _add_box(bm, drawer_width, board_t, side_h,
             0.0, -inner_depth + board_t / 2.0, body_z)

    _add_cylinder(bm, knob_r, knob_len,
                  0.0, knob_len / 2.0 + 0.0001, board_h / 2.0,
                  segments=32, axis='Y')

    obj = _finalize_bmesh_obj(bm, "drawer")
    obj.rotation_euler = (0.0, 0.0, -math.pi / 2.0)
    apply_transform(obj, rot=True)
    # Drawers use board_material / drawer_material (same slot in kitchen_cabinet.py)
    obj.data.materials.append(MAT_BOARD)
    return obj

class CabinetDrawerBaseFactory(AssetFactory):
    _build_fn = staticmethod(build_drawer)

    def __init__(self, factory_seed, coarse=False):
        super().__init__(factory_seed, coarse=coarse)
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
            np.random.choice(["white", "black_wood", "wood"], p=[0.5, 0.2, 0.3])
            np.random.choice(["white", "metal"], p=[0.5, 0.5])
        return params

# KitchenCabinet assembly

class KitchenCabinetBaseFactory(AssetFactory):
    def __init__(self, factory_seed, coarse=False):
        super().__init__(factory_seed, coarse=coarse)
        self.frame_params = {}
        self.cabinet_widths = []
        self.frame_fac = LargeShelfBaseFactory(factory_seed)
        self.door_fac = CabinetDoorBaseFactory(factory_seed)
        self.drawer_fac = CabinetDrawerBaseFactory(factory_seed)
        self.drawer_only = False
        with FixedSeed(factory_seed):
            self.params = self.sample_params()

    def sample_params(self):
        pass

    def get_frame_params(self, width, i=0):
        params = self.frame_params.copy()
        params["shelf_cell_width"] = [width]
        return params

    def get_attach_params(self, attach_type, i=0):
        param_sets = []
        if attach_type == "none":
            pass
        elif attach_type == "door":
            params = dict()
            shelf_width = (
                self.frame_params["shelf_width"]
                + self.frame_params["side_board_thickness"] * 2
            )
            if shelf_width <= 0.6:
                params["door_width"] = shelf_width
                params["has_mid_ramp"] = False
                params["edge_thickness_1"] = 0.01
                params["door_hinge_pos"] = [(
                    self.frame_params["shelf_depth"] / 2.0 + 0.0025,
                    -shelf_width / 2.0,
                    self.frame_params["bottom_board_height"],
                )]
                params["door_open_angle"] = 0
            else:
                params["door_width"] = shelf_width / 2.0 - 0.0005
                params["has_mid_ramp"] = False
                params["edge_thickness_1"] = 0.01
                params["door_hinge_pos"] = [
                    (
                        self.frame_params["shelf_depth"] / 2.0 + 0.008,
                        -shelf_width / 2.0,
                        self.frame_params["bottom_board_height"],
                    ),
                    (
                        self.frame_params["shelf_depth"] / 2.0 + 0.008,
                        shelf_width / 2.0,
                        self.frame_params["bottom_board_height"],
                    ),
                ]
                params["door_open_angle"] = 0
            params["door_height"] = (
                self.frame_params["division_board_z_translation"][-1]
                - self.frame_params["division_board_z_translation"][0]
                + self.frame_params["division_board_thickness"]
            )
            param_sets.append(params)
        elif attach_type == "drawer":
            for i, h in enumerate(self.frame_params["shelf_cell_height"]):
                params = dict()
                drawer_h = (
                    self.frame_params["division_board_z_translation"][i + 1]
                    - self.frame_params["division_board_z_translation"][i]
                    - self.frame_params["division_board_thickness"]
                )
                params["drawer_board_width"] = self.frame_params["shelf_width"]
                params["drawer_board_height"] = drawer_h
                params["drawer_depth"] = self.frame_params["shelf_depth"]
                params["drawer_hinge_pos"] = (
                    self.frame_params["shelf_depth"] / 2.0,
                    0,
                    (
                        self.frame_params["division_board_thickness"] / 2.0
                        + self.frame_params["division_board_z_translation"][i]
                    ),
                )
                param_sets.append(params)
        else:
            raise NotImplementedError
        return param_sets

    def get_cabinet_params(self, i=0):
        y_translations = []
        accum = 0.0
        thickness = self.frame_params.get("side_board_thickness", 0.005)
        for w in self.cabinet_widths:
            accum += thickness + w / 2.0
            y_translations.append(accum)
            accum += thickness + w / 2.0 + 0.0005
        return y_translations

    def create_cabinet_components(self, i, drawer_only=False):
        components = []
        for k, w in enumerate(self.cabinet_widths):
            frame_params = self.get_frame_params(w, i=i)
            self.frame_fac.params = frame_params
            frame, frame_params = self.frame_fac.create_asset(i=i, ret_params=True)
            frame.name = f"cabinet_frame_{k}"
            self.frame_params = frame_params

            if drawer_only:
                attach_type = np.random.choice(["drawer", "door"], p=[0.5, 0.5])
            else:
                attach_type = np.random.choice(
                    ["drawer", "door", "none"], p=[0.4, 0.4, 0.2]
                )

            attach_params = self.get_attach_params(attach_type, i=i)
            if attach_type == "door":
                self.door_fac.params = attach_params[0]
                self.door_fac.params["door_left_hinge"] = False
                right_door, door_obj_params = self.door_fac.create_asset(i=i, ret_params=True)
                right_door.name = f"cabinet_right_door_{k}"
                self.door_fac.params = door_obj_params
                self.door_fac.params["door_left_hinge"] = True
                left_door, _ = self.door_fac.create_asset(i=i, ret_params=True)
                left_door.name = f"cabinet_left_door_{k}"
                components.append([frame, "door", [right_door, left_door, attach_params[0]]])

            elif attach_type == "drawer":
                drawers = []
                for j, p in enumerate(attach_params):
                    self.drawer_fac.params = p
                    drawer = self.drawer_fac.create_asset(i=i)
                    drawer.name = f"drawer_{k}_layer{j}"
                    drawers.append([drawer, p])
                components.append([frame, "drawer", drawers])

            elif attach_type == "none":
                components.append([frame, "none"])

            else:
                raise NotImplementedError

        return components

    def create_asset(self, i=0, **params):
        components = self.create_cabinet_components(i=i, drawer_only=self.drawer_only)
        cabinet_params = self.get_cabinet_params(i=i)

        join_objs = []
        for k, component in enumerate(components):
            y_off = cabinet_params[k]
            frame = component[0]
            frame.location = (0, y_off, 0)
            apply_transform(frame, loc=True)
            join_objs.append(frame)

            if component[1] == "door":
                right_door, left_door, attach = component[2]
                hinges = attach["door_hinge_pos"]
                rh = hinges[0]
                right_door.location = (rh[0], rh[1] + y_off, rh[2])
                apply_transform(right_door, loc=True)
                join_objs.append(right_door)
                if len(hinges) > 1:
                    lh = hinges[1]
                    left_door.location = (lh[0], lh[1] + y_off, lh[2])
                    apply_transform(left_door, loc=True)
                    join_objs.append(left_door)
                else:
                    delete(left_door)

            elif component[1] == "drawer":
                for drawer, dparams in component[2]:
                    dh = dparams["drawer_hinge_pos"]
                    drawer.location = (dh[0], dh[1] + y_off, dh[2])
                    apply_transform(drawer, loc=True)
                    join_objs.append(drawer)

        return join_objects(join_objs)

class KitchenCabinetFactory(KitchenCabinetBaseFactory):
    def __init__(self, factory_seed, coarse=False, dimensions=None, drawer_only=False):
        self.dimensions = dimensions
        super().__init__(factory_seed, coarse=coarse)
        self.drawer_only = drawer_only

    def sample_params(self):
        params = dict()
        if self.dimensions is None:
            dimensions = (uniform(0.25, 0.35), uniform(1.0, 4.0), uniform(0.5, 1.3))
            self.dimensions = dimensions
        else:
            dimensions = self.dimensions
        params["Dimensions"] = dimensions

        params["shelf_depth"] = params["Dimensions"][0] - 0.01
        num_h = int((params["Dimensions"][2] - 0.06) / 0.3)
        params["shelf_cell_height"] = [
            (params["Dimensions"][2] - 0.06) / num_h for _ in range(num_h)
        ]
        params["side_board_thickness"] = 0.02
        params["division_board_thickness"] = 0.02
        params["bottom_board_height"] = 0.06

        self.frame_params = params

        n_cells = max(int(params["Dimensions"][1] / 0.45), 1)
        intervals = np.random.uniform(0.55, 1.0, size=(n_cells,))
        intervals = intervals / intervals.sum() * params["Dimensions"][1]
        self.cabinet_widths = intervals.tolist()

# Kitchen space assembly

def add_countertop(cabinet_obj, thickness=0.05):
    """Glue a flat countertop slab on top of a finished cabinet object.

    Original used a nodegroup (`geometry_nodes_add_cabinet_top`) that read
    the cabinet's bbox, produced a square cube via a `generate_table_top`
    helper, then joined it in. Net effect: slab size = (dx × 0.99979,
    dy × 0.99979, thickness), centered at world X = 0. The slab material
    is shader_marble (set inside the GeoNodes via
    `surface.shaderfunc_to_material(shader_marble)`).
    """

    mw = cabinet_obj.matrix_world
    verts = [mw @ v.co for v in cabinet_obj.data.vertices]
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [v.z for v in verts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    max_z = max(zs)
    scale = 1.4140 * 0.7071
    dx = (max_x - min_x) * scale
    dy = (max_y - min_y) * scale
    bm = bmesh.new()
    _add_box(
        bm, dx, dy, thickness,
        0.0, (min_y + max_y) / 2.0, max_z + thickness / 2.0,
    )
    top_obj = _finalize_bmesh_obj(bm, cabinet_obj.name + "_top")
    # Countertop slab uses shader_marble, mirroring the SetMaterial node
    # in geometry_nodes_add_cabinet_top.
    top_obj.data.materials.append(MAT_COUNTERTOP)
    return join_objects([cabinet_obj, top_obj])

class KitchenSpaceFactory(AssetFactory):
    """Sample overall dimensions and drop a drawer-only cabinet plus an
    optional top row (two side cabinets + one mid cabinet). Island mode
    skips the top row entirely.
    """


    def __init__(self, factory_seed, coarse=False, dimensions=None, island=False):
        super().__init__(factory_seed, coarse=coarse)
        with FixedSeed(factory_seed):
            if dimensions is None:
                dimensions = [
                    uniform(0.7, 1.0),
                    uniform(1.7, 5.0),
                    uniform(2.3, 2.5),
                ]
            self.island = island
            if self.island:
                dimensions[0] *= uniform(1.5, 2.0)
            self.dimensions = list(dimensions)
            self.sample_parameters(self.dimensions)

    def sample_parameters(self, dimensions):
        self.cabinet_bottom_height = uniform(0.8, 1.0)
        self.cabinet_top_height = uniform(0.8, 1.0)

    def create_placeholder(self, **kwargs):
        x, y, z = self.dimensions
        box = new_bbox(
            -x / 2.0 * 1.08, x / 2.0 * 1.08, 0, y, 0, self.cabinet_bottom_height + 0.13
        )
        if not self.island:
            top = new_bbox(-x / 2.0, x * 0.16, 0, y, z - self.cabinet_top_height - 0.1, z)
            box = join_objects([box, top])
        return box

    def create_asset(self, i=0, **kwargs):
        x, y, z = self.dimensions
        parts = []

        bottom_fac = KitchenCabinetFactory(
            self.factory_seed,
            dimensions=(x, y - 0.15, self.cabinet_bottom_height),
            drawer_only=True,
        )
        bottom = bottom_fac(i=0)
        bottom = add_countertop(bottom, thickness=0.05)
        parts.append(bottom)

        if not self.island:
            top_mid_width = uniform(1.0, 1.3)
            top_side_width = (y - top_mid_width) / 2.0 - 0.05
            top_fac = KitchenCabinetFactory(
                self.factory_seed,
                dimensions=(x / 2.0, top_side_width, self.cabinet_top_height),
                drawer_only=False,
            )
            top_left = top_fac(i=0)
            top_right = top_fac(i=1)
            top_left.location = (-x / 4.0, 0.0, z - self.cabinet_top_height)
            apply_transform(top_left, loc=True)
            top_right.location = (-x / 4.0, y - top_side_width, z - self.cabinet_top_height)
            apply_transform(top_right, loc=True)

            mid_fac = KitchenCabinetFactory(
                self.factory_seed,
                dimensions=(x * 0.66, top_mid_width, self.cabinet_top_height * 0.8),
                drawer_only=False,
            )
            top_mid = mid_fac(i=0)
            top_mid.location = (
                -x / 6.0,
                y / 2.0 - top_mid_width / 2.0,
                z - self.cabinet_top_height * 0.8,
            )
            apply_transform(top_mid, loc=True)
            parts += [top_left, top_right, top_mid]

        result = join_objects(parts)
        # Non-island mode: rescale to match the sampled self.dimensions
        # exactly. Island mode keeps the natural bottom-cabinet extent.
        if not self.island and result is not None:
            result.dimensions = self.dimensions
            apply_transform(result)
        return result

def build(seed=0):
    derived = int_hash((int(seed), 0))
    random.seed(derived)
    np.random.seed(derived)
    fac = KitchenSpaceFactory(int(seed))
    ph = fac.create_placeholder()
    result = fac.create_asset(i=0)
    if ph is not None and ph.name in bpy.data.objects:
        bpy.data.objects.remove(ph, do_unlink=True)
    if result is not None:
        result.name = "KitchenSpaceFactory"
    return result

build(SEED)

