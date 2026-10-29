# [FL_INDEX: keywords="blender_factory, procedural_3d, TwigBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TwigBaseCoralFactory | Category: factories_geo
# Prompt: A white base mesh 3D model of a twig coral structure. The object shows the raw geometric skeleton of a twig coral — a dense central point from which many slender, smooth branches extend outward and upward in all directions, with each branch further splitting into finer sub-branches toward the tips. Without any texture or material color, the pure white geometry clearly exposes the intricate, low-growing branching network with an extremely complex cast shadow on the white background below.

import bpy
import numpy as np
import math
from scipy.interpolate import interp1d

np.random.seed(0)


# ═══════════════════════════════════════════════════════════════════════════════

def rodrigues_rot(vec, axis, angle):
    """Rodrigues' rotation formula (from trees/utils/helper.py)."""

    axis = axis / (np.linalg.norm(axis) + 1e-12)
    cs = np.cos(angle)
    sn = np.sin(angle)
    return vec * cs + sn * np.cross(axis, vec) + axis * np.dot(axis, vec) * (1 - cs)


def rand_path(
    n_pts, sz=1, std=0.3, momentum=0.5,
    init_vec=(0, 0, 1), init_pt=(0, 0, 0),
    pull_dir=None, pull_init=1, pull_factor=0,
    sz_decay=1, decay_mom=True,
):
    """Random path generator (exact port from trees/tree.py:196-237)."""

    init_vec = np.array(init_vec, dtype=float)
    if pull_dir is not None:
        pull_dir = np.array(pull_dir, dtype=float)
        init_vec += pull_init * pull_dir
    init_vec = init_vec / (np.linalg.norm(init_vec) + 1e-12)

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
            new_delta += pull_factor * pull_dir
        new_delta = (new_delta / (np.linalg.norm(new_delta) + 1e-12)) * prev_sz

        if decay_mom:
            tmp_momentum = 1 - (1 - momentum) * (i + 1) / n_pts
        else:
            tmp_momentum = momentum
        delta = prev_delta * tmp_momentum + new_delta * (1 - tmp_momentum)
        delta = (delta / (np.linalg.norm(delta) + 1e-12)) * sz * (sz_decay ** i)
        path[i] = path[i - 1] + delta

    return path


def get_spawn_pt(
    path, rng=(0.5, 1),
    ang_min=np.pi / 6, ang_max=0.9 * np.pi / 2,
    rnd_idx=None, ang_sign=None, axis2=None,
    init_vec=None, z_bias=0,
):
    """Compute spawn point on parent path (exact port from trees/tree.py:240-271)."""

    n = len(path)
    if n == 1:
        return 0, path[0], init_vec

    if rnd_idx is None:
        rnd_idx = np.random.randint(int(n * rng[0]), int(n * rng[1]))
    rnd_idx = min(rnd_idx, n - 1)

    if init_vec is None:
        curr_vec = path[rnd_idx] - path[max(0, rnd_idx - 1)]
        axis1 = np.array([curr_vec[1], -curr_vec[0], 0])
        if axis2 is None:
            axis2 = rodrigues_rot(curr_vec, axis1, np.pi / 2)
        if callable(axis2):
            axis2 = axis2()
        rnd_ang = np.random.rand() * (ang_max - ang_min) + ang_min
        if ang_sign is None:
            ang_sign = np.sign(np.random.randn())
        rnd_ang *= ang_sign
        init_vec = rodrigues_rot(curr_vec, axis2, rnd_ang)

    return rnd_idx, path[rnd_idx], init_vec


# ═══════════════════════════════════════════════════════════════════════════════
# FineTreeVertices (ported from trees/tree.py:495-538)
# ═══════════════════════════════════════════════════════════════════════════════

class TreeVertices:
    def __init__(self, vtxs=None, parent=None, level=None):
        if vtxs is None:
            vtxs = np.array([[0, 0, 0]])
        elif isinstance(vtxs, list):
            vtxs = np.array(vtxs)
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


class FineTreeVertices(TreeVertices):
    def __init__(self, vtxs=None, parent=None, level=None, radius_fn=None, resolution=1):
        super().__init__(vtxs, parent, level)
        self.resolution = resolution
        if radius_fn is None:
            def radius_fn(base_radius, size, resolution):
                return [1] * size
        self.radius_fn = radius_fn
        self.detailed_locations = [[0, 0, 0]]
        self.radius = [1]
        self.detailed_parents = [-1]

    def append(self, v, p, l=None):
        super().append(v, p, l)
        f = interp1d(
            np.arange(len(v) + 1),
            np.concatenate([self.vtxs[p[0]:p[0] + 1], v]),
            axis=0, kind="quadratic",
        )
        self.detailed_locations.extend(
            f(np.linspace(0, len(v), len(v) * self.resolution + 1))[1:]
        )
        base_radius = self.radius[p[0] * self.resolution]
        self.radius.extend(self.radius_fn(base_radius, len(v), self.resolution))
        self.detailed_parents.append(p[0] * self.resolution)
        self.detailed_parents.extend(
            np.arange(0, len(v) * self.resolution - 1)
            + len(self.detailed_parents) - 1
        )

    @property
    def edges(self):
        edges = np.stack(
            [np.arange(len(self.detailed_locations)),
             np.array(self.detailed_parents)], 1,
        )
        return edges[edges[:, 1] != -1]

    def fix_first(self):
        self.radius[0] = self.radius[1]


# ═══════════════════════════════════════════════════════════════════════════════
# recursive_path (ported from trees/tree.py:274-310)
# ═══════════════════════════════════════════════════════════════════════════════

def recursive_path(
    tree, parent_idxs, level,
    path_kargs=None, spawn_kargs=None,
    n=1, symmetry=False, children=None,
):
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


# ═══════════════════════════════════════════════════════════════════════════════
# build_radius_tree (ported from trees/tree.py:541-552)
# ═══════════════════════════════════════════════════════════════════════════════

def build_radius_tree(radius_fn, branch_config, base_radius=0.002, resolution=1):
    vtx = FineTreeVertices(
        np.zeros((1, 3)), radius_fn=radius_fn, resolution=resolution
    )
    recursive_path(vtx, vtx.get_idxs(), level=0, **branch_config)

    # Create mesh from detailed locations and edges
    locations = np.array(vtx.detailed_locations)
    edges = vtx.edges

    mesh = bpy.data.meshes.new("tree_skeleton")
    mesh.from_pydata(locations.tolist(), edges.tolist(), [])
    mesh.update()

    obj = bpy.data.objects.new("tree_skeleton", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Create "radius" vertex group
    vg = obj.vertex_groups.new(name="radius")
    for i, r in enumerate(vtx.radius):
        vg.add([i], base_radius * r, "REPLACE")

    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# radius_fn (from corals/tree.py:172-182)
# ═══════════════════════════════════════════════════════════════════════════════

def radius_fn(base_radius, size, resolution):
    radius_decay_root = 0.85
    radius_decay_leaf = np.random.uniform(0.4, 0.6)
    radius = base_radius * radius_decay_root ** (
        np.arange(size * resolution) / resolution
    )
    radius[-resolution:] *= radius_decay_leaf ** (
        np.arange(resolution) / resolution
    )
    return radius


# ═══════════════════════════════════════════════════════════════════════════════
# twig_config (from corals/tree.py:109-170)
# ═══════════════════════════════════════════════════════════════════════════════

n_branch = np.random.randint(6, 8)
n_major = np.random.randint(4, 5)
n_minor = np.random.randint(4, 5)
n_detail = np.random.randint(3, 4)
span = np.random.uniform(0.7, 0.8)

detail_config = {
    "n": n_minor,
    "path_kargs": lambda idx: {
        "n_pts": n_detail * 2 + 1,
        "std": 0.4,
        "momentum": 0.6,
        "sz": 0.01 * (2.5 * n_detail - idx),
    },
    "spawn_kargs": lambda idx: {
        "rnd_idx": 2 * idx + 1,
        "ang_min": np.pi / 8,
        "ang_max": np.pi / 6,
        "axis2": [0, 0, 1],
    },
    "children": [],
}

minor_config = {
    "n": n_major,
    "path_kargs": lambda idx: {
        "n_pts": n_minor * 2 + 1,
        "std": 0.4,
        "momentum": 0.4,
        "sz": 0.03 * (2.2 * n_minor - idx),
    },
    "spawn_kargs": lambda idx: {
        "rnd_idx": 2 * idx + 1,
        "ang_min": np.pi / 8,
        "ang_max": np.pi / 6,
        "axis2": [0, 0, 1],
    },
    "children": [detail_config],
}

major_config = {
    "n": n_branch,
    "path_kargs": lambda idx: {
        "n_pts": n_major * 2 + 1,
        "std": 0.4,
        "momentum": 0.4,
        "sz": np.random.uniform(0.08, 0.1),
    },
    "spawn_kargs": lambda idx: {
        "init_vec": [
            span * np.cos(2 * np.pi * idx / n_branch + np.random.uniform(-np.pi / 9, np.pi / 9)),
            span * np.sin(2 * np.pi * idx / n_branch + np.random.uniform(-np.pi / 9, np.pi / 9)),
            math.sqrt(1 - span * span),
        ]
    },
    "children": [minor_config],
}

twig_config = major_config


# ═══════════════════════════════════════════════════════════════════════════════
# Build skeleton mesh
# ═══════════════════════════════════════════════════════════════════════════════

print("Building twig coral skeleton...")
obj = build_radius_tree(radius_fn, twig_config, base_radius=0.08, resolution=16)

# Scale to fit: 2 * default_scale / max(dimensions[:2])
max_xy = max(obj.dimensions[0], obj.dimensions[1], 1e-6)
scale_factor = 2.0 / max_xy
obj.scale = (scale_factor, scale_factor, scale_factor)
bpy.ops.object.transform_apply(scale=True)

print(f"Skeleton: {len(obj.data.vertices)} verts, {len(obj.data.edges)} edges")


# ═══════════════════════════════════════════════════════════════════════════════
# Apply geo_radius via Geometry Nodes
# (MeshToCurve → align_tilt → SetCurveRadius → CurveToMesh(32) → MergeByDistance)
# ═══════════════════════════════════════════════════════════════════════════════

ng = bpy.data.node_groups.new("geo_radius", 'GeometryNodeTree')

# Interface sockets
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

# Nodes
n_input = ng.nodes.new("NodeGroupInput")
n_output = ng.nodes.new("NodeGroupOutput")

# 1. MeshToCurve
n_mesh2curve = ng.nodes.new("GeometryNodeMeshToCurve")
ng.links.new(n_input.outputs["Geometry"], n_mesh2curve.inputs["Mesh"])

# 2. align_tilt: compute tilt to align cross-section to axis (0,0,1)
#    tilt = atan2(dot(cross(normal, axis_proj), tangent), dot(axis_proj, normal))
#    where axis_proj = normalize(axis - dot(axis, tangent) * tangent)
align_axis = (0, 0, 1)

# Get curve tangent and normal
n_tangent = ng.nodes.new("GeometryNodeInputTangent")
n_normal = ng.nodes.new("GeometryNodeInputNormal")

# Normalize tangent
n_norm_tangent = ng.nodes.new("ShaderNodeVectorMath")
n_norm_tangent.operation = "NORMALIZE"
ng.links.new(n_tangent.outputs[0], n_norm_tangent.inputs[0])

# axis constant
n_axis = ng.nodes.new("ShaderNodeVectorMath")
n_axis.operation = "NORMALIZE"
n_axis.inputs[0].default_value = align_axis

# dot(axis, tangent)
n_dot_at = ng.nodes.new("ShaderNodeVectorMath")
n_dot_at.operation = "DOT_PRODUCT"
ng.links.new(n_axis.outputs[0], n_dot_at.inputs[0])
ng.links.new(n_norm_tangent.outputs[0], n_dot_at.inputs[1])

# axis - dot(axis, tangent) * tangent  =>  SCALE tangent by dot, then SUBTRACT
n_scale_t = ng.nodes.new("ShaderNodeVectorMath")
n_scale_t.operation = "SCALE"
ng.links.new(n_norm_tangent.outputs[0], n_scale_t.inputs[0])
ng.links.new(n_dot_at.outputs["Value"], n_scale_t.inputs["Scale"])

n_sub_axis = ng.nodes.new("ShaderNodeVectorMath")
n_sub_axis.operation = "SUBTRACT"
ng.links.new(n_axis.outputs[0], n_sub_axis.inputs[0])
ng.links.new(n_scale_t.outputs[0], n_sub_axis.inputs[1])

# normalize axis_proj
n_norm_axis = ng.nodes.new("ShaderNodeVectorMath")
n_norm_axis.operation = "NORMALIZE"
ng.links.new(n_sub_axis.outputs[0], n_norm_axis.inputs[0])

# cos = dot(axis_proj, normal)
n_cos = ng.nodes.new("ShaderNodeVectorMath")
n_cos.operation = "DOT_PRODUCT"
ng.links.new(n_norm_axis.outputs[0], n_cos.inputs[0])
ng.links.new(n_normal.outputs[0], n_cos.inputs[1])

# cross(normal, axis_proj)
n_cross = ng.nodes.new("ShaderNodeVectorMath")
n_cross.operation = "CROSS_PRODUCT"
ng.links.new(n_normal.outputs[0], n_cross.inputs[0])
ng.links.new(n_norm_axis.outputs[0], n_cross.inputs[1])

# sin = dot(cross_result, tangent)
n_sin = ng.nodes.new("ShaderNodeVectorMath")
n_sin.operation = "DOT_PRODUCT"
ng.links.new(n_cross.outputs[0], n_sin.inputs[0])
ng.links.new(n_norm_tangent.outputs[0], n_sin.inputs[1])

# tilt = atan2(sin, cos)
n_atan2 = ng.nodes.new("ShaderNodeMath")
n_atan2.operation = "ARCTAN2"
ng.links.new(n_sin.outputs["Value"], n_atan2.inputs[0])
ng.links.new(n_cos.outputs["Value"], n_atan2.inputs[1])

# SetCurveTilt
n_set_tilt = ng.nodes.new("GeometryNodeSetCurveTilt")
ng.links.new(n_mesh2curve.outputs[0], n_set_tilt.inputs["Curve"])
ng.links.new(n_atan2.outputs[0], n_set_tilt.inputs["Tilt"])

# 3. Read "radius" named attribute → SetCurveRadius
n_named_attr = ng.nodes.new("GeometryNodeInputNamedAttribute")
n_named_attr.data_type = "FLOAT"
n_named_attr.inputs["Name"].default_value = "radius"

n_set_radius = ng.nodes.new("GeometryNodeSetCurveRadius")
ng.links.new(n_set_tilt.outputs[0], n_set_radius.inputs["Curve"])
# Connect the Float output (index depends on data_type=FLOAT → output index 1 in some versions)
# Use the named output "Attribute" which is the first non-Exists output
for out in n_named_attr.outputs:
    if out.type == 'VALUE':
        ng.links.new(out, n_set_radius.inputs["Radius"])
        break

# 4. CurveCircle(32)
n_circle = ng.nodes.new("GeometryNodeCurvePrimitiveCircle")
n_circle.inputs["Resolution"].default_value = 32

# 5. CurveToMesh — Blender 5.0: SetCurveRadius no longer affects CurveToMesh,
#    must pass radius as "Scale" input
n_curve2mesh = ng.nodes.new("GeometryNodeCurveToMesh")
ng.links.new(n_set_radius.outputs[0], n_curve2mesh.inputs["Curve"])
ng.links.new(n_circle.outputs[0], n_curve2mesh.inputs["Profile Curve"])
# Connect radius to Scale input for Blender 5.0+
n_named_attr2 = ng.nodes.new("GeometryNodeInputNamedAttribute")
n_named_attr2.data_type = "FLOAT"
n_named_attr2.inputs["Name"].default_value = "radius"
for out in n_named_attr2.outputs:
    if out.type == 'VALUE':
        try:
            ng.links.new(out, n_curve2mesh.inputs["Scale"])
        except Exception:
            pass  # Blender < 5.0 doesn't have Scale input
        break

# 6. MergeByDistance(0.004)
n_merge = ng.nodes.new("GeometryNodeMergeByDistance")
ng.links.new(n_curve2mesh.outputs[0], n_merge.inputs["Geometry"])
n_merge.inputs["Distance"].default_value = 0.004

# Output
ng.links.new(n_merge.outputs[0], n_output.inputs["Geometry"])

# Apply the GeoNodes modifier
mod = obj.modifiers.new("geo_radius", 'NODES')
mod.node_group = ng

print("Applying geo_radius modifier...")
bpy.ops.object.modifier_apply(modifier="geo_radius")

# Set origin
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

obj.name = "TwigBaseCoralFactory"
print(f"Done: TwigBaseCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
