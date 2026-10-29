# [FL_INDEX: keywords="blender_factory, procedural_3d, CurvedStaircaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CurvedStaircaseFactory | Category: factories_tex
# Prompt: An elegant curved staircase rendered as a richly textured 3D model, featuring a dramatic outward-bowing curved base that sweeps to one side.

import os
import random

import bmesh
import bpy
import numpy as np

SEED = 0
random.seed(SEED)
SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

import os as _os, random as _random, colorsys as _colorsys


def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h)%1, max(0,min(1,float(s))), max(0,min(1,float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear()
    return m

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

WOOD_COLORS = [
    0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170,
    0x3D2B1F, 0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43,
    0x4E3828, 0x4E3828, 0xC09A6B, 0x944536, 0x3F0110, 0x773C12,
    0x6E4E37, 0x5C4033, 0x5C4033, 0x3C3034, 0x96704C, 0x371B1A,
    0x483B32, 0x43141A, 0x471713, 0xC3B090, 0x6B4423, 0x674D46,
    0x5D2E1A, 0x331C1F, 0x7A5640, 0xB99984, 0x71543D, 0x8F4B28,
    0x491A00, 0x836446, 0x7F461B, 0x6A3208, 0x724115, 0xA0522B,
    0x832A0C, 0x371B1A, 0xC7A373, 0x483B32, 0x635147, 0x664228,
    0x5C5248,
]

def _srgb_to_linear(c):
    if c < 0: return 0.0
    elif c < 0.04045: return c / 12.92
    else: return ((c + 0.055) / 1.055) ** 2.4

def _hex2rgba_linear(hexval):
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0)

def _wood_base_color(seed):
    """Sample wood color"""

    rng = np.random.RandomState(((seed + 7) * 2654435761) & 0xFFFFFFFF)
    hexval = WOOD_COLORS[rng.randint(0, len(WOOD_COLORS))]
    r, g, b, _ = _hex2rgba_linear(hexval)
    h, s, v = _colorsys.rgb_to_hsv(r, g, b)
    # Variation in wood color
    h2 = (h + rng.uniform(-0.0, 0.05)) % 1.0
    s2 = max(0, min(1, s + rng.uniform(-0.3, 0.2)))
    v2 = max(0, min(1, v * float(np.exp(rng.uniform(np.log(0.2), np.log(20))))))
    return _colorsys.hsv_to_rgb(h2, s2, v2)

def make_mat(seed, name="WoodMaterial"):
    """Wood material with color"""

    r1, g1, b1 = _wood_base_color(seed)
    r2, g2, b2 = _wood_base_color(seed + 3)
    c1 = (r1, g1, b1, 1.0)
    c2 = (r2, g2, b2, 1.0)
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

ELEM_MAT = make_mat(SEED, "CurvedStaircaseFactory_Material")
STEP_MAT = make_mat(SEED + 11, "CurvedStaircaseFactory_Step")
RAIL_MAT = make_mat(SEED + 17, "CurvedStaircaseFactory_Rail")
TREAD_MAT = make_mat(SEED + 23, "CurvedStaircaseFactory_Tread")
SIDE_MAT = make_mat(SEED + 29, "CurvedStaircaseFactory_Side")
HANDRAIL_MAT = make_mat(SEED + 31, "CurvedStaircaseFactory_Handrail")
POST_MAT = make_mat(SEED + 37, "CurvedStaircaseFactory_Post")
np.random.seed(SEED)

def assign_material(obj, mat):
    if obj is not None:
        obj.data.materials.append(mat)
    return obj

def assign_materials(objs, mat):
    for obj in objs:
        assign_material(obj, mat)
    return objs

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

def triangulate(obj):
    add_mod(obj, "TRIANGULATE", min_vertices=3)
    add_mod(obj, "SUBSURF", levels=1, render_levels=1, subdivision_type="SIMPLE")
    return obj

def subdivide_for_curve(obj, levels=2):
    """Add subdivision so spiral transform has enough vertices to curve smoothly."""

    add_mod(obj, "SUBSURF", levels=levels, render_levels=levels, subdivision_type="SIMPLE")
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

def spiral_transform(obj, radius, step_width, step_length, theta):
    """

    Apply the curved staircase spiral coordinate transform to all vertices.
      u = x + radius - step_width
      t = y / step_length * theta
      new_co = (u*cos(t), u*sin(t), z)
    """

    mesh = obj.data
    n_verts = len(mesh.vertices)
    co = np.zeros(n_verts * 3)
    mesh.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)

    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    u = x + radius - step_width
    t = y / step_length * theta
    new_co = np.stack([u * np.cos(t), u * np.sin(t), z], axis=-1)

    mesh.vertices.foreach_set('co', new_co.flatten().astype(np.float32))
    mesh.update()

# ---------------------------------------------------------------------------
# Geometry builders (all in straight coordinates: x=0..step_w, y=0..n*step_l)
# ---------------------------------------------------------------------------

def make_step_profile(n, step_w, step_l, step_h, hole_size=0.0, has_hole=False):
    """Create solid stair-step profile, solidified in x."""

    bm = bmesh.new()
    # Build stair profile in y-z plane at x=0
    coords = [(0, 0)]
    for i in range(n):
        coords.append((i * step_l, (i + 1) * step_h))
        coords.append(((i + 1) * step_l, (i + 1) * step_h))
    coords.append((n * step_l, 0))

    if has_hole:
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
    mesh = bpy.data.meshes.new("step_profile")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("step_profile", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    add_mod(obj, "SOLIDIFY", thickness=step_w, offset=-1)
    triangulate(obj)
    return obj

def make_treads_straight(n, step_w, step_l, step_h, tread_h, tread_l, tread_w):
    """Tread boards in straight coordinates."""

    parts = []
    for i in range(n):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        tread = bpy.context.active_object
        tread.scale = (tread_w / 2, tread_l / 2, tread_h / 2)
        x_center = step_w / 2  # centered on step width
        y_center = i * step_l + step_l / 2
        z_center = (i + 1) * step_h + tread_h / 2
        tread.location = (x_center, y_center, z_center)
        apply_tf(tread)
        triangulate(tread)
        parts.append(tread)
    return parts

def make_rail_straight(n, step_l, step_h, alpha, step_w, rail_w, rail_h, is_circular):
    """Support rail as polyline in straight coordinates."""

    x = alpha * step_w

    bm = bmesh.new()
    bm_verts = []
    for i in range(n + 1):
        y_val = i * step_l
        z_val = i * step_h
        bm_verts.append(bm.verts.new((x, y_val, z_val)))
    for i in range(len(bm_verts) - 1):
        bm.edges.new((bm_verts[i], bm_verts[i + 1]))

    mesh = bpy.data.meshes.new("rail_line")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("rail_line", mesh)
    bpy.context.collection.objects.link(obj)
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

def make_side_panel_straight(n, step_l, step_h, side_x, side_type, thickness,
                              side_height, tread_h):
    """Side panel in straight coordinates."""

    total_rise = n * step_h
    bm = bmesh.new()

    if side_type == "zig-zag":
        upper = [(0, 0)]
        for i in range(n):
            upper.append((i * step_l, (i + 1) * step_h))
            upper.append(((i + 1) * step_l, (i + 1) * step_h))
        lower = [(y, max(0, z - side_height)) for y, z in upper]
        coords = upper + list(reversed(lower))
    else:
        total_run = n * step_l
        coords = [
            (0, 0),
            (0, step_h),                             # first step top
            (total_run, total_rise),                 # last step top
            (total_run, total_rise - side_height),   # bottom-right
        ]

    bm_verts = [bm.verts.new((side_x, y, z)) for y, z in coords]
    try:
        bm.faces.new(bm_verts)
    except ValueError:
        pass

    mesh = bpy.data.meshes.new("side_panel")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("side_panel", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    add_mod(obj, "SOLIDIFY", thickness=thickness, offset=0)
    triangulate(obj)
    return obj

def make_handrail_straight(n, step_l, step_h, alpha, step_w, hw, hh, is_circular,
                            post_height, extension):
    """Handrail as a polyline in straight coordinates, shifted up by post_height."""

    x = alpha * step_w

    # Build line at step midpoints + post_height
    points = []
    for i in range(n):
        y_val = i * step_l + step_l / 2
        z_val = (i + 1) * step_h + post_height
        points.append((x, y_val, z_val))

    # Add horizontal extensions at both ends
    if len(points) >= 2:
        # Start extension: horizontal backward (z stays the same)
        points.insert(0, (x, points[0][1] - extension, points[0][2]))
        # End extension: horizontal forward (z stays the same)
        points.append((x, points[-1][1] + extension, points[-1][2]))

    # Create polyline mesh
    bm = bmesh.new()
    bm_verts = [bm.verts.new(p) for p in points]
    for i in range(len(bm_verts) - 1):
        bm.edges.new((bm_verts[i], bm_verts[i + 1]))
    mesh = bpy.data.meshes.new("handrail_line")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("handrail_line", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    if is_circular:
        geo_radius_tube(obj, hw, resolution=16)
    else:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_edges_move(
            TRANSFORM_OT_translate={"value": (0, 0, -hh * 2)})
        bpy.ops.object.mode_set(mode='OBJECT')
        add_mod(obj, "SOLIDIFY", thickness=hw * 2, offset=0)
        triangulate(obj)

    return obj

def _make_posts_at_straight(n, step_l, step_h, alpha, step_w, post_width,
                            post_height, is_circular, indices, cyl_verts=12):
    """Create vertical posts at given tread indices in straight coordinates."""

    parts = []
    x = alpha * step_w

    for idx in indices:
        y = idx * step_l + step_l / 2
        z_base = (idx + 1) * step_h

        if is_circular:
            bpy.ops.mesh.primitive_cylinder_add(vertices=cyl_verts, radius=post_width,
                                                 depth=post_height, location=(0, 0, 0))
        else:
            bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
            bpy.context.active_object.scale = (post_width, post_width,
                                                post_height / 2)
        post = bpy.context.active_object
        post.location = (x, y, z_base + post_height / 2)
        apply_tf(post)
        parts.append(post)

    return parts

def make_posts_straight(n, step_l, step_h, alpha, step_w, post_width, post_height,
                         is_circular, post_k):
    indices = sorted(set(list(range(0, n, post_k)) + [n - 1]))
    return _make_posts_at_straight(n, step_l, step_h, alpha, step_w, post_width,
                                   post_height, is_circular, indices, 12)

def make_vertical_posts_straight(n, step_l, step_h, alpha, step_w, post_width,
                                  post_height, is_circular, post_k):
    main_indices = set(list(range(0, n, post_k)) + [n - 1])
    indices = [i for i in range(n) if i not in main_indices]
    return _make_posts_at_straight(n, step_l, step_h, alpha, step_w, post_width,
                                   post_height, is_circular, indices, 8)

def make_bars_straight(n, step_l, step_h, alpha, step_w, post_height, n_bars,
                       bar_width, post_k, bar_size):
    """Horizontal bars between main posts in straight coordinates."""

    parts = []
    x = alpha * step_w
    indices = sorted(set(list(range(0, n, post_k)) + [n - 1]))

    # Build post base locations (no flat-top extension)
    locs = []
    for idx in indices:
        locs.append(np.array([x, idx * step_l + step_l / 2, (idx + 1) * step_h]))

    for pi in range(len(locs) - 1):
        p0 = locs[pi]
        p1 = locs[pi + 1]

        for bi in range(n_bars):
            bar_z_offset = post_height - (bi + 1) * bar_size

            # Create line with many intermediate vertices
            n_seg = 16
            bm = bmesh.new()
            bm_verts = []
            for si in range(n_seg + 1):
                t_val = si / n_seg
                pos = p0 * (1 - t_val) + p1 * t_val
                bm_verts.append(bm.verts.new(
                    (float(pos[0]), float(pos[1]), float(pos[2]) + bar_z_offset)))
            for si in range(n_seg):
                bm.edges.new((bm_verts[si], bm_verts[si + 1]))

            mesh = bpy.data.meshes.new("bar_line")
            bm.to_mesh(mesh)
            bm.free()
            obj = bpy.data.objects.new("bar_line", mesh)
            bpy.context.collection.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            geo_radius_tube(obj, bar_width, resolution=6)
            parts.append(obj)

    return parts

# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------
def build_curved_stair():
    clear_scene()

    # Size config with retry loop
    wall_height = np.random.uniform(2.8, 3.2)
    while True:
        full_angle = np.random.randint(1, 5) * np.pi / 2
        n = np.random.randint(13, 21)
        step_h = wall_height / n
        theta = full_angle / n
        step_l = step_h * log_uniform(1, 1.5)
        step_w = log_uniform(0.9, 1.5)
        radius = step_l / theta
        if radius / step_w > 1.5:
            break

    total_rise = n * step_h

    # Support type (curved weights favor side/solid/hole)
    support_type = weighted_choice([
        (2, "single-rail"), (2, "double-rail"),
        (4, "side"), (4, "solid"), (4, "hole")])

    has_step = support_type in ["solid", "hole"]
    has_rail = support_type in ["single-rail", "double-rail"]
    has_sides = support_type in ["side", "solid", "hole"]

    hole_size = log_uniform(0.6, 1.0)

    # Rail parameters
    rail_offset = step_w * np.random.uniform(0.15, 0.3)
    is_rail_circular = np.random.uniform() < 0.5
    rail_width = log_uniform(0.08, 0.2)
    rail_height = log_uniform(0.08, 0.12)

    # Tread parameters
    has_tread = (not has_step) or (np.random.uniform() < 0.75)
    tread_h = np.random.uniform(0.01, 0.02) if has_step else np.random.uniform(0.06, 0.08)
    tread_l = step_l + np.random.uniform(0.01, 0.02)
    tread_w = step_w + np.random.uniform(0.01, 0.02) if np.random.uniform() < 0.8 else step_w

    # Side parameters
    side_type = np.random.choice(["zig-zag", "straight"])
    side_height = step_h * log_uniform(0.2, 0.8)
    side_thickness = np.random.uniform(0.03, 0.08)

    # Handrail type (no glass for curved)
    handrail_type = weighted_choice([
        (2, "horizontal-post"), (2, "vertical-post")])
    is_handrail_circular = np.random.uniform() < 0.7
    handrail_width = log_uniform(0.02, 0.06)
    handrail_height = log_uniform(0.02, 0.06)
    handrail_offset = handrail_width * log_uniform(1, 2)
    handrail_extension = np.random.uniform(0.1, 0.2)
    handrail_alphas = [
        handrail_offset / step_w,
        1 - handrail_offset / step_w,
    ]

    # Post parameters
    post_height = log_uniform(0.8, 1.2)
    post_k = 1
    post_width = handrail_width * log_uniform(0.6, 0.8)
    post_minor_width = post_width * log_uniform(0.3, 0.5)
    is_post_circular = np.random.uniform() < 0.5

    has_vertical_post = handrail_type == "vertical-post"
    has_bars = handrail_type == "horizontal-post"
    bar_size = log_uniform(0.1, 0.2)
    n_bars = max(1, int(np.floor(post_height / bar_size * np.random.uniform(0.35, 0.75))))

    do_mirror = np.random.uniform() < 0.5
    rot_z = np.random.randint(4) * np.pi / 2

    # ==== Build ALL geometry in STRAIGHT coordinates ========================
    all_parts = []

    # Steps (solid/hole support)
    if has_step:
        solid = make_step_profile(n, step_w, step_l, step_h,
                                   hole_size=hole_size,
                                   has_hole=(support_type == "hole"))
        subdivide_for_curve(solid, levels=2)
        assign_material(solid, STEP_MAT)
        all_parts.append(solid)

    # Rails
    if has_rail:
        if support_type == "single-rail":
            rail_alphas = [0.5]
        else:
            rail_alphas = [rail_offset / step_w, 1 - rail_offset / step_w]
        for alpha in rail_alphas:
            rail = make_rail_straight(n, step_l, step_h, alpha, step_w,
                                      rail_width, rail_height, is_rail_circular)
            subdivide_for_curve(rail, levels=2)
            assign_material(rail, RAIL_MAT)
            all_parts.append(rail)

    # Treads
    if has_tread:
        treads = make_treads_straight(n, step_w, step_l, step_h, tread_h, tread_l, tread_w)
        for tread in treads:
            subdivide_for_curve(tread, levels=2)
        assign_materials(treads, TREAD_MAT)
        all_parts.extend(treads)

    # Side panels
    if has_sides:
        for side_x in [0, step_w]:
            panel = make_side_panel_straight(n, step_l, step_h, side_x, side_type,
                                              side_thickness, side_height, tread_h)
            subdivide_for_curve(panel, levels=2)
            assign_material(panel, SIDE_MAT)
            all_parts.append(panel)

    # Handrails
    for alpha in handrail_alphas:
        hr = make_handrail_straight(n, step_l, step_h, alpha, step_w,
                                     handrail_width, handrail_height,
                                     is_handrail_circular, post_height,
                                     handrail_extension)
        subdivide_for_curve(hr, levels=1)
        assign_material(hr, HANDRAIL_MAT)
        all_parts.append(hr)

    # Main posts (subdivide for smooth spiral curving)
    for alpha in handrail_alphas:
        posts = make_posts_straight(n, step_l, step_h, alpha, step_w,
                                     post_width, post_height, is_post_circular,
                                     post_k)
        for p in posts:
            subdivide_for_curve(p, levels=1)
        assign_materials(posts, POST_MAT)
        all_parts.extend(posts)

    # Vertical minor posts (subdivide for smooth spiral curving)
    if has_vertical_post:
        for alpha in handrail_alphas:
            vposts = make_vertical_posts_straight(n, step_l, step_h, alpha, step_w,
                                                   post_minor_width, post_height,
                                                   is_post_circular, post_k)
            for p in vposts:
                subdivide_for_curve(p, levels=1)
            assign_materials(vposts, POST_MAT)
            all_parts.extend(vposts)

    # Horizontal bars
    if has_bars:
        for alpha in handrail_alphas:
            bars = make_bars_straight(n, step_l, step_h, alpha, step_w,
                                      post_height, n_bars, post_minor_width,
                                      post_k, bar_size)
            assign_materials(bars, RAIL_MAT)
            all_parts.extend(bars)

    # ==== Join everything ===================================================
    if not all_parts:
        bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, 0))
        result = bpy.context.active_object
    else:
        result = join_objs(all_parts)

    # ==== Apply spiral transform to ALL vertices ============================
    spiral_transform(result, radius, step_w, step_l, theta)

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

    result.name = "CurvedStaircaseFactory"
    # [auto-append] ensure material bound
    if result is not None:
        if len(result.data.materials) == 0:
            result.data.materials.append(ELEM_MAT)
        elif result.data.materials[0] is None:
            result.data.materials[0] = ELEM_MAT
    return result

build_curved_stair()

