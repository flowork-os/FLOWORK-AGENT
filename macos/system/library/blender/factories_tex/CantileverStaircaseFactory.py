# [FL_INDEX: keywords="blender_factory, procedural_3d, CantileverStaircaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CantileverStaircaseFactory | Category: factories_tex
# Prompt: A modern cantilever staircase rendered as a detailed 3D model, featuring dark navy blue floating steps that appear unsupported on one side — the hallmark of cantilever design.

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

ELEM_MAT = make_mat(SEED, "CantileverStaircaseFactory_Material")
TREAD_MAT = make_mat(SEED + 11, "CantileverStaircaseFactory_Tread")
HANDRAIL_MAT = make_mat(SEED + 23, "CantileverStaircaseFactory_Handrail")
POST_MAT = make_mat(SEED + 31, "CantileverStaircaseFactory_Post")
RAIL_MAT = make_mat(SEED + 37, "CantileverStaircaseFactory_Rail")
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

def triangulate(obj):
    """Triangulate + simple subdivision."""

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

# ---------------------------------------------------------------------------
# Treads: full-width floating step boards
# ---------------------------------------------------------------------------
def make_treads(n, step_w, step_l, step_h, tread_h, tread_l, tread_w):
    """Create full-width tread boards at each step position."""

    parts = []
    for i in range(n):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
        tread = bpy.context.active_object
        tread.scale = (tread_w / 2, tread_l / 2, tread_h / 2)
        x_center = -(tread_w - step_w) / 2 + tread_w / 2
        y_center = i * step_l + step_l / 2
        z_center = (i + 1) * step_h + tread_h / 2
        tread.location = (x_center, y_center, z_center)
        apply_tf(tread)
        triangulate(tread)
        parts.append(tread)
    return parts

# ---------------------------------------------------------------------------
# Handrail along the stair slope — polyline with horizontal extensions
# ---------------------------------------------------------------------------
def make_handrail(n, step_l, step_h, step_w, alpha, hw, hh, is_circular,
                  post_height, extension):
    """Handrail following the stair slope with horizontal extensions at ends."""

    x = alpha * step_w

    # Vertices at each tread center, shifted up by post_height
    verts = []
    for i in range(n):
        y = i * step_l + step_l / 2
        z = (i + 1) * step_h + post_height
        verts.append((x, y, z))

    # Horizontal extensions
    if len(verts) >= 2:
        # Start extension: direction from v0 toward v1, but horizontal (z=0)
        dy = verts[1][1] - verts[0][1]
        ext_start = (x, verts[0][1] - extension, verts[0][2])  # horizontal backward
        verts.insert(0, ext_start)

        # End extension: direction from v[-2] toward v[-1], horizontal
        ext_end = (x, verts[-1][1] + extension, verts[-1][2])  # horizontal forward
        verts.append(ext_end)

    # Create mesh from vertices
    bm = bmesh.new()
    bverts = [bm.verts.new(v) for v in verts]
    for i in range(len(bverts) - 1):
        bm.edges.new((bverts[i], bverts[i + 1]))

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
        # Rectangular: extrude edges downward + solidify
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_edges_move(
            TRANSFORM_OT_translate={"value": (0, 0, -hh * 2)})
        bpy.ops.object.mode_set(mode='OBJECT')
        add_mod(obj, "SOLIDIFY", thickness=hw * 2, offset=0)

    return obj

# ---------------------------------------------------------------------------
# Posts along the stair slope — placed at actual tread positions
# ---------------------------------------------------------------------------
def _make_posts_at_cantilever(n, step_l, step_h, step_w, alpha, post_width,
                              post_height, is_circular, indices, cyl_verts=12):
    """Create vertical posts at given tread indices."""

    parts = []
    x = alpha * step_w

    for i in indices:
        y = i * step_l + step_l / 2
        z_base = (i + 1) * step_h

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

def make_posts_along_rail(n, step_l, step_h, step_w, alpha, post_width, post_height,
                          is_circular, post_k):
    indices = sorted(set(list(range(0, n, post_k)) + [n - 1]))
    return _make_posts_at_cantilever(n, step_l, step_h, step_w, alpha, post_width,
                                     post_height, is_circular, indices, 12)

# ---------------------------------------------------------------------------
# Horizontal bars between posts (for horizontal-post handrail type)
# ---------------------------------------------------------------------------
def make_horizontal_bars(n, step_l, step_h, step_w, alpha, post_height, n_bars,
                         bar_spacing, bar_thickness, post_k):
    """Horizontal bars connecting main posts at tread-aligned positions."""

    parts = []
    x = alpha * step_w
    indices = sorted(set(list(range(0, n, post_k)) + [n - 1]))

    locs = []
    for i in indices:
        y = i * step_l + step_l / 2
        z = (i + 1) * step_h
        locs.append((y, z))

    for pi in range(len(locs) - 1):
        y0, z0 = locs[pi]
        y1, z1 = locs[pi + 1]

        bar_len = math.sqrt((y1 - y0) ** 2 + (z1 - z0) ** 2)
        angle = math.atan2(z1 - z0, y1 - y0)

        for bi in range(n_bars):
            bar_z_offset = post_height - (bi + 1) * bar_spacing

            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=bar_thickness,
                                                depth=bar_len, location=(0, 0, 0))
            bar = bpy.context.active_object
            bar.rotation_euler.x = -(math.pi / 2 - angle)
            bar.location = (x, (y0 + y1) / 2,
                            (z0 + z1) / 2 + bar_z_offset)
            apply_tf(bar)
            parts.append(bar)

    return parts

def make_vertical_minor_posts(n, step_l, step_h, step_w, alpha, post_width,
                              post_height, is_circular, post_k):
    main_indices = set(list(range(0, n, post_k)) + [n - 1])
    indices = [i for i in range(n) if i not in main_indices]
    return _make_posts_at_cantilever(n, step_l, step_h, step_w, alpha, post_width,
                                     post_height, is_circular, indices, 8)

# Main builder
def build_cantilever_stair():
    clear_scene()

    # ---- Size configuration ------------------------------------------------
    wall_height = np.random.uniform(2.8, 3.2)
    n = np.random.randint(13, 21)
    step_h = wall_height / n
    step_w = np.random.uniform(0.8, 1.6)
    step_l = step_h * log_uniform(0.8, 1.2)

    # ---- Tread parameters (thicker since has_step=False) ------------------
    tread_h = np.random.uniform(0.06, 0.08)
    tread_l = step_l + np.random.uniform(0.01, 0.02)
    tread_w = step_w + np.random.uniform(0.01, 0.02) if np.random.uniform() < 0.8 else step_w

    # ---- Handrail type: only horizontal-post or vertical-post (no glass) --
    handrail_type = weighted_choice([
        (2, "horizontal-post"), (2, "vertical-post")])

    is_handrail_circular = np.random.uniform() < 0.7
    handrail_width = log_uniform(0.03, 0.06)
    handrail_height = log_uniform(0.03, 0.06)
    handrail_offset = handrail_width * log_uniform(1, 2)
    handrail_extension = np.random.uniform(0.05, 0.15)

    handrail_alphas = [
        handrail_offset / step_w,
        1 - handrail_offset / step_w,
    ]

    # ---- Post parameters --------------------------------------------------
    post_height = log_uniform(0.8, 1.2)
    post_k = 1
    post_width = handrail_width * log_uniform(0.6, 0.8)
    post_minor_width = post_width * log_uniform(0.3, 0.5)
    is_post_circular = np.random.uniform() < 0.5

    has_vertical_post = (handrail_type == "vertical-post")
    has_bars = (handrail_type == "horizontal-post")

    # Bar parameters (for horizontal-post type)
    bar_size = log_uniform(0.1, 0.2)
    n_bars = max(1, int(np.floor(
        post_height / bar_size * np.random.uniform(0.35, 0.75))))

    # ---- Mirror and rotation ------------------------------------------------
    do_mirror = np.random.uniform() < 0.5
    rot_z = np.random.randint(4) * math.pi / 2

    # ==== Build all parts ==================================================
    all_parts = []

    # 1. Full-width treads (the only structural element for cantilever)
    #    No stringer/side panels — cantilever treads mount directly to wall
    treads = make_treads(n, step_w, step_l, step_h, tread_h, tread_l, tread_w)
    assign_materials(treads, TREAD_MAT)
    all_parts.extend(treads)

    # 2. Handrails (on both sides) — polyline with horizontal extensions
    for alpha in handrail_alphas:
        hr = make_handrail(n, step_l, step_h, step_w, alpha,
                           handrail_width, handrail_height, is_handrail_circular,
                           post_height, handrail_extension)
        assign_material(hr, HANDRAIL_MAT)
        all_parts.append(hr)

    # 3. Main posts (at post_k intervals + first/last + flat top post)
    for alpha in handrail_alphas:
        posts = make_posts_along_rail(n, step_l, step_h, step_w, alpha,
                                      post_width, post_height, is_post_circular,
                                      post_k)
        assign_materials(posts, POST_MAT)
        all_parts.extend(posts)

    # 4. Vertical minor posts (for vertical-post handrail type)
    if has_vertical_post:
        for alpha in handrail_alphas:
            minor_posts = make_vertical_minor_posts(
                n, step_l, step_h, step_w, alpha,
                post_minor_width, post_height, is_post_circular, post_k)
            assign_materials(minor_posts, POST_MAT)
            all_parts.extend(minor_posts)

    # 5. Horizontal bars (for horizontal-post handrail type)
    if has_bars:
        for alpha in handrail_alphas:
            bars = make_horizontal_bars(n, step_l, step_h, step_w, alpha,
                                        post_height, n_bars, bar_size,
                                        post_minor_width, post_k)
            assign_materials(bars, RAIL_MAT)
            all_parts.extend(bars)

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

    result.name = "CantileverStaircaseFactory"
    # [auto-append] ensure material bound
    if result is not None:
        if len(result.data.materials) == 0:
            result.data.materials.append(ELEM_MAT)
        elif result.data.materials[0] is None:
            result.data.materials[0] = ELEM_MAT
    return result

build_cantilever_stair()

