# [FL_INDEX: keywords="blender_factory, procedural_3d, LiteDoorFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LiteDoorFactory | Category: factories_geo
# Prompt: A dark navy arched door rendered as a 3D model, featuring a single inset rectangular lite (panel opening) positioned in the upper-center of the door face.

import os
import math
import random
import colorsys

import bmesh
import bpy
import numpy as np

SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

def _seed_mat(seed):
    _s = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s); random.seed(_s)

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h)%1, max(0,min(1,float(s))), max(0,min(1,float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear()
    return m

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def make_mat(seed, name="WoodMaterial"):
    _seed_mat(seed)
    base_hue = float(np.random.uniform(0.04, 0.1))
    c1 = _hsv2rgba(base_hue, np.random.uniform(0.4, 0.8), np.random.uniform(0.15, 0.5))
    c2 = _hsv2rgba(base_hue + float(np.random.uniform(-0.02, 0.02)), np.random.uniform(0.3, 0.6), np.random.uniform(0.3, 0.7))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(np.random.uniform(5, 20))
    noise.inputs["Detail"].default_value = 5.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = c1
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = c2
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.3, 0.6))
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

ELEM_MAT = make_mat(SEED, "LiteDoorFactory_Material")
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
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    m = obj.modifiers.new("w", "WELD")
    m.merge_threshold = 1e-3
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def spin_profile(obj, axis=(0, 1, 0)):
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
    bm = bmesh.new()
    verts = [bm.verts.new((i / n, 0, 0)) for i in range(n + 1)]
    for i in range(n):
        bm.edges.new((verts[i], verts[i + 1]))
    mesh = bpy.data.meshes.new("line")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("line", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def make_wire_mesh(vertices, edges):
    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in vertices]
    for e in edges:
        bm.edges.new((bm_verts[e[0]], bm_verts[e[1]]))
    mesh = bpy.data.meshes.new("wire")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("wire", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def apply_geo_radius(obj, radius, resolution=32, merge_dist=0.004):
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
    cc.inputs['Radius'].default_value = radius
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
    lever_radius = np.random.uniform(0.03, 0.04)
    lever_mid_radius = np.random.uniform(0.01, 0.02)
    lever_depth = np.random.uniform(0.05, 0.08)
    lever_mid_depth = np.random.uniform(0.15, 0.25)
    lever_length = log_uniform(0.15, 0.2)
    lever_type = np.random.choice(["wave", "cylinder", "bent"])
    handle_height = height * np.random.uniform(0.45, 0.50)

    x_a = np.array([lever_radius, lever_radius, lever_mid_radius, lever_mid_radius, 0.0])
    y_a = np.array([0, lever_mid_depth, lever_mid_depth, 1.0, 1.001]) * lever_depth
    base = make_bezier_profile(x_a, y_a, vector_locations=[0, 1, 2, 3])
    spin_profile(base, axis=(0, 1, 0))
    cap_spin(base)

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

    arm.scale = (lever_length, lever_length, lever_length)
    apply_tf(arm)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_edges_move(
        TRANSFORM_OT_translate={"value": (0, 0, lever_mid_radius * 2)})
    bpy.ops.object.mode_set(mode='OBJECT')

    add_mod(arm, "SOLIDIFY", thickness=lever_mid_radius, offset=0)
    add_mod(arm, "SUBSURF", render_levels=1, levels=1)

    arm.location = (-lever_mid_radius, lever_depth, -lever_mid_radius)
    apply_tf(arm, loc=True)

    obj = join_objs([base, arm])
    obj.location = (width * 0.1, depth / 2, handle_height)
    apply_tf(obj, loc=True)
    return obj

def make_pull(width, height, depth):
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
    else:
        verts = [
            (0, 0, pull_size),
            (0, pull_depth_val, pull_size),
            (pull_width_val, pull_depth_val, pull_size),
            (pull_width_val, pull_depth_val, 0),
        ]
        edges = [(0, 1), (1, 2), (2, 3)]

    obj = make_wire_mesh(verts, edges)
    add_mod(obj, "MIRROR", use_axis=(False, False, True))

    if to_bevel:
        add_mod(obj, "BEVEL", width=bevel_width, segments=4, affect="VERTICES")

    if is_circular:
        apply_geo_radius(obj, pull_radius, resolution=32)
    else:
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
    total_length = np.random.uniform(0.7, 0.9) * width
    thickness = np.random.uniform(0.025, 0.045) * height
    aspect_ratio = np.random.uniform(0.4, 0.6)
    height_ratio = np.random.uniform(0.7, 0.9)
    length_ratio = np.random.uniform(0.5, 0.8)
    end_length_ratio = np.random.uniform(0.1, 0.15)
    end_height_ratio = np.random.uniform(1.8, 3.0)
    z_offset = -np.random.uniform(0.0, 0.1) * height

    handle_z = height * 0.5 + z_offset
    main_half_y = thickness * aspect_ratio / 2
    bar_y = -main_half_y
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
    main = make_rounded_bar(total_length / 2, main_half_y, thickness / 2)
    main.location = (width / 2, bar_y, handle_z)
    apply_tf(main, loc=True)
    parts.append(main)

    end_len = total_length * end_length_ratio
    end_w = thickness * end_height_ratio
    end = make_rounded_bar(end_len / 2, end_w * aspect_ratio / 2, end_w / 2)
    end.location = (width / 2 - total_length / 2 + end_len / 2, bar_y, handle_z)
    apply_tf(end, loc=True)
    parts.append(end)

    grab_w = thickness * height_ratio
    grab_len = total_length * length_ratio
    grab = make_rounded_bar(grab_len / 2, grab_w * aspect_ratio / 2, grab_w / 2)
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
    return None

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
    arc_radius = width / 2
    n_seg = 24
    bm = bmesh.new()
    center_x = width / 2
    center_z = height

    front_center = bm.verts.new((center_x, 0, center_z))
    front_rim = []
    for i in range(n_seg + 1):
        angle = math.pi * i / n_seg
        x = center_x + arc_radius * math.cos(angle)
        z = center_z + arc_radius * math.sin(angle)
        front_rim.append(bm.verts.new((x, 0, z)))

    back_center = bm.verts.new((center_x, depth, center_z))
    back_rim = []
    for i in range(n_seg + 1):
        angle = math.pi * i / n_seg
        x = center_x + arc_radius * math.cos(angle)
        z = center_z + arc_radius * math.sin(angle)
        back_rim.append(bm.verts.new((x, depth, z)))

    for i in range(n_seg):
        bm.faces.new([front_center, front_rim[i], front_rim[i + 1]])
    for i in range(n_seg):
        bm.faces.new([back_center, back_rim[i + 1], back_rim[i]])
    for i in range(n_seg):
        bm.faces.new([front_rim[i], front_rim[i + 1],
                       back_rim[i + 1], back_rim[i]])
    bm.faces.new([front_rim[0], back_rim[0], back_rim[-1], front_rim[-1]])

    mesh = bpy.data.meshes.new("door_arc")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("door_arc", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

# ── Panel bevel ───────────────────────────────────────────────────────────

def bevel_panel(door, panel_dim, bevel_width, shrink_width, depth, attribute_name=None):
    x_min, x_max, y_min, y_max = panel_dim

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    cutter = bpy.context.active_object

    cmesh = cutter.data
    attr = cmesh.attributes.new("cut", 'INT', 'FACE')
    vals = np.ones(len(cmesh.polygons), dtype=np.int32)
    attr.data.foreach_set("value", vals)

    if attribute_name is not None:
        ga = cmesh.attributes.new(attribute_name, 'INT', 'FACE')
        ga.data.foreach_set("value", vals)

    cutter.location = ((x_max + x_min) / 2, bevel_width * 0.5 - 0.1, (y_max + y_min) / 2)
    cutter.scale = ((x_max - x_min) / 2 - 2e-3, 0.1, (y_max - y_min) / 2 - 2e-3)
    apply_tf(cutter)

    bool_mod = door.modifiers.new("pf", "BOOLEAN")
    bool_mod.operation = "DIFFERENCE"
    bool_mod.solver = "FLOAT"
    bool_mod.object = cutter
    bpy.context.view_layer.objects.active = door
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    prepare_for_boolean(door)

    cutter.location[1] += 0.2 + depth - bevel_width
    apply_tf(cutter, loc=True)

    bool_mod = door.modifiers.new("pb", "BOOLEAN")
    bool_mod.operation = "DIFFERENCE"
    bool_mod.solver = "FLOAT"
    bool_mod.object = cutter
    bpy.context.view_layer.objects.active = door
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    prepare_for_boolean(door)
    bpy.data.objects.remove(cutter, do_unlink=True)

    mesh = door.data
    n_polys = len(mesh.polygons)

    if "cut" in mesh.attributes and n_polys > 0:
        cut_data = np.zeros(n_polys, dtype=np.int32)
        mesh.attributes["cut"].data.foreach_get("value", cut_data)
        areas = np.zeros(n_polys)
        mesh.polygons.foreach_get("area", areas)

        sel = (cut_data > 0) & (areas > 0.01)
        if np.any(sel):
            mesh.polygons.foreach_set("select", sel.astype(bool))
            mesh.update()

            bpy.context.view_layer.objects.active = door
            door.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.inset(thickness=shrink_width)
            bpy.ops.mesh.inset(thickness=bevel_width, depth=bevel_width)
            bpy.ops.object.mode_set(mode='OBJECT')

        if "cut" in door.data.attributes:
            door.data.attributes.remove(door.data.attributes["cut"])

# ── Main builder ──────────────────────────────────────────────────────────

def build_lite_door():
    clear_scene()

    wall_thickness = np.random.uniform(0.2, 0.3)
    segment_margin = 1.4
    door_width_ratio = np.random.uniform(0.7, 0.8)
    width = (segment_margin - wall_thickness) * door_width_ratio
    height = np.random.uniform(2.0, 2.4)
    depth = wall_thickness * log_uniform(0.25, 0.5)
    panel_margin = log_uniform(0.08, 0.12)
    bevel_width = np.random.uniform(0.005, 0.01)
    shrink_width = log_uniform(0.005, 0.06)

    # Frame style (4 options with bevel_frame)
    frame_style = np.random.choice([
        "single_column", "full_frame_square", "full_frame_dome", "full_frame_double_door"])
    frame_width = np.random.uniform(0.04, 0.08)
    full_frame = frame_style != "single_column"
    top_dome = frame_style == "full_frame_dome"

    # Select lite configuration (matches source: 6 ranges via uniform())
    r = np.random.uniform()
    subdivide_glass = False
    if r <= 1 / 6:
        x_min, x_max = 0, 1
        y_min = np.random.uniform(0.4, 0.6)
        y_max = 1.0
        subdivide_glass = True
    elif r <= 1 / 3:
        x_min, x_max, y_min, y_max = 0, 1, 0, 1
        subdivide_glass = True
    elif r <= 1 / 2:
        x_min = 0
        x_max = np.random.uniform(0.3, 0.4)
        y_min = np.random.uniform(0.4, 0.6)
        y_max = 1.0
    elif r <= 2 / 3:
        x_min = 0
        x_max = np.random.uniform(0.3, 0.4)
        y_min = np.random.uniform(0.4, 0.6)
        y_max = 1.0
    elif r <= 5 / 6:
        x_min, x_max, y_min, y_max = 0, 1, 0, 1
    else:
        x = np.random.uniform(0.3, 0.35)
        x_min, x_max = x, 1 - x
        y_min = np.random.uniform(0.7, 0.8)
        y_max = 1.0

    if subdivide_glass:
        x_subdivisions = np.random.choice([1, 3])
        y_subdivisions = int(height / width * x_subdivisions) + np.random.randint(-1, 2)
        y_subdivisions = max(1, y_subdivisions)
    else:
        x_subdivisions = 1
        y_subdivisions = 1

    x_range = np.linspace(x_min, x_max, x_subdivisions + 1) * (width - panel_margin * 2) + panel_margin
    y_range = np.linspace(y_min, y_max, y_subdivisions + 1) * (height - panel_margin * 2) + panel_margin

    parts = []

    # Door slab
    door = make_door_slab(width, height, depth)
    door.name = "door_body"

    # Bevel glass panels
    for xi in range(x_subdivisions):
        for yi in range(y_subdivisions):
            px_min, px_max = x_range[xi], x_range[xi + 1]
            py_min, py_max = y_range[yi], y_range[yi + 1]
            pw = (px_max - px_min) / 2 - 2e-3
            ph = (py_max - py_min) / 2 - 2e-3
            if pw <= 0.01 or ph <= 0.01:
                continue
            bevel_panel(door, (px_min, px_max, py_min, py_max),
                       bevel_width, shrink_width, depth)

    parts.append(door)

    # Door frame
    frame = make_door_frame(width, height, depth, frame_width, full_frame, top_dome)
    if frame:
        parts.append(frame)

    # Door arc (dome top)
    if top_dome:
        arc = make_door_arc(width, height, depth)
        parts.append(arc)

    # Handle
    handle = make_handle(width, height, depth)
    if handle:
        parts.append(handle)

    result = join_objs(parts)

    # Apply bevel for rounded edges
    add_mod(result, "BEVEL", width=0.001, segments=1)

    result.name = "LiteDoorFactory"
    # [auto-append] ensure material bound
    if result is not None:
        if len(result.data.materials) == 0:
            result.data.materials.append(ELEM_MAT)
        elif result.data.materials[0] is None:
            result.data.materials[0] = ELEM_MAT
    return result

door = build_lite_door()
