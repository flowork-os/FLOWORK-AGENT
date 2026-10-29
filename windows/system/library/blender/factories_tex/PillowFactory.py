# [FL_INDEX: keywords="blender_factory, procedural_3d, PillowFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PillowFactory | Category: factories_tex
# Prompt: A 3D model of a soft pillow rendered from an elevated three-quarter perspective, featuring a plump rectangular cushion with a light lavender coloring, natural-looking surface wrinkles and creases from cloth simulation, and slightly irregular edges that give it a realistic resting appearance.

"""
PillowFactory - standalone Blender script (geometry + fabric materials).

Source geometry : objects_blender/seating/PillowFactory.py
Registry key    : material_assignments.fabrics (PillowFactory uses plain fabrics, no ArtFabric)
UV unwrap       : yes (pillow.py calls unwrap_faces on the grid before SOLIDIFY)
Wear/tear       : none (PillowFactory.finalize_assets only calls surface.assign_material)
"""
import os, math, bpy, bmesh, random, colorsys
import numpy as np
from mathutils import Vector

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
        pass
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
    if "Sheen Weight" in bsdf.inputs: bsdf.inputs["Sheen Weight"].default_value = 1.0

    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(_fac(brick), disp.inputs["Height"]); disp.inputs["Scale"].default_value = strength
    _connect_out(nt, bsdf, disp)
    return mat

# ═══════════════════════════════════════════════════════════════════════════
#  Registry (mirrors material_assignments.fabrics)
#     (fabric.CoarseKnitFabric, 1.0),
#     (fabric.FineKnitFabric,   1.0),
#     (fabric.Leather,          0.3),
#     (fabric.SofaFabric,       1.0),
#  PillowFactory uses plain `fabrics` — no ArtFabric unlike BlanketFactory.
# ═══════════════════════════════════════════════════════════════════════════
FABRIC_REGISTRY = [
    (make_coarse_knit_fabric, 1.0),
    (make_fine_knit_fabric,   1.0),
    (make_leather,            0.3),
    (make_sofa_fabric,        1.0),
]

def get_material(name=None):
    ctor = weighted_sample(FABRIC_REGISTRY)
    return ctor(name=name or "PillowFabric")

# ═══════════════════════════════════════════════════════════════════════════
#  Scene cleanup
# ═══════════════════════════════════════════════════════════════════════════
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for c in list(bpy.data.curves):
    bpy.data.curves.remove(c)
bpy.context.scene.cursor.location = (0, 0, 0)

# ═══════════════════════════════════════════════════════════════════════════
#  Phase 1 — RNG-aligned parameter + material sampling
# ═══════════════════════════════════════════════════════════════════════════
SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)

# weighted_choice: rg((4,'square'),(4,'rect'),(1,'circle'),(1,'torus'))
def _weighted_choice(choices):
    weights = np.array([c[0] for c in choices], dtype=float)
    values  = [c[1] for c in choices]
    return values[int(np.random.choice(len(values), p=weights / weights.sum()))]

shape = _weighted_choice([(4, "square"), (4, "rectangle"), (1, "circle"), (1, "torus")])
width = float(np.random.uniform(0.4, 0.7))
if shape == "square":
    size = width
else:
    size = width * log_uniform(0.6, 0.8)
bevel_width = float(np.random.uniform(0.02, 0.05))
thickness = log_uniform(0.006, 0.008)
extrude_thickness = thickness * log_uniform(1, 8) if np.random.uniform() < 0.5 else 0
has_seam = (np.random.uniform() < 0.3) and (shape != "torus")
seam_radius = float(np.random.uniform(0.01, 0.02))

MAT = get_material("PillowFabric")

# ═══════════════════════════════════════════════════════════════════════════
#  Geometry utilities (copied verbatim from objects_blender/seating/PillowFactory.py)
# ═══════════════════════════════════════════════════════════════════════════

def apply_transform(obj, loc=False):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    obj.select_set(False)

def new_grid(x_subdivisions=10, y_subdivisions=10):
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=x_subdivisions, y_subdivisions=y_subdivisions, location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    apply_transform(obj, loc=True)
    return obj

def new_base_circle(vertices=32, radius=1.0):
    bpy.ops.mesh.primitive_circle_add(vertices=vertices, radius=radius, location=(0, 0, 0))
    return bpy.context.active_object

def join_objects(objs):
    if len(objs) == 1:
        return objs[0]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = objs[0]
    for o in objs:
        o.select_set(True)
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)
    bpy.ops.object.select_all(action='DESELECT')
    return obj

def read_normal(obj):
    arr = np.zeros(len(obj.data.polygons) * 3)
    obj.data.polygons.foreach_get("normal", arr)
    return arr.reshape(-1, 3)

def read_center(obj):
    arr = np.zeros(len(obj.data.polygons) * 3)
    obj.data.polygons.foreach_get("center", arr)
    return arr.reshape(-1, 3)

def read_selected(obj):
    arr = np.zeros(len(obj.data.vertices), int)
    obj.data.vertices.foreach_get("select", arr)
    return arr.ravel()

def select_faces(obj, to_select):
    if callable(to_select):
        x, y, z = read_center(obj).T
        to_select = to_select(x, y, z)
    to_select = np.nonzero(to_select)[0]
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='FACE')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    for i in to_select:
        bm.faces[i].select_set(True)
    bm.select_flush(False)
    bmesh.update_edit_mesh(obj.data)

def center_obj(obj):
    bb_min = Vector(obj.bound_box[0])
    bb_max = Vector(obj.bound_box[6])
    c = (bb_min + bb_max) / 2.0
    return c

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
            mod = o.modifiers.new("Collision", 'COLLISION')
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

def subsurf(obj, levels):
    if levels > 0:
        modify_mesh(obj, 'SUBSURF', levels=levels, render_levels=levels)

def set_shade_smooth(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)

# ═══════════════════════════════════════════════════════════════════════════
#  Build pillow (geometry verbatim from objects_blender/seating/PillowFactory.py)
# ═══════════════════════════════════════════════════════════════════════════

if shape == "circle":
    obj = new_base_circle(vertices=128)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.fill_grid()
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)
elif shape == "torus":
    outer = new_base_circle(vertices=128)
    inner = new_base_circle(vertices=128, radius=float(np.random.uniform(0.2, 0.4)))
    obj = join_objects([outer, inner])
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bridge_edge_loops(number_cuts=12, interpolation='LINEAR')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj = bpy.context.active_object
    obj.select_set(False)
else:
    obj = new_grid(x_subdivisions=32, y_subdivisions=32)

obj.scale = (width / 2, size / 2, 1)
apply_transform(obj, True)

# ── UV unwrap (mirrors unwrap_faces(obj) in pillow.py, called
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
try:
    bpy.ops.uv.smart_project()
except Exception:
    try:
        bpy.ops.uv.unwrap()
    except Exception:
        pass
bpy.ops.object.mode_set(mode='OBJECT')
obj.select_set(False)

# Solidify
modify_mesh(obj, 'SOLIDIFY', thickness=thickness, offset=0)

# Read normals for pin selection
normal = read_normal(obj)

# Vertex group for seam pinning
group = obj.vertex_groups.new(name="pin")
if has_seam:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    select_faces(obj, lambda x, y, z: (x**2 + y**2 < seam_radius**2) & (z > 0))
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    selection = read_selected(obj)
    group.add(np.nonzero(selection)[0].tolist(), 1, "REPLACE")
    obj.select_set(False)

# Cloth simulation
if shape == "torus":
    pressure = float(np.random.uniform(8, 12))
else:
    pressure = float(np.random.uniform(1, 2))

cloth_sim(
    obj,
    tension_stiffness=float(np.random.uniform(0, 5)),
    gravity=0,
    use_pressure=True,
    uniform_pressure_force=pressure,
    vertex_group_mass="pin" if has_seam else "",
)

# Optional extrude
if extrude_thickness > 0:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_shrink_fatten(
        TRANSFORM_OT_shrink_fatten={"value": extrude_thickness}
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)

# Center
c = center_obj(obj)
obj.location = (-c.x, -c.y, -c.z)
apply_transform(obj, True)

# Subdivision surface
subsurf(obj, 2)
set_shade_smooth(obj)

# ── assign material ─────────────────────────────────────────────────────────
obj.data.materials.append(MAT)

obj.name = "PillowFactory"
print(f"[PillowFactory] SEED={SEED}  shape={shape}  material={MAT.name}  "
      f"slots={len(obj.data.materials)}  verts={len(obj.data.vertices)}")

