# [FL_INDEX: keywords="blender_factory, procedural_3d, BushBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BushBaseCoralFactory | Category: factories_tex
# Prompt: A white base mesh 3D model of a bush-type branching coral. The object displays the raw geometric skeleton of a bush coral — multiple thick branches radiate outward from a central junction point, extending in various directions with a complex, low-lying spread. Rendered without any material color or texture, the pure white geometry reveals the branching topology and the irregular organic silhouette, with a sharp shadow beneath highlighting the structure against the white background.

"""
Standalone Blender script (geometry + coral material) – BushBaseCoralFactory, seed 0.
Run:  blender --background --python BushBaseCoralFactory.py

Bush coral with dense, organic branching structure.
Uses quadratic interpolation (resolution=8) to upsample coarse control points
into smooth curves, matching the original TreeBaseCoralFactory's
FineTreeVertices + interp1d(kind='quadratic') pipeline.

Branch hierarchy: trunk → major (6-7) → minor (4-5 each) → detail (4-5 each)
"""
import os
import bpy
import numpy as np
import math

SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
#  Coral material — translated from generate.py:shader_coral (raw bpy)
# ═══════════════════════════════════════════════════════════════════════════
import os, random, colorsys

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

# from FixedSeed(factory_seed). To get equivalent diversity, we hash the seed for material
# sampling (otherwise consecutive seeds all produce similar warm-red hues).
_mat_seed = ((SEED + 1) * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
_seed_all(_mat_seed)
_coral_base_hue = _build_base_hue()
CORAL_MAT = make_coral_material(_coral_base_hue, "BushBaseCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)

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

# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "BushBaseCoralFactory"
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
print(
    f"Done: BushBaseCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}"
)

