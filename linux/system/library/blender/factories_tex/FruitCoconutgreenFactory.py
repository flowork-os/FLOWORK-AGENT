# [FL_INDEX: keywords="blender_factory, procedural_3d, FruitCoconutgreenFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FruitCoconutgreenFactory | Category: factories_tex
# Prompt: A green coconut rendered as a textured 3D model. The fruit has a large, rounded oval shape — wider at the base and tapering slightly toward the top — with a smooth, glossy husk surface in bright fresh green. The coloring transitions subtly with lighter white-green areas toward the bottom and darker green toward the top. A three-part flower scar mark is visible at the crown, surrounded by a slightly raised ring. A short pale green stalk protrudes from the top center. The clean, smooth, modern-looking husk surface is characteristic of a young drinking coconut.

import os
import math
import random

import bmesh
import bpy
import numpy as np

SEED = 0
random.seed(SEED)
SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
#  Fruit material — translated from fruit surface shaders (raw bpy)
# ═══════════════════════════════════════════════════════════════════════════
import os as _os, random as _random, colorsys as _colorsys


def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h) % 1.0, max(0, min(1, float(s))), max(0, min(1, float(v))))
    return (r, g, b, 1.0)

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True; mat.node_tree.nodes.clear()
    return mat

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def make_fruit_material(seed, name="CoconutGreenMaterial"):
    """Green coconut: dark green with stripe pattern."""

    c1 = _hsv2rgba(0.235 + float(np.random.normal(0.0, 0.025)),
                   0.989 + float(np.random.normal(0.0, 0.05)),
                   0.413 + float(np.random.normal(0.0, 0.05)))
    c2 = _hsv2rgba(0.282 + float(np.random.normal(0.0, 0.02)),
                   0.951 + float(np.random.normal(0.0, 0.05)),
                   0.266 + float(np.random.normal(0.0, 0.05)))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 1.0; noise.inputs["Detail"].default_value = 10.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = c2
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = c1
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.45
    sk = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[sk].default_value = 0.48
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_color_material(name, color, roughness=0.8):
    mat = _new_mat(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def sanitize_material_slots(obj, replacement_mat):
    if obj is None or not hasattr(obj.data, "materials"):
        return obj
    if len(obj.data.materials) == 0:
        obj.data.materials.append(replacement_mat)
    for i in range(len(obj.data.materials)):
        if obj.data.materials[i] is None:
            obj.data.materials[i] = replacement_mat
    first_valid = next((i for i, mat in enumerate(obj.data.materials) if mat is not None), 0)
    for poly in obj.data.polygons:
        if poly.material_index >= len(obj.data.materials) or obj.data.materials[poly.material_index] is None:
            poly.material_index = first_valid
    obj.data.update()
    return obj

FRUIT_MAT = make_fruit_material(SEED, "FruitFactoryCoconutgreen_Material")
STEM_MAT = make_color_material("FruitFactoryCoconutgreen_StemMaterial", (0.1119, 0.2122, 0.008, 1.0))
np.random.seed(SEED)

# ── scene helpers ─────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

# ── GeoNodes helpers ─────────────────────────────────────────────────────────

def assign_float_curve(curve_mapping, control_points):
    """Assign control points to a FloatCurve CurveMapping."""

    curve = curve_mapping.curves[0]
    curve.points[0].location = (control_points[0][0], control_points[0][1])
    curve.points[0].handle_type = 'AUTO'
    curve.points[-1].location = (control_points[-1][0], control_points[-1][1])
    curve.points[-1].handle_type = 'AUTO'
    for x, y in control_points[1:-1]:
        p = curve.points.new(x, y)
        p.handle_type = 'AUTO'
    curve_mapping.update()

def build_coconut_body_geonodes(radius_cp, cs_cp, n_fold, cs_radius,
                                 start, middle, end, resolution=256):
    """

    Build coconut body with 3-fold cross-section using GeoNodes.
    Cross-section: CurveCircle + PINGPONG(N=3) + FloatCurve -> 3-fold profile
    Body: QuadraticBezier + FloatCurve(radius_cp) + CurveToMesh
    """

    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    obj = bpy.context.active_object

    ng = bpy.data.node_groups.new("CoconutBody", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT',
                            socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT',
                            socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')

    # ── Profile curve: CurveCircle with 3-fold symmetry ──
    circle_profile = nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle_profile.inputs['Resolution'].default_value = resolution

    # SplineParameter for profile -> PINGPONG for N-fold symmetry
    sp_profile = nodes.new('GeometryNodeSplineParameter')

    # PINGPONG triangle wave: divide = 0.5 / N
    divide = nodes.new('ShaderNodeMath')
    divide.operation = 'DIVIDE'
    divide.inputs[0].default_value = 0.5
    divide.inputs[1].default_value = float(n_fold)

    pingpong = nodes.new('ShaderNodeMath')
    pingpong.operation = 'PINGPONG'
    links.new(sp_profile.outputs['Factor'], pingpong.inputs[0])
    links.new(divide.outputs['Value'], pingpong.inputs[1])

    # MapRange: [0, divide] -> [0, 1]
    map_range = nodes.new('ShaderNodeMapRange')
    links.new(pingpong.outputs['Value'], map_range.inputs['Value'])
    map_range.inputs['From Min'].default_value = 0.0
    links.new(divide.outputs['Value'], map_range.inputs['From Max'])
    map_range.inputs['To Min'].default_value = 0.0
    map_range.inputs['To Max'].default_value = 1.0

    # FloatCurve for cross-section profile shape
    cs_fcurve = nodes.new('ShaderNodeFloatCurve')
    assign_float_curve(cs_fcurve.mapping, cs_cp)
    links.new(map_range.outputs['Result'], cs_fcurve.inputs['Value'])

    # Get position of profile circle and scale radially by FloatCurve
    pos_profile = nodes.new('GeometryNodeInputPosition')

    scale_profile = nodes.new('ShaderNodeVectorMath')
    scale_profile.operation = 'SCALE'
    links.new(pos_profile.outputs['Position'], scale_profile.inputs[0])
    links.new(cs_fcurve.outputs['Value'], scale_profile.inputs['Scale'])

    set_pos_profile = nodes.new('GeometryNodeSetPosition')
    links.new(circle_profile.outputs['Curve'], set_pos_profile.inputs['Geometry'])
    links.new(scale_profile.outputs['Vector'], set_pos_profile.inputs['Position'])

    # Scale by overall cs_radius
    xform = nodes.new('GeometryNodeTransform')
    xform.inputs['Scale'].default_value = (cs_radius, cs_radius, cs_radius)
    links.new(set_pos_profile.outputs['Geometry'], xform.inputs['Geometry'])

    # ── Body axis: QuadraticBezier ──
    bezier = nodes.new('GeometryNodeCurveQuadraticBezier')
    bezier.inputs['Resolution'].default_value = resolution
    bezier.inputs['Start'].default_value = start
    bezier.inputs['Middle'].default_value = middle
    bezier.inputs['End'].default_value = end

    # SplineParameter -> FloatCurve for radius envelope
    sp_axis = nodes.new('GeometryNodeSplineParameter')
    fcurve_axis = nodes.new('ShaderNodeFloatCurve')
    assign_float_curve(fcurve_axis.mapping, radius_cp)
    links.new(sp_axis.outputs['Factor'], fcurve_axis.inputs['Value'])

    # SetCurveRadius (for Blender 4.x)
    set_rad = nodes.new('GeometryNodeSetCurveRadius')
    links.new(bezier.outputs['Curve'], set_rad.inputs['Curve'])
    links.new(fcurve_axis.outputs['Value'], set_rad.inputs['Radius'])

    # CurveToMesh
    c2m = nodes.new('GeometryNodeCurveToMesh')
    links.new(set_rad.outputs['Curve'], c2m.inputs['Curve'])
    links.new(xform.outputs['Geometry'], c2m.inputs['Profile Curve'])
    c2m.inputs['Fill Caps'].default_value = True

    # Blender 5.0+: Scale input (SetCurveRadius is ignored by CurveToMesh)
    scale_inputs = [s for s in c2m.inputs if s.name == 'Scale']
    if scale_inputs:
        links.new(fcurve_axis.outputs['Value'], scale_inputs[0])

    links.new(c2m.outputs['Mesh'], group_out.inputs['Geometry'])

    # Apply modifier
    mod = obj.modifiers.new("CoconutBody", 'NODES')
    mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # [auto-append] ensure material bound
    if obj is not None:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(FRUIT_MAT)
        elif obj.data.materials[0] is None:
            obj.data.materials[0] = FRUIT_MAT
    return obj

# ── dent processing (matches nodegroup_add_dent) ─────────────────────────────

def compute_spline_attrs(obj, start, middle, end):
    """Compute spline parameter, tangent, and distance-to-center for each vertex."""

    mesh = obj.data
    mesh.update()

    S = np.array(start, dtype=float)
    M = np.array(middle, dtype=float)
    E = np.array(end, dtype=float)

    n_verts = len(mesh.vertices)
    coords = np.zeros((n_verts, 3))
    for i, v in enumerate(mesh.vertices):
        coords[i] = [v.co.x, v.co.y, v.co.z]

    # Solve for t from z: (S_z - 2M_z + E_z)t^2 + (-2S_z + 2M_z)t + (S_z - z) = 0
    a = S[2] - 2*M[2] + E[2]
    b = -2*S[2] + 2*M[2]
    z_vals = coords[:, 2]
    c = S[2] - z_vals

    if abs(a) < 1e-10:
        spline_params = np.clip(-c / b, 0, 1) if abs(b) > 1e-10 else np.full(n_verts, 0.5)
    else:
        disc = b*b - 4*a*c
        disc = np.maximum(disc, 0)
        sqrt_disc = np.sqrt(disc)
        t1 = (-b + sqrt_disc) / (2*a)
        t2 = (-b - sqrt_disc) / (2*a)
        spline_params = np.where(np.abs(t1 - 0.5) < np.abs(t2 - 0.5), t1, t2)
        spline_params = np.clip(spline_params, 0, 1)

    t = spline_params
    tangents = (np.outer(2*(1-t), (M - S)) + np.outer(2*t, (E - M)))
    tang_lens = np.linalg.norm(tangents, axis=1, keepdims=True)
    tangents = tangents / np.maximum(tang_lens, 1e-6)

    bez_pts = np.outer((1-t)**2, S) + np.outer(2*(1-t)*t, M) + np.outer(t**2, E)
    distances = np.linalg.norm(coords - bez_pts, axis=1)

    return spline_params, tangents, distances

def apply_dent(obj, spline_params, tangents, distances,
               dent_cp, max_radius, intensity, bottom):
    """Apply dent displacement matching nodegroup_add_dent."""

    mesh = obj.data

    cp_x = np.array([p[0] for p in dent_cp])
    cp_y = np.array([p[1] for p in dent_cp])

    if bottom:
        sel = spline_params < 0.5
    else:
        sel = spline_params > 0.5

    norm_dist = np.clip(distances / max_radius, 0, 1)
    curve_vals = np.interp(norm_dist, cp_x, cp_y)
    mapped = -1.0 + 2.0 * curve_vals  # MapRange [0,1] -> [-1,1]

    if isinstance(intensity, np.ndarray):
        strength = np.where(sel, mapped * intensity, 0.0)
    else:
        strength = np.where(sel, mapped * intensity, 0.0)

    offsets = tangents * strength[:, np.newaxis]

    for i, v in enumerate(mesh.vertices):
        if sel[i]:
            v.co.x += offsets[i, 0]
            v.co.y += offsets[i, 1]
            v.co.z += offsets[i, 2]

    mesh.update()

# ── coconut stem (matches stem_lib.nodegroup_coconut_stem) ────────────────────

def build_coconut_stem(top_z, body_r, n_calyx=5, calyx_width=0.22,
                       stem_radius=0.04, stem_mid=(0.0, -0.05, 0.2),
                       stem_end=(-0.1, 0.0, 0.4)):
    """

    Coconut stem: small calyx disc/petal shapes at top + thin basic stem.
    Matches stem_lib.nodegroup_coconut_stem:
      calyx leaves on a spiral at top, plus basic_stem above.
    """

    parts = []

    # Calyx: small rounded petal shapes at top of fruit
    calyx_r = body_r * calyx_width

    for i in range(n_calyx):
        angle = 2 * math.pi * i / n_calyx + float(np.random.uniform(-0.15, 0.15))
        bm = bmesh.new()

        # Diamond/petal shape (matches coconut_calyx FillCurve)
        w = calyx_r * 0.4
        h = calyx_r
        v0 = bm.verts.new((0, 0, 0))
        v1 = bm.verts.new((w, 0, h * 0.4))
        v2 = bm.verts.new((0, 0, h))
        v3 = bm.verts.new((-w, 0, h * 0.4))
        bm.faces.new([v0, v1, v2, v3])

        # Subdivide for smoothness
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3,
                                   use_grid_fill=True)

        mesh = bpy.data.meshes.new(f"calyx_{i}")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(f"calyx_{i}", mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(STEM_MAT)

        # Scale varies: base_scale=0.3 -> top_scale=0.24
        sc = 0.3 - 0.06 * (i / max(1, n_calyx - 1))
        obj.scale = (sc, sc, sc)

        # Tilt outward and rotate around z
        obj.rotation_euler.x = math.radians(float(np.random.uniform(45, 65)))
        obj.rotation_euler.z = angle
        obj.location.z = top_z
        apply_tf(obj)
        parts.append(obj)

    # Thin stem above calyx (basic_stem at Translation z=0.98 in source)
    n_segs = 16
    n_ring = 8
    bm = bmesh.new()

    p0 = np.array([0.0, 0.0, top_z])
    p1 = p0 + np.array(stem_mid)
    p2 = p0 + np.array(stem_end)

    rings = []
    for i in range(n_segs + 1):
        t = i / n_segs
        pos = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
        r = stem_radius * (1 - t * 0.5)
        ring = []
        for j in range(n_ring):
            theta = 2 * math.pi * j / n_ring
            ring.append(bm.verts.new((pos[0] + r * math.cos(theta),
                                       pos[1] + r * math.sin(theta),
                                       pos[2])))
        rings.append(ring)

    for i in range(n_segs):
        for j in range(n_ring):
            j2 = (j + 1) % n_ring
            bm.faces.new([rings[i][j], rings[i][j2],
                          rings[i + 1][j2], rings[i + 1][j]])

    tp = p2
    tip = bm.verts.new((float(tp[0]), float(tp[1]), float(tp[2])))
    for j in range(n_ring):
        j2 = (j + 1) % n_ring
        bm.faces.new([tip, rings[-1][j], rings[-1][j2]])

    smesh = bpy.data.meshes.new("stem")
    bm.to_mesh(smesh)
    bm.free()

    stem_obj = bpy.data.objects.new("stem", smesh)
    bpy.context.collection.objects.link(stem_obj)
    stem_obj.data.materials.append(STEM_MAT)
    parts.append(stem_obj)

    return join_objs(parts)

# ── main ──────────────────────────────────────────────────────────────────────

def build_coconutgreen():
    np.random.seed(SEED)
    clear_scene()

    # From coconutgreen.py sample_cross_section_params
    _ = np.random.uniform(-100, 100)  # random seed (discarded)
    cs_radius = float(np.random.normal(1.8, 0.1))
    rad_small = float(np.random.uniform(0.65, 0.75))
    cs_cp = [(0.0, rad_small), (0.1, rad_small), (1.0, 0.76)]

    # From coconutgreen.py sample_shape_params
    radius_cp = [
        (0.0, 0.0),
        (0.0591, 0.3156),
        (float(np.random.uniform(0.2, 0.3)), 0.6125),
        (float(np.random.uniform(0.6, 0.7)), 0.675),
        (0.9636, 0.3625),
        (1.0, 0.0),
    ]
    start = (float(np.random.uniform(-0.1, 0.1)),
             float(np.random.uniform(-0.1, 0.1)),
             float(np.random.normal(-1.0, 0.1)))
    middle = (0.0, 0.0, 0.0)
    end = (0.0, 0.0, 1.0)

    # Build body with 3-fold cross-section using GeoNodes
    body = build_coconut_body_geonodes(
        radius_cp, cs_cp, n_fold=3, cs_radius=cs_radius,
        start=start, middle=middle, end=end, resolution=256
    )

    # Apply surface dent (bottom half)
    # coconutgreen_surface: MapRange(distance, [0.05, 0.2] -> [0, 0.68])
    #   * cross_section_param -> intensity for add_dent(bottom=True, max_radius=3.0)
    dent_cp = [
        (0.0, 0.4219),
        (0.0977, 0.4469),
        (0.2273, 0.4844),
        (0.5568, 0.5125),
        (1.0, 0.5),
    ]
    sp, tang, dist = compute_spline_attrs(body, start, middle, end)
    # Simplified intensity: distance-based (omitting cross_section_parameter modulation)
    dist_intensity = np.clip((dist - 0.05) / (0.2 - 0.05), 0, 1) * 0.68
    apply_dent(body, sp, tang, dist, dent_cp,
               max_radius=3.0, intensity=dist_intensity, bottom=True)

    # Coconut stem — start below body top to ensure overlap (not floating)
    top_z = max(v.co.z for v in body.data.vertices)
    top_z = top_z - 0.12  # embed into body
    body_r = max(max(abs(v.co.x), abs(v.co.y)) for v in body.data.vertices)

    n_calyx = int(np.random.randint(4, 7))
    calyx_w = float(np.random.uniform(0.2, 0.25))
    stem_r = float(np.random.normal(0.04, 0.005))
    stem_x = float(np.random.uniform(-0.4, 0.4))
    stem_y = float(np.random.uniform(-0.4, 0.4))

    stem = build_coconut_stem(
        top_z=top_z, body_r=body_r, n_calyx=n_calyx,
        calyx_width=calyx_w, stem_radius=stem_r,
        stem_mid=(stem_x, stem_y, 0.0),
        stem_end=(2 * stem_x, 2 * stem_y,
                  float(np.random.uniform(0.3, 0.5)))
    )

    result = join_objs([body, stem])

    # scale_multiplier = 1.5
    s = float(np.random.normal(1, 0.1)) * 1.5
    result.scale = (s, s, s)
    apply_tf(result)

    # Align top to Z=0 (hanging convention)
    max_z = max(v.co.z for v in result.data.vertices)
    result.location.z = -max_z
    apply_tf(result)

    return sanitize_material_slots(result, STEM_MAT)

coconut = build_coconutgreen()
coconut.name = "FruitFactoryCoconutgreen"

