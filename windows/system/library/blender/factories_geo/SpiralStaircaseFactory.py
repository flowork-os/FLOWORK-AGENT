# [FL_INDEX: keywords="blender_factory, procedural_3d, SpiralStaircaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SpiralStaircaseFactory | Category: factories_geo
# Prompt: An elegant spiral staircase rendered as a 3D model, featuring triangular wedge-shaped treads that radiate outward from a central cylindrical post and wrap in a tight helix upward.

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
    """Wood: warm brown with noise grain pattern."""

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

ELEM_MAT = make_mat(SEED, "SpiralStaircaseFactory_Material")
np.random.seed(SEED)


def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def weighted_choice(items):
    """items: list of (weight, value)"""

    weights = [w for w, v in items]
    values = [v for w, v in items]
    total = sum(weights)
    probs = [w / total for w in weights]
    return values[np.random.choice(len(values), p=probs)]

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
    if mtype == "SUBSURF" and getattr(m, 'levels', 1) == 0:
        obj.modifiers.remove(m)
        return obj
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def join_objs(objs):
    if not objs:
        return None
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def geo_radius_tube(obj, radius, resolution=16):
    """Apply GeoNodes: MeshToCurve -> SetCurveRadius -> CurveToMesh(circle)."""

    tree = bpy.data.node_groups.new("geo_radius", 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = tree.nodes.new('NodeGroupInput')
    inp.location = (-400, 0)

    m2c = tree.nodes.new('GeometryNodeMeshToCurve')
    m2c.location = (-200, 0)
    tree.links.new(inp.outputs[0], m2c.inputs[0])

    scr = tree.nodes.new('GeometryNodeSetCurveRadius')
    scr.location = (0, 0)
    scr.inputs['Radius'].default_value = radius
    tree.links.new(m2c.outputs[0], scr.inputs[0])

    circle = tree.nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.location = (0, -200)
    circle.inputs['Resolution'].default_value = resolution
    circle.inputs['Radius'].default_value = 1.0

    c2m = tree.nodes.new('GeometryNodeCurveToMesh')
    c2m.location = (200, 0)
    tree.links.new(scr.outputs[0], c2m.inputs['Curve'])
    tree.links.new(circle.outputs[0], c2m.inputs['Profile Curve'])
    c2m.inputs['Fill Caps'].default_value = True
    try:
        c2m.inputs['Scale'].default_value = radius
    except (KeyError, IndexError):
        pass

    out = tree.nodes.new('NodeGroupOutput')
    out.location = (400, 0)
    tree.links.new(c2m.outputs[0], out.inputs[0])

    mod = obj.modifiers.new("geo_r", 'NODES')
    mod.node_group = tree
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj

def make_curved_step(inner_r, outer_r, a0, a1, z_base, step_h):
    """Wedge step between angles a0..a1 at given z_base, extruded by step_h."""

    n_arc = max(3, int(abs(a1 - a0) / (math.pi / 12)))
    bm = bmesh.new()

    angles = [a0 + (a1 - a0) * k / n_arc for k in range(n_arc + 1)]

    # Bottom face vertices: inner arc then outer arc (reversed for correct winding)
    bot_inner = [bm.verts.new((inner_r * math.cos(a), inner_r * math.sin(a), 0))
                 for a in angles]
    bot_outer = [bm.verts.new((outer_r * math.cos(a), outer_r * math.sin(a), 0))
                 for a in angles]
    # Top ring
    top_inner = [bm.verts.new((v.co.x, v.co.y, step_h)) for v in bot_inner]
    top_outer = [bm.verts.new((v.co.x, v.co.y, step_h)) for v in bot_outer]

    # Bottom face quads
    for k in range(n_arc):
        bm.faces.new([bot_inner[k], bot_inner[k + 1],
                       bot_outer[k + 1], bot_outer[k]])
    # Top face quads
    for k in range(n_arc):
        bm.faces.new([top_inner[k + 1], top_inner[k],
                       top_outer[k], top_outer[k + 1]])
    # Outer arc side
    for k in range(n_arc):
        bm.faces.new([bot_outer[k], bot_outer[k + 1],
                       top_outer[k + 1], top_outer[k]])
    # Inner arc side
    for k in range(n_arc):
        bm.faces.new([bot_inner[k + 1], bot_inner[k],
                       top_inner[k], top_inner[k + 1]])
    # Start cap (radial face at a0)
    bm.faces.new([bot_inner[0], bot_outer[0], top_outer[0], top_inner[0]])
    # End cap (radial face at a1)
    bm.faces.new([bot_outer[-1], bot_inner[-1], top_inner[-1], top_outer[-1]])

    mesh = bpy.data.meshes.new("spiral_step")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("spiral_step", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location.z = z_base
    apply_tf(obj)
    return obj

def make_tread(inner_r, outer_r, a0, a1, z_pos, tread_h, tread_overhang):
    """Tread board on top of a step with slight overhang."""
    # Tread extends slightly beyond the step
    tr_inner = max(0.001, inner_r - tread_overhang)
    tr_outer = outer_r + tread_overhang
    # Widen the angle slightly for overhang
    da = tread_overhang / max(outer_r, 0.01)
    ta0 = a0 - da * 0.5
    ta1 = a1 + da * 0.5

    n_arc = max(3, int(abs(ta1 - ta0) / (math.pi / 12)))
    bm = bmesh.new()

    angles = [ta0 + (ta1 - ta0) * k / n_arc for k in range(n_arc + 1)]

    bot_inner = [bm.verts.new((tr_inner * math.cos(a), tr_inner * math.sin(a), 0))
                 for a in angles]
    bot_outer = [bm.verts.new((tr_outer * math.cos(a), tr_outer * math.sin(a), 0))
                 for a in angles]
    top_inner = [bm.verts.new((v.co.x, v.co.y, tread_h)) for v in bot_inner]
    top_outer = [bm.verts.new((v.co.x, v.co.y, tread_h)) for v in bot_outer]

    for k in range(n_arc):
        bm.faces.new([bot_inner[k], bot_inner[k + 1], bot_outer[k + 1], bot_outer[k]])
    for k in range(n_arc):
        bm.faces.new([top_inner[k + 1], top_inner[k], top_outer[k], top_outer[k + 1]])
    for k in range(n_arc):
        bm.faces.new([bot_outer[k], bot_outer[k + 1], top_outer[k + 1], top_outer[k]])
    for k in range(n_arc):
        bm.faces.new([bot_inner[k + 1], bot_inner[k], top_inner[k], top_inner[k + 1]])
    bm.faces.new([bot_inner[0], bot_outer[0], top_outer[0], top_inner[0]])
    bm.faces.new([bot_outer[-1], bot_inner[-1], top_inner[-1], top_outer[-1]])

    mesh = bpy.data.meshes.new("tread")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("tread", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location.z = z_pos
    apply_tf(obj)
    return obj

def make_column_cylinder(radius, height):
    """Central column: a cylinder from z=0 to z=height."""

    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=height, location=(0, 0, 0))
    col = bpy.context.active_object
    col.location.z = height / 2
    apply_tf(col)
    add_mod(col, "SUBSURF", levels=1, render_levels=1, subdivision_type="SIMPLE")
    return col

def make_helical_rail(n_steps, step_h, radius, theta, rail_r, z_offset, extension_angle=0.15):
    """

    Helical handrail along outer edge.
    Build as a polyline then give it thickness via geo_radius_tube.
    """

    n_sub = 4  # subdivisions per step for smooth helix
    total_pts = n_steps * n_sub + 2  # +2 for extensions

    # Extend at start and end
    start_angle = -extension_angle
    end_angle = n_steps * theta + extension_angle
    total_angle = end_angle - start_angle

    bm = bmesh.new()
    bm_verts = []
    for i in range(total_pts):
        t = i / (total_pts - 1)
        a = start_angle + t * total_angle
        # z follows the step heights, clamped
        z_frac = (a / theta) if theta > 0 else 0
        z = z_frac * step_h + z_offset
        z = max(z_offset, min(z, n_steps * step_h + z_offset))

        x = radius * math.cos(a)
        y = radius * math.sin(a)
        bm_verts.append(bm.verts.new((x, y, z)))

    for i in range(len(bm_verts) - 1):
        bm.edges.new((bm_verts[i], bm_verts[i + 1]))

    mesh = bpy.data.meshes.new("helical_rail")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("helical_rail", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    geo_radius_tube(obj, rail_r, resolution=12)
    return obj

def make_post(x, y, z_base, post_height, post_width, is_circular):
    """Single vertical post."""

    if is_circular:
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=post_width,
                                            depth=post_height, location=(0, 0, 0))
    else:
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        bpy.context.active_object.scale = (post_width, post_width, post_height / 2)
    post = bpy.context.active_object
    post.location = (x, y, z_base + post_height / 2)
    apply_tf(post)
    return post

def make_horizontal_bar(x0, y0, z0, x1, y1, z1, bar_width):
    """Single horizontal bar between two post positions."""

    cx, cy, cz = (x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5
    seg_len = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)
    if seg_len < 1e-6:
        return None
    yaw = math.atan2(y1 - y0, x1 - x0)
    pitch = math.atan2(z1 - z0, math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2))

    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=bar_width, depth=seg_len, location=(0, 0, 0))
    bar = bpy.context.active_object
    bar.rotation_euler.y = math.pi / 2 - pitch
    bar.rotation_euler.z = yaw
    bar.location = (cx, cy, cz)
    apply_tf(bar)
    return bar

def build_spiral_stair():
    clear_scene()

    # ===== Room constants =====
    wall_height = np.random.uniform(2.8, 3.2)

    # ===== Size configuration (SpiralStaircaseFactory.build_size_config) =====
    # Retry until 0.9 < radius < 1.5
    for _attempt in range(200):
        full_angle = np.random.randint(1, 5) * np.pi / 2
        n = np.random.randint(13, 21)
        step_height = wall_height / n
        theta = full_angle / n  # angle per step
        step_length = step_height * log_uniform(1.0, 1.2)
        radius = step_length / theta
        if 0.9 < radius < 1.5:
            step_width = radius * np.random.uniform(0.9, 0.95)
            break
    else:
        # Fallback
        full_angle = np.pi
        n = 16
        step_height = wall_height / n
        theta = full_angle / n
        step_length = step_height * 1.1
        radius = step_length / theta
        step_width = radius * 0.92

    # Inner radius: the column sits at the inner edge
    # Spiral transform: u = x + radius - step_width
    # At x=0 (inner edge): u = radius - step_width (= column surface)
    # At x=step_width (outer edge): u = radius
    inner_r = radius - step_width  # inner radius of step annulus

    # ===== Column parameters (SpiralStaircaseFactory.__init__) =====
    column_radius = radius - step_width + np.random.uniform(0.05, 0.08)

    # ===== Tread parameters (from StraightStaircaseFactory.__init__) =====
    has_tread = np.random.uniform() < 0.75
    tread_height = np.random.uniform(0.01, 0.02)
    tread_overhang = np.random.uniform(0.005, 0.015)

    # ===== Handrail parameters (from StraightStaircaseFactory.__init__) =====
    # Spiral staircase uses "horizontal-post" or "vertical-post" handrail types
    handrail_type = weighted_choice([(2, "horizontal-post"), (2, "vertical-post")])

    is_handrail_circular = np.random.uniform() < 0.7
    handrail_width = log_uniform(0.02, 0.06)
    handrail_height = log_uniform(0.02, 0.06)
    handrail_offset = handrail_width * log_uniform(1.0, 2.0)

    # Spiral staircase: single outer handrail only
    # alpha = 1 - handrail_offset / step_width
    handrail_alpha = 1.0 - handrail_offset / step_width
    handrail_r = inner_r + handrail_alpha * step_width  # radial position of handrail

    # ===== Post parameters =====
    post_height = log_uniform(0.8, 1.2)
    post_k = max(1, int(np.ceil(step_width / step_length)))
    post_width = handrail_width * log_uniform(0.6, 0.8)
    post_minor_width = post_width * log_uniform(0.3, 0.5)
    is_post_circular = np.random.uniform() < 0.5

    has_vertical_post = handrail_type == "vertical-post"
    has_bars = handrail_type == "horizontal-post"
    bar_size = log_uniform(0.1, 0.2)
    n_bars = max(1, int(np.floor(post_height / bar_size * np.random.uniform(0.35, 0.75))))

    # ===== Mirror and rotation =====
    do_mirror = np.random.uniform() < 0.5
    rot_z = np.random.randint(4) * np.pi / 2

    total_height = n * step_height
    outer_r = radius  # outer edge of steps

    all_parts = []

    # ===== 1. Central column =====
    col_height = total_height + post_height
    col = make_column_cylinder(column_radius, col_height)
    all_parts.append(col)

    # ===== 2. Wedge-shaped steps =====
    for i in range(n):
        a0 = i * theta
        a1 = (i + 1) * theta
        z_base = i * step_height
        # Step extends from inner_r to outer_r
        step = make_curved_step(inner_r, outer_r, a0, a1, z_base, step_height)
        all_parts.append(step)

    # ===== 3. Treads (optional overhang boards) =====
    if has_tread:
        for i in range(n):
            a0 = i * theta
            a1 = (i + 1) * theta
            z_pos = (i + 1) * step_height  # on top of step
            tread = make_tread(inner_r, outer_r, a0, a1, z_pos, tread_height, tread_overhang)
            all_parts.append(tread)

    # ===== 4. Helical handrail on outer edge =====
    # z_offset derived so rail passes through post tops:
    # post at step i has top at step_h*(i+1)+post_height,
    # rail z at post angle (i+0.5)*theta = (i+0.5)*step_h + z_offset
    # => z_offset = step_h/2 + post_height
    rail = make_helical_rail(n, step_height, handrail_r, theta, handrail_width,
                             step_height / 2 + post_height)
    if rail:
        all_parts.append(rail)

    # ===== 5. Posts along outer handrail =====
    # Main posts: at every post_k steps along the offset line
    # Main (thick) posts: every post_k steps
    post_indices_main = []
    chunks = np.array_split(np.arange(n - 1),
                            max(1, int(np.ceil((n - 1) / post_k))))
    post_indices_main = [c[0] for c in chunks] + [n - 1, n]

    def get_post_pos(step_i):
        """Get handrail post position at step_i along the offset line.
        Posts sit at the midpoint of each step's angular span.
        The last post (step_i >= n) sits at the END of the staircase."""

        if step_i >= n:
            # Place at end of last step (angle = n*theta), not beyond
            y_lin = step_length * n
            z_lin = step_height * n
        else:
            y_lin = step_length * step_i + step_length / 2
            z_lin = step_height * (step_i + 1)
        # Spiral transform: u = x + radius - step_width, t = y / step_length * theta
        u = handrail_alpha * step_width + radius - step_width
        t = y_lin / step_length * theta
        px = u * math.cos(t)
        py = u * math.sin(t)
        pz = z_lin
        return px, py, pz

    # Place main posts
    existing_positions = []
    for idx in post_indices_main:
        if idx > n:
            continue
        px, py, pz = get_post_pos(idx)
        # Check minimum distance from existing posts
        too_close = False
        for ex, ey, ez in existing_positions:
            if math.sqrt((px - ex) ** 2 + (py - ey) ** 2) < handrail_width * 2:
                too_close = True
                break
        if too_close:
            continue
        post = make_post(px, py, pz, post_height, post_width, is_post_circular)
        all_parts.append(post)
        existing_positions.append((px, py, pz))

    # Vertical posts (thin, between main posts) if handrail_type == "vertical-post"
    if has_vertical_post:
        vert_indices = []
        for c in chunks:
            vert_indices.extend(c[1:].tolist())
        vert_indices.append(n)
        for idx in vert_indices:
            if idx > n:
                continue
            px, py, pz = get_post_pos(idx)
            too_close = False
            for ex, ey, ez in existing_positions:
                if math.sqrt((px - ex) ** 2 + (py - ey) ** 2) < handrail_width * 2:
                    too_close = True
                    break
            if too_close:
                continue
            post = make_post(px, py, pz, post_height, post_minor_width, is_post_circular)
            all_parts.append(post)
            existing_positions.append((px, py, pz))

    # ===== 6. Horizontal bars (if handrail_type == "horizontal-post") =====
    if has_bars:
        for ci, chunk in enumerate(chunks):
            if ci + 1 >= len(chunks) and len(chunk) == 0:
                continue
            # Bars span between main posts
            idx0 = chunk[0]
            if ci + 1 < len(chunks):
                idx1 = chunks[ci + 1][0]
            else:
                idx1 = n - 1
            px0, py0, pz0 = get_post_pos(idx0)
            px1, py1, pz1 = get_post_pos(idx1)
            for bi in range(n_bars):
                frac = (bi + 1) / (n_bars + 1)
                z_off = post_height * frac
                bar = make_horizontal_bar(
                    px0, py0, pz0 + z_off,
                    px1, py1, pz1 + z_off,
                    post_minor_width)
                if bar:
                    all_parts.append(bar)

    # ===== Join all parts =====
    result = join_objs(all_parts)
    if result is None:
        # Shouldn't happen, but just in case
        bpy.ops.mesh.primitive_cube_add(size=0.01)
        result = bpy.context.active_object

    # Mirror
    if do_mirror:
        result.scale.x = -1
        apply_tf(result)
        bpy.context.view_layer.objects.active = result
        result.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.mode_set(mode='OBJECT')

    # Rotation
    if rot_z != 0:
        result.rotation_euler.z = rot_z
        apply_tf(result)

    result.name = "SpiralStaircaseFactory"
    # [auto-append] ensure material bound
    if result is not None:
        if len(result.data.materials) == 0:
            result.data.materials.append(ELEM_MAT)
        elif result.data.materials[0] is None:
            result.data.materials[0] = ELEM_MAT
    return result

build_spiral_stair()
