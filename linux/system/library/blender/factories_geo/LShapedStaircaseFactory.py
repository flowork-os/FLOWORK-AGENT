# [FL_INDEX: keywords="blender_factory, procedural_3d, LShapedStaircaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LShapedStaircaseFactory | Category: factories_geo
# Prompt: An L-shaped staircase with a mid-level landing platform rendered as a 3D model, featuring dark navy blue structural framing with semi-transparent brown-tinted glass panel railings on all open sides.

import os
import math
import random
import colorsys

import bmesh
import bpy
import numpy as np

SEED = int(os.environ.get("SEED", "0"))
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

ELEM_MAT = make_mat(SEED, "LShapedStaircaseFactory_Material")
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

def new_line(subdivisions=1):
    """Create a line (polyline) object with subdivisions+1 vertices."""

    verts = [(i, 0.0, 0.0) for i in range(subdivisions + 1)]
    edges = [(i, i + 1) for i in range(subdivisions)]
    mesh = bpy.data.meshes.new("line")
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    obj = bpy.data.objects.new("line", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def write_co(obj, arr):
    obj.data.vertices.foreach_set("co", arr.reshape(-1))
    obj.data.update()

def triangulate_and_subsurf(obj):
    add_mod(obj, "TRIANGULATE", min_vertices=3)
    add_mod(obj, "SUBSURF", levels=1, render_levels=1, subdivision_type="SIMPLE")

def extend_line(obj, extension):
    """Extend a polyline at both ends by `extension` distance (horizontal only)."""

    if len(obj.data.vertices) <= 1:
        return
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    v0, v1 = bm.verts[0], bm.verts[1]
    v_last, v_prev = bm.verts[-1], bm.verts[-2]
    # Start extension
    n_0 = v0.co - v1.co
    n_0.z = 0
    if n_0.length > 1e-9:
        v_new = bm.verts.new(v0.co + n_0 / n_0.length * extension)
        bm.edges.new((v_new, v0))
    # End extension
    n_1 = v_last.co - v_prev.co
    n_1.z = 0
    if n_1.length > 1e-9:
        v_new2 = bm.verts.new(v_last.co + n_1 / n_1.length * extension)
        bm.edges.new((v_last, v_new2))
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def make_l_line(n, m, step_length, step_width, step_height, alpha):
    """

    Build the L-shaped handrail/post path.
    Returns a numpy array of shape (n+3, 3) with coordinates.

    The path has three segments:
    - First m+1 points going in +Y (x = alpha * step_width)
    - 1 corner point (turning point)
    - n-m+1 points going in -X
    """

    x = np.concatenate([
        np.full(m + 2, alpha * step_width),
        -np.arange(n - m + 1) * step_length,
    ])
    y = np.concatenate([
        np.arange(m + 1) * step_length,
        [m * step_length + alpha * step_width],
        np.full(n - m + 1, m * step_length + alpha * step_width),
    ])
    z = np.concatenate([
        np.arange(m + 1),
        [m],
        np.arange(m, n + 1),
    ]) * step_height

    return np.stack([x, y, z], -1)

def make_l_line_offset(n, m, step_length, step_width, step_height, alpha):
    """

    Build the offset L-shaped path for handrail and post placement
    (stepped offsets for mid-step positioning).
    """

    co = make_l_line(n, m, step_length, step_width, step_height, alpha).copy()
    # Collapse the corner: co[m:m+2] = co[m+1:m+3]
    co[m:m + 2] = co[m + 1:m + 3]
    x, y, z = co.T
    x[m + 1] += min(step_length / 2, alpha * step_width)
    x[m + 2:] -= step_length / 2
    y[:m] += step_length / 2
    z += step_height
    z[[m, m + 1, -1]] -= step_height
    return np.stack([x, y, z], -1)

def split_indices(start, end=None, post_k=1):
    """Split range into chunks of size post_k."""

    if end is None:
        arr = np.arange(start)
    else:
        arr = np.arange(start, end)
    n_chunks = int(np.ceil(len(arr) / post_k))
    if n_chunks == 0:
        return []
    return np.array_split(arr, n_chunks)

def make_l_post_locs(n, m, step_length, step_width, step_height, alpha, post_k):
    """Post locations along the L-shaped path."""

    cos = make_l_line_offset(n, m, step_length, step_width, step_height, alpha)
    chunks = split_indices(m - 1, post_k=post_k)
    chunks_ = split_indices(m + 1, n + 2, post_k=post_k)
    indices = (
        [c[0] for c in chunks]
        + [m - 1, m, m + 1]
        + [c[0] for c in chunks_]
        + [n + 1]
    )
    # Deduplicate while preserving order
    seen = set()
    unique_indices = []
    for idx in indices:
        if idx not in seen and idx < len(cos):
            seen.add(idx)
            unique_indices.append(idx)
    return cos[unique_indices]

def make_l_vertical_post_locs(n, m, step_length, step_width, step_height, alpha, post_k):
    """Vertical (minor) post locations along the L-shaped path."""

    cos = make_l_line_offset(n, m, step_length, step_width, step_height, alpha)
    chunks = split_indices(m - 1, post_k=post_k)
    chunks_ = split_indices(m + 1, n + 1, post_k=post_k)

    indices = sum([c[1:].tolist() for c in chunks], [])
    indices_ = sum([c[1:].tolist() for c in chunks_], [])

    mid_cos = []
    for mid_idx in [m - 1, m]:
        n_interp = post_k + 1 if mid_idx >= m else post_k + 2
        if mid_idx + 1 < len(cos):
            for r in np.linspace(0, 1, n_interp)[1:-1]:
                mid_cos.append(r * cos[mid_idx] + (1 - r) * cos[mid_idx + 1])

    result_parts = []
    valid_indices = [i for i in indices if i < len(cos)]
    if valid_indices:
        result_parts.append(cos[valid_indices])
    if mid_cos:
        result_parts.append(np.array(mid_cos))
    valid_indices_ = [i for i in indices_ if i < len(cos)]
    if valid_indices_:
        result_parts.append(cos[valid_indices_])

    if result_parts:
        return np.concatenate(result_parts, 0)
    return np.zeros((0, 3))

def make_straight_step_profile(n, step_h, step_l, support_type, hole_size):
    """

    Build the 2D staircase step profile.
    Returns a list of (y, z) coordinate tuples forming the step outline polygon.
    Coordinates are in "index space".
    """

    coords = [(0, 0)]
    for i in range(n):
        coords.extend([(i, i + 1), (i + 1, i + 1)])
    coords.extend([(n, 0), (0, 0)])
    return coords

def vertical_cut_and_solidify(coords_list, n, step_l, step_h, step_w):
    """

    Extrude 2D profile polygons into 3D objects with width step_w.
    Each polygon is in (y_index, z_index) space.
    """

    parts = []
    # Cut into per-step vertical slices
    for cut_start in range(n):
        cut_end = cut_start + 1
        # Clip polygon to this vertical strip
        clipped = clip_polygon_to_strip(coords_list, cut_start, cut_end)
        if not clipped:
            continue
        # Create mesh from 2D polygon
        bm = bmesh.new()
        bm_verts = [bm.verts.new((0, y * step_l, z * step_h)) for y, z in clipped]
        if len(bm_verts) >= 3:
            try:
                bm.faces.new(bm_verts)
            except ValueError:
                bm.free()
                continue
        else:
            bm.free()
            continue
        mesh = bpy.data.meshes.new("step_slice")
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new("step_slice", mesh)
        bpy.context.scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        add_mod(obj, "SOLIDIFY", thickness=step_w)
        triangulate_and_subsurf(obj)
        parts.append(obj)
    return parts

def clip_polygon_to_strip(coords, y_min, y_max):
    """

    Clip a polygon (list of (y, z) tuples) to the vertical strip [y_min, y_max].
    Uses Sutherland-Hodgman for two vertical clip lines.
    """

    def clip_edge(poly, boundary, keep_ge):
        """Clip polygon to y >= boundary (keep_ge=True) or y <= boundary (keep_ge=False)."""

        if not poly:
            return []
        result = []
        for i in range(len(poly)):
            curr = poly[i]
            prev = poly[i - 1]
            curr_in = (curr[0] >= boundary) if keep_ge else (curr[0] <= boundary)
            prev_in = (prev[0] >= boundary) if keep_ge else (prev[0] <= boundary)
            if curr_in:
                if not prev_in:
                    t = (boundary - prev[0]) / (curr[0] - prev[0]) if abs(curr[0] - prev[0]) > 1e-12 else 0
                    result.append((boundary, prev[1] + t * (curr[1] - prev[1])))
                result.append(curr)
            elif prev_in:
                t = (boundary - prev[0]) / (curr[0] - prev[0]) if abs(curr[0] - prev[0]) > 1e-12 else 0
                result.append((boundary, prev[1] + t * (curr[1] - prev[1])))
        return result

    # Remove last point if it duplicates the first (closed polygon)
    poly = list(coords)
    if poly and poly[0] == poly[-1]:
        poly = poly[:-1]
    poly = clip_edge(poly, y_min, keep_ge=True)
    poly = clip_edge(poly, y_max, keep_ge=False)
    return poly

def make_l_steps(n, m, step_h, step_l, step_w, support_type, hole_size):
    """

    Create step geometry for L-shaped staircase.
    First m steps go in +Y, then rotate remaining steps 90 degrees at corner.
    """
    # Build full step profile in index space
    coords = make_straight_step_profile(n, step_h, step_l, support_type, hole_size)

    # Create all n step slices using the straight factory method
    all_objs = vertical_cut_and_solidify(coords, n, step_l, step_h, step_w)

    # Rotate second leg steps (index >= m) by 90 degrees and translate to corner
    for obj in all_objs[m:]:
        obj.rotation_euler[2] = math.pi / 2
        obj.location = (m * step_l, m * step_l, 0)
        apply_tf(obj, loc=True)

    # Platform at corner
    # lowest = min Z of first rotated step
    if all_objs and len(all_objs) > m:
        lowest = min(v.co.z for v in all_objs[m].data.vertices)
    else:
        lowest = 0

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1, 1, 1))
    platform = bpy.context.active_object
    apply_tf(platform, loc=True)
    platform.location = (0, step_l * m, lowest)
    platform.scale = (step_w / 2, step_w / 2, (step_h * m - lowest) / 2)
    apply_tf(platform, loc=True)

    return all_objs + [platform]

def make_l_treads(n, m, step_h, step_l, step_w, tread_h, tread_l, tread_w):
    """Create tread boards for L-shaped staircase."""

    treads = []
    for i in range(n):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1, 1, 1))
        tread = bpy.context.active_object
        apply_tf(tread, loc=True)
        tread.scale = (tread_w / 2, tread_l / 2, tread_h / 2)
        tread.location = (
            -(tread_w - step_w) / 2,
            -(tread_l - step_l) + i * step_l,
            step_h + i * step_h,
        )
        apply_tf(tread, loc=True)
        triangulate_and_subsurf(tread)
        treads.append(tread)

    # For second leg, apply same transform as steps
    for obj in treads[m:]:
        obj.rotation_euler[2] = math.pi / 2
        obj.location = (m * step_l, m * step_l, 0)
        apply_tf(obj, loc=True)

    # Platform tread
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(1, 1, 1))
    platform_tread = bpy.context.active_object
    apply_tf(platform_tread, loc=True)
    platform_tread.location = (0, step_l * m, step_h * m)
    platform_tread.scale = (step_w / 2, step_w / 2, tread_h / 2)
    apply_tf(platform_tread, loc=True)

    return treads + [platform_tread]

def make_l_inner_sides(n, m, step_h, step_l, step_w, side_type, side_height,
                       side_thickness, tread_h):
    """Create inner side panels for L-shaped staircase."""

    objs = make_inner_sides_straight_base(n, step_h, step_l, step_w, side_type,
                                           side_height, side_thickness, tread_h)

    # Rotate second leg sides
    for obj in objs[m:]:
        obj.rotation_euler[2] = math.pi / 2
        obj.location = (m * step_l, m * step_l, 0)
        apply_tf(obj, loc=True)

    # Cut first leg sides at platform height
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 1))
    top_cutter = bpy.context.active_object
    apply_tf(top_cutter, loc=True)
    top_cutter.scale = (100, 100, 100)
    top_cutter.location[2] = m * step_h + tread_h
    apply_tf(top_cutter)

    for obj in objs[:m]:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        mod = obj.modifiers.new("bool_cut", "BOOLEAN")
        mod.object = top_cutter
        mod.operation = "DIFFERENCE"
        mod.solver = "FLOAT"
        bpy.ops.object.modifier_apply(modifier=mod.name)

    bpy.data.objects.remove(top_cutter, do_unlink=True)
    return objs

def make_inner_sides_straight_base(n, step_h, step_l, step_w, side_type,
                                    side_height, side_thickness, tread_h):
    """Build the straight staircase inner side panels (per-step slices)."""

    offset = -side_height / step_h
    if side_type == "zig-zag":
        # Build zig-zag line and buffer it
        coords = [(0, 0)]
        for i in range(n):
            coords.extend([(i, i + 1), (i + 1, i + 1)])
        # Buffer the zigzag path downward
        buffered = buffer_zigzag(coords, offset)
        if not buffered:
            # Fallback: use straight profile
            buffered = [
                (0, offset),
                (0, 1),
                (n, n + 1),
                (n, n + offset),
            ]
    else:
        buffered = [
            (0, offset),
            (0, 1),
            (n, n + 1),
            (n, n + offset),
        ]

    # Vertical cut into per-step slices
    objs = []
    for cut_start in range(n):
        cut_end = cut_start + 1
        clipped = clip_polygon_to_strip(buffered, cut_start, cut_end)
        if not clipped or len(clipped) < 3:
            continue
        bm = bmesh.new()
        bm_verts = [bm.verts.new((0, y * step_l, z * step_h)) for y, z in clipped]
        try:
            bm.faces.new(bm_verts)
        except ValueError:
            bm.free()
            continue
        mesh = bpy.data.meshes.new("inner_side")
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new("inner_side", mesh)
        bpy.context.scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        add_mod(obj, "SOLIDIFY", thickness=side_thickness, offset=0)

        # Cut top and bottom
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, -1))
        bottom_cutter = bpy.context.active_object
        apply_tf(bottom_cutter, loc=True)
        bottom_cutter.scale = (100, 100, 100)
        apply_tf(bottom_cutter)

        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 1))
        top_cutter = bpy.context.active_object
        apply_tf(top_cutter, loc=True)
        top_cutter.scale = (100, 100, 100)
        top_cutter.location[2] = n * step_h + tread_h

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        for cutter in [top_cutter, bottom_cutter]:
            mod = obj.modifiers.new("bool_cut", "BOOLEAN")
            mod.object = cutter
            mod.operation = "DIFFERENCE"
            mod.solver = "FLOAT"
            bpy.ops.object.modifier_apply(modifier=mod.name)

        bpy.data.objects.remove(top_cutter, do_unlink=True)
        bpy.data.objects.remove(bottom_cutter, do_unlink=True)

        objs.append(obj)

    return objs

def buffer_zigzag(coords, offset):
    """

    Buffer a zigzag stair line downward by `offset` (negative = down).
    Creates a polygon by duplicating the path shifted down.
    """
    # The zigzag path goes up; offset is negative to go below the zigzag
    upper = list(coords)
    lower = [(y, z + offset) for y, z in reversed(coords)]
    return upper + lower

def make_l_outer_sides(n, m, step_h, step_l, step_w, side_type, side_height,
                       side_thickness, tread_h):
    """Create outer side panels for L-shaped staircase."""

    objs = make_l_inner_sides(n, m, step_h, step_l, step_w, side_type, side_height,
                              side_thickness, tread_h)

    # Offset: first leg inner sides move by +step_width in X
    for obj in objs[:m]:
        obj.location[0] += step_w
        apply_tf(obj, loc=True)

    # Second leg inner sides move by +step_width in Y
    for obj in objs[m:]:
        obj.location[1] += step_w
        apply_tf(obj, loc=True)

    # Corner platform outer side: L-shaped panel connecting the two legs
    bm = bmesh.new()
    x_coords = [step_w, step_w, 0]
    y_coords = [m * step_l, m * step_l + step_w, m * step_l + step_w]
    z_coords = [m * step_h, m * step_h, m * step_h]

    v0 = bm.verts.new((x_coords[0], y_coords[0], z_coords[0]))
    v1 = bm.verts.new((x_coords[1], y_coords[1], z_coords[1]))
    v2 = bm.verts.new((x_coords[2], y_coords[2], z_coords[2]))
    bm.edges.new((v0, v1))
    bm.edges.new((v1, v2))

    mesh = bpy.data.meshes.new("corner_side")
    bm.to_mesh(mesh)
    bm.free()
    platform_side = bpy.data.objects.new("corner_side", mesh)
    bpy.context.scene.collection.objects.link(platform_side)
    bpy.context.view_layer.objects.active = platform_side
    platform_side.select_set(True)

    # Extrude edges downward
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={"value": (0, 0, -side_height)})
    bpy.ops.object.mode_set(mode='OBJECT')
    add_mod(platform_side, "SOLIDIFY", thickness=side_thickness)

    return objs + [platform_side]

def make_l_handrail_path(n, m, step_length, step_width, step_height, alpha):
    """

    Create a polyline object following the L-shaped handrail offset path.
    """

    co = make_l_line_offset(n, m, step_length, step_width, step_height, alpha)
    # Exclude the last flat-top landing vertex to avoid floating handrail
    co = co[:-1]
    n_verts = len(co)
    obj = new_line(n_verts - 1)
    write_co(obj, co)
    return obj

def make_handrail_mesh(obj, hw, hh, is_circular, post_height, extension):
    """Build a handrail tube/box around a polyline path."""

    extend_line(obj, extension)
    if is_circular:
        build_tube_from_polyline(obj, hw / 2, 32)
    else:
        # Extrude edges and solidify
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={"value": (0, 0, -hh * 2)})
        bpy.ops.object.mode_set(mode='OBJECT')
        add_mod(obj, "SOLIDIFY", thickness=hw * 2, offset=0,
                solidify_mode="NON_MANIFOLD")
        # Bevel
        bevel_w = hw * np.random.uniform(0.2, 0.5)
        bevel_seg = np.random.randint(4, 7)
        add_mod(obj, "BEVEL", width=bevel_w, segments=bevel_seg)
        obj.location[2] += hh

    obj.location[2] += post_height
    apply_tf(obj, loc=True)
    triangulate_and_subsurf(obj)

def build_tube_from_polyline(obj, radius, resolution=16):
    """Convert a polyline mesh to a tube using GeoNodes (MeshToCurve -> CurveToMesh)."""

    tree = bpy.data.node_groups.new("geo_tube", 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = tree.nodes.new('NodeGroupInput')
    inp.location = (-400, 0)
    out = tree.nodes.new('NodeGroupOutput')
    out.location = (400, 0)

    # MeshToCurve
    m2c = tree.nodes.new('GeometryNodeMeshToCurve')
    m2c.location = (-200, 0)
    tree.links.new(inp.outputs[0], m2c.inputs[0])

    # SetCurveRadius
    scr = tree.nodes.new('GeometryNodeSetCurveRadius')
    scr.location = (-50, 0)
    tree.links.new(m2c.outputs[0], scr.inputs[0])

    # Radius value
    rv = tree.nodes.new('ShaderNodeValue')
    rv.location = (-250, -100)
    rv.outputs[0].default_value = radius
    tree.links.new(rv.outputs[0], scr.inputs[2])

    # CurveCircle profile
    cc = tree.nodes.new('GeometryNodeCurvePrimitiveCircle')
    cc.location = (-50, -150)
    cc.inputs[0].default_value = resolution  # Resolution
    cc.inputs[4].default_value = radius  # Radius

    # CurveToMesh
    c2m = tree.nodes.new('GeometryNodeCurveToMesh')
    c2m.location = (150, 0)
    tree.links.new(scr.outputs[0], c2m.inputs['Curve'])
    tree.links.new(cc.outputs[0], c2m.inputs['Profile Curve'])

    # Try setting Scale input for Blender 5.0+
    if 'Scale' in c2m.inputs:
        # Connect radius to Scale
        tree.links.new(rv.outputs[0], c2m.inputs['Scale'])

    tree.links.new(c2m.outputs[0], out.inputs[0])

    mod = obj.modifiers.new("geo_tube", 'NODES')
    mod.node_group = tree
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    obj.location[2] = -radius
    apply_tf(obj, loc=True)

def make_l_posts(locs_list, widths_list, post_height, is_circular, handrail_width):
    """Create vertical posts at given locations."""

    parts = []
    existing = np.zeros((0, 3))
    for locs, width in zip(locs_list, widths_list):
        if len(locs) == 0:
            continue
        existing = np.concatenate([existing, locs[:1]], 0)
        cos_indices = [0]
        for i in range(1, len(locs)):
            if np.min(np.linalg.norm(existing - locs[i][np.newaxis, :], axis=1)) > handrail_width * 2:
                cos_indices.append(i)
                existing = np.concatenate([existing, locs[i:i + 1]], 0)

        selected_locs = locs[cos_indices]
        for loc in selected_locs:
            if is_circular:
                bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=width, depth=post_height)
            else:
                bpy.ops.mesh.primitive_cube_add(size=2.0)
                bpy.context.active_object.scale = (width, width, post_height / 2)

            post = bpy.context.active_object
            post.location = (loc[0], loc[1], loc[2] + post_height / 2)
            apply_tf(post)
            parts.append(post)
    return parts

def make_l_bars(locs_list, post_height, n_bars, bar_size, post_minor_width):
    """

    Horizontal bars between posts along the L-shaped path.
    """

    parts = []
    for locs in locs_list:
        for i in range(len(locs) - 1):
            p0, p1 = locs[i], locs[i + 1]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            bar_len = math.sqrt(dx ** 2 + dy ** 2)
            if bar_len < 1e-6:
                continue
            angle_z = math.atan2(dy, dx)

            for bi in range(n_bars):
                z_offset = post_height - (bi + 1) * bar_size
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices=8, radius=post_minor_width, depth=bar_len)
                bar = bpy.context.active_object
                bar.rotation_euler = (math.pi / 2, 0, angle_z)
                bar.location = (
                    (p0[0] + p1[0]) / 2,
                    (p0[1] + p1[1]) / 2,
                    (p0[2] + p1[2]) / 2 + z_offset,
                )
                apply_tf(bar)
                parts.append(bar)
    return parts

def make_l_glasses(locs_list, post_height, glass_height, glass_margin, post_minor_width):
    """

    Glass panels between posts along the L-shaped path.
    """

    parts = []
    for locs in locs_list:
        for i in range(len(locs) - 1):
            p0, p1 = locs[i], locs[i + 1]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            panel_len = math.sqrt(dx ** 2 + dy ** 2)
            if panel_len < 1e-6:
                continue
            angle_z = math.atan2(dy, dx)

            # Create line between the two post positions
            bm = bmesh.new()
            v0 = bm.verts.new((p0[0], p0[1], p0[2]))
            v1 = bm.verts.new((p1[0], p1[1], p1[2]))
            bm.edges.new((v0, v1))
            mesh = bpy.data.meshes.new("glass_line")
            bm.to_mesh(mesh)
            bm.free()
            obj = bpy.data.objects.new("glass_panel", mesh)
            bpy.context.scene.collection.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.extrude_edges_move(
                TRANSFORM_OT_translate={"value": (0, 0, glass_height - glass_margin)})
            bpy.ops.object.mode_set(mode='OBJECT')
            add_mod(obj, "SOLIDIFY", thickness=post_minor_width)
            obj.location[2] += glass_margin
            apply_tf(obj, loc=True)
            parts.append(obj)
    return parts

def make_l_rails(n, m, step_l, step_h, step_w, rail_offset, rail_width, rail_height,
                 is_rail_circular):
    """

    Support rails under the L-shaped staircase.
    For L-shaped: is_rail_circular is always True.
    """

    parts = []
    alphas = [rail_offset / step_w, 1 - rail_offset / step_w]
    for alpha in alphas:
        co = make_l_line(n, m, step_l, step_w, step_h, alpha)
        obj = new_line(len(co) - 1)
        write_co(obj, co)
        if is_rail_circular:
            build_tube_from_polyline(obj, rail_width / 2, 16)
        else:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.extrude_edges_move(
                TRANSFORM_OT_translate={"value": (0, 0, -rail_height * 2)})
            bpy.ops.object.mode_set(mode='OBJECT')
            add_mod(obj, "SOLIDIFY", thickness=rail_width, offset=0)
        triangulate_and_subsurf(obj)
        parts.append(obj)
    return parts

# ──────────────────────────────────────────────────────────────────────────────
# Main build function
# ──────────────────────────────────────────────────────────────────────────────

def build_l_stair():
    clear_scene()

    # ── Size configuration ──────────────────────────────────────────────────
    wall_height = np.random.uniform(2.8, 3.2)
    n = np.random.randint(13, 21)
    step_h = wall_height / n
    step_w = np.random.uniform(0.8, 1.6)
    step_l = step_h * log_uniform(0.8, 1.2)

    # ── L-shaped specific: split point ─────────────────────────────────────
    m = int(n * np.random.uniform(0.4, 0.6))

    # ── Support type ───────────────────────────────────────────────────────
    support_type = weighted_choice([
        (2, "single-rail"), (2, "double-rail"), (3, "side"), (3, "solid"), (3, "hole")])

    has_step = support_type in ["solid", "hole"]
    hole_size = log_uniform(0.6, 1.0)

    has_rail = support_type in ["single-rail", "double-rail"]
    is_rail_circular = True  # L-shaped always uses circular rails
    rail_width = log_uniform(0.08, 0.2)
    rail_height = log_uniform(0.08, 0.12)
    rail_offset = step_w * np.random.uniform(0.15, 0.3)

    has_tread = (not has_step) or (np.random.uniform() < 0.75)
    tread_h = np.random.uniform(0.01, 0.02) if has_step else np.random.uniform(0.06, 0.08)
    tread_l = step_l + np.random.uniform(0.01, 0.02)
    tread_w = step_w + np.random.uniform(0.01, 0.02) if np.random.uniform() < 0.8 else step_w

    has_sides = support_type in ["side", "solid", "hole"]
    side_type = np.random.choice(["zig-zag", "straight"])
    side_height = step_h * log_uniform(0.2, 0.8)
    side_thickness = np.random.uniform(0.03, 0.08)

    # ── Handrail parameters ────────────────────────────────────────────────
    handrail_type = weighted_choice([
        (2, "glass"), (2, "horizontal-post"), (2, "vertical-post")])

    is_handrail_circular = np.random.uniform() < 0.7
    handrail_width = log_uniform(0.02, 0.06)
    handrail_height = log_uniform(0.02, 0.06)
    handrail_offset = handrail_width * log_uniform(1, 2)
    handrail_extension = np.random.uniform(0.1, 0.2)
    handrail_alphas = [
        handrail_offset / step_w,
        1 - handrail_offset / step_w,
    ]

    # ── Post parameters ────────────────────────────────────────────────────
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

    # ── Mirror and rotation ────────────────────────────────────────────────
    do_mirror = np.random.uniform() < 0.5
    rot_z = np.random.randint(4) * math.pi / 2

    all_parts = []

    # ── Steps (solid/hole support types) ───────────────────────────────────
    if has_step:
        steps = make_l_steps(n, m, step_h, step_l, step_w, support_type, hole_size)
        all_parts.extend(steps)

    # ── Rails (single-rail / double-rail) ──────────────────────────────────
    if has_rail:
        if support_type == "single-rail":
            co = make_l_line(n, m, step_l, step_w, step_h, 0.5)
            obj = new_line(len(co) - 1)
            write_co(obj, co)
            build_tube_from_polyline(obj, rail_width / 2, 16)
            triangulate_and_subsurf(obj)
            all_parts.append(obj)
        else:
            rails = make_l_rails(n, m, step_l, step_h, step_w, rail_offset,
                                 rail_width, rail_height, is_rail_circular)
            all_parts.extend(rails)

    # ── Treads ─────────────────────────────────────────────────────────────
    if has_tread:
        treads = make_l_treads(n, m, step_h, step_l, step_w, tread_h, tread_l, tread_w)
        all_parts.extend(treads)

    # ── Side panels ────────────────────────────────────────────────────────
    if has_sides:
        inner_sides = make_l_inner_sides(n, m, step_h, step_l, step_w, side_type,
                                         side_height, side_thickness, tread_h)
        all_parts.extend(inner_sides)

        outer_sides = make_l_outer_sides(n, m, step_h, step_l, step_w, side_type,
                                         side_height, side_thickness, tread_h)
        all_parts.extend(outer_sides)

    # ── Handrails ──────────────────────────────────────────────────────────
    for alpha in handrail_alphas:
        obj = make_l_handrail_path(n, m, step_l, step_w, step_h, alpha)
        make_handrail_mesh(obj, handrail_width, handrail_height, is_handrail_circular,
                          post_height, handrail_extension)
        all_parts.append(obj)

    # ── Posts ──────────────────────────────────────────────────────────────
    post_locs = [make_l_post_locs(n, m, step_l, step_w, step_h, alpha, post_k)
                 for alpha in handrail_alphas]

    if has_vertical_post:
        vp_locs = [make_l_vertical_post_locs(n, m, step_l, step_w, step_h, alpha, post_k)
                   for alpha in handrail_alphas]
        posts = make_l_posts(
            post_locs + vp_locs,
            [post_width] * len(post_locs) + [post_minor_width] * len(vp_locs),
            post_height, is_post_circular, handrail_width)
    else:
        posts = make_l_posts(
            post_locs,
            [post_width] * len(post_locs),
            post_height, is_post_circular, handrail_width)
    all_parts.extend(posts)

    # ── Bars ───────────────────────────────────────────────────────────────
    if has_bars:
        bars = make_l_bars(post_locs, post_height, n_bars, bar_size, post_minor_width)
        all_parts.extend(bars)

    # ── Glass panels ───────────────────────────────────────────────────────
    if has_glasses:
        glasses = make_l_glasses(post_locs, post_height, glass_height,
                                 glass_margin, post_minor_width)
        all_parts.extend(glasses)

    # ── Join all parts ─────────────────────────────────────────────────────
    all_parts = [p for p in all_parts if p is not None]
    result = join_objs(all_parts)

    if result is None:
        # Fallback: create a simple placeholder
        bpy.ops.mesh.primitive_cube_add(size=2.0)
        result = bpy.context.active_object

    # ── Mirror ─────────────────────────────────────────────────────────────
    if do_mirror:
        result.scale.x = -1
        apply_tf(result)
        bpy.context.view_layer.objects.active = result
        result.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.mode_set(mode='OBJECT')

    # ── Rotation ───────────────────────────────────────────────────────────
    if rot_z != 0:
        result.rotation_euler.z = rot_z
        apply_tf(result)

    result.name = "LShapedStaircaseFactory"
    # [auto-append] ensure material bound
    if result is not None:
        if len(result.data.materials) == 0:
            result.data.materials.append(ELEM_MAT)
        elif result.data.materials[0] is None:
            result.data.materials[0] = ELEM_MAT
    return result

build_l_stair()
