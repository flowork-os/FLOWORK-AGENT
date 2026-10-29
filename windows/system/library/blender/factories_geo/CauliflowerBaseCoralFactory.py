# [FL_INDEX: keywords="blender_factory, procedural_3d, CauliflowerBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CauliflowerBaseCoralFactory | Category: factories_geo
# Prompt: A white base mesh 3D model of a cauliflower coral structure. The object shows the raw geometry of clustered, rounded lobes that together form the compact mass characteristic of cauliflower coral. Without any texture or material color applied, the white mesh clearly exposes how multiple smooth blob-like volumes are packed together and stacked, with a wavy, lobed lower skirt at the base. A soft shadow beneath grounds the object on the white background.

import bpy
import numpy as np
from numpy.random import uniform
from scipy.ndimage import convolve
from skimage.measure import marching_cubes

np.random.seed(0)

# ── Laplacian growth (exact copy of laplacian.py) ──────────────────────────

def mesh_grid(n, sizes):
    shapes = [int((h - l) * n) + 1 for l, h in sizes]
    return np.meshgrid(*(np.linspace(*sz, sh) for sz, sh in zip(sizes, shapes)))

def init_mesh_3d(n, sizes):
    x, y, z = mesh_grid(n, sizes)
    f = (uniform(0.5, 1) * (x - uniform(-0.2, 0.2)) ** 2
         + uniform(0.5, 1) * (y - uniform(-0.2, 0.2)) ** 2
         + uniform(0.1, 0.2) * z ** 2
         < 0.2 * 0.2)
    def extend(f_):
        return uniform(0, 1, f_.shape) < convolve(f_.astype(float), np.ones((3, 3, 3)))
    a = np.where(f, uniform(0.1, 0.5, x.shape), 0) + uniform(0, 0.02, x.shape)
    b = np.where(extend(f), 1, uniform(-1, 1, x.shape)).astype(float)
    return a, b

def build_laplacian(st, a, b, t, k, dt, tau, eps, alpha, gamma, teq):
    for _ in range(t):
        lap_a = convolve(a, st)
        lap_b = convolve(b, st)
        m = alpha / np.pi * np.arctan(gamma * (teq - b))
        da = (eps * eps * lap_a + a * (1.0 - a) * (a - 0.5 + m)) / tau
        db = lap_b + k * da
        a += da * dt
        b += db * dt
    return a, b

n = 32; t = 800
stencil = np.array([
    [[1, 3, 1], [3, 14, 3], [1, 3, 1]],
    [[3, 14, 3], [14, -128, 14], [3, 14, 3]],
    [[1, 3, 1], [3, 14, 3], [1, 3, 1]],
]) / 128.0
height = 1.5
sizes = [-1, 1], [-1, 1], [0, height]

print(f"Running Laplacian growth ({n}^3 grid, {t} iterations) ...")
a_arr, b_arr = init_mesh_3d(n, sizes)
a_arr, b_arr = build_laplacian(stencil * n * n, a_arr, b_arr,
                                t, 2.0, 0.0005, 0.0003, 0.01, 0.9, 10.0, 1.0)

# Apply circular fade to prevent square grid boundary from showing
x_g, y_g, z_g = mesh_grid(n, sizes)
r_xy = np.sqrt(x_g**2 + y_g**2)
fade = np.clip((1.0 - r_xy) / 0.15, 0, 1)
a_arr *= fade

a_pad = np.pad(a_arr, 1)
print("Extracting isosurface (marching cubes) ...")
verts, faces, _, _ = marching_cubes(a_pad, 0.5)
verts -= 1
verts /= n
verts[:, :2] -= 1
print(f"Laplacian mesh: {len(verts)} verts, {len(faces)} faces")

# ── Create Blender mesh ────────────────────────────────────────────────────
mesh = bpy.data.meshes.new("CauliflowerBaseCoralFactory")
mesh.from_pydata(verts.tolist(), [], faces.tolist())
mesh.update()

obj = bpy.data.objects.new("CauliflowerBaseCoralFactory", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bpy.ops.object.editmode_toggle()
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.editmode_toggle()

# ── geo_extension via Geometry Nodes (exact match to decorate.py) ──────────
# offset = pos * (Musgrave(normalize(pos) + rand_offset, scale) + 0.25) * strength
noise_strength = float(uniform(0.1, 0.2))
noise_scale = float(uniform(1.4, 2.8))
rand_offset = list(uniform(-1, 1, 3).astype(float))
print(f"geo_extension: noise_strength={noise_strength:.3f}, noise_scale={noise_scale:.3f}")

ng = bpy.data.node_groups.new("geo_extension", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

inp = ng.nodes.new("NodeGroupInput")
out = ng.nodes.new("NodeGroupOutput")
pos = ng.nodes.new("GeometryNodeInputPosition")

vec_len = ng.nodes.new("ShaderNodeVectorMath"); vec_len.operation = "LENGTH"
ng.links.new(pos.outputs["Position"], vec_len.inputs[0])
div = ng.nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"
div.inputs[0].default_value = 1.0
ng.links.new(vec_len.outputs["Value"], div.inputs[1])
norm = ng.nodes.new("ShaderNodeVectorMath"); norm.operation = "SCALE"
ng.links.new(pos.outputs["Position"], norm.inputs[0])
ng.links.new(div.outputs[0], norm.inputs["Scale"])

add_off = ng.nodes.new("ShaderNodeVectorMath"); add_off.operation = "ADD"
ng.links.new(norm.outputs["Vector"], add_off.inputs[0])
add_off.inputs[1].default_value = rand_offset

try:
    tex = ng.nodes.new("ShaderNodeTexMusgrave")
    tex.musgrave_dimensions = "3D"
    ng.links.new(add_off.outputs["Vector"], tex.inputs["Vector"])
    tex.inputs["Scale"].default_value = noise_scale
    noise_out = tex.outputs["Fac"]
except:
    tex = ng.nodes.new("ShaderNodeTexNoise")
    tex.noise_dimensions = "3D"
    ng.links.new(add_off.outputs["Vector"], tex.inputs["Vector"])
    tex.inputs["Scale"].default_value = noise_scale
    noise_out = tex.outputs[0]

add_b = ng.nodes.new("ShaderNodeMath"); add_b.operation = "ADD"
add_b.inputs[1].default_value = 0.25
ng.links.new(noise_out, add_b.inputs[0])
mul_s = ng.nodes.new("ShaderNodeMath"); mul_s.operation = "MULTIPLY"
mul_s.inputs[1].default_value = noise_strength
ng.links.new(add_b.outputs[0], mul_s.inputs[0])

sc = ng.nodes.new("ShaderNodeVectorMath"); sc.operation = "SCALE"
ng.links.new(pos.outputs["Position"], sc.inputs[0])
ng.links.new(mul_s.outputs[0], sc.inputs["Scale"])

sp = ng.nodes.new("GeometryNodeSetPosition")
ng.links.new(inp.outputs[0], sp.inputs["Geometry"])
ng.links.new(sc.outputs["Vector"], sp.inputs["Offset"])
ng.links.new(sp.outputs[0], out.inputs[0])

mod = obj.modifiers.new("GeoExt", "NODES")
mod.node_group = ng
bpy.ops.object.modifier_apply(modifier="GeoExt")

# ── SUBSURF level 1 ───────────────────────────────────────────────────────
m_s = obj.modifiers.new("Sub", "SUBSURF")
m_s.levels = 1; m_s.render_levels = 1
bpy.ops.object.modifier_apply(modifier="Sub")

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
obj.name = "CauliflowerBaseCoralFactory"
print(f"Done: CauliflowerBaseCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
