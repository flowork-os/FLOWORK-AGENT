# [FL_INDEX: keywords="blender_factory, procedural_3d, FruitStarfruitFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FruitStarfruitFactory | Category: factories_geo
# Prompt: A starfruit (carambola) rendered as a textured 3D model. The fruit has a distinctive cross-sectional star shape — a rounded body with five prominent longitudinal lobes or ridges running from top to bottom, creating a star-shaped silhouette when viewed from above or below. The surface is smooth and waxy with a pale cream-yellow color with subtle green highlights at the ridge edges and light shading in the grooves between lobes. A short, slightly twisted brown stem protrudes from the top. The overall form is plump and rounded with a gentle glossy sheen across the surface.

import math
import random

import bmesh
import bpy
import numpy as np

SEED = 0
random.seed(SEED)
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

def build_starfruit_body_geonodes(radius_cp, cs_radius, start, middle, end,
                                   star_cp, n_star=5, resolution=256):
    """

    Build starfruit body with star cross-section using GeoNodes.
    Star cross-section: rot_symmetry(N=5, PINGPONG triangle wave) → FloatCurve → scale
    Body: QuadraticBezier + FloatCurve + CurveToMesh
    """

    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    obj = bpy.context.active_object

    ng = bpy.data.node_groups.new("StarfruitBody", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT',
                            socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT',
                            socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links
    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')

    # ════════════════════════════════════════════════════════════════════════
    # STAR CROSS-SECTION PROFILE
    # ════════════════════════════════════════════════════════════════════════

    # CurveCircle
    circle = nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.inputs['Resolution'].default_value = resolution

    # SplineParameter → Factor (0-1 around the circle)
    sp_profile = nodes.new('GeometryNodeSplineParameter')

    # rot_symmetry: divide(0.5, N) → pingpong(factor, divide) → map_range [0,divide]→[0,1]
    divide = nodes.new('ShaderNodeMath')
    divide.operation = 'DIVIDE'
    divide.inputs[0].default_value = 0.5
    divide.inputs[1].default_value = float(n_star)

    pingpong = nodes.new('ShaderNodeMath')
    pingpong.operation = 'PINGPONG'
    links.new(sp_profile.outputs['Factor'], pingpong.inputs[0])
    links.new(divide.outputs['Value'], pingpong.inputs[1])

    # MapRange: [0, 0.5/N] → [0, 1]
    map_range = nodes.new('ShaderNodeMapRange')
    links.new(pingpong.outputs['Value'], map_range.inputs['Value'])
    map_range.inputs['From Min'].default_value = 0.0
    links.new(divide.outputs['Value'], map_range.inputs['From Max'])
    map_range.inputs['To Min'].default_value = 0.0
    map_range.inputs['To Max'].default_value = 1.0

    # FloatCurve: rot_symmetry → star modulation
    star_fcurve = nodes.new('ShaderNodeFloatCurve')
    assign_float_curve(star_fcurve.mapping, star_cp)
    links.new(map_range.outputs['Result'], star_fcurve.inputs['Value'])

    # Scale circle positions by star modulation × radius
    pos_profile = nodes.new('GeometryNodeInputPosition')

    scale_star = nodes.new('ShaderNodeVectorMath')
    scale_star.operation = 'SCALE'
    links.new(pos_profile.outputs['Position'], scale_star.inputs[0])
    links.new(star_fcurve.outputs['Value'], scale_star.inputs['Scale'])

    scale_radius = nodes.new('ShaderNodeVectorMath')
    scale_radius.operation = 'SCALE'
    links.new(scale_star.outputs['Vector'], scale_radius.inputs[0])
    scale_radius.inputs['Scale'].default_value = cs_radius

    # SetPosition on circle
    set_pos_profile = nodes.new('GeometryNodeSetPosition')
    links.new(circle.outputs['Curve'], set_pos_profile.inputs['Geometry'])
    links.new(scale_radius.outputs['Vector'], set_pos_profile.inputs['Position'])

    # ════════════════════════════════════════════════════════════════════════
    # AXIS CURVE + CURVTOMESH
    # ════════════════════════════════════════════════════════════════════════

    # QuadraticBezier axis
    bezier = nodes.new('GeometryNodeCurveQuadraticBezier')
    bezier.inputs['Resolution'].default_value = resolution
    bezier.inputs['Start'].default_value = start
    bezier.inputs['Middle'].default_value = middle
    bezier.inputs['End'].default_value = end

    # SplineParameter → FloatCurve → radius modulation
    sp_axis = nodes.new('GeometryNodeSplineParameter')
    radius_fcurve = nodes.new('ShaderNodeFloatCurve')
    assign_float_curve(radius_fcurve.mapping, radius_cp)
    links.new(sp_axis.outputs['Factor'], radius_fcurve.inputs['Value'])

    # SetCurveRadius
    set_rad = nodes.new('GeometryNodeSetCurveRadius')
    links.new(bezier.outputs['Curve'], set_rad.inputs['Curve'])
    links.new(radius_fcurve.outputs['Value'], set_rad.inputs['Radius'])

    # CurveToMesh
    c2m = nodes.new('GeometryNodeCurveToMesh')
    links.new(set_rad.outputs['Curve'], c2m.inputs['Curve'])
    links.new(set_pos_profile.outputs['Geometry'], c2m.inputs['Profile Curve'])
    c2m.inputs['Fill Caps'].default_value = True

    # Blender 5.0+: Scale input
    scale_inputs = [s for s in c2m.inputs if s.name == 'Scale']
    if scale_inputs:
        links.new(radius_fcurve.outputs['Value'], scale_inputs[0])

    links.new(c2m.outputs['Mesh'], group_out.inputs['Geometry'])

    # Apply modifier
    mod = obj.modifiers.new("StarfruitBody", 'NODES')
    mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

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

    a = S[2] - 2*M[2] + E[2]
    b = -2*S[2] + 2*M[2]
    z_vals = coords[:, 2]
    c = S[2] - z_vals

    if abs(a) < 1e-10:
        spline_params = np.clip(-c / b, 0, 1) if abs(b) > 1e-10 else np.full(n_verts, 0.5)
    else:
        disc = np.maximum(b*b - 4*a*c, 0)
        sqrt_disc = np.sqrt(disc)
        t1 = (-b + sqrt_disc) / (2*a)
        t2 = (-b - sqrt_disc) / (2*a)
        spline_params = np.where(np.abs(t1 - 0.5) < np.abs(t2 - 0.5), t1, t2)
        spline_params = np.clip(spline_params, 0, 1)

    t = spline_params
    tangents = np.outer(2*(1-t), (M - S)) + np.outer(2*t, (E - M))
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
    mapped = -1.0 + 2.0 * curve_vals  # MapRange [0,1] → [-1, 1]
    strength = np.where(sel, mapped * intensity, 0.0)
    offsets = tangents * strength[:, np.newaxis]

    for i, v in enumerate(mesh.vertices):
        if sel[i]:
            v.co.x += offsets[i, 0]
            v.co.y += offsets[i, 1]
            v.co.z += offsets[i, 2]
    mesh.update()

# ── surface bump (matches nodegroup_surface_bump) ────────────────────────────

def apply_surface_bump(obj, displacement=0.03, scale=10.0):
    """

    Apply surface bump using GeoNodes: NoiseTexture → (Fac-0.5) × displacement × Normal → SetPosition.
    Matches nodegroup_surface_bump(Displacement=0.03, Scale=10.0) from starfruit_surface.py.
    """

    ng = bpy.data.node_groups.new("SurfaceBump", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT',
                            socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT',
                            socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')

    # InputNormal
    normal = nodes.new('GeometryNodeInputNormal')

    # NoiseTexture(Scale=scale) → Fac/Factor output
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    # Output index 0 = "Fac" (Blender 4.x) / "Factor" (Blender 5.x)

    # Subtract 0.5: center noise around 0
    subtract = nodes.new('ShaderNodeMath')
    subtract.operation = 'SUBTRACT'
    links.new(noise.outputs[0], subtract.inputs[0])
    subtract.inputs[1].default_value = 0.5

    # Multiply by displacement
    multiply_disp = nodes.new('ShaderNodeMath')
    multiply_disp.operation = 'MULTIPLY'
    links.new(subtract.outputs['Value'], multiply_disp.inputs[0])
    multiply_disp.inputs[1].default_value = displacement

    # VectorMath MULTIPLY: normal × scalar offset
    vec_mul = nodes.new('ShaderNodeVectorMath')
    vec_mul.operation = 'MULTIPLY'
    links.new(normal.outputs['Normal'], vec_mul.inputs[0])
    links.new(multiply_disp.outputs['Value'], vec_mul.inputs[1])

    # SetPosition with Offset
    set_pos = nodes.new('GeometryNodeSetPosition')
    links.new(group_in.outputs['Geometry'], set_pos.inputs['Geometry'])
    links.new(vec_mul.outputs['Vector'], set_pos.inputs['Offset'])

    links.new(set_pos.outputs['Geometry'], group_out.inputs['Geometry'])

    # Apply modifier
    mod = obj.modifiers.new("SurfaceBump", 'NODES')
    mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    return obj

# ── stem (matches nodegroup_basic_stem) ───────────────────────────────────────

def build_basic_stem(cross_radius=0.04, quad_mid=(0, -0.05, 0.2),
                     quad_end=(-0.1, 0, 0.4), translation=(0, 0, 0.8)):
    n_segs = 32
    n_ring = 16
    bm = bmesh.new()
    p0 = np.array([0.0, 0.0, 0.0])
    p1 = np.array(quad_mid)
    p2 = np.array(quad_end)
    tz = np.array(translation)
    scale_z = 2.0

    rings = []
    for i in range(n_segs + 1):
        t = i / n_segs
        pos = (1 - t)**2 * p0 + 2*(1 - t)*t * p1 + t**2 * p2
        pos_final = np.array([pos[0], pos[1], pos[2] * scale_z]) + tz
        r = cross_radius * (1 - t * 0.3)
        ring = []
        for j in range(n_ring):
            theta = 2 * math.pi * j / n_ring
            ring.append(bm.verts.new((pos_final[0] + r * math.cos(theta),
                                       pos_final[1] + r * math.sin(theta),
                                       pos_final[2])))
        rings.append(ring)

    for i in range(n_segs):
        for j in range(n_ring):
            j2 = (j + 1) % n_ring
            bm.faces.new([rings[i][j], rings[i][j2],
                          rings[i + 1][j2], rings[i + 1][j]])

    tp_final = np.array([p2[0], p2[1], p2[2] * scale_z]) + tz
    tip = bm.verts.new((float(tp_final[0]), float(tp_final[1]), float(tp_final[2])))
    for j in range(n_ring):
        j2 = (j + 1) % n_ring
        bm.faces.new([tip, rings[-1][j], rings[-1][j2]])

    mesh = bpy.data.meshes.new("stem")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("stem", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

# ── main ──────────────────────────────────────────────────────────────────────

def build_starfruit():
    np.random.seed(SEED)
    clear_scene()

    # Star cross-section modulation curve
    star_cp = [(0.0, 0.4156), (0.65, 0.8125), (1.0, 1.0)]

    # From starfruit.py sample_cross_section_params
    _ = np.random.uniform(-100, 100)  # random seed (discarded)
    cs_radius = float(np.random.normal(1.3, 0.05))

    # From starfruit.py sample_shape_params
    radius_cp = [
        (0.0727, 0.2),
        (0.2636, 0.6063),
        (float(np.random.uniform(0.45, 0.65)), float(np.random.uniform(0.7, 0.9))),
        (0.8886, 0.6094),
        (1.0, 0.0),
    ]
    start = (float(np.random.uniform(-0.3, 0.3)),
             float(np.random.uniform(-0.3, 0.3)),
             float(np.random.uniform(-1.0, -2.0)))
    middle = (0.0, 0.0, 0.0)
    end = (0.0, 0.0, 1.0)

    body = build_starfruit_body_geonodes(
        radius_cp, cs_radius, start, middle, end,
        star_cp, n_star=5, resolution=256
    )

    # Surface: one add_dent (top half only)
    dent_cp = [
        (0.0, 0.4219),
        (0.0977, 0.4469),
        (0.2273, 0.4844),
        (0.5568, 0.5125),
        (1.0, 0.5),
    ]
    dent_intensity = float(np.random.normal(1.0, 0.1))

    sp, tang, dist = compute_spline_attrs(body, start, middle, end)
    apply_dent(body, sp, tang, dist, dent_cp,
               max_radius=1.0, intensity=dent_intensity, bottom=False)

    # Surface bump: NoiseTexture displacement along normals (matches starfruit_surface.py)
    apply_surface_bump(body, displacement=0.03, scale=10.0)

    # Stem — compute top_z after dent to ensure overlap
    top_z = max(v.co.z for v in body.data.vertices)
    stem_r = float(np.random.uniform(0.03, 0.05))
    mid = (float(np.random.uniform(-0.1, 0.1)),
           float(np.random.uniform(-0.1, 0.1)),
           float(np.random.uniform(0.15, 0.2)))
    end_s = (float(np.random.uniform(-0.2, 0.2)),
             float(np.random.uniform(-0.2, 0.2)),
             float(np.random.uniform(0.3, 0.4)))
    stem = build_basic_stem(cross_radius=stem_r, quad_mid=mid, quad_end=end_s,
                            translation=(0.0, 0.0, top_z - 0.15))

    result = join_objs([body, stem])

    # scale_multiplier = 1.0
    s = float(np.random.normal(1, 0.1)) * 1.0
    result.scale = (s, s, s)
    apply_tf(result)

    # Align top to Z=0
    max_z = max(v.co.z for v in result.data.vertices)
    result.location.z = -max_z
    apply_tf(result)

    return result

starfruit = build_starfruit()
starfruit.name = "FruitFactoryStarfruit"
