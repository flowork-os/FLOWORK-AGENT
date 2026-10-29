# [FL_INDEX: keywords="blender_factory, procedural_3d, PillarFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PillarFactory | Category: factories_tex
# Prompt: A tall classical architectural pillar rendered as a weathered 3D model, featuring a fluted cylindrical shaft with vertical grooves running its full height, a decorative capital at the top with a flat square abacus, and a stepped rectangular base (plinth).

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

def make_mat(seed, name="MarbleMaterial"):
    """Marble: light gray/white with voronoi veins.
    Marble material implementation"""

    base_c = _hsv2rgba(float(np.random.uniform(0, 0.1)), np.random.uniform(0.02, 0.08), np.random.uniform(0.7, 0.95))
    vein_c = _hsv2rgba(float(np.random.uniform(0, 0.1)), np.random.uniform(0.05, 0.15), np.random.uniform(0.3, 0.5))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE"
    ln(tc.outputs["Object"], vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = float(np.random.uniform(3, 8))
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(vor.outputs["Distance"], cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = vein_c
    cr.color_ramp.elements[1].position = 0.15; cr.color_ramp.elements[1].color = base_c
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.1, 0.3))
    sk = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[sk].default_value = 0.5
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

ELEM_MAT = make_mat(SEED, "PillarFactory_Material")
np.random.seed(SEED)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

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

def new_base_circle(vertices):
    bpy.ops.mesh.primitive_circle_add(
        vertices=vertices, radius=1.0, fill_type='NOTHING', location=(0, 0, 0)
    )
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

def subdivide_edge_ring(obj, cuts=16):
    """Subdivide vertical edges to create horizontal edge rings."""

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    mesh = obj.data
    mesh.update()
    n_verts = len(mesh.vertices)
    n_edges = len(mesh.edges)
    co = np.zeros(n_verts * 3)
    mesh.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)

    edge_verts = np.zeros(n_edges * 2, dtype=int)
    mesh.edges.foreach_get('vertices', edge_verts)
    edge_verts = edge_verts.reshape(-1, 2)

    dirs = co[edge_verts[:, 1]] - co[edge_verts[:, 0]]
    norms = np.linalg.norm(dirs, axis=1, keepdims=True)
    norms[norms < 1e-8] = 1
    dirs /= norms

    vertical = np.abs(dirs[:, 2]) > 1 - 1e-3
    vert_indices = np.nonzero(vertical)[0]

    if len(vert_indices) == 0:
        return

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()

    edges = [bm.edges[i] for i in vert_indices]
    bmesh.ops.subdivide_edgering(bm, edges=edges, cuts=int(cuts))
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def build_pillar():
    clear_scene()

    # Parameters
    wall_height = np.random.uniform(2.8, 3.2)
    wall_thickness = np.random.uniform(0.2, 0.3)
    height = wall_height - wall_thickness

    n = np.random.randint(5, 10)
    radius = np.random.uniform(0.08, 0.12)
    outer_radius = radius * np.random.uniform(1.3, 1.5)
    lower_offset = np.random.uniform(0.05, 0.15)
    upper_offset = np.random.uniform(0.05, 0.15)
    detail_type = np.random.choice(["fluting", "reeding"])

    width = math.pi / 2 / n
    inset_width = width * log_uniform(0.1, 0.2)
    inset_width_ = (width - inset_width * 2) * np.random.uniform(-0.1, 0.3)
    inset_depth = np.random.uniform(0.1, 0.15)
    inset_scale_val = np.random.uniform(0.05, 0.1)
    outer_n = np.random.choice([1, 2, n])

    m = np.random.randint(12, 20)

    # z_profile: random weighted cumsum
    z_weights = np.random.uniform(1, 3, m)
    z_profile = np.array([0, *(np.cumsum(z_weights) / np.sum(z_weights))[:-1]])

    # r_profile: convolution-smoothed
    alpha = np.random.uniform(0.7, 0.85)
    r_raw = np.random.uniform(0, 1, m + 3)
    r_raw[[0, 1]] = 1
    r_raw[[-2, -1]] = 0
    r_convolved = np.convolve(r_raw, np.array([(1 - alpha) / 2, alpha, (1 - alpha) / 2]))
    r_profile = np.array([1, *r_convolved[2:-2]]) * (outer_radius - radius) + radius

    # n_profile
    n_profile = np.where(
        np.arange(m) < np.random.randint(2, max(3, m - 1)),
        outer_n, n
    )

    # inset_profile
    inset_profile = np.random.uniform(0, 1, m) < 0.3

    inset_scale = 1 + inset_scale_val * (1 if detail_type == "reeding" else -1)

    # Step 1: Create main cylinder with 4*n vertices
    verts_count = 4 * n
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts_count, radius=1.0, depth=1.0, location=(0, 0, 0.5)
    )
    obj = bpy.context.active_object
    obj.data.materials.clear()
    obj.data.materials.append(ELEM_MAT)

    obj.name = "pillar_shaft"
    apply_tf(obj, loc=True)

    # Remove non-quad faces (top/bottom caps)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    geom = [f for f in bm.faces if len(f.verts) > 4]
    if geom:
        bmesh.ops.delete(bm, geom=geom, context='FACES_ONLY')
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Scale to proper dimensions
    obj.scale = (radius, radius, (1 - lower_offset - upper_offset) * height)
    obj.location[2] = lower_offset * height
    apply_tf(obj)

    # Step 2: Fluting/reeding via inset operations
    if detail_type in ["fluting", "reeding"]:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.inset(thickness=inset_width * radius, use_individual=True)
        bpy.ops.mesh.inset(thickness=inset_width_ * radius, use_individual=True)
        bpy.ops.transform.resize(value=(inset_scale, inset_scale, 1))
        bpy.ops.object.mode_set(mode='OBJECT')

    # Step 3: subdivide_edgering
    subdivide_edge_ring(obj, 16)

    # Step 4: Select boundary edges for bridging
    parts = [obj]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Step 5: Create cap rings at z_profile heights
    z_rot = math.pi / 2 * np.random.randint(2)

    for zi, ri, ni, inset_i in zip(z_profile, r_profile, n_profile, inset_profile):
        o = new_base_circle(vertices=4 * ni)

        if inset_i:
            co = read_co(o)
            stride = np.random.choice([2, 4, 8])
            mask = np.where(np.arange(len(co)) % stride == 0, 1, inset_scale)
            co *= mask[:, np.newaxis]
            write_co(o, co)

        cuts = n // ni - 1
        if cuts > 0:
            bpy.context.view_layer.objects.active = o
            o.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.subdivide(number_cuts=cuts)
            bpy.ops.object.mode_set(mode='OBJECT')

        r_scaled = ri / math.cos(math.pi / 4 / ni)

        # Lower cap ring
        o.location[2] = zi * lower_offset * height
        o.scale = (r_scaled, r_scaled, 1)
        o.rotation_euler[2] = z_rot

        # Upper cap ring
        o2 = new_base_circle(vertices=4 * ni)
        if inset_i:
            co2 = read_co(o2)
            co2 *= mask[:, np.newaxis]
            write_co(o2, co2)

        if cuts > 0:
            bpy.context.view_layer.objects.active = o2
            o2.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.subdivide(number_cuts=cuts)
            bpy.ops.object.mode_set(mode='OBJECT')

        o2.location[2] = (1 - zi * upper_offset) * height
        o2.scale = (r_scaled, r_scaled, 1)
        o2.rotation_euler[2] = z_rot

        apply_tf(o)
        apply_tf(o2)

        # Mark edges as selected for bridging
        for ring in [o, o2]:
            rmesh = ring.data
            sel = np.ones(len(rmesh.edges), dtype=bool)
            rmesh.edges.foreach_set('select', sel)

        parts.extend([o, o2])

    # Step 6: Join all parts
    result = join_objs(parts)

    # Step 7: Bridge edge loops
    smoothness = np.random.uniform(1, 1.4)

    bpy.context.view_layer.objects.active = result
    result.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    # Bridge lower half: select wire/boundary edges with z < 0.5
    bm = bmesh.from_edit_mesh(result.data)
    bm.edges.ensure_lookup_table()
    for e in bm.edges:
        cz = (e.verts[0].co.z + e.verts[1].co.z) / 2
        e.select = (e.is_wire or e.is_boundary) and cz < 0.5
    bmesh.update_edit_mesh(result.data)
    try:
        bpy.ops.mesh.bridge_edge_loops(number_cuts=0, smoothness=smoothness)
    except RuntimeError:
        pass

    # Bridge upper half: after lower bridge, upper wire/boundary edges remain
    bm = bmesh.from_edit_mesh(result.data)
    bm.edges.ensure_lookup_table()
    for e in bm.edges:
        cz = (e.verts[0].co.z + e.verts[1].co.z) / 2
        e.select = (e.is_wire or e.is_boundary) and cz > 0.5
    bmesh.update_edit_mesh(result.data)
    try:
        bpy.ops.mesh.bridge_edge_loops(number_cuts=0, smoothness=smoothness)
    except RuntimeError:
        pass

    bpy.ops.object.mode_set(mode='OBJECT')

    # Step 8: Dual SUBSURF
    add_mod(result, "SUBSURF", levels=1, render_levels=1,
            subdivision_type='SIMPLE')
    add_mod(result, "SUBSURF", levels=1, render_levels=1)

    result.name = "PillarFactory"
    for i in range(len(result.data.materials)):
        if result.data.materials[i] is None:
            result.data.materials[i] = ELEM_MAT
    return result

pillar = build_pillar()

