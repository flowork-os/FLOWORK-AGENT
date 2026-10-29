# [FL_INDEX: keywords="blender_factory, procedural_3d, BushBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BushBaseCoralFactory | Category: factories_geo
# Prompt: A white base mesh 3D model of a bush-type branching coral. The object displays the raw geometric skeleton of a bush coral — multiple thick branches radiate outward from a central junction point, extending in various directions with a complex, low-lying spread. Rendered without any material color or texture, the pure white geometry reveals the branching topology and the irregular organic silhouette, with a sharp shadow beneath highlighting the structure against the white background.

import bpy
import numpy as np
import math

np.random.seed(0)

# ── Branch config (bush variant) ─────────────────────────────────────────────
n_branch = np.random.randint(6, 8)
n_major  = np.random.randint(4, 5)
n_minor  = np.random.randint(4, 5)
n_detail = np.random.randint(3, 4)
span     = np.random.uniform(0.4, 0.5)

base_radius = 0.05
resolution  = 8  # interpolation factor per control-point interval


# ── Quadratic interpolation (replaces scipy.interpolate.interp1d) ────────────

def quadratic_interp(points, res):
    """Piecewise-quadratic interpolation of 3-D control points.

    Given *N* control points at integer positions 0 … N-1, returns
    (N-1)*res + 1 smoothly interpolated positions using Lagrange quadratic
    polynomials – the same behaviour as
    ``scipy.interpolate.interp1d(kind='quadratic')``.
    """

    N = len(points)
    if N < 2:
        return points.copy()
    if N == 2:
        t = np.linspace(0, 1, res + 1)[:, None]
        return points[0] * (1 - t) + points[1] * t

    out_n = (N - 1) * res + 1
    fine_t = np.linspace(0, N - 1, out_n)
    result = np.empty((out_n, points.shape[1]))

    for k in range(out_n):
        t = fine_t[k]
        i = min(int(t), N - 2)
        # pick 3 neighbouring points for the Lagrange basis
        if i == 0:
            i0, i1, i2 = 0, 1, 2
        elif i >= N - 2:
            i0, i1, i2 = N - 3, N - 2, N - 1
        else:
            i0, i1, i2 = i - 1, i, i + 1
        t0, t1, t2 = float(i0), float(i1), float(i2)
        L0 = (t - t1) * (t - t2) / ((t0 - t1) * (t0 - t2))
        L1 = (t - t0) * (t - t2) / ((t1 - t0) * (t1 - t2))
        L2 = (t - t0) * (t - t1) / ((t2 - t0) * (t2 - t1))
        result[k] = points[i0] * L0 + points[i1] * L1 + points[i2] * L2

    return result


# ── Radius function ──────────────────────────────────────────────────────────

def radius_fn(base_r, size, res):
    """Exponential decay with leaf taper. Decay rate 0.88 keeps branches thicker."""

    decay_root = 0.88
    decay_leaf = np.random.uniform(0.45, 0.65)
    n = size * res
    r = base_r * decay_root ** (np.arange(n) / res)
    r[-res:] *= decay_leaf ** (np.arange(res) / res)
    return r


# ── Path generation (matches original rand_path with decay_mom) ──────────────

def rand_path(n_pts, init_vec, std=0.4, momentum=0.5, sz=0.05, sz_decay=1.0,
              pull_up=0.0):
    """Random walk with decaying momentum — branches curve more toward tips.
    pull_up adds a slight upward bias to every step."""

    init_vec = np.array(init_vec, dtype=float)
    init_vec = init_vec / (np.linalg.norm(init_vec) + 1e-8)

    path = np.zeros((n_pts, 3))
    for i in range(1, n_pts):
        if i == 1:
            prev_delta = init_vec * sz
        else:
            prev_delta = path[i - 1] - path[i - 2]

        prev_sz = np.linalg.norm(prev_delta) + 1e-8
        new_delta = prev_delta + np.random.randn(3) * std
        if pull_up > 0:
            new_delta[2] += pull_up * sz  # upward bias
        new_delta = (new_delta / (np.linalg.norm(new_delta) + 1e-8)) * prev_sz

        # Momentum decays toward tip (original: decay_mom=True)
        tmp_mom = 1 - (1 - momentum) * (i + 1) / n_pts
        delta = prev_delta * tmp_mom + new_delta * (1 - tmp_mom)
        delta = (delta / (np.linalg.norm(delta) + 1e-8)) * sz * (sz_decay ** i)
        path[i] = path[i - 1] + delta

    return path


# ── Rodrigues rotation (for proper spawn directions) ─────────────────────────

def rodrigues_rot(v, axis, angle):
    """Rotate vector *v* around *axis* by *angle* radians."""

    axis = axis / (np.linalg.norm(axis) + 1e-8)
    c, s = math.cos(angle), math.sin(angle)
    return v * c + np.cross(axis, v) * s + axis * np.dot(axis, v) * (1 - c)


def get_spawn_direction(path, idx, ang_min, ang_max):
    """Compute a child-branch initial direction by rotating the parent tangent."""

    if idx < 1:
        idx = 1
    curr_vec = path[idx] - path[idx - 1]
    norm = np.linalg.norm(curr_vec)
    if norm < 1e-10:
        curr_vec = np.array([0, 0, 1.0])
    # perpendicular axis in XY plane
    axis1 = np.array([curr_vec[1], -curr_vec[0], 0.0])
    if np.linalg.norm(axis1) < 1e-10:
        axis1 = np.array([1.0, 0, 0])
    axis2 = np.array([0.0, 0.0, 1.0])
    rnd_ang = np.random.uniform(ang_min, ang_max)
    rnd_ang *= np.sign(np.random.randn())
    return rodrigues_rot(curr_vec, axis2, rnd_ang)


# ── Swept tube mesh builder ──────────────────────────────────────────────────

def swept_tube(path, radii, n_ring=6):
    N = len(path)
    all_verts = []
    for i in range(N):
        pt, r = path[i], radii[min(i, len(radii) - 1)]
        if i == 0:
            tangent = path[1] - path[0]
        elif i == N - 1:
            tangent = path[-1] - path[-2]
        else:
            tangent = path[i + 1] - path[i - 1]
        tn = np.linalg.norm(tangent)
        if tn < 1e-10:
            tangent = np.array([0.0, 0.0, 1.0])
        else:
            tangent /= tn
        ref = np.array([0.0, 0, 1]) if abs(tangent[2]) < 0.9 else np.array([1.0, 0, 0])
        nx = np.cross(ref, tangent)
        nx /= np.linalg.norm(nx) + 1e-8
        ny = np.cross(tangent, nx)
        angles = np.linspace(0, 2 * np.pi, n_ring, endpoint=False)
        ring = pt + r * (np.cos(angles)[:, None] * nx + np.sin(angles)[:, None] * ny)
        all_verts.append(ring)
    verts = np.concatenate(all_verts, axis=0)
    faces = []
    for i in range(N - 1):
        for j in range(n_ring):
            a = i * n_ring + j
            b = i * n_ring + (j + 1) % n_ring
            c = (i + 1) * n_ring + (j + 1) % n_ring
            d = (i + 1) * n_ring + j
            faces.append([a, b, c, d])
    # tip cap
    tip_idx = len(verts)
    verts = np.vstack([verts, path[-1]])
    for j in range(n_ring):
        a = (N - 1) * n_ring + j
        b = (N - 1) * n_ring + (j + 1) % n_ring
        faces.append([a, b, tip_idx])
    return verts, faces


# ── Accumulator ──────────────────────────────────────────────────────────────

all_verts = []
all_faces = []
offset = 0


def add_branch(ctrl_pts, parent_pt, base_r, n_ring=6):
    """Interpolate control points, compute radii, emit swept tube."""

    global offset
    # Prepend parent point for smooth quadratic interpolation
    full_pts = np.vstack([parent_pt.reshape(1, 3), ctrl_pts])
    smooth = quadratic_interp(full_pts, resolution)
    # Skip the parent point itself (already part of parent branch)
    smooth = smooth[1:]

    n_ctrl = len(ctrl_pts)
    radii = radius_fn(base_r, n_ctrl, resolution)
    # Trim radii to match smooth path length
    radii = radii[: len(smooth)]

    v, f = swept_tube(smooth, radii, n_ring=n_ring)
    all_verts.append(v)
    all_faces.extend([[fi + offset for fi in face] for face in f])
    offset += len(v)


# ── Build the coral ──────────────────────────────────────────────────────────

# Trunk — short stub; branches emerge close to base
trunk_ctrl = rand_path(3, [0, 0, 1], std=0.2, momentum=0.7, sz=0.03)
add_branch(trunk_ctrl[1:], trunk_ctrl[0], base_radius, n_ring=6)

for b_idx in range(n_branch):
    # Major branches radiate from trunk — all attach near the base
    angle = 2 * np.pi * b_idx / n_branch + np.random.uniform(-np.pi / 9, np.pi / 9)
    init_vec = [
        span * math.cos(angle),
        span * math.sin(angle),
        math.sqrt(max(0, 1 - span * span)),
    ]
    # Attach near base of trunk (idx 1 or 2 out of 3 points)
    attach_idx = min(b_idx % 2 + 1, len(trunk_ctrl) - 1)
    attach_pt = trunk_ctrl[attach_idx]

    major_sz = np.random.uniform(0.08, 0.10)
    major_ctrl = rand_path(n_major + 2, init_vec, std=0.4, momentum=0.4, sz=major_sz)
    major_ctrl += attach_pt  # translate to attachment point
    add_branch(major_ctrl[1:], attach_pt, base_radius * 0.75, n_ring=6)

    for m_idx in range(n_major):
        # Minor branches spawn along major
        m_attach_idx = min(m_idx + 1, len(major_ctrl) - 1)
        m_attach_pt = major_ctrl[m_attach_idx]
        m_init_vec = get_spawn_direction(
            major_ctrl, m_attach_idx, np.pi / 12, np.pi / 8
        )

        sz_minor = 0.03 * (1.2 * n_minor - m_idx)
        sz_minor = max(sz_minor, 0.005)
        minor_ctrl = rand_path(
            n_minor + 1, m_init_vec, std=0.4, momentum=0.4, sz=sz_minor
        )
        minor_ctrl += m_attach_pt
        add_branch(minor_ctrl[1:], m_attach_pt, base_radius * 0.45, n_ring=5)

        for d_idx in range(n_minor):
            # Detail branches spawn along minor
            d_attach_idx = min(d_idx + 1, len(minor_ctrl) - 1)
            d_attach_pt = minor_ctrl[d_attach_idx]
            d_init_vec = get_spawn_direction(
                minor_ctrl, d_attach_idx, np.pi / 12, np.pi / 8
            )

            sz_detail = 0.01 * (1.5 * n_detail - d_idx)
            sz_detail = max(sz_detail, 0.003)
            det_ctrl = rand_path(
                n_detail + 1, d_init_vec, std=0.4, momentum=0.6, sz=sz_detail
            )
            det_ctrl += d_attach_pt
            add_branch(det_ctrl[1:], d_attach_pt, base_radius * 0.2, n_ring=4)


# ── Assemble mesh ────────────────────────────────────────────────────────────

verts = np.concatenate(all_verts, axis=0)
print(f"Bush coral raw: {len(verts)} verts, {len(all_faces)} faces")

mesh = bpy.data.meshes.new("BushBaseCoralFactory")
mesh.from_pydata(verts.tolist(), [], all_faces)
mesh.update()

obj = bpy.data.objects.new("BushBaseCoralFactory", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bpy.ops.object.editmode_toggle()
bpy.ops.mesh.remove_doubles(threshold=0.002)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.editmode_toggle()

# Normalise to consistent scale
max_dim = max(obj.dimensions[:2])
if max_dim > 0:
    obj.scale = (2 / max_dim,) * 3
bpy.ops.object.transform_apply(scale=True)

# Subdivision surface for smoother tube cross-sections
m_ss = obj.modifiers.new("SS", "SUBSURF")
m_ss.levels = 1
m_ss.render_levels = 1
bpy.ops.object.modifier_apply(modifier="SS")

# Subtle surface displacement for organic feel
tex = bpy.data.textures.new("bush_coral_d", type="CLOUDS")
tex.noise_scale = 0.05
m_d = obj.modifiers.new("D", "DISPLACE")
m_d.texture = tex
m_d.strength = 0.01
m_d.mid_level = 0
bpy.ops.object.modifier_apply(modifier="D")

obj.name = "BushBaseCoralFactory"
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
print(
    f"Done: BushBaseCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}"
)
