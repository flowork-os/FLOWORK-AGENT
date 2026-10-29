# [FL_INDEX: keywords="blender_factory, procedural_3d, RackFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: RackFactory | Category: factories_tex
# Prompt: A tall industrial warehouse storage rack rendered as a 3D model, featuring a dark steel frame with vertical perforated uprights connected by horizontal beams at multiple levels.

import os
import math
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

def _srgb_to_linear(c):
    if c < 0: return 0.0
    elif c < 0.04045: return c / 12.92
    else: return ((c + 0.055) / 1.055) ** 2.4

def _hex2rgba_linear(hexval):
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

NATURAL_BASE_COLORS = [
    (0xC0C0C0, 1), (0x8C7853, 1), (0xBDBAAE, 1), (0xA9ACB6, 1), (0xB6AFA9, 1),
]

def _metal_color_hsv():
    
    if np.random.uniform() < 0.2:
        weights = np.array([w for _, w in NATURAL_BASE_COLORS], dtype=float)
        idx = int(np.random.choice(len(NATURAL_BASE_COLORS), p=weights / weights.sum()))
        hexval = NATURAL_BASE_COLORS[idx][0]
        r, g, b, _ = _hex2rgba_linear(hexval)
        h, s, v = _colorsys.rgb_to_hsv(r, g, b)
        return (h + np.random.uniform(-0.1, 0.1),
                s + np.random.uniform(-0.1, 0.1),
                v * _log_uniform(0.5, 0.2))
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            _log_uniform(0.02, 0.5))

def make_mat(seed, name="MetalMaterial"):
    """Metal material"""

    h, s, v = _metal_color_hsv()
    c = _hsv2rgba(h, s, v)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    ln(tc.outputs["Object"], noise.inputs["Vector"])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Metallic"].default_value = 1.0
    sk = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[sk].default_value = float(np.random.uniform(0.5, 1.0))
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.1, 0.5))
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

ELEM_MAT = make_mat(SEED, "RackFactory_Material")
np.random.seed(SEED)

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
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def read_co(obj):
    mesh = obj.data
    co = np.zeros(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', co)
    return co.reshape(-1, 3)

def write_co(obj, co):
    mesh = obj.data
    mesh.vertices.foreach_set('co', co.flatten().astype(np.float32))
    mesh.update()

def new_cube():
    """Create a cube: size=2 at (0,0,0.5) with applied transform.
    Results in z range [-0.5, 1.5] in mesh data (asymmetric z)."""

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0.5))
    obj = bpy.context.active_object
    apply_tf(obj)
    return obj

def deep_clone(obj):
    """Clone an object with its mesh data."""

    new_mesh = obj.data.copy()
    new_obj = obj.copy()
    new_obj.data = new_mesh
    bpy.context.collection.objects.link(new_obj)
    return new_obj

def geo_radius_tube(obj, radius, resolution=16):
    """Convert edge mesh to tube via GeoNodes: MeshToCurve → SetCurveRadius → CurveToMesh."""

    ng = bpy.data.node_groups.new("GeoRadius", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    input_node = ng.nodes.new('NodeGroupInput')
    output_node = ng.nodes.new('NodeGroupOutput')
    input_node.location = (-400, 0)
    output_node.location = (400, 0)

    m2c = ng.nodes.new('GeometryNodeMeshToCurve')
    m2c.location = (-200, 0)
    ng.links.new(input_node.outputs[0], m2c.inputs[0])

    scr = ng.nodes.new('GeometryNodeSetCurveRadius')
    scr.location = (-50, 0)
    ng.links.new(m2c.outputs[0], scr.inputs[0])
    scr.inputs['Radius'].default_value = radius

    circle = ng.nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.location = (50, -150)
    circle.inputs['Resolution'].default_value = resolution
    circle.inputs['Radius'].default_value = 1.0

    c2m = ng.nodes.new('GeometryNodeCurveToMesh')
    c2m.location = (200, 0)
    ng.links.new(scr.outputs[0], c2m.inputs['Curve'])
    ng.links.new(circle.outputs[0], c2m.inputs['Profile Curve'])
    # Blender 5.0: need Scale input for radius to take effect
    c2m.inputs['Fill Caps'].default_value = True
    try:
        c2m.inputs['Scale'].default_value = radius
    except (KeyError, IndexError):
        pass

    ng.links.new(c2m.outputs[0], output_node.inputs[0])

    mod = obj.modifiers.new("GeoRadius", 'NODES')
    mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

def solidify_edge_mesh(obj, axis, thickness):
    """Extrude edges in two perpendicular directions to give thickness."""

    axes = [0, 1, 2]
    axes.remove(axis)
    u = [0, 0, 0]
    u[axes[0]] = thickness
    v = [0, 0, 0]
    v[axes[1]] = thickness

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_edges_move(TRANSFORM_OT_translate={"value": tuple(u)})
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": tuple(v)})
    bpy.ops.object.mode_set(mode='OBJECT')

    # Center the extruded mesh
    offset = np.array(u) + np.array(v)
    obj.location = -offset[0] / 2, -offset[1] / 2, -offset[2] / 2
    apply_tf(obj, loc=True)

def new_line_mesh(n, total_height):
    """Create a line mesh with n+1 vertices along X from 0 to total_height."""

    mesh = bpy.data.meshes.new("line")
    vertices = [(i / n * total_height, 0, 0) for i in range(n + 1)]
    edges = [(i, i + 1) for i in range(n)]
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    obj = bpy.data.objects.new("line", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def make_pallet_inline(p_depth, p_width, height_p, tile_w, tile_slack, board_t):
    """5-layer crossed-board pallet matching PalletFactory.

    Layers (bottom to top):
    1. Horizontal boards (spanning width X, arrayed along depth Y)
    2. Vertical boards (spanning depth Y, arrayed along width X)
    3. 3x3 support blocks
    4. Horizontal boards (spanning width X)
    5. Vertical boards (spanning depth Y)
    """

    parts = []

    def _make_board(bw, bd, bt, bx, by, bz):
        """Create a single board at the given position."""

        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        b = bpy.context.active_object
        b.scale = (bw / 2, bd / 2, bt / 2)
        b.location = (bx + bw / 2, by + bd / 2, bz + bt / 2)
        apply_tf(b)
        return b

    # Vertical boards: each tile_w wide, p_depth long, board_t thick
    # Arrayed along width (X)
    def make_vertical_layer(z_off):
        count = int(np.floor((p_width - tile_w) / tile_w / tile_slack) / 2) * 2
        count = max(count, 2)
        spacing = (p_width - tile_w) / count
        obj = _make_board(tile_w, p_depth, board_t, 0, 0, z_off)
        if count > 0:
            add_mod(obj, "ARRAY",
                    use_relative_offset=False,
                    use_constant_offset=True,
                    constant_offset_displace=(spacing, 0, 0),
                    count=count + 1)
        return obj

    # Horizontal boards: p_width wide, each tile_w deep, board_t thick
    # Arrayed along depth (Y)
    def make_horizontal_layer(z_off):
        count = int(np.floor((p_depth - tile_w) / tile_w / tile_slack) / 2) * 2
        count = max(count, 2)
        spacing = (p_depth - tile_w) / count
        obj = _make_board(p_width, tile_w, board_t, 0, 0, z_off)
        if count > 0:
            add_mod(obj, "ARRAY",
                    use_relative_offset=False,
                    use_constant_offset=True,
                    constant_offset_displace=(0, spacing, 0),
                    count=count + 1)
        return obj

    # 3x3 support blocks between board layers
    def make_support_layer(z_off):
        support_h = height_p - 4 * board_t
        if support_h < 0.005:
            return None
        obj = _make_board(tile_w, tile_w, support_h, 0, 0, z_off)
        x_sp = (p_width - tile_w) / 2
        y_sp = (p_depth - tile_w) / 2
        add_mod(obj, "ARRAY",
                use_relative_offset=False,
                use_constant_offset=True,
                constant_offset_displace=(x_sp, 0, 0),
                count=3)
        add_mod(obj, "ARRAY",
                use_relative_offset=False,
                use_constant_offset=True,
                constant_offset_displace=(0, y_sp, 0),
                count=3)
        return obj

    # Build 5 layers bottom-to-top
    parts.append(make_horizontal_layer(0))                         # Layer 1
    parts.append(make_vertical_layer(board_t))                     # Layer 2
    sup = make_support_layer(2 * board_t)                          # Layer 3
    if sup:
        parts.append(sup)
    parts.append(make_horizontal_layer(height_p - 2 * board_t))   # Layer 4
    parts.append(make_vertical_layer(height_p - board_t))          # Layer 5

    pallet = join_objs(parts)
    return pallet

def make_stand_unit(thickness, hole_radius):
    """Single upright unit with 2 perpendicular holes."""

    obj = new_cube()
    obj.scale = [thickness / 2] * 3
    apply_tf(obj)

    for rot_axis in ['x', 'y']:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8, radius=hole_radius, depth=thickness * 2, location=(0, 0, 0)
        )
        cyl = bpy.context.active_object
        if rot_axis == 'x':
            cyl.rotation_euler.y = math.pi / 2
        else:
            cyl.rotation_euler.x = math.pi / 2
        apply_tf(cyl)

        bool_mod = obj.modifiers.new("hole", "BOOLEAN")
        bool_mod.operation = "DIFFERENCE"
        bool_mod.object = cyl
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cyl, do_unlink=True)

    # Remove interior faces
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    to_delete = []
    for f in bm.faces:
        center = f.calc_center_median()
        x, y, z = abs(center.x), abs(center.y), abs(center.z)
        if (x < thickness * 0.49 and y < thickness * 0.49 and z < thickness * 0.49):
            to_delete.append(f)
        elif x + y < thickness * 0.1:
            to_delete.append(f)
    if to_delete:
        bmesh.ops.delete(bm, geom=to_delete, context='FACES')
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj

def make_stands(width, depth, thickness, hole_radius, height, steps):
    """Create 4 corner upright posts via ARRAY modifier stacking."""

    total_height = height * steps
    obj = make_stand_unit(thickness, hole_radius)

    # Position base at z=0 (move up by thickness/2 so bottom is at z=0)
    obj.location[2] = thickness / 2
    apply_tf(obj, loc=True)

    # Array vertically
    n_stack = int(np.ceil(total_height / thickness))
    add_mod(obj, "ARRAY",
            count=n_stack,
            relative_offset_displace=(0, 0, 1),
            use_merge_vertices=True)

    stands = [obj]
    for locs in [(0, 1), (1, 1), (1, 0)]:
        o = deep_clone(obj)
        o.location = (locs[0] * width, locs[1] * depth, 0)
        apply_tf(o, loc=True)
        stands.append(o)

    return stands

def make_supports(width, depth, thickness, height, steps, support_angle, is_round):
    """Create continuous zigzag support braces."""

    total_height = height * steps
    n = int(np.floor(total_height / depth / np.tan(support_angle)))

    # Create line mesh along X with n+1 vertices
    obj = new_line_mesh(n, total_height)

    # Rotate -90° around Y to put line along Z
    obj.rotation_euler[1] = -math.pi / 2
    apply_tf(obj)

    # Shift every other vertex to Y=depth (zigzag pattern)
    co = read_co(obj)
    co[1::2, 1] = depth
    write_co(obj, co)

    # Give thickness
    if is_round:
        geo_radius_tube(obj, thickness / 2, 16)
    else:
        solidify_edge_mesh(obj, 1, thickness)

    # Clone for opposite side
    o2 = deep_clone(obj)
    o2.location[0] = width
    apply_tf(o2, loc=True)

    return [obj, o2]

def make_frames(width, depth, thickness, height, steps, frame_height, frame_count):
    """Create horizontal frame bars at the TOP of each shelf level.
    Bars at z = height - frame_height/2 (TOP of level 0),
    then cloned for levels 1 through steps-2."""

    parts = []

    # X-direction bars (front and back) at top of first level
    x_bar = new_cube()
    x_bar.scale = (width / 2, thickness / 2, frame_height / 2)
    x_bar.location = (width / 2, 0, height - frame_height / 2)
    apply_tf(x_bar)

    x_bar_back = deep_clone(x_bar)
    x_bar_back.location[1] = depth
    apply_tf(x_bar_back, loc=True)

    # Y-direction bars (perpendicular, evenly spaced along X)
    margin = width / frame_count
    y_bar = new_cube()
    y_bar.scale = (thickness / 2, depth / 2, thickness / 2)
    y_bar.location = (margin, depth / 2, height - thickness / 2)
    apply_tf(y_bar)

    # Array to create frame_count-1 total bars
    if frame_count > 2:
        add_mod(y_bar, "ARRAY",
                use_relative_offset=False,
                use_constant_offset=True,
                count=frame_count - 1,
                constant_offset_displace=(margin, 0, 0))

    frames = [x_bar, x_bar_back, y_bar]

    # Clone for additional levels (1 through steps-2)
    for i in range(1, steps - 1):
        for base_obj in [x_bar, x_bar_back, y_bar]:
            o = deep_clone(base_obj)
            o.location[2] += height * i
            apply_tf(o, loc=True)
            frames.append(o)

    # Ground-level y-bars to support bottom pallets (prevents floating appearance)
    gnd_y = new_cube()
    gnd_y.scale = (thickness / 2, depth / 2, thickness / 2)
    gnd_y.location = (margin, depth / 2, thickness / 2)
    apply_tf(gnd_y)
    if frame_count > 2:
        add_mod(gnd_y, "ARRAY",
                use_relative_offset=False,
                use_constant_offset=True,
                count=frame_count - 1,
                constant_offset_displace=(margin, 0, 0))
    frames.append(gnd_y)

    return frames

def make_metal_material():
    """Dark metal material for rack frame."""

    mat = bpy.data.materials.new("rack_metal")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        hue = np.random.uniform(0.06, 0.10)  # warm brown-gray
        sat = np.random.uniform(0.15, 0.30)
        val = np.random.uniform(0.10, 0.20)
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.85
        bsdf.inputs['Roughness'].default_value = np.random.uniform(0.55, 0.75)
    return mat

def make_wood_material():
    """Light wood material for pallets."""

    mat = bpy.data.materials.new("pallet_wood")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        hue = np.random.uniform(0.07, 0.12)  # warm wood tone
        sat = np.random.uniform(0.30, 0.55)
        val = np.random.uniform(0.60, 0.80)
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
        bsdf.inputs['Roughness'].default_value = np.random.uniform(0.75, 0.90)
    return mat

def assign_material(obj, mat):
    """Assign material to all faces of an object."""

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def build_rack():
    clear_scene()

    # Parameters
    depth = np.random.uniform(1.0, 1.2)
    width = np.random.uniform(4.0, 5.0)
    height = np.random.uniform(1.6, 1.8)
    steps = np.random.randint(3, 6)
    thickness = np.random.uniform(0.06, 0.08)
    hole_radius = thickness / 2 * np.random.uniform(0.5, 0.6)
    support_angle = np.random.uniform(math.pi / 6, math.pi / 4)
    is_support_round = np.random.uniform() < 0.5
    frame_height = thickness * np.random.uniform(3, 4)
    frame_count = np.random.randint(20, 30)

    total_height = height * steps

    # Create materials
    metal_mat = make_metal_material()
    wood_mat = make_wood_material()

    # Stands (4 corner uprights)
    stands = make_stands(width, depth, thickness, hole_radius, height, steps)
    for s in stands:
        assign_material(s, metal_mat)

    # Supports (continuous zigzag braces)
    supports = make_supports(width, depth, thickness, height, steps, support_angle, is_support_round)
    for s in supports:
        assign_material(s, metal_mat)

    # Frames (horizontal bars at TOP of each level)
    frames = make_frames(width, depth, thickness, height, steps, frame_height, frame_count)
    for f in frames:
        assign_material(f, metal_mat)

    # Join structure
    all_parts = stands + supports + frames
    obj = join_objs(all_parts)

    # Clip Z coordinates to [0, total_height]
    co = read_co(obj)
    co[:, 2] = np.clip(co[:, 2], 0, total_height)
    write_co(obj, co)

    # Pallets: 2 per level, constrained INSIDE the upright posts
    # Pallet board parameters (shared across all pallets on this rack)
    pallet_h = np.random.uniform(0.20, 0.25)
    pallet_tile_w = np.random.uniform(0.06, 0.10)
    pallet_tile_slack = np.random.uniform(1.5, 2.0)
    pallet_board_t = np.random.uniform(0.010, 0.015)

    # Pallet dimensions (fixed size, NOT derived from rack)
    actual_pw = np.random.uniform(1.2, 1.4)
    actual_pd = np.random.uniform(1.2, 1.4)
    # Width clamp: each pallet must fit within half the rack width
    actual_pw = min(actual_pw, (width - thickness) / 2 - 0.1)
    # Depth clamp: fit between the upright posts (inner face at thickness/2 on each side)
    # Clamp to avoid visible out-of-bounds geometry since everything is joined
    # into one mesh.
    actual_pd = min(actual_pd, depth - thickness)
    # Margin from rack edge
    margin_range = (0.3, 0.5)

    pallet_parts = []

    for level in range(steps):
        for side in range(2):  # 2 pallets per level
            p = make_pallet_inline(actual_pd, actual_pw, pallet_h,
                                   pallet_tile_w, pallet_tile_slack, pallet_board_t)
            assign_material(p, wood_mat)

            pw = p.dimensions[0]
            pd = p.dimensions[1]

            margin = np.random.uniform(*margin_range)
            if side == 0:
                px = margin
            else:
                px = width - margin - pw

            py = (depth - pd) / 2
            # Z position: level * height
            pz = level * height

            p.location = (px, py, pz)
            apply_tf(p, loc=True)
            pallet_parts.append(p)

    # Join pallets to main object
    all_final = [obj] + pallet_parts
    result = join_objs(all_final)

    # Final rotation: 90 degrees around Z
    result.rotation_euler[2] = math.pi / 2
    apply_tf(result)

    result.name = "RackFactory"
    return result

rack = build_rack()

