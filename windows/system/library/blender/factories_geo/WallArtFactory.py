# [FL_INDEX: keywords="blender_factory, procedural_3d, WallArtFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: WallArtFactory | Category: factories_geo
# Prompt: A 3D model of a framed wall art canvas rendered from a three-quarter perspective. The piece features a rectangular wooden frame surrounding a canvas panel with an abstract painted composition of irregular organic color patches in earthy greens, yellows, and browns against a light blue background.

"""WallArtFactory — textured standalone Blender script.

Geometry copied verbatim from objects_blender/wall_decorations/WallArtFactory.py
(canvas plane + extruded frame ring). Materials faithfully ported from:

Sampling order mirrors wall_art.py:WallArtFactory.assign_materials:
  1. surface_gen_class = weighted_sample(abstract_art)   (Art | DarkArt)
  2. surface_material_gen = surface_gen_class()           (__init__ consumes rng)
  3. surface = surface_material_gen()                     (generate -> material)
  4. frame_surface_gen_class = weighted_sample(frame)
  5. frame_surface_gen = frame_surface_gen_class()
  6. scratch gate (0.5)
  7. edge_wear gate (0.5)
same here after SAMPLING the class+instance on the raw seed.
"""
# SEED-deterministic: all random calls seeded from SEED
import os
import io
import math
import colorsys
import random
import inspect

import bmesh
import bpy
import numpy as np
from numpy.random import uniform, rand

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager
import matplotlib.pyplot as plt
from matplotlib.patches import (
    Arrow, BoxStyle, Circle, Ellipse, FancyBboxPatch,
    Rectangle, RegularPolygon, Wedge,
)
from PIL import Image

# ============================================================================
# Helper primitives (shared by all inlined shaders)
# ============================================================================

def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)

def _mat_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

_NATURAL_BASE_HSV = [
    (0.0,    0.0,    0.5271),  # 0xC0C0C0 silver
    (0.0961, 0.6702, 0.2623),  # 0x8C7853 khaki
    (0.1319, 0.1682, 0.5089),  # 0xBDBAAE light gray
    (0.6296, 0.1518, 0.4678),  # 0xA9ACB6 gray-blue
    (0.0749, 0.1518, 0.4678),  # 0xB6AFA9 gray-beige
]

def metal_natural_hsv():
    
    idx = np.random.randint(0, len(_NATURAL_BASE_HSV))
    h, s, v = _NATURAL_BASE_HSV[idx]
    return (
        h + float(np.random.uniform(-0.1, 0.1)),
        s + float(np.random.uniform(-0.1, 0.1)),
        v * float(_mat_log_uniform(0.2, 0.5)),
    )

def metal_hsv():
    
    if np.random.uniform() < 0.2:
        return metal_natural_hsv()
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            _mat_log_uniform(0.02, 0.5))

def bark_hsv():
    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e",
                "#6b4423", "#5d4037", "#7b3f00"]
    h = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)

def weighted_sample_mat(reg):
    classes, weights = zip(*reg)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]

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
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for n in names:
            if n in bsdf.inputs:
                bsdf.inputs[n].default_value = v
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

# ============================================================================
# ============================================================================

def make_brushed_metal(name="BrushedMetal", base_color_hsv=None):
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try: noise.noise_dimensions = "4D"
        except TypeError: pass
    noise.inputs["Scale"].default_value = 100.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:  noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 0.1
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(mapping_1.outputs["Vector"], noise.inputs["Vector"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.4
    map_range.inputs[2].default_value = 0.6
    map_range.inputs[3].default_value = 0.8
    map_range.inputs[4].default_value = 1.2
    nt.links.new(_noise_fac_output(noise), map_range.inputs[0])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    nt.links.new(map_range.outputs["Result"], hsv_node.inputs["Value"])

    map_range_r = nt.nodes.new("ShaderNodeMapRange")
    map_range_r.inputs[1].default_value = 0.4
    map_range_r.inputs[2].default_value = 0.6
    map_range_r.inputs[3].default_value = 0.2
    map_range_r.inputs[4].default_value = 0.3
    nt.links.new(_noise_fac_output(noise), map_range_r.inputs[0])

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
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
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
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
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
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0,
           "Base Color": hsv2rgba(base_color_hsv), "Roughness": 0.1},
    )
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ============================================================================
# ============================================================================

def make_wood(name="Wood", color=None):
    """MusgraveTexture (removed in Blender 5.0) is approximated by stretched
    multi-octave NoiseTexture. Color / curve / displacement logic preserved."""

    if color is None:
        h, s, v = bark_hsv()
        color = hsv2rgba((h + np.random.uniform(-0.0, 0.05),
                          max(0.0, s + np.random.uniform(-0.3, 0.2)),
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

# ============================================================================
# Art.__init__ overrides Text: n_barcodes=0, n_texts=0, n_patches=randint(10,15).
# DarkArt adds a DARKEN mix over the base shader color.
# ============================================================================

# Font setup (matches text.py font loading)
_FONT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "infinigen", "assets", "fonts",
)
if os.path.isdir(_FONT_DIR):
    for _f in matplotlib.font_manager.findSystemFonts([_FONT_DIR]):
        matplotlib.font_manager.fontManager.addfont(_f)
    _FONT_NAMES = [fn.replace("_", " ") for fn in os.listdir(_FONT_DIR)]
else:
    _FONT_NAMES = list(matplotlib.font_manager.get_font_names())[:10]

def _simple_decimate(points, n):
    if len(points) <= n:
        return points
    return points[np.random.permutation(len(points))[:n]]

def _random_general(var):
    
    if not isinstance(var, (tuple, list)):
        return var
    func, *args = var
    if func == "weighted_choice":
        weights, recargs = zip(*args)
        p = np.array(weights, dtype=float) / sum(weights)
        idx = int(np.random.choice(len(recargs), p=p))
        return _random_general(recargs[idx])
    return var

class AbstractArtBuilder:
    """Faithful port of text.py:Text specialised for Art (n_texts=0, n_barcodes=0,
    n_patches=randint(10,15))."""


    patch_fns = (
        "weighted_choice",
        (2, Circle),
        (4, Rectangle),
        (1, Wedge),
        (1, RegularPolygon),
        (1, Ellipse),
        (2, Arrow),
        (2, FancyBboxPatch),
    )
    hatches = {"/", "\\", "|", "-", "+", "x", "o", "O", ".", "*"}

    def __init__(self, darken=False):
        # --- Text.__init__ rng consumption order --------------------------
        self.size = 4
        self.dpi = 100
        self.colormap = (
            self._build_sequential_colormap()
            if uniform() < 0.5
            else self._build_diverging_colormap()
        )
        self.white_chance = 0.03
        self.black_chance = 0.05
        _unused_n_patches_text = np.random.randint(5, 8)
        self.force_horizontal = uniform() < 0.75
        _unused_n_texts_text = np.random.randint(2, 4)
        _unused_n_barcodes_flag = uniform()
        self.barcode_scale = float(uniform(0.3, 0.6))
        self.barcode_length = np.random.randint(25, 40)
        self.barcode_aspect = _mat_log_uniform(1.5, 3)
        self.emission = 0
        # --- Art.__init__ overrides ---------------------------------------
        self.n_barcodes = 0
        self.n_texts = 0
        self.n_patches = np.random.randint(10, 15)
        # --- DarkArt.__init__ --------------------------------------------
        self.darken = darken
        if darken:
            self.darken_scale = float(uniform(5, 10))
            self.darken_ratio = float(uniform(0.5, 1))
        # Shader-time params sampled here so matplotlib build_image
        # consumes rng in the same order as the original.
        # (These match the inline uniform() calls inside text.py:shader_text.)
        self.voronoi_distort_factor = None  # sampled after build_image
        self.uv_mix_factor = None
        self.metallic = None
        self.specular = None

    @staticmethod
    def _build_diverging_colormap():
        count = 20
        hue = (uniform() + np.linspace(0, 0.5, count)) % 1
        mid = uniform(0.6, 0.8)
        lightness = np.concatenate([
            np.linspace(uniform(0.1, 0.3), mid, count // 2),
            np.linspace(mid, uniform(0.1, 0.3), count // 2),
        ])
        saturation = np.concatenate([
            np.linspace(1, 0.5, count // 2),
            np.linspace(0.5, 1, count // 2),
        ])
        saturation *= uniform(0, 1)
        lightness *= uniform(0.5, 1)
        return np.array([
            colorsys.hls_to_rgb(h, l, s)
            for h, l, s in zip(hue, lightness, saturation)
        ])

    @staticmethod
    def _build_sequential_colormap():
        count = 20
        hue = (uniform() + np.linspace(0, 0.5, count)) % 1
        lightness = np.linspace(uniform(0.0), uniform(0.6, 0.8), count)
        saturation = np.concatenate([
            np.linspace(1, 0.5, count // 2),
            np.linspace(0.5, 1, count // 2),
        ])
        saturation *= uniform(0, 1)
        lightness *= uniform(0.5, 1)
        return np.array([
            colorsys.hls_to_rgb(h, l, s)
            for h, l, s in zip(hue, lightness, saturation)
        ])

    @property
    def random_color(self):
        r = uniform()
        if r < self.white_chance:
            return np.array([1, 1, 1])
        if r < self.white_chance + self.black_chance:
            return np.array([0, 0, 0])
        return self.colormap[np.random.randint(len(self.colormap))]

    @property
    def random_colors(self):
        while True:
            c, d = self.random_color, self.random_color
            if np.abs(c - d).sum() > 0.2:
                return c, d

    @staticmethod
    def _loc_uniform(lo, hi, size=None):
        ratio = 0.1
        return uniform(lo + ratio * (hi - lo), lo + (1 - ratio) * (hi - lo), size)

    @staticmethod
    def _scale_uniform(lo, hi):
        # Art.scale_uniform override: log_uniform(0.1, 0.5)
        return (hi - lo) * _mat_log_uniform(0.1, 0.5)

    def _get_locs(self, bbox, n):
        if n <= 0:
            return np.zeros((0, 2))
        m = 8 * n
        x = self._loc_uniform(bbox[0], bbox[1], m)
        y = self._loc_uniform(bbox[2], bbox[3], m)
        return _simple_decimate(np.stack([x, y], -1), n)

    def _add_divider(self, bbox):
        if uniform() < 0.6:
            return
        angle = 0 if uniform() < 0.7 else float(uniform(5, 10))
        x_pos = float(self._loc_uniform(bbox[0], bbox[1]))
        y_pos = float(self._loc_uniform(bbox[2], bbox[3]))
        if bbox[0] == 0 or self.force_horizontal:
            args_list = [
                [(0, y_pos), 2, 2, angle],
                [(0, y_pos), 2, -2, -angle],
                [(1, y_pos), -2, -2, angle],
                [(1, y_pos), -2, 2, -angle],
            ]
        else:
            args_list = [
                [(x_pos, 0), -2, 2, angle],
                [(x_pos, 0), 2, 2, -angle],
                [(x_pos, 1), 2, -2, angle],
                [(x_pos, 1), -2, -2, -angle],
            ]
        args = args_list[np.random.randint(len(args_list))]
        plt.gca().add_patch(
            Rectangle(*args[:-1], angle=args[-1], color=self.random_color)
        )

    def _add_patches(self, locs, bbox):
        for x, y in locs:
            w = self._scale_uniform(bbox[0], bbox[1])
            h = self._scale_uniform(bbox[2], bbox[3])
            x_, y_ = x - w / 2, y - h / 2
            r = min(w, h) / 2
            fn = _random_general(self.patch_fns)
            kwargs_all = {
                "alpha": float(uniform(0.5, 0.8)) if uniform() < 0.2 else 1,
                "fill": bool(uniform() < 0.2),
                "angle": 0 if uniform() < 0.8 else float(uniform(-30, 30)),
                "orientation": float(uniform(0, np.pi * 2)),
            }
            kwargs = {
                k: kwargs_all[k]
                for k in inspect.signature(fn).parameters
                if k in kwargs_all
            }
            face_color, edge_color = self.random_colors
            kwargs.update({
                "facecolor": face_color,
                "edgecolor": edge_color,
                "hatch": np.random.choice(list(self.hatches)) if uniform() < 0.3 else "none",
                "linewidth": float(uniform(2, 5)),
            })
            try:
                if fn.__name__ == "Circle":
                    patch = Circle((x, y), r, **kwargs)
                elif fn.__name__ == "Rectangle":
                    patch = Rectangle((x_, y_), w, h, **kwargs)
                elif fn.__name__ == "Wedge":
                    start = float(uniform(0, 360))
                    patch = Wedge((x, y), r, start, start + float(uniform(0, 360)),
                                  width=float(uniform(0.2, 0.8)) * r, **kwargs)
                elif fn.__name__ == "RegularPolygon":
                    patch = RegularPolygon((x, y), np.random.randint(3, 9), radius=r, **kwargs)
                elif fn.__name__ == "Ellipse":
                    patch = Ellipse((x, y), w, h, **kwargs)
                elif fn.__name__ == "Arrow":
                    w_ = w if uniform() < 0.5 else -w
                    h_ = h if uniform() < 0.5 else -h
                    patch = Arrow(x - w_ / 2, y - h_ / 2, w, h,
                                  width=_mat_log_uniform(0.6, 1.5), **kwargs)
                elif fn.__name__ == "FancyBboxPatch":
                    pad = float(uniform(0.2, 0.4)) * min(w, h)
                    box_style = np.random.choice(list(BoxStyle.get_styles().values()))(pad=pad)
                    patch = FancyBboxPatch(
                        (x_, y_), w - pad, h - pad, box_style,
                        mutation_scale=_mat_log_uniform(0.6, 1.5),
                        mutation_aspect=_mat_log_uniform(0.6, 1.5), **kwargs)
                else:
                    continue
                plt.gca().add_patch(patch)
            except (MemoryError, Exception) as e:
                print(f"  [art] patch {fn.__name__} failed: {e}")

    def build_image(self, bbox=(0, 1, 0, 1)):
        fig = plt.figure(figsize=(self.size, self.size), dpi=self.dpi)
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set_facecolor(self.random_color)
        total = self.n_patches + self.n_texts + self.n_barcodes
        locs = self._get_locs(bbox, total)
        self._add_divider(bbox)
        self._add_patches(locs[: self.n_patches], bbox)
        # n_texts = n_barcodes = 0 for Art — skipped
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        size = self.size * self.dpi
        image = bpy.data.images.new(
            "art_texture", width=size, height=size, alpha=True)
        data = np.asarray(Image.open(buffer), dtype=np.float32)[::-1, :] / 255.0
        image.pixels.foreach_set(data.ravel())
        image.pack()
        plt.close("all")
        try:
            plt.clf()
        except Exception:
            pass
        return image

def make_art_material(builder, name="Art"):
    """Raw-bpy translation of text.py:shader_text.

    Builds the matplotlib image first, then the shader graph.  Rng consumption
    source.  For DarkArt we add a DARKEN mix over the final image color.
    """

    image = builder.build_image(bbox=(0, 1, 0, 1))

    # Rng consumed inside shader_text (match order):
    #   mix_3 factor: uniform(0.2, 1.0)
    #   uv_or_not branch: rand() < 0.5
    #     if: mix_2 factor uniform(0, 0.4)   (else constant 1.0)
    #   metallic: uniform(0, 0.5)
    #   specular: uniform(0, 0.2)
    builder.voronoi_distort_factor = float(uniform(0.2, 1.0))
    if rand() < 0.5:
        builder.uv_mix_factor = float(uniform(0, 0.4))
    else:
        builder.uv_mix_factor = 1.0
    builder.metallic = float(uniform(0, 0.5))
    builder.specular = float(uniform(0, 0.2))

    mat = _new_material(name)
    nt = mat.node_tree

    uv_map = nt.nodes.new("ShaderNodeUVMap")
    uv_out = uv_map.outputs["UV"]

    voronoi_1 = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi_1.inputs["Scale"].default_value = 60.0
    nt.links.new(uv_out, voronoi_1.inputs["Vector"])

    voronoi_2 = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi_2.inputs["Scale"].default_value = 60.0
    nt.links.new(uv_out, voronoi_2.inputs["Vector"])

    mix_vor = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_vor, "data_type"):
        mix_vor.data_type = "RGBA"
    mix_vor.inputs[0].default_value = 0.5
    pos_1 = voronoi_1.outputs.get("Position") or voronoi_1.outputs[0]
    pos_2 = voronoi_2.outputs.get("Position") or voronoi_2.outputs[0]
    nt.links.new(pos_1, mix_vor.inputs[6])
    nt.links.new(pos_2, mix_vor.inputs[7])

    # Musgrave replacement (NoiseTexture with high detail)
    musgrave_approx = nt.nodes.new("ShaderNodeTexNoise")
    musgrave_approx.inputs["Scale"].default_value = 1.0
    if "Detail" in musgrave_approx.inputs:
        musgrave_approx.inputs["Detail"].default_value = 5.6
    if "Roughness" in musgrave_approx.inputs:
        musgrave_approx.inputs["Roughness"].default_value = 0.5
    nt.links.new(uv_out, musgrave_approx.inputs["Vector"])

    noise_tex = nt.nodes.new("ShaderNodeTexNoise")
    noise_tex.inputs["Scale"].default_value = 35.4
    if "Detail" in noise_tex.inputs:    noise_tex.inputs["Detail"].default_value = 3.3
    if "Roughness" in noise_tex.inputs: noise_tex.inputs["Roughness"].default_value = 1.0
    nt.links.new(uv_out, noise_tex.inputs["Vector"])

    mix_noise = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_noise, "data_type"):
        mix_noise.data_type = "RGBA"
    mix_noise.inputs[0].default_value = builder.voronoi_distort_factor
    nt.links.new(_noise_fac_output(musgrave_approx), mix_noise.inputs[6])
    nt.links.new(noise_tex.outputs["Color"], mix_noise.inputs[7])

    mix_combined = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_combined, "data_type"):
        mix_combined.data_type = "RGBA"
    mix_combined.inputs[0].default_value = 0.0417
    nt.links.new(mix_vor.outputs[2], mix_combined.inputs[6])
    nt.links.new(mix_noise.outputs[2], mix_combined.inputs[7])

    mix_uv = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_uv, "data_type"):
        mix_uv.data_type = "RGBA"
    mix_uv.inputs[0].default_value = builder.uv_mix_factor
    nt.links.new(mix_combined.outputs[2], mix_uv.inputs[6])
    nt.links.new(uv_out, mix_uv.inputs[7])

    img_tex = nt.nodes.new("ShaderNodeTexImage")
    img_tex.image = image
    nt.links.new(mix_uv.outputs[2], img_tex.inputs["Vector"])

    art_color_socket = img_tex.outputs["Color"]

    # DarkArt overlay: DARKEN mix with NoiseTexture color
    if builder.darken:
        dark_noise = nt.nodes.new("ShaderNodeTexNoise")
        dark_noise.inputs["Scale"].default_value = builder.darken_scale
        nt.links.new(uv_out, dark_noise.inputs["Vector"])
        darken_mix = nt.nodes.new("ShaderNodeMix")
        if hasattr(darken_mix, "data_type"):
            darken_mix.data_type = "RGBA"
        if hasattr(darken_mix, "blend_type"):
            try: darken_mix.blend_type = "DARKEN"
            except TypeError: pass
        darken_mix.inputs[0].default_value = builder.darken_ratio
        nt.links.new(art_color_socket, darken_mix.inputs[6])
        dark_color_out = dark_noise.outputs.get("Color") or dark_noise.outputs[1]
        nt.links.new(dark_color_out, darken_mix.inputs[7])
        art_color_socket = darken_mix.outputs[2]

    roughness_noise = nt.nodes.new("ShaderNodeTexNoise")

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(art_color_socket, bsdf.inputs["Base Color"])
    nt.links.new(_noise_fac_output(roughness_noise), bsdf.inputs["Roughness"])
    _set_principled(bsdf, Metallic=builder.metallic,
                    **{"Specular IOR Level": builder.specular})
    _connect_output(nt, bsdf)
    return mat

# ============================================================================
# Registries — mirror material_assignments.py entries for wall_art
# ============================================================================

# material_assignments.py:155 -- abstract_art = [(Art, 1.0), (DarkArt, 0.5)]
ABSTRACT_ART_SHADERS = [
    ("art", 1.0),
    ("dark_art", 0.5),
]

# material_assignments.py:282 -- frame = decorative_metal + woods
# decorative_metal: BrushedMetal, GalvanizedMetal, GrainedMetal, HammeredMetal
# woods: Wood 1.0, WhitePlywood 0.1, BlackPlywood 0.1, BlondePlywood 0.1
# re-using make_wood (color varies through bark_hsv).
FRAME_REG = [
    (make_brushed_metal,     1.0),
    (make_galvanized_metal,  1.0),
    (make_grained_metal,     1.0),
    (make_hammered_metal,    1.0),
    (make_wood,              1.0),  # wood.Wood
    (make_wood,              0.1),  # wood.WhitePlywood
    (make_wood,              0.1),  # wood.BlackPlywood
    (make_wood,              0.1),  # wood.BlondePlywood
]

def pick_frame_ctor():
    return weighted_sample_mat(FRAME_REG)

# ============================================================================
# wear_tear post-processing (faithful raw-bpy translation)
# ============================================================================
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"

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
    if "Detail" in n.inputs:     n.inputs["Detail"].default_value = detail
    if "Distortion" in n.inputs: n.inputs["Distortion"].default_value = distortion
    if "Roughness" in n.inputs:  n.inputs["Roughness"].default_value = roughness
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

    noise_a = _noise_tex(nt, mapping.outputs["Vector"],
                         n_scratch_mask_randomness.outputs[0], detail=1.0)
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

    noise_b = _noise_tex(nt, mapping.outputs["Vector"],
                         n_worn_mask_randomness.outputs[0], detail=1.0)
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
# FixedSeed(factory_seed)).
#
# Sampling order follows wall_art.py:assign_materials:
#   1. surface_gen_class = weighted_sample(abstract_art)
#   2. surface_material_gen = surface_gen_class()    (Text.__init__ sequence)
#   3. surface = surface_material_gen()              (build_image + shader)
#   4. frame_surface_gen_class = weighted_sample(frame)
#   5. frame_surface_gen = frame_surface_gen_class() (trivial for our port)
#   6. scratch gate (0.5)
#   7. edge_wear gate (0.5)
# Material to a class (always False), so we don't reproduce it.
# ============================================================================
SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)

_art_key = weighted_sample_mat(ABSTRACT_ART_SHADERS)
_art_builder = AbstractArtBuilder(darken=(_art_key == "dark_art"))
MAT_SURFACE = make_art_material(_art_builder, name="WallArtSurface")

_frame_ctor = pick_frame_ctor()
MAT_FRAME = _frame_ctor(name="WallArtFrame")

WEAR_DO_SCRATCH  = np.random.uniform() <= 0.5
WEAR_DO_EDGEWEAR = np.random.uniform() <= 0.5

# ============================================================================
# Geometry (copied verbatim from objects_blender/wall_decorations/WallArtFactory.py)
# with per-part material assignment added before join.
# ============================================================================

def clear_scene():
    bpy.context.scene.cursor.location = (0, 0, 0)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def uv_smart_project(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode="OBJECT")

def build(seed=SEED):
    np.random.seed(seed)
    rng = np.random.default_rng(seed)
    clear_scene()

    width = float(np.exp(rng.uniform(math.log(0.4), math.log(2.0))))
    height = float(np.exp(rng.uniform(math.log(0.4), math.log(2.0))))
    thickness = float(rng.uniform(0.02, 0.05))
    depth = float(rng.uniform(0.01, 0.02))
    bevel_segments = int(rng.choice([0, 1, 4]))
    bevel_width = float(rng.uniform(depth / 4, depth / 2))

    hw = width / 2
    hh = height / 2

    # Canvas (flat panel in YZ plane, facing +X)
    bm = bmesh.new()
    v0 = bm.verts.new((0, -hw, -hh))
    v1 = bm.verts.new((0,  hw, -hh))
    v2 = bm.verts.new((0,  hw,  hh))
    v3 = bm.verts.new((0, -hw,  hh))
    bm.faces.new([v0, v1, v2, v3])
    mesh_canvas = bpy.data.meshes.new("canvas")
    bm.to_mesh(mesh_canvas)
    bm.free()
    canvas = bpy.data.objects.new("canvas", mesh_canvas)
    bpy.context.scene.collection.objects.link(canvas)

    sol = canvas.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.005
    sol.offset = 1
    bpy.context.view_layer.objects.active = canvas
    bpy.ops.object.modifier_apply(modifier=sol.name)
    apply_tf(canvas)

    # UV unwrap the canvas so the art image texture lands on the surface
    uv_smart_project(canvas)
    canvas.data.materials.append(MAT_SURFACE)

    # Frame ring
    bm2 = bmesh.new()
    ohw = hw + thickness
    ohh = hh + thickness
    ov0 = bm2.verts.new((0, -ohw, -ohh))
    ov1 = bm2.verts.new((0,  ohw, -ohh))
    ov2 = bm2.verts.new((0,  ohw,  ohh))
    ov3 = bm2.verts.new((0, -ohw,  ohh))
    iv0 = bm2.verts.new((0, -hw, -hh))
    iv1 = bm2.verts.new((0,  hw, -hh))
    iv2 = bm2.verts.new((0,  hw,  hh))
    iv3 = bm2.verts.new((0, -hw,  hh))
    bm2.faces.new([ov0, ov1, iv1, iv0])
    bm2.faces.new([ov1, ov2, iv2, iv1])
    bm2.faces.new([ov2, ov3, iv3, iv2])
    bm2.faces.new([ov3, ov0, iv0, iv3])
    mesh_frame = bpy.data.meshes.new("frame")
    bm2.to_mesh(mesh_frame)
    bm2.free()
    frame = bpy.data.objects.new("frame", mesh_frame)
    bpy.context.scene.collection.objects.link(frame)

    sol2 = frame.modifiers.new("sol2", "SOLIDIFY")
    sol2.thickness = depth
    sol2.offset = 1
    bpy.context.view_layer.objects.active = frame
    bpy.ops.object.modifier_apply(modifier=sol2.name)

    if bevel_segments > 0:
        bv = frame.modifiers.new("bevel", "BEVEL")
        bv.width = bevel_width
        bv.segments = bevel_segments
        bpy.ops.object.modifier_apply(modifier=bv.name)

    apply_tf(frame)
    frame.data.materials.append(MAT_FRAME)

    result = join_objs([canvas, frame])
    result.name = "WallArtFactory"
    apply_tf(result)

    if result is not None:
        if WEAR_DO_SCRATCH:
            apply_scratches(result)
        if WEAR_DO_EDGEWEAR:
            apply_edge_wear(result)

    return result

build(SEED)
