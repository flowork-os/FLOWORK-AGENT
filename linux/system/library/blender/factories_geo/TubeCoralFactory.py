# [FL_INDEX: keywords="blender_factory, procedural_3d, TubeCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TubeCoralFactory | Category: factories_geo
# Prompt: A tube coral rendered as a textured 3D model. The coral features multiple thick, upright cylindrical finger-like tubes growing upward from a shared base, fanning outward in a hand-like arrangement. The entire surface of each tube is covered in dense granular polyp bumps giving a rough, coarse texture. The coloring is warm sandy beige with muted olive-green tones and subtle pink blush highlights. The finger-like tubes vary slightly in height and lean outward, creating a distinctive splayed silhouette on the white background.

"""
Standalone Blender script (geometry + coral material) – TubeCoralFactory, seed 0.
Run:  blender --background --python TubeCoralFactory.py

TubeBaseCoralFactory base shape + CoralFactory postprocess:
  scale normalization + voxel remesh + noise/bump displacement.

Pipeline:
  icosphere(2) → GeoNodes: SetPosition(perturb ±0.2) → DualMesh →
  6× (ExtrudeMesh + ScaleElements) → DeleteGeometry(top faces) →
  BEVEL(10%, 1seg) + SOLIDIFY(0.05) + SUBSURF(2) + DISPLACE(STUCCI, 0.1) →
  scale to [0.7]*3 normalized → voxel remesh(0.01) → noise/bump displace
"""
import os
import random
import colorsys
import bpy
import numpy as np
import math


SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
#  Coral material — translated from generate.py:shader_coral (raw bpy)
# ═══════════════════════════════════════════════════════════════════════════

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


# Phase 1: material sampling (mirrors CoralFactory.__init__ with FixedSeed)
# from FixedSeed(factory_seed). To get equivalent diversity, we hash the seed for material
# sampling (otherwise consecutive seeds all produce similar warm-red hues).
_mat_seed = ((SEED + 1) * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
_seed_all(_mat_seed)
_coral_base_hue = _build_base_hue()
CORAL_MAT = make_coral_material(_coral_base_hue, "TubeCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)


# ── Clean scene ───────────────────────────────────────────────────────────────
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)


def apply_geomod(obj, tree, name="GN"):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    gn = obj.modifiers.new(name, 'NODES')
    gn.node_group = tree
    bpy.ops.object.modifier_apply(modifier=name)


def make_geo_coral_tube():
    """Build GeoNodes tree replicating tube.py geo_coral_tube exactly.

    icosphere → perturb → DualMesh → 6× (ExtrudeMesh + ScaleElements) →
    DeleteGeometry(top faces)
    """
    # ── Parameters (match tube.py hardcoded constants) ──
    ico_sphere_perturb = 0.2
    growth_z = 1
    short_length_range = (0.2, 0.4)
    long_length_range = (0.4, 1.2)
    angles = np.linspace(np.pi * 2 / 5, np.pi / 10, 6)
    scales = np.linspace(1, 0.9, 6)
    face_perturb = 0.4
    growth_prob = 0.75
    seed = np.random.randint(1000)

    tree = bpy.data.node_groups.new("geo_coral_tube", 'GeometryNodeTree')
    for n in tree.nodes:
        tree.nodes.remove(n)

    inp = tree.nodes.new('NodeGroupInput');  inp.location = (-2400, 0)
    out = tree.nodes.new('NodeGroupOutput'); out.location = (6000, 0)
    tree.interface.new_socket('Geometry', in_out='INPUT',  socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # ── SetPosition: perturb vertices ±0.2 ──
    rnd_perturb = tree.nodes.new('FunctionNodeRandomValue')
    rnd_perturb.location = (-2200, -200)
    rnd_perturb.data_type = 'FLOAT_VECTOR'
    rnd_perturb.inputs[0].default_value = (-ico_sphere_perturb,) * 3
    rnd_perturb.inputs[1].default_value = (ico_sphere_perturb,) * 3
    rnd_perturb.inputs[8].default_value = seed  # Seed

    set_pos = tree.nodes.new('GeometryNodeSetPosition')
    set_pos.location = (-2000, 0)
    tree.links.new(inp.outputs[0], set_pos.inputs['Geometry'])
    tree.links.new(rnd_perturb.outputs[0], set_pos.inputs['Offset'])

    # ── DualMesh: convert triangles to pentagons/hexagons ──
    dual = tree.nodes.new('GeometryNodeDualMesh')
    dual.location = (-1800, 0)
    tree.links.new(set_pos.outputs[0], dual.inputs[0])

    # ── InputNormal + SeparateXYZ (shared by all iterations) ──
    normal_node = tree.nodes.new('GeometryNodeInputNormal')
    normal_node.location = (-1600, -600)

    sep_xyz = tree.nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (-1400, -600)
    tree.links.new(normal_node.outputs[0], sep_xyz.inputs[0])

    # ── Initial "top" selection: upward-facing AND bernoulli(0.75) ──
    cmp_init = tree.nodes.new('FunctionNodeCompare')
    cmp_init.location = (-1200, -600)
    cmp_init.data_type = 'FLOAT'
    cmp_init.operation = 'GREATER_THAN'
    tree.links.new(sep_xyz.outputs[2], cmp_init.inputs[0])  # Z
    cmp_init.inputs[1].default_value = float(np.cos(angles[0]))

    # Bernoulli: boolean random with probability = growth_prob
    bern = tree.nodes.new('FunctionNodeRandomValue')
    bern.location = (-1200, -800)
    bern.data_type = 'BOOLEAN'
    bern.inputs[6].default_value = growth_prob   # Probability
    bern.inputs[8].default_value = seed          # Seed

    # AND: direction_ok AND bernoulli
    and_node = tree.nodes.new('FunctionNodeBooleanMath')
    and_node.location = (-1000, -600)
    and_node.operation = 'AND'
    tree.links.new(cmp_init.outputs[0], and_node.inputs[0])
    tree.links.new(bern.outputs[3], and_node.inputs[1])  # Boolean at idx 3

    # Track current mesh output and top selection through iterations
    cur_mesh_out = dual.outputs[0]
    cur_top_out = and_node.outputs[0]

    # ── 6 extrusion iterations ──
    for i, (angle, scale) in enumerate(zip(angles, scales)):
        x = -800 + i * 1000
        y_off = 0

        # --- Direction = normalize(normal + (0,0,gz) + noise) ---

        # Random z growth: uniform(0, growth_z)
        rnd_gz = tree.nodes.new('FunctionNodeRandomValue')
        rnd_gz.location = (x, -300)
        rnd_gz.data_type = 'FLOAT'
        rnd_gz.inputs[2].default_value = 0.0
        rnd_gz.inputs[3].default_value = float(growth_z)
        rnd_gz.inputs[8].default_value = seed + i

        # CombineXYZ(0, 0, gz)
        comb_z = tree.nodes.new('ShaderNodeCombineXYZ')
        comb_z.location = (x, -500)
        comb_z.inputs[0].default_value = 0.0
        comb_z.inputs[1].default_value = 0.0
        tree.links.new(rnd_gz.outputs[1], comb_z.inputs[2])

        # normal + (0,0,gz)
        add_nz = tree.nodes.new('ShaderNodeVectorMath')
        add_nz.location = (x + 200, -400)
        add_nz.operation = 'ADD'
        tree.links.new(normal_node.outputs[0], add_nz.inputs[0])
        tree.links.new(comb_z.outputs[0], add_nz.inputs[1])

        # Face perturbation noise: uniform(-face_perturb, face_perturb)
        rnd_fp = tree.nodes.new('FunctionNodeRandomValue')
        rnd_fp.location = (x, -700)
        rnd_fp.data_type = 'FLOAT_VECTOR'
        rnd_fp.inputs[0].default_value = (-face_perturb,) * 3
        rnd_fp.inputs[1].default_value = (face_perturb,) * 3
        rnd_fp.inputs[8].default_value = seed + i

        # (normal + z_offset) + perturbation
        add_fp = tree.nodes.new('ShaderNodeVectorMath')
        add_fp.location = (x + 400, -400)
        add_fp.operation = 'ADD'
        tree.links.new(add_nz.outputs[0], add_fp.inputs[0])
        tree.links.new(rnd_fp.outputs[0], add_fp.inputs[1])

        # Normalize direction
        norm_dir = tree.nodes.new('ShaderNodeVectorMath')
        norm_dir.location = (x + 600, -400)
        norm_dir.operation = 'NORMALIZE'
        tree.links.new(add_fp.outputs[0], norm_dir.inputs[0])

        # --- Length: switch(upward → long, else → short) ---

        # Compare: normal.z > cos(angle)
        cmp_dir = tree.nodes.new('FunctionNodeCompare')
        cmp_dir.location = (x, -900)
        cmp_dir.data_type = 'FLOAT'
        cmp_dir.operation = 'GREATER_THAN'
        tree.links.new(sep_xyz.outputs[2], cmp_dir.inputs[0])
        cmp_dir.inputs[1].default_value = float(np.cos(angle))

        # Long length: uniform(0.4, 1.2)
        rnd_long = tree.nodes.new('FunctionNodeRandomValue')
        rnd_long.location = (x + 200, -1000)
        rnd_long.data_type = 'FLOAT'
        rnd_long.inputs[2].default_value = float(long_length_range[0])
        rnd_long.inputs[3].default_value = float(long_length_range[1])
        rnd_long.inputs[8].default_value = seed + i

        # Short length: uniform(0.2, 0.4)
        rnd_short = tree.nodes.new('FunctionNodeRandomValue')
        rnd_short.location = (x + 200, -1200)
        rnd_short.data_type = 'FLOAT'
        rnd_short.inputs[2].default_value = float(short_length_range[0])
        rnd_short.inputs[3].default_value = float(short_length_range[1])
        rnd_short.inputs[8].default_value = seed + i

        # Switch: upward=True → long, upward=False → short
        switch = tree.nodes.new('GeometryNodeSwitch')
        switch.location = (x + 400, -1000)
        switch.input_type = 'FLOAT'
        tree.links.new(cmp_dir.outputs[0], switch.inputs[0])      # Switch
        tree.links.new(rnd_short.outputs[1], switch.inputs[1])     # False → short
        tree.links.new(rnd_long.outputs[1], switch.inputs[2])      # True → long

        # --- ExtrudeMesh ---
        extrude = tree.nodes.new('GeometryNodeExtrudeMesh')
        extrude.location = (x + 600, y_off)
        tree.links.new(cur_mesh_out, extrude.inputs[0])         # Mesh
        tree.links.new(cur_top_out, extrude.inputs[1])           # Selection
        tree.links.new(norm_dir.outputs[0], extrude.inputs[2])  # Offset
        tree.links.new(switch.outputs[0], extrude.inputs[3])    # Offset Scale

        # --- ScaleElements ---
        scale_elem = tree.nodes.new('GeometryNodeScaleElements')
        scale_elem.location = (x + 800, y_off)
        tree.links.new(extrude.outputs[0], scale_elem.inputs[0])  # Geometry
        tree.links.new(extrude.outputs[1], scale_elem.inputs[1])  # Selection = Top
        scale_elem.inputs[2].default_value = float(scale)         # Scale

        # Update tracked outputs for next iteration
        cur_mesh_out = scale_elem.outputs[0]
        cur_top_out = extrude.outputs[1]  # Top

    # ── Delete top faces (open tube ends) ──
    delete = tree.nodes.new('GeometryNodeDeleteGeometry')
    delete.location = (5600, 0)
    delete.domain = 'FACE'
    tree.links.new(cur_mesh_out, delete.inputs[0])
    tree.links.new(cur_top_out, delete.inputs[1])

    tree.links.new(delete.outputs[0], out.inputs[0])
    return tree


# ══════════════════════════════════════════════════════════════════════════════
# Main: create base mesh (same as TubeBaseCoralFactory)
# ══════════════════════════════════════════════════════════════════════════════

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
obj = bpy.context.active_object
obj.name = "TubeCoralFactory"

# Apply GeoNodes tube extrusion
apply_geomod(obj, make_geo_coral_tube(), "CoralTube")
print(f"After GeoNodes: verts={len(obj.data.vertices)} faces={len(obj.data.polygons)}")

# Post-modifiers (match tube.py create_asset)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# BEVEL: offset_type=PERCENT, width_pct=10, segments=1
m_bev = obj.modifiers.new("Bevel", "BEVEL")
m_bev.offset_type = 'PERCENT'
m_bev.width_pct = 10
m_bev.segments = 1
bpy.ops.object.modifier_apply(modifier="Bevel")

# SOLIDIFY: thickness=0.05
m_sol = obj.modifiers.new("Solidify", "SOLIDIFY")
m_sol.thickness = 0.05
bpy.ops.object.modifier_apply(modifier="Solidify")

# SUBSURF: levels=2
m_sub = obj.modifiers.new("SubSurf", "SUBSURF")
m_sub.levels = 2
m_sub.render_levels = 2
bpy.ops.object.modifier_apply(modifier="SubSurf")

# DISPLACE: STUCCI texture, strength=0.1, mid_level=0
tex = bpy.data.textures.new("tube_coral", type='STUCCI')
m_disp = obj.modifiers.new("Displace", "DISPLACE")
m_disp.texture = tex
m_disp.strength = 0.1
m_disp.mid_level = 0
bpy.ops.object.modifier_apply(modifier="Displace")

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
print(f"After base modifiers: verts={len(obj.data.vertices)} faces={len(obj.data.polygons)}")

# ══════════════════════════════════════════════════════════════════════════════
# CoralFactory postprocess (generate.py create_asset)
# ══════════════════════════════════════════════════════════════════════════════

default_scale = [0.7, 0.7, 0.7]
noise_strength = 0.02
bump_prob = 0.3

# Scale normalization: 2 * default_scale / max(dims_xy) * uniform(0.8, 1.2, 3)
dims = [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z]
max_xy = max(dims[0], dims[1], 1e-6)
scale = 2.0 * np.array(default_scale) / max_xy * np.random.uniform(0.8, 1.2, 3)
obj.scale = tuple(scale)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(scale=True)

# Voxel remesh (face_size=0.01)
m_rem = obj.modifiers.new("Remesh", "REMESH")
m_rem.mode = "VOXEL"
m_rem.voxel_size = 0.01
bpy.ops.object.modifier_apply(modifier="Remesh")
print(f"After remesh: verts={len(obj.data.vertices)} faces={len(obj.data.polygons)}")

# Noise/bump displacement
if noise_strength > 0:
    has_bump = np.random.uniform() < bump_prob
    if has_bump:
        # apply_noise_texture: STUCCI or MARBLE
        tex_type = np.random.choice(['STUCCI', 'MARBLE'])
        tex_n = bpy.data.textures.new("coral_noise", type=tex_type)
        tex_n.noise_scale = math.exp(np.random.uniform(math.log(0.01), math.log(0.02)))
        m_d = obj.modifiers.new("Noise", "DISPLACE")
        m_d.texture = tex_n
        m_d.strength = noise_strength * np.random.uniform(0.9, 1.2)
        m_d.mid_level = 0
    else:
        # apply_bump: VORONOI
        tex_b = bpy.data.textures.new("coral_bump", type='VORONOI')
        tex_b.noise_scale = math.exp(np.random.uniform(math.log(0.02), math.log(0.03)))
        tex_b.noise_intensity = math.exp(np.random.uniform(math.log(1.5), math.log(2.0)))
        tex_b.distance_metric = 'MINKOVSKY'
        tex_b.minkovsky_exponent = np.random.uniform(1, 1.5)
        m_d = obj.modifiers.new("Bump", "DISPLACE")
        m_d.texture = tex_b
        m_d.strength = -noise_strength * np.random.uniform(1, 2)
        m_d.mid_level = 1
    bpy.ops.object.modifier_apply(modifier=m_d.name)

# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "TubeCoralFactory"
print(f"Done: TubeCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
