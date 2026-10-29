# [FL_INDEX: keywords="blender_factory, procedural_3d, SnakeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SnakeFactory | Category: factories_tex
# Prompt: A snake rendered as a textured 3D model. The creature is shown in a simple sinuous S-curve pose with the head elevated at the upper left and the body sweeping downward in a smooth curve, tapering to a very thin tail at the bottom right. The entire body is a uniform deep olive-green with a smooth, slightly matte surface. The head is small and slightly flattened with a blunt rounded snout. The long tubular body has a subtle bilateral flattening that emphasizes the smooth serpentine form. The cast shadow mirrors the curved silhouette of the body.

import os
import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector

SEED = int(os.environ.get("SEED", "0"))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
import random as _random, colorsys as _colorsys


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

def _sample_color_inplace(color, offset=0, keep_sum=False):
    import random as _rnd
    if keep_sum:
        mean = (color[0] + color[1] + color[2]) / 3.0
        off = min(mean, 1.0 - mean) * _rnd.random()
        idx = _rnd.randint(0, 2)
        f = 1
        pcg = _rnd.random()
        for i in range(3):
            if i == idx:
                color[i] = mean + off
            else:
                color[i] = mean - off * (f * pcg + (1 - f) * (1 - pcg))
                f = 0
        return
    for i in range(3):
        if offset == 0:
            color[i] = _rnd.random()
        else:
            color[i] += (_rnd.random() - 0.5) * 2 * offset
        color[i] = max(0.0, min(1.0, color[i]))


def _set_bsdf_subsurface_burley(bsdf):
    """Set subsurface method to BURLEY (Blender 4.x) or skip if unavailable."""

    try:
        bsdf.subsurface_method = "BURLEY"
    except Exception:
        pass


def _spec_key(bsdf):
    return "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"


# ---------- Shader 1: shader_black_white_snake ----------
def _shader_black_white_snake(name, rand=True):
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    # Position attribute
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Position"

    mapping = nt.nodes.new("ShaderNodeMapping")
    ln(attr.outputs["Vector"], mapping.inputs["Vector"])

    # Wave texture
    wave = nt.nodes.new("ShaderNodeTexWave")
    ln(mapping.outputs["Vector"], wave.inputs["Vector"])
    wave.inputs["Scale"].default_value = 10.0
    wave.inputs["Distortion"].default_value = 1.5
    wave.inputs["Detail"].default_value = 5.0
    wave.inputs["Detail Roughness"].default_value = 0.8

    # Second mapping + noise for voronoi distortion
    mapping1 = nt.nodes.new("ShaderNodeMapping")
    ln(attr.outputs["Vector"], mapping1.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    ln(mapping1.outputs["Vector"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 5.0

    mix0 = nt.nodes.new("ShaderNodeMix"); mix0.data_type = "RGBA"
    mix0.inputs[0].default_value = 0.8
    ln(noise.outputs["Color"], mix0.inputs[6])
    ln(mapping1.outputs["Vector"], mix0.inputs[7])

    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(mix0.outputs[2], vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = 8.0
    vor.feature = "DISTANCE_TO_EDGE"

    mix1 = nt.nodes.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    mix1.inputs[0].default_value = 0.2
    ln(_fac(wave), mix1.inputs[6])
    ln(vor.outputs["Distance"], mix1.inputs[7])

    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(mix1.outputs[2], cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.0
    cr.color_ramp.elements[0].color = [1.0, 0.9647, 0.8308, 1.0]
    cr.color_ramp.elements[1].position = 0.0977
    cr.color_ramp.elements[1].color = [0.0003, 0.0003, 0.0009, 1.0]
    if rand:
        for e in cr.color_ramp.elements:
            c = list(e.color)
            _sample_color_inplace(c, offset=0.05, keep_sum=True)
            e.color = c

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.6
    bsdf.inputs[_spec_key(bsdf)].default_value = 0.2
    bsdf.inputs["Roughness"].default_value = 0.4
    _set_bsdf_subsurface_burley(bsdf)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ---------- Shader 2: shader_shining_golden ----------
def _shader_shining_golden(name, rand=True):
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    base_color = [0.8, 0.2227, 0.0326, 1.0]
    if rand:
        _sample_color_inplace(base_color, keep_sum=True)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = 0.6
    bsdf.inputs["Roughness"].default_value = 0.27
    _set_bsdf_subsurface_burley(bsdf)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ---------- Shader 3: shader_golden ----------
def _shader_golden(name, rand=False):
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Position"

    mapping = nt.nodes.new("ShaderNodeMapping")
    ln(attr.outputs["Vector"], mapping.inputs["Vector"])
    mapping.inputs["Scale"].default_value = (0.5, 1.0, 1.0)

    wave = nt.nodes.new("ShaderNodeTexWave")
    ln(mapping.outputs["Vector"], wave.inputs["Vector"])
    wave.inputs["Distortion"].default_value = 1.0
    wave.inputs["Detail"].default_value = 15.0
    wave.inputs["Detail Roughness"].default_value = 0.8
    wave.inputs["Phase Offset"].default_value = 2.0

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    ln(wave.outputs["Color"], noise1.inputs["Vector"])
    noise1.inputs["Scale"].default_value = 1.5
    noise1.inputs["Detail"].default_value = 5.0
    noise1.inputs["Roughness"].default_value = 0.4

    mapping1 = nt.nodes.new("ShaderNodeMapping")
    ln(attr.outputs["Vector"], mapping1.inputs["Vector"])

    noise0 = nt.nodes.new("ShaderNodeTexNoise")
    ln(mapping1.outputs["Vector"], noise0.inputs["Vector"])
    noise0.inputs["Scale"].default_value = 3.0
    noise0.inputs["Detail"].default_value = 5.0

    mix0 = nt.nodes.new("ShaderNodeMix"); mix0.data_type = "RGBA"
    mix0.inputs[0].default_value = 0.8
    ln(noise0.outputs["Color"], mix0.inputs[6])
    ln(mapping1.outputs["Vector"], mix0.inputs[7])

    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(mix0.outputs[2], vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = 8.0
    vor.feature = "DISTANCE_TO_EDGE"

    mix1 = nt.nodes.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    mix1.inputs[0].default_value = 0.1
    ln(noise1.outputs["Color"], mix1.inputs[6])
    ln(vor.outputs["Distance"], mix1.inputs[7])

    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(mix1.outputs[2], cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.4682
    cr.color_ramp.elements[0].color = [0.017, 0.0094, 0.0033, 1.0]
    cr.color_ramp.elements[1].position = 1.0
    cr.color_ramp.elements[1].color = [0.4969, 0.2582, 0.0666, 1.0]
    if rand:
        for e in cr.color_ramp.elements:
            c = list(e.color)
            _sample_color_inplace(c, offset=0.05, keep_sum=True)
            e.color = c

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.4
    bsdf.inputs[_spec_key(bsdf)].default_value = 0.2
    bsdf.inputs["Roughness"].default_value = 0.4
    _set_bsdf_subsurface_burley(bsdf)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ---------- Shader 4: shader_green ----------
def _shader_green(name, rand=True):
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Position"

    # Belly/back Z-gradient (upper = principled_bsdf, lower = principled_bsdf_1)
    mapping3 = nt.nodes.new("ShaderNodeMapping")
    ln(attr.outputs["Vector"], mapping3.inputs["Vector"])
    sep_z = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(mapping3.outputs["Vector"], sep_z.inputs["Vector"])
    cr3 = nt.nodes.new("ShaderNodeValToRGB")
    ln(sep_z.outputs["Z"], cr3.inputs["Fac"])
    cr3.color_ramp.elements[0].position = 0.3864
    cr3.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr3.color_ramp.elements[1].position = 0.6682
    cr3.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # --- BSDF 1: belly (noise-based warm tones) ---
    mapping2 = nt.nodes.new("ShaderNodeMapping")
    ln(attr.outputs["Vector"], mapping2.inputs["Vector"])
    mapping2.inputs["Scale"].default_value = (0.5, 1.0, 1.0)

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    ln(mapping2.outputs["Vector"], noise2.inputs["Vector"])
    noise2.inputs["Scale"].default_value = 10.0
    noise2.inputs["Detail"].default_value = 10.0
    noise2.inputs["Roughness"].default_value = 0.4
    noise2.inputs["Distortion"].default_value = 0.1

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(noise2), cr2.inputs["Fac"])
    cr2.color_ramp.elements.new(0)
    cr2.color_ramp.elements[0].position = 0.2318
    cr2.color_ramp.elements[0].color = [0.6445, 0.5271, 0.0012, 1.0]
    cr2.color_ramp.elements[1].position = 0.375
    cr2.color_ramp.elements[1].color = [0.0503, 0.0338, 0.0072, 1.0]
    cr2.color_ramp.elements[2].position = 0.45
    cr2.color_ramp.elements[2].color = [0.0172, 0.0406, 0.0, 1.0]
    if rand:
        for e in cr2.color_ramp.elements:
            c = list(e.color)
            _sample_color_inplace(c, offset=0.1, keep_sum=True)
            e.color = c

    bsdf1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr2.outputs["Color"], bsdf1.inputs["Base Color"])
    bsdf1.inputs["Metallic"].default_value = 0.4
    bsdf1.inputs["Roughness"].default_value = 0.27
    _set_bsdf_subsurface_burley(bsdf1)

    # --- BSDF 2: back (wave+voronoi green pattern) ---
    mapping_w = nt.nodes.new("ShaderNodeMapping")
    ln(attr.outputs["Vector"], mapping_w.inputs["Vector"])
    mapping_w.inputs["Scale"].default_value = (0.5, 1.0, 1.0)

    wave = nt.nodes.new("ShaderNodeTexWave")
    ln(mapping_w.outputs["Vector"], wave.inputs["Vector"])
    wave.inputs["Distortion"].default_value = 1.0
    wave.inputs["Detail"].default_value = 15.0
    wave.inputs["Detail Roughness"].default_value = 0.8
    wave.inputs["Phase Offset"].default_value = 2.0

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    ln(wave.outputs["Color"], noise1.inputs["Vector"])
    noise1.inputs["Scale"].default_value = 1.4
    noise1.inputs["Detail"].default_value = 5.0
    noise1.inputs["Roughness"].default_value = 0.4

    mapping1 = nt.nodes.new("ShaderNodeMapping")
    ln(attr.outputs["Vector"], mapping1.inputs["Vector"])

    noise0 = nt.nodes.new("ShaderNodeTexNoise")
    ln(mapping1.outputs["Vector"], noise0.inputs["Vector"])
    noise0.inputs["Scale"].default_value = 3.0
    noise0.inputs["Detail"].default_value = 5.0

    mix0 = nt.nodes.new("ShaderNodeMix"); mix0.data_type = "RGBA"
    mix0.inputs[0].default_value = 0.8
    ln(noise0.outputs["Color"], mix0.inputs[6])
    ln(mapping1.outputs["Vector"], mix0.inputs[7])

    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    ln(mix0.outputs[2], vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = 8.0
    vor.feature = "DISTANCE_TO_EDGE"

    mix1 = nt.nodes.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    mix1.inputs[0].default_value = 0.1
    ln(noise1.outputs["Color"], mix1.inputs[6])
    ln(vor.outputs["Distance"], mix1.inputs[7])

    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(mix1.outputs[2], cr.inputs["Fac"])
    # 4 stops: light grey-green -> near-black -> dark green -> bright green
    cr.color_ramp.elements.new(0)
    cr.color_ramp.elements.new(0)
    cr.color_ramp.elements[0].position = 0.2818
    cr.color_ramp.elements[0].color = [0.7682, 0.7835, 0.7605, 1.0]
    cr.color_ramp.elements[1].position = 0.4295
    cr.color_ramp.elements[1].color = [0.0013, 0.0013, 0.0013, 1.0]
    cr.color_ramp.elements[2].position = 0.5068
    cr.color_ramp.elements[2].color = [0.0096, 0.0149, 0.0, 1.0]
    cr.color_ramp.elements[3].position = 0.6727
    cr.color_ramp.elements[3].color = [0.0872, 0.2355, 0.0, 1.0]
    if rand:
        for e in cr.color_ramp.elements:
            c = list(e.color)
            _sample_color_inplace(c, keep_sum=True)
            e.color = c

    bsdf2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf2.inputs["Base Color"])
    bsdf2.inputs["Metallic"].default_value = 0.4
    bsdf2.inputs["Roughness"].default_value = 0.27
    _set_bsdf_subsurface_burley(bsdf2)

    # Mix shader: Z-gradient blends belly and back
    mix_sh = nt.nodes.new("ShaderNodeMixShader")
    ln(cr3.outputs["Color"], mix_sh.inputs["Fac"])
    ln(bsdf1.outputs["BSDF"], mix_sh.inputs[1])
    ln(bsdf2.outputs["BSDF"], mix_sh.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_sh.outputs["Shader"], out.inputs["Surface"])
    return mat


# ---------- Main entry: randomly pick one of the 4 shaders ----------
_ALL_SHADERS = [
    _shader_black_white_snake,
    _shader_shining_golden,
    _shader_golden,
    _shader_green,
]

def make_creature_material(seed, name="ReptileMaterial"):
    np.random.seed(seed); _random.seed(seed)
    shader_fn = _random.choice(_ALL_SHADERS)
    rand = np.random.uniform() > 0.3
    return shader_fn(name, rand=rand)


# Phase 1: creature material
CREATURE_MAT = make_creature_material(SEED, "SnakeFactory_Material")
np.random.seed(SEED)


def clear_scene():
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

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

clear_scene()

# ============================================================
# Randomized parameters (controlled by SEED)
# ============================================================

snake_length = np.random.uniform(1.5, 3.0)
body_radius = np.random.uniform(0.055, 0.095)

# Cross-section shape: snakes are wider than tall
width_aspect = np.random.normal(1.15, 0.05)
height_aspect = np.random.normal(0.85, 0.05)

# S-curve wave pattern
n_waves = np.random.uniform(1.0, 2.0)
amplitude = snake_length * np.random.uniform(0.06, 0.14)

# Body taper profile parameters
wrist_frac = np.random.uniform(0.30, 0.42)       # where body reaches full thickness
breast_bulge = np.random.uniform(0.0, 0.06)       # mid-body extra fullness
tail_thinness = np.random.uniform(0.01, 0.04)     # how thin the tail tip starts
taper_power = np.random.uniform(0.4, 0.8)         # taper curve shape

# Head shape parameters
head_start = np.random.uniform(0.88, 0.93)        # where head region begins
head_widening = np.random.uniform(0.03, 0.09)     # how much head widens
head_flatten = np.random.uniform(0.06, 0.14)      # head flattening amount
snout_taper_power = np.random.uniform(0.8, 1.6)   # snout bluntness (low=blunt, high=pointed)
snout_length_frac = np.random.uniform(0.03, 0.06) # fraction of body length for snout

# Mouth parameters
mouth_gap_scale = np.random.uniform(0.15, 0.30)
mouth_angle_z = np.random.uniform(-0.12, -0.04)   # mouth line position

# Eye parameters
eye_radius_frac = max(0.10, np.random.normal(0.18, 0.03))  # fraction of body_radius
eye_t = np.random.uniform(0.92, 0.96)                       # position along head
eye_height_frac = np.random.uniform(0.35, 0.55)             # vertical position on head

# Mesh resolution (fixed for quality)
n_body_segs = 120
n_ring = 32

# ============================================================
# Generate sinusoidal path
# ============================================================
total_pts = n_body_segs + 1
path = []
for i in range(total_pts):
    t = i / (total_pts - 1)
    x = t * snake_length
    y = amplitude * math.sin(t * 2 * math.pi * n_waves)
    path.append(Vector((x, y, 0.0)))

# ============================================================
# Taper function: parameterized by random variables
# ============================================================
def body_taper(t):
    """t in [0,1]: 0 = tail tip, 1 = head end. Returns radius multiplier [0,1]."""

    tail_tip_end = 0.02
    tail_mid = 0.08
    head_region = head_start
    snout_start = 1.0 - snout_length_frac

    if t < tail_tip_end:
        return tail_thinness + (0.08 - tail_thinness) * (t / tail_tip_end)
    elif t < tail_mid:
        frac = (t - tail_tip_end) / (tail_mid - tail_tip_end)
        return 0.08 + 0.22 * frac
    elif t < wrist_frac:
        frac = (t - tail_mid) / (wrist_frac - tail_mid)
        return 0.30 + 0.60 * (frac ** taper_power)
    elif t < head_region:
        frac = (t - wrist_frac) / (head_region - wrist_frac)
        base = 0.90 + 0.10 * frac
        mid = 0.5
        bulge = breast_bulge * math.exp(-((frac - mid) ** 2) / 0.08)
        return min(base + bulge, 1.0)
    elif t < snout_start:
        return 1.0
    else:
        ht = (t - snout_start) / snout_length_frac
        return 1.0 - 0.55 * (ht ** snout_taper_power)

def head_shape(t):
    """Returns (width_mult, height_mult) for head widening/flattening."""

    if t < head_start:
        return 1.0, 1.0
    ht = (t - head_start) / (1.0 - head_start)
    if ht < 0.4:
        w = 1.0 + head_widening * (ht / 0.4)
    elif ht < 0.6:
        w = 1.0 + head_widening
    else:
        w = (1.0 + head_widening) * (1.0 - 0.40 * ((ht - 0.6) / 0.4))
    h = 1.0 - head_flatten * ht
    return w, h

# ============================================================
# Compute tangent at each path point
# ============================================================
def get_tangent(i):
    if i == 0:
        return (path[1] - path[0]).normalized()
    elif i >= total_pts - 1:
        return (path[-1] - path[-2]).normalized()
    else:
        return (path[i + 1] - path[i - 1]).normalized()

# ============================================================
# Build unified body+head tube mesh
# ============================================================
bm = bmesh.new()
up = Vector((0, 0, 1))

rings = []
ring_centers = []
ring_binormals = []
ring_normals = []

for i in range(total_pts):
    t = i / (total_pts - 1)
    center = path[i]
    tangent = get_tangent(i)

    binormal = tangent.cross(up)
    if binormal.length < 1e-6:
        binormal = Vector((0, 1, 0))
    binormal.normalize()
    normal = binormal.cross(tangent).normalized()

    r = body_radius * body_taper(t)
    w_mult, h_mult = head_shape(t)

    head_start_t = head_start

    ring_verts = []
    for j in range(n_ring):
        angle = 2 * math.pi * j / n_ring
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)
        rx = r * width_aspect * w_mult
        rz = r * height_aspect * h_mult

        jaw_offset = Vector((0, 0, 0))
        if t > head_start_t:
            raw_progress = (t - head_start_t) / (1.0 - head_start_t)
            if raw_progress < 0.25:
                head_progress = raw_progress / 0.25
            else:
                head_progress = 1.0
            head_progress = max(0.0, min(1.0, head_progress))
            snout_taper = 1.0 - 0.55 * raw_progress
            gap = r * mouth_gap_scale * head_progress * snout_taper

            if sin_a > mouth_angle_z + 0.15:
                jaw_offset = normal * (gap * 0.5)
            elif sin_a < mouth_angle_z - 0.15:
                jaw_offset = normal * (-gap * 0.5)
                rz *= (1.0 - 0.15 * head_progress)
                rx *= (1.0 - 0.05 * head_progress)
            else:
                pinch = 1.0 - abs(sin_a - mouth_angle_z) / 0.15
                rx *= (1.0 - 0.35 * pinch * head_progress)
                rz *= (1.0 - 0.35 * pinch * head_progress)

        offset = binormal * (rx * cos_a) + normal * (rz * sin_a) + jaw_offset
        v = bm.verts.new(center + offset)
        ring_verts.append(v)
    rings.append(ring_verts)
    ring_centers.append(center)
    ring_binormals.append(binormal.copy())
    ring_normals.append(normal.copy())

bm.verts.ensure_lookup_table()

# Determine which vertex indices are at the mouth slit
mouth_slit_js = set()
for j in range(n_ring):
    angle = 2 * math.pi * j / n_ring
    if abs(math.sin(angle) - mouth_angle_z) < 0.14:
        mouth_slit_js.add(j)

head_start_idx = int(head_start * (total_pts - 1))
mouth_open_start = int((head_start + (1.0 - head_start) * 0.08) * (total_pts - 1))

# Quad faces between adjacent rings — skip mouth slit faces in head region
for i in range(len(rings) - 1):
    for j in range(n_ring):
        jn = (j + 1) % n_ring
        if i >= mouth_open_start:
            angle_j = 2 * math.pi * j / n_ring
            angle_jn = 2 * math.pi * jn / n_ring
            sin_j = math.sin(angle_j)
            sin_jn = math.sin(angle_jn)
            if (sin_j - mouth_angle_z) * (sin_jn - mouth_angle_z) < 0:
                continue
            if j in mouth_slit_js and jn in mouth_slit_js:
                continue
        bm.faces.new([rings[i][j], rings[i][jn], rings[i + 1][jn], rings[i + 1][j]])

# Cap tail with a fan
tail_center = bm.verts.new(path[0])
for j in range(n_ring):
    jn = (j + 1) % n_ring
    bm.faces.new([tail_center, rings[0][jn], rings[0][j]])

# Cap snout: separate upper and lower jaw caps
snout_dir = get_tangent(total_pts - 1)
last_ring = rings[-1]
slit_thresh = 0.14
snout_r = body_radius * body_taper(1.0)

tip_gap = snout_r * mouth_gap_scale * 0.45 * 0.5

upper_tip = bm.verts.new(
    path[-1] + snout_dir * snout_r * 0.5 + up * tip_gap * 0.5
)
for j in range(n_ring):
    jn = (j + 1) % n_ring
    sin_j = math.sin(2 * math.pi * j / n_ring)
    sin_jn = math.sin(2 * math.pi * jn / n_ring)
    if sin_j > mouth_angle_z + slit_thresh and sin_jn > mouth_angle_z + slit_thresh:
        bm.faces.new([upper_tip, last_ring[j], last_ring[jn]])

lower_tip = bm.verts.new(
    path[-1] + snout_dir * snout_r * 0.25 - up * tip_gap * 0.5
)
for j in range(n_ring):
    jn = (j + 1) % n_ring
    sin_j = math.sin(2 * math.pi * j / n_ring)
    sin_jn = math.sin(2 * math.pi * jn / n_ring)
    if sin_j < mouth_angle_z - slit_thresh and sin_jn < mouth_angle_z - slit_thresh:
        bm.faces.new([lower_tip, last_ring[j], last_ring[jn]])

body_mesh = bpy.data.meshes.new("snake_body")
bm.to_mesh(body_mesh)
bm.free()

snake_body = bpy.data.objects.new("snake_body", body_mesh)
bpy.context.scene.collection.objects.link(snake_body)
bpy.context.view_layer.objects.active = snake_body
snake_body.select_set(True)
bpy.ops.object.shade_smooth()

parts = [snake_body]

# ============================================================
# Eyes: spheres on the head sides
# ============================================================
eye_idx = int(eye_t * (total_pts - 1))
eye_center = ring_centers[eye_idx]
eye_binormal = ring_binormals[eye_idx]
eye_normal = ring_normals[eye_idx]

r_at_eye = body_radius * body_taper(eye_t)
w_at_eye, h_at_eye = head_shape(eye_t)

eye_r = body_radius * eye_radius_frac

for side in [-1, 1]:
    eye_pos = (
        eye_center
        + eye_binormal * (side * r_at_eye * width_aspect * w_at_eye * 0.92)
        + eye_normal * (r_at_eye * height_aspect * h_at_eye * eye_height_frac)
    )
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=10, ring_count=6, radius=eye_r, location=eye_pos
    )
    eye = bpy.context.active_object
    eye.name = f"eye_{side}"
    apply_tf(eye)
    parts.append(eye)

# ============================================================
# Nostrils: tiny bumps near the snout tip
# ============================================================
nostril_t = 0.985
nostril_idx = int(nostril_t * (total_pts - 1))
nostril_center = ring_centers[nostril_idx]
nostril_binormal = ring_binormals[nostril_idx]
nostril_normal = ring_normals[nostril_idx]
nostril_tangent = get_tangent(nostril_idx)
r_at_nostril = body_radius * body_taper(nostril_t)

nostril_r = body_radius * 0.06
for side in [-1, 1]:
    nostril_pos = (
        nostril_center
        + nostril_binormal * (side * r_at_nostril * 0.5)
        + nostril_normal * (r_at_nostril * 0.3)
        + nostril_tangent * (r_at_nostril * 0.1)
    )
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=6, ring_count=4, radius=nostril_r, location=nostril_pos
    )
    nostril = bpy.context.active_object
    nostril.name = f"nostril_{side}"
    apply_tf(nostril)
    parts.append(nostril)

# ============================================================
# Join all parts
# ============================================================
result = join_objs(parts)
if result is not None and len(result.data.materials) == 0:
    result.data.materials.append(CREATURE_MAT)
result.name = "SnakeFactory"
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
