# [FL_INDEX: keywords="blender_factory, procedural_3d, FlowerFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FlowerFactory | Category: factories_geo
# Prompt: A 3D model of a flower bloom rendered from a slightly elevated three-quarter perspective, featuring multiple layers of light blue petals arranged in a cup or bowl shape with visible brown stamens at the center, and a ring of smaller dark green sepals at the base.

import os
SEED = int(os.environ.get("SEED", "0"))
import math
import random

import bmesh
import bpy
import numpy as np

random.seed(SEED)
np.random.seed(SEED)

# ── scene helpers ─────────────────────────────────────────────────────────────


import random as _random, colorsys as _colorsys

def _seed_mat(seed):
    _s = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s); _random.seed(_s)

def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h)%1, max(0,min(1,float(s))), max(0,min(1,float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear()
    return m

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def make_category_mat(seed, name="GreeneryMaterial"):
    """Plant greenery: green with noise + translucent/principled mix."""

    _seed_mat(seed)
    base_hue = float(np.random.uniform(0.22, 0.38))
    green_c = _hsv2rgba(base_hue, np.random.uniform(0.5, 0.9), np.random.uniform(0.08, 0.3))
    light_c = _hsv2rgba(base_hue + float(np.random.uniform(-0.05, 0.05)),
                         np.random.uniform(0.3, 0.6), np.random.uniform(0.15, 0.4))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.noise_dimensions = "4D"
    ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = float(np.random.uniform(-2, 2))
    noise.inputs["Scale"].default_value = float(np.random.uniform(5, 15))
    noise.inputs["Detail"].default_value = 5.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.color_mode = "HSV"
    cr.color_ramp.hue_interpolation = "NEAR"
    ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = green_c
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = light_c
    # Translucent + Principled mix (matches simple_greenery 60-90% translucent)
    trans = nt.nodes.new("ShaderNodeBsdfTranslucent"); ln(cr.outputs["Color"], trans.inputs["Color"])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.4, 0.8))
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = float(np.random.uniform(0.6, 0.9))
    ln(bsdf.outputs["BSDF"], mix.inputs[1]); ln(trans.outputs["BSDF"], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_petal_mat(seed, name="FlowerPetal"):
    """Petal shader: colorful Principled+Translucent mix.
    Color sampled from the petal_hsv palette (pink/red/yellow/white/purple/blue)."""

    _seed_mat(seed + 31)
    # petal_hsv palette — a mix of flower colors
    palette = [
        (0.0, 0.05, 0.98),   # white
        (0.95, 0.75, 0.90),  # pink
        (0.0, 0.85, 0.75),   # red
        (0.13, 0.80, 0.95),  # yellow
        (0.75, 0.70, 0.80),  # purple
        (0.58, 0.70, 0.85),  # blue
        (0.08, 0.80, 0.95),  # orange
    ]
    hue_base, sat_base, val_base = palette[int(np.random.uniform(0, len(palette)))]
    hue = (hue_base + float(np.random.uniform(-0.03, 0.03))) % 1.0
    sat = float(max(0.1, min(1.0, sat_base + np.random.uniform(-0.1, 0.1))))
    val = float(max(0.1, min(1.0, val_base + np.random.uniform(-0.1, 0.1))))
    petal_rgba = _hsv2rgba(hue, sat, val)

    specular = float(np.random.uniform(0.5, 0.7))
    roughness = float(np.random.uniform(0.35, 0.45))
    translucent_amt = float(np.random.uniform(0.25, 0.35))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = petal_rgba
    trans = nt.nodes.new("ShaderNodeBsdfTranslucent")
    ln(rgb.outputs[0], trans.inputs["Color"])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(rgb.outputs[0], bsdf.inputs["Base Color"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular
    bsdf.inputs["Roughness"].default_value = roughness
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = translucent_amt
    ln(bsdf.outputs["BSDF"], mix.inputs[1])
    ln(trans.outputs["BSDF"], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def make_center_mat(seed, name="FlowerCenter"):
    """Flower center shader: dark-brown -> dark-red -> orange ColorRamp driven by AmbientOcclusion."""

    _seed_mat(seed + 59)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    cr = nt.nodes.new("ShaderNodeValToRGB")
    ln(ao.outputs["Color"], cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.4841
    cr.color_ramp.elements[0].color = (0.0127, 0.0075, 0.0026, 1.0)
    cr.color_ramp.elements.new(0.8591)
    cr.color_ramp.elements[1].position = 0.8591
    cr.color_ramp.elements[1].color = (0.0848, 0.0066, 0.0007, 1.0)
    cr.color_ramp.elements[2].position = 1.0
    cr.color_ramp.elements[2].color = (1.0, 0.6228, 0.1069, 1.0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# Keep original greenery CATEG_MAT for backward compatibility (referenced elsewhere).
CATEG_MAT = make_category_mat(SEED, "FlowerFactory_Material")
CATEG_MAT.use_fake_user = True

# Save/restore RNG state so downstream build-time sampling is unchanged.
_saved_state = np.random.get_state()
PETAL_MAT  = make_petal_mat(SEED, "FlowerFactory_Petal")
CENTER_MAT = make_center_mat(SEED, "FlowerFactory_Center")
PETAL_MAT.use_fake_user = True
CENTER_MAT.use_fake_user = True
np.random.set_state(_saved_state)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

# ── math helpers ─────────────────────────────────────────────────────────────

def sample_quadratic_bezier(start, mid, end, n):
    """Sample n points along a quadratic Bezier curve."""

    pts = []
    for i in range(n):
        t = i / max(n - 1, 1)
        p = (1-t)**2 * np.array(start) + 2*(1-t)*t * np.array(mid) + t**2 * np.array(end)
        pts.append(p)
    return np.array(pts)

def compute_curve_frames(pts):
    """Compute tangent, normal, binormal frames along a polyline.
    Uses rotation-minimizing frame (matches Blender's Minimum twist)."""

    n = len(pts)
    tangents = np.zeros_like(pts)
    for i in range(n):
        if i == 0:
            tangents[i] = pts[1] - pts[0]
        elif i == n - 1:
            tangents[i] = pts[-1] - pts[-2]
        else:
            tangents[i] = pts[i+1] - pts[i-1]
        norm = np.linalg.norm(tangents[i])
        if norm > 1e-12:
            tangents[i] /= norm

    normals = np.zeros_like(pts)
    binormals = np.zeros_like(pts)

    t0 = tangents[0]
    if abs(t0[2]) < 0.9:
        up = np.array([0, 0, 1], dtype=float)
    else:
        up = np.array([1, 0, 0], dtype=float)
    n0 = np.cross(t0, up)
    n0 /= np.linalg.norm(n0) + 1e-12
    normals[0] = n0
    binormals[0] = np.cross(t0, n0)

    for i in range(1, n):
        v1 = pts[i] - pts[i-1]
        c1 = np.dot(v1, v1) + 1e-12
        rL = normals[i-1] - (2/c1) * np.dot(v1, normals[i-1]) * v1
        tL = tangents[i-1] - (2/c1) * np.dot(v1, tangents[i-1]) * v1
        v2 = tangents[i] - tL
        c2 = np.dot(v2, v2) + 1e-12
        normals[i] = rL - (2/c2) * np.dot(v2, rL) * v2
        nn = np.linalg.norm(normals[i])
        if nn > 1e-12:
            normals[i] /= nn
        binormals[i] = np.cross(tangents[i], normals[i])

    return tangents, normals, binormals

def eval_float_curve(x, control_points):
    """Piecewise-linear interpolation of a float curve."""

    if x <= control_points[0][0]:
        return control_points[0][1]
    if x >= control_points[-1][0]:
        return control_points[-1][1]
    for i in range(len(control_points) - 1):
        x0, y0 = control_points[i]
        x1, y1 = control_points[i + 1]
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0 + 1e-12)
            return y0 + t * (y1 - y0)
    return control_points[-1][1]

def _hash_int(ix, iy, seed=0):
    """Deterministic integer hash -> float in [0,1]."""

    h = (ix * 1234567 + iy * 7654321 + seed * 9876543 + 42) & 0xFFFFFFFF
    h = ((h >> 16) ^ h) * 0x45d9f3b & 0xFFFFFFFF
    h = ((h >> 16) ^ h) * 0x45d9f3b & 0xFFFFFFFF
    h = (h >> 16) ^ h
    return (h & 0xFFFF) / 65536.0

def value_noise_2d(x, y, scale=1.0, seed=0):
    """Smooth 2D value noise with bilinear interpolation + smoothstep."""

    x *= scale
    y *= scale
    ix = int(math.floor(x))
    iy = int(math.floor(y))
    fx = x - ix
    fy = y - iy
    v00 = _hash_int(ix, iy, seed)
    v10 = _hash_int(ix + 1, iy, seed)
    v01 = _hash_int(ix, iy + 1, seed)
    v11 = _hash_int(ix + 1, iy + 1, seed)
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    return (v00 * (1-fx) * (1-fy) + v10 * fx * (1-fy) +
            v01 * (1-fx) * fy + v11 * fx * fy)

def value_noise_3d(x, y, z, scale=1.0, seed=0):
    """Smooth 3D value noise with trilinear interpolation + smoothstep."""

    x *= scale
    y *= scale
    z *= scale
    ix = int(math.floor(x))
    iy = int(math.floor(y))
    iz = int(math.floor(z))
    fx = x - ix
    fy = y - iy
    fz = z - iz

    def h(i, j, k):
        return _hash_int(i * 997 + k * 3571, j * 2741 + k * 5113, seed)

    v000 = h(ix, iy, iz); v100 = h(ix+1, iy, iz)
    v010 = h(ix, iy+1, iz); v110 = h(ix+1, iy+1, iz)
    v001 = h(ix, iy, iz+1); v101 = h(ix+1, iy, iz+1)
    v011 = h(ix, iy+1, iz+1); v111 = h(ix+1, iy+1, iz+1)

    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    fz = fz * fz * (3 - 2 * fz)
    v00 = v000 * (1-fx) + v100 * fx
    v10 = v010 * (1-fx) + v110 * fx
    v01 = v001 * (1-fx) + v101 * fx
    v11 = v011 * (1-fx) + v111 * fx
    v0 = v00 * (1-fy) + v10 * fy
    v1 = v01 * (1-fy) + v11 * fy
    return v0 * (1-fz) + v1 * fz

# ── plant seed (teardrop shape) ──────────────────────────────────────────────

def build_plant_seed(dimensions, u_res=6, v_res=6):
    """

    Build a teardrop-shaped seed matching nodegroup_plant_seed.
    Straight spine along X with FloatCurve-controlled radius profile.
    """

    length = dimensions[0]
    rad_y = dimensions[1]

    # Source QuadraticBezier: Start=(0,0,0), Mid=(length/2, 0, 0), End=(length, 0, 0)
    # This is a straight line along X — the teardrop comes from radius variation
    start = np.array([0, 0, 0])
    mid = np.array([length * 0.5, 0, 0])
    end = np.array([length, 0, 0])
    spine = sample_quadratic_bezier(start, mid, end, u_res)

    # FloatCurve for radius: teardrop (fat at ~0.32, thin at ends)
    float_curve_pts = [(0.0, 0.0), (0.3159, 0.4469), (1.0, 0.0156)]

    bm = bmesh.new()
    rings = []
    for i in range(u_res):
        t = i / max(u_res - 1, 1)
        fc_val = eval_float_curve(t, float_curve_pts)
        # MapRange 0..1 -> 0..3, then scale by circle radius
        radius = fc_val * 3.0 * rad_y
        pos = spine[i]

        ring = []
        for j in range(v_res):
            theta = 2 * math.pi * j / v_res
            vx = pos[0]
            vy = pos[1] + radius * math.cos(theta)
            vz = pos[2] + radius * math.sin(theta)
            ring.append(bm.verts.new((vx, vy, vz)))
        rings.append(ring)

    for i in range(u_res - 1):
        for j in range(v_res):
            j2 = (j + 1) % v_res
            bm.faces.new([rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]])

    if u_res > 1:
        bot = bm.verts.new(tuple(spine[0]))
        for j in range(v_res):
            j2 = (j + 1) % v_res
            bm.faces.new([bot, rings[0][j2], rings[0][j]])
        top = bm.verts.new(tuple(spine[-1]))
        for j in range(v_res):
            j2 = (j + 1) % v_res
            bm.faces.new([top, rings[-1][j], rings[-1][j2]])

    mesh = bpy.data.meshes.new("seed")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("seed", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

# ── flower petal ─────────────────────────────────────────────────────────────

def build_petal(length, base_width, upper_width, bevel_exp=1.83,
                point=0.56, point_height=-0.1, wrinkle=0.01, curl=0.5,
                res_h=8, res_v=16):
    """

    Build one flower petal matching nodegroup_flower_petal + follow_curve.

    1. Create MeshGrid (Vertices_X=res_v, Vertices_Y=res_h*2+1)
    2. Deform: X=wrinkle noise, Y=width*bevel, Z=along-petal*tip_shaping
    3. Warp along QuadraticBezier curl curve via follow_curve
    """

    n_along = res_v           # vertices along petal (X axis of MeshGrid)
    n_across = res_h * 2 + 1  # vertices across petal (Y axis of MeshGrid)

    # Grid positions: X from -0.5..0.5, Y from -0.5..0.5
    grid_x = np.linspace(-0.5, 0.5, n_along)
    grid_y = np.linspace(-0.5, 0.5, n_across)

    # Deform grid to petal shape: (wrinkle_X, width_Y, along_Z)
    verts_flat = []
    for ix in range(n_along):
        x_orig = grid_x[ix]
        x_norm = x_orig + 0.5  # 0..1 normalized along-petal

        for iy in range(n_across):
            y_orig = grid_y[iy]
            abs_y = abs(y_orig)

            # Bevel mask: 1 - (|Y|*2)^Bevel
            bevel_mask = max(0.0, 1.0 - (abs_y * 2) ** bevel_exp)

            # Width: Y * (x_norm * bevel_mask * upper_width + base_width)
            y_new = y_orig * (x_norm * bevel_mask * upper_width + base_width)

            # Point/tip shaping:
            # (1 - |Y|^point) * point_height + (1 - point_height)  ->  multiplied by bevel_mask & x_norm
            tip_factor = (1.0 - abs_y ** max(point, 0.01)) * point_height
            tip_rest = 1.0 - point_height
            z_new = x_norm * (tip_factor + tip_rest) * bevel_mask

            # Wrinkle: smooth 2D noise (source: NoiseTexture 2D, scale=7.9)
            nx = value_noise_2d(0.05 * x_orig, y_orig, scale=7.9, seed=42)
            x_wrinkle = (nx - 0.5) * wrinkle

            verts_flat.append(np.array([x_wrinkle, y_new, z_new]))

    verts_flat = np.array(verts_flat)

    # Build QuadraticBezier curl curve
    # Source: Start=(0,0,0), Mid=(0, Length/2, 0),
    #   End = polar_to_cart(Addend=(0,L/2,0), Value=Curl, Vector=L/2)
    #       = (0, L/2 + L/2*cos(Curl), L/2*sin(Curl))
    half_len = length * 0.5
    bezier_start = np.array([0, 0, 0])
    bezier_mid = np.array([0, half_len, 0])
    bezier_end = np.array([0,
                           half_len + half_len * math.cos(curl),
                           half_len * math.sin(curl)])

    n_curve_samples = 64
    curve_pts = sample_quadratic_bezier(bezier_start, bezier_mid, bezier_end, n_curve_samples)
    tangents, normals, binormals = compute_curve_frames(curve_pts)

    # Cumulative arc lengths
    arc_lengths = np.zeros(n_curve_samples)
    for i in range(1, n_curve_samples):
        arc_lengths[i] = arc_lengths[i-1] + np.linalg.norm(curve_pts[i] - curve_pts[i-1])
    total_length = arc_lengths[-1] + 1e-12

    # Follow curve: warp each vertex
    # Source: Z maps to position along curve, X to binormal offset, Y to normal offset
    verts_warped = np.zeros_like(verts_flat)
    z_vals = verts_flat[:, 2]
    z_min = z_vals.min()
    z_max = z_vals.max()

    for vi in range(len(verts_flat)):
        vx, vy, vz = verts_flat[vi]

        # Map Z to [0, 1] along the curve (CurveMin=0, CurveMax=1)
        if z_max - z_min > 1e-12:
            t_curve = (vz - z_min) / (z_max - z_min)
        else:
            t_curve = 0.0
        t_curve = np.clip(t_curve, 0.0, 1.0)

        # Find position along curve at this arc length fraction
        target_len = t_curve * total_length
        idx = np.searchsorted(arc_lengths, target_len) - 1
        idx = max(0, min(idx, n_curve_samples - 2))
        seg_len = arc_lengths[idx+1] - arc_lengths[idx]
        if seg_len > 1e-12:
            seg_t = (target_len - arc_lengths[idx]) / seg_len
        else:
            seg_t = 0.0
        seg_t = np.clip(seg_t, 0.0, 1.0)

        pos = curve_pts[idx] + seg_t * (curve_pts[idx+1] - curve_pts[idx])
        tang = tangents[idx] + seg_t * (tangents[idx+1] - tangents[idx])
        norm = normals[idx] + seg_t * (normals[idx+1] - normals[idx])
        nn = np.linalg.norm(norm)
        if nn > 1e-12:
            norm /= nn
        binorm = np.cross(tang, norm)
        bn = np.linalg.norm(binorm)
        if bn > 1e-12:
            binorm /= bn

        # Source: Position = curve_pos, Offset = cross(T,N)*X + N*Y
        verts_warped[vi] = pos + binorm * vx + norm * vy

    # Build mesh
    bm = bmesh.new()
    bm_verts = []
    for v in verts_warped:
        bm_verts.append(bm.verts.new(tuple(v)))

    for ix in range(n_along - 1):
        for iy in range(n_across - 1):
            i00 = ix * n_across + iy
            i01 = ix * n_across + iy + 1
            i10 = (ix + 1) * n_across + iy
            i11 = (ix + 1) * n_across + iy + 1
            bm.faces.new([bm_verts[i00], bm_verts[i01],
                          bm_verts[i11], bm_verts[i10]])

    mesh = bpy.data.meshes.new("petal")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("petal", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

# ── center disc with seeds ──────────────────────────────────────────────────

def build_center(center_rad, seed_size):
    """

    Flattened UV sphere + teardrop seeds via golden-angle distribution.
    Matches geo_flower center: UV sphere (8 seg, 8 rings), scaled Z=0.05.
    """

    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=8, radius=center_rad, location=(0, 0, 0))
    center = bpy.context.active_object
    center.scale.z = 0.05
    apply_tf(center)

    parts = [center]

    seed_len = seed_size * 10
    seed_template = build_plant_seed((seed_len, seed_size, seed_size), u_res=6, v_res=6)
    # Source rotation: (0, -pi/2, 0.0541) — seed points upward from center surface
    seed_template.rotation_euler = (0, -math.pi / 2, 0.0541)
    apply_tf(seed_template)

    golden = 2.39996
    min_dist = seed_size * 1.5
    n_seeds = max(3, int((center_rad / max(min_dist, 0.001))**2 * 3))
    n_seeds = min(n_seeds, 60)

    rng = np.random.default_rng(SEED + 10)
    for i in range(n_seeds):
        t = (i + 0.5) / n_seeds
        r = center_rad * math.sqrt(t) * 0.9
        angle = golden * i
        x = r * math.cos(angle)
        y = r * math.sin(angle)

        sx = float(rng.uniform(0.34, 1.21))
        seed_inst = seed_template.copy()
        seed_inst.data = seed_template.data.copy()
        bpy.context.scene.collection.objects.link(seed_inst)
        seed_inst.scale = (sx, 1.0, 1.0)
        seed_inst.location = (x, y, 0)
        apply_tf(seed_inst)
        parts.append(seed_inst)

    bpy.ops.object.select_all(action="DESELECT")
    seed_template.select_set(True)
    bpy.ops.object.delete()

    return join_objs(parts)

# ── main ──────────────────────────────────────────────────────────────────────

def get_flower_params(overall_rad=0.15):
    """Matches FlowerFactory.get_flower_params (source line 912-930)."""

    pct_inner = np.random.uniform(0.05, 0.4)
    base_width = 2 * np.pi * overall_rad * pct_inner / np.random.normal(20, 5)
    base_width = max(base_width, 0.001)
    top_width = overall_rad * np.clip(np.random.normal(0.7, 0.3), base_width * 1.2, 100)

    min_angle, max_angle = np.deg2rad(np.sort(np.random.uniform(-20, 100, 2)))

    # Source: subtract(top_width, base_width) with use_clamp=True -> clamp to [0, 1]
    upper_width = np.clip(top_width - base_width, 0.0, 1.0)

    return {
        "center_rad": overall_rad * pct_inner,
        "petal_length": overall_rad * (1 - pct_inner),
        "base_width": base_width,
        "upper_width": upper_width,
        "seed_size": np.random.uniform(0.005, 0.01),
        "min_petal_angle": min_angle,
        "max_petal_angle": max_angle,
        "wrinkle": np.random.uniform(0.003, 0.02),
        "curl": np.deg2rad(np.random.normal(30, 50)),
    }

def build_flower():
    np.random.seed(SEED)
    clear_scene()

    overall_rad = 0.15
    params = get_flower_params(overall_rad)

    center_rad = params["center_rad"]
    petal_length = params["petal_length"]
    base_width = params["base_width"]
    upper_width = params["upper_width"]
    wrinkle = params["wrinkle"]
    curl = params["curl"]

    # Center disc with seeds -> CENTER_MAT (orange/brown flower center)
    center = build_center(center_rad, params["seed_size"])
    center.data.materials.append(CENTER_MAT)

    # Petal count: 2*pi*center_rad / base_width * 1.2 (matches source)
    circ = 2 * math.pi * center_rad
    n_petals = max(4, int(circ / max(base_width, 1e-4) * 1.2))
    n_petals = min(n_petals, 80)

    # Build petal template -> PETAL_MAT (bright colorful petal shader)
    petal_template = build_petal(
        length=petal_length,
        base_width=base_width,
        upper_width=upper_width,
        bevel_exp=1.83,
        point=0.56,
        point_height=-0.1,
        wrinkle=wrinkle,
        curl=curl,
        res_h=8,
        res_v=16
    )
    petal_template.data.materials.append(PETAL_MAT)

    # Distribute petals using phyllotaxis pattern
    # Source: position at (center_rad*cos(i), center_rad*sin(i), 0)
    # Source: yaw = index + yaw_offset = i + (-pi/2) = i - pi/2
    # Source: elevation interpolates from min_angle to max_angle over t=i/count
    parts = [center]
    rng = np.random.default_rng(SEED + 20)

    for i in range(n_petals):
        t = i / max(n_petals - 1, 1)

        # Position: cos/sin of raw index (NOT golden angle)
        px = center_rad * math.cos(i)
        py = center_rad * math.sin(i)

        # Yaw: raw index - pi/2 (makes petal face radially outward)
        yaw = i - math.pi / 2

        # Elevation: interpolate min_angle -> max_angle
        elevation = params["min_petal_angle"] + t * (params["max_petal_angle"] - params["min_petal_angle"])
        elevation += float(rng.uniform(-0.1, 0.1))

        petal = petal_template.copy()
        petal.data = petal_template.data.copy()
        bpy.context.scene.collection.objects.link(petal)

        petal.rotation_euler = (elevation, float(rng.uniform(-0.1, 0.1)), yaw)
        petal.location = (px, py, 0)
        apply_tf(petal)
        parts.append(petal)

    # Delete template
    bpy.ops.object.select_all(action="DESELECT")
    petal_template.select_set(True)
    bpy.ops.object.delete()

    result = join_objs(parts)

    # Post-instance noise displacement (0.025 amplitude)
    # Source: NoiseTexture(scale=3.73, detail=5.41, distortion=-1.0)
    mesh = result.data
    for v in mesh.vertices:
        co = v.co
        nx = value_noise_3d(co.x, co.y, co.z, scale=3.73, seed=100) - 0.5
        ny = value_noise_3d(co.x, co.y, co.z, scale=3.73, seed=200) - 0.5
        nz = value_noise_3d(co.x, co.y, co.z, scale=3.73, seed=300) - 0.5
        v.co.x += nx * 0.025
        v.co.y += ny * 0.025
        v.co.z += nz * 0.025
    mesh.update()

    result.rotation_euler.z = np.random.uniform(0, 2 * math.pi)
    apply_tf(result)

    # Per-part materials were appended to center + petal_template before copies + join;
    # Blender preserves the two material slots through copy + join operations.
    if len(result.data.materials) == 0:
        result.data.materials.append(PETAL_MAT)

    result.name = "FlowerFactory"
    return result

flower = build_flower()
