# [FL_INDEX: keywords="blender_factory, procedural_3d, DandelionFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: DandelionFactory | Category: factories_tex
# Prompt: A 3D model of a dandelion in its seed-head (puffball) stage rendered from a slightly elevated perspective, featuring a spherical cluster of delicate, wispy white seed filaments atop a long, slender green stem that curves gently, with a soft shadow cast below.

import os
SEED = int(os.environ.get('SEED', 0))
import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

SEED = int(os.environ.get("SEED", 0))
random.seed(SEED)
np.random.seed(SEED)

# ── scene helpers ─────────────────────────────────────────────────────────────

import os as _os, random as _random, colorsys as _colorsys


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

def _make_rough_principled(seed, name, base_color):
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

def make_brown_mat(seed, name="BrownStemMaterial"):
    """Port of simple_brownish.py:shader_simple_brown."""

    v = float(np.random.uniform(0.01, 0.2))
    base_color = (v, v * float(np.random.uniform(0, 0.15)),
                  v * float(np.random.uniform(0, 0.12)), 1.0)
    return _make_rough_principled(seed + 101, name, base_color)

def make_white_mat(seed, name="WhitePappusMaterial"):
    """Port of simple_whitish.py:shader_simple_white."""

    v = float(np.random.uniform(0.7, 1.0))
    base_color = (
        v * (1.0 + float(np.random.normal(0, 0.05))),
        v * (1.0 + float(np.random.normal(0, 0.05))),
        v * (1.0 + float(np.random.normal(0, 0.05))),
        1.0,
    )
    return _make_rough_principled(seed + 202, name, base_color)

def assign_material(obj, mat):
    if obj is not None and hasattr(obj, "data") and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(mat)

CATEG_MAT = GREEN_MAT = make_category_mat(SEED, "DandelionFactory_StemGreen")
BROWN_MAT = make_brown_mat(SEED, "DandelionFactory_BrownSeed")
WHITE_MAT = make_white_mat(SEED, "DandelionFactory_WhitePappus")
for _mat in (GREEN_MAT, BROWN_MAT, WHITE_MAT):
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

def delete_obj(obj):
    if obj is not None and obj.name in bpy.data.objects:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.ops.object.delete()

# ── math helpers ─────────────────────────────────────────────────────────────

def sample_quadratic_bezier(start, mid, end, n):
    """Sample n points along a quadratic Bezier curve."""

    pts = []
    for i in range(n):
        t = i / max(n - 1, 1)
        p = (1-t)**2 * np.array(start) + 2*(1-t)*t * np.array(mid) + t**2 * np.array(end)
        pts.append(p)
    return np.array(pts)

def eval_float_curve(x, cps):
    """Piecewise-linear float curve evaluation."""

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
    """

    Build a tube mesh along a polyline path with variable radius.
    radius_func(t) returns radius at parameter t in [0, 1].
    """

    n_pts = len(points)
    if n_pts < 2:
        return None

    bm = bmesh.new()
    rings = []

    for i in range(n_pts):
        t = i / max(n_pts - 1, 1)
        r = radius_func(t)
        pos = points[i]

        # Compute local frame
        if i == 0:
            tang = points[1] - points[0]
        elif i == n_pts - 1:
            tang = points[-1] - points[-2]
        else:
            tang = points[i+1] - points[i-1]
        tn = np.linalg.norm(tang)
        if tn > 1e-12:
            tang /= tn

        # Find perpendicular vectors
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

    # Build quad faces
    for i in range(n_pts - 1):
        for j in range(n_circle):
            j2 = (j + 1) % n_circle
            bm.faces.new([rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]])

    # End caps
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
    bpy.context.collection.objects.link(obj)
    return obj

# ── stem geometry ────────────────────────────────────────────────────────────

def build_stem(stem_radius, n_circle=10):
    """

    Matches nodegroup_stem_geometry + geometry_dandelion_nodes stem:
    QuadraticBezier from (0,0,0) through random mid to random end.
    Radius taper from 0.4 at tip to uniform(0.2,0.4) at base.
    """

    mid = (np.random.normal(0, 0.1), np.random.normal(0, 0.1), 0.5)
    end = (np.random.normal(0, 0.1), np.random.normal(0, 0.1), 1.0)
    pts = sample_quadratic_bezier((0, 0, 0), mid, end, 32)

    base_radius_factor = np.random.uniform(0.2, 0.4)

    def radius_fn(t):
        # MapRange: Factor 0..1 -> 0.4 (tip) .. base_val
        # At t=0 (start/base): factor=0 -> radius=0.4
        # At t=1 (top/tip): factor=1 -> radius=base_radius_factor
        # Wait, source maps SplineParameter Factor -> MapRange(0..1 -> 0.4..base_val)
        # SplineParameter Factor goes 0 at start, 1 at end
        # So at start (base): radius = 0.4 * stem_radius
        # At end (tip): radius = base_val * stem_radius
        r = (0.4 + (base_radius_factor - 0.4) * t) * stem_radius
        return max(r, 0.001)

    obj = build_tube_mesh(pts, radius_fn, n_circle=n_circle, name="stem")
    assign_material(obj, GREEN_MAT)
    return obj, pts[-1]  # return top position

# ── petal stem head/end with cone studs ──────────────────────────────────────

def build_sphere_with_studs(center, radius, scale=(1, 1, 1), n_segments=16, n_cones=0):
    """

    UV sphere with cone studs on surface.
    Matches petal_stem_head_geometry and petal_stem_end_geometry.
    """

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=n_segments, ring_count=max(n_segments // 2, 4),
        radius=radius, location=tuple(center)
    )
    sphere = bpy.context.active_object
    sphere.scale = scale
    apply_tf(sphere)

    if n_cones > 0:
        parts = [sphere]
        # Add cone studs on surface
        golden = 2.39996
        for i in range(n_cones):
            t = (i + 0.5) / n_cones
            incl = math.acos(1 - 2 * t)
            azimuth = golden * i
            nx = math.sin(incl) * math.cos(azimuth)
            ny = math.sin(incl) * math.sin(azimuth)
            nz = math.cos(incl)

            cx = center[0] + nx * radius * scale[0]
            cy = center[1] + ny * radius * scale[1]
            cz = center[2] + nz * radius * scale[2]

            bpy.ops.mesh.primitive_cone_add(
                vertices=4, radius1=0.004, depth=0.004,
                location=(cx, cy, cz)
            )
            cone = bpy.context.active_object
            # Align cone to surface normal
            cone.rotation_euler = (
                math.atan2(ny, math.sqrt(nx*nx + nz*nz + 1e-12)),
                0,
                math.atan2(-nx, nz + 1e-12)
            )
            apply_tf(cone)
            parts.append(cone)
        sphere = join_objs(parts)

    assign_material(sphere, BROWN_MAT)
    return sphere

# ── petal stem (single seed unit with pappus) ────────────────────────────────

def build_petal_stem():
    """

    Build one petal_stem unit matching nodegroup_petal_stem.
    Components:
    1. Body: QuadraticBezier tube
    2. Pappus branches: 40 filaments curving upward
    3. Head sphere at top
    4. End sphere at base endpoint
    """
    # Petal stem parameters
    top_point = np.array([0.0, 0.0, 1.0])
    mid_point = np.array([np.random.normal(0, 0.05),
                          np.random.normal(0, 0.05), 0.5])
    stem_radius = np.random.uniform(0.02, 0.045)
    top_radius = np.random.uniform(0.005, 0.008)
    branch_tube_radius = np.random.uniform(0.001, 0.0025)

    parts = []

    # 1. Body tube: QuadraticBezier from origin to top_point
    body_pts = sample_quadratic_bezier((0, 0, 0), mid_point, top_point, 16)
    profile_radius = 0.2  # CurveCircle radius in source
    actual_radius = stem_radius * profile_radius

    body = build_tube_mesh(
        body_pts, lambda t: actual_radius, n_circle=8, name="ps_body"
    )
    assign_material(body, WHITE_MAT)
    parts.append(body)

    # 2. Pappus branches: 40 filaments on a circle at top_point
    n_branches = 40
    branch_length = 0.5
    z_height_mult = np.random.uniform(0.15, 0.4)

    # FloatCurve for branch Z-offset shape
    fc_pts = [
        (0.0, 0.0),
        (0.2, 0.08 * np.random.normal(1.0, 0.15)),
        (0.4, 0.22 * np.random.normal(1.0, 0.2)),
        (0.6, 0.45 * np.random.normal(1.0, 0.2)),
        (0.8, 0.70 * np.random.normal(1.0, 0.1)),
        (1.0, 1.0),
    ]

    # Branch contour FloatCurve
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

        # Direction on circle (outward from center in XY plane)
        dir_x = math.cos(angle)
        dir_y = math.sin(angle)

        # Build filament points along the branch
        n_fil_pts = 20
        fil_pts = np.zeros((n_fil_pts, 3))
        for fi in range(n_fil_pts):
            t = fi / max(n_fil_pts - 1, 1)
            # X-Y: radial outward
            r = t * branch_length
            # Z: FloatCurve shape * height multiplier
            z_fc = eval_float_curve(t, fc_pts) * z_height_mult

            # Additional contour offset
            contour_scale = float(rng.uniform(0.05, 0.35))
            z_contour = eval_float_curve(t, contour_fc) * contour_scale

            fil_pts[fi] = [
                dir_x * r,
                dir_y * r,
                z_fc + z_contour
            ]

        # Random rotation +/-0.2 each axis
        rot_x = float(rng.uniform(-0.2, 0.2))
        rot_y = float(rng.uniform(-0.2, 0.2))
        rot_z = float(rng.uniform(-0.2, 0.2))
        cx, sx = math.cos(rot_x), math.sin(rot_x)
        cy, sy = math.cos(rot_y), math.sin(rot_y)
        cz, sz = math.cos(rot_z), math.sin(rot_z)

        for fi in range(n_fil_pts):
            p = fil_pts[fi].copy()
            # Rotate X
            y2, z2 = cx*p[1] - sx*p[2], sx*p[1] + cx*p[2]
            p[1], p[2] = y2, z2
            # Rotate Y
            x2, z2 = cy*p[0] + sy*p[2], -sy*p[0] + cy*p[2]
            p[0], p[2] = x2, z2
            # Rotate Z
            x2, y2 = cz*p[0] - sz*p[1], sz*p[0] + cz*p[1]
            p[0], p[1] = x2, y2
            fil_pts[fi] = p

        # Random scale 0.8-1.0
        scale = float(rng.uniform(0.8, 1.0))
        fil_pts *= scale

        # Translate to top_point
        fil_pts += top_point

        # Build thin tube for this filament
        fil_obj = build_tube_mesh(
            fil_pts, lambda t: branch_tube_radius,
            n_circle=4, name=f"fil_{bi}"
        )
        if fil_obj is not None:
            assign_material(fil_obj, WHITE_MAT)
            parts.append(fil_obj)

    # 3. Head sphere at top (small sphere with cone studs)
    head = build_sphere_with_studs(
        top_point, top_radius,
        scale=(np.random.uniform(0.45, 0.7),
               np.random.uniform(0.45, 0.7),
               np.random.uniform(2.0, 3.0)),
        n_segments=12, n_cones=8
    )
    assign_material(head, BROWN_MAT)
    parts.append(head)

    # 4. End sphere at base
    end = build_sphere_with_studs(
        (0, 0, 0), 0.04,
        scale=(np.random.uniform(0.45, 0.7),
               np.random.uniform(0.45, 0.7),
               np.random.uniform(2.0, 3.0)),
        n_segments=12, n_cones=6
    )
    assign_material(end, BROWN_MAT)
    parts.append(end)

    result = join_objs(parts)
    return result

# ── flower geometry (core sphere + petal_stem instances) ─────────────────────

def build_flower_geometry(mode_params):
    """

    Matches nodegroup_flower_geometry:
    UV sphere core + petal_stem instances aligned to normals.
    """

    num_segments = np.random.randint(8, 25)
    num_rings = np.random.randint(8, 20)
    core_radius = np.random.uniform(0.02, 0.05)

    core_scale = (np.random.uniform(0.8, 1.2),
                  np.random.uniform(0.8, 1.2),
                  np.random.uniform(0.5, 0.8))

    # Create core sphere
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=num_segments, ring_count=num_rings,
        radius=core_radius, location=(0, 0, 0)
    )
    core = bpy.context.active_object
    core.scale = core_scale
    apply_tf(core)
    assign_material(core, WHITE_MAT)

    # Get surface points and normals for instancing
    mesh = core.data
    mesh.update()

    # Calculate face centers and normals for petal_stem placement
    face_centers = []
    face_normals = []
    for poly in mesh.polygons:
        face_centers.append(np.array(poly.center))
        face_normals.append(np.array(poly.normal))

    # Apply selection mask
    random_dropout = mode_params["random_dropout"]
    row_lt = mode_params["row_less_than"]
    row_gt = mode_params["row_great_than"]
    col_lt = mode_params["col_less_than"]
    col_gt = mode_params["col_great_than"]

    rng = np.random.default_rng(SEED + 100)

    n_faces = len(face_centers)
    selected = []
    for fi in range(n_faces):
        # Random dropout check
        if rng.random() > random_dropout:
            continue

        # Row/column selection
        row = fi // num_segments
        col = fi % num_segments

        # Row check: must be in range (row_gt*num_rings, row_lt*num_rings)
        # Source: NAND of (row_in_range AND col_in_range)
        row_in = (row < row_lt * num_rings) and (row > row_gt * num_rings)
        col_in = (col < col_lt * num_segments) and (col > col_gt * num_segments)

        # NAND: not(row_in and col_in) - removes the specified region
        if not (row_in and col_in):
            selected.append(fi)

    # Build petal_stem template
    petal_stem = build_petal_stem()
    if petal_stem is None:
        return core

    parts = [core]

    for fi in selected:
        center = face_centers[fi]
        normal = face_normals[fi]
        nn = np.linalg.norm(normal)
        if nn < 1e-6:
            continue
        normal = normal / nn

        # Scale variation (source: random 0.4-0.7, then multiply)
        inst_scale = float(rng.uniform(0.4, 0.7))

        # Duplicate petal_stem
        inst = petal_stem.copy()
        inst.data = petal_stem.data.copy()
        bpy.context.collection.objects.link(inst)

        # Scale
        inst.scale = (inst_scale, inst_scale, inst_scale)
        apply_tf(inst)

        # Align Z axis to surface normal
        # Compute rotation to align (0,0,1) to normal
        z_axis = np.array([0, 0, 1], dtype=float)
        cross = np.cross(z_axis, normal)
        cn = np.linalg.norm(cross)
        dot = np.dot(z_axis, normal)

        if cn > 1e-6:
            cross /= cn
            angle = math.acos(np.clip(dot, -1, 1))
            # Rodrigues rotation
            rot_mat = Matrix.Rotation(angle, 4, Vector(cross))
            inst.matrix_world = rot_mat @ inst.matrix_world
        elif dot < 0:
            inst.rotation_euler.x = math.pi

        inst.location = Vector(center)
        apply_tf(inst)

        parts.append(inst)

    # Delete template
    delete_obj(petal_stem)

    result = join_objs(parts)
    return result

# ── mode parameters ──────────────────────────────────────────────────────────

def get_mode_params(mode):
    """Matches DandelionFactory.get_mode_params."""

    if mode == "full_flower":
        return {
            "random_dropout": np.random.uniform(0.5, 1.0),
            "row_less_than": 0.0, "row_great_than": 0.0,
            "col_less_than": 0.0, "col_great_than": 0.0,
        }
    elif mode == "no_flower":
        return {
            "random_dropout": 0.0,
            "row_less_than": 1.0, "row_great_than": 0.0,
            "col_less_than": 1.0, "col_great_than": 0.0,
        }
    elif mode == "top_half_flower":
        return {
            "random_dropout": np.random.uniform(0.6, 1.0),
            "row_less_than": np.random.uniform(0.3, 0.5),
            "row_great_than": 0.0,
            "col_less_than": 1.0, "col_great_than": 0.0,
        }
    elif mode == "top_missing_flower":
        col = np.random.uniform(0.3, 1.0)
        return {
            "random_dropout": np.random.uniform(0.5, 0.9),
            "row_less_than": 1.0,
            "row_great_than": np.random.uniform(0.5, 0.7),
            "col_less_than": col,
            "col_great_than": col - np.random.uniform(0.2, 0.4),
        }
    elif mode == "sparse_flower":
        return {
            "random_dropout": np.random.uniform(0.3, 0.5),
            "row_less_than": 0.0, "row_great_than": 0.0,
            "col_less_than": 0.0, "col_great_than": 0.0,
        }
    else:
        raise ValueError(f"Unknown mode: {mode}")

# ── main ──────────────────────────────────────────────────────────────────────

def build_dandelion():
    np.random.seed(SEED)
    clear_scene()

    # Select flower mode
    flower_modes = ["full_flower", "no_flower", "top_half_flower",
                    "top_missing_flower", "sparse_flower"]
    probs = [0.4, 0.04, 0.23, 0.13, 0.2]
    mode = np.random.choice(flower_modes, p=probs)

    # Stem
    stem_radius = np.random.uniform(0.01, 0.024)
    stem_obj, stem_top = build_stem(stem_radius)

    parts = [stem_obj]

    if mode != "no_flower":
        # Build flower head
        mode_params = get_mode_params(mode)
        flower = build_flower_geometry(mode_params)

        if flower is not None:
            # Scale flower (negative for mirror, matches source)
            flower_scale = np.random.uniform(-0.15, -0.5)
            flower.scale = (flower_scale, flower_scale, flower_scale)
            apply_tf(flower)

            # Place at stem top
            flower.location = Vector(stem_top)
            apply_tf(flower)
            parts.append(flower)

    result = join_objs(parts)
    result.location.z = 0
    apply_tf(result)

    result.name = "DandelionFactory"
    return result, mode

dandelion, mode = build_dandelion()

