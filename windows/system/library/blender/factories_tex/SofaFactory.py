# [FL_INDEX: keywords="blender_factory, procedural_3d, SofaFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SofaFactory | Category: factories_tex
# Prompt: A 3D model of a sectional sofa rendered from an elevated three-quarter perspective, featuring an L-shaped configuration with multiple seat cushions, padded backrest segments of varying heights, solid armrests on each end, and a chaise lounge extension on one side.

"""
SofaFactory — standalone Blender script (geometry + fabric material).

Source geometry : objects_blender/seating/SofaFactory.py (copied verbatim)
                  fine_knit_fabric,leather,sofa_fabric}.py
Registry key   : material_assignments.fabrics
                 (SofaFactory.__init__ draws from
                 `weighted_sample(material_assignments.fabrics)`)
Wear/tear      : NONE — SofaFactory.create_placeholder only calls
                 `surface.assign_material(obj, self.sofa_fabric)`; no
                 `scratch` / `edge_wear` fields are created in __init__
                 and no `.apply()` is called after placeholder creation.
                 Contrast with bedframe.py / office_chair.py / bar_chair.py
                 which DO sample wear_tear in seating. Matches the pattern
                 already used by objects_blender_texture/seating/MattressFactory.py.

Material call order inside SofaFactory.__init__:
    self.params = sofa_parameter_distribution()   # consumes many uniforms
    sofa_fabric_gen_class = weighted_sample(material_assignments.fabrics)
    self.sofa_fabric = sofa_fabric_gen_class()()

To keep numpy.random consumption identical to factory, Phase 1
below first calls `sofa_parameter_distribution()` (storing the result for
build()) and THEN samples the fabric shader.
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
for _c in list(bpy.data.collections):
    if _c != bpy.context.scene.collection:
        bpy.data.collections.remove(_c)
bpy.context.scene.cursor.location = (0, 0, 0)

# ═══════════════════════════════════════════════════════════════════════════
#  Fabric material library
#   helpers used by objects_blender_texture/seating/MattressFactory.py)
# ═══════════════════════════════════════════════════════════════════════════

def seed_all(seed):
    np.random.seed(seed); random.seed(seed)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def weighted_sample_mat(reg):
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

FABRICS_REGISTRY = [
    (make_coarse_knit_fabric, 1.0),
    (make_fine_knit_fabric,   1.0),
    (make_leather,            0.3),
    (make_sofa_fabric,        1.0),
]

def get_fabric_material(name="SofaFabric"):
    ctor = weighted_sample_mat(FABRICS_REGISTRY)
    return ctor(name=name)

# ═══════════════════════════════════════════════════════════════════════════
#  Geometry utilities (copied verbatim from objects_blender/seating/SofaFactory.py)
# ═══════════════════════════════════════════════════════════════════════════
def clip_gaussian(mean, std, lo, hi):
    return float(np.clip(np.random.normal(mean, std), lo, hi))

def assign_curve(curve, points):
    """Assign control points to a float curve mapping curve (like node_utils.assign_curve)."""

    for i, p in enumerate(points):
        if i < len(curve.points):
            curve.points[i].location = p
        else:
            curve.points.new(*p)

ARM_TYPE_SQUARE = 0
ARM_TYPE_ROUND = 1
ARM_TYPE_ANGULAR = 2

# ═══════════════════════════════════════════════════════════════
#  Node Group 1: nodegroup_array_fill_line
# ═══════════════════════════════════════════════════════════════
def create_array_fill_line():
    ng = bpy.data.node_groups.new("nodegroup_array_fill_line", 'GeometryNodeTree')

    # Interface sockets
    ng.interface.new_socket('Line Start', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Line End', in_out='INPUT', socket_type='NodeSocketVector')
    ng.interface.new_socket('Instance Dimensions', in_out='INPUT', socket_type='NodeSocketVector')
    s_count = ng.interface.new_socket('Count', in_out='INPUT', socket_type='NodeSocketInt')
    s_count.default_value = 10
    ng.interface.new_socket('Instance', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Nodes
    group_input = ng.nodes.new('NodeGroupInput')
    group_input.location = (-600, 0)

    group_output = ng.nodes.new('NodeGroupOutput')
    group_output.location = (600, 0)

    # multiply = VectorMath MULTIPLY: Instance Dimensions * (0, -0.5, 0)
    multiply = ng.nodes.new('ShaderNodeVectorMath')
    multiply.operation = 'MULTIPLY'
    multiply.inputs[1].default_value = (0.0, -0.5, 0.0)
    ng.links.new(group_input.outputs['Instance Dimensions'], multiply.inputs[0])

    # add = VectorMath ADD: Line End + multiply
    add = ng.nodes.new('ShaderNodeVectorMath')
    add.operation = 'ADD'
    ng.links.new(group_input.outputs['Line End'], add.inputs[0])
    ng.links.new(multiply.outputs[0], add.inputs[1])

    # subtract = VectorMath SUBTRACT: Line Start - multiply
    subtract = ng.nodes.new('ShaderNodeVectorMath')
    subtract.operation = 'SUBTRACT'
    ng.links.new(group_input.outputs['Line Start'], subtract.inputs[0])
    ng.links.new(multiply.outputs[0], subtract.inputs[1])

    # mesh_line: mode=END_POINTS, Count, Start Location, Offset (=end point in END_POINTS mode)
    mesh_line = ng.nodes.new('GeometryNodeMeshLine')
    mesh_line.mode = 'END_POINTS'
    ng.links.new(group_input.outputs['Count'], mesh_line.inputs['Count'])
    ng.links.new(add.outputs[0], mesh_line.inputs['Start Location'])
    ng.links.new(subtract.outputs[0], mesh_line.inputs['Offset'])

    # instance_on_points
    instance_on_points = ng.nodes.new('GeometryNodeInstanceOnPoints')
    ng.links.new(mesh_line.outputs[0], instance_on_points.inputs['Points'])
    ng.links.new(group_input.outputs['Instance'], instance_on_points.inputs['Instance'])

    # realize_instances
    realize = ng.nodes.new('GeometryNodeRealizeInstances')
    ng.links.new(instance_on_points.outputs[0], realize.inputs[0])

    # output
    ng.links.new(realize.outputs[0], group_output.inputs[0])

    return ng

# ═══════════════════════════════════════════════════════════════
#  Node Group 2: nodegroup_corner_cube
# ═══════════════════════════════════════════════════════════════
def create_corner_cube():
    ng = bpy.data.node_groups.new("nodegroup_corner_cube", 'GeometryNodeTree')

    # Interface sockets
    ng.interface.new_socket('Location', in_out='INPUT', socket_type='NodeSocketVector')
    s_cl = ng.interface.new_socket('CenteringLoc', in_out='INPUT', socket_type='NodeSocketVector')
    s_cl.default_value = (0.5, 0.5, 0.0)
    s_dim = ng.interface.new_socket('Dimensions', in_out='INPUT', socket_type='NodeSocketVector')
    s_dim.default_value = (1.0, 1.0, 1.0)
    ng.interface.new_socket('SupportingEdgeFac', in_out='INPUT', socket_type='NodeSocketFloat')
    s_vx = ng.interface.new_socket('Vertices X', in_out='INPUT', socket_type='NodeSocketInt')
    s_vx.default_value = 4
    s_vy = ng.interface.new_socket('Vertices Y', in_out='INPUT', socket_type='NodeSocketInt')
    s_vy.default_value = 4
    s_vz = ng.interface.new_socket('Vertices Z', in_out='INPUT', socket_type='NodeSocketInt')
    s_vz.default_value = 4
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Nodes
    group_input = ng.nodes.new('NodeGroupInput')
    group_output = ng.nodes.new('NodeGroupOutput')

    # cube
    cube = ng.nodes.new('GeometryNodeMeshCube')
    ng.links.new(group_input.outputs['Dimensions'], cube.inputs['Size'])
    ng.links.new(group_input.outputs['Vertices X'], cube.inputs['Vertices X'])
    ng.links.new(group_input.outputs['Vertices Y'], cube.inputs['Vertices Y'])
    ng.links.new(group_input.outputs['Vertices Z'], cube.inputs['Vertices Z'])

    # map_range (FLOAT_VECTOR): CenteringLoc mapped from (0.5,0.5,0.5) to (-0.5,-0.5,-0.5)
    map_range = ng.nodes.new('ShaderNodeMapRange')
    map_range.data_type = 'FLOAT_VECTOR'
    ng.links.new(group_input.outputs['CenteringLoc'], map_range.inputs['Vector'])
    # From Min Vector = input 9, From Max Vector = input 10 in Blender 5.0
    # But let's use named sockets where possible
    # In FLOAT_VECTOR mode: inputs are Vector, Steps, From Min (vec), From Max (vec), To Min (vec), To Max (vec)
    # indices: 0=Value(float), 1=From Min(float), 2=From Max(float), 3=To Min(float), 4=To Max(float),
    #          5=Steps(float), 6=Vector, 7=From Min(vec), 8=From Max(vec), 9=To Min(vec), 10=To Max(vec), 11=Steps(vec)
    # In Blender 5.0 for FLOAT_VECTOR:
    #   input "Vector" at index 6
    #   input "From Min" (vector) at index 7
    #   input "From Max" (vector) at index 8
    #   input "To Min" (vector) at index 9
    #   input "To Max" (vector) at index 10
    # The original code uses input indices 9 and 10 for From Min Vector and From Max Vector
    # In code: 9: (0.5, 0.5, 0.5), 10: (-0.5, -0.5, -0.5)
    # These correspond to the vector From Min and From Max
    # Let's find the right sockets by iterating
    _set_map_range_vector_inputs(map_range,
                                 from_min_vec=(0.5, 0.5, 0.5),
                                 from_max_vec=(-0.5, -0.5, -0.5))

    # multiply_add = VectorMath MULTIPLY_ADD: map_range * Dimensions + Location
    multiply_add = ng.nodes.new('ShaderNodeVectorMath')
    multiply_add.operation = 'MULTIPLY_ADD'
    ng.links.new(map_range.outputs['Vector'], multiply_add.inputs[0])
    ng.links.new(group_input.outputs['Dimensions'], multiply_add.inputs[1])
    ng.links.new(group_input.outputs['Location'], multiply_add.inputs[2])

    # transform_geometry
    transform = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(cube.outputs['Mesh'], transform.inputs['Geometry'])
    ng.links.new(multiply_add.outputs[0], transform.inputs['Translation'])

    # store_named_attribute: store UV Map
    store_uv = ng.nodes.new('GeometryNodeStoreNamedAttribute')
    store_uv.data_type = 'FLOAT_VECTOR'
    store_uv.domain = 'CORNER'
    ng.links.new(transform.outputs[0], store_uv.inputs['Geometry'])
    store_uv.inputs['Name'].default_value = "UVMap"
    # Value socket for FLOAT_VECTOR - use named access
    ng.links.new(cube.outputs['UV Map'], store_uv.inputs['Value'])

    # output
    ng.links.new(store_uv.outputs[0], group_output.inputs[0])

    return ng

def _set_map_range_vector_inputs(node, from_min_vec, from_max_vec,
                                  to_min_vec=None, to_max_vec=None):
    """Set MapRange FLOAT_VECTOR inputs by finding the vector sockets."""
    # In Blender 5.0 FLOAT_VECTOR MapRange, the vector sockets are named:
    # "From Min" (vector), "From Max" (vector), "To Min" (vector), "To Max" (vector)
    # But there are also float sockets with the same names. We need the vector ones.
    # Strategy: find all inputs, set by index based on Blender version.
    #
    # The code used indices 9 and 10 for From Min Vec and From Max Vec.
    # In Blender 5.0 (and 4.x), for FLOAT_VECTOR MapRange:
    #   Index 0: Value (float, hidden)
    #   Index 1: From Min (float, hidden)
    #   Index 2: From Max (float, hidden)
    #   Index 3: To Min (float, hidden)
    #   Index 4: To Max (float, hidden)
    #   Index 5: Steps (float, hidden)
    #   Index 6: Vector
    #   Index 7: From Min (vector)
    #   Index 8: From Max (vector)
    #   Index 9: To Min (vector)
    #   Index 10: To Max (vector)
    #   Index 11: Steps (vector)
    #
    # Wait - the code set 9: (0.5,...) and 10: (-0.5,...).
    # In the original, input 9 was "From Min Vector" and 10 was "From Max Vector"
    # But that maps (0.5→-0.5) which is From Min to From Max... that makes the mapping
    # go from [0.5, -0.5] to [default to_min, default to_max] = [0, 1]
    # Actually looking more carefully: the uses indices 9 and 10.
    # In Blender 4.x these were indices for the FLOAT_VECTOR variant.
    # Let me just try setting by index and see.

    # Actually, re-reading the original code:
    # map_range with data_type FLOAT_VECTOR, input_kwargs={
    #     "Vector": group_input.outputs["CenteringLoc"],
    #     9: (0.5, 0.5, 0.5),    <-- From Min (vector)
    #     10: (-0.5, -0.5, -0.5),  <-- From Max (vector)
    # }
    # In Blender 5.0, the vector sockets indices may differ.
    # Let's find them by name+type.

    vec_inputs = []
    for i, inp in enumerate(node.inputs):
        if inp.type == 'VECTOR' and inp.name != 'Vector':
            vec_inputs.append((i, inp.name, inp))

    # vec_inputs should be: From Min, From Max, To Min, To Max, Steps (all vector)
    # Set From Min and From Max
    for idx, name, inp in vec_inputs:
        if 'From Min' in name or name == 'From Min':
            inp.default_value = from_min_vec
        elif 'From Max' in name or name == 'From Max':
            inp.default_value = from_max_vec
        elif to_min_vec is not None and ('To Min' in name or name == 'To Min'):
            inp.default_value = to_min_vec
        elif to_max_vec is not None and ('To Max' in name or name == 'To Max'):
            inp.default_value = to_max_vec

# ═══════════════════════════════════════════════════════════════
#  Helper: find Switch node socket by role
# ═══════════════════════════════════════════════════════════════
def create_sofa_geometry(corner_cube_ng, array_fill_line_ng):
    ng = bpy.data.node_groups.new("nodegroup_sofa_geometry", 'GeometryNodeTree')

    # ── Interface sockets (inputs) ──
    s_geom_in = ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    s_dims = ng.interface.new_socket('Dimensions', in_out='INPUT', socket_type='NodeSocketVector')
    s_dims.default_value = (0.0, 0.9, 2.5)
    s_arm_dims = ng.interface.new_socket('Arm Dimensions', in_out='INPUT', socket_type='NodeSocketVector')
    s_back_dims = ng.interface.new_socket('Back Dimensions', in_out='INPUT', socket_type='NodeSocketVector')
    s_seat_dims = ng.interface.new_socket('Seat Dimensions', in_out='INPUT', socket_type='NodeSocketVector')
    s_foot_dims = ng.interface.new_socket('Foot Dimensions', in_out='INPUT', socket_type='NodeSocketVector')
    s_baseboard = ng.interface.new_socket('Baseboard Height', in_out='INPUT', socket_type='NodeSocketFloat')
    s_baseboard.default_value = 0.13
    s_backrest_w = ng.interface.new_socket('Backrest Width', in_out='INPUT', socket_type='NodeSocketFloat')
    s_backrest_w.default_value = 0.11
    s_seat_margin = ng.interface.new_socket('Seat Margin', in_out='INPUT', socket_type='NodeSocketFloat')
    s_seat_margin.default_value = 0.97
    s_backrest_angle = ng.interface.new_socket('Backrest Angle', in_out='INPUT', socket_type='NodeSocketFloat')
    s_backrest_angle.default_value = -0.2
    s_arm_width = ng.interface.new_socket('arm_width', in_out='INPUT', socket_type='NodeSocketFloat')
    s_arm_width.default_value = 0.7
    s_arm_type = ng.interface.new_socket('Arm Type', in_out='INPUT', socket_type='NodeSocketInt')
    s_arm_type.default_value = 0
    s_arm_height = ng.interface.new_socket('Arm_height', in_out='INPUT', socket_type='NodeSocketFloat')
    s_arm_height.default_value = 0.7318
    s_arms_angle = ng.interface.new_socket('arms_angle', in_out='INPUT', socket_type='NodeSocketFloat')
    s_arms_angle.default_value = 0.8727
    s_footrest = ng.interface.new_socket('Footrest', in_out='INPUT', socket_type='NodeSocketBool')
    s_footrest.default_value = False
    s_count = ng.interface.new_socket('Count', in_out='INPUT', socket_type='NodeSocketInt')
    s_count.default_value = 4
    s_scaling_fr = ng.interface.new_socket('Scaling footrest', in_out='INPUT', socket_type='NodeSocketFloat')
    s_scaling_fr.default_value = 1.5
    s_reflection = ng.interface.new_socket('Reflection', in_out='INPUT', socket_type='NodeSocketInt')
    s_reflection.default_value = 0
    s_leg_type = ng.interface.new_socket('leg_type', in_out='INPUT', socket_type='NodeSocketBool')
    s_leg_type.default_value = False
    s_leg_dimensions = ng.interface.new_socket('leg_dimensions', in_out='INPUT', socket_type='NodeSocketFloat')
    s_leg_dimensions.default_value = 0.5
    s_leg_z = ng.interface.new_socket('leg_z', in_out='INPUT', socket_type='NodeSocketFloat')
    s_leg_z.default_value = 1.0
    s_leg_faces = ng.interface.new_socket('leg_faces', in_out='INPUT', socket_type='NodeSocketInt')
    s_leg_faces.default_value = 20
    s_subdivide = ng.interface.new_socket('Subdivide', in_out='INPUT', socket_type='NodeSocketBool')
    s_subdivide.default_value = True

    # ── Interface sockets (outputs) ──
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('BoundingBox', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # ── Nodes ──
    group_input = ng.nodes.new('NodeGroupInput')
    group_output = ng.nodes.new('NodeGroupOutput')

    # ─── multiply: Dimensions * (0, 0.5, 0) ───
    multiply = ng.nodes.new('ShaderNodeVectorMath')
    multiply.operation = 'MULTIPLY'
    multiply.inputs[1].default_value = (0.0, 0.5, 0.0)
    ng.links.new(group_input.outputs['Dimensions'], multiply.inputs[0])

    # ─── reroute (Arm Dimensions) ───
    # We don't need actual Reroute nodes in standalone; just use the output directly.
    # But for clarity and correct connection tracking, we'll skip reroutes
    # and connect directly.

    # ─── arm_cube: corner_cube(Location=multiply, CenteringLoc=(0,1,0), Dimensions=ArmDims, VerticesZ=10) ───
    arm_cube = ng.nodes.new('GeometryNodeGroup')
    arm_cube.node_tree = corner_cube_ng
    arm_cube.inputs['CenteringLoc'].default_value = (0.0, 1.0, 0.0)
    arm_cube.inputs['Vertices Z'].default_value = 10
    ng.links.new(multiply.outputs[0], arm_cube.inputs['Location'])
    ng.links.new(group_input.outputs['Arm Dimensions'], arm_cube.inputs['Dimensions'])

    # ─── position ───
    position = ng.nodes.new('GeometryNodeInputPosition')

    # ─── separate_xyz (position) ───
    sep_xyz = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position.outputs[0], sep_xyz.inputs[0])

    # ─── separate_xyz_1 (Arm Dimensions) ───
    sep_xyz_1 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(group_input.outputs['Arm Dimensions'], sep_xyz_1.inputs[0])

    # ─── map_range: Value=sep_xyz.Z, 1=-0.1, 2=sep_xyz_1.Z, 3=-0.1, 4=0.2 ───
    map_range = ng.nodes.new('ShaderNodeMapRange')
    map_range.data_type = 'FLOAT'
    ng.links.new(sep_xyz.outputs['Z'], map_range.inputs['Value'])
    map_range.inputs['From Min'].default_value = -0.1
    ng.links.new(sep_xyz_1.outputs['Z'], map_range.inputs['From Max'])
    map_range.inputs['To Min'].default_value = -0.1
    map_range.inputs['To Max'].default_value = 0.2

    # ─── float_curve: Factor=arm_width, Value=map_range.Result ───
    float_curve = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(group_input.outputs['arm_width'], float_curve.inputs['Factor'])
    ng.links.new(map_range.outputs['Result'], float_curve.inputs['Value'])
    assign_curve(float_curve.mapping.curves[0], [
        (0.0092, 0.7688),
        (0.1011, 0.5937),
        (0.1494, 0.4062),
        (0.3954, 0.0781),
        (1.0000, 0.2187),
    ])

    # ─── separate_xyz_2 (multiply output = half-dims) ───
    sep_xyz_2 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(multiply.outputs[0], sep_xyz_2.inputs[0])

    # ─── subtract: sep_xyz.Y - sep_xyz_2.Y ───
    subtract = ng.nodes.new('ShaderNodeMath')
    subtract.operation = 'SUBTRACT'
    ng.links.new(sep_xyz.outputs['Y'], subtract.inputs[0])
    ng.links.new(sep_xyz_2.outputs['Y'], subtract.inputs[1])

    # ─── multiply_1: float_curve * subtract ───
    multiply_1 = ng.nodes.new('ShaderNodeMath')
    multiply_1.operation = 'MULTIPLY'
    ng.links.new(float_curve.outputs[0], multiply_1.inputs[0])
    ng.links.new(subtract.outputs[0], multiply_1.inputs[1])

    # ─── position_1 ───
    position_1 = ng.nodes.new('GeometryNodeInputPosition')

    # ─── separate_xyz_14 (position_1) ───
    sep_xyz_14 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(position_1.outputs[0], sep_xyz_14.inputs[0])

    # ─── map_range_1: Value=sep_xyz_14.X, 1=-1, 2=0.6, 3=2.1, 4=-1.1 ───
    map_range_1 = ng.nodes.new('ShaderNodeMapRange')
    map_range_1.data_type = 'FLOAT'
    ng.links.new(sep_xyz_14.outputs['X'], map_range_1.inputs['Value'])
    map_range_1.inputs['From Min'].default_value = -1.0
    map_range_1.inputs['From Max'].default_value = 0.6
    map_range_1.inputs['To Min'].default_value = 2.1
    map_range_1.inputs['To Max'].default_value = -1.1

    # ─── float_curve_1: Factor=Arm_height, Value=map_range_1.Result ───
    float_curve_1 = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(group_input.outputs['Arm_height'], float_curve_1.inputs['Factor'])
    ng.links.new(map_range_1.outputs['Result'], float_curve_1.inputs['Value'])
    assign_curve(float_curve_1.mapping.curves[0], [
        (0.1341, 0.2094),
        (0.7386, 1.0000),
        (0.9682, 0.0781),
        (1.0000, 0.0000),
    ])

    # ─── separate_xyz_15: constant (-2.9, 3.3, 0.0) ───
    sep_xyz_15 = ng.nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz_15.inputs[0].default_value = (-2.9, 3.3, 0.0)

    # ─── subtract_1: sep_xyz_14.Z - sep_xyz_15.Z ───
    subtract_1 = ng.nodes.new('ShaderNodeMath')
    subtract_1.operation = 'SUBTRACT'
    ng.links.new(sep_xyz_14.outputs['Z'], subtract_1.inputs[0])
    ng.links.new(sep_xyz_15.outputs['Z'], subtract_1.inputs[1])

    # ─── multiply_2: float_curve_1 * subtract_1 ───
    multiply_2 = ng.nodes.new('ShaderNodeMath')
    multiply_2.operation = 'MULTIPLY'
    ng.links.new(float_curve_1.outputs[0], multiply_2.inputs[0])
    ng.links.new(subtract_1.outputs[0], multiply_2.inputs[1])

    # ─── combine_xyz: Y=multiply_1, Z=multiply_2 ───
    combine_xyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(multiply_1.outputs[0], combine_xyz.inputs['Y'])
    ng.links.new(multiply_2.outputs[0], combine_xyz.inputs['Z'])

    # ─── vector_rotate: Vector=combine_xyz, Axis=(1,0,0), Angle=arms_angle ───
    vector_rotate = ng.nodes.new('ShaderNodeVectorRotate')
    vector_rotate.inputs['Axis'].default_value = (1.0, 0.0, 0.0)
    ng.links.new(combine_xyz.outputs[0], vector_rotate.inputs['Vector'])
    ng.links.new(group_input.outputs['arms_angle'], vector_rotate.inputs['Angle'])

    # ─── set_position: Geometry=arm_cube, Offset=vector_rotate ───
    set_position = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(arm_cube.outputs[0], set_position.inputs['Geometry'])
    ng.links.new(vector_rotate.outputs[0], set_position.inputs['Offset'])

    # ─── multiply_3: Dimensions * (0, 0.5, 0) (same as multiply) ───
    multiply_3 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_3.operation = 'MULTIPLY'
    multiply_3.inputs[1].default_value = (0.0, 0.5, 0.0)
    ng.links.new(group_input.outputs['Dimensions'], multiply_3.inputs[0])

    # ─── separate_xyz_3: Arm Dimensions ───
    sep_xyz_3 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(group_input.outputs['Arm Dimensions'], sep_xyz_3.inputs[0])

    # ─── subtract_2: sep_xyz_3.Z - sep_xyz_3.Y ───
    subtract_2 = ng.nodes.new('ShaderNodeMath')
    subtract_2.operation = 'SUBTRACT'
    ng.links.new(sep_xyz_3.outputs['Z'], subtract_2.inputs[0])
    ng.links.new(sep_xyz_3.outputs['Y'], subtract_2.inputs[1])

    # ─── combine_xyz_1: X=sep_xyz_3.X, Y=sep_xyz_3.Y, Z=subtract_2 ───
    combine_xyz_1 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(sep_xyz_3.outputs['X'], combine_xyz_1.inputs['X'])
    ng.links.new(sep_xyz_3.outputs['Y'], combine_xyz_1.inputs['Y'])
    ng.links.new(subtract_2.outputs[0], combine_xyz_1.inputs['Z'])

    # ─── arm_cube_1: corner_cube(Location=multiply_3, CenteringLoc=(0,1,0), Dimensions=combine_xyz_1) ───
    arm_cube_1 = ng.nodes.new('GeometryNodeGroup')
    arm_cube_1.node_tree =corner_cube_ng
    arm_cube_1.inputs['CenteringLoc'].default_value = (0.0, 1.0, 0.0)
    ng.links.new(multiply_3.outputs[0], arm_cube_1.inputs['Location'])
    ng.links.new(combine_xyz_1.outputs[0], arm_cube_1.inputs['Dimensions'])

    # ─── separate_xyz_4: combine_xyz_1 ───
    sep_xyz_4 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(combine_xyz_1.outputs[0], sep_xyz_4.inputs[0])

    # ─── multiply_4: sep_xyz_4.X * 1.0001 ───
    multiply_4 = ng.nodes.new('ShaderNodeMath')
    multiply_4.operation = 'MULTIPLY'
    multiply_4.inputs[1].default_value = 1.0001
    ng.links.new(sep_xyz_4.outputs['X'], multiply_4.inputs[0])

    # ─── arm_cylinder: MeshCylinder(SideSegments=4, Radius=sep_xyz_4.Y, Depth=multiply_4) ───
    arm_cylinder = ng.nodes.new('GeometryNodeMeshCylinder')
    arm_cylinder.fill_type = 'TRIANGLE_FAN'
    arm_cylinder.inputs['Side Segments'].default_value = 4
    ng.links.new(sep_xyz_4.outputs['Y'], arm_cylinder.inputs['Radius'])
    ng.links.new(multiply_4.outputs[0], arm_cylinder.inputs['Depth'])

    # ─── store UV on cylinder ───
    store_uv_cyl = ng.nodes.new('GeometryNodeStoreNamedAttribute')
    store_uv_cyl.data_type = 'FLOAT_VECTOR'
    store_uv_cyl.domain = 'CORNER'
    store_uv_cyl.inputs['Name'].default_value = "UVMap"
    ng.links.new(arm_cylinder.outputs['Mesh'], store_uv_cyl.inputs['Geometry'])
    ng.links.new(arm_cylinder.outputs['UV Map'], store_uv_cyl.inputs['Value'])

    # ─── divide: multiply_4 / 2 ───
    divide = ng.nodes.new('ShaderNodeMath')
    divide.operation = 'DIVIDE'
    divide.inputs[1].default_value = 2.0
    ng.links.new(multiply_4.outputs[0], divide.inputs[0])

    # ─── separate_xyz_5: multiply_3 output ───
    sep_xyz_5 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(multiply_3.outputs[0], sep_xyz_5.inputs[0])

    # ─── combine_xyz_2: X=divide, Y=sep_xyz_5.Y, Z=sep_xyz_4.Z ───
    combine_xyz_2 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(divide.outputs[0], combine_xyz_2.inputs['X'])
    ng.links.new(sep_xyz_5.outputs['Y'], combine_xyz_2.inputs['Y'])
    ng.links.new(sep_xyz_4.outputs['Z'], combine_xyz_2.inputs['Z'])

    # ─── transform cylinder: Translation=combine_xyz_2, Rotation=(0, pi/2, 0) ───
    transform_cyl = ng.nodes.new('GeometryNodeTransform')
    transform_cyl.inputs['Rotation'].default_value = (0.0, 1.5708, 0.0)
    ng.links.new(store_uv_cyl.outputs[0], transform_cyl.inputs['Geometry'])
    ng.links.new(combine_xyz_2.outputs[0], transform_cyl.inputs['Translation'])

    # ─── roundtop: JoinGeometry(arm_cube_1, transform_cyl) ───
    roundtop = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(arm_cube_1.outputs[0], roundtop.inputs[0])
    ng.links.new(transform_cyl.outputs[0], roundtop.inputs[0])

    # ─── Compare: Arm Type == ARM_TYPE_SQUARE (0) ───
    compare_sq = ng.nodes.new('FunctionNodeCompare')
    compare_sq.data_type = 'INT'
    compare_sq.operation = 'EQUAL'
    ng.links.new(group_input.outputs['Arm Type'], compare_sq.inputs[2])
    compare_sq.inputs[3].default_value = ARM_TYPE_SQUARE

    # ─── square_or_round: Switch(compare_sq, False=roundtop, True=arm_cube_1) ───
    switch_sq_round = ng.nodes.new('GeometryNodeSwitch')
    # default input_type is GEOMETRY
    ng.links.new(compare_sq.outputs[0], switch_sq_round.inputs[0])
    ng.links.new(roundtop.outputs[0], switch_sq_round.inputs[1])  # False
    ng.links.new(arm_cube_1.outputs[0], switch_sq_round.inputs[2])  # True

    # ─── Compare: Arm Type == ARM_TYPE_ANGULAR (2) ───
    compare_ang = ng.nodes.new('FunctionNodeCompare')
    compare_ang.data_type = 'INT'
    compare_ang.operation = 'EQUAL'
    ng.links.new(group_input.outputs['Arm Type'], compare_ang.inputs[2])
    compare_ang.inputs[3].default_value = ARM_TYPE_ANGULAR

    # ─── angular_or_squareround: Switch(compare_ang, False=square_or_round, True=set_position) ───
    switch_ang = ng.nodes.new('GeometryNodeSwitch')
    ng.links.new(compare_ang.outputs[0], switch_ang.inputs[0])
    ng.links.new(switch_sq_round.outputs[0], switch_ang.inputs[1])  # False
    ng.links.new(set_position.outputs[0], switch_ang.inputs[2])  # True

    # ─── transform_geometry_1: Scale=(1, -1, 1) to mirror ───
    transform_mirror = ng.nodes.new('GeometryNodeTransform')
    transform_mirror.inputs['Scale'].default_value = (1.0, -1.0, 1.0)
    ng.links.new(switch_ang.outputs[0], transform_mirror.inputs['Geometry'])

    # ─── flip_faces ───
    flip_faces = ng.nodes.new('GeometryNodeFlipFaces')
    ng.links.new(transform_mirror.outputs[0], flip_faces.inputs[0])

    # ─── join_geometry_2: [flip_faces, angular_or_squareround] ───
    join_2 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(flip_faces.outputs[0], join_2.inputs[0])
    ng.links.new(switch_ang.outputs[0], join_2.inputs[0])

    # ─── separate_xyz_6: Back Dimensions ───
    sep_xyz_6 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(group_input.outputs['Back Dimensions'], sep_xyz_6.inputs[0])

    # ─── separate_xyz_7: Arm Dimensions ───
    sep_xyz_7 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(group_input.outputs['Arm Dimensions'], sep_xyz_7.inputs[0])

    # ─── separate_xyz_8: Dimensions ───
    sep_xyz_8 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(group_input.outputs['Dimensions'], sep_xyz_8.inputs[0])

    # ─── multiply_add: sep_xyz_7.Y * -2 + sep_xyz_8.Y ───
    multiply_add_node = ng.nodes.new('ShaderNodeMath')
    multiply_add_node.operation = 'MULTIPLY_ADD'
    ng.links.new(sep_xyz_7.outputs['Y'], multiply_add_node.inputs[0])
    multiply_add_node.inputs[1].default_value = -2.0
    ng.links.new(sep_xyz_8.outputs['Y'], multiply_add_node.inputs[2])

    # ─── combine_xyz_3: X=sep_xyz_6.X, Y=multiply_add, Z=sep_xyz_6.Z ───
    combine_xyz_3 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(sep_xyz_6.outputs['X'], combine_xyz_3.inputs['X'])
    ng.links.new(multiply_add_node.outputs[0], combine_xyz_3.inputs['Y'])
    ng.links.new(sep_xyz_6.outputs['Z'], combine_xyz_3.inputs['Z'])

    # ─── back_board: corner_cube(CenteringLoc=(0,0.5,-1), Dimensions=combine_xyz_3, Verts=2,2,2) ───
    back_board = ng.nodes.new('GeometryNodeGroup')
    back_board.node_tree =corner_cube_ng
    back_board.inputs['CenteringLoc'].default_value = (0.0, 0.5, -1.0)
    back_board.inputs['Vertices X'].default_value = 2
    back_board.inputs['Vertices Y'].default_value = 2
    back_board.inputs['Vertices Z'].default_value = 2
    ng.links.new(combine_xyz_3.outputs[0], back_board.inputs['Dimensions'])

    # ─── join_geometry_3: [join_2, back_board] ───
    join_3 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(join_2.outputs[0], join_3.inputs[0])
    ng.links.new(back_board.outputs[0], join_3.inputs[0])

    # ─── multiply_5: combine_xyz_3 * (1, 0, 0) ───
    multiply_5 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_5.operation = 'MULTIPLY'
    multiply_5.inputs[1].default_value = (1.0, 0.0, 0.0)
    ng.links.new(combine_xyz_3.outputs[0], multiply_5.inputs[0])

    # ─── multiply_add_1: Arm Dimensions * (0, -2, 0) + Dimensions ───
    multiply_add_1 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_add_1.operation = 'MULTIPLY_ADD'
    multiply_add_1.inputs[1].default_value = (0.0, -2.0, 0.0)
    ng.links.new(group_input.outputs['Arm Dimensions'], multiply_add_1.inputs[0])
    ng.links.new(group_input.outputs['Dimensions'], multiply_add_1.inputs[2])

    # ─── multiply_add_2: Back Dimensions * (-1, 0, 0) + multiply_add_1 ───
    multiply_add_2 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_add_2.operation = 'MULTIPLY_ADD'
    multiply_add_2.inputs[1].default_value = (-1.0, 0.0, 0.0)
    ng.links.new(group_input.outputs['Back Dimensions'], multiply_add_2.inputs[0])
    ng.links.new(multiply_add_1.outputs[0], multiply_add_2.inputs[2])

    # ─── separate_xyz_9: multiply_add_2 ───
    sep_xyz_9 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(multiply_add_2.outputs[0], sep_xyz_9.inputs[0])

    # ─── combine_xyz_4: X=sep_xyz_9.X, Y=sep_xyz_9.Y, Z=Baseboard Height ───
    combine_xyz_4 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(sep_xyz_9.outputs['X'], combine_xyz_4.inputs['X'])
    ng.links.new(sep_xyz_9.outputs['Y'], combine_xyz_4.inputs['Y'])
    ng.links.new(group_input.outputs['Baseboard Height'], combine_xyz_4.inputs['Z'])

    # ─── base_board: corner_cube(Location=multiply_5, CenteringLoc=(0,0.5,-1), Dims=combine_xyz_4, Verts=2,2,2) ───
    base_board = ng.nodes.new('GeometryNodeGroup')
    base_board.node_tree =corner_cube_ng
    base_board.inputs['CenteringLoc'].default_value = (0.0, 0.5, -1.0)
    base_board.inputs['Vertices X'].default_value = 2
    base_board.inputs['Vertices Y'].default_value = 2
    base_board.inputs['Vertices Z'].default_value = 2
    ng.links.new(multiply_5.outputs[0], base_board.inputs['Location'])
    ng.links.new(combine_xyz_4.outputs[0], base_board.inputs['Dimensions'])

    # ─── equal: Count == 4 ───
    equal = ng.nodes.new('FunctionNodeCompare')
    equal.data_type = 'INT'
    equal.operation = 'EQUAL'
    equal.inputs[3].default_value = 4
    ng.links.new(group_input.outputs['Count'], equal.inputs[2])

    # ─── reroute_5: sep_xyz_9.Y (reused as reroute_5) ───
    # (just reference sep_xyz_9.outputs['Y'] directly)

    # ─── separate_xyz_10: Seat Dimensions ───
    sep_xyz_10 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(group_input.outputs['Seat Dimensions'], sep_xyz_10.inputs[0])

    # ─── divide_1: sep_xyz_9.Y / sep_xyz_10.Y ───
    divide_1 = ng.nodes.new('ShaderNodeMath')
    divide_1.operation = 'DIVIDE'
    ng.links.new(sep_xyz_9.outputs['Y'], divide_1.inputs[0])
    ng.links.new(sep_xyz_10.outputs['Y'], divide_1.inputs[1])

    # ─── ceil: ceil(divide_1) ───
    ceil_node = ng.nodes.new('ShaderNodeMath')
    ceil_node.operation = 'CEIL'
    ng.links.new(divide_1.outputs[0], ceil_node.inputs[0])

    # ─── combine_xyz_14: (1, ceil, 1) ───
    combine_xyz_14 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_14.inputs['X'].default_value = 1.0
    combine_xyz_14.inputs['Z'].default_value = 1.0
    ng.links.new(ceil_node.outputs[0], combine_xyz_14.inputs['Y'])

    # ─── divide_2: combine_xyz_4 / combine_xyz_14 ───
    divide_2 = ng.nodes.new('ShaderNodeVectorMath')
    divide_2.operation = 'DIVIDE'
    ng.links.new(combine_xyz_4.outputs[0], divide_2.inputs[0])
    ng.links.new(combine_xyz_14.outputs[0], divide_2.inputs[1])

    # ─── base_board_1: corner_cube(Location=multiply_5, CenteringLoc=(0,0.5,-1), Dims=divide_2, Verts=2,2,2) ───
    base_board_1 = ng.nodes.new('GeometryNodeGroup')
    base_board_1.node_tree =corner_cube_ng
    base_board_1.inputs['CenteringLoc'].default_value = (0.0, 0.5, -1.0)
    base_board_1.inputs['Vertices X'].default_value = 2
    base_board_1.inputs['Vertices Y'].default_value = 2
    base_board_1.inputs['Vertices Z'].default_value = 2
    ng.links.new(multiply_5.outputs[0], base_board_1.inputs['Location'])
    ng.links.new(divide_2.outputs[0], base_board_1.inputs['Dimensions'])

    # ─── equal_1: Count == 4 (same comparison) ───
    equal_1 = ng.nodes.new('FunctionNodeCompare')
    equal_1.data_type = 'INT'
    equal_1.operation = 'EQUAL'
    equal_1.inputs[3].default_value = 4
    ng.links.new(group_input.outputs['Count'], equal_1.inputs[2])

    # ─── switch_8: input_type=VECTOR, 0=equal_1, 1=divide_2(False), 2=combine_xyz_4(True) ───
    switch_8 = ng.nodes.new('GeometryNodeSwitch')
    switch_8.input_type = 'VECTOR'
    ng.links.new(equal_1.outputs[0], switch_8.inputs[0])
    ng.links.new(divide_2.outputs[0], switch_8.inputs[1])  # False
    ng.links.new(combine_xyz_4.outputs[0], switch_8.inputs[2])  # True

    # ─── separate_xyz_16: switch_8 output ───
    sep_xyz_16 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(switch_8.outputs[0], sep_xyz_16.inputs[0])

    # ─── multiply_6: sep_xyz_16.Y * 0.7 ───
    multiply_6 = ng.nodes.new('ShaderNodeMath')
    multiply_6.operation = 'MULTIPLY'
    multiply_6.inputs[1].default_value = 0.7
    ng.links.new(sep_xyz_16.outputs['Y'], multiply_6.inputs[0])

    # ─── grid_1: MeshGrid(SizeY=multiply_6, VerticesX=1, VerticesY=2) ───
    grid_1 = ng.nodes.new('GeometryNodeMeshGrid')
    grid_1.inputs['Vertices X'].default_value = 1
    grid_1.inputs['Vertices Y'].default_value = 2
    ng.links.new(multiply_6.outputs[0], grid_1.inputs['Size Y'])

    # ─── combine_xyz_18: (0.1, sep_xyz_16.Y, sep_xyz_16.Z) ───
    combine_xyz_18 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_18.inputs['X'].default_value = 0.1
    ng.links.new(sep_xyz_16.outputs['Y'], combine_xyz_18.inputs['Y'])
    ng.links.new(sep_xyz_16.outputs['Z'], combine_xyz_18.inputs['Z'])

    # ─── subtract_3: switch_8 - combine_xyz_18 ───
    subtract_3 = ng.nodes.new('ShaderNodeVectorMath')
    subtract_3.operation = 'SUBTRACT'
    ng.links.new(switch_8.outputs[0], subtract_3.inputs[0])
    ng.links.new(combine_xyz_18.outputs[0], subtract_3.inputs[1])

    # ─── multiply_7: Back Dimensions * (1, 0, 0) ───
    multiply_7 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_7.operation = 'MULTIPLY'
    multiply_7.inputs[1].default_value = (1.0, 0.0, 0.0)
    ng.links.new(group_input.outputs['Back Dimensions'], multiply_7.inputs[0])

    # ─── add: subtract_3 + multiply_7 ───
    add_node = ng.nodes.new('ShaderNodeVectorMath')
    add_node.operation = 'ADD'
    ng.links.new(subtract_3.outputs[0], add_node.inputs[0])
    ng.links.new(multiply_7.outputs[0], add_node.inputs[1])

    # ─── transform_geometry_10: grid_1, Translation=add, Scale=(1,1,0.9) ───
    transform_10 = ng.nodes.new('GeometryNodeTransform')
    transform_10.inputs['Scale'].default_value = (1.0, 1.0, 0.9)
    ng.links.new(grid_1.outputs['Mesh'], transform_10.inputs['Geometry'])
    ng.links.new(add_node.outputs[0], transform_10.inputs['Translation'])

    # ─── cone: MeshCone (wider body-end for better visual connection) ───
    cone = ng.nodes.new('GeometryNodeMeshCone')
    cone.inputs['Side Segments'].default_value = 4
    cone.inputs['Radius Top'].default_value = 0.015
    cone.inputs['Radius Bottom'].default_value = 0.06
    cone.inputs['Depth'].default_value = 0.10
    ng.links.new(group_input.outputs['leg_faces'], cone.inputs['Vertices'])

    # ─── combine_xyz_17: (leg_dimensions, leg_dimensions, leg_z) ───
    combine_xyz_17 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(group_input.outputs['leg_dimensions'], combine_xyz_17.inputs['X'])
    ng.links.new(group_input.outputs['leg_dimensions'], combine_xyz_17.inputs['Y'])
    ng.links.new(group_input.outputs['leg_z'], combine_xyz_17.inputs['Z'])

    # ─── transform_geometry_9: cone, Translation=(0,0,0.01), Rotation=(0,pi,0), Scale=combine_xyz_17 ───
    transform_9 = ng.nodes.new('GeometryNodeTransform')
    transform_9.inputs['Translation'].default_value = (0.0, 0.0, 0.03)
    transform_9.inputs['Rotation'].default_value = (0.0, 3.1416, 0.0)
    ng.links.new(cone.outputs['Mesh'], transform_9.inputs['Geometry'])
    ng.links.new(combine_xyz_17.outputs[0], transform_9.inputs['Scale'])

    # ─── foot_cube: corner_cube(CenteringLoc=(0.5,0.5,0.75), Dims=Foot Dimensions) ───
    foot_cube = ng.nodes.new('GeometryNodeGroup')
    foot_cube.node_tree =corner_cube_ng
    foot_cube.inputs['CenteringLoc'].default_value = (0.5, 0.5, 0.75)
    ng.links.new(group_input.outputs['Foot Dimensions'], foot_cube.inputs['Dimensions'])

    # ─── transform_geometry_12: foot_cube, Translation + Scale for baseboard junction ───
    transform_12 = ng.nodes.new('GeometryNodeTransform')
    transform_12.inputs['Translation'].default_value = (0.0, 0.0, 0.04)
    transform_12.inputs['Scale'].default_value = (0.6, 0.9, 0.9)
    ng.links.new(foot_cube.outputs[0], transform_12.inputs['Geometry'])

    # ─── switch_6: Switch(leg_type, False=transform_9, True=transform_12) ───
    switch_6 = ng.nodes.new('GeometryNodeSwitch')
    ng.links.new(group_input.outputs['leg_type'], switch_6.inputs[0])
    ng.links.new(transform_9.outputs[0], switch_6.inputs[1])  # False
    ng.links.new(transform_12.outputs[0], switch_6.inputs[2])  # True

    # ─── transform_geometry_8: switch_6 (just pass-through transform) ───
    transform_8 = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(switch_6.outputs[0], transform_8.inputs['Geometry'])

    # ─── instance_on_points_1: Points=transform_10, Instance=transform_8, Scale=(1,1,1.2) ───
    iop_1 = ng.nodes.new('GeometryNodeInstanceOnPoints')
    iop_1.inputs['Scale'].default_value = (1.0, 1.0, 1.2)
    ng.links.new(transform_10.outputs[0], iop_1.inputs['Points'])
    ng.links.new(transform_8.outputs[0], iop_1.inputs['Instance'])

    # ─── realize_instances_1 ───
    realize_1 = ng.nodes.new('GeometryNodeRealizeInstances')
    ng.links.new(iop_1.outputs[0], realize_1.inputs[0])

    # ─── join_geometry_10: [base_board_1, realize_1] ───
    join_10 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(base_board_1.outputs[0], join_10.inputs[0])
    ng.links.new(realize_1.outputs[0], join_10.inputs[0])

    # ─── subtract_4: combine_xyz_14 - (1,1,1) ───
    subtract_4 = ng.nodes.new('ShaderNodeVectorMath')
    subtract_4.operation = 'SUBTRACT'
    subtract_4.inputs[1].default_value = (1.0, 1.0, 1.0)
    ng.links.new(combine_xyz_14.outputs[0], subtract_4.inputs[0])

    # ─── multiply_8: subtract_4 * (0, 0.5, 0) ───
    multiply_8 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_8.operation = 'MULTIPLY'
    multiply_8.inputs[1].default_value = (0.0, 0.5, 0.0)
    ng.links.new(subtract_4.outputs[0], multiply_8.inputs[0])

    # ─── multiply_9: divide_2 * multiply_8 ───
    multiply_9 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_9.operation = 'MULTIPLY'
    ng.links.new(divide_2.outputs[0], multiply_9.inputs[0])
    ng.links.new(multiply_8.outputs[0], multiply_9.inputs[1])

    # ─── combine_xyz_16: (1, Reflection, 1) ───
    combine_xyz_16 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_16.inputs['X'].default_value = 1.0
    combine_xyz_16.inputs['Z'].default_value = 1.0
    ng.links.new(group_input.outputs['Reflection'], combine_xyz_16.inputs['Y'])

    # ─── multiply_10: multiply_9 * combine_xyz_16 ───
    multiply_10 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_10.operation = 'MULTIPLY'
    ng.links.new(multiply_9.outputs[0], multiply_10.inputs[0])
    ng.links.new(combine_xyz_16.outputs[0], multiply_10.inputs[1])

    # ─── combine_xyz_12: (Scaling footrest, 1, 1) ───
    combine_xyz_12 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_12.inputs['Y'].default_value = 1.0
    combine_xyz_12.inputs['Z'].default_value = 1.0
    ng.links.new(group_input.outputs['Scaling footrest'], combine_xyz_12.inputs['X'])

    # ─── transform_geometry_5: join_10, Translation=multiply_10, Scale=combine_xyz_12 ───
    transform_5 = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(join_10.outputs[0], transform_5.inputs['Geometry'])
    ng.links.new(multiply_10.outputs[0], transform_5.inputs['Translation'])
    ng.links.new(combine_xyz_12.outputs[0], transform_5.inputs['Scale'])

    # ─── switch_2: Switch(Footrest, False=None, True=transform_5) ───
    # Original: switch_2 = Switch(0: Footrest, 1: transform_5)  (only input 1 = False connected)
    switch_2 = ng.nodes.new('GeometryNodeSwitch')
    ng.links.new(group_input.outputs['Footrest'], switch_2.inputs[0])
    ng.links.new(transform_5.outputs[0], switch_2.inputs[1])  # False

    # ─── combine_xyz_19: (Scaling footrest, 1.3, 1) ───
    combine_xyz_19 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_19.inputs['Y'].default_value = 1.3
    combine_xyz_19.inputs['Z'].default_value = 1.0
    ng.links.new(group_input.outputs['Scaling footrest'], combine_xyz_19.inputs['X'])

    # ─── transform_geometry_11: realize_1, Scale=combine_xyz_19 ───
    transform_11 = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(realize_1.outputs[0], transform_11.inputs['Geometry'])
    ng.links.new(combine_xyz_19.outputs[0], transform_11.inputs['Scale'])

    # ─── base_board_2: corner_cube(Location=multiply_5, CenteringLoc=(0,0.5,-1), Dims=combine_xyz_4, Verts=3,3,3) ───
    base_board_2 = ng.nodes.new('GeometryNodeGroup')
    base_board_2.node_tree =corner_cube_ng
    base_board_2.inputs['CenteringLoc'].default_value = (0.0, 0.5, -1.0)
    base_board_2.inputs['Vertices X'].default_value = 3
    base_board_2.inputs['Vertices Y'].default_value = 3
    base_board_2.inputs['Vertices Z'].default_value = 3
    ng.links.new(multiply_5.outputs[0], base_board_2.inputs['Location'])
    ng.links.new(combine_xyz_4.outputs[0], base_board_2.inputs['Dimensions'])

    # ─── combine_xyz_13: (Scaling footrest, 1, 1) ───
    combine_xyz_13 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_13.inputs['Y'].default_value = 1.0
    combine_xyz_13.inputs['Z'].default_value = 1.0
    ng.links.new(group_input.outputs['Scaling footrest'], combine_xyz_13.inputs['X'])

    # ─── transform_geometry_6: base_board_2, Scale=combine_xyz_13 ───
    transform_6 = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(base_board_2.outputs[0], transform_6.inputs['Geometry'])
    ng.links.new(combine_xyz_13.outputs[0], transform_6.inputs['Scale'])

    # ─── join_geometry_11: [transform_11, transform_6] ───
    join_11 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(transform_11.outputs[0], join_11.inputs[0])
    ng.links.new(transform_6.outputs[0], join_11.inputs[0])

    # ─── switch_4: Switch(Footrest, False=None, True=join_11) ───
    switch_4 = ng.nodes.new('GeometryNodeSwitch')
    ng.links.new(group_input.outputs['Footrest'], switch_4.inputs[0])
    ng.links.new(join_11.outputs[0], switch_4.inputs[2])  # True

    # ─── switch_5: Switch(equal, False=switch_2, True=switch_4) ───
    switch_5 = ng.nodes.new('GeometryNodeSwitch')
    ng.links.new(equal.outputs[0], switch_5.inputs[0])
    ng.links.new(switch_2.outputs[0], switch_5.inputs[1])  # False
    ng.links.new(switch_4.outputs[0], switch_5.inputs[2])  # True

    # ─── join_geometry_4: [join_3, base_board, switch_5] ───
    join_4 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(join_3.outputs[0], join_4.inputs[0])
    ng.links.new(base_board.outputs[0], join_4.inputs[0])
    ng.links.new(switch_5.outputs[0], join_4.inputs[0])

    # ─── grid: MeshGrid(VerticesX=2, VerticesY=2) ───
    grid = ng.nodes.new('GeometryNodeMeshGrid')
    grid.inputs['Vertices X'].default_value = 2
    grid.inputs['Vertices Y'].default_value = 2

    # ─── multiply_11: Dimensions * (0.5, 0, 0) ───
    multiply_11 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_11.operation = 'MULTIPLY'
    multiply_11.inputs[1].default_value = (0.5, 0.0, 0.0)
    ng.links.new(group_input.outputs['Dimensions'], multiply_11.inputs[0])

    # ─── multiply_12: Dimensions * (1, 1, 0) ───
    multiply_12 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_12.operation = 'MULTIPLY'
    multiply_12.inputs[1].default_value = (1.0, 1.0, 0.0)
    ng.links.new(group_input.outputs['Dimensions'], multiply_12.inputs[0])

    # ─── multiply_13: Foot Dimensions * (2.5, 2.5, 0) ───
    multiply_13 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_13.operation = 'MULTIPLY'
    multiply_13.inputs[1].default_value = (2.5, 2.5, 0.0)
    ng.links.new(group_input.outputs['Foot Dimensions'], multiply_13.inputs[0])

    # ─── subtract_5: multiply_12 - multiply_13 ───
    subtract_5 = ng.nodes.new('ShaderNodeVectorMath')
    subtract_5.operation = 'SUBTRACT'
    ng.links.new(multiply_12.outputs[0], subtract_5.inputs[0])
    ng.links.new(multiply_13.outputs[0], subtract_5.inputs[1])

    # ─── transform_geometry_2: grid, Translation=multiply_11, Scale=subtract_5 ───
    transform_2 = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(grid.outputs['Mesh'], transform_2.inputs['Geometry'])
    ng.links.new(multiply_11.outputs[0], transform_2.inputs['Translation'])
    ng.links.new(subtract_5.outputs[0], transform_2.inputs['Scale'])

    # ─── instance_on_points: Points=transform_2, Instance=transform_8 ───
    iop = ng.nodes.new('GeometryNodeInstanceOnPoints')
    ng.links.new(transform_2.outputs[0], iop.inputs['Points'])
    ng.links.new(transform_8.outputs[0], iop.inputs['Instance'])

    # ─── realize_instances ───
    realize = ng.nodes.new('GeometryNodeRealizeInstances')
    ng.links.new(iop.outputs[0], realize.inputs[0])

    # ─── join_geometry_5: [join_4, realize] ───
    join_5 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(join_4.outputs[0], join_5.inputs[0])
    ng.links.new(realize.outputs[0], join_5.inputs[0])

    # ─── equal_2: Count == 4 ───
    equal_2 = ng.nodes.new('FunctionNodeCompare')
    equal_2.data_type = 'INT'
    equal_2.operation = 'EQUAL'
    equal_2.inputs[3].default_value = 4
    ng.links.new(group_input.outputs['Count'], equal_2.inputs[2])

    # ─── multiply_14: combine_xyz_4 * (0, -0.5, 1) ───
    multiply_14 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_14.operation = 'MULTIPLY'
    multiply_14.inputs[1].default_value = (0.0, -0.5, 1.0)
    ng.links.new(combine_xyz_4.outputs[0], multiply_14.inputs[0])

    # ─── multiply_15: combine_xyz_4 * (0, 0.5, 1) ───
    multiply_15 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_15.operation = 'MULTIPLY'
    multiply_15.inputs[1].default_value = (0.0, 0.5, 1.0)
    ng.links.new(combine_xyz_4.outputs[0], multiply_15.inputs[0])

    # ─── equal_3: Count == 4 ───
    equal_3 = ng.nodes.new('FunctionNodeCompare')
    equal_3.data_type = 'INT'
    equal_3.operation = 'EQUAL'
    equal_3.inputs[3].default_value = 4
    ng.links.new(group_input.outputs['Count'], equal_3.inputs[2])

    # ─── switch_7: input_type=INT, Switch=equal_3, False=Reflection, True=1 ───
    switch_7 = ng.nodes.new('GeometryNodeSwitch')
    switch_7.input_type = 'INT'
    switch_7.inputs[2].default_value = 1  # True value
    ng.links.new(equal_3.outputs[0], switch_7.inputs[0])
    ng.links.new(group_input.outputs['Reflection'], switch_7.inputs[1])  # False

    # ─── combine_xyz_15: (1, switch_7, 1.1) ───
    combine_xyz_15 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_15.inputs['X'].default_value = 1.0
    combine_xyz_15.inputs['Z'].default_value = 1.1
    ng.links.new(switch_7.outputs[0], combine_xyz_15.inputs['Y'])

    # ─── multiply_16: multiply_15 * combine_xyz_15 ───
    multiply_16 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_16.operation = 'MULTIPLY'
    ng.links.new(multiply_15.outputs[0], multiply_16.inputs[0])
    ng.links.new(combine_xyz_15.outputs[0], multiply_16.inputs[1])

    # ─── divide_3: sep_xyz_9.Y / ceil ───
    divide_3 = ng.nodes.new('ShaderNodeMath')
    divide_3.operation = 'DIVIDE'
    ng.links.new(sep_xyz_9.outputs['Y'], divide_3.inputs[0])
    ng.links.new(ceil_node.outputs[0], divide_3.inputs[1])

    # ─── combine_xyz_5: (sep_xyz_10.X, divide_3, sep_xyz_10.Z) ───
    combine_xyz_5 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(sep_xyz_10.outputs['X'], combine_xyz_5.inputs['X'])
    ng.links.new(divide_3.outputs[0], combine_xyz_5.inputs['Y'])
    ng.links.new(sep_xyz_10.outputs['Z'], combine_xyz_5.inputs['Z'])

    # ─── multiply_17: combine_xyz_5 * combine_xyz_15 ───
    multiply_17 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_17.operation = 'MULTIPLY'
    ng.links.new(combine_xyz_5.outputs[0], multiply_17.inputs[0])
    ng.links.new(combine_xyz_15.outputs[0], multiply_17.inputs[1])

    # ─── multiply_18: combine_xyz_5 * (1, 1.03, 1) ───
    multiply_18 = ng.nodes.new('ShaderNodeVectorMath')
    multiply_18.operation = 'MULTIPLY'
    multiply_18.inputs[1].default_value = (1.0, 1.03, 1.0)
    ng.links.new(combine_xyz_5.outputs[0], multiply_18.inputs[0])

    # ─── seat_cushion: corner_cube(CenteringLoc=(0,0.5,0), Dims=multiply_18, Verts=2,2,2) ───
    seat_cushion = ng.nodes.new('GeometryNodeGroup')
    seat_cushion.node_tree =corner_cube_ng
    seat_cushion.inputs['CenteringLoc'].default_value = (0.0, 0.5, 0.0)
    seat_cushion.inputs['Vertices X'].default_value = 2
    seat_cushion.inputs['Vertices Y'].default_value = 2
    seat_cushion.inputs['Vertices Z'].default_value = 2
    ng.links.new(multiply_18.outputs[0], seat_cushion.inputs['Dimensions'])

    # ─── (SKIP tagging) ───
    # Original code tags support surface, we skip it for standalone.
    # We still need to add the TAG_support and TAG_cushion store operations
    # since they may affect geometry flow.

    # ─── index ───
    index_node = ng.nodes.new('GeometryNodeInputIndex')

    # ─── equal_4: index == 1 ───
    equal_4 = ng.nodes.new('FunctionNodeCompare')
    equal_4.data_type = 'INT'
    equal_4.operation = 'EQUAL'
    equal_4.inputs[3].default_value = 1
    ng.links.new(index_node.outputs[0], equal_4.inputs[2])

    # ─── store TAG_support (BOOLEAN, FACE domain) ───
    store_tag_support = ng.nodes.new('GeometryNodeStoreNamedAttribute')
    store_tag_support.data_type = 'BOOLEAN'
    store_tag_support.domain = 'FACE'
    store_tag_support.inputs['Name'].default_value = "TAG_support"
    # In Blender 5.0, for BOOLEAN StoreNamedAttribute, the Value socket is named "Value"
    store_tag_support.inputs['Value'].default_value = True
    ng.links.new(seat_cushion.outputs[0], store_tag_support.inputs['Geometry'])
    ng.links.new(equal_4.outputs[0], store_tag_support.inputs['Selection'])

    # ─── value node = 1.0 ───
    value_node = ng.nodes.new('ShaderNodeValue')
    value_node.outputs[0].default_value = 1.0

    # ─── store TAG_cushion (BOOLEAN, FACE domain) ───
    store_tag_cushion = ng.nodes.new('GeometryNodeStoreNamedAttribute')
    store_tag_cushion.data_type = 'BOOLEAN'
    store_tag_cushion.domain = 'FACE'
    store_tag_cushion.inputs['Name'].default_value = "TAG_cushion"
    store_tag_cushion.inputs['Value'].default_value = True
    ng.links.new(store_tag_support.outputs[0], store_tag_cushion.inputs['Geometry'])
    ng.links.new(value_node.outputs[0], store_tag_cushion.inputs['Selection'])

    # ─── combine_xyz_6: (Seat Margin, Seat Margin, 1) ───
    combine_xyz_6 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_6.inputs['Z'].default_value = 1.0
    ng.links.new(group_input.outputs['Seat Margin'], combine_xyz_6.inputs['X'])
    ng.links.new(group_input.outputs['Seat Margin'], combine_xyz_6.inputs['Y'])

    # ─── transform_geometry_3: store_tag_cushion, Scale=combine_xyz_6 ───
    transform_3 = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(store_tag_cushion.outputs[0], transform_3.inputs['Geometry'])
    ng.links.new(combine_xyz_6.outputs[0], transform_3.inputs['Scale'])

    # ─── combine_xyz_11: (Scaling footrest, 1, 1.1) ───
    combine_xyz_11 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_11.inputs['Y'].default_value = 1.0
    combine_xyz_11.inputs['Z'].default_value = 1.1
    ng.links.new(group_input.outputs['Scaling footrest'], combine_xyz_11.inputs['X'])

    # ─── transform_geometry_7: transform_3, Scale=combine_xyz_11 ───
    transform_7 = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(transform_3.outputs[0], transform_7.inputs['Geometry'])
    ng.links.new(combine_xyz_11.outputs[0], transform_7.inputs['Scale'])

    # ─── nodegroup_array_fill_line_002: array_fill_line(
    #      LineStart=multiply_14, LineEnd=multiply_16, InstanceDims=multiply_17,
    #      Count=Count, Instance=transform_7) ───
    afl_002 = ng.nodes.new('GeometryNodeGroup')
    afl_002.node_tree =array_fill_line_ng
    ng.links.new(multiply_14.outputs[0], afl_002.inputs['Line Start'])
    ng.links.new(multiply_16.outputs[0], afl_002.inputs['Line End'])
    ng.links.new(multiply_17.outputs[0], afl_002.inputs['Instance Dimensions'])
    ng.links.new(group_input.outputs['Count'], afl_002.inputs['Count'])
    ng.links.new(transform_7.outputs[0], afl_002.inputs['Instance'])

    # ─── separate_xyz_17: multiply_16 ───
    sep_xyz_17 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(multiply_16.outputs[0], sep_xyz_17.inputs[0])

    # ─── combine_xyz_21: (0, 0, sep_xyz_17.Z) ───
    combine_xyz_21 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(sep_xyz_17.outputs['Z'], combine_xyz_21.inputs['Z'])

    # ─── combine_xyz_20: (1, ceil, 1) ───
    combine_xyz_20 = ng.nodes.new('ShaderNodeCombineXYZ')
    combine_xyz_20.inputs['X'].default_value = 1.0
    combine_xyz_20.inputs['Z'].default_value = 1.0
    ng.links.new(ceil_node.outputs[0], combine_xyz_20.inputs['Y'])

    # ─── transform_geometry_13: transform_7, Scale=combine_xyz_20 ───
    transform_13 = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(transform_7.outputs[0], transform_13.inputs['Geometry'])
    ng.links.new(combine_xyz_20.outputs[0], transform_13.inputs['Scale'])

    # ─── nodegroup_array_fill_line_002_1: array_fill_line(
    #      LineEnd=combine_xyz_21, Count=1, Instance=transform_13) ───
    afl_002_1 = ng.nodes.new('GeometryNodeGroup')
    afl_002_1.node_tree =array_fill_line_ng
    afl_002_1.inputs['Count'].default_value = 1
    ng.links.new(combine_xyz_21.outputs[0], afl_002_1.inputs['Line End'])
    ng.links.new(transform_13.outputs[0], afl_002_1.inputs['Instance'])

    # ─── switch_9: Switch(equal_2, False=afl_002, True=afl_002_1) ───
    switch_9 = ng.nodes.new('GeometryNodeSwitch')
    ng.links.new(equal_2.outputs[0], switch_9.inputs[0])
    ng.links.new(afl_002.outputs[0], switch_9.inputs[1])  # False
    ng.links.new(afl_002_1.outputs[0], switch_9.inputs[2])  # True

    # ─── switch_3: Switch(Footrest, False=None, True=switch_9) ───
    switch_3 = ng.nodes.new('GeometryNodeSwitch')
    ng.links.new(group_input.outputs['Footrest'], switch_3.inputs[0])
    ng.links.new(switch_9.outputs[0], switch_3.inputs[2])  # True

    # ─── nodegroup_array_fill_line_002_2: array_fill_line(
    #      LineStart=multiply_14, LineEnd=multiply_15, InstanceDims=combine_xyz_5,
    #      Count=ceil, Instance=transform_3) ───
    afl_002_2 = ng.nodes.new('GeometryNodeGroup')
    afl_002_2.node_tree =array_fill_line_ng
    ng.links.new(multiply_14.outputs[0], afl_002_2.inputs['Line Start'])
    ng.links.new(multiply_15.outputs[0], afl_002_2.inputs['Line End'])
    ng.links.new(combine_xyz_5.outputs[0], afl_002_2.inputs['Instance Dimensions'])
    ng.links.new(ceil_node.outputs[0], afl_002_2.inputs['Count'])
    ng.links.new(transform_3.outputs[0], afl_002_2.inputs['Instance'])

    # ─── join_geometry_9: [switch_3, afl_002_2] ───
    join_9 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(switch_3.outputs[0], join_9.inputs[0])
    ng.links.new(afl_002_2.outputs[0], join_9.inputs[0])

    # ─── subdivide_mesh: join_9, Level=2 ───
    subdivide_mesh = ng.nodes.new('GeometryNodeSubdivideMesh')
    subdivide_mesh.inputs['Level'].default_value = 2
    ng.links.new(join_9.outputs[0], subdivide_mesh.inputs[0])

    # ─── separate_xyz_11: Seat Dimensions ───
    sep_xyz_11 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(group_input.outputs['Seat Dimensions'], sep_xyz_11.inputs[0])

    # ─── combine_xyz_7: (Backrest Width, 0, sep_xyz_11.Z) ───
    combine_xyz_7 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(group_input.outputs['Backrest Width'], combine_xyz_7.inputs['X'])
    ng.links.new(sep_xyz_11.outputs['Z'], combine_xyz_7.inputs['Z'])

    # ─── add_1: multiply_14 + combine_xyz_7 ───
    add_1 = ng.nodes.new('ShaderNodeVectorMath')
    add_1.operation = 'ADD'
    ng.links.new(multiply_14.outputs[0], add_1.inputs[0])
    ng.links.new(combine_xyz_7.outputs[0], add_1.inputs[1])

    # ─── add_2: multiply_15 + combine_xyz_7 ───
    add_2 = ng.nodes.new('ShaderNodeVectorMath')
    add_2.operation = 'ADD'
    ng.links.new(multiply_15.outputs[0], add_2.inputs[0])
    ng.links.new(combine_xyz_7.outputs[0], add_2.inputs[1])

    # ─── separate_xyz_12: Dimensions ───
    sep_xyz_12 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(group_input.outputs['Dimensions'], sep_xyz_12.inputs[0])

    # ─── subtract_6: sep_xyz_12.Z - sep_xyz_11.Z ───
    subtract_6 = ng.nodes.new('ShaderNodeMath')
    subtract_6.operation = 'SUBTRACT'
    ng.links.new(sep_xyz_12.outputs['Z'], subtract_6.inputs[0])
    ng.links.new(sep_xyz_11.outputs['Z'], subtract_6.inputs[1])

    # ─── subtract_7: subtract_6 - Baseboard Height ───
    subtract_7 = ng.nodes.new('ShaderNodeMath')
    subtract_7.operation = 'SUBTRACT'
    ng.links.new(subtract_6.outputs[0], subtract_7.inputs[0])
    ng.links.new(group_input.outputs['Baseboard Height'], subtract_7.inputs[1])

    # ─── combine_xyz_8: (subtract_7, divide_3, Backrest Width) ───
    combine_xyz_8 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(subtract_7.outputs[0], combine_xyz_8.inputs['X'])
    ng.links.new(divide_3.outputs[0], combine_xyz_8.inputs['Y'])
    ng.links.new(group_input.outputs['Backrest Width'], combine_xyz_8.inputs['Z'])

    # ─── seat_cushion_1: corner_cube(CenteringLoc=(0.1,0.5,1), Dims=combine_xyz_8, Verts=2,2,2) ───
    seat_cushion_1 = ng.nodes.new('GeometryNodeGroup')
    seat_cushion_1.node_tree =corner_cube_ng
    seat_cushion_1.inputs['CenteringLoc'].default_value = (0.1, 0.5, 1.0)
    seat_cushion_1.inputs['Vertices X'].default_value = 2
    seat_cushion_1.inputs['Vertices Y'].default_value = 2
    seat_cushion_1.inputs['Vertices Z'].default_value = 2
    ng.links.new(combine_xyz_8.outputs[0], seat_cushion_1.inputs['Dimensions'])

    # ─── extrude_mesh: seat_cushion_1, OffsetScale=0.03 ───
    extrude_mesh = ng.nodes.new('GeometryNodeExtrudeMesh')
    extrude_mesh.inputs['Offset Scale'].default_value = 0.03
    ng.links.new(seat_cushion_1.outputs[0], extrude_mesh.inputs['Mesh'])

    # ─── scale_elements: Selection=extrude_mesh.Top, Scale=0.6 ───
    scale_elements = ng.nodes.new('GeometryNodeScaleElements')
    scale_elements.inputs['Scale'].default_value = 0.6
    ng.links.new(extrude_mesh.outputs['Mesh'], scale_elements.inputs['Geometry'])
    ng.links.new(extrude_mesh.outputs['Top'], scale_elements.inputs['Selection'])

    # ─── subdivision_surface_1: scale_elements ───
    subdiv_surf_1 = ng.nodes.new('GeometryNodeSubdivisionSurface')
    ng.links.new(scale_elements.outputs[0], subdiv_surf_1.inputs['Mesh'])

    # ─── random_value: FLOAT_VECTOR ───
    random_value = ng.nodes.new('FunctionNodeRandomValue')
    random_value.data_type = 'FLOAT_VECTOR'

    # ─── store UVMap on backrest cushion ───
    store_uv_back = ng.nodes.new('GeometryNodeStoreNamedAttribute')
    store_uv_back.data_type = 'FLOAT_VECTOR'
    store_uv_back.domain = 'CORNER'
    store_uv_back.inputs['Name'].default_value = "UVMap"
    ng.links.new(subdiv_surf_1.outputs[0], store_uv_back.inputs['Geometry'])
    ng.links.new(random_value.outputs[0], store_uv_back.inputs['Value'])

    # ─── multiply_19: Backrest Width * -1 ───
    multiply_19 = ng.nodes.new('ShaderNodeMath')
    multiply_19.operation = 'MULTIPLY'
    multiply_19.inputs[1].default_value = -1.0
    ng.links.new(group_input.outputs['Backrest Width'], multiply_19.inputs[0])

    # ─── separate_xyz_13: Back Dimensions ───
    sep_xyz_13 = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(group_input.outputs['Back Dimensions'], sep_xyz_13.inputs[0])

    # ─── add_3: sep_xyz_13.X + 0.1 ───
    add_3 = ng.nodes.new('ShaderNodeMath')
    add_3.operation = 'ADD'
    add_3.inputs[1].default_value = 0.1
    ng.links.new(sep_xyz_13.outputs['X'], add_3.inputs[0])

    # ─── add_4: multiply_19 + add_3 ───
    add_4 = ng.nodes.new('ShaderNodeMath')
    add_4.operation = 'ADD'
    ng.links.new(multiply_19.outputs[0], add_4.inputs[0])
    ng.links.new(add_3.outputs[0], add_4.inputs[1])

    # ─── combine_xyz_9: (add_4, 0, 0) ───
    combine_xyz_9 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(add_4.outputs[0], combine_xyz_9.inputs['X'])

    # ─── add_5: Backrest Angle + (-pi/2) ───
    add_5 = ng.nodes.new('ShaderNodeMath')
    add_5.operation = 'ADD'
    add_5.inputs[1].default_value = -1.5708
    ng.links.new(group_input.outputs['Backrest Angle'], add_5.inputs[0])

    # ─── combine_xyz_10: (0, add_5, 0) ───
    combine_xyz_10 = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(add_5.outputs[0], combine_xyz_10.inputs['Y'])

    # ─── transform_geometry_4: store_uv_back, Translation=combine_xyz_9, Rotation=combine_xyz_10, Scale=combine_xyz_6 ───
    transform_4 = ng.nodes.new('GeometryNodeTransform')
    ng.links.new(store_uv_back.outputs[0], transform_4.inputs['Geometry'])
    ng.links.new(combine_xyz_9.outputs[0], transform_4.inputs['Translation'])
    ng.links.new(combine_xyz_10.outputs[0], transform_4.inputs['Rotation'])
    ng.links.new(combine_xyz_6.outputs[0], transform_4.inputs['Scale'])

    # ─── nodegroup_array_fill_line_003: array_fill_line(
    #      LineStart=add_1, LineEnd=add_2, InstanceDims=combine_xyz_5,
    #      Count=ceil, Instance=transform_4) ───
    afl_003 = ng.nodes.new('GeometryNodeGroup')
    afl_003.node_tree =array_fill_line_ng
    ng.links.new(add_1.outputs[0], afl_003.inputs['Line Start'])
    ng.links.new(add_2.outputs[0], afl_003.inputs['Line End'])
    ng.links.new(combine_xyz_5.outputs[0], afl_003.inputs['Instance Dimensions'])
    ng.links.new(ceil_node.outputs[0], afl_003.inputs['Count'])
    ng.links.new(transform_4.outputs[0], afl_003.inputs['Instance'])

    # ─── join_geometry_6: [subdivide_mesh, afl_003] ───
    join_6 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(subdivide_mesh.outputs[0], join_6.inputs[0])
    ng.links.new(afl_003.outputs[0], join_6.inputs[0])

    # ─── join_geometry_7: [join_5, realize, join_6] ───
    join_7 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(join_5.outputs[0], join_7.inputs[0])
    ng.links.new(realize.outputs[0], join_7.inputs[0])
    ng.links.new(join_6.outputs[0], join_7.inputs[0])

    # ─── subdivide_mesh_1: join_5, Level=2 ───
    subdivide_mesh_1 = ng.nodes.new('GeometryNodeSubdivideMesh')
    subdivide_mesh_1.inputs['Level'].default_value = 2
    ng.links.new(join_5.outputs[0], subdivide_mesh_1.inputs[0])

    # ─── join_geometry_8: [subdivide_mesh_1, realize, join_6] ───
    join_8 = ng.nodes.new('GeometryNodeJoinGeometry')
    ng.links.new(subdivide_mesh_1.outputs[0], join_8.inputs[0])
    ng.links.new(realize.outputs[0], join_8.inputs[0])
    ng.links.new(join_6.outputs[0], join_8.inputs[0])

    # ─── subdivision_surface_2: join_8, Level=1 ───
    subdiv_surf_2 = ng.nodes.new('GeometryNodeSubdivisionSurface')
    subdiv_surf_2.inputs['Level'].default_value = 1
    ng.links.new(join_8.outputs[0], subdiv_surf_2.inputs['Mesh'])

    # ─── switch_1: Switch(True, False=join_7, True=subdiv_surf_2) ─── (this is the hardcoded True switch)
    # Original: switch_1 = Switch(0: True, 1: join_7, 2: subdiv_surf_2)
    # But this switch is immediately followed by switch which overrides it.
    # The group_output uses switch_1, but looking at original code line 1383:
    #   group_output input_kwargs={"Geometry": switch_1, "BoundingBox": reroute_8}
    # Wait, but switch (line 1358) also exists. Let me re-read...
    # Line 1354-1357: switch_1 uses 0: True (hardcoded)
    # Line 1358-1365: switch uses 0: Subdivide input
    # Line 1383: group_output uses switch_1 (NOT switch!)
    # So the actual output is switch_1 which always selects subdiv_surf_2 (True branch)
    switch_1 = ng.nodes.new('GeometryNodeSwitch')
    switch_1.inputs[0].default_value = True  # hardcoded True
    ng.links.new(join_7.outputs[0], switch_1.inputs[1])  # False
    ng.links.new(subdiv_surf_2.outputs[0], switch_1.inputs[2])  # True

    # ─── (switch is created but not used in group_output, skip it) ───

    # ─── bounding_box: corner_cube(CenteringLoc=(0,0.5,-1), Dims=Dimensions, Verts=2,2,2) ───
    bounding_box = ng.nodes.new('GeometryNodeGroup')
    bounding_box.node_tree =corner_cube_ng
    bounding_box.inputs['CenteringLoc'].default_value = (0.0, 0.5, -1.0)
    bounding_box.inputs['Vertices X'].default_value = 2
    bounding_box.inputs['Vertices Y'].default_value = 2
    bounding_box.inputs['Vertices Z'].default_value = 2
    ng.links.new(group_input.outputs['Dimensions'], bounding_box.inputs['Dimensions'])

    # ─── group_output ───
    ng.links.new(switch_1.outputs[0], group_output.inputs['Geometry'])
    ng.links.new(bounding_box.outputs[0], group_output.inputs['BoundingBox'])

    return ng

# ═══════════════════════════════════════════════════════════════
#  Parameter distribution
# ═══════════════════════════════════════════════════════════════
def sofa_parameter_distribution(dimensions=None):
    from numpy.random import uniform
    if dimensions is None:
        dimensions = (
            uniform(0.95, 1.1),
            clip_gaussian(1.75, 0.75, 0.9, 3),
            uniform(0.69, 0.97),
        )
    return {
        "Dimensions": dimensions,
        "Arm Dimensions": (
            uniform(1, 1),
            uniform(0.06, 0.15),
            uniform(0.5, 0.75),
        ),
        "Back Dimensions": (uniform(0.15, 0.25), 0.0, uniform(0.5, 0.75)),
        "Seat Dimensions": (dimensions[0], uniform(0.7, 1), uniform(0.15, 0.3)),
        "Foot Dimensions": (uniform(0.07, 0.25), 0.06, 0.06),
        "Baseboard Height": uniform(0.05, 0.09),
        "Backrest Width": uniform(0.1, 0.2),
        "Seat Margin": uniform(0.97, 1),
        "Backrest Angle": uniform(-0.15, -0.5),
        "Arm Type": int(np.random.choice(
            [ARM_TYPE_SQUARE, ARM_TYPE_ROUND, ARM_TYPE_ANGULAR], p=[0.4, 0.2, 0.4]
        )),
        "arm_width": uniform(0.6, 0.9),
        "Arm_height": uniform(0.7, 1.0),
        "arms_angle": uniform(0.0, 1.08),
        "Footrest": True if uniform() > 0.5 and dimensions[1] > 2 else False,
        "Count": 1 if uniform() > 0.2 else 4,
        "Scaling footrest": uniform(1.3, 1.6),
        "Reflection": 1 if uniform() > 0.5 else -1,
        "leg_type": True,  # Block legs create better baseboard junction than cones
        "leg_dimensions": uniform(0.4, 0.9),
        "leg_z": uniform(1.1, 2.5),
        "leg_faces": int(uniform(4, 25)),
    }

# ═══════════════════════════════════════════════════════════════
#  Main: build the sofa
# ═══════════════════════════════════════════════════════════════
def main(params, sofa_fabric_mat):
    # Create node groups
    corner_cube_ng = create_corner_cube()
    array_fill_line_ng = create_array_fill_line()
    sofa_geom_ng = create_sofa_geometry(corner_cube_ng, array_fill_line_ng)

    # Create spawn vert
    mesh = bpy.data.meshes.new('SofaFactory_mesh')
    mesh.from_pydata([(0, 0, 0)], [], [])
    mesh.update()
    obj = bpy.data.objects.new('SofaFactory', mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    # Add GeoNodes modifier
    mod = obj.modifiers.new("SofaGeometry", 'NODES')
    mod.node_group = sofa_geom_ng

    # Set modifier inputs from params
    for key, val in params.items():
        # Find the input socket identifier in the node group interface
        sock_id = None
        for item in sofa_geom_ng.interface.items_tree:
            if item.name == key and item.in_out == 'INPUT':
                sock_id = item.identifier
                break
        if sock_id is None:
            continue

        # Set the value on the modifier
        mod[sock_id] = val

    # Apply the GeoNodes modifier
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Weld close vertices at component junctions, then SubdivSurf
    mod_weld = obj.modifiers.new("Weld", 'WELD')
    mod_weld.merge_threshold = 0.003
    bpy.ops.object.modifier_apply(modifier=mod_weld.name)

    # SUBSURF level=1
    mod_sub = obj.modifiers.new("Subdivision", 'SUBSURF')
    mod_sub.levels = 1
    mod_sub.render_levels = 1
    bpy.ops.object.modifier_apply(modifier=mod_sub.name)

    # Shade smooth
    bpy.ops.object.shade_smooth()

    #    surface.assign_material(obj, self.sofa_fabric) in create_placeholder) ──
    obj.data.materials.append(sofa_fabric_mat)
    for i in range(len(obj.data.materials)):
        if obj.data.materials[i] is None:
            obj.data.materials[i] = sofa_fabric_mat

    # Report
    n_verts = len(obj.data.vertices)
    n_faces = len(obj.data.polygons)
    print(f"[SofaFactory] SEED={SEED}  material={sofa_fabric_mat.name}  "
          f"slots={len(obj.data.materials)}  verts={n_verts}  faces={n_faces}")
    return obj

# ═══════════════════════════════════════════════════════════════════════════
#  Phase 1 — material sampling on raw SEED
#
#  Numpy random consumption order inside SofaFactory.__init__:
#     1. sofa_parameter_distribution()   -- consumes ~25 uniforms
#     2. weighted_sample(material_assignments.fabrics)
#     3. fabric shader constructor       -- constructor-specific uniforms
# ═══════════════════════════════════════════════════════════════════════════
SEED = int(os.environ.get('SEED', 0))
seed_all(SEED)

SOFA_PARAMS = sofa_parameter_distribution()

# 2. Sample fabric shader from the same weighted registry
MAT_SOFA_FABRIC = get_fabric_material(name="SofaFabric")

# SofaFactory does NOT use wear_tear — create_placeholder only calls
# surface.assign_material; no scratch/edge_wear.apply() is invoked.

main(SOFA_PARAMS, MAT_SOFA_FABRIC)

