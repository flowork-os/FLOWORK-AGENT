# [FL_INDEX: keywords="blender_factory, procedural_3d, DandelionSeedFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: DandelionSeedFactory | Category: factories_geo
# Prompt: A 3D model of an individual dandelion seed rendered from a slightly elevated angle, featuring a small dark brown elongated achene at the bottom connected by a thin stalk to a radiating umbrella-like pappus of fine white filaments that spread outward in a delicate parasol shape.

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

def make_category_mat(seed, name="BrownStemMaterial"):
    """Brown stem/dried plant: near-black brown with faint red tint, noise-driven roughness.
    RGB formula: v = U(0.01, 0.2); color = (v, v*U(0,0.15), v*U(0,0.12), 1).
    Diffuse-only Principled BSDF (no translucent/glossy), roughness driven by 4D noise → MapRange."""

    _seed_mat(seed)
    v = float(np.random.uniform(0.01, 0.2))
    r = v
    g = v * float(np.random.uniform(0, 0.15))
    b = v * float(np.random.uniform(0, 0.12))
    base_color = (r, g, b, 1.0)

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    noise = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise.noise_dimensions = "4D"
    except Exception:
        pass
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = float(np.random.uniform(0, 100))
    noise.inputs["Scale"].default_value = float(np.random.normal(60, 25))
    noise.inputs["Detail"].default_value = float(np.random.uniform(0, 10))
    noise.inputs["Roughness"].default_value = float(np.random.uniform(0, 1))
    noise.inputs["Distortion"].default_value = float(np.random.uniform(0, 3))

    # MapRange (SMOOTHSTEP) mapping noise factor → roughness
    mr = nt.nodes.new("ShaderNodeMapRange")
    try:
        mr.interpolation_type = "SMOOTHSTEP"
    except Exception:
        pass
    ln(_fac(noise), mr.inputs["Value"])
    # inputs 3 and 4 are "To Min" and "To Max"
    mr.inputs[3].default_value = float(np.random.uniform(0.1, 0.8))
    mr.inputs[4].default_value = float(np.random.uniform(0.1, 0.8))

    # Diffuse-only Principled BSDF (no translucent/glossy mix)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    ln(mr.outputs["Result"], bsdf.inputs["Roughness"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_white_mat(seed, name="WhitePappusMaterial"):
    _seed_mat(seed)
    v = float(np.random.uniform(0.7, 1.0))
    base_color = (
        v * (1.0 + float(np.random.normal(0, 0.05))),
        v * (1.0 + float(np.random.normal(0, 0.05))),
        v * (1.0 + float(np.random.normal(0, 0.05))),
        1.0,
    )

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    noise = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise.noise_dimensions = "4D"
    except Exception:
        pass
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = float(np.random.uniform(0, 100))
    noise.inputs["Scale"].default_value = float(np.random.normal(60, 25))
    noise.inputs["Detail"].default_value = float(np.random.uniform(0, 10))
    noise.inputs["Roughness"].default_value = float(np.random.uniform(0, 1))
    noise.inputs["Distortion"].default_value = float(np.random.uniform(0, 3))
    mr = nt.nodes.new("ShaderNodeMapRange")
    try:
        mr.interpolation_type = "SMOOTHSTEP"
    except Exception:
        pass
    ln(_fac(noise), mr.inputs["Value"])
    mr.inputs[3].default_value = float(np.random.uniform(0.1, 0.8))
    mr.inputs[4].default_value = float(np.random.uniform(0.1, 0.8))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    ln(mr.outputs["Result"], bsdf.inputs["Roughness"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def assign_material(obj, mat):
    if obj is not None and hasattr(obj, "data") and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(mat)

CATEG_MAT = BROWN_MAT = make_category_mat(SEED, "DandelionSeedFactory_BrownSeed")
WHITE_MAT = make_white_mat(SEED, "DandelionSeedFactory_WhitePappus")
for _mat in (BROWN_MAT, WHITE_MAT):
    _mat.use_fake_user = True

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
    valid = [o for o in objs if o is not None and o.name in bpy.data.objects]
    if not valid:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in valid:
        o.select_set(True)
    bpy.context.view_layer.objects.active = valid[0]
    if len(valid) > 1:
        bpy.ops.object.join()
    return bpy.context.active_object

# ── math helpers ─────────────────────────────────────────────────────────────

def sample_quadratic_bezier(start, mid, end, n):
    pts = []
    for i in range(n):
        t = i / max(n - 1, 1)
        p = (1-t)**2 * np.array(start) + 2*(1-t)*t * np.array(mid) + t**2 * np.array(end)
        pts.append(p)
    return np.array(pts)

def eval_float_curve(x, cps):
    if x <= cps[0][0]:
        return cps[0][1]
    if x >= cps[-1][0]:
        return cps[-1][1]
    for i in range(len(cps) - 1):
        x0, y0 = cps[i]
        x1, y1 = cps[i + 1]
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0 + 1e-12)
            return y0 + t * (y1 - y0)
    return cps[-1][1]

def build_tube_mesh(points, radius_func, n_circle=8, name="tube"):
    n_pts = len(points)
    if n_pts < 2:
        return None

    bm = bmesh.new()
    rings = []

    for i in range(n_pts):
        t = i / max(n_pts - 1, 1)
        r = radius_func(t)
        pos = points[i]

        if i == 0:
            tang = points[1] - points[0]
        elif i == n_pts - 1:
            tang = points[-1] - points[-2]
        else:
            tang = points[i+1] - points[i-1]
        tn = np.linalg.norm(tang)
        if tn > 1e-12:
            tang /= tn

        if abs(tang[2]) < 0.9:
            up = np.array([0, 0, 1], dtype=float)
        else:
            up = np.array([1, 0, 0], dtype=float)
        perp1 = np.cross(tang, up)
        pn = np.linalg.norm(perp1)
        if pn > 1e-12:
            perp1 /= pn
        perp2 = np.cross(tang, perp1)

        ring = []
        for j in range(n_circle):
            theta = 2 * math.pi * j / n_circle
            offset = r * (math.cos(theta) * perp1 + math.sin(theta) * perp2)
            ring.append(bm.verts.new(tuple(pos + offset)))
        rings.append(ring)

    for i in range(n_pts - 1):
        for j in range(n_circle):
            j2 = (j + 1) % n_circle
            bm.faces.new([rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]])

    if n_pts > 1:
        bot = bm.verts.new(tuple(points[0]))
        for j in range(n_circle):
            j2 = (j + 1) % n_circle
            bm.faces.new([bot, rings[0][j2], rings[0][j]])
        top = bm.verts.new(tuple(points[-1]))
        for j in range(n_circle):
            j2 = (j + 1) % n_circle
            bm.faces.new([top, rings[-1][j], rings[-1][j2]])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

# ── head sphere (smooth, no studs) ───────────────────────────────────────────

def build_head_sphere(center, radius):
    """

    Matches nodegroup_petal_stem_head_geometry:
    Simple smooth UV sphere with 64 segments at the top of the seed.
    No cone studs — just a clean sphere.
    """

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64, ring_count=32,
        radius=radius, location=tuple(center)
    )
    sphere = bpy.context.active_object
    assign_material(sphere, BROWN_MAT)
    return sphere

# ── end sphere (ridged seed pod) ─────────────────────────────────────────────

def build_seed_pod(center, radius=0.04, scale=(1, 1, 1)):
    """

    Matches nodegroup_petal_stem_end_geometry:
    UV sphere (64 segments) stretched vertically, with a micro cone instanced
    at EVERY vertex aligned to the normal. This creates the visible horizontal
    ridge rings that characterize the dandelion seed pod.
    """
    # 1. Create the elongated sphere
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64, ring_count=32,
        radius=radius, location=tuple(center)
    )
    sphere = bpy.context.active_object
    sphere.scale = scale
    apply_tf(sphere)

    # 2. Collect vertex positions and normals
    mesh = sphere.data
    mesh.update()

    vert_positions = []
    vert_normals = []
    for v in mesh.vertices:
        vert_positions.append(np.array(v.co))
        vert_normals.append(np.array(v.normal))

    # 3. Instance a micro cone at every vertex, aligned to the normal
    cone_radius = 0.004
    cone_depth = 0.004
    parts = [sphere]

    # Use bmesh to create all cones efficiently in one mesh
    bm = bmesh.new()
    cone_verts_per = 5  # 4 base + 1 tip for each cone

    for vi in range(len(vert_positions)):
        pos = vert_positions[vi]
        nrm = vert_normals[vi]
        nn = np.linalg.norm(nrm)
        if nn < 1e-6:
            continue
        nrm = nrm / nn

        # Build local frame: nrm is the "up" direction of the cone
        if abs(nrm[2]) < 0.9:
            ref = np.array([0, 0, 1], dtype=float)
        else:
            ref = np.array([1, 0, 0], dtype=float)
        perp1 = np.cross(nrm, ref)
        p1n = np.linalg.norm(perp1)
        if p1n > 1e-12:
            perp1 /= p1n
        perp2 = np.cross(nrm, perp1)

        # Cone tip is at pos + nrm * cone_depth
        tip = pos + nrm * cone_depth
        tip_v = bm.verts.new(tuple(tip))

        # Base ring (4 vertices)
        base_verts = []
        for j in range(4):
            theta = 2 * math.pi * j / 4
            offset = cone_radius * (math.cos(theta) * perp1 + math.sin(theta) * perp2)
            base_verts.append(bm.verts.new(tuple(pos + offset)))

        # Faces: 4 triangular side faces
        for j in range(4):
            j2 = (j + 1) % 4
            bm.faces.new([tip_v, base_verts[j], base_verts[j2]])

        # Base face
        bm.faces.new(base_verts[::-1])

    cone_mesh = bpy.data.meshes.new("pod_cones")
    bm.to_mesh(cone_mesh)
    bm.free()
    cone_obj = bpy.data.objects.new("pod_cones", cone_mesh)
    bpy.context.scene.collection.objects.link(cone_obj)
    parts.append(cone_obj)

    result = join_objs(parts)
    assign_material(result, BROWN_MAT)
    return result

# ── petal stem (single seed unit with pappus) ────────────────────────────────

def build_petal_stem():
    """

    Build one petal_stem unit matching nodegroup_petal_stem.
    """

    top_point = np.array([0.0, 0.0, 1.0])
    mid_point = np.array([np.random.normal(0, 0.05),
                          np.random.normal(0, 0.05), 0.5])
    stem_radius = np.random.uniform(0.02, 0.045)
    top_radius = np.random.uniform(0.005, 0.008)
    branch_tube_radius = np.random.uniform(0.001, 0.0025)

    parts = []

    # 1. Body tube (QuadraticBezier, 8-sided profile, radius = stem_radius * 0.2)
    body_pts = sample_quadratic_bezier((0, 0, 0), mid_point, top_point, 24)
    actual_radius = stem_radius * 0.2

    body = build_tube_mesh(
        body_pts, lambda t: actual_radius, n_circle=8, name="ps_body"
    )
    assign_material(body, WHITE_MAT)
    parts.append(body)

    # 2. Pappus branches (40 filaments curving upward)
    n_branches = 40
    branch_length = 0.5
    z_height_mult = np.random.uniform(0.15, 0.4)

    # FloatCurve for upward Z-offset (smooth ascending curve)
    fc_pts = [
        (0.0, 0.0),
        (0.2, 0.08 * np.random.normal(1.0, 0.15)),
        (0.4, 0.22 * np.random.normal(1.0, 0.2)),
        (0.6, 0.45 * np.random.normal(1.0, 0.2)),
        (0.8, 0.70 * np.random.normal(1.0, 0.1)),
        (1.0, 1.0),
    ]

    # Contour curve for additional shape variation
    dist = np.random.uniform(-0.05, -0.25)
    contour_fc = [
        (0.0, 0.0),
        (0.2, 0.2 + (dist + np.random.normal(0, 0.05)) / 2.0),
        (0.4, 0.4 + (dist + np.random.normal(0, 0.05))),
        (0.6, 0.6 + (dist + np.random.normal(0, 0.05)) / 1.2),
        (0.8, 0.8 + (dist + np.random.normal(0, 0.05)) / 2.4),
        (1.0, 0.95 + np.random.normal(0, 0.05)),
    ]

    rng = np.random.default_rng(SEED + 50)
    for bi in range(n_branches):
        angle = 2 * math.pi * bi / n_branches
        dir_x = math.cos(angle)
        dir_y = math.sin(angle)

        # Per-branch contour scale (sampled ONCE, not per-point)
        contour_scale = float(rng.uniform(0.05, 0.35))

        # More sample points for smoother curves
        n_fil_pts = 40
        fil_pts = np.zeros((n_fil_pts, 3))
        for fi in range(n_fil_pts):
            t = fi / max(n_fil_pts - 1, 1)
            r = t * branch_length
            z_fc = eval_float_curve(t, fc_pts) * z_height_mult
            z_contour = eval_float_curve(t, contour_fc) * contour_scale

            fil_pts[fi] = [dir_x * r, dir_y * r, z_fc + z_contour]

        # Random rotation per branch (small perturbation — keep gentle)
        rot_x = float(rng.uniform(-0.08, 0.08))
        rot_y = float(rng.uniform(-0.08, 0.08))
        rot_z = float(rng.uniform(-0.08, 0.08))
        cx, sx = math.cos(rot_x), math.sin(rot_x)
        cy, sy = math.cos(rot_y), math.sin(rot_y)
        cz, sz = math.cos(rot_z), math.sin(rot_z)

        for fi in range(n_fil_pts):
            p = fil_pts[fi].copy()
            y2, z2 = cx*p[1] - sx*p[2], sx*p[1] + cx*p[2]
            p[1], p[2] = y2, z2
            x2, z2 = cy*p[0] + sy*p[2], -sy*p[0] + cy*p[2]
            p[0], p[2] = x2, z2
            x2, y2 = cz*p[0] - sz*p[1], sz*p[0] + cz*p[1]
            p[0], p[1] = x2, y2
            fil_pts[fi] = p

        scale = float(rng.uniform(0.8, 1.0))
        fil_pts *= scale
        fil_pts += top_point

        fil_obj = build_tube_mesh(
            fil_pts, lambda t: branch_tube_radius,
            n_circle=4, name=f"fil_{bi}"
        )
        if fil_obj is not None:
            assign_material(fil_obj, WHITE_MAT)
            parts.append(fil_obj)

    # 3. Head sphere at top (smooth, no studs — matches source)
    head = build_head_sphere(top_point, top_radius)
    parts.append(head)

    # 4. End sphere at base (ridged seed pod — cones on every vertex)
    end_scale = (np.random.uniform(0.45, 0.7),
                 np.random.uniform(0.45, 0.7),
                 np.random.uniform(2.0, 3.0))
    end = build_seed_pod((0, 0, 0), 0.04, scale=end_scale)
    parts.append(end)

    result = join_objs(parts)
    return result

# ── main ──────────────────────────────────────────────────────────────────────

def build_dandelion_seed():
    np.random.seed(SEED)
    clear_scene()

    seed = build_petal_stem()
    seed.name = "DandelionSeedFactory"
    return seed

result = build_dandelion_seed()
