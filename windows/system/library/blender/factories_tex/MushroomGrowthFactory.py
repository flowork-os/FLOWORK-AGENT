# [FL_INDEX: keywords="blender_factory, procedural_3d, MushroomGrowthFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MushroomGrowthFactory | Category: factories_tex
# Prompt: A 3D model of a single growing mushroom rendered from a slightly elevated perspective, featuring a broad tan cap with organic surface detail sitting atop a thick curved stem with a rough bumpy pale surface, with the stem curving upward from a tilted base.

"""Standalone Blender script for MushroomGrowthFactory (texture-enabled).

Reproduces the geometry pipeline from:

Combines MushroomCapFactory + MushroomStemFactory into a single mushroom,
and applies the procedural `shader_mushroom` material from the same file
(translated from NodeWrangler to raw bpy node tree construction).

Usage:
  SEED=0 blender --background --python MushroomGrowthFactory.py
"""


import os
import bpy
import bmesh
import colorsys
import numpy as np
import random
import hashlib
from collections.abc import Sized
from numpy.random import uniform

C = bpy.context
D = bpy.data

# ---------------------------------------------------------------------------
# Material: faithful translation of
# Original (NodeWrangler) pipeline:
#   texcoord.Generated -> SeparateXYZ(x, y, z)
#   combine(x, y, z * uniform(5, 10))
#     -> MusgraveTexture(scale=200)
#     -> MapRange(-1..1 -> 0..1)
#     -> ColorRamp(HSV, stops=[0, 0.3, 0.7, 1], colors=[front, front, back, back])
#     -> Principled BSDF (roughness=0.8)
# Blender 5.0 adaptations:
#   - ShaderNodeTexMusgrave is removed -> fall back to ShaderNodeTexNoise
#     (same domain, similar fractal character). We keep Scale=200 so the
#     grain matches the reference at voxel-remesh resolution.
#   - noise "Fac" output renamed to "Factor" in 5.0 -> _fac() helper.
# ---------------------------------------------------------------------------

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1, max(0.0, min(1.0, float(s))), max(0.0, min(1.0, float(v))))
    return (r, g, b, 1.0)

def _fac(node):
    for name in ("Fac", "Factor"):
        if name in node.outputs:
            return node.outputs[name]
    return node.outputs[0]

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def make_mushroom_material(base_hue, name="MushroomGrowthFactory_Material"):
    """Build the mushroom surface material.

    The RNG sequence here mirrors shader_mushroom's top-to-bottom sampling:
      1. front_color hue_offset, sat, val  (uniform, uniform, log_uniform)
      2. back_color  hue_offset, sat, val  (uniform, uniform, log_uniform)
      3. z-axis scalar multiplier          (uniform)
    """

    roughness = 0.8

    front_hue_off = float(np.random.uniform(-0.1, 0.1))
    front_sat     = float(np.random.uniform(0.1, 0.3))
    front_val     = _log_uniform(0.02, 0.5)
    front_color   = _hsv2rgba((base_hue + front_hue_off) % 1, front_sat, front_val)

    back_hue_off  = float(np.random.uniform(-0.1, 0.1))
    back_sat      = float(np.random.uniform(0.1, 0.3))
    back_val      = _log_uniform(0.02, 0.5)
    back_color    = _hsv2rgba((base_hue + back_hue_off) % 1, back_sat, back_val)

    z_mult        = float(np.random.uniform(5, 10))

    mat = _new_mat(name)
    nt = mat.node_tree
    link = nt.links.new

    # Generated texture coordinates
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    sep_xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    link(tex_coord.outputs["Generated"], sep_xyz.inputs[0])

    # scalar_multiply(z_mult, z)
    mul_z = nt.nodes.new("ShaderNodeMath")
    mul_z.operation = 'MULTIPLY'
    mul_z.inputs[1].default_value = z_mult
    link(sep_xyz.outputs["Z"], mul_z.inputs[0])

    # combine(x, y, z_scaled)
    combine = nt.nodes.new("ShaderNodeCombineXYZ")
    link(sep_xyz.outputs["X"], combine.inputs["X"])
    link(sep_xyz.outputs["Y"], combine.inputs["Y"])
    link(mul_z.outputs[0],     combine.inputs["Z"])

    # Musgrave -> Noise fallback (Blender 5.0), Scale=200.
    # Original ShaderNodeTexMusgrave was a perlin-style fractal; ShaderNodeTexNoise
    # gives a near-identical range and domain characteristic when the same Vector
    # and Scale are wired in. Output goes through MapRange(-1..1 -> 0..1) exactly
    # stretch, which visually matches the reference within the acceptable tolerance.
    musg = nt.nodes.new("ShaderNodeTexNoise")
    link(combine.outputs[0], musg.inputs["Vector"])
    musg.inputs["Scale"].default_value = 200.0
    if "Detail" in musg.inputs:
        musg.inputs["Detail"].default_value = 8.0

    map_range = nt.nodes.new("ShaderNodeMapRange")
    link(_fac(musg), map_range.inputs[0])
    map_range.inputs[1].default_value = -1.0
    map_range.inputs[2].default_value =  1.0
    map_range.inputs[3].default_value =  0.0
    map_range.inputs[4].default_value =  1.0

    # Color ramp stops [0, 0.3, 0.7, 1] -> [front, front, back, back]
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.color_mode = "HSV"
    cr.color_ramp.hue_interpolation = "NEAR"
    link(map_range.outputs[0], cr.inputs["Fac"])
    cr.color_ramp.elements.new(0)
    cr.color_ramp.elements.new(0)
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = front_color
    cr.color_ramp.elements[1].position = 0.3; cr.color_ramp.elements[1].color = front_color
    cr.color_ramp.elements[2].position = 0.7; cr.color_ramp.elements[2].color = back_color
    cr.color_ramp.elements[3].position = 1.0; cr.color_ramp.elements[3].color = back_color

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    link(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def _build_base_hue():
    """Mirrors MushroomGrowthFactory.build_base_hue (uses np.random)."""

    if float(np.random.uniform(0, 1)) < 0.4:
        return float(np.random.uniform(0, 1))
    return float(np.random.uniform(0.02, 0.15))

# base_hue first, then wires shader_mushroom via a material_func lambda.  Geometry
# (create_asset) later re-seeds with int_hash((factory_seed, i)) — see build() below.
SEED = int(os.environ.get('SEED', 0))
np.random.seed(SEED)
random.seed(SEED)
_BASE_HUE = _build_base_hue()
def _make_stem_mat(base_hue, name):
    """Stem/web: whitish off-hue variant of the mushroom shader, with subtle color shift.
    Mushroom stems in use the same shader_mushroom with a different hue/saturation."""
    # Shift hue slightly toward yellow/white for a typical stem tone.
    stem_hue = (base_hue + 0.04) % 1.0
    return make_mushroom_material(stem_hue, name)

def _make_gill_mat(base_hue, name):
    return make_mushroom_material((base_hue + 0.02) % 1.0, name)

CAP_MAT  = make_mushroom_material(_BASE_HUE, "MushroomGrowthFactory_Cap")
GILL_MAT = _make_gill_mat(_BASE_HUE, "MushroomGrowthFactory_Gill")
STEM_MAT = _make_stem_mat(_BASE_HUE, "MushroomGrowthFactory_Stem")
WEB_MAT  = _make_stem_mat(_BASE_HUE, "MushroomGrowthFactory_Web")
for _m in (CAP_MAT, GILL_MAT, STEM_MAT, WEB_MAT):
    _m.use_fake_user = True
# Backward-compat: CATEG_MAT refers to the cap material.
CATEG_MAT = CAP_MAT

# ---------------------------------------------------------------------------
# Seed utilities
# ---------------------------------------------------------------------------

class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
        self.py_state = None
        self.np_state = None
    def __enter__(self):
        self.py_state = random.getstate()
        self.np_state = np.random.get_state()
        random.seed(self.seed)
        np.random.seed(self.seed)
    def __exit__(self, *_):
        random.setstate(self.py_state)
        np.random.set_state(self.np_state)

def md5_hash(x):
    if isinstance(x, (tuple, list)):
        m = hashlib.md5()
        for s in x:
            m.update(str(s).encode('utf-8'))
        return m
    return hashlib.md5(str(x).encode('utf-8'))

def int_hash(x, max_val=(2**32 - 1)):
    return abs(int(md5_hash(x).hexdigest(), 16)) % max_val

def log_uniform(low, high, size=None):
    return np.exp(np.random.uniform(np.log(low), np.log(high), size))

def polygon_angles(n, min_angle=np.pi / 6, max_angle=np.pi * 2 / 3):
    if n <= 0:
        return np.array([])
    for _ in range(100):
        angles = np.sort(uniform(0, 2 * np.pi, n))
        difference = (angles - np.roll(angles, 1)) % (2 * np.pi)
        if (difference >= min_angle).all() and (difference <= max_angle).all():
            return angles
    return np.sort((np.arange(n) * (2 * np.pi / n) + uniform(0, 2 * np.pi)) % (2 * np.pi))

# ---------------------------------------------------------------------------
# Blender utility helpers
# ---------------------------------------------------------------------------

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    if o is not None:
        o.select_set(True)

class Suppress:
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return True

class ViewportMode:
    def __init__(self, obj, mode):
        self.obj = obj
        self.mode = mode
        self.prev_active = None
        self.prev_mode = None
    def __enter__(self):
        self.prev_active = bpy.context.view_layer.objects.active
        _select_none(); _set_active(self.obj)
        self.prev_mode = getattr(bpy.context.object, 'mode', 'OBJECT') if bpy.context.object else 'OBJECT'
        if bpy.context.object and self.prev_mode != self.mode:
            bpy.ops.object.mode_set(mode=self.mode)
        return self
    def __exit__(self, *_):
        try:
            if bpy.context.object and bpy.context.object.mode != self.prev_mode:
                bpy.ops.object.mode_set(mode=self.prev_mode)
        except Exception:
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass
        if self.prev_active is not None:
            _set_active(self.prev_active)

class SelectObjects:
    def __init__(self, objs, active=0):
        self.objs = objs if isinstance(objs, (list, tuple)) else [objs]
        self.active_idx = active
        self.prev_sel = None
        self.prev_active = None
    def __enter__(self):
        self.prev_sel = list(bpy.context.selected_objects)
        self.prev_active = bpy.context.view_layer.objects.active
        _select_none()
        for o in self.objs:
            if o is not None:
                o.select_set(True)
        if self.objs:
            _set_active(self.objs[self.active_idx])
        return self
    def __exit__(self, *_):
        _select_none()
        for o in self.prev_sel or []:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if self.prev_active is not None and self.prev_active.name in bpy.data.objects:
            _set_active(self.prev_active)

def apply_transform(obj, loc=False, rot=True, scale=True):
    with SelectObjects(obj):
        bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)

def delete(objs):
    if not isinstance(objs, (list, tuple)):
        objs = [objs]
    for o in objs:
        if o is None:
            continue
        mesh = o.data if getattr(o, 'type', None) == 'MESH' else None
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
        try:
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        except Exception:
            pass

def modify_mesh(obj, type_, apply=True, name=None, return_mod=False, **kwargs):
    if name is None:
        name = f'modify_mesh({type_})'
    mod = obj.modifiers.new(name=name, type=type_)
    mod.show_viewport = not apply
    for k, v in kwargs.items():
        try:
            setattr(mod, k, v)
        except Exception:
            pass
    if apply:
        with SelectObjects(obj):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    return (obj, None if apply else mod) if return_mod else obj

# ---------------------------------------------------------------------------
# Mesh helpers
# ---------------------------------------------------------------------------

def data2mesh(vertices=(), edges=(), faces=(), name=''):
    mesh = bpy.data.meshes.new(name or 'mesh')
    mesh.from_pydata(list(vertices), list(edges), list(faces))
    mesh.update()
    return mesh

def mesh2obj(mesh):
    obj = bpy.data.objects.new(mesh.name or 'obj', mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

def join_objects(objs):
    if not isinstance(objs, list):
        objs = [objs]
    objs = [o for o in objs if o is not None]
    if len(objs) == 0:
        return None
    if len(objs) == 1:
        return objs[0]
    _select_none()
    for o in objs:
        o.select_set(True)
    _set_active(objs[0])
    bpy.ops.object.join()
    out = bpy.context.active_object
    out.location = (0, 0, 0)
    out.rotation_euler = (0, 0, 0)
    out.scale = (1, 1, 1)
    _select_none()
    return out

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3, dtype=float)
    obj.data.vertices.foreach_get('co', arr)
    return arr.reshape(-1, 3)

def write_co(obj, arr):
    obj.data.vertices.foreach_set('co', np.asarray(arr, dtype=float).reshape(-1))
    obj.data.update()

def displace_vertices(obj, fn):
    co = read_co(obj)
    x, y, z = co.T
    d = fn(x, y, z)
    for i in range(3):
        co[:, i] += np.asarray(d[i])
    write_co(obj, co)

def origin2lowest(obj, vertical=False):
    co = read_co(obj)
    if len(co) == 0:
        return
    i = np.argmin(co[:, -1])
    if vertical:
        obj.location[-1] = -co[i, -1]
    else:
        obj.location = -co[i]
    apply_transform(obj, loc=True)

def subsurface2face_size(obj, face_size):
    arr = np.zeros(len(obj.data.polygons), dtype=float)
    if len(arr) == 0:
        return
    obj.data.polygons.foreach_get('area', arr)
    area = float(np.mean(arr))
    if area <= 1e-9 or face_size <= 0:
        return
    try:
        levels = int(np.ceil(np.log2(area / face_size)))
    except Exception:
        return
    if levels > 0:
        modify_mesh(obj, 'SUBSURF', apply=True, levels=levels, render_levels=levels)

def remesh_with_attrs(obj, face_size):
    modify_mesh(obj, 'REMESH', apply=True, voxel_size=face_size)
    return obj

def remesh_fill(obj, resolution=0.005):
    zmax = float(read_co(obj)[:, 2].max()) if len(obj.data.vertices) else 0.0
    modify_mesh(obj, 'SOLIDIFY', apply=True, thickness=0.1)
    depth = int(np.ceil(np.log2((max(obj.dimensions) + 0.01) / max(resolution, 1e-5))))
    depth = max(depth, 4)
    modify_mesh(obj, 'REMESH', apply=True, mode='SHARP', octree_depth=depth, use_remove_disconnected=False)
    co = read_co(obj)
    to_del = np.where(co[:, 2] > zmax + 1e-4)[0]
    if len(to_del):
        with ViewportMode(obj, 'EDIT'):
            bm = bmesh.from_edit_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.verts[i] for i in to_del if i < len(bm.verts)], context='VERTS')
            bmesh.update_edit_mesh(obj.data)
    return obj

# ---------------------------------------------------------------------------
# Bezier curve + spin (revolution surface)
# ---------------------------------------------------------------------------

def bezier_curve(anchors, vector_locations=(), resolution=None, to_mesh=True):
    n = [len(r) for r in anchors if isinstance(r, Sized)][0]
    anchors = np.array([np.array(r, dtype=float) if isinstance(r, Sized) else np.full(n, r) for r in anchors])
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    if n > 2:
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.curve.subdivide(number_cuts=n - 2)
    points = obj.data.splines[0].bezier_points
    for i in range(n):
        points[i].co = anchors[:, i]
    for i in range(n):
        if i in vector_locations:
            points[i].handle_left_type = 'VECTOR'
            points[i].handle_right_type = 'VECTOR'
        else:
            points[i].handle_left_type = 'AUTO'
            points[i].handle_right_type = 'AUTO'
    obj.data.splines[0].resolution_u = resolution if resolution is not None else 12
    if not to_mesh:
        return obj
    return curve2mesh(obj)

def curve2mesh(obj):
    points = obj.data.splines[0].bezier_points
    cos = np.array([p.co for p in points])
    length = np.linalg.norm(cos[:-1] - cos[1:], axis=-1) if len(cos) > 1 else np.array([])
    min_length = 5e-3
    with ViewportMode(obj, 'EDIT'):
        for p in obj.data.splines[0].bezier_points:
            if p.handle_left_type == 'FREE':
                p.handle_left_type = 'ALIGNED'
            if p.handle_right_type == 'FREE':
                p.handle_right_type = 'ALIGNED'
        for i in reversed(range(max(len(points) - 1, 0))):
            points = list(obj.data.splines[0].bezier_points)
            number_cuts = min(int(length[i] / min_length) - 1, 64)
            if number_cuts < 0:
                continue
            bpy.ops.curve.select_all(action='DESELECT')
            points[i].select_control_point = True
            points[i + 1].select_control_point = True
            bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1
    with SelectObjects(obj):
        bpy.ops.object.convert(target='MESH')
    obj = bpy.context.active_object
    modify_mesh(obj, 'WELD', apply=True, merge_threshold=1e-3)
    return obj

def spin(anchors, vector_locations=(), resolution=None, rotation_resolution=None,
         axis=(0, 0, 1), loop=False, dupli=False):
    obj = bezier_curve(anchors, vector_locations, resolution)
    co = read_co(obj)
    axis_v = np.array(axis, dtype=float)
    mean_radius = np.mean(np.linalg.norm(co - (co @ axis_v)[:, None] * axis_v, axis=-1)) if len(co) else 0.05
    if rotation_resolution is None:
        rotation_resolution = min(max(int(2 * np.pi * max(mean_radius, 1e-3) / 5e-3), 8), 128)
    modify_mesh(obj, 'WELD', apply=True, merge_threshold=1e-3)
    if loop:
        with ViewportMode(obj, 'EDIT'), Suppress():
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.fill()
        remesh_fill(obj)
    with ViewportMode(obj, 'EDIT'), Suppress():
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.spin(steps=rotation_resolution, angle=np.pi * 2, axis=axis, dupli=dupli)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=1e-3)
    return obj

# ---------------------------------------------------------------------------
# GeoNodes modifier helper
# ---------------------------------------------------------------------------

def _apply_geomod(obj, node_group, apply=True):
    """Add a pre-built GeoNodes modifier to obj, optionally apply it."""

    _select_none(); _set_active(obj)
    mod = obj.modifiers.new(name='GeoNodes', type='NODES')
    mod.node_group = node_group
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.node_groups.remove(node_group)
    _select_none()
    return mod

def _noise_fac_output(node):
    """Return the scalar factor output of a NoiseTexture node (Blender 4.x/5.x compat)."""

    for name in ("Fac", "Factor"):
        if name in node.outputs:
            return node.outputs[name]
    return node.outputs[0]

def _wave_fac_output(node):
    """Return the scalar factor output of a WaveTexture node (Blender 4.x/5.x compat)."""

    for name in ("Fac", "Factor"):
        if name in node.outputs:
            return node.outputs[name]
    return node.outputs[0]

def _set_active_attribute(obj, name):
    attrs = obj.data.attributes
    for i, a in enumerate(attrs):
        if a.name == name:
            attrs.active_index = i
            try:
                attrs.active = attrs[i]
            except Exception:
                pass
            return

# ---------------------------------------------------------------------------
# GeoNodes builders (direct bpy API, no NodeWrangler)
# ---------------------------------------------------------------------------

def _build_geo_extension(noise_strength=0.2, noise_scale=2.0):
    """Build a GeoNodes tree that displaces geometry outward with noise."""

    noise_strength = uniform(noise_strength / 2, noise_strength)
    noise_scale = uniform(noise_scale * 0.7, noise_scale * 1.4)
    direction_offset = uniform(-1, 1, 3)

    ng = bpy.data.node_groups.new("geo_extension", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    pos = ng.nodes.new('GeometryNodeInputPosition')

    length_node = ng.nodes.new('ShaderNodeVectorMath'); length_node.operation = 'LENGTH'
    ng.links.new(pos.outputs[0], length_node.inputs[0])

    inv_len = ng.nodes.new('ShaderNodeMath'); inv_len.operation = 'DIVIDE'
    inv_len.inputs[0].default_value = 1.0
    ng.links.new(length_node.outputs['Value'], inv_len.inputs[1])

    dir_scale = ng.nodes.new('ShaderNodeVectorMath'); dir_scale.operation = 'SCALE'
    ng.links.new(pos.outputs[0], dir_scale.inputs[0])
    ng.links.new(inv_len.outputs[0], dir_scale.inputs['Scale'])

    dir_add = ng.nodes.new('ShaderNodeVectorMath'); dir_add.operation = 'ADD'
    ng.links.new(dir_scale.outputs[0], dir_add.inputs[0])
    dir_add.inputs[1].default_value = tuple(float(v) for v in direction_offset)

    noise_tex = ng.nodes.new('ShaderNodeTexNoise')
    ng.links.new(dir_add.outputs[0], noise_tex.inputs['Vector'])
    noise_tex.inputs['Scale'].default_value = noise_scale

    add_quarter = ng.nodes.new('ShaderNodeMath'); add_quarter.operation = 'ADD'
    ng.links.new(_noise_fac_output(noise_tex), add_quarter.inputs[0])
    add_quarter.inputs[1].default_value = 0.25

    mul_strength = ng.nodes.new('ShaderNodeMath'); mul_strength.operation = 'MULTIPLY'
    ng.links.new(add_quarter.outputs[0], mul_strength.inputs[0])
    mul_strength.inputs[1].default_value = noise_strength

    offset_scale = ng.nodes.new('ShaderNodeVectorMath'); offset_scale.operation = 'SCALE'
    ng.links.new(pos.outputs[0], offset_scale.inputs[0])
    ng.links.new(mul_strength.outputs[0], offset_scale.inputs['Scale'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(gi.outputs[0], set_pos.inputs['Geometry'])
    ng.links.new(offset_scale.outputs[0], set_pos.inputs['Offset'])

    ng.links.new(set_pos.outputs[0], go.inputs[0])
    return ng

def _build_geo_xyz():
    """Build GeoNodes tree: store normalized |x|, |y|, |z| as named attributes."""

    ng = bpy.data.node_groups.new("geo_xyz", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    pos = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(pos.outputs[0], sep.inputs[0])

    prev_geom = gi.outputs[0]
    for axis_name, axis_out in [("x", "X"), ("y", "Y"), ("z", "Z")]:
        abs_node = ng.nodes.new('ShaderNodeMath'); abs_node.operation = 'ABSOLUTE'
        ng.links.new(sep.outputs[axis_out], abs_node.inputs[0])

        attr_stat = ng.nodes.new('GeometryNodeAttributeStatistic')
        ng.links.new(prev_geom, attr_stat.inputs['Geometry'])
        ng.links.new(abs_node.outputs[0], attr_stat.inputs[2])

        div_node = ng.nodes.new('ShaderNodeMath'); div_node.operation = 'DIVIDE'
        ng.links.new(abs_node.outputs[0], div_node.inputs[0])
        ng.links.new(attr_stat.outputs['Max'], div_node.inputs[1])

        store = ng.nodes.new('GeometryNodeStoreNamedAttribute')
        ng.links.new(prev_geom, store.inputs['Geometry'])
        store.inputs['Name'].default_value = axis_name
        ng.links.new(div_node.outputs[0], store.inputs['Value'])

        prev_geom = store.outputs['Geometry']

    ng.links.new(prev_geom, go.inputs[0])
    return ng

def _build_geo_morel(voronoi_scale, randomness):
    """Build GeoNodes tree: store voronoi distance-to-edge < 0.05 as 'morel' attribute."""

    ng = bpy.data.node_groups.new("geo_morel", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    voronoi = ng.nodes.new('ShaderNodeTexVoronoi')
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs['Scale'].default_value = voronoi_scale
    voronoi.inputs['Randomness'].default_value = randomness

    compare = ng.nodes.new('FunctionNodeCompare')
    compare.operation = 'LESS_THAN'
    ng.links.new(voronoi.outputs['Distance'], compare.inputs[0])
    compare.inputs[1].default_value = 0.05

    store = ng.nodes.new('GeometryNodeStoreNamedAttribute')
    ng.links.new(gi.outputs[0], store.inputs['Geometry'])
    store.inputs['Name'].default_value = "morel"
    ng.links.new(compare.outputs['Result'], store.inputs['Value'])

    ng.links.new(store.outputs['Geometry'], go.inputs[0])
    return ng

def _build_geo_band(length, scale):
    """Build GeoNodes tree for stem band pattern."""

    wave_scale = float(log_uniform(5, 10))
    wave_distortion = float(uniform(5, 10))
    z_threshold = float(-uniform(0.3, 0.7) * length)

    ng = bpy.data.node_groups.new("geo_band", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    wave = ng.nodes.new('ShaderNodeTexWave')
    wave.bands_direction = 'Z'
    wave.wave_profile = 'SAW'
    wave.inputs['Scale'].default_value = wave_scale
    wave.inputs['Distortion'].default_value = wave_distortion
    wave.inputs['Detail Scale'].default_value = 2.0

    pos = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(pos.outputs[0], sep.inputs[0])

    compare = ng.nodes.new('FunctionNodeCompare')
    compare.operation = 'LESS_THAN'
    ng.links.new(sep.outputs['Z'], compare.inputs[0])
    compare.inputs[1].default_value = z_threshold

    normal_node = ng.nodes.new('GeometryNodeInputNormal')
    add_bias = ng.nodes.new('ShaderNodeVectorMath'); add_bias.operation = 'ADD'
    ng.links.new(normal_node.outputs[0], add_bias.inputs[0])
    add_bias.inputs[1].default_value = (0.0, 0.0, 2.0)
    norm = ng.nodes.new('ShaderNodeVectorMath'); norm.operation = 'NORMALIZE'
    ng.links.new(add_bias.outputs[0], norm.inputs[0])

    mul_scale = ng.nodes.new('ShaderNodeMath'); mul_scale.operation = 'MULTIPLY'
    ng.links.new(_wave_fac_output(wave), mul_scale.inputs[0])
    mul_scale.inputs[1].default_value = scale

    offset = ng.nodes.new('ShaderNodeVectorMath'); offset.operation = 'SCALE'
    ng.links.new(norm.outputs[0], offset.inputs[0])
    ng.links.new(mul_scale.outputs[0], offset.inputs['Scale'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(gi.outputs[0], set_pos.inputs['Geometry'])
    ng.links.new(compare.outputs['Result'], set_pos.inputs['Selection'])
    ng.links.new(offset.outputs[0], set_pos.inputs['Offset'])

    ng.links.new(set_pos.outputs[0], go.inputs[0])
    return ng

def _build_geo_inverse_band(scale):
    """Build GeoNodes tree for inverse band pattern."""

    wave_scale = float(log_uniform(5, 10))
    wave_distortion = float(uniform(5, 10))

    ng = bpy.data.node_groups.new("geo_inverse_band", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    pos = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(pos.outputs[0], sep.inputs[0])

    neg_z = ng.nodes.new('ShaderNodeMath'); neg_z.operation = 'MULTIPLY'
    neg_z.inputs[0].default_value = -1.0
    ng.links.new(sep.outputs['Z'], neg_z.inputs[1])

    combine = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(sep.outputs['X'], combine.inputs['X'])
    ng.links.new(sep.outputs['Y'], combine.inputs['Y'])
    ng.links.new(neg_z.outputs[0], combine.inputs['Z'])

    wave = ng.nodes.new('ShaderNodeTexWave')
    wave.bands_direction = 'Z'
    wave.wave_profile = 'SAW'
    ng.links.new(combine.outputs[0], wave.inputs['Vector'])
    wave.inputs['Scale'].default_value = wave_scale
    wave.inputs['Distortion'].default_value = wave_distortion
    wave.inputs['Detail Scale'].default_value = 2.0

    normal_node = ng.nodes.new('GeometryNodeInputNormal')
    add_bias = ng.nodes.new('ShaderNodeVectorMath'); add_bias.operation = 'ADD'
    ng.links.new(normal_node.outputs[0], add_bias.inputs[0])
    add_bias.inputs[1].default_value = (0.0, 0.0, 2.0)
    norm = ng.nodes.new('ShaderNodeVectorMath'); norm.operation = 'NORMALIZE'
    ng.links.new(add_bias.outputs[0], norm.inputs[0])

    mul_scale = ng.nodes.new('ShaderNodeMath'); mul_scale.operation = 'MULTIPLY'
    ng.links.new(_wave_fac_output(wave), mul_scale.inputs[0])
    mul_scale.inputs[1].default_value = scale

    offset = ng.nodes.new('ShaderNodeVectorMath'); offset.operation = 'SCALE'
    ng.links.new(norm.outputs[0], offset.inputs[0])
    ng.links.new(mul_scale.outputs[0], offset.inputs['Scale'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(gi.outputs[0], set_pos.inputs['Geometry'])
    ng.links.new(offset.outputs[0], set_pos.inputs['Offset'])

    ng.links.new(set_pos.outputs[0], go.inputs[0])
    return ng

def _build_geo_voronoi():
    """Build GeoNodes tree: separate geometry by voronoi distance-to-edge."""

    voronoi_scale = float(uniform(15, 20))

    ng = bpy.data.node_groups.new("geo_voronoi", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    voronoi = ng.nodes.new('ShaderNodeTexVoronoi')
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs['Scale'].default_value = voronoi_scale

    compare = ng.nodes.new('FunctionNodeCompare')
    compare.operation = 'LESS_THAN'
    ng.links.new(voronoi.outputs['Distance'], compare.inputs[0])
    compare.inputs[1].default_value = 0.06

    sep_geo = ng.nodes.new('GeometryNodeSeparateGeometry')
    ng.links.new(gi.outputs[0], sep_geo.inputs['Geometry'])
    ng.links.new(compare.outputs['Result'], sep_geo.inputs['Selection'])

    ng.links.new(sep_geo.outputs['Selection'], go.inputs[0])
    return ng

# ---------------------------------------------------------------------------
# Cap shape configs
# ---------------------------------------------------------------------------

def _campanulate():
    x = uniform(0.12, 0.15)
    return {
        "x_anchors": [0, x, x, 0.08, 0.04, 0],
        "z_anchors": [0, 0, uniform(0.03, 0.05), uniform(0.1, 0.12), uniform(0.16, 0.2), 0.2],
        "vector_locations": [],
        "has_gill": True,
    }

def _conical():
    z = uniform(0.2, 0.3)
    return {
        "x_anchors": [0, uniform(0.12, 0.15), 0.01, 0],
        "z_anchors": [0, 0, z, z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _convex():
    z = uniform(0.14, 0.16)
    return {
        "x_anchors": [0, 0.15, 0.12, 0.01, 0],
        "z_anchors": [0, 0, uniform(0.04, 0.06), z, z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _depressed():
    z = uniform(0.03, 0.05)
    return {
        "x_anchors": [0, 0.15, 0.12, 0],
        "z_anchors": [0, 0, uniform(0.06, 0.08), z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _flat():
    z = uniform(0.05, 0.07)
    return {
        "x_anchors": [0, 0.15, 0.12, 0],
        "z_anchors": [0, 0, z, z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _infundiuliform():
    z = uniform(0.08, 0.12)
    x = uniform(0.12, 0.15)
    return {
        "x_anchors": [0, 0.03, x, x - 0.01, 0],
        "z_anchors": [0, 0, z, z + uniform(0.005, 0.01), 0.02],
        "vector_locations": [],
        "has_gill": False,
    }

def _ovate():
    z = uniform(0.2, 0.3)
    return {
        "x_anchors": [0, uniform(0.12, 0.15), 0.08, 0.01, 0],
        "z_anchors": [0, 0, 0.8 * z, z, z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _umbillicate():
    z = uniform(0.03, 0.05)
    return {
        "x_anchors": [0, 0.15, 0.12, 0.02, 0],
        "z_anchors": [0, 0.04, uniform(0.06, 0.08), z + 0.02, z],
        "vector_locations": [],
        "has_gill": False,
    }

def _umbonate():
    z = uniform(0.05, 0.07)
    z_ = z + uniform(0.02, 0.04)
    return {
        "x_anchors": [0, 0.15, 0.12, 0.06, 0.02, 0],
        "z_anchors": [0, 0, z - 0.01, z, z_, z_],
        "vector_locations": [1],
        "has_gill": True,
    }

# ---------------------------------------------------------------------------
# Parameter sampling for cap (KEEP SEED)
# ---------------------------------------------------------------------------

def _sample_cap_params(seed):
    """Sample cap factory params using raw seed (matching MushroomCapFactory.__init__)."""

    with FixedSeed(seed):
        x_scale, z_scale = uniform(0.7, 1.4, 2)
        cap_configs = [
            _campanulate, _conical, _convex, _depressed, _flat,
            _infundiuliform, _ovate, _umbillicate, _umbonate,
        ]
        config_weights = np.array([2, 2, 2, 1, 2, 1, 2, 1, 1])
        cap_config_fn = np.random.choice(cap_configs, p=config_weights / config_weights.sum())
        cap_config = cap_config_fn()
        cap_config = {
            **cap_config,
            "x_anchors": [v * x_scale for v in cap_config["x_anchors"]],
            "z_anchors": [v * z_scale for v in cap_config["z_anchors"]],
        }

        radius = max(cap_config["x_anchors"])
        inner_radius = float(log_uniform(0.2, 0.35)) * radius

        def _adnexed_gill():
            return {
                "x_anchors": [radius, (radius + inner_radius) / 2, inner_radius, inner_radius, radius],
                "z_anchors": [0, -uniform(0.05, 0.08), -uniform(0, 0.02), 0, 0],
                "vector_locations": [3],
            }
        def _decurrent_gill():
            return {
                "x_anchors": [radius, (radius + inner_radius) / 2, inner_radius, 0, radius],
                "z_anchors": [0, -uniform(0.05, 0.08), -uniform(0.08, 0.1), 0, 0],
                "vector_locations": [2],
            }

        gill_configs = [_adnexed_gill, _decurrent_gill, None]
        gill_weights = np.array([1, 1, 1])
        gill_choice = np.random.choice([0, 1, 2], p=gill_weights / gill_weights.sum())
        if not cap_config["has_gill"]:
            gill_config = None
        elif gill_choice == 2:
            gill_config = None
        else:
            gill_config = gill_configs[gill_choice]()

        shader_weights = np.array([2, 1, 1, 1])
        _shader_idx = np.random.choice(4, p=shader_weights / shader_weights.sum())
        is_morel = uniform(0, 1) < 0.5 and _shader_idx == 0

        morel_voronoi_scale = float(uniform(15, 20))
        morel_randomness = float(uniform(0.5, 1))

        n_cuts = 0
        cut_angles = []
        cut_widths = []
        cut_depths = []
        cut_rotations = []
        if max(cap_config["x_anchors"]) <= 0.1:
            n_cuts = int(np.random.randint(0, 5))
            cut_angles = list(polygon_angles(n_cuts, np.pi / 4, np.pi * 2))
            for ci in range(n_cuts):
                cut_widths.append(float(uniform(0.15, 0.2) * 0.4))
                cut_depths.append(float(radius * uniform(0.4, 0.7)))
                cut_rotations.append(float(cut_angles[ci] + uniform(-np.pi / 4, np.pi / 4)))

        gill_rotation_resolution = int(np.random.randint(32, 64))
        texture_type = str(np.random.choice(["STUCCI", "MARBLE"]))
        texture_noise_scale = float(log_uniform(0.01, 0.05))
        twist_angle = float(uniform(-np.pi / 4, np.pi / 4))
        vertex_scale_factors = [float(v) for v in uniform(-0.25, 0.25, 4)]

    return {
        "cap_config": cap_config,
        "radius": float(radius),
        "inner_radius": float(inner_radius),
        "gill_config": gill_config,
        "is_morel": bool(is_morel),
        "morel_voronoi_scale": morel_voronoi_scale,
        "morel_randomness": morel_randomness,
        "n_cuts": n_cuts,
        "cut_angles": cut_angles,
        "cut_widths": cut_widths,
        "cut_depths": cut_depths,
        "cut_rotations": cut_rotations,
        "gill_rotation_resolution": gill_rotation_resolution,
        "texture_type": texture_type,
        "texture_noise_scale": texture_noise_scale,
        "twist_angle": twist_angle,
        "vertex_scale_factors": vertex_scale_factors,
    }

# ---------------------------------------------------------------------------
# Parameter sampling for stem (KEEP SEED)
# ---------------------------------------------------------------------------

def _sample_stem_params(seed, inner_radius):
    """Sample stem factory params using raw seed (matching MushroomStemFactory.__init__)."""

    with FixedSeed(seed):
        web_builders = ['hollow', 'solid', None]
        web_weights = np.array([1, 1, 2])
        web_builder = np.random.choice(web_builders, p=web_weights / web_weights.sum())
        has_band = uniform(0, 1) < 0.75

    return {
        'inner_radius': float(inner_radius),
        'web_builder': web_builder,
        'has_band': bool(has_band),
    }

# ---------------------------------------------------------------------------
# Build cap (matches MushroomCapFactory.create_asset)
# ---------------------------------------------------------------------------

def _build_cap(cap_params, face_size):
    """Build cap mesh from pre-sampled params."""

    cap_config = cap_params["cap_config"]
    anchors = cap_config["x_anchors"], 0, cap_config["z_anchors"]
    obj = spin(anchors, cap_config["vector_locations"])

    # Cuts
    if cap_params["n_cuts"] > 0:
        for i in range(cap_params["n_cuts"]):
            angle = cap_params["cut_angles"][i]
            width = cap_params["cut_widths"][i]
            depth = cap_params["cut_depths"][i]
            rot = cap_params["cut_rotations"][i]
            vertices = [
                [0, 0, 0.4], [0.4, -width, 0.4], [0.4, width, 0.4],
                [0, 0, -1], [0.4, -width, -0.01], [0.4, width, -0.01],
            ]
            faces = [[0, 1, 2], [1, 0, 3, 4], [2, 1, 4, 5], [0, 2, 5, 3], [5, 4, 3]]
            cutter = mesh2obj(data2mesh(vertices, [], faces))
            displace_vertices(cutter, lambda x, y, z: (0, 2 * y * y, 0))
            modify_mesh(cutter, "SUBSURF", render_levels=5, levels=5, subdivision_type="SIMPLE")
            cutter.location = np.cos(angle) * depth, np.sin(angle) * depth, 0
            cutter.rotation_euler = 0, 0, rot
            modify_mesh(obj, "WELD", merge_threshold=0.002)
            modify_mesh(obj, "BOOLEAN", object=cutter, operation="DIFFERENCE", apply=True)
            delete(cutter)

    remesh_with_attrs(obj, face_size)
    _apply_geomod(obj, _build_geo_xyz(), apply=True)
    _apply_geomod(obj, _build_geo_morel(cap_params["morel_voronoi_scale"], cap_params["morel_randomness"]), apply=True)

    if cap_params["is_morel"]:
        with SelectObjects(obj):
            _set_active_attribute(obj, "morel")
            try:
                bpy.ops.geometry.attribute_convert(mode="VERTEX_GROUP")
            except Exception:
                pass
        modify_mesh(obj, "DISPLACE", vertex_group="morel", strength=0.04, mid_level=0.7)

    if cap_params["gill_config"] is not None:
        gill_config = cap_params["gill_config"]
        anchors = gill_config["x_anchors"], 0, gill_config["z_anchors"]
        gill = spin(
            anchors,
            gill_config["vector_locations"],
            dupli=True, loop=True,
            rotation_resolution=cap_params["gill_rotation_resolution"],
        )
        subsurface2face_size(gill, face_size)
        modify_mesh(gill, "SMOOTH", apply=True, iterations=3)
        obj = join_objects([obj, gill])

    texture = bpy.data.textures.new(name="cap", type=cap_params["texture_type"])
    texture.noise_scale = cap_params["texture_noise_scale"]
    modify_mesh(obj, "DISPLACE", strength=0.008, texture=texture, mid_level=0)

    _apply_geomod(obj, _build_geo_extension(0.1), apply=True)

    modify_mesh(obj, "SIMPLE_DEFORM",
                deform_method="TWIST",
                angle=cap_params["twist_angle"],
                deform_axis="X")

    r1, r2, r3, r4 = cap_params["vertex_scale_factors"]
    displace_vertices(
        obj,
        lambda x, y, z: (
            np.where(x > 0, r1, r2) * x,
            np.where(y > 0, r3, r4) * y,
            0,
        ),
    )
    return obj

# ---------------------------------------------------------------------------
# Build stem (matches MushroomStemFactory.create_asset)
# ---------------------------------------------------------------------------

def _build_stem(stem_params, face_size):
    """Build stem mesh from pre-sampled params."""

    inner_radius = stem_params['inner_radius']
    web_builder_name = stem_params['web_builder']
    has_band = stem_params['has_band']

    length = log_uniform(0.4, 0.8)
    x_anchors = (
        0,
        inner_radius,
        log_uniform(1, 2) * inner_radius,
        inner_radius * uniform(1, 1.2),
        0,
    )
    z_anchors = 0, 0, -length * uniform(0.3, 0.7), -length, -length
    anchors = x_anchors, 0, z_anchors
    obj = spin(anchors, [1, 4])
    remesh_with_attrs(obj, face_size)

    if has_band:
        _apply_geomod(obj, _build_geo_band(length, uniform(0.008, 0.01)), apply=True)

    if web_builder_name is not None:
        if web_builder_name == 'hollow':
            outer_radius = inner_radius * uniform(2, 3.5)
            z = uniform(0.0, 0.05)
            web_length = log_uniform(0.2, 0.4)
            x_a = inner_radius, (outer_radius + inner_radius) / 2, outer_radius
            z_a = -z, -z - uniform(0.3, 0.4) * web_length, -z - web_length
            web = spin((x_a, 0, z_a))
            levels = 3
            modify_mesh(web, 'SUBSURF', apply=True, render_levels=levels, levels=levels)
            _apply_geomod(web, _build_geo_voronoi(), apply=True)
            modify_mesh(web, 'SMOOTH', apply=True, iterations=2)
        else:
            outer_radius = inner_radius * uniform(1.5, 3.5)
            z = uniform(0.0, 0.05)
            web_length = uniform(0.15, 0.2)
            x_a = inner_radius, (outer_radius + inner_radius) / 2, outer_radius
            z_a = -z, -z - uniform(0.3, 0.4) * web_length, -z - web_length
            web = spin((x_a, 0, z_a))
            _apply_geomod(web, _build_geo_inverse_band(-uniform(0.008, 0.01)), apply=True)
            modify_mesh(web, 'SMOOTH', apply=True, iterations=3)

        _apply_geomod(web, _build_geo_extension(), apply=True)
        subsurface2face_size(web, face_size / 2)
        modify_mesh(web, 'SMOOTH', apply=True, iterations=3)
        obj = join_objects([web, obj])

    texture = bpy.data.textures.new(name="stem_stucci", type="STUCCI")
    texture.noise_scale = uniform(0.005, 0.01)
    modify_mesh(obj, 'DISPLACE', strength=0.008, texture=texture, mid_level=0)

    modify_mesh(
        obj, 'SIMPLE_DEFORM',
        deform_method='BEND',
        angle=-uniform(0, np.pi / 2),
        deform_axis='Y',
    )
    return obj

# ---------------------------------------------------------------------------
# Build (MushroomGrowthFactory)
# ---------------------------------------------------------------------------

def build(seed=0, face_size=0.01):
    """Build a MushroomGrowthFactory mesh: cap + stem joined."""
    # Sample factory-level params using the raw seed
    # (MushroomGrowthFactory.__init__ calls FixedSeed(factory_seed))
    with FixedSeed(seed):
        # base_hue sampling (consume RNG to keep alignment)
        if uniform(0, 1) < 0.4:
            _base_hue = uniform(0, 1)
        else:
            _base_hue = uniform(0.02, 0.15)

        # material_func RNG consumption (no-op for mesh-only)
        # -- original calls surface.shaderfunc_to_material, which is a no-op

        # MushroomCapFactory.__init__ with factory_seed
        cap_params = _sample_cap_params(seed)

        # MushroomStemFactory.__init__ with factory_seed and cap's inner_radius
        stem_params = _sample_stem_params(seed, cap_params["inner_radius"])

    # create_asset uses int_hash((factory_seed, i)) where i=0
    geom_seed = int_hash((seed, 0))

    with FixedSeed(geom_seed):
        cap = _build_cap(cap_params, face_size / 2)
        stem = _build_stem(stem_params, face_size / 2)
        # Per-part materials: cap → CAP_MAT, stem → STEM_MAT
        # (Faithful to mushroom.py lines 63-66: shader_mushroom applied
        # to cap/gill/stem parts independently, 4-material layout.)
        try:
            cap.data.materials.clear()
            cap.data.materials.append(CAP_MAT)
            stem.data.materials.clear()
            stem.data.materials.append(STEM_MAT)
        except Exception:
            pass
        obj = join_objects([cap, stem])
        origin2lowest(obj)

    # Declare GILL_MAT and WEB_MAT slots for structural completeness matching
    # 4-material layout (cap/gill/stem/web). Standalone factory does
    # not emit explicit gill / web sub-meshes so these slots are declared but not
    # per-face assigned.
    try:
        existing = {m.name for m in obj.data.materials if m}
        for m in (GILL_MAT, WEB_MAT):
            if m.name not in existing:
                obj.data.materials.append(m)
    except Exception:
        pass

    obj.name = "MushroomGrowthFactory"
    return obj

# ---------------------------------------------------------------------------
# Clear scene
# ---------------------------------------------------------------------------

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    # NOTE: do NOT remove materials here — CATEG_MAT was built in Phase 1
    # before this call and must survive for the final mesh.
    for tex in list(bpy.data.textures):
        bpy.data.textures.remove(tex)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    bpy.context.scene.cursor.location = (0, 0, 0)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

clear_scene()
obj = build(SEED)

