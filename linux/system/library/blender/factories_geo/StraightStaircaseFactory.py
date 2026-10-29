# [FL_INDEX: keywords="blender_factory, procedural_3d, StraightStaircaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: StraightStaircaseFactory | Category: factories_geo
# Prompt: A straight single-flight staircase rendered as a 3D model, featuring a compact dark maroon/purple structural frame with semi-transparent brownish-grey glass panel railings on both sides.

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


def make_glass_mat(seed, name="GlassMaterial"):
    """Glass surface matching the staircase glass registry path."""

    _seed_mat(seed + 701)
    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new
    glass = nt.nodes.new("ShaderNodeBsdfGlass")
    if "Color" in glass.inputs:
        glass.inputs["Color"].default_value = _hsv2rgba(
            np.random.uniform(0.50, 0.62),
            np.random.uniform(0.05, 0.18),
            np.random.uniform(0.75, 1.0),
        )
    if "Roughness" in glass.inputs:
        glass.inputs["Roughness"].default_value = float(np.random.uniform(0.0, 0.04))
    if "IOR" in glass.inputs:
        glass.inputs["IOR"].default_value = 1.45
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(glass.outputs[0], out.inputs["Surface"])
    mat.blend_method = "BLEND"
    mat.use_screen_refraction = True
    return mat


ELEM_MAT = make_mat(SEED, "StraightStaircaseFactory_Material")
STEP_MAT = make_mat(SEED + 11, "StraightStaircaseFactory_Step")
RAIL_MAT = make_mat(SEED + 17, "StraightStaircaseFactory_Rail")
TREAD_MAT = make_mat(SEED + 23, "StraightStaircaseFactory_Tread")
SIDE_MAT = make_mat(SEED + 29, "StraightStaircaseFactory_Side")
HANDRAIL_MAT = make_mat(SEED + 31, "StraightStaircaseFactory_Handrail")
POST_MAT = make_mat(SEED + 37, "StraightStaircaseFactory_Post")
GLASS_MAT = make_glass_mat(SEED, "StraightStaircaseFactory_Glass")
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


def assign_material(obj, mat):
    if obj is not None:
        obj.data.materials.append(mat)
    return obj


def assign_materials(objs, mat):
    for obj in objs:
        assign_material(obj, mat)
    return objs

def triangulate(obj):
    add_mod(obj, "TRIANGULATE", min_vertices=3)
    add_mod(obj, "SUBSURF", levels=1, render_levels=1, subdivision_type="SIMPLE")
    return obj

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

def get_line_offset_positions(n, step_l, step_h, alpha, step_w):
    """Return (n+1) positions for handrail/post placement."""

    x = alpha * step_w
    positions = []
    for i in range(n + 1):
        y = i * step_l + step_l / 2
        z = (i + 1) * step_h
        if i == n:
            z = n * step_h  # flat top
        positions.append(np.array([x, y, z]))
    return positions

def get_post_indices(n, post_k):
    """Return main post indices: split into chunks of post_k, take first of each chunk + [n-1, n]."""

    if n <= 1:
        return [0, n]
    chunks = np.array_split(np.arange(n - 1), max(1, int(np.ceil((n - 1) / post_k))))
    indices = sorted(set([c[0] for c in chunks] + [n - 1, n]))
    return indices

def get_vertical_post_indices(n, post_k):
    """Return minor vertical post indices (all tread positions EXCEPT main posts + vertex n)."""

    if n <= 1:
        return []
    main_indices = set(get_post_indices(n, post_k))
    chunks = np.array_split(np.arange(n - 1), max(1, int(np.ceil((n - 1) / post_k))))
    indices = []
    for c in chunks:
        indices.extend(c[1:].tolist())
    indices.append(n)
    # Remove indices that are in main posts
    indices = [i for i in indices if i not in main_indices]
    return sorted(set(indices))

def make_steps_solid(n, step_w, step_l, step_h, hole_size=0.0, has_hole=False):
    """Create solid stair-step profile polygon, solidified by step_w."""

    bm = bmesh.new()
    coords = [(0, 0)]
    for i in range(n):
        coords.append((i * step_l, (i + 1) * step_h))
        coords.append(((i + 1) * step_l, (i + 1) * step_h))
    coords.append((n * step_l, 0))

    if has_hole:
        # Triangular hole cut
        cut_y = (1 - hole_size) * n * step_l
        cut_z = hole_size * n * step_h
        new_coords = []
        for k, (y, z) in enumerate(coords):
            if k == len(coords) - 1:
                new_coords.append((n * step_l, cut_z))
                new_coords.append((cut_y, 0))
            else:
                new_coords.append((y, z))
        coords = new_coords

    bm_verts = [bm.verts.new((0, y, z)) for y, z in coords]
    bm.faces.new(bm_verts)
    mesh = bpy.data.meshes.new("steps_solid")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("steps_solid", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    add_mod(obj, "SOLIDIFY", thickness=step_w)
    triangulate(obj)
    return obj

def make_rail(n, step_l, step_h, alpha, step_w, rail_w, rail_h, is_circular):
    """Support rail along stair slope."""

    bm = bmesh.new()
    bm_verts = []
    x = alpha * step_w
    for i in range(n + 1):
        bm_verts.append(bm.verts.new((x, i * step_l, i * step_h)))
    for i in range(len(bm_verts) - 1):
        bm.edges.new((bm_verts[i], bm_verts[i + 1]))
    mesh = bpy.data.meshes.new("rail_line")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("rail_line", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    if is_circular:
        geo_radius_tube(obj, rail_w, resolution=16)
        obj.location.z = -rail_w
        apply_tf(obj, loc=True)
    else:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_edges_move(
            TRANSFORM_OT_translate={"value": (0, 0, -rail_h * 2)})
        bpy.ops.object.mode_set(mode='OBJECT')
        add_mod(obj, "SOLIDIFY", thickness=rail_w, offset=0)

    triangulate(obj)
    return obj

def make_treads(n, step_w, step_l, step_h, tread_h, tread_l, tread_w):
    """Tread boards at each step position."""

    parts = []
    for i in range(n):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        tread = bpy.context.active_object
        tread.location = (1, 1, 1)
        apply_tf(tread, loc=True)
        tread.scale = (tread_w / 2, tread_l / 2, tread_h / 2)
        tread.location = (
            -(tread_w - step_w) / 2,
            -(tread_l - step_l) + step_l * i,
            step_h + step_h * i,
        )
        apply_tf(tread)
        triangulate(tread)
        parts.append(tread)
    return parts

def make_side_panel(n, step_l, step_h, side_x, side_type, thickness, side_height, tread_h):
    """Side panel at x=side_x."""

    bm = bmesh.new()

    if side_type == "zig-zag":
        # Zig-zag: step outline buffered inward
        offset = -side_height / step_h
        coords = [(0, 0)]
        for i in range(n):
            coords.append((i * step_l, (i + 1) * step_h))
            coords.append(((i + 1) * step_l, (i + 1) * step_h))
        # Lower boundary: offset below each step
        lower = [(y, z + offset * step_h) for y, z in coords]
        all_coords = coords + list(reversed(lower))
    else:
        # Straight diagonal
        offset = -side_height / step_h
        total_run = n * step_l
        total_rise = n * step_h
        all_coords = [
            (0, offset * step_h),
            (0, step_h),
            (total_run, total_rise),
            (total_run, total_rise + offset * step_h),
        ]

    bm_verts = [bm.verts.new((side_x, y, z)) for y, z in all_coords]
    try:
        bm.faces.new(bm_verts)
    except ValueError:
        pass

    mesh = bpy.data.meshes.new("side_panel")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("side_panel", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    add_mod(obj, "SOLIDIFY", thickness=thickness, offset=0)
    return obj

def make_handrail(n, step_l, step_h, alpha, step_w, hw, hh, is_circular,
                  post_height, extension):
    """Handrail as polyline at step positions + post_height, with horizontal extensions."""

    x = alpha * step_w

    # Build line at step midpoints
    points = []
    for i in range(n + 1):
        y_val = i * step_l + step_l / 2
        z_val = (i + 1) * step_h
        if i == n:
            z_val = n * step_h  # flat top
        points.append((x, y_val, z_val + post_height))

    if len(points) >= 2:
        points.insert(0, (x, points[0][1] - extension, points[0][2]))
        points.append((x, points[-1][1] + extension, points[-1][2]))

    bm = bmesh.new()
    bm_verts = [bm.verts.new(p) for p in points]
    for i in range(len(bm_verts) - 1):
        bm.edges.new((bm_verts[i], bm_verts[i + 1]))
    mesh = bpy.data.meshes.new("handrail_line")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("handrail_line", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    if is_circular:
        geo_radius_tube(obj, hw, resolution=32)
    else:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_edges_move(
            TRANSFORM_OT_translate={"value": (0, 0, -hh * 2)})
        bpy.ops.object.mode_set(mode='OBJECT')
        add_mod(obj, "SOLIDIFY", thickness=hw * 2, offset=0)
        bevel_w = hw * np.random.uniform(0.2, 0.5)
        bevel_seg = np.random.randint(4, 7)
        add_mod(obj, "BEVEL", width=bevel_w, segments=bevel_seg)
        obj.location.z += hh
        apply_tf(obj, loc=True)

    triangulate(obj)
    return obj

def _make_posts_at(n, step_l, step_h, alpha, step_w, post_width, post_height,
                   is_circular, indices, cyl_verts=12):
    """Create vertical posts at given index positions along the stair path."""

    parts = []
    positions = get_line_offset_positions(n, step_l, step_h, alpha, step_w)

    for idx in indices:
        pos = positions[idx]
        x, y, z_base = float(pos[0]), float(pos[1]), float(pos[2])

        if is_circular:
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=cyl_verts, radius=post_width, depth=post_height,
                location=(0, 0, 0))
        else:
            bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
            bpy.context.active_object.scale = (post_width, post_width,
                                                post_height / 2)
        post = bpy.context.active_object
        post.location = (x, y, z_base + post_height / 2)
        apply_tf(post)
        parts.append(post)

    return parts

def make_posts(n, step_l, step_h, alpha, step_w, post_width, post_height,
               is_circular, post_k):
    return _make_posts_at(n, step_l, step_h, alpha, step_w, post_width,
                          post_height, is_circular, get_post_indices(n, post_k), 12)

def make_vertical_posts(n, step_l, step_h, alpha, step_w, post_width, post_height,
                        is_circular, post_k):
    return _make_posts_at(n, step_l, step_h, alpha, step_w, post_width,
                          post_height, is_circular, get_vertical_post_indices(n, post_k), 8)

def make_bars(n, step_l, step_h, alpha, step_w, post_height, n_bars,
              bar_size, bar_width, post_k):
    """Horizontal bars between main posts."""

    parts = []
    positions = get_line_offset_positions(n, step_l, step_h, alpha, step_w)
    indices = get_post_indices(n, post_k)

    for pi in range(len(indices) - 1):
        p0 = positions[indices[pi]]
        p1 = positions[indices[pi + 1]]

        for bi in range(n_bars):
            z_offset = post_height - (bi + 1) * bar_size

            # Create line with 16 segments
            n_seg = 16
            bm = bmesh.new()
            bm_verts = []
            for si in range(n_seg + 1):
                t_val = si / n_seg
                pos = p0 * (1 - t_val) + p1 * t_val
                bm_verts.append(bm.verts.new(
                    (float(pos[0]), float(pos[1]), float(pos[2]) + z_offset)))
            for si in range(n_seg):
                bm.edges.new((bm_verts[si], bm_verts[si + 1]))

            mesh = bpy.data.meshes.new("bar_line")
            bm.to_mesh(mesh)
            bm.free()
            obj = bpy.data.objects.new("bar_line", mesh)
            bpy.context.scene.collection.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            geo_radius_tube(obj, bar_width, resolution=6)
            parts.append(obj)

    return parts

def make_glasses(n, step_l, step_h, alpha, step_w, glass_height, glass_margin,
                 post_minor_width, post_k):
    """Glass panels between main posts."""

    parts = []
    positions = get_line_offset_positions(n, step_l, step_h, alpha, step_w)
    indices = get_post_indices(n, post_k)

    for pi in range(len(indices) - 1):
        p0 = positions[indices[pi]]
        p1 = positions[indices[pi + 1]]

        # Create line from p0 to p1
        bm = bmesh.new()
        v0 = bm.verts.new((float(p0[0]), float(p0[1]), float(p0[2])))
        v1 = bm.verts.new((float(p1[0]), float(p1[1]), float(p1[2])))
        bm.edges.new((v0, v1))
        mesh = bpy.data.meshes.new("glass_line")
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new("glass_line", mesh)
        bpy.context.scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_edges_move(
            TRANSFORM_OT_translate={"value": (0, 0, glass_height - glass_margin)})
        bpy.ops.object.mode_set(mode='OBJECT')
        add_mod(obj, "SOLIDIFY", thickness=post_minor_width)
        obj.location.z += glass_margin
        apply_tf(obj, loc=True)
        parts.append(obj)

    return parts

# ===========================================================================
# Main builder
# ===========================================================================
def build_straight_stair():
    clear_scene()

    # ---- Size configuration ------------------------------------------------
    wall_height = np.random.uniform(2.8, 3.2)
    n = np.random.randint(13, 21)
    step_h = wall_height / n
    step_w = np.random.uniform(0.8, 1.6)
    step_l = step_h * log_uniform(0.8, 1.2)

    # ---- Support type ------------------------------------------------------
    support_type = weighted_choice([
        (2, "single-rail"), (2, "double-rail"),
        (3, "side"), (3, "solid"), (3, "hole")])

    has_step = support_type in ["solid", "hole"]
    has_rail = support_type in ["single-rail", "double-rail"]
    has_sides = support_type in ["side", "solid", "hole"]

    hole_size = log_uniform(0.6, 1.0)

    # ---- Rail parameters -------------------------------------------------
    rail_offset = step_w * np.random.uniform(0.15, 0.3)
    is_rail_circular = np.random.uniform() < 0.5
    rail_width = log_uniform(0.08, 0.2)
    rail_height = log_uniform(0.08, 0.12)

    # ---- Tread parameters ------------------------------------------------
    has_tread = (not has_step) or (np.random.uniform() < 0.75)
    tread_h = np.random.uniform(0.01, 0.02) if has_step else np.random.uniform(0.06, 0.08)
    tread_l = step_l + np.random.uniform(0.01, 0.02)
    tread_w = step_w + np.random.uniform(0.01, 0.02) if np.random.uniform() < 0.8 else step_w

    # ---- Side parameters -------------------------------------------------
    side_type = np.random.choice(["zig-zag", "straight"])
    side_height = step_h * log_uniform(0.2, 0.8)
    side_thickness = np.random.uniform(0.03, 0.08)

    # ---- Handrail type ---------------------------------------------------
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

    # ---- Post parameters -------------------------------------------------
    post_height = log_uniform(0.8, 1.2)
    post_k = max(1, int(np.ceil(step_w / step_l)))
    post_width = handrail_width * log_uniform(0.6, 0.8)
    post_minor_width = post_width * log_uniform(0.3, 0.5)
    is_post_circular = np.random.uniform() < 0.5

    has_vertical_post = handrail_type == "vertical-post"
    has_bars = handrail_type == "horizontal-post"
    has_glasses = handrail_type == "glass"

    # Bar parameters
    bar_size = log_uniform(0.1, 0.2)
    n_bars = max(1, int(np.floor(post_height / bar_size * np.random.uniform(0.35, 0.75))))

    # Glass parameters
    glass_height = post_height - np.random.uniform(0, 0.05)
    glass_margin = step_h / 2 + np.random.uniform(0, 0.05)

    # Mirror and rotation
    do_mirror = np.random.uniform() < 0.5
    rot_z = np.random.randint(4) * math.pi / 2

    # ==== Build all parts ==================================================
    all_parts = []

    # 1. Steps (solid/hole profile)
    if has_step:
        steps = make_steps_solid(n, step_w, step_l, step_h,
                                 hole_size=hole_size,
                                 has_hole=(support_type == "hole"))
        assign_material(steps, STEP_MAT)
        all_parts.append(steps)

    # 2. Support rails
    if has_rail:
        if support_type == "single-rail":
            rail_alphas = [0.5]
        else:
            rail_alphas = [rail_offset / step_w, 1 - rail_offset / step_w]
        for alpha in rail_alphas:
            rail = make_rail(n, step_l, step_h, alpha, step_w,
                             rail_width, rail_height, is_rail_circular)
            assign_material(rail, RAIL_MAT)
            all_parts.append(rail)

    # 3. Treads
    if has_tread:
        treads = make_treads(n, step_w, step_l, step_h, tread_h, tread_l, tread_w)
        assign_materials(treads, TREAD_MAT)
        all_parts.extend(treads)

    # 4. Side panels (at x=0 and x=step_w)
    if has_sides:
        for side_x in [0, step_w]:
            panel = make_side_panel(n, step_l, step_h, side_x, side_type,
                                   side_thickness, side_height, tread_h)
            assign_material(panel, SIDE_MAT)
            all_parts.append(panel)

    # 5. Handrails (always on both sides)
    for alpha in handrail_alphas:
        hr = make_handrail(n, step_l, step_h, alpha, step_w,
                           handrail_width, handrail_height, is_handrail_circular,
                           post_height, handrail_extension)
        assign_material(hr, HANDRAIL_MAT)
        all_parts.append(hr)

    # 6. Main posts
    for alpha in handrail_alphas:
        posts = make_posts(n, step_l, step_h, alpha, step_w,
                           post_width, post_height, is_post_circular, post_k)
        assign_materials(posts, POST_MAT)
        all_parts.extend(posts)

    # 7. Vertical minor posts
    if has_vertical_post:
        for alpha in handrail_alphas:
            vposts = make_vertical_posts(n, step_l, step_h, alpha, step_w,
                                         post_minor_width, post_height,
                                         is_post_circular, post_k)
            assign_materials(vposts, POST_MAT)
            all_parts.extend(vposts)

    # 8. Horizontal bars
    if has_bars:
        for alpha in handrail_alphas:
            bars_list = make_bars(n, step_l, step_h, alpha, step_w,
                                  post_height, n_bars, bar_size,
                                  post_minor_width, post_k)
            assign_materials(bars_list, RAIL_MAT)
            all_parts.extend(bars_list)

    # 9. Glass panels
    if has_glasses:
        for alpha in handrail_alphas:
            glass_list = make_glasses(n, step_l, step_h, alpha, step_w,
                                      glass_height, glass_margin,
                                      post_minor_width, post_k)
            assign_materials(glass_list, GLASS_MAT)
            all_parts.extend(glass_list)

    # ==== Join and finalize ================================================
    result = join_objs(all_parts)

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

    result.name = "StraightStaircaseFactory"
    # [auto-append] ensure material bound
    if result is not None:
        if len(result.data.materials) == 0:
            result.data.materials.append(ELEM_MAT)
        elif result.data.materials[0] is None:
            result.data.materials[0] = ELEM_MAT
    return result

build_straight_stair()
