# [FL_INDEX: keywords="blender_factory, procedural_3d, ElkhornCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: ElkhornCoralFactory | Category: factories_geo
# Prompt: An elkhorn coral rendered as a textured 3D model. The coral features large, flattened, palmate branches that fan outward from a shared base, resembling the broad antlers of an elk. The branches are wide and blade-like, with a rough, granular surface texture across both faces. The coloring is warm sandy beige with subtle tan variation. The broad, sweeping form creates a distinctive wide silhouette with a dramatic shadow cast on the plain white background.

import os
import random
import colorsys
import bpy
import bmesh
import numpy as np
import math
from mathutils import kdtree
from numpy.random import uniform
from scipy.interpolate import interp1d

SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

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
    n = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc_obj_out, n.inputs["Vector"])
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 2.0
    n.inputs["Roughness"].default_value = 0.5
    return _fac_out(n)

def _color_ramp_hsv(nt, ln, fac_out, positions, colors):
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
    if np.random.uniform(0, 1) < 0.25:
        return float(np.random.uniform(0, 1))
    else:
        return float(np.random.uniform(-0.2, 0.3)) % 1.0

def make_coral_material(base_hue, name="CoralMaterial"):
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

# sampling (otherwise consecutive seeds all produce similar warm-red hues).
_mat_seed = ((SEED + 1) * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
_seed_all(_mat_seed)
_coral_base_hue = _build_base_hue()
CORAL_MAT = make_coral_material(_coral_base_hue, "ElkhornCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)

# ── Utility functions ─────────────────────────────────────────────────────────

def polygon_angles(n, min_angle=np.pi / 6, max_angle=np.pi * 2 / 3):
    """Generate n well-spaced angles around a circle."""

    for _ in range(100):
        angles = np.sort(uniform(0, 2 * np.pi, n))
        difference = (angles - np.roll(angles, 1)) % (np.pi * 2)
        if (difference >= min_angle).all() and (difference <= max_angle).all():
            break
    else:
        angles = np.sort(
            (np.arange(n) * (2 * np.pi / n) + uniform(0, np.pi * 2)) % (np.pi * 2)
        )
    return angles

def make_circular_interp(lo, hi, n):
    """Circular quadratic interpolation."""

    xs = polygon_angles(n)
    ys = uniform(lo, hi, n)
    # Wrap for circular continuity
    xs_ext = np.array([xs[-1] - 2 * np.pi, *xs, xs[0] + 2 * np.pi])
    ys_ext = np.array([ys[-1], *ys, ys[0]])
    return interp1d(xs_ext, ys_ext, kind="quadratic")

def separate_loose(obj):
    """Keep only the largest connected component of a mesh."""

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    visited = set()
    components = []
    for v in bm.verts:
        if v.index in visited:
            continue
        comp = set()
        stack = [v]
        while stack:
            cur = stack.pop()
            if cur.index in visited:
                continue
            visited.add(cur.index)
            comp.add(cur.index)
            for e in cur.link_edges:
                o = e.other_vert(cur)
                if o.index not in visited:
                    stack.append(o)
        components.append(comp)
    if len(components) <= 1:
        bm.free()
        return obj
    largest = max(components, key=len)
    to_remove = [v for v in bm.verts if v.index not in largest]
    bmesh.ops.delete(bm, geom=to_remove, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj

# ── Step 1: Create disk mesh (circle + fill_grid) ────────────────────────────
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_circle_add(vertices=1024, radius=1.0, fill_type='NOTHING')
obj = bpy.context.active_object
obj.name = "ElkhornCoralFactory"
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.fill_grid()
bpy.ops.object.mode_set(mode='OBJECT')

# ── Step 2: XY jitter ────────────────────────────────────────────────────────
bm = bmesh.new()
bm.from_mesh(obj.data)
for v in bm.verts:
    v.co.x += uniform(-0.005, 0.005)
    v.co.y += uniform(-0.005, 0.005)
bm.to_mesh(obj.data)
bm.free()

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
obj.data.update()

# ── Step 4: geo_elkhorn via Geometry Nodes (tree carving) ─────────────────────
bpy.ops.object.select_all(action='DESELECT')
tree_mesh = obj.data.copy()
tree_obj = bpy.data.objects.new("tree_temp", tree_mesh)
bpy.context.scene.collection.objects.link(tree_obj)
bpy.context.view_layer.objects.active = tree_obj
tree_obj.select_set(True)

ng = bpy.data.node_groups.new("geo_elkhorn", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
inp_n = ng.nodes.new("NodeGroupInput")
out_n = ng.nodes.new("NodeGroupOutput")

# start_index = AND(length > 0.7, bernoulli(0.003))
pos1 = ng.nodes.new("GeometryNodeInputPosition")
len1 = ng.nodes.new("ShaderNodeVectorMath"); len1.operation = "LENGTH"
ng.links.new(pos1.outputs["Position"], len1.inputs[0])
cmp_gt = ng.nodes.new("FunctionNodeCompare")
cmp_gt.data_type = "FLOAT"; cmp_gt.operation = "GREATER_THAN"
ng.links.new(len1.outputs["Value"], cmp_gt.inputs[0])
cmp_gt.inputs[1].default_value = 0.7
rand_seed = int(np.random.randint(1e5))
rand_bool = ng.nodes.new("FunctionNodeRandomValue")
rand_bool.data_type = "BOOLEAN"
for s in rand_bool.inputs:
    if "Probability" in s.name:
        s.default_value = 0.003
    if "Seed" in s.name:
        s.default_value = rand_seed
bool_and = ng.nodes.new("FunctionNodeBooleanMath"); bool_and.operation = "AND"
ng.links.new(cmp_gt.outputs["Result"], bool_and.inputs[0])
rand_out = [o for o in rand_bool.outputs if o.type == 'BOOLEAN']
ng.links.new(rand_out[0] if rand_out else rand_bool.outputs[3], bool_and.inputs[1])

# end_index = length < 0.02
pos2 = ng.nodes.new("GeometryNodeInputPosition")
len2 = ng.nodes.new("ShaderNodeVectorMath"); len2.operation = "LENGTH"
ng.links.new(pos2.outputs["Position"], len2.inputs[0])
cmp_lt = ng.nodes.new("FunctionNodeCompare")
cmp_lt.data_type = "FLOAT"; cmp_lt.operation = "LESS_THAN"
ng.links.new(len2.outputs["Value"], cmp_lt.inputs[0])
cmp_lt.inputs[1].default_value = 0.02

# ShortestEdgePath → EdgePathToCurves → NURBS → CurveToMesh → MergeByDistance
shortest = ng.nodes.new("GeometryNodeInputShortestEdgePaths")
ng.links.new(cmp_lt.outputs["Result"], shortest.inputs["End Vertex"])
path2curve = ng.nodes.new("GeometryNodeEdgePathsToCurves")
ng.links.new(inp_n.outputs[0], path2curve.inputs["Mesh"])
ng.links.new(bool_and.outputs[0], path2curve.inputs["Start Vertices"])
ng.links.new(shortest.outputs["Next Vertex Index"], path2curve.inputs["Next Vertex Index"])
spline_type = ng.nodes.new("GeometryNodeCurveSplineType")
spline_type.spline_type = "NURBS"
ng.links.new(path2curve.outputs["Curves"], spline_type.inputs["Curve"])
curve2mesh = ng.nodes.new("GeometryNodeCurveToMesh")
ng.links.new(spline_type.outputs["Curve"], curve2mesh.inputs["Curve"])
merge = ng.nodes.new("GeometryNodeMergeByDistance")
ng.links.new(curve2mesh.outputs["Mesh"], merge.inputs["Geometry"])
merge.inputs["Distance"].default_value = 0.005
ng.links.new(merge.outputs["Geometry"], out_n.inputs[0])

mod = tree_obj.modifiers.new("GeoElkhorn", "NODES")
mod.node_group = ng
bpy.ops.object.modifier_apply(modifier="GeoElkhorn")

tree_locations = np.array([tree_obj.matrix_world @ v.co for v in tree_obj.data.vertices])
print(f"Tree mesh: {len(tree_locations)} vertices")
tree_mesh_ref = tree_obj.data
bpy.data.objects.remove(tree_obj, do_unlink=True)
bpy.data.meshes.remove(tree_mesh_ref, do_unlink=True)

# ── Step 5: tree2mesh (KDTree) ───────────────────────────────────────────────
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

kd = kdtree.KDTree(len(tree_locations))
for i, loc in enumerate(tree_locations):
    kd.insert(loc, i)
kd.balance()

large_radius = uniform(0.08, 0.12)
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table()
to_remove = []
for v in bm.verts:
    x, y, z = v.co
    _, _, d = kd.find(v.co)
    r = math.sqrt(x * x + y * y)
    if d > 0.015 + large_radius * (1 - r):
        to_remove.append(v)
bmesh.ops.delete(bm, geom=to_remove, context='VERTS')
bm.to_mesh(obj.data)
bm.free()
obj.data.update()

# ── Step 6–9: separate, angles, displace, separate ───────────────────────────
separate_loose(obj)

bm = bmesh.new()
bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
angle_radius = 0.2
n_verts = len(bm.verts)
angles_arr = np.full(n_verts, -100.0)
queue = set()
for v in bm.verts:
    x, y, z = v.co
    if math.sqrt(x * x + y * y) <= angle_radius:
        angles_arr[v.index] = math.atan2(y, x)
        for e in v.link_edges:
            queue.add(e.other_vert(v))
while queue:
    new_queue = set()
    for v in queue:
        if angles_arr[v.index] <= -100.0:
            pairs = [(e.calc_length(), angles_arr[e.other_vert(v).index])
                     for e in v.link_edges
                     if angles_arr[e.other_vert(v).index] > -100.0]
            if pairs:
                angles_arr[v.index] = min(pairs)[1]
        for e in v.link_edges:
            o = e.other_vert(v)
            if angles_arr[o.index] <= -100.0:
                new_queue.add(o)
    queue = new_queue
bm.free()
for i in range(n_verts):
    if angles_arr[i] <= -100.0:
        v = obj.data.vertices[i]
        angles_arr[i] = math.atan2(v.co.y, v.co.x)

f_scale = make_circular_interp(0.3, 1.0, 5)
f_rotation = make_circular_interp(0, np.pi / 3, 10)
f_power = make_circular_interp(1.0, 1.6, 5)
co = np.array([v.co[:] for v in obj.data.vertices])
x, y, z = co.T
a = angles_arr[:len(x)] + np.pi
z += f_scale(a) * (x * x + y * y) ** f_power(a)
rotation = f_rotation(a)
c, s = np.cos(rotation), np.sin(rotation)
new_co = np.stack([c * x - s * z, c * y - s * z, c * z + s * np.sqrt(x * x + y * y)], -1)
for i, v in enumerate(obj.data.vertices):
    v.co[:] = new_co[i]
obj.data.update()

bm = bmesh.new()
bm.from_mesh(obj.data)
bm.edges.ensure_lookup_table()
long_edges = [e for e in bm.edges if e.calc_length() > 0.04]
bmesh.ops.delete(bm, geom=long_edges, context='EDGES')
bm.to_mesh(obj.data)
bm.free()
obj.data.update()
separate_loose(obj)

obj.rotation_euler[2] = uniform(0, 2 * np.pi)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(rotation=True)

# ── Step 11: SOLIDIFY ────────────────────────────────────────────────────────
m_sol = obj.modifiers.new("Solid", "SOLIDIFY")
m_sol.thickness = 0.02
bpy.ops.object.modifier_apply(modifier="Solid")

# ── Step 12: geo_extension (2D) ──────────────────────────────────────────────
noise_strength_ext = float(uniform(0.1, 0.2))
noise_scale_ext = float(uniform(1.4, 2.8))
rand_offset = list(uniform(-1, 1, 3).astype(float))

ng2 = bpy.data.node_groups.new("geo_extension", "GeometryNodeTree")
ng2.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng2.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
inp2 = ng2.nodes.new("NodeGroupInput")
out2 = ng2.nodes.new("NodeGroupOutput")
pos_e = ng2.nodes.new("GeometryNodeInputPosition")
vec_len = ng2.nodes.new("ShaderNodeVectorMath"); vec_len.operation = "LENGTH"
ng2.links.new(pos_e.outputs["Position"], vec_len.inputs[0])
div_n = ng2.nodes.new("ShaderNodeMath"); div_n.operation = "DIVIDE"
div_n.inputs[0].default_value = 1.0
ng2.links.new(vec_len.outputs["Value"], div_n.inputs[1])
norm_n = ng2.nodes.new("ShaderNodeVectorMath"); norm_n.operation = "SCALE"
ng2.links.new(pos_e.outputs["Position"], norm_n.inputs[0])
ng2.links.new(div_n.outputs[0], norm_n.inputs["Scale"])
add_off = ng2.nodes.new("ShaderNodeVectorMath"); add_off.operation = "ADD"
ng2.links.new(norm_n.outputs["Vector"], add_off.inputs[0])
add_off.inputs[1].default_value = rand_offset
try:
    tex2 = ng2.nodes.new("ShaderNodeTexMusgrave")
    tex2.musgrave_dimensions = "2D"
    ng2.links.new(add_off.outputs["Vector"], tex2.inputs["Vector"])
    tex2.inputs["Scale"].default_value = noise_scale_ext
    noise_out = tex2.outputs["Fac"]
except Exception:
    tex2 = ng2.nodes.new("ShaderNodeTexNoise")
    tex2.noise_dimensions = "2D"
    ng2.links.new(add_off.outputs["Vector"], tex2.inputs["Vector"])
    tex2.inputs["Scale"].default_value = noise_scale_ext
    noise_out = tex2.outputs[0]
add_b = ng2.nodes.new("ShaderNodeMath"); add_b.operation = "ADD"
add_b.inputs[1].default_value = 0.25
ng2.links.new(noise_out, add_b.inputs[0])
mul_s = ng2.nodes.new("ShaderNodeMath"); mul_s.operation = "MULTIPLY"
mul_s.inputs[1].default_value = noise_strength_ext
ng2.links.new(add_b.outputs[0], mul_s.inputs[0])
sc = ng2.nodes.new("ShaderNodeVectorMath"); sc.operation = "SCALE"
ng2.links.new(pos_e.outputs["Position"], sc.inputs[0])
ng2.links.new(mul_s.outputs[0], sc.inputs["Scale"])
sp = ng2.nodes.new("GeometryNodeSetPosition")
ng2.links.new(inp2.outputs[0], sp.inputs["Geometry"])
ng2.links.new(sc.outputs["Vector"], sp.inputs["Offset"])
ng2.links.new(sp.outputs[0], out2.inputs[0])

mod2 = obj.modifiers.new("GeoExt", "NODES")
mod2.node_group = ng2
bpy.ops.object.modifier_apply(modifier="GeoExt")

# ── Step 13: STUCCI displacement (Z) ─────────────────────────────────────────
tex_s = bpy.data.textures.new("elk_stucci", type='STUCCI')
tex_s.noise_scale = float(np.exp(uniform(np.log(0.1), np.log(0.5))))
m_z = obj.modifiers.new("Z_Disp", "DISPLACE")
m_z.texture = tex_s
m_z.strength = float(uniform(0.1, 0.2))
m_z.mid_level = 0
m_z.direction = 'Z'
bpy.ops.object.modifier_apply(modifier="Z_Disp")

# ── Step 14: origin2lowest (matching original: origin at lowest vertex) ──────
co_arr = np.array([v.co[:] for v in obj.data.vertices])
lowest_idx = np.argmin(co_arr[:, 2])
obj.location = tuple(-co_arr[lowest_idx])
bpy.ops.object.transform_apply(location=True)

# ── CoralFactory postprocess ─────────────────────────────────────────────────
default_scale = [0.8, 0.8, 0.8]
noise_strength_post = 0.005    # ElkhornBaseCoralFactory.noise_strength
bump_prob = 0.3

dims = [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z]
max_xy = max(dims[0], dims[1], 1e-6)
s = 2.0 * np.array(default_scale) / max_xy * uniform(0.8, 1.2, 3)
obj.scale = tuple(s)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(scale=True)

# Voxel remesh
m_rem = obj.modifiers.new("Remesh", "REMESH")
m_rem.mode = "VOXEL"; m_rem.voxel_size = 0.01
bpy.ops.object.modifier_apply(modifier="Remesh")

# Noise/bump displacement
if noise_strength_post > 0:
    has_bump = uniform() < bump_prob
    if has_bump:
        tex_type = np.random.choice(['STUCCI', 'MARBLE'])
        tex = bpy.data.textures.new("coral_noise", type=tex_type)
        tex.noise_scale = math.exp(uniform(math.log(0.01), math.log(0.02)))
        m_d = obj.modifiers.new("Noise", "DISPLACE")
        m_d.texture = tex
        m_d.strength = noise_strength_post * uniform(0.9, 1.2)
        m_d.mid_level = 0
    else:
        tex = bpy.data.textures.new("coral_bump", type='VORONOI')
        tex.noise_scale = math.exp(uniform(math.log(0.02), math.log(0.03)))
        tex.noise_intensity = math.exp(uniform(math.log(1.5), math.log(2.0)))
        tex.distance_metric = 'MINKOVSKY'
        tex.minkovsky_exponent = uniform(1, 1.5)
        m_d = obj.modifiers.new("Bump", "DISPLACE")
        m_d.texture = tex
        m_d.strength = -noise_strength_post * uniform(1, 2)
        m_d.mid_level = 1
    bpy.ops.object.modifier_apply(modifier=m_d.name)

# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "ElkhornCoralFactory"
print(f"Done: ElkhornCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
