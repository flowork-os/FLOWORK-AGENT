# [FL_INDEX: keywords="blender_factory, procedural_3d, ShirtFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: ShirtFactory | Category: factories_tex
# Prompt: A 3D model of a shirt or top garment laid flat on a surface, viewed from above at a slight angle. The garment shows the recognizable shape of a T-shirt or long-sleeve shirt with a body section and two arms extending outward. The fabric is light pink/blush with a smooth flat texture and a dark patterned trim along the edges. The arms appear slightly raised from the body surface.

"""
ShirtFactory — standalone Blender script (geometry + fabric materials).

Source geometry : objects_blender/clothes/ShirtFactory.py
Registry key   : material_assignments.pants  (ShirtFactory uses pants registry, NOT a dedicated shirt one)
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
    bk_tex = nt.nodes.new("ShaderNodeTexBrick"); ln(m1.outputs["Vector"], bk_tex.inputs["Vector"]); bk_tex.inputs["Scale"].default_value = br
    c1 = nt.nodes.new("ShaderNodeValToRGB"); ln(bk_tex.outputs["Color"], c1.inputs["Fac"])
    c1.color_ramp.elements[0].position = 0.0; c1.color_ramp.elements[0].color = (1, 1, 1, 1)
    c1.color_ramp.elements[1].position = 1.0; c1.color_ramp.elements[1].color = (0, 0, 0, 1)
    m2 = nt.nodes.new("ShaderNodeMapping"); ln(tc.outputs["Object"], m2.inputs["Vector"])
    m2.inputs["Rotation"].default_value = (0, 0, 0.7854); m2.inputs["Scale"].default_value = (238.8, 1.0, 35.6)
    v1 = nt.nodes.new("ShaderNodeTexVoronoi"); v1.feature = "F2"
    ln(m2.outputs["Vector"], v1.inputs["Vector"]); v1.inputs["Scale"].default_value = pd; v1.inputs["Randomness"].default_value = 0.0
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
    ml1 = nt.nodes.new("ShaderNodeMath"); ml1.operation = "MULTIPLY"; ml1.inputs[0].default_value = sc; ml1.inputs[1].default_value = 10.0
    ns = nt.nodes.new("ShaderNodeTexNoise"); ns.noise_dimensions = "4D"; ln(tc.outputs["Object"], ns.inputs["Vector"])
    ns.inputs["W"].default_value = sv; ln(ml1.outputs[0], ns.inputs["Scale"])
    ns.inputs["Detail"].default_value = 15.0; ns.inputs["Distortion"].default_value = 0.2
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(ns), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.2841; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.9455; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    mll = nt.nodes.new("ShaderNodeMix"); mll.data_type = "RGBA"; mll.blend_type = "LINEAR_LIGHT"; mll.inputs[0].default_value = 0.02
    ln(tc.outputs["Object"], mll.inputs[6]); ln(ns.outputs["Color"], mll.inputs[7])
    ml2 = nt.nodes.new("ShaderNodeMath"); ml2.operation = "MULTIPLY"; ml2.inputs[0].default_value = sc; ml2.inputs[1].default_value = 800.0
    vr = nt.nodes.new("ShaderNodeTexVoronoi"); vr.voronoi_dimensions = "4D"; vr.feature = "DISTANCE_TO_EDGE"
    ln(mll.outputs[2], vr.inputs["Vector"]); vr.inputs["W"].default_value = sv; ln(ml2.outputs[0], vr.inputs["Scale"])
    ml3 = nt.nodes.new("ShaderNodeMath"); ml3.operation = "MULTIPLY"; ml3.use_clamp = True
    ln(vr.outputs["Distance"], ml3.inputs[0]); ml3.inputs[1].default_value = sc
    h1 = nt.nodes.new("ShaderNodeHueSaturation"); h1.inputs["Value"].default_value = 0.6; ln(rgb.outputs[0], h1.inputs["Color"])
    mx1 = nt.nodes.new("ShaderNodeMix"); mx1.data_type = "RGBA"
    ln(ml3.outputs[0], mx1.inputs[0]); ln(rgb.outputs[0], mx1.inputs[6]); ln(h1.outputs["Color"], mx1.inputs[7])
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
    bc = nt.nodes.new("ShaderNodeBrightContrast"); ln(rgb.outputs[0], bc.inputs["Color"]); bc.inputs["Bright"].default_value = br
    bk = nt.nodes.new("ShaderNodeTexBrick"); ln(mp.outputs["Vector"], bk.inputs["Vector"])
    ln(rgb.outputs[0], bk.inputs["Color1"]); ln(bc.outputs["Color"], bk.inputs["Color2"])
    bk.inputs["Scale"].default_value = 276.98; bk.inputs["Mortar Size"].default_value = 0.01
    bk.inputs["Mortar Smooth"].default_value = 1.0; bk.inputs["Bias"].default_value = 0.5
    bk.inputs["Row Height"].default_value = 0.1; bk.offset = 0.5479; bk.squash_frequency = 1
    bsdf = _principled(nt, Roughness=0.8624); ln(bk.outputs["Color"], bsdf.inputs["Base Color"])
    if "Sheen Weight" in bsdf.inputs: bsdf.inputs["Sheen Weight"].default_value = 1.0
    dp = nt.nodes.new("ShaderNodeDisplacement"); ln(_fac(bk), dp.inputs["Height"]); dp.inputs["Scale"].default_value = st
    _connect_out(nt, bsdf, dp); return mat

def make_art_fabric(name="ArtFabric"):
    idx = int(np.random.choice(4, p=np.array([1, 1, 2, 1], dtype=float) / 5.0))
    return [make_coarse_knit_fabric, make_fine_knit_fabric, make_leather, make_sofa_fabric][idx](name=name)

# ═══════════════════════════════════════════════════════════════════════════
#  Registry  (material_assignments.pants — ArtFabric weight=5.0)
# ═══════════════════════════════════════════════════════════════════════════
PANTS_REGISTRY = [
    (make_coarse_knit_fabric, 1.0),
    (make_fine_knit_fabric,   1.0),
    (make_leather,            0.3),
    (make_sofa_fabric,        1.0),
    (make_art_fabric,         5.0),
]

def get_material(name=None):
    ctor = weighted_sample(PANTS_REGISTRY)
    return ctor(name=name or "ShirtFabric")

# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)

width        = log_uniform(0.45, 0.55)
size         = width + float(np.random.uniform(0.25, 0.3))
size_neck    = float(np.random.uniform(0.1, 0.15)) * size
shirt_type   = str(np.random.choice(["short", "long"]))
if shirt_type == "short":
    sleeve_length = size / 2 + float(np.random.uniform(-0.35, -0.3))
else:
    sleeve_length = size / 2 + float(np.random.uniform(-0.05, 0.0))
sleeve_width = float(np.random.uniform(0.14, 0.18))
sleeve_angle = float(np.random.uniform(np.pi / 6, np.pi / 4))
thickness    = log_uniform(0.02, 0.03)

MAT = get_material("ShirtFabric")

# ═══════════════════════════════════════════════════════════════════════════
#  Geometry  (from objects_blender/clothes/ShirtFactory.py)
# ═══════════════════════════════════════════════════════════════════════════

def read_co(o):
    a = np.zeros(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", a); return a.reshape(-1, 3)

def write_co(o, a):
    o.data.vertices.foreach_set("co", a.reshape(-1))

def read_fc(o):
    a = np.zeros(len(o.data.polygons) * 3)
    o.data.polygons.foreach_get("center", a); return a.reshape(-1, 3)

def read_fn(o):
    a = np.zeros(len(o.data.polygons) * 3)
    o.data.polygons.foreach_get("normal", a); return a.reshape(-1, 3)

def sel_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def set_active(o):
    bpy.context.view_layer.objects.active = o; o.select_set(True)

def mod(o, t, **kw):
    m = o.modifiers.new(t, t)
    for k, v in kw.items(): setattr(m, k, v)
    sel_none(); set_active(o)
    bpy.ops.object.modifier_apply(modifier=m.name); sel_none()

def subsurf(o):
    mod(o, "SUBSURF", levels=1, render_levels=1)

def del_faces(o, mask):
    idxs = np.nonzero(mask)[0]
    sel_none(); set_active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(o.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in idxs], context="FACES_ONLY")
    bmesh.update_edit_mesh(o.data)
    bpy.ops.mesh.select_mode(type="EDGE")
    bpy.ops.mesh.select_loose()
    bpy.ops.mesh.delete(type="EDGE")
    bpy.ops.object.mode_set(mode='OBJECT')

def remesh_fill(o, res=0.02):
    mod(o, "SOLIDIFY", thickness=0.1)
    depth = max(4, int(np.ceil(np.log2((max(o.dimensions) + 0.01) / res))))
    mod(o, "REMESH", mode='SHARP', octree_depth=depth, use_remove_disconnected=False)
    to_del = np.nonzero(read_co(o)[:, 2] < -0.05)[0]
    sel_none(); set_active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(o.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in to_del], context="VERTS")
    bmesh.update_edit_mesh(o.data)
    bpy.ops.object.mode_set(mode='OBJECT')

# ── build ──────────────────────────────────────────────────────────────────
sin_a = np.sin(sleeve_angle); cos_a = np.cos(sleeve_angle)
neck_y_top = size + size_neck * float(np.random.uniform(0.3, 0.7))

x_anchors = (
    0, width / 2, width / 2,
    width / 2 + sleeve_length * sin_a,
    width / 2 + sleeve_length * sin_a + sleeve_width * cos_a,
    width / 2, width / 4, 0,
)
y_anchors = (
    0, 0, size - sleeve_width / sin_a,
    size - sleeve_width / sin_a - sleeve_length * cos_a,
    size - sleeve_width / sin_a - sleeve_length * cos_a + sleeve_width * sin_a,
    size, size + size_neck, neck_y_top,
)

bpy.ops.mesh.primitive_circle_add(vertices=8, location=(0, 0, 0))
obj = bpy.context.active_object
sel_none(); set_active(obj)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.edge_face_add()
bpy.ops.mesh.flip_normals()
bpy.ops.object.mode_set(mode='OBJECT')
write_co(obj, np.stack([x_anchors, y_anchors, np.zeros(8)], -1))

m = obj.modifiers.new("MIR", "MIRROR"); m.use_axis[0] = True
sel_none(); set_active(obj)
bpy.ops.object.modifier_apply(modifier=m.name); sel_none()

remesh_fill(obj, 0.02)
mod(obj, "SOLIDIFY", thickness=thickness)

x = read_fc(obj)[:, 0]
fn = read_fn(obj); x_, y_ = fn[:, 0], fn[:, 1]
del_faces(obj, (y_ < -0.5) | ((y_ > 0.5) & (x_ * x < 0)))

sel_none(); set_active(obj)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.remove_doubles(threshold=1e-3)
bpy.ops.object.mode_set(mode='OBJECT')

# ── assign material ───────────────────────────────────────────────────────
obj.data.materials.append(MAT)

mod(obj, "BEVEL", width=sleeve_width * float(np.random.uniform(0.1, 0.15)))
subsurf(obj)

obj.name = "Shirt"
print(f"[ShirtFactory] SEED={SEED}  type={shirt_type}  material={MAT.name}  "
      f"slots={len(obj.data.materials)}  verts={len(obj.data.vertices)}")

