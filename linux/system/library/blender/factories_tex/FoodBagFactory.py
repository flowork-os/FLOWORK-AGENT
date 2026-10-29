# [FL_INDEX: keywords="blender_factory, procedural_3d, FoodBagFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FoodBagFactory | Category: factories_tex
# Prompt: A 3D model of a flexible food packaging bag rendered from a three-quarter perspective. The bag features a tall, thin flat pouch form with a slightly pinched and folded top seal, colorful printed surface patterns including dots, stripes, and geometric sections in green, pink, and black, and a gusset fold along the bottom edge.

# FoodBagFactory -- textured conversion
#
# Geometry copied verbatim from:
#   objects_blender/tableware/FoodBagFactory.py
# Shaders translated faithfully from:
# UV mapping translated from:
# Surface displacement from:
# Wear/tear: none
#
# Material binding model:
#   weighted_sample(graphicdesign) picks Text(90.9%) or BasicBSDF(9.1%).
#   Text generates a matplotlib figure (patches + text + barcodes) and uses it as
#   an image texture, UV-mapped with Voronoi+Noise distortion.
#   wrap_front_back assigns material to front/back faces based on normals.

import os
import io
import math
import string
import colorsys
import random

import bpy
import bmesh
import numpy as np
from numpy.random import uniform, rand, normal

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.font_manager
    from matplotlib.patches import (
        Arrow, BoxStyle, Circle, Ellipse, FancyBboxPatch,
        Rectangle, RegularPolygon, Wedge,
    )
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from sklearn.linear_model import LinearRegression
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Seed

SEED = int(os.environ.get("SEED", "0"))
np.random.seed(SEED)
random.seed(SEED)

# Helpers

def log_uniform(low, high, size=None):
    return np.exp(np.random.uniform(np.log(low), np.log(high), size))

def clip_gaussian(mean, std, lo, hi, max_tries=20):
    for _ in range(max_tries):
        val = np.random.normal(mean, std)
        if lo <= val <= hi:
            return val
    return np.clip(np.random.normal(mean, std), lo, hi)

def weighted_sample(registry):
    classes, weights = zip(*registry)
    w = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=w / w.sum()))]

def hsv2rgba_tuple(h, s, v):
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    bpy.context.scene.cursor.location = (0, 0, 0)

def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_transform(obj, loc=False):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)

def modify_mesh(obj, mod_type, apply=True, **kwargs):
    select_only(obj)
    mod = obj.modifiers.new(name=mod_type, type=mod_type)
    for k, v in kwargs.items():
        setattr(mod, k, v)
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', arr)
    return arr.reshape(-1, 3)

def write_co(obj, arr):
    obj.data.vertices.foreach_set('co', arr.reshape(-1))

def subsurf(obj, levels, simple=False):
    if levels > 0:
        modify_mesh(obj, 'SUBSURF',
                     levels=levels, render_levels=levels,
                     subdivision_type='SIMPLE' if simple else 'CATMULL_CLARK')

def read_edges(obj):
    arr = np.zeros(len(obj.data.edges) * 2, dtype=int)
    obj.data.edges.foreach_get('vertices', arr)
    return arr.reshape(-1, 2)

def normalize_vec(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    n[n == 0] = 1
    return v / n

def read_edge_direction(obj):
    cos = read_co(obj)[read_edges(obj).reshape(-1)].reshape(-1, 2, 3)
    return normalize_vec(cos[:, 1] - cos[:, 0])

def subdivide_edge_ring(obj, cuts=64, axis=(0, 0, 1)):
    bpy.ops.object.select_all(action='DESELECT')
    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    selected = (
        np.abs((read_edge_direction(obj) * np.array(axis)[np.newaxis, :]).sum(1))
        > 1 - 1e-3
    )
    edges = [bm.edges[i] for i in np.nonzero(selected)[0]]
    bmesh.ops.subdivide_edgering(bm, edges=edges, cuts=int(cuts))
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def new_base_cylinder():
    bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    apply_transform(obj, loc=True)
    return obj

def read_loop_vertices(obj):
    arr = np.zeros(len(obj.data.loops), dtype=int)
    obj.data.loops.foreach_get('vertex_index', arr)
    return arr

def read_loop_edges(obj):
    arr = np.zeros(len(obj.data.loops), dtype=int)
    obj.data.loops.foreach_get('edge_index', arr)
    return arr

def read_loop_starts(obj):
    arr = np.zeros(len(obj.data.polygons), dtype=int)
    obj.data.polygons.foreach_get('loop_start', arr)
    return arr

def read_loop_totals(obj):
    arr = np.zeros(len(obj.data.polygons), dtype=int)
    obj.data.polygons.foreach_get('loop_total', arr)
    return arr

def read_normal(obj):
    arr = np.zeros(len(obj.data.polygons) * 3)
    obj.data.polygons.foreach_get('normal', arr)
    return arr.reshape(-1, 3)

def read_uv(obj):
    if len(obj.data.uv_layers) == 0:
        return np.zeros((len(obj.data.loops), 2))
    uv_layer = obj.data.uv_layers.active
    arr = np.zeros(len(obj.data.loops) * 2)
    uv_layer.data.foreach_get('uv', arr)
    return arr.reshape(-1, 2)

def write_uv(obj, uv_arr):
    if len(obj.data.uv_layers) == 0:
        obj.data.uv_layers.new(name="UVMap")
    uv_layer = obj.data.uv_layers.active
    uv_layer.data.foreach_set('uv', uv_arr.reshape(-1))

def face_corner2faces(obj):
    loop_starts = read_loop_starts(obj)
    faces = np.zeros(len(obj.data.loops), dtype=int)
    faces[loop_starts] = 1
    faces = np.cumsum(faces) - 1
    return faces

def ensure_uv(obj):
    if len(obj.data.uv_layers) == 0:
        select_only(obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

def unwrap_faces_selection(obj, selection):
    """Unwrap faces identified by boolean per-face selection array."""

    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bpy.ops.mesh.select_all(action='DESELECT')
    for i, sel in enumerate(selection):
        if sel:
            bm.faces[i].select_set(True)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')

def str2vec(axis):
    if not isinstance(axis, str):
        return np.array(axis)
    table = {
        'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1),
        'u': (-1, 0, 0), 'v': (0, -1, 0), 'w': (0, 0, -1),
    }
    ch = axis[-1].lower()
    vec = np.array(table[ch], dtype=float)
    if axis[0] == '-':
        vec = -vec
    return vec

def compute_uv_direction(obj, x_axis='x', y_axis='y', selection=None):
    """Compute UV coords that align with world-space x_axis/y_axis directions."""

    ensure_uv(obj)
    x_vec, y_vec = str2vec(x_axis), str2vec(y_axis)
    co = read_co(obj)
    edges = read_edges(obj)
    loop_vertices = read_loop_vertices(obj)
    loop_edges_arr = read_loop_edges(obj)
    uv = read_uv(obj)
    if selection is None:
        selection = np.full(len(uv), True)
    selection = selection.astype(bool)
    loop_starts = read_loop_starts(obj)
    loop_totals_arr = read_loop_totals(obj)
    next_vertices = edges[loop_edges_arr].sum(1) - loop_vertices
    next_loops = np.arange(len(uv)) + 1
    next_loops[loop_starts + loop_totals_arr - 1] -= loop_totals_arr
    uv_diff = uv[next_loops] - uv
    co_diff = co[next_vertices] - co[loop_vertices]

    if HAS_SKLEARN and selection.sum() > 3:
        lr = LinearRegression()
        lr.fit(co_diff[selection], uv_diff[selection])
        lr.coef_[lr.coef_ > 1e3] = 0
        axes = lr.predict(np.stack([x_vec, y_vec]))
    else:
        # Fallback: project directly
        axes = np.stack([x_vec[:2], y_vec[:2]])

    norms = np.linalg.norm(axes, axis=-1) + 1e-6
    axes = axes / norms[:, np.newaxis]
    pred = uv @ axes.T
    pred_sel = pred[selection]
    x_min, x_max = np.min(pred_sel[:, 0]), np.max(pred_sel[:, 0])
    y_min, y_max = np.min(pred_sel[:, 1]), np.max(pred_sel[:, 1])
    if x_max - x_min > y_max - y_min:
        scale = 1 / (x_max - x_min + 1e-4)
        mid = (y_max + y_min) / 2
        pred = np.stack(
            [(pred[:, 0] - x_min) * scale, (pred[:, 1] - mid) * scale + 0.5], -1
        )
        bbox = (
            0, 1,
            0.5 - 0.5 * (y_max - y_min) * scale,
            0.5 + 0.5 * (y_max - y_min) * scale,
        )
    else:
        scale = 1 / (y_max - y_min + 1e-4)
        mid = (x_max + x_min) / 2
        pred = np.stack(
            [(pred[:, 0] - mid) * scale + 0.5, (pred[:, 1] - y_min) * scale], -1
        )
        bbox = (
            0.5 - 0.5 * (x_max - x_min) * scale,
            0.5 + 0.5 * (x_max - x_min) * scale,
            0, 1,
        )
    new_uv = np.where(selection[:, np.newaxis], pred, uv)
    write_uv(obj, new_uv)
    return bbox

def wrap_sides(obj, mat, axes_str, xs_str, ys_str, groupings=None):
    """Assign material to faces based on normal direction, compute UVs.
    axes_str: one char per axis direction (e.g. 'vy' for front-back)."""

    fc2f = face_corner2faces(obj)
    axes = np.array([str2vec(c) for c in axes_str])
    face_normals = read_normal(obj)
    face_dirs = np.argmax(face_normals @ axes.T, -1)
    selections = []
    bboxes = []
    for i in range(len(axes)):
        selected = (face_dirs == i).astype(float)
        selections.append(selected)
        unwrap_faces_selection(obj, selected)
        bboxes.append(
            compute_uv_direction(
                obj,
                str2vec(xs_str[i]),
                str2vec(ys_str[i]),
                selected.astype(bool)[fc2f],
            )
        )
    # Assign material to the object
    if mat is not None:
        if mat.name not in [ms.name for ms in obj.data.materials]:
            obj.data.materials.append(mat)

def wrap_front_back(obj, mat, shared=True):
    wrap_sides(obj, mat, 'vy', 'xu', 'zz', [[0, 1]] if shared else None)

_CHAR_SET = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
_CHAR_WEIGHTS = np.concatenate([
    1.5 * np.ones(len(string.ascii_lowercase)),
    0.5 * np.ones(len(string.ascii_uppercase)),
    0.5 * np.ones(len(string.digits)),
])
_CHAR_WEIGHTS = _CHAR_WEIGHTS / _CHAR_WEIGHTS.sum()

def generate_text():
    return "".join(
        np.random.choice(
            _CHAR_SET,
            size=int(clip_gaussian(3, 7, 2, 15)),
            replace=True,
            p=_CHAR_WEIGHTS,
        )
    )

def _weighted_choice_patch():
    """Weighted random choice among patch types (mirrors text.py patch_fns)."""

    fns = [(2, Circle), (4, Rectangle), (1, Wedge), (1, RegularPolygon),
           (1, Ellipse), (2, Arrow), (2, FancyBboxPatch)]
    weights = np.array([w for w, _ in fns], dtype=float)
    idx = int(np.random.choice(len(fns), p=weights / weights.sum()))
    return fns[idx][1]

def _decimate_points(points, n):
    """Select n well-separated points from the given array (simplified decimate)."""

    if len(points) <= n:
        return points
    # Simple greedy farthest-point sampling
    selected = [0]
    for _ in range(n - 1):
        dists = np.min(
            np.linalg.norm(points[:, None, :] - points[None, np.array(selected), :], axis=-1),
            axis=-1,
        )
        selected.append(int(np.argmax(dists)))
    return points[selected]

class TextImageGenerator:
    """Generates a matplotlib-based text/graphic image for use as a texture."""



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
        self.barcode_aspect = float(log_uniform(1.5, 3))
        self.emission = emission

    @staticmethod
    def _build_diverging_colormap():
        count = 20
        hue = (uniform() + np.linspace(0, 0.5, count)) % 1
        mid = uniform(0.6, 0.8)
        lightness = np.concatenate([
            np.linspace(uniform(0.1, 0.3), mid, count // 2),
            np.linspace(mid, uniform(0.1, 0.3), count // 2),
        ])
        saturation = np.concatenate(
            [np.linspace(1, 0.5, count // 2), np.linspace(0.5, 1, count // 2)]
        )
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
        saturation = np.concatenate(
            [np.linspace(1, 0.5, count // 2), np.linspace(0.5, 1, count // 2)]
        )
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
            return np.array([1.0, 1.0, 1.0])
        elif r < self.white_chance + self.black_chance:
            return np.array([0.0, 0.0, 0.0])
        else:
            return self.colormap[np.random.randint(len(self.colormap))]

    @property
    def random_colors(self):
        while True:
            c, d = self.random_color, self.random_color
            if np.abs(c - d).sum() > 0.2:
                return c, d

    @staticmethod
    def _loc_uniform(min_, max_, size=None):
        ratio = 0.1
        return uniform(
            min_ + ratio * (max_ - min_), min_ + (1 - ratio) * (max_ - min_), size
        )

    @staticmethod
    def _scale_uniform(min_, max_):
        return (max_ - min_) * float(log_uniform(0.2, 0.8))

    def _get_locs(self, bbox, n):
        m = 8 * n
        x = self._loc_uniform(bbox[0], bbox[1], m)
        y = self._loc_uniform(bbox[2], bbox[3], m)
        pts = np.stack([x, y], -1)
        return _decimate_points(pts, n)

    def _add_divider(self, rs):
        if uniform() < 0.6:
            return
        a = 0 if uniform() < 0.7 else float(uniform(5, 10))
        x = self._loc_uniform(rs[0], rs[1])
        y = self._loc_uniform(rs[2], rs[3])
        if rs[0] == 0 or self.force_horizontal:
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
            fn = _weighted_choice_patch()
            kwargs = {
                "alpha": float(uniform(0.5, 0.8)) if uniform() < 0.2 else 1.0,
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
                "hatch": np.random.choice(list({"/", "\\", "|", "-", "+", "x", "o", "O", ".", "*"}))
                    if uniform() < 0.3 else "none",
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
                        patch = Wedge(
                            (x, y), r, start, start + float(uniform(0, 360)),
                            width=float(uniform(0.2, 0.8)) * r, **kwargs,
                        )
                    case "RegularPolygon":
                        patch = RegularPolygon(
                            (x, y), np.random.randint(3, 9), radius=r, **kwargs
                        )
                    case "Ellipse":
                        patch = Ellipse((x, y), w, h, **kwargs)
                    case "Arrow":
                        w_ = w if uniform() < 0.5 else -w
                        h_ = h if uniform() < 0.5 else -h
                        patch = Arrow(
                            x - w_ / 2, y - h_ / 2, w, h,
                            width=float(log_uniform(0.6, 1.5)), **kwargs,
                        )
                    case "FancyBboxPatch":
                        pad = float(uniform(0.2, 0.4)) * min(w, h)
                        box_style = np.random.choice(
                            list(BoxStyle.get_styles().values())
                        )(pad=pad)
                        patch = FancyBboxPatch(
                            (x_, y_), w - pad, h - pad, box_style,
                            mutation_scale=float(log_uniform(0.6, 1.5)),
                            mutation_aspect=float(log_uniform(0.6, 1.5)),
                            **kwargs,
                        )
                    case _:
                        continue
                plt.gca().add_patch(patch)
            except (MemoryError, ValueError):
                pass

    def _add_texts(self, locs):
        # Use system default font (no custom fonts)
        for x, y in locs:
            x_c = 0.5 + (x - 0.5) * 0.6
            txt = generate_text()
            color, bg_color = self.random_colors
            plt.figtext(
                x_c, y, txt,
                family="DejaVu Sans",
                size=float(log_uniform(0.75, 1.0))
                    * self.dpi * clip_gaussian(0.3, 0.2, 0.2, 0.65),
                ha="center", va="center",
                c=color,
                rotation=float(uniform(-10, 10)),
                wrap=True,
                fontweight=np.random.choice(["normal", "bold", "heavy"]),
                fontstyle=np.random.choice(["normal", "italic", "oblique"]),
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
            ax.imshow(
                code.reshape(1, -1), cmap="binary",
                aspect="auto", interpolation="nearest",
            )

    def build_image(self, bbox):
        """Create a bpy.data.images from matplotlib figure."""

        fig = plt.figure(figsize=(self.size, self.size), dpi=self.dpi)
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set_facecolor(self.random_color)
        total = self.n_patches + self.n_texts + self.n_barcodes
        locs = self._get_locs(bbox, total)
        self._add_divider(bbox)
        self._add_patches(locs[: self.n_patches], bbox)
        self._add_texts(locs[self.n_patches : self.n_patches + self.n_texts])
        self._add_barcodes(locs[self.n_patches + self.n_texts :])
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        px_size = self.size * self.dpi
        image = bpy.data.images.new("text_texture", width=px_size, height=px_size, alpha=True)
        data = np.asarray(Image.open(buf), dtype=np.float32)[::-1, :] / 255.0
        image.pixels.foreach_set(data.ravel())
        image.pack()
        plt.close("all")
        plt.clf()
        return image

# Material helpers

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac(node):
    """Noise/Wave Fac output (Blender 5.0 renamed Fac -> Factor)."""

    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

def _connect_out(nt, surface_node, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(surface_node.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement.outputs[0], out.inputs["Displacement"])

# Shader: Text (image-based with Voronoi+Noise UV distortion)

def make_text_material(tex_gen, bbox):
    """Build the Text shader material (translates text.py::Text.make_shader_func)."""

    image = tex_gen.build_image(bbox)

    mat = _new_mat("FoodBag_Text")
    nt = mat.node_tree
    ln = nt.links.new

    # UV Map
    uv_map = nt.nodes.new("ShaderNodeUVMap")

    reroute = nt.nodes.new("NodeReroute")
    ln(uv_map.outputs["UV"], reroute.inputs[0])

    # Voronoi 1
    vor1 = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(reroute.outputs[0], vor1.inputs["Vector"])
    vor1.inputs["Scale"].default_value = 60.0

    # Voronoi 2
    vor2 = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(reroute.outputs[0], vor2.inputs["Vector"])
    vor2.inputs["Scale"].default_value = 60.0

    # Mix voronoi positions
    mix_vor = nt.nodes.new("ShaderNodeMix")
    mix_vor.data_type = "RGBA"
    ln(vor1.outputs["Position"], mix_vor.inputs[6])
    ln(vor2.outputs["Position"], mix_vor.inputs[7])

    # Noise texture (replacing MusgraveTexture which is removed in Blender 5.0)
    noise_musgrave = nt.nodes.new("ShaderNodeTexNoise")
    ln(reroute.outputs[0], noise_musgrave.inputs["Vector"])
    noise_musgrave.inputs["Scale"].default_value = 5.0
    noise_musgrave.inputs["Detail"].default_value = 5.6
    noise_musgrave.inputs["Roughness"].default_value = 0.5
    # Musgrave had Dimension=1.4; noise approximation is acceptable

    # Another noise
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    ln(reroute.outputs[0], noise2.inputs["Vector"])
    noise2.inputs["Scale"].default_value = 35.4
    noise2.inputs["Detail"].default_value = 3.3
    noise2.inputs["Roughness"].default_value = 1.0

    # Mix musgrave+noise
    mix_noise = nt.nodes.new("ShaderNodeMix")
    mix_noise.data_type = "RGBA"
    mix_noise.inputs[0].default_value = float(uniform(0.2, 1.0))
    ln(_fac(noise_musgrave), mix_noise.inputs[6])
    ln(noise2.outputs["Color"], mix_noise.inputs[7])

    # Mix voronoi blend + noise blend
    mix_combined = nt.nodes.new("ShaderNodeMix")
    mix_combined.data_type = "RGBA"
    mix_combined.inputs[0].default_value = 0.0417
    ln(mix_vor.outputs[2], mix_combined.inputs[6])
    ln(mix_noise.outputs[2], mix_combined.inputs[7])

    # Final UV distortion mix
    mix_final = nt.nodes.new("ShaderNodeMix")
    mix_final.data_type = "RGBA"
    if rand() < 0.5:
        mix_final.inputs[0].default_value = float(uniform(0, 0.4))
    else:
        mix_final.inputs[0].default_value = 1.0
    ln(mix_combined.outputs[2], mix_final.inputs[6])
    ln(uv_map.outputs["UV"], mix_final.inputs[7])

    # Image texture
    img_tex = nt.nodes.new("ShaderNodeTexImage")
    img_tex.image = image
    ln(mix_final.outputs[2], img_tex.inputs["Vector"])

    # Roughness noise
    roughness_noise = nt.nodes.new("ShaderNodeTexNoise")

    # Principled BSDF
    emission = tex_gen.emission
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    if emission > 0:
        bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.05
        ln(img_tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission
    else:
        ln(img_tex.outputs["Color"], bsdf.inputs["Base Color"])
        ln(_fac(roughness_noise), bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = float(uniform(0, 0.5))
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = float(uniform(0, 0.2))

    _connect_out(nt, bsdf)
    return mat

# Shader: BasicBSDF (simple random-colour PrincipledBSDF)

def make_basic_bsdf_material():
    """Translates dev/basic_bsdf.py::shader_basic_bsdf."""

    hsv = uniform(0.05, 0.95, 3)
    mat = _new_mat("FoodBag_BasicBSDF")
    nt = mat.node_tree

    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = hsv2rgba_tuple(hsv[0], hsv[1], hsv[2])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(rgb.outputs[0], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(np.clip(normal(0.6, 0.3), 0.05, 0.95))
    bsdf.inputs["Metallic"].default_value = float(uniform(0, 1)) if uniform() < 0.3 else 0.0

    _connect_out(nt, bsdf)
    return mat

# geo_extension GeoNodes modifier (surface displacement)

def _noise_fac_output(node):
    for name in ("Fac", "Factor"):
        if name in node.outputs:
            return node.outputs[name]
    return node.outputs[0]

def build_geo_extension(noise_strength=0.2, noise_scale=2.0):
    """Build GeoNodes group for surface noise displacement.
    Uses NoiseTexture (replacing MusgraveTexture removed in Blender 5.0)."""

    noise_strength = float(uniform(noise_strength / 2, noise_strength))
    noise_scale = float(uniform(noise_scale * 0.7, noise_scale * 1.4))
    direction_offset = uniform(-1, 1, 3)

    ng = bpy.data.node_groups.new("geo_extension", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')
    go.is_active_output = True

    pos = ng.nodes.new('GeometryNodeInputPosition')

    # direction = normalize(pos) + offset
    length_node = ng.nodes.new('ShaderNodeVectorMath')
    length_node.operation = 'LENGTH'
    ng.links.new(pos.outputs[0], length_node.inputs[0])

    inv_len = ng.nodes.new('ShaderNodeMath')
    inv_len.operation = 'DIVIDE'
    inv_len.inputs[0].default_value = 1.0
    ng.links.new(length_node.outputs['Value'], inv_len.inputs[1])

    dir_scale = ng.nodes.new('ShaderNodeVectorMath')
    dir_scale.operation = 'SCALE'
    ng.links.new(pos.outputs[0], dir_scale.inputs[0])
    ng.links.new(inv_len.outputs[0], dir_scale.inputs['Scale'])

    dir_add = ng.nodes.new('ShaderNodeVectorMath')
    dir_add.operation = 'ADD'
    ng.links.new(dir_scale.outputs[0], dir_add.inputs[0])
    dir_add.inputs[1].default_value = tuple(float(v) for v in direction_offset)

    # noise(direction) * strength
    noise_tex = ng.nodes.new('ShaderNodeTexNoise')
    ng.links.new(dir_add.outputs[0], noise_tex.inputs['Vector'])
    noise_tex.inputs['Scale'].default_value = noise_scale

    add_quarter = ng.nodes.new('ShaderNodeMath')
    add_quarter.operation = 'ADD'
    ng.links.new(_noise_fac_output(noise_tex), add_quarter.inputs[0])
    add_quarter.inputs[1].default_value = 0.25

    mul_strength = ng.nodes.new('ShaderNodeMath')
    mul_strength.operation = 'MULTIPLY'
    ng.links.new(add_quarter.outputs[0], mul_strength.inputs[0])
    mul_strength.inputs[1].default_value = noise_strength

    # offset = pos * musgrave_value
    offset_scale = ng.nodes.new('ShaderNodeVectorMath')
    offset_scale.operation = 'SCALE'
    ng.links.new(pos.outputs[0], offset_scale.inputs[0])
    ng.links.new(mul_strength.outputs[0], offset_scale.inputs['Scale'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(gi.outputs[0], set_pos.inputs['Geometry'])
    ng.links.new(offset_scale.outputs[0], set_pos.inputs['Offset'])

    ng.links.new(set_pos.outputs[0], go.inputs[0])
    return ng

def apply_geo_extension(obj):
    """Apply geo_extension GeoNodes modifier to object."""

    ng = build_geo_extension()
    mod = obj.modifiers.new("geo_extension", 'NODES')
    mod.node_group = ng
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

# Geometry (verbatim from objects_blender/tableware/FoodBagFactory.py)

def add_seal(obj, length, extrude_length):
    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    co = read_co(obj)
    for i in [-1, 1]:
        bpy.ops.mesh.select_all(action='DESELECT')
        bm.verts.ensure_lookup_table()
        indices = np.nonzero(co[:, -1] * i >= length / 2 - 1e-3)[0]
        for idx in indices:
            bm.verts[idx].select_set(True)
        bm.select_flush(False)
        bmesh.update_edit_mesh(obj.data)
        bpy.ops.mesh.extrude_edges_move(
            TRANSFORM_OT_translate={'value': (0, 0, extrude_length * length * i)}
        )
    bpy.ops.object.mode_set(mode='OBJECT')

# Main factory

# Material registry (mirrors material_assignments.graphicdesign)
GRAPHICDESIGN_REGISTRY = [
    ("Text", 1.0),
    ("BasicBSDF", 0.1),
]

def create_food_bag():
    # -- Sample parameters (mirrors FoodBagFactory.__init__ with FixedSeed) --
    length = float(uniform(0.1, 0.3))
    is_packet = uniform() < 0.6
    if is_packet:
        width = length * float(log_uniform(0.6, 1.0))
        depth_val = width * float(uniform(0.5, 0.8))
        curve_profile = float(uniform(2, 4))
    else:
        width = length * float(log_uniform(0.2, 0.4))
        depth_val = width * float(uniform(0.6, 1.0))
        curve_profile = float(uniform(4, 8))
    extrude_length = float(uniform(0.05, 0.1))

    # Material selection (mirrors weighted_sample(graphicdesign))
    mat_choice = weighted_sample(GRAPHICDESIGN_REGISTRY)
    texture_shared = uniform() < 0.2

    # -- Geometry --
    obj = new_base_cylinder()
    subdivide_edge_ring(obj, 64)
    obj.scale = width / 2, depth_val / 2, length / 2
    apply_transform(obj)
    x, y, z = read_co(obj).T
    ratio = 1 - (2 * np.abs(z) / length) ** curve_profile
    write_co(obj, np.stack([x, ratio * y, z], -1))
    modify_mesh(obj, 'WELD', merge_threshold=1e-3)

    add_seal(obj, length, extrude_length)

    # -- UV + Material assignment --
    # Before subsurf, handle UV and material like the original
    if mat_choice == "Text" and HAS_MATPLOTLIB and HAS_PIL:
        tex_gen = TextImageGenerator(has_barcode=True, emission=0)
        # Rotate for UV if not packet (original does this before wrap_front_back)
        if not is_packet:
            obj.rotation_euler[1] = np.pi / 2
            apply_transform(obj)

        # UV unwrap front/back faces
        wrap_front_back(obj, None, shared=bool(texture_shared))

        # Build material with the UV bbox (use default (0,1,0,1))
        mat = make_text_material(tex_gen, (0, 1, 0, 1))
        obj.data.materials.append(mat)

        # Rotate back if not packet
        if not is_packet:
            obj.rotation_euler[1] = -np.pi / 2
            apply_transform(obj)
    else:
        # BasicBSDF fallback
        if not is_packet:
            obj.rotation_euler[1] = np.pi / 2
            apply_transform(obj)
        mat = make_basic_bsdf_material()
        obj.data.materials.append(mat)
        if not is_packet:
            obj.rotation_euler[1] = -np.pi / 2
            apply_transform(obj)

    # -- Subdivision --
    subsurf(obj, 2)

    # -- Surface displacement (geo_extension with musgrave_dimensions="2D") --
    apply_geo_extension(obj)

    return obj

# Entry point

clear_scene()
create_food_bag()

