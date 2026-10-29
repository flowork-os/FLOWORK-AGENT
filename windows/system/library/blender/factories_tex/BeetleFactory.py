# [FL_INDEX: keywords="blender_factory, procedural_3d, BeetleFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BeetleFactory | Category: factories_tex
# Prompt: A large beetle rendered as a textured 3D model. The creature has a broad, flat oval body with a dark brown to deep burgundy elytra (wing covers) featuring swirling organic patterns in vivid magenta-pink and dark crimson. The head is small and rounded with a prominent pair of large curved mandibles or horns projecting forward — dark reddish-brown with a slightly glossy surface. Six slender, articulated legs extend from beneath the body, each with pointed tips. The exoskeleton has a low surface roughness with subtle iridescence on the wing covers.

import os
#!/usr/bin/env python3

import hashlib
import math

import bpy
import mathutils
import numpy as np
from mathutils.bvhtree import BVHTree

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

def make_creature_material(seed, name="ChitinMaterial"):
    """Chitin exoskeleton: metallic with pointiness-driven edge highlights."""


    noise_w = float(np.random.uniform(-2, 2))
    chitin_color = _hsv2rgba(float(np.mod(np.random.normal(0.2, 0.4), 1)),
                              float(np.random.uniform(0, 1)),
                              float(np.random.uniform(0.05, 0.5)))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    geo = nt.nodes.new("ShaderNodeNewGeometry")

    # Pointiness -> edge highlight (3-stop ramp)
    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    ln(geo.outputs["Pointiness"], cr1.inputs["Fac"])
    cr1.color_ramp.elements.new(0)
    cr1.color_ramp.elements[0].position = 0.4091; cr1.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr1.color_ramp.elements[1].position = 0.4455; cr1.color_ramp.elements[1].color = (1, 1, 1, 1)
    cr1.color_ramp.elements[2].position = 0.5127; cr1.color_ramp.elements[2].color = (0, 0, 0, 1)

    cr10 = nt.nodes.new("ShaderNodeValToRGB")
    ln(cr1.outputs["Color"], cr10.inputs["Fac"])
    cr10.color_ramp.elements[0].position = 0.0; cr10.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr10.color_ramp.elements[1].position = 0.2273; cr10.color_ramp.elements[1].color = (1, 1, 1, 1)

    cr4 = nt.nodes.new("ShaderNodeValToRGB")
    ln(geo.outputs["Pointiness"], cr4.inputs["Fac"])
    cr4.color_ramp.elements[0].position = 0.4909; cr4.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr4.color_ramp.elements[1].position = 0.6773; cr4.color_ramp.elements[1].color = (1, 1, 1, 1)

    mul_edge = nt.nodes.new("ShaderNodeMath"); mul_edge.operation = "MULTIPLY"
    ln(cr10.outputs["Color"], mul_edge.inputs[0]); ln(cr4.outputs["Color"], mul_edge.inputs[1])

    cr3 = nt.nodes.new("ShaderNodeValToRGB"); cr3.color_ramp.interpolation = "EASE"
    ln(mul_edge.outputs[0], cr3.inputs["Fac"])
    cr3.color_ramp.elements[0].position = 0.0; cr3.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr3.color_ramp.elements[1].position = 0.0864; cr3.color_ramp.elements[1].color = (1, 1, 1, 1)

    # Diagonal mapping + noise for chitin pattern
    tc = nt.nodes.new("ShaderNodeTexCoord")
    map1 = nt.nodes.new("ShaderNodeMapping")
    ln(tc.outputs["Object"], map1.inputs["Vector"])
    map1.inputs["Rotation"].default_value = (0, 0, -0.7854)
    map1.inputs["Scale"].default_value = (1, 1, 0)
    sep1 = nt.nodes.new("ShaderNodeSeparateXYZ"); ln(map1.outputs["Vector"], sep1.inputs["Vector"])

    map2 = nt.nodes.new("ShaderNodeMapping")
    ln(tc.outputs["Object"], map2.inputs["Vector"])
    map2.inputs["Rotation"].default_value = (0, 0, 0.7854)
    map2.inputs["Scale"].default_value = (1, 10, 0)
    sep2 = nt.nodes.new("ShaderNodeSeparateXYZ"); ln(map2.outputs["Vector"], sep2.inputs["Vector"])

    sep_obj = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(tc.outputs["Object"], sep_obj.inputs["Vector"])
    sign = nt.nodes.new("ShaderNodeMath"); sign.operation = "SIGN"
    ln(sep_obj.outputs["X"], sign.inputs[0])

    mix_diag = nt.nodes.new("ShaderNodeMix"); mix_diag.data_type = "RGBA"
    ln(sign.outputs[0], mix_diag.inputs[0])
    ln(sep1.outputs["X"], mix_diag.inputs[6]); ln(sep2.outputs["X"], mix_diag.inputs[7])

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.inputs["Scale"].default_value = 10.0; noise1.inputs["Detail"].default_value = 10.0
    mix_n = nt.nodes.new("ShaderNodeMix"); mix_n.data_type = "RGBA"
    mix_n.inputs[0].default_value = 0.2
    ln(mix_diag.outputs[2], mix_n.inputs[6]); ln(_fac(noise1), mix_n.inputs[7])

    noise2 = nt.nodes.new("ShaderNodeTexNoise"); noise2.noise_dimensions = "4D"
    ln(mix_n.outputs[2], noise2.inputs["Vector"])
    noise2.inputs["W"].default_value = noise_w
    noise2.inputs["Scale"].default_value = 100.0
    noise2.inputs["Detail"].default_value = 10.0
    noise2.inputs["Roughness"].default_value = 0.0

    # mix_2: edge-darken the chitin base via cr3 (pointiness edge mask).
    # feeds mix_2(Fac=multiply_3, black, noise2) where multiply_3
    # reduces to cr3 in the absence of tag_body/tag_head/tag_leg attributes
    # (geometry in this standalone script does not write them, so they
    # default to 0 -- multiply_2 -> cr3*white = cr3, invert(tag_leg) -> white).
    mix_2 = nt.nodes.new("ShaderNodeMix"); mix_2.data_type = "RGBA"
    ln(cr3.outputs["Color"], mix_2.inputs[0])
    mix_2.inputs[6].default_value = (0.0, 0.0, 0.0, 1.0)
    ln(_fac(noise2), mix_2.inputs[7])

    # Color ramp for base color
    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    ln(mix_2.outputs[2], cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.0
    cr2.color_ramp.elements[0].color = (0.0068, 0, 0.0005, 1)
    cr2.color_ramp.elements[1].position = 0.9955
    cr2.color_ramp.elements[1].color = chitin_color

    # Roughness from edge highlight
    inv = nt.nodes.new("ShaderNodeInvert")
    ln(cr3.outputs["Color"], inv.inputs["Color"])
    cr11 = nt.nodes.new("ShaderNodeValToRGB")
    ln(inv.outputs["Color"], cr11.inputs["Fac"])
    cr11.color_ramp.elements[0].position = 0.3932; cr11.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr11.color_ramp.elements[1].position = 1.0; cr11.color_ramp.elements[1].color = (0.51, 0.51, 0.51, 1)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    try:
        bsdf.subsurface_method = "BURLEY"
    except Exception:
        pass
    ln(cr2.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.7
    ln(cr11.outputs["Color"], bsdf.inputs["Roughness"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

CREATURE_MAT = make_creature_material(SEED, "BeetleFactory_Material")

def md5_hash(x):
    if isinstance(x, (tuple, list)):
        m = hashlib.md5()
        for s in x:
            m.update(str(s).encode("utf-8"))
        return m
    return hashlib.md5(str(x).encode("utf-8"))

def int_hash(x, max_val=(2**32 - 1)):
    return abs(int(md5_hash(x).hexdigest(), 16)) % max_val

# NURBS DATA -- decoded control point arrays

NURBS_DATA = {
    "body_insect_tarantula": np.array([
        [
            [-0.06,  0.00,  0.17],
            [-0.06,  0.00,  0.17],
            [-0.06,  0.00,  0.17],
            [-0.06, -0.00,  0.17],
            [-0.06, -0.00,  0.17],
            [-0.06, -0.00,  0.17],
            [-0.06, -0.00,  0.17],
            [-0.06, -0.00,  0.17],
        ],
        [
            [-0.06,  0.10,  0.13],
            [-0.06,  0.13,  0.17],
            [-0.06,  0.10,  0.24],
            [-0.06, -0.00,  0.24],
            [-0.06, -0.10,  0.24],
            [-0.06, -0.13,  0.17],
            [-0.06, -0.10,  0.13],
            [-0.06, -0.00,  0.10],
        ],
        [
            [ 0.16,  0.16,  0.09],
            [ 0.16,  0.23,  0.17],
            [ 0.15,  0.19,  0.34],
            [ 0.16,  0.00,  0.37],
            [ 0.15, -0.19,  0.34],
            [ 0.16, -0.23,  0.17],
            [ 0.16, -0.16,  0.09],
            [ 0.16,  0.00,  0.09],
        ],
        [
            [ 0.37,  0.14,  0.07],
            [ 0.38,  0.17,  0.19],
            [ 0.39,  0.14,  0.28],
            [ 0.41,  0.00,  0.31],
            [ 0.39, -0.13,  0.28],
            [ 0.39, -0.16,  0.19],
            [ 0.38, -0.13,  0.07],
            [ 0.37,  0.00,  0.06],
        ],
        [
            [ 0.43,  0.09,  0.11],
            [ 0.43,  0.09,  0.15],
            [ 0.43,  0.09,  0.19],
            [ 0.43, -0.00,  0.19],
            [ 0.43, -0.09,  0.19],
            [ 0.43, -0.09,  0.15],
            [ 0.43, -0.09,  0.11],
            [ 0.43, -0.00,  0.11],
        ],
        [
            [ 0.44,  0.12,  0.10],
            [ 0.44,  0.13,  0.15],
            [ 0.45,  0.11,  0.21],
            [ 0.45,  0.00,  0.22],
            [ 0.45, -0.10,  0.21],
            [ 0.44, -0.13,  0.15],
            [ 0.44, -0.12,  0.10],
            [ 0.44, -0.00,  0.09],
        ],
        [
            [ 0.55,  0.14,  0.08],
            [ 0.56,  0.20,  0.12],
            [ 0.57,  0.14,  0.24],
            [ 0.57,  0.00,  0.25],
            [ 0.57, -0.14,  0.24],
            [ 0.56, -0.19,  0.12],
            [ 0.55, -0.14,  0.08],
            [ 0.55,  0.00,  0.07],
        ],
        [
            [ 0.71,  0.10,  0.09],
            [ 0.72,  0.14,  0.10],
            [ 0.72,  0.10,  0.18],
            [ 0.72,  0.00,  0.19],
            [ 0.72, -0.10,  0.18],
            [ 0.72, -0.13,  0.10],
            [ 0.71, -0.10,  0.09],
            [ 0.71,  0.00,  0.08],
        ],
        [
            [ 0.72,  0.00,  0.14],
            [ 0.72,  0.00,  0.14],
            [ 0.72,  0.00,  0.14],
            [ 0.72,  0.00,  0.14],
            [ 0.72,  0.00,  0.14],
            [ 0.72,  0.00,  0.14],
            [ 0.72,  0.00,  0.14],
            [ 0.72,  0.00,  0.14],
        ],
    ]),
    "body_insect_beetle": np.array([
        [
            [ 0.00,  0.00, -0.04],
            [ 0.00,  0.00, -0.04],
            [ 0.00,  0.00, -0.04],
            [ 0.00,  0.00, -0.04],
            [ 0.00,  0.00, -0.04],
            [ 0.00,  0.00, -0.04],
            [ 0.00,  0.00, -0.04],
            [ 0.00,  0.00, -0.04],
        ],
        [
            [ 0.01,  0.31, -0.03],
            [ 0.01,  0.35, -0.02],
            [ 0.01,  0.21,  0.10],
            [ 0.01,  0.00,  0.03],
            [ 0.01, -0.21,  0.10],
            [ 0.01, -0.35, -0.02],
            [ 0.01, -0.31, -0.03],
            [ 0.01,  0.00, -0.17],
        ],
        [
            [ 0.57,  0.33, -0.11],
            [ 0.57,  0.37, -0.07],
            [ 0.57,  0.21,  0.25],
            [ 0.57,  0.00,  0.09],
            [ 0.57, -0.21,  0.25],
            [ 0.57, -0.37, -0.07],
            [ 0.57, -0.33, -0.11],
            [ 0.57,  0.00, -0.19],
        ],
        [
            [ 1.03,  0.41, -0.16],
            [ 1.03,  0.45, -0.13],
            [ 0.97,  0.21,  0.20],
            [ 0.97,  0.00,  0.09],
            [ 0.97, -0.21,  0.20],
            [ 1.03, -0.45, -0.13],
            [ 1.03, -0.41, -0.16],
            [ 0.97,  0.00, -0.19],
        ],
        [
            [ 1.01,  0.16, -0.12],
            [ 1.01,  0.16, -0.07],
            [ 1.01,  0.09,  0.05],
            [ 1.01,  0.00, -0.00],
            [ 1.01, -0.09,  0.05],
            [ 1.01, -0.16, -0.07],
            [ 1.01, -0.16, -0.12],
            [ 1.01,  0.00, -0.16],
        ],
        [
            [ 1.07,  0.34, -0.11],
            [ 1.03,  0.38, -0.08],
            [ 0.94,  0.21,  0.18],
            [ 0.98, -0.00,  0.07],
            [ 0.94, -0.21,  0.18],
            [ 1.03, -0.38, -0.08],
            [ 1.07, -0.34, -0.11],
            [ 1.04, -0.00, -0.20],
        ],
        [
            [ 1.21,  0.31, -0.07],
            [ 1.19,  0.35, -0.05],
            [ 1.13,  0.20,  0.20],
            [ 1.15,  0.00,  0.10],
            [ 1.13, -0.20,  0.20],
            [ 1.19, -0.35, -0.05],
            [ 1.21, -0.31, -0.07],
            [ 1.20,  0.00, -0.17],
        ],
        [
            [ 1.43,  0.31, -0.03],
            [ 1.40,  0.35, -0.01],
            [ 1.35,  0.20,  0.24],
            [ 1.32,  0.00,  0.14],
            [ 1.35, -0.20,  0.24],
            [ 1.40, -0.35, -0.01],
            [ 1.43, -0.31, -0.03],
            [ 1.36,  0.00, -0.13],
        ],
        [
            [ 1.34,  0.00,  0.04],
            [ 1.34,  0.00,  0.04],
            [ 1.34,  0.00,  0.04],
            [ 1.34,  0.00,  0.04],
            [ 1.34, -0.00,  0.04],
            [ 1.34, -0.00,  0.04],
            [ 1.34, -0.00,  0.04],
            [ 1.34,  0.00,  0.04],
        ],
    ]),
    "body_insect_bee": np.array([
        [
            [-0.00,  0.00, -0.00],
            [-0.00,  0.00, -0.00],
            [-0.00,  0.00, -0.00],
            [-0.00, -0.00, -0.00],
            [-0.00, -0.00, -0.00],
            [-0.00, -0.00, -0.00],
            [-0.00, -0.00, -0.00],
            [-0.00, -0.00, -0.00],
        ],
        [
            [ 0.04,  0.07, -0.05],
            [-0.00,  0.09, -0.00],
            [-0.03,  0.07,  0.05],
            [-0.04, -0.00,  0.08],
            [-0.03, -0.07,  0.05],
            [-0.00, -0.09, -0.00],
            [ 0.04, -0.07, -0.05],
            [ 0.04, -0.00, -0.08],
        ],
        [
            [ 0.23,  0.12, -0.00],
            [ 0.17,  0.17,  0.09],
            [ 0.11,  0.14,  0.22],
            [ 0.11, -0.00,  0.25],
            [ 0.11, -0.14,  0.22],
            [ 0.17, -0.17,  0.09],
            [ 0.23, -0.12, -0.00],
            [ 0.23, -0.00, -0.07],
        ],
        [
            [ 0.38,  0.13,  0.01],
            [ 0.38,  0.17,  0.16],
            [ 0.36,  0.12,  0.27],
            [ 0.38, -0.00,  0.32],
            [ 0.36, -0.12,  0.27],
            [ 0.38, -0.17,  0.16],
            [ 0.38, -0.13,  0.01],
            [ 0.38, -0.00, -0.01],
        ],
        [
            [ 0.43,  0.09,  0.10],
            [ 0.43,  0.09,  0.16],
            [ 0.43,  0.09,  0.23],
            [ 0.43, -0.00,  0.23],
            [ 0.43, -0.09,  0.23],
            [ 0.43, -0.09,  0.16],
            [ 0.43, -0.09,  0.10],
            [ 0.43, -0.00,  0.10],
        ],
        [
            [ 0.44,  0.12,  0.08],
            [ 0.44,  0.13,  0.17],
            [ 0.45,  0.11,  0.26],
            [ 0.45,  0.00,  0.28],
            [ 0.45, -0.10,  0.26],
            [ 0.44, -0.13,  0.17],
            [ 0.44, -0.12,  0.08],
            [ 0.44, -0.00,  0.06],
        ],
        [
            [ 0.55,  0.14,  0.04],
            [ 0.56,  0.18,  0.16],
            [ 0.57,  0.14,  0.28],
            [ 0.57,  0.00,  0.31],
            [ 0.57, -0.14,  0.28],
            [ 0.56, -0.17,  0.16],
            [ 0.55, -0.14,  0.04],
            [ 0.55,  0.00,  0.01],
        ],
        [
            [ 0.71,  0.10,  0.07],
            [ 0.72,  0.12,  0.16],
            [ 0.73,  0.10,  0.24],
            [ 0.73,  0.00,  0.26],
            [ 0.73, -0.10,  0.24],
            [ 0.72, -0.12,  0.16],
            [ 0.71, -0.10,  0.07],
            [ 0.71,  0.00,  0.05],
        ],
        [
            [ 0.72,  0.00,  0.15],
            [ 0.72,  0.00,  0.16],
            [ 0.72,  0.00,  0.16],
            [ 0.72,  0.00,  0.16],
            [ 0.72,  0.00,  0.16],
            [ 0.72,  0.00,  0.16],
            [ 0.72,  0.00,  0.15],
            [ 0.72,  0.00,  0.15],
        ],
    ]),
    "head_insect_wasp": np.array([
        [
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
            [-0.07,  0.01,  0.09],
        ],
        [
            [-0.07,  0.10, -0.00],
            [-0.07,  0.13,  0.06],
            [-0.07,  0.13,  0.10],
            [-0.07,  0.11,  0.14],
            [-0.07,  0.06,  0.18],
            [-0.07,  0.01,  0.18],
            [-0.07, -0.05,  0.18],
            [-0.07, -0.10,  0.15],
            [-0.07, -0.11,  0.10],
            [-0.07, -0.12,  0.06],
            [-0.07, -0.08,  0.02],
            [-0.07,  0.01, -0.03],
        ],
        [
            [-0.00,  0.12, -0.03],
            [-0.00,  0.17,  0.05],
            [-0.01,  0.16,  0.10],
            [-0.00,  0.14,  0.16],
            [-0.00,  0.08,  0.21],
            [-0.00,  0.01,  0.21],
            [-0.00, -0.07,  0.21],
            [-0.00, -0.13,  0.17],
            [-0.01, -0.15,  0.10],
            [-0.00, -0.16,  0.05],
            [-0.00, -0.11,  0.00],
            [-0.00,  0.01, -0.07],
        ],
        [
            [ 0.08,  0.13, -0.03],
            [ 0.08,  0.18,  0.05],
            [ 0.08,  0.17,  0.11],
            [ 0.08,  0.15,  0.17],
            [ 0.08,  0.08,  0.21],
            [ 0.08,  0.01,  0.21],
            [ 0.08, -0.08,  0.21],
            [ 0.08, -0.14,  0.17],
            [ 0.08, -0.16,  0.11],
            [ 0.08, -0.17,  0.05],
            [ 0.08, -0.11,  0.00],
            [ 0.09,  0.01, -0.07],
        ],
        [
            [ 0.15,  0.12, -0.03],
            [ 0.15,  0.17,  0.05],
            [ 0.15,  0.16,  0.11],
            [ 0.15,  0.14,  0.16],
            [ 0.16,  0.08,  0.21],
            [ 0.16,  0.01,  0.21],
            [ 0.16, -0.07,  0.21],
            [ 0.15, -0.13,  0.17],
            [ 0.15, -0.15,  0.11],
            [ 0.15, -0.16,  0.05],
            [ 0.15, -0.11,  0.00],
            [ 0.14,  0.01, -0.07],
        ],
        [
            [ 0.21,  0.10, -0.02],
            [ 0.21,  0.14,  0.04],
            [ 0.22,  0.14,  0.10],
            [ 0.22,  0.12,  0.14],
            [ 0.22,  0.07,  0.18],
            [ 0.22,  0.00,  0.18],
            [ 0.22, -0.06,  0.18],
            [ 0.22, -0.11,  0.14],
            [ 0.22, -0.13,  0.10],
            [ 0.21, -0.14,  0.04],
            [ 0.21, -0.09,  0.01],
            [ 0.21,  0.00, -0.05],
        ],
        [
            [ 0.27,  0.08, -0.01],
            [ 0.27,  0.10,  0.04],
            [ 0.27,  0.10,  0.07],
            [ 0.28,  0.09,  0.11],
            [ 0.28,  0.05,  0.13],
            [ 0.29,  0.00,  0.13],
            [ 0.28, -0.04,  0.13],
            [ 0.28, -0.08,  0.11],
            [ 0.28, -0.10,  0.07],
            [ 0.27, -0.10,  0.04],
            [ 0.27, -0.07,  0.01],
            [ 0.26,  0.00, -0.03],
        ],
        [
            [ 0.35,  0.03,  0.02],
            [ 0.35,  0.04,  0.03],
            [ 0.35,  0.04,  0.04],
            [ 0.35,  0.04,  0.05],
            [ 0.35,  0.02,  0.06],
            [ 0.35,  0.01,  0.06],
            [ 0.35, -0.01,  0.06],
            [ 0.35, -0.01,  0.05],
            [ 0.35, -0.02,  0.04],
            [ 0.35, -0.02,  0.03],
            [ 0.35, -0.01,  0.02],
            [ 0.34,  0.01,  0.01],
        ],
        [
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
            [ 0.35,  0.01,  0.04],
        ],
    ]),
    "head_insect_beetle": np.array([
        [
            [-0.04,  0.01,  0.02],
            [-0.04,  0.01,  0.02],
            [-0.04,  0.01,  0.02],
            [-0.04,  0.01,  0.02],
            [-0.04,  0.01,  0.02],
            [-0.05,  0.00,  0.02],
            [-0.04,  0.00,  0.02],
            [-0.04,  0.00,  0.02],
            [-0.04,  0.00,  0.02],
            [-0.04,  0.00,  0.02],
            [-0.04,  0.00,  0.02],
            [-0.04,  0.00,  0.02],
        ],
        [
            [-0.02,  0.14, -0.04],
            [-0.02,  0.12, -0.02],
            [-0.04,  0.15,  0.02],
            [-0.05,  0.13,  0.05],
            [-0.05,  0.15,  0.06],
            [-0.06,  0.03,  0.13],
            [-0.05, -0.10,  0.06],
            [-0.05, -0.08,  0.05],
            [-0.04, -0.10,  0.02],
            [-0.02, -0.07, -0.02],
            [-0.02, -0.08, -0.04],
            [-0.02,  0.03, -0.05],
        ],
        [
            [ 0.06,  0.28, -0.10],
            [ 0.04,  0.24, -0.04],
            [ 0.01,  0.31,  0.04],
            [-0.03,  0.26,  0.11],
            [-0.03,  0.32,  0.15],
            [ 0.01,  0.01,  0.14],
            [-0.03, -0.31,  0.15],
            [-0.03, -0.25,  0.12],
            [ 0.01, -0.30,  0.04],
            [ 0.04, -0.24, -0.04],
            [ 0.06, -0.27, -0.10],
            [ 0.05,  0.01, -0.13],
        ],
        [
            [ 0.14,  0.28, -0.10],
            [ 0.13,  0.24, -0.04],
            [ 0.11,  0.31,  0.03],
            [ 0.07,  0.26,  0.10],
            [ 0.07,  0.32,  0.13],
            [ 0.17,  0.00,  0.14],
            [ 0.07, -0.31,  0.13],
            [ 0.07, -0.25,  0.10],
            [ 0.11, -0.30,  0.03],
            [ 0.13, -0.24, -0.04],
            [ 0.14, -0.27, -0.10],
            [ 0.13,  0.01, -0.12],
        ],
        [
            [ 0.20,  0.28, -0.10],
            [ 0.20,  0.24, -0.04],
            [ 0.19,  0.31,  0.03],
            [ 0.16,  0.26,  0.09],
            [ 0.16,  0.32,  0.12],
            [ 0.28,  0.00,  0.18],
            [ 0.16, -0.31,  0.12],
            [ 0.16, -0.25,  0.10],
            [ 0.19, -0.30,  0.03],
            [ 0.21, -0.24, -0.04],
            [ 0.20, -0.27, -0.10],
            [ 0.19,  0.01, -0.12],
        ],
        [
            [ 0.26,  0.28, -0.10],
            [ 0.26,  0.24, -0.04],
            [ 0.26,  0.31,  0.04],
            [ 0.25,  0.26,  0.10],
            [ 0.25,  0.32,  0.13],
            [ 0.37,  0.00,  0.21],
            [ 0.25, -0.31,  0.13],
            [ 0.25, -0.25,  0.10],
            [ 0.26, -0.30,  0.04],
            [ 0.26, -0.24, -0.04],
            [ 0.26, -0.27, -0.10],
            [ 0.25,  0.01, -0.12],
        ],
        [
            [ 0.33,  0.28, -0.10],
            [ 0.33,  0.24, -0.04],
            [ 0.33,  0.31,  0.05],
            [ 0.33,  0.26,  0.11],
            [ 0.33,  0.32,  0.14],
            [ 0.45,  0.00,  0.23],
            [ 0.33, -0.31,  0.14],
            [ 0.33, -0.25,  0.11],
            [ 0.33, -0.30,  0.05],
            [ 0.33, -0.24, -0.04],
            [ 0.33, -0.27, -0.10],
            [ 0.32,  0.01, -0.13],
        ],
        [
            [ 0.36,  0.13, -0.03],
            [ 0.34,  0.11, -0.01],
            [ 0.34,  0.14,  0.04],
            [ 0.34,  0.11,  0.06],
            [ 0.36,  0.14,  0.09],
            [ 0.40, -0.01,  0.12],
            [ 0.36, -0.16,  0.09],
            [ 0.34, -0.13,  0.07],
            [ 0.35, -0.16,  0.03],
            [ 0.34, -0.13, -0.01],
            [ 0.36, -0.14, -0.03],
            [ 0.35, -0.01, -0.05],
        ],
        [
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
            [ 0.35, -0.01,  0.03],
        ],
    ]),
}

def load_nurbs(name):
    return NURBS_DATA[name]

# MATH UTILITIES

def lerp(a, b, t):
    return (1.0 - t) * a + t * b

def lerp_sample(vec, ts):

    """Linearly sample array at fractional positions ts in [0, len-1]."""

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
    N = len(axi)
    eye = np.zeros((N, 3, 3))
    eye[:, [0, 1, 2], [0, 1, 2]] = 1.0
    th = angle[:, None, None]
    K = cross_matrix(axi)
    return eye + np.sin(th) * K + (1.0 - np.cos(th)) * (K @ K)

def rotate_match_directions(a, b):
    assert a.shape == b.shape
    axes = np.cross(a, b, axis=-1)
    m = np.linalg.norm(axes, axis=-1) > 1e-4
    rots = np.tile(np.eye(3), (len(a), 1, 1))
    if not m.any():
        return rots
    na = np.linalg.norm(a[m], axis=-1)
    nb = np.linalg.norm(b[m], axis=-1)
    dots = np.clip((a[m] * b[m]).sum(axis=-1) / (na * nb + 1e-12), -1.0, 1.0)
    rots[m] = rodrigues(np.arccos(dots), axes[m])
    return rots

def skeleton_to_tangents(skeleton):
    axes = np.empty_like(skeleton, dtype=np.float64)
    axes[-1] = skeleton[-1] - skeleton[-2]
    axes[:-1] = skeleton[1:] - skeleton[:-1]
    axes[1:-1] = (axes[1:-1] + axes[:-2]) / 2.0
    norm = np.linalg.norm(axes, axis=-1, keepdims=True)
    norm = np.maximum(norm, 1e-8)
    return axes / norm

def clip_gaussian(mean, std, lo, hi, max_tries=20):
    for _ in range(max_tries):
        v = np.random.normal(mean, std)
        if lo <= v <= hi:
            return v
    return float(np.clip(np.random.normal(mean, std), lo, hi))

def euler_quat(roll_deg, pitch_deg, yaw_deg):
    """Degrees -> quaternion.  Matches creature_util.euler(r, p, y)."""

    return mathutils.Euler(
        [math.radians(roll_deg), math.radians(pitch_deg), math.radians(yaw_deg)]
    ).to_quaternion()

def quat_align(a, b):
    """Quaternion rotating a -> b.  Matches creature.quat_align_vecs."""

    if not isinstance(a, mathutils.Vector):
        a = mathutils.Vector(a)
    if not isinstance(b, mathutils.Vector):
        b = mathutils.Vector(b)
    cross = a.cross(b)
    if cross.length < 1e-8:
        return mathutils.Quaternion()
    return mathutils.Quaternion(cross, a.angle(b))

def build_world_matrix(rot_quat, translation):


    """4x4 matrix = T(translation) @ R(rot_quat)."""

    M = rot_quat.to_matrix().to_4x4()
    M.translation = mathutils.Vector([float(x) for x in translation[:3]])
    return M

MIRROR_Y = mathutils.Matrix.Scale(-1, 4, (0, 1, 0))

# NURBS DECOMPOSE / RECOMPOSE
# Mirrors generic_nurbs.py + lofting.py exactly.

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

    return edges, faces

# BLENDER UTILITIES

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.node_groups):
        for item in list(coll):
            if item.users == 0:
                coll.remove(item)

def set_active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_tf(obj):
    set_active(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def create_mesh_obj(verts, edges, faces, name="mesh"):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), edges.tolist(), faces.tolist())
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def clean_mesh(obj, threshold=1e-4):
    set_active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=threshold)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

def shade_smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

def apply_subsurf(obj, levels=2):
    set_active(obj)
    mod = obj.modifiers.new("SUBSURF", "SUBSURF")
    mod.levels = levels
    mod.render_levels = levels
    bpy.ops.object.modifier_apply(modifier=mod.name)

# NURBS MESH BUILDER

def sample_nurbs_params(prefix, temperature=0.3, var=1):
    """Matches NurbsPart.sample_params() in generic_nurbs.py exactly."""
    # Key order must match original Path.iterdir() order (see _NURBS_RAW dict above)
    target_keys = [k for k in NURBS_DATA if k.startswith(prefix)]

    # Dirichlet weights (matches part_util.random_convex_coord with select=None)
    weights = np.random.dirichlet(np.full(len(target_keys), temperature))
    handles = sum(w * load_nurbs(k) for k, w in zip(target_keys, weights))

    p = decompose_nurbs_handles(handles)

    # Noise -- N(u, v, d=1) returns np.random.normal(u, v*var, d)
    def N(u, v, d=1):
        return np.random.normal(u, np.array(v) * var, d)

    sz = N(1, 0.1)
    p["length"] *= sz * N(1, 0.1)
    p["rads"] *= sz * N(1, 0.1) * N(1, 0.15, p["rads"].shape)
    p["proportions"] *= N(1, 0.15)

    ang_noise = N(0, 7, p["thetas"].shape)
    ang_noise -= ang_noise.mean()
    p["thetas"] += ang_noise

    n, m, _ = p["profiles_norm"].shape
    pn = N(1, 0.07, (1, m, 1)) * N(1, 0.15, (n, m, 1))
    pn[:, :m // 2 - 1] = pn[:, m // 2:-1][:, ::-1]  # symmetrise
    p["profiles_norm"] *= pn

    return p

def build_nurbs_mesh(params, name="nurbs_mesh", subsurf_levels=2):
    handles = recompose_nurbs_handles(params)
    n, m, _ = handles.shape
    verts = handles.reshape(-1, 3)
    edges, faces = compute_cylinder_topology(n, m, cyclic=True)
    obj = create_mesh_obj(verts, edges, faces, name)
    clean_mesh(obj, threshold=1e-3)
    shade_smooth(obj)
    if subsurf_levels > 0:
        apply_subsurf(obj, subsurf_levels)
    return obj

# INSECT LEG / MANDIBLE -- CurveToMesh pipeline (matches original GeoNodes)

def polar_bezier_skeleton(origin, angles_deg, seg_lengths,
                          resolution=25, do_bezier=False):
    """3-segment skeleton from CUMULATIVE polar angles.

    Matches nodegroup_polar_bezier + SubdivideCurve(Cuts=resolution).
    For do_bezier=False: linear subdivision (POLY curve), no smoothing.
    For do_bezier=True: cubic Bezier interpolation.
    """

    origin = np.asarray(origin, dtype=np.float64)
    a = np.deg2rad(np.asarray(angles_deg, dtype=np.float64))
    a0, a1, a2 = a[0], a[0] + a[1], a[0] + a[1] + a[2]

    def ptc(orig, angle, length):
        return orig + length * np.array([np.cos(angle), 0.0, np.sin(angle)])

    p0 = origin
    p1 = ptc(p0, a0, seg_lengths[0])
    p2 = ptc(p1, a1, seg_lengths[1])
    p3 = ptc(p2, a2, seg_lengths[2])

    if not do_bezier:
        # Linear subdivision -- matches SubdivideCurve(Cuts=resolution) on 3-edge POLY.
        # Each edge gets `resolution` cuts -> (resolution+1) sub-segments.
        # Total points: 3*(resolution+1) + 1
        pts = []
        n_sub = resolution + 1
        for i, (pa, pb) in enumerate([(p0, p1), (p1, p2), (p2, p3)]):
            for j in range(n_sub + 1):
                if j == 0 and i > 0:
                    continue
                pts.append(lerp(pa, pb, j / n_sub))
        return np.array(pts)
    else:
        # Cubic Bezier -- BezierSegment(Res=2) + SubdivideCurve(Cuts=resolution//2)
        # Original: BezierSegment gives 3 control points (2 segments),
        # SubdivideCurve(Cuts=resolution//2) -> 2*(resolution//2) + 3 = 27 pts
        n_pts = 2 * (resolution // 2) + 3
        ts = np.linspace(0.0, 1.0, n_pts)
        return (np.outer((1 - ts)**3, p0)
                + np.outer(3 * (1 - ts)**2 * ts, p1)
                + np.outer(3 * (1 - ts) * ts**2, p2)
                + np.outer(ts**3, p3))

def smooth_taper_radius(t_arr, rad1, rad2, fullness=4.0):
    """sin(πt)^(1/fullness) x lerp(rad1, rad2, t) -- matches GeoNodes smooth_taper."""

    t = np.clip(np.asarray(t_arr, dtype=np.float64), 0.0, 1.0)
    env = np.sin(np.pi * t) ** (1.0 / max(fullness, 1e-4))
    base = lerp(rad1, rad2, t)
    return env * base

def build_curve_tube(skeleton_pts, radii, n_profile=40, aspect=1.0,
                     fill_caps=True, name="tube"):
    """Build tube mesh using POLY curve + GeoNodes CurveToMesh.

    Matches the original profile_part pipeline:
      CurveCircle(n_profile) -> [optional Transform for aspect] ->
      SetCurveRadius(smooth_taper) -> CurveToMesh(Scale=radius, Fill Caps)
    """
    # Create POLY curve with per-point radii
    curve_data = bpy.data.curves.new(name + "_c", 'CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(skeleton_pts) - 1)
    for i, (pt, r) in enumerate(zip(skeleton_pts, radii)):
        spline.points[i].co = (float(pt[0]), float(pt[1]), float(pt[2]), 1.0)
        spline.points[i].radius = max(float(r), 0.0)

    curve_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(curve_obj)

    # GeoNodes modifier: CurveCircle -> CurveToMesh(Scale=radius)
    tree = bpy.data.node_groups.new(name + "_gn", 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = tree.nodes.new('NodeGroupInput')
    out = tree.nodes.new('NodeGroupOutput')

    # Profile circle (40 verts for main tubes, 24 for carapace)
    circle = tree.nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.inputs['Resolution'].default_value = n_profile
    circle.inputs['Radius'].default_value = 1.0

    if abs(aspect - 1.0) > 0.01:
        # Scale profile by aspect (matching original ProfileHeight on X axis)
        xform = tree.nodes.new('GeometryNodeTransform')
        xform.inputs['Scale'].default_value = (aspect, 1.0, 1.0)
        tree.links.new(circle.outputs['Curve'], xform.inputs['Geometry'])
        profile_out = xform.outputs['Geometry']
    else:
        profile_out = circle.outputs['Curve']

    # Read per-point radius from curve
    radius_node = tree.nodes.new('GeometryNodeInputRadius')

    # CurveToMesh -- Blender 5.0: Scale input replaces implicit curve radius
    c2m = tree.nodes.new('GeometryNodeCurveToMesh')
    tree.links.new(inp.outputs['Geometry'], c2m.inputs['Curve'])
    tree.links.new(profile_out, c2m.inputs['Profile Curve'])
    tree.links.new(radius_node.outputs['Radius'], c2m.inputs['Scale'])
    c2m.inputs['Fill Caps'].default_value = fill_caps

    tree.links.new(c2m.outputs['Mesh'], out.inputs['Geometry'])

    # Add modifier and evaluate via depsgraph (can't apply GeoNodes on curve)
    mod = curve_obj.modifiers.new("GN", 'NODES')
    mod.node_group = tree
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    new_mesh = bpy.data.meshes.new_from_object(eval_obj)

    # Create mesh object from evaluated result
    mesh_obj = bpy.data.objects.new(name, new_mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)

    # Smooth shading for organic appearance
    for p in mesh_obj.data.polygons:
        p.use_smooth = True

    # Cleanup curve object and node group
    bpy.data.objects.remove(curve_obj, do_unlink=True)
    bpy.data.node_groups.remove(tree)

    return mesh_obj

def build_insect_leg(length_rad1_rad2, angles_deg,
                     proportions=(0.2533, 0.3333, 0.1333),
                     fullness=4.0, aspect=1.0, do_bezier=False,
                     carapace_pct=0.0, spike_lrr=None,
                     resolution=25, n_profile=40, name="leg"):
    """Build an insect leg using the CurveToMesh pipeline.

    Matches nodegroup_insect_leg: main tube + surface_muscle carapace + spikes.
    """

    length = float(length_rad1_rad2[0])
    rad1 = float(length_rad1_rad2[1])
    rad2 = float(length_rad1_rad2[2])

    props = np.asarray(proportions, dtype=np.float64)
    props = props / props.sum()
    seg_lengths = props * length

    skeleton = polar_bezier_skeleton(
        origin=(0.0, 0.0, 0.0), angles_deg=angles_deg,
        seg_lengths=seg_lengths, resolution=resolution, do_bezier=do_bezier,
    )

    # SplineParameter.Factor for POLY = point_index / (n_points - 1)
    # This matches the original smooth_taper which uses SplineParameter.Factor
    n_pts = len(skeleton)
    t_arr = np.arange(n_pts, dtype=np.float64) / max(n_pts - 1, 1)
    radii = smooth_taper_radius(t_arr, rad1, rad2, fullness)

    # Build main tube
    main_tube = build_curve_tube(skeleton, radii, n_profile=n_profile,
                                 aspect=aspect, name=name)
    parts = [main_tube]

    # Surface muscle (carapace) -- separate overlapping tube over first 35%
    # Original: QuadraticBezier(Res=16) through 3 skeleton pts at (0, 0.01, 0.35)
    # StartRad = EndRad = rad1 * carapace_pct, Fullness=30, ProfileHeight=0.73
    if carapace_pct > 0.0:
        carapace_rad = carapace_pct * rad1
        n_carapace = max(int(0.35 * n_pts), 3)
        carapace_skel = skeleton[:n_carapace]
        carapace_t = np.arange(n_carapace, dtype=np.float64) / max(n_carapace - 1, 1)
        carapace_radii = smooth_taper_radius(
            carapace_t, carapace_rad, carapace_rad, fullness=30.0
        )
        carapace_tube = build_curve_tube(
            carapace_skel, carapace_radii, n_profile=24,
            aspect=0.73, name=name + "_car",
        )
        parts.append(carapace_tube)

    # Spikes -- 4 small tubes instanced along middle section (t=0.4892..0.725)
    # Original: TrimCurve(0.4892, 0.725) -> ResampleCurve(4) -> InstanceOnPoints
    # Rotation=(0, 0.1239, 0) is a FIXED euler (not tangent-aligned)
    if spike_lrr is not None and spike_lrr[0] > 0.001:
        spike_t_start = int(0.4892 * n_pts)
        spike_t_end = int(0.725 * n_pts)
        if spike_t_end > spike_t_start + 1:
            spike_indices = np.linspace(
                spike_t_start, spike_t_end, 4
            ).astype(int)
            spike_rot = mathutils.Euler((0.0, 0.1239, 0.0)).to_quaternion()
            for si, idx in enumerate(spike_indices):
                spike_pt = skeleton[idx]
                spike_obj = build_insect_leg(
                    spike_lrr, (0.0, -40.0, 0.0),
                    proportions=(0.333, 0.333, 0.333),
                    fullness=4.0, do_bezier=True,
                    name=f"{name}_sp{si}",
                )
                spike_obj.matrix_world = build_world_matrix(
                    spike_rot, spike_pt
                )
                apply_tf(spike_obj)
                parts.append(spike_obj)

    if len(parts) > 1:
        result = join_objs(parts)
        result.name = name
        return result
    return main_tube

def build_mandible(length_rad1_rad2, angles_deg, aspect=1.0, name="mandible"):
    return build_insect_leg(
        length_rad1_rad2, angles_deg,
        proportions=(0.333, 0.333, 0.333),
        fullness=4.0, aspect=aspect, do_bezier=True, name=name,
    )

# RAYCAST SURFACE -- matches creature.py::raycast_surface

def raycast_attach(skeleton, bvh, coord, obj_rot_quat=None):
    """Compute attachment location from coord=(u, v, r).
    u = position along skeleton [0,1]
    v = azimuthal angle [0,1]  (v=0 -> -Z, v=0.5 -> +Y)
    r = lerp(skeleton_center, surface_hit, r)

    Matches creature.py::raycast_surface + apply_attach_transform.
    """

    u, v, r = coord

    if obj_rot_quat is None:
        obj_rot_quat = mathutils.Quaternion()  # identity

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

# ASSEMBLY -- matches beetle_genome() + genome_to_creature()

def build_beetle():
    # Match original spawn_asset() which uses int_hash((factory_seed, idx))
    np.random.seed(int_hash((SEED, 0)))
    clear_scene()

    # ══ Random call order matches beetle_genome() exactly ══════════════════

    # 1. NurbsBody(prefix="body_insect", var=2).sample_params()
    body_params = sample_nurbs_params("body_insect", temperature=0.3, var=2)

    # 2. Proportions amplification (beetle_genome lines 74-78)
    if np.random.uniform() < 0.5:
        n = len(body_params["proportions"])
        noise = np.random.uniform(1, 3, n)
        noise[-n // 3:] = 1.0
        body_params["proportions"] *= noise

    body_length = np.sum(body_params["proportions"]).item() * np.asarray(body_params["length"]).item()

    # 3. InsectLeg().sample_params() -- shared factory, 10 random calls
    leg_lrr = np.array((1.0, 0.02, 0.01)) * np.random.normal(1, 0.25, 3)
    leg_angles = np.array((0.0, -63.9, 31.39)) + np.random.normal(0, 10, 3)
    carapace_pct = 1.4 * np.random.uniform(0.5, 2)
    _spikes = np.array((0.2, 0.025, 0.0)) * np.random.normal(1, (0.2, 0.1, 0.1), 3)

    n_leg_pairs = int(np.clip(body_length * clip_gaussian(3, 2, 2, 6), 2, 15))
    splay = np.random.uniform(30, 60)

    # 5. NurbsHead(prefix="head_insect", var=1).sample_params()
    head_params = sample_nurbs_params("head_insect", temperature=0.3, var=1)

    # 6. Mandible check + InsectMandible().sample_params() + joint rotation
    has_mandibles = np.random.uniform() < 0.7
    if has_mandibles:
        # InsectMandible.sample_params() -- 7 random calls
        mand_lrr = (1.1 * np.random.uniform(0.2, 1.0),
                    0.1 * np.random.normal(1, 0.2),
                    0.02 * np.random.normal(1, 0.1))
        mand_angles = np.array((-4.4, 58.22, 77.96)) * np.random.normal(1, 0.2, 3)
        mand_aspect = np.random.uniform(0.3, 1.0)
        # Joint rotation -- scalar broadcast, 1 random call
        mand_joint_rot = np.array((120.0, 20.0, 80.0)) * np.random.normal(1, 0.15)

    # ══ Build geometry ═════════════════════════════════════════════════════

    # Skeletons -- exclude first/last rings to match nurbs_to_part (skeleton[1:-1])
    body_skeleton = get_skeleton_from_params(body_params)[1:-1]
    head_skeleton = get_skeleton_from_params(head_params)[1:-1]

    # Build body and head meshes at origin (no subsurf yet -- apply after join per pipeline)
    body_obj = build_nurbs_mesh(body_params, name="body", subsurf_levels=0)
    head_obj = build_nurbs_mesh(head_params, name="head", subsurf_levels=0)

    # BVH trees for raycast attachment
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_bvh = BVHTree.FromObject(body_obj, depsgraph)
    head_bvh = BVHTree.FromObject(head_obj, depsgraph)

    # Head world transform: coord=(1,0,0) -> skeleton endpoint (body tip);
    # r=0 -> skeleton center (inside body mesh -> natural overlap); Joint=(0,-15,0) tilts head
    head_attach_pt, _ = raycast_attach(body_skeleton, body_bvh, (1.0, 0.0, 0.0))
    M_head = build_world_matrix(euler_quat(0.0, -15.0, 0.0), head_attach_pt)

    all_parts = [body_obj]

    # ── Legs ───────────────────────────────────────────────────────────────
    for t in np.linspace(0.15, 0.6, n_leg_pairs):
        # coord=(t, splay/180, 1) -> raycast to body surface at splay angle
        attach_pt, _ = raycast_attach(
            body_skeleton, body_bvh,
            (float(t), splay / 180.0, 1.0),
        )
        # Joint rotation: euler(xrot, 5, 90), rotation_basis="global"
        xrot = lerp(70.0, -100.0, float(t))
        M_right = build_world_matrix(euler_quat(xrot, 5.0, 90.0), attach_pt)

        for side in (1, -1):
            leg = build_insect_leg(
                leg_lrr.copy(), leg_angles.copy(),
                carapace_pct=carapace_pct,
                spike_lrr=_spikes.copy(),
                name=f"leg_{side}_{int(t * 100)}",
            )
            # side=1: identity, side=-1: Scale_Y(-1) mirrors in Y
            leg.matrix_world = M_right if side == 1 else MIRROR_Y @ M_right
            apply_tf(leg)
            all_parts.append(leg)

    # ── Mandibles (POSTORDER: head at origin during raycast) ───────────────
    if has_mandibles:
        # coord=(0.75, 0.5, 0.1): 75% along head, phi=0.5 -> +Y, r=0.1
        mand_loc, _ = raycast_attach(head_skeleton, head_bvh, (0.75, 0.5, 0.1))
        mand_rot_quat = euler_quat(*mand_joint_rot.tolist())

        for side in (1, -1):
            mand = build_mandible(
                mand_lrr, mand_angles, aspect=mand_aspect,
                name=f"mandible_{side}",
            )
            # M_mand_in_head = Scale_Y(side) @ T(mand_loc) @ R(mand_rot)
            M_local = build_world_matrix(mand_rot_quat, mand_loc)
            if side == -1:
                M_local = MIRROR_Y @ M_local
            # World = M_head @ M_local (head transform applied to head-local coords)
            mand.matrix_world = M_head @ M_local
            apply_tf(mand)
            all_parts.append(mand)

    # ── Position head ──────────────────────────────────────────────────────
    head_obj.matrix_world = M_head
    apply_tf(head_obj)
    all_parts.append(head_obj)

    # ── Join and finalise ──────────────────────────────────────────────────
    beetle = join_objs(all_parts)
    beetle.name = "BeetleFactory"

    # Post-processing -- matching joining.py pipeline:
    set_active(beetle)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    # SUBSURF after join (matches pipeline order)
    apply_subsurf(beetle, 1)

    # Voxel remesh -- matches adapt_mesh_resolution(face_size=0.015)
    # default is 0.07 but that's too coarse at this scale;
    # 0.015 provides good balance: merges overlapping tubes while preserving detail
    mod = beetle.modifiers.new("Remesh", "REMESH")
    mod.mode = 'VOXEL'
    mod.voxel_size = 0.03
    set_active(beetle)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    shade_smooth(beetle)

    # Set bottom at z=0
    verts = np.array([v.co for v in beetle.data.vertices])
    beetle.location.z = -verts[:, 2].min()
    apply_tf(beetle)

    return beetle

# ── Entry point ──────────────────────────────────────────────────────────────
beetle = build_beetle()
if beetle is not None and len(beetle.data.materials) == 0:
    beetle.data.materials.append(CREATURE_MAT)
verts = np.array([v.co for v in beetle.data.vertices])

