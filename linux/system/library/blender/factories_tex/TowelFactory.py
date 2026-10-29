# [FL_INDEX: keywords="blender_factory, procedural_3d, TowelFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TowelFactory | Category: factories_tex
# Prompt: A 3D model of a folded bath towel rendered from a three-quarter angle. The towel is neatly folded into a thick rectangular stack with many visible layered folds creating a heavily textured, fluffy surface. The towel is light sky blue with shades of lighter blue, and the folded edge detail is visible on the sides showing thin green/teal stripe accents. The surface has a rich, dense terry cloth-like texture.

"""
TowelFactory — standalone Blender script (geometry + fabric materials).

Source geometry : objects_blender/clothes/TowelFactory.py
Registry key   : material_assignments.towel
Wear/tear      : none
"""
import os, math, bpy, bmesh, random, colorsys
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
    mat.use_nodes = True; mat.node_tree.nodes.clear()
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
        if nm in bsdf.inputs: bsdf.inputs[nm].default_value = v
        elif k == "Specular" and "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = v
    return bsdf

# ═══════════════════════════════════════════════════════════════════════════
#  Fabric shader constructors
# ═══════════════════════════════════════════════════════════════════════════

def make_coarse_knit_fabric(name="CoarseKnitFabric"):
    pm = float(np.random.choice([np.random.uniform(0.0, 0.1), np.random.uniform(0.1, 0.9)]))
    pd = float(np.random.choice([np.random.uniform(0.1, 1.0), np.random.uniform(1.0, 10.0)]))
    _h, _s, _v = fabric_hsv()
    color = np.array(colorsys.hsv_to_rgb(_h, _s, _v))
    bk = float(np.random.choice([np.random.uniform(0.0, 0.05), np.random.uniform(0.05, 0.95), np.random.uniform(0.95, 1.0)]))
    kr = float(np.random.uniform(0.5, 0.6)); br = float(np.random.uniform(20.0, 30.0))
    cres = float(np.random.uniform(50.0, 80.0))
    sm = float(np.random.choice([np.random.uniform(0.0, 0.2), np.random.uniform(0.2, 0.5)]))
    csf = float(np.random.uniform(0.1, 0.9))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    m1 = nt.nodes.new("ShaderNodeMapping"); ln(tc.outputs["Object"], m1.inputs["Vector"]); m1.inputs["Scale"].default_value = (3.2, 1.0, 1.0)
    bt = nt.nodes.new("ShaderNodeTexBrick"); ln(m1.outputs["Vector"], bt.inputs["Vector"]); bt.inputs["Scale"].default_value = br
    c1 = nt.nodes.new("ShaderNodeValToRGB"); ln(bt.outputs["Color"], c1.inputs["Fac"])
    c1.color_ramp.elements[0].position = 0.0; c1.color_ramp.elements[0].color = (1, 1, 1, 1)
    c1.color_ramp.elements[1].position = 1.0; c1.color_ramp.elements[1].color = (0, 0, 0, 1)
    m2 = nt.nodes.new("ShaderNodeMapping"); ln(tc.outputs["Object"], m2.inputs["Vector"])
    m2.inputs["Rotation"].default_value = (0, 0, 0.7854); m2.inputs["Scale"].default_value = (238.8, 1.0, 35.6)
    v1 = nt.nodes.new("ShaderNodeTexVoronoi"); v1.feature = "F2"; ln(m2.outputs["Vector"], v1.inputs["Vector"])
    v1.inputs["Scale"].default_value = pd; v1.inputs["Randomness"].default_value = 0.0
    c2 = nt.nodes.new("ShaderNodeValToRGB"); ln(v1.outputs["Distance"], c2.inputs["Fac"])
    c2.color_ramp.elements[0].position = 0.1018; c2.color_ramp.elements[0].color = (1, 1, 1, 1)
    c2.color_ramp.elements[1].position = 1.0; c2.color_ramp.elements[1].color = (0, 0, 0, 1)
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.clamp_result = True; mx.inputs[0].default_value = pm
    ln(c1.outputs["Color"], mx.inputs[6]); ln(c2.outputs["Color"], mx.inputs[7])
    b1 = _principled(nt, Specular=0.6309, Roughness=0.9945); ln(mx.outputs[2], b1.inputs["Base Color"])
    cb = nt.nodes.new("ShaderNodeCombineColor")
    cb.inputs["Red"].default_value = float(color[0]); cb.inputs["Green"].default_value = float(color[1]); cb.inputs["Blue"].default_value = float(color[2])
    b2 = _principled(nt, Specular=0.6309, Roughness=0.9945); ln(cb.outputs["Color"], b2.inputs["Base Color"])
    ms = nt.nodes.new("ShaderNodeMixShader"); ms.inputs["Fac"].default_value = csf
    ln(b1.outputs["BSDF"], ms.inputs[1]); ln(b2.outputs["BSDF"], ms.inputs[2])
    iv = nt.nodes.new("ShaderNodeMath"); iv.operation = "SUBTRACT"; iv.use_clamp = True; iv.inputs[0].default_value = 1.0; ln(c1.outputs["Color"], iv.inputs[1])
    s0 = nt.nodes.new("ShaderNodeMath"); s0.operation = "MULTIPLY"; s0.use_clamp = True; ln(iv.outputs[0], s0.inputs[0]); s0.inputs[1].default_value = bk
    m3 = nt.nodes.new("ShaderNodeMapping"); ln(tc.outputs["Object"], m3.inputs["Vector"])
    m3.inputs["Rotation"].default_value = (0, 0, 0.6196); m3.inputs["Scale"].default_value = (217.5, 176.2, 42.0)
    v2 = nt.nodes.new("ShaderNodeTexVoronoi"); v2.feature = "F2"; ln(m3.outputs["Vector"], v2.inputs["Vector"])
    v2.inputs["Scale"].default_value = kr; v2.inputs["Randomness"].default_value = 0.0
    m4 = nt.nodes.new("ShaderNodeMapping"); ln(tc.outputs["Object"], m4.inputs["Vector"])
    ns = nt.nodes.new("ShaderNodeTexNoise"); ln(m4.outputs["Vector"], ns.inputs["Vector"]); ns.inputs["Scale"].default_value = cres
    an = nt.nodes.new("ShaderNodeMath"); an.use_clamp = True; ln(_fac(ns), an.inputs[0]); an.inputs[1].default_value = sm
    mn = nt.nodes.new("ShaderNodeMath"); mn.operation = "MULTIPLY"; mn.use_clamp = True
    ln(v2.outputs["Distance"], mn.inputs[0]); ln(an.outputs[0], mn.inputs[1])
    sn = nt.nodes.new("ShaderNodeMath"); sn.operation = "SUBTRACT"; sn.inputs[0].default_value = 1.0; sn.inputs[1].default_value = bk
    s1 = nt.nodes.new("ShaderNodeMath"); s1.operation = "MULTIPLY"; ln(mn.outputs[0], s1.inputs[0]); ln(sn.outputs[0], s1.inputs[1])
    a1 = nt.nodes.new("ShaderNodeMath"); ln(s0.outputs[0], a1.inputs[0]); ln(s1.outputs[0], a1.inputs[1])
    dp = nt.nodes.new("ShaderNodeDisplacement"); ln(a1.outputs[0], dp.inputs["Height"])
    dp.inputs["Midlevel"].default_value = 0.4; dp.inputs["Scale"].default_value = 0.01
    _connect_out(nt, ms, dp); return mat

def make_fine_knit_fabric(name="FineKnitFabric"):
    _h, _s, _v = fabric_hsv()
    color = np.array(colorsys.hsv_to_rgb(_h, _s, _v))
    ro = float(np.random.uniform(0, 1.0))
    tdx = float(np.random.uniform(100, 300)); rdy = float(np.random.uniform(0.75, 1.33))
    ds = float(np.random.uniform(0.001, 0.005))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    cb = nt.nodes.new("ShaderNodeCombineColor")
    cb.inputs["Red"].default_value = float(color[0]); cb.inputs["Green"].default_value = float(color[1]); cb.inputs["Blue"].default_value = float(color[2])
    b1 = _principled(nt, Roughness=ro); ln(cb.outputs["Color"], b1.inputs["Base Color"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ml = nt.nodes.new("ShaderNodeMath"); ml.operation = "MULTIPLY"; ml.inputs[0].default_value = tdx; ml.inputs[1].default_value = rdy
    wy = nt.nodes.new("ShaderNodeTexWave"); wy.bands_direction = "Y"; ln(tc.outputs["Object"], wy.inputs["Vector"])
    ln(ml.outputs[0], wy.inputs["Scale"]); wy.inputs["Distortion"].default_value = 5.0; wy.inputs["Detail"].default_value = 6.1
    b2 = _principled(nt, Roughness=ro); ln(wy.outputs["Color"], b2.inputs["Base Color"])
    ms = nt.nodes.new("ShaderNodeMixShader"); ms.inputs["Fac"].default_value = 0.1333
    ln(b1.outputs["BSDF"], ms.inputs[1]); ln(b2.outputs["BSDF"], ms.inputs[2])
    wx = nt.nodes.new("ShaderNodeTexWave"); ln(tc.outputs["Object"], wx.inputs["Vector"])
    wx.inputs["Scale"].default_value = tdx; wx.inputs["Distortion"].default_value = 3.8; wx.inputs["Detail"].default_value = 6.1
    c1 = nt.nodes.new("ShaderNodeValToRGB"); ln(wx.outputs["Color"], c1.inputs["Fac"])
    c1.color_ramp.elements[0].position = 0.8109; c1.color_ramp.elements[0].color = (0, 0, 0, 1)
    c1.color_ramp.elements[1].position = 1.0; c1.color_ramp.elements[1].color = (1, 1, 1, 1)
    iv = nt.nodes.new("ShaderNodeInvert"); iv.inputs["Fac"].default_value = 0.84; ln(c1.outputs["Color"], iv.inputs["Color"])
    c2 = nt.nodes.new("ShaderNodeValToRGB"); ln(wy.outputs["Color"], c2.inputs["Fac"])
    c2.color_ramp.elements[0].position = 0.0727; c2.color_ramp.elements[0].color = (0, 0, 0, 1)
    c2.color_ramp.elements[1].position = 0.8655; c2.color_ramp.elements[1].color = (1, 1, 1, 1)
    ad = nt.nodes.new("ShaderNodeMath"); ln(iv.outputs["Color"], ad.inputs[0]); ln(c2.outputs["Color"], ad.inputs[1])
    dp = nt.nodes.new("ShaderNodeDisplacement"); ln(ad.outputs[0], dp.inputs["Height"])
    dp.inputs["Midlevel"].default_value = 0.4; dp.inputs["Scale"].default_value = ds
    _connect_out(nt, ms, dp); return mat

def make_leather(name="Leather"):
    sv = float(np.random.uniform(-1000.0, 1000.0)); sc = 1.0
    hsv = leather_hsv(); bc = hsv2rgba(float(hsv[0]), float(hsv[1]), float(hsv[2]))
    rl = float(np.random.uniform(0.3, 0.5)); rh = float(np.random.uniform(0.5, 0.7))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord"); rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = bc
    mul1 = nt.nodes.new("ShaderNodeMath"); mul1.operation = "MULTIPLY"; mul1.inputs[0].default_value = sc; mul1.inputs[1].default_value = 10.0
    ns = nt.nodes.new("ShaderNodeTexNoise"); ns.noise_dimensions = "4D"; ln(tc.outputs["Object"], ns.inputs["Vector"])
    ns.inputs["W"].default_value = sv; ln(mul1.outputs[0], ns.inputs["Scale"])
    ns.inputs["Detail"].default_value = 15.0; ns.inputs["Distortion"].default_value = 0.2
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(ns), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.2841; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.9455; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    mll = nt.nodes.new("ShaderNodeMix"); mll.data_type = "RGBA"; mll.blend_type = "LINEAR_LIGHT"; mll.inputs[0].default_value = 0.02
    ln(tc.outputs["Object"], mll.inputs[6]); ln(ns.outputs["Color"], mll.inputs[7])
    mul2 = nt.nodes.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"; mul2.inputs[0].default_value = sc; mul2.inputs[1].default_value = 800.0
    vr = nt.nodes.new("ShaderNodeTexVoronoi"); vr.voronoi_dimensions = "4D"; vr.feature = "DISTANCE_TO_EDGE"
    ln(mll.outputs[2], vr.inputs["Vector"]); vr.inputs["W"].default_value = sv; ln(mul2.outputs[0], vr.inputs["Scale"])
    mul3 = nt.nodes.new("ShaderNodeMath"); mul3.operation = "MULTIPLY"; mul3.use_clamp = True
    ln(vr.outputs["Distance"], mul3.inputs[0]); mul3.inputs[1].default_value = sc
    h1 = nt.nodes.new("ShaderNodeHueSaturation"); h1.inputs["Value"].default_value = 0.6; ln(rgb.outputs[0], h1.inputs["Color"])
    mx1 = nt.nodes.new("ShaderNodeMix"); mx1.data_type = "RGBA"
    ln(mul3.outputs[0], mx1.inputs[0]); ln(rgb.outputs[0], mx1.inputs[6]); ln(h1.outputs["Color"], mx1.inputs[7])
    h2 = nt.nodes.new("ShaderNodeHueSaturation"); h2.inputs["Value"].default_value = 0.4; ln(rgb.outputs[0], h2.inputs["Color"])
    mx2 = nt.nodes.new("ShaderNodeMix"); mx2.data_type = "RGBA"
    ln(cr.outputs["Color"], mx2.inputs[0]); ln(mx1.outputs[2], mx2.inputs[6]); ln(h2.outputs["Color"], mx2.inputs[7])
    mr = nt.nodes.new("ShaderNodeMapRange"); ln(mx2.outputs[2], mr.inputs["Value"]); mr.inputs[3].default_value = rl; mr.inputs[4].default_value = rh
    bsdf = _principled(nt); ln(mx2.outputs[2], bsdf.inputs["Base Color"]); ln(mr.outputs[0], bsdf.inputs["Roughness"])
    d4 = nt.nodes.new("ShaderNodeMath"); d4.operation = "MULTIPLY"; ln(mx1.outputs[2], d4.inputs[0]); d4.inputs[1].default_value = -0.2
    d5 = nt.nodes.new("ShaderNodeMath"); d5.operation = "MULTIPLY"; ln(cr.outputs["Color"], d5.inputs[0]); d5.inputs[1].default_value = 0.05
    da = nt.nodes.new("ShaderNodeMath"); ln(d4.outputs[0], da.inputs[0]); ln(d5.outputs[0], da.inputs[1])
    d6 = nt.nodes.new("ShaderNodeMath"); d6.operation = "MULTIPLY"; ln(da.outputs[0], d6.inputs[0]); d6.inputs[1].default_value = 0.02
    dp = nt.nodes.new("ShaderNodeDisplacement"); ln(d6.outputs[0], dp.inputs["Height"]); dp.inputs["Midlevel"].default_value = 0.0
    _connect_out(nt, bsdf, dp); return mat

def make_sofa_fabric(name="SofaFabric"):
    st = log_uniform(0.005, 0.01); hsv = fabric_hsv(); rgba = hsv2rgba(*hsv)
    br = float(np.random.uniform(-0.15, -0.05))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); ln(tc.outputs["Object"], mp.inputs["Vector"])
    rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = rgba
    bcc = nt.nodes.new("ShaderNodeBrightContrast"); ln(rgb.outputs[0], bcc.inputs["Color"]); bcc.inputs["Bright"].default_value = br
    bk = nt.nodes.new("ShaderNodeTexBrick"); ln(mp.outputs["Vector"], bk.inputs["Vector"])
    ln(rgb.outputs[0], bk.inputs["Color1"]); ln(bcc.outputs["Color"], bk.inputs["Color2"])
    bk.inputs["Scale"].default_value = 276.98; bk.inputs["Mortar Size"].default_value = 0.01
    bk.inputs["Mortar Smooth"].default_value = 1.0; bk.inputs["Bias"].default_value = 0.5
    bk.inputs["Row Height"].default_value = 0.1; bk.offset = 0.5479; bk.squash_frequency = 1
    bsdf = _principled(nt, Roughness=0.8624); ln(bk.outputs["Color"], bsdf.inputs["Base Color"])
    if "Sheen Weight" in bsdf.inputs: bsdf.inputs["Sheen Weight"].default_value = 1.0
    dp = nt.nodes.new("ShaderNodeDisplacement"); ln(_fac(bk), dp.inputs["Height"]); dp.inputs["Scale"].default_value = st
    _connect_out(nt, bsdf, dp); return mat

# ---------- 5. Rug ----------
# Translates rug.py : shader_rug — 3 Voronoi layers + color mixing
# nw.musgrave() → NoiseTexture (Musgrave removed in Blender 5.0)
# nw.build_float_curve() → ColorRamp approximation

def make_rug(name="Rug"):
    strength = log_uniform(0.01, 0.02)
    mix_fac = float(np.random.uniform(0.8, 0.9))
    base_scale = log_uniform(250, 500)

    # Color params — boosted saturation and value for visible fabric color
    base_hue = float(np.random.uniform(0, 1))
    base_value = float(np.random.uniform(0.4, 0.75))
    if np.random.uniform() < 0.2:
        base_sat = log_uniform(0.15, 0.3)
    else:
        base_sat = log_uniform(0.35, 0.7)
    front_color = hsv2rgba(base_hue, base_sat, base_value)
    back_color = hsv2rgba(
        base_hue + float(np.random.uniform(-0.01, 0.01)),
        base_sat * float(np.random.uniform(0.9, 1.1)),
        base_value * float(np.random.uniform(0.9, 1.1)))

    # Float curve params
    curve_mid = float(np.random.uniform(0.3, 0.4))
    musgrave_color_scale = float(np.random.uniform(20, 50))
    musgrave_rough_scale = float(np.random.uniform(20, 50))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    tc = nt.nodes.new("ShaderNodeTexCoord")
    coord = nt.nodes.new("ShaderNodeMapping")
    ln(tc.outputs["Object"], coord.inputs["Vector"])

    # Mix noise into coord for variation
    noise0 = nt.nodes.new("ShaderNodeTexNoise")
    ln(coord.outputs["Vector"], noise0.inputs["Vector"])
    vec_mix = nt.nodes.new("ShaderNodeMix"); vec_mix.data_type = "RGBA"
    vec_mix.inputs[0].default_value = mix_fac
    ln(noise0.outputs["Color"], vec_mix.inputs[6])
    ln(coord.outputs["Vector"], vec_mix.inputs[7])

    # 3 Voronoi layers accumulated via GREATER_THAN + MixRGB
    prev_height = None
    for scale_mul, thresh in zip([1, 0.75, 0.5], [1.0, 0.5, 0.33]):
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        ln(vec_mix.outputs[2], vor.inputs["Vector"])
        vor.inputs["Scale"].default_value = scale_mul * base_scale

        gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"
        ln(vor.outputs[0], gt.inputs[0]); gt.inputs[1].default_value = thresh

        if prev_height is None:
            # First layer: mix voronoi with black
            layer_mix = nt.nodes.new("ShaderNodeMix"); layer_mix.data_type = "RGBA"
            ln(gt.outputs[0], layer_mix.inputs[0])
            ln(vor.outputs[0], layer_mix.inputs[6])
            layer_mix.inputs[7].default_value = (0, 0, 0, 1)
        else:
            layer_mix = nt.nodes.new("ShaderNodeMix"); layer_mix.data_type = "RGBA"
            ln(gt.outputs[0], layer_mix.inputs[0])
            ln(vor.outputs[0], layer_mix.inputs[6])
            ln(prev_height.outputs[2], layer_mix.inputs[7])
        prev_height = layer_mix

    # Displacement from voronoi height
    disp = nt.nodes.new("ShaderNodeDisplacement")
    ln(prev_height.outputs[2], disp.inputs["Height"])
    disp.inputs["Scale"].default_value = strength

    # Musgrave replacement for color curve: NoiseTexture
    noise_color = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Object"], noise_color.inputs["Vector"])
    noise_color.inputs["Scale"].default_value = musgrave_color_scale

    # Float curve approximation via ColorRamp: (0→1, curve_mid→0, 1→0)
    cr_curve = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(noise_color), cr_curve.inputs["Fac"])
    cr_curve.color_ramp.elements[0].position = 0.0
    cr_curve.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr_curve.color_ramp.elements[1].position = curve_mid
    cr_curve.color_ramp.elements[1].color = (0, 0, 0, 1)

    # Color mix: front_color <-> back_color by float curve
    fc_node = nt.nodes.new("ShaderNodeRGB"); fc_node.outputs[0].default_value = front_color
    bc_node = nt.nodes.new("ShaderNodeRGB"); bc_node.outputs[0].default_value = back_color
    color_mix = nt.nodes.new("ShaderNodeMix"); color_mix.data_type = "RGBA"
    ln(cr_curve.outputs["Color"], color_mix.inputs[0])
    ln(fc_node.outputs[0], color_mix.inputs[6])
    ln(bc_node.outputs[0], color_mix.inputs[7])

    # Roughness: ~0.85 constant (simplified from float curve of musgrave)
    noise_rough = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc.outputs["Object"], noise_rough.inputs["Vector"])
    noise_rough.inputs["Scale"].default_value = musgrave_rough_scale
    cr_rough = nt.nodes.new("ShaderNodeValToRGB")
    ln(_fac(noise_rough), cr_rough.inputs["Fac"])
    cr_rough.color_ramp.elements[0].position = 0.5
    cr_rough.color_ramp.elements[0].color = (0.9, 0.9, 0.9, 1)
    cr_rough.color_ramp.elements[1].position = 1.0
    cr_rough.color_ramp.elements[1].color = (0.8, 0.8, 0.8, 1)

    bsdf = _principled(nt)
    ln(color_mix.outputs[2], bsdf.inputs["Base Color"])
    ln(cr_rough.outputs["Color"], bsdf.inputs["Roughness"])

    _connect_out(nt, bsdf, disp)
    return mat

def make_art_fabric(name="ArtFabric"):
    idx = int(np.random.choice(4, p=np.array([1, 1, 2, 1], dtype=float) / 5.0))
    return [make_coarse_knit_fabric, make_fine_knit_fabric, make_leather, make_sofa_fabric][idx](name=name)

def make_art_rug(name="ArtRug"):
    """Simplified ArtRug: uses rug shader as base (no art overlay)."""

    return make_rug(name=name)

# ═══════════════════════════════════════════════════════════════════════════
#  Registry  (material_assignments.towel — fabrics + ArtRug(2.0) + Rug(5.0))
# ═══════════════════════════════════════════════════════════════════════════
TOWEL_REGISTRY = [
    (make_coarse_knit_fabric, 1.0),
    (make_fine_knit_fabric,   1.0),
    (make_leather,            0.3),
    (make_sofa_fabric,        1.0),
    (make_art_rug,            2.0),
    (make_rug,                5.0),
]

def get_material(name=None):
    ctor = weighted_sample(TOWEL_REGISTRY)
    return ctor(name=name or "TowelFabric")

# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)

width           = log_uniform(0.3, 0.6)
length          = width * log_uniform(1, 1.5)
thickness       = log_uniform(0.003, 0.01)
fold_type       = str(np.random.choice(["fold", "roll"], p=np.array([2, 1]) / 3))
folds           = int(np.random.randint(2, 4))
extra_thickness = thickness * float(np.random.uniform(0.2, 0.3))
fold_count      = 15
roll_count      = 256

def compute_roll_total():
    c = length / (thickness + extra_thickness) * (4 * np.pi)
    t = max(c / 2, 1e-6)
    for _ in range(200):
        sq = np.sqrt(1 + t * t)
        f  = t * sq + np.log(t + sq) - c
        fp = 2 * sq
        dt = f / fp; t -= dt; t = max(t, 1e-8)
        if abs(dt) < 1e-12: break
    return t

roll_total = compute_roll_total()

MAT = get_material("TowelFabric")

# create_asset params (after material)
noise_strength = float(np.random.uniform(0.025, 0.05))
noise_scale    = float(np.random.uniform(1.4, 2.8))
bevel_width    = thickness * float(np.random.uniform(0.4, 0.8))

# ═══════════════════════════════════════════════════════════════════════════
#  Geometry  (from objects_blender/clothes/TowelFactory.py)
# ═══════════════════════════════════════════════════════════════════════════

def read_co(o):
    a = np.zeros(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", a); return a.reshape(-1, 3)

def write_co(o, a):
    o.data.vertices.foreach_set("co", a.reshape(-1))

def read_edges(o):
    a = np.zeros(len(o.data.edges) * 2, int)
    o.data.edges.foreach_get("vertices", a); return a.reshape(-1, 2)

def read_edge_dir(o):
    ep = read_co(o)[read_edges(o).reshape(-1)].reshape(-1, 2, 3)
    d = ep[:, 1] - ep[:, 0]
    n = np.linalg.norm(d, axis=-1, keepdims=True)
    return np.where(n > 1e-8, d / n, d)

def obj_center(o):
    co = read_co(o)
    return (np.max(co, 0) + np.min(co, 0)) / 2

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

def subsurf(o):
    mod(o, "SUBSURF", levels=1, render_levels=1)

def subdiv_edge_ring(o, cuts, axis=(0, 0, 1), smooth=0):
    dirs = read_edge_dir(o)
    ax = np.array(axis, float)
    sel = np.abs((dirs * ax).sum(1)) > 1 - 1e-3
    sel_none(); set_active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(o.data); bm.edges.ensure_lookup_table()
    es = [bm.edges[i] for i in np.nonzero(sel)[0]]
    kw = dict(edges=es, cuts=int(cuts))
    if smooth: kw["smooth"] = smooth
    bmesh.ops.subdivide_edgering(bm, **kw)
    bmesh.update_edit_mesh(o.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def do_fold(o):
    x, y, z = read_co(o).T
    offset = 0 if np.max(x) - np.min(x) > np.max(y) - np.min(y) else np.pi / 2
    o.rotation_euler[2] = np.pi * (np.random.uniform() < 0.5) + offset
    apply_tf(o, True)
    c = obj_center(o)
    o.location[0] = -c[0] + float(np.random.uniform(-thickness, thickness))
    o.location[1] = -c[1]; o.location[2] = 0
    apply_tf(o, True)
    n = len(o.data.vertices)
    subdiv_edge_ring(o, fold_count, axis=(1, 0, 0), smooth=2)
    co = read_co(o)
    order = np.where(co[n::fold_count, 0] < co[n + 1::fold_count, 0], 1, -1)
    x_ = np.linspace(-thickness * order, thickness * order, fold_count).T.ravel()
    co[n:, 0] = x_
    x, y, z = co.T
    max_z = np.max(z) + extra_thickness
    theta = x / thickness * np.pi / 2
    x__ = np.where(x < -thickness, x,
          np.where(x > thickness, -x,
                   -thickness + (max_z - z) * np.cos(theta)))
    z_ = np.where(x < -thickness, z,
         np.where(x > thickness, max_z * 2 - z,
                  max_z + (max_z - z) * np.sin(theta)))
    write_co(o, np.stack([x__, y, z_], -1))
    if np.random.uniform() < 0.5:
        o.scale[0] = -1; apply_tf(o)
        sel_none(); set_active(o)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.mode_set(mode='OBJECT')

def pre_roll(o):
    subdiv_edge_ring(o, roll_count, axis=(1, 0, 0))
    x, y, z = read_co(o).T
    i = np.round((x / length + 0.5) * roll_count).astype(int)
    i = np.clip(i, 0, roll_count)
    t = np.linspace(0, roll_total, roll_count + 1)[i]
    sq = np.sqrt(1 + t * t)
    arc = (t * sq + np.log(t + sq)) * (thickness + extra_thickness) / (4 * np.pi)
    write_co(o, np.stack([arc, y, z], -1))
    return i

def do_roll(o, i):
    t = np.linspace(0, roll_total, roll_count + 1)[np.concatenate([i, i])]
    x, y, z = read_co(o).T
    r = ((thickness + extra_thickness) / (2 * np.pi) * t
         + np.where(z > thickness / 2, -thickness / 2, thickness / 2))
    write_co(o, np.stack([r * np.cos(t), y, r * np.sin(t)], -1))

# ── build ──────────────────────────────────────────────────────────────────
bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
obj = bpy.context.active_object
apply_tf(obj, True)

if fold_type == "roll":
    obj.scale = length / 2, width / 2, 1
else:
    obj.scale = width / 2, length / 2, 1
apply_tf(obj, True)

i_roll = None
if fold_type == "roll":
    i_roll = pre_roll(obj)

mod(obj, "SOLIDIFY", thickness=thickness, offset=1)

if fold_type == "roll":
    do_roll(obj, i_roll)
    subdiv_edge_ring(obj, 16, (0, 1, 0))
else:
    for _ in range(folds):
        do_fold(obj)
    subdiv_edge_ring(obj, 16, (1, 0, 0))
    subdiv_edge_ring(obj, 16, (0, 1, 0))

mod(obj, "BEVEL", width=bevel_width, segments=2)

# geo_extension replacement: DISPLACE modifier with cloud texture
tex = bpy.data.textures.new("ext", "CLOUDS")
tex.noise_scale = 1.0 / noise_scale
dm = obj.modifiers.new("DISP", "DISPLACE")
dm.texture = tex; dm.texture_coords = 'OBJECT'; dm.strength = noise_strength
sel_none(); set_active(obj)
bpy.ops.object.modifier_apply(modifier=dm.name); sel_none()

# ── assign material ───────────────────────────────────────────────────────
obj.data.materials.append(MAT)

subsurf(obj)
obj.name = "Towel"
print(f"[TowelFactory] SEED={SEED}  fold={fold_type}  material={MAT.name}  "
      f"slots={len(obj.data.materials)}  verts={len(obj.data.vertices)}")

