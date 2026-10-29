# [FL_INDEX: keywords="blender_factory, procedural_3d, SeaweedFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SeaweedFactory | Category: factories_geo
# Prompt: A 3D model of a seaweed plant rendered from a slightly elevated front perspective. The seaweed features a cluster of broad, ruffled green leaves growing upward from a dark base, with overlapping lobed blades that vary in orientation and curvature.

# SEED-deterministic: all random calls seeded from SEED
import os
import math
import random
import colorsys
from itertools import chain
from statistics import mean

import bmesh
import bpy
import numpy as np
from mathutils import Vector, kdtree, noise
from numpy.random import uniform

SEED = int(os.environ.get("SEED", "0"))


# Helpers and seaweed material (raw-bpy port of shader_seaweed)

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)


def log_uniform(lo, hi):
    return float(np.exp(uniform(np.log(lo), np.log(hi))))


def hsv2rgba(h, s, v):
    # colorsys needs clamped inputs to be safe; clamp just for the final RGB.
    h = float(h) % 1.0
    s_c = max(0.0, min(1.0, float(s)))
    v_c = max(0.0, min(1.0, float(v)))
    r, g, b = colorsys.hsv_to_rgb(h, s_c, v_c)
    return (r, g, b, 1.0)


def _fac_out(noise_node):
    return noise_node.outputs.get("Fac") or noise_node.outputs.get("Factor") or noise_node.outputs[0]


def _musgrave_replacement(nt, ln, scale, vector_out=None):
    """ShaderNodeTexNoise replaces removed MusgraveTexture (already outputs [0,1])."""

    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = float(scale)
    n.inputs["Detail"].default_value = 2.0
    n.inputs["Roughness"].default_value = 0.5
    if vector_out is not None:
        ln(vector_out, n.inputs["Vector"])
    return _fac_out(n)


def _color_ramp_hsv(nt, ln, fac_out, positions, colors):
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


def make_seaweed_material(base_hue, name="SeaweedMaterial"):
    h_perturb = float(uniform(-0.1, 0.1))
    s_perturb = float(uniform(-0.1, -0.0))
    v_perturb = log_uniform(1.0, 2.0)

    def map_perturb(h, s, v):
        return hsv2rgba(h + h_perturb, s + s_perturb, v / v_perturb)

    subsurface_ratio = 0.01
    roughness = 0.8
    mix_ratio = float(uniform(0.2, 0.4))
    specular = 0.2

    color_1_s = float(uniform(0.6, 0.8))
    color_1 = map_perturb(base_hue, color_1_s, 0.25)

    color_2_dh = float(uniform(0.05, 0.1))
    color_2_s = float(uniform(0.6, 0.8))
    color_2 = map_perturb(base_hue - color_2_dh, color_2_s, 0.15)

    musgrave_scale = float(uniform(5, 10))
    ss_color = map_perturb(base_hue, 0.6, 0.2)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    ln = nt.links.new

    tc = nt.nodes.new("ShaderNodeTexCoord")

    m_fac = _musgrave_replacement(nt, ln, musgrave_scale, tc.outputs["Object"])
    cr = _color_ramp_hsv(
        nt, ln, m_fac,
        [0.0, 0.3, 0.7, 1.0],
        [color_1, color_1, color_2, color_2],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = specular
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface_ratio
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (0.01, 0.01, 0.01)
    if "Subsurface Color" in bsdf.inputs:
        bsdf.inputs["Subsurface Color"].default_value = ss_color

    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    ln(cr.outputs["Color"], trans.inputs["Color"])

    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    mix_shader.inputs[0].default_value = mix_ratio
    ln(bsdf.outputs["BSDF"], mix_shader.inputs[1])
    ln(trans.outputs["BSDF"], mix_shader.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_shader.outputs[0], out.inputs["Surface"])

    mat.use_backface_culling = False  # thin blade: double-sided lighting
    return mat


# Phase 1 — material sampling on raw SEED (mirrors SeaweedFactory.__init__)
seed_all(SEED)

# Match __init__ RNG order: branch pick for hue range, then shader calls, then freq
_branch = float(uniform(0, 1))
if _branch < 0.5:
    BASE_HUE = float(uniform(0.0, 0.1))
else:
    BASE_HUE = float(uniform(0.3, 0.4))

MAT_SEAWEED = make_seaweed_material(BASE_HUE, name="Seaweed")
_ = 1.0 / log_uniform(200, 500)  # burn freq = 1/log_uniform(200,500) from __init__


# Geometry — from objects_blender/underwater/SeaweedFactory.py

def clear_scene():
    bpy.context.scene.cursor.location = (0, 0, 0)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


def _set_active(obj):
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def apply_tf(obj):
    _set_active(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def polygon_angles(n, min_angle=np.pi / 6, max_angle=np.pi * 2 / 3):
    for _ in range(100):
        angles = np.sort(uniform(0, 2 * np.pi, n))
        diff = (angles - np.roll(angles, 1)) % (2 * np.pi)
        if (diff >= min_angle).all() and (diff <= max_angle).all():
            return angles
    return np.sort((np.arange(n) * (2 * np.pi / n) + uniform(0, 2 * np.pi)) % (2 * np.pi))


def grow_step(bm, vg_index=0, split_radius=0.5, repulsion_radius=1.0, dt=0.1,
              growth_scale=(1, 1, 1), noise_scale=2.0, growth_vec=(0, 0, 1),
              fac_attr=1.0, fac_rep=1.0, fac_noise=1.0, inhibit_base=1.0, inhibit_shell=0.0):
    kd = kdtree.KDTree(len(bm.verts))
    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)
    kd.balance()

    seed_vec = Vector((0, 0, np.random.randint(0, 1000)))
    gv = Vector(growth_vec)
    gs = Vector(growth_scale)

    for v in bm.verts:
        w = v[bm.verts.layers.deform.active].get(vg_index, 0)
        if w > 0:
            f_attr = Vector()
            for e in v.link_edges:
                f_attr += e.other_vert(v).co - v.co
            f_rep = Vector()
            for co, idx, dist in kd.find_range(v.co, repulsion_radius):
                if idx != v.index:
                    f_rep += (v.co - co).normalized() * (math.exp(-dist / repulsion_radius + 1) - 1)
            f_noise = noise.noise_vector(v.co * noise_scale + seed_vec)
            force = fac_attr * f_attr + fac_rep * f_rep + fac_noise * f_noise + gv
            v.co += force * dt * dt * w * gs

            if inhibit_base > 0 and not v.is_boundary:
                w = w ** (1 + inhibit_base) - 0.01
            if inhibit_shell > 0:
                w = w * pow(v.calc_shell_factor(), -inhibit_shell)
            v[bm.verts.layers.deform.active][vg_index] = w

    to_subdiv = []
    for e in bm.edges:
        avg_w = mean(v2[bm.verts.layers.deform.active].get(vg_index, 0) for v2 in e.verts)
        if avg_w > 0 and e.calc_length() / split_radius > 1 / avg_w:
            to_subdiv.append(e)

    if to_subdiv:
        bmesh.ops.subdivide_edges(bm, edges=to_subdiv, smooth=1.0, cuts=1,
                                  use_grid_fill=True, use_single_edge=True)
        adj_faces = set(chain.from_iterable(e.link_faces for e in to_subdiv))
        bmesh.ops.triangulate(bm, faces=list(adj_faces))


def build_diff_growth(obj, vg_index, max_polygons=1e4, **kwargs):
    _set_active(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    plateau = 0
    while len(bm.faces) < max_polygons:
        v_count = len(bm.verts)
        grow_step(bm, vg_index, **kwargs)
        if len(bm.verts) == v_count:
            plateau += 1
            if plateau > 50:
                break
        else:
            plateau = 0
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')


def build(seed=SEED):
    np.random.seed(seed)
    clear_scene()

    growth_z = uniform(3.0, 6.0)
    growth_vec = (0, 0, growth_z)
    inhibit_shell = uniform(0.6, 0.8)
    max_polygons = int(log_uniform(2e3, 1e4))
    fac_noise = uniform(1.5, 2.5)
    repulsion_radius = log_uniform(1.0, 1.5)

    # Build initial polygon base
    n_base = np.random.randint(5, 7)
    angles = polygon_angles(n_base)
    vertices = np.block(
        [[np.cos(angles), 0], [np.sin(angles), 0], [np.zeros(n_base + 1)]]
    ).T
    faces = np.stack(
        [np.arange(n_base), np.roll(np.arange(n_base), 1), np.full(n_base, n_base)]
    ).T

    mesh = bpy.data.meshes.new("seaweed_mesh")
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    mesh.update()

    obj = bpy.data.objects.new("seaweed", mesh)
    bpy.context.scene.collection.objects.link(obj)
    _set_active(obj)

    # Boundary vertex group — outer vertices grow
    boundary = obj.vertex_groups.new(name="Boundary")
    boundary.add(list(range(n_base)), 1.0, 'REPLACE')

    # Differential growth
    build_diff_growth(
        obj, boundary.index,
        max_polygons=max_polygons,
        growth_vec=growth_vec,
        inhibit_shell=inhibit_shell,
        repulsion_radius=repulsion_radius,
        fac_noise=fac_noise,
        dt=0.25,
    )

    # Scale to ~2m, stretch Z
    dims = max(obj.dimensions[:])
    if dims > 0:
        s = 2.0 / dims
        z_stretch = uniform(1.5, 2.0)
        obj.scale = (s, s, s * z_stretch)
    obj.location.z -= 0.02
    apply_tf(obj)

    # Circular scale variation by azimuth angle
    n_interp = np.random.randint(2, 6)
    interp_angles = polygon_angles(n_interp)
    interp_values = np.array([log_uniform(2, 5) for _ in range(n_interp)])

    verts = obj.data.vertices
    for v in verts:
        azimuth = math.atan2(v.co.y, v.co.x) + math.pi  # [0, 2pi]
        dists = np.abs((interp_angles - azimuth + np.pi) % (2 * np.pi) - np.pi)
        weights = np.exp(-dists * 2)
        weights /= weights.sum()
        scale = float(np.dot(weights, interp_values))
        v.co.x *= scale
        v.co.y *= scale
    obj.data.update()

    # subsurface2face_size equivalent: 2 levels ≈ face_size 0.01/2
    _set_active(obj)
    mod = obj.modifiers.new("subsurf", "SUBSURF")
    mod.levels = 2
    mod.render_levels = 2
    bpy.ops.object.modifier_apply(modifier=mod.name)

    mod = obj.modifiers.new("tri", "TRIANGULATE")
    bpy.ops.object.modifier_apply(modifier=mod.name)

    smooth_factor = uniform(-0.8, 0.8)
    mod = obj.modifiers.new("smooth", "SMOOTH")
    mod.factor = smooth_factor
    mod.iterations = 3
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Displace (STUCCI or MARBLE)
    tex_type = str(np.random.choice(["STUCCI", "MARBLE"]))
    tex = bpy.data.textures.new("sw_disp", type=tex_type)
    tex.noise_scale = log_uniform(0.05, 0.2)
    mod = obj.modifiers.new("disp", "DISPLACE")
    mod.texture = tex
    mod.strength = uniform(0.0, 0.03)
    mod.mid_level = 0.5
    bpy.ops.object.modifier_apply(modifier=mod.name)

    bend_angle = uniform(-math.pi / 4, 0)  # static; original uses animated driver
    mod = obj.modifiers.new("bend", "SIMPLE_DEFORM")
    mod.deform_method = 'BEND'
    mod.deform_axis = 'Y'
    mod.angle = bend_angle
    bpy.ops.object.modifier_apply(modifier=mod.name)

    apply_tf(obj)
    obj.name = "SeaweedFactory"

    obj.data.materials.clear()
    obj.data.materials.append(MAT_SEAWEED)

    return obj


build(SEED)
