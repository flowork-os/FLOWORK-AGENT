# [FL_INDEX: keywords="blender_factory, procedural_3d, CrustaceanFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CrustaceanFactory | Category: factories_geo
# Prompt: A crustacean (lobster/crayfish) rendered as a textured 3D model. The creature lies horizontally with a long segmented abdomen composed of multiple smooth, rounded carapace segments in warm reddish-brown. At the front, two prominent large chelae (claws) — one larger crusher claw with a white-tipped pincer and one slender smaller claw — extend outward. Two long thin antennae rise vertically from the cephalothorax. Several pairs of small walking legs and swimmerets are present underneath the body. The tail fan spreads at the rear. The smooth, slightly glossy exoskeleton has subtle specular highlights.

import os

import bmesh
import bpy
import numpy as np
from mathutils import Euler as MEuler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

try:
    from scipy.interpolate import interp1d
except ImportError:
    def interp1d(x, y, kind='linear', fill_value=None, bounds_error=True):
        x, y = np.asarray(x), np.asarray(y)
        def f(xi):
            return np.interp(np.asarray(xi), x, y)
        return f

SEED = 0
np.random.seed(SEED)


def log_uniform(low, high):
    return np.exp(np.random.uniform(np.log(low), np.log(high)))


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.curves):
        bpy.data.curves.remove(block)


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_tf(obj, loc=True, rot=True, scale=True):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)


def join_objs(objs):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def add_modifier(obj, mod_type, apply=True, **kwargs):
    select_only(obj)
    mod = obj.modifiers.new("mod", mod_type)
    for k, v in kwargs.items():
        setattr(mod, k, v)
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return mod


def read_co(obj):
    n = len(obj.data.vertices)
    if n == 0:
        return np.zeros((0, 3))
    arr = np.zeros(n * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)


def write_co(obj, co):
    obj.data.vertices.foreach_set("co", co.ravel())
    obj.data.update()


def displace_vertices(obj, fn):
    co = read_co(obj)
    if len(co) == 0:
        return
    x, y, z = co.T
    dx, dy, dz = fn(x, y, z)
    co[:, 0] += np.asarray(dx, dtype=float).ravel()
    co[:, 1] += np.asarray(dy, dtype=float).ravel()
    co[:, 2] += np.asarray(dz, dtype=float).ravel()
    write_co(obj, co)


def remove_verts_by_mask(obj, mask):
    indices = np.nonzero(mask)[0]
    if len(indices) == 0:
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    geom = [bm.verts[i] for i in indices]
    bmesh.ops.delete(bm, geom=geom, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def keep_largest_island(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    visited = set()
    islands = []
    for v in bm.verts:
        if v.index in visited:
            continue
        island = []
        stack = [v]
        while stack:
            cur = stack.pop()
            if cur.index in visited:
                continue
            visited.add(cur.index)
            island.append(cur)
            for e in cur.link_edges:
                other = e.other_vert(cur)
                if other.index not in visited:
                    stack.append(other)
        islands.append(island)
    if len(islands) > 1:
        largest = max(islands, key=len)
        largest_set = {v.index for v in largest}
        to_remove = [v for v in bm.verts if v.index not in largest_set]
        if to_remove:
            bmesh.ops.delete(bm, geom=to_remove, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def deep_clone(obj):
    new_mesh = obj.data.copy()
    new_obj = obj.copy()
    new_obj.data = new_mesh
    bpy.context.collection.objects.link(new_obj)
    return new_obj


def write_attr(obj, name, data, data_type='FLOAT', domain='POINT'):
    attr = obj.data.attributes.get(name)
    if attr is not None:
        obj.data.attributes.remove(attr)
    attr = obj.data.attributes.new(name, data_type, domain)
    attr.data.foreach_set("value", data.ravel())


def read_attr(obj, name):
    attr = obj.data.attributes[name]
    data = np.zeros(len(attr.data))
    attr.data.foreach_get("value", data)
    return data


# ═══════════════════════════════════════════════════════════════════════════════
# BEZIER / SPIN / LEAF
# ═══════════════════════════════════════════════════════════════════════════════

def bezier_curve(anchors, vector_locations=(), resolution=None):
    """Create mesh polyline from bezier control points."""

    n = next(len(r) for r in anchors if hasattr(r, '__len__'))
    anchors_arr = np.array([
        np.array(r, dtype=float) if hasattr(r, '__len__') else np.full(n, float(r))
        for r in anchors
    ])

    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object

    if n > 2:
        select_only(obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.subdivide(number_cuts=n - 2)
        bpy.ops.object.mode_set(mode='OBJECT')

    points = obj.data.splines[0].bezier_points
    for i in range(n):
        points[i].co = anchors_arr[:, i]
    for i in range(n):
        if i in vector_locations:
            points[i].handle_left_type = "VECTOR"
            points[i].handle_right_type = "VECTOR"
        else:
            points[i].handle_left_type = "AUTO"
            points[i].handle_right_type = "AUTO"

    obj.data.splines[0].resolution_u = resolution if resolution is not None else 12

    cos = np.array([p.co for p in points])
    seg_lengths = np.linalg.norm(cos[:-1] - cos[1:], axis=-1)

    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    for i in range(len(points)):
        pts = obj.data.splines[0].bezier_points
        if pts[i].handle_left_type == "FREE":
            pts[i].handle_left_type = "ALIGNED"
        if pts[i].handle_right_type == "FREE":
            pts[i].handle_right_type = "ALIGNED"
    for i in reversed(range(len(seg_lengths))):
        pts = list(obj.data.splines[0].bezier_points)
        number_cuts = min(int(seg_lengths[i] / 5e-3) - 1, 64)
        if number_cuts < 0:
            continue
        bpy.ops.curve.select_all(action="DESELECT")
        pts[i].select_control_point = True
        pts[i + 1].select_control_point = True
        bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1
    bpy.ops.object.mode_set(mode='OBJECT')

    select_only(obj)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    add_modifier(obj, "WELD", merge_threshold=1e-3)
    return obj


def remesh_fill(obj, resolution=0.015):
    """Convert filled flat polygon to open surface with uniform vertices."""

    add_modifier(obj, "SOLIDIFY", thickness=0.1, offset=-1)
    add_modifier(obj, "REMESH", mode='VOXEL', voxel_size=resolution)
    co = read_co(obj)
    if len(co) == 0:
        return obj
    z_mid = (co[:, 2].min() + co[:, 2].max()) / 2
    if abs(co[:, 2].min()) > abs(co[:, 2].max()):
        remove_verts_by_mask(obj, co[:, 2] < z_mid)
    else:
        remove_verts_by_mask(obj, co[:, 2] > z_mid)
    co = read_co(obj)
    if len(co) > 0:
        co[:, 2] = 0
        write_co(obj, co)
    return obj


def spin_mesh(anchors, vector_locations=(), axis=(0, 0, 1)):
    """Create surface of revolution from bezier profile."""

    obj = bezier_curve(anchors, vector_locations)
    co = read_co(obj)
    axis_arr = np.array(axis, dtype=float)
    axis_arr = axis_arr / (np.linalg.norm(axis_arr) + 1e-10)
    proj = (co @ axis_arr)[:, np.newaxis] * axis_arr[np.newaxis, :]
    mean_radius = np.mean(np.linalg.norm(co - proj, axis=-1))
    rot_res = max(min(int(2 * np.pi * mean_radius / 5e-3), 128), 8)

    add_modifier(obj, "WELD", merge_threshold=1e-3)

    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.spin(
        steps=rot_res, angle=np.pi * 2,
        center=(0.0, 0.0, 0.0), axis=axis
    )
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=1e-3)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def leaf_mesh(x_anchors, y_anchors, vector_locations=(), subdivision=64):
    """Create leaf-shaped flat mesh from two mirrored bezier curves."""

    curves = []
    for sign in [-1, 1]:
        anchors = [x_anchors, sign * np.array(y_anchors), 0]
        curves.append(bezier_curve(anchors, vector_locations, subdivision))
    obj = join_objs(curves)
    add_modifier(obj, "WELD", merge_threshold=0.001)

    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.fill()
    bpy.ops.object.mode_set(mode='OBJECT')

    remesh_fill(obj)
    keep_largest_island(obj)
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# NOISE HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def pseudo_noise(positions, scale=1.0):
    """Multi-octave sinusoidal noise approximation (symmetric in y)."""

    p = positions * scale
    return (
        np.sin(p[:, 0] * 1.0 + p[:, 1] * 2.3 + p[:, 2] * 1.7) * 0.30
        + np.sin(p[:, 0] * 3.1 + p[:, 1] * 0.7 + p[:, 2] * 2.9) * 0.30
        + np.sin(p[:, 0] * 5.3 + p[:, 1] * 4.1 + p[:, 2] * 3.3) * 0.20
        + np.sin(p[:, 0] * 7.7 + p[:, 1] * 6.5 + p[:, 2] * 5.1) * 0.10
        + np.sin(p[:, 0] * 11.3 + p[:, 1] * 9.7 + p[:, 2] * 8.3) * 0.10
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LOBSTER BODY (Surface of Revolution)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_lobster_body_params():
    x_length = np.random.uniform(0.6, 0.8)
    y_length = np.random.uniform(0.15, 0.2)
    z_length = y_length * np.random.uniform(1.0, 1.2)
    midpoint_first = np.random.uniform(0.65, 0.75)    # at 2/3 position
    midpoint_second = np.random.uniform(0.95, 1.05)   # at 1/3 position
    z_shift = np.random.uniform(0.4, 0.6)
    z_shift_midpoint = np.random.uniform(0.2, 0.3)
    bottom_cutoff = np.random.uniform(0.2, 0.3)
    bottom_shift = np.random.uniform(0.3, 0.5)
    noise_scale = np.random.uniform(5, 8)
    noise_strength = np.random.uniform(0.02, 0.04)
    return dict(
        x_length=x_length, y_length=y_length, z_length=z_length,
        midpoint_first=midpoint_first, midpoint_second=midpoint_second,
        z_shift=z_shift, z_shift_midpoint=z_shift_midpoint,
        bottom_cutoff=bottom_cutoff, bottom_shift=bottom_shift,
        noise_scale=noise_scale, noise_strength=noise_strength,
    )


def build_lobster_body(params):
    """Build lobster body via surface of revolution (spin around X).

    The body extends from x=0 (wide back/thorax) to x=x_length (narrow head).
    """

    xl = params['x_length']
    yl = params['y_length']
    mp1 = params['midpoint_first']    # radius fraction at 2/3
    mp2 = params['midpoint_second']   # radius fraction at 1/3

    # Profile: 6 control points for the bezier
    # Wide at x=0, tapering to near-zero at x=xl
    x_anch = np.array([0, 0, 1/3, 2/3, 1, 1]) * xl
    y_anch = np.array([0, 1, mp2, mp1, 0.01, 0]) * yl

    # Spin around X axis with VECTOR handles at points 1 and 4
    obj = spin_mesh([x_anch, y_anch, 0.0], [1, 4], axis=(1, 0, 0))

    # Height shift: lift head end upward
    z_s = params['z_shift']
    z_sm = params['z_shift_midpoint']
    h_fn = interp1d([0, 0.5, 1], [0, z_sm / 2, z_s], kind='quadratic')
    co = read_co(obj)
    x_norm = np.clip(co[:, 0] / xl, 0, 1)
    co[:, 2] += h_fn(x_norm) * yl
    write_co(obj, co)

    # Bottom cutoff: flatten the underside
    bc = params['bottom_cutoff']
    bs = params['bottom_shift']
    displace_vertices(obj, lambda x, y, z: (
        0, 0, -np.clip(z + yl * bc, None, 0) * (1 - bs)
    ))

    # Z-scale (non-uniform height)
    obj.scale[2] = params['z_length'] / yl
    apply_tf(obj)

    # Noise displacement along radial normals
    co = read_co(obj)
    sym = np.column_stack([co[:, 0], np.abs(co[:, 1]), co[:, 2]])
    noise = pseudo_noise(sym, params['noise_scale'])
    normals = co.copy()
    normals[:, 0] = 0
    nl = np.linalg.norm(normals, axis=-1, keepdims=True)
    nl[nl == 0] = 1
    normals /= nl
    co += normals * (noise * params['noise_strength'])[:, np.newaxis]
    write_co(obj, co)

    # Build skeleton (4 points along X)
    co = read_co(obj)
    head_z = co[co[:, 0].argmax(), 2]
    skeleton = np.zeros((4, 3))
    skeleton[:, 0] = np.linspace(0, xl, 4)
    skeleton[:, 2] = np.linspace(0, head_z, 4)

    print(f"  Body: {len(obj.data.vertices)} verts, x_length={xl:.3f}")
    return obj, skeleton


# ═══════════════════════════════════════════════════════════════════════════════
# TAIL (Multi-segment overlapping shell plates)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_tail_params(body_params):
    x_length = body_params['x_length'] * log_uniform(1.2, 1.8)
    y_length = body_params['y_length']  # match body width at junction
    z_length = y_length * np.random.uniform(1.0, 1.2)
    n_segments = np.random.randint(6, 10)
    x_decay = np.random.uniform(0.2, 0.3)
    shell_ratio = np.random.uniform(1.10, 1.15)  # more visible overlap
    y_midpoint_first = np.random.uniform(0.5, 0.65)
    y_midpoint_second = np.random.uniform(0.35, 0.50)  # wider tail tip
    bottom_cutoff = np.random.uniform(0.2, 0.3)
    bottom_shift = np.random.uniform(0.3, 0.5)
    top_shift = np.random.uniform(0.2, 0.4)
    top_cutoff = np.random.uniform(0.6, 0.8)
    noise_scale = log_uniform(5, 10)
    noise_strength = np.random.uniform(0.005, 0.01)
    return dict(
        x_length=x_length, y_length=y_length, z_length=z_length,
        n_segments=n_segments, x_decay=x_decay, shell_ratio=shell_ratio,
        y_midpoint_first=y_midpoint_first, y_midpoint_second=y_midpoint_second,
        bottom_cutoff=bottom_cutoff, bottom_shift=bottom_shift,
        top_shift=top_shift, top_cutoff=top_cutoff,
        noise_scale=noise_scale, noise_strength=noise_strength,
    )


def build_tail_segment(x0, x1, y0, y1, params):
    """Build one tail segment via spin. shell_ratio creates overlap."""

    xl = params['x_length']
    yl = params['y_length']
    sr = params['shell_ratio']

    # 3-point profile + zero endpoints
    x_anch = np.array([x0, (x0 + x1) / 2, x1]) * xl
    y_anch = np.array([y0, np.sqrt(max(y0 * y1, 0.001)), y1 * sr]) * yl
    xa = np.array([x_anch[0], *x_anch, x_anch[-1]])
    ya = np.array([0, *y_anch, 0])

    seg = spin_mesh([xa, ya, 0.0], [1, 3], axis=(1, 0, 0))

    # Bottom cutoff
    y_base = max(y0, y1) * yl
    bc = params['bottom_cutoff']
    bs = params['bottom_shift']
    displace_vertices(seg, lambda x, y, z: (
        0, 0, -np.clip(z + y_base * bc, None, 0) * (1 - bs)
    ))

    # Top shift
    tc = params['top_cutoff']
    ts = params['top_shift']
    displace_vertices(seg, lambda x, y, z: (
        0, 0, np.where(z > 0,
                       np.clip(tc * y_base - np.abs(y), 0, None) * ts, 0)
    ))

    # Noise
    co = read_co(seg)
    if len(co) > 0:
        sym = np.column_stack([co[:, 0], np.abs(co[:, 1]), co[:, 2]])
        noise = pseudo_noise(sym, params['noise_scale'])
        normals = co.copy()
        normals[:, 0] = 0
        nl = np.linalg.norm(normals, axis=-1, keepdims=True)
        nl[nl == 0] = 1
        normals /= nl
        co += normals * (noise * params['noise_strength'])[:, np.newaxis]
        write_co(seg, co)

    # Z-scale
    seg.scale[2] = params['z_length'] / yl
    apply_tf(seg)
    return seg


def build_tail(params):
    """Build segmented lobster tail with overlapping shell plates."""

    xl = params['x_length']
    n_seg = params['n_segments']
    x_decay = params['x_decay']
    sr = params['shell_ratio']

    # Exponentially decaying segment lengths
    decay_per = np.exp(np.log(x_decay) / n_seg)
    widths = np.array([decay_per ** i for i in range(n_seg)])
    x_cuts = np.concatenate([[0], np.cumsum(widths)])
    x_cuts /= x_cuts[-1]

    # Y-cuts: tapering from wide to narrow
    y_interp = interp1d(
        [0, 0.33, 0.67, 1],
        [1.0 / sr, params['y_midpoint_first'],
         params['y_midpoint_second'], 0.1],
        kind='linear'
    )
    y_cuts = y_interp(x_cuts)

    segments = []
    for i in range(n_seg):
        seg = build_tail_segment(
            x_cuts[i], x_cuts[i + 1],
            y_cuts[i], y_cuts[i + 1], params)
        segments.append(seg)

    obj = join_objs(segments)
    add_modifier(obj, "WELD", merge_threshold=0.001)

    # Build skeleton (2 points along X)
    skeleton = np.array([[0, 0, 0], [xl, 0, 0]], dtype=float)
    print(f"  Tail: {len(obj.data.vertices)} verts, {n_seg} segments")
    return obj, skeleton


# ═══════════════════════════════════════════════════════════════════════════════
# LEG SEGMENT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def sample_lobster_leg_params():
    """Lobster legs are thinner than crab legs."""

    x_length = np.random.uniform(0.8, 1.2)
    y_length = np.random.uniform(0.01, 0.015)
    z_length = y_length * np.random.uniform(1.0, 1.2)
    x_mid_first = np.random.uniform(0.3, 0.4)
    x_mid_second = np.random.uniform(0.6, 0.7)
    y_mid_first = np.random.uniform(0.7, 1.0)
    y_mid_second = y_mid_first / 2 * np.random.uniform(1.1, 1.3)
    y_expand = np.random.uniform(1.1, 1.3)
    noise_strength = np.random.uniform(0.003, 0.006)
    noise_scale = log_uniform(5, 10)
    bottom_shift = np.random.uniform(0.3, 0.5)
    bottom_cutoff = np.random.uniform(0.2, 0.5)
    top_shift = np.random.uniform(0.2, 0.4)
    top_cutoff = np.random.uniform(0.6, 0.8)
    return dict(
        x_length=x_length, y_length=y_length, z_length=z_length,
        x_mid_first=x_mid_first, x_mid_second=x_mid_second,
        y_mid_first=y_mid_first, y_mid_second=y_mid_second,
        y_expand=y_expand, noise_strength=noise_strength,
        noise_scale=noise_scale, bottom_shift=bottom_shift,
        bottom_cutoff=bottom_cutoff, top_shift=top_shift,
        top_cutoff=top_cutoff,
    )


def build_segment(x_start, x_end, y_start, y_end, params):
    """Build one tapered tube segment via surface-of-revolution."""

    xl = params['x_length']
    yl = params['y_length']
    ye = params['y_expand']

    xs = np.array([x_start, x_start + 0.01,
                   (x_start + x_end) / 2,
                   x_end - 0.01, x_end])
    ys = np.array([y_start * 0.9, y_start,
                   (y_start + y_end) / 2 * ye,
                   y_end, y_end * 0.9])

    obj = spin_mesh(
        [np.array([xs[0], *xs, xs[-1]]) * xl,
         np.array([0, *ys, 0]) * yl, 0.0],
        [1, len(xs)], axis=(1, 0, 0),
    )

    # Bottom cutoff
    y_base = yl * y_start
    bc, bs = params['bottom_cutoff'], params['bottom_shift']
    displace_vertices(obj, lambda x, y, z: (
        0, 0, -np.clip(z + y_base * bc, None, 0) * (1 - bs)
    ))

    # Top shift
    tc, ts = params['top_cutoff'], params['top_shift']
    displace_vertices(obj, lambda x, y, z: (
        0, 0, np.where(z > 0,
                       np.clip(tc * y_base - np.abs(y), 0, None) * ts, 0)
    ))

    # Noise decoration
    co = read_co(obj)
    if len(co) > 0:
        sym = np.column_stack([co[:, 0], np.abs(co[:, 1]), co[:, 2]])
        noise = pseudo_noise(sym, params['noise_scale'])
        normals = co.copy()
        normals[:, 0] = 0
        nl = np.linalg.norm(normals, axis=-1, keepdims=True)
        nl[nl == 0] = 1
        normals /= nl
        co += normals * (noise * params['noise_strength'])[:, np.newaxis]
        write_co(obj, co)

    obj.scale[2] = params['z_length'] / yl
    apply_tf(obj)
    return obj


def leg_bend(obj, bend_angle):
    """Gently bend a leg downward via progressive arc."""

    co = read_co(obj)
    if len(co) == 0:
        return
    x_max = co[:, 0].max()
    if x_max < 1e-6:
        return

    t = np.clip(co[:, 0] / x_max, 0, 1)
    y_cs = co[:, 1].copy()
    z_cs = co[:, 2].copy()
    L = x_max

    # Progressive bend (smooth arc)
    n_grid = 200
    t_grid = np.linspace(0, 1, n_grid)
    a_grid = bend_angle * t_grid
    ds = L / (n_grid - 1)

    x_grid = np.cumsum(np.concatenate(
        [[0], 0.5 * (np.cos(a_grid[:-1]) + np.cos(a_grid[1:])) * ds]))
    z_grid = np.cumsum(np.concatenate(
        [[0], 0.5 * (np.sin(a_grid[:-1]) + np.sin(a_grid[1:])) * ds]))

    x_center = np.interp(t, t_grid, x_grid)
    z_center = np.interp(t, t_grid, z_grid)

    angle_at_t = bend_angle * t
    co[:, 0] = x_center - z_cs * np.sin(angle_at_t)
    co[:, 1] = y_cs
    co[:, 2] = z_center + z_cs * np.cos(angle_at_t)
    write_co(obj, co)


def build_leg(params, bend_angle=-np.pi * 0.35):
    """Build a lobster leg (3 segments, gently bent downward)."""

    x_cuts = [0, params['x_mid_first'], params['x_mid_second'], 1]
    y_cuts = [1, params['y_mid_first'], params['y_mid_second'], 0.01]
    segs = []
    for i in range(len(x_cuts) - 1):
        segs.append(build_segment(
            x_cuts[i], x_cuts[i + 1],
            y_cuts[i], y_cuts[i + 1], params))
    obj = join_objs(segs)
    add_modifier(obj, "WELD", merge_threshold=0.001)
    leg_bend(obj, bend_angle)
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# CLAW (Segmented base + pincer)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_lobster_claw_params():
    base = sample_lobster_leg_params()
    z_length = base['y_length'] * np.random.uniform(1.0, 1.2)
    x_mid_first = np.random.uniform(0.2, 0.25)
    x_mid_second = np.random.uniform(0.4, 0.6)
    y_mid_first = np.random.uniform(1.5, 2.0)
    y_mid_second = y_mid_first * log_uniform(1.2, 1.6)
    y_expand = np.random.uniform(1.4, 1.5)
    noise_strength = np.random.uniform(0.005, 0.01)
    top_shift = np.random.uniform(0.6, 0.8)
    claw_y_first = np.random.uniform(1.2, 1.5)
    claw_y_second = claw_y_first * np.random.uniform(0.7, 0.8)
    claw_x_depth = (1 - x_mid_second) * np.random.uniform(0.3, 0.5)
    claw_x_turn = np.random.uniform(0.2, 0.4)
    claw_z_width = np.random.uniform(0.2, 0.3)
    claw_spike_strength = np.random.uniform(0.01, 0.02)
    lower_z_scale = np.random.uniform(0.4, 0.6)
    lower_scale = np.random.uniform(0.75, 0.9)
    lower_z_offset = np.random.uniform(-0.5, 0.5)
    base.update(dict(
        z_length=z_length, x_mid_first=x_mid_first, x_mid_second=x_mid_second,
        y_mid_first=y_mid_first, y_mid_second=y_mid_second,
        y_expand=y_expand, noise_strength=noise_strength, top_shift=top_shift,
        claw_y_first=claw_y_first, claw_y_second=claw_y_second,
        claw_x_depth=claw_x_depth, claw_x_turn=claw_x_turn,
        claw_z_width=claw_z_width, claw_spike_strength=claw_spike_strength,
        lower_z_scale=lower_z_scale, lower_scale=lower_scale,
        lower_z_offset=lower_z_offset,
    ))
    return base


def smooth_curl(obj, total_curl, base_angle=0.0):
    """Smoothly curve a part along a single circular arc in the XZ plane."""

    co = read_co(obj)
    if len(co) == 0:
        return
    x_max = co[:, 0].max()
    if x_max < 1e-6:
        return

    t = np.clip(co[:, 0] / x_max, 0.0, 1.0)
    y_cs = co[:, 1].copy()
    z_cs = co[:, 2].copy()
    L = x_max
    abs_curl = abs(total_curl)

    if abs_curl < 0.01:
        cb, sb = np.cos(base_angle), np.sin(base_angle)
        co[:, 0] = t * L * cb - z_cs * sb
        co[:, 1] = y_cs
        co[:, 2] = t * L * sb + z_cs * cb
    else:
        R = L / abs_curl
        cx = R * np.sin(base_angle)
        cz = -R * np.cos(base_angle)
        phi = abs_curl * t
        co[:, 0] = cx + (R + z_cs) * np.sin(phi - base_angle)
        co[:, 1] = y_cs
        co[:, 2] = cz + (R + z_cs) * np.cos(phi - base_angle)

    write_co(obj, co)


def build_claw(params):
    """Build lobster claw: 2 base segments + pincer with lower jaw."""

    xl = params['x_length']
    yl = params['y_length']
    zl = params['z_length']
    x_mid = params['x_mid_second']
    y_mid = params['y_mid_second']

    # 2 base segments (arm)
    x_cuts = [0, params['x_mid_first'], x_mid, 1]
    y_cuts = [1, params['y_mid_first'], y_mid, 0.01]
    base_segs = []
    for i in range(2):
        base_segs.append(build_segment(
            x_cuts[i], x_cuts[i + 1],
            y_cuts[i], y_cuts[i + 1], params))

    # Claw (3rd segment = pincer)
    xs = np.array([x_mid, (x_mid + 1) / 2, (x_mid + 3) / 4, 1])
    ys = np.array([y_mid, y_mid * params['claw_y_first'],
                   y_mid * params['claw_y_second'], 0.01])
    claw = spin_mesh(
        [np.array([xs[0], *xs, xs[-1]]) * xl,
         np.array([0, *ys, 0]) * yl, 0.0],
        [1, len(xs)], axis=(1, 0, 0),
    )

    # Bottom depth cut
    bc = params['bottom_cutoff']
    cxd = params['claw_x_depth']
    displace_vertices(claw, lambda x, y, z: (
        0, 0,
        -np.clip(
            z + yl * bc + yl * (y_mid - bc) * (x / xl - x_mid) / max(cxd, 0.01),
            None, 0
        ) * (1 - params['bottom_shift'])
    ))

    # Width expansion (z-direction bulge)
    cxt = params['claw_x_turn']
    czw = params['claw_z_width']
    wfn = interp1d(
        [x_mid, x_mid + cxd,
         x_mid + cxd + cxt * (1 - x_mid - cxd), 1],
        [0, 0, czw, 0], kind='linear', fill_value='extrapolate',
    )
    displace_vertices(claw, lambda x, y, z: (
        0, 0,
        np.where(x > (x_mid + cxd) * xl,
                 wfn(x / xl) * y_mid * yl, 0)
    ))

    # Top shift
    tc, ts = params['top_cutoff'], params['top_shift']
    displace_vertices(claw, lambda x, y, z: (
        0, 0,
        np.where(z > 0,
                 np.clip(tc * yl - np.abs(y), 0, None) * ts, 0)
    ))

    # Inner spikes
    co = read_co(claw)
    x, y, z = co.T
    inner = ((z < 0) & (x > (x_mid + cxd * 1.5) * xl)
             & (x < xl * 0.98) & (np.abs(y) < yl * 0.5))
    if np.any(inner):
        n_sp = min(15, int(np.sum(inner)))
        if n_sp > 0:
            sp_idx = np.random.choice(np.where(inner)[0],
                                      size=n_sp, replace=False)
            sp_locs = co[sp_idx]
            d2 = np.linalg.norm(
                co[np.newaxis] - sp_locs[:, np.newaxis], axis=-1)
            min_d = np.min(d2, axis=0)
            extr = params['claw_spike_strength'] * \
                np.clip(1 - min_d / 0.01, 0, None)
            co[:, 2] -= extr
            write_co(claw, co)

    # Noise
    co = read_co(claw)
    sym = np.column_stack([co[:, 0], np.abs(co[:, 1]), co[:, 2]])
    noise = pseudo_noise(sym, params['noise_scale'])
    normals = co.copy()
    normals[:, 0] = 0
    nl = np.linalg.norm(normals, axis=-1, keepdims=True)
    nl[nl == 0] = 1
    normals /= nl
    co += normals * (noise * params['noise_strength'])[:, np.newaxis]
    write_co(claw, co)

    claw.scale[2] = zl / yl
    apply_tf(claw)

    # Lower jaw
    lower = deep_clone(claw)
    co_l = read_co(lower)
    remove_verts_by_mask(lower, co_l[:, 0] < (x_mid + cxd) * xl)

    lower.location[0] = -(x_mid + cxd) * xl
    apply_tf(lower, loc=True, rot=False, scale=False)

    ls = params['lower_scale']
    lzs = params['lower_z_scale']
    lower.scale = (ls, ls, -ls * lzs)
    lower.rotation_euler[1] = np.random.uniform(np.pi / 12, np.pi / 4)
    apply_tf(lower)

    lower.location[0] = (x_mid + cxd) * xl
    lower.location[2] = params['lower_z_offset'] * zl
    apply_tf(lower, loc=True, rot=False, scale=False)
    add_modifier(lower, "WELD", merge_threshold=0.001)

    obj = join_objs(base_segs + [claw, lower])
    add_modifier(obj, "WELD", merge_threshold=0.001)
    # Gentle curl for claw
    smooth_curl(obj, total_curl=-0.2, base_angle=0.05)
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# FIN (Leaf-shaped)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_fin_params(body_params):
    """Sample params for the center telson fin."""

    x_length = body_params['y_length'] * log_uniform(1.8, 2.5)
    y_length = x_length * np.random.uniform(0.35, 0.50)
    x_tip = np.random.uniform(0.7, 0.8)
    y_mid = np.random.uniform(0.6, 0.8)
    return dict(
        x_length=x_length, y_length=y_length,
        x_tip=x_tip, y_mid=y_mid,
    )


def sample_side_fin_params(body_params):
    """Sample params for side uropod fins (similar size to center)."""

    x_length = body_params['y_length'] * log_uniform(1.5, 2.0)
    y_length = x_length * np.random.uniform(0.35, 0.48)
    x_tip = np.random.uniform(0.65, 0.75)
    y_mid = np.random.uniform(0.55, 0.75)
    return dict(
        x_length=x_length, y_length=y_length,
        x_tip=x_tip, y_mid=y_mid,
    )


def build_fin(params):
    """Build a leaf-shaped tail fin."""

    xl = params['x_length']
    yl = params['y_length']
    x_tip = params['x_tip']
    y_mid = params['y_mid']

    x_anch = np.array([0, x_tip / 2, x_tip, 1]) * xl
    y_anch = np.array([0, y_mid, 1, 0]) * yl

    obj = leaf_mesh(x_anch, y_anch)
    add_modifier(obj, "SOLIDIFY", thickness=0.012, offset=0.0)
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# ANTENNA (Thin tube with quadratic bend)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_antenna_params(body_params):
    x_length = body_params['x_length'] * log_uniform(1.6, 3.0)
    y_length = np.random.uniform(0.008, 0.012)
    z_length = y_length * np.random.uniform(1.0, 1.2)
    x_mid_first = np.random.uniform(0.1, 0.15)
    x_mid_second = np.random.uniform(0.25, 0.3)
    y_mid_first = np.random.uniform(0.7, 1.0)
    y_mid_second = y_mid_first / 2 * np.random.uniform(1.1, 1.3)
    y_expand = np.random.uniform(1.1, 1.3)
    noise_strength = np.random.uniform(0.002, 0.004)
    noise_scale = log_uniform(5, 10)
    bottom_shift = np.random.uniform(0.3, 0.5)
    bottom_cutoff = np.random.uniform(0.2, 0.5)
    top_shift = np.random.uniform(0.2, 0.4)
    top_cutoff = np.random.uniform(0.6, 0.8)
    antenna_bend = np.random.uniform(2, 5)
    return dict(
        x_length=x_length, y_length=y_length, z_length=z_length,
        x_mid_first=x_mid_first, x_mid_second=x_mid_second,
        y_mid_first=y_mid_first, y_mid_second=y_mid_second,
        y_expand=y_expand, noise_strength=noise_strength,
        noise_scale=noise_scale, bottom_shift=bottom_shift,
        bottom_cutoff=bottom_cutoff, top_shift=top_shift,
        top_cutoff=top_cutoff, antenna_bend=antenna_bend,
    )


def build_antenna(params):
    """Build a lobster antenna: 3-segment tube with quadratic upward bend."""

    x_cuts = [0, params['x_mid_first'], params['x_mid_second'], 1]
    y_cuts = [1, params['y_mid_first'], params['y_mid_second'], 0.01]

    segs = []
    for i in range(len(x_cuts) - 1):
        seg = build_segment(x_cuts[i], x_cuts[i + 1],
                            y_cuts[i], y_cuts[i + 1], params)
        segs.append(seg)

    obj = join_objs(segs)
    add_modifier(obj, "WELD", merge_threshold=0.001)

    # Apply quadratic upward bend
    xl = params['x_length']
    bend = params['antenna_bend']
    x_bend_start = params['x_mid_second']
    co = read_co(obj)
    if len(co) > 0:
        x_norm = co[:, 0] / xl
        mask = x_norm > x_bend_start
        dz = np.where(mask,
                      bend * (x_norm - x_bend_start) ** 2 * params['z_length'],
                      0)
        co[:, 2] += dz
        write_co(obj, co)

    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# EYE (Sphere + cylinder stalk)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_eye_params():
    radius = np.random.uniform(0.015, 0.02)
    length = radius * np.random.uniform(1.0, 1.5)
    return dict(radius=radius, length=length)


def build_eye(params):
    radius = params['radius']
    length = params['length']

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius)
    sphere = bpy.context.active_object

    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.008, depth=length, location=(-length / 2, 0, 0))
    cylinder = bpy.context.active_object
    cylinder.rotation_euler[1] = np.pi / 2
    apply_tf(cylinder)

    obj = join_objs([sphere, cylinder])
    add_modifier(obj, "REMESH", mode='VOXEL', voxel_size=0.005)

    # Origin to leftmost
    co = read_co(obj)
    co[:, 0] -= co[:, 0].min()
    write_co(obj, co)
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# ATTACHMENT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

def euler_quat(x_deg, y_deg, z_deg):
    return MEuler(np.deg2rad([x_deg, y_deg, z_deg]).tolist()).to_quaternion()


def quat_align_vecs(a, b):
    a = Vector(a).normalized()
    b = Vector(b).normalized()
    dot = a.dot(b)
    if dot > 0.9999:
        return Quaternion()
    if dot < -0.9999:
        perp = Vector((1, 0, 0)).cross(a)
        if perp.length < 0.01:
            perp = Vector((0, 1, 0)).cross(a)
        return Quaternion(perp.normalized(), np.pi)
    return Quaternion(a.cross(b).normalized(), a.angle(b))


def raycast_attach(skeleton, body_obj, u, v, rad):
    """Find attachment point on body surface via BVH raycast."""

    n = len(skeleton)
    idx = u * (n - 1)
    i = min(int(idx), max(n - 2, 0))
    t = idx - i
    j = min(i + 1, n - 1)
    origin = (1 - t) * skeleton[i] + t * skeleton[j]

    tangent = skeleton[j] - skeleton[i] if n > 1 else np.array([1, 0, 0])
    tn = np.linalg.norm(tangent)
    tangent = tangent / tn if tn > 1e-10 else np.array([1, 0, 0])

    basis = quat_align_vecs(Vector((1, 0, 0)), Vector(tangent))
    dir_rot = euler_quat(180 * v, 0, 0) @ euler_quat(0, 90, 0)
    direction = basis @ dir_rot @ Vector((1, 0, 0))

    depsgraph = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(body_obj, depsgraph)
    loc, normal, index, dist = bvh.ray_cast(Vector(origin), direction)

    if loc is None:
        loc = Vector(origin)
    else:
        loc = Vector(origin).lerp(loc, rad)

    loc = body_obj.matrix_world @ loc
    return np.array(loc), normal, tangent


def place_part(part_obj, body_obj, skeleton, u, v, rad, joint_deg, side):
    """Attach a part to the body surface with joint rotation and mirroring."""

    loc, normal, tangent = raycast_attach(skeleton, body_obj, u, v, rad)
    rot = euler_quat(*joint_deg)
    rot_mat = np.array(rot.to_matrix())

    co = read_co(part_obj)
    co = co @ rot_mat.T + loc
    if side == -1:
        co[:, 1] = -co[:, 1]
    write_co(part_obj, co)

    if side == -1:
        select_only(part_obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.mode_set(mode='OBJECT')


# ═══════════════════════════════════════════════════════════════════════════════
# ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════════════

def build_lobster():
    """Build the complete lobster."""

    print("CrustaceanFactory: Building lobster (seed=0)...")

    n_legs = 4
    n_limbs = 5

    # ── Sample assembly parameters ──

    # Leg positions on body (clustered near the body-tail junction)
    x_start = np.random.uniform(0.05, 0.08)
    x_end = np.random.uniform(0.2, 0.25)
    x_legs = (np.linspace(x_start, x_end, n_limbs)
              + np.arange(n_limbs) * 0.02)[::-1]

    leg_angle = np.random.uniform(0.3, 0.35)
    ljx = np.sort(np.random.uniform(-5, 5, n_legs))
    ljy = np.sort(np.random.uniform(0, 10, n_legs))
    ljz = (np.sort(np.random.uniform(95, 110, n_legs)
                   + np.random.uniform(-8, 8))
           + np.arange(n_legs) * 2)

    x_claw_off = np.random.uniform(0.08, 0.1)
    claw_angle = np.random.uniform(0.4, 0.5)
    claw_joint = (np.random.uniform(-80, -70),
                  np.random.uniform(-10, 10),
                  np.random.uniform(10, 20))

    x_eye = np.random.uniform(0.8, 0.88)
    eye_angle = np.random.uniform(0.8, 0.85)
    eye_joint = (0, np.random.uniform(-60, 0),
                 np.random.uniform(10, 70))

    x_antenna = np.random.uniform(0.76, 0.8)
    antenna_angle = np.random.uniform(0.6, 0.7)
    antenna_joint = (np.random.uniform(70, 110),
                     np.random.uniform(-40, -30),
                     np.random.uniform(20, 40))

    # Fin positions on tail
    x_fins = np.sort(np.random.uniform(0.85, 0.95, 2))
    fin_angle_side = np.random.uniform(0.3, 0.4)
    fin_joint_side = (np.random.uniform(10, 40), 0,
                      np.random.uniform(20, 50))  # wider fan spread
    fin_joint_center = (0, 0, 0)

    # ── Sample part parameters ──

    body_params = sample_lobster_body_params()

    leg_x_length = body_params['x_length'] * log_uniform(0.6, 0.8)
    leg_x_lengths = np.sort(
        np.random.uniform(0.6, 1, n_legs))[::-1] * leg_x_length

    shared_lp = sample_lobster_leg_params()
    leg_params_list = []
    for i in range(n_legs):
        lp = sample_lobster_leg_params()
        lp['bottom_cutoff'] = shared_lp['bottom_cutoff']
        lp['x_length'] = leg_x_lengths[i]
        leg_params_list.append(lp)

    claw_x_length = body_params['x_length'] * log_uniform(1.2, 1.5)
    claw_params = sample_lobster_claw_params()
    claw_params['x_length'] = claw_x_length

    tail_params = sample_tail_params(body_params)

    fin_params = sample_fin_params(body_params)

    antenna_params = sample_antenna_params(body_params)

    eye_params = sample_eye_params()

    print(f"  Body x={body_params['x_length']:.3f}, "
          f"Tail x={tail_params['x_length']:.3f}, "
          f"Claw x={claw_x_length:.3f}")

    # ══════════════════════════════════════════════════════════════════════
    # BUILD ALL GEOMETRY
    # ══════════════════════════════════════════════════════════════════════

    # Body
    print("  Building body...")
    body_obj, body_skeleton = build_lobster_body(body_params)
    all_parts = [body_obj]

    # Tail (rotate 180° to extend backward from body x=0)
    print("  Building tail...")
    tail_obj, tail_skeleton = build_tail(tail_params)
    tail_rot = euler_quat(0, 0, 180)
    tail_rot_mat = np.array(tail_rot.to_matrix())
    co = read_co(tail_obj)
    co = co @ tail_rot_mat.T
    write_co(tail_obj, co)
    # Flip normals after 180° rotation around Z (handedness preserved but
    # the Y-flip reverses face winding for non-symmetric details)
    tail_world_skeleton = tail_skeleton @ tail_rot_mat.T
    all_parts.append(tail_obj)

    # Fins (forming horizontal fan at tail tip via direct positioning)
    print("  Building fins...")
    # Find actual tail tip centroid from mesh
    tail_co = read_co(tail_obj)
    tip_x = tail_co[:, 0].min()
    tip_mask = tail_co[:, 0] < tip_x + 0.03
    tail_tip_pos = tail_co[tip_mask].mean(axis=0)

    # 5 fins: 1 center telson + 2 per side (upper/lower uropod pair)
    # Each side has endopod (upper) + exopod (lower), nearly parallel
    fin_parts = []
    side_fin_params = sample_side_fin_params(body_params)
    side_angle = np.random.uniform(50, 60)  # shared splay angle for each side
    fan_specs = [
        # (angle_deg, x_stagger, z_offset, x_tilt_deg, use_side_params)
        # Center telson
        (0,           0.0,    0.0,     0,    False),
        # Right side: upper (exopod) + lower (endopod)
        (side_angle,  0.025,  0.015,   5,    True),   # upper right
        (side_angle,  0.035, -0.008,   3,    True),   # lower right
        # Left side: upper (exopod) + lower (endopod)
        (-side_angle, 0.025, -0.015,  -5,    True),   # upper left
        (-side_angle, 0.035,  0.008,  -3,    True),   # lower left
    ]
    for angle, x_stag, z_off, x_tilt, use_side in fan_specs:
        fp = side_fin_params if use_side else fin_params
        fin = build_fin(fp)
        co = read_co(fin)
        rot = euler_quat(x_tilt, 0, 180 + angle)
        rot_mat = np.array(rot.to_matrix())
        origin = tail_tip_pos + np.array([x_stag, 0, z_off])
        co = co @ rot_mat.T + origin
        write_co(fin, co)
        fin_parts.append(fin)

    # Legs
    print("  Building legs...")
    for i in range(n_legs):
        for side in [1, -1]:
            leg = build_leg(leg_params_list[i])
            place_part(leg, body_obj, body_skeleton,
                       x_legs[i + 1], leg_angle, 0.99,
                       (ljx[i], ljy[i], ljz[i]), side)
            all_parts.append(leg)
        print(f"    Leg pair {i + 1}/{n_legs} done")

    # Claws
    print("  Building claws...")
    claw_r = build_claw(claw_params)
    claw_l = deep_clone(claw_r)
    place_part(claw_r, body_obj, body_skeleton,
               x_legs[0] + x_claw_off, claw_angle, 0.99,
               claw_joint, 1)
    place_part(claw_l, body_obj, body_skeleton,
               x_legs[0] + x_claw_off, claw_angle, 0.99,
               claw_joint, -1)
    all_parts.extend([claw_r, claw_l])

    # Antennae
    print("  Building antennae...")
    ant_r = build_antenna(antenna_params)
    ant_l = deep_clone(ant_r)
    place_part(ant_r, body_obj, body_skeleton,
               x_antenna, antenna_angle, 0.99,
               antenna_joint, 1)
    place_part(ant_l, body_obj, body_skeleton,
               x_antenna, antenna_angle, 0.99,
               antenna_joint, -1)
    all_parts.extend([ant_r, ant_l])

    # Eyes
    print("  Building eyes...")
    for side in [1, -1]:
        eye = build_eye(eye_params)
        place_part(eye, body_obj, body_skeleton,
                   x_eye, eye_angle, 0.99, eye_joint, side)
        all_parts.append(eye)

    # ── Join body parts (without fins) and apply SUBSURF ──
    print("  Joining body parts (excluding fins)...")
    result = join_objs(all_parts)
    add_modifier(result, "WELD", merge_threshold=0.002)

    # Subdivide for smoother surface (body/tail/legs/claws/antennae/eyes only)
    add_modifier(result, "SUBSURF", levels=1, render_levels=1)

    # ── Now join fins (no SUBSURF — keeps them as distinct paddles) ──
    print("  Joining fins to body...")
    if fin_parts:
        fin_combined = join_objs(fin_parts)
        # Smooth shade the fins individually
        select_only(fin_combined)
        bpy.ops.object.shade_smooth()
        result = join_objs([result, fin_combined])

    # Smooth shading
    select_only(result)
    bpy.ops.object.shade_smooth()

    # Ground the lobster (z-min = 0)
    co = read_co(result)
    co[:, 2] -= co[:, 2].min()
    write_co(result, co)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

clear_scene()
bpy.context.scene.cursor.location = (0, 0, 0)
lobster = build_lobster()
lobster.name = "CrustaceanFactory"
print(f"\nCrustaceanFactory built: {len(lobster.data.vertices)} verts, "
      f"{len(lobster.data.polygons)} faces")

# Save .blend file
script_dir = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
blend_path = os.path.join(script_dir, "CrustaceanFactory.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"Saved: {blend_path}")
