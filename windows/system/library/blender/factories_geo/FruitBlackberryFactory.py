# [FL_INDEX: keywords="blender_factory, procedural_3d, FruitBlackberryFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FruitBlackberryFactory | Category: factories_geo
# Prompt: A blackberry rendered as a textured 3D model. The fruit has a characteristic elongated oval shape composed of many closely packed, rounded drupelet spheres arranged in a tight honeycomb-like cluster. Each individual drupelet is a glossy, deep dark purple-black sphere with strong specular highlights giving a shiny, wet appearance. A short pale green stem protrudes from the top. Fine hair-like structures (fine drupelets) are visible around the edges between the main drupelet spheres. The deep shadowing between the drupelets creates strong surface contrast.

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

def build_blackberry_body_with_drupelets(radius_cp, cs_radius, start, middle, end,
                                          drupelet_scale=0.35, dist_min=0.4,
                                          resolution=256):
    """

    Build blackberry body with CurveToMesh and distribute drupelets using GeoNodes.
    Body: QuadraticBezier + FloatCurve + CurveToMesh (matches shape_quadratic)
    Drupelets: DistributePointsOnFaces (Poisson) + UV Sphere InstanceOnPoints
    """

    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    obj = bpy.context.active_object

    ng = bpy.data.node_groups.new("BlackberryBody", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT',
                            socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT',
                            socket_type='NodeSocketGeometry')

    nodes = ng.nodes
    links = ng.links

    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')

    # ── Body shape: CurveCircle + QuadraticBezier + FloatCurve + CurveToMesh ──
    circle = nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.inputs['Resolution'].default_value = resolution

    xform = nodes.new('GeometryNodeTransform')
    xform.inputs['Scale'].default_value = (cs_radius, cs_radius, cs_radius)
    links.new(circle.outputs['Curve'], xform.inputs['Geometry'])

    bezier = nodes.new('GeometryNodeCurveQuadraticBezier')
    bezier.inputs['Resolution'].default_value = resolution
    bezier.inputs['Start'].default_value = start
    bezier.inputs['Middle'].default_value = middle
    bezier.inputs['End'].default_value = end

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

    # Blender 5.0+: Scale input
    scale_inputs = [s for s in c2m.inputs if s.name == 'Scale']
    if scale_inputs:
        links.new(fcurve.outputs['Value'], scale_inputs[0])

    # ── Distribute drupelets on body surface (Poisson disk) ──
    dist_pts = nodes.new('GeometryNodeDistributePointsOnFaces')
    dist_pts.distribute_method = 'POISSON'
    dist_pts.inputs['Distance Min'].default_value = dist_min
    dist_pts.inputs['Density Max'].default_value = 10000.0
    links.new(c2m.outputs['Mesh'], dist_pts.inputs['Mesh'])

    # ── Drupelet template: UV Sphere + SubdivisionSurface ──
    uv_sphere = nodes.new('GeometryNodeMeshUVSphere')
    uv_sphere.inputs['Segments'].default_value = 16
    uv_sphere.inputs['Rings'].default_value = 8
    uv_sphere.inputs['Radius'].default_value = drupelet_scale

    subdiv = nodes.new('GeometryNodeSubdivisionSurface')
    subdiv.inputs['Level'].default_value = 1
    links.new(uv_sphere.outputs['Mesh'], subdiv.inputs['Mesh'])

    # ── InstanceOnPoints (align to surface normal via Rotation) ──
    inst = nodes.new('GeometryNodeInstanceOnPoints')
    links.new(dist_pts.outputs['Points'], inst.inputs['Points'])
    links.new(subdiv.outputs['Mesh'], inst.inputs['Instance'])
    links.new(dist_pts.outputs['Rotation'], inst.inputs['Rotation'])

    # ── RealizeInstances ──
    realize = nodes.new('GeometryNodeRealizeInstances')
    links.new(inst.outputs['Instances'], realize.inputs['Geometry'])

    # ── Join body + drupelets ──
    join = nodes.new('GeometryNodeJoinGeometry')
    links.new(c2m.outputs['Mesh'], join.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], join.inputs['Geometry'])

    links.new(join.outputs['Geometry'], group_out.inputs['Geometry'])

    # Apply modifier
    mod = obj.modifiers.new("Blackberry", 'NODES')
    mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    return obj

# ── stem (matches nodegroup_basic_stem) ───────────────────────────────────────

def build_basic_stem(cross_radius=0.075, quad_mid=(0, -0.05, 0.2),
                     quad_end=(-0.1, 0, 0.4), translation=(0, 0, 0)):
    """

    Thin tapered cylinder along a QuadraticBezier.
    """

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

def build_blackberry():
    np.random.seed(SEED)
    clear_scene()

    # From blackberry.py sample_cross_section_params
    _ = np.random.uniform(-100, 100)  # random seed (discarded)
    cs_radius = float(np.random.normal(0.9, 0.05))

    # From blackberry.py sample_shape_params
    radius_cp = [
        (0.0, 0.0),
        (0.0841, 0.3469),
        (float(np.random.uniform(0.4, 0.6)), 0.8),
        (0.9432, 0.4781),
        (1.0, 0.0),
    ]
    start = (float(np.random.uniform(-0.5, 0.5)),
             float(np.random.uniform(-0.5, 0.5)),
             float(np.random.uniform(-0.5, -3.0)))
    middle = (0.0, 0.0, 0.0)
    end = (0.0, 0.0, 1.0)

    # Build body + drupelets using GeoNodes
    # Drupelet scale=0.35 matches randomrotationscale(scale_mean=0.35)
    # Distance Min=0.4 matches point_on_mesh(Distance Min=0.4)
    body = build_blackberry_body_with_drupelets(
        radius_cp, cs_radius, start, middle, end,
        drupelet_scale=0.35, dist_min=0.4, resolution=256
    )

    # Stem at top of body — use Bezier endpoint as reference (not max vertex Z,
    # which includes drupelet protrusion and would cause floating stem)
    body_top_z = end[2]  # body axis endpoint = 1.0
    stem_r = float(np.random.normal(0.075, 0.005))
    mid = (float(np.random.uniform(-0.1, 0.1)),
           float(np.random.uniform(-0.1, 0.1)),
           float(np.random.uniform(0.2, 0.3)))
    end_s = (float(np.random.uniform(-0.2, 0.2)),
             float(np.random.uniform(-0.2, 0.2)),
             float(np.random.uniform(0.4, 0.6)))
    stem = build_basic_stem(cross_radius=stem_r, quad_mid=mid, quad_end=end_s,
                            translation=(0.0, 0.0, body_top_z - 0.10))

    result = join_objs([body, stem])

    # scale_multiplier = 0.3
    s = float(np.random.normal(1, 0.1)) * 0.3
    result.scale = (s, s, s)
    apply_tf(result)

    # Align top to Z=0 (hanging convention)
    max_z = max(v.co.z for v in result.data.vertices)
    result.location.z = -max_z
    apply_tf(result)

    return result

blackberry = build_blackberry()
blackberry.name = "FruitFactoryBlackberry"
