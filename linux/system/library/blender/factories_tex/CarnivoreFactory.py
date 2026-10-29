# [FL_INDEX: keywords="blender_factory, procedural_3d, CarnivoreFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CarnivoreFactory | Category: factories_tex
# Prompt: A large carnivorous quadruped rendered as a textured 3D model. The creature resembles a big cat such as a tiger, with a powerful, muscular body covered in a dense, fluffy fur coat rendered with a particle hair system. The fur coloring is a warm orange-red with dark black horizontal stripe markings across the body, flanks, and legs, and lighter creamy-white areas on the underbelly and muzzle. The animal stands in a low, slightly crouching pose with four thick legs ending in dark clawed paws. The head is broad and rounded with small white and gray facial markings.

import os
#!/usr/bin/env python3

import base64
import hashlib
import math

import bmesh
import bpy
import mathutils
import numpy as np
from mathutils.bvhtree import BVHTree
from numpy.random import normal as N
from numpy.random import uniform as U

SEED = int(os.environ.get("SEED", "0"))

#  Creature material -- translated from creature shaders (raw bpy)
import os as _os, random as _random, colorsys as _colorsys


def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h) % 1.0, max(0, min(1, float(s))), max(0, min(1, float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def _sample_ratio(base, lo_frac, hi_frac):
    return float(np.exp(np.random.uniform(np.log(base * lo_frac), np.log(base * hi_frac))))

def _color_mask_approx(nt, ln, tc):
    """Approximate nodegroup_color_mask using Object-space position.
    Original reads tag_body/tag_leg/tag_head/local_pos attributes (unavailable here).
    We replicate the spatial variation: Musgrave + Z-gradient + X/Y ramps."""

    obj_pos = tc.outputs["Object"]

    # Musgrave-like noise on position (original: 4D musgrave on abs(local_pos.y))
    noise_cm = nt.nodes.new("ShaderNodeTexNoise")
    ln(obj_pos, noise_cm.inputs["Vector"])
    noise_cm.inputs["Scale"].default_value = float(np.random.normal(7, 1))
    noise_cm.inputs["Detail"].default_value = float(np.random.normal(7, 1))
    noise_cm.inputs["Roughness"].default_value = 0.5

    add_cm = nt.nodes.new("ShaderNodeMath")
    add_cm.operation = "ADD"
    ln(_fac(noise_cm), add_cm.inputs[0])
    add_cm.inputs[1].default_value = 0.7

    cr_cm = nt.nodes.new("ShaderNodeValToRGB")
    cr_cm.color_ramp.interpolation = "EASE"
    ln(add_cm.outputs[0], cr_cm.inputs["Fac"])
    cr_cm.color_ramp.elements[0].position = 0.0
    cr_cm.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr_cm.color_ramp.elements[1].position = 0.4864
    cr_cm.color_ramp.elements[1].color = (1, 1, 1, 1)

    # Z-gradient (original: normalized local_pos Z)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(obj_pos, sep.inputs["Vector"])

    cr_z = nt.nodes.new("ShaderNodeValToRGB")
    cr_z.color_ramp.interpolation = "EASE"
    ln(sep.outputs["Z"], cr_z.inputs["Fac"])
    cr_z.color_ramp.elements[0].position = 0.0
    cr_z.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr_z.color_ramp.elements[1].position = 0.5318
    cr_z.color_ramp.elements[1].color = (1, 1, 1, 1)

    # Multiply noise * Z-gradient
    mul_cm = nt.nodes.new("ShaderNodeMath")
    mul_cm.operation = "MULTIPLY"
    ln(cr_cm.outputs["Color"], mul_cm.inputs[0])
    ln(cr_z.outputs["Color"], mul_cm.inputs[1])

    return mul_cm.outputs[0]

def make_tiger_material(seed, name="TigerMaterial"):
    """Tiger body shader -- faithful to shader_tiger_attr + nodegroup_tiger_fac.
    Topology: NoiseTexture(4D)->MixRGB->MusgraveTexture(4D) band-pass +
              dual-Mapping->WaveTexture->MapRange -> MixRGB with band-pass mask ->
              color_mask->ColorRamp(HSV) -> MixRGB(stripe dark, base color) -> PrincipledBSDF."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # --- nodegroup_tiger_fac equivalent ---

    # Scale factor: U(2,4) (original: Value node for body scale)
    scale_val = float(np.random.uniform(2, 4))

    # Scale the Object position
    scale_node = nt.nodes.new("ShaderNodeVectorMath")
    scale_node.operation = "SCALE"
    ln(tc.outputs["Object"], scale_node.inputs[0])
    scale_node.inputs["Scale"].default_value = scale_val

    vec_input = scale_node.outputs["Vector"]

    # NoiseTexture 4D -> MixRGB blend with input vector
    noise_4d = nt.nodes.new("ShaderNodeTexNoise")
    noise_4d.noise_dimensions = "4D"
    ln(vec_input, noise_4d.inputs["Vector"])
    noise_4d.inputs["W"].default_value = float(np.random.uniform(-10, 10))

    mix_blend = nt.nodes.new("ShaderNodeMix"); mix_blend.data_type = "RGBA"
    mix_blend.inputs[0].default_value = float(np.random.uniform(0.8, 0.9))
    ln(noise_4d.outputs["Color"], mix_blend.inputs[6])
    ln(vec_input, mix_blend.inputs[7])

    # Musgrave (using NoiseTexture as Musgrave substitute) 4D for band-pass
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.noise_dimensions = "4D"
    ln(mix_blend.outputs[2], musgrave.inputs["Vector"])
    musgrave.inputs["W"].default_value = float(np.random.uniform(-10, 10))
    musgrave.inputs["Scale"].default_value = 1.0

    # Band-pass filter: value1 = N(0.118, 0.01), value2 = N(0.06, 0.01)
    val1 = float(np.random.normal(0.118, 0.01))
    val2 = float(np.random.normal(0.06, 0.01))
    threshold_hi = val1 + val2
    threshold_lo = val1 - val2

    gt_hi = nt.nodes.new("ShaderNodeMath")
    gt_hi.operation = "GREATER_THAN"
    ln(_fac(musgrave), gt_hi.inputs[0])
    gt_hi.inputs[1].default_value = threshold_hi

    gt_lo = nt.nodes.new("ShaderNodeMath")
    gt_lo.operation = "GREATER_THAN"
    ln(_fac(musgrave), gt_lo.inputs[0])
    gt_lo.inputs[1].default_value = threshold_lo

    less_than = nt.nodes.new("ShaderNodeMath")
    less_than.operation = "LESS_THAN"
    ln(gt_hi.outputs[0], less_than.inputs[0])
    ln(gt_lo.outputs[0], less_than.inputs[1])

    # ColorRamp CONSTANT on musgrave output (directional selector)
    cr_dir = nt.nodes.new("ShaderNodeValToRGB")
    cr_dir.color_ramp.interpolation = "CONSTANT"
    ln(_fac(musgrave), cr_dir.inputs["Fac"])
    cr_dir.color_ramp.elements[0].position = 0.0
    cr_dir.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr_dir.color_ramp.elements[1].position = 0.1182
    cr_dir.color_ramp.elements[1].color = (1, 1, 1, 1)

    # Dual Mapping nodes
    map_a = nt.nodes.new("ShaderNodeMapping")
    ln(mix_blend.outputs[2], map_a.inputs["Vector"])
    map_a.inputs["Location"].default_value = (
        float(np.random.uniform(0, 10)),
        float(np.random.uniform(0, 10)),
        float(np.random.uniform(0, 10)),
    )

    map_b = nt.nodes.new("ShaderNodeMapping")
    ln(mix_blend.outputs[2], map_b.inputs["Vector"])
    map_b.inputs["Location"].default_value = (
        float(np.random.uniform(0, 10)),
        float(np.random.uniform(0, 10)),
        float(np.random.uniform(0, 10)),
    )
    map_b.inputs["Rotation"].default_value = (0.7854, 0.0, 0.0)

    # Mix the two mappings by directional selector
    mix_dir = nt.nodes.new("ShaderNodeMix"); mix_dir.data_type = "RGBA"
    ln(cr_dir.outputs["Color"], mix_dir.inputs[0])
    ln(map_a.outputs["Vector"], mix_dir.inputs[6])
    ln(map_b.outputs["Vector"], mix_dir.inputs[7])

    # Wave texture (core stripe pattern)
    wave = nt.nodes.new("ShaderNodeTexWave")
    ln(mix_dir.outputs[2], wave.inputs["Vector"])
    wave.inputs["Scale"].default_value = float(np.random.normal(1.0, 0.1))
    wave.inputs["Distortion"].default_value = float(np.random.normal(10.0, 0.5))
    wave.inputs["Detail"].default_value = 0.0
    wave.inputs["Phase Offset"].default_value = float(np.random.uniform(-20, 20))

    # MapRange on wave Fac
    mr = nt.nodes.new("ShaderNodeMapRange")
    ln(_fac(wave), mr.inputs["Value"])
    mr.inputs[1].default_value = 0.2
    mr.inputs[2].default_value = 0.4

    # MixRGB: band-pass mask selects between wave-stripe result and white (non-stripe)
    mix_bandpass = nt.nodes.new("ShaderNodeMix"); mix_bandpass.data_type = "RGBA"
    ln(less_than.outputs[0], mix_bandpass.inputs[0])
    ln(mr.outputs[0], mix_bandpass.inputs[6])
    mix_bandpass.inputs[7].default_value = (1, 1, 1, 1)

    # --- shader_tiger_attr: color_mask -> ColorRamp -> final MixRGB ---

    color_mask = _color_mask_approx(nt, ln, tc)

    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    ln(color_mask, cr_base.inputs["Fac"])
    cr_base.color_ramp.elements[0].position = 0.0
    cr_base.color_ramp.elements[0].color = _hsv2rgba(
        np.random.uniform(0.015, 0.06), np.random.uniform(0.85, 0.95), np.random.uniform(0.15, 0.7))
    cr_base.color_ramp.elements[1].position = 1.0
    cr_base.color_ramp.elements[1].color = _hsv2rgba(
        np.random.uniform(0.02, 0.05), np.random.uniform(0.3, 0.7), np.random.uniform(0.15, 0.7))

    # Final MixRGB: tiger_fac drives mix between dark stripes and base color
    mix_final = nt.nodes.new("ShaderNodeMix"); mix_final.data_type = "RGBA"
    ln(mix_bandpass.outputs[2], mix_final.inputs[0])
    mix_final.inputs[6].default_value = (0.01, 0.01, 0.01, 1.0)  # stripe dark color
    ln(cr_base.outputs["Color"], mix_final.inputs[7])

    # PrincipledBSDF -- Specular=0, no Roughness override (default 0.5)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_final.outputs[2], bsdf.inputs["Base Color"])
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = 0.0
    try:
        bsdf.subsurface_method = "BURLEY"
    except Exception:
        pass

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_spot_sparse_material(seed, name="SpotSparseMaterial"):
    """SpotSparse body shader -- faithful to shader_spots_sparse_attr.
    Topology: Position->Noise->Voronoi+Noise mix -> 3-element ColorRamp threshold ->
              color_mask->ColorRamp(HSV) -> MixRGB -> PrincipledBSDF(Specular=0)."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Position scaled by random factor (geometry_spots_sparse equivalent)
    pos_scale = float(np.random.uniform(0.1, 1))
    scale_node = nt.nodes.new("ShaderNodeVectorMath")
    scale_node.operation = "SCALE"
    ln(tc.outputs["Object"], scale_node.inputs[0])
    scale_node.inputs["Scale"].default_value = pos_scale

    # Noise on scaled position
    noise_pos = nt.nodes.new("ShaderNodeTexNoise")
    ln(scale_node.outputs["Vector"], noise_pos.inputs["Vector"])

    # Mix position + noise
    mix_pn = nt.nodes.new("ShaderNodeMix"); mix_pn.data_type = "RGBA"
    mix_pn.inputs[0].default_value = 0.1
    ln(scale_node.outputs["Vector"], mix_pn.inputs[6])
    ln(_fac(noise_pos), mix_pn.inputs[7])

    # Voronoi for spot cells
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(mix_pn.outputs[2], voronoi.inputs["Vector"])
    voronoi.inputs["Scale"].default_value = _sample_ratio(8, 0.5, 2)

    # Second noise for spot edge variation
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    ln(scale_node.outputs["Vector"], noise2.inputs["Vector"])
    noise2.inputs["Scale"].default_value = 15.0
    noise2.inputs["Roughness"].default_value = 1.0

    # Mix voronoi distance + noise
    mix_vn = nt.nodes.new("ShaderNodeMix"); mix_vn.data_type = "RGBA"
    mix_vn.inputs[0].default_value = 0.5
    ln(voronoi.outputs["Distance"], mix_vn.inputs[6])
    ln(_fac(noise2), mix_vn.inputs[7])

    # 3-element ColorRamp threshold (offset-like)
    cr_offset = nt.nodes.new("ShaderNodeValToRGB")
    ln(mix_vn.outputs[2], cr_offset.inputs["Fac"])
    cr_offset.color_ramp.elements[0].position = 0.0
    cr_offset.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr_offset.color_ramp.elements.new(0.4341)
    cr_offset.color_ramp.elements[1].position = 0.4341
    cr_offset.color_ramp.elements[1].color = (0.0942, 0.0942, 0.0942, 1)
    cr_offset.color_ramp.elements[2].position = 0.5
    cr_offset.color_ramp.elements[2].color = (1, 1, 1, 1)

    # color_mask approx -> ColorRamp for base color variation
    color_mask = _color_mask_approx(nt, ln, tc)

    def _getcolor():
        return _hsv2rgba(np.random.uniform(0.02, 0.06), np.random.uniform(0.05, 0.9),
                         abs(float(np.random.normal(0.05, 0.1))))

    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    ln(color_mask, cr_base.inputs["Fac"])
    cr_base.color_ramp.elements[0].position = float(np.random.uniform(0, 0.5))
    cr_base.color_ramp.elements[0].color = _getcolor()
    cr_base.color_ramp.elements[1].position = 1.0
    cr_base.color_ramp.elements[1].color = _hsv2rgba(
        np.random.uniform(0.02, 0.06), np.random.uniform(0.4, 0.8), np.random.uniform(0.15, 0.7))

    # Use offset ramp output (60% chance) as fac to mix dark spots with base color
    use_offset = np.random.uniform() < 0.6
    mix_final = nt.nodes.new("ShaderNodeMix"); mix_final.data_type = "RGBA"
    if use_offset:
        ln(cr_offset.outputs["Color"], mix_final.inputs[0])
    else:
        mix_final.inputs[0].default_value = 1.0
    mix_final.inputs[6].default_value = _getcolor()
    ln(cr_base.outputs["Color"], mix_final.inputs[7])

    # PrincipledBSDF -- Specular=0, Roughness driven by offset ramp
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_final.outputs[2], bsdf.inputs["Base Color"])
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = 0.0
    ln(cr_offset.outputs["Color"], bsdf.inputs["Roughness"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_giraffe_material(seed, name="GiraffeMaterial"):
    """Giraffe body shader -- faithful to shader_giraffe_attr.
    Topology: Object->Noise->MixRGB->Mapping->Voronoi(2D)+SMOOTH_F1->Subtract->LessThan->
              ColorRamp boundary -> color_mask->ColorRamp(HSV) -> MixRGB -> PrincipledBSDF."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Noise on object coords
    noise_g = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Object"], noise_g.inputs["Vector"])

    # Mix noise color with object coords (Fac=0.9)
    mix_g = nt.nodes.new("ShaderNodeMix"); mix_g.data_type = "RGBA"
    mix_g.inputs[0].default_value = 0.9
    ln(noise_g.outputs["Color"], mix_g.inputs[6])
    ln(tc.outputs["Object"], mix_g.inputs[7])

    # Mapping
    map_g = nt.nodes.new("ShaderNodeMapping")
    ln(mix_g.outputs[2], map_g.inputs["Vector"])

    # Voronoi scale
    vor_scale = _sample_ratio(10.0, 0.5, 2)

    # Voronoi F1 (distance)
    vor_f1 = nt.nodes.new("ShaderNodeTexVoronoi")
    vor_f1.voronoi_dimensions = "2D"
    ln(map_g.outputs["Vector"], vor_f1.inputs["Vector"])
    vor_f1.inputs["Scale"].default_value = vor_scale

    # Voronoi SMOOTH_F1
    vor_sf1 = nt.nodes.new("ShaderNodeTexVoronoi")
    vor_sf1.voronoi_dimensions = "2D"
    vor_sf1.feature = "SMOOTH_F1"
    ln(map_g.outputs["Vector"], vor_sf1.inputs["Vector"])
    vor_sf1.inputs["Scale"].default_value = vor_scale

    # Subtract distances for cell boundary detection
    sub_g = nt.nodes.new("ShaderNodeMath")
    sub_g.operation = "SUBTRACT"
    ln(vor_f1.outputs["Distance"], sub_g.inputs[0])
    ln(vor_sf1.outputs["Distance"], sub_g.inputs[1])

    # Less than threshold -> boundary
    lt_g = nt.nodes.new("ShaderNodeMath")
    lt_g.operation = "LESS_THAN"
    ln(sub_g.outputs[0], lt_g.inputs[0])
    lt_g.inputs[1].default_value = float(np.random.uniform(0.04, 0.08))

    # ColorRamp on boundary
    cr_bnd = nt.nodes.new("ShaderNodeValToRGB")
    ln(lt_g.outputs[0], cr_bnd.inputs["Fac"])
    cr_bnd.color_ramp.elements[0].position = 0.2545
    cr_bnd.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr_bnd.color_ramp.elements[1].position = 0.2886
    cr_bnd.color_ramp.elements[1].color = (1, 1, 1, 1)

    # color_mask approx -> ColorRamp for base color
    color_mask = _color_mask_approx(nt, ln, tc)

    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    ln(color_mask, cr_base.inputs["Fac"])
    cr_base.color_ramp.elements[0].position = 0.0
    cr_base.color_ramp.elements[0].color = _hsv2rgba(
        np.random.uniform(0.02, 0.06), np.random.uniform(0.4, 0.8), np.random.uniform(0.15, 0.7))
    cr_base.color_ramp.elements[1].position = 1.0
    cr_base.color_ramp.elements[1].color = _hsv2rgba(
        np.random.uniform(0.02, 0.06), np.random.uniform(0.4, 0.8), np.random.uniform(0.15, 0.7))

    # Boundary dark color
    boundary_color = _hsv2rgba(
        np.random.uniform(0.02, 0.06), np.random.uniform(0.4, 0.9), np.random.uniform(0.04, 0.1))

    # Final mix: boundary selects between base and dark boundary
    mix_final = nt.nodes.new("ShaderNodeMix"); mix_final.data_type = "RGBA"
    ln(cr_bnd.outputs["Color"], mix_final.inputs[0])
    ln(cr_base.outputs["Color"], mix_final.inputs[6])
    mix_final.inputs[7].default_value = boundary_color

    # PrincipledBSDF -- default specular (original doesn't override)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_final.outputs[2], bsdf.inputs["Base Color"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_tongue_material(seed, name="TongueMaterial"):
    """Tongue shader -- faithful to shader_tongue.
    Musgrave->ColorRamp->Roughness, fixed Base Color, Subsurface."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Scale"].default_value = 37.88

    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(musgrave), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.24
    cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 1.0
    cr.color_ramp.elements[1].color = (0.0979, 0.0979, 0.0979, 1)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.8, 0.0605, 0.0437, 1.0)
    sw_key = "Subsurface Weight" if "Subsurface Weight" in bsdf.inputs else "Subsurface"
    bsdf.inputs[sw_key].default_value = 0.0312
    sc_key = "Subsurface Color" if "Subsurface Color" in bsdf.inputs else "Subsurface Color"
    if sc_key in bsdf.inputs:
        bsdf.inputs[sc_key].default_value = (0.8, 0.0, 0.2679, 1.0)
    ln(cr.outputs["Color"], bsdf.inputs["Roughness"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_bone_material(seed, name="BoneMaterial"):
    """Bone/teeth shader -- faithful to shader_bone.
    Voronoi->Noise->ColorRamp chain -> MixRGB -> PrincipledBSDF + Glass mix."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Mapping 1
    map1 = nt.nodes.new("ShaderNodeMapping")
    ln(tc.outputs["Object"], map1.inputs["Vector"])
    map1.inputs["Location"].default_value = (
        1.7 + float(np.random.uniform(-1, 1)) * 0.05,
        0.3 + float(np.random.uniform(-1, 1)) * 0.05,
        float(np.random.uniform(-1, 1)) * 0.05,
    )

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    ln(map1.outputs["Vector"], noise1.inputs["Vector"])
    noise1.inputs["Scale"].default_value = 10.8 + float(np.random.uniform(-1, 1)) * 3
    noise1.inputs["Detail"].default_value = 15.0
    noise1.inputs["Roughness"].default_value = 0.7667

    vor1 = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(_fac(noise1), vor1.inputs["Vector"])
    vor1.inputs["Scale"].default_value = 10.0

    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    ln(vor1.outputs["Color"], cr1.inputs["Fac"])
    cr1.color_ramp.elements[0].position = 0.4364 + float(np.random.uniform(-1, 1)) * 0.05
    cr1.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr1.color_ramp.elements[1].position = 0.58 + float(np.random.uniform(-1, 1)) * 0.05
    cr1.color_ramp.elements[1].color = (1, 1, 1, 1)

    # Mapping 2
    map2 = nt.nodes.new("ShaderNodeMapping")
    ln(tc.outputs["Object"], map2.inputs["Vector"])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    ln(map2.outputs["Vector"], noise2.inputs["Vector"])
    noise2.inputs["Scale"].default_value = 98.9 + float(np.random.uniform(-0.3, 1)) * 30
    noise2.inputs["Detail"].default_value = 15.0
    noise2.inputs["Roughness"].default_value = 0.7667

    vor2 = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(_fac(noise2), vor2.inputs["Vector"])
    vor2.inputs["Scale"].default_value = 10.0 + float(np.random.uniform(-1, 1)) * 0.05

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    ln(vor2.outputs["Color"], cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.3089 + float(np.random.uniform(-1, 1)) * 0.05
    cr2.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr2.color_ramp.elements[1].position = 0.673 + float(np.random.uniform(-1, 1)) * 0.05
    cr2.color_ramp.elements[1].color = (1, 1, 1, 1)

    # Multiply cr1 * cr2
    mul_v = nt.nodes.new("ShaderNodeVectorMath")
    mul_v.operation = "MULTIPLY"
    ln(cr1.outputs["Color"], mul_v.inputs[0])
    ln(cr2.outputs["Color"], mul_v.inputs[1])

    # UV noise -> color ramp for bone color
    map3 = nt.nodes.new("ShaderNodeMapping")
    ln(tc.outputs["UV"], map3.inputs["Vector"])
    map3.inputs["Scale"].default_value = (1, 1, 0)

    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    ln(map3.outputs["Vector"], noise3.inputs["Vector"])
    noise3.inputs["Scale"].default_value = 6.4 + float(np.random.uniform(-1, 1))

    cr3 = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(noise3), cr3.inputs["Fac"])
    cr3.color_ramp.elements[0].position = 0.3682 + float(np.random.uniform(-1, 1)) * 0.05
    cr3.color_ramp.elements[0].color = (0.3813, 0.2384, 0.1183, 1)
    cr3.color_ramp.elements[1].position = 0.7591 + float(np.random.uniform(-1, 1)) * 0.05
    cr3.color_ramp.elements[1].color = (0.4969, 0.5029, 0.4678, 1)

    # Mix: mul_v selects between dark bone and colored bone
    mix_bone = nt.nodes.new("ShaderNodeMix"); mix_bone.data_type = "RGBA"
    ln(mul_v.outputs["Vector"], mix_bone.inputs[0])
    mix_bone.inputs[6].default_value = (0.1912, 0.0452, 0.0103, 1)
    ln(cr3.outputs["Color"], mix_bone.inputs[7])

    # PrincipledBSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_bone.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.4409

    # Glass BSDF
    glass = nt.nodes.new("ShaderNodeBsdfGlass")

    # Mix Shader: 0.2 glass
    mix_sh = nt.nodes.new("ShaderNodeMixShader")
    mix_sh.inputs["Fac"].default_value = 0.2
    ln(bsdf.outputs["BSDF"], mix_sh.inputs[1])
    ln(glass.outputs["BSDF"], mix_sh.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_sh.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_nose_material(seed, name="NoseMaterial"):
    """Nose shader -- faithful to shader_nose.
    Musgrave->ColorRamp for base, Musgrave->MapRange for roughness."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    musgrave1 = nt.nodes.new("ShaderNodeTexNoise")
    musgrave1.inputs["Scale"].default_value = float(np.random.uniform(2, 6))
    musgrave1.inputs["Detail"].default_value = 14.7

    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(musgrave1), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = float(np.random.uniform(0.2, 0.6))
    cr.color_ramp.elements[0].color = (0.008, 0.0053, 0.0044, 1)
    cr.color_ramp.elements[1].position = 1.0
    cr.color_ramp.elements[1].color = (0.7068, 0.436, 0.35, 1)

    musgrave2 = nt.nodes.new("ShaderNodeTexNoise")
    musgrave2.inputs["Scale"].default_value = 10.0

    mr = nt.nodes.new("ShaderNodeMapRange")
    ln(_fac(musgrave2), mr.inputs["Value"])
    mr.inputs[3].default_value = float(np.random.normal(0.4, 0.1))
    mr.inputs[4].default_value = float(np.random.normal(0.7, 0.15))

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    ln(mr.outputs[0], bsdf.inputs["Roughness"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_eyeball_material(seed, name="EyeballMaterial"):
    """Carnivore eyeball shader: white sclera, colored iris ring, dark pupil, glossy wet surface."""


    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Use Object coords to create concentric ring pattern (iris/pupil)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(tc.outputs["Object"], sep.inputs["Vector"])

    # Radial distance from center in YZ plane (eye looks along X)
    mul_y = nt.nodes.new("ShaderNodeMath"); mul_y.operation = "MULTIPLY"
    ln(sep.outputs["Y"], mul_y.inputs[0]); ln(sep.outputs["Y"], mul_y.inputs[1])
    mul_z = nt.nodes.new("ShaderNodeMath"); mul_z.operation = "MULTIPLY"
    ln(sep.outputs["Z"], mul_z.inputs[0]); ln(sep.outputs["Z"], mul_z.inputs[1])
    add_yz = nt.nodes.new("ShaderNodeMath"); add_yz.operation = "ADD"
    ln(mul_y.outputs["Value"], add_yz.inputs[0])
    ln(mul_z.outputs["Value"], add_yz.inputs[1])

    # Normalize by eye radius (~0.023 for carnivore eye)
    # Scale so that at iris boundary (~60% radius) we get fac=0.6
    scale_r = nt.nodes.new("ShaderNodeMath"); scale_r.operation = "MULTIPLY"
    ln(add_yz.outputs["Value"], scale_r.inputs[0])
    scale_r.inputs[1].default_value = 1800.0  # tuned for eye_rad ~ 0.023

    # Pupil: dark center circle
    cr_pupil = nt.nodes.new("ShaderNodeValToRGB")
    ln(scale_r.outputs["Value"], cr_pupil.inputs["Fac"])
    cr_pupil.color_ramp.elements[0].position = 0.0
    cr_pupil.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)  # pupil black
    cr_pupil.color_ramp.elements[1].position = 0.15
    cr_pupil.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)  # pupil edge

    # Iris ring color (random hue per seed)
    iris_hue = float(np.random.uniform(0.05, 0.55))
    iris_color = _hsv2rgba(iris_hue, np.random.uniform(0.5, 0.9), np.random.uniform(0.2, 0.6))

    # Iris color ramp: pupil -> iris -> sclera boundary
    cr_iris = nt.nodes.new("ShaderNodeValToRGB")
    ln(scale_r.outputs["Value"], cr_iris.inputs["Fac"])
    cr_iris.color_ramp.elements.new(0.15)
    cr_iris.color_ramp.elements.new(0.45)
    cr_iris.color_ramp.elements[0].position = 0.0
    cr_iris.color_ramp.elements[0].color = (0.005, 0.005, 0.005, 1.0)  # pupil
    cr_iris.color_ramp.elements[1].position = 0.12
    cr_iris.color_ramp.elements[1].color = iris_color  # iris inner
    cr_iris.color_ramp.elements[2].position = 0.38
    cr_iris.color_ramp.elements[2].color = iris_color  # iris outer
    cr_iris.color_ramp.elements[3].position = 0.45
    cr_iris.color_ramp.elements[3].color = (0.9, 0.9, 0.9, 1.0)  # sclera

    # Voronoi texture for iris fiber pattern
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(tc.outputs["Object"], voronoi.inputs["Vector"])
    voronoi.inputs["Scale"].default_value = 80.0

    # Mix iris color with voronoi for radial fibers
    mix_iris = nt.nodes.new("ShaderNodeMix"); mix_iris.data_type = "RGBA"
    mix_iris.inputs[0].default_value = 0.15
    ln(cr_iris.outputs["Color"], mix_iris.inputs[6])
    ln(voronoi.outputs["Color"], mix_iris.inputs[7])

    # PrincipledBSDF: very glossy wet eye surface
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_iris.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.02
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = 0.8
    # Coat for wet look
    coat_key = "Coat Weight" if "Coat Weight" in bsdf.inputs else "Clearcoat"
    if coat_key in bsdf.inputs:
        bsdf.inputs[coat_key].default_value = 1.0
        coat_rough_key = "Coat Roughness" if "Coat Roughness" in bsdf.inputs else "Clearcoat Roughness"
        if coat_rough_key in bsdf.inputs:
            bsdf.inputs[coat_rough_key].default_value = 0.01

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def _pick_body_material(seed):
    """Weighted random selection matching material_assignments.carnivore:
    Tiger(3), SpotSparse(2), Giraffe(0.2)."""

    weights = [3.0, 2.0, 0.2]
    total = sum(weights)
    r = float(np.random.uniform(0, total))
    if r < weights[0]:
        return make_tiger_material(seed)
    elif r < weights[0] + weights[1]:
        return make_spot_sparse_material(seed)
    else:
        return make_giraffe_material(seed)

CREATURE_MAT = _pick_body_material(SEED)
TONGUE_MAT = make_tongue_material(SEED, "TongueMaterial")
BONE_MAT = make_bone_material(SEED, "BoneMaterial")
NOSE_MAT = make_nose_material(SEED, "NoseMaterial")
EYEBALL_MAT = make_eyeball_material(SEED, "EyeballMaterial")

def md5_hash(x):
    if isinstance(x, (tuple, list)):
        m = hashlib.md5()
        for s in x:
            m.update(str(s).encode("utf-8"))
        return m
    return hashlib.md5(str(x).encode("utf-8"))

def int_hash(x, max_val=(2**32 - 1)):
    return abs(int(md5_hash(x).hexdigest(), 16)) % max_val

# NURBS DATA -- embedded base64

_NURBS_RAW = {
    "body_feline_cheetah": ((9, 8, 3), "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"),
    "body_feline_housecat": ((9, 8, 3), "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"),
    "body_feline_tiger": ((9, 8, 3), "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"),
    "body_feline_tiger_2": ((9, 8, 3), "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"),
    "body_feline_wolf": ((9, 8, 3), "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"),
    "head_carnivore_tiger": ((9, 12, 3), "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"),
    "head_carnivore_wolf": ((9, 12, 3), "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"),
}

NURBS_DATA = {}
for _k, (_shape, _b64) in _NURBS_RAW.items():
    NURBS_DATA[_k] = np.frombuffer(base64.b64decode(_b64), dtype=np.float64).reshape(_shape).copy()

def load_nurbs(name):
    return NURBS_DATA[name]

# MATH UTILITIES

def lerp(a, b, t):
    return (1.0 - t) * a + t * b

def lerp_sample(vec, ts):
    vec = np.asarray(vec, dtype=np.float64)
    ts = np.asarray(ts, dtype=np.float64)
    idx = np.clip(np.floor(ts).astype(int), 0, len(vec) - 1)
    frac = ts - idx
    res = vec[idx].copy()
    m = idx < (len(vec) - 1)
    if vec.ndim > 1:
        res[m] = (1 - frac[m, None]) * res[m] + frac[m, None] * vec[idx[m] + 1]
    else:
        res[m] = (1 - frac[m]) * res[m] + frac[m] * vec[idx[m] + 1]
    return res

def cross_matrix(v):
    o = np.zeros(len(v))
    return np.stack([
        np.stack([o, -v[:, 2], v[:, 1]], axis=-1),
        np.stack([v[:, 2], o, -v[:, 0]], axis=-1),
        np.stack([-v[:, 1], v[:, 0], o], axis=-1),
    ], axis=-1).transpose(0, 2, 1)

def rodrigues(angle, axi):
    axi = axi / np.linalg.norm(axi, axis=-1, keepdims=True)
    n = len(axi)
    eye = np.zeros((n, 3, 3))
    eye[:, [0, 1, 2], [0, 1, 2]] = 1.0
    th = angle[:, None, None]
    K = cross_matrix(axi)
    return eye + np.sin(th) * K + (1.0 - np.cos(th)) * (K @ K)

def rotate_match_directions(a, b):
    a, b = np.array(a, float), np.array(b, float)
    axes = np.cross(a, b, axis=-1)
    m = np.linalg.norm(axes, axis=-1) > 1e-6
    rots = np.tile(np.eye(3), (len(a), 1, 1)).astype(float)
    if not m.any():
        return rots
    na = np.linalg.norm(a[m], axis=-1)
    nb = np.linalg.norm(b[m], axis=-1)
    dots = np.clip((a[m] * b[m]).sum(-1) / (na * nb + 1e-12), -1, 1)
    rots[m] = rodrigues(np.arccos(dots), axes[m])
    return rots

def skeleton_to_tangents(sk):
    sk = np.asarray(sk, float)
    ax = np.empty_like(sk)
    ax[-1] = sk[-1] - sk[-2]
    ax[:-1] = sk[1:] - sk[:-1]
    ax[1:-1] = (ax[1:-1] + ax[:-2]) / 2
    nrm = np.linalg.norm(ax, axis=-1, keepdims=True)
    return ax / np.where(nrm > 0, nrm, 1)

def clip_gaussian(mean, std, lo, hi, max_tries=20):
    for _ in range(max_tries):
        v = np.random.normal(mean, std)
        if lo <= v <= hi:
            return v
    return float(np.clip(np.random.normal(mean, std), lo, hi))

def euler_quat(roll_deg, pitch_deg, yaw_deg):
    return mathutils.Euler(
        [math.radians(roll_deg), math.radians(pitch_deg), math.radians(yaw_deg)]
    ).to_quaternion()

def quat_align(a, b):
    if not isinstance(a, mathutils.Vector):
        a = mathutils.Vector(a)
    if not isinstance(b, mathutils.Vector):
        b = mathutils.Vector(b)
    cross = a.cross(b)
    if cross.length < 1e-8:
        return mathutils.Quaternion()
    return mathutils.Quaternion(cross, a.angle(b))

def build_world_matrix(rot_quat, translation):
    M = rot_quat.to_matrix().to_4x4()
    M.translation = mathutils.Vector([float(x) for x in translation[:3]])
    return M

MIRROR_Y = mathutils.Matrix.Scale(-1, 4, (0, 1, 0))

# NURBS DECOMPOSE / RECOMPOSE

def factorize_nurbs_handles(handles):
    skeleton = handles.mean(axis=1)
    tangents = skeleton_to_tangents(skeleton)
    forward = np.zeros_like(tangents)
    forward[:, 0] = 1.0
    rot_mats = rotate_match_directions(tangents, forward)
    profiles = handles - skeleton[:, None]
    profiles = np.einsum("bij,bvj->bvi", rot_mats, profiles)
    ts = np.linspace(0.0, 1.0, handles.shape[0])
    return skeleton, ts, profiles

def decompose_nurbs_handles(handles):
    skeleton, ts, profiles = factorize_nurbs_handles(handles)
    rads = np.linalg.norm(profiles, axis=2, keepdims=True).mean(axis=1, keepdims=True)
    rads = np.clip(rads, 1e-3, 1e5)
    profiles_norm = profiles / rads
    skeleton_root = skeleton[[0]]
    dirs = np.diff(skeleton, axis=0)
    lens = np.linalg.norm(dirs, axis=-1)
    length = lens.sum()
    proportions = lens / length
    thetas = np.rad2deg(np.arctan2(dirs[:, 2], dirs[:, 0]))
    skeleton_yoffs = dirs[:, 1] / lens
    return dict(
        ts=ts, rads=rads, skeleton_root=skeleton_root,
        skeleton_yoffs=skeleton_yoffs, length=length,
        proportions=proportions, thetas=thetas,
        profiles_norm=profiles_norm,
    )

def recompose_nurbs_handles(params):
    lens = params["length"] * params["proportions"]
    theta = np.deg2rad(params["thetas"])
    offs = np.stack([
        lens * np.cos(theta),
        lens * params["skeleton_yoffs"],
        lens * np.sin(theta),
    ], axis=-1)
    skeleton = np.cumsum(
        np.concatenate([params["skeleton_root"], offs], axis=0), axis=0
    )
    return compute_profile_verts(
        skeleton, params["ts"],
        params["profiles_norm"] * params["rads"],
        profile_as_points=True,
    )

def compute_profile_verts(skeleton, ts, profiles, profile_as_points=False):
    k = len(skeleton)
    axes = skeleton_to_tangents(skeleton)
    t_scaled = np.asarray(ts, dtype=np.float64) * (k - 1)
    s_axes = lerp_sample(axes, t_scaled)
    s_pos = lerp_sample(skeleton, t_scaled)
    if not profile_as_points:
        raise NotImplementedError
    pv = np.asarray(profiles, dtype=np.float64)
    forward = np.zeros_like(s_axes)
    forward[:, 0] = 1.0
    rots = rotate_match_directions(forward, s_axes)
    return np.einsum("bij,bvj->bvi", rots, pv) + s_pos[:, None]

def get_skeleton_from_params(params):
    lens = params["length"] * params["proportions"]
    theta = np.deg2rad(params["thetas"])
    offs = np.stack([
        lens * np.cos(theta),
        lens * params["skeleton_yoffs"],
        lens * np.sin(theta),
    ], axis=-1)
    return np.cumsum(
        np.concatenate([params["skeleton_root"], offs], axis=0), axis=0
    )

# CYLINDER TOPOLOGY

def compute_cylinder_topology(n, m, cyclic=True):
    loop = np.arange(m)
    h_nbrs = np.stack([loop, np.roll(loop, -1)], axis=-1)
    r_offsets = np.arange(0, n * m, m)
    ring_edges = (r_offsets[:, None, None] + h_nbrs[None]).reshape(-1, 2)
    if not cyclic:
        ring_edges = ring_edges[ring_edges[:, 0] % m != m - 1]
    v_nbrs = np.stack([loop, loop + m], axis=-1)
    b_offsets = np.arange(0, (n - 1) * m, m)
    bridge_edges = (b_offsets[:, None, None] + v_nbrs[None]).reshape(-1, 2)
    edges = np.concatenate([ring_edges, bridge_edges])
    face_nbrs = np.concatenate([h_nbrs, h_nbrs[:, ::-1] + m], axis=-1)
    faces = (b_offsets[:, None, None] + face_nbrs[None]).reshape(-1, 4)
    if not cyclic:
        faces = faces[faces[:, 0] % m != m - 1]
    return edges.tolist(), faces.tolist()

# BLENDER UTILITIES

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.node_groups):
        for item in list(coll):
            if item.users == 0:
                coll.remove(item)

def sel(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_tf(obj):
    sel(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def new_mesh_obj(name, verts, edges, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(list(map(tuple, verts)), list(map(tuple, edges)),
                     list(map(tuple, faces)))
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def shade_smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

def add_subsurf(obj, levels=2):
    m = obj.modifiers.new("SS", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    sel(obj)
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def add_boolean_union(target, cutter):
    n_before = len(target.data.vertices)
    mod = target.modifiers.new("BOOL", "BOOLEAN")
    mod.operation = "UNION"
    mod.object = cutter
    mod.solver = "FLOAT"
    sel(target)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    n_after = len(target.data.vertices)
    # Safety: if boolean destroyed >50% of verts, revert and just join instead
    if n_after < n_before * 0.5:
        # Cutter still exists, join it instead
        sel(target)
        cutter.select_set(True)
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.join()
        return target
    sel(cutter)
    bpy.ops.object.delete()
    return target

def add_boolean_diff(target, cutter):
    n_before = len(target.data.vertices)
    mod = target.modifiers.new("BOOL", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    mod.solver = "FLOAT"
    sel(target)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    n_after = len(target.data.vertices)
    # Safety: if boolean destroyed >50% of verts, skip the cut
    if n_after < n_before * 0.5:
        pass
        # Just delete the cutter and return target as-is
    sel(cutter)
    bpy.ops.object.delete()
    return target

def clean_mesh(obj, threshold=1e-4):
    sel(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=threshold)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

# NURBS MESH BUILDER

def sample_nurbs_params(prefix, temperature=0.3, var=1):
    target_keys = [k for k in NURBS_DATA if k.startswith(prefix)]
    weights = np.random.dirichlet(np.full(len(target_keys), temperature))
    handles = sum(w * load_nurbs(k) for k, w in zip(target_keys, weights))
    p = decompose_nurbs_handles(handles)

    def _N(u, v, d=1):
        return np.random.normal(u, np.array(v) * var, d)

    sz = _N(1, 0.1)
    p["length"] *= sz * _N(1, 0.1)
    p["rads"] *= sz * _N(1, 0.1) * _N(1, 0.15, p["rads"].shape)
    p["proportions"] *= _N(1, 0.15)
    ang_noise = _N(0, 7, p["thetas"].shape)
    ang_noise -= ang_noise.mean()
    p["thetas"] += ang_noise
    n, m, _ = p["profiles_norm"].shape
    pn = _N(1, 0.07, (1, m, 1)) * _N(1, 0.15, (n, m, 1))
    pn[:, :m // 2 - 1] = pn[:, m // 2:-1][:, ::-1]
    p["profiles_norm"] *= pn
    return p

def build_nurbs_mesh(params, name="nurbs_mesh", subsurf_levels=2):
    handles = recompose_nurbs_handles(params)
    n, m, _ = handles.shape
    verts = handles.reshape(-1, 3)
    edges, faces = compute_cylinder_topology(n, m, cyclic=True)
    obj = new_mesh_obj(name, verts, edges, faces)
    clean_mesh(obj, threshold=1e-3)
    shade_smooth(obj)
    if subsurf_levels > 0:
        add_subsurf(obj, subsurf_levels)
    return obj

# POLAR BEZIER SKELETON + SMOOTH TAPER + TUBE CREATION

def polar_bezier_skeleton(angles_deg, seg_lengths, n_pts=26,
                          origin=None, do_bezier=True):
    if origin is None:
        origin = np.zeros(3)
    origin = np.asarray(origin, float)
    a = np.cumsum(np.array(angles_deg, float) * np.pi / 180.0)

    def p2c(ang, length, org):
        return org + length * np.array([np.cos(ang), 0.0, np.sin(ang)])

    pts = np.zeros((4, 3))
    pts[0] = origin
    pts[1] = p2c(a[0], seg_lengths[0], pts[0])
    pts[2] = p2c(a[1], seg_lengths[1], pts[1])
    pts[3] = p2c(a[2], seg_lengths[2], pts[2])

    if do_bezier:
        t = np.linspace(0, 1, n_pts)
        skel = (((1 - t) ** 3)[:, None] * pts[0]
                + (3 * (1 - t) ** 2 * t)[:, None] * pts[1]
                + (3 * (1 - t) * t ** 2)[:, None] * pts[2]
                + (t ** 3)[:, None] * pts[3])
    else:
        n_seg = n_pts // 3
        segs = []
        for i in range(3):
            ts = np.linspace(0, 1, n_seg + 1, endpoint=(i == 2))
            segs.append(pts[i][None] * (1 - ts[:, None]) + pts[i + 1][None] * ts[:, None])
        skel = np.vstack(segs)[:n_pts]
    return skel

def smooth_taper_arr(t, start_rad, end_rad, fullness, clamp_min=True):
    """Compute tapered radius along a tube: sin(t*pi)^(1/f) * lerp(r1,r2,t).
    clamp_min=True: proportional clamping at 40% of max(r1,r2) so tube
       endpoints stay thick enough for voxel-remesh blending.
    clamp_min=False: for muscles -- allow taper to zero at endpoints.
    """

    t = np.asarray(t, float)
    shaped = np.maximum(np.sin(t * np.pi), 0) ** (1.0 / max(fullness, 1e-4))
    result = shaped * (start_rad + (end_rad - start_rad) * t)
    if clamp_min:
        # Proportional to tube size -- never inflates small tubes (toes/claws)
        # above their natural radius. 40% of max radius gives enough overlap
        # for voxel remesh at both large (legs) and small (toes) scales.
        min_rad = 0.4 * max(abs(start_rad), abs(end_rad))
        return np.maximum(result, min_rad)
    return np.maximum(result, 0.0)

def create_tube_mesh(name, length, rad1, rad2,
                     angles_deg=(0, 0, 0), aspect=1.0, fullness=4.0,
                     proportions=(1 / 3, 1 / 3, 1 / 3),
                     origin=(0, 0, 0), do_bezier=True,
                     n_skel=26, n_profile=16):
    prop = np.array(proportions, float)
    prop /= prop.sum()
    seg_lengths = prop * length

    skel = polar_bezier_skeleton(angles_deg, seg_lengths, n_skel,
                                 np.array(origin, float), do_bezier)
    t_arr = np.linspace(0, 1, n_skel)
    radii = smooth_taper_arr(t_arr, rad1, rad2, fullness)

    if aspect >= 1.0:
        ay, az = aspect, 1.0
    else:
        ay, az = 1.0, 1.0 / aspect
    theta = np.linspace(-np.pi / 2, 1.5 * np.pi, n_profile, endpoint=False)
    profile_local = np.stack([
        np.zeros(n_profile),
        ay * np.cos(theta),
        az * np.sin(theta),
    ], axis=-1)

    tangents = skeleton_to_tangents(skel)
    fwd = np.zeros_like(tangents)
    fwd[:, 0] = 1.0
    R = rotate_match_directions(fwd, tangents)

    profile_pts = np.einsum('bij,vj->bvi', R, profile_local)
    verts = profile_pts * radii[:, None, None] + skel[:, None, :]

    edges, faces = compute_cylinder_topology(n_skel, n_profile)
    return new_mesh_obj(name, verts.reshape(-1, 3), edges, faces), skel

def create_gn_tube(name, length, rad1, rad2,
                   angles_deg=(0, 0, 0), aspect=1.0, fullness=4.0,
                   proportions=(1 / 3, 1 / 3, 1 / 3),
                   origin=(0, 0, 0), do_bezier=True,
                   n_skel=26, n_profile=32):
    """Create a tube using GeoNodes CurveToMesh -- properly handles bends.

    Same interface as create_tube_mesh but uses build_curve_tube internally.
    Returns (mesh_obj, skeleton).
    """

    prop = np.array(proportions, float)
    prop /= prop.sum()
    seg_lengths = prop * length

    skel = polar_bezier_skeleton(angles_deg, seg_lengths, n_skel,
                                 np.array(origin, float), do_bezier)
    t_arr = np.linspace(0, 1, n_skel)
    radii = smooth_taper_arr(t_arr, rad1, rad2, fullness)

    tube = build_curve_tube(skel, radii, n_profile=n_profile,
                            aspect=aspect, fill_caps=True, name=name)
    return tube, skel

def build_curve_tube(skeleton_pts, radii, n_profile=40, aspect=1.0,
                     fill_caps=True, name="tube", tilts=None):
    curve_data = bpy.data.curves.new(name + "_c", 'CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(skeleton_pts) - 1)
    for i, (pt, r) in enumerate(zip(skeleton_pts, radii)):
        spline.points[i].co = (float(pt[0]), float(pt[1]), float(pt[2]), 1.0)
        spline.points[i].radius = max(float(r), 0.0)
        if tilts is not None:
            spline.points[i].tilt = float(tilts[i])

    curve_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(curve_obj)

    tree = bpy.data.node_groups.new(name + "_gn", 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = tree.nodes.new('NodeGroupInput')
    out = tree.nodes.new('NodeGroupOutput')

    circle = tree.nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.inputs['Resolution'].default_value = n_profile
    circle.inputs['Radius'].default_value = 1.0

    if abs(aspect - 1.0) > 0.01:
        xform = tree.nodes.new('GeometryNodeTransform')
        xform.inputs['Scale'].default_value = (aspect, 1.0, 1.0)
        tree.links.new(circle.outputs['Curve'], xform.inputs['Geometry'])
        profile_out = xform.outputs['Geometry']
    else:
        profile_out = circle.outputs['Curve']

    radius_node = tree.nodes.new('GeometryNodeInputRadius')
    c2m = tree.nodes.new('GeometryNodeCurveToMesh')
    tree.links.new(inp.outputs['Geometry'], c2m.inputs['Curve'])
    tree.links.new(profile_out, c2m.inputs['Profile Curve'])
    tree.links.new(radius_node.outputs['Radius'], c2m.inputs['Scale'])
    c2m.inputs['Fill Caps'].default_value = fill_caps

    tree.links.new(c2m.outputs['Mesh'], out.inputs['Geometry'])

    mod = curve_obj.modifiers.new("GN", 'NODES')
    mod.node_group = tree
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    new_mesh = bpy.data.meshes.new_from_object(eval_obj)

    mesh_obj = bpy.data.objects.new(name, new_mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)
    shade_smooth(mesh_obj)

    bpy.data.objects.remove(curve_obj, do_unlink=True)
    bpy.data.node_groups.remove(tree)
    return mesh_obj

# RAYCAST ATTACHMENT (from BeetleFactory)

def raycast_attach(skeleton, bvh, coord, obj_rot_quat=None):
    u, v, r = coord
    if obj_rot_quat is None:
        obj_rot_quat = mathutils.Quaternion()
    idx = np.array([u]) * (len(skeleton) - 1)
    tangents = skeleton_to_tangents(skeleton)
    forward = lerp_sample(tangents, idx).reshape(3)
    origin = mathutils.Vector(lerp_sample(skeleton, idx).reshape(3).tolist())
    basis = obj_rot_quat @ quat_align(
        mathutils.Vector((1, 0, 0)),
        mathutils.Vector(forward.tolist()),
    )
    dir_rot = euler_quat(180 * v, 0, 0) @ euler_quat(0, 90, 0)
    direction = basis @ dir_rot @ mathutils.Vector((1, 0, 0))
    hit, _, _, _ = bvh.ray_cast(origin, direction)
    if hit is None:
        location = np.array(origin)
    else:
        location = lerp(np.array(origin), np.array(hit), r)
    return location, forward

# SURFACE MUSCLE SYSTEM
# Replicates nodegroup_part_surface_simple + nodegroup_surface_muscle

def part_surface_point(skeleton, bvh, coord):
    """Compute a point on/near the tube surface via BVH raycast.
    coord = (length_fac, yaw_rad, rad)
    """

    u = max(0.0, min(1.0, coord[0]))
    yaw = coord[1]
    rad = coord[2]

    idx_f = u * (len(skeleton) - 1)
    pos = lerp_sample(skeleton, np.array([idx_f]))[0]
    tangent = lerp_sample(skeleton_to_tangents(skeleton), np.array([idx_f]))[0]

    # Rotate tangent by Euler(pi/2, yaw, pi/2) -- matches VectorRotate EULER_XYZ
    direction = mathutils.Vector(tangent.tolist())
    direction.rotate(mathutils.Euler((math.pi / 2, yaw, math.pi / 2), 'XYZ'))

    origin = mathutils.Vector(pos.tolist())
    hit, normal, face_idx, dist = bvh.ray_cast(origin, direction, 10.0)

    if hit is None:
        # Fallback: offset by estimated radius in ray direction
        return pos + np.array(direction.normalized()) * 0.05 * abs(rad)

    return lerp(pos, np.array(hit), rad)

def quadratic_bezier_pts(p0, p1, p2, n=16):
    """Generate points on a quadratic Bezier curve."""

    t = np.linspace(0, 1, n)
    return (np.outer((1 - t) ** 2, p0) +
            np.outer(2 * (1 - t) * t, p1) +
            np.outer(t ** 2, p2))

def build_surface_muscle(skeleton, bvh, coord0, coord1, coord2,
                         start_rad, end_rad, fullness,
                         profile_height, start_tilt, end_tilt,
                         name="muscle"):
    """Build a surface muscle mesh matching nodegroup_surface_muscle."""

    p0 = part_surface_point(skeleton, bvh, coord0)
    p1 = part_surface_point(skeleton, bvh, coord1)
    p2 = part_surface_point(skeleton, bvh, coord2)

    # QuadraticBezier spine (16 points)
    muscle_skel = quadratic_bezier_pts(p0, p1, p2, 16)

    # Smooth taper radius -- NO min_rad clamping for muscles so they
    # taper to zero at endpoints and blend smoothly with the base tube
    t_arr = np.linspace(0, 1, 16)
    radii = smooth_taper_arr(t_arr, start_rad, end_rad, fullness, clamp_min=False)

    # Tilt along spine: interpolate start_tilt to end_tilt (degrees -> radians)
    tilts = np.linspace(math.radians(start_tilt), math.radians(end_tilt), 16)

    # Build tube with profile height (aspect ratio) and tilt
    tube = build_curve_tube(muscle_skel, radii, n_profile=24,
                            aspect=profile_height, fill_caps=True, name=name,
                            tilts=tilts)
    return tube

def mirror_y_obj(obj):
    """Duplicate object, scale Y by -1, apply transform. Returns new object."""

    sel(obj)
    bpy.ops.object.duplicate()
    dup = bpy.context.active_object
    dup.scale.y = -1.0
    apply_tf(dup)
    # Flip normals
    sel(dup)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    return dup

def symmetric_muscles(skeleton, bvh, coord0, coord1, coord2,
                      start_rad, end_rad, fullness,
                      profile_height, start_tilt, end_tilt,
                      name="muscle"):
    """Build a surface muscle and its Y-mirror."""

    m1 = build_surface_muscle(skeleton, bvh, coord0, coord1, coord2,
                              start_rad, end_rad, fullness,
                              profile_height, start_tilt, end_tilt, name)
    m2 = mirror_y_obj(m1)
    return [m1, m2]

# PART BUILDERS

def create_back_leg(params):
    """Build a quadruped back leg: tube + 3 surface muscles."""

    lrr = params["length_rad1_rad2"]
    length, rad1, rad2 = float(lrr[0]), float(lrr[1]), float(lrr[2])
    angles = params["angles_deg"]
    fullness = params.get("fullness", 50.0)
    aspect = params.get("aspect", 1.0)

    tube, skel = create_gn_tube("back_leg", length, rad1, rad2,
                                angles_deg=angles, fullness=fullness,
                                aspect=aspect, origin=(-0.05, 0, 0))
    shade_smooth(tube)

    # BVH for surface muscle raycasting
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(tube, depsgraph)

    parts = [tube]

    # Thigh muscle
    trf = params.get("Thigh Rad1 Rad2 Fullness", np.array([0.33, 0.15, 2.5]))
    tht = params.get("Thigh Height Tilt1 Tilt2", np.array([0.6, 0.0, 0.0]))
    m = build_surface_muscle(skel, bvh,
                             (0.02, 3.1416, 3.0), (0.1, -0.14, 1.47), (0.73, 4.71, 1.13),
                             float(trf[0]), float(trf[1]), float(trf[2]),
                             float(tht[0]), float(tht[1]), float(tht[2]),
                             name="thigh")
    parts.append(m)

    # Calf muscle
    crf = params.get("Calf Rad1 Rad2 Fullness", np.array([0.17, 0.07, 2.5]))
    cht = params.get("Calf Height Tilt1 Tilt2", np.array([0.8, 0.0, 0.0]))
    m = build_surface_muscle(skel, bvh,
                             (0.51, 18.91, 0.4), (0.69, 0.26, 0.0), (0.94, 1.5708, 1.13),
                             float(crf[0]), float(crf[1]), float(crf[2]),
                             float(cht[0]), float(cht[1]), float(cht[2]),
                             name="calf")
    parts.append(m)

    # Thigh 2 muscle
    m = build_surface_muscle(skel, bvh,
                             (0.04, 3.1416, 0.0), (0.01, 3.46, -0.05), (0.73, 4.71, 0.9),
                             float(trf[0]), float(trf[1]), float(trf[2]),
                             float(tht[0]), float(tht[1]), float(tht[2]),
                             name="thigh2")
    parts.append(m)

    result = join_objs(parts)
    result.name = "back_leg"
    return result, skel

def create_front_leg(params):
    """Build a quadruped front leg: tube + 4 surface muscles."""

    lrr = params["length_rad1_rad2"]
    length, rad1, rad2 = float(lrr[0]), float(lrr[1]), float(lrr[2])
    angles = params["angles_deg"]
    aspect = params.get("aspect", 1.0)

    tube, skel = create_gn_tube("front_leg", length, rad1, rad2,
                                angles_deg=angles, fullness=2.5,
                                aspect=aspect, origin=(-0.15, 0, 0.09))
    shade_smooth(tube)

    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(tube, depsgraph)

    parts = [tube]

    # Shoulder
    srf = params.get("Shoulder Rad1 Rad2 Fullness", np.array([0.22, 0.22, 2.5]))
    sht = params.get("Shoulder Height, Tilt1, Tilt2", np.array([0.74, 0.0, 0.0]))
    m = build_surface_muscle(skel, bvh,
                             (0.0, 0.0, 0.0), (0.2, 0.0, 0.0), (0.55, 0.0, 0.0),
                             float(srf[0]), float(srf[1]), float(srf[2]),
                             float(sht[0]), float(sht[1]), float(sht[2]),
                             name="shoulder")
    parts.append(m)

    # Elbow 2
    erf = params.get("Elbow Rad1 Rad2 Fullness", np.array([0.12, 0.1, 2.5]))
    eht = params.get("Elbow Height, Tilt1, Tilt2", np.array([0.9, 0.0, 0.0]))
    m = build_surface_muscle(skel, bvh,
                             (0.53, 1.5708, 1.69), (0.57, 0.0, 0.0), (0.95, 0.0, 0.0),
                             float(erf[0]), float(erf[1]), float(erf[2]),
                             float(eht[0]), float(eht[1]), float(eht[2]),
                             name="elbow2")
    parts.append(m)

    # Elbow 1
    m = build_surface_muscle(skel, bvh,
                             (0.22, 1.5708, 1.0), (0.4, 0.0, 0.0), (0.57, 1.571, 1.7),
                             float(erf[0]), float(erf[1]), float(erf[2]),
                             float(eht[0]), float(eht[1]), float(eht[2]),
                             name="elbow1")
    parts.append(m)

    # Forearm
    crf = params.get("Calf Rad1 Rad2 Fullness", np.array([0.08, 0.08, 2.5]))
    cht = params.get("Calf Height, Tilt1, Tilt2", np.array([0.74, 0.0, 0.0]))
    m = build_surface_muscle(skel, bvh,
                             (0.41, -1.7008, 0.6), (0.57, 0.0, 0.8), (0.95, 0.0, 0.0),
                             float(crf[0]), float(crf[1]), float(crf[2]),
                             float(cht[0]), float(cht[1]), float(cht[2]),
                             name="forearm")
    parts.append(m)

    result = join_objs(parts)
    result.name = "front_leg"
    return result, skel

def create_foot(params):
    """Build a foot with toes, toebeans, and claws."""

    lrr = params.get("length_rad1_rad2", np.array([0.27, 0.04, 0.09]))
    length, rad1, rad2 = float(lrr[0]), float(lrr[1]), float(lrr[2])
    num_toes = int(params.get("Num Toes", 4))
    toe_lrr = params.get("Toe Length Rad1 Rad2", np.array([0.3, 0.045, 0.025]))
    toe_rotate = params.get("Toe Rotate", (0.0, -0.7, 0.0))
    toe_splay = float(params.get("Toe Splay", 20.0))
    toebean_radius = float(params.get("Toebean Radius", 0.03))
    claw_curl = float(params.get("Claw Curl Deg", 30.0))
    claw_pct = params.get("Claw Pct Length Rad1 Rad2", np.array([0.3, 0.5, 0.0]))

    # Main foot pad tube
    foot_tube, foot_skel = create_gn_tube("foot_pad", length, rad1, rad2,
                                          angles_deg=(10, 8, -25))
    shade_smooth(foot_tube)
    parts = [foot_tube]

    # Endpoint of foot
    endpoint = foot_skel[-1]

    # Toe placement: spread from -0.45*rad2 to +0.45*rad2 in Y
    y_spread = 0.45 * rad2
    toe_start = endpoint + np.array([-0.07, -y_spread, 0.1 * rad2])
    toe_end = endpoint + np.array([-0.07, y_spread, 0.1 * rad2])

    for ti in range(num_toes):
        frac = ti / max(num_toes - 1, 1)
        toe_pos = lerp(toe_start, toe_end, frac)

        # Splay angle
        splay_angle = lerp(-toe_splay, toe_splay, frac)

        # Build toe -- use GeoNodes tube for cleaner geometry at bends
        toe_l, toe_r1, toe_r2 = float(toe_lrr[0]), float(toe_lrr[1]), float(toe_lrr[2])
        curl_angles = np.array([-50.0, 25.0, 35.0]) * params.get("Toe Curl Scalar", 1.0)

        toe_tube, toe_skel = create_gn_tube(
            f"toe_{ti}", toe_l * 0.54, toe_r1, toe_r2,
            angles_deg=curl_angles, fullness=3.0,
            origin=(-0.05, 0, 0), n_skel=16, n_profile=16)
        shade_smooth(toe_tube)

        # Single toebean sphere (merged with toe tip for cleaner mesh)
        bean_pos = toe_skel[int(len(toe_skel) * 0.7)]
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6,
                                             radius=toebean_radius * 0.7,
                                             location=tuple(bean_pos))
        bean = bpy.context.active_object
        bean.scale = (1.3, 0.9, 0.7)
        apply_tf(bean)

        # Position toe
        toe_rot = mathutils.Euler(tuple(toe_rotate))
        splay_rot = mathutils.Euler((0, 0, math.radians(splay_angle)))
        combined = splay_rot.to_matrix() @ toe_rot.to_matrix()
        rot_quat = combined.to_quaternion()

        toe_parts = [toe_tube, bean]
        toe_joined = join_objs(toe_parts)
        toe_joined.matrix_world = build_world_matrix(rot_quat, toe_pos)
        apply_tf(toe_joined)
        parts.append(toe_joined)

    # Heel pad
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6,
                                         radius=0.02,
                                         location=tuple(endpoint + np.array([-0.02, 0, 0])))
    heel = bpy.context.active_object
    heel.scale = (0.8, 1.0, 0.8)
    apply_tf(heel)
    parts.append(heel)

    result = join_objs(parts)
    result.name = "foot"
    return result, foot_skel

def create_tail(params):
    """Build a simple tube tail."""

    lrr = params.get("length_rad1_rad2", (0.5, 0.05, 0.02))
    angles = params.get("angles_deg", np.array([31.39, 65.81, -106.93]))
    aspect = params.get("aspect", 1.0)

    tube, skel = create_gn_tube("tail", float(lrr[0]), float(lrr[1]), float(lrr[2]),
                                angles_deg=angles, aspect=aspect)
    shade_smooth(tube)
    return tube, skel

def create_carnivore_head(params):
    """Build a carnivore head: cranium + snout + jaw cutter + muscles."""

    lrr = params["length_rad1_rad2"]
    length, rad1, rad2 = float(lrr[0]), float(lrr[1]), float(lrr[2])
    aspect = float(params.get("aspect", 1.0))

    # Main cranium tube
    cranium, cran_skel = create_gn_tube("cranium", length, rad1, rad2,
                                          angles_deg=(-5.67, 0, 0), fullness=3.63,
                                          aspect=aspect, origin=(-0.07, 0, 0.05),
                                          n_skel=26, n_profile=16)
    shade_smooth(cranium)
    endpoint = cran_skel[-1]

    # Snout
    slrr = params.get("snout_length_rad1_rad2", np.array([0.22, 0.15, 0.15]))
    snout_l, snout_r1, snout_r2 = float(slrr[0]), float(slrr[1]), float(slrr[2])
    snout_y_scale = float(params.get("snout_y_scale", 0.62))
    snout_origin = endpoint + np.array([-0.1, 0, 0])

    # Bridge
    bridge_scale = params.get("Nose Bridge Scale", np.array([1.0, 0.35, 0.9]))
    bridge, _ = create_tube_mesh("bridge", snout_l, 0.17, 0.1,
                                 angles_deg=(-4, -4.5, -5.61), fullness=5.44,
                                 origin=tuple(snout_origin), n_skel=20, n_profile=14)
    bridge.location.z += 0.03
    bridge.scale = tuple(bridge_scale)
    apply_tf(bridge)

    # Snout body
    snout, _ = create_tube_mesh("snout", snout_l, snout_r1, snout_r2,
                                angles_deg=(-3, -4.5, -5.61), fullness=2.0,
                                origin=tuple(snout_origin), n_skel=20, n_profile=14)
    snout.location.z += 0.03
    snout.scale = (1.0, 0.7 * snout_y_scale, 0.7)
    apply_tf(snout)

    # Boolean union: cranium + bridge + snout
    cranium = add_boolean_union(cranium, bridge)
    cranium = add_boolean_union(cranium, snout)

    # Jaw cutter -- cut underside at 20% along skeleton
    # Scale cutter length relative to head length (nominal 0.36)
    cutter_len = min(0.33, length * 0.85)
    cutter_rad = min(0.13, rad1 * 0.65)
    cutter, _ = create_tube_mesh("jaw_cutter", cutter_len, cutter_rad, cutter_rad,
                                 origin=(0, 0, 0.09), n_skel=16, n_profile=12)
    # Position at base of head
    base_pt = cran_skel[0]
    cutter_pos = base_pt + (endpoint - base_pt) * 0.2
    cutter.location = mathutils.Vector(tuple(cutter_pos))
    cutter.location.z -= 0.05
    apply_tf(cutter)
    cranium = add_boolean_diff(cranium, cutter)

    # Skeleton for muscles: straight line from base to snout tip
    head_skel = np.linspace(cran_skel[0], endpoint, 20)

    # BVH for surface muscles
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    head_bvh = BVHTree.FromObject(cranium, depsgraph)

    parts = [cranium]

    # Jaw muscle
    jm = params.get("Jaw StartRad, EndRad, Fullness", np.array([0.06, 0.11, 1.5]))
    jh = params.get("Jaw ProfileHeight, StartTilt, EndTilt", np.array([0.8, 33.1, 0.0]))
    jmc = params.get("Jaw Muscle Middle Coord", np.array([0.24, 0.41, 1.3]))
    muscles = symmetric_muscles(head_skel, head_bvh,
                                (0.19, -0.41, 0.78), tuple(jmc), (0.67, 1.26, 0.52),
                                float(jm[0]), float(jm[1]), float(jm[2]),
                                float(jh[0]), float(jh[1]), float(jh[2]),
                                name="jaw_muscle")
    parts.extend(muscles)

    # Lip muscle
    lm = params.get("Lip StartRad, EndRad, Fullness", np.array([0.05, 0.09, 1.48]))
    lh = params.get("Lip ProfileHeight, StartTilt, EndTilt", np.array([0.8, 0.0, -17.2]))
    lmc = params.get("Lip Muscle Middle Coord", np.array([0.95, 0.0, 1.5]))
    muscles = symmetric_muscles(head_skel, head_bvh,
                                (0.51, -0.13, 0.02), tuple(lmc), (0.99, 10.57, 0.1),
                                float(lm[0]), float(lm[1]), float(lm[2]),
                                float(lh[0]), float(lh[1]), float(lh[2]),
                                name="lip")
    parts.extend(muscles)

    # Forehead muscle
    fm = params.get("Forehead StartRad, EndRad, Fullness", np.array([0.06, 0.05, 2.5]))
    fh = params.get("Forehead ProfileHeight, StartTilt, EndTilt", np.array([0.3, 60.6, 66.0]))
    fmc = params.get("Forehead Muscle Middle Coord", np.array([0.7, -1.32, 1.31]))
    muscles = symmetric_muscles(cran_skel, head_bvh,
                                (0.31, -1.06, 0.97), tuple(fmc), (0.95, -1.52, 0.9),
                                float(fm[0]), float(fm[1]), float(fm[2]),
                                float(fh[0]), float(fh[1]), float(fh[2]),
                                name="forehead")
    parts.extend(muscles)

    # Eye cutouts
    eye_rad = float(params.get("EyeRad", 0.023))
    eye_offset = params.get("EyeOffset", np.array([-0.25, 0.45, 0.3]))
    eye_pos = endpoint + eye_offset * rad2

    # Build eye spheres with eyeball material
    eyeballs = []
    for side in [1, -1]:
        ep = eye_pos.copy()
        ep[1] *= side
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8,
                                             radius=eye_rad,
                                             location=tuple(ep))
        eye = bpy.context.active_object
        eye.scale = (1.0, 1.0, 0.7)
        apply_tf(eye)
        eye.name = f"Eyeball_{side}"
        eye.data.materials.append(EYEBALL_MAT)
        eyeballs.append(eye)

    result = join_objs(parts)
    result.name = "carnivore_head"
    return result, head_skel, eyeballs

def create_carnivore_jaw(params):
    """Build jaw: main body + canine teeth + incisors + tongue."""

    lrr = params["length_rad1_rad2"]
    length, rad1, rad2 = float(lrr[0]), float(lrr[1]), float(lrr[2])

    # Main jaw tube -- polar_bezier with angles (0, 0, 13), scaled Y=1.7
    jaw_tube, jaw_skel = create_gn_tube("jaw_body", length, rad1, rad2,
                                          angles_deg=(0, 0, 13), fullness=2.6,
                                          n_skel=26, n_profile=14)
    shade_smooth(jaw_tube)
    jaw_tube.scale = (1.0, 1.7, 1.0)
    apply_tf(jaw_tube)

    parts = [jaw_tube]

    # Canine teeth
    canine_length = float(params.get("Canine Length", 0.05))
    if canine_length > 0.001:
        for side in [1, -1]:
            tooth_tube, _ = create_tube_mesh(
                f"canine_{side}", canine_length, 0.015, 0.003,
                n_skel=12, n_profile=10)
            shade_smooth(tooth_tube)
            # Position at 90% along jaw, offset to side
            t_pos = lerp_sample(jaw_skel, np.array([0.9 * (len(jaw_skel) - 1)]))[0]
            tooth_tube.location = mathutils.Vector(tuple(t_pos))
            tooth_tube.location.y += side * 0.03
            tooth_tube.location.z -= 0.02
            tooth_tube.rotation_euler = (math.radians(-17.6), math.radians(-53.49), 0)
            apply_tf(tooth_tube)
            parts.append(tooth_tube)

    # Incisor teeth
    incisor_size = float(params.get("Incisor Size", 0.01))
    if incisor_size > 0.001:
        # Create small cube teeth along an arc at the jaw tip
        tip = jaw_skel[-1]
        for yi in range(3):
            y_pos = lerp(-0.03, 0.03, yi / 2.0)
            bpy.ops.mesh.primitive_cube_add(size=incisor_size * 3)
            tooth = bpy.context.active_object
            add_subsurf(tooth, 2)
            tooth.scale = (1.0, 0.3, 0.6)
            tooth.location = mathutils.Vector(tuple(tip + np.array([0.01, y_pos, -0.005])))
            tooth.rotation_euler.y = -math.pi / 2
            apply_tf(tooth)
            parts.append(tooth)

    # Tongue -- simplified as a flattened elongated sphere
    tongue_shaping = float(params.get("Tongue Shaping", 1.0))
    tongue_x_scale = float(params.get("Tongue X Scale", 0.9))
    if tongue_shaping > 0.1:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12,
                                             radius=rad1 * 0.7)
        tongue = bpy.context.active_object
        tongue.scale = (tongue_x_scale * length * 1.5, rad1 * 8, 0.3)
        tongue.location = mathutils.Vector(tuple(jaw_skel[len(jaw_skel) // 2]))
        tongue.location.z += 0.01
        apply_tf(tongue)
        add_subsurf(tongue, 1)
        tongue.name = "Tongue"
        parts.append(tongue)

    result = join_objs(parts)
    result.name = "jaw"
    return result, jaw_skel

def create_cat_ear(params):
    """Build a cat ear from polar bezier + bell-curve radius + solidified CurveToMesh."""

    lrr = params.get("length_rad1_rad2", np.array([0.25, 0.1, 0.0]))
    depth = float(params.get("Depth", 0.06))
    thickness = float(params.get("Thickness", 0.01))
    curl_deg = float(params.get("Curl Deg", 49.0))

    length = float(lrr[0])
    width = float(lrr[1])
    seg_l = length / 3.0

    # Polar bezier skeleton
    curl_angles = np.array([-curl_deg, curl_deg, curl_deg])
    skel = polar_bezier_skeleton(curl_angles, [seg_l, seg_l, seg_l], n_pts=20,
                                origin=np.array([-0.07, 0, 0]), do_bezier=True)

    # Bell-curve radius profile: [(0,0), (0.324,0.98), (0.746,0.63), (1,0)]
    t_arr = np.linspace(0, 1, 20)
    # Piecewise linear approximation of the float curve
    radius_profile = np.interp(t_arr, [0, 0.324, 0.746, 1.0], [0, 0.98, 0.63, 0])
    radii = radius_profile * width

    # Build tube with CurveToMesh
    ear = build_curve_tube(skel, radii, n_profile=16, aspect=depth / max(width, 0.01),
                           fill_caps=False, name="ear")

    # Solidify
    mod = ear.modifiers.new("Solid", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 0
    sel(ear)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Merge by distance
    sel(ear)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.005)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Subdivide
    add_subsurf(ear, 1)
    shade_smooth(ear)

    return ear

def create_cat_nose(params):
    """Build a cat nose: subdivided cube with nostril boolean cutouts."""

    nose_radius = float(params.get("Nose Radius", 0.077))
    nostril_size = float(params.get("Nostril Size", 0.021))
    crease = float(params.get("Crease", 0.237))

    # Subdivided cube
    bpy.ops.mesh.primitive_cube_add(size=nose_radius)
    nose = bpy.context.active_object
    # Edge crease for all edges
    sel(nose)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.transform.edge_crease(value=crease)
    bpy.ops.object.mode_set(mode="OBJECT")
    add_subsurf(nose, 4)
    nose.scale = (1.2, 1.0, 1.0)
    apply_tf(nose)

    # Nostrils -- two UV spheres, boolean difference
    for side in [1, -1]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6,
                                             radius=nostril_size)
        nostril = bpy.context.active_object
        nostril.location = (0.04, side * 0.025, 0.015)
        nostril.rotation_euler = (0.5643, 0, 0)
        nostril.scale = (1.0, 0.87, 0.31)
        apply_tf(nostril)
        nose = add_boolean_diff(nose, nostril)

    nose.name = "Nose"
    return nose

def create_eye_sphere(radius=0.03):
    """Create an eyeball UV sphere with eyeball material."""

    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=radius)
    eye = bpy.context.active_object
    eye.scale = (1.0, 1.0, 0.7)
    apply_tf(eye)
    shade_smooth(eye)
    eye.name = "Eyeball"
    eye.data.materials.append(EYEBALL_MAT)
    return eye

# PARAMETER SAMPLING

def sample_back_leg_params(override_lrr=None):
    params = {
        "length_rad1_rad2": np.array((1.8, 0.1, 0.05)) * N(1, (0.2, 0, 0), 3),
        "angles_deg": np.array((40.0, -120.0, 100)),
        "fullness": 50.0,
        "aspect": 1.0,
        "Thigh Rad1 Rad2 Fullness": np.array((0.33, 0.15, 2.5)) * N(1, 0.1, 3),
        "Calf Rad1 Rad2 Fullness": np.array((0.17, 0.07, 2.5)) * N(1, 0.1, 3),
        "Thigh Height Tilt1 Tilt2": np.array((0.6, 0.0, 0.0)) + N(0, [0.05, 2, 10]),
        "Calf Height Tilt1 Tilt2": np.array((0.8, 0.0, 0.0)) + N(0, [0.05, 10, 10]),
    }
    if override_lrr is not None:
        params["length_rad1_rad2"] = override_lrr
    return params

def sample_front_leg_params(override_lrr=None):
    params = {
        "length_rad1_rad2": np.array((1.43, 0.1, 0.1)) * N(1, (0.2, 0, 0), 3),
        "angles_deg": np.array((-40.0, 120.0, -100)),
        "aspect": 1.0,
        "Shoulder Rad1 Rad2 Fullness": np.array((0.22, 0.22, 2.5)) * N(1, 0.1, 3),
        "Calf Rad1 Rad2 Fullness": np.array((0.08, 0.08, 2.5)) * N(1, 0.1, 3),
        "Elbow Rad1 Rad2 Fullness": np.array((0.12, 0.1, 2.5)) * N(1, 0.1, 3),
        "Shoulder Height, Tilt1, Tilt2": np.array((0.74, 0.0, 0.0)) + N(0, [0.05, 10, 10]),
        "Elbow Height, Tilt1, Tilt2": np.array((0.9, 0.0, 0.0)) + N(0, [0.05, 10, 10]),
        "Calf Height, Tilt1, Tilt2": np.array((0.74, 0.0, 0.0)) + N(0, [0.05, 10, 10]),
    }
    if override_lrr is not None:
        params["length_rad1_rad2"] = override_lrr
    return params

def sample_foot_params():
    return {
        "length_rad1_rad2": np.array((0.27, 0.04, 0.09)) * N(1, (0.2, 0.05, 0.05), 3),
        "Num Toes": max(int(N(4, 1)), 2),
        "Toe Length Rad1 Rad2": np.array((0.3, 0.045, 0.025)) * N(1, 0.1, 3),
        "Toe Rotate": (0.0, -N(0.7, 0.15), 0.0),
        "Toe Splay": 20.0 * N(1, 0.2),
        "Toebean Radius": 0.03 * N(1, 0.2),
        "Claw Curl Deg": 30 * N(1, 0.4),
        "Claw Pct Length Rad1 Rad2": np.array((0.3, 0.5, 0.0)) * N(1, 0.1, 3),
    }

def sample_tail_params():
    return {
        "length_rad1_rad2": (N(0.5, 0.1), 0.08, 0.04),
        "angles_deg": np.array((31.39, 65.81, -106.93)) * N(1, 0.1),
        "aspect": N(1, 0.05),
    }

def sample_carnivore_head_params(override_lrr=None):
    if override_lrr is not None:
        lrr = override_lrr
    else:
        lrr = np.array((0.36, 0.20, 0.18)) * N(1, 0.2, 3)

    params = {
        "length_rad1_rad2": lrr,
        "snout_length_rad1_rad2": np.array((0.22, 0.15, 0.15)) * N(1, 0.2, 3),
        "aspect": N(1, 0.2),
    }

    muscle_params = {
        "Nose Bridge Scale": (1.0, 0.35, 0.9),
        "Jaw Muscle Middle Coord": (0.24, 0.41, 1.3),
        "Jaw StartRad, EndRad, Fullness": (0.06, 0.11, 1.5),
        "Jaw ProfileHeight, StartTilt, EndTilt": (0.8, 33.1, 0.0),
        "Lip Muscle Middle Coord": (0.95, 0.0, 1.5),
        "Lip StartRad, EndRad, Fullness": (0.05, 0.09, 1.48),
        "Lip ProfileHeight, StartTilt, EndTilt": (0.8, 0.0, -17.2),
        "Forehead Muscle Middle Coord": (0.7, -1.32, 1.31),
        "Forehead StartRad, EndRad, Fullness": (0.06, 0.05, 2.5),
        "Forehead ProfileHeight, StartTilt, EndTilt": (0.3, 60.6, 66.0),
    }

    for k, v in muscle_params.items():
        v = np.array(v)
        v *= N(1, 0.05, len(v))
        params[k] = v

    params["EyeRad"] = 0.023 * N(1, 0.3)
    params["EyeOffset"] = np.array((-0.25, 0.45, 0.3)) + N(0, (0, 0.02, 0.03))
    return params

def sample_jaw_params(override_lrr=None):
    params = {
        "length_rad1_rad2": np.array((0.4, 0.12, 0.08)) * N(1, 0.1, 3),
        "Width Shaping": 1.0 * clip_gaussian(1, 0.1, 0.5, 1),
        "Canine Length": 0.05 * N(1, 0.2),
        "Incisor Size": 0.01 * N(1, 0.2),
        "Tooth Crookedness": 1.2 * N(1, 0.3),
        "Tongue Shaping": 1.0 * clip_gaussian(1, 0.1, 0.5, 1),
        "Tongue X Scale": 0.9 * clip_gaussian(1, 0.1, 0.5, 1),
    }
    if override_lrr is not None:
        params["length_rad1_rad2"] = override_lrr
    return params

def sample_cat_ear_params():
    _size = clip_gaussian(1, 0.1, 0.2, 5)
    return {
        "length_rad1_rad2": np.array((0.25, 0.1, 0.0)) * N(1, (0.1, 0.05, 0.05)),
        "Depth": 0.06 * N(1, 0.1),
        "Thickness": 0.01,
        "Curl Deg": 49.0 * N(1, 0.2),
    }

def sample_cat_nose_params():
    size_mult = N(0.7, 0.05)
    return {
        "Nose Radius": 0.11 * size_mult,
        "Nostril Size": 0.03 * size_mult * N(1, 0.1),
        "Crease": 0.237 * N(1, 0.1),
    }

# MAIN ASSEMBLY -- matches tiger_genome() random call sequence

def build_carnivore():
    np.random.seed(int_hash((SEED, 0)))
    clear_scene()

    # ═══ 1. Body NURBS ════════════════════════════════════════════════════════
    body_params = sample_nurbs_params("body_feline", temperature=0.2, var=0.7)
    body_params["thetas"][-3] *= N(1, 0.1)

    # ═══ 2. Tail params ═══════════════════════════════════════════════════════
    tail_params = sample_tail_params()
    tail_joint_y = N(0, 10)  # Joint rest Y for tail

    # ═══ 3. Head path choice ══════════════════════════════════════════════════
    use_tube_head = U() < 0.5

    if use_tube_head:
        head_lrr = np.array((0.36, 0.20, 0.18)) * N(1, 0.1, 3)
        # Clamp head to minimum size to prevent boolean failures
        head_lrr[0] = max(head_lrr[0], 0.32)  # min length
        head_lrr[1] = max(head_lrr[1], 0.17)  # min rad1
        head_lrr[2] = max(head_lrr[2], 0.15)  # min rad2
        head_params = sample_carnivore_head_params(override_lrr=head_lrr)
        jaw_pct = np.array((1.05, 0.55, 0.5))
        jaw_params = sample_jaw_params(override_lrr=head_lrr * jaw_pct)
        jaw_coord = (0.2 * N(1, 0.1), 0, 0.35 * N(1, 0.1))
        jaw_joint_y = U(10, 35)
    else:
        head_params_nurbs = sample_nurbs_params("head_carnivore", temperature=0.3, var=0.5)
        headl = float(np.asarray(head_params_nurbs["length"]).flat[0])
        head_lrr = np.array((headl, 0.20, 0.18)) * N(1, 0.1, 3)
        jaw_pct = np.array((0.7, 0.55, 0.5))
        jaw_params = sample_jaw_params(override_lrr=head_lrr * jaw_pct)
        jaw_coord = (0.12, 0, 0.3 * N(1, 0.1))
        jaw_joint_y = U(10, 35)
        # Eye params for NURBS head
        eye_radius = N(0.027, 0.009)
        eye_t = U(0.61, 0.64)
        eye_splay = U(90, 140) / 180
        eye_r = U(0.8, 0.9)

    # ═══ 4. Nose, Ears ════════════════════════════════════════════════════════
    nose_params = sample_cat_nose_params()
    ear_params = sample_cat_ear_params()  # shared for both ears
    ear_t = N(0.33, 0.07)
    ear_splay = U(100, 150) / 180
    ear_rot = np.array([-20, -10, -23]) + N(0, 4, 3)

    # ═══ 5. Legs ══════════════════════════════════════════════════════════════
    splay = clip_gaussian(130, 7, 90, 130) / 180
    shoulder_t = clip_gaussian(0.12, 0.05, 0.08, 0.12)
    leg_lrr = np.array((1.6, 0.1, 0.05)) * N(1, (0.15, 0.05, 0.05), 3)
    foot_params = sample_foot_params()
    back_leg_params = sample_back_leg_params(override_lrr=leg_lrr.copy())
    front_leg_params = sample_front_leg_params(override_lrr=leg_lrr.copy())

    # ═══ 6. Head attachment ═══════════════════════════════════════════════════
    head_coord_t = N(0.97, 0.01)
    head_joint_y = N(20, 5)
    neck_t = 0.7

    # ═══ BUILD GEOMETRY ══════════════════════════════════════════════════════

    # -- Body --
    body_skeleton = get_skeleton_from_params(body_params)[1:-1]
    body_obj = build_nurbs_mesh(body_params, name="body", subsurf_levels=3)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_bvh = BVHTree.FromObject(body_obj, depsgraph)

    all_parts = [body_obj]

    # -- Tail --
    tail_obj, tail_skel = create_tail(tail_params)
    tail_loc, _ = raycast_attach(body_skeleton, body_bvh, (0.07, 1, 1))
    tail_obj.matrix_world = build_world_matrix(
        euler_quat(tail_joint_y, 180, 0), tail_loc)
    apply_tf(tail_obj)
    all_parts.append(tail_obj)

    # -- Head --
    if use_tube_head:
        head_obj, head_skel, head_eyeballs = create_carnivore_head(head_params)
    else:
        head_obj = build_nurbs_mesh(head_params_nurbs, name="head", subsurf_levels=2)
        head_skel = get_skeleton_from_params(head_params_nurbs)[1:-1]
        head_eyeballs = []

    # Scale factor for head details (ears/nose/jaw) relative to nominal head length 0.36
    head_detail_scale = float(head_lrr[0]) / 0.36
    head_detail_scale = max(0.5, min(head_detail_scale, 1.5))  # clamp to sane range

    # Build head BVH before attaching parts to it
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    head_bvh = BVHTree.FromObject(head_obj, depsgraph)

    # -- Jaw --
    jaw_obj, jaw_skel = create_carnivore_jaw(jaw_params)
    jaw_loc, _ = raycast_attach(head_skel, head_bvh, jaw_coord)
    jaw_obj.matrix_world = build_world_matrix(euler_quat(0, jaw_joint_y, 0), jaw_loc)
    apply_tf(jaw_obj)

    # -- Nose --
    nose_obj = create_cat_nose(nose_params)
    nose_u = U(0.9, 0.96)
    nose_r = U(0.5, 0.7)
    nose_loc, _ = raycast_attach(head_skel, head_bvh, (nose_u, 1, nose_r))
    nose_obj.matrix_world = build_world_matrix(euler_quat(0, 20, 0), nose_loc)
    apply_tf(nose_obj)
    # Scale nose relative to head size
    if head_detail_scale < 0.9:
        nose_obj.scale = (head_detail_scale,) * 3
        apply_tf(nose_obj)

    # -- Ears --
    ears = []
    # Embed ears slightly into head surface (0.85 instead of 1.0) to prevent gaps
    ear_r_factor = 0.85
    for side in [-1, 1]:
        ear = create_cat_ear(ear_params)
        # Scale ear relative to head size to prevent oversized ears on small heads
        if head_detail_scale < 0.9:
            ear.scale = (head_detail_scale,) * 3
            apply_tf(ear)
        ear_loc, _ = raycast_attach(head_skel, head_bvh,
                                    (ear_t, ear_splay, ear_r_factor))
        ear.matrix_world = build_world_matrix(euler_quat(*ear_rot.tolist()), ear_loc)
        if side == -1:
            ear.matrix_world = MIRROR_Y @ ear.matrix_world
        apply_tf(ear)
        ears.append(ear)

    # -- Eyes (NURBS head path) --
    nurbs_eyes = []
    if not use_tube_head:
        for side in [-1, 1]:
            eye = create_eye_sphere(radius=abs(eye_radius))
            eye_loc, _ = raycast_attach(head_skel, head_bvh,
                                        (eye_t, eye_splay * side, eye_r))
            eye.location = mathutils.Vector(tuple(eye_loc))
            apply_tf(eye)
            nurbs_eyes.append(eye)

    # Assemble head parts
    head_all = [head_obj, jaw_obj, nose_obj] + ears + head_eyeballs + nurbs_eyes
    head_assembled = join_objs(head_all)
    head_assembled.name = "head_assembly"

    # Scale head proportional to body if body is unusually large
    body_verts = np.array([v.co[:] for v in body_obj.data.vertices])
    body_y_extent = body_verts[:, 1].max() - body_verts[:, 1].min()
    # Nominal body Y extent is ~0.55-0.60. Scale head only if body is significantly larger
    nominal_body_y = 0.58
    body_scale_factor = max(1.0, body_y_extent / nominal_body_y)
    body_scale_factor = min(body_scale_factor, 1.4)  # cap at 1.4x
    if body_scale_factor > 1.05:
        head_assembled.scale = (body_scale_factor,) * 3
        apply_tf(head_assembled)

    # Attach head to body
    head_loc, _ = raycast_attach(body_skeleton, body_bvh, (head_coord_t, 0, 0))
    head_assembled.matrix_world = build_world_matrix(
        euler_quat(0, head_joint_y, 0), head_loc)
    apply_tf(head_assembled)

    # Extract eye world positions from the assembled+positioned head for post-remesh lookup.
    # Eye vertices have EYEBALL_MAT assigned; find their centers.
    _eye_centers_world = []
    _eye_radius_world = 0.025
    _eye_mat_idx = None
    for i, m in enumerate(head_assembled.data.materials):
        if m and m.name == EYEBALL_MAT.name:
            _eye_mat_idx = i
            break
    if _eye_mat_idx is not None:
        eye_verts_co = []
        eye_face_verts = set()
        for poly in head_assembled.data.polygons:
            if poly.material_index == _eye_mat_idx:
                for vi in poly.vertices:
                    eye_face_verts.add(vi)
        if eye_face_verts:
            coords = np.array([head_assembled.data.vertices[vi].co[:] for vi in eye_face_verts])
            # Cluster into left/right eyes by Y sign
            left_mask = coords[:, 1] < 0
            right_mask = coords[:, 1] >= 0
            for mask in [left_mask, right_mask]:
                if mask.any():
                    center = coords[mask].mean(axis=0)
                    _eye_centers_world.append(center)
                    _eye_radius_world = max(_eye_radius_world,
                                            np.linalg.norm(coords[mask] - center, axis=1).max())

    all_parts.append(head_assembled)

    # -- Back legs + feet --
    for side in [-1, 1]:
        leg_obj, leg_skel = create_back_leg(back_leg_params)
        foot_obj, foot_skel = create_foot(foot_params)

        # Foot attaches at 90% along leg (coord=(0.9, 0, 0) in original)
        # so the foot overlaps with the last 10% of the leg tube,
        # creating a smooth junction via voxel remesh.
        foot_idx = int(0.9 * (len(leg_skel) - 1))
        foot_pos = leg_skel[foot_idx]
        foot_obj.location = mathutils.Vector(tuple(foot_pos))
        apply_tf(foot_obj)

        # Join leg + foot
        leg_with_foot = join_objs([leg_obj, foot_obj])
        leg_with_foot.name = f"back_leg_{side}"

        # Attach to body
        attach_pt, _ = raycast_attach(body_skeleton, body_bvh,
                                      (shoulder_t, splay, 1.2))
        M = build_world_matrix(euler_quat(0, 90, 0), attach_pt)
        if side == -1:
            M = MIRROR_Y @ M
        leg_with_foot.matrix_world = M
        apply_tf(leg_with_foot)
        all_parts.append(leg_with_foot)

    # -- Front legs + feet --
    for side in [-1, 1]:
        leg_obj, leg_skel = create_front_leg(front_leg_params)
        foot_obj, foot_skel = create_foot(foot_params)

        # Foot at 90% along leg (same coord=(0.9, 0, 0))
        foot_idx = int(0.9 * (len(leg_skel) - 1))
        foot_pos = leg_skel[foot_idx]
        foot_obj.location = mathutils.Vector(tuple(foot_pos))
        apply_tf(foot_obj)

        leg_with_foot = join_objs([leg_obj, foot_obj])
        leg_with_foot.name = f"front_leg_{side}"

        attach_pt, _ = raycast_attach(body_skeleton, body_bvh,
                                      (neck_t - shoulder_t, splay, 0.8))
        M = build_world_matrix(euler_quat(0, 90, 0), attach_pt)
        if side == -1:
            M = MIRROR_Y @ M
        leg_with_foot.matrix_world = M
        apply_tf(leg_with_foot)
        all_parts.append(leg_with_foot)

    # ═══ JOIN & POST-PROCESS ══════════════════════════════════════════════════

    carnivore = join_objs(all_parts)
    carnivore.name = "CarnivoreFactory"

    # Remove doubles -- threshold=0.01 matches original joining.py:160
    sel(carnivore)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.01)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Triangulate via bmesh
    bm = bmesh.new()
    bm.from_mesh(carnivore.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(carnivore.data)
    bm.free()

    # Subdivision surface (matches original joining.py:199)
    add_subsurf(carnivore, 1)

    # Voxel remesh -- voxel_size=0.01 matches original
    # (joining.py:124 min_remesh_size=0.01, detail.py:94)
    mod = carnivore.modifiers.new("Remesh", "REMESH")
    mod.mode = 'VOXEL'
    mod.voxel_size = 0.01
    sel(carnivore)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Corrective smooth to blend muscle/body junctions
    # (approximates the smooth_joins effect from joining.py)
    mod = carnivore.modifiers.new("Smooth", "CORRECTIVE_SMOOTH")
    mod.factor = 0.5
    mod.iterations = 3
    mod.use_only_smooth = True
    sel(carnivore)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    shade_smooth(carnivore)

    # Ground the model
    verts = np.array([v.co for v in carnivore.data.vertices])
    if len(verts) > 0:
        z_offset = -verts[:, 2].min()
        carnivore.location.z = z_offset
        apply_tf(carnivore)
        # Apply same offset to stored eye centers
        for i in range(len(_eye_centers_world)):
            _eye_centers_world[i] = _eye_centers_world[i] + np.array([0, 0, z_offset])

    return carnivore, _eye_centers_world, _eye_radius_world

_build_result = build_carnivore()
carnivore = _build_result[0] if _build_result else None
_eye_centers = _build_result[1] if _build_result else []
_eye_radius = _build_result[2] if _build_result else 0.025

if carnivore is not None:
    # Assign materials
    carnivore.data.materials.clear()
    carnivore.data.materials.append(CREATURE_MAT)    # slot 0: body
    carnivore.data.materials.append(TONGUE_MAT)      # slot 1: tongue
    carnivore.data.materials.append(BONE_MAT)        # slot 2: bone/teeth
    carnivore.data.materials.append(NOSE_MAT)        # slot 3: nose
    carnivore.data.materials.append(EYEBALL_MAT)     # slot 4: eyeball

    # After voxel remesh, identify eye faces spatially using stored eye centers.
    # Faces whose center is within eye_radius of a known eye center get eyeball material.
    if _eye_centers:
        eye_centers_arr = np.array(_eye_centers)
        search_radius = _eye_radius * 1.2  # slight margin
        for poly in carnivore.data.polygons:
            fc = np.array(poly.center[:])
            dists = np.linalg.norm(eye_centers_arr - fc, axis=1)
            if dists.min() < search_radius:
                poly.material_index = 4
            else:
                poly.material_index = 0
    else:
        # No eye centers found; all faces get body material
        for poly in carnivore.data.polygons:
            poly.material_index = 0
