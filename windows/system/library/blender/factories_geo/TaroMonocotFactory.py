# [FL_INDEX: keywords="blender_factory, procedural_3d, TaroMonocotFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TaroMonocotFactory | Category: factories_geo
# Prompt: A 3D model of a taro plant rendered from a slightly elevated perspective, featuring several large, heart-shaped or arrow-shaped leaves on long, upright petioles emerging from a central base, with the leaves drooping slightly outward and displaying a light green coloring.

import os
SEED = int(os.environ.get("SEED", "0"))
import bpy
import bmesh
import numpy as np
import random
import hashlib
from collections.abc import Iterable, Sized
from numpy.random import uniform


# ──────────────────────────────────────────────────────────
# Random seed infrastructure
# ──────────────────────────────────────────────────────────


import random as _random, colorsys as _colorsys

def _seed_mat(seed):
    _s = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s); _random.seed(_s)

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

def make_category_mat(seed, name="MonocotMaterial"):
    """Monocot plant: musgrave-driven green color ramp + subsurface."""

    _seed_mat(seed)
    base_hue = float(np.random.uniform(0.15, 0.35))
    bright_c = _hsv2rgba(base_hue, np.random.uniform(0.6, 0.8), np.random.uniform(0.05, 0.1))
    dark_c = _hsv2rgba((base_hue + float(np.random.uniform(-0.03, 0.03))) % 1,
                        np.random.uniform(0.8, 1.0), np.random.uniform(0.05, 0.2))
    musg_scale = float(np.random.uniform(10, 30))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Noise as musgrave replacement
    noise = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = musg_scale
    noise.inputs["Detail"].default_value = 2.0

    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.color_mode = "HSV"
    cr.color_ramp.hue_interpolation = "NEAR"
    ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements.new(0); cr.color_ramp.elements.new(0)
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = bright_c
    cr.color_ramp.elements[1].position = 0.3; cr.color_ramp.elements[1].color = bright_c
    cr.color_ramp.elements[2].position = 0.7; cr.color_ramp.elements[2].color = dark_c
    cr.color_ramp.elements[3].position = 1.0; cr.color_ramp.elements[3].color = dark_c

    # Roughness from noise
    noise_r = nt.nodes.new("ShaderNodeTexNoise"); noise_r.inputs["Scale"].default_value = 50.0
    fc = nt.nodes.new("ShaderNodeFloatCurve"); ln(_fac(noise_r), fc.inputs["Value"])
    c = fc.mapping.curves[0]
    c.points[0].location = (0, float(np.random.uniform(0.5, 0.6)))
    c.points[1].location = (1, float(np.random.uniform(0.7, 0.9)))
    fc.mapping.update()

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    ln(fc.outputs["Value"], bsdf.inputs["Roughness"])
    sk = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[sk].default_value = float(np.random.uniform(0.0, 0.2))
    bsdf.inputs["Subsurface Weight"].default_value = 0.01
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = float(np.random.choice([0, np.random.uniform(0.2, 0.5)]))

    out = nt.nodes.new("ShaderNodeOutputMaterial"); ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

CATEG_MAT = make_category_mat(SEED, "TaroMonocotFactory_Material")
CATEG_MAT.use_fake_user = True

class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
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

def int_hash(x, mx=(2**32 - 1)):
    return abs(int(md5_hash(x).hexdigest(), 16)) % mx

def log_uniform(low, high):
    return np.exp(uniform(np.log(low), np.log(high)))

# ──────────────────────────────────────────────────────────
# Blender utility helpers
# ──────────────────────────────────────────────────────────

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)

def apply_transform(obj, loc=False):
    _select_none(); _set_active(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    _select_none()

class ViewportMode:
    def __init__(self, obj, mode='EDIT'):
        self.obj = obj; self.mode = mode
    def __enter__(self):
        _select_none(); _set_active(self.obj)
        self.prev = self.obj.mode
        bpy.ops.object.mode_set(mode=self.mode)
        return self
    def __exit__(self, *_):
        bpy.ops.object.mode_set(mode=self.prev)
        _select_none()

def modify_mesh(obj, mod_type, apply=True, **kwargs):
    _select_none(); _set_active(obj)
    mod = obj.modifiers.new(name=mod_type, type=mod_type)
    for k, v in kwargs.items():
        try: setattr(mod, k, v)
        except Exception: pass
    if apply:
        try: bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception: obj.modifiers.remove(mod)
    _select_none()

def delete_objects(objs):
    if not isinstance(objs, list): objs = [objs]
    for o in objs: bpy.data.objects.remove(o, do_unlink=True)

def select_objs(objs):
    _select_none()
    for o in objs: o.select_set(True)
    if objs: bpy.context.view_layer.objects.active = objs[0]

def delete_collection(coll):
    for o in list(coll.objects): bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(coll)

# ──────────────────────────────────────────────────────────
# Mesh data helpers
# ──────────────────────────────────────────────────────────

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def write_co(obj, arr):
    obj.data.vertices.foreach_set("co", arr.reshape(-1))

def data2mesh(vertices=(), edges=(), faces=(), name=""):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()
    return mesh

def mesh2obj(mesh):
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

def origin2leftmost(obj):
    co = read_co(obj)
    if not len(co): return
    i = np.argmin(co[:, 0])
    obj.location = -co[i]
    apply_transform(obj, loc=True)

def origin2lowest(obj):
    """Set origin to the lowest vertex (min z)."""

    co = read_co(obj)
    if not len(co): return
    i = np.argmin(co[:, -1])
    obj.location = -co[i]
    apply_transform(obj, loc=True)

def join_objects(objs):
    _select_none()
    if not isinstance(objs, list): objs = [objs]
    if len(objs) == 1: return objs[0]
    bpy.context.view_layer.objects.active = objs[0]
    _select_none(); select_objs(objs)
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.location = 0, 0, 0; obj.rotation_euler = 0, 0, 0; obj.scale = 1, 1, 1
    _select_none(); return obj

def separate_loose(obj):
    _select_none(); _set_active(obj)
    try:
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.separate(type='LOOSE')
    except Exception: return obj
    objs = list(bpy.context.selected_objects)
    if obj not in objs: objs.append(obj)
    if len(objs) <= 1: _select_none(); return obj
    i = np.argmax([len(o.data.vertices) for o in objs])
    result = objs[i]; objs.remove(result); delete_objects(objs)
    _select_none(); return result

def displace_vertices(obj, fn):
    co = read_co(obj)
    if not isinstance(fn, Iterable):
        x, y, z = co.T; fn = fn(x, y, z)
        for i in range(3): co[:, i] += fn[i]
    else: co += fn
    write_co(obj, co)

def read_normal(obj):
    """Read per-polygon normals."""

    arr = np.zeros(len(obj.data.polygons) * 3)
    obj.data.polygons.foreach_get("normal", arr)
    return arr.reshape(-1, 3)

def select_faces(obj, to_select):
    """Select faces by boolean mask."""

    if not isinstance(to_select, Iterable):
        co = np.zeros(len(obj.data.polygons) * 3)
        obj.data.polygons.foreach_get("center", co)
        co = co.reshape(-1, 3)
        x, y, z = co.T
        to_select = to_select(x, y, z)
    to_select = np.nonzero(to_select)[0]
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        for i in to_select:
            bm.faces[i].select_set(True)
        bm.select_flush(False)
        bmesh.update_edit_mesh(obj.data)
    return obj

def point_normal_up(obj):
    """Flip face normals that point downward (negative z)."""

    obj.data.update()
    no_z = read_normal(obj)[:, -1]
    select_faces(obj, no_z < 0)
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.flip_normals()

# ──────────────────────────────────────────────────────────
# Helpers for GeoNodes
# ──────────────────────────────────────────────────────────

def _assign_curve(curve_mapping_curve, points, handle="VECTOR"):
    for i, p in enumerate(points):
        if i < 2: curve_mapping_curve.points[i].location = p
        else: curve_mapping_curve.points.new(*p)
        curve_mapping_curve.points[i].handle_type = handle

def _set_default(socket, value):
    if value is None: return
    try: socket.default_value = value
    except Exception:
        if isinstance(value, np.ndarray): socket.default_value = value.tolist()
        elif isinstance(value, (tuple, list)): socket.default_value = tuple(value)
        else: raise

def _build_geo_extension(noise_strength=0.2, noise_scale=2.0):
    noise_strength = uniform(noise_strength / 2, noise_strength)
    noise_scale = uniform(noise_scale * 0.7, noise_scale * 1.4)
    direction_offset = uniform(-1, 1, 3)
    ng = bpy.data.node_groups.new("geo_extension", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True
    pos = ng.nodes.new('GeometryNodeInputPosition')
    ln = ng.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; ng.links.new(pos.outputs[0], ln.inputs[0])
    inv = ng.nodes.new('ShaderNodeMath'); inv.operation = 'DIVIDE'
    inv.inputs[0].default_value = 1.0; ng.links.new(ln.outputs['Value'], inv.inputs[1])
    ds = ng.nodes.new('ShaderNodeVectorMath'); ds.operation = 'SCALE'
    ng.links.new(pos.outputs[0], ds.inputs[0]); ng.links.new(inv.outputs[0], ds.inputs['Scale'])
    da = ng.nodes.new('ShaderNodeVectorMath'); da.operation = 'ADD'
    ng.links.new(ds.outputs[0], da.inputs[0]); da.inputs[1].default_value = tuple(float(v) for v in direction_offset)
    nt = ng.nodes.new('ShaderNodeTexNoise')
    ng.links.new(da.outputs[0], nt.inputs['Vector']); nt.inputs['Scale'].default_value = noise_scale
    nc = ng.nodes.new('ShaderNodeMath'); nc.operation = 'SUBTRACT'
    ng.links.new(nt.outputs[0], nc.inputs[0]); nc.inputs[1].default_value = 0.5
    aq = ng.nodes.new('ShaderNodeMath'); aq.operation = 'ADD'
    ng.links.new(nc.outputs[0], aq.inputs[0]); aq.inputs[1].default_value = 0.25
    ms = ng.nodes.new('ShaderNodeMath'); ms.operation = 'MULTIPLY'
    ng.links.new(aq.outputs[0], ms.inputs[0]); ms.inputs[1].default_value = noise_strength
    os_ = ng.nodes.new('ShaderNodeVectorMath'); os_.operation = 'SCALE'
    ng.links.new(ms.outputs[0], os_.inputs['Scale']); ng.links.new(pos.outputs[0], os_.inputs[0])
    sp = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(gi.outputs[0], sp.inputs['Geometry']); ng.links.new(os_.outputs[0], sp.inputs['Offset'])
    ng.links.new(sp.outputs[0], go.inputs[0]); return ng

def _build_align_tilt_nodes(ng, curve_socket, axis=(1, 0, 0)):
    an = ng.nodes.new('ShaderNodeVectorMath'); an.operation = 'NORMALIZE'
    an.inputs[0].default_value = tuple(float(v) for v in axis)
    nn = ng.nodes.new('GeometryNodeInputNormal'); tn = ng.nodes.new('GeometryNodeInputTangent')
    tnm = ng.nodes.new('ShaderNodeVectorMath'); tnm.operation = 'NORMALIZE'; ng.links.new(tn.outputs[0], tnm.inputs[0])
    dat = ng.nodes.new('ShaderNodeVectorMath'); dat.operation = 'DOT_PRODUCT'
    ng.links.new(an.outputs[0], dat.inputs[0]); ng.links.new(tnm.outputs[0], dat.inputs[1])
    pr = ng.nodes.new('ShaderNodeVectorMath'); pr.operation = 'SCALE'
    ng.links.new(dat.outputs['Value'], pr.inputs['Scale']); ng.links.new(tnm.outputs[0], pr.inputs[0])
    sp = ng.nodes.new('ShaderNodeVectorMath'); sp.operation = 'SUBTRACT'
    ng.links.new(an.outputs[0], sp.inputs[0]); ng.links.new(pr.outputs[0], sp.inputs[1])
    apn = ng.nodes.new('ShaderNodeVectorMath'); apn.operation = 'NORMALIZE'; ng.links.new(sp.outputs[0], apn.inputs[0])
    co = ng.nodes.new('ShaderNodeVectorMath'); co.operation = 'DOT_PRODUCT'
    ng.links.new(apn.outputs[0], co.inputs[0]); ng.links.new(nn.outputs[0], co.inputs[1])
    cr = ng.nodes.new('ShaderNodeVectorMath'); cr.operation = 'CROSS_PRODUCT'
    ng.links.new(nn.outputs[0], cr.inputs[0]); ng.links.new(apn.outputs[0], cr.inputs[1])
    si = ng.nodes.new('ShaderNodeVectorMath'); si.operation = 'DOT_PRODUCT'
    ng.links.new(cr.outputs[0], si.inputs[0]); ng.links.new(tnm.outputs[0], si.inputs[1])
    at = ng.nodes.new('ShaderNodeMath'); at.operation = 'ARCTAN2'
    ng.links.new(si.outputs['Value'], at.inputs[0]); ng.links.new(co.outputs['Value'], at.inputs[1])
    st = ng.nodes.new('GeometryNodeSetCurveTilt')
    ng.links.new(curve_socket, st.inputs['Curve']); ng.links.new(at.outputs[0], st.inputs['Tilt'])
    return st.outputs['Curve']

def _build_geo_radius(radius, resolution=6, merge_distance=0.004):
    ng = bpy.data.node_groups.new("geo_radius", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True
    m2c = ng.nodes.new('GeometryNodeMeshToCurve'); ng.links.new(gi.outputs[0], m2c.inputs['Mesh'])
    tilted = _build_align_tilt_nodes(ng, m2c.outputs['Curve'])
    sr = ng.nodes.new('GeometryNodeSetCurveRadius'); ng.links.new(tilted, sr.inputs['Curve']); sr.inputs['Radius'].default_value = radius
    ci = ng.nodes.new('GeometryNodeCurvePrimitiveCircle'); ci.inputs['Resolution'].default_value = resolution
    tr = ng.nodes.new('GeometryNodeTransform'); ng.links.new(ci.outputs[0], tr.inputs['Geometry'])
    c2m = ng.nodes.new('GeometryNodeCurveToMesh')
    ng.links.new(sr.outputs[0], c2m.inputs['Curve']); ng.links.new(tr.outputs[0], c2m.inputs['Profile Curve'])
    c2m.inputs['Fill Caps'].default_value = True
    try: c2m.inputs['Scale'].default_value = radius
    except (KeyError, IndexError): pass
    ss = ng.nodes.new('GeometryNodeSetShadeSmooth'); ng.links.new(c2m.outputs[0], ss.inputs['Geometry']); ss.inputs[2].default_value = False
    if merge_distance > 0:
        mg = ng.nodes.new('GeometryNodeMergeByDistance'); ng.links.new(ss.outputs[0], mg.inputs['Geometry'])
        mg.inputs['Distance'].default_value = merge_distance; ng.links.new(mg.outputs[0], go.inputs[0])
    else: ng.links.new(ss.outputs[0], go.inputs[0])
    return ng

def _apply_geomod(obj, node_group, apply=True):
    _select_none(); _set_active(obj)
    mod = obj.modifiers.new(name='GeoNodes', type='NODES'); mod.node_group = node_group
    if apply: bpy.ops.object.modifier_apply(modifier=mod.name); bpy.data.node_groups.remove(node_group)
    _select_none(); return mod

# ──────────────────────────────────────────────────────────
# Drawing utilities
# ──────────────────────────────────────────────────────────

def bezier_curve(anchors, vector_locations=(), resolution=None, to_mesh=True):
    n = [len(r) for r in anchors if isinstance(r, Sized)][0]
    anchors = np.array([np.array(r, dtype=float) if isinstance(r, Sized) else np.full(n, r) for r in anchors])
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    if n > 2:
        with ViewportMode(obj, 'EDIT'): bpy.ops.curve.subdivide(number_cuts=n - 2)
    points = obj.data.splines[0].bezier_points
    for i in range(n): points[i].co = anchors[:, i]
    for i in range(n):
        if i in vector_locations: points[i].handle_left_type = 'VECTOR'; points[i].handle_right_type = 'VECTOR'
        else: points[i].handle_left_type = 'AUTO'; points[i].handle_right_type = 'AUTO'
    obj.data.splines[0].resolution_u = resolution if resolution is not None else 12
    if not to_mesh: return obj
    return curve2mesh_draw(obj)

def curve2mesh_draw(obj):
    points = obj.data.splines[0].bezier_points
    cos = np.array([p.co for p in points])
    length = np.linalg.norm(cos[:-1] - cos[1:], axis=-1)
    min_length = 5e-3
    with ViewportMode(obj, 'EDIT'):
        for i in range(len(points)):
            if points[i].handle_left_type == 'FREE': points[i].handle_left_type = 'ALIGNED'
            if points[i].handle_right_type == 'FREE': points[i].handle_right_type = 'ALIGNED'
        for i in reversed(range(len(points) - 1)):
            points = list(obj.data.splines[0].bezier_points)
            number_cuts = min(int(length[i] / min_length) - 1, 64)
            if number_cuts < 0: continue
            bpy.ops.curve.select_all(action='DESELECT')
            points[i].select_control_point = True; points[i + 1].select_control_point = True
            bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1; _select_none(); _set_active(obj)
    bpy.ops.object.convert(target='MESH'); obj = bpy.context.active_object
    modify_mesh(obj, 'WELD', merge_threshold=1e-3); return obj

def _delete_non_top_faces(obj, avg_normal, threshold=0.25):
    ng = bpy.data.node_groups.new("_DeleteNonTop", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput')
    nn = ng.nodes.new('GeometryNodeInputNormal')
    xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    xyz.inputs[0].default_value = float(avg_normal[0]); xyz.inputs[1].default_value = float(avg_normal[1]); xyz.inputs[2].default_value = float(avg_normal[2])
    dot = ng.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    ng.links.new(nn.outputs[0], dot.inputs[0]); ng.links.new(xyz.outputs[0], dot.inputs[1])
    cmp = ng.nodes.new('FunctionNodeCompare'); cmp.data_type = 'FLOAT'; cmp.operation = 'LESS_EQUAL'
    ng.links.new(dot.outputs[1], cmp.inputs[0]); cmp.inputs[1].default_value = threshold
    dg = ng.nodes.new('GeometryNodeDeleteGeometry'); dg.domain = 'FACE'
    ng.links.new(gi.outputs[0], dg.inputs[0]); ng.links.new(cmp.outputs[0], dg.inputs[1])
    ng.links.new(dg.outputs[0], go.inputs[0])
    mod = obj.modifiers.new("_del", 'NODES'); mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name); bpy.data.node_groups.remove(ng)

def remesh_fill(obj, resolution=0.005):
    obj.data.update()
    n_polys = len(obj.data.polygons)
    if n_polys > 0:
        normals = np.zeros(n_polys * 3); obj.data.polygons.foreach_get("normal", normals); normals = normals.reshape(-1, 3)
        areas = np.zeros(n_polys); obj.data.polygons.foreach_get("area", areas)
        avg_normal = (normals * areas[:, np.newaxis]).sum(axis=0)
        nrm = np.linalg.norm(avg_normal); avg_normal = avg_normal / nrm if nrm > 1e-10 else np.array([0, 0, 1])
    else: avg_normal = np.array([0, 0, 1])
    modify_mesh(obj, 'SOLIDIFY', thickness=0.1)
    d = max(obj.dimensions); octree_depth = max(1, int(np.ceil(np.log2((d + 0.01) / resolution))))
    modify_mesh(obj, 'REMESH', mode='SHARP', octree_depth=octree_depth, use_remove_disconnected=False)
    _delete_non_top_faces(obj, avg_normal, threshold=0.25); return obj

def leaf(x_anchors, y_anchors, vector_locations=(), subdivision=64, face_size=None):
    curves = []
    for i in [-1, 1]:
        anchors = [x_anchors, i * np.array(y_anchors), 0]
        curves.append(bezier_curve(anchors, vector_locations, subdivision))
    obj = join_objects(curves); modify_mesh(obj, 'WELD', merge_threshold=0.001)
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.fill()
    remesh_fill(obj)
    if face_size is not None: modify_mesh(obj, 'WELD', merge_threshold=face_size / 2)
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.region_to_loop()
        bpy.context.object.vertex_groups.new(name='boundary')
        bpy.ops.object.vertex_group_assign()
    obj = separate_loose(obj); return obj

def spin(anchors, vector_locations=(), resolution=None,
         rotation_resolution=None, axis=(0, 0, 1), loop=False, dupli=False):
    obj = bezier_curve(anchors, vector_locations, resolution)
    co = read_co(obj); axis_arr = np.array(axis)
    mean_radius = np.mean(np.linalg.norm(co - (co @ axis_arr)[:, np.newaxis] * axis_arr, axis=-1))
    if rotation_resolution is None: rotation_resolution = min(int(2 * np.pi * mean_radius / 5e-3), 128)
    modify_mesh(obj, 'WELD', merge_threshold=1e-3)
    if loop:
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.fill()
        remesh_fill(obj)
    with ViewportMode(obj, 'EDIT'):
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.spin(steps=rotation_resolution, angle=np.pi * 2, axis=axis, dupli=dupli)
        bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=1e-3)
    return obj

# ──────────────────────────────────────────────────────────
# GeoNodes builder: geo_flower
# ──────────────────────────────────────────────────────────

def _build_geo_flower(factory, leaves_collection):
    ng = bpy.data.node_groups.new("geo_flower", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True
    line = ng.nodes.new('GeometryNodeCurvePrimitiveLine'); line.inputs['End'].default_value = (0, 0, factory.stem_offset)
    resample = ng.nodes.new('GeometryNodeResampleCurve')
    ng.links.new(line.outputs[0], resample.inputs['Curve']); resample.inputs['Count'].default_value = factory.count
    parameter = ng.nodes.new('GeometryNodeSplineParameter')
    yr = ng.nodes.new('ShaderNodeFloatCurve'); ng.links.new(parameter.outputs[0], yr.inputs['Value'])
    _assign_curve(yr.mapping.curves[0], [(0, -factory.min_y_angle), (1, -factory.max_y_angle)], "VECTOR"); yr.mapping.use_clip = False
    ra = ng.nodes.new('FunctionNodeRandomValue'); ra.data_type = 'FLOAT'
    ra.inputs['Min'].default_value = factory.angle * 0.95; ra.inputs['Max'].default_value = factory.angle * 1.05
    ra.inputs['Seed'].default_value = np.random.randint(1e5)
    acc = ng.nodes.new('GeometryNodeAccumulateField'); ng.links.new(ra.outputs[1], acc.inputs[0])
    cr = ng.nodes.new('ShaderNodeCombineXYZ'); cr.inputs['X'].default_value = 0.0
    ng.links.new(yr.outputs[0], cr.inputs['Y']); ng.links.new(acc.outputs[0], cr.inputs['Z'])
    sc = ng.nodes.new('ShaderNodeFloatCurve'); ng.links.new(parameter.outputs[0], sc.inputs['Value'])
    _assign_curve(sc.mapping.curves[0], factory.scale_curve, "AUTO"); sc.mapping.use_clip = False
    rot_out = cr.outputs[0]; scl_out = sc.outputs[0]
    if factory.perturb:
        rpr = ng.nodes.new('FunctionNodeRandomValue'); rpr.data_type = 'FLOAT_VECTOR'
        _set_default(rpr.inputs['Min'], tuple([-factory.perturb]*3)); _set_default(rpr.inputs['Max'], tuple([factory.perturb]*3))
        rpr.inputs['Seed'].default_value = np.random.randint(1e5)
        addr = ng.nodes.new('ShaderNodeVectorMath'); addr.operation = 'ADD'
        ng.links.new(rot_out, addr.inputs[0]); ng.links.new(rpr.outputs[0], addr.inputs[1]); rot_out = addr.outputs[0]
        rps = ng.nodes.new('FunctionNodeRandomValue'); rps.data_type = 'FLOAT_VECTOR'
        _set_default(rps.inputs['Min'], tuple([-factory.perturb]*3)); _set_default(rps.inputs['Max'], tuple([factory.perturb]*3))
        rps.inputs['Seed'].default_value = np.random.randint(1e5)
        adds = ng.nodes.new('ShaderNodeVectorMath'); adds.operation = 'ADD'
        ng.links.new(scl_out, adds.inputs[0]); ng.links.new(rps.outputs[0], adds.inputs[1]); scl_out = adds.outputs[0]
    if factory.align_factor:
        al = ng.nodes.new('FunctionNodeAlignEulerToVector'); al.pivot_axis = 'Z'
        ng.links.new(rot_out, al.inputs['Rotation']); al.inputs['Factor'].default_value = factory.align_factor
        _set_default(al.inputs['Vector'], tuple(factory.align_direction)); rot_out = al.outputs[0]
    cap = ng.nodes.new('GeometryNodeCaptureAttribute')
    try:
        if len(cap.capture_items) == 0: cap.capture_items.new('FLOAT', 'Value')
        else: cap.capture_items[0].data_type = 'FLOAT'
    except Exception: pass
    ng.links.new(resample.outputs[0], cap.inputs['Geometry'])
    for s in cap.inputs:
        if s.name == 'Value' and s.type != 'GEOMETRY': ng.links.new(acc.outputs[0], s); break
    zrc = None
    for s in cap.outputs:
        if s.name == 'Value': zrc = s; break
    if zrc is None: zrc = cap.outputs[1]
    ci = ng.nodes.new('GeometryNodeCollectionInfo')
    ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
    bn = ng.nodes.new('FunctionNodeRandomValue'); bn.data_type = 'BOOLEAN'
    bn.inputs['Probability'].default_value = factory.leaf_prob; bn.inputs['Seed'].default_value = np.random.randint(1e5)
    ge = ng.nodes.new('FunctionNodeCompare'); ge.data_type = 'FLOAT'; ge.operation = 'GREATER_EQUAL'
    ng.links.new(parameter.outputs[0], ge.inputs[0]); ge.inputs[1].default_value = factory.leaf_range[0]
    le = ng.nodes.new('FunctionNodeCompare'); le.data_type = 'FLOAT'; le.operation = 'LESS_EQUAL'
    ng.links.new(parameter.outputs[0], le.inputs[0]); le.inputs[1].default_value = factory.leaf_range[1]
    a1 = ng.nodes.new('FunctionNodeBooleanMath'); a1.operation = 'AND'
    ng.links.new(bn.outputs[3], a1.inputs[0]); ng.links.new(ge.outputs[0], a1.inputs[1])
    a2 = ng.nodes.new('FunctionNodeBooleanMath'); a2.operation = 'AND'
    ng.links.new(a1.outputs[0], a2.inputs[0]); ng.links.new(le.outputs[0], a2.inputs[1])
    iop = ng.nodes.new('GeometryNodeInstanceOnPoints')
    ng.links.new(cap.outputs['Geometry'], iop.inputs['Points']); ng.links.new(a2.outputs[0], iop.inputs['Selection'])
    ng.links.new(ci.outputs[0], iop.inputs['Instance']); iop.inputs['Pick Instance'].default_value = True
    ng.links.new(rot_out, iop.inputs['Rotation']); ng.links.new(scl_out, iop.inputs['Scale'])
    rl = ng.nodes.new('GeometryNodeRealizeInstances'); ng.links.new(iop.outputs[0], rl.inputs[0])
    st = ng.nodes.new('GeometryNodeStoreNamedAttribute'); st.data_type = 'FLOAT'
    ng.links.new(rl.outputs[0], st.inputs['Geometry']); st.inputs['Name'].default_value = "z_rotation"
    for s in st.inputs:
        if s.name == 'Value' and s.type != 'GEOMETRY': ng.links.new(zrc, s); break
    jg = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(st.outputs[0], jg.inputs[0]); ng.links.new(gi.outputs[0], jg.inputs[0])
    ng.links.new(jg.outputs[0], go.inputs[0])
    return ng, ci

# ──────────────────────────────────────────────────────────
# Asset collection helper
# ──────────────────────────────────────────────────────────

def make_asset_collection(build_fn, count, name="leaves", verbose=False, **kwargs):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    for i in range(count):
        with FixedSeed(int_hash(("collection", i))):
            obj = build_fn(i, **kwargs)
            if obj is None: continue
            for c in obj.users_collection: c.objects.unlink(obj)
            coll.objects.link(obj)
    return coll

# ──────────────────────────────────────────────────────────
# MonocotGrowthFactory base class
# ──────────────────────────────────────────────────────────

class MonocotGrowthFactory:
    use_distance = False

    def __init__(self, factory_seed, coarse=False):
        self.factory_seed = int(factory_seed); self.coarse = coarse
        with FixedSeed(factory_seed):
            self.count = 128; self.perturb = 0.05; self.angle = np.pi / 6
            self.min_y_angle = 0.0; self.max_y_angle = np.pi / 2
            self.leaf_prob = uniform(0.8, 0.9); self.leaf_range = 0, 1
            self.stem_offset = 0.2; self.scale_curve = [(0, 1), (1, 1)]
            self.radius = 0.01; self.bend_angle = np.pi / 4; self.twist_angle = np.pi / 6
            self.z_drag = 0.0; self.z_scale = uniform(1.0, 1.2)
            self.align_factor = 0; self.align_direction = 1, 0, 0

    @property
    def is_grass(self): return False

    def build_leaf(self, face_size): raise NotImplementedError

    @staticmethod
    def decorate_leaf(obj, y_ratio=4, y_bend_angle=np.pi / 6,
                      z_bend_angle=np.pi / 6, noise_scale=0.1, strength=0.02, leftmost=True):
        obj.rotation_euler[1] = -np.pi / 2; apply_transform(obj)
        modify_mesh(obj, 'SIMPLE_DEFORM', deform_method='BEND', angle=uniform(0.5, 1) * y_bend_angle, deform_axis='Y')
        obj.rotation_euler[1] = np.pi / 2; apply_transform(obj)
        modify_mesh(obj, 'SIMPLE_DEFORM', deform_method='BEND', angle=uniform(-1, 1) * z_bend_angle, deform_axis='Z')
        displace_vertices(obj, lambda x, y, z: (0, 0, y_ratio * uniform(0, 1) * y * y))
        _apply_geomod(obj, _build_geo_extension(), apply=True)
        texture = bpy.data.textures.new(name='grasses', type='STUCCI'); texture.noise_scale = noise_scale
        modify_mesh(obj, 'DISPLACE', strength=strength, texture=texture)
        for direction, width in zip('XY', obj.dimensions[:2]):
            texture = bpy.data.textures.new(name='grasses', type='STUCCI'); texture.noise_scale = noise_scale
            modify_mesh(obj, 'DISPLACE', strength=uniform(0.01, 0.02) * width, texture=texture, direction=direction)
        if leftmost: origin2leftmost(obj)
        return obj

    def build_instance(self, i, face_size):
        obj = self.build_leaf(face_size); origin2leftmost(obj)
        obj.location[0] -= 0.01; apply_transform(obj, loc=True); return obj

    def make_collection(self, face_size):
        return make_asset_collection(self.build_instance, 10, "leaves", verbose=False, face_size=face_size)

    def build_stem(self, face_size):
        obj = mesh2obj(data2mesh([[0, 0, 0], [0, 0, self.stem_offset]], [[0, 1]]))
        modify_mesh(obj, 'SUBSURF', True, levels=9, render_levels=9)
        _apply_geomod(obj, _build_geo_radius(self.radius, 16), apply=True)
        if face_size and face_size > 0 and len(obj.data.edges) > 0:
            verts = np.array([v.co for v in obj.data.vertices]); edges = np.array([e.vertices for e in obj.data.edges])
            if len(edges) > 0 and len(verts) > 0:
                lens = np.sort(np.linalg.norm(verts[edges[:, 0]] - verts[edges[:, 1]], axis=-1))
                lmax = lens[-len(lens) // 4] if len(lens) > 4 else lens[-1]
                if lmax > face_size:
                    levels = min(int(np.ceil(np.log2(lmax / face_size))), 6)
                    if levels > 0: modify_mesh(obj, 'SUBSURF', levels=levels, render_levels=levels)
        texture = bpy.data.textures.new(name='grasses', type='STUCCI'); texture.noise_scale = 0.1
        modify_mesh(obj, 'DISPLACE', strength=0.01, texture=texture); return obj

    def create_asset(self, **params):
        obj = self.create_raw(**params); self.decorate_monocot(obj); return obj

    def create_raw(self, face_size=0.01, apply=True, **params):
        if self.angle != 0:
            frequency = 2 * np.pi / self.angle
            if 0.01 < frequency - int(frequency) < 0.05: frequency += 0.05
            elif -0.05 < frequency - int(frequency) < -0.01: frequency -= 0.05
            self.angle = 2 * np.pi / frequency
        leaves = self.make_collection(face_size); obj = self.build_stem(face_size)
        flower_ng, coll_info_node = _build_geo_flower(self, leaves)
        _select_none(); _set_active(obj)
        mod = obj.modifiers.new(name='geo_flower', type='NODES'); mod.node_group = flower_ng
        coll_info_node.inputs['Collection'].default_value = leaves
        if apply:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.node_groups.remove(flower_ng); _select_none(); delete_collection(leaves)
        return obj

    def decorate_monocot(self, obj):
        displace_vertices(obj, lambda x, y, z: (0, 0, -self.z_drag * (x * x + y * y)))
        _apply_geomod(obj, _build_geo_extension(0.4), apply=True)
        modify_mesh(obj, 'SIMPLE_DEFORM', deform_method='TWIST', angle=uniform(-self.twist_angle, self.twist_angle), deform_axis='Z')
        modify_mesh(obj, 'SIMPLE_DEFORM', deform_method='BEND', angle=uniform(0, self.bend_angle))
        obj.scale = uniform(0.8, 1.2), uniform(0.8, 1.2), self.z_scale
        obj.rotation_euler[-1] = uniform(0, np.pi * 2); apply_transform(obj)

# ──────────────────────────────────────────────────────────
# BananaMonocotFactory (embedded, needed for Taro inheritance)
# ──────────────────────────────────────────────────────────

class BananaMonocotFactory(MonocotGrowthFactory):
    def __init__(self, factory_seed, coarse=False):
        super().__init__(factory_seed, coarse)
        with FixedSeed(factory_seed):
            self.stem_offset = uniform(0.6, 1.0)
            self.angle = uniform(np.pi / 4, np.pi / 3)
            self.z_scale = uniform(1, 1.5); self.z_drag = uniform(0.1, 0.2)
            self.min_y_angle = uniform(np.pi * 0.05, np.pi * 0.1)
            self.max_y_angle = uniform(np.pi * 0.25, np.pi * 0.45)
            self.leaf_range = uniform(0.5, 0.7), 1
            self.count = int(log_uniform(16, 24))
            self.scale_curve = [(0, uniform(0.4, 1.0)), (1, uniform(0.6, 1.0))]
            self.radius = uniform(0.04, 0.06)
            self.bud_angle = uniform(np.pi / 8, np.pi / 6)
            self.cut_angle = self.bud_angle + uniform(np.pi / 20, np.pi / 12)
            self.freq = log_uniform(100, 300)
            self.n_cuts = np.random.randint(6, 10) if uniform(0, 1) < 0.8 else 0

    def cut_leaf(self, obj):
        coords = read_co(obj); x, y, z = coords.T
        coords = coords[(np.abs(y) < 0.08) & (np.abs(y) > 0.01)]
        if len(coords) == 0 or self.n_cuts == 0: return
        positive_coords = coords[coords.T[1] > 0]
        positive_coords = positive_coords[np.argsort(positive_coords[:, 0])]
        negative_coords = coords[coords.T[1] < 0]
        negative_coords = negative_coords[np.argsort(negative_coords[:, 0])]
        if len(positive_coords) < self.n_cuts or len(negative_coords) < self.n_cuts: return
        positive_coords = positive_coords[np.random.choice(len(positive_coords), self.n_cuts, replace=False)]
        negative_coords = negative_coords[np.random.choice(len(negative_coords), self.n_cuts, replace=False)]
        for (x1, y1, _), (x2, y2, _) in zip(
            np.concatenate([positive_coords[:-1], negative_coords[:-1]], 0),
            np.concatenate([positive_coords[1:], negative_coords[1:]], 0),
        ):
            coeff = 1 if y1 > 0 else -1
            ratio = uniform(-2.0, 0.4); exponent = uniform(1.2, 1.6)
            _x1, _y1, _x2, _y2 = x1, y1, x2, y2
            _coeff, _ratio, _exponent = coeff, ratio, exponent
            _cut_angle = self.cut_angle
            def cut(x, y, z, x1=_x1, y1=_y1, x2=_x2, y2=_y2,
                    coeff=_coeff, ratio=_ratio, exponent=_exponent, cut_angle=_cut_angle):
                m1 = x1 * np.sin(cut_angle) - y1 * np.cos(cut_angle) * coeff
                m2 = x2 * np.sin(cut_angle) - y2 * np.cos(cut_angle) * coeff
                m = x * np.sin(cut_angle) - y * np.cos(cut_angle) * coeff
                dist = ((x - x1) * (y1 - y2) + (y - y1) * (x1 - x2)) / np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + 0.1)
                return (0, 0, np.where((m1 < m) & (m < m2) & (dist * coeff < 0), ratio * np.abs(dist) ** exponent, 0))
            displace_vertices(obj, cut)
        with ViewportMode(obj, 'EDIT'):
            bm = bmesh.from_edit_mesh(obj.data)
            geom = [e for e in bm.edges if e.calc_length() > 0.02]
            bmesh.ops.delete(bm, geom=geom, context='EDGES')
            bmesh.update_edit_mesh(obj.data)

    def build_leaf(self, face_size):
        x_anchors = 0, 0.2 * np.cos(self.bud_angle), uniform(0.8, 1.2), 2.0
        y_anchors = 0, 0.2 * np.sin(self.bud_angle), uniform(0.2, 0.25), 0
        obj = leaf(x_anchors, y_anchors, face_size=face_size)
        self.cut_leaf(obj); self.displace_veins(obj); self.decorate_leaf(obj); return obj

    def displace_veins(self, obj):
        vg = obj.vertex_groups.new(name="distance")
        x, y, z = read_co(obj).T
        if len(x) == 0: return
        branch = np.cos((np.abs(y) * np.cos(self.cut_angle) - x * np.sin(self.cut_angle)) * self.freq) > uniform(0.85, 0.9, len(x))
        leaf_vein = np.abs(y) < uniform(0.002, 0.008, len(x))
        weights = branch | leaf_vein
        for i, l in enumerate(weights): vg.add([i], float(l), "REPLACE")
        modify_mesh(obj, 'DISPLACE', strength=-uniform(5e-3, 8e-3), mid_level=0, vertex_group="distance")

# ──────────────────────────────────────────────────────────
# TaroMonocotFactory
# ──────────────────────────────────────────────────────────

class TaroMonocotFactory(BananaMonocotFactory):
    def __init__(self, factory_seed, coarse=False):
        super().__init__(factory_seed, coarse)
        with FixedSeed(factory_seed):
            self.stem_offset = uniform(0.05, 0.1)
            self.radius = uniform(0.02, 0.04)
            self.z_drag = uniform(0.2, 0.3)
            self.bud_angle = uniform(np.pi * 0.6, np.pi * 0.7)
            self.freq = log_uniform(10, 20)
            self.count = int(log_uniform(12, 16))
            self.n_cuts = np.random.randint(1, 2) if uniform(0, 1) < 0.5 else 0
            self.min_y_angle = uniform(-np.pi * 0.25, -np.pi * 0.05)
            self.max_y_angle = uniform(-np.pi * 0.05, 0)

    def displace_veins(self, obj):
        point_normal_up(obj)
        vg = obj.vertex_groups.new(name="distance")
        x, y, z = read_co(obj).T
        if len(x) == 0: return
        branch = np.cos(
            uniform(0, np.pi * 2)
            + np.arctan2(y - np.where(y > 0, -1, 1) * uniform(0.1, 0.2), x - uniform(0.1, 0.4)) * self.freq
        ) > uniform(0.98, 0.99, len(x))
        leaf_vein = np.abs(y) < uniform(0.002, 0.008, len(x))
        weights = branch | leaf_vein
        for i, l in enumerate(weights): vg.add([i], float(l), "REPLACE")
        modify_mesh(obj, 'DISPLACE', strength=-uniform(5e-3, 8e-3), mid_level=0, vertex_group="distance")

    def build_leaf(self, face_size):
        x_anchors = (0, 0.2 * np.cos(self.bud_angle), uniform(0.4, 1.0), uniform(0.8, 1.0))
        y_anchors = 0, 0.2 * np.sin(self.bud_angle), uniform(0.25, 0.3), 0
        obj = leaf(x_anchors, y_anchors, face_size=face_size)
        self.cut_leaf(obj); self.displace_veins(obj)
        self.decorate_leaf(obj, 2, leftmost=False)
        bezier_branch = self.build_branch()
        obj = join_objects([obj, bezier_branch])
        origin2lowest(obj); return obj

    def build_branch(self):
        offset = uniform(0.2, 0.3); length = uniform(1, 2)
        x_anchors = 0, -0.05, -offset - uniform(0.01, 0.02), -offset
        z_anchors = 0, 0, -length + 0.1, -length
        bez = bezier_curve([x_anchors, 0, z_anchors])
        _apply_geomod(bez, _build_geo_radius(uniform(0.02, 0.03), 32), apply=True)
        return bez

    def build_instance(self, i, face_size):
        return self.build_leaf(face_size)

# ──────────────────────────────────────────────────────────
# Scene setup & main
# SEED-deterministic: material via _seed_mat(SEED); geometry via FixedSeed(factory_seed) + FixedSeed(int_hash((seed,0)))
# ──────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for mesh in bpy.data.meshes: bpy.data.meshes.remove(mesh)
    for coll in list(bpy.data.collections): bpy.data.collections.remove(coll)
    for tex in bpy.data.textures: bpy.data.textures.remove(tex)
    for ng in bpy.data.node_groups: bpy.data.node_groups.remove(ng)
    for curve in bpy.data.curves: bpy.data.curves.remove(curve)
    bpy.context.scene.cursor.location = (0, 0, 0)

def main():
    seed = SEED
    clear_scene()
    factory = TaroMonocotFactory(factory_seed=seed)
    with FixedSeed(int_hash((seed, 0))):
        obj = factory.create_asset()
    obj.data.materials.clear()
    obj.data.materials.append(CATEG_MAT)

    obj.name = "TaroMonocotFactory"
    co = read_co(obj)
    if len(co):
        center = (co.min(axis=0) + co.max(axis=0)) / 2
        obj.location[0] -= center[0]; obj.location[1] -= center[1]
        obj.location[2] -= co[:, 2].min(); apply_transform(obj, loc=True)

if __name__ == "__main__":
    main()
