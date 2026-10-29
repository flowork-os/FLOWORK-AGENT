# [FL_INDEX: keywords="blender_factory, procedural_3d, LichenFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LichenFactory | Category: factories_geo
# Prompt: A 3D model of a lichen growth rendered from a slightly elevated front perspective, featuring a dense cluster of ruffled, leaf-like lobes in muted sage green that radiate outward from a central base to form a low rosette-shaped organic structure.

import os
import math
import random
import colorsys
from itertools import chain
from statistics import mean

import bmesh
import bpy
import numpy as np
from numpy.random import uniform, normal as N
from mathutils import Vector, kdtree, noise

SEED = int(os.environ.get("SEED", 0))


def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)


# ==============================================================================
# Inlined material (hand-crafted for LichenFactory)
#
# Upstream shader structure:
#   - Procedural musgrave texture drives a 3-stop HSV color ramp (2 lichen tints
#     + pure black).
#   - MixRGB uses ObjectInfo Random as factor to blend the ramp with a darker
#     desaturated background tint (per-instance variation in upstream).
#   - Principled BSDF: Base Color = mix, Subsurface Weight = 0.02,
#     Subsurface Radius = (0.01, 0.01, 0.01), Subsurface Color = background,
#     Roughness = 1.0.
#
# Blender 5.0 adaptation:
#   - ShaderNodeTexMusgrave was removed → use ShaderNodeTexNoise with a
#     high Scale. noise `Factor` is already 0..1 so no MapRange wrap is needed
#     (the upstream MapRange(-1,1→0,1) around Musgrave existed because the
#     Musgrave Fac output was signed).
#   - Mix RGBA socket indices: inputs[0]=Fac, inputs[6]=A, inputs[7]=B,
#     outputs[2]=Result.
# ==============================================================================


def _hsv2rgba(h, s, v):
    h = float(h) % 1.0
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, min(1.0, float(v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def make_lichen_mat(base_hue, h_perturb, s_perturb, v_perturb,
                    name="LichenFactory_Material"):
    def map_perturb(h, s, v):
        return _hsv2rgba(h + h_perturb, s + s_perturb, v / v_perturb)

    subsurface_ratio = 0.02
    roughness = 1.0

    # Ramp anchor colours
    color_0 = map_perturb(base_hue, 1.0, 0.05)
    color_1 = map_perturb((base_hue + 0.05) % 1.0, 1.0, 0.05)
    color_2 = (0.0, 0.0, 0.0, 1.0)
    background = map_perturb(base_hue, 0.5, 0.3)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    link = nt.links.new

    # Procedural noise stand-in for Musgrave (scale 5000 in upstream)
    noise_tex = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise_tex.noise_dimensions = "3D"
    except Exception:
        pass
    noise_tex.inputs["Scale"].default_value = 5000.0
    # Keep detail/roughness/distortion at node defaults; the visual target is
    # a fine speckle just like the upstream high-scale musgrave.

    noise_fac_sock = (
        noise_tex.outputs.get("Fac")
        or noise_tex.outputs.get("Factor")
        or noise_tex.outputs[0]
    )

    # 3-stop color ramp driven by noise Factor
    cr = nt.nodes.new("ShaderNodeValToRGB")
    link(noise_fac_sock, cr.inputs["Fac"])
    ramp = cr.color_ramp
    # There are 2 default stops; add a third.
    ramp.elements.new(0.5)
    ramp.elements[0].position = 0.0
    ramp.elements[1].position = 0.5
    ramp.elements[2].position = 1.0
    ramp.elements[0].color = color_0
    ramp.elements[1].color = color_1
    ramp.elements[2].color = color_2

    # Object Info Random drives mix factor (per-instance variation)
    obj_info = nt.nodes.new("ShaderNodeObjectInfo")

    # Background RGB constant
    bg_rgb = nt.nodes.new("ShaderNodeRGB")
    bg_rgb.outputs[0].default_value = background

    # Mix ramp colour with background, factor = Object Info Random
    mix_rgb = nt.nodes.new("ShaderNodeMix")
    mix_rgb.data_type = "RGBA"
    link(obj_info.outputs["Random"], mix_rgb.inputs[0])
    link(cr.outputs["Color"], mix_rgb.inputs[6])
    link(bg_rgb.outputs[0], mix_rgb.inputs[7])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    link(mix_rgb.outputs[2], bsdf.inputs["Base Color"])

    # Subsurface (socket naming differs across versions; use best match)
    ss_weight_key = None
    for key in ("Subsurface Weight", "Subsurface"):
        if key in bsdf.inputs:
            ss_weight_key = key
            break
    if ss_weight_key is not None:
        bsdf.inputs[ss_weight_key].default_value = subsurface_ratio
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (0.01, 0.01, 0.01)
    # Subsurface Color: Blender 5.0 removed the dedicated socket; it only
    # exists on Principled v1 (Blender 3.x). Attempt to set it, skip if gone.
    if "Subsurface Color" in bsdf.inputs:
        bsdf.inputs["Subsurface Color"].default_value = background
    bsdf.inputs["Roughness"].default_value = roughness

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# Phase 1 — material; mirrors LichenFactory.__init__ RNG order exactly
seed_all(SEED)
_base_hue_init = float(np.random.uniform(0.15, 0.3))    # __init__ base_hue
_h_perturb = float(np.random.uniform(-0.02, 0.02))
_s_perturb = float(np.random.uniform(-0.05, 0.0))
_v_perturb = float(np.random.uniform(1.0, 1.5))
_final_hue = (_base_hue_init + float(np.random.uniform(-0.04, 0.04))) % 1.0

CATEG_MAT = make_lichen_mat(
    base_hue=_final_hue,
    h_perturb=_h_perturb,
    s_perturb=_s_perturb,
    v_perturb=_v_perturb,
    name="LichenFactory_Material",
)
CATEG_MAT.use_fake_user = True

# === Geometry ===
random.seed(SEED)
np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.context.scene.cursor.location = (0, 0, 0)


def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)


def _set_active(obj):
    _select_none()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


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


# --- Build initial polygon mesh (matches original LichenFactory.build_lichen_circle_mesh) ---
n = np.random.randint(4, 6)
angles = polygon_angles(n)
z_jitter = N(0, 0.02, n)
r_jitter = np.exp(uniform(-0.2, 0.0, n))

# Vertex/face layout matching original: faces = (i, (i-1)%n, center)
verts = list(zip(np.cos(angles) * r_jitter, np.sin(angles) * r_jitter, z_jitter))
verts.append((0, 0, 0))  # center
faces = [(i, (i - 1) % n, n) for i in range(n)]

mesh = bpy.data.meshes.new("lichen_mesh")
mesh.from_pydata(verts, [], faces)
mesh.update()

obj = bpy.data.objects.new("LichenFactory", mesh)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj

# Boundary vertex group — outer vertices grow
vg = obj.vertex_groups.new(name="Boundary")
vg.add(list(range(n)), 1.0, 'REPLACE')

# --- Differential growth (matches original max_polygon range) ---
max_polys = 1e4 * uniform(0.2, 1.0)
build_diff_growth(
    obj, vg.index,
    max_polygons=max_polys,
    growth_scale=(1, 1, 0.5),
    inhibit_shell=4,
    repulsion_radius=2,
    dt=0.25,
)

# --- Post-processing modifiers ---
_set_active(obj)

# Solidify: give the paper-thin mesh realistic thickness
mod_sol = obj.modifiers.new("Solidify", 'SOLIDIFY')
mod_sol.thickness = 0.06  # in pre-scale units
mod_sol.offset = 1  # grow along normal direction (original face winding has normals pointing down)
mod_sol.use_even_offset = True
bpy.ops.object.modifier_apply(modifier=mod_sol.name)

# Subdivision surface for smooth organic look
mod_sub = obj.modifiers.new("Subsurf", 'SUBSURF')
mod_sub.levels = 1
mod_sub.render_levels = 2
bpy.ops.object.modifier_apply(modifier=mod_sub.name)

# Scale down to final size
obj.scale = (0.004, 0.004, 0.004)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Smooth shading
bpy.ops.object.shade_smooth()

# === Material binding ===
obj.data.materials.clear()
obj.data.materials.append(CATEG_MAT)

print(
    f"LichenFactory built: {len(obj.data.vertices)} verts, "
    f"{len(obj.data.polygons)} faces, "
    f"{len(obj.data.materials)} material slot(s)"
)
