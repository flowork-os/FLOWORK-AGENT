# [FL_INDEX: keywords="blender_factory, procedural_3d, StarBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: StarBaseCoralFactory | Category: factories_tex
# Prompt: A white base mesh 3D model of a star coral structure. The object shows a rounded, squat dome shape densely covered in raised cylindrical ring elements — each ring representing an individual polyp cup with an open hollow center, arrayed tightly across the entire dome surface. Without any texture or material color, the pure white geometry clearly reveals the regular pattern of protruding rings and hollow openings, with a wavy perimeter at the base where the rings meet the ground plane.

import os
import bpy
import bmesh
import numpy as np
from mathutils import Vector

SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
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
    """
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

_mat_seed = ((SEED + 1) * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
_seed_all(_mat_seed)
_coral_base_hue = _build_base_hue()
CORAL_MAT = make_coral_material(_coral_base_hue, "StarBaseCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)

# ── Clean scene ───────────────────────────────────────────────────────────────
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)

resolution = 16  # Array count = resolution + 1 = 17

# ── Helper: apply GeoNodes modifier ──────────────────────────────────────────
def apply_geomod(obj, tree, name="GN"):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    gn = obj.modifiers.new(name, 'NODES')
    gn.node_group = tree
    bpy.ops.object.modifier_apply(modifier=name)

# ══════════════════════════════════════════════════════════════════════════════
# GeoNodes tree builders
# ══════════════════════════════════════════════════════════════════════════════

def make_geo_dual_mesh():
    """SetPosition(random ±0.05) → DualMesh"""
    tree = bpy.data.node_groups.new("geo_dual_mesh", 'GeometryNodeTree')
    for n in tree.nodes:
        tree.nodes.remove(n)

    inp = tree.nodes.new('NodeGroupInput');  inp.location = (-600, 0)
    out = tree.nodes.new('NodeGroupOutput'); out.location = (400, 0)
    tree.interface.new_socket('Geometry', in_out='INPUT',  socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Random offset ±0.05 per vertex
    rnd = tree.nodes.new('FunctionNodeRandomValue')
    rnd.location = (-400, -200)
    rnd.data_type = 'FLOAT_VECTOR'
    rnd.inputs[0].default_value = (-0.05, -0.05, -0.05)
    rnd.inputs[1].default_value = (0.05, 0.05, 0.05)

    sp = tree.nodes.new('GeometryNodeSetPosition')
    sp.location = (-200, 0)
    tree.links.new(inp.outputs[0], sp.inputs['Geometry'])
    tree.links.new(rnd.outputs[0], sp.inputs['Offset'])

    dm = tree.nodes.new('GeometryNodeDualMesh')
    dm.location = (0, 0)
    tree.links.new(sp.outputs[0], dm.inputs['Mesh'])
    tree.links.new(dm.outputs[0], out.inputs[0])
    return tree

def make_geo_separate_faces():
    """SeparateGeometry(z>0) → SplitEdges → ScaleElements(0.9-1.2)
       → StoreNamedAttribute('custom_normal')"""
    tree = bpy.data.node_groups.new("geo_separate_faces", 'GeometryNodeTree')
    for n in tree.nodes:
        tree.nodes.remove(n)

    inp = tree.nodes.new('NodeGroupInput');  inp.location = (-800, 0)
    out = tree.nodes.new('NodeGroupOutput'); out.location = (800, 0)
    tree.interface.new_socket('Geometry', in_out='INPUT',  socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Position → Z component
    pos = tree.nodes.new('GeometryNodeInputPosition');  pos.location = (-600, -200)
    sep = tree.nodes.new('ShaderNodeSeparateXYZ');       sep.location = (-400, -200)
    tree.links.new(pos.outputs[0], sep.inputs[0])

    # Z > 0
    cmp = tree.nodes.new('FunctionNodeCompare')
    cmp.location = (-200, -200)
    cmp.data_type = 'FLOAT'
    cmp.operation = 'GREATER_THAN'
    tree.links.new(sep.outputs['Z'], cmp.inputs[0])
    cmp.inputs[1].default_value = 0.0

    # SeparateGeometry
    sg = tree.nodes.new('GeometryNodeSeparateGeometry')
    sg.location = (-200, 0)
    tree.links.new(inp.outputs[0], sg.inputs[0])
    tree.links.new(cmp.outputs[0], sg.inputs[1])

    # SplitEdges
    se = tree.nodes.new('GeometryNodeSplitEdges')
    se.location = (0, 0)
    tree.links.new(sg.outputs[0], se.inputs[0])

    # ScaleElements with random scale per face
    rnd = tree.nodes.new('FunctionNodeRandomValue')
    rnd.location = (0, -200)
    rnd.data_type = 'FLOAT'
    rnd.inputs[2].default_value = 0.9   # Min (Float socket at idx 2)
    rnd.inputs[3].default_value = 1.2   # Max (Float socket at idx 3)

    sce = tree.nodes.new('GeometryNodeScaleElements')
    sce.location = (200, 0)
    tree.links.new(se.outputs[0], sce.inputs[0])        # Geometry
    tree.links.new(rnd.outputs[1], sce.inputs['Scale'])  # Float output at idx 1

    # InputNormal → StoreNamedAttribute("custom_normal", FLOAT_VECTOR)
    nrm = tree.nodes.new('GeometryNodeInputNormal')
    nrm.location = (200, -200)

    sna = tree.nodes.new('GeometryNodeStoreNamedAttribute')
    sna.location = (400, 0)
    sna.data_type = 'FLOAT_VECTOR'
    sna.domain = 'POINT'
    tree.links.new(sce.outputs[0], sna.inputs['Geometry'])
    sna.inputs['Name'].default_value = "custom_normal"
    # Connect normal to the first Value socket
    for s in sna.inputs:
        if s.name == 'Value':
            tree.links.new(nrm.outputs[0], s)
            break

    tree.links.new(sna.outputs[0], out.inputs[0])
    return tree

def make_geo_flower(size, res, anchor):
    """Bell-curve displacement along stored normals.
    t = floor(Index/size) / resolution
    offset = FloatCurve(t) * custom_normal
    Also stores 'outermost' attribute (0.4 < t < 0.6).
    """
    tree = bpy.data.node_groups.new("geo_flower", 'GeometryNodeTree')
    for n in tree.nodes:
        tree.nodes.remove(n)

    inp = tree.nodes.new('NodeGroupInput');  inp.location = (-1000, 0)
    out = tree.nodes.new('NodeGroupOutput'); out.location = (800, 0)
    tree.interface.new_socket('Geometry', in_out='INPUT',  socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # t = floor(Index / size) / resolution
    idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (-800, -200)

    d1 = tree.nodes.new('ShaderNodeMath'); d1.location = (-600, -200)
    d1.operation = 'DIVIDE'
    tree.links.new(idx.outputs[0], d1.inputs[0])
    d1.inputs[1].default_value = float(size)

    fl = tree.nodes.new('ShaderNodeMath'); fl.location = (-400, -200)
    fl.operation = 'FLOOR'
    tree.links.new(d1.outputs[0], fl.inputs[0])

    d2 = tree.nodes.new('ShaderNodeMath'); d2.location = (-200, -200)
    d2.operation = 'DIVIDE'
    tree.links.new(fl.outputs[0], d2.inputs[0])
    d2.inputs[1].default_value = float(res)

    # FloatCurve: bell shape (0,0) → anchor → (1,0)
    fc = tree.nodes.new('ShaderNodeFloatCurve')
    fc.location = (0, -200)
    tree.links.new(d2.outputs[0], fc.inputs[1])  # Value input at index 1
    c = fc.mapping.curves[0]
    c.points[0].location = (0.0, 0.0);   c.points[0].handle_type = 'AUTO'
    c.points[1].location = anchor;        c.points[1].handle_type = 'AUTO'
    pt = c.points.new(1.0, 0.0);         pt.handle_type = 'AUTO'
    fc.mapping.use_clip = False
    fc.mapping.update()

    # NamedAttribute("custom_normal")
    na = tree.nodes.new('GeometryNodeInputNamedAttribute')
    na.location = (0, -400)
    na.data_type = 'FLOAT_VECTOR'
    na.inputs['Name'].default_value = "custom_normal"

    # offset = curve_val * normal
    sc = tree.nodes.new('ShaderNodeVectorMath')
    sc.location = (200, -300)
    sc.operation = 'SCALE'
    tree.links.new(na.outputs[0], sc.inputs[0])       # Vector (Attribute)
    tree.links.new(fc.outputs[0], sc.inputs['Scale'])  # Scale factor

    # SetPosition
    sp = tree.nodes.new('GeometryNodeSetPosition')
    sp.location = (400, 0)
    tree.links.new(inp.outputs[0], sp.inputs['Geometry'])
    tree.links.new(sc.outputs[0], sp.inputs['Offset'])

    # Store "outermost": 0.4 < t < 0.6
    gt = tree.nodes.new('FunctionNodeCompare')
    gt.location = (0, -600)
    gt.data_type = 'FLOAT'; gt.operation = 'GREATER_THAN'
    tree.links.new(d2.outputs[0], gt.inputs[0])
    gt.inputs[1].default_value = 0.4

    lt = tree.nodes.new('FunctionNodeCompare')
    lt.location = (0, -800)
    lt.data_type = 'FLOAT'; lt.operation = 'LESS_THAN'
    tree.links.new(d2.outputs[0], lt.inputs[0])
    lt.inputs[1].default_value = 0.6

    ba = tree.nodes.new('FunctionNodeBooleanMath')
    ba.location = (200, -700)
    ba.operation = 'AND'
    tree.links.new(gt.outputs[0], ba.inputs[0])
    tree.links.new(lt.outputs[0], ba.inputs[1])

    so = tree.nodes.new('GeometryNodeStoreNamedAttribute')
    so.location = (600, 0)
    so.data_type = 'BOOLEAN'
    so.domain = 'POINT'
    tree.links.new(sp.outputs[0], so.inputs['Geometry'])
    so.inputs['Name'].default_value = "outermost"
    for s in so.inputs:
        if s.name == 'Value':
            tree.links.new(ba.outputs[0], s)
            break

    tree.links.new(so.outputs[0], out.inputs[0])
    return tree

def make_geo_extension(noise_strength=0.2, noise_scale=2.0):
    """Radial noise displacement (replicates decorate.geo_extension)."""
    ns = np.random.uniform(noise_strength / 2, noise_strength)
    sc_val = np.random.uniform(noise_scale * 0.7, noise_scale * 1.4)
    off = tuple(np.random.uniform(-1, 1, 3))

    tree = bpy.data.node_groups.new("geo_extension", 'GeometryNodeTree')
    for n in tree.nodes:
        tree.nodes.remove(n)

    inp_n = tree.nodes.new('NodeGroupInput');  inp_n.location = (-1200, 0)
    out_n = tree.nodes.new('NodeGroupOutput'); out_n.location = (800, 0)
    tree.interface.new_socket('Geometry', in_out='INPUT',  socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # InputPosition
    pos = tree.nodes.new('GeometryNodeInputPosition'); pos.location = (-1000, -200)

    # Normalize: direction = pos / length(pos)
    vlen = tree.nodes.new('ShaderNodeVectorMath')
    vlen.location = (-800, -400)
    vlen.operation = 'LENGTH'
    tree.links.new(pos.outputs[0], vlen.inputs[0])

    inv = tree.nodes.new('ShaderNodeMath')
    inv.location = (-600, -400)
    inv.operation = 'DIVIDE'
    inv.inputs[0].default_value = 1.0
    tree.links.new(vlen.outputs['Value'], inv.inputs[1])

    norm_dir = tree.nodes.new('ShaderNodeVectorMath')
    norm_dir.location = (-600, -200)
    norm_dir.operation = 'SCALE'
    tree.links.new(pos.outputs[0], norm_dir.inputs[0])
    tree.links.new(inv.outputs[0], norm_dir.inputs['Scale'])

    # direction + random offset
    add_off = tree.nodes.new('ShaderNodeVectorMath')
    add_off.location = (-400, -200)
    add_off.operation = 'ADD'
    tree.links.new(norm_dir.outputs[0], add_off.inputs[0])
    add_off.inputs[1].default_value = off

    # Noise texture
    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.location = (-200, -200)
    noise.noise_dimensions = '3D'
    tree.links.new(add_off.outputs[0], noise.inputs['Vector'])
    noise.inputs['Scale'].default_value = sc_val

    # (noise_val + 0.25) * noise_strength
    add_c = tree.nodes.new('ShaderNodeMath')
    add_c.location = (0, -200)
    add_c.operation = 'ADD'
    tree.links.new(noise.outputs[0], add_c.inputs[0])
    add_c.inputs[1].default_value = 0.25

    mul_s = tree.nodes.new('ShaderNodeMath')
    mul_s.location = (200, -200)
    mul_s.operation = 'MULTIPLY'
    tree.links.new(add_c.outputs[0], mul_s.inputs[0])
    mul_s.inputs[1].default_value = ns

    # offset = pos * scalar
    ofs = tree.nodes.new('ShaderNodeVectorMath')
    ofs.location = (400, -200)
    ofs.operation = 'SCALE'
    tree.links.new(pos.outputs[0], ofs.inputs[0])
    tree.links.new(mul_s.outputs[0], ofs.inputs['Scale'])

    # SetPosition
    sp = tree.nodes.new('GeometryNodeSetPosition')
    sp.location = (600, 0)
    tree.links.new(inp_n.outputs[0], sp.inputs['Geometry'])
    tree.links.new(ofs.outputs[0], sp.inputs['Offset'])

    tree.links.new(sp.outputs[0], out_n.inputs[0])
    return tree

# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

# ── Step 1: Base icosphere ────────────────────────────────────────────────────
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0)
obj = bpy.context.active_object
obj.name = "star_base"
obj.location[2] = np.random.uniform(0.25, 0.5)
bpy.ops.object.transform_apply(location=True)
print(f"Step 1: icosphere verts={len(obj.data.vertices)} faces={len(obj.data.polygons)}")

# ── Step 2: DualMesh ─────────────────────────────────────────────────────────
apply_geomod(obj, make_geo_dual_mesh(), "DualMesh")
print(f"Step 2: DualMesh verts={len(obj.data.vertices)} faces={len(obj.data.polygons)}")

# ── Step 3: Flatten bottom hemisphere ─────────────────────────────────────────
bm = bmesh.new()
bm.from_mesh(obj.data)
for v in bm.verts:
    z = v.co.z
    v.co.z = z - 0.9 * min(z, 0)
bm.to_mesh(obj.data)
bm.free()
obj.data.update()

# ── Step 4: Clone → rings; SubSurf(3) base; ShrinkWrap rings → base ──────────
# Clone
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.duplicate()
rings_obj = bpy.context.active_object
rings_obj.name = "rings"

# SubSurf(3) on base
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
ms = obj.modifiers.new("Sub", "SUBSURF")
ms.levels = 3; ms.render_levels = 3
bpy.ops.object.modifier_apply(modifier="Sub")
print(f"Step 4a: base SubSurf verts={len(obj.data.vertices)}")

# ShrinkWrap rings → smoothed base
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = rings_obj
rings_obj.select_set(True)
msw = rings_obj.modifiers.new("SW", "SHRINKWRAP")
msw.target = obj
bpy.ops.object.modifier_apply(modifier="SW")

# ── Step 5: geo_separate_faces on rings ───────────────────────────────────────
apply_geomod(rings_obj, make_geo_separate_faces(), "SepFaces")
print(f"Step 5: separate_faces verts={len(rings_obj.data.vertices)} "
      f"faces={len(rings_obj.data.polygons)}")

# ── Step 6: SubSurf(3) + hollow rings ────────────────────────────────────────
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = rings_obj
rings_obj.select_set(True)
ms2 = rings_obj.modifiers.new("Sub2", "SUBSURF")
ms2.levels = 3; ms2.render_levels = 3
bpy.ops.object.modifier_apply(modifier="Sub2")
print(f"Step 6a: rings SubSurf verts={len(rings_obj.data.vertices)}")

# Hollow: select all → region_to_loop → invert → delete interior verts
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.region_to_loop()
bpy.ops.mesh.select_all(action='INVERT')
bpy.ops.mesh.delete(type='VERT')
bpy.ops.object.mode_set(mode='OBJECT')
print(f"Step 6b: hollow rings verts={len(rings_obj.data.vertices)}")

# ── Step 7: Split + Array + Bridge + geo_flower ──────────────────────────────
# Split into loose parts
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = rings_obj
rings_obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')

# Collect all ring pieces
ring_pieces = [o for o in bpy.data.objects if o != obj and o.type == 'MESH']
print(f"Step 7: {len(ring_pieces)} ring pieces")

flowers = []
for ring in ring_pieces:
    size = len(ring.data.vertices)
    if size < 3:
        bpy.data.objects.remove(ring, do_unlink=True)
        continue

    center = np.mean([list(v.co) for v in ring.data.vertices], axis=0)

    # Create empty at origin with progressive scale
    s = np.random.uniform(0.3, 0.5) ** (1.0 / resolution)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    empty = bpy.context.active_object

    empty.scale = (s, s, s)

    # Array modifier
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ring
    ring.select_set(True)
    m_arr = ring.modifiers.new("Arr", "ARRAY")
    m_arr.use_relative_offset = False
    m_arr.use_object_offset = True
    m_arr.count = resolution + 1
    m_arr.offset_object = empty
    bpy.ops.object.modifier_apply(modifier="Arr")
    bpy.data.objects.remove(empty, do_unlink=True)

    # Edit mode: bridge + center-adjust + close
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ring
    ring.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bridge_edge_loops()

    # Center-adjust each copy
    ebm = bmesh.from_edit_mesh(ring.data)
    ebm.verts.ensure_lookup_table()
    for i in range(1, resolution + 1):
        verts_slice = ebm.verts[i * size : (i + 1) * size]
        c = np.mean([list(v.co) for v in verts_slice], axis=0)
        offset = center - c
        for v in verts_slice:
            v.co += Vector(offset)
    bmesh.update_edit_mesh(ring.data)

    # Close open ends
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.bridge_edge_loops()

    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply geo_flower
    anchor = (np.random.uniform(0.4, 0.6), np.random.uniform(0.08, 0.15))
    apply_geomod(ring, make_geo_flower(size, resolution, anchor), "Flower")

    flowers.append(ring)

print(f"Total flowers: {len(flowers)}")

# ── Step 8: Join + geo_extension ──────────────────────────────────────────────
bpy.ops.object.select_all(action='DESELECT')
for f in flowers:
    f.select_set(True)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.join()

apply_geomod(obj, make_geo_extension(), "Extension")

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "StarBaseCoralFactory"
print(f"Done: StarBaseCoralFactory  verts={len(obj.data.vertices)}  "
      f"faces={len(obj.data.polygons)}")

