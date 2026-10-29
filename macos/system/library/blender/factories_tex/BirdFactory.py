# [FL_INDEX: keywords="blender_factory, procedural_3d, BirdFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BirdFactory | Category: factories_tex
# Prompt: A perching bird rendered as a textured 3D model. The creature stands upright on two orange-red feet with clawed toes, showing a plump rounded body covered in a dense feather texture. The plumage is a mix of dark charcoal gray and black on the wings and back, transitioning to lighter pale gray on the chest and head. The head has a small black eye and a short, slightly curved salmon-pink beak. White feather highlights are scattered across the dark wing surface. The natural resting pose with folded wings gives it the appearance of a small gull or shore bird.

import os
import math
from dataclasses import dataclass
from math import cos, exp, pi, sin

import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree
from numpy.random import normal as N

DEFAULT_SEED = int(os.environ.get("SEED", "0"))
SEED = DEFAULT_SEED
# SEED-deterministic: all random calls seeded from SEED (np.random.seed(seed) in build_bird)

# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
import random as _random, colorsys as _colorsys


def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h) % 1.0, max(0, min(1, float(s))), max(0, min(1, float(v))))
    return (r, g, b, 1.0)

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac(n):
    """Get Fac/Factor output, compatible across Blender 4.x/5.x."""

    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def _sample_range(lo, hi):
    return float(np.random.uniform(lo, hi))

def _sample_color_keep_sum(color_elem, offset=None):
    c = list(color_elem)
    s = c[0] + c[1] + c[2]
    for i in range(3):
        if offset is not None:
            c[i] = max(0.0, c[i] + _sample_range(-offset, offset))
        else:
            c[i] = max(0.0, _sample_range(0, s))
    # renormalize to keep sum
    ns = c[0] + c[1] + c[2]
    if ns > 1e-9:
        ratio = s / ns
        for i in range(3):
            c[i] *= ratio
    for i in range(4):
        color_elem[i] = c[i] if i < 3 else 1.0


def _spec_key(bsdf):
    return "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"


#    the standalone geometry does not write).  The original shader layers
#    colours driven by tag_body, tag_leg, tag_wing, tag_foot, tag_tail,
#    tag_head.  Without those attributes the mix factors are all 0, which
#    collapses the chain to the foot layer (mix_3 base = black, then mix_8
#    passes through, then mix_7 passes through = black).  To keep visual
#    richness we reproduce the *body-colour branch* (two noise+linear
#    gradients mixed) which is the dominant visible colour on the body mesh.

def make_body_material(seed, name="BirdBody_Material"):
    """Bird body shader: two linear-gradient-mixed noise patterns.
    Matches shader_bird_body topology (noise + nodegroup_l_inear + colorramp)
    with Specular IOR Level=0, IOR=0, Roughness=1."""


    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    tc = nt.nodes.new("ShaderNodeTexCoord")

    # --- Noise distortion (shared pattern) ---------------------------------
    noise_dist = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Generated"], noise_dist.inputs["Vector"])

    # Mix Generated with noise for slight distortion (Fac=0.2)
    mix_dist = nt.nodes.new("ShaderNodeMix")
    mix_dist.data_type = "RGBA"
    mix_dist.inputs[0].default_value = 0.2  # Factor
    ln(tc.outputs["Generated"], mix_dist.inputs[6])  # A (Color)
    ln(noise_dist.outputs["Color"], mix_dist.inputs[7])  # B (Color)

    # --- nodegroup_l_inear equivalent: CoffX*X + CoffZ*Z -------------------
    sep1 = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(mix_dist.outputs[2], sep1.inputs["Vector"])

    coffx1 = _sample_range(0, 0.08)
    coffz1 = 1.1 - coffx1

    mul_x1 = nt.nodes.new("ShaderNodeMath"); mul_x1.operation = "MULTIPLY"
    mul_x1.inputs[1].default_value = coffx1
    ln(sep1.outputs["X"], mul_x1.inputs[0])

    mul_z1 = nt.nodes.new("ShaderNodeMath"); mul_z1.operation = "MULTIPLY"
    mul_z1.inputs[1].default_value = coffz1
    ln(sep1.outputs["Z"], mul_z1.inputs[0])

    add1 = nt.nodes.new("ShaderNodeMath"); add1.operation = "ADD"
    ln(mul_x1.outputs[0], add1.inputs[0])
    ln(mul_z1.outputs[0], add1.inputs[1])

    # offset
    add1b = nt.nodes.new("ShaderNodeMath"); add1b.operation = "ADD"
    add1b.inputs[1].default_value = _sample_range(-0.07, 0.03)
    ln(add1.outputs[0], add1b.inputs[0])

    # colorramp -> body stripe pattern
    cr_stripe = nt.nodes.new("ShaderNodeValToRGB")
    cr_stripe.color_ramp.elements[0].position = 0.6295
    cr_stripe.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    cr_stripe.color_ramp.elements[1].position = 0.7068
    cr_stripe.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    ln(add1b.outputs[0], cr_stripe.inputs["Fac"])

    # --- Noise color A (fine body speckle) ---------------------------------
    noise_a = nt.nodes.new("ShaderNodeTexNoise")
    noise_a.inputs["Scale"].default_value = 20.0
    cr_a = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(noise_a), cr_a.inputs["Fac"])
    # Default dark body tones
    cr_a.color_ramp.elements[0].position = 0.3341
    cr_a.color_ramp.elements[0].color = (0.0079, 0.0062, 0.0063, 1.0)
    cr_a.color_ramp.elements[1].position = 0.9932
    cr_a.color_ramp.elements[1].color = (0.0302, 0.0264, 0.0262, 1.0)
    # randomize
    for i in range(3):
        cr_a.color_ramp.elements[0].color[i] = _sample_range(0, 0.2)
        cr_a.color_ramp.elements[1].color[i] = _sample_range(0, 0.2)

    # --- Noise color B (broad variation) -----------------------------------
    noise_b = nt.nodes.new("ShaderNodeTexNoise")
    noise_b.noise_dimensions = "4D"
    noise_b.inputs["Scale"].default_value = 10.0
    noise_b.inputs["W"].default_value = _sample_range(-2, 2)
    x = _random.random()
    if x < 0.3:
        noise_b.inputs["Scale"].default_value = 1
    elif x > 0.7:
        noise_b.inputs["Scale"].default_value = 50

    cr_b = nt.nodes.new("ShaderNodeValToRGB")
    ln(noise_b.outputs["Color"], cr_b.inputs["Fac"])
    cr_b.color_ramp.elements[0].position = 0.4614
    cr_b.color_ramp.elements[0].color = (0.1, 0.1, 0.1, 1.0)
    cr_b.color_ramp.elements[1].position = 1.0
    cr_b.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    mix_ab = nt.nodes.new("ShaderNodeMix")
    mix_ab.data_type = "RGBA"
    ln(cr_stripe.outputs["Color"], mix_ab.inputs[0])
    ln(cr_a.outputs["Color"], mix_ab.inputs[6])
    ln(cr_b.outputs["Color"], mix_ab.inputs[7])

    # --- Second linear gradient for belly/breast colour --------------------
    noise_dist2 = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Generated"], noise_dist2.inputs["Vector"])

    mix_dist2 = nt.nodes.new("ShaderNodeMix")
    mix_dist2.data_type = "RGBA"
    mix_dist2.inputs[0].default_value = 0.2
    ln(tc.outputs["Generated"], mix_dist2.inputs[6])
    ln(noise_dist2.outputs["Color"], mix_dist2.inputs[7])

    sep2 = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(mix_dist2.outputs[2], sep2.inputs["Vector"])

    coffx2 = _sample_range(-0.1, 0.8) if _random.random() > 0.5 else _sample_range(-0.1, 0.1)

    mul_x2 = nt.nodes.new("ShaderNodeMath"); mul_x2.operation = "MULTIPLY"
    mul_x2.inputs[1].default_value = coffx2
    ln(sep2.outputs["X"], mul_x2.inputs[0])

    mul_z2 = nt.nodes.new("ShaderNodeMath"); mul_z2.operation = "MULTIPLY"
    mul_z2.inputs[1].default_value = 1.0
    ln(sep2.outputs["Z"], mul_z2.inputs[0])

    add2 = nt.nodes.new("ShaderNodeMath"); add2.operation = "ADD"
    ln(mul_x2.outputs[0], add2.inputs[0])
    ln(mul_z2.outputs[0], add2.inputs[1])

    add2b = nt.nodes.new("ShaderNodeMath"); add2b.operation = "ADD"
    add2b.inputs[1].default_value = 0.1
    ln(add2.outputs[0], add2b.inputs[0])

    cr_belly = nt.nodes.new("ShaderNodeValToRGB")
    cr_belly.color_ramp.elements[0].position = 0.4159
    cr_belly.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    cr_belly.color_ramp.elements[1].position = 0.6886
    cr_belly.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    ln(add2b.outputs[0], cr_belly.inputs["Fac"])

    # Belly colour noise
    noise_belly = nt.nodes.new("ShaderNodeTexNoise")
    noise_belly.noise_dimensions = "4D"
    noise_belly.inputs["Scale"].default_value = 20.0
    noise_belly.inputs["W"].default_value = _sample_range(-2, 2)

    cr_belly_col = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(noise_belly), cr_belly_col.inputs["Fac"])
    cr_belly_col.color_ramp.elements[0].position = 0.4636
    cr_belly_col.color_ramp.elements[0].color = (0.0112, 0.0053, 0.0047, 1.0)
    cr_belly_col.color_ramp.elements[1].position = 1.0
    cr_belly_col.color_ramp.elements[1].color = (0.0231, 0.0128, 0.0121, 1.0)
    _sample_color_keep_sum(cr_belly_col.color_ramp.elements[0].color)
    _sample_color_keep_sum(cr_belly_col.color_ramp.elements[1].color)

    mix_belly = nt.nodes.new("ShaderNodeMix")
    mix_belly.data_type = "RGBA"
    ln(cr_belly.outputs["Color"], mix_belly.inputs[0])
    ln(cr_belly_col.outputs["Color"], mix_belly.inputs[6])
    ln(mix_ab.outputs[2], mix_belly.inputs[7])

    # --- Head/neck region: noise distortion + Z-based threshold ------------
    # nodegroup_head_neck: adds green-dark head coloring in upper Z region
    noise_head = nt.nodes.new("ShaderNodeTexNoise")
    noise_head.noise_dimensions = "4D"
    noise_head.inputs["Scale"].default_value = 2.0
    noise_head.inputs["W"].default_value = _sample_range(-2, 2)
    ln(tc.outputs["Generated"], noise_head.inputs["Vector"])

    sub_head = nt.nodes.new("ShaderNodeVectorMath"); sub_head.operation = "SUBTRACT"
    sub_head.inputs[1].default_value = (0.0, 0.0, 0.0)
    ln(_fac(noise_head), sub_head.inputs[0])

    mix_head_dist = nt.nodes.new("ShaderNodeMix")
    mix_head_dist.data_type = "RGBA"
    mix_head_dist.inputs[0].default_value = 0.2
    ln(tc.outputs["Generated"], mix_head_dist.inputs[6])
    ln(sub_head.outputs["Vector"], mix_head_dist.inputs[7])

    sep_head = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(mix_head_dist.outputs[2], sep_head.inputs["Vector"])

    add_head = nt.nodes.new("ShaderNodeMath"); add_head.operation = "ADD"
    add_head.inputs[1].default_value = 0.05
    ln(sep_head.outputs["Z"], add_head.inputs[0])

    # CR threshold: sharp band at Z~0.83 (head region)
    cr_head_band = nt.nodes.new("ShaderNodeValToRGB")
    cr_head_band.color_ramp.elements[0].position = 0.83
    cr_head_band.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_head_band.color_ramp.elements[1].position = 0.84
    cr_head_band.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    ln(add_head.outputs[0], cr_head_band.inputs["Fac"])

    # Head color: dark green-tinted
    noise_head_col = nt.nodes.new("ShaderNodeTexNoise")
    noise_head_col.noise_dimensions = "4D"
    noise_head_col.inputs["W"].default_value = 1.7
    noise_head_col.inputs["Scale"].default_value = 3.0
    cr_head_col = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(noise_head_col), cr_head_col.inputs["Fac"])
    cr_head_col.color_ramp.elements[0].position = 0.5077
    cr_head_col.color_ramp.elements[0].color = (0.0063, 0.017, 0.005, 1.0)
    cr_head_col.color_ramp.elements[1].position = 1.0
    cr_head_col.color_ramp.elements[1].color = (0.0018, 0.0571, 0.0, 1.0)
    _sample_color_keep_sum(cr_head_col.color_ramp.elements[0].color)
    for i in range(3):
        cr_head_col.color_ramp.elements[1].color[i] = (
            cr_head_col.color_ramp.elements[0].color[i] + 0.005)

    # Mix head color onto body
    mix_head = nt.nodes.new("ShaderNodeMix")
    mix_head.data_type = "RGBA"
    ln(cr_head_band.outputs["Color"], mix_head.inputs[0])
    ln(mix_belly.outputs[2], mix_head.inputs[6])
    ln(cr_head_col.outputs["Color"], mix_head.inputs[7])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_head.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs[_spec_key(bsdf)].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 1.0
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = 0.0

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_feather_material(seed, name="BirdFeather_Material", tail=False):
    """Bird feather shader: noise(4D) + wave texture.
    Matches shader_bird_feather topology: Specular=0, Roughness=1."""


    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    # Noise colour base
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["W"].default_value = _sample_range(-2, 2)

    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.377
    cr.color_ramp.elements[0].color = (0.02, 0.02, 0.02, 1.0)
    cr.color_ramp.elements[1].position = 1.0
    x = _sample_range(0.02, 0.15)
    cr.color_ramp.elements[1].color = (x, x, x, 1.0)

    # Wave texture for feather barb pattern
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    ln(tc.outputs["Object"], mapping.inputs["Vector"])

    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 5.0
    wave.inputs["Distortion"].default_value = 10.0
    wave.inputs["Detail"].default_value = 10.0
    wave.inputs["Detail Roughness"].default_value = 2.0
    ln(mapping.outputs["Vector"], wave.inputs["Vector"])

    cr_wave = nt.nodes.new("ShaderNodeValToRGB")
    ln(wave.outputs["Color"], cr_wave.inputs["Fac"])
    cr_wave.color_ramp.elements[0].position = 0.0955
    cr_wave.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_wave.color_ramp.elements[1].position = 0.6364
    cr_wave.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Mix wave and noise colour (Fac=0.5 for tail, 1.0 otherwise)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.5 if tail else 1.0
    ln(cr_wave.outputs["Color"], mix.inputs[6])
    ln(cr.outputs["Color"], mix.inputs[7])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs[_spec_key(bsdf)].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 1.0

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_beak_material(seed, name="BirdBeak_Material"):
    """Bird beak shader: noise(4D,Scale=20) + EASE colorramp with yellow-green.
    Matches shader_bird_beak: Roughness=0.3408."""


    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["W"].default_value = _sample_range(-2, 2)
    noise.inputs["Scale"].default_value = 20.0
    noise.inputs["Roughness"].default_value = 0.5142

    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "EASE"
    ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3815
    cr.color_ramp.elements[0].color = (0.2773, 0.271, 0.047, 1.0)
    cr.color_ramp.elements[1].position = 0.7736
    cr.color_ramp.elements[1].color = (0.141, 0.146, 0.007, 1.0)
    _sample_color_keep_sum(cr.color_ramp.elements[0].color)
    _sample_color_keep_sum(cr.color_ramp.elements[1].color)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.3408

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_eye_material(seed, name="BirdEye_Material"):
    """Bird eyeball: black, Roughness=0.0 (matches shader_bird_eyeball)."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.0

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_claw_material(seed, name="BirdClaw_Material"):
    """Bird claw: near-black, Specular=0, Roughness~0.44 (matches shader_bird_claw)."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.0091, 0.0091, 0.0091, 1.0)
    bsdf.inputs[_spec_key(bsdf)].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.4409

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_spot_sparse_material_bird(seed, name="BirdSpotSparse_Material"):
    """SpotSparse body shader: voronoi spot pattern with warm earth tones."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # Voronoi spot pattern
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(tc.outputs["Object"], vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = 8.0 * float(np.random.uniform(0.5, 2.0))
    # Noise for organic variation
    noise = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 15.0
    noise.inputs["Roughness"].default_value = 1.0
    mix_pat = nt.nodes.new("ShaderNodeMix"); mix_pat.data_type = "RGBA"
    mix_pat.inputs[0].default_value = 0.5
    ln(vor.outputs["Distance"], mix_pat.inputs[6])
    ln(_fac(noise), mix_pat.inputs[7])
    # Color ramp for body
    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(mix_pat.outputs[2], cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.0
    cr.color_ramp.elements[0].color = _hsv2rgba(
        np.random.uniform(0.02, 0.06), np.random.uniform(0.05, 0.9),
        abs(float(np.random.normal(0.05, 0.1))))
    cr.color_ramp.elements[1].position = 1.0
    cr.color_ramp.elements[1].color = _hsv2rgba(
        np.random.uniform(0.02, 0.06), np.random.uniform(0.4, 0.8),
        np.random.uniform(0.15, 0.7))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs[_spec_key(bsdf)].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_reptile_brown_circle_material_bird(seed, name="BirdReptileBrownCircle_Material"):
    """ReptileBrownCircle body shader: brown circle pattern."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # Voronoi for circle pattern
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(tc.outputs["Object"], vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = float(np.random.uniform(8, 20))
    # Body color: warm brown tones
    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(vor.outputs["Distance"], cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.0
    cr.color_ramp.elements[0].color = _hsv2rgba(
        np.random.uniform(0.02, 0.08), np.random.uniform(0.5, 0.9),
        np.random.uniform(0.05, 0.25))
    cr.color_ramp.elements[1].position = 1.0
    cr.color_ramp.elements[1].color = _hsv2rgba(
        np.random.uniform(0.02, 0.08), np.random.uniform(0.3, 0.7),
        np.random.uniform(0.15, 0.5))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs[_spec_key(bsdf)].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_reptile_two_color_material_bird(seed, name="BirdReptileTwoColor_Material"):
    """ReptileTwoColor body shader: two-color reptile pattern."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # Noise for two-color pattern
    noise = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(np.random.uniform(3, 8))
    noise.noise_dimensions = "4D"
    noise.inputs["W"].default_value = float(np.random.uniform(-10, 10))
    # Two colors
    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.4
    cr.color_ramp.elements[0].color = _hsv2rgba(
        np.random.uniform(0.02, 0.12), np.random.uniform(0.5, 0.9),
        np.random.uniform(0.05, 0.3))
    cr.color_ramp.elements[1].position = 0.6
    cr.color_ramp.elements[1].color = _hsv2rgba(
        np.random.uniform(0.02, 0.12), np.random.uniform(0.3, 0.7),
        np.random.uniform(0.2, 0.6))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs[_spec_key(bsdf)].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _pick_bird_body_material(seed):
    """SpotSparse(4), ReptileBrownCircle(0.5), ReptileTwoColor(0.5), Bird(5).
    Uses np.random.seed(seed) + np.random.choice to match FixedSeed + weighted_sample."""

    np.random.seed(seed); _random.seed(seed)
    classes = ['SpotSparse', 'ReptileBrownCircle', 'ReptileTwoColor', 'Bird']
    weights = np.array([4.0, 0.5, 0.5, 5.0])
    chosen = classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]
    if chosen == 'Bird':
        return make_body_material(seed)
    elif chosen == 'SpotSparse':
        return make_spot_sparse_material_bird(seed)
    elif chosen == 'ReptileBrownCircle':
        return make_reptile_brown_circle_material_bird(seed)
    else:
        return make_reptile_two_color_material_bird(seed)

CREATURE_MAT = _pick_bird_body_material(SEED)

DEFAULT_JOIN_RESULT = True
DEFAULT_BEAK_SELECT = None

# ---------------------------------------------------------------------------
# Blender helpers
# ---------------------------------------------------------------------------

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for b in list(bpy.data.meshes):   bpy.data.meshes.remove(b)
    for b in list(bpy.data.curves):   bpy.data.curves.remove(b)

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
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def add_subsurf(obj, levels=2):
    m = obj.modifiers.new("SS", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    sel(obj)
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def add_boolean_union(target, cutter):
    """Boolean union: target | cutter, cutter removed."""

    mod = target.modifiers.new("BOOL", "BOOLEAN")
    mod.operation = "UNION"
    mod.object = cutter
    mod.solver = "FLOAT"
    sel(target)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    sel(cutter)
    bpy.ops.object.delete()
    return target

def add_solidify(obj, thickness=0.005, offset=-1.0):
    """Add a Solidify modifier and apply it."""

    m = obj.modifiers.new("Solidify", "SOLIDIFY")
    m.thickness = thickness
    m.offset = offset
    sel(obj)
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

# ---------------------------------------------------------------------------
# Pure-numpy math (no Blender API)
# ---------------------------------------------------------------------------

def compute_cylinder_topology(n, m):
    """n x m cylinder mesh (cyclic in m). Returns (edges, faces) as lists."""

    lp = np.arange(m)
    h = np.stack([lp, np.roll(lp, -1)], axis=-1)          # ring-edge pairs
    rs = np.arange(0, n * m, m)                            # ring start offsets
    ring_edges  = (rs[:, None, None] + h[None]).reshape(-1, 2)
    v = np.stack([lp, lp + m], axis=-1)                    # vertical pairs
    bs = np.arange(0, (n - 1) * m, m)
    bridge_edges = (bs[:, None, None] + v[None]).reshape(-1, 2)
    edges = np.concatenate([ring_edges, bridge_edges])
    fn = np.concatenate([h, h[:, ::-1] + m], axis=-1)     # quad face indices
    faces = (bs[:, None, None] + fn[None]).reshape(-1, 4)
    return edges.tolist(), faces.tolist()

def lerp_sample(vec, ts):
    vec = np.asarray(vec, dtype=np.float64)
    ts  = np.asarray(ts,  dtype=np.float64)
    idx = np.clip(np.floor(ts).astype(int), 0, len(vec) - 1)
    rem = ts - idx
    res = vec[idx].copy()
    m = idx < len(vec) - 1
    res[m] = (1 - rem[m, None]) * res[m] + rem[m, None] * vec[idx[m] + 1]
    return res

def cross_matrix(v):
    o = np.zeros(len(v))
    return np.stack([
        np.stack([o, -v[:,2],  v[:,1]], axis=-1),
        np.stack([ v[:,2], o, -v[:,0]], axis=-1),
        np.stack([-v[:,1],  v[:,0], o], axis=-1),
    ], axis=-1).transpose(0, 2, 1)

def rodrigues(angle, axis):
    axis = axis / np.linalg.norm(axis, axis=-1, keepdims=True)
    Id = np.zeros((len(axis), 3, 3)); Id[:, [0,1,2], [0,1,2]] = 1
    K  = cross_matrix(axis)
    th = angle[:, None, None]
    return Id + np.sin(th) * K + (1 - np.cos(th)) * (K @ K)

def rotate_match_directions(a, b):
    a, b = np.array(a, float), np.array(b, float)
    axes = np.cross(a, b, axis=-1)
    m    = np.linalg.norm(axes, axis=-1) > 1e-6
    rots = np.tile(np.eye(3), (len(a), 1, 1)).astype(float)
    if not m.any():
        return rots
    na = np.linalg.norm(a[m], axis=-1)
    nb = np.linalg.norm(b[m], axis=-1)
    dots = np.clip((a[m] * b[m]).sum(-1) / (na * nb), -1, 1)
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

def smooth_taper_arr(t, start_rad, end_rad, fullness):
    """

    Matches Blender's nodegroup_smooth_taper:
      shaped = sin(t*pi)^(1/fullness)
      output = shaped * lerp(start_rad, end_rad, t)
    """

    t = np.asarray(t, float)
    shaped = np.maximum(np.sin(t * np.pi), 0) ** (1.0 / fullness)
    return shaped * (start_rad + (end_rad - start_rad) * t)

def polar_bezier_skeleton(angles_deg, seg_lengths, n_pts=26,
                          origin=None, do_bezier=True):
    """

    Reimplements nodegroup_polar_bezier.
    angles_deg: 3 INCREMENTAL angles (degrees)
    seg_lengths: 3 segment lengths
    Returns (n_pts, 3) skeleton in the XZ plane.
    """

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
        skel = (((1-t)**3)[:, None] * pts[0]
                + (3*(1-t)**2*t)[:, None]  * pts[1]
                + (3*(1-t)*t**2)[:, None]  * pts[2]
                + (t**3)[:, None]           * pts[3])
    else:
        n_seg = n_pts // 3
        segs = []
        for i in range(3):
            ts = np.linspace(0, 1, n_seg + 1, endpoint=(i == 2))
            segs.append(pts[i][None] * (1 - ts[:, None]) + pts[i+1][None] * ts[:, None])
        skel = np.vstack(segs)[:n_pts]

    return skel

# ---------------------------------------------------------------------------
# Core tube mesh (= simple_tube_v2 equivalent)
# ---------------------------------------------------------------------------

def create_tube_mesh(name, length, rad1, rad2,
                     angles_deg=(0, 0, 0), aspect=1.0, fullness=4.0,
                     proportions=(1/3, 1/3, 1/3),
                     origin=(0, 0, 0), do_bezier=True,
                     n_skel=26, n_profile=16):
    """

    Creates a tube mesh matching simple_tube_v2:
      - polar bezier skeleton in XZ plane
      - circular (or elliptical) profile in YZ plane
      - smooth_taper radius along the skeleton
    """

    prop = np.array(proportions, float)
    prop /= prop.sum()
    seg_lengths = prop * length

    skel  = polar_bezier_skeleton(angles_deg, seg_lengths, n_skel,
                                  np.array(origin, float), do_bezier)
    t_arr = np.linspace(0, 1, n_skel)
    radii = smooth_taper_arr(t_arr, rad1, rad2, fullness)  # (n_skel,)

    # Profile ellipse in YZ  (aspect_to_dim logic)
    if aspect >= 1.0:
        ay, az = aspect, 1.0
    else:
        ay, az = 1.0, 1.0 / aspect
    theta = np.linspace(-np.pi/2, 1.5*np.pi, n_profile, endpoint=False)
    profile_local = np.stack([
        np.zeros(n_profile),
        ay * np.cos(theta),
        az * np.sin(theta),
    ], axis=-1)                                           # (n_profile, 3)

    tangents = skeleton_to_tangents(skel)                 # (n_skel, 3)
    fwd = np.zeros_like(tangents); fwd[:, 0] = 1.0
    R   = rotate_match_directions(fwd, tangents)          # (n_skel, 3, 3)

    # profile_pts[i,j] = R[i] @ profile_local[j] * radii[i] + skel[i]
    profile_pts = np.einsum('bij,vj->bvi', R, profile_local)  # (n_skel, n_p, 3)
    verts = profile_pts * radii[:, None, None] + skel[:, None, :]  # (n_skel, n_p, 3)

    edges, faces = compute_cylinder_topology(n_skel, n_profile)
    return new_mesh_obj(name, verts.reshape(-1, 3), edges, faces), skel

# ---------------------------------------------------------------------------
# NURBS body data  (3 templates embedded from .npy files)
# ---------------------------------------------------------------------------
BODY_BIRD_DUCK = np.array([
    -0.0008446425, 0.0000432707, 0.0042036064, -0.0008423664, 0.0000432707,
     0.0042549223, -0.0008400902, 0.0000432707, 0.0043062381, -0.0008400902,
    -0.0000000110, 0.0043062381, -0.0008400902,-0.0000432926, 0.0043062381,
    -0.0008423664,-0.0000432926, 0.0042549223, -0.0008446425,-0.0000432926,
     0.0042036064, -0.0008446425,-0.0000000110, 0.0042036064,
    -0.0038748081, 0.0576728210,-0.0641253665, -0.0008423664, 0.0865634978,
     0.0042548925,  0.0021896202, 0.0576728210, 0.0726351365,  0.0037088096,
     0.0000000152, 0.1068896353,  0.0021896202,-0.0576727726, 0.0726351365,
    -0.0008423664,-0.0865634829, 0.0042548887, -0.0038748081,-0.0576727726,
    -0.0641253665, -0.0051269941, 0.0000000147,-0.0923689082,
     0.2280129939, 0.1242700592,-0.1799076647,  0.2376113832, 0.2190986276,
    -0.0211708322,  0.2417448312, 0.1753083915, 0.2034341246,  0.2434599549,
    -0.0000000456, 0.2513115704,  0.2417448014,-0.1753084511, 0.2034341246,
     0.2376115024,-0.2190987021,-0.0211707912,  0.2280129641,-0.1242700294,
    -0.1799076647,  0.2395231277, 0.0000000085,-0.2473705113,
     0.4720124006, 0.2412946075,-0.3435566425,  0.4723560810, 0.3435192108,
    -0.1214741394,  0.4552413821, 0.2412946075, 0.2577252388,  0.4534164667,
    -0.0000000850, 0.3231527805,  0.4552413821,-0.2412948012, 0.2577252388,
     0.4723560810,-0.3435195684,-0.1214741394,  0.4720124006,-0.2412948012,
    -0.3435566425,  0.4738373160,-0.0000000856,-0.4089842141,
     1.0277198553, 0.2756166160,-0.2381114811,  0.8027335405, 0.3661958873,
    -0.0150295347,  0.6696565747, 0.2236986160, 0.2823533416,  0.6310566068,
    -0.0000000894, 0.3403475285,  0.6696563363,-0.2236988544, 0.2823533416,
     0.8027334213,-0.3661960065,-0.0150294825,  1.0277197361,-0.2756168246,
    -0.2381115407,  1.0676177740,-0.0000001068,-0.2961056530,
     1.1593320370, 0.1279801428, 0.1653562337,  0.9484238029, 0.1758911312,
     0.2006424665,  0.8047918081, 0.1279801428, 0.2991563082,  0.7384287715,
    -0.0000000492, 0.3242011666,  0.8047918081,-0.1279802322, 0.2991563082,
     0.9484238029,-0.1758911610, 0.2006425858,  1.1593319178,-0.1279802173,
     0.1653560996,  1.2256954908,-0.0000000705, 0.1403112113,
     0.9364205599, 0.0775696561, 0.5178570151,  0.8450711370, 0.1090546697,
     0.5099512935,  0.7558270693, 0.0775696784, 0.4882979095,  0.7191765904,
     0.0000000960, 0.4822989702,  0.7558270693,-0.0775695071, 0.4882979095,
     0.8450711370,-0.1090545133, 0.5099512935,  0.9364205599,-0.0775695369,
     0.5178570151,  0.9730718732, 0.0000000537, 0.5238559246,
     0.9153573513, 0.0694428384, 0.7882130742,  0.8525727391, 0.0989146829,
     0.8199751973,  0.7882714868, 0.0714144409, 0.8701693416,  0.7639108896,
     0.0000012585, 0.8926386237,  0.7882714868,-0.0717879683, 0.8701693416,
     0.8525727391,-0.0989122242, 0.8199751377,  0.9166370630,-0.0717879906,
     0.7865754962,  0.9412414432, 0.0000012477, 0.7637939453,
     0.8685617447, 0.0004801478, 0.8163174391,  0.8681309223, 0.0004801479,
     0.8167157173,  0.8676999211, 0.0004801479, 0.8171137571,  0.8676999211,
    -0.0000005544, 0.8171137571,  0.8676999211,-0.0004812564, 0.8171137571,
     0.8681309223,-0.0004812565, 0.8167157173,  0.8685617447,-0.0004812565,
     0.8163174391,  0.8685617447,-0.0000005545, 0.8163174391,
]).reshape(9, 8, 3)

BODY_BIRD_GULL = np.array([
    -0.0008446574, 0.0000389173, 0.0042036176, -0.0008423328, 0.0000389173,
     0.0042549372, -0.0008400679, 0.0000389173, 0.0043062270, -0.0008400679,
    -0.0000000356, 0.0043062270, -0.0008400679,-0.0000389886, 0.0043062270,
    -0.0008423328,-0.0000389886, 0.0042549372, -0.0008446574,-0.0000389886,
     0.0042036176, -0.0008446574,-0.0000000356, 0.0042036176,
    -0.0036253994, 0.0476352312,-0.0585005879, -0.0008423328, 0.0779060796,
     0.0042548776,  0.0019401778, 0.0476352312, 0.0670102984,  0.0037088394,
    -0.0000000121, 0.1068896353,  0.0019401778,-0.0476352535, 0.0670102984,
    -0.0008423328,-0.0779061168, 0.0042548776, -0.0036253994,-0.0476352535,
    -0.0585005879, -0.0051269531,-0.0000000125,-0.0923689008,
     0.2314901054, 0.1120816320,-0.1459159702,  0.2402983904, 0.1892039031,
    -0.0079555959,  0.2442464530, 0.1363076717, 0.1256272346,  0.2455003858,
    -0.0000000770, 0.2168057114,  0.2442464530,-0.1363077611, 0.1256272346,
     0.2402985096,-0.1892040223,-0.0079555437,  0.2314900905,-0.1120816916,
    -0.1459159702,  0.2419987917,-0.0000000302,-0.1945398450,
     0.4965955019, 0.2086859345,-0.2613779604,  0.5101122260, 0.4297458529,
    -0.0325832814,  0.3843834102, 0.1844004393, 0.1778219044,  0.3799831271,
    -0.0000001011, 0.2822841108,  0.3843834102,-0.1844006777, 0.1778219044,
     0.5101122260,-0.4297462106,-0.0325832814,  0.4965955019,-0.2086861730,
    -0.2613779604,  0.4948223829,-0.0000000966,-0.3577124178,
     0.8900600672, 0.1934320033,-0.1532992125,  0.7192924619, 0.3778997660,
     0.0885101557,  0.5617794991, 0.1361570656, 0.2552843094,  0.5079537034,
    -0.0000001034, 0.3325076699,  0.5617793202,-0.1361573189, 0.2552843094,
     0.7192923427,-0.3778999448, 0.0885102004,  0.8900600076,-0.1934322566,
    -0.1532992423,  0.9918751717,-0.0000001250,-0.2738099396,
     0.9954238534, 0.1541375518, 0.1391703784,  0.8373568058, 0.2891549468,
     0.2173147500,  0.6491269469, 0.1192853004, 0.3669389784,  0.5892390013,
    -0.0000000732, 0.3985656202,  0.6491269469,-0.1192854568, 0.3669389784,
     0.8373568654,-0.2891550660, 0.2173148841,  0.9954237342,-0.1541376263,
     0.1391702741,  1.1442900896,-0.0000000984, 0.0642386526,
     0.8683233261, 0.0922141746, 0.4804127514,  0.8136795759, 0.1370076984,
     0.4970114231,  0.6975598931, 0.0922141820, 0.5007689595,  0.6501832604,
     0.0000000914, 0.5050302744,  0.6975598931,-0.0922139883, 0.5007689595,
     0.8136795759,-0.1370075494, 0.4970114231,  0.8683233261,-0.0922140107,
     0.4804127514,  0.9578036070, 0.0000000487, 0.4761514366,
     0.9301526546, 0.1139396355, 0.7646466494,  0.8306376338, 0.1599938273,
     0.8406182528,  0.7311317325, 0.1139396727, 0.9166037440,  0.6909090281,
     0.0000018519, 0.9473146200,  0.7311317325,-0.1139360294, 0.9166037440,
     0.8306376338,-0.1599902064, 0.8406181931,  0.9301525354,-0.1139360592,
     0.7646467090,  0.9703747630, 0.0000018308, 0.7339358926,
     0.8530505300, 0.0007764509, 0.8509535193,  0.8523715734, 0.0007764509,
     0.8514721394,  0.8516923189, 0.0007764509, 0.8519904017,  0.8516923189,
    -0.0000010827, 0.8519904017,  0.8516923189,-0.0007786158, 0.8519904017,
     0.8523715734,-0.0007786159, 0.8514721394,  0.8530505300,-0.0007786159,
     0.8509535193,  0.8530505300,-0.0000010828, 0.8509535193,
]).reshape(9, 8, 3)

BODY_BIRD_ROBIN = np.array([
     0.0019502416, 0.0000192641,-0.0013356097,  0.0019516125, 0.0000192641,
    -0.0013043471,  0.0019530132, 0.0000192641,-0.0012730844,  0.0019530132,
    -0.0000020929,-0.0012730844,  0.0019530132,-0.0000234500,-0.0012730844,
     0.0019516125,-0.0000234500,-0.0013043471,  0.0019502416,-0.0000234500,
    -0.0013356097,  0.0019502416,-0.0000020929,-0.0013356097,
    -0.0000873432, 0.0314187147,-0.0472836383,  0.0019516125, 0.0427121259,
    -0.0013043769,  0.0039903298, 0.0314187147, 0.0446749963,  0.0047233477,
    -0.0000020800, 0.0612010695,  0.0039903298,-0.0314228758, 0.0446749963,
     0.0019516125,-0.0427163020,-0.0013043769, -0.0000873432,-0.0314228758,
    -0.0472836383, -0.0006577298,-0.0000020803,-0.0601490736,
     0.1409156024, 0.0792493969,-0.1364282668,  0.1467560828, 0.1572373509,
    -0.0255848356,  0.1493794620, 0.1117983907, 0.1287831515,  0.1501991451,
    -0.0000021173, 0.1544668376,  0.1493794620,-0.1118026301, 0.1287831515,
     0.1467561424,-0.1572415233,-0.0255848356,  0.1409156024,-0.0792535916,
    -0.1364282668,  0.1478814781,-0.0000020844,-0.1750537455,
     0.2941623032, 0.1160812005,-0.1762729287,  0.2728885114, 0.1900214553,
    -0.0478633232,  0.2282768190, 0.1158870757, 0.1797394902,  0.2224938869,
    -0.0000021217, 0.2132386863,  0.2286419272,-0.1161037683, 0.1797395498,
     0.2728885114,-0.1900257617,-0.0478633232,  0.2941623032,-0.1161037683,
    -0.1762729287,  0.3003444970,-0.0000021221,-0.2097719908,
     0.5199529529, 0.1572557390,-0.0435361303,  0.3738709390, 0.1707959920,
     0.0599466898,  0.2951515913, 0.0930423513, 0.2279425263,  0.2737649083,
    -0.0000021242, 0.2590380013,  0.2951515317,-0.0930466428, 0.2279425263,
     0.3738708794,-0.1708002239, 0.0599467196,  0.5199528337,-0.1572599560,
    -0.0435361303,  0.5420725942,-0.0000021332,-0.1068537086,
     0.5941743255, 0.1420249492, 0.0772553831,  0.4498490691, 0.1375948191,
     0.1536994576,  0.3578301072, 0.0868864357, 0.2551501095,  0.3182914257,
    -0.0000021148, 0.2852081358,  0.3578301072,-0.0868906751, 0.2551501095,
     0.4498491883,-0.1375989765, 0.1536995471,  0.5941742063,-0.1420290917,
     0.0772553310,  0.6337128282,-0.0000021183, 0.0471971594,
     0.6169554591, 0.0809673667, 0.2371438742,  0.5225717425, 0.1217206046,
     0.2988375127,  0.4145042300, 0.0809673741, 0.3472932279,  0.3856923282,
    -0.0000020997, 0.3626746237,  0.4145042300,-0.0809716210, 0.3472932279,
     0.5225717425,-0.1217248738, 0.2988375127,  0.6169554591,-0.0809716210,
     0.2371438742,  0.6454198956,-0.0000021235, 0.2211283445,
     0.6404874921, 0.0641967878, 0.3754986823,  0.5604026914, 0.0987554193,
     0.4284239411,  0.5004996657, 0.0641967952, 0.4789372683,  0.4797393680,
    -0.0000009627, 0.4964408875,  0.5004996657,-0.0641987324, 0.4789372683,
     0.5604026914,-0.0987573937, 0.4284238815,  0.6404874921,-0.0641987324,
     0.3754986823,  0.6612477899,-0.0000009733, 0.3579950929,
     0.5760942101, 0.0004771697, 0.4347584248,  0.5756464601, 0.0004771698,
     0.4351361096,  0.5751983523, 0.0004771698, 0.4355135560,  0.5751983523,
    -0.0000027692, 0.4355135560,  0.5751983523,-0.0004827080, 0.4355135560,
     0.5756464601,-0.0004827080, 0.4351361096,  0.5760942101,-0.0004827082,
     0.4347584248,  0.5760942101,-0.0000027693, 0.4347584248,
]).reshape(9, 8, 3)

BODY_TEMPLATES = [BODY_BIRD_DUCK, BODY_BIRD_GULL, BODY_BIRD_ROBIN]

# ---------------------------------------------------------------------------
# NURBS body: decompose / recompose (from generic_nurbs.py + lofting.py)
# ---------------------------------------------------------------------------

def compute_profile_verts_lofting(skeleton, ts, profiles, profile_as_points=False):
    """Exactly as in lofting.compute_profile_verts."""

    n, m = profiles.shape[:2]
    k = len(skeleton)
    tangents = skeleton_to_tangents(skeleton)
    axes = lerp_sample(tangents, ts * (k - 1))
    pos  = lerp_sample(skeleton,  ts * (k - 1))

    if profile_as_points:
        profile_verts = np.array(profiles, float)
    else:
        angles = np.linspace(-np.pi/2, 1.5*np.pi, m, endpoint=False)
        unit_c = np.stack([np.zeros(m), np.cos(angles), np.sin(angles)], axis=-1)
        profile_verts = profiles[..., None] * unit_c[None]

    fwd = np.zeros_like(axes); fwd[:, 0] = 1.0
    R   = rotate_match_directions(fwd, axes)
    return np.einsum('bij,bvj->bvi', R, profile_verts) + pos[:, None]

def ordered_polyline_vertices(obj):
    adjacency = {i: [] for i in range(len(obj.data.vertices))}
    for edge in obj.data.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)

    endpoints = [idx for idx, nbrs in adjacency.items() if len(nbrs) == 1]
    start = endpoints[0] if endpoints else 0

    order = [start]
    prev = None
    curr = start
    for _ in range(max(0, len(obj.data.vertices) - 1)):
        nxts = [nbr for nbr in adjacency[curr] if nbr != prev]
        if not nxts:
            break
        prev, curr = curr, nxts[0]
        order.append(curr)

    return np.array([obj.data.vertices[i].co[:] for i in order], dtype=float)

def refine_open_skeleton(points, levels=2, name="skeleton_temp"):
    points = np.asarray(points, dtype=float)
    if len(points) < 2:
        return points.copy()

    edges = [[i, i + 1] for i in range(len(points) - 1)]
    obj = new_mesh_obj(name, points, edges, [])
    add_subsurf(obj, levels=levels)
    refined = ordered_polyline_vertices(obj)
    sel(obj)
    bpy.ops.object.delete()
    return refined

def decompose_nurbs_handles(handles):
    """From generic_nurbs.decompose_nurbs_handles."""

    skeleton = handles.mean(axis=1)   # (n, 3)
    tangents = skeleton_to_tangents(skeleton)
    fwd = np.zeros_like(tangents); fwd[:, 0] = 1.0
    rot = rotate_match_directions(tangents, fwd)          # rotate tangent -> X

    profiles = handles - skeleton[:, None]                # offset from center
    profiles = np.einsum('bij,bvj->bvi', rot, profiles)  # rotate to local frame

    rads = np.linalg.norm(profiles, axis=2, keepdims=True).mean(axis=1, keepdims=True)
    rads = np.clip(rads, 1e-3, 1e5)
    profiles_norm = profiles / rads

    dirs  = np.diff(skeleton, axis=0)
    lens  = np.linalg.norm(dirs, axis=-1)
    length = lens.sum()
    proportions = lens / length
    thetas      = np.rad2deg(np.arctan2(dirs[:, 2], dirs[:, 0]))
    yoffs       = dirs[:, 1] / lens

    return {
        "ts":           np.linspace(0, 1, handles.shape[0]),
        "rads":         rads,
        "skeleton_root": skeleton[[0]],
        "skeleton_yoffs": yoffs,
        "length":       float(length),
        "proportions":  proportions,
        "thetas":       thetas,
        "profiles_norm": profiles_norm,
    }

def recompose_nurbs_handles(params):
    """From generic_nurbs.recompose_nurbs_handles."""

    lens   = params["length"] * params["proportions"]
    thetas = np.deg2rad(params["thetas"])
    offs   = np.stack([
        lens * np.cos(thetas),
        lens * params["skeleton_yoffs"],
        lens * np.sin(thetas),
    ], axis=-1)
    skeleton = np.cumsum(
        np.concatenate([params["skeleton_root"], offs], axis=0), axis=0)

    handles = compute_profile_verts_lofting(
        skeleton, params["ts"],
        params["profiles_norm"] * params["rads"],
        profile_as_points=True,
    )
    return handles

def create_nurbs_body():
    """

    Blends 3 bird-body templates with Dirichlet(0.3) weights, adds noise,
    creates a subdivided mesh, and exports the attachment skeleton the same
    way official `part_util.nurbs_to_part()` does.
    """
    # random_convex_coord with temp=0.3 -> Dirichlet([0.3,0.3,0.3])
    w = np.random.dirichlet([0.3, 0.3, 0.3])
    handles = sum(wi * ti for wi, ti in zip(w, BODY_TEMPLATES))

    decomp = decompose_nurbs_handles(handles)

    # NurbsPart.sample_params noise (var = U(0.3,1))
    var = np.random.uniform(0.3, 1.0)

    def Nv(m, v, shape=None):
        return np.random.normal(m, np.array(v) * var,
                                shape if shape else None)

    sz = Nv(1, 0.1)
    decomp["length"]      *= float(sz) * float(Nv(1, 0.1))
    decomp["rads"]        *= sz * Nv(1, 0.1) * Nv(1, 0.15, decomp["rads"].shape)
    decomp["proportions"] *= Nv(1, 0.15, decomp["proportions"].shape)

    ang_noise  = Nv(0, 7, decomp["thetas"].shape)
    ang_noise -= ang_noise.mean()
    decomp["thetas"] += ang_noise

    n, m, _ = decomp["profiles_norm"].shape
    pnoise  = Nv(1, 0.07, (1, m, 1)) * Nv(1, 0.15, (n, m, 1))
    # symmetrize
    pnoise[:, :m//2-1] = pnoise[:, m//2:-1][:, ::-1]
    decomp["profiles_norm"] *= pnoise

    body_length = decomp["length"]
    handles_f   = recompose_nurbs_handles(decomp)           # (9, 8, 3)

    n_c, m_c, _ = handles_f.shape
    edges, faces = compute_cylinder_topology(n_c, m_c)
    body_obj = new_mesh_obj("body", handles_f.reshape(-1, 3), edges, faces)

    # Smooth the mesh via SUBSURF
    add_subsurf(body_obj, levels=3)

    body_skeleton = handles_f.mean(axis=1)[1:-1]
    body_skeleton = refine_open_skeleton(
        body_skeleton, levels=2, name="body_skeleton_temp"
    )
    return body_obj, float(body_length), body_skeleton

# ---------------------------------------------------------------------------
# Beak (parametric surface)  --  from beak.py
# ---------------------------------------------------------------------------

class Beak:
    """Faithful transcription of beak.Beak."""

    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.hook_x = lambda x, th: self._hook(
            self.hook_scale_x, self.hook_a, self.hook_b,
            self.hook_pos_x, self.hook_thickness_x, x, th)
        self.hook_z = lambda x, th: self._hook(
            self.hook_scale_z, self.hook_a, self.hook_b,
            self.hook_pos_z, self.hook_thickness_z, x, th)
        self.crown_z = lambda x, th: self._crown(
            self.crown_scale_z, self.crown_a, self.crown_b, self.crown_pos_z, x, th)
        self.bump_z  = lambda x, th: self._bump(
            self.bump_scale_z, x, self.bump_l, self.bump_r) * max(sin(th), 0)

    def cx(self, x):  return x
    def cy(self, x):  return 1 - exp(self.cy_a * (x - 1))
    def cz(self, x):  return 1 - (x ** self.cz_a)

    def _hook(self, scale, a, b, p, t, x, th):
        return scale * a * exp(b * (x - p - (1 - x) * t * sin(th)))

    def _bump(self, scale, x, lo, hi):
        if x < lo or x > hi: return 0
        return scale * sin((x - lo) / (hi - lo) * pi)

    def _crown(self, scale, a, b, p, x, th):
        return scale * a * exp(b * (p - x)) * max(sin(th), 0)

    def dx(self, x, th):
        return self.hook_x(x, th) + self.sharpness * max(x - 0.95, 0)

    def dz(self, x, th):
        return self.hook_z(x, th) + self.crown_z(x, th) + self.bump_z(x, th)

    def generate_verts(self, n_p=None, n_t=None):
        """

        Returns (n,m,3) vertex array for the beak surface.
        n_p: number of samples in p (default self.n)
        n_t: number of samples in theta (default self.m)
        """

        n_p = int(n_p or self.n)
        n_t = int(n_t or self.m)
        verts = np.zeros((n_p, n_t, 3))
        for i in range(n_p):
            p = i / (n_p - 1)
            for j in range(n_t):
                th = 2 * pi * j / n_t
                verts[i, j, 0] = self.sx * self.cx(p) + self.dx(p, th)
                verts[i, j, 1] = self.sy * self.cy(p) * self.r * cos(th)
                verts[i, j, 2] = self.reverse * (
                    self.sz * self.cz(p) * self.r * max(sin(th), 0) + self.dz(p, th))
        return verts

BeakSurface = Beak


def create_feather_mesh(name, feather_len, rad1, rad2, n_pts=28):
    """

    Flat leaf-shaped feather.
    Profile curve: [(0,0),(0.23,0.985),(0.89,0.6),(1,0)] x lerp(rad1,rad2,t)
    Swept with Y-line profile -> flat strip in XY plane.
    """

    t = np.linspace(0, 1, n_pts)
    profile_t = [0.0, 0.2327, 0.8909, 1.0]
    profile_v = [0.0, 0.985,  0.6,    0.0]
    shape  = np.interp(t, profile_t, profile_v)
    width  = shape * (rad1 + (rad2 - rad1) * t)      # per-point half-width
    x      = t * feather_len

    top  = np.stack([x,  width, np.zeros(n_pts)], axis=-1)
    bot  = np.stack([x, -width, np.zeros(n_pts)], axis=-1)
    verts = np.vstack([top, bot])

    faces = [[i, i+1, n_pts+i+1, n_pts+i] for i in range(n_pts-1)]
    return new_mesh_obj(name, verts, [], faces)

# ---------------------------------------------------------------------------
# Body surface attachment helper
# ---------------------------------------------------------------------------


def create_head():
    """

    Mesh approximation of `parts.head.BirdHead`.

    This keeps the official parameterization instead of scaling by body length.
    it is two fixed-scale `simple_tube_v2` shapes unioned together.
    """

    lrr = np.array([0.35, 0.11, 0.13]) * N(1, 0.05) * N(1, 0.1, 3)
    ang = N(0, 5, 3)
    l, r1, r2 = lrr

    t1, _sk1 = create_tube_mesh(
        "head_t1",
        l,
        r1,
        r2,
        angles_deg=ang,
        aspect=0.86,
        fullness=1.7,
        origin=(-0.13, 0.0, 0.10),
        n_skel=20,
        n_profile=20,
    )

    t2, _sk2 = create_tube_mesh(
        "head_t2",
        l,
        r1,
        r2,
        angles_deg=ang,
        aspect=1.19,
        fullness=2.25,
        origin=(-0.13, 0.0, 0.06),
        n_skel=20,
        n_profile=20,
    )

    head = add_boolean_union(t1, t2)
    head.name = "head"
    add_subsurf(head, levels=1)

    head_skel = _sk1
    return head, head_skel, float(l)

# ---------------------------------------------------------------------------
# Eyes
# ---------------------------------------------------------------------------

def create_eye(radius=0.03):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=8, radius=radius)
    obj = bpy.context.active_object
    obj.name = "eye"
    return obj

# ---------------------------------------------------------------------------
# Wings  (nodegroup_bird_wing: tube + 3 feather layers)
# ---------------------------------------------------------------------------

def _build_tube_from_skeleton(name, skel, rad1, rad2, fullness=4.0,
                               aspect=1.0, n_profile=8, z_shift=0.0,
                               radii_override=None):
    """Build a tube mesh around an arbitrary skeleton (array of 3D points).

    z_shift : shift the profile center in local Z (in radius-units).
              Negative values make the tube hang *below* the skeleton.
    radii_override : if given, use this array of per-vertex radii instead of
                     the default smooth_taper_arr.
    """

    n_skel = len(skel)
    if radii_override is not None:
        radii = radii_override
    else:
        t_arr = np.linspace(0, 1, n_skel)
        radii = smooth_taper_arr(t_arr, rad1, rad2, fullness)

    if aspect >= 1.0:
        ay, az = aspect, 1.0
    else:
        ay, az = 1.0, 1.0 / aspect
    theta = np.linspace(-np.pi/2, 1.5*np.pi, n_profile, endpoint=False)
    profile_local = np.stack([
        np.zeros(n_profile),
        ay * np.cos(theta),
        az * np.sin(theta) + z_shift,
    ], axis=-1)

    tangents = skeleton_to_tangents(skel)
    fwd = np.zeros_like(tangents); fwd[:, 0] = 1.0
    R = rotate_match_directions(fwd, tangents)

    profile_pts = np.einsum('bij,vj->bvi', R, profile_local)
    verts = profile_pts * radii[:, None, None] + skel[:, None, :]

    edges, faces = compute_cylinder_topology(n_skel, n_profile)
    return new_mesh_obj(name, verts.reshape(-1, 3), edges, faces)

def create_wing(body_length, side=1):
    """

    BirdWing (duck_genome): arm tube (simple_tube_v2) + 3 layers of instanced feathers.

    BirdWing.sample_params + duck_genome overrides.
    Wing is built in local XZ plane (matching polar_bezier convention).
    Caller handles positioning, rotation, and side mirroring.

    Returns (wing_obj, arm_skeleton, extension).
    """
    # -- duck_genome parameters ------------------------------------------------
    # wing_len = body_length * 0.5 * clip_gaussian(1.2, 0.7, 0.5, 2.5)
    wing_len = body_length * 0.5 * np.clip(N(1.2, 0.7), 0.5, 2.5)
    arm_r1 = 0.1 * N(1, 0.1)
    arm_r2 = 0.02 * N(1, 0.2)

    # Extension: U(0.01, 0.1) from duck_genome (non-flying mode)
    extension = np.random.uniform(0.01, 0.1)
    ext = np.clip(extension, 0, 1)

    # BirdWing.sample_params defaults (not overridden by duck_genome)
    aspect = N(0.4, 0.05)
    fullness = N(4, 0.1)
    wing_sculpt = np.random.uniform(0.6, 1.0)

    # Feather params: BirdWing.sample_params (wings.py:524) passes
    # np.array((0.7*N(1,0.2), 0.04, 0.04)) — NOT the nodegroup socket default
    feather_density = 30
    f_len = 0.7 * N(1, 0.2)
    f_r1 = 0.04
    f_r2 = 0.04

    # -- Arm angles from Extension -----------------------------------------
    # MapRange: ext [0,1] -> angles_deg
    # BirdWing: min=(-83.46, 154.85, -155.38), max=(-15.04, 60.5, -41.1)
    angles_deg = (
        -83.46 + ext * (-15.04 - (-83.46)),
        154.85 + ext * (60.5 - 154.85),
        -155.38 + ext * (-41.1 - (-155.38)),
    )

    # -- Create arm tube ---------------------------------------------------
    proportions = (0.2, 0.27, 0.3)   # BirdWing proportions
    prop = np.array(proportions, float)
    prop /= prop.sum()
    seg_lengths = prop * wing_len
    n_skel = 26
    arm_skel = polar_bezier_skeleton(angles_deg, seg_lengths, n_skel,
                                      np.zeros(3), do_bezier=False)

    t_arr = np.linspace(0, 1, n_skel)
    base_radii = smooth_taper_arr(t_arr, arm_r1, arm_r2, fullness)
    n_tube_profile = 16
    arm_tube = _build_tube_from_skeleton(
        f"wing_arm_{side}", arm_skel, arm_r1, arm_r2,
        fullness=fullness, aspect=aspect, n_profile=n_tube_profile,
        radii_override=base_radii
    )

    # -- Resample skeleton for feather placement ---------------------------
    diffs = np.diff(arm_skel, axis=0)
    seg_lens = np.linalg.norm(diffs, axis=1)
    curve_length = seg_lens.sum()

    n_feathers = max(10, int(curve_length * feather_density))
    cum_lens = np.concatenate([[0], np.cumsum(seg_lens)])
    t_uniform = np.linspace(0, cum_lens[-1], n_feathers)

    feather_pts = np.zeros((n_feathers, 3))
    for i, t_val in enumerate(t_uniform):
        idx = np.searchsorted(cum_lens, t_val, side='right') - 1
        idx = int(np.clip(idx, 0, len(arm_skel) - 2))
        local_t = (t_val - cum_lens[idx]) / max(seg_lens[idx], 1e-10)
        local_t = float(np.clip(local_t, 0, 1))
        feather_pts[i] = arm_skel[idx] * (1 - local_t) + arm_skel[idx + 1] * local_t

    # -- Curve evaluation helper -------------------------------------------
    def _eval_curve(pts, x):
        if x <= pts[0][0]:
            return pts[0][1]
        for j in range(len(pts) - 1):
            x0, y0 = pts[j]; x1, y1 = pts[j + 1]
            if x <= x1:
                return y0 + (x - x0) / max(x1 - x0, 1e-10) * (y1 - y0)
        return pts[-1][1]

    # -- FloatCurve: skeleton X position -> rotation weight ----------------
    # From nodegroup_bird_wing (operates on skeleton vertex X coordinate)
    _fc_pts = [(0.0, 0.0), (0.5164, 0.245), (0.7564, 0.625), (1.0, 1.0)]

    # -- VectorCurves X: skeleton X position -> feather scale factor -------
    # From nodegroup_bird_wing (X channel; Y,Z channels -> constant 1.0)
    # Original values from nodegroup_bird_wing; tip (1.0) reduced from 0.58
    # to 0.30 because without fur coverage the tip feathers protrude visually.
    _sc_pts = [
        (-1.0, 0.0), (0.0036, 0.0), (0.0473, 0.6), (0.3527, 0.54),
        (0.6, 0.9), (0.8836, 0.85), (1.0, 0.45)
    ]

    # -- Y rotation range (Extension -> max Y rotation) --------------------
    # MapRange: ext [0,1] -> [115.65, 0.0]
    y_rot_max_deg = 115.65 * (1 - ext)

    # -- Place feathers: 3 layers ------------------------------------------
    parts = [arm_tube]

    # Layer offsets and X-scale multipliers from nodegroup_bird_wing
    layer_offsets = [(-5.0, 0.0, -1.0), (-5.0, 0.0, 0.0), (-10.3, 0.0, 1.0)]
    layer_sx_mult = [1.0, 0.75, 0.45]

    for layer_i in range(3):
        rx_off, ry_off, rz_off = layer_offsets[layer_i]
        sx_mult = layer_sx_mult[layer_i]

        for fi in range(n_feathers):
            pos = feather_pts[fi].copy()
            # Original GeoNodes: index is normalized [0,1] via MapRange,
            # then SampleNearest re-indexes it — effectively the same as
            # uniformly spaced t ∈ [0,1] along the resampled curve.
            t_param = fi / max(n_feathers - 1, 1)

            # VectorCurves X -> base feather scale
            sc_raw = _eval_curve(_sc_pts, t_param)
            sc_x = t_param * (1 - wing_sculpt) + sc_raw * wing_sculpt
            if sc_x < 0.01:
                continue

            # Per-layer X scale multiplier
            sx = sc_x * sx_mult

            flen = f_len * sx
            if flen < 0.003:
                continue

            # FloatCurve -> rotation weight [0,1]
            fc_raw = _eval_curve(_fc_pts, t_param)
            fc_val = t_param * (1 - wing_sculpt) + fc_raw * wing_sculpt

            # MapRange: fc_val [0,1] -> Y rotation [80 deg, y_rot_max deg]
            y_rot = 80.0 + fc_val * (y_rot_max_deg - 80.0)

            # Add per-layer offset
            rot_deg = np.array([rx_off, y_rot + ry_off, rz_off])
            rot_rad = np.radians(rot_deg)

            f_obj = create_feather_mesh(
                f"f_{layer_i}_{side}_{fi}",
                flen, f_r1, f_r2
            )
            f_obj.location = tuple(pos)
            f_obj.rotation_euler = tuple(rot_rad)
            apply_tf(f_obj)
            parts.append(f_obj)

    result = join_objs(parts)
    add_solidify(result, thickness=0.003, offset=1.0)
    result.name = f"wing_{side}"
    return result, arm_skel, extension

# ---------------------------------------------------------------------------
# Tail  (nodegroup_bird_tail: tube core + feather fan)
# ---------------------------------------------------------------------------

def create_tail():
    """

    Mesh approximation of `parts.wings.BirdTail`.

    Official duck tails do not rescale with sampled body length; only the wing/leg
    factories pick up body-dependent lengths in `duck_genome`.
    """

    n_f = max(2, int(N(16, 3)))
    feather_lrr = np.array((0.4, 0.06, 0.04)) * N(1, 0.1) * N(1, 0.1, 3)
    f_l, f_r1, f_r2 = feather_lrr
    rot_ext = np.array((25.0, -10.0, -16.0)) * N(1, 0.1, 3)
    rot_rnd = np.array((2.0, 2.0, 2.0)) * N(1, 0.1) * N(1, 0.05, 3)

    tail_obj, tail_skel = create_tube_mesh(
        "tail_core",
        0.33,
        0.07,
        0.02,
        angles_deg=(0, 0, 0),
        proportions=(1 / 3, 1 / 3, 1 / 3),
        fullness=3.0,
        n_skel=10,
        n_profile=8,
    )

    parts = [tail_obj]

    def qbez(t, p0, p1, p2):
        return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t**2 * p2

    p0 = np.array((0.0, 0.0, -0.1))
    p1 = np.array((0.0, 0.15, -0.05))
    p2 = np.array((0.0, 0.15, 0.11))
    rot_start = np.array((-90.0, -14.88, 4.01))

    for i in range(n_f):
        t = i / max(n_f - 1, 1)
        pos = qbez(t, p0, p1, p2)
        rot_deg = rot_start + t * (rot_ext - rot_start)
        rot_deg += np.random.uniform(-rot_rnd, rot_rnd)

        f_obj = create_feather_mesh(f"tail_f_{i}", f_l, f_r1, f_r2)
        f_obj.location = tuple(pos)
        f_obj.rotation_euler = tuple(np.radians(rot_deg))
        apply_tf(f_obj)
        parts.append(f_obj)

        f_mir = create_feather_mesh(f"tail_fm_{i}", f_l, f_r1, f_r2)
        f_mir.location = (pos[0], -pos[1], pos[2])
        f_mir.rotation_euler = tuple(np.radians(rot_deg * np.array((1.0, -1.0, -1.0))))
        apply_tf(f_mir)
        parts.append(f_mir)

    result = join_objs(parts)
    add_solidify(result, thickness=0.008, offset=0.0)
    result.name = "tail"
    return result, tail_skel

# ---------------------------------------------------------------------------
# Leg  (nodegroup_bird_leg: tube + thigh + shin muscles)
# ---------------------------------------------------------------------------

def create_leg(body_length, side=1):
    """

    BirdLeg:
      tube: length=body_length*0.5, rad1=0.09, rad2=0.06, angles=(-70,90,-2),
            fullness=8
      thigh muscle: tube at coords 0->0.2->0.4 of leg skeleton, rad 0.18->0.10
      shin  muscle: tube at coords 0.32->0.5->0.74, rad 0.07->0.06
    """

    leg_len = body_length * 0.5 * N(1, 0.05)
    r1 = 0.09 * N(1, 0.1)
    r2 = 0.06 * N(1, 0.1)

    leg_obj, leg_skel = create_tube_mesh(
        f"leg_{side}", leg_len, r1, r2,
        angles_deg=(-70.0, 90.0, -2.0), fullness=8.0 * N(1, 0.1),
        n_skel=20, n_profile=12)

    parts = [leg_obj]

    def skel_point(t):
        return lerp_sample(leg_skel, np.array([t * (len(leg_skel) - 1)]))[0]

    # Thigh muscle: original surface_muscle wraps from (0,0,0) to (0.4,pi/2,1)
    # along the leg, starting on top and curving to the side.
    # Radii from BirdLeg.sample_params: (0.18, 0.10, 1.26) * N(1, 0.1, 3)
    thigh_rf = np.array((0.18, 0.10, 1.26)) * N(1, 0.1, 3)
    thigh_mr1, thigh_mr2, thigh_full = thigh_rf
    n_muscle_pts = 8
    thigh_ts = np.linspace(0.0, 0.4, n_muscle_pts)
    thigh_skel = np.array([skel_point(t) for t in thigh_ts])
    tangents = skeleton_to_tangents(leg_skel)
    for i, t in enumerate(thigh_ts):
        idx = t * (len(leg_skel) - 1)
        tang = lerp_sample(tangents, np.array([idx]))[0]
        tang_n = tang / max(np.linalg.norm(tang), 1e-8)
        perp = np.cross(tang_n, np.array([0, 1, 0]))
        perp_n = perp / max(np.linalg.norm(perp), 1e-8)
        blend = t / 0.4
        thigh_skel[i] += perp_n * r1 * (0.2 + 0.6 * blend)
    tm_obj = _build_tube_from_skeleton(
        f"thigh_m_{side}", thigh_skel, thigh_mr1, thigh_mr2,
        fullness=thigh_full, aspect=0.72, n_profile=10)
    parts.append(tm_obj)

    # Shin muscle: original coords (0.32,0,0) to (0.74,1.32,0.29)
    # Radii from BirdLeg.sample_params: (0.07, 0.06, 5.0) * N(1, 0.1, 3)
    shin_rf = np.array((0.07, 0.06, 5.0)) * N(1, 0.1, 3)
    shin_mr1, shin_mr2, shin_full = shin_rf
    shin_ts = np.linspace(0.32, 0.74, n_muscle_pts)
    shin_skel = np.array([skel_point(t) for t in shin_ts])
    for i, t in enumerate(shin_ts):
        idx = t * (len(leg_skel) - 1)
        tang = lerp_sample(tangents, np.array([idx]))[0]
        tang_n = tang / max(np.linalg.norm(tang), 1e-8)
        perp = np.cross(tang_n, np.array([0, 1, 0]))
        perp_n = perp / max(np.linalg.norm(perp), 1e-8)
        blend = (t - 0.32) / 0.42
        shin_skel[i] += perp_n * r1 * (0.1 + 0.3 * blend)
    sm_obj = _build_tube_from_skeleton(
        f"shin_m_{side}", shin_skel, shin_mr1, shin_mr2,
        fullness=shin_full, aspect=0.72, n_profile=10)
    parts.append(sm_obj)

    result = join_objs(parts)
    result.name = f"leg_{side}"
    return result, leg_skel

# ---------------------------------------------------------------------------
# Foot  (nodegroup_foot + nodegroup_tiger_toe)
# ---------------------------------------------------------------------------

def create_tiger_toe(name, toe_len, toe_r1, toe_r2,
                     toebean_r, curl_scalar,
                     claw_pct_lrr):
    """

    nodegroup_tiger_toe: toe tube + toebean spheres + claw.
    curl_scalar: 0.34 for duck
    """
    # Toe angles: (-50,25,35) * curl_scalar
    curl = np.array([-50.0, 25.0, 35.0]) * curl_scalar

    toe_obj, toe_skel = create_tube_mesh(
        name + "_toe", toe_len * 0.54, toe_r1, toe_r2,
        angles_deg=curl, n_skel=15, n_profile=8,
        origin=(-0.05, 0, 0))
    add_subsurf(toe_obj, levels=1)

    parts = [toe_obj]

    def skel_pt(t):
        return lerp_sample(toe_skel, np.array([t * (len(toe_skel) - 1)]))[0]

    # Toebean pads -- smaller than toe radius for subtle bumps (not dominating)
    bean_r = min(toebean_r, toe_r1 * 0.7)  # cap at 70% of toe radius
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=bean_r)
    bean1 = bpy.context.active_object
    bean1.scale = (1.3, 0.8, 0.5)   # flatter pad shape
    bean1.location = tuple(skel_pt(0.45))
    apply_tf(bean1)
    parts.append(bean1)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=bean_r * 0.7)
    bean2 = bpy.context.active_object
    bean2.scale = (1.0, 0.7, 0.5)
    bean2.location = tuple(skel_pt(0.75))
    apply_tf(bean2)
    parts.append(bean2)

    # Claw at toe tip -- connect from skeleton endpoint direction
    claw_len = claw_pct_lrr[0] * toe_len
    claw_r1  = claw_pct_lrr[1] * toe_r1
    claw_r2  = max(claw_pct_lrr[2] * toe_r1, 0.002)  # minimum tip radius to avoid spikes
    claw_ang = np.array([1.0, -2.0, -1.0]) * 12.0

    claw_origin = skel_pt(0.90)   # start claw near toe tip
    claw_obj, _ = create_tube_mesh(
        name + "_claw", claw_len, claw_r1, claw_r2,
        angles_deg=claw_ang, fullness=4.0, n_skel=8, n_profile=6,
        origin=tuple(claw_origin))
    parts.append(claw_obj)

    result = join_objs(parts)
    result.name = name
    return result, skel_pt(1.0)

def create_foot_legacy(body_length, side=1):
    """

    Foot: ankle stub + 4 toes (3 front + 1 hallux/thumb) with claws.
    Params from duck_genome (bird.py + foot.py).
    The 4-toe arrangement:
      Front 3 toes: fan from -splay to +splay in the horizontal XY plane.
      Hallux (toe 3): extends backward+slightly inward, shorter+thicker per duck_genome.
    """
    # Original duck_genome values (foot.py + bird.py duck_genome overrides)
    foot_lrr  = np.array([body_length * 0.1, 0.025, 0.04]) * N(1, 0.1) * N(1, 0.1, 3)
    toe_len   = body_length * max(0.1, N(0.4, 0.07))
    toe_lrr   = np.array([toe_len, 0.03, 0.02]) * N(1, 0.1) * N(1, 0.1, 3)
    toe_splay = math.radians(35.0 * N(1, 0.2))
    toebean_r = 0.03 * N(1, 0.1)
    curl_s    = 0.34 * N(1, 0.2)
    claw_pct  = np.array([0.13, 0.64, 0.05]) * N(1, 0.1) * N(1, 0.1, 3)
    # Hallux (thumb/rear toe): shorter (61%) and thicker (117%/150%) per duck_genome
    thumb_pct = np.array([0.61, 1.17, 1.50]) * N(1, 0.1) * N(1, 0.1, 3)

    # Foot base tube -- ankle stub pointing forward with a slight downward curve
    foot_obj, foot_skel = create_tube_mesh(
        f"foot_{side}", foot_lrr[0], foot_lrr[1], foot_lrr[2],
        angles_deg=(10, 8, -25), n_skel=10, n_profile=8)

    foot_end = foot_skel[-1]
    foot_parts = [foot_obj]

    # slightly in Y (across foot width) starting from behind the foot endpoint.
    # MeshLine: Start = endpoint + (-0.07, -0.45*rad2, -0.1*rad2)
    #           End   = endpoint + (-0.07, +0.45*rad2, +0.1*rad2)
    foot_rad2 = foot_lrr[2]
    y_spread = 0.45 * foot_rad2      # half-width of toe spread line
    z_spread = 0.10 * foot_rad2
    toe_base = foot_end + np.array([-0.07, 0, 0])  # slightly behind endpoint

    # Front 3 toes: spread along Y, fanned by splay angle
    for ti in range(3):
        t_frac  = ti / 2.0   # 0, 0.5, 1
        fan_ang = -toe_splay + t_frac * 2 * toe_splay

        # Offset each toe along the Y spread line
        y_off = -y_spread + t_frac * 2 * y_spread
        z_off = -z_spread + t_frac * 2 * z_spread
        toe_origin = toe_base + np.array([0, y_off, z_off])

        toe, _ = create_tiger_toe(
            f"toe_{side}_{ti}",
            toe_lrr[0], toe_lrr[1], toe_lrr[2],
            toebean_r, curl_s, claw_pct)

        toe.location = tuple(toe_origin)
        toe.rotation_euler = (0.0, -1.57, fan_ang)
        apply_tf(toe)
        foot_parts.append(toe)

    heel_r = 0.015 * (body_length / 1.5)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=heel_r)
    heel = bpy.context.active_object
    heel.name = f"heel_{side}"
    heel.scale = (0.7, 1.0, 0.8)
    heel.location = tuple(foot_end + np.array([-0.02, 0, 0]))
    apply_tf(heel)
    foot_parts.append(heel)

    # Hallux (toe 4, rear-facing): attached at ~30% along foot skeleton
    # with Length Fac = 0.3.
    def foot_skel_pt(t):
        return lerp_sample(foot_skel, np.array([t * (len(foot_skel) - 1)]))[0]

    hallux_pos = foot_skel_pt(0.35)  # 35% along foot = near ankle/heel
    thumb_lrr = toe_lrr * thumb_pct
    thumb, _ = create_tiger_toe(
        f"thumb_{side}",
        thumb_lrr[0], thumb_lrr[1], thumb_lrr[2],
        toebean_r, curl_s, claw_pct)

    thumb.location = tuple(hallux_pos)
    # pi = straight backward; +/-0.25 rad (approx 14 deg) inward offset per side
    hallux_ang = math.pi + 0.25 * (-1 if side > 0 else 1)
    thumb.rotation_euler = (0.0, -1.57, hallux_ang)
    apply_tf(thumb)
    foot_parts.append(thumb)

    result = join_objs(foot_parts)
    result.name = f"foot_{side}"
    return result

# ---------------------------------------------------------------------------
# Wrapper layer: assembly, attachment, and build_bird
# ---------------------------------------------------------------------------

def euler_deg(r, p, y):
    return Euler(np.deg2rad([r, p, y])).to_quaternion()

def quat_align_vecs(a, b):
    a = Vector(a)
    b = Vector(b)
    if a.length < 1e-8 or b.length < 1e-8:
        return Quaternion()
    a.normalize()
    b.normalize()
    axis = a.cross(b)
    if axis.length < 1e-8:
        if a.dot(b) > 0:
            return Quaternion()
        fallback = Vector((0.0, 1.0, 0.0))
        if abs(a.dot(fallback)) > 0.95:
            fallback = Vector((0.0, 0.0, 1.0))
        axis = a.cross(fallback)
        axis.normalize()
        return Quaternion(axis, math.pi)
    axis.normalize()
    return Quaternion(axis, a.angle(b))

def transform_points(points, matrix):
    return np.array([(matrix @ Vector(p))[:] for p in points], dtype=float)

def mesh_world_bounds(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    if eval_obj.type != "MESH":
        return None
    mesh = eval_obj.to_mesh()
    try:
        verts = np.array(
            [(eval_obj.matrix_world @ v.co)[:] for v in mesh.vertices], dtype=float
        )
    finally:
        eval_obj.to_mesh_clear()
    if len(verts) == 0:
        return None
    return verts.min(axis=0), verts.max(axis=0)

def tree_world_bounds(root):
    bounds = [mesh_world_bounds(o) for o in [root, *root.children_recursive] if o.type == "MESH"]
    bounds = [b for b in bounds if b is not None]
    if not bounds:
        return np.zeros(3), np.zeros(3)
    mins = np.stack([b[0] for b in bounds], axis=0)
    maxs = np.stack([b[1] for b in bounds], axis=0)
    return mins.min(axis=0), maxs.max(axis=0)

@dataclass
class PartState:
    obj: bpy.types.Object
    skeleton: np.ndarray
    side: int = 1
    label: str = ""
    _bvh: BVHTree | None = None

    def bvh(self):
        if self._bvh is None:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            self._bvh = BVHTree.FromObject(self.obj, depsgraph)
        return self._bvh

    def invalidate_bvh(self):
        self._bvh = None

    def apply_world_matrix(self, matrix, side=None):
        self.obj.matrix_world = matrix
        bpy.context.view_layer.update()
        self.skeleton = transform_points(self.skeleton, matrix)
        apply_tf(self.obj)
        self.invalidate_bvh()
        if side is not None:
            self.side = side

def raycast_surface(target: PartState, coord):
    u, v, r = map(float, coord)
    idx = np.array([u * max(len(target.skeleton) - 1, 0)], dtype=float)
    tangents = skeleton_to_tangents(target.skeleton)
    tangent = Vector(lerp_sample(tangents, idx).reshape(-1))
    if tangent.length < 1e-8:
        tangent = Vector((1.0, 0.0, 0.0))
    tangent.normalize()

    origin = Vector(lerp_sample(target.skeleton, idx).reshape(-1))
    dir_rot = euler_deg(180.0 * v, 0.0, 0.0) @ euler_deg(0.0, 90.0, 0.0)
    basis = quat_align_vecs((1.0, 0.0, 0.0), tangent)
    direction = basis @ (dir_rot @ Vector((1.0, 0.0, 0.0)))
    direction.normalize()

    location, normal, _, _ = target.bvh().ray_cast(origin, direction)
    if location is None:
        location = origin
        normal = basis @ Vector((0.0, 1.0, 0.0))
    if normal.length < 1e-8:
        normal = basis @ Vector((0.0, 1.0, 0.0))
    normal.normalize()
    location = origin.lerp(location, r)
    return location, normal, tangent

def attach_part(
    child: PartState,
    target: PartState,
    coord,
    rest=(0.0, 0.0, 0.0),
    rotation_basis="global",
    side=1,
):
    location, normal, tangent = raycast_surface(target, coord)

    if rotation_basis == "global":
        basis_rot = Quaternion()
    elif rotation_basis == "normal":
        basis_rot = quat_align_vecs((1.0, 0.0, 0.0), normal)
    elif rotation_basis == "tangent":
        basis_rot = quat_align_vecs((1.0, 0.0, 0.0), tangent)
    else:
        raise ValueError(f"Unsupported rotation_basis={rotation_basis}")

    rot = basis_rot @ euler_deg(*rest)
    child.obj.location = location
    child.obj.rotation_euler = rot.to_euler()
    bpy.context.view_layer.update()

    matrix = child.obj.matrix_world.copy()
    child_side = target.side * int(side)
    if child_side < 0:
        mirror = Matrix.Scale(-1.0, 4, (0.0, 1.0, 0.0))
        if target.side == 1:
            matrix = mirror @ matrix
        else:
            matrix = matrix @ mirror
    child.apply_world_matrix(matrix, side=child_side)
    return child

def translate_part(part: PartState, offset):
    offset = Vector(offset)
    part.apply_world_matrix(Matrix.Translation(offset) @ part.obj.matrix_world, side=part.side)
    return part

def center_object_on_ground(obj):
    mins, maxs = tree_world_bounds(obj)
    obj.location -= Vector(((mins[0] + maxs[0]) * 0.5, (mins[1] + maxs[1]) * 0.5, mins[2]))
    bpy.context.view_layer.update()
    return obj

def make_material(name, color, roughness=0.45, metallic=0.0):
    """Simple flat-color material (legacy helper, used only for foot/leg)."""

    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled is None:
        principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = (*color, 1.0)
    principled.inputs["Roughness"].default_value = roughness
    principled.inputs["Metallic"].default_value = metallic
    return mat

def assign_material(obj, material):
    if obj.data is None or not hasattr(obj.data, "materials"):
        return
    obj.data.materials.clear()
    obj.data.materials.append(material)

def random_convex_coord(names, select=None, temp=1.0):
    names = list(names)
    if isinstance(select, str):
        return {n: 1.0 if n == select else 0.0 for n in names}
    if isinstance(select, dict):
        total = float(sum(select.values()))
        return {k: float(v) / total for k, v in select.items()}
    if isinstance(temp, (float, int)):
        temp = np.full(len(names), float(temp))
    weights = np.random.dirichlet(temp)
    return {name: float(weights[i]) for i, name in enumerate(names)}

def linear_combination(corners, weights):
    first = corners[0]
    if isinstance(first, dict):
        return {
            key: linear_combination([corner[key] for corner in corners], weights)
            for key in first.keys()
        }
    return sum(corners[i] * weights[i] for i in range(len(corners)))

def rdict_comb(corners, weights):
    weights = dict(weights)
    norm = float(sum(weights.values()))
    for key in list(weights.keys()):
        weights[key] /= norm
    corners_list = [corners[key] for key in weights]
    weights_list = [weights[key] for key in weights]
    return linear_combination(corners_list, weights_list)

BEAK_DEFAULT = dict(
    n=20,
    m=20,
    r=1.0,
    sx=1.0,
    sy=1.0,
    sz=1.0,
    cy_a=1.0,
    cz_a=2.0,
    reverse=1,
    hook_a=0.1,
    hook_b=5.0,
    hook_scale_x=0.0,
    hook_pos_x=0.0,
    hook_thickness_x=0.0,
    hook_scale_z=0.0,
    hook_pos_z=0.0,
    hook_thickness_z=0.0,
    crown_scale_z=0.0,
    crown_a=0.5,
    crown_b=0.5,
    crown_pos_z=0.5,
    bump_scale_z=0.0,
    bump_l=0.5,
    bump_r=0.5,
    sharpness=0.0,
)

BEAK_SCALES = {
    "r": np.array([0.3, 1.0]),
    "sx": np.array([0.2, 1.0]),
    "sy": np.array([0.2, 1.0]),
    "sz": np.array([0.2, 1.0]),
    "cy_a": np.array([1.0, 10.0]),
    "cz_a": np.array([1.0, 5.0]),
    "hook_a": np.array([0.1, 0.8]),
    "hook_b": np.array([1.0, 5.0]),
    "hook_scale_x": np.array([-0.5, 0.5]),
    "hook_pos_x": np.array([0.5, 1.0]),
    "hook_thickness_x": np.array([0.0, 0.5]),
    "hook_scale_z": np.array([-0.5, 0.5]),
    "hook_pos_z": np.array([0.5, 1.0]),
    "hook_thickness_z": np.array([0.0, 0.5]),
    "crown_scale_z": np.array([0.0, 0.3]),
    "crown_a": np.array([0.1, 0.8]),
    "crown_b": np.array([0.0, 2.0]),
    "crown_pos_z": np.array([0.0, 0.5]),
    "bump_scale_z": np.array([0.0, 0.03]),
    "bump_l": np.array([0.0, 0.4]),
    "bump_r": np.array([0.6, 1.0]),
    "sharpness": np.array([-0.5, 0.5]),
}

EAGLE_UPPER = BEAK_DEFAULT | {
    "r": 0.4,
    "sx": 0.8,
    "sy": 0.4,
    "sz": 1.0,
    "hook_a": 0.1,
    "hook_b": 5.0,
    "hook_scale_x": -1.0,
    "hook_pos_x": 0.72,
    "hook_thickness_x": 0.35,
    "hook_scale_z": -0.8,
    "hook_pos_z": 0.7,
    "hook_thickness_z": 0.0,
}

EAGLE_LOWER = BEAK_DEFAULT | {
    "r": 0.4,
    "sx": 0.4,
    "sy": 0.4,
    "sz": 0.2,
    "reverse": -1,
    "hook_a": 0.1,
    "hook_b": 5.0,
    "hook_scale_x": 0.0,
    "hook_pos_x": 0.72,
    "hook_thickness_x": 0.35,
    "hook_scale_z": 0.1,
    "hook_pos_z": 0.6,
    "hook_thickness_z": -0.2,
}

NORMAL_UPPER = BEAK_DEFAULT | {
    "r": 0.4,
    "sx": 0.7,
    "sy": 0.3,
    "sz": 0.5,
    "hook_a": 0.1,
    "hook_b": 2.0,
    "hook_scale_x": 0.0,
    "hook_pos_x": 0.72,
    "hook_thickness_x": 0.35,
    "hook_scale_z": -0.8,
    "hook_pos_z": 0.7,
    "hook_thickness_z": 0.0,
}

NORMAL_LOWER = BEAK_DEFAULT | {
    "r": 0.4,
    "sx": 0.7,
    "sy": 0.3,
    "sz": 0.3,
    "reverse": -1,
    "hook_a": 0.1,
    "hook_b": 2.0,
    "hook_scale_x": 0.0,
    "hook_pos_x": 0.72,
    "hook_thickness_x": 0.35,
    "hook_scale_z": 0.8,
    "hook_pos_z": 0.7,
    "hook_thickness_z": 0.0,
}

DUCK_UPPER = BEAK_DEFAULT | {
    "n": 50,
    "r": 0.4,
    "sx": 1.0,
    "sy": 0.4,
    "sz": 0.5,
    "cy_a": 10.0,
    "hook_a": 0.1,
    "hook_b": 2.0,
    "hook_scale_x": -1.5,
    "hook_pos_x": 0.9,
    "hook_thickness_x": 0.0,
    "hook_scale_z": 0.4,
    "hook_pos_z": 0.6,
    "hook_thickness_z": 0.2,
    "crown_scale_z": 0.3,
    "crown_a": 0.1,
    "crown_b": 5.0,
    "crown_pos_z": 0.3,
    "bump_scale_z": 0.02,
    "bump_l": 0.4,
    "bump_r": 1.0,
    "sharpness": -0.5,
}

DUCK_LOWER = BEAK_DEFAULT | {
    "n": 50,
    "r": 0.4,
    "sx": 0.97,
    "sy": 0.4,
    "sz": 0.1,
    "cy_a": 10.0,
    "reverse": -1,
    "hook_a": 0.1,
    "hook_b": 2.0,
    "hook_scale_x": -1.5,
    "hook_pos_x": 0.9,
    "hook_thickness_x": 0.0,
    "hook_scale_z": -0.4,
    "hook_pos_z": 0.6,
    "hook_thickness_z": 0.0,
    "crown_scale_z": 0.1,
    "crown_a": 0.1,
    "crown_b": 5.0,
    "crown_pos_z": 0.3,
    "bump_scale_z": 0.03,
    "bump_l": 0.3,
    "bump_r": 1.0,
    "sharpness": -0.5,
}

SHORT_UPPER = BEAK_DEFAULT | {
    "r": 0.4,
    "sx": 0.25,
    "sy": 0.3,
    "sz": 0.3,
    "hook_a": 0.1,
    "hook_b": 2.0,
    "hook_scale_x": -0.5,
    "hook_pos_x": 0.8,
    "hook_thickness_x": 0.35,
    "hook_scale_z": -0.15,
    "hook_pos_z": 0.7,
    "hook_thickness_z": 0.0,
}

SHORT_LOWER = BEAK_DEFAULT | {
    "r": 0.4,
    "sx": 0.25,
    "sy": 0.3,
    "sz": 0.3,
    "cy_a": 1.0,
    "cz_a": 1.1,
    "reverse": -1,
    "hook_a": 0.1,
    "hook_b": 2.0,
    "hook_scale_x": -0.5,
    "hook_pos_x": 0.8,
    "hook_thickness_x": 0.35,
    "hook_scale_z": 0.15,
    "hook_pos_z": 0.7,
    "hook_thickness_z": 0.0,
}

BEAK_TEMPLATES = {
    "normal": {"upper": NORMAL_UPPER, "lower": NORMAL_LOWER, "range": BEAK_SCALES},
    "duck": {"upper": DUCK_UPPER, "lower": DUCK_LOWER, "range": BEAK_SCALES},
    "eagle": {"upper": EAGLE_UPPER, "lower": EAGLE_LOWER, "range": BEAK_SCALES},
    "short": {"upper": SHORT_UPPER, "lower": SHORT_LOWER, "range": BEAK_SCALES},
}

def sample_beak_params(select=None, var=1.0):
    weights = random_convex_coord(BEAK_TEMPLATES.keys(), select=select, temp=1.0)
    params = rdict_comb(BEAK_TEMPLATES, weights)

    def local_n(mean, width):
        return np.random.normal(mean, width * var)

    for key in params["upper"]:
        if key in params["range"]:
            low, high = params["range"][key]
            noise = local_n(0.0, 0.05 * (high - low))
            params["upper"][key] += noise
            params["lower"][key] += noise
            params["upper"][key] = float(np.clip(params["upper"][key], low, high))
            params["lower"][key] = float(np.clip(params["lower"][key], low, high))

    params["lower"]["sx"] = min(
        params["lower"]["sx"],
        params["upper"]["sx"]
        * (
            params["upper"]["hook_pos_x"]
            - params["upper"]["hook_thickness_x"] / 2.0
        ),
    )
    return params

def create_beak_part(select=None, head_length=0.35):
    params = sample_beak_params(select=select)
    beak_scale = 0.38 * (head_length / 0.35)
    objs = []
    for tmpl, name in ((params["upper"], "beak_upper"), (params["lower"], "beak_lower")):
        surf = BeakSurface(**tmpl)
        verts = surf.generate_verts(n_p=max(int(tmpl["n"]), 40), n_t=int(tmpl["m"]))
        edges, faces = compute_cylinder_topology(verts.shape[0], verts.shape[1])
        obj = new_mesh_obj(name, verts.reshape(-1, 3), edges, faces)
        add_subsurf(obj, levels=2)
        obj.scale = (beak_scale, beak_scale, beak_scale)
        apply_tf(obj)
        objs.append(obj)
    beak_obj = join_objs(objs)
    return PartState(beak_obj, np.zeros((1, 3), dtype=float), label="beak")

def tag_part(obj, role):
    obj["bird_role"] = role
    for child in obj.children_recursive:
        child["bird_role"] = role

def shade_smooth_all(root):
    for obj in [root, *root.children_recursive]:
        if obj.type != "MESH":
            continue
        sel(obj)
        bpy.ops.object.shade_smooth()

def build_bird(seed=0, beak_select=None, join_result=True):
    np.random.seed(seed)
    clear_scene()

    body_obj, body_length, body_skel = create_nurbs_body()
    body = PartState(body_obj, np.array(body_skel, dtype=float), label="body")
    tag_part(body.obj, "body")

    # Save geometry RNG state, create materials (which corrupt np.random),
    # then restore so subsequent geometry matches the shape-only version.
    _geom_rng_state = np.random.get_state()
    body_mat = make_body_material(seed, "BirdCodexBody")
    feather_mat = make_feather_material(seed, "BirdCodexFeather", tail=False)
    tail_mat = make_feather_material(seed, "BirdCodexTailFeather", tail=True)
    beak_mat = make_beak_material(seed, "BirdCodexBeak")
    eye_mat = make_eye_material(seed, "BirdCodexEye")
    claw_mat = make_claw_material(seed, "BirdCodexClaw")
    np.random.set_state(_geom_rng_state)

    assign_material(body.obj, body_mat)

    tail_obj, tail_skel = create_tail()
    tail = PartState(tail_obj, np.array(tail_skel, dtype=float), label="tail")
    tag_part(tail.obj, "tail")
    assign_material(tail.obj, tail_mat)
    attach_part(
        tail,
        body,
        coord=(0.2, 1.0, 0.5),
        rest=(0.0, 170.0 * N(1, 0.1), 0.0),
    )

    head_obj, head_skel, head_length = create_head()
    head = PartState(head_obj, np.array(head_skel, dtype=float), label="head")
    tag_part(head.obj, "head")
    assign_material(head.obj, body_mat)
    attach_part(head, body, coord=(1.0, 0.0, 0.0), rest=(0.0, 0.0, 0.0))

    beak = create_beak_part(select=beak_select, head_length=head_length)
    tag_part(beak.obj, "beak")
    assign_material(beak.obj, beak_mat)
    attach_part(beak, head, coord=(0.75, 0.0, 0.5), rest=(0.0, 0.0, 0.0))

    eye_radius = abs(N(0.03, 0.005))
    eye_t = np.random.uniform(0.6, 0.85)
    eye_splay = np.random.uniform(80.0, 110.0) / 180.0
    eye_r = 0.85
    eyes = []
    for side in (-1, 1):
        eye_state = PartState(create_eye(radius=max(0.01, eye_radius)), np.zeros((1, 3), dtype=float), label=f"eye_{side}")
        tag_part(eye_state.obj, "eye")
        assign_material(eye_state.obj, eye_mat)
        attach_part(
            eye_state,
            head,
            coord=(eye_t, eye_splay, eye_r),
            rest=(0.0, 0.0, 0.0),
            rotation_basis="normal",
            side=side,
        )
        eyes.append(eye_state)

    wing_coord = (N(0.7, 0.02), (110.0 / 180.0) * N(1, 0.1), 0.98)
    wing_rng = np.random.get_state()
    wings = []
    for side in (-1, 1):
        np.random.set_state(wing_rng)
        wing_obj, wing_skel, wing_ext = create_wing(body_length, side=side)
        wing = PartState(wing_obj, np.array(wing_skel, dtype=float), label=f"wing_{side}")
        tag_part(wing.obj, "wing")
        assign_material(wing.obj, feather_mat)
        rest = (90.0, 0.0, 90.0) if wing_ext > 0.5 else (90.0, 40.0, 90.0)
        attach_part(wing, body, coord=wing_coord, rest=rest, side=side)
        wings.append(wing)

    leg_fac_rng = np.random.get_state()
    foot_fac_rng = np.random.get_state()
    leg_coord = (N(0.5, 0.05), N(0.7, 0.05), N(0.95, 0.05))
    leg_attach_tangent = Vector(raycast_surface(body, leg_coord)[2]).normalized()
    leg_base_correction = -leg_attach_tangent * (0.055 * body_length)
    legs = []
    feet = []
    for side in (-1, 1):
        np.random.set_state(leg_fac_rng)
        leg_obj, leg_skel = create_leg(body_length, side=side)
        leg = PartState(leg_obj, np.array(leg_skel, dtype=float), label=f"leg_{side}")
        tag_part(leg.obj, "leg")
        assign_material(leg.obj, claw_mat)
        attach_part(
            leg,
            body,
            coord=leg_coord,
            rest=(0.0, 90.0, 0.0),
            side=side,
        )
        translate_part(
            leg,
            leg_base_correction + Vector((0.0, side * 0.02 * body_length, 0.0)),
        )
        legs.append(leg)

        np.random.set_state(foot_fac_rng)
        foot_obj = create_foot_legacy(body_length, side=side)
        foot = PartState(
            foot_obj,
            np.array([[0.0, 0.0, 0.0], [0.1, 0.0, 0.0]], dtype=float),
            label=f"foot_{side}",
        )
        foot.obj.name = f"foot_{side}"
        tag_part(foot.obj, "foot")
        assign_material(foot.obj, claw_mat)
        foot_anchor = lerp_sample(
            leg.skeleton, np.array([0.9 * (len(leg.skeleton) - 1)], dtype=float)
        ).reshape(-1)
        foot_matrix = (
            Matrix.Translation(Vector(foot_anchor))
            @ Matrix.Diagonal((1.1, float(side), 1.1, 1.0))
        )
        foot.apply_world_matrix(foot_matrix, side=side)
        feet.append(foot)

    parts = [body, tail, head, beak, *eyes, *wings, *legs, *feet]

    root = bpy.data.objects.new("BirdFactory_codex_root", None)
    bpy.context.scene.collection.objects.link(root)
    for part in parts:
        part.obj.parent = root

    shade_smooth_all(root)
    center_object_on_ground(root)

    if not join_result:
        return root, parts

    mesh_objs = [part.obj for part in parts if part.obj.type == "MESH"]
    for obj in mesh_objs:
        if obj.parent is not None:
            matrix = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = matrix
    bpy.context.view_layer.update()
    joined = join_objs(mesh_objs)
    joined.name = "BirdFactory_codex"
    shade_smooth_all(joined)
    mins, maxs = tree_world_bounds(joined)
    joined.location -= Vector(((mins[0] + maxs[0]) * 0.5, (mins[1] + maxs[1]) * 0.5, mins[2]))
    bpy.context.view_layer.update()
    if joined is not None and len(joined.data.materials) == 0:
        joined.data.materials.append(CREATURE_MAT)
    return joined, parts

def main(
    seed=DEFAULT_SEED,
    join_result=DEFAULT_JOIN_RESULT,
    beak_select=DEFAULT_BEAK_SELECT,
):
    result, _parts = build_bird(
        seed=seed,
        beak_select=beak_select,
        join_result=join_result,
    )
    mins, maxs = tree_world_bounds(result)
    return result

if __name__ == "__main__":
    main()
