# [FL_INDEX: keywords="blender_factory, procedural_3d, ReactionDiffusionBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: ReactionDiffusionBaseCoralFactory | Category: factories_tex
# Prompt: A white base mesh 3D model of a reaction-diffusion coral structure. The object displays a rounded dome shape with a surface patterned by deeply pitted cells and raised ridges generated through a reaction-diffusion algorithm, creating an irregular, organic cellular texture across the entire dome. Without any texture or material color, the white mesh reveals the complex network of small concave cells and interconnecting ridges at varying scales, with a dark shadow at the base contrasting with the white geometry above.

"""
Standalone Blender script (geometry + coral material) – Brain / Honeycomb coral, seed 0.
Run:  blender --background --python coral_reaction_diffusion_bpy.py

Direct port of reaction_diffusion.py + mesh.py:build_convex_mesh():
  Brain    – feed=0.055, kill=sqrt(feed)/2-feed, n_instances=100, stride=0.02
  Honeycomb – feed=0.070, kill=…-0.001,          n_instances=5,   stride=0.1

Pipeline (replicates ReactionDiffusionBaseCoralFactory.reaction_diffusion_make()):
  1. build_convex_mesh() → irregular polygon prism (base scaffold)
  2. new_icosphere(subdivisions=5, radius=3) → growth substrate
  3. reaction_diffusion() on icosphere mesh edges (Gray-Scott, 500 steps)
  4. SHRINKWRAP icosphere → convex base
  5. geo_extension → DISPLACE(CLOUDS)
  6. DISPLACE by vertex group B (strength=0.4)
  7. Delete convex base
"""
import os
import bpy
import bmesh
import math
import numpy as np

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
CORAL_MAT = make_coral_material(_coral_base_hue, "ReactionDiffusionBaseCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)

# ── Choose Brain or Honeycomb based on seed ─────────────────────────────────
maker = np.random.choice(['brain', 'honeycomb'], p=[0.5, 0.5])
print(f"Coral type: {maker}")

def feed2kill(feed):
    return math.sqrt(feed) / 2 - feed

if maker == 'brain':
    feed_rate  = 0.055
    kill_rate  = feed2kill(feed_rate)
    n_inst, stride = 100, 0.02
else:
    feed_rate  = 0.070
    kill_rate  = feed2kill(feed_rate) - 0.001
    n_inst, stride = 5, 0.1

# ── build_convex_mesh(): irregular polygon prism ─────────────────────────────
def polygon_angles(n):
    for _ in range(100):
        angles = np.sort(np.random.uniform(0, 2*np.pi, n))
        diff = (angles - np.roll(angles, 1)) % (2*np.pi)
        if (diff >= np.pi/6).all() and (diff <= 2*np.pi/3).all():
            return angles
    return np.sort((np.arange(n) * (2*np.pi/n) + np.random.uniform(0, 2*np.pi)) % (2*np.pi))

n_sides = 6
angs = polygon_angles(n_sides)
height = 0.2; tilt = 0.2
a_up = np.random.uniform(-np.pi/18, 0,       n_sides)
a_lo = np.random.uniform(0,          np.pi/18, n_sides)
z_up = 1 + np.random.normal(0, height, n_sides) + np.random.uniform(0, tilt) * np.cos(angs + np.random.uniform(-np.pi, np.pi))
z_lo = 1 + np.random.normal(0, height, n_sides) + np.random.uniform(0, tilt) * np.cos(angs + np.random.uniform(-np.pi, np.pi))
R = 1.8
verts_c = np.block([
    [R*np.cos(angs+a_up), R*np.cos(angs+a_lo), 0, 0],
    [R*np.sin(angs+a_up), R*np.sin(angs+a_lo), 0, 0],
    [z_up, -z_lo, z_up.max()+np.random.uniform(0.1,0.2), -z_lo.max()-np.random.uniform(0.1,0.2)],
]).T
ri = np.arange(n_sides);  si = np.roll(ri, -1)
faces_c = np.block([
    [ri, ri, ri+n_sides, si+n_sides],
    [si, ri+n_sides, si+n_sides, ri+n_sides],
    [np.full(n_sides, 2*n_sides), si, si, np.full(n_sides, 2*n_sides+1)],
]).T

mesh_c = bpy.data.meshes.new("coral_base")
mesh_c.from_pydata(verts_c.tolist(), [], faces_c.tolist())
mesh_c.update()
obj_base = bpy.data.objects.new("coral_base", mesh_c)
bpy.context.collection.objects.link(obj_base)

# SUBSURF level 2 on convex base (matches original)
bpy.context.view_layer.objects.active = obj_base
obj_base.select_set(True)
m_sub = obj_base.modifiers.new("Sub", "SUBSURF")
m_sub.levels = 2;  m_sub.render_levels = 2
bpy.ops.object.modifier_apply(modifier="Sub")
bpy.ops.object.select_all(action='DESELECT')

# ── Icosphere as reaction-diffusion substrate ────────────────────────────────
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=8, radius=3.0)
obj = bpy.context.active_object
obj.name = "ReactionDiffusionBaseCoralFactory"

# ── Gray-Scott reaction diffusion on mesh graph ──────────────────────────────
def make_weight(coords):
    """make_periodic_weight_fn: periodic cosine pattern → binary 0/1 on vertices."""

    rng = np.random.default_rng(42)
    mult   = rng.uniform(20, 100, (1, n_inst))
    center = coords[rng.integers(0, len(coords)-1, n_inst)]
    phi    = (coords[:, np.newaxis, :] * center[np.newaxis, :, :]).sum(-1) * mult
    measure = np.cos(phi).sum(-1) / math.sqrt(n_inst)
    return (np.abs(measure) < stride).astype(float)

print(f"Running Gray-Scott RD (ReactionDiffusionBaseCoralFactory, {len(obj.data.vertices)} verts, 1000 steps) ...")
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
n_v = len(bm.verts)
coords    = np.array([v.co[:] for v in bm.verts])
edge_from = np.array([e.verts[0].index for e in bm.edges])
edge_to   = np.array([e.verts[1].index for e in bm.edges])
size      = max(len(v.link_edges) for v in bm.verts)
bm.free()

a_rd = np.ones(n_v,  dtype=np.float64)
b_rd = make_weight(coords)
diff_a = 0.18 * 0.5;  diff_b = 0.09 * 0.5

for _ in range(1000):
    a_msg = a_rd[edge_to] - a_rd[edge_from]
    b_msg = b_rd[edge_to] - b_rd[edge_from]
    lap_a = np.bincount(edge_from, a_msg, size) - np.bincount(edge_to, a_msg, size)
    lap_b = np.bincount(edge_from, b_msg, size) - np.bincount(edge_to, b_msg, size)
    ab2   = a_rd * b_rd**2
    a_rd  = a_rd + (diff_a*lap_a - ab2 + feed_rate*(1-a_rd))
    b_rd  = b_rd + (diff_b*lap_b + ab2 - (kill_rate+feed_rate)*b_rd)

b_rd *= 1 + np.random.normal(0, 0.05, n_v)

vg_b = obj.vertex_groups.new(name="B")
for i in range(n_v):
    vg_b.add([i], float(np.clip(b_rd[i], 0, 1)), "REPLACE")

# ── Shrinkwrap icosphere onto convex base ────────────────────────────────────
centroid = verts_c.mean(axis=0)
obj.location = tuple(centroid)
bpy.ops.object.transform_apply(location=True)

m_sw = obj.modifiers.new("Shrink", "SHRINKWRAP")
m_sw.target = obj_base
m_sw.wrap_method = 'PROJECT'
m_sw.use_negative_direction = True
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier="Shrink")

obj.location[2] = 1.0
bpy.ops.object.transform_apply(location=True)

# geo_extension → DISPLACE(CLOUDS)
tex = bpy.data.textures.new("rd_ext", type='CLOUDS')
tex.noise_scale = 0.5
m_ext = obj.modifiers.new("Ext", "DISPLACE")
m_ext.texture = tex;  m_ext.strength = 0.05;  m_ext.mid_level = 0
bpy.ops.object.modifier_apply(modifier="Ext")

# Displace by vertex group B
m_b = obj.modifiers.new("B_Disp", "DISPLACE")
m_b.strength = 0.4;  m_b.mid_level = 0.0;  m_b.vertex_group = "B"
bpy.ops.object.modifier_apply(modifier="B_Disp")

# Remove scaffold
bpy.data.objects.remove(obj_base, do_unlink=True)

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "ReactionDiffusionBaseCoralFactory"
print(f"Done: ReactionDiffusionBaseCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")

