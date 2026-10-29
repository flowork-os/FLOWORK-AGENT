# [FL_INDEX: keywords="blender_factory, procedural_3d, CauliflowerCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CauliflowerCoralFactory | Category: factories_geo
# Prompt: A cauliflower coral rendered as a textured 3D model. The object is a dense, compact mass of rounded lobes and knobby polyp clusters, closely resembling a cauliflower head in form. Each lobe is covered in fine, granular surface bumps that give the entire structure a rough, tactile quality. The color is warm sandy beige and tan with faint green-gray undertones, typical of a living reef coral. The mass sits low and wide, casting a deep shadow on the plain white background.

import os
import random
import colorsys
import bpy
import math
import numpy as np
from numpy.random import uniform
from scipy.ndimage import convolve
from skimage.measure import marching_cubes


SEED = int(os.environ.get("SEED", "0"))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
#  Coral material — translated from generate.py:shader_coral (raw bpy)
# ═══════════════════════════════════════════════════════════════════════════

def _seed_all(seed):
    np.random.seed(seed); random.seed(seed)

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0,
                                   max(0.0, min(1.0, float(s))),
                                   max(0.0, min(1.0, float(v))))
    return (r, g, b, 1.0)

def _new_coral_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac_out(node):
    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

def _noise_as_musgrave(nt, ln, scale, tc_obj_out):
    """Musgrave replacement: NoiseTexture (Musgrave removed in Blender 5.0).
    Original: MusgraveTexture -> MapRange[-1,1]->[0,1]. Noise already [0,1]."""

    n = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc_obj_out, n.inputs["Vector"])
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 2.0
    n.inputs["Roughness"].default_value = 0.5
    return _fac_out(n)

def _color_ramp_hsv(nt, ln, fac_out, positions, colors):
    """build_color_ramp with HSV interpolation mode."""

    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.color_mode = "HSV"
    cr.color_ramp.hue_interpolation = "NEAR"
    ln(fac_out, cr.inputs["Fac"])
    for _ in range(len(positions) - 2):
        cr.color_ramp.elements.new(0.0)
    for i, (p, c) in enumerate(zip(positions, colors)):
        cr.color_ramp.elements[i].position = p
        cr.color_ramp.elements[i].color = c
    return cr

def _float_curve(nt, ln, fac_out, anchors):
    """build_float_curve with VECTOR handles."""

    fc = nt.nodes.new("ShaderNodeFloatCurve")
    ln(fac_out, fc.inputs["Value"])
    c = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            c.points[i].location = (x, y)
        else:
            c.points.new(x, y)
        c.points[i].handle_type = "VECTOR"
    fc.mapping.use_clip = False
    fc.mapping.update()
    return fc

def _build_base_hue():
    """CoralFactory.build_base_hue()"""

    if np.random.uniform(0, 1) < 0.25:
        return float(np.random.uniform(0, 1))
    else:
        return float(np.random.uniform(-0.2, 0.3)) % 1.0

def make_coral_material(base_hue, name="CoralMaterial"):
    """Faithful translation of generate.py:shader_coral(nw, base_hue).
    Musgrave-driven 4-stop ColorRamp + light_color mix + noise roughness + SSS."""

    shift = float(np.random.uniform(0.05, 0.1)) * ((-1) ** int(np.random.randint(2)))
    subsurface_color = _hsv2rgba(np.random.uniform(0, 1), np.random.uniform(0, 1), 1.0)
    bright_color = _hsv2rgba((base_hue + shift) % 1, np.random.uniform(0.7, 0.9), 0.2)
    dark_color   = _hsv2rgba(base_hue, np.random.uniform(0.5, 0.7), 0.1)
    light_color  = _hsv2rgba((base_hue + float(np.random.uniform(-0.2, 0.2))) % 1,
                              np.random.uniform(0.2, 0.4), 0.4)
    specular = float(np.random.uniform(0.25, 0.5))
    musg1_scale = float(np.random.uniform(10, 20))
    musg2_scale = float(np.random.uniform(10, 20))
    fc_mid = float(np.random.uniform(0.3, 0.4))
    ss_ratio = float(np.random.uniform(0, 0.05)) if np.random.uniform(0, 1) > 0.5 else 0.0
    ss_r = float(np.random.uniform(0.05, 0.2))

    mat = _new_coral_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Color ramp: musgrave1 -> 4-stop HSV (dark -> bright)
    m1 = _noise_as_musgrave(nt, ln, musg1_scale, tc.outputs["Object"])
    cr = _color_ramp_hsv(nt, ln, m1,
        [0.0, 0.3, 0.7, 1.0],
        [dark_color, dark_color, bright_color, bright_color])

    # Mix with light_color via float curve of musgrave2
    m2 = _noise_as_musgrave(nt, ln, musg2_scale, tc.outputs["Object"])
    fc = _float_curve(nt, ln, m2, [(0, 1), (fc_mid, 0), (1, 0)])
    light_rgb = nt.nodes.new("ShaderNodeRGB")
    light_rgb.outputs[0].default_value = light_color
    mix_c = nt.nodes.new("ShaderNodeMix"); mix_c.data_type = "RGBA"
    ln(fc.outputs["Value"], mix_c.inputs[0])
    ln(cr.outputs["Color"], mix_c.inputs[6])
    ln(light_rgb.outputs[0], mix_c.inputs[7])

    # Roughness: noise(50) -> float curve (0.5 -> 1.0)
    n_r = nt.nodes.new("ShaderNodeTexNoise"); n_r.inputs["Scale"].default_value = 50.0
    fc_r = _float_curve(nt, ln, _fac_out(n_r), [(0, 0.5), (1, 1.0)])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_c.outputs[2], bsdf.inputs["Base Color"])
    ln(fc_r.outputs["Value"], bsdf.inputs["Roughness"])
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = specular
    bsdf.inputs["Subsurface Weight"].default_value = ss_ratio
    bsdf.inputs["Subsurface Radius"].default_value = (ss_r, ss_r, ss_r)
    if "Subsurface Color" in bsdf.inputs:
        bsdf.inputs["Subsurface Color"].default_value = subsurface_color

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# Phase 1: material sampling (mirrors CoralFactory.__init__ with FixedSeed)
# from FixedSeed(factory_seed). To get equivalent diversity, we hash the seed for material
# sampling (otherwise consecutive seeds all produce similar warm-red hues).
_mat_seed = ((SEED + 1) * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
_seed_all(_mat_seed)
_coral_base_hue = _build_base_hue()
CORAL_MAT = make_coral_material(_coral_base_hue, "CauliflowerCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)


# ── Laplacian growth (exact copy of laplacian.py) ──────────────────────────

def mesh_grid(n, sizes):
    shapes = [int((h - l) * n) + 1 for l, h in sizes]
    return np.meshgrid(*(np.linspace(*sz, sh) for sz, sh in zip(sizes, shapes)))

def init_mesh_3d(n, sizes):
    x, y, z = mesh_grid(n, sizes)
    f = (uniform(0.5, 1) * (x - uniform(-0.2, 0.2)) ** 2
         + uniform(0.5, 1) * (y - uniform(-0.2, 0.2)) ** 2
         + uniform(0.1, 0.2) * z ** 2
         < 0.2 * 0.2)
    def extend(f_):
        return uniform(0, 1, f_.shape) < convolve(f_.astype(float), np.ones((3, 3, 3)))
    a = np.where(f, uniform(0.1, 0.5, x.shape), 0) + uniform(0, 0.02, x.shape)
    b = np.where(extend(f), 1, uniform(-1, 1, x.shape)).astype(float)
    return a, b

def build_laplacian(st, a, b, t, k, dt, tau, eps, alpha, gamma, teq):
    for _ in range(t):
        lap_a = convolve(a, st)
        lap_b = convolve(b, st)
        m = alpha / np.pi * np.arctan(gamma * (teq - b))
        da = (eps * eps * lap_a + a * (1.0 - a) * (a - 0.5 + m)) / tau
        db = lap_b + k * da
        a += da * dt
        b += db * dt
    return a, b

n = 32; t = 800
stencil = np.array([
    [[1, 3, 1], [3, 14, 3], [1, 3, 1]],
    [[3, 14, 3], [14, -128, 14], [3, 14, 3]],
    [[1, 3, 1], [3, 14, 3], [1, 3, 1]],
]) / 128.0
height = 1.5
sizes = [-1, 1], [-1, 1], [0, height]

print(f"Running Laplacian growth ({n}^3 grid, {t} iterations) ...")
a_arr, b_arr = init_mesh_3d(n, sizes)
a_arr, b_arr = build_laplacian(stencil * n * n, a_arr, b_arr,
                                t, 2.0, 0.0005, 0.0003, 0.01, 0.9, 10.0, 1.0)

# Apply circular fade to prevent square grid boundary from showing
x_g, y_g, z_g = mesh_grid(n, sizes)
r_xy = np.sqrt(x_g**2 + y_g**2)
fade = np.clip((1.0 - r_xy) / 0.15, 0, 1)
a_arr *= fade

a_pad = np.pad(a_arr, 1)
print("Extracting isosurface (marching cubes) ...")
verts, faces, _, _ = marching_cubes(a_pad, 0.5)
verts -= 1
verts /= n
verts[:, :2] -= 1
print(f"Laplacian mesh: {len(verts)} verts, {len(faces)} faces")

# ── Create Blender mesh ────────────────────────────────────────────────────
mesh = bpy.data.meshes.new("CauliflowerCoralFactory")
mesh.from_pydata(verts.tolist(), [], faces.tolist())
mesh.update()

obj = bpy.data.objects.new("CauliflowerCoralFactory", mesh)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bpy.ops.object.editmode_toggle()
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.editmode_toggle()

# ── geo_extension via Geometry Nodes (exact match to decorate.py) ──────────
noise_strength = float(uniform(0.1, 0.2))
noise_scale = float(uniform(1.4, 2.8))
rand_offset = list(uniform(-1, 1, 3).astype(float))
print(f"geo_extension: noise_strength={noise_strength:.3f}, noise_scale={noise_scale:.3f}")

ng = bpy.data.node_groups.new("geo_extension", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

inp = ng.nodes.new("NodeGroupInput")
out = ng.nodes.new("NodeGroupOutput")
pos = ng.nodes.new("GeometryNodeInputPosition")

vec_len = ng.nodes.new("ShaderNodeVectorMath"); vec_len.operation = "LENGTH"
ng.links.new(pos.outputs["Position"], vec_len.inputs[0])
div = ng.nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"
div.inputs[0].default_value = 1.0
ng.links.new(vec_len.outputs["Value"], div.inputs[1])
norm = ng.nodes.new("ShaderNodeVectorMath"); norm.operation = "SCALE"
ng.links.new(pos.outputs["Position"], norm.inputs[0])
ng.links.new(div.outputs[0], norm.inputs["Scale"])

add_off = ng.nodes.new("ShaderNodeVectorMath"); add_off.operation = "ADD"
ng.links.new(norm.outputs["Vector"], add_off.inputs[0])
add_off.inputs[1].default_value = rand_offset

try:
    tex = ng.nodes.new("ShaderNodeTexMusgrave")
    tex.musgrave_dimensions = "3D"
    ng.links.new(add_off.outputs["Vector"], tex.inputs["Vector"])
    tex.inputs["Scale"].default_value = noise_scale
    noise_out = tex.outputs["Fac"]
except:
    tex = ng.nodes.new("ShaderNodeTexNoise")
    tex.noise_dimensions = "3D"
    ng.links.new(add_off.outputs["Vector"], tex.inputs["Vector"])
    tex.inputs["Scale"].default_value = noise_scale
    noise_out = tex.outputs[0]

add_b = ng.nodes.new("ShaderNodeMath"); add_b.operation = "ADD"
add_b.inputs[1].default_value = 0.25
ng.links.new(noise_out, add_b.inputs[0])
mul_s = ng.nodes.new("ShaderNodeMath"); mul_s.operation = "MULTIPLY"
mul_s.inputs[1].default_value = noise_strength
ng.links.new(add_b.outputs[0], mul_s.inputs[0])

sc = ng.nodes.new("ShaderNodeVectorMath"); sc.operation = "SCALE"
ng.links.new(pos.outputs["Position"], sc.inputs[0])
ng.links.new(mul_s.outputs[0], sc.inputs["Scale"])

sp = ng.nodes.new("GeometryNodeSetPosition")
ng.links.new(inp.outputs[0], sp.inputs["Geometry"])
ng.links.new(sc.outputs["Vector"], sp.inputs["Offset"])
ng.links.new(sp.outputs[0], out.inputs[0])

mod = obj.modifiers.new("GeoExt", "NODES")
mod.node_group = ng
bpy.ops.object.modifier_apply(modifier="GeoExt")

# ── SUBSURF level 1 ───────────────────────────────────────────────────────
m_s = obj.modifiers.new("Sub", "SUBSURF")
m_s.levels = 1; m_s.render_levels = 1
bpy.ops.object.modifier_apply(modifier="Sub")

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

# ── CoralFactory.create_asset() postprocess ────────────────────────────────
default_scale = [0.8, 0.8, 0.8]
noise_strength_post = 0.015     # CauliflowerBaseCoralFactory.noise_strength
bump_prob = 0.3

dims = [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z]
max_xy = max(dims[0], dims[1], 1e-6)
s = 2.0 * np.array(default_scale) / max_xy * uniform(0.8, 1.2, 3)
obj.scale = tuple(s)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(scale=True)

# Voxel remesh (face_size=0.01)
m_rem = obj.modifiers.new("Remesh", "REMESH")
m_rem.mode = "VOXEL"; m_rem.voxel_size = 0.01
bpy.ops.object.modifier_apply(modifier="Remesh")

# Noise/bump displacement
if noise_strength_post > 0:
    has_bump = uniform() < bump_prob
    if has_bump:
        tex_type = np.random.choice(['STUCCI', 'MARBLE'])
        tex = bpy.data.textures.new("coral_noise", type=tex_type)
        tex.noise_scale = math.exp(uniform(math.log(0.01), math.log(0.02)))
        m_d = obj.modifiers.new("Noise", "DISPLACE")
        m_d.texture = tex
        m_d.strength = noise_strength_post * uniform(0.9, 1.2)
        m_d.mid_level = 0
    else:
        tex = bpy.data.textures.new("coral_bump", type='VORONOI')
        tex.noise_scale = math.exp(uniform(math.log(0.02), math.log(0.03)))
        tex.noise_intensity = math.exp(uniform(math.log(1.5), math.log(2.0)))
        tex.distance_metric = 'MINKOVSKY'
        tex.minkovsky_exponent = uniform(1, 1.5)
        m_d = obj.modifiers.new("Bump", "DISPLACE")
        m_d.texture = tex
        m_d.strength = -noise_strength_post * uniform(1, 2)
        m_d.mid_level = 1
    bpy.ops.object.modifier_apply(modifier=m_d.name)

# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "CauliflowerCoralFactory"
print(f"Done: CauliflowerCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
