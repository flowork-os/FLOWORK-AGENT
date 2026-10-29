# [FL_INDEX: keywords="blender_factory, procedural_3d, LeatherBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeatherBaseCoralFactory | Category: factories_geo
# Prompt: A white base mesh 3D model of a leather coral structure. The object shows the raw geometry of a soft coral colony — multiple smooth, fleshy lobes rise and curl from a central root point, each with gently wavy and scalloped margins. The form is compact and roughly dome-shaped with many petal-like protrusions. Without any texture or material color applied, the pure white smooth surfaces reveal the organic lobe topology with soft shadows indicating the depth between lobes.

"""
Standalone Blender script – LeatherBaseCoralFactory, seed 0.
Run:  blender --background --python LeatherBaseCoralFactory.py

Forces diff_growth leather variant (upward-growing colonies).
Uses proper build_diff_growth() with attraction/repulsion/noise simulation.
"""
import bpy
import bmesh
import numpy as np
import math
from itertools import chain
from statistics import mean
from mathutils import Vector, kdtree, noise

np.random.seed(0)

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
bpy.context.collection.objects.link(obj)
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

obj.name = "LeatherBaseCoralFactory"
print(f"Done: LeatherBaseCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
