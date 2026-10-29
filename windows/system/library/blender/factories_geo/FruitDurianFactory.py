# [FL_INDEX: keywords="blender_factory, procedural_3d, FruitDurianFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FruitDurianFactory | Category: factories_geo
# Prompt: A durian fruit rendered as a textured 3D model. The fruit has a large, rounded body densely covered in sharp, conical spines arranged in a regular geometric pattern. Each spine is pyramidal with a pointed tip and a slightly ridged surface, arranged in clusters that create a distinctive symmetrical thorn pattern visible from any angle. The coloring is pale yellow-green with darker olive-green shading in the recesses between spine clusters. A short tan-brown woody stem protrudes from the top. The spiky, imposing silhouette and dramatic shadow are characteristic of this Southeast Asian tropical fruit.

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

def build_durian_body_with_thorns(radius_cp, cs_radius,
                                   start, middle, end,
                                   thorn_dist_min=0.1,
                                   thorn_displacement=0.3,
                                   thorn_control_points=None,
                                   noise_amount=0.2,
                                   resolution=512):
    """

    Build durian body + displacement-based thorns using GeoNodes.

    Pipeline (matches original durian_surface.py):
      Body: CurveCircle + QuadraticBezier + FloatCurve + CurveToMesh
      Surface bump: NoiseTexture → (Fac-0.5) × 0.5 × Normal → SetPosition
      Seed points: DistributePointsOnFaces (Poisson) + noise jitter + snap to surface
      Thorns: Per-vertex GeometryProximity → Manhattan distance to nearest seed →
              MapRange(0..2*dist_min → 1..0) → FloatCurve → Normal × displacement → SetPosition
    """

    if thorn_control_points is None:
        thorn_control_points = [(0.0, 0.0), (0.7318, 0.4344), (1.0, 1.0)]

    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    obj = bpy.context.active_object

    ng = bpy.data.node_groups.new("DurianBody", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT',
                            socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT',
                            socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')

    # ═══════════════════════════════════════════════════════════════════════════
    # STAGE 1: Build body mesh (CurveToMesh)
    # ═══════════════════════════════════════════════════════════════════════════

    # Cross-section: CurveCircle
    circle = nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.inputs['Resolution'].default_value = resolution

    xform = nodes.new('GeometryNodeTransform')
    xform.inputs['Scale'].default_value = (cs_radius, cs_radius, cs_radius)
    links.new(circle.outputs['Curve'], xform.inputs['Geometry'])

    # Body axis: QuadraticBezier
    bezier = nodes.new('GeometryNodeCurveQuadraticBezier')
    bezier.inputs['Resolution'].default_value = resolution
    bezier.inputs['Start'].default_value = start
    bezier.inputs['Middle'].default_value = middle
    bezier.inputs['End'].default_value = end

    # SplineParameter -> FloatCurve for radius envelope
    sparam = nodes.new('GeometryNodeSplineParameter')
    fcurve = nodes.new('ShaderNodeFloatCurve')
    assign_float_curve(fcurve.mapping, radius_cp)
    links.new(sparam.outputs['Factor'], fcurve.inputs['Value'])

    set_rad = nodes.new('GeometryNodeSetCurveRadius')
    links.new(bezier.outputs['Curve'], set_rad.inputs['Curve'])
    links.new(fcurve.outputs['Value'], set_rad.inputs['Radius'])

    c2m = nodes.new('GeometryNodeCurveToMesh')
    links.new(set_rad.outputs['Curve'], c2m.inputs['Curve'])
    links.new(xform.outputs['Geometry'], c2m.inputs['Profile Curve'])
    c2m.inputs['Fill Caps'].default_value = True

    # Blender 5.0+: Scale input for CurveToMesh
    scale_inputs = [s for s in c2m.inputs if s.name == 'Scale']
    if scale_inputs:
        links.new(fcurve.outputs['Value'], scale_inputs[0])

    # ═══════════════════════════════════════════════════════════════════════════
    # STAGE 2: Surface bump (noise displacement on body)
    # Matches: nodegroup_surface_bump(Displacement=0.5, Scale=0.5)
    # Pipeline: NoiseTexture(Scale=0.5) → (Fac - 0.5) → × 0.5 → × Normal → SetPosition
    # ═══════════════════════════════════════════════════════════════════════════

    bump_normal = nodes.new('GeometryNodeInputNormal')

    bump_noise = nodes.new('ShaderNodeTexNoise')
    bump_noise.inputs['Scale'].default_value = 0.5

    # (Fac - 0.5)
    bump_sub = nodes.new('ShaderNodeMath')
    bump_sub.operation = 'SUBTRACT'
    bump_sub.inputs[1].default_value = 0.5
    links.new(bump_noise.outputs[0], bump_sub.inputs[0])  # outputs[0] = Fac/Factor

    # × displacement (0.5)
    bump_mul = nodes.new('ShaderNodeMath')
    bump_mul.operation = 'MULTIPLY'
    bump_mul.inputs[1].default_value = 0.5  # bump displacement amount
    links.new(bump_sub.outputs[0], bump_mul.inputs[0])

    # × Normal (vector × scalar → vector offset)
    bump_vec_mul = nodes.new('ShaderNodeVectorMath')
    bump_vec_mul.operation = 'SCALE'
    links.new(bump_normal.outputs['Normal'], bump_vec_mul.inputs[0])
    links.new(bump_mul.outputs[0], bump_vec_mul.inputs['Scale'])

    # SetPosition: apply bump
    bump_setpos = nodes.new('GeometryNodeSetPosition')
    links.new(c2m.outputs['Mesh'], bump_setpos.inputs['Geometry'])
    links.new(bump_vec_mul.outputs['Vector'], bump_setpos.inputs['Offset'])

    # ═══════════════════════════════════════════════════════════════════════════
    # STAGE 3: Distribute seed points (thorn centers) on bumped body
    # Matches: nodegroup_point_on_mesh(Mesh, dist_min, noise_amount=0.2, noise_scale=5)
    # Pipeline: DistributePointsOnFaces(Poisson) + noise jitter + snap back to surface
    # ═══════════════════════════════════════════════════════════════════════════

    dist_pts = nodes.new('GeometryNodeDistributePointsOnFaces')
    dist_pts.distribute_method = 'POISSON'
    dist_pts.inputs['Distance Min'].default_value = thorn_dist_min
    dist_pts.inputs['Density Max'].default_value = 10000.0
    links.new(bump_setpos.outputs['Geometry'], dist_pts.inputs['Mesh'])

    # Noise jitter on seed points (matches point_on_mesh noise)
    seed_noise = nodes.new('ShaderNodeTexNoise')
    seed_noise.inputs['Scale'].default_value = 5.0  # noise_scale

    # (Color - 0.5) vector
    seed_val = nodes.new('ShaderNodeValue')
    seed_val.outputs[0].default_value = 0.5

    seed_sub = nodes.new('ShaderNodeVectorMath')
    seed_sub.operation = 'SUBTRACT'
    links.new(seed_noise.outputs['Color'], seed_sub.inputs[0])
    links.new(seed_val.outputs[0], seed_sub.inputs[1])

    # × noise_amount
    seed_scale = nodes.new('ShaderNodeVectorMath')
    seed_scale.operation = 'SCALE'
    seed_scale.inputs['Scale'].default_value = noise_amount
    links.new(seed_sub.outputs['Vector'], seed_scale.inputs[0])

    # SetPosition: jitter seed points
    seed_setpos = nodes.new('GeometryNodeSetPosition')
    links.new(dist_pts.outputs['Points'], seed_setpos.inputs['Geometry'])
    links.new(seed_scale.outputs['Vector'], seed_setpos.inputs['Offset'])

    # Snap jittered points back to original surface (GeometryProximity → SetPosition)
    seed_snap = nodes.new('GeometryNodeProximity')
    seed_snap.target_element = 'FACES'
    links.new(bump_setpos.outputs['Geometry'], seed_snap.inputs['Target'])

    seed_setpos2 = nodes.new('GeometryNodeSetPosition')
    links.new(seed_setpos.outputs['Geometry'], seed_setpos2.inputs['Geometry'])
    links.new(seed_snap.outputs['Position'], seed_setpos2.inputs['Position'])

    # ═══════════════════════════════════════════════════════════════════════════
    # STAGE 4: Per-vertex thorn displacement
    # Matches: nodegroup_durian_surface
    # For each body vertex:
    #   1. GeometryProximity → nearest seed point position
    #   2. Manhattan distance = |dx| + |dy| + |dz|
    #   3. MapRange(manhattan, 0, 2*dist_min, 1, 0)
    #   4. FloatCurve → thorn profile
    #   5. Normal × float_curve_val × displacement → SetPosition
    # ═══════════════════════════════════════════════════════════════════════════

    # Get body vertex normal
    thorn_normal = nodes.new('GeometryNodeInputNormal')

    # Body vertex position
    thorn_pos = nodes.new('GeometryNodeInputPosition')

    # GeometryProximity: find nearest seed point for each body vertex
    proximity = nodes.new('GeometryNodeProximity')
    proximity.target_element = 'POINTS'
    links.new(seed_setpos2.outputs['Geometry'], proximity.inputs['Target'])
    links.new(thorn_pos.outputs['Position'], proximity.inputs['Source Position'])

    # ── Manhattan distance: |v1.x-v2.x| + |v1.y-v2.y| + |v1.z-v2.z| ──

    # SeparateXYZ for nearest seed position
    sep1 = nodes.new('ShaderNodeSeparateXYZ')
    links.new(proximity.outputs['Position'], sep1.inputs['Vector'])

    # SeparateXYZ for body vertex position
    sep2 = nodes.new('ShaderNodeSeparateXYZ')
    links.new(thorn_pos.outputs['Position'], sep2.inputs['Vector'])

    # |X1 - X2|
    sub_x = nodes.new('ShaderNodeMath')
    sub_x.operation = 'SUBTRACT'
    links.new(sep1.outputs['X'], sub_x.inputs[0])
    links.new(sep2.outputs['X'], sub_x.inputs[1])

    abs_x = nodes.new('ShaderNodeMath')
    abs_x.operation = 'ABSOLUTE'
    links.new(sub_x.outputs[0], abs_x.inputs[0])

    # |Y1 - Y2|
    sub_y = nodes.new('ShaderNodeMath')
    sub_y.operation = 'SUBTRACT'
    links.new(sep1.outputs['Y'], sub_y.inputs[0])
    links.new(sep2.outputs['Y'], sub_y.inputs[1])

    abs_y = nodes.new('ShaderNodeMath')
    abs_y.operation = 'ABSOLUTE'
    links.new(sub_y.outputs[0], abs_y.inputs[0])

    # |Z1 - Z2|
    sub_z = nodes.new('ShaderNodeMath')
    sub_z.operation = 'SUBTRACT'
    links.new(sep1.outputs['Z'], sub_z.inputs[0])
    links.new(sep2.outputs['Z'], sub_z.inputs[1])

    abs_z = nodes.new('ShaderNodeMath')
    abs_z.operation = 'ABSOLUTE'
    links.new(sub_z.outputs[0], abs_z.inputs[0])

    # |dx| + |dy|
    add_xy = nodes.new('ShaderNodeMath')
    add_xy.operation = 'ADD'
    links.new(abs_x.outputs[0], add_xy.inputs[0])
    links.new(abs_y.outputs[0], add_xy.inputs[1])

    # + |dz| = manhattan distance
    manhattan = nodes.new('ShaderNodeMath')
    manhattan.operation = 'ADD'
    links.new(add_xy.outputs[0], manhattan.inputs[0])
    links.new(abs_z.outputs[0], manhattan.inputs[1])

    # ── MapRange: manhattan → thorn coordinate ──
    # MapRange(value=manhattan, from_min=0, from_max=2*dist_min, to_min=1, to_max=0)
    # Close to seed center → 1, far → 0
    map_range = nodes.new('ShaderNodeMapRange')
    links.new(manhattan.outputs[0], map_range.inputs['Value'])
    map_range.inputs['From Min'].default_value = 0.0
    map_range.inputs['From Max'].default_value = 2.0 * thorn_dist_min
    map_range.inputs['To Min'].default_value = 1.0
    map_range.inputs['To Max'].default_value = 0.0

    # ── FloatCurve: thorn shape profile ──
    # [(0,0), (0.7318, 0.4344), (1,1)] → broad angular shape
    thorn_fcurve = nodes.new('ShaderNodeFloatCurve')
    assign_float_curve(thorn_fcurve.mapping, thorn_control_points)
    links.new(map_range.outputs['Result'], thorn_fcurve.inputs['Value'])

    # ── Normal × float_curve_value (vector scale) ──
    thorn_scale1 = nodes.new('ShaderNodeVectorMath')
    thorn_scale1.operation = 'SCALE'
    links.new(thorn_normal.outputs['Normal'], thorn_scale1.inputs[0])
    links.new(thorn_fcurve.outputs['Value'], thorn_scale1.inputs['Scale'])

    # ── × displacement amount ──
    thorn_scale2 = nodes.new('ShaderNodeVectorMath')
    thorn_scale2.operation = 'SCALE'
    thorn_scale2.inputs['Scale'].default_value = thorn_displacement
    links.new(thorn_scale1.outputs['Vector'], thorn_scale2.inputs[0])

    # ── SetPosition: displace body vertices to form thorns ──
    thorn_setpos = nodes.new('GeometryNodeSetPosition')
    links.new(bump_setpos.outputs['Geometry'], thorn_setpos.inputs['Geometry'])
    links.new(thorn_scale2.outputs['Vector'], thorn_setpos.inputs['Offset'])

    # Output the displaced body (thorns are now integral to the mesh)
    links.new(thorn_setpos.outputs['Geometry'], group_out.inputs['Geometry'])

    # Apply modifier
    mod = obj.modifiers.new("Durian", 'NODES')
    mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    return obj

# ── stem (matches nodegroup_basic_stem) ───────────────────────────────────────

def build_basic_stem(cross_radius=0.08, quad_mid=(0, -0.05, 0.2),
                     quad_end=(-0.1, 0, 0.4), translation=(0, 0, 0.9)):
    """Thin tapered cylinder along a QuadraticBezier."""

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
        pos = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
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

def build_durian():
    np.random.seed(SEED)
    clear_scene()

    # From durian.py sample_cross_section_params
    _ = np.random.uniform(-100, 100)  # random seed (discarded)
    cs_radius = float(np.random.normal(1.2, 0.03))

    # From durian.py sample_shape_params
    radius_cp = [
        (0.0, 0.0031),
        (0.0841, 0.3469),
        (float(np.random.uniform(0.4, 0.6)), 0.8),
        (0.8886, 0.6094),
        (1.0, 0.0),
    ]
    start = (float(np.random.uniform(-0.3, 0.3)),
             float(np.random.uniform(-0.3, 0.3)),
             float(np.random.uniform(-0.5, -1.5)))
    middle = (0.0, 0.0, 0.0)
    end = (0.0, 0.0, 1.0)

    # From durian_surface: thorn distribution parameters
    thorn_dist_min = float(np.random.uniform(0.07, 0.13))
    thorn_displacement = float(np.random.uniform(0.25, 0.35))

    # Thorn shape profile control points (from durian_surface.py)
    thorn_control_points = [(0.0, 0.0), (0.7318, 0.4344), (1.0, 1.0)]

    # Build body + displacement thorns using GeoNodes (resolution=512 matches original)
    body = build_durian_body_with_thorns(
        radius_cp, cs_radius, start, middle, end,
        thorn_dist_min=thorn_dist_min,
        thorn_displacement=thorn_displacement,
        thorn_control_points=thorn_control_points,
        noise_amount=0.2,
        resolution=512
    )

    # Stem — use Bezier endpoint as reference (not max vertex Z,
    # which includes thorn protrusion and would cause floating stem)
    body_top_z = end[2]  # body axis endpoint = 1.0
    stem_r = float(np.random.uniform(0.07, 0.09))
    mid = (float(np.random.uniform(-0.1, 0.1)),
           float(np.random.uniform(-0.1, 0.1)),
           float(np.random.uniform(0.15, 0.2)))
    end_s = (float(np.random.uniform(-0.2, 0.2)),
             float(np.random.uniform(-0.2, 0.2)),
             float(np.random.uniform(0.3, 0.4)))
    stem = build_basic_stem(cross_radius=stem_r, quad_mid=mid, quad_end=end_s,
                            translation=(0.0, 0.0, body_top_z - 0.10))

    result = join_objs([body, stem])

    # scale_multiplier = 2.0
    s = float(np.random.normal(1, 0.1)) * 2.0
    result.scale = (s, s, s)
    apply_tf(result)

    # Align top to Z=0 (hanging convention)
    max_z = max(v.co.z for v in result.data.vertices)
    result.location.z = -max_z
    apply_tf(result)

    return result

durian = build_durian()
durian.name = "FruitFactoryDurian"
