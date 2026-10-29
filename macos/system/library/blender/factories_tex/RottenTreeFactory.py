# [FL_INDEX: keywords="blender_factory, procedural_3d, RottenTreeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: RottenTreeFactory | Category: factories_tex
# Prompt: A rotten dead tree rendered as a textured 3D model. The object depicts a bare, weathered tree with a short, dark brown-black trunk that shows extensive decay — the bark is rough, deeply fissured, and darkened with a mottled brown-black surface conveying rotting wood. Multiple bare branches extend upward from the trunk; two main primary branches shoot nearly vertically creating a distinctive pitchfork silhouette, with many secondary bare branches and fine twigs radiating outward. The entire structure is devoid of leaves. A large dramatic cast shadow spreads across the white background.

import math
import random
import sys
import warnings

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils import noise as mnoise

import os
SEED = int(os.environ.get("SEED", 0))
def sel_none():
    for obj in list(bpy.context.selected_objects):
        obj.select_set(False)


def set_active(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def apply_modifier(obj, mod):
    sel_none()
    set_active(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    sel_none()


def apply_transform(obj, location=False):
    sel_none()
    set_active(obj)
    bpy.ops.object.transform_apply(location=location, rotation=True, scale=True)
    sel_none()


def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                  bpy.data.textures, bpy.data.images):
        for item in list(block):
            block.remove(item)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)


# ---------------------------------------------------------------------------
# Tree skeleton -- space colonization
# ---------------------------------------------------------------------------

class TreeVertices:
    """Accumulates vertices, parent indices, and branch level for the skeleton."""


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
    """Rotate vector *v* around axis *k* by angle *theta* (Rodrigues)."""

    k = np.array(k, dtype=float)
    v = np.array(v, dtype=float)
    k_norm = np.linalg.norm(k)
    if k_norm < 1e-10:
        return v
    k = k / k_norm
    return (v * math.cos(theta)
            + np.cross(k, v) * math.sin(theta)
            + k * np.dot(k, v) * (1 - math.cos(theta)))


def rand_path(n_pts, sz=1, std=0.3, momentum=0.5, init_vec=None, init_pt=None,
              pull_dir=None, pull_init=1, pull_factor=0, sz_decay=1,
              decay_mom=True):
    """Generate a random walk path (trunk or branch centreline)."""

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


def get_spawn_pt(path, rng=None, ang_min=math.pi / 6,
                 ang_max=0.9 * math.pi / 2, rnd_idx=None,
                 ang_sign=None, axis2=None, init_vec=None, z_bias=0):
    """Pick a point along *path* and compute an outgoing branch direction."""

    if rng is None:
        rng = [0.5, 1]
    n = len(path)
    if n == 1:
        return 0, path[0], init_vec if init_vec is not None else np.array([0, 0, 1])

    if rnd_idx is None:
        lo = int(n * rng[0])
        hi = max(int(n * rng[1]), lo + 1)
        rnd_idx = np.random.randint(lo, hi)
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


def recursive_path(tree, parent_idxs, level, path_kargs=None,
                   spawn_kargs=None, n=1, symmetry=False, children=None):
    """Recursively grow branches off an existing skeleton path."""

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
            for child_cfg in children:
                recursive_path(tree, node_idxs, level + 1, **child_cfg)


# -- Distance computation for space colonization --

def compute_dists(atts, vtxs):
    diff = atts[:, None, :] - vtxs[None, :, :]
    dists = np.linalg.norm(diff, axis=2)
    return dists, diff


def space_colonization(tree, atts, D=0.1, d=10.0, s=0.1, pull_dir=None,
                       dir_rand=0.1, mag_rand=0.15, n_steps=200, level=0):
    """Grow the tree toward attractor points (space colonization algorithm)."""

    if callable(atts):
        atts = atts(tree.vtxs)

    curr_min = np.zeros(len(atts)) + d
    curr_match = -np.ones(len(atts), dtype=int)

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
            norms = np.linalg.norm(matched_deltas[:, n_idx, :], axis=1,
                                   keepdims=True)
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

        dists_new, deltas_new = compute_dists(atts, new_vtxs)
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


# -- DFS tree attributes --

def dfs_tree(idx, edge_ref, parents, depth, rev_depth, n_leaves, child_idx):
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
            dfs_tree(c, edge_ref, parents, depth, rev_depth, n_leaves,
                     child_idx)


def parse_tree_attributes(vtx):
    sys.setrecursionlimit(10000)
    n = len(vtx.vtxs)
    parents = np.zeros(n, dtype=int)
    depth = np.zeros(n, dtype=int)
    rev_depth = np.zeros(n, dtype=int)
    n_leaves = np.zeros(n, dtype=int)
    child_idx_arr = np.zeros(n, dtype=int)

    edge_ref = {i: [] for i in range(n)}
    for e in vtx.get_edges():
        v0, v1 = e
        edge_ref[v0].append(v1)
        edge_ref[v1].append(v0)

    dfs_tree(0, edge_ref, parents, depth, rev_depth, n_leaves, child_idx_arr)
    return rev_depth


def get_pts_from_shape_simple(n, scaling, pt_offset):
    """Sample random points inside a box (attractor cloud)."""

    scaling = np.array(scaling)
    pts = (np.random.rand(n, 3) - 0.5) * 2 * scaling + np.array(pt_offset)
    return pts


# ---------------------------------------------------------------------------
# Skeleton -> Mesh via GeoNodes
# ---------------------------------------------------------------------------

def skeleton_to_mesh(vtx, rev_depth, scale=0.35,
                     min_radius=0.02, max_radius=0.2, exponent=1.5,
                     profile_res=12):
    """Convert tree skeleton to tube mesh using GeoNodes pipeline.

    MeshToCurve -> SetCurveRadius -> CurveToMesh(CurveCircle) -> MergeByDistance.
    In Blender 5.0 SetCurveRadius does not affect CurveToMesh, so the computed
    radius is also fed into CurveToMesh's "Scale" input.
    """

    verts = vtx.vtxs * scale
    edges = vtx.get_edges()

    mesh_data = bpy.data.meshes.new("TreeSkeleton")
    mesh_data.from_pydata(verts.tolist(), edges.tolist(), [])
    mesh_data.update()

    obj = bpy.data.objects.new("TreeSkeleton", mesh_data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    # Store rev_depth as integer vertex attribute
    attr = mesh_data.attributes.new(name="rev_depth", type="INT",
                                    domain="POINT")
    attr.data.foreach_set("value", rev_depth.astype(int))

    # Normalized rev_depth as FLOAT (0 = tip, 1 = trunk base)
    max_rd = int(rev_depth.max()) if rev_depth.max() > 0 else 1
    norm_depth = rev_depth.astype(float) / max_rd
    attr_n = mesh_data.attributes.new(name="rev_depth_norm", type="FLOAT",
                                      domain="POINT")
    attr_n.data.foreach_set("value", norm_depth)

    # ---- Build GeoNodes modifier ----
    ng = bpy.data.node_groups.new("SetTreeRadius_Standalone",
                                  'GeometryNodeTree')

    in_sock = ng.interface.new_socket('Geometry', in_out='INPUT',
                                      socket_type='NodeSocketGeometry')
    ng.interface.move(in_sock, 0)
    ng.interface.new_socket('Geometry', in_out='OUTPUT',
                            socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    gi = nodes.new('NodeGroupInput')
    gi.location = (-800, 0)
    go = nodes.new('NodeGroupOutput')
    go.location = (800, 0)

    # MeshToCurve
    m2c = nodes.new('GeometryNodeMeshToCurve')
    m2c.location = (-600, 0)
    links.new(gi.outputs['Geometry'], m2c.inputs['Mesh'])

    # Named Attribute for normalised depth
    named_attr = nodes.new('GeometryNodeInputNamedAttribute')
    named_attr.location = (-600, -200)
    named_attr.data_type = 'FLOAT'
    named_attr.inputs['Name'].default_value = "rev_depth_norm"

    # Power node: norm_depth ^ exponent
    pow_node = nodes.new('ShaderNodeMath')
    pow_node.operation = 'POWER'
    pow_node.location = (-400, -200)
    links.new(named_attr.outputs[0], pow_node.inputs[0])
    pow_node.inputs[1].default_value = exponent

    # Multiply by (max_radius - min_radius)
    range_r = max_radius - min_radius
    mul_r = nodes.new('ShaderNodeMath')
    mul_r.operation = 'MULTIPLY'
    mul_r.location = (-200, -200)
    links.new(pow_node.outputs[0], mul_r.inputs[0])
    mul_r.inputs[1].default_value = range_r

    # Add min_radius
    add_r = nodes.new('ShaderNodeMath')
    add_r.operation = 'ADD'
    add_r.location = (0, -200)
    links.new(mul_r.outputs[0], add_r.inputs[0])
    add_r.inputs[1].default_value = min_radius

    # SetCurveRadius
    scr = nodes.new('GeometryNodeSetCurveRadius')
    scr.location = (-200, 0)
    links.new(m2c.outputs['Curve'], scr.inputs['Curve'])
    links.new(add_r.outputs[0], scr.inputs['Radius'])

    # CurveCircle (radius=1 -- actual size via Scale input)
    cc = nodes.new('GeometryNodeCurvePrimitiveCircle')
    cc.location = (0, -400)
    cc.inputs['Resolution'].default_value = profile_res
    cc.inputs['Radius'].default_value = 1.0

    # CurveToMesh -- pass radius into Scale for Blender 5.0 compat
    c2m = nodes.new('GeometryNodeCurveToMesh')
    c2m.location = (200, 0)
    links.new(scr.outputs['Curve'], c2m.inputs['Curve'])
    links.new(cc.outputs['Curve'], c2m.inputs['Profile Curve'])
    # Blender 5.0 has a "Scale" input; 4.x does not
    if 'Scale' in c2m.inputs:
        links.new(add_r.outputs[0], c2m.inputs['Scale'])
    c2m.inputs['Fill Caps'].default_value = True

    # MergeByDistance
    mbd = nodes.new('GeometryNodeMergeByDistance')
    mbd.location = (400, 0)
    links.new(c2m.outputs['Mesh'], mbd.inputs['Geometry'])
    mbd.inputs['Distance'].default_value = 0.001

    links.new(mbd.outputs['Geometry'], go.inputs['Geometry'])

    # Apply modifier
    mod = obj.modifiers.new("TreeRadius", 'NODES')
    mod.node_group = ng

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    return obj


# ---------------------------------------------------------------------------
# Tree config generation
# ---------------------------------------------------------------------------

def generate_tree_config():
    sz = np.random.uniform(12, 22)
    n_tree_pts = int(sz)
    trunk_std = np.random.uniform(0.15, 0.45)
    trunk_mtm = np.clip(0.70 + np.random.randn() * 0.10, 0.50, 0.92)

    # --- Level 3: sub-sub-branches (twigs) ---
    sub_sub_config = {
        "n": np.random.randint(2, 4),
        "path_kargs": lambda idx: {
            "n_pts": max(2, int(n_tree_pts * np.random.uniform(0.10, 0.20))),
            "sz": 1,
            "std": 0.8,
            "momentum": 0.30,
            "pull_dir": [0, 0, np.random.rand() * 0.15 - 0.05],  # slight droop
            "pull_factor": np.random.rand() * 0.15,
        },
        "spawn_kargs": lambda idx: {
            "rng": [0.3, 0.9],
            "ang_min": math.pi / 4,
            "ang_max": math.pi / 4 + math.pi / 16,
        },
    }

    # --- Level 2: sub-branches ---
    sub_branch_config = {
        "n": np.random.randint(3, 6),
        "path_kargs": lambda idx: {
            "n_pts": max(3, int(n_tree_pts * np.random.uniform(0.15, 0.30))),
            "sz": 1,
            "std": 1.0,
            "momentum": 0.35,
            "pull_dir": [0, 0, np.random.rand() * 0.3],
            "pull_factor": np.random.rand() * 0.3,
        },
        "spawn_kargs": lambda idx: {
            "rng": [0.25, 0.85],
            "ang_min": math.pi / 5,
            "ang_max": math.pi / 3,
        },
        "children": [sub_sub_config],
    }

    # --- Level 1: main branches ---
    n_main = np.random.randint(5, 10)
    avail_idxs = np.arange(n_tree_pts)
    start_idx = 1 + int(n_tree_pts * np.random.uniform(0.35, 0.65))
    sample_density = max(1, (n_tree_pts - start_idx) // max(n_main, 1))
    avail_idxs = avail_idxs[start_idx::max(1, sample_density)][:n_main]

    branch_config = {
        "n": len(avail_idxs),
        "path_kargs": lambda idx: {
            "n_pts": max(4, int(n_tree_pts * np.random.uniform(0.30, 0.55))),
            "sz": 1,
            "std": 1.4,
            "momentum": 0.40,
            "pull_dir": [0, 0, np.random.rand() * 0.4],
            "pull_factor": np.random.rand() * 0.5,
        },
        "spawn_kargs": lambda idx, _ai=avail_idxs: {
            "rnd_idx": _ai[min(idx, len(_ai) - 1)],
            "ang_min": math.pi / 4,
            "ang_max": math.pi / 4 + math.pi / 16,
        },
        "children": [sub_branch_config],
    }

    # --- Level 0: trunk ---
    tree_config = {
        "n": 1,
        "path_kargs": lambda idx: {
            "n_pts": n_tree_pts,
            "sz": 1,
            "std": trunk_std,
            "momentum": trunk_mtm,
            "pull_dir": [0, 0, 0],
        },
        "spawn_kargs": lambda idx: {"init_vec": [0, 0, 1]},
        "children": [branch_config],
    }

    # --- Space colonization: 8-15 steps for crown density ---
    start_ht = sz * (start_idx / n_tree_pts)
    box_ht = (sz - start_ht) * 0.5

    def att_fn(nodes):
        return get_pts_from_shape_simple(
            120, [sz / 3, sz / 3, box_ht], [0, 0, start_ht + sz * 0.35]
        )

    step_dist = 0.30 + 0.20 * (sz / 30)
    spacecol_params = {
        "atts": att_fn,
        "D": step_dist,
        "s": step_dist * 1.3,
        "d": 10,
        "pull_dir": [0, 0, np.random.randn() * 0.3],
        "n_steps": np.random.randint(8, 15),
    }

    skinning_params = {
        "min_radius": 0.015,
        "max_radius": 0.30,
        "exponent": np.random.uniform(1.6, 2.2),
    }

    return tree_config, spacecol_params, skinning_params, sz


# ---------------------------------------------------------------------------
# Build tree (skeleton -> mesh)
# ---------------------------------------------------------------------------

def make_tree(seed):
    """Build a full tree mesh from skeleton (no leaves/twigs)."""

    np.random.seed(seed)
    random.seed(seed)

    tree_cfg, spacecol_params, skinning_params, tree_sz = generate_tree_config()

    vtx = TreeVertices(np.array([[0.0, 0.0, 0.0]]))
    recursive_path(vtx, vtx.get_idxs(), level=0, **tree_cfg)
    space_colonization(vtx, **spacecol_params)

    rev_depth = parse_tree_attributes(vtx)

    obj = skeleton_to_mesh(
        vtx, rev_depth,
        scale=0.35,
        min_radius=skinning_params["min_radius"],
        max_radius=skinning_params["max_radius"],
        exponent=skinning_params["exponent"],
        profile_res=12,
    )
    return obj


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def create_bark_material(base_hue=None):
    if base_hue is None:
        base_hue = np.random.uniform(0.02, 0.08)

    mat = bpy.data.materials.new("BarkMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value = 0.85
    links.new(bsdf.outputs[0], output.inputs[0])

    # Texture coordinate (Object space)
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)

    # --- Color: Noise-based bark color variation ---
    noise_col = nodes.new('ShaderNodeTexNoise')
    noise_col.location = (-400, 200)
    noise_col.inputs['Scale'].default_value = np.random.uniform(8, 15)
    noise_col.inputs['Detail'].default_value = 6.0
    links.new(tex_coord.outputs['Object'], noise_col.inputs['Vector'])

    # Dark bark color
    import colorsys
    dark_r, dark_g, dark_b = colorsys.hsv_to_rgb(
        base_hue, np.random.uniform(0.5, 0.8), np.random.uniform(0.10, 0.22))
    # Bright bark color
    bright_r, bright_g, bright_b = colorsys.hsv_to_rgb(
        base_hue, np.random.uniform(0.4, 0.7), np.random.uniform(0.35, 0.65))

    mix_col = nodes.new('ShaderNodeMix')
    mix_col.location = (0, 200)
    mix_col.data_type = 'RGBA'
    mix_col.inputs[6].default_value = (dark_r, dark_g, dark_b, 1)    # A
    mix_col.inputs[7].default_value = (bright_r, bright_g, bright_b, 1)  # B
    links.new(noise_col.outputs[0], mix_col.inputs[0])  # Factor
    links.new(mix_col.outputs[2], bsdf.inputs['Base Color'])

    # --- Bump: multi-scale noise for bark texture ---
    # Large-scale bark ridges
    noise_bump1 = nodes.new('ShaderNodeTexNoise')
    noise_bump1.location = (-400, -100)
    noise_bump1.inputs['Scale'].default_value = np.random.uniform(15, 25)
    noise_bump1.inputs['Detail'].default_value = 8.0
    noise_bump1.inputs['Roughness'].default_value = 0.7
    links.new(tex_coord.outputs['Object'], noise_bump1.inputs['Vector'])

    bump1 = nodes.new('ShaderNodeBump')
    bump1.location = (0, -100)
    bump1.inputs['Strength'].default_value = 0.4
    bump1.inputs['Distance'].default_value = 0.02
    links.new(noise_bump1.outputs[0], bump1.inputs['Height'])

    # Fine-scale bark detail
    noise_bump2 = nodes.new('ShaderNodeTexNoise')
    noise_bump2.location = (-400, -300)
    noise_bump2.inputs['Scale'].default_value = np.random.uniform(40, 80)
    noise_bump2.inputs['Detail'].default_value = 4.0
    links.new(tex_coord.outputs['Object'], noise_bump2.inputs['Vector'])

    bump2 = nodes.new('ShaderNodeBump')
    bump2.location = (0, -300)
    bump2.inputs['Strength'].default_value = 0.15
    bump2.inputs['Distance'].default_value = 0.005
    links.new(noise_bump2.outputs[0], bump2.inputs['Height'])
    links.new(bump1.outputs[0], bump2.inputs['Normal'])

    links.new(bump2.outputs[0], bsdf.inputs['Normal'])

    return mat


def create_ring_material(base_hue=None):
    if base_hue is None:
        base_hue = np.random.uniform(0.02, 0.08)

    mat = bpy.data.materials.new("RingMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value = 0.75
    links.new(bsdf.outputs[0], output.inputs[0])

    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)

    wave = nodes.new('ShaderNodeTexWave')
    wave.location = (-200, 0)
    wave.wave_type = 'RINGS'
    wave.rings_direction = 'Z'
    wave.wave_profile = 'SAW'
    wave.inputs['Scale'].default_value = np.random.uniform(10, 20)
    wave.inputs['Distortion'].default_value = np.random.uniform(4, 10)
    links.new(tex_coord.outputs['Object'], wave.inputs['Vector'])

    # Dark ring color
    import colorsys
    dark_r, dark_g, dark_b = colorsys.hsv_to_rgb(
        (base_hue + np.random.uniform(-0.02, 0.02)) % 1,
        np.random.uniform(0.4, 0.8),
        np.random.uniform(0.02, 0.05))
    # Bright ring color
    bright_r, bright_g, bright_b = colorsys.hsv_to_rgb(
        base_hue, np.random.uniform(0.4, 0.8), np.random.uniform(0.2, 0.6))

    mix_col = nodes.new('ShaderNodeMix')
    mix_col.location = (100, 0)
    mix_col.data_type = 'RGBA'
    mix_col.inputs[6].default_value = (dark_r, dark_g, dark_b, 1)
    mix_col.inputs[7].default_value = (bright_r, bright_g, bright_b, 1)
    links.new(wave.outputs['Color'], mix_col.inputs[0])
    links.new(mix_col.outputs[2], bsdf.inputs['Base Color'])

    return mat


def apply_voxel_remesh(obj, voxel_size=0.030):
    """Voxel remesh only (no displacement) — needed for boolean to work."""

    sel_none()
    set_active(obj)
    obj.data.remesh_voxel_size = voxel_size
    obj.data.remesh_voxel_adaptivity = 0
    bpy.ops.object.voxel_remesh()
    return obj


def apply_bark_displacement(obj, voxel_size=0.030,
                            musgrave_strength=0.035,
                            clouds_strength=0.015):
    """Voxel remesh then displace along normals with noise textures.

    Used when bark needs to be geometric (e.g., before boolean cuts).
    """

    sel_none()
    set_active(obj)

    # Voxel remesh
    obj.data.remesh_voxel_size = voxel_size
    obj.data.remesh_voxel_adaptivity = 0
    bpy.ops.object.voxel_remesh()

    # --- Musgrave displacement for broad bark ridges ---
    tex_musgrave = bpy.data.textures.new("BarkMusgrave", type="MUSGRAVE")
    tex_musgrave.noise_scale = 0.12

    mod_musgrave = obj.modifiers.new("BarkMusgrave", 'DISPLACE')
    mod_musgrave.texture = tex_musgrave
    mod_musgrave.strength = musgrave_strength
    mod_musgrave.direction = 'NORMAL'
    mod_musgrave.texture_coords = 'LOCAL'
    apply_modifier(obj, mod_musgrave)

    # --- Clouds displacement ---
    tex_clouds = bpy.data.textures.new("BarkClouds", type="CLOUDS")
    tex_clouds.noise_scale = 0.06
    tex_clouds.noise_depth = 3

    mod_clouds = obj.modifiers.new("BarkClouds", 'DISPLACE')
    mod_clouds.texture = tex_clouds
    mod_clouds.strength = clouds_strength
    mod_clouds.direction = 'NORMAL'
    mod_clouds.texture_coords = 'LOCAL'
    apply_modifier(obj, mod_clouds)

    return obj


# ---------------------------------------------------------------------------
# Cavity cutter creation
# ---------------------------------------------------------------------------

def create_cavity_cutter(trunk_radius, height):
    angle = np.random.uniform(-math.pi, 0)
    depth = trunk_radius * np.random.uniform(0.4, 0.9)

    # log_uniform(lo, hi) = exp(uniform(log(lo), log(hi)))
    log_lo, log_hi = math.log(1.0), math.log(1.2)
    cutter_scale = np.array([
        trunk_radius * np.random.uniform(0.8, 1.2),
        trunk_radius * np.random.uniform(0.8, 1.2),
        math.exp(np.random.uniform(log_lo, log_hi)),
    ])

    cutter_location = np.array([
        depth * math.cos(angle),
        depth * math.sin(angle),
        height,
    ])

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=6, radius=1.0,
        location=(0, 0, 0),
    )
    cutter = bpy.context.active_object
    cutter.name = "CavityCutter"
    # Set object-level scale/location (DO NOT apply_transform —
    cutter.scale = tuple(cutter_scale)
    cutter.location = tuple(cutter_location)

    return cutter, cutter_location, cutter_scale


# ---------------------------------------------------------------------------
# Splinter tubes at cavity rim
# ---------------------------------------------------------------------------

def build_splinter_tubes(obj, cutter_location, cutter_scale, trunk_radius):
    """Create NURBS tube splinters at the cavity rim for torn-wood effect.

    These are added as separate mesh objects, joined with the tree, and go
    through the same boolean cut -- portions inside the cutter are removed,
    leaving only the protruding splinter stubs.
    """

    center = np.asarray(cutter_location, dtype=float)
    scale = np.asarray(cutter_scale, dtype=float)

    cavity_dir_angle = math.atan2(center[1], center[0])
    cutter_top_z = center[2] + scale[2]
    cutter_bot_z = center[2] - scale[2]

    splinter_objs = []

    # --- Upward splinters (torn fibers pointing up) ---
    n_up = np.random.randint(6, 12)
    for i in range(n_up):
        ang_offset = np.random.uniform(-1.4, 1.4)
        ang = cavity_dir_angle + ang_offset

        surface_x = trunk_radius * math.cos(ang) * np.random.uniform(0.85, 1.05)
        surface_y = trunk_radius * math.sin(ang) * np.random.uniform(0.85, 1.05)
        base_z = cutter_top_z - scale[2] * np.random.uniform(0.2, 0.7)

        # Mix of tall and shorter splinters
        if np.random.uniform() < 0.4:
            splinter_height = np.random.uniform(0.3, 0.6)
            splinter_radius = np.random.uniform(0.012, 0.025)
        else:
            splinter_height = np.random.uniform(0.15, 0.35)
            splinter_radius = np.random.uniform(0.008, 0.018)

        # Outward lean
        lean_out = np.random.uniform(0.05, 0.25)
        lean_x = math.cos(ang) * lean_out
        lean_y = math.sin(ang) * lean_out

        n_pts = 6
        verts = []
        for j in range(n_pts):
            t = j / (n_pts - 1)
            px = surface_x + lean_x * t * splinter_height
            py = surface_y + lean_y * t * splinter_height
            pz = base_z + splinter_height * t
            verts.append((px, py, pz))

        # Taper from base to tip
        radii = [splinter_radius * max(0.15, 1.0 - 0.6 * (j / (n_pts - 1)))
                 for j in range(n_pts)]
        radii[-1] = splinter_radius * 0.05

        splinter_obj = _tube_from_verts(verts, radii, f"SplinterUp_{i:03d}")
        if splinter_obj is not None:
            splinter_objs.append(splinter_obj)

    # --- Downward splinters (hanging fibers at cavity bottom) ---
    n_down = np.random.randint(3, 7)
    for i in range(n_down):
        ang_offset = np.random.uniform(-1.2, 1.2)
        ang = cavity_dir_angle + ang_offset

        surface_x = trunk_radius * math.cos(ang) * np.random.uniform(0.88, 1.04)
        surface_y = trunk_radius * math.sin(ang) * np.random.uniform(0.88, 1.04)
        top_z = cutter_bot_z + scale[2] * np.random.uniform(0.2, 0.6)

        hang_length = np.random.uniform(0.10, 0.25)
        hang_radius = np.random.uniform(0.006, 0.015)
        lean_out = np.random.uniform(0.03, 0.15)

        n_pts = 5
        verts = []
        for j in range(n_pts):
            t = j / (n_pts - 1)
            px = surface_x + math.cos(ang) * lean_out * t * hang_length
            py = surface_y + math.sin(ang) * lean_out * t * hang_length
            pz = top_z - hang_length * t
            verts.append((px, py, pz))

        radii = [hang_radius * max(0.15, 1.0 - 0.5 * t)
                 for t in np.linspace(0, 1, n_pts)]
        radii[-1] = hang_radius * 0.06

        splinter_obj = _tube_from_verts(verts, radii, f"SplinterDown_{i:03d}")
        if splinter_obj is not None:
            splinter_objs.append(splinter_obj)

    return splinter_objs


def _tube_from_verts(verts, radii, name, segments=8):
    """Create a tube mesh from a polyline with per-point radii.

    Uses bmesh: at each polyline point a circle of vertices is placed
    perpendicular to the local direction, then adjacent rings are bridged.
    """

    if len(verts) < 2:
        return None

    points = [np.array(v, dtype=float) for v in verts]
    bm = bmesh.new()

    rings = []
    for idx in range(len(points)):
        pos = points[idx]
        radius = radii[idx] if idx < len(radii) else radii[-1]

        # Local direction
        if idx == 0:
            direction = points[1] - points[0]
        elif idx == len(points) - 1:
            direction = points[-1] - points[-2]
        else:
            direction = points[idx + 1] - points[idx - 1]
        d_norm = np.linalg.norm(direction)
        if d_norm < 1e-10:
            direction = np.array([0, 0, 1])
        else:
            direction = direction / d_norm

        # Build orthonormal basis
        up = np.array([0, 0, 1]) if abs(direction[2]) < 0.9 else np.array([0, 1, 0])
        tangent = np.cross(direction, up)
        t_norm = np.linalg.norm(tangent)
        if t_norm < 1e-10:
            tangent = np.array([1, 0, 0])
        else:
            tangent = tangent / t_norm
        bitangent = np.cross(direction, tangent)

        ring = []
        for s in range(segments):
            theta = 2.0 * math.pi * s / segments
            offset = (math.cos(theta) * tangent + math.sin(theta) * bitangent) * radius
            vert = bm.verts.new(pos + offset)
            ring.append(vert)
        rings.append(ring)

    # Bridge adjacent rings with faces
    for ring_idx in range(len(rings) - 1):
        ring_a = rings[ring_idx]
        ring_b = rings[ring_idx + 1]
        for s in range(segments):
            s_next = (s + 1) % segments
            bm.faces.new([ring_a[s], ring_a[s_next], ring_b[s_next], ring_b[s]])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# Fiber texture displacement on cavity interior
# ---------------------------------------------------------------------------

def add_fiber_texture(obj, cutter_location, cutter_scale,
                      strength_override=None, scale_override=None):
    center = np.asarray(cutter_location, dtype=float)
    scl = np.asarray(cutter_scale, dtype=float)

    noise_scale = scale_override if scale_override is not None else np.random.uniform(10.0, 15.0)
    strength = strength_override if strength_override is not None else scl[2] * np.random.uniform(0.5, 0.8)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.normal_update()

    for vert in bm.verts:
        pos = np.array(vert.co, dtype=float)

        # Selection: x²+y² < 1 (inside trunk base radius)
        if pos[0] ** 2 + pos[1] ** 2 >= 1.0:
            continue

        # Metric: normalized distance from cutter center
        rel = (pos - center) / np.maximum(scl, 1e-8)
        metric = np.linalg.norm(rel)

        # Curve anchors: (0,1), (1.02,1), (1.05,0), (2,0)
        # Full strength at metric < 1.02, linear fade to 0 at 1.05, zero beyond
        if metric <= 1.02:
            curve_val = 1.0
        elif metric <= 1.05:
            curve_val = 1.0 - (metric - 1.02) / 0.03
        else:
            continue  # zero beyond 1.05

        # 2D noise clamped to [0.3, 0.7]
        noise_co = Vector((pos[0] * noise_scale, pos[1] * noise_scale, 0.0))
        raw = mnoise.noise(noise_co)
        clamped = max(0.3, min(0.7, 0.5 + 0.5 * raw))

        offset = clamped * strength * curve_val
        sign = 1.0 if vert.normal.z > 0 else -1.0
        vert.co.z += sign * offset

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


# ---------------------------------------------------------------------------
# Connected component cleanup
# ---------------------------------------------------------------------------

def retain_largest_components(obj, keep_count=1, min_vertices=200):
    """Keep the largest connected component(s) and remove small fragments."""

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    visited = set()
    components = []
    for vert in bm.verts:
        if vert.index in visited:
            continue
        stack = [vert]
        comp = []
        visited.add(vert.index)
        while stack:
            node = stack.pop()
            comp.append(node)
            for edge in node.link_edges:
                other = edge.other_vert(node)
                if other.index not in visited:
                    visited.add(other.index)
                    stack.append(other)
        components.append(comp)

    components.sort(key=len, reverse=True)
    keep = set()
    kept = 0
    for comp in components:
        if kept < keep_count or len(comp) >= min_vertices:
            keep.update(v.index for v in comp)
            kept += 1
        else:
            break

    doomed = [v for v in bm.verts if v.index not in keep]
    if doomed:
        bmesh.ops.delete(bm, geom=doomed, context="VERTS")
        bm.to_mesh(obj.data)
        obj.data.update()
    bm.free()
    return obj


# ---------------------------------------------------------------------------
# Main: build rotten tree
# ---------------------------------------------------------------------------

def clone_object(obj):
    """Create a deep copy of the mesh object."""

    dup = obj.copy()
    dup.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(dup)
    return dup


def _remove_verts_by_metric(obj, cutter_location, cutter_scale, keep_outside):
    loc = np.asarray(cutter_location, dtype=float)
    scl = np.asarray(cutter_scale, dtype=float)
    scl = np.maximum(scl, 1e-8)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    to_delete = []
    for v in bm.verts:
        pos = np.array(v.co, dtype=float)
        metric = np.linalg.norm((pos - loc) / scl)
        if keep_outside and metric < 1.0001:
            to_delete.append(v)
        elif not keep_outside and metric > 1.0001:
            to_delete.append(v)

    if to_delete:
        bmesh.ops.delete(bm, geom=to_delete, context="VERTS")

    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()
    return obj


def build_rotten_tree(seed):
    np.random.seed(seed)
    random.seed(seed)

    clear_scene()

    # 1. Build the full tree mesh
    outer = make_tree(seed)

    # 2. Voxel remesh (needed for clean boolean cuts) — NO geometric displacement
    apply_voxel_remesh(outer, voxel_size=0.030)

    # Create materials
    base_hue = np.random.uniform(0.02, 0.08)
    bark_mat = create_bark_material(base_hue)
    ring_mat = create_ring_material(base_hue)

    # 3. Determine trunk radius from vertices near ground
    coords = read_co(outer)
    if len(coords) == 0:
        outer.name = "RottenTree"
        return outer

    ground_mask = coords[:, 2] < 0.1
    if ground_mask.any():
        trunk_radius = np.sqrt(
            coords[ground_mask, 0] ** 2 + coords[ground_mask, 1] ** 2
        ).max()
    else:
        trunk_radius = 0.2

    cavity_height = np.random.uniform(0.8, 1.6)
    cutter, cutter_location, cutter_scale = create_cavity_cutter(
        trunk_radius, cavity_height
    )

    # 4. Boolean DIFFERENCE (matching line 127)
    mod = outer.modifiers.new("BoolCavity", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    try:
        mod.solver = "FLOAT"
    except TypeError:
        mod.solver = "FAST"
    mod.object = cutter
    apply_modifier(outer, mod)

    # 5. Separate loose → keep largest (matching line 128)
    retain_largest_components(outer, keep_count=1, min_vertices=50)

    # 6. Clone for inner surface (matching line 129)
    inner = clone_object(outer)

    # 7-8. Split outer/inner by cutter metric (matching lines 130-131)
    _remove_verts_by_metric(outer, cutter_location, cutter_scale, keep_outside=True)
    _remove_verts_by_metric(inner, cutter_location, cutter_scale, keep_outside=False)

    # 9. Apply materials: bark shader on outer, ring shader on inner
    outer.data.materials.clear()
    outer.data.materials.append(bark_mat)
    inner.data.materials.clear()
    inner.data.materials.append(ring_mat)

    # 10. Join outer + inner (matching line 135)
    sel_none()
    outer.select_set(True)
    inner.select_set(True)
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.join()
    obj = bpy.context.active_object
    sel_none()

    # 11. Bridge edge loops (matching lines 136-139)
    set_active(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.bridge_edge_loops(
        number_cuts=10, interpolation="LINEAR"
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    sel_none()

    # 12. Cavity surface noise (matching lines 155-162: geo_cutter)
    #     noise_strength = cutter.scale[-1] * uniform(0.5, 0.8)
    noise_strength = cutter_scale[2] * np.random.uniform(0.5, 0.8)
    noise_scale = np.random.uniform(10, 15)
    add_fiber_texture(obj, cutter_location, cutter_scale,
                      strength_override=noise_strength,
                      scale_override=noise_scale)

    # Cleanup: delete cutter
    bpy.data.objects.remove(cutter, do_unlink=True)

    # 13. Retain largest + ground + smooth
    retain_largest_components(obj, keep_count=1, min_vertices=200)

    coords = read_co(obj)
    if len(coords) > 0:
        min_z = coords[:, 2].min()
        obj.location.z -= min_z
        apply_transform(obj, location=True)

    sel_none()
    set_active(obj)
    bpy.ops.object.shade_smooth()
    if hasattr(obj.data, "use_auto_smooth"):
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = math.radians(60.0)

    obj.name = "RottenTree"
    obj.data.name = "RottenTree"
    return obj


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

obj = build_rotten_tree(SEED)
