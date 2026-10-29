# [FL_INDEX: keywords="blender_factory, procedural_3d, BookFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BookFactory | Category: factories_tex
# Prompt: A 3D model of a single closed book lying flat, rendered from a slightly elevated three-quarter perspective. The book features a rectangular hardcover with a visible front cover, a thin spine along one edge, and a slim profile of page edges visible along the other three sides.

import os
import io
import math
import string
import colorsys
import random

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


def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)

def _mat_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def hsv2rgba(h, s, v):
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

# ----------------------------------------------------------------------------
# Plaster material (paper pages)
# Uses Noise textures (Blender 5.0 removed ShaderNodeTexMusgrave)
# ----------------------------------------------------------------------------
def make_plaster(name="Plaster", plaster_colored=None) -> bpy.types.Material:
    if plaster_colored is None:
        plaster_colored = np.random.uniform() < 0.4

    hue = float(np.random.uniform(0, 1))
    front_value = _mat_log_uniform(0.5, 1.0)
    back_value = front_value * float(np.random.uniform(0.6, 1))

    if plaster_colored:
        front_color = hsv2rgba(hue, float(np.random.uniform(0.3, 0.5)), front_value)
        back_color = hsv2rgba(
            hue + float(np.random.uniform(-0.1, 0.1)),
            float(np.random.uniform(0.3, 0.5)),
            back_value,
        )
    else:
        front_color = hsv2rgba(hue, 0, front_value)
        back_color = hsv2rgba(
            hue + float(np.random.uniform(-0.1, 0.1)), 0, back_value
        )

    mat = _new_material(name)
    nt = mat.node_tree

    uv_map = nt.nodes.new("ShaderNodeUVMap")

    # Musgrave-equivalent: Noise with high detail + dimension mapping
    # maps to Noise with high detail, no dimension param available in Noise.
    # We replicate the visual character using a high-detail Noise.
    musgrave_detail = _mat_log_uniform(15, 30)
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    if "Detail" in musgrave.inputs:
        musgrave.inputs["Detail"].default_value = musgrave_detail
    if "Roughness" in musgrave.inputs:
        musgrave.inputs["Roughness"].default_value = 0.5
    nt.links.new(uv_map.outputs["UV"], musgrave.inputs["Vector"])

    # Noise texture: Detail=log_uniform(15,30), Distortion=log_uniform(4,8)
    noise_detail = _mat_log_uniform(15, 30)
    noise_distortion = _mat_log_uniform(4, 8)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = noise_detail
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = noise_distortion
    nt.links.new(uv_map.outputs["UV"], noise.inputs["Vector"])

    # ColorRamp on noise: [0, uniform(0.3,0.5)] -> black to white
    noise_ramp_pos = float(np.random.uniform(0.3, 0.5))
    noise_cr = nt.nodes.new("ShaderNodeValToRGB")
    noise_cr.color_ramp.color_mode = "HSV"
    noise_cr.color_ramp.elements[0].position = 0.0
    noise_cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    noise_cr.color_ramp.elements[1].position = noise_ramp_pos
    noise_cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(_noise_fac_output(noise), noise_cr.inputs.get("Fac") or noise_cr.inputs[0])

    # MixRGB DIFFERENCE: musgrave fac, noise_cr color
    difference = nt.nodes.new("ShaderNodeMix")
    if hasattr(difference, "data_type"):
        difference.data_type = "RGBA"
    if hasattr(difference, "blend_type"):
        try:
            difference.blend_type = "DIFFERENCE"
        except (TypeError, AttributeError):
            pass
    # inputs: 0=Fac, 6=A, 7=B for RGBA mix
    difference.inputs[0].default_value = 1.0
    nt.links.new(_noise_fac_output(musgrave), difference.inputs[6])
    nt.links.new(noise_cr.outputs["Color"], difference.inputs[7])

    # ColorRamp on difference: [uniform(0.2,0.3), 1] -> back_color, front_color
    base_cr_pos0 = float(np.random.uniform(0.2, 0.3))
    base_cr = nt.nodes.new("ShaderNodeValToRGB")
    base_cr.color_ramp.color_mode = "HSV"
    base_cr.color_ramp.elements[0].position = base_cr_pos0
    base_cr.color_ramp.elements[0].color = back_color
    base_cr.color_ramp.elements[1].position = 1.0
    base_cr.color_ramp.elements[1].color = front_color
    nt.links.new(difference.outputs[2], base_cr.inputs.get("Fac") or base_cr.inputs[0])

    # Displacement: MusgraveTexture(Scale=uniform(1e3,2e3)) * log_uniform(0.0001,0.0003)
    disp_scale = float(np.random.uniform(1e3, 2e3))
    disp_height_noise = nt.nodes.new("ShaderNodeTexNoise")
    disp_height_noise.inputs["Scale"].default_value = disp_scale
    if "Detail" in disp_height_noise.inputs:
        disp_height_noise.inputs["Detail"].default_value = 2.0

    disp_amount = _mat_log_uniform(0.0001, 0.0003)
    disp_node = nt.nodes.new("ShaderNodeDisplacement")
    disp_node.inputs["Scale"].default_value = disp_amount
    disp_node.inputs["Midlevel"].default_value = 0.0
    nt.links.new(_noise_fac_output(disp_height_noise), disp_node.inputs["Height"])

    # Principled BSDF
    roughness = float(np.random.uniform(0.7, 0.8))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(base_cr.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Roughness=roughness)

    _connect_output(nt, bsdf, displacement=disp_node.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# Text/cover material — procedural book cover image texture
# Generates a matplotlib image with patches/text/barcodes, then uses it as
# an image texture with procedural UV distortion in the shader.
# ----------------------------------------------------------------------------

# Font setup
_FONT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
)
if os.path.isdir(_FONT_DIR):
    for _f in matplotlib.font_manager.findSystemFonts([_FONT_DIR]):
        matplotlib.font_manager.fontManager.addfont(_f)
    _FONT_NAMES = [fn.replace("_", " ") for fn in os.listdir(_FONT_DIR)]
else:
    _FONT_NAMES = list(matplotlib.font_manager.get_font_names())[:10]

# Character set for random text
_CHAR_SET = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
_CHAR_WEIGHTS = np.concatenate([
    1.5 * np.ones(len(string.ascii_lowercase)),
    0.5 * np.ones(len(string.ascii_uppercase)),
    0.5 * np.ones(len(string.digits)),
])
_CHAR_WEIGHTS = _CHAR_WEIGHTS / _CHAR_WEIGHTS.sum()

def _clip_gaussian(mean, std, lo, hi, max_tries=20):
    for _ in range(max_tries):
        val = np.random.normal(mean, std)
        if lo <= val <= hi:
            return val
    return np.clip(np.random.normal(mean, std), lo, hi)

def _generate_text():
    length = int(_clip_gaussian(3, 7, 2, 15))
    return "".join(np.random.choice(_CHAR_SET, size=length, replace=True, p=_CHAR_WEIGHTS))

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

def _simple_decimate(points, n):
    if len(points) <= n:
        return points
    indices = np.random.permutation(len(points))[:n]
    return points[indices]

class TextImageBuilder:
    """Builds a matplotlib-based book cover image (port of text.py:Text)."""


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
    font_weights = ["normal", "bold", "heavy"]
    font_styles = ["normal", "italic", "oblique"]

    def __init__(self, has_barcode=True, emission=0):
        self.size = 4
        self.dpi = 100
        self.colormap = (
            self._build_sequential_colormap()
            if uniform() < 0.5
            else self._build_diverging_colormap()
        )
        self.white_chance = 0.03
        self.black_chance = 0.05
        self.n_patches = np.random.randint(5, 8)
        self.force_horizontal = uniform() < 0.75
        self.n_texts = np.random.randint(2, 4)
        self.n_barcodes = 1 if has_barcode and uniform() < 0.5 else 0
        self.barcode_scale = float(uniform(0.3, 0.6))
        self.barcode_length = np.random.randint(25, 40)
        self.barcode_aspect = _mat_log_uniform(1.5, 3)
        self.emission = emission
        # Shader params sampled here
        self.uv_mix_factor = float(uniform(0, 0.4)) if rand() < 0.5 else 1.0
        self.metallic = float(uniform(0, 0.5))
        self.specular = float(uniform(0, 0.2))
        self.voronoi_distort_factor = float(uniform(0.2, 1.0))

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
        elif r < self.white_chance + self.black_chance:
            return np.array([0, 0, 0])
        else:
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
        return (hi - lo) * _mat_log_uniform(0.2, 0.8)

    def _get_locs(self, bbox, n):
        m = 8 * n
        x = self._loc_uniform(bbox[0], bbox[1], m)
        y = self._loc_uniform(bbox[2], bbox[3], m)
        points = np.stack([x, y], -1)
        return _simple_decimate(points, n)

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
        import inspect
        for x, y in locs:
            w = self._scale_uniform(bbox[0], bbox[1])
            h = self._scale_uniform(bbox[2], bbox[3])
            x_, y_ = x - w / 2, y - h / 2
            r = min(w, h) / 2
            fn = _random_general(self.patch_fns)
            kwargs = {
                "alpha": float(uniform(0.5, 0.8)) if uniform() < 0.2 else 1,
                "fill": bool(uniform() < 0.2),
                "angle": 0 if uniform() < 0.8 else float(uniform(-30, 30)),
                "orientation": float(uniform(0, np.pi * 2)),
            }
            kwargs = {
                k: kwargs[k]
                for k in inspect.signature(fn).parameters
                if k in kwargs
            }
            face_color, edge_color = self.random_colors
            kwargs.update({
                "facecolor": face_color,
                "edgecolor": edge_color,
                "hatch": np.random.choice(list(self.hatches)) if uniform() < 0.3 else "none",
                "linewidth": float(uniform(2, 5)),
            })
            try:
                match fn.__name__:
                    case "Circle":
                        patch = Circle((x, y), r, **kwargs)
                    case "Rectangle":
                        patch = Rectangle((x_, y_), w, h, **kwargs)
                    case "Wedge":
                        start = float(uniform(0, 360))
                        patch = Wedge((x, y), r, start, start + float(uniform(0, 360)),
                                      width=float(uniform(0.2, 0.8)) * r, **kwargs)
                    case "RegularPolygon":
                        patch = RegularPolygon((x, y), np.random.randint(3, 9), radius=r, **kwargs)
                    case "Ellipse":
                        patch = Ellipse((x, y), w, h, **kwargs)
                    case "Arrow":
                        w_ = w if uniform() < 0.5 else -w
                        h_ = h if uniform() < 0.5 else -h
                        patch = Arrow(x - w_ / 2, y - h_ / 2, w, h,
                                      width=_mat_log_uniform(0.6, 1.5), **kwargs)
                    case "FancyBboxPatch":
                        pad = float(uniform(0.2, 0.4)) * min(w, h)
                        box_style = np.random.choice(list(BoxStyle.get_styles().values()))(pad=pad)
                        patch = FancyBboxPatch(
                            (x_, y_), w - pad, h - pad, box_style,
                            mutation_scale=_mat_log_uniform(0.6, 1.5),
                            mutation_aspect=_mat_log_uniform(0.6, 1.5), **kwargs)
                    case _:
                        continue
                plt.gca().add_patch(patch)
            except (MemoryError, Exception):
                pass

    def _add_texts(self, locs):
        for x, y in locs:
            x = 0.5 + (x - 0.5) * 0.6
            text_str = _generate_text()
            family = np.random.choice(_FONT_NAMES) if _FONT_NAMES else "sans-serif"
            color, bg_color = self.random_colors
            font_size = _mat_log_uniform(0.75, 1) * self.dpi * _clip_gaussian(0.3, 0.2, 0.2, 0.65)
            plt.figtext(
                x, y, text_str,
                family=family,
                size=font_size,
                ha="center", va="center",
                c=color,
                rotation=float(uniform(-10, 10)),
                wrap=True,
                fontweight=np.random.choice(self.font_weights),
                fontstyle=np.random.choice(self.font_styles),
                backgroundcolor=bg_color,
            )

    def _add_barcodes(self, locs):
        fig = plt.gcf()
        for x, y in locs:
            code = np.random.randint(0, 2, self.barcode_length)
            h = self.barcode_scale / self.size
            w = h * self.barcode_aspect
            ax = fig.add_axes((x - w / 2, y - h / 2, w, h))
            ax.set_axis_off()
            ax.imshow(code.reshape(1, -1), cmap="binary", aspect="auto",
                      interpolation="nearest")

    def build_image(self, bbox=(0, 1, 0, 1)):
        fig = plt.figure(figsize=(self.size, self.size), dpi=self.dpi)
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set_facecolor(self.random_color)
        total = self.n_patches + self.n_texts + self.n_barcodes
        locs = self._get_locs(bbox, total)
        self._add_divider(bbox)
        self._add_patches(locs[: self.n_patches], bbox)
        self._add_texts(locs[self.n_patches: self.n_patches + self.n_texts])
        self._add_barcodes(locs[self.n_patches + self.n_texts:])
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        size = self.size * self.dpi
        image = bpy.data.images.new("text_texture", width=size, height=size, alpha=True)
        data = np.asarray(Image.open(buffer), dtype=np.float32)[::-1, :] / 255.0
        image.pixels.foreach_set(data.ravel())
        image.pack()
        plt.close("all")
        try:
            plt.clf()
        except Exception:
            pass
        return image

def make_text_cover(text_builder, name="TextCover") -> bpy.types.Material:
    image = text_builder.build_image(bbox=(0, 1, 0, 1))
    mat = _new_material(name)
    nt = mat.node_tree

    uv_map = nt.nodes.new("ShaderNodeUVMap")
    uv_out = uv_map.outputs["UV"]

    # Voronoi textures for UV distortion
    voronoi_1 = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi_1.inputs["Scale"].default_value = 60.0
    nt.links.new(uv_out, voronoi_1.inputs["Vector"])

    voronoi_2 = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi_2.inputs["Scale"].default_value = 60.0
    nt.links.new(uv_out, voronoi_2.inputs["Vector"])

    # Mix voronoi positions
    mix_vor = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_vor, "data_type"):
        mix_vor.data_type = "RGBA"
    mix_vor.inputs[0].default_value = 0.5
    pos_out_1 = voronoi_1.outputs.get("Position") or voronoi_1.outputs[0]
    pos_out_2 = voronoi_2.outputs.get("Position") or voronoi_2.outputs[0]
    nt.links.new(pos_out_1, mix_vor.inputs[6])
    nt.links.new(pos_out_2, mix_vor.inputs[7])

    # Noise texture (replaces MusgraveTexture in original)
    musgrave_approx = nt.nodes.new("ShaderNodeTexNoise")
    musgrave_approx.inputs["Scale"].default_value = 1.0
    if "Detail" in musgrave_approx.inputs:
        musgrave_approx.inputs["Detail"].default_value = 5.6
    if "Roughness" in musgrave_approx.inputs:
        musgrave_approx.inputs["Roughness"].default_value = 0.5
    nt.links.new(uv_out, musgrave_approx.inputs["Vector"])

    noise_tex = nt.nodes.new("ShaderNodeTexNoise")
    noise_tex.inputs["Scale"].default_value = 35.4
    if "Detail" in noise_tex.inputs:
        noise_tex.inputs["Detail"].default_value = 3.3
    if "Roughness" in noise_tex.inputs:
        noise_tex.inputs["Roughness"].default_value = 1.0
    nt.links.new(uv_out, noise_tex.inputs["Vector"])

    # Mix musgrave + noise
    mix_noise = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_noise, "data_type"):
        mix_noise.data_type = "RGBA"
    mix_noise.inputs[0].default_value = text_builder.voronoi_distort_factor
    nt.links.new(_noise_fac_output(musgrave_approx), mix_noise.inputs[6])
    nt.links.new(noise_tex.outputs["Color"], mix_noise.inputs[7])

    # Mix voronoi + noise
    mix_combined = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_combined, "data_type"):
        mix_combined.data_type = "RGBA"
    mix_combined.inputs[0].default_value = 0.0417
    nt.links.new(mix_vor.outputs[2], mix_combined.inputs[6])
    nt.links.new(mix_noise.outputs[2], mix_combined.inputs[7])

    # Mix with UV
    mix_uv = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_uv, "data_type"):
        mix_uv.data_type = "RGBA"
    mix_uv.inputs[0].default_value = text_builder.uv_mix_factor
    nt.links.new(mix_combined.outputs[2], mix_uv.inputs[6])
    nt.links.new(uv_map.outputs["UV"], mix_uv.inputs[7])

    # Image texture
    img_tex = nt.nodes.new("ShaderNodeTexImage")
    img_tex.image = image
    nt.links.new(mix_uv.outputs[2], img_tex.inputs["Vector"])

    # Roughness noise
    roughness_noise = nt.nodes.new("ShaderNodeTexNoise")

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(img_tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(_noise_fac_output(roughness_noise), bsdf.inputs["Roughness"])
    _set_principled(bsdf, Metallic=text_builder.metallic,
                    **{"Specular IOR Level": text_builder.specular})

    _connect_output(nt, bsdf)
    return mat

WEAR_TEAR_PROB = [0.5, 0.5]
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
        try:
            map1.vector_type = "TEXTURE"
        except TypeError:
            pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map2, "vector_type"):
        try:
            map2.vector_type = "TEXTURE"
        except TypeError:
            pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    map3 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map3, "vector_type"):
        try:
            map3.vector_type = "TEXTURE"
        except TypeError:
            pass
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
        except Exception as exc:
            print(f"  [scratches] failed on {mat.name}: {type(exc).__name__}: {exc}")

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
        try:
            combine_color.mode = "HSV"
        except TypeError:
            pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_result"):
        try:
            mix.clamp_result = True
        except TypeError:
            pass
    if hasattr(mix, "clamp_factor"):
        try:
            mix.clamp_factor = False
        except TypeError:
            pass
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
        try:
            vor_h.feature = "DISTANCE_TO_EDGE"
        except TypeError:
            pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])
    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_v, "feature"):
        try:
            vor_v.feature = "DISTANCE_TO_EDGE"
        except TypeError:
            pass
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
        except Exception as exc:
            print(f"  [edge_wear] failed on {mat.name}: {type(exc).__name__}: {exc}")

# --- Original geometry helpers (copied verbatim from objects_blender/) ---

def log_uniform(lo, hi):
    return np.exp(np.random.uniform(np.log(lo), np.log(hi)))

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    bpy.context.scene.cursor.location = (0, 0, 0)

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_tf(obj, loc=False):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def uv_smart_project(obj):
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode="OBJECT")

# ── book creation (verbatim from objects_blender/table_decorations/BookFactory.py) ──

def make_paper(width, height, depth, mat_paper):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    paper = bpy.context.active_object
    paper.location = (width / 2, height / 2, depth / 2)
    paper.scale = (width / 2 - 1e-4, height / 2, depth / 2 - 1e-4)
    apply_tf(paper, loc=True)
    paper.data.materials.append(mat_paper)
    return paper

def make_paperback(width, height, depth, mat_paper, mat_cover):
    paper = make_paper(width, height, depth, mat_paper)

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.location = (width / 2, height / 2, depth / 2)
    obj.scale = (width / 2, height / 2, depth / 2)
    apply_tf(obj, loc=True)

    # Delete back-face vertical edges (where x > 0 and two verts differ in z)
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(obj.data)
    geom = []
    for e in bm.edges:
        u, v = e.verts
        if u.co[0] > 0 and v.co[0] > 0 and u.co[2] != v.co[2]:
            geom.append(e)
    bmesh.ops.delete(bm, geom=geom, context="EDGES")
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    _apply_cover(obj, mat_cover)

    return join_objs([paper, obj])

def make_hardcover(width, height, depth, margin, offset, thickness, mat_paper, mat_cover):
    paper = make_paper(width, height, depth, mat_paper)

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    count = 8

    # Array modifier
    mod = obj.modifiers.new("ARRAY", "ARRAY")
    mod.count = count
    mod.relative_offset_displace = (0, 0, 1)
    mod.use_merge_vertices = True
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    obj.location = (1, 1, 1)
    apply_tf(obj, loc=True)

    # Delete interior verts
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(obj.data)
    geom = []
    for v in bm.verts:
        if v.co[0] > 0 and 0 < v.co[2] < count * 2:
            geom.append(v)
    bmesh.ops.delete(bm, geom=geom, context="VERTS")
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    obj.location = (0, -margin, 0)
    obj.scale = ((width + margin) / 2, height / 2 + margin, depth / 2 / count)
    apply_tf(obj, loc=True)

    # Spine bow (parabolic X displacement)
    x, y, z = read_co(obj).T
    ratio = np.minimum(z / depth, 1 - z / depth)
    x -= 4 * ratio * (1 - ratio) * offset
    obj.data.vertices.foreach_set("co", np.stack([x, y, z]).T.reshape(-1))
    obj.data.update()

    _apply_cover(obj, mat_cover)

    # Solidify
    mod = obj.modifiers.new("SOLIDIFY", "SOLIDIFY")
    mod.thickness = thickness
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    return join_objs([paper, obj])

def _apply_cover(obj, mat_cover):
    """

    Mirrors make_cover() + wrap_front_back_side() behavior.
    Rotates 90deg around X, UV smart-projects, assigns cover material,
    then rotates back.
    """

    obj.rotation_euler[0] = np.pi / 2
    apply_tf(obj)
    uv_smart_project(obj)
    obj.data.materials.append(mat_cover)
    obj.rotation_euler[0] = -np.pi / 2
    apply_tf(obj)

SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)

_REL_SCALE = log_uniform(1, 1.5)
_SKEWNESS = log_uniform(1.3, 1.8)
_IS_PAPERBACK = np.random.uniform() < 0.5
_MARGIN = float(np.random.uniform(0.005, 0.01))
_OFFSET = 0 if np.random.uniform() < 0.5 else float(log_uniform(0.002, 0.008))
_THICKNESS = float(np.random.uniform(0.002, 0.003))

MAT_PAPER = make_plaster(name="Paper")

_TEXT_BUILDER = TextImageBuilder(has_barcode=True, emission=0)
MAT_COVER = make_text_cover(_TEXT_BUILDER, name="Cover")

_scratch_prob, _edge_wear_prob = WEAR_TEAR_PROB
WEAR_DO_SCRATCH = np.random.uniform() <= _scratch_prob
WEAR_DO_EDGEWEAR = np.random.uniform() <= _edge_wear_prob

_TEXTURE_SHARED = np.random.uniform() < 0.2

# --- Geometry with per-part material assignment ---
def build(seed=SEED):
    np.random.seed(seed)
    clear_scene()

    unit = 0.0127
    width = int(log_uniform(0.08, 0.15) * _REL_SCALE / unit) * unit
    height = int(width * _SKEWNESS / unit) * unit
    depth = float(np.random.uniform(0.01, 0.02)) * _REL_SCALE

    if _IS_PAPERBACK:
        obj = make_paperback(width, height, depth, MAT_PAPER, MAT_COVER)
    else:
        obj = make_hardcover(width, height, depth, _MARGIN, _OFFSET, _THICKNESS,
                             MAT_PAPER, MAT_COVER)

    if obj is not None:
        obj.name = "BookFactory"
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_smooth()
        obj.select_set(False)
        obj.data.update()
        if WEAR_DO_SCRATCH:
            apply_scratches(obj)
        if WEAR_DO_EDGEWEAR:
            apply_edge_wear(obj)

    return obj

build(SEED)

