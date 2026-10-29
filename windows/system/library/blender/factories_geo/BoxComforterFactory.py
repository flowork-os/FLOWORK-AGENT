# [FL_INDEX: keywords="blender_factory, procedural_3d, BoxComforterFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BoxComforterFactory | Category: factories_geo
# Prompt: A 3D model of a box-stitched comforter laid flat, viewed from above at a slight angle. The comforter is rectangular with visible box stitch seam lines dividing it into segments. The surface has a colorful patchwork-like fabric print with pastel pink, lavender, blue, and cream tones. The comforter has a slight thickness and soft edges with a visible folded edge at one side.

import os, bpy, bmesh, random, colorsys
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════

def seed_all(seed):
    np.random.seed(seed); random.seed(seed)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def weighted_sample(reg):
    classes, weights = zip(*reg)
    w = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=w / w.sum()))]

def hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0, float(s), float(v))
    return (r, g, b, 1.0)

def mixture_of_gaussian(means, stds, weights, clamp_min=None, clamp_max=None):
    p = np.array(weights) / np.sum(weights)
    idx = int(np.random.choice(len(p), p=p))
    res = np.random.normal(means[idx], stds[idx])
    if clamp_min is not None: res = np.maximum(res, clamp_min)
    if clamp_max is not None: res = np.minimum(res, clamp_max)
    return res

def leather_hsv():
    return mixture_of_gaussian(
        means=np.array([[0.07, 0.45, 0.40], [0.6, 0.3, 0.40]]),
        stds=0.7 * np.array([[0.0035, 0.0063, 0.2], [0.0105, 0.028, 0.2]]),
        clamp_min=[0, 0, 0.06], clamp_max=[1, 1, 0.93], weights=[0.7, 0.3])

def fabric_hsv():
    return (float(np.random.uniform(0, 1)),
            float(np.random.uniform(0.3, 0.8)),
            float(np.random.uniform(0.6, 0.9)))

# ═══════════════════════════════════════════════════════════════════════════
#  Material helpers
# ═══════════════════════════════════════════════════════════════════════════

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac(node):
    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

def _connect_out(nt, surface, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(surface.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement.outputs[0], out.inputs["Displacement"])

def _principled(nt, **kwargs):
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    for k, v in kwargs.items():
        nm = k.replace("_", " ")
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = v
        elif k == "Specular" and "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = v
    return bsdf

# ═══════════════════════════════════════════════════════════════════════════
#  Fabric shader constructors
# ═══════════════════════════════════════════════════════════════════════════

def make_coarse_knit_fabric(name="CoarseKnitFabric"):
    pattern_mixer     = float(np.random.choice([np.random.uniform(0.0, 0.1),
                                                 np.random.uniform(0.1, 0.9)]))
    pattern_density   = float(np.random.choice([np.random.uniform(0.1, 1.0),
                                                 np.random.uniform(1.0, 10.0)]))
    color             = np.random.uniform(0.0, 1.0, 3)
    brick_knit        = float(np.random.choice([np.random.uniform(0.0, 0.05),
                                                 np.random.uniform(0.05, 0.95),
                                                 np.random.uniform(0.95, 1.0)]))
    knit_resolution   = float(np.random.uniform(0.5, 0.6))
    brick_resolution  = float(np.random.uniform(20.0, 30.0))
    crease_resolution = float(np.random.uniform(50.0, 80.0))
    smoothness        = float(np.random.choice([np.random.uniform(0.0, 0.2),
                                                 np.random.uniform(0.2, 0.5)]))
    color_shader_frac = float(np.random.uniform(0.1, 0.9))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    map1 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], map1.inputs["Vector"])
    map1.inputs["Scale"].default_value = (3.2, 1.0, 1.0)
    brick = nt.nodes.new("ShaderNodeTexBrick")
    ln(map1.outputs["Vector"], brick.inputs["Vector"])
    brick.inputs["Scale"].default_value = brick_resolution
    cr1 = nt.nodes.new("ShaderNodeValToRGB"); ln(brick.outputs["Color"], cr1.inputs["Fac"])
    cr1.color_ramp.elements[0].position = 0.0;  cr1.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr1.color_ramp.elements[1].position = 1.0;  cr1.color_ramp.elements[1].color = (0, 0, 0, 1)
    map2 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], map2.inputs["Vector"])
    map2.inputs["Rotation"].default_value = (0, 0, 0.7854)
    map2.inputs["Scale"].default_value = (238.8, 1.0, 35.6)
    vor1 = nt.nodes.new("ShaderNodeTexVoronoi"); vor1.feature = "F2"
    ln(map2.outputs["Vector"], vor1.inputs["Vector"])
    vor1.inputs["Scale"].default_value = pattern_density; vor1.inputs["Randomness"].default_value = 0.0
    cr2 = nt.nodes.new("ShaderNodeValToRGB"); ln(vor1.outputs["Distance"], cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.1018; cr2.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr2.color_ramp.elements[1].position = 1.0;    cr2.color_ramp.elements[1].color = (0, 0, 0, 1)
    mix_pat = nt.nodes.new("ShaderNodeMix"); mix_pat.data_type = "RGBA"; mix_pat.clamp_result = True
    mix_pat.inputs[0].default_value = pattern_mixer
    ln(cr1.outputs["Color"], mix_pat.inputs[6]); ln(cr2.outputs["Color"], mix_pat.inputs[7])
    bsdf1 = _principled(nt, Specular=0.6309, Roughness=0.9945)
    ln(mix_pat.outputs[2], bsdf1.inputs["Base Color"])
    comb = nt.nodes.new("ShaderNodeCombineColor")
    comb.inputs["Red"].default_value = float(color[0])
    comb.inputs["Green"].default_value = float(color[1])
    comb.inputs["Blue"].default_value = float(color[2])
    bsdf2 = _principled(nt, Specular=0.6309, Roughness=0.9945)
    ln(comb.outputs["Color"], bsdf2.inputs["Base Color"])
    msh = nt.nodes.new("ShaderNodeMixShader"); msh.inputs["Fac"].default_value = color_shader_frac
    ln(bsdf1.outputs["BSDF"], msh.inputs[1]); ln(bsdf2.outputs["BSDF"], msh.inputs[2])
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.use_clamp = True
    inv.inputs[0].default_value = 1.0; ln(cr1.outputs["Color"], inv.inputs[1])
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.use_clamp = True
    ln(inv.outputs[0], sc.inputs[0]); sc.inputs[1].default_value = brick_knit
    map3 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], map3.inputs["Vector"])
    map3.inputs["Rotation"].default_value = (0, 0, 0.6196)
    map3.inputs["Scale"].default_value = (217.5, 176.2, 42.0)
    vor2 = nt.nodes.new("ShaderNodeTexVoronoi"); vor2.feature = "F2"
    ln(map3.outputs["Vector"], vor2.inputs["Vector"])
    vor2.inputs["Scale"].default_value = knit_resolution; vor2.inputs["Randomness"].default_value = 0.0
    map4 = nt.nodes.new("ShaderNodeMapping"); ln(tex_coord.outputs["Object"], map4.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(map4.outputs["Vector"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = crease_resolution
    add_n = nt.nodes.new("ShaderNodeMath"); add_n.use_clamp = True
    ln(_fac(noise), add_n.inputs[0]); add_n.inputs[1].default_value = smoothness
    mul_n = nt.nodes.new("ShaderNodeMath"); mul_n.operation = "MULTIPLY"; mul_n.use_clamp = True
    ln(vor2.outputs["Distance"], mul_n.inputs[0]); ln(add_n.outputs[0], mul_n.inputs[1])
    sub_n = nt.nodes.new("ShaderNodeMath"); sub_n.operation = "SUBTRACT"
    sub_n.inputs[0].default_value = 1.0; sub_n.inputs[1].default_value = brick_knit
    sc1 = nt.nodes.new("ShaderNodeMath"); sc1.operation = "MULTIPLY"
    ln(mul_n.outputs[0], sc1.inputs[0]); ln(sub_n.outputs[0], sc1.inputs[1])
    add1 = nt.nodes.new("ShaderNodeMath"); ln(sc.outputs[0], add1.inputs[0]); ln(sc1.outputs[0], add1.inputs[1])
    disp = nt.nodes.new("ShaderNodeDisplacement"); ln(add1.outputs[0], disp.inputs["Height"])
    disp.inputs["Midlevel"].default_value = 0.4; disp.inputs["Scale"].default_value = 0.01
    _connect_out(nt, msh, disp)
    return mat

def make_fine_knit_fabric(name="FineKnitFabric"):
    color = np.random.uniform(0.2, 1.0, 3)
    roughness = float(np.random.uniform(0, 1.0))
    thread_density_x = float(np.random.uniform(100, 300))
    relative_density_y = float(np.random.uniform(0.75, 1.33))
    displacement_scale = float(np.random.uniform(0.001, 0.005))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    comb = nt.nodes.new("ShaderNodeCombineColor")
    comb.inputs["Red"].default_value = float(color[0])
    comb.inputs["Green"].default_value = float(color[1])
    comb.inputs["Blue"].default_value = float(color[2])
    bsdf1 = _principled(nt, Roughness=roughness); ln(comb.outputs["Color"], bsdf1.inputs["Base Color"])
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    mul.inputs[0].default_value = thread_density_x; mul.inputs[1].default_value = relative_density_y
    wy = nt.nodes.new("ShaderNodeTexWave"); wy.bands_direction = "Y"
    ln(tex_coord.outputs["Object"], wy.inputs["Vector"]); ln(mul.outputs[0], wy.inputs["Scale"])
    wy.inputs["Distortion"].default_value = 5.0; wy.inputs["Detail"].default_value = 6.1
    bsdf2 = _principled(nt, Roughness=roughness); ln(wy.outputs["Color"], bsdf2.inputs["Base Color"])
    msh = nt.nodes.new("ShaderNodeMixShader"); msh.inputs["Fac"].default_value = 0.1333
    ln(bsdf1.outputs["BSDF"], msh.inputs[1]); ln(bsdf2.outputs["BSDF"], msh.inputs[2])
    wx = nt.nodes.new("ShaderNodeTexWave"); ln(tex_coord.outputs["Object"], wx.inputs["Vector"])
    wx.inputs["Scale"].default_value = thread_density_x
    wx.inputs["Distortion"].default_value = 3.8; wx.inputs["Detail"].default_value = 6.1
    cr1 = nt.nodes.new("ShaderNodeValToRGB"); ln(wx.outputs["Color"], cr1.inputs["Fac"])
    cr1.color_ramp.elements[0].position = 0.8109; cr1.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr1.color_ramp.elements[1].position = 1.0;    cr1.color_ramp.elements[1].color = (1, 1, 1, 1)
    inv = nt.nodes.new("ShaderNodeInvert"); inv.inputs["Fac"].default_value = 0.84
    ln(cr1.outputs["Color"], inv.inputs["Color"])
    cr2 = nt.nodes.new("ShaderNodeValToRGB"); ln(wy.outputs["Color"], cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.0727; cr2.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr2.color_ramp.elements[1].position = 0.8655; cr2.color_ramp.elements[1].color = (1, 1, 1, 1)
    add = nt.nodes.new("ShaderNodeMath"); ln(inv.outputs["Color"], add.inputs[0]); ln(cr2.outputs["Color"], add.inputs[1])
    disp = nt.nodes.new("ShaderNodeDisplacement"); ln(add.outputs[0], disp.inputs["Height"])
    disp.inputs["Midlevel"].default_value = 0.4; disp.inputs["Scale"].default_value = displacement_scale
    _connect_out(nt, msh, disp)
    return mat

def make_leather(name="Leather"):
    seed_val = float(np.random.uniform(-1000.0, 1000.0)); scale = 1.0
    hsv = leather_hsv(); base_color = hsv2rgba(float(hsv[0]), float(hsv[1]), float(hsv[2]))
    rough_lo = float(np.random.uniform(0.3, 0.5)); rough_hi = float(np.random.uniform(0.5, 0.7))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = base_color
    mul1 = nt.nodes.new("ShaderNodeMath"); mul1.operation = "MULTIPLY"
    mul1.inputs[0].default_value = scale; mul1.inputs[1].default_value = 10.0
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.noise_dimensions = "4D"
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = seed_val; ln(mul1.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0; noise.inputs["Distortion"].default_value = 0.2
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.2841; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.9455; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    mix_ll = nt.nodes.new("ShaderNodeMix"); mix_ll.data_type = "RGBA"; mix_ll.blend_type = "LINEAR_LIGHT"
    mix_ll.inputs[0].default_value = 0.02
    ln(tex_coord.outputs["Object"], mix_ll.inputs[6]); ln(noise.outputs["Color"], mix_ll.inputs[7])
    mul2 = nt.nodes.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"
    mul2.inputs[0].default_value = scale; mul2.inputs[1].default_value = 800.0
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.voronoi_dimensions = "4D"; vor.feature = "DISTANCE_TO_EDGE"
    ln(mix_ll.outputs[2], vor.inputs["Vector"]); vor.inputs["W"].default_value = seed_val
    ln(mul2.outputs[0], vor.inputs["Scale"])
    mul3 = nt.nodes.new("ShaderNodeMath"); mul3.operation = "MULTIPLY"; mul3.use_clamp = True
    ln(vor.outputs["Distance"], mul3.inputs[0]); mul3.inputs[1].default_value = scale
    hsv1 = nt.nodes.new("ShaderNodeHueSaturation"); hsv1.inputs["Value"].default_value = 0.6
    ln(rgb.outputs[0], hsv1.inputs["Color"])
    mix1 = nt.nodes.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    ln(mul3.outputs[0], mix1.inputs[0]); ln(rgb.outputs[0], mix1.inputs[6]); ln(hsv1.outputs["Color"], mix1.inputs[7])
    hsv2 = nt.nodes.new("ShaderNodeHueSaturation"); hsv2.inputs["Value"].default_value = 0.4
    ln(rgb.outputs[0], hsv2.inputs["Color"])
    mix2 = nt.nodes.new("ShaderNodeMix"); mix2.data_type = "RGBA"
    ln(cr.outputs["Color"], mix2.inputs[0]); ln(mix1.outputs[2], mix2.inputs[6]); ln(hsv2.outputs["Color"], mix2.inputs[7])
    mr = nt.nodes.new("ShaderNodeMapRange"); ln(mix2.outputs[2], mr.inputs["Value"])
    mr.inputs[3].default_value = rough_lo; mr.inputs[4].default_value = rough_hi
    bsdf = _principled(nt); ln(mix2.outputs[2], bsdf.inputs["Base Color"]); ln(mr.outputs[0], bsdf.inputs["Roughness"])
    m4 = nt.nodes.new("ShaderNodeMath"); m4.operation = "MULTIPLY"; ln(mix1.outputs[2], m4.inputs[0]); m4.inputs[1].default_value = -0.2
    m5 = nt.nodes.new("ShaderNodeMath"); m5.operation = "MULTIPLY"; ln(cr.outputs["Color"], m5.inputs[0]); m5.inputs[1].default_value = 0.05
    a = nt.nodes.new("ShaderNodeMath"); ln(m4.outputs[0], a.inputs[0]); ln(m5.outputs[0], a.inputs[1])
    m6 = nt.nodes.new("ShaderNodeMath"); m6.operation = "MULTIPLY"; ln(a.outputs[0], m6.inputs[0]); m6.inputs[1].default_value = 0.02
    disp = nt.nodes.new("ShaderNodeDisplacement"); ln(m6.outputs[0], disp.inputs["Height"]); disp.inputs["Midlevel"].default_value = 0.0
    _connect_out(nt, bsdf, disp)
    return mat

def make_sofa_fabric(name="SofaFabric"):
    strength = log_uniform(0.005, 0.01); hsv = fabric_hsv(); rgba = hsv2rgba(*hsv)
    bright = float(np.random.uniform(-0.15, -0.05))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping"); ln(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = rgba
    bc = nt.nodes.new("ShaderNodeBrightContrast"); ln(rgb.outputs[0], bc.inputs["Color"]); bc.inputs["Bright"].default_value = bright
    brick = nt.nodes.new("ShaderNodeTexBrick"); ln(mapping.outputs["Vector"], brick.inputs["Vector"])
    ln(rgb.outputs[0], brick.inputs["Color1"]); ln(bc.outputs["Color"], brick.inputs["Color2"])
    brick.inputs["Scale"].default_value = 276.98; brick.inputs["Mortar Size"].default_value = 0.01
    brick.inputs["Mortar Smooth"].default_value = 1.0; brick.inputs["Bias"].default_value = 0.5
    brick.inputs["Row Height"].default_value = 0.1; brick.offset = 0.5479; brick.squash_frequency = 1
    bsdf = _principled(nt, Roughness=0.8624); ln(brick.outputs["Color"], bsdf.inputs["Base Color"])
    if "Sheen Weight" in bsdf.inputs: bsdf.inputs["Sheen Weight"].default_value = 1.0
    disp = nt.nodes.new("ShaderNodeDisplacement"); ln(_fac(brick), disp.inputs["Height"])
    disp.inputs["Scale"].default_value = strength
    _connect_out(nt, bsdf, disp)
    return mat

def make_art_fabric(name="ArtFabric"):
    idx = int(np.random.choice(4, p=np.array([1, 1, 2, 1], dtype=float) / 5.0))
    return [make_coarse_knit_fabric, make_fine_knit_fabric, make_leather, make_sofa_fabric][idx](name=name)

# ═══════════════════════════════════════════════════════════════════════════
#  Registry  (material_assignments.blanket)
# ═══════════════════════════════════════════════════════════════════════════
BLANKET_REGISTRY = [
    (make_coarse_knit_fabric, 1.0),
    (make_fine_knit_fabric,   1.0),
    (make_leather,            0.3),
    (make_sofa_fabric,        1.0),
    (make_art_fabric,         3.0),
]

def get_material(name=None):
    ctor = weighted_sample(BLANKET_REGISTRY)
    return ctor(name=name or "BoxComforterFabric")

# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
SEED = int(os.environ.get("SEED", "0"))
seed_all(SEED)

width      = log_uniform(0.9, 1.2)
size       = width * log_uniform(0.4, 0.7)
_thickness = log_uniform(0.004, 0.008)

margin = float(np.random.uniform(0.3, 0.4))

# Material sampling (isolated from geometry RNG to avoid polluting margin draw)
_geom_rng_state = np.random.get_state()
MAT = get_material("BoxComforterFabric")
np.random.set_state(_geom_rng_state)

# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

def sel_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def set_active(o):
    bpy.context.view_layer.objects.active = o; o.select_set(True)

def apply_tf(o, loc=False):
    sel_none(); set_active(o)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    sel_none()

def mod(o, t, **kw):
    m = o.modifiers.new(t, t)
    for k, v in kw.items(): setattr(m, k, v)
    sel_none(); set_active(o)
    bpy.ops.object.modifier_apply(modifier=m.name); sel_none()

def read_co(o):
    a = np.zeros(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)

y_subs = max(1, int(size / width * 64))
bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=y_subs,
                                location=(0, 0, 0))
obj = bpy.context.active_object
apply_tf(obj, True)
obj.scale = width / 2, size / 2, 1
apply_tf(obj, True)
mod(obj, "SOLIDIFY", thickness=0.01)

# Step 2: Box quilt pattern
x, y, _ = read_co(obj).T
half_cell = width / 64 / 2
_x = np.abs(x / margin - np.round(x / margin)) * margin < half_cell
_y = np.abs(y / margin - np.round(y / margin)) * margin < half_cell
sel_mask = _x | _y

sel_none(); set_active(obj)
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(obj.data)
bm.verts.ensure_lookup_table()
bpy.ops.mesh.select_all(action="DESELECT")
for i, v in enumerate(bm.verts):
    v.select = bool(sel_mask[i])
bm.select_flush(True)
bmesh.update_edit_mesh(obj.data)
bpy.ops.mesh.remove_doubles(threshold=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
sel_none()

# ── assign material ───────────────────────────────────────────────────────
obj.data.materials.append(MAT)

obj.name = "BoxComforter"
print(f"[BoxComforterFactory] SEED={SEED}  material={MAT.name}  "
      f"slots={len(obj.data.materials)}  verts={len(obj.data.vertices)}")
