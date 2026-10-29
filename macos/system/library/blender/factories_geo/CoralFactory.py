# [FL_INDEX: keywords="blender_factory, procedural_3d, CoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CoralFactory | Category: factories_geo
# Prompt: A densely branching coral rendered as a textured 3D model. The coral features an intricate, highly detailed network of fine branches and sub-branches radiating outward in all directions from a central base, creating a spreading bush-like form. Each branch is covered in small polyp bumps and encrusting organisms, giving a cream-ivory to pale green coloration with organic depth. The overall silhouette is wide and irregular, casting an elaborate shadow pattern on the white background.

"""
Standalone Blender script – CoralFactory, seed 0.
Run:  blender --background --python CoralFactory.py

Randomly picks one of: diff_growth, reaction_diffusion, tube, tree,
cauliflower, elkhorn, star with weights [0.15, 0.2, 0.15, 0.2, 0.2, 0.15, 0.2]
then applies appropriate coral_postprocess.
"""
import bpy
import bmesh
import numpy as np
import math
from itertools import chain
from statistics import mean
from mathutils import Vector, kdtree, noise
from scipy.interpolate import interp1d
from scipy.ndimage import convolve as ndimage_convolve
from scipy.spatial import KDTree as ScipyKDTree
from skimage.measure import marching_cubes

np.random.seed(0)

# ── Choose base type ──────────────────────────────────────────────────────────
_type_weights = np.array([0.15, 0.2, 0.15, 0.2, 0.2, 0.15, 0.2])
_type_weights /= _type_weights.sum()
_type_names = ["diff_growth", "reaction_diffusion", "tube", "tree",
               "cauliflower", "elkhorn", "star"]

chosen_base = np.random.choice(_type_names, p=_type_weights)
print(f"\nCoralFactory: chosen base = {chosen_base}")

# ── post-process parameters per type ─────────────────────────────────────────
_postprocess_params = {
    "diff_growth":        ([1, 1, 1],       0.02),
    "reaction_diffusion": ([0.8, 0.8, 0.8], 0.01),
    "tube":               ([0.7, 0.7, 0.7], 0.02),
    "tree":               ([1, 1, 1],       0.01),
    "cauliflower":        ([0.8, 0.8, 0.8], 0.015),
    "elkhorn":            ([0.8, 0.8, 0.8], 0.005),
    "star":               ([0.8, 0.8, 0.8], 0.002),
}
default_scale, noise_strength = _postprocess_params[chosen_base]
bump_prob = 0.3


# ──────────────────────────────────────────────────────────────────────────────
# GEOMETRY helpers
# ──────────────────────────────────────────────────────────────────────────────

def _polygon_angles(n):
    for _ in range(100):
        angles = np.sort(np.random.uniform(0, 2*np.pi, n))
        diff = (angles - np.roll(angles, 1)) % (2*np.pi)
        if (diff >= np.pi/6).all() and (diff <= 2*np.pi/3).all():
            return angles
    return np.sort((np.arange(n) * (2*np.pi/n) + np.random.uniform(0, 2*np.pi)) % (2*np.pi))


# ── Shared tree/branch helpers ───────────────────────────────────────────────

def _smooth_interp(points, res):
    """Quadratic interpolation of 3-D control points using scipy."""

    N = len(points)
    if N < 2:
        return points.copy()
    t_ctrl = np.arange(N)
    t_fine = np.linspace(0, N - 1, (N - 1) * res + 1)
    fn = interp1d(t_ctrl, points, axis=0, kind='quadratic' if N >= 3 else 'linear')
    return fn(t_fine)


def _rand_path(n_pts, init_vec, std=0.4, momentum=0.5, sz=0.05, sz_decay=1.0,
               pull_dir=None, pull_factor=0):
    init_vec = np.array(init_vec, dtype=float)
    if pull_dir is not None:
        pull_dir = np.array(pull_dir, dtype=float)
    init_vec = init_vec / (np.linalg.norm(init_vec) + 1e-8)
    path = np.zeros((n_pts, 3))
    for i in range(1, n_pts):
        if i == 1:
            prev_delta = init_vec * sz
        else:
            prev_delta = path[i - 1] - path[i - 2]
        new_delta = prev_delta + np.random.randn(3) * std
        if pull_dir is not None:
            new_delta += pull_factor * pull_dir
        prev_sz = np.linalg.norm(prev_delta) + 1e-8
        new_delta = (new_delta / (np.linalg.norm(new_delta) + 1e-8)) * prev_sz
        tmp_mom = 1 - (1 - momentum) * (i + 1) / n_pts
        delta = prev_delta * tmp_mom + new_delta * (1 - tmp_mom)
        delta = (delta / (np.linalg.norm(delta) + 1e-8)) * sz * (sz_decay ** i)
        path[i] = path[i - 1] + delta
    return path


def _rodrigues_rot(v, axis, angle):
    axis = axis / (np.linalg.norm(axis) + 1e-8)
    c, s = math.cos(angle), math.sin(angle)
    return v * c + np.cross(axis, v) * s + axis * np.dot(axis, v) * (1 - c)


def _get_spawn_direction(path, idx, ang_min, ang_max):
    if idx < 1: idx = 1
    curr_vec = path[idx] - path[idx - 1]
    if np.linalg.norm(curr_vec) < 1e-10: curr_vec = np.array([0, 0, 1.0])
    rnd_ang = np.random.uniform(ang_min, ang_max) * np.sign(np.random.randn())
    return _rodrigues_rot(curr_vec, np.array([0.0, 0.0, 1.0]), rnd_ang)


def _swept_tube_mesh(path, radii, n_ring=6):
    """Build tube mesh along path with given radii per cross-section."""

    N = len(path)
    all_v = []
    for i in range(N):
        pt, r = path[i], radii[min(i, len(radii) - 1)]
        if i == 0: tangent = path[1] - path[0]
        elif i == N - 1: tangent = path[-1] - path[-2]
        else: tangent = path[i + 1] - path[i - 1]
        tn = np.linalg.norm(tangent)
        tangent = tangent / tn if tn > 1e-10 else np.array([0.0, 0.0, 1.0])
        ref = np.array([0.0, 0, 1]) if abs(tangent[2]) < 0.9 else np.array([1.0, 0, 0])
        nx = np.cross(ref, tangent); nx /= np.linalg.norm(nx) + 1e-8
        ny = np.cross(tangent, nx)
        ang = np.linspace(0, 2 * np.pi, n_ring, endpoint=False)
        all_v.append(pt + r * (np.cos(ang)[:, None] * nx + np.sin(ang)[:, None] * ny))
    verts = np.concatenate(all_v, axis=0)
    faces = []
    for i in range(N - 1):
        for j in range(n_ring):
            a = i * n_ring + j; b = i * n_ring + (j + 1) % n_ring
            c = (i + 1) * n_ring + (j + 1) % n_ring; d = (i + 1) * n_ring + j
            faces.append([a, b, c, d])
    tip_idx = len(verts)
    verts = np.vstack([verts, path[-1]])
    for j in range(n_ring):
        faces.append([(N - 1) * n_ring + j, (N - 1) * n_ring + (j + 1) % n_ring, tip_idx])
    return verts, faces


# ── Tentacle system ──────────────────────────────────────────────────────────

def _sample_direction(min_z=0.6):
    """Rejection-sample a random unit direction with z > min_z."""

    for _ in range(100):
        x = np.random.randn(3)
        y = x / (np.linalg.norm(x) + 1e-8)
        if y[2] > min_z:
            return y
    return np.array([0.0, 0.0, 1.0])


def _build_tentacle_curve(base_radius=0.003):
    """Build one tentacle using Blender curves for smooth cylindrical tubes.

    5 branches, 8 pts each, std=0.5, momentum=0.5, sz=0.008.
    """

    parts = []
    for b in range(5):
        path = _rand_path(8, _sample_direction(0.6), std=0.5, momentum=0.5, sz=0.008)

        # Create curve with circular bevel (smooth tube)
        curve = bpy.data.curves.new(f"_tent_{b}", 'CURVE')
        curve.dimensions = '3D'
        curve.bevel_depth = base_radius
        curve.bevel_resolution = 1  # 8-sided circle profile (close to original's 6)
        curve.use_fill_caps = True

        sp = curve.splines.new('POLY')
        sp.points.add(len(path) - 1)
        for i, pt in enumerate(path):
            sp.points[i].co = (*pt, 1.0)
            # Taper: exponential decay toward tip (matches original radius_fn)
            sp.points[i].radius = max(0.05, 1.0 * (0.5 ** (i / max(1, len(path) / 2.5))))

        obj_c = bpy.data.objects.new(f"_tent_{b}", curve)
        bpy.context.collection.objects.link(obj_c)
        bpy.ops.object.select_all(action='DESELECT')
        obj_c.select_set(True)
        bpy.context.view_layer.objects.active = obj_c
        bpy.ops.object.convert(target='MESH')
        parts.append(bpy.context.active_object)

    # Join all branches into one tentacle
    if len(parts) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for p in parts:
            p.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
    tent = bpy.context.active_object

    # Extract mesh data as numpy arrays
    verts = np.array([v.co[:] for v in tent.data.vertices])
    faces = [list(p.vertices) for p in tent.data.polygons]

    # Clean up temp object
    bpy.data.objects.remove(tent, do_unlink=True)
    return verts, faces


def _distribute_tentacles(obj, n_variants=5, density=500, radius_threshold=0.4):
    """Sample surface points via bmesh, filter with KDTree, place curve-based tentacles.

    - density=500, merge_distance=0.05, radius_threshold=0.4 for tree coral
    - Points near center (< radius_threshold) get sparser placement
    - Tentacles aligned to surface normals, random scale 0.6-1.0
    """
    # Build smooth tentacle variants using Blender curves
    variants = []
    for i in range(n_variants):
        verts, faces = _build_tentacle_curve(base_radius=np.random.uniform(0.002, 0.004))
        variants.append((verts, faces))

    # Sample surface points using bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    face_areas = np.array([f.calc_area() for f in bm.faces])
    total_area = face_areas.sum()
    if total_area < 1e-10:
        bm.free(); return

    n_raw = min(int(total_area * density), 5000)
    probs = face_areas / total_area
    face_indices = np.random.choice(len(bm.faces), size=n_raw, p=probs)

    points, normals = [], []
    for fi in face_indices:
        face = bm.faces[fi]
        vco = [np.array(v.co[:]) for v in face.verts]
        if len(vco) == 3:
            r1, r2 = np.random.random(), np.random.random()
            if r1 + r2 > 1: r1, r2 = 1 - r1, 1 - r2
            pt = vco[0] * (1 - r1 - r2) + vco[1] * r1 + vco[2] * r2
        elif len(vco) == 4:
            u, v_ = np.random.random(), np.random.random()
            pt = vco[0]*(1-u)*(1-v_) + vco[1]*u*(1-v_) + vco[2]*u*v_ + vco[3]*(1-u)*v_
        else:
            pt = np.mean(vco, axis=0)
        points.append(pt)
        normals.append(np.array(face.normal[:]))
    bm.free()

    if not points: return
    points = np.array(points)
    normals = np.array(normals)

    # Radius filtering (matches make_radius_points_fn):
    # - Points very near center excluded
    # - Points within radius_threshold get sparser merge (2x distance)
    radii = np.linalg.norm(points[:, :2], axis=1)
    mask = radii > 0.08
    points, normals, radii = points[mask], normals[mask], radii[mask]
    if len(points) == 0: return

    # Merge by distance using scipy KDTree (matches MergeByDistance in geo_tentacles)
    # Inner region (< radius_threshold) gets 2x merge distance
    tree = ScipyKDTree(points)
    keep = np.ones(len(points), dtype=bool)
    for i in range(len(points)):
        if not keep[i]: continue
        md = 0.1 if radii[i] < radius_threshold else 0.05
        for j in tree.query_ball_point(points[i], md):
            if j > i: keep[j] = False
    points, normals = points[keep], normals[keep]
    if len(points) == 0: return

    # Place tentacles at each point, aligned to surface normal
    all_tv, all_tf, t_off = [], [], 0
    for idx in range(len(points)):
        pt, nrm = points[idx], normals[idx]
        nrm_len = np.linalg.norm(nrm)
        nrm = nrm / nrm_len if nrm_len > 1e-8 else np.array([0, 0, 1.0])

        tv, tf = variants[idx % n_variants]
        if len(tv) == 0: continue

        scale = np.random.uniform(0.6, 1.0)  # matches original

        # Rotation: align Z-up to surface normal
        up = np.array([0, 0, 1.0])
        if abs(np.dot(up, nrm)) > 0.999:
            R = np.eye(3) if nrm[2] > 0 else np.diag([1, -1, -1])
        else:
            axis = np.cross(up, nrm)
            axis /= np.linalg.norm(axis) + 1e-8
            angle = np.arccos(np.clip(np.dot(up, nrm), -1, 1))
            c, s = np.cos(angle), np.sin(angle)
            K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
            R = np.eye(3) + s * K + (1 - c) * (K @ K)

        # Random spin around normal
        spin = np.random.uniform(0, 2 * np.pi)
        S = np.array([[np.cos(spin), -np.sin(spin), 0],
                      [np.sin(spin),  np.cos(spin), 0],
                      [0, 0, 1]])

        transformed = (tv * scale) @ S.T @ R.T + pt
        all_tv.append(transformed)
        all_tf.extend([[fi + t_off for fi in face] for face in tf])
        t_off += len(transformed)

    if not all_tv: return
    tent_verts = np.concatenate(all_tv, axis=0)
    print(f"  Tentacles: {len(points)} placements, {len(tent_verts)} verts")

    tent_mesh = bpy.data.meshes.new("tentacles")
    tent_mesh.from_pydata(tent_verts.tolist(), [], all_tf)
    tent_mesh.update()
    tent_obj = bpy.data.objects.new("tentacles", tent_mesh)
    bpy.context.collection.objects.link(tent_obj)

    # Smooth-shade tentacles (they're smooth cylinders)
    bpy.ops.object.select_all(action='DESELECT')
    tent_obj.select_set(True)
    bpy.context.view_layer.objects.active = tent_obj
    bpy.ops.object.shade_smooth()

    # Join with coral body
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    tent_obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()


# ──────────────────────────────────────────────────────────────────────────────
# GEOMETRY builders
# ──────────────────────────────────────────────────────────────────────────────

def _grow_step(bm, vg_index=0, split_radius=0.5, repulsion_radius=1.0, dt=0.1,
               growth_scale=(1, 1, 1), noise_scale=2.0, growth_vec=(0, 0, 1),
               fac_attr=1.0, fac_rep=1.0, fac_noise=1.0, inhibit_base=1.0,
               inhibit_shell=0.0):
    kd = kdtree.KDTree(len(bm.verts))
    for i, vert in enumerate(bm.verts):
        kd.insert(vert.co, i)
    kd.balance()
    seed_vector = Vector((0, 0, np.random.randint(0, 1000)))
    gv = Vector(growth_vec); gs = Vector(growth_scale)
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


def _run_diff_growth(obj, vg_index, max_polygons=1e4, **kwargs):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.verts.layers.deform.verify(); bm.verts.ensure_lookup_table()
    deform_layer = bm.verts.layers.deform.active
    for mv in obj.data.vertices:
        bv = bm.verts[mv.index]
        for g in mv.groups:
            bv[deform_layer][g.group] = g.weight
    plateau = 0
    while len(bm.faces) < max_polygons:
        v = len(bm.verts)
        _grow_step(bm, vg_index, **kwargs)
        bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        if v == len(bm.verts):
            plateau += 1
            if plateau > 50: break
        else:
            plateau = 0
    bm.to_mesh(obj.data); bm.free(); obj.data.update()


def build_diff_growth():
    makers  = ['leather', 'flat']
    weights = [0.7, 0.3]
    maker   = np.random.choice(makers, p=weights)
    print(f"  DiffGrowth variant: {maker}")

    n_base = 4
    if maker == 'leather':
        prob_multiple = 0.5
        n_colonies = np.random.randint(2, 3) if np.random.uniform() < prob_multiple else 1
        growth_vec = (0, 0, float(np.random.uniform(0.8, 1.2)))
        growth_scale = (1.0, 1.0, float(np.random.uniform(0.5, 0.7)))
        max_polys = int(1e3 * n_colonies)
        dg_kwargs = dict(max_polygons=max_polys, fac_noise=2.0, dt=0.25,
                         growth_scale=growth_scale, growth_vec=growth_vec)
    else:
        n_colonies = 1
        max_polys = int(4e2)
        dg_kwargs = dict(max_polygons=max_polys, repulsion_radius=2, inhibit_shell=1)

    if n_colonies > 1:
        angles_c = _polygon_angles(np.random.randint(2, 6))
        offsets = np.stack([np.cos(angles_c), np.sin(angles_c), np.zeros_like(angles_c)]).T * 2.0
    else:
        offsets = np.zeros((1, 3))
    all_verts = []; all_faces = []
    for i, offset in enumerate(offsets):
        angles = _polygon_angles(n_base)
        verts = np.block([[np.cos(angles), 0], [np.sin(angles), 0], [np.zeros(n_base + 1)]]).T + offset
        base = (n_base + 1) * i
        faces = [[base + j, base + (j+1) % n_base, base + n_base] for j in range(n_base)]
        all_verts.append(verts); all_faces.extend(faces)
    verts0 = np.concatenate(all_verts)

    mesh = bpy.data.meshes.new("CoralFactory_dg")
    mesh.from_pydata(verts0.tolist(), [], all_faces); mesh.update()
    obj = bpy.data.objects.new("CoralFactory_dg", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)

    n_verts = len(verts0)
    boundary_vg = obj.vertex_groups.new(name="Boundary")
    boundary_verts = set(range(n_verts))
    boundary_verts -= set(range(n_base, n_verts, n_base + 1))
    boundary_vg.add(list(boundary_verts), 1.0, "REPLACE")

    print(f"  Running differential growth (max_polygons={max_polys}) ...")
    _run_diff_growth(obj, boundary_vg.index, **dg_kwargs)

    if maker == 'flat':
        obj.scale = (1, 1, float(np.random.uniform(1.0, 2.0)))
        bpy.ops.object.transform_apply(scale=True)

    m_sm = obj.modifiers.new("Sm", "SMOOTH"); m_sm.iterations = 2
    bpy.ops.object.modifier_apply(modifier="Sm")
    m_ss = obj.modifiers.new("SS", "SUBSURF"); m_ss.levels = 2; m_ss.render_levels = 2
    bpy.ops.object.modifier_apply(modifier="SS")
    max_dim = max(obj.dimensions[:2])
    if max_dim > 0: obj.scale = (2/max_dim,)*3
    bpy.ops.object.transform_apply(scale=True)
    tex_ext = bpy.data.textures.new("dg_ext", type='CLOUDS'); tex_ext.noise_scale = 0.5
    m_ext = obj.modifiers.new("Ext","DISPLACE"); m_ext.texture=tex_ext; m_ext.strength=0.03; m_ext.mid_level=0
    bpy.ops.object.modifier_apply(modifier="Ext")
    m_sol = obj.modifiers.new("Sol","SOLIDIFY"); m_sol.thickness=0.01
    bpy.ops.object.modifier_apply(modifier="Sol")
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    min_z = min(v.co.z for v in obj.data.vertices)
    obj.location[2] -= min_z * 0.8
    bpy.ops.object.transform_apply(location=True)
    return obj


def build_reaction_diffusion():
    maker = np.random.choice(['brain', 'honeycomb'], p=[0.5, 0.5])
    print(f"  RD variant: {maker}")

    def feed2kill(feed): return math.sqrt(feed) / 2 - feed
    if maker == 'brain':
        feed_rate = 0.055; kill_rate = feed2kill(feed_rate); n_inst, stride = 100, 0.02
    else:
        feed_rate = 0.070; kill_rate = feed2kill(feed_rate) - 0.001; n_inst, stride = 5, 0.1

    n_sides = 6; angs = _polygon_angles(n_sides)
    height = 0.2; tilt = 0.2
    a_up = np.random.uniform(-np.pi/18, 0, n_sides)
    a_lo = np.random.uniform(0, np.pi/18, n_sides)
    z_up = 1 + np.random.normal(0, height, n_sides) + np.random.uniform(0, tilt) * np.cos(angs + np.random.uniform(-np.pi, np.pi))
    z_lo = 1 + np.random.normal(0, height, n_sides) + np.random.uniform(0, tilt) * np.cos(angs + np.random.uniform(-np.pi, np.pi))
    R = 1.8
    verts_c = np.block([
        [R*np.cos(angs+a_up), R*np.cos(angs+a_lo), 0, 0],
        [R*np.sin(angs+a_up), R*np.sin(angs+a_lo), 0, 0],
        [z_up, -z_lo, z_up.max()+np.random.uniform(0.1,0.2), -z_lo.max()-np.random.uniform(0.1,0.2)],
    ]).T
    ri = np.arange(n_sides); si = np.roll(ri, -1)
    faces_c = np.block([
        [ri, ri, ri+n_sides, si+n_sides],
        [si, ri+n_sides, si+n_sides, ri+n_sides],
        [np.full(n_sides, 2*n_sides), si, si, np.full(n_sides, 2*n_sides+1)],
    ]).T

    mesh_c = bpy.data.meshes.new("coral_base"); mesh_c.from_pydata(verts_c.tolist(), [], faces_c.tolist()); mesh_c.update()
    obj_base = bpy.data.objects.new("coral_base", mesh_c); bpy.context.collection.objects.link(obj_base)

    bpy.context.view_layer.objects.active = obj_base
    obj_base.select_set(True)
    m_sub = obj_base.modifiers.new("Sub", "SUBSURF")
    m_sub.levels = 2;  m_sub.render_levels = 2
    bpy.ops.object.modifier_apply(modifier="Sub")

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=8, radius=3.0)
    obj = bpy.context.active_object

    def make_weight(coords):
        rng = np.random.default_rng(42)
        mult = rng.uniform(20, 100, (1, n_inst))
        center = coords[rng.integers(0, len(coords)-1, n_inst)]
        phi = (coords[:, np.newaxis, :] * center[np.newaxis, :, :]).sum(-1) * mult
        measure = np.cos(phi).sum(-1) / math.sqrt(n_inst)
        return (np.abs(measure) < stride).astype(float)

    print(f"  Running Gray-Scott RD ({len(obj.data.vertices)} verts, 1000 steps) …")
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    n_v = len(bm.verts)
    coords = np.array([v.co[:] for v in bm.verts])
    edge_from = np.array([e.verts[0].index for e in bm.edges])
    edge_to   = np.array([e.verts[1].index for e in bm.edges])
    size = max(len(v.link_edges) for v in bm.verts)
    bm.free()

    a_rd = np.ones(n_v, dtype=np.float64); b_rd = make_weight(coords)
    diff_a = 0.18*0.5; diff_b = 0.09*0.5
    for _ in range(1000):
        a_msg = a_rd[edge_to] - a_rd[edge_from]; b_msg = b_rd[edge_to] - b_rd[edge_from]
        lap_a = np.bincount(edge_from, a_msg, size) - np.bincount(edge_to, a_msg, size)
        lap_b = np.bincount(edge_from, b_msg, size) - np.bincount(edge_to, b_msg, size)
        ab2 = a_rd * b_rd**2
        a_rd = a_rd + (diff_a*lap_a - ab2 + feed_rate*(1-a_rd))
        b_rd = b_rd + (diff_b*lap_b + ab2 - (kill_rate+feed_rate)*b_rd)
    b_rd *= 1 + np.random.normal(0, 0.05, n_v)

    vg_b = obj.vertex_groups.new(name="B")
    for i in range(n_v): vg_b.add([i], float(np.clip(b_rd[i], 0, 1)), "REPLACE")

    centroid = verts_c.mean(axis=0); obj.location = tuple(centroid)
    bpy.ops.object.transform_apply(location=True)
    m_sw = obj.modifiers.new("Shrink","SHRINKWRAP"); m_sw.target=obj_base
    m_sw.wrap_method='PROJECT'; m_sw.use_negative_direction=True
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Shrink")
    obj.location[2] = 1.0; bpy.ops.object.transform_apply(location=True)

    tex = bpy.data.textures.new("rd_ext", type='CLOUDS'); tex.noise_scale=0.5
    m_ext = obj.modifiers.new("Ext","DISPLACE"); m_ext.texture=tex; m_ext.strength=0.05; m_ext.mid_level=0
    bpy.ops.object.modifier_apply(modifier="Ext")
    m_b = obj.modifiers.new("B_Disp","DISPLACE"); m_b.strength=0.4; m_b.mid_level=0.0; m_b.vertex_group="B"
    bpy.ops.object.modifier_apply(modifier="B_Disp")
    bpy.data.objects.remove(obj_base, do_unlink=True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    return obj


def build_tube():
    seed_val = np.random.randint(1000)
    angles_threshold = [math.radians(72), math.radians(54), math.radians(45),
                        math.radians(36), math.radians(27), math.radians(18)]
    scales = np.linspace(1.0, 0.9, 6)
    growth_z = np.random.uniform(0, 1.0)
    face_perturb = 0.4
    short_len_range = (0.2, 0.4); long_len_range = (0.4, 1.2)
    growth_prob = 0.75; ico_perturb = 0.2

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
    obj = bpy.context.active_object

    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    rng = np.random.default_rng(seed_val)
    for v in bm.verts:
        delta = (rng.random(3) * 2 - 1) * ico_perturb * 0.1
        v.co.x += float(delta[0]); v.co.y += float(delta[1]); v.co.z += float(delta[2])

    cos_thresh = math.cos(angles_threshold[0])
    selected_faces = [f for f in bm.faces if f.normal.length_squared > 0
                      and f.normal[2] > cos_thresh and rng.random() < growth_prob]
    top_faces = selected_faces[:]

    for i, (angle_thresh, sc) in enumerate(zip(angles_threshold, scales)):
        if not top_faces: break
        new_top = []
        for face in top_faces:
            if not face.is_valid: continue
            normal = face.normal.copy()
            gz = rng.uniform(0, growth_z)
            noise_v = (rng.random(3) * 2 - 1) * face_perturb
            direction = np.array([normal[0]+noise_v[0], normal[1]+noise_v[1], normal[2]+gz+noise_v[2]])
            d_len = np.linalg.norm(direction)
            if d_len < 1e-6: continue
            direction /= d_len
            length = rng.uniform(*long_len_range) if normal[2] > math.cos(angle_thresh) else rng.uniform(*short_len_range)
            ret = bmesh.ops.extrude_face_region(bm, geom=[face])
            new_geom = ret['geom']
            new_face = [g for g in new_geom if isinstance(g, bmesh.types.BMFace)]
            new_verts = [g for g in new_geom if isinstance(g, bmesh.types.BMVert)]
            offset = np.array(direction) * length
            for v in new_verts: v.co.x+=float(offset[0]); v.co.y+=float(offset[1]); v.co.z+=float(offset[2])
            if new_face:
                f_new = new_face[0]
                center = np.mean([v.co[:] for v in f_new.verts], axis=0)
                for v in f_new.verts:
                    co = np.array(v.co[:])
                    v.co[:] = center + (co - center) * sc
                new_top.append(f_new)
        top_faces = new_top

    for f in top_faces:
        if f.is_valid: bm.faces.remove(f)
    bm.to_mesh(obj.data); bm.free(); obj.data.update()

    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    def apply_mod(o, t, **kw):
        m = o.modifiers.new(t, t)
        for k, v in kw.items():
            if hasattr(m, k): setattr(m, k, v)
        bpy.ops.object.modifier_apply(modifier=m.name)
    apply_mod(obj,"BEVEL", offset_type='PERCENT', width_pct=10, segments=1)
    apply_mod(obj,"SOLIDIFY", thickness=0.05)
    apply_mod(obj,"SUBSURF", levels=2, render_levels=2)
    tex = bpy.data.textures.new("tube_coral",type='STUCCI'); tex.noise_scale=np.random.uniform(0.1,0.5)
    m_d = obj.modifiers.new("Disp","DISPLACE"); m_d.texture=tex; m_d.strength=0.1; m_d.mid_level=0
    bpy.ops.object.modifier_apply(modifier="Disp")
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    return obj


def build_tree():
    """Tree coral with bush/twig config — matching original TreeBaseCoralFactory."""

    tree_type = np.random.choice(['bush', 'twig'])
    print(f"  Tree variant: {tree_type}")

    n_branch = np.random.randint(6, 8)
    n_major  = np.random.randint(4, 5)
    n_minor  = np.random.randint(4, 5)
    n_detail = np.random.randint(3, 4)
    base_r   = 0.10
    res      = 8

    if tree_type == 'bush':
        span = np.random.uniform(0.4, 0.5)
        major_npts = n_major + 1
        minor_npts = n_minor + 1
        detail_npts = n_detail + 1
        sz_minor_base, sz_minor_mult = 0.03, 1.2
        sz_detail_base, sz_detail_mult = 0.01, 1.5
        spawn_ang_min, spawn_ang_max = np.pi / 12, np.pi / 8
    else:
        span = np.random.uniform(0.7, 0.8)
        major_npts = n_major * 2 + 1
        minor_npts = n_minor * 2 + 1
        detail_npts = n_detail * 2 + 1
        sz_minor_base, sz_minor_mult = 0.03, 2.2
        sz_detail_base, sz_detail_mult = 0.01, 2.5
        spawn_ang_min, spawn_ang_max = np.pi / 8, np.pi / 6

    def _rfn(br, size):
        decay_root = 0.85
        decay_leaf = np.random.uniform(0.4, 0.6)
        n = size * res
        r = br * decay_root ** (np.arange(n) / res)
        r[-res:] *= decay_leaf ** (np.arange(res) / res)
        return r

    all_v = []; all_f = []; off = [0]

    def _add(ctrl_pts, parent_pt, br, n_ring=6):
        full = np.vstack([parent_pt.reshape(1, 3), ctrl_pts])
        smooth = _smooth_interp(full, res)[1:]
        radii = _rfn(br, len(ctrl_pts))[:len(smooth)]
        v, f = _swept_tube_mesh(smooth, radii, n_ring=n_ring)
        all_v.append(v)
        all_f.extend([[fi + off[0] for fi in face] for face in f])
        off[0] += len(v)

    # Trunk — short stub (12-ring for smoother tubes, matching original 32-ring geo_radius)
    trunk = _rand_path(3, [0, 0, 1], std=0.2, momentum=0.7, sz=0.03)
    _add(trunk[1:], trunk[0], base_r, n_ring=12)

    for b_idx in range(n_branch):
        angle = 2 * np.pi * b_idx / n_branch + np.random.uniform(-np.pi / 9, np.pi / 9)
        init_vec = [span * math.cos(angle), span * math.sin(angle),
                    math.sqrt(max(0, 1 - span * span))]
        attach_idx = min(b_idx % 2 + 1, len(trunk) - 1)
        attach_pt = trunk[attach_idx]

        major_sz = np.random.uniform(0.08, 0.10)
        major_ctrl = _rand_path(major_npts, init_vec, std=0.4, momentum=0.4, sz=major_sz,
                                pull_dir=[0, 0, 1], pull_factor=0.003)
        major_ctrl += attach_pt
        _add(major_ctrl[1:], attach_pt, base_r * 0.75, n_ring=12)

        for m_idx in range(n_major):
            if tree_type == 'bush':
                m_ai = min(m_idx + 1, len(major_ctrl) - 1)
            else:
                m_ai = min(2 * m_idx + 1, len(major_ctrl) - 1)
            m_pt = major_ctrl[m_ai]
            m_iv = _get_spawn_direction(major_ctrl, m_ai, spawn_ang_min, spawn_ang_max)

            sz_m = sz_minor_base * (sz_minor_mult * n_minor - m_idx)
            sz_m = max(sz_m, 0.005)
            minor_ctrl = _rand_path(minor_npts, m_iv, std=0.4, momentum=0.4, sz=sz_m,
                                    pull_dir=[0, 0, 1], pull_factor=0.002)
            minor_ctrl += m_pt
            _add(minor_ctrl[1:], m_pt, base_r * 0.45, n_ring=8)

            for d_idx in range(n_minor):
                if tree_type == 'bush':
                    d_ai = min(d_idx + 1, len(minor_ctrl) - 1)
                else:
                    d_ai = min(2 * d_idx + 1, len(minor_ctrl) - 1)
                d_pt = minor_ctrl[d_ai]
                d_iv = _get_spawn_direction(minor_ctrl, d_ai, spawn_ang_min, spawn_ang_max)

                sz_d = sz_detail_base * (sz_detail_mult * n_detail - d_idx)
                sz_d = max(sz_d, 0.003)
                det_ctrl = _rand_path(detail_npts, d_iv, std=0.4, momentum=0.6, sz=sz_d)
                det_ctrl += d_pt
                _add(det_ctrl[1:], d_pt, base_r * 0.3, n_ring=6)

                # Micro-branches on detail twigs
                for t_idx in range(2):
                    t_ai = min(t_idx + 1, len(det_ctrl) - 1)
                    t_pt = det_ctrl[t_ai]
                    t_iv = _get_spawn_direction(det_ctrl, t_ai, np.pi / 6, np.pi / 3)
                    t_ctrl = _rand_path(3, t_iv, std=0.5, momentum=0.3, sz=0.006)
                    t_ctrl += t_pt
                    _add(t_ctrl[1:], t_pt, base_r * 0.15, n_ring=4)

    verts = np.concatenate(all_v, axis=0)
    mesh = bpy.data.meshes.new("CoralFactory_tree")
    mesh.from_pydata(verts.tolist(), [], all_f); mesh.update()
    obj = bpy.data.objects.new("CoralFactory_tree", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.remove_doubles(threshold=0.002)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()
    max_dim = max(obj.dimensions[:2])
    if max_dim > 0: obj.scale = (2 / max_dim,) * 3
    bpy.ops.object.transform_apply(scale=True)
    m_ss = obj.modifiers.new("SS", "SUBSURF"); m_ss.levels = 1; m_ss.render_levels = 1
    bpy.ops.object.modifier_apply(modifier="SS")
    tex = bpy.data.textures.new("tree_d", type='CLOUDS'); tex.noise_scale = 0.05
    m_d = obj.modifiers.new("D", "DISPLACE"); m_d.texture = tex; m_d.strength = 0.01; m_d.mid_level = 0
    bpy.ops.object.modifier_apply(modifier="D")
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    return obj


def build_cauliflower():
    def mesh_grid(n, sizes):
        shapes = [int((h - l) * n) + 1 for l, h in sizes]
        return np.meshgrid(*(np.linspace(*sz, sh) for sz, sh in zip(sizes, shapes)))

    def init_mesh_3d(n, sizes):
        x, y, z = mesh_grid(n, sizes)
        f = (np.random.uniform(0.5,1)*(x-np.random.uniform(-0.2,0.2))**2
             + np.random.uniform(0.5,1)*(y-np.random.uniform(-0.2,0.2))**2
             + np.random.uniform(0.1,0.2)*z**2 < 0.2*0.2)
        def extend(f_): return np.random.random(f_.shape) < ndimage_convolve(f_.astype(float), np.ones((3,3,3)))
        a = np.where(f, np.random.uniform(0.1,0.5,x.shape), 0) + np.random.random(x.shape)*0.02
        b = np.where(extend(f), 1.0, np.random.uniform(-1,1,x.shape)).astype(float)
        return a, b

    def build_laplacian(st, a, b, t, k, dt, tau, eps, alpha, gamma, teq):
        for _ in range(t):
            lap_a = ndimage_convolve(a, st); lap_b = ndimage_convolve(b, st)
            m = alpha / np.pi * np.arctan(gamma * (teq - b))
            da = (eps*eps*lap_a + a*(1.0-a)*(a-0.5+m)) / tau
            db = lap_b + k * da
            a += da * dt; b += db * dt
        return a, b

    n = 32; t_steps = 800
    k=2.0; dt=0.0005; tau=0.0003; eps=0.01; alpha=0.9; gamma=10.0; teq=1.0
    stencil = np.array([[[1,3,1],[3,14,3],[1,3,1]],[[3,14,3],[14,-128,14],[3,14,3]],[[1,3,1],[3,14,3],[1,3,1]]]) / 128.0
    height = 1.5; sizes = ([-1,1],[-1,1],[0,height])
    print(f"  Laplacian growth ({n}^3 grid, {t_steps} iterations) …")
    a_arr, b_arr = init_mesh_3d(n, sizes)
    a_arr, b_arr = build_laplacian(stencil*n*n, a_arr, b_arr, t_steps, k, dt, tau, eps, alpha, gamma, teq)
    a_pad = np.pad(a_arr, 1)

    # Use skimage marching_cubes (much cleaner mesh than hand-written version)
    mc_verts, mc_faces, _, _ = marching_cubes(a_pad, level=0.5)
    mc_verts -= 1; mc_verts /= n; mc_verts[:,:2] -= 1
    x, y, z = mc_verts.T
    scale_arr = (np.maximum(np.abs(x),np.abs(y))/(np.sqrt(x**2+y**2)+1e-6)*(1-z/height)+z/height)
    mc_verts[:,:2] *= scale_arr[:,np.newaxis]

    mesh = bpy.data.meshes.new("CoralFactory_caul")
    mesh.from_pydata(mc_verts.tolist(), [], mc_faces.tolist()); mesh.update()
    obj = bpy.data.objects.new("CoralFactory_caul", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()
    tex = bpy.data.textures.new("caul_ext",type='CLOUDS'); tex.noise_scale=0.5
    m_d = obj.modifiers.new("Ext","DISPLACE"); m_d.texture=tex; m_d.strength=0.03; m_d.mid_level=0
    bpy.ops.object.modifier_apply(modifier="Ext")
    m_s = obj.modifiers.new("Sub","SUBSURF"); m_s.levels=1; m_s.render_levels=1
    bpy.ops.object.modifier_apply(modifier="Sub")
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    return obj


def build_elkhorn():
    large_radius = np.random.uniform(0.08, 0.12)

    def make_circular_interp(lo, hi, n):
        angles_ctrl = np.sort(np.random.uniform(0, 2*np.pi, n))
        vals_ctrl   = np.random.uniform(lo, hi, n)
        a_ext = np.concatenate([angles_ctrl-2*np.pi, angles_ctrl, angles_ctrl+2*np.pi])
        v_ext = np.tile(vals_ctrl, 3)
        def fn(a): return np.interp(a % (2*np.pi), a_ext, v_ext)
        return fn

    f_scale = make_circular_interp(0.3, 1.0, 5)
    f_rotation = make_circular_interp(0, np.pi/3, 10)
    f_power = make_circular_interp(1.0, 1.6, 5)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_circle_add(vertices=256, radius=1.0, fill_type='NGON')
    obj = bpy.context.active_object
    bpy.context.view_layer.objects.active = obj

    bm_init = bmesh.new(); bm_init.from_mesh(obj.data)
    bmesh.ops.triangulate(bm_init, faces=bm_init.faces[:])
    bmesh.ops.subdivide_edges(bm_init, edges=bm_init.edges[:], cuts=3, use_grid_fill=True)
    bm_init.to_mesh(obj.data); bm_init.free(); obj.data.update()

    bm = bmesh.new(); bm.from_mesh(obj.data)
    for v in bm.verts:
        v.co.x += np.random.uniform(-0.005, 0.005)
        v.co.y += np.random.uniform(-0.005, 0.005)
    bm.to_mesh(obj.data); bm.free()

    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    to_remove = []
    for v in bm.verts:
        x, y, _ = v.co; r = math.sqrt(x*x+y*y)
        thresh = 0.015 + large_radius * (1-r)
        if np.random.random() > min(1.0, thresh*20): to_remove.append(v)
    bmesh.ops.delete(bm, geom=to_remove, context='VERTS')
    bm.to_mesh(obj.data); bm.free()

    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    angle_radius = 0.2; angles_arr = np.full(len(bm.verts), -100.0)
    queue = set()
    for v in bm.verts:
        x, y, z = v.co
        if math.sqrt(x*x+y*y) <= angle_radius:
            angles_arr[v.index] = math.atan2(y, x)
            for e in v.link_edges: queue.add(e.other_vert(v))
    while queue:
        new_queue = set()
        for v in queue:
            if angles_arr[v.index] <= -100.0:
                pairs = [(e.calc_length(), angles_arr[e.other_vert(v).index])
                         for e in v.link_edges if angles_arr[e.other_vert(v).index] > -100.0]
                if pairs: angles_arr[v.index] = min(pairs)[1]
            for e in v.link_edges:
                o = e.other_vert(v)
                if angles_arr[o.index] <= -100.0: new_queue.add(o)
        queue = new_queue
    for v in bm.verts:
        if angles_arr[v.index] <= -100.0:
            x, y, _ = v.co; angles_arr[v.index] = math.atan2(y, x)

    for v in bm.verts:
        x, y, z = v.co; a = angles_arr[v.index] + np.pi
        v.co.z += f_scale(a) * (x*x+y*y)**f_power(a)
        rotation = f_rotation(a); c, s = math.cos(rotation), math.sin(rotation)
        nx = c*x-s*z; nz = c*z+s*math.sqrt(x*x+y*y); ny = c*y-s*z
        v.co.x, v.co.y, v.co.z = nx, ny, nz

    long_edges = [e for e in bm.edges if e.calc_length() > 0.04]
    bmesh.ops.delete(bm, geom=long_edges, context='EDGES')
    bm.to_mesh(obj.data); bm.free(); obj.data.update()

    obj.rotation_euler[2] = np.random.uniform(0, 2*np.pi)
    bpy.ops.object.transform_apply(rotation=True)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)

    m_sol = obj.modifiers.new("Solid","SOLIDIFY"); m_sol.thickness=0.02
    bpy.ops.object.modifier_apply(modifier="Solid")
    tex_ext = bpy.data.textures.new("elk_ext",type='CLOUDS'); tex_ext.noise_scale=0.5
    m_ext = obj.modifiers.new("Ext","DISPLACE"); m_ext.texture=tex_ext; m_ext.strength=0.005; m_ext.mid_level=0
    bpy.ops.object.modifier_apply(modifier="Ext")
    tex_s = bpy.data.textures.new("elk_stucci",type='STUCCI'); tex_s.noise_scale=np.random.uniform(0.1,0.5)
    m_z = obj.modifiers.new("Z_Disp","DISPLACE"); m_z.texture=tex_s; m_z.strength=np.random.uniform(0.1,0.2); m_z.mid_level=0; m_z.direction='Z'
    bpy.ops.object.modifier_apply(modifier="Z_Disp")
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    min_z = min(v.co.z for v in obj.data.vertices); obj.location[2] -= min_z; bpy.ops.object.transform_apply(location=True)
    return obj


def build_star():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0)
    obj = bpy.context.active_object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    for v in bm.verts: x,y,z = v.co; v.co.z = z - 0.9*min(z,0)
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    obj.location[2] = np.random.uniform(0.25, 0.5); bpy.ops.object.transform_apply(location=True)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    m_s = obj.modifiers.new("Sub","SUBSURF"); m_s.levels=3; m_s.render_levels=3
    bpy.ops.object.modifier_apply(modifier="Sub")
    tex_vor = bpy.data.textures.new("star_cells",type='VORONOI')
    tex_vor.noise_scale=np.random.uniform(0.15,0.25); tex_vor.noise_intensity=np.random.uniform(1.5,2.5)
    tex_vor.distance_metric='MINKOVSKY'; tex_vor.minkovsky_exponent=np.random.uniform(1.0,1.5)
    m_vor = obj.modifiers.new("PolyPattern","DISPLACE"); m_vor.texture=tex_vor; m_vor.strength=-np.random.uniform(0.04,0.10); m_vor.mid_level=1.0
    bpy.ops.object.modifier_apply(modifier="PolyPattern")
    tex_ext = bpy.data.textures.new("star_ext",type='CLOUDS'); tex_ext.noise_scale=0.5
    m_ext = obj.modifiers.new("Ext","DISPLACE"); m_ext.texture=tex_ext; m_ext.strength=0.002; m_ext.mid_level=0
    bpy.ops.object.modifier_apply(modifier="Ext")
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    return obj


# ── Build chosen base ─────────────────────────────────────────────────────────
builders = {
    "diff_growth":        build_diff_growth,
    "reaction_diffusion": build_reaction_diffusion,
    "tube":               build_tube,
    "tree":               build_tree,
    "cauliflower":        build_cauliflower,
    "elkhorn":            build_elkhorn,
    "star":               build_star,
}

obj = builders[chosen_base]()

# ── coral_postprocess ────────────────────────────────────────────────────────
dims = [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z]
max_xy = max(dims[0], dims[1], 1e-6)
scale = 2.0 * np.array(default_scale) / max_xy * np.random.uniform(0.8, 1.2, 3)
obj.scale = tuple(scale)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(scale=True)

# Step 1: Remesh (voxel) — fuses overlapping branches into smooth blobs
m_rem = obj.modifiers.new("Remesh", "REMESH")
m_rem.mode = "VOXEL"
m_rem.voxel_size = 0.01
bpy.ops.object.modifier_apply(modifier="Remesh")

# Step 2: Smooth shading on body (critical for rounded appearance)
bpy.ops.object.shade_smooth()

# Step 4: Displacement for organic surface bumps
# For tree coral: force VORONOI bump to create nodular surface + tentacles
if noise_strength > 0:
    if chosen_base == 'tree':
        # Tree coral with tentacles: always use VORONOI bump (matching reference)
        has_bump = False
    else:
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
        # Larger noise_scale = bigger bumps (each bump spans more vertices → rounder)
        if chosen_base == 'tree':
            tex.noise_scale = math.exp(np.random.uniform(math.log(0.03), math.log(0.05)))
        else:
            tex.noise_scale = math.exp(np.random.uniform(math.log(0.02), math.log(0.03)))
        tex.noise_intensity = math.exp(np.random.uniform(math.log(1.5), math.log(2.0)))
        tex.distance_metric = 'MINKOVSKY'
        tex.minkovsky_exponent = np.random.uniform(1, 1.5)
        m_d = obj.modifiers.new("Bump", "DISPLACE")
        m_d.texture = tex
        m_d.strength = -noise_strength * np.random.uniform(1, 2)
        m_d.mid_level = 1
    bpy.ops.object.modifier_apply(modifier=m_d.name)
    # Smooth pass to round out displacement bumps into organic nodules
    m_sm2 = obj.modifiers.new("PostSmooth", "SMOOTH")
    m_sm2.iterations = 2
    bpy.ops.object.modifier_apply(modifier="PostSmooth")

# Tentacles only when NOT has_bump (VORONOI path) — original condition
# Tentacles are NOT remeshed — they stay as smooth curve-based tubes
if chosen_base == 'tree' and not has_bump:
    print("  Adding curve-based tentacle geometry...")
    _distribute_tentacles(obj, n_variants=5, density=500)

obj.name = "CoralFactory"
print(f"Done: CoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
