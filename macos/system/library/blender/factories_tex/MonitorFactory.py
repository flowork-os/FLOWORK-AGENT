# [FL_INDEX: keywords="blender_factory, procedural_3d, MonitorFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MonitorFactory | Category: factories_tex
# Prompt: A 3D model of a flat-panel computer monitor displayed at a slight angle. The monitor has a thin rectangular screen with a slim dark metallic bezel, showing abstract pink and rose-toned artwork on the display. It is mounted on a slim central pedestal arm connected to a wide rectangular dark base stand, with clean modern proportions typical of a desktop LCD monitor.

import os, math
import bpy, bmesh
import numpy as np
import random, colorsys

def log_uniform(lo, hi):
    return np.exp(np.random.uniform(np.log(lo), np.log(hi)))

def read_co(o):
    a = np.zeros(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)

def write_co(o, a):
    o.data.vertices.foreach_set("co", np.asarray(a).reshape(-1))

class VM:
    def __init__(self, o, m): self.o, self.m = o, m
    def __enter__(self):
        self.pa = bpy.context.active_object
        bpy.context.view_layer.objects.active = self.o
        self.pm = bpy.context.object.mode
        bpy.ops.object.mode_set(mode=self.m)
    def __exit__(self, *_):
        bpy.context.view_layer.objects.active = self.o
        bpy.ops.object.mode_set(mode=self.pm)
        if self.pa: bpy.context.view_layer.objects.active = self.pa

def sel_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def set_active(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)

def apply_tf(o, loc=False, rot=True, scale=True):
    sel_none(); set_active(o)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    sel_none()

def mod(o, t, **kw):
    m = o.modifiers.new(t, t)
    for k, v in kw.items():
        setattr(m, k, v)
    sel_none(); set_active(o)
    bpy.ops.object.modifier_apply(modifier=m.name)
    sel_none()
    return o

def bool_diff(o, cutter):
    m = o.modifiers.new("BOOLEAN", "BOOLEAN")
    m.object = cutter
    m.operation = "DIFFERENCE"
    if hasattr(m, "use_hole_tolerant"):
        m.use_hole_tolerant = True
    sel_none(); set_active(o)
    bpy.ops.object.modifier_apply(modifier=m.name)
    sel_none()
    return o

def join(objs):
    objs = [o for o in objs if o is not None]
    if len(objs) == 1:
        return objs[0]
    sel_none()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    sel_none()
    return o

def clone(o):
    n = o.copy(); n.data = o.data.copy()
    for m in list(n.modifiers):
        n.modifiers.remove(m)
    while n.data.materials:
        n.data.materials.pop()
    bpy.context.collection.objects.link(n)
    return n

def delete(objs):
    if not isinstance(objs, (list, tuple, set)):
        objs = [objs]
    for o in objs:
        if o and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)

def new_cube():
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    return bpy.context.active_object

def new_plane():
    bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
    o = bpy.context.active_object
    apply_tf(o, loc=True)
    return o

def data2mesh(vertices=(), edges=(), faces=(), name=""):
    me = bpy.data.meshes.new(name)
    me.from_pydata(vertices, edges, faces)
    me.update()
    return me

def mesh2obj(me):
    o = bpy.data.objects.new(me.name or "obj", me)
    bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    return o

def mirror_x(o):
    o.scale[0] *= -1
    apply_tf(o)
    with VM(o, "EDIT"):
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.flip_normals()
    return o

def tube_from_edges(vertices, edges, radius, res=16):
    o = mesh2obj(data2mesh(vertices, edges, name="leg_skel"))
    sel_none(); set_active(o)
    bpy.ops.object.convert(target="CURVE")
    c = bpy.context.active_object
    c.data.dimensions = "3D"
    c.data.bevel_depth = radius
    c.data.bevel_resolution = res
    c.data.use_fill_caps = True
    sel_none(); set_active(c)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.active_object

def H(p): return p["aspect_ratio"] * p["width"]
def TW(p): return p["width"] + 2 * p["side_margin"]
def TH(p): return H(p) + p["side_margin"] + p["bottom_margin"]

def int_hash(x):
    import hashlib
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)

def sample_params(seed=0):
    # ── TVFactory.__init__: FixedSeed(factory_seed) ──
    np.random.seed(seed)
    p = {
        "aspect_ratio": float(np.random.choice([9 / 16, 3 / 4])),
        "width": np.random.uniform(0.6, 2.1),
        "screen_bevel_width": np.random.uniform(0, 0.01),
        "side_margin": log_uniform(0.005, 0.01),
        "bottom_margin": np.random.uniform(0.005, 0.03),
        "depth": np.random.uniform(0.02, 0.04),
    }
    p["has_depth_extrude"] = bool(np.random.uniform() < 0.4)
    p["depth_extrude"] = (
        p["depth"] * np.random.uniform(2, 5) if p["has_depth_extrude"] else p["depth"] * 1.5
    )
    p["leg_type"] = str(np.random.choice(["two-legged", "single-legged"]))
    p["leg_length"] = np.random.uniform(0.1, 0.2)
    p["leg_length_y"] = np.random.uniform(0.1, 0.15)
    p["leg_radius"] = np.random.uniform(0.008, 0.015)
    p["leg_width"] = np.random.uniform(0.5, 0.8)
    p["leg_bevel_width"] = np.random.uniform(0.01, 0.02)
    # ── MonitorFactory.__init__: FixedSeed(factory_seed) ──
    np.random.seed(seed)
    p["width"] = float(log_uniform(0.4, 0.8))
    p["leg_type"] = "single-legged"

    # ── create_asset: FixedSeed(int_hash((factory_seed, 0))) ──
    np.random.seed(int_hash((seed, 0)))
    if p["has_depth_extrude"]:
        p["base_hmin_fac"] = np.random.uniform(0.1, 0.3)
        p["base_hmax_fac"] = np.random.uniform(0.5, 0.7)
        p["base_width_fac"] = np.random.uniform(0.3, 0.6)
        p["base_profile_fac"] = np.random.uniform(0.0, 0.4)
    p["single_leg_w_fac"] = np.random.uniform(0.05, 0.1)
    p["single_leg_h_fac"] = np.random.uniform(0.3, 0.5)
    p["single_base_w_fac"] = np.random.uniform(0.15, 0.3)
    return p

def make_base(p):
    o = new_cube()
    o.location = (0, 1, 1); apply_tf(o, loc=True)
    o.scale = (TW(p) / 2, p["depth"] / 2, TH(p) / 2); apply_tf(o)
    if p["screen_bevel_width"] > 1e-6:
        mod(o, "BEVEL", width=p["screen_bevel_width"], segments=8)
    if not p["has_depth_extrude"]:
        return o

    with VM(o, "EDIT"):
        bm = bmesh.from_edit_mesh(o.data)
        geom = [f for f in bm.faces if f.normal[1] > 0.5]
        bmesh.ops.delete(bm, geom=geom, context="FACES_KEEP_BOUNDARY")
        bmesh.update_edit_mesh(o.data)

    hmin = TH(p) * p["base_hmin_fac"]
    hmax = TH(p) * p["base_hmax_fac"]
    ext_w = TW(p) * p["base_width_fac"]
    extra = new_plane()
    extra.scale = (ext_w / 2, (hmax - hmin) / 2, 1)
    extra.rotation_euler[0] = -np.pi / 2
    extra.location = (0, p["depth_extrude"] + p["depth"], TH(p) / 2)
    o = join([o, extra])
    with VM(o, "EDIT"):
        bm = bmesh.from_edit_mesh(o.data); bm.edges.ensure_lookup_table()
        for e in bm.edges:
            e.select_set(e.is_boundary)
        bmesh.update_edit_mesh(o.data)
        bpy.ops.mesh.select_mode(type="EDGE")
        bpy.ops.mesh.bridge_edge_loops(number_cuts=32, profile_shape_factor=-p["base_profile_fac"])
    x, y, z = read_co(o).T
    z += ((hmax + hmin - TH(p)) / 2) * np.clip(y - p["depth"], 0, None) / p["depth_extrude"]
    write_co(o, np.stack([x, y, z], -1))
    return o

def make_screen(o, p):
    c = new_cube()
    c.location = (0, -1, 1); apply_tf(c, loc=True)
    c.scale = (p["width"] / 2, 1, H(p) / 2)
    c.location = (0, 1e-3, p["bottom_margin"]); apply_tf(c, loc=True)
    bool_diff(o, c)
    delete(c)

def add_two_legs(p):
    verts = [
        (-TW(p) / 2 * p["leg_width"] * p["leg_root_x_fac"], 0, TH(p) * p["leg_root_z_fac"]),
        (0, 0, -p["leg_length"]),
        (0, p["leg_length_y"] / 2, -p["leg_length"]),
        (0, -p["leg_length_y"] / 2, -p["leg_length"]),
    ]
    edges = [(0, 1), (1, 2), (1, 3)]
    leg = tube_from_edges(verts, edges, p["leg_radius"], 16)
    x, y, z = read_co(leg).T
    zmin = -p["leg_length"] - p["leg_radius"] * p["leg_floor_fac"]
    write_co(leg, np.stack([x, y, np.maximum(z, zmin)], -1))
    leg2 = clone(leg)
    leg_y = (1 - p["leg_width"]) * p["depth_extrude"]
    leg.location = (TW(p) / 2 * p["leg_width"], leg_y, 0)
    apply_tf(leg, loc=True)
    mirror_x(leg2)
    leg2.location = (-TW(p) / 2 * p["leg_width"], leg_y, 0)
    apply_tf(leg2, loc=True)
    return [leg, leg2]

def add_single_leg(p):
    leg_y = p["depth_extrude"] / 2
    leg = new_cube()
    leg.location = (0, 1, 1); apply_tf(leg, loc=True)
    leg.location = (0, leg_y, -p["leg_length"])
    leg.scale = (
        TW(p) * p["single_leg_w_fac"],
        p["leg_radius"],
        (p["leg_length"] + TH(p) * p["single_leg_h_fac"]) / 2,
    )
    apply_tf(leg, loc=True)
    mod(leg, "BEVEL", width=p["leg_bevel_width"], segments=8)

    base = new_cube()
    base.location = (0, leg_y, -p["leg_length"])
    base.scale = (TW(p) * p["single_base_w_fac"], p["leg_length_y"] / 2, p["leg_radius"])
    apply_tf(base, loc=True)
    mod(base, "BEVEL", width=p["leg_bevel_width"], segments=8)
    return [leg, base]

def assign_screen_material(o, p):
    """Assign MAT_SCREEN to screen-facing polygons (normal pointing -Y, within screen bounds)."""

    o.data.materials.append(MAT_SCREEN)
    screen_mat_idx = len(o.data.materials) - 1
    # Screen face: created by boolean cut, faces -Y direction, within screen width/height
    half_w = p["width"] / 2
    z_lo = p["bottom_margin"]
    z_hi = p["bottom_margin"] + H(p)
    for poly in o.data.polygons:
        if poly.normal[1] < -0.9:
            cx, cy, cz = poly.center
            if abs(cx) < half_w * 0.99 and z_lo < cz < z_hi:
                poly.material_index = screen_mat_idx

def build(seed=0):
    p = sample_params(seed)
    o = make_base(p)
    make_screen(o, p)
    o.data.materials.append(MAT_BODY)
    assign_screen_material(o, p)

    legs = add_two_legs(p) if p["leg_type"] == "two-legged" else add_single_leg(p)
    for leg_obj in legs:
        leg_obj.data.materials.append(MAT_LEG)

    o = join([o, *legs])
    o.rotation_euler[2] = np.pi / 2
    apply_tf(o)
    o.name = "Monitor"
    if WEAR_DO_SCRATCH:  apply_scratches(o)
    if WEAR_DO_EDGEWEAR: apply_edge_wear(o)
    return o

# Helpers
def seed_all(seed: int):
    """Seed numpy + python random. Call once before any geometry/material sampling."""

    np.random.seed(seed)
    random.seed(seed)

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def metal_hsv():
    """py:metal_hsv (simplified — drops natural-base lookup).

    Original: 20% chance returns metal_natural_hsv (sampled from a hex color list);
    80% returns (uniform(0,1), uniform(0.3,0.6), log_uniform(0.02,0.5)).
    We approximate metal_natural with a desaturated dark sample.
    """

    if np.random.uniform() < 0.2:
        return (np.random.uniform(0, 1),
                np.random.uniform(0.0, 0.2),
                log_uniform(0.05, 0.3))
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            log_uniform(0.02, 0.5))

def bark_hsv():
    """py:bark_hsv (uses a small hardcoded wood palette)."""

    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e", "#6b4423", "#5d4037", "#7b3f00"]
    h_str = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(h_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)

def weighted_sample(reg):
    """py:weighted_sample.

    `reg` is a list of (constructor_callable, weight) tuples.
    """

    classes, weights = zip(*reg)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]

def _new_material(name: str) -> bpy.types.Material:
    """Create a fresh material with empty node tree (BSDF removed)."""

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat

def _set_input(node, key, value):
    """Set an input socket value, preferring name lookup but falling back to index."""

    try:
        node.inputs[key].default_value = value
    except (KeyError, TypeError):
        if isinstance(key, int):
            raise
        # try common renames
        for alt in (key.replace(" IOR Level", ""), key + " IOR Level"):
            if alt in node.inputs:
                node.inputs[alt].default_value = value
                return
        raise

def _set_principled(bsdf, **kw):
    """Set Principled BSDF inputs with Blender-version-tolerant socket names."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
        "Sheen Tint": ("Sheen Tint",),
        "Subsurface Color": ("Subsurface Color",),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

def _build_float_curve(nt, value_socket, anchors):
    """Replica of NodeWrangler.build_float_curve — creates ShaderNodeFloatCurve."""

    fc = nt.nodes.new("ShaderNodeFloatCurve")
    fc.mapping.use_clip = False
    curve = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
        curve.points[i].handle_type = "VECTOR"
    fc.mapping.update()
    nt.links.new(value_socket, fc.inputs["Value"])
    return fc

def _noise_fac_output(noise_node):
    """Blender 5.0 renamed Fac→Factor on some nodes; fall back to first output."""

    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

# Base material constructors
def make_metal_basic(name="MetalBasic", color_hsv=None) -> bpy.types.Material:
    """py:shader_metal."""

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    fc = _build_float_curve(
        nt,
        _noise_fac_output(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0))},
        **{"Base Color": hsv2rgba(color_hsv or metal_hsv())},
    )
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_brushed_metal(name="BrushedMetal", base_color_hsv=None) -> bpy.types.Material:
    """py:shader_brushed_metal.

    Original chains 3 noise textures, mixes, mapranges and an HSV node. We use a
    simplified single-axis-stretched noise to fake the brushed look while keeping
    the math close to the original mapranges.
    """

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Stretched mapping in Z to simulate brush direction
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise2, "noise_dimensions"):
        try: noise2.noise_dimensions = "4D"
        except TypeError: pass
    noise2.inputs["Scale"].default_value = float(100.0)
    if "Detail" in noise2.inputs:    noise2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise2.inputs: noise2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise2.inputs:noise2.inputs["Distortion"].default_value = 0.1
    if "W" in noise2.inputs:         noise2.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(mapping_1.outputs["Vector"], noise2.inputs["Vector"])

    # Map range to brighten
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.4
    map_range.inputs[2].default_value = 0.6
    map_range.inputs[3].default_value = 0.8
    map_range.inputs[4].default_value = 1.2
    nt.links.new(_noise_fac_output(noise2), map_range.inputs[0])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    nt.links.new(map_range.outputs["Result"], hsv_node.inputs["Value"])

    # Roughness map range
    map_range_r = nt.nodes.new("ShaderNodeMapRange")
    map_range_r.inputs[1].default_value = 0.4
    map_range_r.inputs[2].default_value = 0.6
    map_range_r.inputs[3].default_value = 0.2
    map_range_r.inputs[4].default_value = 0.3
    nt.links.new(_noise_fac_output(noise2), map_range_r.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(map_range_r.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of materials/metal/galvanized_metal.py:shader_galvanized_metal.

    Uses Voronoi for the spangle pattern. Falls back to 3D Voronoi if 4D unsupported.
    """

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try: voronoi.voronoi_dimensions = "4D"
        except TypeError:
            voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "distance"):
        try: voronoi.distance = "MINKOWSKI"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 500.0
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[3].default_value = 0.1
    map_range.inputs[4].default_value = 0.5
    # Voronoi outputs may be named "Distance"/"Color"; default index 0 is fine
    nt.links.new(voronoi.outputs[0], map_range.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_grained_metal(name="GrainedMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of materials/metal/grained_and_polished_metal.py."""

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # Displacement chain
    mul1 = nt.nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul1.inputs[0])
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul2.inputs[0])
    nt.links.new(mul1.outputs[0], mul2.inputs[1])
    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    mul3.inputs[1].default_value = 0.01
    nt.links.new(mul2.outputs[0], mul3.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_hammered_metal(name="HammeredMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of materials/metal/hammered_metal.py — Voronoi smooth_f1 displacement."""

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "feature"):
        try: voronoi.feature = "SMOOTH_F1"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 300.0
    if "Smoothness" in voronoi.inputs:
        voronoi.inputs["Smoothness"].default_value = 0.2
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

    # Distance ** 2.5 * small_factor → displacement
    pow_node = nt.nodes.new("ShaderNodeMath")
    pow_node.operation = "POWER"
    pow_node.inputs[1].default_value = 2.5
    # Voronoi distance output may be named "Distance" — fall back to index 0
    dist_out = voronoi.outputs.get("Distance") or voronoi.outputs[0]
    nt.links.new(dist_out, pow_node.inputs[0])

    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = log_uniform(0.001, 0.003)
    nt.links.new(pow_node.outputs[0], mul.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv), "Roughness": 0.1},
    )
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_brushed_black_metal(name="BrushedBlackMetal") -> bpy.types.Material:
    """Re-impl of materials/metal/appliance.py:shader_brushed_black_metal.

    Original uses ShaderNodeBsdfAnisotropic. We use Principled BSDF with high
    anisotropic + dark color, since Anisotropic BSDF socket layout differs.
    """

    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        Roughness=0.4,
        Anisotropic=0.9,
        **{"Specular IOR Level": 0.5, "Base Color": (0.0167, 0.0167, 0.0167, 1.0)},
    )
    _connect_output(nt, bsdf)
    return mat

def make_white_metal(name="WhiteMetal") -> bpy.types.Material:
    """Re-impl of materials/metal/appliance.py:shader_white_metal."""

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 50.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 20.0
    if "Detail" in noise.inputs:    noise.inputs["Detail"].default_value = 20.0
    if "Distortion" in noise.inputs:noise.inputs["Distortion"].default_value = 1.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.25
    cr.color_ramp.elements[0].color = (0.5244, 0.5244, 0.5244, 1.0)
    cr.color_ramp.elements[1].position = 1.0
    cr.color_ramp.elements[1].color = (0.9698, 0.9698, 0.9698, 1.0)
    # ColorRamp Fac input
    cr_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(_noise_fac_output(noise), cr_in)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        Roughness=0.1,
        Anisotropic=0.9182,
        **{"Specular IOR Level": 1.0, "Sheen Weight": 0.0455},
    )
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf)
    return mat

def make_glass(name="Glass") -> bpy.types.Material:
    """Re-impl of materials/ceramic/glass.py:shader_glass (non-window variant)."""

    mat = _new_material(name)
    nt = mat.node_tree
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    if "Roughness" in glass.inputs:
        glass.inputs["Roughness"].default_value = 0.02
    if "IOR" in glass.inputs:
        glass.inputs["IOR"].default_value = 1.5
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0
        if "Transmission Weight" in glass.inputs:
            glass.inputs["Transmission Weight"].default_value = 1.0
        elif "Transmission" in glass.inputs:
            glass.inputs["Transmission"].default_value = 1.0
    # Tint via 50/50 white-or-light-color
    if np.random.uniform() < 0.5:
        color = (1.0, 1.0, 1.0, 1.0)
    else:
        color = hsv2rgba((np.random.uniform(0, 1), np.random.uniform(0.05, 0.25), 1.0))
    if "Color" in glass.inputs:
        glass.inputs["Base Color"].default_value = color
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(glass.outputs[0], out.inputs["Surface"])
    return mat

def make_black_glass(name="BlackGlass") -> bpy.types.Material:
    """Re-impl of materials/metal/appliance.py:shader_black_glass — GlossyBSDF dark."""

    mat = _new_material(name)
    nt = mat.node_tree
    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    if "Color" in glossy.inputs:
        glossy.inputs["Color"].default_value = (0.0068, 0.0068, 0.0068, 1.0)
    if "Roughness" in glossy.inputs:
        glossy.inputs["Roughness"].default_value = 0.2
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(glossy.outputs[0], out.inputs["Surface"])
    return mat

def make_plastic_rough(name="PlasticRough", base_color=None) -> bpy.types.Material:
    """Re-impl of materials/plastic/plastic_rough.py:shader_rough_plastic."""

    if base_color is None:
        base_color = hsv2rgba((np.random.uniform(0, 1),
                               np.random.uniform(0.5, 0.8),
                               log_uniform(0.01, 0.5)))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # Tiny displacement
    mul1 = nt.nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul1.inputs[0])
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul2.inputs[0])
    nt.links.new(mul1.outputs[0], mul2.inputs[1])
    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    mul3.inputs[1].default_value = 0.003
    nt.links.new(mul2.outputs[0], mul3.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_wood(name="Wood", color=None) -> bpy.types.Material:
    """Simplified re-impl of materials/wood/wood.py:shader_wood.

    Original uses MusgraveTexture (REMOVED in Blender 5.0) for the wood grain.
    We substitute multi-octave NoiseTexture in stretched mapping to fake the
    grain look. Visually approximate, NOT pixel-identical to original.
    """

    if color is None:
        color = hsv2rgba(bark_hsv())
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Stretched mapping to make wood grain anisotropic
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 10.0
    if "Detail" in grain.inputs:     grain.inputs["Detail"].default_value = 15.0
    if "Distortion" in grain.inputs: grain.inputs["Distortion"].default_value = 0.5
    nt.links.new(mapping.outputs["Vector"], grain.inputs["Vector"])

    # Color mix: dark grain over base color
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    # Mix node — Blender 5.0 uses ShaderNodeMix with data_type RGBA
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    # On RGBA mix: inputs[0]=Factor, inputs[6]=A_Color, inputs[7]=B_Color, outputs[2]=Result
    nt.links.new(_noise_fac_output(grain), mix.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix.inputs[6])  # A: dark grain color
    mix.inputs[7].default_value = color                     # B: base color

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=float(np.random.uniform(0.4, 0.7)),
                    **{"Coat Weight": 0.2})
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf)
    return mat

def make_screen_emissive(name="Screen") -> bpy.types.Material:
    """Substitute for the complex `text.Text` shader used by TV/Monitor screens.

    Picks a random tinted dark base + low-level emission so the screen reads as
    "powered on but display content not modeled".
    """

    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    base = hsv2rgba((np.random.uniform(0, 1),
                     np.random.uniform(0.2, 0.6),
                     np.random.uniform(0.05, 0.2)))
    _set_principled(bsdf, **{"Base Color": base, "Roughness": 0.2, "Metallic": 0.0})
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = base
    elif "Emission" in bsdf.inputs:
        bsdf.inputs["Emission"].default_value = base
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = float(np.random.uniform(1.5, 3.0))
    _connect_output(nt, bsdf)
    return mat

metals = [
    (make_metal_basic, 3.0),
    (make_brushed_metal, 2.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 0.7),
    (make_brushed_black_metal, 0.3),
]

metal_neutral = [
    (make_metal_basic, 1.0),
]

appliance_front_maybeglass = metals + [
    (make_black_glass, 4.0),
    (make_glass, 10.0),
]

appliance_front_glass = [
    (make_black_glass, 2.0),
    (make_glass, 10.0),
]

appliance_handle = metals + [
    (make_plastic_rough, 1.0),
    (make_wood, 3.0),
    (make_white_metal, 2.0),
]

graphicdesign = [
    (make_screen_emissive, 1.0),
]

REGISTRY = {
    "metals": metals,
    "metal_neutral": metal_neutral,
    "appliance_front_maybeglass": appliance_front_maybeglass,
    "appliance_front_glass": appliance_front_glass,
    "appliance_handle": appliance_handle,
    "graphicdesign": graphicdesign,
}

def get_material(registry_key: str, name: str = None) -> bpy.types.Material:
    """Pick a constructor via weighted_sample (uses current numpy.random state)."""

    ctor = weighted_sample(REGISTRY[registry_key])
    return ctor(name=name or registry_key.title())

# wear_tear post-processing
# Faithful raw-bpy translations of:
# Both follow the same pattern: walk obj.data.materials, find existing
# MaterialOutput / BSDF, inject a procedural wear graph, reconnect.
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"

def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)

def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    if in0 is not None:
        if hasattr(in0, "default_value") or hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "default_value") or hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    return n

def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    if in0 is not None:
        if hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    if scale is not None:
        # SCALE op uses inputs[3] (Scale) on VectorMath
        for inp in n.inputs:
            if inp.name == "Scale":
                inp.default_value = scale
                break
    return n

def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = value
    return n

def _color_ramp(nt, fac_socket, stops):
    """stops = [(position, (r,g,b,a)), ...]"""

    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(fac_socket, fac_in)
    elements = cr.color_ramp.elements
    for i, (pos, color) in enumerate(stops):
        if i < len(elements):
            elements[i].position = pos
            elements[i].color = color
        else:
            e = elements.new(pos)
            e.color = color
    return cr

def _noise_tex(nt, vector_socket, scale, detail=2.0, distortion=0.0, roughness=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_socket is not None:
        nt.links.new(vector_socket, n.inputs["Vector"])
    if isinstance(scale, (int, float)):
        n.inputs["Scale"].default_value = float(scale)
    else:
        nt.links.new(scale, n.inputs["Scale"])
    if "Detail" in n.inputs:
        n.inputs["Detail"].default_value = detail
    if "Distortion" in n.inputs:
        n.inputs["Distortion"].default_value = distortion
    if "Roughness" in n.inputs:
        n.inputs["Roughness"].default_value = roughness
    return n

def get_scratch_params():
    """Replica of wear_tear/scratches.py:get_scratch_params."""

    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=log_uniform(5, 80),
        scratch_mask_ratio=log_uniform(0.01, 0.9),
        scratch_mask_noise=log_uniform(5, 40),
        scratch_depth=log_uniform(0.1, 1.0),
    )

def _build_scratch_graph(nt, params):
    """Build the scratch displacement node graph and return the Displacement output socket.

    Faithful translation of wear_tear/scratches.py:scratch_shader.
    """

    n_angle1 = _value_node(nt, params["angle1"])
    n_angle2 = _value_node(nt, params["angle2"])
    n_scale = _value_node(nt, params["scratch_scale"])
    n_mask_ratio = _value_node(nt, params["scratch_mask_ratio"])
    n_mask_noise = _value_node(nt, params["scratch_mask_noise"])
    n_depth = _value_node(nt, params["scratch_depth"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # First scratch direction
    cxyz1 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle1.outputs[0], cxyz1.inputs["Y"])
    map1 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map1, "vector_type"):
        try: map1.vector_type = "TEXTURE"
        except TypeError: pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    # Second scratch direction
    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map2, "vector_type"):
        try: map2.vector_type = "TEXTURE"
        except TypeError: pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    # Mask noise
    map3 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map3, "vector_type"):
        try: map3.vector_type = "TEXTURE"
        except TypeError: pass
    map3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.1920)
    nt.links.new(tex_coord.outputs["Object"], map3.inputs["Vector"])
    noise3 = _noise_tex(nt, map3.outputs["Vector"], n_mask_noise.outputs[0], detail=1.0)
    cr_mask = _color_ramp(nt, _noise_fac_output(noise3),
                          [(0.4109, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))])
    mul_mask = _math(nt, "MULTIPLY", n_mask_ratio.outputs[0], cr_mask.outputs["Color"])
    add_combined = _math(nt, "ADD", add.outputs[0], mul_mask.outputs[0], clamp=True)

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.7
    map_range.inputs[2].default_value = 0.72
    map_range.inputs[4].default_value = 0.9
    nt.links.new(add_combined.outputs[0], map_range.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(map_range.outputs["Result"], disp.inputs["Height"])
    nt.links.new(n_depth.outputs[0], disp.inputs["Scale"])

    return disp.outputs[0]

def apply_scratches(obj, **params):
    """Faithful raw-bpy port of wear_tear/scratches.py:Scratches.apply_over."""

    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_scratch_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == SCRATCH_LABEL for n in nt.nodes):
            continue   # idempotency: already applied
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        try:
            disp_out = _build_scratch_graph(nt, params)
            nt.links.new(disp_out, mat_out.inputs["Displacement"])
            # Mark idempotency
            disp_out.node.label = SCRATCH_LABEL
        except Exception as e:
            print(f"  [scratches] failed on {mat.name}: {type(e).__name__}: {e}")

def get_edge_wear_params():
    """Replica of wear_tear/edge_wear.py:get_edge_wear_params."""

    return dict(
        worn_off_opacity=float(np.random.uniform(0, 0.01)),
        worn_off_radius=float(np.random.uniform(0.005, 0.01)),
        scratch_radius=float(np.random.uniform(0.01, 0.03)),
        worn_off_mask_randomness=float(np.random.uniform(2.5, 3.0)),
        edge_base_color_hue=float(np.random.uniform(0.0, 1.0)),
        edge_base_color_whiteness=float(np.random.uniform(0.1, 0.6)),
        scratch_mask_randomness=float(np.random.choice(
            [np.random.uniform(0.1, 5.0), np.random.uniform(1.0, 10.0)])),
        scratch_density=float(np.random.uniform(1.5, 10.0)),
        scratch_opacity=float(np.random.uniform(0.5, 1.0)),
    )

def _build_edge_wear_graph(nt, original_bsdf_node, original_displacement_node, params):
    """Faithful raw-bpy port of edge_wear.py:shader_edge_tear_free_node_group.

    Returns (final_bsdf_socket, final_displacement_socket).
    """

    p = params
    n_scratch_opacity = _value_node(nt, p["scratch_opacity"])
    n_scratch_mask_randomness = _value_node(nt, p["scratch_mask_randomness"])
    n_scratch_radius = _value_node(nt, p["scratch_radius"])
    n_worn_opacity = _value_node(nt, p["worn_off_opacity"])
    n_worn_radius = _value_node(nt, p["worn_off_radius"])
    n_worn_mask_randomness = _value_node(nt, p["worn_off_mask_randomness"])
    n_edge_whiteness = _value_node(nt, p["edge_base_color_whiteness"])
    n_edge_hue = _value_node(nt, p["edge_base_color_hue"])
    n_scratch_density = _value_node(nt, p["scratch_density"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    # Scratch mask noise
    noise_a = _noise_tex(nt, mapping.outputs["Vector"], n_scratch_mask_randomness.outputs[0], detail=1.0)
    cr_a = _color_ramp(nt, _noise_fac_output(noise_a),
                       [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    # Bevel edge detection (scratch radius)
    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.samples = 20
    nt.links.new(n_scratch_radius.outputs[0], bevel.inputs["Radius"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub = _vmath(nt, "SUBTRACT", bevel.outputs[0], geo.outputs["Normal"])
    abs_a = _math(nt, "ABSOLUTE", sub.outputs["Vector"])
    cr_b = _color_ramp(nt, abs_a.outputs[0],
                       [(0.0691, (0, 0, 0, 1)), (0.1564, (1, 1, 1, 1))])

    mul_a = _math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"], clamp=True)
    mul_a1 = _math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0], clamp=True)

    # Bevel edge detection (worn-off radius)
    bevel2 = nt.nodes.new("ShaderNodeBevel")
    bevel2.samples = 20
    nt.links.new(n_worn_radius.outputs[0], bevel2.inputs["Radius"])
    sub2 = _vmath(nt, "SUBTRACT", bevel2.outputs[0], geo.outputs["Normal"])
    abs_b = _math(nt, "ABSOLUTE", sub2.outputs["Vector"])

    noise_b = _noise_tex(nt, mapping.outputs["Vector"], n_worn_mask_randomness.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac_output(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
    cr_d = _color_ramp(nt, mul_b1.outputs[0],
                       [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])

    # Edge color HSV
    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    if hasattr(combine_color, "mode"):
        try: combine_color.mode = "HSV"
        except TypeError: pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_result"):
        try: mix.clamp_result = True
        except TypeError: pass
    if hasattr(mix, "clamp_factor"):
        try: mix.clamp_factor = False
        except TypeError: pass
    nt.links.new(n_edge_whiteness.outputs[0], mix.inputs[0])
    nt.links.new(combine_color.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

    # Worn-edge BSDFs (Principled)
    bsdf_worn1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn1.inputs["Base Color"])
    _set_principled(bsdf_worn1, Metallic=0.3745, Roughness=0.1436,
                    **{"Specular IOR Level": 0.0})

    # Mix the original BSDF with the worn version
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cr_d.outputs["Color"], mix_shader.inputs["Fac"])
    nt.links.new(original_bsdf_node.outputs[0], mix_shader.inputs[1])
    nt.links.new(bsdf_worn1.outputs[0], mix_shader.inputs[2])

    # Scratch density via voronoi distance-to-edge (two perpendicular)
    map_h = nt.nodes.new("ShaderNodeMapping")
    map_h.inputs["Scale"].default_value = (10.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_h.inputs["Vector"])
    vor_h = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_h, "feature"):
        try: vor_h.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])

    # Scale density by 2 for vertical
    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_v, "feature"):
        try: vor_v.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_v.outputs["Vector"], vor_v.inputs["Vector"])
    nt.links.new(scale_v.outputs[0], vor_v.inputs["Scale"])

    dist_h = vor_h.outputs.get("Distance") or vor_h.outputs[0]
    dist_v = vor_v.outputs.get("Distance") or vor_v.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_e = _color_ramp(nt, mul_dist.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_e = _math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"], clamp=True)
    mul_f = _math(nt, "MULTIPLY", mul_a.outputs[0], mul_e.outputs[0], clamp=True)

    bsdf_worn2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn2.inputs["Base Color"])
    _set_principled(bsdf_worn2, Metallic=0.3855, Roughness=0.0,
                    **{"Specular IOR Level": 0.0})

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_a1.outputs[0], mix_shader_2.inputs["Fac"])
    nt.links.new(mix_shader.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(bsdf_worn2.outputs[0], mix_shader_2.inputs[2])

    # Displacement
    scale_disp = _vmath(nt, "SCALE", in0=mul_f.outputs[0], scale=2.0)
    if original_displacement_node is None:
        total_displacement = scale_disp.outputs[0]
    else:
        add_disp = _math(nt, "ADD", original_displacement_node.outputs[0],
                         scale_disp.outputs[0], clamp=True)
        total_displacement = add_disp.outputs[0]

    return mix_shader_2.outputs[0], total_displacement

def apply_edge_wear(obj, **params):
    """Faithful raw-bpy port of wear_tear/edge_wear.py:EdgeWear.apply_over."""

    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_edge_wear_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == EDGE_WEAR_LABEL for n in nt.nodes):
            continue   # idempotency
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        # Find original BSDF feeding Surface
        surface_links = mat_out.inputs["Surface"].links
        if not surface_links:
            continue
        original_bsdf = surface_links[0].from_node
        # Find original displacement (if any)
        disp_links = mat_out.inputs["Displacement"].links
        original_disp = disp_links[0].from_node if disp_links else None
        try:
            final_bsdf_socket, final_disp_socket = _build_edge_wear_graph(
                nt, original_bsdf, original_disp, params)
            # Reconnect
            nt.links.new(final_bsdf_socket, mat_out.inputs["Surface"])
            nt.links.new(final_disp_socket, mat_out.inputs["Displacement"])
            # Mark idempotency on the new mix_shader
            final_bsdf_socket.node.label = EDGE_WEAR_LABEL
        except Exception as e:
            print(f"  [edge_wear] failed on {mat.name}: {type(e).__name__}: {e}")

def apply_wear_tear(obj):
    """

    Two independent 50% probability gates: scratches and edge_wear.
    """

    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    scratch_p, edge_p = WEAR_TEAR_PROB
    if np.random.uniform() <= scratch_p:
        apply_scratches(obj)
    if np.random.uniform() <= edge_p:
        apply_edge_wear(obj)

SEED = int(os.environ.get('SEED', 0))

# ----------------------------------------------------------------------------
# geometry which uses int_hash((factory_seed, i)) in create_asset. We mirror this
# by sampling all materials + wear_tear gates on a clean seed_all(SEED) state here,
# then hand off to build() which re-seeds internally for geometry.
seed_all(SEED)
MAT_BODY       = get_material('metal_neutral', 'Surface')
MAT_LEG        = get_material('metal_neutral', 'SupportSurface')
MAT_SCREEN     = get_material('graphicdesign', 'ScreenSurface')
# wear_tear probability gates (50/50 each, mirroring factory.get_material_params)
_scratch_p, _edge_wear_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

build(SEED)

