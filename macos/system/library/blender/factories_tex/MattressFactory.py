# [FL_INDEX: keywords="blender_factory, procedural_3d, MattressFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MattressFactory | Category: factories_tex
# Prompt: A 3D model of a rectangular mattress rendered from an elevated three-quarter perspective, featuring a thick padded slab with softly rounded edges, a quilted or tufted surface pattern across the top, and a light mint-green coloring throughout.

"""
MattressFactory — standalone Blender script (geometry + fabric materials).

Source geometry : objects_blender/seating/MattressFactory.py
                  fine_knit_fabric,leather,sofa_fabric}.py
Registry key   : material_assignments.fabrics
                 (MattressFactory.__init__ draws from
                 `weighted_sample(material_assignments.fabrics)`)
Wear/tear      : NONE — MattressFactory.finalize_assets only calls
                 `surface.assign_material(assets, self.surface)`; no
                 `scratch` / `edge_wear` fields are created in __init__
                 and no `.apply(assets)` is called after join. Contrast
                 with bedframe.py / office_chair.py / bar_chair.py which
                 DO sample wear_tear in seating.
"""
import os, math, bpy, bmesh, random, colorsys
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
#  Scene cleanup
# ═══════════════════════════════════════════════════════════════════════════
for _o in list(bpy.data.objects):
    bpy.data.objects.remove(_o, do_unlink=True)
for _m in list(bpy.data.meshes):
    bpy.data.meshes.remove(_m)
bpy.context.scene.cursor.location = (0, 0, 0)

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
#   code path as objects_blender_texture/clothes/ComforterFactory.py)
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

    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    ln(brick.outputs["Color"], cr1.inputs["Fac"])
    cr1.color_ramp.elements[0].position = 0.0;  cr1.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr1.color_ramp.elements[1].position = 1.0;  cr1.color_ramp.elements[1].color = (0, 0, 0, 1)

    map2 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], map2.inputs["Vector"])
    map2.inputs["Rotation"].default_value = (0, 0, 0.7854)
    map2.inputs["Scale"].default_value = (238.8, 1.0, 35.6)

    vor1 = nt.nodes.new("ShaderNodeTexVoronoi"); vor1.feature = "F2"
    ln(map2.outputs["Vector"], vor1.inputs["Vector"])
    vor1.inputs["Scale"].default_value = pattern_density
    vor1.inputs["Randomness"].default_value = 0.0

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    ln(vor1.outputs["Distance"], cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.1018; cr2.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr2.color_ramp.elements[1].position = 1.0;    cr2.color_ramp.elements[1].color = (0, 0, 0, 1)

    mix_pat = nt.nodes.new("ShaderNodeMix")
    mix_pat.data_type = "RGBA"; mix_pat.clamp_result = True
    mix_pat.inputs[0].default_value = pattern_mixer
    ln(cr1.outputs["Color"], mix_pat.inputs[6])
    ln(cr2.outputs["Color"], mix_pat.inputs[7])

    bsdf1 = _principled(nt, Specular=0.6309, Roughness=0.9945)
    ln(mix_pat.outputs[2], bsdf1.inputs["Base Color"])

    comb = nt.nodes.new("ShaderNodeCombineColor")
    comb.inputs["Red"].default_value   = float(color[0])
    comb.inputs["Green"].default_value = float(color[1])
    comb.inputs["Blue"].default_value  = float(color[2])
    bsdf2 = _principled(nt, Specular=0.6309, Roughness=0.9945)
    ln(comb.outputs["Color"], bsdf2.inputs["Base Color"])

    msh = nt.nodes.new("ShaderNodeMixShader")
    msh.inputs["Fac"].default_value = color_shader_frac
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
    vor2.inputs["Scale"].default_value = knit_resolution
    vor2.inputs["Randomness"].default_value = 0.0

    map4 = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], map4.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    ln(map4.outputs["Vector"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = crease_resolution

    add_n = nt.nodes.new("ShaderNodeMath"); add_n.use_clamp = True
    ln(_fac(noise), add_n.inputs[0]); add_n.inputs[1].default_value = smoothness
    mul_n = nt.nodes.new("ShaderNodeMath"); mul_n.operation = "MULTIPLY"; mul_n.use_clamp = True
    ln(vor2.outputs["Distance"], mul_n.inputs[0]); ln(add_n.outputs[0], mul_n.inputs[1])
    sub_n = nt.nodes.new("ShaderNodeMath"); sub_n.operation = "SUBTRACT"
    sub_n.inputs[0].default_value = 1.0; sub_n.inputs[1].default_value = brick_knit
    sc1 = nt.nodes.new("ShaderNodeMath"); sc1.operation = "MULTIPLY"
    ln(mul_n.outputs[0], sc1.inputs[0]); ln(sub_n.outputs[0], sc1.inputs[1])
    add1 = nt.nodes.new("ShaderNodeMath")
    ln(sc.outputs[0], add1.inputs[0]); ln(sc1.outputs[0], add1.inputs[1])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(add1.outputs[0], disp.inputs["Height"])
    disp.inputs["Midlevel"].default_value = 0.4; disp.inputs["Scale"].default_value = 0.01
    _connect_out(nt, msh, disp)
    return mat

def make_fine_knit_fabric(name="FineKnitFabric"):
    color              = np.random.uniform(0.2, 1.0, 3)
    roughness          = float(np.random.uniform(0, 1.0))
    thread_density_x   = float(np.random.uniform(100, 300))
    relative_density_y = float(np.random.uniform(0.75, 1.33))
    displacement_scale = float(np.random.uniform(0.001, 0.005))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    comb = nt.nodes.new("ShaderNodeCombineColor")
    comb.inputs["Red"].default_value   = float(color[0])
    comb.inputs["Green"].default_value = float(color[1])
    comb.inputs["Blue"].default_value  = float(color[2])
    bsdf1 = _principled(nt, Roughness=roughness)
    ln(comb.outputs["Color"], bsdf1.inputs["Base Color"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    mul.inputs[0].default_value = thread_density_x; mul.inputs[1].default_value = relative_density_y

    wy = nt.nodes.new("ShaderNodeTexWave"); wy.bands_direction = "Y"
    ln(tex_coord.outputs["Object"], wy.inputs["Vector"])
    ln(mul.outputs[0], wy.inputs["Scale"])
    wy.inputs["Distortion"].default_value = 5.0; wy.inputs["Detail"].default_value = 6.1

    bsdf2 = _principled(nt, Roughness=roughness)
    ln(wy.outputs["Color"], bsdf2.inputs["Base Color"])
    msh = nt.nodes.new("ShaderNodeMixShader"); msh.inputs["Fac"].default_value = 0.1333
    ln(bsdf1.outputs["BSDF"], msh.inputs[1]); ln(bsdf2.outputs["BSDF"], msh.inputs[2])

    wx = nt.nodes.new("ShaderNodeTexWave")
    ln(tex_coord.outputs["Object"], wx.inputs["Vector"])
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

    add = nt.nodes.new("ShaderNodeMath")
    ln(inv.outputs["Color"], add.inputs[0]); ln(cr2.outputs["Color"], add.inputs[1])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(add.outputs[0], disp.inputs["Height"])
    disp.inputs["Midlevel"].default_value = 0.4; disp.inputs["Scale"].default_value = displacement_scale
    _connect_out(nt, msh, disp)
    return mat

def make_leather(name="Leather"):
    seed_val = float(np.random.uniform(-1000.0, 1000.0))
    scale = 1.0
    hsv = leather_hsv()
    base_color = hsv2rgba(float(hsv[0]), float(hsv[1]), float(hsv[2]))
    rough_lo = float(np.random.uniform(0.3, 0.5)); rough_hi = float(np.random.uniform(0.5, 0.7))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = base_color

    mul1 = nt.nodes.new("ShaderNodeMath"); mul1.operation = "MULTIPLY"
    mul1.inputs[0].default_value = scale; mul1.inputs[1].default_value = 10.0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise.noise_dimensions = "4D"
    except Exception:
        noise.noise_dimensions = "3D"
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed_val
    ln(mul1.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0; noise.inputs["Distortion"].default_value = 0.2

    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.2841; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.9455; cr.color_ramp.elements[1].color = (1, 1, 1, 1)

    mix_ll = nt.nodes.new("ShaderNodeMix")
    mix_ll.data_type = "RGBA"; mix_ll.blend_type = "LINEAR_LIGHT"
    mix_ll.inputs[0].default_value = 0.02
    ln(tex_coord.outputs["Object"], mix_ll.inputs[6]); ln(noise.outputs["Color"], mix_ll.inputs[7])

    mul2 = nt.nodes.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"
    mul2.inputs[0].default_value = scale; mul2.inputs[1].default_value = 800.0
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        vor.voronoi_dimensions = "4D"
    except Exception:
        vor.voronoi_dimensions = "3D"
    vor.feature = "DISTANCE_TO_EDGE"
    ln(mix_ll.outputs[2], vor.inputs["Vector"])
    if "W" in vor.inputs:
        vor.inputs["W"].default_value = seed_val
    ln(mul2.outputs[0], vor.inputs["Scale"])

    mul3 = nt.nodes.new("ShaderNodeMath"); mul3.operation = "MULTIPLY"; mul3.use_clamp = True
    ln(vor.outputs["Distance"], mul3.inputs[0]); mul3.inputs[1].default_value = scale

    hsv1 = nt.nodes.new("ShaderNodeHueSaturation"); hsv1.inputs["Value"].default_value = 0.6
    ln(rgb.outputs[0], hsv1.inputs["Color"])
    mix1 = nt.nodes.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    ln(mul3.outputs[0], mix1.inputs[0])
    ln(rgb.outputs[0], mix1.inputs[6]); ln(hsv1.outputs["Color"], mix1.inputs[7])

    hsv2 = nt.nodes.new("ShaderNodeHueSaturation"); hsv2.inputs["Value"].default_value = 0.4
    ln(rgb.outputs[0], hsv2.inputs["Color"])
    mix2 = nt.nodes.new("ShaderNodeMix"); mix2.data_type = "RGBA"
    ln(cr.outputs["Color"], mix2.inputs[0])
    ln(mix1.outputs[2], mix2.inputs[6]); ln(hsv2.outputs["Color"], mix2.inputs[7])

    mr = nt.nodes.new("ShaderNodeMapRange"); ln(mix2.outputs[2], mr.inputs["Value"])
    mr.inputs[3].default_value = rough_lo; mr.inputs[4].default_value = rough_hi
    bsdf = _principled(nt)
    ln(mix2.outputs[2], bsdf.inputs["Base Color"]); ln(mr.outputs[0], bsdf.inputs["Roughness"])

    m4 = nt.nodes.new("ShaderNodeMath"); m4.operation = "MULTIPLY"
    ln(mix1.outputs[2], m4.inputs[0]); m4.inputs[1].default_value = -0.2
    m5 = nt.nodes.new("ShaderNodeMath"); m5.operation = "MULTIPLY"
    ln(cr.outputs["Color"], m5.inputs[0]); m5.inputs[1].default_value = 0.05
    a = nt.nodes.new("ShaderNodeMath"); ln(m4.outputs[0], a.inputs[0]); ln(m5.outputs[0], a.inputs[1])
    m6 = nt.nodes.new("ShaderNodeMath"); m6.operation = "MULTIPLY"
    ln(a.outputs[0], m6.inputs[0]); m6.inputs[1].default_value = 0.02

    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(m6.outputs[0], disp.inputs["Height"]); disp.inputs["Midlevel"].default_value = 0.0
    _connect_out(nt, bsdf, disp)
    return mat

def make_sofa_fabric(name="SofaFabric"):
    strength = log_uniform(0.005, 0.01)
    hsv = fabric_hsv(); rgba = hsv2rgba(*hsv)
    bright = float(np.random.uniform(-0.15, -0.05))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    ln(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = rgba
    bc = nt.nodes.new("ShaderNodeBrightContrast")
    ln(rgb.outputs[0], bc.inputs["Color"]); bc.inputs["Bright"].default_value = bright

    brick = nt.nodes.new("ShaderNodeTexBrick")
    ln(mapping.outputs["Vector"], brick.inputs["Vector"])
    ln(rgb.outputs[0], brick.inputs["Color1"]); ln(bc.outputs["Color"], brick.inputs["Color2"])
    brick.inputs["Scale"].default_value = 276.98
    brick.inputs["Mortar Size"].default_value = 0.01
    brick.inputs["Mortar Smooth"].default_value = 1.0
    brick.inputs["Bias"].default_value = 0.5; brick.inputs["Row Height"].default_value = 0.1
    brick.offset = 0.5479; brick.squash_frequency = 1

    bsdf = _principled(nt, Roughness=0.8624)
    ln(brick.outputs["Color"], bsdf.inputs["Base Color"])
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 1.0

    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(_fac(brick), disp.inputs["Height"]); disp.inputs["Scale"].default_value = strength
    _connect_out(nt, bsdf, disp)
    return mat

# ═══════════════════════════════════════════════════════════════════════════
#  (CoarseKnitFabric, FineKnitFabric, Leather, SofaFabric) — same list used
#  by MattressFactory.__init__ via
#     surface_gen_class = weighted_sample(material_assignments.fabrics)
# ═══════════════════════════════════════════════════════════════════════════
FABRICS_REGISTRY = [
    (make_coarse_knit_fabric, 1.0),
    (make_fine_knit_fabric,   1.0),
    (make_leather,            0.3),
    (make_sofa_fabric,        1.0),
]

def get_surface_material(name="MattressFabric"):
    ctor = weighted_sample(FABRICS_REGISTRY)
    return ctor(name=name)

# ═══════════════════════════════════════════════════════════════════════════
#  Phase 1 — material sampling on raw SEED
# ═══════════════════════════════════════════════════════════════════════════
SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)

# Replicate exact numpy.random consumption order of MattressFactory.__init__:
#   width, size, thickness, dot_distance, dot_size, dot_depth, type, surface
mat_width     = log_uniform(0.9, 2.0)
mat_size      = float(np.random.uniform(2, 2.4))
mat_thickness = float(np.random.uniform(0.2, 0.35))
dot_distance  = log_uniform(0.16, 0.2)
dot_size      = float(np.random.uniform(0.005, 0.02))
dot_depth     = float(np.random.uniform(0.04, 0.08))
wrap_distance = 0.05

_types = [(1, "coiled"), (1, "wrapped")]
_weights = np.array([c[0] for c in _types], dtype=float)
mattress_type = _types[int(np.random.choice(len(_types), p=_weights / _weights.sum()))][1]

MAT_SURFACE = get_surface_material("MattressFabric")

# MattressFactory.finalize_assets() only calls surface.assign_material → NO
# wear_tear sampling needed (contrast with bedframe / chair / office_chair).

# ═══════════════════════════════════════════════════════════════════════════
#  Geometry  (from objects_blender/seating/MattressFactory.py, verbatim)
# ═══════════════════════════════════════════════════════════════════════════
random.seed(SEED)

def apply_transform(obj, loc=False):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    obj.select_set(False)

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def read_edge_direction(obj):
    edges_arr = np.zeros(len(obj.data.edges) * 2, dtype=int)
    obj.data.edges.foreach_get("vertices", edges_arr)
    edges_arr = edges_arr.reshape(-1, 2)
    co = read_co(obj)
    cos = co[edges_arr.reshape(-1)].reshape(-1, 2, 3)
    d = cos[:, 1] - cos[:, 0]
    norms = np.linalg.norm(d, axis=-1, keepdims=True)
    norms[norms == 0] = 1
    return d / norms

def subdivide_edge_ring(obj, cuts, axis):
    axis = np.array(axis, dtype=float)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    dirs = read_edge_direction(obj)
    selected = np.abs((dirs * axis[np.newaxis, :]).sum(1)) > 1 - 1e-3
    edges = [bm.edges[i] for i in np.nonzero(selected)[0]]
    bmesh.ops.subdivide_edgering(bm, edges=edges, cuts=int(cuts))
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)

def modify_mesh(obj, mod_type, apply=True, **kwargs):
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new(name=mod_type, type=mod_type)
    for k, v in kwargs.items():
        setattr(mod, k, v)
    if apply:
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.select_set(False)
    return mod

def cloth_sim(obj, collision_objs=None, end_frame=50, **kwargs):
    if collision_objs is not None:
        if not isinstance(collision_objs, list):
            collision_objs = [collision_objs]
        for o in collision_objs:
            o.modifiers.new("Collision", 'COLLISION')
            o.collision.damping_factor = 0.9
            o.collision.cloth_friction = 10.0
            o.collision.friction_factor = 1.0
            o.collision.stickiness = 0.9
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new("Cloth", 'CLOTH')
    mod.settings.effector_weights.gravity = kwargs.pop('gravity', 1)
    mod.collision_settings.distance_min = kwargs.pop('distance_min', 0.015)
    mod.collision_settings.use_self_collision = kwargs.pop('use_self_collision', False)
    for k, v in kwargs.items():
        setattr(mod.settings, k, v)
    mod.point_cache.frame_start = 1
    mod.point_cache.frame_end = end_frame
    override = {'scene': bpy.context.scene, 'active_object': obj, 'point_cache': mod.point_cache}
    with bpy.context.temp_override(**override):
        bpy.ops.ptcache.bake(bake=True)
    bpy.context.scene.frame_set(end_frame)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)
    if collision_objs is not None:
        for o in collision_objs:
            bpy.context.view_layer.objects.active = o
            o.select_set(True)
            bpy.ops.object.modifier_remove(modifier=o.modifiers[-1].name)
            o.select_set(False)

def write_attr_data(obj, name, data, data_type='FLOAT', domain='FACE'):
    mesh = obj.data
    if name in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[name])
    attr = mesh.attributes.new(name=name, type=data_type, domain=domain)
    data = np.asarray(data).ravel()
    attr.data.foreach_set("value", data)

def make_coiled(obj, dot_distance, dot_depth, dot_size):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.poke()
    bpy.ops.mesh.tris_convert_to_quads()
    bpy.ops.mesh.poke()
    bpy.ops.mesh.poke()
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    for v in bm.verts:
        if len(v.link_edges) == 16:
            v.select_set(True)
    bm.select_flush(False)
    bmesh.update_edit_mesh(obj.data)
    radius = dot_distance * np.random.uniform(0.06, 0.08)
    bpy.ops.mesh.bevel(offset=radius, affect='VERTICES')
    bpy.ops.mesh.extrude_region_shrink_fatten(
        TRANSFORM_OT_shrink_fatten={"value": -dot_depth}
    )
    bpy.ops.mesh.extrude_region_shrink_fatten(
        TRANSFORM_OT_shrink_fatten={"value": dot_depth}
    )
    bpy.ops.mesh.select_more()
    bpy.ops.mesh.select_more()
    bpy.ops.object.mode_set(mode='OBJECT')

    write_attr_data(obj, "tip", np.zeros(len(obj.data.polygons)), 'FLOAT', 'FACE')

    bpy.ops.object.mode_set(mode='EDIT')
    obj.data.attributes.active = obj.data.attributes["tip"]
    bpy.ops.mesh.attribute_set(value_float=1)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)

    _apply_scale_elements(obj, "tip", dot_size / radius)

    modify_mesh(obj, 'TRIANGULATE', min_vertices=4)
    modify_mesh(obj, 'SMOOTH', factor=np.random.uniform(0.5, 1.0), iterations=5)

def _apply_scale_elements(obj, attr_name, scale_val):
    ng = bpy.data.node_groups.new("geo_scale", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = ng.nodes.new('NodeGroupInput'); inp.location = (-400, 0)
    out = ng.nodes.new('NodeGroupOutput'); out.location = (400, 0)

    named = ng.nodes.new('GeometryNodeInputNamedAttribute')
    named.data_type = 'FLOAT'
    named.inputs[0].default_value = attr_name
    named.location = (-200, -100)

    combine = ng.nodes.new('ShaderNodeCombineXYZ')
    combine.inputs[0].default_value = scale_val
    combine.inputs[1].default_value = scale_val
    combine.inputs[2].default_value = scale_val
    combine.location = (-200, -200)

    scale_el = ng.nodes.new('GeometryNodeScaleElements')
    scale_el.location = (0, 0)

    ng.links.new(inp.outputs[0], scale_el.inputs['Geometry'])
    ng.links.new(named.outputs[0], scale_el.inputs['Selection'])
    ng.links.new(combine.outputs[0], scale_el.inputs['Scale'])
    ng.links.new(scale_el.outputs[0], out.inputs[0])

    mod = obj.modifiers.new("GeoScale", 'NODES')
    mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)

# ── Build mattress ─────────────────────────────────────────────────────────
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
obj = bpy.context.active_object
obj.scale = (mat_width / 2, mat_size / 2, mat_thickness / 2)
apply_transform(obj)

if mattress_type == "coiled":
    for i, dim_size in enumerate(obj.dimensions):
        axis = np.zeros(3)
        axis[i] = 1
        subdivide_edge_ring(obj, int(np.ceil(dim_size / dot_distance)), axis)
    make_coiled(obj, dot_distance, dot_depth, dot_size)

elif mattress_type == "wrapped":
    for i, dim_size in enumerate([mat_width, mat_size, mat_thickness]):
        axis = np.zeros(3)
        axis[i] = 1
        subdivide_edge_ring(obj, int(np.ceil(dim_size / wrap_distance)), axis)
    modify_mesh(obj, 'BEVEL', width=wrap_distance / 3, segments=2)
    vg = obj.vertex_groups.new(name="pin")
    co = read_co(obj)
    pin_verts = np.nonzero(co[:, -1] < 1e-1 - mat_thickness / 2)[0].tolist()
    vg.add(pin_verts, 1, "REPLACE")
    cloth_sim(
        obj,
        gravity=0,
        use_pressure=True,
        uniform_pressure_force=np.random.uniform(0.1, 0.2),
        vertex_group_mass="pin",
    )

# Shade smooth
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.shade_smooth()
obj.select_set(False)

# ── Assign surface material ────────────────────────────────────────────────
obj.data.materials.append(MAT_SURFACE)

obj.name = "MattressFactory"
print(f"[MattressFactory] SEED={SEED}  type={mattress_type}  "
      f"material={MAT_SURFACE.name}  slots={len(obj.data.materials)}  "
      f"verts={len(obj.data.vertices)}")

