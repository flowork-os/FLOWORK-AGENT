# [FL_INDEX: keywords="blender_factory, procedural_3d, UShapedStaircaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: UShapedStaircaseFactory | Category: factories_geo
# Prompt: A U-shaped staircase with an intermediate landing rendered as a 3D model, featuring dark navy/purple structural framing and semi-transparent brownish-tinted glass panel balustrades enclosing the perimeter.

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

ELEM_MAT = make_mat(SEED, "UShapedStaircaseFactory_Material")
np.random.seed(SEED)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def weighted_choice(items):
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

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
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
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

# ---------------------------------------------------------------------------
# Step geometry
# ---------------------------------------------------------------------------

def make_steps_leg1(m, step_w, step_l, step_h):
    """Leg 1 solid steps: x=[0, step_w], y ascending from 0 to m*step_l.
    Step i (i=0..m-1) fills from z=0 to z=(i+1)*step_h."""

    parts = []
    for i in range(m):
        h = (i + 1) * step_h
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        step = bpy.context.active_object
        step.scale = (step_w / 2, step_l / 2, h / 2)
        step.location = (step_w / 2, i * step_l + step_l / 2, h / 2)
        apply_tf(step)
        parts.append(step)
    return parts

def make_steps_leg2(m, n, step_w, step_l, step_h):
    """Leg 2 solid steps: x=[-step_w, 0], y from m*step_l (near landing) to 0 (far end).
    Step nearest landing (y≈(m-1)*step_l) has height (m+1)*step_h.
    Step farthest (y≈0) has height n*step_h."""

    parts = []
    for k in range(m):
        # k=0: nearest to landing, lowest of leg 2
        # k=m-1: farthest from landing, highest
        h = (m + k + 1) * step_h
        y_pos = (m - 1 - k) * step_l + step_l / 2
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        step = bpy.context.active_object
        step.scale = (step_w / 2, step_l / 2, h / 2)
        step.location = (-step_w / 2, y_pos, h / 2)
        apply_tf(step)
        parts.append(step)
    return parts

def make_landing_platform(m, step_w, step_l, step_h):
    """Landing platform connecting both legs at y=[m*step_l, m*step_l+step_w].
    Spans x=[-step_w, step_w], z=[0, m*step_h]."""

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    plat = bpy.context.active_object
    plat.scale = (step_w, step_w / 2, m * step_h / 2)
    plat.location = (0, m * step_l + step_w / 2, m * step_h / 2)
    apply_tf(plat)
    return plat

# ---------------------------------------------------------------------------
# Treads
# ---------------------------------------------------------------------------

def make_treads_leg1(m, step_w, step_l, step_h, tread_h, tread_l, tread_w):
    """Treads for leg 1: on top of each step."""

    parts = []
    for i in range(m):
        z = (i + 1) * step_h + tread_h / 2
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        tread = bpy.context.active_object
        tread.scale = (tread_w / 2, tread_l / 2, tread_h / 2)
        tread.location = (step_w / 2, i * step_l + step_l / 2, z)
        apply_tf(tread)
        parts.append(tread)
    return parts

def make_treads_leg2(m, n, step_w, step_l, step_h, tread_h, tread_l, tread_w):
    """Treads for leg 2: on top of each step."""

    parts = []
    for k in range(m):
        h = (m + k + 1) * step_h
        y_pos = (m - 1 - k) * step_l + step_l / 2
        z = h + tread_h / 2
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        tread = bpy.context.active_object
        tread.scale = (tread_w / 2, tread_l / 2, tread_h / 2)
        tread.location = (-step_w / 2, y_pos, z)
        apply_tf(tread)
        parts.append(tread)
    return parts

def make_landing_tread(m, step_w, step_l, step_h, tread_h):
    """Tread on the landing platform."""

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    tread = bpy.context.active_object
    tread.scale = (step_w, step_w / 2, tread_h / 2)
    tread.location = (0, m * step_l + step_w / 2, m * step_h + tread_h / 2)
    apply_tf(tread)
    return tread

# ---------------------------------------------------------------------------
# Side panels
# ---------------------------------------------------------------------------

def make_zigzag_side(heights, step_l, side_height, thickness):
    """Create a zig-zag side panel from step heights.
    heights[i] = top-of-step z for step i.
    Panel spans y=[0, len(heights)*step_l], created at x=0."""

    n_steps = len(heights)
    if n_steps == 0:
        return None
    bm = bmesh.new()
    # Upper edge: stair profile
    upper = []
    for i in range(n_steps):
        upper.append((i * step_l, heights[i]))
        upper.append(((i + 1) * step_l, heights[i]))
    # Lower edge: shifted down by side_height, reversed
    lower = []
    for i in range(n_steps - 1, -1, -1):
        lower.append(((i + 1) * step_l, heights[i] - side_height))
        lower.append((i * step_l, heights[i] - side_height))
    verts_2d = upper + lower
    bm_verts = [bm.verts.new((0, y, z)) for y, z in verts_2d]
    if len(bm_verts) >= 3:
        try:
            bm.faces.new(bm_verts)
        except ValueError:
            pass
    mesh = bpy.data.meshes.new("zigzag_side")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("zigzag_side", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    add_mod(obj, "SOLIDIFY", thickness=thickness, offset=0)
    return obj

def make_straight_side(heights, step_l, side_height, thickness):
    """Create a straight diagonal side panel from step heights.
    Diagonal from first step to last step."""

    n_steps = len(heights)
    if n_steps == 0:
        return None
    bm = bmesh.new()
    total_run = n_steps * step_l
    z_start = heights[0]
    z_end = heights[-1]
    bm_verts = [
        bm.verts.new((0, 0, z_start - side_height)),
        bm.verts.new((0, 0, z_start)),
        bm.verts.new((0, total_run, z_end)),
        bm.verts.new((0, total_run, z_end - side_height)),
    ]
    bm.faces.new(bm_verts)
    mesh = bpy.data.meshes.new("straight_side")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("straight_side", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    add_mod(obj, "SOLIDIFY", thickness=thickness, offset=0)
    return obj

def make_side_panel(heights, step_l, side_height, thickness, side_type):
    """Create a side panel (zig-zag or straight) at x=0."""

    if side_type == "zig-zag":
        return make_zigzag_side(heights, step_l, side_height, thickness)
    else:
        return make_straight_side(heights, step_l, side_height, thickness)

def make_all_sides(m, n, step_w, step_l, step_h, side_type, side_height, side_thickness, tread_h):
    """Create all side panels for the U-shaped staircase."""

    parts = []

    # Leg 1 heights: ascending
    leg1_heights = [(i + 1) * step_h for i in range(m)]
    # Leg 2 heights: in Y order (y=0 highest, y=(m-1)*step_l lowest of leg 2)
    leg2_heights = [(n - k) * step_h for k in range(m)]

    # ── Inner sides (at x=0, between the two legs) ──
    inner1 = make_side_panel(leg1_heights, step_l, side_height, side_thickness, side_type)
    if inner1:
        # Cut at landing height so it doesn't extend above
        parts.append(inner1)

    inner2 = make_side_panel(leg2_heights, step_l, side_height, side_thickness, side_type)
    if inner2:
        parts.append(inner2)

    # ── Outer sides ──
    # Leg 1 outer at x=step_w
    outer1 = make_side_panel(leg1_heights, step_l, side_height, side_thickness, side_type)
    if outer1:
        outer1.location[0] = step_w
        apply_tf(outer1)
        parts.append(outer1)

    # Leg 2 outer at x=-step_w
    outer2 = make_side_panel(leg2_heights, step_l, side_height, side_thickness, side_type)
    if outer2:
        outer2.location[0] = -step_w
        apply_tf(outer2)
        parts.append(outer2)

    # ── Outer U-turn connecting panel at landing ──
    bm = bmesh.new()
    mid_y = m * step_l + step_w
    z_plat = m * step_h
    pts = [
        (step_w, m * step_l, z_plat),
        (step_w, mid_y, z_plat),
        (0, mid_y, z_plat),
        (-step_w, mid_y, z_plat),
        (-step_w, m * step_l, z_plat),
    ]
    bm_verts = [bm.verts.new(p) for p in pts]
    for i in range(len(bm_verts) - 1):
        bm.edges.new((bm_verts[i], bm_verts[i + 1]))
    mesh = bpy.data.meshes.new("outer_landing")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("outer_landing", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_edges_move(
        TRANSFORM_OT_translate={"value": (0, 0, -side_height)})
    bpy.ops.object.mode_set(mode='OBJECT')
    add_mod(obj, "SOLIDIFY", thickness=side_thickness)
    parts.append(obj)

    return parts

def make_line_coords(n, m, step_l, step_h, step_w, alpha):
    """U-shaped path coordinates for rails/handrails.
    Returns (n+5) x 3 array following the path:
    Leg1 (+X side, ascending Y) -> Landing turn -> Leg2 (-X side, descending Y)."""

    x = np.concatenate([
        np.full(m + 2, alpha * step_w),
        [0],
        np.full(m + 2, -alpha * step_w),
    ])
    y = np.concatenate([
        np.arange(m + 1) * step_l,
        [m * step_l + alpha * step_w] * 3,
        np.arange(m, -1, -1) * step_l,
    ])
    z = (
        np.concatenate([
            np.arange(m + 1), [m] * 3, np.arange(m, n + 1)
        ]) * step_h
    )
    return np.stack([x, y, z], axis=-1)

def make_line_offset_coords(n, m, step_l, step_h, step_w, alpha):
    """Offset path for post/tread locations (shifted to tread centers)."""

    co = make_line_coords(n, m, step_l, step_h, step_w, alpha).copy()
    co[m:m + 4] = co[m + 1:m + 5].copy()
    x, y, z = co.T
    y[:m] += step_l / 2
    y[m + 3] += min(step_l / 2, alpha * step_w)
    y[m + 4:] -= step_l / 2
    z += step_h
    z[[m, m + 1, m + 2, m + 3, -1]] -= step_h
    return np.stack([x, y, z], axis=-1)

# ---------------------------------------------------------------------------
# Handrail
# ---------------------------------------------------------------------------

def extend_line_bmesh(obj, extension):
    """Extend a polyline at both ends horizontally."""

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    if len(bm.verts) < 2:
        bpy.ops.object.mode_set(mode='OBJECT')
        return
    v0, v1 = bm.verts[0], bm.verts[1]
    v_last, v_prev = bm.verts[-1], bm.verts[-2]
    n_0 = v0.co - v1.co
    n_0[2] = 0
    if n_0.length > 1e-6:
        v_new = bm.verts.new(v0.co + n_0 / n_0.length * extension)
        bm.edges.new((v_new, v0))
    n_1 = v_last.co - v_prev.co
    n_1[2] = 0
    if n_1.length > 1e-6:
        v_new = bm.verts.new(v_last.co + n_1 / n_1.length * extension)
        bm.edges.new((v_last, v_new))
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def make_handrail(coords, hw, hh, is_circular, post_height, extension):
    """Create handrail tube following a polyline path, elevated by post_height."""

    verts = [(c[0], c[1], c[2] + post_height) for c in coords]
    edges = [(i, i + 1) for i in range(len(verts) - 1)]
    mesh = bpy.data.meshes.new("handrail_path")
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    obj = bpy.data.objects.new("handrail_path", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    extend_line_bmesh(obj, extension)

    if is_circular:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target='CURVE')
        obj.data.bevel_depth = hw
        obj.data.bevel_resolution = 4
        obj.data.use_fill_caps = True
        bpy.ops.object.convert(target='MESH')
    else:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.extrude_edges_move(
            TRANSFORM_OT_translate={"value": (0, 0, -hh * 2)})
        bpy.ops.object.mode_set(mode='OBJECT')
        add_mod(obj, "SOLIDIFY", thickness=hw * 2, offset=0)
        obj.location[2] += hh
        apply_tf(obj)

    return obj

# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------

def compute_post_locs(n, m, step_l, step_h, step_w, alpha, post_k):
    """Main post locations along the U-shaped offset path."""

    cos = make_line_offset_coords(n, m, step_l, step_h, step_w, alpha)

    # Split first leg into chunks
    first_range = np.arange(m - 1) if m > 1 else np.array([], dtype=int)
    n_chunks1 = max(1, int(np.ceil(len(first_range) / post_k))) if len(first_range) > 0 else 0
    chunks1 = np.array_split(first_range, n_chunks1) if n_chunks1 > 0 else []

    # Split second leg
    second_end = min(n + 4, len(cos))
    second_range = np.arange(m + 3, second_end)
    n_chunks2 = max(1, int(np.ceil(len(second_range) / post_k))) if len(second_range) > 0 else 0
    chunks2 = np.array_split(second_range, n_chunks2) if n_chunks2 > 0 else []

    mid = [m - 1, m, m + 1, m + 2, m + 3]
    indices = (
        [int(c[0]) for c in chunks1 if len(c) > 0]
        + [min(i, len(cos) - 1) for i in mid]
        + [int(c[0]) for c in chunks2 if len(c) > 0]
    )
    # Add second-to-last post (n+3) but NOT the flat-top post (n+4)
    if n + 3 < len(cos):
        indices.append(n + 3)

    indices = [min(i, len(cos) - 1) for i in indices]
    # Remove duplicates preserving order
    seen = set()
    unique = []
    for i in indices:
        if i not in seen:
            seen.add(i)
            unique.append(i)
    return cos[unique]

def make_posts(locs_list, post_width, post_height, is_circular, handrail_width):
    """Create vertical posts at locations. Dedup nearby posts."""

    parts = []
    existing = np.zeros((0, 3))
    for locs in locs_list:
        for pt in locs:
            if len(existing) > 0:
                dists = np.linalg.norm(existing - pt[np.newaxis, :], axis=1)
                if np.min(dists) < handrail_width * 2:
                    continue
            existing = np.concatenate([existing, pt[np.newaxis, :]], 0)
            x, y, z = pt
            if is_circular:
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices=8, radius=post_width, depth=post_height,
                    location=(0, 0, 0))
            else:
                bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
                bpy.context.active_object.scale = (
                    post_width, post_width, post_height / 2)
            post = bpy.context.active_object
            post.location = (x, y, z + post_height / 2)
            apply_tf(post)
            parts.append(post)
    return parts

def make_horizontal_bars(locs_list, post_height, n_bars, bar_spacing, bar_thickness):
    """Horizontal bars between consecutive post locations."""

    parts = []
    for locs in locs_list:
        for i in range(len(locs) - 1):
            p0 = locs[i]
            p1 = locs[i + 1]
            dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
            bar_len = math.sqrt(dx**2 + dy**2 + dz**2)
            if bar_len < 1e-4:
                continue
            angle_y = math.atan2(dz, math.sqrt(dx**2 + dy**2))
            angle_z = math.atan2(dy, dx)
            for bi in range(n_bars):
                z_off = post_height - (bi + 1) * bar_spacing
                if z_off < 0:
                    continue
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices=8, radius=bar_thickness, depth=bar_len,
                    location=(0, 0, 0))
                bar = bpy.context.active_object
                bar.rotation_euler = (0, -(math.pi / 2 - angle_y), angle_z)
                bar.location = (
                    (p0[0] + p1[0]) / 2,
                    (p0[1] + p1[1]) / 2,
                    (p0[2] + p1[2]) / 2 + z_off,
                )
                apply_tf(bar)
                parts.append(bar)
    return parts

def make_glass_panels(locs_list, glass_height, glass_margin, thickness):
    """Glass panels between consecutive post locations."""

    parts = []
    for locs in locs_list:
        for i in range(len(locs) - 1):
            p0 = locs[i]
            p1 = locs[i + 1]
            verts = [
                (p0[0], p0[1], p0[2] + glass_margin),
                (p1[0], p1[1], p1[2] + glass_margin),
                (p1[0], p1[1], p1[2] + glass_height),
                (p0[0], p0[1], p0[2] + glass_height),
            ]
            faces = [(0, 1, 2, 3)]
            mesh = bpy.data.meshes.new("glass")
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            obj = bpy.data.objects.new("glass", mesh)
            bpy.context.scene.collection.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            add_mod(obj, "SOLIDIFY", thickness=thickness)
            parts.append(obj)
    return parts

# ---------------------------------------------------------------------------
# Rail (under-step support)
# ---------------------------------------------------------------------------

def make_rail(n, m, step_l, step_h, step_w, alpha, rail_width):
    """Create a circular rail following the U-path underneath the steps."""

    coords = make_line_coords(n, m, step_l, step_h, step_w, alpha)
    verts = [(c[0], c[1], c[2] - rail_width) for c in coords]
    edges = [(i, i + 1) for i in range(len(verts) - 1)]
    mesh = bpy.data.meshes.new("rail_path")
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    obj = bpy.data.objects.new("rail_path", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='CURVE')
    obj.data.bevel_depth = rail_width
    obj.data.bevel_resolution = 4
    obj.data.use_fill_caps = True
    bpy.ops.object.convert(target='MESH')
    return obj

# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_u_shaped_stair():
    clear_scene()

    # ── Size configuration ────────────────────────────────────────────────
    wall_height = np.random.uniform(2.8, 3.2)
    n = int(np.random.randint(13, 21) / 2) * 2
    m = n // 2
    step_h = wall_height / n
    step_w = log_uniform(0.9, 1.5)
    step_l = step_h * log_uniform(1.0, 1.2)

    # ── Support type ──────────────────────────────────────────────────────
    support_type = weighted_choice([
        (2, "single-rail"), (2, "double-rail"), (3, "side"), (3, "solid"), (3, "hole")])

    has_step = support_type in ("solid", "hole")
    has_rail = support_type in ("single-rail", "double-rail")
    has_sides = support_type in ("side", "solid", "hole")

    # ── Rail parameters ───────────────────────────────────────────────────
    rail_width = log_uniform(0.08, 0.2)
    rail_offset = step_w * np.random.uniform(0.15, 0.3)

    # ── Tread parameters ──────────────────────────────────────────────────
    has_tread = (not has_step) or (np.random.uniform() < 0.75)
    tread_h = np.random.uniform(0.01, 0.02) if has_step else np.random.uniform(0.06, 0.08)
    tread_l = step_l + np.random.uniform(0.01, 0.02)
    tread_w = step_w + np.random.uniform(0.01, 0.02) if np.random.uniform() < 0.8 else step_w

    # ── Side parameters ───────────────────────────────────────────────────
    side_type = np.random.choice(["zig-zag", "straight"])
    side_height = step_h * log_uniform(0.2, 0.8)
    side_thickness = np.random.uniform(0.03, 0.08)

    # ── Handrail type ─────────────────────────────────────────────────────
    handrail_type = weighted_choice([
        (2, "glass"), (2, "horizontal-post"), (2, "vertical-post")])

    is_handrail_circular = True
    handrail_width = log_uniform(0.02, 0.06)
    handrail_height = log_uniform(0.02, 0.06)
    handrail_offset = handrail_width * log_uniform(1, 2)
    handrail_extension = np.random.uniform(0.1, 0.2)
    handrail_alphas = [
        handrail_offset / step_w,
        1 - handrail_offset / step_w,
    ]

    # ── Post parameters ───────────────────────────────────────────────────
    post_height = log_uniform(0.8, 1.2)
    post_k = max(1, int(np.ceil(step_w / step_l)))
    post_width = handrail_width * log_uniform(0.6, 0.8)
    post_minor_width = post_width * log_uniform(0.3, 0.5)
    is_post_circular = np.random.uniform() < 0.5

    has_vertical_post = handrail_type == "vertical-post"
    has_bars = handrail_type == "horizontal-post"
    has_glasses = handrail_type == "glass"

    bar_size = log_uniform(0.1, 0.2)
    n_bars = max(1, int(np.floor(post_height / bar_size * np.random.uniform(0.35, 0.75))))
    glass_height = post_height - np.random.uniform(0, 0.05)
    glass_margin = step_h / 2 + np.random.uniform(0, 0.05)

    # ── Mirror and rotation ───────────────────────────────────────────────
    do_mirror = np.random.uniform() < 0.5
    rot_z = np.random.randint(4) * math.pi / 2

    all_parts = []

    # ======================================================================
    # STEPS (solid/hole support types)
    # ======================================================================
    if has_step:
        all_parts.extend(make_steps_leg1(m, step_w, step_l, step_h))
        all_parts.extend(make_steps_leg2(m, n, step_w, step_l, step_h))
        all_parts.append(make_landing_platform(m, step_w, step_l, step_h))

    # ======================================================================
    # RAILS (under-step support)
    # ======================================================================
    if has_rail:
        if support_type == "single-rail":
            rail_alphas = [0.5]
        else:
            rail_alphas = [rail_offset / step_w, 1 - rail_offset / step_w]
        for alpha in rail_alphas:
            rail_obj = make_rail(n, m, step_l, step_h, step_w, alpha, rail_width)
            all_parts.append(rail_obj)

    # ======================================================================
    # TREADS
    # ======================================================================
    if has_tread:
        all_parts.extend(make_treads_leg1(m, step_w, step_l, step_h, tread_h, tread_l, tread_w))
        all_parts.extend(make_treads_leg2(m, n, step_w, step_l, step_h, tread_h, tread_l, tread_w))
        all_parts.append(make_landing_tread(m, step_w, step_l, step_h, tread_h))

    # ======================================================================
    # SIDE PANELS
    # ======================================================================
    if has_sides:
        sides = make_all_sides(m, n, step_w, step_l, step_h, side_type,
                               side_height, side_thickness, tread_h)
        all_parts.extend(sides)

    # ======================================================================
    # HANDRAILS (follow U-path offset coordinates)
    # ======================================================================
    for alpha in handrail_alphas:
        coords = make_line_offset_coords(n, m, step_l, step_h, step_w, alpha)
        # Exclude the flat-top landing vertex at the end
        coords = coords[:-1]
        hr = make_handrail(
            coords, handrail_width, handrail_height, is_handrail_circular,
            post_height, handrail_extension)
        all_parts.append(hr)

    # ======================================================================
    # POSTS
    # ======================================================================
    post_locs_list = []
    for alpha in handrail_alphas:
        plocs = compute_post_locs(n, m, step_l, step_h, step_w, alpha, post_k)
        post_locs_list.append(plocs)

    posts = make_posts(
        post_locs_list, post_width, post_height, is_post_circular, handrail_width)
    all_parts.extend(posts)

    # ======================================================================
    # BARS / GLASS / VERTICAL POSTS
    # ======================================================================
    if has_bars:
        bars = make_horizontal_bars(
            post_locs_list, post_height, n_bars, bar_size, post_minor_width)
        all_parts.extend(bars)

    if has_glasses:
        glasses = make_glass_panels(
            post_locs_list, glass_height, glass_margin, post_minor_width)
        all_parts.extend(glasses)

    if has_vertical_post:
        for alpha in handrail_alphas:
            cos = make_line_offset_coords(n, m, step_l, step_h, step_w, alpha)
            cos = cos[:-1]  # exclude flat-top
            main_locs = compute_post_locs(n, m, step_l, step_h, step_w, alpha, post_k)
            for pt in cos:
                if len(main_locs) > 0:
                    dists = np.linalg.norm(main_locs - pt[np.newaxis, :], axis=1)
                    if np.min(dists) < handrail_width * 2:
                        continue
                x, y, z = pt
                if is_post_circular:
                    bpy.ops.mesh.primitive_cylinder_add(
                        vertices=8, radius=post_minor_width, depth=post_height,
                        location=(0, 0, 0))
                else:
                    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
                    bpy.context.active_object.scale = (
                        post_minor_width, post_minor_width, post_height / 2)
                vpost = bpy.context.active_object
                vpost.location = (x, y, z + post_height / 2)
                apply_tf(vpost)
                all_parts.append(vpost)

    # ======================================================================
    # JOIN, MIRROR, ROTATE
    # ======================================================================
    result = join_objs(all_parts)
    if result is None:
        bpy.ops.mesh.primitive_cube_add(size=0.01, location=(0, 0, 0))
        result = bpy.context.active_object

    if do_mirror:
        result.scale.x = -1
        apply_tf(result)
        bpy.context.view_layer.objects.active = result
        result.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.mode_set(mode='OBJECT')

    if rot_z != 0:
        result.rotation_euler.z = rot_z
        apply_tf(result)

    result.name = "UShapedStaircaseFactory"
    # [auto-append] ensure material bound
    if result is not None:
        if len(result.data.materials) == 0:
            result.data.materials.append(ELEM_MAT)
        elif result.data.materials[0] is None:
            result.data.materials[0] = ELEM_MAT
    return result

build_u_shaped_stair()
