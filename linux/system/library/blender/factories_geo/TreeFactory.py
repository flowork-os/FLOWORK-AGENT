# [FL_INDEX: keywords="blender_factory, procedural_3d, TreeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TreeFactory | Category: factories_geo
# Prompt: A 3D model of a broadleaf tree rendered from a top-down perspective. The tree features a short, thick brown trunk that splits into multiple gnarled branches supporting a broad, irregular canopy of small green leaves with scattered pink flower-like clusters.

import colorsys
import math
import os
import random
import sys
import warnings

import bmesh
import bpy
import numpy as np

SEED = int(os.environ.get("SEED", "0"))
random.seed(SEED)
np.random.seed(SEED)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    bpy.context.scene.cursor.location = (0, 0, 0)

# ── Space colonization tree skeleton ─────────────────────────────────────────
class TreeVertices:
    def __init__(self, vtxs=None, parent=None, level=None):
        if vtxs is None:
            vtxs = np.array([[0, 0, 0]], dtype=float)
        elif isinstance(vtxs, list):
            vtxs = np.array(vtxs, dtype=float)
        parent = [-1] * len(vtxs) if parent is None else parent
        level = [0] * len(vtxs) if level is None else level
        self.vtxs = vtxs
        self.parent = parent
        self.level = level

    def get_idxs(self):
        return list(np.arange(len(self.vtxs)))

    def get_edges(self):
        edges = np.stack([np.arange(len(self.vtxs)), np.array(self.parent)], 1)
        return edges[edges[:, 1] != -1]

    def append(self, v, p, l=None):
        self.vtxs = np.append(self.vtxs, v, axis=0)
        self.parent += p
        if l is None:
            l = [0] * len(v)
        elif isinstance(l, int):
            l = [l] * len(v)
        self.level += l

    def __len__(self):
        return len(self.vtxs)

def rodrigues_rot(v, k, theta):
    """Rotate vector v around axis k by angle theta (Rodrigues formula)."""

    k = np.array(k, dtype=float)
    v = np.array(v, dtype=float)
    k_norm = np.linalg.norm(k)
    if k_norm < 1e-10:
        return v
    k = k / k_norm
    return v * math.cos(theta) + np.cross(k, v) * math.sin(theta) + k * np.dot(k, v) * (1 - math.cos(theta))

def rotation_between_vectors(a, b):
    """Rotation matrix that rotates unit vector a to unit vector b."""

    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    a /= max(np.linalg.norm(a), 1e-10)
    b /= max(np.linalg.norm(b), 1e-10)
    v = np.cross(a, b)
    c = np.dot(a, b)
    if np.linalg.norm(v) < 1e-10:
        if c > 0:
            return np.eye(3)
        perp = np.array([1, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1, 0])
        perp = perp - a * np.dot(a, perp)
        perp /= np.linalg.norm(perp)
        return 2 * np.outer(perp, perp) - np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)

def axis_angle_matrix(axis, angle):
    """Rotation matrix around axis by angle (radians)."""

    axis = np.array(axis, dtype=float)
    an = np.linalg.norm(axis)
    if an < 1e-10:
        return np.eye(3)
    axis /= an
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(angle) * K + (1 - math.cos(angle)) * K @ K

def rand_path(n_pts, sz=1, std=0.3, momentum=0.5, init_vec=None, init_pt=None,
              pull_dir=None, pull_init=1, pull_factor=0, sz_decay=1, decay_mom=True):
    if init_vec is None:
        init_vec = [0, 0, 1]
    if init_pt is None:
        init_pt = [0, 0, 0]
    init_vec = np.array(init_vec, dtype=float)
    init_pt = np.array(init_pt, dtype=float)

    if pull_dir is not None:
        pull_dir = np.array(pull_dir, dtype=float)
        init_vec = init_vec + pull_init * pull_dir

    norm = np.linalg.norm(init_vec)
    if norm > 1e-10:
        init_vec = init_vec / norm

    path = np.zeros((n_pts, 3))
    path[0] = init_pt
    for i in range(1, n_pts):
        if i == 1:
            prev_delta = init_vec * sz
        else:
            prev_delta = path[i - 1] - path[i - 2]

        prev_sz = np.linalg.norm(prev_delta)
        new_delta = prev_delta + np.random.randn(3) * std
        if pull_dir is not None:
            new_delta = new_delta + pull_factor * pull_dir
        nd_norm = np.linalg.norm(new_delta)
        if nd_norm > 1e-10:
            new_delta = (new_delta / nd_norm) * prev_sz

        if decay_mom:
            tmp_momentum = 1 - (1 - momentum) * (i + 1) / n_pts
        else:
            tmp_momentum = momentum
        delta = prev_delta * tmp_momentum + new_delta * (1 - tmp_momentum)
        d_norm = np.linalg.norm(delta)
        if d_norm > 1e-10:
            delta = (delta / d_norm) * sz * (sz_decay ** i)
        path[i] = path[i - 1] + delta

    return path

def get_spawn_pt(path, rng=None, ang_min=math.pi / 6, ang_max=0.9 * math.pi / 2,
                 rnd_idx=None, ang_sign=None, axis2=None, init_vec=None, z_bias=0):
    if rng is None:
        rng = [0.5, 1]
    n = len(path)
    if n == 1:
        return 0, path[0], init_vec if init_vec is not None else np.array([0, 0, 1])

    if rnd_idx is None:
        rnd_idx = np.random.randint(int(n * rng[0]), max(int(n * rng[1]), int(n * rng[0]) + 1))
    rnd_idx = max(1, min(rnd_idx, n - 1))

    if init_vec is None:
        curr_vec = path[rnd_idx] - path[rnd_idx - 1]
        axis1 = np.array([curr_vec[1], -curr_vec[0], 0])
        if axis2 is None:
            axis2 = rodrigues_rot(curr_vec, axis1, math.pi / 2)
        if callable(axis2):
            axis2 = axis2()
        rnd_ang = np.random.rand() * (ang_max - ang_min) + ang_min
        if ang_sign is None:
            ang_sign = np.sign(np.random.randn())
        rnd_ang *= ang_sign
        init_vec = rodrigues_rot(curr_vec, axis2, rnd_ang)

    return rnd_idx, path[rnd_idx], init_vec

def recursive_path(tree, parent_idxs, level, path_kargs=None, spawn_kargs=None,
                   n=1, symmetry=False, children=None):
    if path_kargs is None:
        return

    if symmetry:
        n = 2 * n

    for branch_idx in range(n):
        curr_idx = branch_idx // 2 if symmetry else branch_idx
        curr_path = path_kargs(curr_idx)
        curr_spawn = spawn_kargs(curr_idx)
        if symmetry:
            curr_spawn["ang_sign"] = 2 * (branch_idx % 2) - 1

        parent_idx, init_pt, init_vec = get_spawn_pt(
            tree.vtxs[parent_idxs], **curr_spawn
        )
        parent_idx = parent_idxs[parent_idx]

        path = rand_path(**curr_path, init_pt=init_pt, init_vec=init_vec)
        new_vtxs = path[1:]
        new_idxs = list(np.arange(len(new_vtxs)) + len(tree))
        node_idxs = [parent_idx] + new_idxs
        tree.append(new_vtxs, node_idxs[:-1], level)

        if children is not None:
            for c in children:
                recursive_path(tree, node_idxs, level + 1, **c)

def compute_dists(atts, vtxs):
    """Compute distances between attractor points and tree vertices."""
    # atts: (N, 3), vtxs: (M, 3)
    diff = atts[:, None, :] - vtxs[None, :, :]  # (N, M, 3)
    dists = np.linalg.norm(diff, axis=2)  # (N, M)
    return dists, diff

def space_colonization(tree, atts, D=0.1, d=10.0, s=0.1, pull_dir=None,
                       dir_rand=0.1, mag_rand=0.15, n_steps=200, level=0):
    if callable(atts):
        atts = atts(tree.vtxs)

    curr_min = np.zeros(len(atts)) + d
    curr_match = -np.ones(len(atts), dtype=int)

    # Initial removal
    dists, deltas = compute_dists(atts, tree.vtxs)
    min_dist = dists.min(1)
    closest = dists.argmin(1)
    to_keep = min_dist > s

    atts = atts[to_keep]
    deltas = deltas[to_keep]
    curr_min = curr_min[to_keep]
    curr_match = curr_match[to_keep]
    min_dist = min_dist[to_keep]
    closest = closest[to_keep]

    to_update = min_dist < curr_min
    curr_min[to_update] = min_dist[to_update]
    curr_match[to_update] = closest[to_update]

    if np.all(curr_match == -1):
        warnings.warn("Space colonization: all curr_match == -1")
        return

    for step in range(n_steps):
        new_vtxs = []
        new_parents = []
        matched_vtxs = np.unique(curr_match)

        for n_idx in matched_vtxs:
            if n_idx == -1:
                continue
            matched_deltas = deltas[curr_match == n_idx]
            # Normalize each delta and average
            norms = np.linalg.norm(matched_deltas[:, n_idx, :], axis=1, keepdims=True)
            norms = np.maximum(norms, 1e-10)
            new_dir = (matched_deltas[:, n_idx, :] / norms).mean(0)
            nd_norm = np.linalg.norm(new_dir)
            if nd_norm > 1e-10:
                new_dir = new_dir / nd_norm

            if pull_dir is not None:
                new_dir = new_dir + np.array(pull_dir)
                nd_norm = np.linalg.norm(new_dir)
                if nd_norm > 1e-10:
                    new_dir = new_dir / nd_norm

            new_dir = new_dir + np.random.randn(3) * dir_rand
            tmp_D = D * np.exp(np.random.randn() * mag_rand)

            n0 = tree.vtxs[n_idx]
            n1 = n0 + tmp_D * new_dir
            new_vtxs.append(n1)
            new_parents.append(n_idx)

        if not new_vtxs:
            break

        idx_offset = len(tree)
        new_vtxs = np.stack(new_vtxs, 0)
        tree.append(new_vtxs, new_parents, level)

        # Removal step
        dists_new, deltas_new = compute_dists(atts, new_vtxs)
        # Append new deltas
        deltas = np.concatenate([deltas, deltas_new], axis=1)

        min_dist_new = dists_new.min(1)
        closest_new = dists_new.argmin(1) + idx_offset

        to_keep = min_dist_new > s
        atts = atts[to_keep]
        deltas = deltas[to_keep]
        curr_min = curr_min[to_keep]
        curr_match = curr_match[to_keep]
        min_dist_new = min_dist_new[to_keep]
        closest_new = closest_new[to_keep]

        to_update = min_dist_new < curr_min
        curr_min[to_update] = min_dist_new[to_update]
        curr_match[to_update] = closest_new[to_update]

        if len(atts) == 0:
            break

def dfs_tree(idx, edge_ref, parents, depth, rev_depth, n_leaves, child_idx):
    """DFS to compute tree attributes."""

    children = [v for v in edge_ref[idx] if v != parents[idx]]
    if len(children) == 0:
        curr_idx = idx
        child_idx[curr_idx] = -1
        curr_depth = 0
        while curr_idx != 0:
            prev_idx = curr_idx
            curr_idx = parents[curr_idx]
            curr_depth += 1
            n_leaves[curr_idx] += 1
            if rev_depth[curr_idx] < curr_depth:
                child_idx[curr_idx] = prev_idx
                rev_depth[curr_idx] = curr_depth
    else:
        for c in children:
            parents[c] = idx
            depth[c] = depth[idx] + 1
            dfs_tree(c, edge_ref, parents, depth, rev_depth, n_leaves, child_idx)

def parse_tree_attributes(vtx):
    """Compute rev_depth and split multi-child branching nodes by duplicating
    """

    sys.setrecursionlimit(20000)
    n = len(vtx.vtxs)
    parents = np.zeros(n, dtype=int)
    depth = np.zeros(n, dtype=int)
    rev_depth = np.zeros(n, dtype=int)
    n_leaves = np.zeros(n, dtype=int)
    child_idx_arr = np.zeros(n, dtype=int)

    edge_ref = {i: [] for i in range(n)}
    for e in vtx.get_edges():
        v0, v1 = e
        edge_ref[int(v0)].append(int(v1))
        edge_ref[int(v1)].append(int(v0))

    dfs_tree(0, edge_ref, parents, depth, rev_depth, n_leaves, child_idx_arr)

    # Multi-child split: keep deepest child connected; reroute siblings through
    # duplicate parents at the same position. Final MergeByDistance stitches them.
    new_p_id = n
    vtx_pos = vtx.vtxs.copy()
    levels = list(vtx.level)
    for idx in range(n):
        children = np.array([v for v in edge_ref[idx] if v != parents[idx]], dtype=int)
        if len(children) >= 2:
            child_depths = rev_depth[children]
            deepest = children[child_depths.argmax()]
            others = np.setdiff1d(children, np.array([deepest]))
            for c in others:
                c = int(c)
                rev_depth = np.append(rev_depth, rev_depth[c] + 1)
                edge_ref[new_p_id] = [c]
                edge_ref[c].remove(idx)
                edge_ref[idx].remove(c)
                vtx.append(vtx_pos[idx:idx + 1].reshape(1, 3), [-1], [levels[idx]])
                vtx.parent[c] = new_p_id
                new_p_id += 1
    return rev_depth

def get_pts_from_shape_simple(n, scaling, pt_offset):
    """Sample random points inside a box (replaces mesh.get_pts_from_shape)."""

    scaling = np.array(scaling)
    pts = (np.random.rand(n, 3) - 0.5) * 2 * scaling + np.array(pt_offset)
    return pts

# ── Skeleton -> Mesh via GeoNodes ─────────────────────────────────────────────
def skeleton_to_mesh(vtx, rev_depth, scale=0.35,
                     min_radius=0.02, max_radius=0.2, exponent=1.5,
                     profile_res=20, scaling=None, wobble=False,
                     subdivide=False, selection_min_level=None,
                     noise_detail=2.0, noise_distortion=0.0):
    """Skeleton -> tube mesh via GeoNodes, aligned to objects_blender TreeFactory."""

    verts = vtx.vtxs * scale
    edges = vtx.get_edges()

    mesh_data = bpy.data.meshes.new("TreeSkeleton")
    mesh_data.from_pydata(verts.tolist(), edges.tolist(), [])
    mesh_data.update()

    obj = bpy.data.objects.new("TreeSkeleton", mesh_data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    # Both raw INT and FLOAT copies; FLOAT lets the math chain consume rev_depth directly.
    attr = mesh_data.attributes.new(name="rev_depth", type="INT", domain="POINT")
    attr.data.foreach_set("value", rev_depth.astype(int))
    attr_f = mesh_data.attributes.new(name="rev_depth_f", type="FLOAT", domain="POINT")
    attr_f.data.foreach_set("value", rev_depth.astype(float))
    max_rd = int(rev_depth.max()) if rev_depth.max() > 0 else 1
    attr_n = mesh_data.attributes.new(name="rev_depth_norm", type="FLOAT", domain="POINT")
    attr_n.data.foreach_set("value", rev_depth.astype(float) / max_rd)

    if selection_min_level is not None and len(vtx.level) == len(verts):
        levels_arr = np.array(vtx.level, dtype=int)
        sel = (levels_arr >= selection_min_level).astype(np.int8)
        attr_sel = mesh_data.attributes.new(name="curve_sel", type="BOOLEAN", domain="POINT")
        attr_sel.data.foreach_set("value", sel)

    ng = bpy.data.node_groups.new("SetTreeRadius_Standalone", 'GeometryNodeTree')
    in_sock = ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.move(in_sock, 0)
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    gi = nodes.new('NodeGroupInput')
    gi.location = (-1200, 0)
    go = nodes.new('NodeGroupOutput')
    go.location = (1000, 0)

    m2c = nodes.new('GeometryNodeMeshToCurve')
    m2c.location = (-1000, 0)
    links.new(gi.outputs['Geometry'], m2c.inputs['Mesh'])

    if selection_min_level is not None:
        sel_attr = nodes.new('GeometryNodeInputNamedAttribute')
        sel_attr.data_type = 'BOOLEAN'
        sel_attr.inputs['Name'].default_value = "curve_sel"
        sel_attr.location = (-1200, 200)
        links.new(sel_attr.outputs[0], m2c.inputs['Selection'])
    curve_out = m2c.outputs['Curve']

    if wobble:
        sst = nodes.new('GeometryNodeCurveSplineType')
        sst.spline_type = 'BEZIER'
        sst.location = (-820, 0)
        links.new(curve_out, sst.inputs['Curve'])

        sht = nodes.new('GeometryNodeCurveSetHandles')
        sht.location = (-640, 0)
        links.new(sst.outputs['Curve'], sht.inputs['Curve'])

        ipos = nodes.new('GeometryNodeInputPosition')
        ipos.location = (-820, 220)

        tnoise = nodes.new('ShaderNodeTexNoise')
        tnoise.location = (-640, 220)
        tnoise.inputs['Scale'].default_value = 1.0
        tnoise.inputs['Detail'].default_value = noise_detail
        if 'Distortion' in tnoise.inputs:
            tnoise.inputs['Distortion'].default_value = noise_distortion
        links.new(ipos.outputs['Position'], tnoise.inputs['Vector'])

        vsc = nodes.new('ShaderNodeVectorMath')
        vsc.operation = 'SCALE'
        vsc.location = (-460, 220)
        links.new(tnoise.outputs[1], vsc.inputs[0])
        vsc.inputs['Scale'].default_value = 0.02

        shp = nodes.new('GeometryNodeSetCurveHandlePositions')
        shp.location = (-280, 0)
        links.new(sht.outputs['Curve'], shp.inputs['Curve'])
        links.new(vsc.outputs[0], shp.inputs['Offset'])
        curve_out = shp.outputs['Curve']

    named_attr = nodes.new('GeometryNodeInputNamedAttribute')
    named_attr.location = (-1000, -260)
    named_attr.data_type = 'FLOAT'

    if scaling is not None:
        named_attr.inputs['Name'].default_value = "rev_depth_f"
        m1 = nodes.new('ShaderNodeMath')
        m1.operation = 'MULTIPLY'
        m1.location = (-820, -260)
        links.new(named_attr.outputs[0], m1.inputs[0])
        m1.inputs[1].default_value = scaling * 0.1

        pw = nodes.new('ShaderNodeMath')
        pw.operation = 'POWER'
        pw.location = (-640, -260)
        links.new(m1.outputs[0], pw.inputs[0])
        pw.inputs[1].default_value = exponent

        mx = nodes.new('ShaderNodeMath')
        mx.operation = 'MAXIMUM'
        mx.location = (-460, -260)
        links.new(pw.outputs[0], mx.inputs[0])
        mx.inputs[1].default_value = min_radius

        mn = nodes.new('ShaderNodeMath')
        mn.operation = 'MINIMUM'
        mn.location = (-280, -260)
        links.new(mx.outputs[0], mn.inputs[0])
        mn.inputs[1].default_value = max_radius
        radius_out = mn.outputs[0]
    else:
        named_attr.inputs['Name'].default_value = "rev_depth_norm"
        pw = nodes.new('ShaderNodeMath')
        pw.operation = 'POWER'
        pw.location = (-820, -260)
        links.new(named_attr.outputs[0], pw.inputs[0])
        pw.inputs[1].default_value = exponent

        ml = nodes.new('ShaderNodeMath')
        ml.operation = 'MULTIPLY'
        ml.location = (-640, -260)
        links.new(pw.outputs[0], ml.inputs[0])
        ml.inputs[1].default_value = max_radius - min_radius

        ad = nodes.new('ShaderNodeMath')
        ad.operation = 'ADD'
        ad.location = (-460, -260)
        links.new(ml.outputs[0], ad.inputs[0])
        ad.inputs[1].default_value = min_radius
        radius_out = ad.outputs[0]

    scr = nodes.new('GeometryNodeSetCurveRadius')
    scr.location = (0, 0)
    links.new(curve_out, scr.inputs['Curve'])
    links.new(radius_out, scr.inputs['Radius'])

    cc = nodes.new('GeometryNodeCurvePrimitiveCircle')
    cc.location = (0, -460)
    cc.inputs['Resolution'].default_value = profile_res
    cc.inputs['Radius'].default_value = 1.0

    c2m = nodes.new('GeometryNodeCurveToMesh')
    c2m.location = (260, 0)
    links.new(scr.outputs['Curve'], c2m.inputs['Curve'])
    links.new(cc.outputs['Curve'], c2m.inputs['Profile Curve'])
    links.new(radius_out, c2m.inputs['Scale'])
    c2m.inputs['Fill Caps'].default_value = True

    mbd = nodes.new('GeometryNodeMergeByDistance')
    mbd.location = (520, 0)
    links.new(c2m.outputs['Mesh'], mbd.inputs['Geometry'])
    mbd.inputs['Distance'].default_value = 0.001

    links.new(mbd.outputs['Geometry'], go.inputs['Geometry'])

    mod = obj.modifiers.new("TreeRadius", 'NODES')
    mod.node_group = ng
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    if subdivide:
        sub = obj.modifiers.new("Sub", 'SUBSURF')
        sub.levels = 1
        sub.render_levels = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=sub.name)

    return obj

# ── Tree generation configs ──────────────────────────────────────────────────
def calc_height(x, min_ht=12, max_ht=30, bias=-0.05, uniform_factor=0.5):
    def map_fn(val):
        return np.tan((val - 0.5 + bias) * np.pi * (1.1 - uniform_factor))
    lo, hi = map_fn(0), map_fn(1)
    y = (map_fn(x) - lo) / (hi - lo)
    return y * (max_ht - min_ht) + min_ht


def generate_tree_config():
    """multi_branch, optional whorled (radial_out) layout, sparse space colonization."""

    g_size = np.random.rand()
    g_trunk_warp = np.random.rand()
    g_n_trunks = np.random.rand()
    g_multi_branch = np.random.rand()
    g_branch_thickness = np.random.rand()

    sz = calc_height(g_size, min_ht=12)
    n_tree_pts = int(sz)

    n_trunks = max(1, int(10 ** (g_n_trunks ** 1.6)))
    ex = np.exp((6 - (5 if n_trunks > 1 else 0)) * (g_trunk_warp - 0.1))
    trunk_std = ((1 - (ex / (1 + ex))) * 4) ** 2
    trunk_mtm = max(0.2, min(0.95, (1 / (trunk_std + 1)) + np.random.randn() * 0.2))

    radial_out = np.random.rand() < 0.15  # whorled / pine-style layered branching

    avail_idxs = np.arange(n_tree_pts)
    start_idx = 1 + int(n_tree_pts * np.random.uniform(0.1, 0.7))
    sample_density = int(np.random.choice(
        np.arange(1, int(np.ceil(np.sqrt(n_tree_pts))) + 1)
    ))
    avail_idxs = avail_idxs[start_idx::sample_density]
    multi_branch = max(1, int(5 ** (g_multi_branch ** 1.6)))
    avail_idxs = np.repeat(avail_idxs, multi_branch).flatten()
    n = max(1, len(avail_idxs))

    start_ht = sz * (start_idx / sz)
    box_ht = max(0.5, (sz - start_ht) * 0.6)
    max_sz = 1.0

    if radial_out:
        per_layer = np.random.randint(3, 6)

        def _branch_path(idx, _n=n, _pl=per_layer, _max=max_sz, _sz=sz):
            band = max(1, _n - idx // _pl)
            lo = max(1, int(np.floor((band / max(_n, 1)) * 6)))
            hi = max(lo + 1, int(np.ceil((band / max(_n, 1)) * 8)))
            return {
                "n_pts": np.random.randint(lo, hi) + 3,
                "std": 0.3,
                "momentum": 0.9,
                "sz": _max - (_max / _sz) * (idx // _pl),
                "pull_dir": [0, 0, np.random.rand()],
                "pull_factor": np.random.rand(),
            }

        def _branch_spawn(idx, _ai=avail_idxs, _pl=per_layer):
            return {
                "rnd_idx": int(_ai[min(idx // _pl, len(_ai) - 1)]),
                "ang_min": math.pi / 2,
                "ang_max": math.pi / 2 + math.pi / 16,
                "axis2": [np.random.randn(), np.random.randn(), 0.5],
            }

        branch_config = {
            "n": n * per_layer,
            "path_kargs": _branch_path,
            "spawn_kargs": _branch_spawn,
        }
    else:
        branch_config = {
            "n": n,
            "path_kargs": lambda idx, _n=n_tree_pts: {
                "n_pts": int(_n * np.random.uniform(0.4, 0.6)),
                "sz": 1,
                "std": 1.4,
                "momentum": 0.4,
                "pull_dir": [0, 0, np.random.rand()],
                "pull_factor": np.random.rand(),
            },
            "spawn_kargs": lambda idx, _ai=avail_idxs: {
                "rnd_idx": int(_ai[min(idx, len(_ai) - 1)])
            },
        }

    tree_config = {
        "n": n_trunks,
        "path_kargs": lambda idx, _n=n_tree_pts, _std=trunk_std, _mtm=trunk_mtm: {
            "n_pts": _n,
            "sz": 1,
            "std": _std,
            "momentum": _mtm,
            "pull_dir": [0, 0, 0],
        },
        "spawn_kargs": lambda idx: {"init_vec": [0, 0, 1]},
        "children": [branch_config],
    }

    def att_fn(nodes, _sz=sz, _bh=box_ht, _sh=start_ht):
        return get_pts_from_shape_simple(
            500, [_sz / 2, _sz / 2, _bh], [0, 0, _sh + _sz * 0.4]
        )

    tmp_D = 0.3 + 0.2 * (sz / 30)
    if n < 5:
        n_steps = int(np.random.choice([2, 3, max(2, int(1 + sz // 2))]))
    else:
        n_steps = int(np.random.choice([2, 2, 2, 3, 4, 5]))

    spacecol_params = {
        "atts": att_fn,
        "D": tmp_D,
        "s": tmp_D * 1.3,
        "d": 10,
        "pull_dir": [0, 0, np.random.randn() * 0.3],
        "n_steps": n_steps,
    }

    # Absolute formula radius: clamp((rev_depth * scaling * 0.1)^exp, [min, max])
    skinning_params = {
        "min_radius": 0.02,
        "max_radius": 0.2,
        "exponent": 2.5 - g_branch_thickness,
        "scaling": 0.2,
    }

    return tree_config, spacecol_params, skinning_params, sz


def generate_pine_config():
    """Whorled pine: tall straight trunk, layers of horizontal branches."""

    per_layer = 4
    tree_ht = np.random.randint(20, 30)
    max_sz = 0.8
    start_ht = int(tree_ht * np.random.uniform(0.1, 0.3))
    n = tree_ht - start_ht

    def _branch_path(idx, _n=n, _max=max_sz, _ht=tree_ht):
        lo = max(1, int(np.floor(((_n - idx // per_layer) / max(_n, 1)) * 6)))
        hi = max(lo + 1, int(np.ceil(((_n - idx // per_layer) / max(_n, 1)) * 8)))
        return {
            "n_pts": np.random.randint(lo, hi) + 3,
            "std": 0.3,
            "momentum": 0.9,
            "sz": _max - (_max / _ht) * (idx // per_layer),
        }

    def _branch_spawn(idx, _start=start_ht):
        return {
            "rng": [0.5, 1],
            "z_bias": 0.2,
            "rnd_idx": (idx // per_layer) + _start,
            "ang_min": math.pi / 2,
            "ang_max": math.pi / 2 + math.pi / 16,
            "axis2": [np.random.randn(), np.random.randn(), 0.5],
        }

    branch_config = {
        "n": n * per_layer,
        "path_kargs": _branch_path,
        "spawn_kargs": _branch_spawn,
        "children": [],
    }
    tree_config = {
        "n": 1,
        "path_kargs": lambda idx, _ht=tree_ht: {
            "n_pts": _ht + 1,
            "sz": 0.8,
            "std": 0.1,
            "momentum": 0.7,
        },
        "spawn_kargs": lambda idx: {"init_vec": [0, 0, 1]},
        "children": [branch_config],
    }

    def att_fn(nodes):
        tmp = nodes[nodes[:, 2] > 3]
        if len(tmp) == 0:
            return get_pts_from_shape_simple(50, [1, 1, 1], [0, 0, tree_ht * 0.5])
        atts = [tmp.copy() + np.random.randn(*tmp.shape) * 0.5 for _ in range(5)]
        return np.concatenate(atts, 0)[::5]

    spacecol_params = {
        "atts": att_fn,
        "D": 0.3,
        "s": 0.4,
        "d": 10,
        "pull_dir": [0, 0, 0.5],
        "n_steps": 20,
    }
    skinning_params = {
        "min_radius": 0.02,
        "max_radius": 0.2,
        "exponent": 1.5,
        "scaling": 0.2,
    }
    return tree_config, spacecol_params, skinning_params, float(tree_ht)


def generate_palm_config():
    """Single curved trunk, no spacecol -- frond crown comes from _add_palm_fronds."""

    pull_angle = np.random.uniform(0.0, 2 * np.pi)
    n_pts = np.random.randint(28, 40)
    tree_config = {
        "n": 1,
        "path_kargs": lambda idx, _np=n_pts: {
            "n_pts": _np,
            "sz": 0.8,
            "std": 0.1,
            "momentum": 0.95,
            "pull_dir": [np.cos(pull_angle), np.sin(pull_angle), 0.0],
            "pull_factor": np.random.uniform(0.0, 1.0),
            "pull_init": 0.0,
        },
        "spawn_kargs": lambda idx: {"init_vec": [0, 0, 1]},
        "children": [],
    }
    spacecol_params = None
    # Near-cylindrical trunk: high min_radius, gentle exponent
    skinning_params = {
        "min_radius": 0.20,
        "max_radius": 0.32,
        "exponent": 2.2,
        "scaling": 0.6,
    }
    return tree_config, spacecol_params, skinning_params, float(n_pts * 0.8)


def generate_baobab_config():
    """Squat thick trunk + mostly crown via spacecol with wide flat box."""

    n_pts = 20
    tree_config = {
        "n": 1,
        "path_kargs": lambda idx: {
            "n_pts": n_pts,
            "sz": 0.8,
            "std": 0.1,
            "momentum": 0.95,
        },
        "spawn_kargs": lambda idx: {"init_vec": [0, 0, 1]},
        "children": [],
    }

    def att_fn(nodes):
        return get_pts_from_shape_simple(800, [10, 10, 1.5], [0, 0, n_pts * 0.7])

    spacecol_params = {
        "atts": att_fn,
        "D": 0.5,
        "s": 0.65,
        "d": 10,
        "pull_dir": [0, 0, 0.0],
        "n_steps": 14,
    }
    # Trunk fattens fast via high scaling+low exp; crown branches stay slim via low min_radius
    skinning_params = {
        "min_radius": 0.05,
        "max_radius": 0.85,
        "exponent": 1.5,
        "scaling": 0.7,
    }
    return tree_config, spacecol_params, skinning_params, float(n_pts)


def generate_bamboo_config():
    """Single tall culm with subtle horizontal lean -- leaves carry the silhouette."""

    pull_angle = np.random.uniform(0.0, 2 * np.pi)
    n_pts = np.random.randint(25, 36)
    tree_config = {
        "n": 1,
        "path_kargs": lambda idx, _np=n_pts: {
            "n_pts": _np,
            "sz": 0.8,
            "std": 0.1,
            "momentum": 0.95,
            "pull_dir": [np.cos(pull_angle), np.sin(pull_angle), 0.0],
            "pull_factor": np.random.uniform(0.1, 0.6),
            "pull_init": 0.0,
        },
        "spawn_kargs": lambda idx: {"init_vec": [0, 0, 1]},
        "children": [],
    }
    spacecol_params = None
    # Near-uniform slender culm -- bamboo has nearly constant diameter
    skinning_params = {
        "min_radius": 0.10,
        "max_radius": 0.15,
        "exponent": 2.5,
        "scaling": 0.5,
    }
    return tree_config, spacecol_params, skinning_params, float(n_pts)


def generate_twig_skeleton(seed=0):
    """Generate a twig skeleton: main stem + side branches + short sub-branches.

    Produces ~15-30 leaf tips total -- enough for a visible leaf cluster without
    the extreme density (~100 tips) of the deep 3-level hierarchy.
    """

    rng = np.random.RandomState(seed)

    # Main twig stem: 6-10 points
    n_main = rng.randint(6, 11)
    twig_len = rng.uniform(2.5, 4.0)
    twig_sz = twig_len / n_main

    # Side branches: 4-7 pairs, symmetric
    n_side_pairs = rng.randint(4, 8)
    start_idx = max(2, int(n_main * 0.2))
    step = max(1, (n_main - start_idx) // n_side_pairs)
    side_idxs = list(range(start_idx, n_main, step))[:n_side_pairs]

    ang_base = rng.uniform(math.pi / 5, math.pi / 3)
    iz = rng.uniform(0, 0.15)
    pf = rng.uniform(0, 0.2)

    # Each side branch: 3-5 points, with optional short sub-branches (2 pts)
    _ssz = rng.uniform(0.12, 0.25)
    _n_sub = rng.randint(3, 6)

    # Sub-sub branches on each side branch: 1-2 pairs at the end
    _subsub_sz = rng.uniform(0.06, 0.12)
    _sub_avail = list(range(max(1, _n_sub - 2), _n_sub))

    subsubtwig_config = {
        "n": len(_sub_avail),
        "symmetry": True,
        "path_kargs": lambda idx, ssz=_subsub_sz, _iz=iz, _pf=pf: {
            "n_pts": 2, "sz": ssz, "std": 0.9, "momentum": 0.5,
            "pull_dir": [0, 0, _iz + rng.randn() * 0.02],
            "pull_factor": _pf,
        },
        "spawn_kargs": lambda idx, av=_sub_avail: {
            "rnd_idx": av[min(idx, len(av) - 1)],
            "ang_min": math.pi / 4, "ang_max": math.pi / 3,
            "axis2": [0, 0, 1],
        },
    }

    subtwig_config = {
        "n": len(side_idxs),
        "symmetry": True,
        "path_kargs": lambda idx, ssz=_ssz, nsub=_n_sub, _iz=iz, _pf=pf: {
            "n_pts": nsub, "sz": ssz, "std": 0.7, "momentum": 0.55,
            "pull_dir": [0, 0, _iz + rng.randn() * 0.02],
            "pull_factor": _pf,
        },
        "spawn_kargs": lambda idx, _si=side_idxs, _ab=ang_base: {
            "rnd_idx": _si[min(idx, len(_si) - 1)],
            "ang_min": _ab, "ang_max": _ab + math.pi / 8,
            "axis2": [0, 0, 1],
        },
        "children": [subsubtwig_config],
    }

    twig_config = {
        "n": 1,
        "path_kargs": lambda idx, _tsz=twig_sz, _ntp=n_main, _iz=iz, _pf=pf: {
            "n_pts": _ntp, "sz": _tsz, "std": 0.4, "momentum": 0.55,
            "pull_dir": [0, 0, _iz + rng.randn() * 0.02],
            "pull_factor": _pf,
        },
        "spawn_kargs": lambda idx, _iz=iz: {"init_vec": [0, 1, -_iz]},
        "children": [subtwig_config],
    }

    vtx = TreeVertices(np.array([[0.0, 0.0, 0.0]]))
    recursive_path(vtx, vtx.get_idxs(), level=0, **twig_config)
    return vtx

def _leaf_width_broadleaf(t):
    """Ovate broadleaf -- narrow base, widest 35%, sharp acuminate tip."""

    if t <= 0.0 or t >= 1.0:
        return 0.0
    if t < 0.12:
        return 0.35 * (t / 0.12)
    if t < 0.38:
        return 0.35 + 0.65 * ((t - 0.12) / 0.26) ** 0.7
    if t < 0.72:
        return 1.0 - 0.08 * ((t - 0.38) / 0.34)
    return 0.92 * (1.0 - (t - 0.72) / 0.28) ** 1.8


def _leaf_width_ginko(t):
    """Ginko fan -- narrow base, widening to broad notched tip."""

    if t <= 0.0 or t >= 1.0:
        return 0.0
    if t < 0.85:
        return 0.15 + 0.85 * (t / 0.85) ** 1.2
    # Slight central notch at tip
    f = (t - 0.85) / 0.15
    return 1.0 * (1.0 - 0.4 * f)


def _leaf_width_maple(t, u):
    """Maple lobed -- angular 5-lobe outline based on (t, u) cell. Caller passes
    column-relative u in [-1,1]; we modulate base ovate width with cosine notches.
    """

    if t <= 0.0 or t >= 1.0:
        return 0.0
    base = 0.85 * math.sin(t * math.pi) ** 0.6
    # 3 lobes radiating outward -- subtract notches at fixed angular positions
    lobe_factor = 1.0 - 0.25 * (1.0 - math.cos(t * math.pi * 3))
    return max(0.05, base * lobe_factor)


def _leaf_width(t, leaf_type="broadleaf", u=0.0):
    if leaf_type == "ginko":
        return _leaf_width_ginko(t)
    if leaf_type == "maple":
        return _leaf_width_maple(t, u)
    return _leaf_width_broadleaf(t)

def _orthonormal_frame(leaf_fwd, leaf_normal):
    leaf_fwd = np.array(leaf_fwd, dtype=float)
    leaf_normal = np.array(leaf_normal, dtype=float)
    fn = np.linalg.norm(leaf_fwd)
    leaf_fwd = leaf_fwd / fn if fn > 1e-10 else np.array([0.0, 1.0, 0.0])
    nn = np.linalg.norm(leaf_normal)
    leaf_normal = leaf_normal / nn if nn > 1e-10 else np.array([0.0, 0.0, 1.0])
    leaf_normal = leaf_normal - leaf_fwd * np.dot(leaf_normal, leaf_fwd)
    nn = np.linalg.norm(leaf_normal)
    leaf_normal = leaf_normal / nn if nn > 1e-10 else np.array([0.0, 0.0, 1.0])
    right = np.cross(leaf_fwd, leaf_normal)
    rn = np.linalg.norm(right)
    right = right / rn if rn > 1e-10 else np.array([1.0, 0.0, 0.0])
    return leaf_fwd, leaf_normal, right


def _make_needle_cluster(bm, base_pos, leaf_fwd, leaf_normal, hw, hl, rng=None):
    """Pine needle: 3-5 thin spikes radiating from base, each a slim quad strip."""

    if rng is None:
        rng = np.random
    leaf_fwd, leaf_normal, right = _orthonormal_frame(leaf_fwd, leaf_normal)
    n_needles = 3 + (int(rng.random() * 3) if hasattr(rng, "random") else 3)
    spread = 0.45
    needle_w = max(0.0006, hw * 0.05)
    needle_l = hl * 1.6
    base_pos = np.array(base_pos)
    for ni in range(n_needles):
        ang = (ni / max(1, n_needles - 1) - 0.5) * spread * 2 * math.pi / 3
        dir_v = leaf_fwd * math.cos(ang) + right * math.sin(ang)
        side = np.cross(dir_v, leaf_normal)
        sn = np.linalg.norm(side)
        side = side / sn if sn > 1e-10 else right
        v0 = bm.verts.new(base_pos + side * (-needle_w))
        v1 = bm.verts.new(base_pos + side * needle_w)
        tip = base_pos + dir_v * needle_l + leaf_normal * (-needle_l * 0.05)
        v2 = bm.verts.new(tip)
        try:
            bm.faces.new([v0, v1, v2])
        except ValueError:
            pass


def _make_flower(bm, base_pos, leaf_fwd, leaf_normal, hw, hl):
    """5-petal starburst -- small flower at branch position."""

    leaf_fwd, leaf_normal, right = _orthonormal_frame(leaf_fwd, leaf_normal)
    base_pos = np.array(base_pos)
    n_petals = 5
    cv = bm.verts.new(base_pos + leaf_normal * (hl * 0.06))
    rim_verts = []
    for pi in range(n_petals):
        ang = 2 * math.pi * pi / n_petals
        d = right * math.cos(ang) + leaf_fwd * math.sin(ang)
        rim_verts.append(bm.verts.new(base_pos + d * (hw * 0.7) + leaf_normal * (hl * 0.02)))
    for pi in range(n_petals):
        ang = 2 * math.pi * (pi + 0.5) / n_petals
        d = right * math.cos(ang) + leaf_fwd * math.sin(ang)
        tip = bm.verts.new(base_pos + d * (hw * 1.05) + leaf_normal * (-hl * 0.01))
        a = rim_verts[pi]
        b = rim_verts[(pi + 1) % n_petals]
        try:
            bm.faces.new([cv, a, tip])
            bm.faces.new([cv, tip, b])
        except ValueError:
            pass


def _make_blade_leaf(bm, base_pos, leaf_fwd, leaf_normal, hw, hl, leaf_type):
    """Generic grid-based leaf blade. Width curve dispatched by leaf_type.
    Reduced grid resolution (5x4) keeps vert count manageable.
    """

    base_pos = np.array(base_pos)
    leaf_fwd, leaf_normal, right = _orthonormal_frame(leaf_fwd, leaf_normal)

    n_rows = 5
    n_cols = 5 if leaf_type == "maple" else 4
    mid_col = n_cols // 2

    grid = []
    for ri in range(n_rows):
        t = ri / (n_rows - 1)
        row = []
        for ci in range(n_cols):
            u = (ci - mid_col) / max(mid_col, 1)
            w = _leaf_width(t, leaf_type=leaf_type, u=u)
            x_local = u * w * hw
            if w < 0.02 and ci != mid_col:
                row.append(None)
                continue
            y_local = t * hl
            abs_u = abs(u)
            midrib_h = 0.04 * hl * (1.0 - abs_u ** 0.55) * max(0, 1.0 - 0.25 * t)
            edge_droop = -0.02 * hl * abs_u ** 2.0
            tip_droop = -0.015 * hl * max(0, t - 0.4) ** 2
            wave = 0.005 * hl * math.sin(abs_u * math.pi * 2) * (1.0 - abs_u)
            z_local = midrib_h + edge_droop + tip_droop + wave
            pt = base_pos + right * x_local + leaf_fwd * y_local + leaf_normal * z_local
            row.append(bm.verts.new(pt))
        grid.append(row)

    # Tip vertex
    tip_z = -0.01 * hl
    tip_v = bm.verts.new(base_pos + leaf_fwd * (hl * 1.03) + leaf_normal * tip_z)

    # Grid quads
    for ri in range(n_rows - 1):
        for ci in range(n_cols - 1):
            corners = [grid[ri][ci], grid[ri][ci + 1],
                       grid[ri + 1][ci + 1], grid[ri + 1][ci]]
            valid = [v for v in corners if v is not None]
            if len(valid) >= 3:
                try:
                    bm.faces.new(valid)
                except ValueError:
                    pass

    # Tip triangles
    last_row = grid[n_rows - 1]
    valid_last = [(ci, v) for ci, v in enumerate(last_row) if v is not None]
    for i in range(len(valid_last) - 1):
        try:
            bm.faces.new([valid_last[i][1], valid_last[i + 1][1], tip_v])
        except ValueError:
            pass

    # Petiole: tapered cylinder connecting branch to leaf base
    pet_len = hl * 0.18
    pet_r_base = hw * 0.06
    pet_r_tip = hw * 0.038
    n_ps = 4
    n_pr = 2
    pet_rings = []
    for pi in range(n_pr):
        frac = pi / (n_pr - 1)
        r = pet_r_base + (pet_r_tip - pet_r_base) * frac
        center = base_pos - leaf_fwd * pet_len * (1.0 - frac)
        ring = []
        for si in range(n_ps):
            ang = 2 * math.pi * si / n_ps
            offset = right * (r * math.cos(ang)) + leaf_normal * (r * math.sin(ang))
            ring.append(bm.verts.new(center + offset))
        pet_rings.append(ring)

    for pi in range(n_pr - 1):
        for si in range(n_ps):
            sn = (si + 1) % n_ps
            try:
                bm.faces.new([pet_rings[pi][si], pet_rings[pi][sn],
                              pet_rings[pi + 1][sn], pet_rings[pi + 1][si]])
            except ValueError:
                pass

    # Connect petiole tip ring to leaf base center
    base_mid = grid[0][mid_col]
    if base_mid is not None:
        pr = pet_rings[-1]
        for si in range(n_ps):
            sn = (si + 1) % n_ps
            try:
                bm.faces.new([pr[si], pr[sn], base_mid])
            except ValueError:
                pass


def _make_leaf(bm, base_pos, leaf_fwd, leaf_normal, hw, hl, leaf_type="broadleaf", rng=None):
    """Dispatch to the per-type leaf builder. Blade types share the grid pipeline,
    needle/flower take their own short codepaths."""

    if leaf_type == "needle":
        _make_needle_cluster(bm, base_pos, leaf_fwd, leaf_normal, hw, hl, rng=rng)
        return
    if leaf_type == "flower":
        _make_flower(bm, base_pos, leaf_fwd, leaf_normal, hw, hl)
        return
    _make_blade_leaf(bm, base_pos, leaf_fwd, leaf_normal, hw, hl, leaf_type)


def _place_leaf_at(bm, pos, branch_dir, rng, leaf_hw, leaf_hl, leaf_type="broadleaf"):
    """Place one leaf at pos with petiole connecting back toward branch."""

    pos = np.array(pos)
    branch_dir = np.array(branch_dir, dtype=float)
    bdn = np.linalg.norm(branch_dir)
    if bdn < 1e-10:
        branch_dir = np.array([0.0, 0.0, 1.0])
    else:
        branch_dir /= bdn

    # Spread from branch direction
    spread_ang = rng.uniform(0.35, 0.75)
    perp = np.array([branch_dir[1], -branch_dir[0], 0.0])
    pn = np.linalg.norm(perp)
    if pn < 1e-10:
        perp = np.array([1.0, 0.0, 0.0])
    else:
        perp /= pn
    azim = rng.uniform(0, 2 * math.pi)
    perp = rodrigues_rot(perp, branch_dir, azim)
    leaf_dir = rodrigues_rot(branch_dir, perp, spread_ang)
    ldn = np.linalg.norm(leaf_dir)
    if ldn > 1e-10:
        leaf_dir /= ldn

    # Leaf normal: mostly upward, tilted slightly away from branch
    leaf_normal = np.array([0.0, 0.0, 1.0]) * 0.6 + leaf_dir * 0.2
    leaf_normal += rng.randn(3) * 0.05
    lnn = np.linalg.norm(leaf_normal)
    if lnn > 1e-10:
        leaf_normal /= lnn
    else:
        leaf_normal = np.array([0.0, 0.0, 1.0])

    hw = rng.uniform(leaf_hw * 0.8, leaf_hw * 1.2)
    hl = rng.uniform(leaf_hl * 0.8, leaf_hl * 1.2)
    _make_leaf(bm, pos, leaf_dir, leaf_normal, hw, hl, leaf_type=leaf_type, rng=rng)

def make_twig_with_leaves(twig_vtx, scale, rng, leaf_hw=0.032, leaf_hl=0.048,
                          leaf_density=1.0, leaf_type="broadleaf"):
    """Build one twig variant: skin skeleton -> add leaves along branches and at tips.

    (not just at tips), using a density parameter to control spacing.
    Returns a single Blender mesh object (twig tubes + leaves).
    """
    # 1. Compute twig attributes
    rev_depth = parse_tree_attributes(twig_vtx)

    # 2. Skin twig skeleton to tube mesh (thin tubes, low-poly profile)
    twig_obj = skeleton_to_mesh(
        twig_vtx, rev_depth, scale=scale,
        min_radius=0.001, max_radius=0.004,
        exponent=1.3, profile_res=4,
    )

    # 3. Collect leaf placement positions along ALL edges (not just tips)
    # For each edge, interpolate positions along it with some spacing
    n_tw = len(twig_vtx)
    leaf_positions = []  # (position, direction) pairs

    for i in range(1, n_tw):
        p = twig_vtx.parent[i]
        if p < 0:
            continue
        p0 = twig_vtx.vtxs[p] * scale
        p1 = twig_vtx.vtxs[i] * scale
        edge_vec = p1 - p0
        edge_len = np.linalg.norm(edge_vec)
        if edge_len < 1e-8:
            continue
        edge_dir = edge_vec / edge_len

        # Only place leaves on outer branches (low rev_depth)
        rd = rev_depth[i]
        max_rd_val = max(1, rev_depth.max())
        norm_rd = rd / max_rd_val
        if norm_rd > 0.60:
            continue  # skip only the thickest main stem

        # Leaf spacing modulated by density knob -- wider spacing -> fewer leaves
        spacing = rng.uniform(0.022, 0.034) / max(0.1, leaf_density)
        n_along = max(1, int(edge_len / spacing))

        for j in range(n_along):
            t = (j + 0.5) / n_along
            if rng.random() > (0.55 + 0.15 * t) * leaf_density:
                continue
            pt = p0 + edge_vec * t
            leaf_positions.append((pt, edge_dir))

    # 4. Build leaves using bmesh
    bm = bmesh.new()
    for pos, direction in leaf_positions:
        _place_leaf_at(bm, pos, direction, rng, leaf_hw, leaf_hl, leaf_type=leaf_type)

    # 5. Create leaf mesh object and join with twig
    if len(bm.verts) > 0:
        leaf_mesh = bpy.data.meshes.new("TwigLeaves")
        bm.to_mesh(leaf_mesh)
        leaf_mesh.update()
        leaf_obj = bpy.data.objects.new("TwigLeaves", leaf_mesh)
        bpy.context.scene.collection.objects.link(leaf_obj)

        # Solidify leaves
        bpy.ops.object.select_all(action='DESELECT')
        leaf_obj.select_set(True)
        bpy.context.view_layer.objects.active = leaf_obj
        sol = leaf_obj.modifiers.new("sol", "SOLIDIFY")
        sol.thickness = 0.001
        bpy.ops.object.modifier_apply(modifier=sol.name)

        # Join twig tube + leaves
        bpy.ops.object.select_all(action='DESELECT')
        twig_obj.select_set(True)
        leaf_obj.select_set(True)
        bpy.context.view_layer.objects.active = twig_obj
        bpy.ops.object.join()

    bm.free()
    return twig_obj

def add_twigs_and_leaves(vtx, rev_depth, scale, seed=0,
                          leaf_density=1.0, leaf_type="broadleaf",
                          max_placements=400, placement_keep=0.5,
                          outer_only_threshold=0.40):
    """Place twig+leaf units on the tree skeleton's outer branches.

    leaf_density: 0-1+ multiplier on leaves per twig (winter->0, summer->1).
    leaf_type: 'broadleaf' / 'ginko' / 'maple' / 'needle' / 'flower'.
    max_placements: hard cap on twig units; lower = lighter mesh.
    placement_keep: pre-cap stochastic keep rate.
    outer_only_threshold: norm_depth gate (lower = more selective on outer branches).
    """

    rng = np.random.RandomState(seed + 8888)

    if leaf_density <= 0.001 and leaf_type != "needle":
        return None  # winter w/o needles -> bare branches

    max_rd = int(rev_depth.max()) if rev_depth.max() > 0 else 1
    norm_depth = rev_depth.astype(float) / max_rd  # 0=tip, 1=trunk

    placement_mask = norm_depth < outer_only_threshold
    placement_indices = np.where(placement_mask)[0]

    keep = rng.random(len(placement_indices)) < placement_keep
    placement_indices = placement_indices[keep]

    if len(placement_indices) > max_placements:
        placement_indices = rng.choice(placement_indices, max_placements, replace=False)

    n_variants = 3
    twig_mesh_data = []
    for ti in range(n_variants):
        twig_vtx = generate_twig_skeleton(seed + ti * 1000 + 7777)
        twig_obj = make_twig_with_leaves(
            twig_vtx, scale, rng, leaf_density=leaf_density, leaf_type=leaf_type
        )

        tv = np.array([v.co[:] for v in twig_obj.data.vertices])
        tf = [tuple(p.vertices) for p in twig_obj.data.polygons]
        twig_mesh_data.append((tv, tf))
        bpy.data.objects.remove(twig_obj, do_unlink=True)

    # Duplicate at placement positions
    all_verts = []
    all_faces = []
    vert_offset = 0

    for pi, idx in enumerate(placement_indices):
        vi = rng.randint(0, n_variants)
        tverts, tfaces = twig_mesh_data[vi]

        pos = vtx.vtxs[idx] * scale

        parent_i = vtx.parent[idx]
        if parent_i >= 0:
            direction = vtx.vtxs[idx] - vtx.vtxs[parent_i]
            dn = np.linalg.norm(direction)
            if dn > 1e-10:
                direction /= dn
            else:
                direction = np.array([0.0, 0.0, 1.0])
        else:
            direction = np.array([0.0, 0.0, 1.0])

        # Rotate twig [0,1,0] -> branch direction
        rot = rotation_between_vectors(np.array([0.0, 1.0, 0.0]), direction)

        # Random yaw around branch axis
        yaw = rng.uniform(0, 2 * math.pi)
        yaw_rot = axis_angle_matrix(direction, yaw)

        # Random scale variation
        s = rng.uniform(0.9, 1.2)

        transformed = (tverts @ rot.T @ yaw_rot.T) * s + pos
        all_verts.append(transformed)
        for f in tfaces:
            all_faces.append(tuple(v + vert_offset for v in f))
        vert_offset += len(tverts)

    if all_verts:
        all_verts_np = np.concatenate(all_verts, axis=0)
        mesh = bpy.data.meshes.new("TwigsAndLeaves")
        mesh.from_pydata(all_verts_np.tolist(), [], all_faces)
        mesh.update()

        obj = bpy.data.objects.new("TwigsAndLeaves", mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj

    return None

SPECIES_WEIGHTS = {
    "broadleaf": 0.65,
    "pine": 0.10,
    "palm": 0.08,
    "baobab": 0.05,
    "bamboo": 0.05,
    "ginko": 0.04,
    "maple": 0.03,
}

SEASON_WEIGHTS = {"summer": 0.30, "spring": 0.40, "autumn": 0.25, "winter": 0.05}


def _pick_species(rng):
    keys = list(SPECIES_WEIGHTS.keys())
    weights = np.array([SPECIES_WEIGHTS[k] for k in keys])
    weights /= weights.sum()
    return keys[int(rng.choice(len(keys), p=weights))]


def _pick_season(rng):
    keys = list(SEASON_WEIGHTS.keys())
    weights = np.array([SEASON_WEIGHTS[k] for k in keys])
    weights /= weights.sum()
    return keys[int(rng.choice(len(keys), p=weights))]


def _season_leaf_params(species, season, rng):
    """Map (species, season) -> (leaf_type, leaf_density). Winter strips leaves
    on broadleaf species; spring swaps in flowers; needle species keep needles."""

    if species == "pine":
        return "needle", 1.0
    if species == "bamboo":
        return "broadleaf", 0.7  # bamboo leaves are blade-shaped
    if species == "palm":
        return "broadleaf", 0.0  # palm fronds via separate fern-leaf system below
    if species == "baobab":
        leaf = "broadleaf"
    elif species in ("ginko", "maple"):
        leaf = species
    else:
        leaf = "broadleaf"

    if season == "winter":
        return leaf, rng.uniform(0.0, 0.05)
    if season == "spring":
        return ("flower" if rng.random() < 0.6 else leaf), rng.uniform(0.4, 0.7)
    if season == "autumn":
        return leaf, rng.uniform(0.5, 0.9)
    return leaf, rng.uniform(0.7, 1.0)  # summer


def _add_palm_fronds(trunk_obj, sz, scale, rng):
    """Place long droopy fronds at trunk top -- palm canopy. 2-3 elevation tiers."""

    bm = bmesh.new()
    n_fronds = rng.randint(18, 26)
    # Use mesh max-z as apex; subtract tiny offset so fronds anchor below tip
    apex_z = max(v.co.z for v in trunk_obj.data.vertices) - 0.03
    apex = np.array([0.0, 0.0, apex_z])
    n_tiers = 3

    for fi in range(n_fronds * n_tiers):
        tier = fi // n_fronds
        within = fi % n_fronds
        ang = 2 * math.pi * within / n_fronds + tier * math.pi / n_fronds + rng.uniform(-0.08, 0.08)
        # Tier 0: nearly horizontal, tier 2: drooping deeply
        droop = 0.15 + tier * 0.55 + rng.uniform(-0.05, 0.10)
        out = np.array([math.cos(ang), math.sin(ang), 0.0])
        frond_fwd = out * 1.0 - np.array([0.0, 0.0, 1.0]) * droop
        nrm = np.array([0.0, 0.0, 1.0]) * 0.7 + out * 0.2
        nrm += rng.randn(3) * 0.04
        nlen = np.linalg.norm(nrm)
        if nlen > 1e-10:
            nrm /= nlen
        hw = rng.uniform(0.08, 0.14)
        hl = rng.uniform(2.4, 3.6)
        anchor = apex + np.array([0, 0, -tier * 0.04])
        _make_blade_leaf(bm, anchor, frond_fwd, nrm, hw, hl, "ginko")

    if len(bm.verts) == 0:
        bm.free()
        return None
    fronds_mesh = bpy.data.meshes.new("PalmFronds")
    bm.to_mesh(fronds_mesh)
    fronds_mesh.update()
    bm.free()
    fronds_obj = bpy.data.objects.new("PalmFronds", fronds_mesh)
    bpy.context.scene.collection.objects.link(fronds_obj)
    bpy.ops.object.select_all(action='DESELECT')
    fronds_obj.select_set(True)
    bpy.context.view_layer.objects.active = fronds_obj
    sol = fronds_obj.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.003
    bpy.ops.object.modifier_apply(modifier=sol.name)
    return fronds_obj


def _make_fruit(bm, pos, fruit_type, scale_radius, rng):
    """Geometric fruit placeholders. Mesh-only, not material-shaded."""

    pos = np.array(pos)
    r = scale_radius
    if fruit_type == "apple":
        n_lat, n_lon = 6, 8
        verts = []
        for la in range(n_lat + 1):
            phi = math.pi * la / n_lat
            ring = []
            for lo in range(n_lon):
                th = 2 * math.pi * lo / n_lon
                p = pos + np.array([
                    r * math.sin(phi) * math.cos(th),
                    r * math.sin(phi) * math.sin(th),
                    -r * math.cos(phi),
                ])
                ring.append(bm.verts.new(p))
            verts.append(ring)
        for la in range(n_lat):
            for lo in range(n_lon):
                ln = (lo + 1) % n_lon
                a, b = verts[la][lo], verts[la][ln]
                c, d = verts[la + 1][ln], verts[la + 1][lo]
                try:
                    bm.faces.new([a, b, c, d])
                except ValueError:
                    pass
    elif fruit_type == "durian":
        # Spiky sphere: short cones radiating
        n = 14
        cv = bm.verts.new(pos)
        for _ in range(n):
            d = rng.randn(3)
            d /= max(np.linalg.norm(d), 1e-10)
            tip = bm.verts.new(pos + d * (r * 1.4))
            perp = np.cross(d, np.array([0, 0, 1]))
            pn = np.linalg.norm(perp)
            if pn < 1e-10:
                perp = np.array([1.0, 0, 0])
            else:
                perp /= pn
            v1 = bm.verts.new(pos + d * r * 0.6 + perp * r * 0.25)
            v2 = bm.verts.new(pos + d * r * 0.6 - perp * r * 0.25)
            try:
                bm.faces.new([cv, v1, tip])
                bm.faces.new([cv, tip, v2])
            except ValueError:
                pass
    elif fruit_type == "starfruit":
        # 5-pointed cross-section, extruded short
        n_pts = 5
        ring_top, ring_bot = [], []
        for pi in range(n_pts * 2):
            ang = 2 * math.pi * pi / (n_pts * 2)
            rr = r if pi % 2 == 0 else r * 0.45
            ring_top.append(bm.verts.new(pos + np.array([rr * math.cos(ang), rr * math.sin(ang), r * 0.4])))
            ring_bot.append(bm.verts.new(pos + np.array([rr * math.cos(ang), rr * math.sin(ang), -r * 0.4])))
        for pi in range(len(ring_top)):
            pn = (pi + 1) % len(ring_top)
            try:
                bm.faces.new([ring_top[pi], ring_top[pn], ring_bot[pn], ring_bot[pi]])
            except ValueError:
                pass
    else:  # coconut / generic -- oblong sphere
        n_lat, n_lon = 5, 7
        rings = []
        for la in range(n_lat + 1):
            phi = math.pi * la / n_lat
            ring = []
            for lo in range(n_lon):
                th = 2 * math.pi * lo / n_lon
                p = pos + np.array([
                    r * math.sin(phi) * math.cos(th),
                    r * math.sin(phi) * math.sin(th),
                    -r * 1.3 * math.cos(phi),
                ])
                ring.append(bm.verts.new(p))
            rings.append(ring)
        for la in range(n_lat):
            for lo in range(n_lon):
                ln = (lo + 1) % n_lon
                try:
                    bm.faces.new([rings[la][lo], rings[la][ln], rings[la + 1][ln], rings[la + 1][lo]])
                except ValueError:
                    pass


def _add_fruits(vtx, rev_depth, scale, seed, fruit_type, density=0.05, max_fruits=30):
    rng = np.random.RandomState(seed + 13579)
    max_rd = int(rev_depth.max()) if rev_depth.max() > 0 else 1
    norm_depth = rev_depth.astype(float) / max_rd
    cand = np.where((norm_depth < 0.30) & (norm_depth > 0.05))[0]
    if len(cand) == 0:
        return None
    keep = rng.random(len(cand)) < density
    cand = cand[keep]
    if len(cand) > max_fruits:
        cand = rng.choice(cand, max_fruits, replace=False)
    if len(cand) == 0:
        return None

    bm = bmesh.new()
    fr_size = {"apple": 0.04, "durian": 0.07, "starfruit": 0.05, "coconutgreen": 0.06}.get(fruit_type, 0.05)
    for idx in cand:
        pos = vtx.vtxs[idx] * scale + np.array([0, 0, -fr_size * 1.2])
        _make_fruit(bm, pos, fruit_type, fr_size, rng)

    if len(bm.verts) == 0:
        bm.free()
        return None
    mesh = bpy.data.meshes.new("Fruits")
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    obj = bpy.data.objects.new("Fruits", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ── Materials ─────────────────────────────────────────────────────────────────
# LeafFactoryBroadleaf shader (objects/leaves/leaf_broadleaf.py). The trunk
# uses a voronoi-cracked brown shader matching shader_random_bark_mat, and
# the canopy leaves use an HSV-space blade+vein shader driven by TexCoord
# noise with season-aware blade hue matching LeafFactoryBroadleaf.__init__.

WOOD_COLORS_HEX = [
    0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170,
    0x3D2B1F, 0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43,
    0x4E3828, 0x4E3828, 0xC09A6B, 0x944536, 0x3F0110, 0x773C12,
    0x6E4E37, 0x5C4033, 0x5C4033, 0x3C3034, 0x96704C, 0x371B1A,
    0x483B32, 0x43141A, 0x471713, 0xC3B090, 0x6B4423, 0x674D46,
    0x5D2E1A, 0x331C1F, 0x7A5640, 0xB99984, 0x71543D, 0x8F4B28,
    0x491A00, 0x836446, 0x7F461B, 0x6A3208, 0x724115, 0xA0522B,
    0x832A0C, 0x371B1A, 0xC7A373, 0x483B32, 0x635147, 0x664228,
    0x5C5248,
]


def _hex_to_rgb(hexval):
    """Convert 0xRRGGBB integer to (R, G, B) floats in [0,1]."""

    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return r, g, b


def _sample_bark_color_hsv():
    hexval = WOOD_COLORS_HEX[np.random.randint(len(WOOD_COLORS_HEX))]
    r, g, b = _hex_to_rgb(hexval)
    return colorsys.rgb_to_hsv(r, g, b)


def _hsv_to_rgba(h, s, v):
    h = float(h) % 1.0
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, min(1.0, float(v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def _fac_output(node):
    """Return the Fac/Factor output of a Noise/Voronoi node (5.0 renamed it)."""

    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]


def create_bark_material():
    """

    Replicates the voronoi-cracked base color pipeline from
    drives a dark/bright mix, secondary noise overlays a slight color shift,
    and multi-scale bump approximates the displacement-based bark ridges
    since the standalone mesh lacks the skeleton_loc attributes needed for
    the real geometric displacement.
    """

    base_h, base_s, base_v = _sample_bark_color_hsv()

    mat = bpy.data.materials.new("BarkMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (500, 0)
    # Matches `Roughness: 0.7` from shader_random_bark_mat
    bsdf.inputs['Roughness'].default_value = 0.7
    links.new(bsdf.outputs[0], output.inputs[0])

    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1000, 0)

    # ── Base color palette (dark / bright / mid) from sampled HSV ──
    dark_rgba = _hsv_to_rgba(base_h, min(1.0, base_s * 1.1), max(0.0, base_v * 0.40))
    bright_rgba = _hsv_to_rgba(base_h, max(0.0, base_s * 0.8), min(1.0, base_v * 1.5 + 0.1))
    mid_rgba = _hsv_to_rgba(base_h, max(0.0, base_s * 0.6), min(1.0, base_v * 1.3))

    # ── Primary Voronoi: bark crack pattern (matches nodegroup_voronoi / primary) ──
    voronoi_primary = nodes.new('ShaderNodeTexVoronoi')
    voronoi_primary.feature = 'DISTANCE_TO_EDGE'
    voronoi_primary.location = (-700, 200)
    # shader_random_bark_mat: primary_voronoi scale ~ 20-40
    voronoi_primary.inputs['Scale'].default_value = float(np.random.uniform(20.0, 40.0))
    voronoi_primary.inputs['Randomness'].default_value = float(np.random.uniform(0.6, 1.0))
    links.new(tex_coord.outputs['Object'], voronoi_primary.inputs['Vector'])

    # MapRange on Voronoi distance -- matches nodegroup_voronoi map_range (0..0.5)
    map_range_primary = nodes.new('ShaderNodeMapRange')
    map_range_primary.location = (-450, 200)
    map_range_primary.inputs['From Min'].default_value = 0.0
    map_range_primary.inputs['From Max'].default_value = 0.5
    links.new(voronoi_primary.outputs['Distance'], map_range_primary.inputs['Value'])

    # ── Secondary Voronoi: finer crack modulation (nodegroup_primary_voronoi overlay) ──
    voronoi_secondary = nodes.new('ShaderNodeTexVoronoi')
    voronoi_secondary.feature = 'DISTANCE_TO_EDGE'
    voronoi_secondary.location = (-700, -50)
    voronoi_secondary.inputs['Scale'].default_value = float(np.random.uniform(30.0, 50.0))
    links.new(tex_coord.outputs['Object'], voronoi_secondary.inputs['Vector'])

    map_range_secondary = nodes.new('ShaderNodeMapRange')
    map_range_secondary.location = (-450, -50)
    map_range_secondary.inputs['From Min'].default_value = 0.0
    map_range_secondary.inputs['From Max'].default_value = 0.1
    links.new(voronoi_secondary.outputs['Distance'], map_range_secondary.inputs['Value'])

    # ── Noise for color variation (noise_texture_1 in shader_random_bark_mat) ──
    noise_color = nodes.new('ShaderNodeTexNoise')
    noise_color.location = (-700, -250)
    noise_color.inputs['Scale'].default_value = float(np.random.uniform(8.0, 15.0))
    noise_color.inputs['Detail'].default_value = 6.0
    links.new(tex_coord.outputs['Object'], noise_color.inputs['Vector'])

    # Mix 1: dark <-> bright via primary voronoi (matches mix_3 in shader_random_bark_mat)
    mix_base = nodes.new('ShaderNodeMix')
    mix_base.location = (-150, 200)
    mix_base.data_type = 'RGBA'
    mix_base.inputs[6].default_value = dark_rgba
    mix_base.inputs[7].default_value = bright_rgba
    links.new(map_range_primary.outputs['Result'], mix_base.inputs[0])

    # Mix 2: blend with mid-tone modulated by secondary voronoi (mix_4)
    mix_mid = nodes.new('ShaderNodeMix')
    mix_mid.location = (100, 200)
    mix_mid.data_type = 'RGBA'
    mix_mid.inputs[7].default_value = mid_rgba
    links.new(mix_base.outputs[2], mix_mid.inputs[6])
    links.new(map_range_secondary.outputs['Result'], mix_mid.inputs[0])

    # Mix 3: subtle noise-driven overlay (mix_2 / MapRange 2 path)
    mix_noise = nodes.new('ShaderNodeMix')
    mix_noise.location = (350, 200)
    mix_noise.data_type = 'RGBA'
    mix_noise.inputs[0].default_value = 0.15
    links.new(mix_mid.outputs[2], mix_noise.inputs[6])
    shift_rgba = _hsv_to_rgba(base_h, max(0.0, base_s * 0.65), min(1.0, base_v * 1.35))
    mix_noise.inputs[7].default_value = shift_rgba
    links.new(_fac_output(noise_color), mix_noise.inputs[0])

    links.new(mix_noise.outputs[2], bsdf.inputs['Base Color'])

    # ── Multi-scale bump: approximates geo_bark_random displacement ──
    noise_bump_large = nodes.new('ShaderNodeTexNoise')
    noise_bump_large.location = (-700, -450)
    noise_bump_large.inputs['Scale'].default_value = float(np.random.uniform(15.0, 25.0))
    noise_bump_large.inputs['Detail'].default_value = 8.0
    noise_bump_large.inputs['Roughness'].default_value = 0.7
    links.new(tex_coord.outputs['Object'], noise_bump_large.inputs['Vector'])

    bump_large = nodes.new('ShaderNodeBump')
    bump_large.location = (-150, -450)
    bump_large.inputs['Strength'].default_value = 0.5
    bump_large.inputs['Distance'].default_value = 0.02
    links.new(_fac_output(noise_bump_large), bump_large.inputs['Height'])

    noise_bump_fine = nodes.new('ShaderNodeTexNoise')
    noise_bump_fine.location = (-700, -650)
    noise_bump_fine.inputs['Scale'].default_value = float(np.random.uniform(40.0, 80.0))
    noise_bump_fine.inputs['Detail'].default_value = 4.0
    links.new(tex_coord.outputs['Object'], noise_bump_fine.inputs['Vector'])

    bump_fine = nodes.new('ShaderNodeBump')
    bump_fine.location = (100, -450)
    bump_fine.inputs['Strength'].default_value = 0.15
    bump_fine.inputs['Distance'].default_value = 0.005
    links.new(_fac_output(noise_bump_fine), bump_fine.inputs['Height'])
    links.new(bump_large.outputs[0], bump_fine.inputs['Normal'])

    links.new(bump_fine.outputs[0], bsdf.inputs['Normal'])

    return mat


def _sample_broadleaf_blade_vein_hsv(season):
    """Replicate LeafFactoryBroadleaf.__init__ blade/vein HSV sampling."""

    if season == "autumn":
        blade = [float(np.random.uniform(0.0, 0.20)), 0.85, 0.9]
        vein = list(blade)
        vein[2] = 0.7
    elif season in ("summer", "spring"):
        blade = [float(np.random.uniform(0.28, 0.32)),
                 float(np.random.uniform(0.6, 0.7)),
                 0.9]
        vein = list(blade)
        blade[2] = float(np.random.uniform(0.1, 0.5))
        vein[2] = float(np.random.uniform(0.1, 0.5))
    elif season == "winter":
        blade = [float(np.random.uniform(0.0, 0.10)),
                 float(np.random.uniform(0.2, 0.6)),
                 float(np.random.uniform(0.0, 0.1))]
        vein = [float(np.random.uniform(0.0, 0.10)),
                float(np.random.uniform(0.2, 0.6)),
                float(np.random.uniform(0.0, 0.1))]
    else:
        blade = [0.3, 0.65, 0.5]
        vein = [0.3, 0.65, 0.35]
    return blade, vein


def create_leaf_material(season):
    """Leaf shader for tree canopies, aligned with LeafFactoryBroadleaf.

    Replicates the blade+vein HSV palette sampled in
    LeafFactoryBroadleaf.__init__ and the Principled+Translucent mix from
    leaf_v2's shader_leaf_new. Blade/vein are seeded per factory_seed and
    interpolated by an object-space noise texture to mimic the vein mask
    from shader_nodegroup_apply_vein_midrib. The LeafFactoryBroadleaf uses
    a more elaborate curve-driven vein pattern, but since our canopy mesh
    is low-poly grid-leaves it suffices to drive vein variation from noise.
    """

    blade_hsv, vein_hsv = _sample_broadleaf_blade_vein_hsv(season)
    blade_rgba = _hsv_to_rgba(*blade_hsv)
    vein_rgba = _hsv_to_rgba(*vein_hsv)
    # vein_color_mix_factor, matches LeafFactoryBroadleaf sampling
    vein_mix_factor = float(np.random.uniform(0.2, 0.6))
    # color_randomness (uniform 0.05-0.10) -- used to offset blade channels
    color_randomness = float(np.random.uniform(0.05, 0.10))
    blade_rgba = tuple(max(0.0, min(1.0, c + np.random.normal(0.0, color_randomness)))
                       for c in blade_rgba[:3]) + (1.0,)

    mat = bpy.data.materials.new("LeafMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (700, 0)

    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)

    # Noise texture -- drives vein/blade mask across leaf surface
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-600, 100)
    noise.inputs['Scale'].default_value = float(np.random.uniform(8.0, 20.0))
    noise.inputs['Detail'].default_value = 6.0
    links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])

    # Color ramp: vein color -> blade color (matches vein_color_mix_factor blend)
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (-350, 100)
    ramp.color_ramp.color_mode = 'HSV'
    ramp.color_ramp.hue_interpolation = 'NEAR'
    ramp.color_ramp.elements[0].position = max(0.0, 0.5 - 0.5 * vein_mix_factor)
    ramp.color_ramp.elements[0].color = vein_rgba
    ramp.color_ramp.elements[1].position = min(1.0, 0.5 + 0.5 * vein_mix_factor)
    ramp.color_ramp.elements[1].color = blade_rgba
    links.new(_fac_output(noise), ramp.inputs['Fac'])

    # Principled BSDF: matches shader_leaf_new Roughness branch
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (150, 250)
    bsdf.inputs['Roughness'].default_value = 0.5
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

    # Translucent BSDF for backlit leaves (matches leaf_v2 Translucent + mix)
    translucent = nodes.new('ShaderNodeBsdfTranslucent')
    translucent.location = (150, -50)
    links.new(ramp.outputs['Color'], translucent.inputs['Color'])

    mix_shader = nodes.new('ShaderNodeMixShader')
    mix_shader.location = (450, 100)
    # 0.7 matches the leaf_v2 Principled+Translucent mix factor
    mix_shader.inputs['Fac'].default_value = 0.7
    links.new(translucent.outputs[0], mix_shader.inputs[1])
    links.new(bsdf.outputs[0], mix_shader.inputs[2])
    links.new(mix_shader.outputs[0], output.inputs['Surface'])

    return mat


# order is: random_species -> trunk_surface (bark) -> season -> child leaf
# factory __init__ (which samples blade/vein colors). We replicate that
# consumption order here so the material sampling drains the raw-seed RNG
# identically; the geometry then re-seeds inside make_tree() via
# generate_tree_config() which already matches objects_blender/TreeFactory.

clear_scene()
random.seed(SEED)
np.random.seed(SEED)

# Mirror the base TreeFactory species/season picks for the material palette.
_tree_material_rng = np.random.RandomState(SEED)
TREE_SPECIES = _pick_species(_tree_material_rng)
TREE_SEASON = _pick_season(_tree_material_rng)

# Bark: weighted_sample over material_assignments.bark is consumed as an int;
# we just drain the RNG then sample bark HSV inside create_bark_material().
np.random.choice([0, 1], p=[0.1, 0.9])  # BarkBirch vs BarkRandom selection

BARK_MATERIAL = create_bark_material()
BARK_MATERIAL.use_fake_user = True

# Leaf: LeafFactoryBroadleaf.__init__ is called under FixedSeed and samples
# blade/vein HSV + vein_color_mix_factor. We replicate that sampling order.
LEAF_MATERIAL = create_leaf_material(TREE_SEASON)
LEAF_MATERIAL.use_fake_user = True


# ── Main entry point ──────────────────────────────────────────────────────────

def make_tree(seed=SEED, species=None, season=None):
    np.random.seed(seed)
    random.seed(seed)
    rng = np.random.RandomState(seed)

    if species is None:
        species = _pick_species(rng)
    if season is None:
        season = _pick_season(rng)

    if species == "pine":
        tree_config, spacecol_params, skinning_params, sz = generate_pine_config()
    elif species == "palm":
        tree_config, spacecol_params, skinning_params, sz = generate_palm_config()
    elif species == "baobab":
        tree_config, spacecol_params, skinning_params, sz = generate_baobab_config()
    elif species == "bamboo":
        tree_config, spacecol_params, skinning_params, sz = generate_bamboo_config()
    else:
        tree_config, spacecol_params, skinning_params, sz = generate_tree_config()

    scale = 0.35
    vtx = TreeVertices(np.array([[0.0, 0.0, 0.0]]))
    recursive_path(vtx, vtx.get_idxs(), level=0, **tree_config)

    if spacecol_params is not None:
        space_colonization(vtx, level=max(vtx.level) + 1, **spacecol_params)

    rev_depth = parse_tree_attributes(vtx)
    trunk_obj = skeleton_to_mesh(
        vtx, rev_depth, scale=scale,
        min_radius=skinning_params["min_radius"],
        max_radius=skinning_params["max_radius"],
        exponent=skinning_params["exponent"],
        scaling=skinning_params["scaling"],
        wobble=True,
        profile_res=20,
        subdivide=True,
    )

    trunk_n_faces = len(trunk_obj.data.polygons)

    leaf_type, leaf_density = _season_leaf_params(species, season, rng)
    canopy_obj = None
    if species == "palm":
        canopy_obj = _add_palm_fronds(trunk_obj, sz, scale, rng)
    elif species == "bamboo":
        canopy_obj = add_twigs_and_leaves(
            vtx, rev_depth, scale, seed,
            leaf_density=leaf_density, leaf_type=leaf_type,
            max_placements=120, placement_keep=0.18, outer_only_threshold=1.01,
        )
    else:
        if leaf_type in ("maple", "ginko"):
            mp, pk = 250, 0.35
        else:
            mp, pk = 400, 0.5
        canopy_obj = add_twigs_and_leaves(
            vtx, rev_depth, scale, seed,
            leaf_density=leaf_density, leaf_type=leaf_type,
            max_placements=mp, placement_keep=pk,
        )

    fruit_obj = None
    if season != "winter" and rng.random() < 0.35 and species in ("broadleaf", "ginko", "maple"):
        fruit_type = rng.choice(["apple", "durian", "starfruit", "coconutgreen"])
        fruit_obj = _add_fruits(vtx, rev_depth, scale, seed, fruit_type)

    trunk_obj.data.materials.append(BARK_MATERIAL)  # slot 0 = bark
    trunk_obj.data.materials.append(LEAF_MATERIAL)  # slot 1 = leaf

    for poly in trunk_obj.data.polygons:
        poly.material_index = 0

    parts = [trunk_obj]
    if canopy_obj is not None:
        canopy_obj.data.materials.append(LEAF_MATERIAL)
        for poly in canopy_obj.data.polygons:
            poly.material_index = 0
        parts.append(canopy_obj)

    if fruit_obj is not None:
        fruit_obj.data.materials.append(LEAF_MATERIAL)
        for poly in fruit_obj.data.polygons:
            poly.material_index = 0
        parts.append(fruit_obj)

    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = trunk_obj
    if len(parts) > 1:
        bpy.ops.object.join()

    result = bpy.context.active_object
    result.name = "TreeFactory"
    result["species"] = species
    result["season"] = season

    for i, poly in enumerate(result.data.polygons):
        poly.material_index = 0 if i < trunk_n_faces else 1

    bpy.ops.object.select_all(action="DESELECT")
    result.select_set(True)
    bpy.context.view_layer.objects.active = result
    bpy.ops.object.shade_smooth()

    return result


result = make_tree(SEED)
n_verts = len(result.data.vertices)
n_faces = len(result.data.polygons)
dims = result.dimensions
