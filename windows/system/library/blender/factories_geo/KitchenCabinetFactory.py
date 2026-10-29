# [FL_INDEX: keywords="blender_factory, procedural_3d, KitchenCabinetFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: KitchenCabinetFactory | Category: factories_geo
# Prompt: A 3D model of a long wall-mounted kitchen cabinet rendered from a three-quarter perspective, featuring a wide rectangular body divided into multiple sections with a mix of open shelf compartments and closed door panels in dark tones.

"""KitchenCabinetFactory (textured)."""


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


# ============================================================================
# ----------------------------------------------------------------------------
# ============================================================================

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
    Returns (mix_2_out, colorramp_1_out, colorramp_2_out) i.e. the
    factor for the final color ramp plus the two inputs needed for the
    displacement mix. Faithfully replicates plywood.py lines 75-165."""
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

    # "Musgrave" substitute: stretched NoiseTexture driven off the previous
    # noise's Fac output. Blender 5.0 removed ShaderNodeTexMusgrave; we use a
    # NoiseTexture with high detail as a visually-close replacement.
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

    # --- final 3-stop ramp: dark / gray / rgb ---------------------------
    cr_final = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr_final.inputs.get("Fac") or cr_final.inputs[0]
    nt.links.new(mix2_out, fac_in)
    # ramp starts with 2 elements; add a third then overwrite all three
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

    # --- final 3-stop ramp: dark/mid/bright (HSV-driven) ----------------
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
# KitchenCabinetBaseFactory.get_material_params().
# Returns (frame_material, board_material). The two shaders share the same
# "key" but the frame uses the Z-axis-tuned variant (as in plywood.py's
# shader_shelves_*_z wrappers).
# ----------------------------------------------------------------------------
def sample_kitchen_cabinet_materials():
    key = np.random.choice(["white", "black_wood", "wood"], p=[0.4, 0.3, 0.3])
    if key == "white":
        # shader_shelves_white has no z variant; sample once, reuse the same
        # where the factory binds the same shader func to both slots).
        p = _sample_white_params()
        frame_mat = make_shelves_white("KCFrame", params=p)
        board_mat = make_shelves_white("KCBoard", params=p)
    elif key == "black_wood":
        p = _sample_black_wood_params()
        frame_mat = make_shelves_black_wood_z("KCFrame", params=p)
        board_mat = make_shelves_black_wood("KCBoard", params=p)
    else:  # "wood"
        p = _sample_wood_params()
        frame_mat = make_shelves_wood_z("KCFrame", params=p)
        board_mat = make_shelves_wood("KCBoard", params=p)
    return frame_mat, board_mat


# ============================================================================
# wear_tear post-processing — faithful raw-bpy translation
# ============================================================================
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"


def _mat_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))


def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)


def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    if in0 is not None:
        if hasattr(in0, "default_value") or hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "default_value") or hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    return n


def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    if in0 is not None:
        if hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    if scale is not None:
        for inp in n.inputs:
            if inp.name == "Scale":
                inp.default_value = scale
                break
    return n


def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = value
    return n


def _color_ramp(nt, fac_socket, stops):
    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(fac_socket, fac_in)
    elements = cr.color_ramp.elements
    for i, (pos, color) in enumerate(stops):
        if i < len(elements):
            elements[i].position = pos
            elements[i].color = color
        else:
            e = elements.new(pos)
            e.color = color
    return cr


def _noise_tex(nt, vector_socket, scale, detail=2.0, distortion=0.0, roughness=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_socket is not None:
        nt.links.new(vector_socket, n.inputs["Vector"])
    if isinstance(scale, (int, float)):
        n.inputs["Scale"].default_value = float(scale)
    else:
        nt.links.new(scale, n.inputs["Scale"])
    if "Detail" in n.inputs:
        n.inputs["Detail"].default_value = detail
    if "Distortion" in n.inputs:
        n.inputs["Distortion"].default_value = distortion
    if "Roughness" in n.inputs:
        n.inputs["Roughness"].default_value = roughness
    return n


def get_scratch_params():
    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=_mat_log_uniform(5, 80),
        scratch_mask_ratio=_mat_log_uniform(0.01, 0.9),
        scratch_mask_noise=_mat_log_uniform(5, 40),
        scratch_depth=_mat_log_uniform(0.1, 1.0),
    )


def _build_scratch_graph(nt, params):
    n_angle1 = _value_node(nt, params["angle1"])
    n_angle2 = _value_node(nt, params["angle2"])
    n_scale = _value_node(nt, params["scratch_scale"])
    n_mask_ratio = _value_node(nt, params["scratch_mask_ratio"])
    n_mask_noise = _value_node(nt, params["scratch_mask_noise"])
    n_depth = _value_node(nt, params["scratch_depth"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    cxyz1 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle1.outputs[0], cxyz1.inputs["Y"])
    map1 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map1, "vector_type"):
        try: map1.vector_type = "TEXTURE"
        except TypeError: pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map2, "vector_type"):
        try: map2.vector_type = "TEXTURE"
        except TypeError: pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    map3 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map3, "vector_type"):
        try: map3.vector_type = "TEXTURE"
        except TypeError: pass
    map3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.1920)
    nt.links.new(tex_coord.outputs["Object"], map3.inputs["Vector"])
    noise3 = _noise_tex(nt, map3.outputs["Vector"], n_mask_noise.outputs[0], detail=1.0)
    cr_mask = _color_ramp(nt, _noise_fac_output(noise3),
                          [(0.4109, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))])
    mul_mask = _math(nt, "MULTIPLY", n_mask_ratio.outputs[0], cr_mask.outputs["Color"])
    add_combined = _math(nt, "ADD", add.outputs[0], mul_mask.outputs[0], clamp=True)

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.7
    map_range.inputs[2].default_value = 0.72
    map_range.inputs[4].default_value = 0.9
    nt.links.new(add_combined.outputs[0], map_range.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(map_range.outputs["Result"], disp.inputs["Height"])
    nt.links.new(n_depth.outputs[0], disp.inputs["Scale"])

    return disp.outputs[0]


def apply_scratches(obj, **params):
    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_scratch_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == SCRATCH_LABEL for n in nt.nodes):
            continue
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        try:
            disp_out = _build_scratch_graph(nt, params)
            nt.links.new(disp_out, mat_out.inputs["Displacement"])
            disp_out.node.label = SCRATCH_LABEL
        except Exception as e:
            print(f"  [scratches] failed on {mat.name}: {type(e).__name__}: {e}")


def get_edge_wear_params():
    return dict(
        worn_off_opacity=float(np.random.uniform(0, 0.01)),
        worn_off_radius=float(np.random.uniform(0.005, 0.01)),
        scratch_radius=float(np.random.uniform(0.01, 0.03)),
        worn_off_mask_randomness=float(np.random.uniform(2.5, 3.0)),
        edge_base_color_hue=float(np.random.uniform(0.0, 1.0)),
        edge_base_color_whiteness=float(np.random.uniform(0.1, 0.6)),
        scratch_mask_randomness=float(np.random.choice(
            [np.random.uniform(0.1, 5.0), np.random.uniform(1.0, 10.0)])),
        scratch_density=float(np.random.uniform(1.5, 10.0)),
        scratch_opacity=float(np.random.uniform(0.5, 1.0)),
    )


def _build_edge_wear_graph(nt, original_bsdf_node, original_displacement_node, params):
    p = params
    n_scratch_opacity = _value_node(nt, p["scratch_opacity"])
    n_scratch_mask_randomness = _value_node(nt, p["scratch_mask_randomness"])
    n_scratch_radius = _value_node(nt, p["scratch_radius"])
    n_worn_opacity = _value_node(nt, p["worn_off_opacity"])
    n_worn_radius = _value_node(nt, p["worn_off_radius"])
    n_worn_mask_randomness = _value_node(nt, p["worn_off_mask_randomness"])
    n_edge_whiteness = _value_node(nt, p["edge_base_color_whiteness"])
    n_edge_hue = _value_node(nt, p["edge_base_color_hue"])
    n_scratch_density = _value_node(nt, p["scratch_density"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise_a = _noise_tex(nt, mapping.outputs["Vector"], n_scratch_mask_randomness.outputs[0], detail=1.0)
    cr_a = _color_ramp(nt, _noise_fac_output(noise_a),
                       [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.samples = 20
    nt.links.new(n_scratch_radius.outputs[0], bevel.inputs["Radius"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub = _vmath(nt, "SUBTRACT", bevel.outputs[0], geo.outputs["Normal"])
    abs_a = _math(nt, "ABSOLUTE", sub.outputs["Vector"])
    cr_b = _color_ramp(nt, abs_a.outputs[0],
                       [(0.0691, (0, 0, 0, 1)), (0.1564, (1, 1, 1, 1))])

    mul_a = _math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"], clamp=True)
    mul_a1 = _math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0], clamp=True)

    bevel2 = nt.nodes.new("ShaderNodeBevel")
    bevel2.samples = 20
    nt.links.new(n_worn_radius.outputs[0], bevel2.inputs["Radius"])
    sub2 = _vmath(nt, "SUBTRACT", bevel2.outputs[0], geo.outputs["Normal"])
    abs_b = _math(nt, "ABSOLUTE", sub2.outputs["Vector"])

    noise_b = _noise_tex(nt, mapping.outputs["Vector"], n_worn_mask_randomness.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac_output(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
    cr_d = _color_ramp(nt, mul_b1.outputs[0],
                       [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])

    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    if hasattr(combine_color, "mode"):
        try: combine_color.mode = "HSV"
        except TypeError: pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_result"):
        try: mix.clamp_result = True
        except TypeError: pass
    if hasattr(mix, "clamp_factor"):
        try: mix.clamp_factor = False
        except TypeError: pass
    nt.links.new(n_edge_whiteness.outputs[0], mix.inputs[0])
    nt.links.new(combine_color.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

    bsdf_worn1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn1.inputs["Base Color"])
    _set_principled(bsdf_worn1, Metallic=0.3745, Roughness=0.1436,
                    **{"Specular IOR Level": 0.0})

    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cr_d.outputs["Color"], mix_shader.inputs["Fac"])
    nt.links.new(original_bsdf_node.outputs[0], mix_shader.inputs[1])
    nt.links.new(bsdf_worn1.outputs[0], mix_shader.inputs[2])

    map_h = nt.nodes.new("ShaderNodeMapping")
    map_h.inputs["Scale"].default_value = (10.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_h.inputs["Vector"])
    vor_h = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_h, "feature"):
        try: vor_h.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])

    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_v, "feature"):
        try: vor_v.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_v.outputs["Vector"], vor_v.inputs["Vector"])
    nt.links.new(scale_v.outputs[0], vor_v.inputs["Scale"])

    dist_h = vor_h.outputs.get("Distance") or vor_h.outputs[0]
    dist_v = vor_v.outputs.get("Distance") or vor_v.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_e = _color_ramp(nt, mul_dist.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_e = _math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"], clamp=True)
    mul_f = _math(nt, "MULTIPLY", mul_a.outputs[0], mul_e.outputs[0], clamp=True)

    bsdf_worn2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn2.inputs["Base Color"])
    _set_principled(bsdf_worn2, Metallic=0.3855, Roughness=0.0,
                    **{"Specular IOR Level": 0.0})

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_a1.outputs[0], mix_shader_2.inputs["Fac"])
    nt.links.new(mix_shader.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(bsdf_worn2.outputs[0], mix_shader_2.inputs[2])

    scale_disp = _vmath(nt, "SCALE", in0=mul_f.outputs[0], scale=2.0)
    if original_displacement_node is None:
        total_displacement = scale_disp.outputs[0]
    else:
        add_disp = _math(nt, "ADD", original_displacement_node.outputs[0],
                         scale_disp.outputs[0], clamp=True)
        total_displacement = add_disp.outputs[0]

    return mix_shader_2.outputs[0], total_displacement


def apply_edge_wear(obj, **params):
    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_edge_wear_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == EDGE_WEAR_LABEL for n in nt.nodes):
            continue
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        surface_links = mat_out.inputs["Surface"].links
        if not surface_links:
            continue
        original_bsdf = surface_links[0].from_node
        disp_links = mat_out.inputs["Displacement"].links
        original_disp = disp_links[0].from_node if disp_links else None
        try:
            final_bsdf_socket, final_disp_socket = _build_edge_wear_graph(
                nt, original_bsdf, original_disp, params)
            nt.links.new(final_bsdf_socket, mat_out.inputs["Surface"])
            nt.links.new(final_disp_socket, mat_out.inputs["Displacement"])
            final_bsdf_socket.node.label = EDGE_WEAR_LABEL
        except Exception as e:
            print(f"  [edge_wear] failed on {mat.name}: {type(e).__name__}: {e}")


# ============================================================================
# === End of inlined material library ========================================
# ============================================================================


# ── Scene cleanup ──
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)


# Phase 1: materials on raw SEED (style key → frame + board shaders + wear-tear gates)
SEED = int(os.environ.get("SEED", "0"))
seed_all(SEED)
MAT_FRAME, MAT_BOARD = sample_kitchen_cabinet_materials()


# ---------------------------------------------------------------------------
# Geometry (per-part material bindings at the end of each build_* function)
# ---------------------------------------------------------------------------

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
    bpy.context.scene.collection.objects.link(result)
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
    bpy.context.scene.collection.objects.link(obj)
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


# =============================================================================
# Shelf frame (LargeShelfBaseFactory)
# =============================================================================

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


# =============================================================================
# Door (CabinetDoorBaseFactory)
# =============================================================================

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
        if params.get("frame_material", None) is None:
            np.random.choice(["white", "black_wood", "wood"], p=[0.5, 0.2, 0.3])
            if params["has_mid_ramp"]:
                np.random.choice(["white", "glass"], p=[0.7, 0.3])
                np.random.choice(["white", "glass"], p=[0.6, 0.4])
        return params


# =============================================================================
# Drawer (CabinetDrawerBaseFactory)
# =============================================================================

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


# =============================================================================
# KitchenCabinet assembly
# =============================================================================

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

    def create_placeholder(self, **kwargs):
        x, y, z = self.dimensions
        num_w_cells = max((y / 0.45), 1)
        width = (num_w_cells - 1) * 0.02 * 2 + (num_w_cells - 1) * 0.001 + y
        height = (int((z - 0.06) / 0.3) + 1) * 0.02 + 0.06 + z
        x += 0.01
        return new_bbox(-x / 2.0, x / 2.0, -width / 2.0, width / 2.0, 0, height)


def build(seed=0):
    derived = int_hash((int(seed), 0))
    random.seed(derived)
    np.random.seed(derived)
    fac = KitchenCabinetFactory(int(seed))
    ph = fac.create_placeholder()
    result = fac.create_asset(i=0)
    bpy.data.objects.remove(ph, do_unlink=True)
    if result is not None:
        result.name = "KitchenCabinetFactory"
    return result


build(SEED)
