# [FL_INDEX: keywords="blender_factory, procedural_3d, DoorFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: DoorFactory | Category: factories_geo
# Prompt: An arched-top door rendered as a detailed 3D model, featuring a dark charcoal frame with a curved arch at the top and two inset louvered panels in a warm copper/rose-gold tone.

import math
import random

import bmesh
import bpy
import numpy as np

SEED = 3451
random.seed(SEED)
np.random.seed(SEED)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj, loc=False):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if loc:
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    else:
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def add_mod(obj, mtype, **kw):
    m = obj.modifiers.new("", mtype)
    for k, v in kw.items():
        setattr(m, k, v)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

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

def prepare_for_boolean(obj):
    bpy.context.view_layer.objects.active = obj
    m = obj.modifiers.new("weld", "WELD")
    m.merge_threshold = 1e-4
    bpy.ops.object.modifier_apply(modifier=m.name)

def write_co(obj, coords):
    mesh = obj.data
    mesh.vertices.foreach_set('co', coords.flatten().astype(np.float32))
    mesh.update()

# ── Shared utilities ──────────────────────────────────────────────────────

def make_door_slab(width, height, depth):
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    slab = bpy.context.active_object
    slab.location = (1, 1, 1)
    apply_tf(slab, loc=True)
    slab.scale = (width / 2, depth / 2, height / 2)
    apply_tf(slab)
    return slab

# ── Handle utilities ──────────────────────────────────────────────────────

def make_bezier_profile(x_anchors, y_anchors, vector_locations, resolution=12):
    """Create a mesh from a 2D Bezier profile curve."""

    n = len(x_anchors)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    if n > 2:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.subdivide(number_cuts=n - 2)
        bpy.ops.object.mode_set(mode='OBJECT')
    points = obj.data.splines[0].bezier_points
    for i in range(n):
        points[i].co = (float(x_anchors[i]), float(y_anchors[i]), 0.0)
        if i in vector_locations:
            points[i].handle_left_type = "VECTOR"
            points[i].handle_right_type = "VECTOR"
        else:
            points[i].handle_left_type = "AUTO"
            points[i].handle_right_type = "AUTO"
    obj.data.splines[0].resolution_u = resolution
    # Convert Bezier curve to mesh
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    # Weld close vertices
    m = obj.modifiers.new("w", "WELD")
    m.merge_threshold = 1e-3
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def spin_profile(obj, axis=(0, 1, 0)):
    """Revolve a mesh profile 360 deg around an axis."""

    co = np.array([v.co[:] for v in obj.data.vertices])
    axis_np = np.array(axis, dtype=float)
    projected = co - np.outer(co @ axis_np, axis_np)
    mean_radius = np.mean(np.linalg.norm(projected, axis=-1))
    steps = min(int(2 * math.pi * mean_radius / 5e-3), 128)
    steps = max(steps, 16)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.spin(steps=steps, angle=2 * math.pi, axis=axis)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=1e-3)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj

def cap_spin(obj):
    """Cap open boundary edges of a revolved mesh."""

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj

def new_line(n):
    """Create a mesh line with n+1 vertices from (0,0,0) to (1,0,0)."""

    bm = bmesh.new()
    verts = [bm.verts.new((i / n, 0, 0)) for i in range(n + 1)]
    for i in range(n):
        bm.edges.new((verts[i], verts[i + 1]))
    mesh = bpy.data.meshes.new("line")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("line", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def make_wire_mesh(vertices, edges):
    """Create a mesh object from vertices and edges."""

    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in vertices]
    for e in edges:
        bm.edges.new((bm_verts[e[0]], bm_verts[e[1]]))
    mesh = bpy.data.meshes.new("wire")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("wire", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def apply_geo_radius(obj, radius, resolution=32, merge_dist=0.004):
    """Sweep a circular cross-section along wire edges using GeoNodes."""

    ng = bpy.data.node_groups.new("geo_radius", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = ng.nodes, ng.links
    gi = nodes.new('NodeGroupInput')
    go = nodes.new('NodeGroupOutput')
    m2c = nodes.new('GeometryNodeMeshToCurve')
    links.new(gi.outputs['Geometry'], m2c.inputs['Mesh'])
    scr = nodes.new('GeometryNodeSetCurveRadius')
    links.new(m2c.outputs['Curve'], scr.inputs['Curve'])
    scr.inputs['Radius'].default_value = radius
    cc = nodes.new('GeometryNodeCurvePrimitiveCircle')
    cc.inputs['Resolution'].default_value = resolution
    cc.inputs['Radius'].default_value = radius  # Set circle size directly (SetCurveRadius ignored in Blender 5.0)
    c2m = nodes.new('GeometryNodeCurveToMesh')
    links.new(scr.outputs['Curve'], c2m.inputs['Curve'])
    links.new(cc.outputs['Curve'], c2m.inputs['Profile Curve'])
    c2m.inputs['Fill Caps'].default_value = True
    mbd = nodes.new('GeometryNodeMergeByDistance')
    links.new(c2m.outputs['Mesh'], mbd.inputs['Geometry'])
    mbd.inputs['Distance'].default_value = merge_dist
    links.new(mbd.outputs['Geometry'], go.inputs['Geometry'])
    mod = obj.modifiers.new("gr", 'NODES')
    mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.node_groups.remove(ng)
    return obj

# ── Handle implementations ────────────────────────────────────────────────

def make_knob(width, height, depth):
    """Knob handle: 7-point Bezier lathe profile revolved around Y axis."""

    knob_radius = np.random.uniform(0.03, 0.04)
    knob_depth = np.random.uniform(0.08, 0.1)
    base_r = np.random.uniform(1.1, 1.2)
    mid_r = np.random.uniform(0.4, 0.5)
    end_r = np.random.uniform(0.6, 0.8)
    radius_mids = [base_r, base_r, mid_r, mid_r, 1.0, end_r, 0.0]
    depth_mids = [0.0, np.random.uniform(0.1, 0.15), np.random.uniform(0.25, 0.3),
                  np.random.uniform(0.35, 0.45), np.random.uniform(0.6, 0.8), 1.0, 1.001]
    x_anchors = np.array(radius_mids) * knob_radius
    y_anchors = np.array(depth_mids) * knob_depth
    obj = make_bezier_profile(x_anchors, y_anchors, vector_locations=[0, 2, 3])
    spin_profile(obj, axis=(0, 1, 0))
    cap_spin(obj)
    handle_height = height * np.random.uniform(0.45, 0.50)
    obj.location = (width * 0.1, depth / 2, handle_height)
    apply_tf(obj, loc=True)
    return obj

def make_lever(width, height, depth):
    """Lever handle: spun rosette base + shaped arm."""

    lever_radius = np.random.uniform(0.03, 0.04)
    lever_mid_radius = np.random.uniform(0.01, 0.02)
    lever_depth = np.random.uniform(0.05, 0.08)
    lever_mid_depth = np.random.uniform(0.15, 0.25)
    lever_length = log_uniform(0.15, 0.2)
    lever_type = np.random.choice(["wave", "cylinder", "bent"])
    handle_height = height * np.random.uniform(0.45, 0.50)

    # --- Rosette base (5-point Bezier lathe) ---
    x_a = np.array([lever_radius, lever_radius, lever_mid_radius, lever_mid_radius, 0.0])
    y_a = np.array([0, lever_mid_depth, lever_mid_depth, 1.0, 1.001]) * lever_depth
    base = make_bezier_profile(x_a, y_a, vector_locations=[0, 1, 2, 3])
    spin_profile(base, axis=(0, 1, 0))
    cap_spin(base)

    # --- Arm (5-vertex line with deformation) ---
    arm = new_line(4)
    if lever_type == "wave":
        co = np.array([v.co[:] for v in arm.data.vertices])
        co[1, 2] = -np.random.uniform(0.2, 0.3)
        co[3, 2] = np.random.uniform(0.1, 0.15)
        for i, v in enumerate(arm.data.vertices):
            v.co = co[i]
        arm.data.update()
    elif lever_type == "bent":
        co = np.array([v.co[:] for v in arm.data.vertices])
        co[4, 1] = -np.random.uniform(0.2, 0.3)
        for i, v in enumerate(arm.data.vertices):
            v.co = co[i]
        arm.data.update()
    # "cylinder": line stays straight

    arm.scale = (lever_length, lever_length, lever_length)
    apply_tf(arm)

    # Extrude edges in +Z to create flat strip
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_edges_move(
        TRANSFORM_OT_translate={"value": (0, 0, lever_mid_radius * 2)})
    bpy.ops.object.mode_set(mode='OBJECT')

    # Solidify to add thickness + SUBSURF for smoothing
    add_mod(arm, "SOLIDIFY", thickness=lever_mid_radius, offset=0)
    add_mod(arm, "SUBSURF", render_levels=1, levels=1)

    # Position arm at front of rosette
    arm.location = (-lever_mid_radius, lever_depth, -lever_mid_radius)
    apply_tf(arm, loc=True)

    obj = join_objs([base, arm])
    obj.location = (width * 0.1, depth / 2, handle_height)
    apply_tf(obj, loc=True)
    return obj

def make_pull(width, height, depth):
    """Pull handle: wire skeleton + mirror + optional bevel + tube sweep."""

    pull_size = log_uniform(0.1, 0.4)
    pull_depth_val = np.random.uniform(0.05, 0.08)
    pull_width_val = log_uniform(0.08, 0.15)
    pull_extension = np.random.uniform(0.05, 0.15)
    pull_radius = np.random.uniform(0.01, 0.02)
    pull_type = np.random.choice(["u", "tee", "zed"])
    is_circular = np.random.uniform() < 0.5 or pull_type == "zed"
    to_bevel = np.random.uniform() < 0.5
    bevel_width = np.random.uniform(0.02, 0.04)
    handle_height = height * np.random.uniform(0.45, 0.50)
    handle_offset = width * 0.1

    # Build wire skeleton
    if pull_type == "u":
        verts = [
            (0, 0, pull_size),
            (0, pull_depth_val, pull_size),
            (0, pull_depth_val, 0),
        ]
        edges = [(0, 1), (1, 2)]
    elif pull_type == "tee":
        verts = [
            (0, 0, pull_size),
            (0, pull_depth_val, pull_size),
            (0, pull_depth_val, 0),
            (0, pull_depth_val, pull_size + pull_extension),
        ]
        edges = [(0, 1), (1, 2), (1, 3)]
    else:  # zed
        verts = [
            (0, 0, pull_size),
            (0, pull_depth_val, pull_size),
            (pull_width_val, pull_depth_val, pull_size),
            (pull_width_val, pull_depth_val, 0),
        ]
        edges = [(0, 1), (1, 2), (2, 3)]

    obj = make_wire_mesh(verts, edges)

    # Mirror across Z=0 for symmetry
    add_mod(obj, "MIRROR", use_axis=(False, False, True))

    # Optional vertex bevel for rounded corners
    if to_bevel:
        add_mod(obj, "BEVEL", width=bevel_width, segments=4, affect="VERTICES")

    if is_circular:
        # Circular cross-section via GeoNodes (MeshToCurve → CurveToMesh)
        apply_geo_radius(obj, pull_radius, resolution=32)
    else:
        # Rectangular cross-section via extrude + solidify
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_edges_move(
            TRANSFORM_OT_translate={"value": (pull_radius * 2, 0, 0)})
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.location = (-pull_radius, -pull_radius, -pull_radius)
        apply_tf(obj, loc=True)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        add_mod(obj, "SOLIDIFY", thickness=pull_radius * 2, offset=0)

    obj.location = (handle_offset, depth / 2, handle_height)
    apply_tf(obj, loc=True)
    return obj

def make_bar_handle(width, height, depth):
    """Push bar handle: mounting bar + end bracket + grab bar."""

    total_length = np.random.uniform(0.7, 0.9) * width
    thickness = np.random.uniform(0.025, 0.045) * height
    aspect_ratio = np.random.uniform(0.4, 0.6)
    height_ratio = np.random.uniform(0.7, 0.9)
    length_ratio = np.random.uniform(0.5, 0.8)
    end_length_ratio = np.random.uniform(0.1, 0.15)
    end_height_ratio = np.random.uniform(1.8, 3.0)
    z_offset = -np.random.uniform(0.0, 0.1) * height

    handle_z = height * 0.5 + z_offset
    # Main bar at door front surface (back face at Y=0, extends toward -Y)
    main_half_y = thickness * aspect_ratio / 2
    bar_y = -main_half_y
    # Grab bar further outward (more negative Y = toward viewer)
    grab_y_offset = thickness * aspect_ratio * 0.4

    def make_rounded_bar(half_x, half_y, half_z):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        bar = bpy.context.active_object
        bar.scale = (half_x, half_y, half_z)
        apply_tf(bar)
        bev = min(half_x, half_y, half_z) * 0.7
        if bev > 1e-4:
            add_mod(bar, "BEVEL", width=bev, segments=4,
                    limit_method="ANGLE", angle_limit=math.radians(60))
        return bar

    parts = []

    # Main horizontal bar (mounting bar at door surface)
    main = make_rounded_bar(total_length / 2,
                             main_half_y,
                             thickness / 2)
    main.location = (width / 2, bar_y, handle_z)
    apply_tf(main, loc=True)
    parts.append(main)

    # End bracket (wider, shorter piece at one end — mounting plate)
    end_len = total_length * end_length_ratio
    end_w = thickness * end_height_ratio
    end = make_rounded_bar(end_len / 2,
                            end_w * aspect_ratio / 2,
                            end_w / 2)
    end.location = (width / 2 - total_length / 2 + end_len / 2, bar_y, handle_z)
    apply_tf(end, loc=True)
    parts.append(end)

    # Grab bar (the part you push — offset outward from door)
    grab_w = thickness * height_ratio
    grab_len = total_length * length_ratio
    grab = make_rounded_bar(grab_len / 2,
                             grab_w * aspect_ratio / 2,
                             grab_w / 2)
    grab_z_shift = (-total_length / 2 + end_len) * 0.95
    grab.location = (width / 2 + grab_z_shift, bar_y - grab_y_offset, handle_z)
    apply_tf(grab, loc=True)
    parts.append(grab)

    return join_objs(parts)

def make_handle(width, height, depth):
    handle_type = np.random.choice(
        ["knob", "lever", "pull", "bar", "none"],
        p=[0.25, 0.25, 0.25, 0.20, 0.05],
    )
    if handle_type == "knob":
        return make_knob(width, height, depth)
    elif handle_type == "lever":
        return make_lever(width, height, depth)
    elif handle_type == "pull":
        return make_pull(width, height, depth)
    elif handle_type == "bar":
        return make_bar_handle(width, height, depth)
    return None  # "none" type

# ── Door frame ────────────────────────────────────────────────────────────

def bevel_frame(obj, offset=0.008):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    m = obj.modifiers.new("bev", "BEVEL")
    m.width = offset
    m.segments = 3
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(60)
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def make_door_frame(width, height, depth, frame_width, full_frame, top_dome):
    """Door frame: single column, square frame, or dome frame."""

    parts = []
    if not full_frame:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
        col = bpy.context.active_object
        col.scale = (frame_width / 2, depth / 2, height / 2)
        col.location = (-frame_width / 2, depth / 2, height / 2)
        apply_tf(col)
        bevel_frame(col)
        parts.append(col)
    else:
        for side_x in [-frame_width / 2, width + frame_width / 2]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
            col = bpy.context.active_object
            col.scale = (frame_width / 2, depth / 2, height / 2 + frame_width / 2)
            col.location = (side_x, depth / 2, height / 2)
            apply_tf(col)
            bevel_frame(col)
            parts.append(col)
        if not top_dome:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
            top = bpy.context.active_object
            top.scale = (width / 2 + frame_width, depth / 2, frame_width / 2)
            top.location = (width / 2, depth / 2, height + frame_width / 2)
            apply_tf(top)
            bevel_frame(top)
            parts.append(top)
    if not parts:
        return None
    return join_objs(parts)

def make_door_arc(width, height, depth):
    """Solid semicircular dome filling the top of the door."""

    arc_radius = width / 2
    n_seg = 24
    bm = bmesh.new()
    center_x = width / 2
    center_z = height

    # Front face: half-disc (fan from center)
    front_center = bm.verts.new((center_x, 0, center_z))
    front_rim = []
    for i in range(n_seg + 1):
        angle = math.pi * i / n_seg
        x = center_x + arc_radius * math.cos(angle)
        z = center_z + arc_radius * math.sin(angle)
        front_rim.append(bm.verts.new((x, 0, z)))

    # Back face: half-disc
    back_center = bm.verts.new((center_x, depth, center_z))
    back_rim = []
    for i in range(n_seg + 1):
        angle = math.pi * i / n_seg
        x = center_x + arc_radius * math.cos(angle)
        z = center_z + arc_radius * math.sin(angle)
        back_rim.append(bm.verts.new((x, depth, z)))

    # Front fan triangles
    for i in range(n_seg):
        bm.faces.new([front_center, front_rim[i], front_rim[i + 1]])

    # Back fan triangles (reversed winding)
    for i in range(n_seg):
        bm.faces.new([back_center, back_rim[i + 1], back_rim[i]])

    # Side faces (curved surface between front and back rims)
    for i in range(n_seg):
        bm.faces.new([front_rim[i], front_rim[i + 1],
                       back_rim[i + 1], back_rim[i]])

    # Bottom edge (straight line connecting the two ends of the semicircle)
    bm.faces.new([front_rim[0], back_rim[0], back_rim[-1], front_rim[-1]])

    mesh = bpy.data.meshes.new("door_arc")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("door_arc", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def bevel_panel(door, panel_dim, bevel_width, shrink_width, depth, attribute_name=None):
    x_min, x_max, y_min, y_max = panel_dim

    # Create CENTERED cube (match source new_cube: vertices from -1 to 1)
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    cutter = bpy.context.active_object

    # Write 'cut' attribute to all cutter faces for boolean attribute transfer
    cmesh = cutter.data
    attr = cmesh.attributes.new("cut", 'INT', 'FACE')
    vals = np.ones(len(cmesh.polygons), dtype=np.int32)
    attr.data.foreach_set("value", vals)

    # If this is a glass panel, also mark with that attribute
    if attribute_name is not None:
        ga = cmesh.attributes.new(attribute_name, 'INT', 'FACE')
        ga.data.foreach_set("value", vals)

    # Position and scale cutter for front face pocket
    # Source: location = (center_x, bevel_width*0.5 - 0.1, center_z)
    # Y extent: [-0.1, 0.1] * scale 0.1 centered at bevel_width*0.5 - 0.1
    # = [bevel_width*0.5 - 0.2, bevel_width*0.5] — only ~0.005 inside door front face
    cutter.location = ((x_max + x_min) / 2, bevel_width * 0.5 - 0.1, (y_max + y_min) / 2)
    cutter.scale = ((x_max - x_min) / 2 - 2e-3, 0.1, (y_max - y_min) / 2 - 2e-3)
    apply_tf(cutter)

    # Boolean on front face (use FLOAT solver for Blender 5.0 robustness)
    bool_mod = door.modifiers.new("pf", "BOOLEAN")
    bool_mod.operation = "DIFFERENCE"
    bool_mod.solver = "FLOAT"
    bool_mod.object = cutter
    bpy.context.view_layer.objects.active = door
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    prepare_for_boolean(door)

    # Move cutter to back face (source: location[1] += 0.2 + depth - bevel_width)
    cutter.location[1] += 0.2 + depth - bevel_width
    apply_tf(cutter, loc=True)

    # Boolean on back face
    bool_mod = door.modifiers.new("pb", "BOOLEAN")
    bool_mod.operation = "DIFFERENCE"
    bool_mod.solver = "FLOAT"
    bool_mod.object = cutter
    bpy.context.view_layer.objects.active = door
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    prepare_for_boolean(door)
    bpy.data.objects.remove(cutter, do_unlink=True)

    # Select "cut" faces and apply INSET operations (the key missing step!)
    mesh = door.data
    n_polys = len(mesh.polygons)

    if "cut" in mesh.attributes and n_polys > 0:
        # Read cut attribute
        cut_data = np.zeros(n_polys, dtype=np.int32)
        mesh.attributes["cut"].data.foreach_get("value", cut_data)

        # Read face areas
        areas = np.zeros(n_polys)
        mesh.polygons.foreach_get("area", areas)

        # Select large cut faces (source: area > 0.01 & cut attribute)
        sel = (cut_data > 0) & (areas > 0.01)

        if np.any(sel):
            mesh.polygons.foreach_set("select", sel.astype(bool))
            mesh.update()

            bpy.context.view_layer.objects.active = door
            door.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
            # Two-stage inset creates the raised panel profile
            bpy.ops.mesh.inset(thickness=shrink_width)
            bpy.ops.mesh.inset(thickness=bevel_width, depth=bevel_width)
            bpy.ops.object.mode_set(mode='OBJECT')

        # Clean up cut attribute
        if "cut" in door.data.attributes:
            door.data.attributes.remove(door.data.attributes["cut"])

# ── Panel Door ────────────────────────────────────────────────────────────

def build_panel_door(width, height, depth):
    panel_margin = log_uniform(0.08, 0.12)
    bevel_width = np.random.uniform(0.005, 0.01)
    shrink_width = log_uniform(0.005, 0.06)
    x_sub = 1 if np.random.uniform() < 0.5 else 2
    y_sub = max(1, int(np.random.binomial(5, 0.45)))

    door = make_door_slab(width, height, depth)
    x_cuts = np.random.randint(1, 4, x_sub)
    x_cuts = np.cumsum(x_cuts / x_cuts.sum())
    y_cuts = np.sort(np.random.randint(2, 5, y_sub))[::-1]
    y_cuts = np.cumsum(y_cuts / y_cuts.sum())

    for j in range(len(y_cuts)):
        for i in range(len(x_cuts)):
            xm = panel_margin + (width - panel_margin) * (x_cuts[i - 1] if i > 0 else 0)
            xM = (width - panel_margin) * x_cuts[i]
            ym = panel_margin + (height - panel_margin) * (y_cuts[j - 1] if j > 0 else 0)
            yM = (height - panel_margin) * y_cuts[j]
            bevel_panel(door, (xm, xM, ym, yM), bevel_width, shrink_width, depth)

    handle = make_handle(width, height, depth)
    return join_objs([door, handle])

# ── Glass Panel Door ──────────────────────────────────────────────────────

def build_glass_panel_door(width, height, depth):
    panel_margin = log_uniform(0.08, 0.12)
    bevel_width = np.random.uniform(0.005, 0.01)
    shrink_width = log_uniform(0.005, 0.06)
    x_sub = 2
    y_sub = max(2, int(np.random.binomial(5, 0.5)))
    merge_glass = y_sub < 4

    door = make_door_slab(width, height, depth)
    x_cuts = np.random.randint(1, 4, x_sub)
    x_cuts = np.cumsum(x_cuts / x_cuts.sum())
    y_cuts = np.sort(np.random.randint(2, 5, y_sub))[::-1]
    y_cuts = np.cumsum(y_cuts / y_cuts.sum())

    # Build panel list
    panels = []
    for j in range(len(y_cuts)):
        for i in range(len(x_cuts)):
            xm = panel_margin + (width - panel_margin) * (x_cuts[i - 1] if i > 0 else 0)
            xM = (width - panel_margin) * x_cuts[i]
            ym = panel_margin + (height - panel_margin) * (y_cuts[j - 1] if j > 0 else 0)
            yM = (height - panel_margin) * y_cuts[j]
            panels.append((xm, xM, ym, yM))

    # Source: glass panels are the top row, with optional merge
    if merge_glass:
        # Merge top x_sub panels into one glass panel
        first = panels[-x_sub]
        last = panels[-1]
        merged = (first[0], last[1], first[2], last[3])
        # Bottom row = normal panels, merged top = glass
        for p in panels[:x_sub]:
            bevel_panel(door, p, bevel_width, shrink_width, depth)
        bevel_panel(door, merged, bevel_width, shrink_width, depth, attribute_name="glass")
    else:
        for p in panels[:-x_sub]:
            bevel_panel(door, p, bevel_width, shrink_width, depth)
        for p in panels[-x_sub:]:
            bevel_panel(door, p, bevel_width, shrink_width, depth, attribute_name="glass")

    handle = make_handle(width, height, depth)
    return join_objs([door, handle])

# ── Louver Door ───────────────────────────────────────────────────────────

def make_louver_slats(x_min, x_max, y_min, y_max, depth, louver_angle, louver_size, louver_width):
    bpy.ops.mesh.primitive_plane_add(size=2.0)
    slat = bpy.context.active_object
    y_upper = y_min + depth * math.tan(louver_angle)
    coords = np.array([
        [x_min, 0, y_min], [x_max, 0, y_min],
        [x_min, depth, y_upper], [x_max, depth, y_upper],
    ], dtype=np.float32)
    write_co(slat, coords)
    add_mod(slat, "SOLIDIFY", thickness=louver_width, offset=0)
    n_slats = max(1, int(np.ceil((y_max - y_min) / louver_size) + 0.5))
    add_mod(slat, "ARRAY", use_relative_offset=False, use_constant_offset=True,
            constant_offset_displace=(0, 0, louver_size), count=n_slats)
    slat.location[2] -= depth * math.tan(louver_angle) / 2
    apply_tf(slat, loc=True)

    bpy.context.view_layer.objects.active = slat
    slat.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(plane_co=(0, 0, y_min), plane_no=(0, 0, 1),
                         use_fill=True, clear_inner=True)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(plane_co=(0, 0, y_max), plane_no=(0, 0, 1),
                         use_fill=True, clear_outer=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    return slat

def build_louver_door(width, height, depth):
    panel_margin = log_uniform(0.08, 0.12)
    y_sub = max(1, int(np.random.binomial(5, 0.4)))
    has_panel = np.random.uniform() < 0.7
    has_upper_panel = np.random.uniform() < 0.5
    louver_width = np.random.uniform(0.002, 0.004)
    louver_margin = np.random.uniform(0.02, 0.03)
    louver_size = log_uniform(0.05, 0.1)
    louver_angle = np.random.uniform(math.pi / 4.5, math.pi / 3.5)

    y_cuts = np.sort(np.random.randint(2, 5, y_sub))[::-1]
    y_cuts = np.cumsum(y_cuts / y_cuts.sum())

    panels = []
    for j in range(len(y_cuts)):
        ym = panel_margin + (height - panel_margin) * (y_cuts[j - 1] if j > 0 else 0)
        yM = (height - panel_margin) * y_cuts[j]
        panels.append((panel_margin, width - panel_margin, ym, yM))

    if len(panels) == 1:
        louver_panels = [panels[0]]
    elif len(panels) == 2:
        louver_panels = [panels[0], panels[1]] if not has_panel else [panels[1]]
    else:
        louver_panels = [panels[0], panels[-1]] if has_upper_panel else [panels[0]]

    door = make_door_slab(width, height, depth)
    parts = [door]

    for panel_dim in louver_panels:
        x_min, x_max, y_min, y_max = panel_dim
        # Cut zone from door
        bpy.ops.mesh.primitive_cube_add(size=2.0)
        cutter = bpy.context.active_object
        cutter.location = (1, 1, 1)
        apply_tf(cutter, loc=True)
        cutter.location = (x_min - louver_margin, -louver_width, y_min - louver_margin)
        cutter.scale = ((x_max - x_min) / 2 + louver_margin,
                         depth / 2 + louver_width,
                         (y_max - y_min) / 2 + louver_margin)
        apply_tf(cutter)

        bpy.ops.mesh.primitive_cube_add(size=2.0)
        hole = bpy.context.active_object
        hole.location = (1, 1, 1)
        apply_tf(hole, loc=True)
        hole.location = (x_min, -louver_width * 2, y_min)
        hole.scale = ((x_max - x_min) / 2, depth / 2 + louver_width * 2, (y_max - y_min) / 2)
        apply_tf(hole)

        bmod = cutter.modifiers.new("h", "BOOLEAN")
        bmod.operation = "DIFFERENCE"
        bmod.solver = "FLOAT"
        bmod.object = hole
        bpy.context.view_layer.objects.active = cutter
        bpy.ops.object.modifier_apply(modifier=bmod.name)
        bpy.data.objects.remove(hole, do_unlink=True)

        bmod2 = door.modifiers.new("lc", "BOOLEAN")
        bmod2.operation = "DIFFERENCE"
        bmod2.solver = "FLOAT"
        bmod2.object = cutter
        bpy.context.view_layer.objects.active = door
        bpy.ops.object.modifier_apply(modifier=bmod2.name)
        prepare_for_boolean(door)
        parts.append(cutter)

        slat = make_louver_slats(x_min, x_max, y_min, y_max, depth,
                                  louver_angle, louver_size, louver_width)
        parts.append(slat)

    handle = make_handle(width, height, depth)
    if handle:
        parts.append(handle)
    return join_objs(parts)

# ── Lite Door ─────────────────────────────────────────────────────────────

def build_lite_door(width, height, depth):
    panel_margin = log_uniform(0.08, 0.12)
    bevel_width = np.random.uniform(0.005, 0.01)
    shrink_width = log_uniform(0.005, 0.06)

    # Lite configs (match source 6-range selection)
    r = np.random.uniform()
    subdivide_glass = False
    if r <= 1 / 6:
        x_min_f, x_max_f, y_min_f, y_max_f = 0, 1, np.random.uniform(0.4, 0.6), 1
        subdivide_glass = True
    elif r <= 1 / 3:
        x_min_f, x_max_f, y_min_f, y_max_f = 0, 1, 0, 1
        subdivide_glass = True
    elif r <= 1 / 2:
        x_min_f, x_max_f, y_min_f, y_max_f = 0, np.random.uniform(0.3, 0.4), np.random.uniform(0.4, 0.6), 1
    elif r <= 2 / 3:
        x_min_f, x_max_f, y_min_f, y_max_f = 0, np.random.uniform(0.3, 0.4), np.random.uniform(0.4, 0.6), 1
    elif r <= 5 / 6:
        x_min_f, x_max_f, y_min_f, y_max_f = 0, 1, 0, 1
    else:
        x_val = np.random.uniform(0.3, 0.35)
        x_min_f, x_max_f, y_min_f, y_max_f = x_val, 1 - x_val, np.random.uniform(0.7, 0.8), 1

    if subdivide_glass:
        x_sub = np.random.choice([1, 3])
        y_sub = max(1, int(height / width * x_sub) + np.random.randint(-1, 2))
    else:
        x_sub, y_sub = 1, 1

    door = make_door_slab(width, height, depth)

    # Generate lite glass panels in the specified region
    x_range = np.linspace(x_min_f, x_max_f, x_sub + 1) * (width - panel_margin * 2) + panel_margin
    y_range = np.linspace(y_min_f, y_max_f, y_sub + 1) * (height - panel_margin * 2) + panel_margin

    for xi in range(x_sub):
        for yi in range(y_sub):
            bevel_panel(door, (x_range[xi], x_range[xi + 1], y_range[yi], y_range[yi + 1]),
                        bevel_width, shrink_width, depth, attribute_name="glass")

    handle = make_handle(width, height, depth)
    return join_objs([door, handle])

# ── Main build (random dispatch) ──────────────────────────────────────────

def build_door():
    clear_scene()

    wall_thickness = np.random.uniform(0.2, 0.3)
    segment_margin = 1.4
    door_width_ratio = np.random.uniform(0.7, 0.8)
    width = (segment_margin - wall_thickness) * door_width_ratio
    height = np.random.uniform(2.0, 2.4)
    depth = wall_thickness * log_uniform(0.25, 0.5)

    # Frame style (matches source: 4 equal-weight options)
    frame_style = np.random.choice([
        "single_column", "full_frame_square", "full_frame_dome", "full_frame_double_door"])
    frame_width = np.random.uniform(0.04, 0.08)
    full_frame = frame_style != "single_column"
    top_dome = frame_style == "full_frame_dome"

    # Random dispatch (match source weights)
    door_types = ["panel", "glass_panel", "louver", "lite"]
    probs = np.array([4, 2, 3, 3], dtype=float)
    probs /= probs.sum()
    door_type = np.random.choice(door_types, p=probs)

    if door_type == "panel":
        result = build_panel_door(width, height, depth)
    elif door_type == "glass_panel":
        result = build_glass_panel_door(width, height, depth)
    elif door_type == "louver":
        result = build_louver_door(width, height, depth)
    else:
        result = build_lite_door(width, height, depth)

    # Add frame and dome
    extra_parts = [result]
    frame = make_door_frame(width, height, depth, frame_width, full_frame, top_dome)
    if frame:
        extra_parts.append(frame)
    if top_dome:
        arc = make_door_arc(width, height, depth)
        extra_parts.append(arc)
    if len(extra_parts) > 1:
        result = join_objs(extra_parts)

    result.name = "DoorFactory"
    return result

door = build_door()
