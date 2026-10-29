# [FL_INDEX: keywords="blender_factory, procedural_3d, CountertopFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CountertopFactory | Category: factories_geo
# Prompt: A 3D model of a countertop assembly rendered from a three-quarter perspective, featuring a flat horizontal surface composed of multiple intersecting slab segments arranged in an L-shaped or cross-shaped layout with clean angular edges and a light gray appearance.

"""CountertopFactory (geometry + materials).

Converted from:
  objects_blender/shelves/CountertopFactory.py   (geometry)
                                                  wood_tile weighted branch,
                                                  see note below)

Notes
-----
(marble, ceramic, wood_tile) and then applies it in `finalize_assets` by
scanning `dir(self.surface)` for a class that has an `.apply` method.

* `marble.Marble.apply`  exists                 -> applied
* `ceramic.Ceramic.apply` exists                -> applied
  and applies NOTHING when the weighted_choice hits the wood_tile branch.

To still give the 2/9 "wood_tile" seeds a visually meaningful shader (rather
than matching the upstream bug and producing an untextured mesh) we use the
faithful raw-bpy port of `shader_wood` for that weighted branch. The weights
and raw-SEED sampling order are preserved so the per-seed material choice
"""
# SEED-deterministic: all random calls seeded from SEED

import os, math, bpy, bmesh, random, colorsys, hashlib, contextlib
import numpy as np
from types import SimpleNamespace
import shapely
from shapely import remove_repeated_points, simplify
from shapely.ops import orient

# ============================================================================
# === Inlined material library (hand-crafted for CountertopFactory) ==========
# ============================================================================

def seed_all(seed):
    np.random.seed(int(seed))
    random.seed(int(seed))


def _mat_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))


def hsv2rgba(h, s, v):
    h = h - math.floor(h)
    s = float(max(0.0, min(1.0, s)))
    v = float(max(0.0, min(1.0, v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def bark_hsv():
    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e",
                "#6b4423", "#5d4037", "#7b3f00"]
    picked = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(picked[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)


def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat


def _set_principled(bsdf, **kwargs):
    """Version-tolerant Principled BSDF input setter (4.x vs 5.x)."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Coat Roughness": ("Coat Roughness", "Clearcoat Roughness"),
        "Subsurface Weight": ("Subsurface Weight", "Subsurface"),
        "Subsurface Radius": ("Subsurface Radius",),
    }
    for key, val in kwargs.items():
        candidates = aliases.get(key, (key,))
        for candidate in candidates:
            if candidate in bsdf.inputs:
                try:
                    bsdf.inputs[candidate].default_value = val
                except Exception:
                    pass
                break


def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]


def _voronoi_distance_output(vor_node):
    if "Distance" in vor_node.outputs:
        return vor_node.outputs["Distance"]
    return vor_node.outputs[0]


def _set_noise_dims(node, dims):
    if hasattr(node, "noise_dimensions"):
        try:
            node.noise_dimensions = dims
            return
        except TypeError:
            pass
    if dims == "4D" and hasattr(node, "noise_dimensions"):
        try:
            node.noise_dimensions = "3D"
        except TypeError:
            pass


def _set_voronoi_dims(node, dims):
    if hasattr(node, "voronoi_dimensions"):
        try:
            node.voronoi_dimensions = dims
            return
        except TypeError:
            pass
    if dims == "4D" and hasattr(node, "voronoi_dimensions"):
        try:
            node.voronoi_dimensions = "3D"
        except TypeError:
            pass


def _connect_output(nt, bsdf, displacement_socket=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement_socket is not None:
        nt.links.new(displacement_socket, out.inputs["Displacement"])
    return out


def _build_float_curve(nt, value_socket, anchors):
    """Mirror of NodeWrangler.build_float_curve for a small anchor list."""

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
def make_marble(name="Marble"):
    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    scale_vec = nt.nodes.new("ShaderNodeVectorMath")
    scale_vec.operation = "SCALE"
    nt.links.new(tex_coord.outputs["Object"], scale_vec.inputs[0])

    vector_rotate = nt.nodes.new("ShaderNodeVectorRotate")
    if hasattr(vector_rotate, "rotation_type"):
        try:
            vector_rotate.rotation_type = "EULER_XYZ"
        except TypeError:
            pass
    nt.links.new(scale_vec.outputs["Vector"], vector_rotate.inputs["Vector"])

    seed_val = nt.nodes.new("ShaderNodeValue")
    seed_val.label = "seed"
    seed_val.outputs[0].default_value = 0.0

    scale_val = nt.nodes.new("ShaderNodeValue")
    scale_val.label = "scale"
    scale_val.outputs[0].default_value = 3.0

    add_scale = nt.nodes.new("ShaderNodeMath")
    add_scale.operation = "ADD"
    nt.links.new(scale_val.outputs[0], add_scale.inputs[0])
    add_scale.inputs[1].default_value = 1.0

    noise_tex_2 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex_2, "4D")
    nt.links.new(vector_rotate.outputs["Vector"], noise_tex_2.inputs["Vector"])
    if "W" in noise_tex_2.inputs:
        nt.links.new(seed_val.outputs[0], noise_tex_2.inputs["W"])
    nt.links.new(add_scale.outputs[0], noise_tex_2.inputs["Scale"])
    if "Detail" in noise_tex_2.inputs:
        noise_tex_2.inputs["Detail"].default_value = 15.0

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.48
    map_range.inputs[2].default_value = 0.60
    nt.links.new(_noise_fac_output(noise_tex_2), map_range.inputs[0])

    noise_tex = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex, "4D")
    nt.links.new(vector_rotate.outputs["Vector"], noise_tex.inputs["Vector"])
    if "W" in noise_tex.inputs:
        nt.links.new(seed_val.outputs[0], noise_tex.inputs["W"])
    nt.links.new(scale_val.outputs[0], noise_tex.inputs["Scale"])
    if "Detail" in noise_tex.inputs:
        noise_tex.inputs["Detail"].default_value = 15.0

    noise_tex_3 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex_3, "3D")
    nt.links.new(_noise_fac_output(noise_tex), noise_tex_3.inputs["Vector"])
    noise_tex_3.inputs["Scale"].default_value = 8.0
    if "Detail" in noise_tex_3.inputs:
        noise_tex_3.inputs["Detail"].default_value = 15.0

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    _set_voronoi_dims(voronoi, "4D")
    if hasattr(voronoi, "feature"):
        try:
            voronoi.feature = "DISTANCE_TO_EDGE"
        except TypeError:
            pass
    nt.links.new(_noise_fac_output(noise_tex_3), voronoi.inputs["Vector"])
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = 1.64
    voronoi.inputs["Scale"].default_value = 3.0

    colorramp_edge = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = colorramp_edge.inputs.get("Fac") or colorramp_edge.inputs[0]
    nt.links.new(_voronoi_distance_output(voronoi), fac_in)
    colorramp_edge.color_ramp.elements[0].position = 0.0
    colorramp_edge.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    colorramp_edge.color_ramp.elements[1].position = 0.03
    colorramp_edge.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    mul_vein = nt.nodes.new("ShaderNodeMath")
    mul_vein.operation = "MULTIPLY"
    nt.links.new(map_range.outputs["Result"], mul_vein.inputs[0])
    nt.links.new(colorramp_edge.outputs["Color"], mul_vein.inputs[1])

    noise_tex_1 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex_1, "4D")
    nt.links.new(_noise_fac_output(noise_tex), noise_tex_1.inputs["Vector"])
    if "W" in noise_tex_1.inputs:
        nt.links.new(seed_val.outputs[0], noise_tex_1.inputs["W"])
    noise_tex_1.inputs["Scale"].default_value = 8.0
    if "Detail" in noise_tex_1.inputs:
        noise_tex_1.inputs["Detail"].default_value = 15.0

    mix_noise = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_noise, "data_type"):
        mix_noise.data_type = "RGBA"
    mix_noise.inputs[0].default_value = 0.8
    nt.links.new(_noise_fac_output(noise_tex), mix_noise.inputs[6])
    nt.links.new(_noise_fac_output(noise_tex_1), mix_noise.inputs[7])

    colorramp_base = nt.nodes.new("ShaderNodeValToRGB")
    fac_in2 = colorramp_base.inputs.get("Fac") or colorramp_base.inputs[0]
    nt.links.new(mix_noise.outputs[2], fac_in2)
    colorramp_base.color_ramp.elements[0].position = 0.30
    colorramp_base.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    colorramp_base.color_ramp.elements[1].position = 0.90
    colorramp_base.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    mix_color = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_color, "data_type"):
        mix_color.data_type = "RGBA"
    nt.links.new(mul_vein.outputs[0], mix_color.inputs[0])
    nt.links.new(colorramp_base.outputs["Color"], mix_color.inputs[6])
    mix_color.inputs[7].default_value = (0.0376, 0.0179, 0.0033, 1.0)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.02
    nt.links.new(mul_vein.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    # the colorramp_base output — we mirror that exactly.
    nt.links.new(mix_noise.outputs[2], bsdf.inputs["Base Color"])
    _set_principled(bsdf, **{"Specular IOR Level": 0.6, "Roughness": 0.1})

    _connect_output(nt, bsdf, displacement_socket=disp.outputs[0])
    return mat


# ----------------------------------------------------------------------------
def make_ceramic(name="Ceramic", clear=False, roughness_min=0.0, roughness_max=0.8):
    if np.random.uniform(0, 1) < 0.8 and not clear:
        color = hsv2rgba(float(np.random.uniform(0, 1)),
                         float(np.random.uniform(0.2, 0.4)),
                         _mat_log_uniform(0.3, 0.6))
    else:
        color = hsv2rgba(0.0, 0.0, _mat_log_uniform(0.3, 0.6))

    mat = _new_material(name)
    nt = mat.node_tree

    # Two independent "musgrave" (noise) driven float-curves for roughness +
    # coat roughness. Blender 5.0 has no Musgrave node → stretched NoiseTexture
    # with log-uniform scale is the faithful substitute per spec.
    def _musgrave_driven_curve(scale_lo_hi):
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = _mat_log_uniform(*scale_lo_hi)
        if "Detail" in noise.inputs:
            noise.inputs["Detail"].default_value = 15.0
        return _build_float_curve(
            nt, _noise_fac_output(noise),
            [(0.0, roughness_min), (1.0, roughness_max)],
        )

    roughness_curve = _musgrave_driven_curve((20, 40))
    coat_rough_curve = _musgrave_driven_curve((20, 40))

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    nt.links.new(roughness_curve.outputs["Value"], bsdf.inputs["Roughness"])
    _set_principled(
        bsdf,
        **{
            "Coat Weight": 1.0,
            "Specular IOR Level": 1.0,
            "Subsurface Weight": float(np.random.uniform(0.02, 0.05)),
        },
    )
    if "Coat Roughness" in bsdf.inputs:
        nt.links.new(coat_rough_curve.outputs["Value"], bsdf.inputs["Coat Roughness"])
    elif "Clearcoat Roughness" in bsdf.inputs:
        nt.links.new(coat_rough_curve.outputs["Value"], bsdf.inputs["Clearcoat Roughness"])
    # Subsurface radius — vector socket
    if "Subsurface Radius" in bsdf.inputs:
        try:
            bsdf.inputs["Subsurface Radius"].default_value = (0.02, 0.02, 0.02)
        except Exception:
            pass

    # Small displacement from a second noise source
    disp_noise = nt.nodes.new("ShaderNodeTexNoise")
    disp_noise.inputs["Scale"].default_value = _mat_log_uniform(20, 40)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = _mat_log_uniform(0.001, 0.005)
    nt.links.new(_noise_fac_output(disp_noise), mul.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, displacement_socket=disp.outputs[0])
    return mat


# ----------------------------------------------------------------------------
# (used for the wood_tile weighted branch; see module docstring).
# ----------------------------------------------------------------------------
def make_wood(name="Wood", color=None, vertical=False):
    if color is None:
        h, s, v = bark_hsv()
        color = hsv2rgba(h + float(np.random.uniform(-0.0, 0.05)),
                         s + float(np.random.uniform(-0.3, 0.2)),
                         v * _mat_log_uniform(0.2, 20))
    w = float(np.random.uniform(0, 1))

    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    if vertical:
        vertical_map = nt.nodes.new("ShaderNodeMapping")
        vertical_map.inputs["Rotation"].default_value = (
            math.pi / 2, 0.0, math.pi / 2 * float(np.random.randint(0, 2)))
        nt.links.new(tex_coord.outputs["Object"], vertical_map.inputs["Vector"])
        vec_socket = vertical_map.outputs["Vector"]
    else:
        vec_socket = tex_coord.outputs["Object"]

    mapping_2 = nt.nodes.new("ShaderNodeMapping")
    mapping_2.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(vec_socket, mapping_2.inputs["Vector"])

    # Musgrave substitute #1: high-scale NoiseTexture
    mus_2 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(mus_2, "4D")
    nt.links.new(mapping_2.outputs["Vector"], mus_2.inputs["Vector"])
    if "W" in mus_2.inputs:
        mus_2.inputs["W"].default_value = w
    mus_2.inputs["Scale"].default_value = 10.0
    if "Detail" in mus_2.inputs:
        mus_2.inputs["Detail"].default_value = 15.0

    map_range_2 = nt.nodes.new("ShaderNodeMapRange")
    map_range_2.inputs[3].default_value = 1.0
    map_range_2.inputs[4].default_value = -1.0
    nt.links.new(_noise_fac_output(mus_2), map_range_2.inputs[0])

    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(vec_socket, mapping_1.inputs["Vector"])

    noise_tex_1 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex_1, "4D")
    nt.links.new(mapping_1.outputs["Vector"], noise_tex_1.inputs["Vector"])
    if "W" in noise_tex_1.inputs:
        noise_tex_1.inputs["W"].default_value = w
    noise_tex_1.inputs["Scale"].default_value = 0.5
    if "Detail" in noise_tex_1.inputs:
        noise_tex_1.inputs["Detail"].default_value = 1.0
    if "Distortion" in noise_tex_1.inputs:
        noise_tex_1.inputs["Distortion"].default_value = 1.1

    mus_1 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(mus_1, "4D")
    if "W" in mus_1.inputs:
        mus_1.inputs["W"].default_value = w
    nt.links.new(_noise_fac_output(noise_tex_1), mus_1.inputs["Scale"])
    if "Detail" in mus_1.inputs:
        mus_1.inputs["Detail"].default_value = 15.0

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[3].default_value = -1.4
    map_range.inputs[4].default_value = 1.5
    nt.links.new(_noise_fac_output(mus_1), map_range.inputs[0])

    map_range_1 = nt.nodes.new("ShaderNodeMapRange")
    map_range_1.inputs[3].default_value = 1.0
    map_range_1.inputs[4].default_value = 0.5
    nt.links.new(map_range.outputs["Result"], map_range_1.inputs[0])

    mapping_0 = nt.nodes.new("ShaderNodeMapping")
    mapping_0.inputs["Scale"].default_value = (0.15, 1.0, 0.15)
    nt.links.new(vec_socket, mapping_0.inputs["Vector"])

    noise_tex = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(noise_tex, "4D")
    nt.links.new(mapping_0.outputs["Vector"], noise_tex.inputs["Vector"])
    if "W" in noise_tex.inputs:
        noise_tex.inputs["W"].default_value = w
    if "Detail" in noise_tex.inputs:
        noise_tex.inputs["Detail"].default_value = 5.0
    if "Distortion" in noise_tex.inputs:
        noise_tex.inputs["Distortion"].default_value = 1.0

    mus_0 = nt.nodes.new("ShaderNodeTexNoise")
    _set_noise_dims(mus_0, "4D")
    nt.links.new(_noise_fac_output(noise_tex), mus_0.inputs["Vector"])
    if "W" in mus_0.inputs:
        mus_0.inputs["W"].default_value = w
    mus_0.inputs["Scale"].default_value = 4.0
    if "Detail" in mus_0.inputs:
        mus_0.inputs["Detail"].default_value = 10.0

    mix_a = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_a, "data_type"):
        mix_a.data_type = "RGBA"
    nt.links.new(_noise_fac_output(noise_tex), mix_a.inputs[6])
    nt.links.new(_noise_fac_output(mus_0), mix_a.inputs[7])

    mix_b = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_b, "data_type"):
        mix_b.data_type = "RGBA"
    if hasattr(mix_b, "blend_type"):
        try:
            mix_b.blend_type = "MULTIPLY"
        except TypeError:
            pass
    mix_b.inputs[0].default_value = 0.9
    nt.links.new(map_range_1.outputs["Result"], mix_b.inputs[6])
    nt.links.new(mix_a.outputs[2], mix_b.inputs[7])

    mix_c = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_c, "data_type"):
        mix_c.data_type = "RGBA"
    if hasattr(mix_c, "blend_type"):
        try:
            mix_c.blend_type = "MULTIPLY"
        except TypeError:
            pass
    mix_c.inputs[0].default_value = 0.95
    nt.links.new(map_range_2.outputs["Result"], mix_c.inputs[6])
    nt.links.new(mix_b.outputs[2], mix_c.inputs[7])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    mix_d = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_d, "data_type"):
        mix_d.data_type = "RGBA"
    nt.links.new(mix_c.outputs[2], mix_d.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix_d.inputs[6])
    mix_d.inputs[7].default_value = color

    mul_disp = nt.nodes.new("ShaderNodeMath")
    mul_disp.operation = "MULTIPLY"
    mul_disp.inputs[1].default_value = _mat_log_uniform(0.0002, 0.01)
    nt.links.new(mix_c.outputs[2], mul_disp.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])

    # Roughness — build_float_curve(noise, [(0, r), (1, r+u)])
    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = _mat_log_uniform(40, 50)
    base_r = float(np.random.uniform(0.0, 0.4))
    top_r = base_r + float(np.random.uniform(0.0, 0.8))
    rough_curve = _build_float_curve(
        nt, _noise_fac_output(noise_r), [(0.0, base_r), (1.0, top_r)])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_d.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(rough_curve.outputs["Value"], bsdf.inputs["Roughness"])
    _set_principled(bsdf, **{
        "Coat Weight": float(np.clip(np.random.uniform(0, 1.4), 0, 1)),
    })
    _connect_output(nt, bsdf, displacement_socket=disp.outputs[0])
    return mat


# ----------------------------------------------------------------------------
# Registry / weighted sampling — mirror CountertopFactory.surfaces exactly:
#   ("weighted_choice", (5, marble), (2, ceramic), (2, wood_tile))
# ----------------------------------------------------------------------------
COUNTERTOP_REGISTRY = [
    (make_marble,  5.0),
    (make_ceramic, 2.0),
    (make_wood,    2.0),   # wood_tile branch — see module docstring note
]


def _weighted_sample(registry):
    ctors, weights = zip(*registry)
    weights = np.array(weights, dtype=float)
    idx = int(np.random.choice(len(ctors), p=weights / weights.sum()))
    return ctors[idx]


def get_countertop_material(name="Countertop"):
    return _weighted_sample(COUNTERTOP_REGISTRY)(name=name)


# ============================================================================
# === Original geometry code (verbatim from objects_blender/shelves/
#     CountertopFactory.py) with a single material-append before the final
#     join_objects() call.
# ============================================================================

def int_hash(x, mod=2**32 - 1):
    m = hashlib.md5()
    for s in (x if isinstance(x, (tuple, list)) else [x]):
        m.update(str(s).encode())
    return abs(int(m.hexdigest(), 16)) % mod


@contextlib.contextmanager
def fixed_seed(seed):
    py_st, np_st = random.getstate(), np.random.get_state()
    random.seed(int(seed)); np.random.seed(int(seed))
    try: yield
    finally: random.setstate(py_st); np.random.set_state(np_st)


# blender helpers
class ViewportMode:
    def __init__(self, obj, mode):
        self.obj = obj; self.mode = mode
    def __enter__(self):
        self._prev = bpy.context.active_object
        bpy.context.view_layer.objects.active = self.obj
        self._prev_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode=self.mode)
    def __exit__(self, *_):
        bpy.context.view_layer.objects.active = self.obj
        bpy.ops.object.mode_set(mode=self._prev_mode)
        bpy.context.view_layer.objects.active = self._prev


class SelectObjects:
    def __init__(self, obj):
        self.objs = obj if isinstance(obj, list) else [obj]
    def __enter__(self):
        for o in bpy.context.selected_objects: o.select_set(False)
        for o in self.objs: o.select_set(True)
        bpy.context.view_layer.objects.active = self.objs[0]
    def __exit__(self, *_):
        for o in bpy.context.selected_objects: o.select_set(False)


def delete(obj):
    objs = obj if isinstance(obj, (list, tuple)) else [obj]
    for o in objs:
        if o is None: continue
        try: bpy.data.objects.remove(o, do_unlink=True)
        except Exception: pass


def apply_transform(obj, loc=False):
    with SelectObjects(obj):
        bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)


def join_objects(objs):
    objs = [o for o in objs if o and o.type == 'MESH' and len(o.data.vertices) > 0]
    if not objs: return None
    if len(objs) == 1: return objs[0]
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def deep_clone_obj(obj):
    new = obj.copy(); new.data = obj.data.copy()
    for m in list(new.modifiers): new.modifiers.remove(m)
    while getattr(new.data, 'materials', None) and new.data.materials:
        new.data.materials.pop()
    bpy.context.scene.collection.objects.link(new)
    return new


def modify_mesh(obj, type_, apply=True, **kwargs):
    mod = obj.modifiers.new(type_, type_)
    for k, v in kwargs.items():
        try: setattr(mod, k, v)
        except (AttributeError, TypeError): pass
    if apply:
        with SelectObjects(obj):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


# mesh data helpers
def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', arr)
    return arr.reshape(-1, 3)


def write_co(obj, arr):
    obj.data.vertices.foreach_set('co', arr.reshape(-1))
    obj.data.update()


def read_edges(obj):
    arr = np.zeros(len(obj.data.edges) * 2, dtype=int)
    obj.data.edges.foreach_get('vertices', arr)
    return arr.reshape(-1, 2)


def read_center(obj):
    arr = np.zeros(len(obj.data.polygons) * 3)
    obj.data.polygons.foreach_get('center', arr)
    return arr.reshape(-1, 3)


def read_normal(obj):
    arr = np.zeros(len(obj.data.polygons) * 3)
    obj.data.polygons.foreach_get('normal', arr)
    return arr.reshape(-1, 3)


def select_faces(obj, mask):
    mask = np.asarray(mask, dtype=bool)
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        for i, sel in enumerate(mask): bm.faces[i].select_set(bool(sel))
        bm.select_flush(False)
        bmesh.update_edit_mesh(obj.data)


def separate_selected(obj, face=False):
    for o in bpy.context.selected_objects: o.select_set(False)
    with ViewportMode(obj, 'EDIT'):
        if face: bpy.ops.mesh.duplicate_move()
        bpy.ops.mesh.separate(type='SELECTED')
    result = next(o for o in bpy.context.selected_objects if o != obj)
    for o in bpy.context.selected_objects: o.select_set(False)
    return result


# shapely / geometry utilities
def normalize(v, in_place=True):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    n[n < 1e-12] = 1.0
    if in_place: v /= n; return v
    return v / n


def dissolve_limited(obj):
    with ViewportMode(obj, 'EDIT'):
        for limit in reversed(0.05 * 0.1 ** np.arange(5)):
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.select_all(action='SELECT')
            try: bpy.ops.mesh.dissolve_limited(angle_limit=float(limit))
            except Exception: pass


def snap_mesh(obj, eps=1e-3):
    prev_vcount = -1
    while True:
        dissolve_limited(obj)
        co = read_co(obj)
        if len(co) == prev_vcount: return obj
        prev_vcount = len(co)
        if len(obj.data.edges) == 0: return obj
        u, w = read_edges(obj).T
        d = co[:, np.newaxis] - co[np.newaxis, u]
        l = co[np.newaxis, w] - co[np.newaxis, u]
        n = normalize(l, in_place=False)
        prod = (d * n).sum(-1)
        diff = np.linalg.norm(d - prod[:, :, np.newaxis] * n, axis=-1)
        diff[u, np.arange(len(u))] = 1
        diff[w, np.arange(len(w))] = 1
        diff[prod < 0] = 1
        diff[prod > np.linalg.norm(l, axis=-1)] = 1
        es, vs = np.nonzero((diff < eps).T)
        if len(vs) == 0: return obj
        indices = np.concatenate([[0], np.nonzero(es[1:] != es[:-1])[0] + 1])
        vs = vs[indices]; es = es[indices]
        with ViewportMode(obj, 'EDIT'):
            bm = bmesh.from_edit_mesh(obj.data)
            bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
            dis   = co[w[es]] - co[u[es]]
            norms = np.linalg.norm(dis, axis=-1)
            valid = norms > 1e-10
            es = es[valid]; vs = vs[valid]; dis = dis[valid]; norms = norms[valid]
            percents = ((co[vs] - co[u[es]]) * dis).sum(-1) / (norms ** 2)
            edges = [bm.edges[e] for e in es]
            for e, p in zip(edges, percents):
                bmesh.ops.subdivide_edges(bm, edges=[e], cuts=1, edge_percents={e: p})
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=eps * 1.5)
            bmesh.update_edit_mesh(obj.data)


def obj2polygon(obj):
    co = read_co(obj)[:, :2]
    p = shapely.union_all([
        shapely.make_valid(orient(shapely.Polygon(co[list(f.vertices)])))
        for f in obj.data.polygons
    ])
    return shapely.ops.orient(shapely.make_valid(shapely.simplify(p, 1e-6)))


def buffer(p, distance):
    with np.errstate(invalid='ignore'):
        return remove_repeated_points(
            simplify(p.buffer(distance, join_style='mitre', cap_style='flat'), 1e-6))


def _polygon_to_obj(p):
    coords = np.array(p.exterior.coords)[:-1]
    if len(coords) < 3:
        return None
    me = bpy.data.meshes.new('poly')
    me.from_pydata([(float(x), float(y), 0.0) for x, y in coords], [], [list(range(len(coords)))])
    me.update()
    obj = bpy.data.objects.new('poly', me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def safe_polygon2obj(poly):
    ps = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
    objs = [_polygon_to_obj(p) for p in ps]
    objs = [o for o in objs if o is not None]
    if not objs: return None
    obj = join_objects(objs) if len(objs) > 1 else objs[0]
    obj.location[-1] = 0
    apply_transform(obj, loc=True)
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
    return obj


def make_shelves(n=10):
    """Generate n rectangular shelf-top planes."""

    objects = []
    for _ in range(n):
        w = float(np.random.uniform(0.4, 1.4))
        d = float(np.random.uniform(0.3, 0.8))
        h = float(np.random.uniform(0.70, 1.0))
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        obj = bpy.context.active_object
        write_co(obj, np.array([[-w/2,-d/2,h],[w/2,-d/2,h],[w/2,d/2,h],[-w/2,d/2,h]]))
        lxy = np.random.uniform(-1.0, 1.0, 2)
        obj.location = (float(lxy[0]), float(lxy[1]), float(np.random.uniform(0.0, 0.5)))
        obj.rotation_euler[2] = float(np.pi / 2 * np.random.randint(4))
        objects.append(obj)
    return SimpleNamespace(objects=objects)


class CountertopFactory:
    def __init__(self, factory_seed, coarse=False):
        self.factory_seed = int(factory_seed)
        with fixed_seed(factory_seed):
            self.thickness = float(np.random.uniform(0.02, 0.06))
            self.extrusion = 0.0 if np.random.uniform() < 0.4 else float(np.random.uniform(0.02, 0.03))
            self.h_snap  = 0.5
            self.v_snap  = 0.5
            self.v_merge = 0.1
            self.z_range = (0.5, 1.5)

    @staticmethod
    def rebuffer(shape, distance):
        return shape.buffer( distance, join_style='mitre', cap_style='flat').buffer(
                            -distance, join_style='mitre', cap_style='flat')

    def create_asset(self, shelves=None, **params):
        if shelves is None:
            shelves = make_shelves()

        geoms, zs = [], []
        for s in shelves.objects:
            t = deep_clone_obj(s)
            z = read_center(t)[:, -1]
            valid = (self.z_range[0] < z) & (z < self.z_range[1])
            if not np.any(valid): delete([t]); continue
            max_z = float(np.max(z[valid]))
            selection = (read_normal(t)[:, -1] > 0.5) & (z - 1e-2 < max_z) & (max_z < z + 1e-2)
            if not np.any(selection): delete([t]); continue
            select_faces(t, selection)
            r = separate_selected(t, True)
            r.location = s.location
            r.rotation_euler = s.rotation_euler
            apply_transform(r, loc=True)
            geoms.append(buffer(self.rebuffer(obj2polygon(r), self.h_snap), self.extrusion))
            zs.append(max_z + s.location[-1])
            delete([r, t])

        if not geoms:
            bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
            delete(shelves.objects)
            obj = bpy.context.active_object
            obj.data.materials.append(MAT_SURFACE)
            return obj

        indices = np.argsort(zs)
        geoms_ = [geoms[i] for i in indices]
        zs_    = [zs[i]    for i in indices]
        geoms, zs = [], []
        for i in range(len(indices)):
            if i == 0:
                geoms.append(geoms_[i]); zs.append(zs_[i])
            elif zs_[i] < zs[-1] + self.v_merge:
                geoms[-1] = self.rebuffer(geoms[-1].union(geoms_[i]), self.h_snap)
            else:
                geoms.append(geoms_[i]); zs.append(zs_[i])

        groups = []
        for i in range(len(geoms)):
            for j in range(i):
                if geoms[i].distance(geoms[j]) <= self.h_snap and zs[i] - zs[j] < self.v_snap:
                    next(g for g in groups if j in g).add(i); break
            else:
                groups.append({i})

        objs = []
        for group in groups:
            n      = len(group)
            group  = sorted(group)
            geoms_ = [geoms[i] for i in group]
            zs_    = [zs[i]    for i in group]
            geom_unions = [self.rebuffer(shapely.union_all(geoms_[i:]), self.h_snap / 2) for i in range(n)]
            geom_unions.append(shapely.Point())
            shapes = [self.rebuffer(geom_unions[i].difference(geom_unions[i + 1]), -1e-4) for i in range(n)]

            for s_shape, z in zip(shapes, zs_):
                if s_shape.area > 0:
                    o = safe_polygon2obj(self.rebuffer(s_shape, -1e-4).buffer(0))
                    if o is not None:
                        o.location[-1] = z; apply_transform(o, loc=True); objs.append(o)

            ss = []
            for i in range(n - 1, -1, -1):
                for j in range(i - 1, -1, -1):
                    s_diff = buffer(shapes[i], 1e-4).intersection(buffer(shapes[j], 1e-4))
                    ss.append(s_diff)
                    for c in ss[:-1]: s_diff = s_diff.difference(buffer(c, 1e-4))
                    if s_diff.area == 0: continue
                    o = safe_polygon2obj(s_diff)
                    if o is None: continue
                    modify_mesh(o, 'WELD', merge_threshold=5e-4)
                    o.location[-1] = zs_[i]
                    with ViewportMode(o, 'EDIT'):
                        bpy.ops.mesh.select_mode(type='EDGE')
                        bpy.ops.mesh.select_all(action='SELECT')
                        bpy.ops.mesh.extrude_edges_move(
                            TRANSFORM_OT_translate={'value': (0, 0, zs_[j] - zs_[i])})
                    objs.append(o)

        # Attach the surface material to every sub-slab BEFORE joining so the
        # resulting single countertop object carries exactly one material slot.
        for sub in objs:
            if sub is not None and sub.data is not None:
                sub.data.materials.append(MAT_SURFACE)

        obj = join_objects(objs)
        snap_mesh(obj, 2e-2)
        dissolve_limited(obj)
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
        modify_mesh(obj, 'SOLIDIFY', thickness=self.thickness, use_even_offset=False, offset=1)

        delete(shelves.objects)
        return obj


# ============================================================================
# Entry point — Phase 1 material sampling on raw SEED, then Phase 2 geometry
# on the re-seeded (int_hash) RNG state used by the upstream geometry script.
# ============================================================================

def clear_scene():
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for col in list(bpy.data.collections): bpy.data.collections.remove(col)
    for mesh in list(bpy.data.meshes): bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials): bpy.data.materials.remove(mat)
    for ng in list(bpy.data.node_groups): bpy.data.node_groups.remove(ng)


SEED = int(os.environ.get("SEED", "0"))
clear_scene()

# with thickness/extrusion draws in between; only the second rg result is used.
seed_all(SEED)
_ = get_countertop_material("CountertopUnused")   # first rg(self.surfaces)
_thickness_preview = float(np.random.uniform(0.02, 0.06))  # drain: thickness
_extrusion_gate = float(np.random.uniform())               # drain: extrusion gate
if _extrusion_gate >= 0.4:
    _ = float(np.random.uniform(0.02, 0.03))               # drain: extrusion value
MAT_SURFACE = get_countertop_material("Countertop")        # second rg — the real one

# Phase 2 — geometry. Original objects_blender script re-seeds via int_hash.
derived = int_hash((SEED, 0))
random.seed(derived); np.random.seed(derived)


def build(seed=SEED):
    return CountertopFactory(int(seed)).create_asset()


build(SEED)
