# [FL_INDEX: keywords="blender_factory, procedural_3d, TableBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TableBaseCoralFactory | Category: factories_tex
# Prompt: A white base mesh 3D model of a table coral structure. The object displays the raw geometry of a wide, flat plate coral — a broad, low horizontal form with smooth curved upper and lower surfaces, irregular lobed margins, and several pointed projection elements rising from the top. Without any texture or material color, the clean white geometry reveals the large-scale flat plate topology and the curving wavy perimeter profile typical of table coral growth.

"""
Standalone Blender script (geometry + coral material) – TableBaseCoralFactory, seed 0.
Run:  blender --background --python TableBaseCoralFactory.py

Forces diff_growth flat variant (thin horizontal spread).
Uses proper build_diff_growth() with attraction/repulsion/noise simulation,
and geo_extension for radial Musgrave-noise displacement (petal undulations).
"""
import os
import bpy
import bmesh
import numpy as np
import math
from itertools import chain
from statistics import mean
from mathutils import Vector, kdtree, noise

SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
#  Coral material — translated from generate.py:shader_coral (raw bpy)
# ═══════════════════════════════════════════════════════════════════════════
import os, random, colorsys

def _seed_all(seed):
    np.random.seed(seed); random.seed(seed)

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0,
                                   max(0.0, min(1.0, float(s))),
                                   max(0.0, min(1.0, float(v))))
    return (r, g, b, 1.0)

def _new_coral_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac_out(node):
    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

def _noise_as_musgrave(nt, ln, scale, tc_obj_out):
    """Musgrave replacement: NoiseTexture (Musgrave removed in Blender 5.0).
    Original: MusgraveTexture -> MapRange[-1,1]->[0,1]. Noise already [0,1]."""

    n = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc_obj_out, n.inputs["Vector"])
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 2.0
    n.inputs["Roughness"].default_value = 0.5
    return _fac_out(n)

def _color_ramp_hsv(nt, ln, fac_out, positions, colors):
    """build_color_ramp with HSV interpolation mode."""

    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.color_mode = "HSV"
    cr.color_ramp.hue_interpolation = "NEAR"
    ln(fac_out, cr.inputs["Fac"])
    for _ in range(len(positions) - 2):
        cr.color_ramp.elements.new(0.0)
    for i, (p, c) in enumerate(zip(positions, colors)):
        cr.color_ramp.elements[i].position = p
        cr.color_ramp.elements[i].color = c
    return cr

def _float_curve(nt, ln, fac_out, anchors):
    """build_float_curve with VECTOR handles."""

    fc = nt.nodes.new("ShaderNodeFloatCurve")
    ln(fac_out, fc.inputs["Value"])
    c = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            c.points[i].location = (x, y)
        else:
            c.points.new(x, y)
        c.points[i].handle_type = "VECTOR"
    fc.mapping.use_clip = False
    fc.mapping.update()
    return fc

def _build_base_hue():
    """CoralFactory.build_base_hue()"""

    if np.random.uniform(0, 1) < 0.25:
        return float(np.random.uniform(0, 1))
    else:
        return float(np.random.uniform(-0.2, 0.3)) % 1.0

def make_coral_material(base_hue, name="CoralMaterial"):
    """Faithful translation of generate.py:shader_coral(nw, base_hue).
    Musgrave-driven 4-stop ColorRamp + light_color mix + noise roughness + SSS."""

    shift = float(np.random.uniform(0.05, 0.1)) * ((-1) ** int(np.random.randint(2)))
    subsurface_color = _hsv2rgba(np.random.uniform(0, 1), np.random.uniform(0, 1), 1.0)
    bright_color = _hsv2rgba((base_hue + shift) % 1, np.random.uniform(0.7, 0.9), 0.2)
    dark_color   = _hsv2rgba(base_hue, np.random.uniform(0.5, 0.7), 0.1)
    light_color  = _hsv2rgba((base_hue + float(np.random.uniform(-0.2, 0.2))) % 1,
                              np.random.uniform(0.2, 0.4), 0.4)
    specular = float(np.random.uniform(0.25, 0.5))
    musg1_scale = float(np.random.uniform(10, 20))
    musg2_scale = float(np.random.uniform(10, 20))
    fc_mid = float(np.random.uniform(0.3, 0.4))
    ss_ratio = float(np.random.uniform(0, 0.05)) if np.random.uniform(0, 1) > 0.5 else 0.0
    ss_r = float(np.random.uniform(0.05, 0.2))

    mat = _new_coral_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Color ramp: musgrave1 -> 4-stop HSV (dark -> bright)
    m1 = _noise_as_musgrave(nt, ln, musg1_scale, tc.outputs["Object"])
    cr = _color_ramp_hsv(nt, ln, m1,
        [0.0, 0.3, 0.7, 1.0],
        [dark_color, dark_color, bright_color, bright_color])

    # Mix with light_color via float curve of musgrave2
    m2 = _noise_as_musgrave(nt, ln, musg2_scale, tc.outputs["Object"])
    fc = _float_curve(nt, ln, m2, [(0, 1), (fc_mid, 0), (1, 0)])
    light_rgb = nt.nodes.new("ShaderNodeRGB")
    light_rgb.outputs[0].default_value = light_color
    mix_c = nt.nodes.new("ShaderNodeMix"); mix_c.data_type = "RGBA"
    ln(fc.outputs["Value"], mix_c.inputs[0])
    ln(cr.outputs["Color"], mix_c.inputs[6])
    ln(light_rgb.outputs[0], mix_c.inputs[7])

    # Roughness: noise(50) -> float curve (0.5 -> 1.0)
    n_r = nt.nodes.new("ShaderNodeTexNoise"); n_r.inputs["Scale"].default_value = 50.0
    fc_r = _float_curve(nt, ln, _fac_out(n_r), [(0, 0.5), (1, 1.0)])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_c.outputs[2], bsdf.inputs["Base Color"])
    ln(fc_r.outputs["Value"], bsdf.inputs["Roughness"])
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = specular
    bsdf.inputs["Subsurface Weight"].default_value = ss_ratio
    bsdf.inputs["Subsurface Radius"].default_value = (ss_r, ss_r, ss_r)
    if "Subsurface Color" in bsdf.inputs:
        bsdf.inputs["Subsurface Color"].default_value = subsurface_color

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

# from FixedSeed(factory_seed). To get equivalent diversity, we hash the seed for material
# sampling (otherwise consecutive seeds all produce similar warm-red hues).
_mat_seed = ((SEED + 1) * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
_seed_all(_mat_seed)
_coral_base_hue = _build_base_hue()
CORAL_MAT = make_coral_material(_coral_base_hue, "TableBaseCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)

maker = 'flat'
print(f"DiffGrowth coral variant: {maker}")

# ── Polygon-base mesh builder ────────────────────────────────────────────────
def polygon_angles(n):
    for _ in range(100):
        angles = np.sort(np.random.uniform(0, 2*np.pi, n))
        diff = (angles - np.roll(angles, 1)) % (2*np.pi)
        if (diff >= np.pi/6).all() and (diff <= 2*np.pi/3).all():
            return angles
    return np.sort((np.arange(n) * (2*np.pi/n) + np.random.uniform(0, 2*np.pi)) % (2*np.pi))

def make_polygon_base(n_base=4, n_colonies=1, stride=2.0):
    if n_colonies > 1:
        angles_c = polygon_angles(np.random.randint(2, 6))
        offsets  = np.stack([np.cos(angles_c), np.sin(angles_c), np.zeros_like(angles_c)]).T * stride
    else:
        offsets = np.zeros((1, 3))

    all_verts = []; all_faces = []
    for i, offset in enumerate(offsets):
        angles = polygon_angles(n_base)
        verts  = np.block([[np.cos(angles), 0], [np.sin(angles), 0], [np.zeros(n_base + 1)]]).T
        verts += offset
        base   = (n_base + 1) * i
        faces  = [[base + j, base + (j+1) % n_base, base + n_base] for j in range(n_base)]
        all_verts.append(verts)
        all_faces.extend(faces)
    return np.concatenate(all_verts), all_faces

# ── Differential growth simulation ──────────────────────────────────────────
def grow_step(bm, vg_index=0, split_radius=0.5, repulsion_radius=1.0, dt=0.1,
              growth_scale=(1, 1, 1), noise_scale=2.0, growth_vec=(0, 0, 1),
              fac_attr=1.0, fac_rep=1.0, fac_noise=1.0, inhibit_base=1.0,
              inhibit_shell=0.0):
    kd = kdtree.KDTree(len(bm.verts))
    for i, vert in enumerate(bm.verts):
        kd.insert(vert.co, i)
    kd.balance()
    seed_vector = Vector((0, 0, np.random.randint(0, 1000)))
    gv = Vector(growth_vec)
    gs = Vector(growth_scale)

    for vert in bm.verts:
        w = vert[bm.verts.layers.deform.active].get(vg_index, 0)
        if w > 0:
            f_attr = Vector()
            for edge in vert.link_edges:
                f_attr += edge.other_vert(vert).co - vert.co
            f_rep = Vector()
            for (co, index, distance) in kd.find_range(vert.co, repulsion_radius):
                if index != vert.index:
                    f_rep += (vert.co - co).normalized() * (math.exp(-1 * (distance / repulsion_radius) + 1) - 1)
            f_noise = noise.noise_vector(vert.co * noise_scale + seed_vector)
            force = fac_attr * f_attr + fac_rep * f_rep + fac_noise * f_noise + gv
            vert.co += force * dt * dt * w * gs

            if inhibit_base > 0 and not vert.is_boundary:
                w = w ** (1 + inhibit_base) - 0.01
            if inhibit_shell > 0:
                w = w * pow(vert.calc_shell_factor(), -1 * inhibit_shell)
            vert[bm.verts.layers.deform.active][vg_index] = w

    edges_to_subdivide = []
    for e in bm.edges:
        avg_weight = mean(v[bm.verts.layers.deform.active].get(vg_index, 0) for v in e.verts)
        if avg_weight > 0:
            l = e.calc_length()
            if l / split_radius > 1 / avg_weight:
                edges_to_subdivide.append(e)

    if edges_to_subdivide:
        bmesh.ops.subdivide_edges(bm, edges=edges_to_subdivide, smooth=1.0, cuts=1,
                                  use_grid_fill=True, use_single_edge=True)
        adjacent_faces = set(chain.from_iterable(e.link_faces for e in edges_to_subdivide))
        bmesh.ops.triangulate(bm, faces=list(adjacent_faces))

def build_diff_growth(obj, vg_index, max_polygons=1e4, **kwargs):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.layers.deform.verify()
    bm.verts.ensure_lookup_table()

    deform_layer = bm.verts.layers.deform.active
    for mv in obj.data.vertices:
        bv = bm.verts[mv.index]
        for g in mv.groups:
            bv[deform_layer][g.group] = g.weight

    plateau = 0
    step = 0
    while len(bm.faces) < max_polygons:
        v = len(bm.verts)
        grow_step(bm, vg_index, **kwargs)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        step += 1
        if v == len(bm.verts):
            plateau += 1
            if plateau > 50:
                break
        else:
            plateau = 0

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()

# ── geo_extension: radial displacement with noise (GeoNodes) ─────────────────
def apply_geo_extension(obj, noise_strength=0.22, noise_scale=2.0):
    """Replicate geo_extension using native Blender geometry nodes.

    Creates a GeoNodes modifier that displaces vertices radially using noise
    texture, producing petal-like undulations along edges.
    Pipeline: pos → normalize → add_jitter → NoiseTexture → scale → SetPosition.
    """

    ns = float(np.random.uniform(noise_strength / 2, noise_strength))
    nsc = float(np.random.uniform(noise_scale * 0.7, noise_scale * 1.4))
    rand_offset = tuple(np.random.uniform(-1, 1, 3).tolist())

    tree = bpy.data.node_groups.new("GeoExtension", 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = tree.nodes
    L = tree.links

    gi = N.new('NodeGroupInput')
    go = N.new('NodeGroupOutput')

    # Position node — output[0] is Position vector
    pos = N.new('GeometryNodeInputPosition')

    # Vector length of position
    vlen = N.new('ShaderNodeVectorMath')
    vlen.operation = 'LENGTH'
    L.new(pos.outputs[0], vlen.inputs[0])

    # 1 / length
    inv = N.new('ShaderNodeMath')
    inv.operation = 'DIVIDE'
    inv.inputs[0].default_value = 1.0
    L.new(vlen.outputs[1], inv.inputs[1])  # outputs[1] = Value (scalar)

    # Normalize: scale pos by 1/length
    norm = N.new('ShaderNodeVectorMath')
    norm.operation = 'SCALE'
    L.new(pos.outputs[0], norm.inputs[0])
    L.new(inv.outputs[0], norm.inputs[3])  # inputs[3] = Scale

    # Add random jitter offset to direction
    add_jit = N.new('ShaderNodeVectorMath')
    add_jit.operation = 'ADD'
    add_jit.inputs[1].default_value = rand_offset
    L.new(norm.outputs[0], add_jit.inputs[0])

    # Noise texture (replaces Musgrave removed in Blender 4.0+)
    ntex = N.new('ShaderNodeTexNoise')
    ntex.noise_dimensions = '3D'
    ntex.inputs['Scale'].default_value = nsc
    ntex.inputs['Detail'].default_value = 2.0
    ntex.inputs['Roughness'].default_value = 0.5
    L.new(add_jit.outputs[0], ntex.inputs['Vector'])

    # noise_fac + 0.25
    add_c = N.new('ShaderNodeMath')
    add_c.operation = 'ADD'
    add_c.inputs[1].default_value = 0.25
    L.new(ntex.outputs[0], add_c.inputs[0])  # outputs[0] = Fac/Factor

    # * noise_strength
    mul_s = N.new('ShaderNodeMath')
    mul_s.operation = 'MULTIPLY'
    mul_s.inputs[1].default_value = ns
    L.new(add_c.outputs[0], mul_s.inputs[0])

    # Scale position by (noise+0.25)*strength → radial offset
    spos = N.new('ShaderNodeVectorMath')
    spos.operation = 'SCALE'
    L.new(pos.outputs[0], spos.inputs[0])
    L.new(mul_s.outputs[0], spos.inputs[3])  # inputs[3] = Scale

    # Set Position: Geometry + Offset
    setp = N.new('GeometryNodeSetPosition')
    L.new(gi.outputs[0], setp.inputs['Geometry'])
    L.new(spos.outputs[0], setp.inputs['Offset'])

    L.new(setp.outputs[0], go.inputs[0])

    # Apply modifier
    mod = obj.modifiers.new("GeoExtension", 'NODES')
    mod.node_group = tree
    bpy.ops.object.modifier_apply(modifier="GeoExtension")

# ── Build flat/table coral ───────────────────────────────────────────────────
n_base = 4
n_colonies = 1

verts0, faces0 = make_polygon_base(n_base, n_colonies)
max_polys = int(4e2)

mesh = bpy.data.meshes.new("table_base")
mesh.from_pydata(verts0.tolist(), [], faces0)
mesh.update()
obj = bpy.data.objects.new("table_base", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# Boundary vertex group: all vertices (matches original code)
n_verts = len(verts0)
boundary_vg = obj.vertex_groups.new(name="Boundary")
boundary_vg.add(list(range(n_verts)), 1.0, "REPLACE")

print(f"Running differential growth (flat, max_polygons={max_polys}) ...")
build_diff_growth(obj, boundary_vg.index, max_polygons=max_polys,
                  repulsion_radius=2, inhibit_shell=1)
print(f"  Growth done: verts={len(obj.data.vertices)} faces={len(obj.data.polygons)}")

# Apply z-scale for flat variant
z_scale = float(np.random.uniform(1.0, 2.0))
obj.scale = (1, 1, z_scale)
bpy.ops.object.transform_apply(scale=True)

# SMOOTH(2)
m_sm = obj.modifiers.new("Smooth", "SMOOTH")
m_sm.iterations = 2
bpy.ops.object.modifier_apply(modifier="Smooth")

# SUBSURF(2)
m_ss = obj.modifiers.new("Sub", "SUBSURF")
m_ss.levels = 2;  m_ss.render_levels = 2
bpy.ops.object.modifier_apply(modifier="Sub")

max_dim = max(obj.dimensions[:2])
if max_dim > 0:
    obj.scale = (2/max_dim,) * 3
bpy.ops.object.transform_apply(scale=True)

# geo_extension: radial fractal-noise displacement for petal undulations
print("Applying geo_extension (radial noise displacement) ...")
apply_geo_extension(obj, noise_strength=0.22, noise_scale=2.0)

m_sol = obj.modifiers.new("Solid", "SOLIDIFY")
m_sol.thickness = 0.01
bpy.ops.object.modifier_apply(modifier="Solid")

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
min_z = min(v.co.z for v in obj.data.vertices)
obj.location[2] -= min_z * 0.8
bpy.ops.object.transform_apply(location=True)

# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "TableBaseCoralFactory"
print(f"Done: TableBaseCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")

