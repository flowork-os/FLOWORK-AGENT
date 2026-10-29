# [FL_INDEX: keywords="blender_factory, procedural_3d, BookStackFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BookStackFactory | Category: factories_tex
# Prompt: A 3D model of a stack of books piled horizontally on top of each other, rendered from a slightly elevated three-quarter perspective. The book stack features multiple closed books of varying sizes layered with slight rotational offsets, creating an irregular but cohesive pile with visible covers, spines, and page edges.

SEED = 0

import hashlib
import io
import math
import os
import random
import string
import colorsys

import bmesh
import bpy
import numpy as np
from numpy.random import uniform

# matplotlib setup (non-interactive backend for headless)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager
from matplotlib.patches import (
    Arrow, BoxStyle, Circle, Ellipse, FancyBboxPatch,
    Rectangle, RegularPolygon, Wedge,
)
from PIL import Image

# --- General helpers ---

def int_hash(x):
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)

def seed_all(seed):
    np.random.seed(int(seed))
    random.seed(int(seed))

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def clip_gaussian(mean, std, lo, hi, max_tries=20):
    for _ in range(max_tries):
        val = np.random.normal(mean, std)
        if lo <= val <= hi:
            return val
    return float(np.clip(np.random.normal(mean, std), lo, hi))

def hsv2rgba(h, s, v):
    h = h - math.floor(h)
    s = float(max(0.0, min(1.0, s)))
    v = float(max(0.0, min(1.0, v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def weighted_choice(registry):
    classes, weights = zip(*registry)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]

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
    if len(objs) == 1:
        return objs[0]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

# --- Material node helpers ---

def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Coat Roughness": ("Coat Roughness", "Clearcoat Roughness"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
        "Subsurface Weight": ("Subsurface Weight", "Subsurface"),
        "Transmission Weight": ("Transmission Weight", "Transmission"),
    }
    for k, v in kw.items():
        if v is None:
            continue
        for name in aliases.get(k, (k,)):
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = float(value)
    return n

def _color_ramp(nt, fac_socket, stops):
    cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(fac_socket, cr.inputs.get("Fac") or cr.inputs[0])
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

def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for idx, val in [(0, in0), (1, in1)]:
        if val is None:
            continue
        if hasattr(val, "links"):
            nt.links.new(val, n.inputs[idx])
        else:
            n.inputs[idx].default_value = float(val)
    return n

def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    for idx, val in [(0, in0), (1, in1)]:
        if val is None:
            continue
        if hasattr(val, "links"):
            nt.links.new(val, n.inputs[idx])
        else:
            n.inputs[idx].default_value = val
    if scale is not None:
        for inp in n.inputs:
            if inp.name == "Scale":
                inp.default_value = scale
                break
    return n

def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)

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

# --- Plaster material (paper pages) ---

def make_plaster(name="Plaster", plaster_colored=None):
    if plaster_colored is None:
        plaster_colored = uniform() < 0.4
    hue = uniform(0, 1)
    front_value = log_uniform(0.5, 1.0)
    back_value = front_value * uniform(0.6, 1)
    if plaster_colored:
        front_color = hsv2rgba(hue, uniform(0.3, 0.5), front_value)
        back_color = hsv2rgba(hue + uniform(-0.1, 0.1), uniform(0.3, 0.5), back_value)
    else:
        front_color = hsv2rgba(hue, 0, front_value)
        back_color = hsv2rgba(hue + uniform(-0.1, 0.1), 0, back_value)

    mat = _new_material(name)
    nt = mat.node_tree

    uv_map = nt.nodes.new("ShaderNodeUVMap")

    # Musgrave-like texture (use Noise in Blender 4.4+/5.0)
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(uv_map.outputs["UV"], musgrave.inputs["Vector"])
    musgrave.inputs["Scale"].default_value = 1.0
    if "Detail" in musgrave.inputs:
        musgrave.inputs["Detail"].default_value = log_uniform(15, 30)
    # Musgrave "Dimension" => use Lacunarity as proxy for variation
    if "Lacunarity" in musgrave.inputs:
        musgrave.inputs["Lacunarity"].default_value = 0.0

    # Noise texture
    noise = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(uv_map.outputs["UV"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 1.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = log_uniform(15, 30)
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = log_uniform(4, 8)

    # Color ramp on noise
    noise_cr = _color_ramp(
        nt, _noise_fac_output(noise),
        [(0.0, (0, 0, 0, 1)), (uniform(0.3, 0.5), (1, 1, 1, 1))]
    )

    # Difference blend of musgrave and noise
    # Use MixRGB / Mix node with DIFFERENCE blend type
    diff = nt.nodes.new("ShaderNodeMix")
    if hasattr(diff, "data_type"):
        diff.data_type = "RGBA"
    if hasattr(diff, "blend_type"):
        diff.blend_type = "DIFFERENCE"
    else:
        # Fallback: try to set blend_type on the node itself
        pass
    diff.inputs[0].default_value = 1.0  # Factor
    nt.links.new(_noise_fac_output(musgrave), diff.inputs[6])
    nt.links.new(noise_cr.outputs["Color"], diff.inputs[7])

    # Base color ramp
    base_cr = _color_ramp(
        nt, diff.outputs[2],
        [(uniform(0.2, 0.3), back_color), (1.0, front_color)]
    )
    base_cr.color_ramp.color_mode = "HSV"

    # Displacement musgrave
    disp_musgrave = nt.nodes.new("ShaderNodeTexNoise")
    disp_musgrave.inputs["Scale"].default_value = uniform(1e3, 2e3)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Scale"].default_value = log_uniform(0.0001, 0.0003)
    nt.links.new(_noise_fac_output(disp_musgrave), disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(base_cr.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Roughness=uniform(0.7, 0.8))

    _connect_output(nt, bsdf, disp.outputs[0])
    return mat

# --- Text / cover material (book cover with image texture) ---

# Character set for random text
_CHARSET = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
_CHARSET_W = np.concatenate([
    1.5 * np.ones(len(string.ascii_lowercase)),
    0.5 * np.ones(len(string.ascii_uppercase)),
    0.5 * np.ones(len(string.digits)),
])
_CHARSET_W /= _CHARSET_W.sum()

# Try to load fonts from assets dir
_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "infinigen", "assets", "fonts")
_FONT_NAMES = []
if os.path.isdir(_FONT_DIR):
    for f in matplotlib.font_manager.findSystemFonts([_FONT_DIR]):
        matplotlib.font_manager.fontManager.addfont(f)
    _FONT_NAMES = [fn.replace("_", " ") for fn in os.listdir(_FONT_DIR)
                   if os.path.isdir(os.path.join(_FONT_DIR, fn))]
if not _FONT_NAMES:
    _FONT_NAMES = ["DejaVu Sans"]

def _generate_text():
    n = int(clip_gaussian(3, 7, 2, 15))
    return "".join(np.random.choice(_CHARSET, size=n, replace=True, p=_CHARSET_W))

def _decimate_points(points, n):
    if len(points) <= n:
        return points[:n]
    # Simple greedy farthest-point sampling
    idx = [0]
    for _ in range(n - 1):
        dists = np.min([np.linalg.norm(points - points[i], axis=1) for i in idx], axis=0)
        idx.append(int(np.argmax(dists)))
    return points[np.array(idx)]

class TextImageBuilder:
    """Builds a matplotlib-based cover image"""

    # Patch function choices with weights
    _PATCH_WEIGHTS = [
        (Circle, 2), (Rectangle, 4), (Wedge, 1), (RegularPolygon, 1),
        (Ellipse, 1), (Arrow, 2), (FancyBboxPatch, 2),
    ]

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
        self.barcode_scale = uniform(0.3, 0.6)
        self.barcode_length = np.random.randint(25, 40)
        self.barcode_aspect = log_uniform(1.5, 3)
        self.emission = emission

    @staticmethod
    def _build_sequential_colormap():
        count = 20
        hue = (uniform() + np.linspace(0, 0.5, count)) % 1
        lightness = np.linspace(uniform(0.0), uniform(0.6, 0.8), count)
        saturation = np.concatenate([
            np.linspace(1, 0.5, count // 2), np.linspace(0.5, 1, count // 2)
        ])
        saturation *= uniform(0, 1)
        lightness *= uniform(0.5, 1)
        return np.array([colorsys.hls_to_rgb(h, l, s)
                         for h, l, s in zip(hue, lightness, saturation)])

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
            np.linspace(1, 0.5, count // 2), np.linspace(0.5, 1, count // 2)
        ])
        saturation *= uniform(0, 1)
        lightness *= uniform(0.5, 1)
        return np.array([colorsys.hls_to_rgb(h, l, s)
                         for h, l, s in zip(hue, lightness, saturation)])

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

    def _get_locs(self, bbox, n):
        m = 8 * n
        x = self._loc_uniform(bbox[0], bbox[1], m)
        y = self._loc_uniform(bbox[2], bbox[3], m)
        pts = np.stack([x, y], -1)
        return _decimate_points(pts, n)

    @staticmethod
    def _loc_uniform(min_, max_, size=None):
        ratio = 0.1
        return uniform(min_ + ratio * (max_ - min_),
                       min_ + (1 - ratio) * (max_ - min_), size)

    @staticmethod
    def _scale_uniform(min_, max_):
        return (max_ - min_) * log_uniform(0.2, 0.8)

    def _add_divider(self, bbox):
        if uniform() < 0.6:
            return
        a = 0 if uniform() < 0.7 else uniform(5, 10)
        x = self._loc_uniform(bbox[0], bbox[1])
        y = self._loc_uniform(bbox[2], bbox[3])
        if bbox[0] == 0 or self.force_horizontal:
            args_list = [
                [(0, y), 2, 2, a], [(0, y), 2, -2, -a],
                [(1, y), -2, -2, a], [(1, y), -2, 2, -a],
            ]
        else:
            args_list = [
                [(x, 0), -2, 2, a], [(x, 0), 2, 2, -a],
                [(x, 1), 2, -2, a], [(x, 1), -2, -2, -a],
            ]
        args = args_list[np.random.randint(len(args_list))]
        try:
            plt.gca().add_patch(Rectangle(*args[:-1], angle=args[-1],
                                          color=self.random_color))
        except Exception:
            pass

    def _add_patches(self, locs, bbox):
        patch_classes, patch_weights = zip(*self._PATCH_WEIGHTS)
        pw = np.array(patch_weights, dtype=float)
        pw /= pw.sum()
        for x, y in locs:
            w = self._scale_uniform(bbox[0], bbox[1])
            h = self._scale_uniform(bbox[2], bbox[3])
            x_, y_ = x - w / 2, y - h / 2
            r = min(w, h) / 2
            fn = patch_classes[int(np.random.choice(len(patch_classes), p=pw))]
            face_color, edge_color = self.random_colors
            kwargs = {
                "facecolor": face_color,
                "edgecolor": edge_color,
                "linewidth": uniform(2, 5),
            }
            if uniform() < 0.2:
                kwargs["alpha"] = uniform(0.5, 0.8)
            if uniform() < 0.3:
                kwargs["hatch"] = np.random.choice(
                    ["/", "\\", "|", "-", "+", "x", "o", "O", ".", "*"])
            try:
                if fn is Circle:
                    patch = Circle((x, y), r, **kwargs)
                elif fn is Rectangle:
                    angle = 0 if uniform() < 0.8 else uniform(-30, 30)
                    patch = Rectangle((x_, y_), w, h, angle=angle, **kwargs)
                elif fn is Wedge:
                    start = uniform(0, 360)
                    patch = Wedge((x, y), r, start, start + uniform(0, 360),
                                  width=uniform(0.2, 0.8) * r, **kwargs)
                elif fn is RegularPolygon:
                    patch = RegularPolygon((x, y), np.random.randint(3, 9),
                                           radius=r, **kwargs)
                elif fn is Ellipse:
                    angle = 0 if uniform() < 0.8 else uniform(-30, 30)
                    patch = Ellipse((x, y), w, h, angle=angle, **kwargs)
                elif fn is Arrow:
                    patch = Arrow(x - w / 2, y - h / 2, w, h,
                                  width=log_uniform(0.6, 1.5), **kwargs)
                elif fn is FancyBboxPatch:
                    pad = uniform(0.2, 0.4) * min(w, h)
                    styles = list(BoxStyle.get_styles().values())
                    box_style = np.random.choice(styles)(pad=pad)
                    patch = FancyBboxPatch(
                        (x_, y_), max(w - pad, 0.01), max(h - pad, 0.01),
                        box_style, mutation_scale=log_uniform(0.6, 1.5),
                        mutation_aspect=log_uniform(0.6, 1.5), **kwargs)
                else:
                    continue
                plt.gca().add_patch(patch)
            except Exception:
                pass

    def _add_texts(self, locs):
        for x, y in locs:
            x = 0.5 + (x - 0.5) * 0.6
            text = _generate_text()
            family = np.random.choice(_FONT_NAMES)
            color, bg = self.random_colors
            try:
                plt.figtext(
                    x, y, text,
                    family=family,
                    size=log_uniform(0.75, 1) * self.dpi * clip_gaussian(0.3, 0.2, 0.2, 0.65),
                    ha="center", va="center", c=color,
                    rotation=uniform(-10, 10), wrap=True,
                    fontweight=np.random.choice(["normal", "bold", "heavy"]),
                    fontstyle=np.random.choice(["normal", "italic", "oblique"]),
                    backgroundcolor=bg,
                )
            except Exception:
                pass

    def _add_barcodes(self, locs):
        fig = plt.gcf()
        for x, y in locs:
            code = np.random.randint(0, 2, self.barcode_length)
            h = self.barcode_scale / self.size
            w = h * self.barcode_aspect
            ax = fig.add_axes((max(0, x - w / 2), max(0, y - h / 2),
                               min(w, 1.0), min(h, 1.0)))
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
        self._add_patches(locs[:self.n_patches], bbox)
        self._add_texts(locs[self.n_patches:self.n_patches + self.n_texts])
        self._add_barcodes(locs[self.n_patches + self.n_texts:])
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        pix_size = self.size * self.dpi
        image = bpy.data.images.new("text_texture", width=pix_size, height=pix_size,
                                     alpha=True)
        data = np.asarray(Image.open(buf), dtype=np.float32)[::-1, :] / 255.0
        image.pixels.foreach_set(data.ravel())
        image.pack()
        plt.close("all")
        return image

def make_text_cover(name="TextCover", text_builder=None, bbox=(0, 1, 0, 1)):
    if text_builder is None:
        text_builder = TextImageBuilder()
    image = text_builder.build_image(bbox)

    mat = _new_material(name)
    nt = mat.node_tree

    uv_map = nt.nodes.new("ShaderNodeUVMap")
    # Use UV map output directly (Reroute removed in Blender 5.0)
    uv_out = uv_map.outputs["UV"]

    # Voronoi textures for UV distortion
    vor1 = nt.nodes.new("ShaderNodeTexVoronoi")
    vor1.inputs["Scale"].default_value = 60.0
    nt.links.new(uv_out, vor1.inputs["Vector"])

    vor2 = nt.nodes.new("ShaderNodeTexVoronoi")
    vor2.inputs["Scale"].default_value = 60.0
    nt.links.new(uv_out, vor2.inputs["Vector"])

    # Mix voronoi positions
    mix_vor = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_vor, "data_type"):
        mix_vor.data_type = "RGBA"
    mix_vor.inputs[0].default_value = 0.5
    vor1_pos = vor1.outputs.get("Position") or vor1.outputs[1]
    vor2_pos = vor2.outputs.get("Position") or vor2.outputs[1]
    nt.links.new(vor1_pos, mix_vor.inputs[6])
    nt.links.new(vor2_pos, mix_vor.inputs[7])

    # Musgrave-like noise
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(uv_out, musgrave.inputs["Vector"])
    musgrave.inputs["Scale"].default_value = 1.0
    if "Detail" in musgrave.inputs:
        musgrave.inputs["Detail"].default_value = 5.6
    if "Lacunarity" in musgrave.inputs:
        musgrave.inputs["Lacunarity"].default_value = 1.4

    # Noise texture
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(uv_out, noise1.inputs["Vector"])
    noise1.inputs["Scale"].default_value = 35.4
    if "Detail" in noise1.inputs:
        noise1.inputs["Detail"].default_value = 3.3
    if "Roughness" in noise1.inputs:
        noise1.inputs["Roughness"].default_value = 1.0

    # Mix musgrave and noise
    mix_mn = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_mn, "data_type"):
        mix_mn.data_type = "RGBA"
    mix_mn.inputs[0].default_value = uniform(0.2, 1.0)
    nt.links.new(_noise_fac_output(musgrave), mix_mn.inputs[6])
    nt.links.new(noise1.outputs["Color"], mix_mn.inputs[7])

    # Mix voronoi blend with musgrave-noise blend
    mix_final = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_final, "data_type"):
        mix_final.data_type = "RGBA"
    mix_final.inputs[0].default_value = 0.0417
    nt.links.new(mix_vor.outputs[2], mix_final.inputs[6])
    nt.links.new(mix_mn.outputs[2], mix_final.inputs[7])

    # UV distortion mix
    uv_distort = nt.nodes.new("ShaderNodeMix")
    if hasattr(uv_distort, "data_type"):
        uv_distort.data_type = "RGBA"
    if np.random.uniform() < 0.5:
        uv_distort.inputs[0].default_value = uniform(0, 0.4)
    else:
        uv_distort.inputs[0].default_value = 1.0
    nt.links.new(mix_final.outputs[2], uv_distort.inputs[6])
    nt.links.new(uv_map.outputs["UV"], uv_distort.inputs[7])

    # Image texture
    img_tex = nt.nodes.new("ShaderNodeTexImage")
    img_tex.image = image
    nt.links.new(uv_distort.outputs[2], img_tex.inputs["Vector"])

    # Roughness noise
    roughness_noise = nt.nodes.new("ShaderNodeTexNoise")

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(img_tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(_noise_fac_output(roughness_noise), bsdf.inputs["Roughness"])
    _set_principled(bsdf,
                    Metallic=uniform(0, 0.5),
                    **{"Specular IOR Level": uniform(0, 0.2)})

    _connect_output(nt, bsdf)
    return mat

# --- Wear/tear (scratches + edge wear) ---

WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"

def get_scratch_params():
    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=log_uniform(5, 80),
        scratch_mask_ratio=log_uniform(0.01, 0.9),
        scratch_mask_noise=log_uniform(5, 40),
        scratch_depth=log_uniform(0.1, 1.0),
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
    try:
        map1.vector_type = "TEXTURE"
    except (TypeError, AttributeError):
        pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    try:
        map2.vector_type = "TEXTURE"
    except (TypeError, AttributeError):
        pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    map3 = nt.nodes.new("ShaderNodeMapping")
    try:
        map3.vector_type = "TEXTURE"
    except (TypeError, AttributeError):
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

def _build_edge_wear_graph(nt, original_bsdf_node, original_displacement_node, p):
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

    mul_a = _math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"],
                  clamp=True)
    mul_a1 = _math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0],
                   clamp=True)

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
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0],
                   clamp=True)
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
    try:
        vor_h.feature = "DISTANCE_TO_EDGE"
    except (TypeError, AttributeError):
        pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])

    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        vor_v.feature = "DISTANCE_TO_EDGE"
    except (TypeError, AttributeError):
        pass
    nt.links.new(map_v.outputs["Vector"], vor_v.inputs["Vector"])
    nt.links.new(scale_v.outputs[0], vor_v.inputs["Scale"])

    dist_h = vor_h.outputs.get("Distance") or vor_h.outputs[0]
    dist_v = vor_v.outputs.get("Distance") or vor_v.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_e = _color_ramp(nt, mul_dist.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_e = _math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"],
                  clamp=True)
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

# --- UV assignment for cover faces ---

def _read_face_normals(obj):
    mesh = obj.data
    mesh.update()
    normals = np.zeros(len(mesh.polygons) * 3)
    mesh.polygons.foreach_get("normal", normals)
    return normals.reshape(-1, 3)

def _ensure_uv(obj):
    if len(obj.data.uv_layers) == 0:
        select_only(obj)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode="OBJECT")

def assign_cover_material_with_uv(cover_obj, cover_material, texture_shared=True):
    """Apply cover material to the cover object with proper UV unwrapping.

    Mirrors wrap_front_back_side: assigns UV coordinates based on
    face normals (front=+Y, back=-Y, side=+Y/-Y), then assigns the material.
    """

    cover_obj.rotation_euler[0] = np.pi / 2
    apply_tf(cover_obj)

    # Smart UV project for the cover faces
    _ensure_uv(cover_obj)

    # Assign material
    cover_obj.data.materials.append(cover_material)

    # Rotate back
    cover_obj.rotation_euler[0] = -np.pi / 2
    apply_tf(cover_obj)

# --- BookFactory style (material params sampled in __init__) ---

class BookStyle:
    """Holds the material parameters for one book style."""

    def __init__(self):
        # Geometry params (from BookFactory.__init__)
        self.rel_scale = log_uniform(1, 1.5)
        self.skewness = log_uniform(1.3, 1.8)
        self.unit = 0.0127
        self.is_paperback = uniform() < 0.5
        self.margin = uniform(0.005, 0.01)
        self.offset = 0 if uniform() < 0.5 else log_uniform(0.002, 0.008)
        self.thickness = uniform(0.002, 0.003)

        # Plaster (paper) material generator: plaster.Plaster()
        # The Plaster class __init__ is trivial (no RNG), so no RNG consumed here
        # But we need to note that plaster_colored is sampled per-generate call

        # Text (cover) material: Text() constructor consumes RNG for colormap, etc.
        self.text_builder = TextImageBuilder()
        # Text.generate() → Text.make_shader_func(bbox) with default bbox
        # In the original, cover_surface = cover_surface_material_gen() which calls
        # This creates the material at __init__ time
        self.cover_material = make_text_cover(
            name=f"Cover_{id(self)}",
            text_builder=self.text_builder,
            bbox=(0, 1, 0, 1),
        )

        # The "if self.cover_surface == text.Text" check is always False
        # because cover_surface_material_gen() returns a Material, not the Text class

        # Wear/tear gates
        scratch_prob, edge_wear_prob = WEAR_TEAR_PROB
        self.do_scratch = uniform() <= scratch_prob
        self.scratch_params = get_scratch_params() if self.do_scratch else None
        self.do_edge_wear = uniform() <= edge_wear_prob
        self.edge_wear_params = get_edge_wear_params() if self.do_edge_wear else None

        self.texture_shared = uniform() < 0.2

    def make_paper_material(self):
        return make_plaster(name=f"Paper_{np.random.randint(100000)}")

# --- Geometry (copied from objects_blender/table_decorations/BookStackFactory.py)

def make_paper(width, height, depth):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    paper = bpy.context.active_object
    paper.location = (width / 2, height / 2, depth / 2)
    paper.scale = (width / 2 - 1e-4, height / 2, depth / 2 - 1e-4)
    apply_tf(paper, loc=True)
    return paper

def make_paperback(width, height, depth):
    paper = make_paper(width, height, depth)

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.location = (width / 2, height / 2, depth / 2)
    obj.scale = (width / 2, height / 2, depth / 2)
    apply_tf(obj, loc=True)

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

    return paper, obj  # Return separate parts for material assignment

def make_hardcover(width, height, depth, margin, offset, thickness):
    paper = make_paper(width, height, depth)

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    count = 8
    mod = obj.modifiers.new("ARRAY", "ARRAY")
    mod.count = count
    mod.relative_offset_displace = (0, 0, 1)
    mod.use_merge_vertices = True
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    obj.location = (1, 1, 1)
    apply_tf(obj, loc=True)

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

    x, y, z = read_co(obj).T
    ratio = np.minimum(z / depth, 1 - z / depth)
    x -= 4 * ratio * (1 - ratio) * offset
    obj.data.vertices.foreach_set("co", np.stack([x, y, z]).T.reshape(-1))
    obj.data.update()

    mod = obj.modifiers.new("SOLIDIFY", "SOLIDIFY")
    mod.thickness = thickness
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    return paper, obj  # Return separate parts for material assignment

def make_book_with_materials(style):
    width = int(log_uniform(0.08, 0.15) * style.rel_scale / style.unit) * style.unit
    height = int(width * style.skewness / style.unit) * style.unit
    depth = uniform(0.01, 0.02) * style.rel_scale

    # Create paper material (per-book, like surface_material_gen())
    paper_mat = style.make_paper_material()

    if style.is_paperback:
        paper, cover = make_paperback(width, height, depth)
    else:
        paper, cover = make_hardcover(width, height, depth,
                                       style.margin, style.offset, style.thickness)

    # Assign paper material
    paper.data.materials.append(paper_mat)

    # Assign cover material with UV unwrap
    assign_cover_material_with_uv(cover, style.cover_material, style.texture_shared)

    # Join paper and cover
    obj = join_objs([paper, cover])
    return obj

# --- Main: BookStackFactory ---

def make_book_stack():
    seed_all(SEED)

    n_styles = np.random.randint(1, 4)
    styles = []
    for _ in range(n_styles):
        _book_seed = np.random.randint(int(1e5))
        # BookFactory.__init__ is called with book_seed, but within the
        # the BookStackFactory stream (BookFactory.__init__ does NOT reseed)
        # WAIT: Actually, looking at the code more carefully:
        # BookFactory(np.random.randint(1e5)) — the np.random.randint(1e5)
        # consumes one RNG value, then BookFactory.__init__ is called.
        # AssetFactory.__init__ just stores factory_seed (no reseed).
        # BookFactory.__init__ body then consumes from the SAME RNG stream.
        # So the book style params are determined by the BookStackFactory seed.
        styles.append(BookStyle())

    n_books = int(log_uniform(5, 15))
    _angle_gate = uniform()
    max_angle = uniform(np.pi / 9, np.pi / 6) if _angle_gate < 0.7 else 0
    # max_rel_scale and max_skewness are derived, no RNG consumed

    # continues (no reseed in BookStackFactory.create_asset)
    books = []
    stack_offset = 0
    for i in range(n_books):
        style = styles[np.random.randint(0, len(styles))]
        saved_state = np.random.get_state()

        # Create book geometry + materials
        obj = make_book_with_materials(style)

        np.random.set_state(saved_state)
        # Consume one random for style choice above (already consumed)

        # Center XY, stack on Z
        co = read_co(obj)
        cx = (co[:, 0].min() + co[:, 0].max()) / 2
        cy = (co[:, 1].min() + co[:, 1].max()) / 2
        obj.location = (-cx, -cy, stack_offset - co[:, 2].min())
        obj.rotation_euler[2] = uniform(-max_angle, max_angle)
        apply_tf(obj, loc=True)

        co = read_co(obj)
        stack_offset = co[:, 2].max()
        books.append(obj)

    # Join all books
    stack = join_objs(books)
    stack.name = "BookStack"

    # to its own books. Since we joined them all, we apply to the whole stack
    # using the first style's wear_tear settings (simplification — original
    # applies per-factory, but since materials are per-factory already,
    # the wear_tear modifies each material's node tree independently)
    for style in styles:
        if style.do_scratch:
            apply_scratches(stack, **style.scratch_params)
        if style.do_edge_wear:
            apply_edge_wear(stack, **style.edge_wear_params)

    return stack

# --- Entry point ---

clear_scene()
stack = make_book_stack()
print(f"BookStack created: {len(stack.data.vertices)} verts, "
      f"{len(stack.data.polygons)} faces, "
      f"{len(stack.data.materials)} material slots")

