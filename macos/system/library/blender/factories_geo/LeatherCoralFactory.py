# [FL_INDEX: keywords="blender_factory, procedural_3d, LeatherCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeatherCoralFactory | Category: factories_geo
# Prompt: A leather coral rendered as a textured 3D model. The coral is a large, low-spreading, fleshy colony with multiple broad lobed sections radiating outward from a central point, creating an irregular, roughly circular footprint. The entire upper surface is densely covered in fine granular polyps and micro-textured bumps, giving it an extremely rough, matte appearance. The coloring is warm sandy brown with olive-green tones throughout, typical of a living soft coral. A single upright spire rises from the center. The form casts a wide shadow on the white background.

"""
Standalone Blender script (geometry + coral material) – LeatherCoralFactory, seed 0.
Run:  blender --background --python LeatherCoralFactory.py

LeatherBaseCoralFactory base shape + coral_postprocess(obj, [1,1,1], 0.02).
Uses proper build_diff_growth() with attraction/repulsion/noise simulation.
"""
import os
import random
import colorsys
import bpy
import bmesh
import numpy as np
import math
from itertools import chain
from statistics import mean
from mathutils import Vector, kdtree, noise


SEED = int(os.environ.get("SEED", 0))
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
CORAL_MAT = make_coral_material(_coral_base_hue, "LeatherCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)


maker = 'leather'
print(f"DiffGrowth coral variant: {maker}")


# ── Polygon-base mesh builder ────────────────────────────────────────────────
def polygon_angles(n):
    for _ in range(100):
        angles = np.sort(np.random.uniform(0, 2*np.pi, n))
        diff = (angles - np.roll(angles, 1)) % (2*np.pi)
        if (diff >= np.pi/6).all() and (diff <= 2*np.pi/3).all():
            return angles
    return np.sort((np.arange(n) * (2*np.pi/n) + np.random.uniform(0, 2*np.pi)) % (2*np.pi))


def make_polygon_base(n_base=4, n_colonies=1, stride=2.0):
    if n_colonies > 1:
        angles_c = polygon_angles(np.random.randint(2, 6))
        offsets  = np.stack([np.cos(angles_c), np.sin(angles_c), np.zeros_like(angles_c)]).T * stride
    else:
        offsets = np.zeros((1, 3))

    all_verts = []; all_faces = []
    for i, offset in enumerate(offsets):
        angles = polygon_angles(n_base)
        verts  = np.block([[np.cos(angles), 0], [np.sin(angles), 0], [np.zeros(n_base + 1)]]).T
        verts += offset
        base   = (n_base + 1) * i
        faces  = [[base + j, base + (j+1) % n_base, base + n_base] for j in range(n_base)]
        all_verts.append(verts)
        all_faces.extend(faces)
    return np.concatenate(all_verts), all_faces


# ── Differential growth simulation ──────────────────────────────────────────
def grow_step(bm, vg_index=0, split_radius=0.5, repulsion_radius=1.0, dt=0.1,
              growth_scale=(1, 1, 1), noise_scale=2.0, growth_vec=(0, 0, 1),
              fac_attr=1.0, fac_rep=1.0, fac_noise=1.0, inhibit_base=1.0,
              inhibit_shell=0.0):
    kd = kdtree.KDTree(len(bm.verts))
    for i, vert in enumerate(bm.verts):
        kd.insert(vert.co, i)
    kd.balance()
    seed_vector = Vector((0, 0, np.random.randint(0, 1000)))
    gv = Vector(growth_vec)
    gs = Vector(growth_scale)

    for vert in bm.verts:
        w = vert[bm.verts.layers.deform.active].get(vg_index, 0)
        if w > 0:
            f_attr = Vector()
            for edge in vert.link_edges:
                f_attr += edge.other_vert(vert).co - vert.co
            f_rep = Vector()
            for (co, index, distance) in kd.find_range(vert.co, repulsion_radius):
                if index != vert.index:
                    f_rep += (vert.co - co).normalized() * (math.exp(-1 * (distance / repulsion_radius) + 1) - 1)
            f_noise = noise.noise_vector(vert.co * noise_scale + seed_vector)
            force = fac_attr * f_attr + fac_rep * f_rep + fac_noise * f_noise + gv
            vert.co += force * dt * dt * w * gs

            if inhibit_base > 0 and not vert.is_boundary:
                w = w ** (1 + inhibit_base) - 0.01
            if inhibit_shell > 0:
                w = w * pow(vert.calc_shell_factor(), -1 * inhibit_shell)
            vert[bm.verts.layers.deform.active][vg_index] = w

    edges_to_subdivide = []
    for e in bm.edges:
        avg_weight = mean(v[bm.verts.layers.deform.active].get(vg_index, 0) for v in e.verts)
        if avg_weight > 0:
            l = e.calc_length()
            if l / split_radius > 1 / avg_weight:
                edges_to_subdivide.append(e)

    if edges_to_subdivide:
        bmesh.ops.subdivide_edges(bm, edges=edges_to_subdivide, smooth=1.0, cuts=1,
                                  use_grid_fill=True, use_single_edge=True)
        adjacent_faces = set(chain.from_iterable(e.link_faces for e in edges_to_subdivide))
        bmesh.ops.triangulate(bm, faces=list(adjacent_faces))


def build_diff_growth(obj, vg_index, max_polygons=1e4, **kwargs):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.layers.deform.verify()
    bm.verts.ensure_lookup_table()

    deform_layer = bm.verts.layers.deform.active
    for mv in obj.data.vertices:
        bv = bm.verts[mv.index]
        for g in mv.groups:
            bv[deform_layer][g.group] = g.weight

    plateau = 0
    step = 0
    while len(bm.faces) < max_polygons:
        v = len(bm.verts)
        grow_step(bm, vg_index, **kwargs)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        step += 1
        if v == len(bm.verts):
            plateau += 1
            if plateau > 50:
                break
        else:
            plateau = 0

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


# ── Build leather coral ──────────────────────────────────────────────────────
n_base = 4
prob_multiple = 0.5
n_colonies = np.random.randint(2, 3) if np.random.uniform() < prob_multiple else 1
growth_vec = (0, 0, float(np.random.uniform(0.8, 1.2)))
growth_scale_z = float(np.random.uniform(0.5, 0.7))
growth_scale = (1.0, 1.0, growth_scale_z)

verts0, faces0 = make_polygon_base(n_base, n_colonies)
max_polys = int(1e3 * n_colonies)

mesh = bpy.data.meshes.new("leather_base")
mesh.from_pydata(verts0.tolist(), [], faces0)
mesh.update()
obj = bpy.data.objects.new("leather_base", mesh)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

n_verts = len(verts0)
boundary_vg = obj.vertex_groups.new(name="Boundary")
boundary_verts = set(range(n_verts))
boundary_verts -= set(range(n_base, n_verts, n_base + 1))
boundary_vg.add(list(boundary_verts), 1.0, "REPLACE")

print(f"Running differential growth (leather, max_polygons={max_polys}) ...")
build_diff_growth(obj, boundary_vg.index, max_polygons=max_polys,
                  fac_noise=2.0, dt=0.25, growth_scale=growth_scale, growth_vec=growth_vec)
print(f"  Growth done: verts={len(obj.data.vertices)} faces={len(obj.data.polygons)}")

# SMOOTH(2)
m_sm = obj.modifiers.new("Smooth", "SMOOTH")
m_sm.iterations = 2
bpy.ops.object.modifier_apply(modifier="Smooth")

# SUBSURF(2)
m_ss = obj.modifiers.new("Sub", "SUBSURF")
m_ss.levels = 2;  m_ss.render_levels = 2
bpy.ops.object.modifier_apply(modifier="Sub")

max_dim = max(obj.dimensions[:2])
if max_dim > 0:
    obj.scale = (2/max_dim,) * 3
bpy.ops.object.transform_apply(scale=True)

tex_ext = bpy.data.textures.new("dg_ext", type='CLOUDS')
tex_ext.noise_scale = 0.5
m_ext = obj.modifiers.new("Ext", "DISPLACE")
m_ext.texture = tex_ext;  m_ext.strength = 0.03;  m_ext.mid_level = 0
bpy.ops.object.modifier_apply(modifier="Ext")

m_sol = obj.modifiers.new("Solid", "SOLIDIFY")
m_sol.thickness = 0.01
bpy.ops.object.modifier_apply(modifier="Solid")

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
min_z = min(v.co.z for v in obj.data.vertices)
obj.location[2] -= min_z * 0.8
bpy.ops.object.transform_apply(location=True)

# ── coral_postprocess ────────────────────────────────────────────────────────
default_scale = [1, 1, 1]
noise_strength = 0.02
bump_prob = 0.3

dims = [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z]
max_xy = max(dims[0], dims[1], 1e-6)
scale = 2.0 * np.array(default_scale) / max_xy * np.random.uniform(0.8, 1.2, 3)
obj.scale = tuple(scale)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(scale=True)

m_rem = obj.modifiers.new("Remesh", "REMESH")
m_rem.mode = "VOXEL"
m_rem.voxel_size = 0.01
bpy.ops.object.modifier_apply(modifier="Remesh")

if noise_strength > 0:
    has_bump = np.random.uniform() < bump_prob
    if has_bump:
        tex_type = np.random.choice(['STUCCI', 'MARBLE'])
        tex = bpy.data.textures.new("coral_noise", type=tex_type)
        tex.noise_scale = math.exp(np.random.uniform(math.log(0.01), math.log(0.02)))
        m_d = obj.modifiers.new("Noise", "DISPLACE")
        m_d.texture = tex
        m_d.strength = noise_strength * np.random.uniform(0.9, 1.2)
        m_d.mid_level = 0
    else:
        tex = bpy.data.textures.new("coral_bump", type='VORONOI')
        tex.noise_scale = math.exp(np.random.uniform(math.log(0.02), math.log(0.03)))
        tex.noise_intensity = math.exp(np.random.uniform(math.log(1.5), math.log(2.0)))
        tex.distance_metric = 'MINKOVSKY'
        tex.minkovsky_exponent = np.random.uniform(1, 1.5)
        m_d = obj.modifiers.new("Bump", "DISPLACE")
        m_d.texture = tex
        m_d.strength = -noise_strength * np.random.uniform(1, 2)
        m_d.mid_level = 1
    bpy.ops.object.modifier_apply(modifier=m_d.name)

# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "LeatherCoralFactory"
print(f"Done: LeatherCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
