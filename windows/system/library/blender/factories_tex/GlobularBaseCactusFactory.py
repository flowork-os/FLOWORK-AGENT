# [FL_INDEX: keywords="blender_factory, procedural_3d, GlobularBaseCactusFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: GlobularBaseCactusFactory | Category: factories_tex
# Prompt: A 3D base mesh model of a globular cactus rendered without texture in plain white. The mesh reveals the smooth organic geometry: a roughly ovoid body with pronounced vertical lobed ribs wrapping around its form, giving it a melon-like or twisted ribbed silhouette. No spines or surface detail are present, showing only the clean geometric base form of the globular cactus structure.

FACTORY_SEED = 0

import os
import random
import bpy
import numpy as np
from numpy.random import uniform

# ── FixedSeed ─────────────────────────────────────────────────────────────
class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
    def __enter__(self):
        self.py_state = random.getstate()
        self.np_state = np.random.get_state()
        random.seed(self.seed)
        np.random.seed(self.seed)
    def __exit__(self, *_):
        random.setstate(self.py_state)
        np.random.set_state(self.np_state)

# Inlined material — hand-crafted for cactus category (single shader).

import math, colorsys

def _hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def make_cactus_material(base_hue, name="Cactus"):
    """Raw-bpy translation of CactusFactory.shader_cactus.

    Consumes numpy.random in the same order as the original:
      shift, log_uniform fresnel mul, (bright_color HSV uses no RNG beyond shift),
      fresnel_color hue shift (uniform 0.05..0.1), fresnel_color value (uniform 0.3..0.5),
      musgrave scale log_uniform.
    """
    # Sample colors in the same order as shader_cactus
    shift = float(np.random.uniform(-0.15, 0.15))
    fresnel_mul = float(np.exp(np.random.uniform(math.log(0.6), math.log(1.0))))
    hue_shift_for_fresnel = float(np.random.uniform(0.05, 0.1))
    fresnel_val = float(np.random.uniform(0.3, 0.5))
    musgrave_scale = float(np.exp(np.random.uniform(math.log(10), math.log(50))))

    bright_color  = _hsv2rgba(((base_hue + shift) % 1.0, 1.0, 0.02))
    dark_color    = _hsv2rgba((base_hue, 0.8, 0.01))
    fresnel_color = _hsv2rgba(((base_hue - hue_shift_for_fresnel) % 1.0, 0.9, fresnel_val))
    specular = 0.25

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    # Fresnel -> scalar multiply
    fresnel = nt.nodes.new("ShaderNodeFresnel")
    mul_f = nt.nodes.new("ShaderNodeMath")
    mul_f.operation = "MULTIPLY"
    mul_f.inputs[1].default_value = fresnel_mul
    nt.links.new(fresnel.outputs["Fac"], mul_f.inputs[0])

    # Noise (substitute for Musgrave) -> 4-stop color ramp
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.inputs["Scale"].default_value = musgrave_scale
    if "Detail" in noise1.inputs:
        noise1.inputs["Detail"].default_value = 10.0

    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.0
    cr.color_ramp.elements[0].color = dark_color
    cr.color_ramp.elements[1].position = 0.3
    cr.color_ramp.elements[1].color = dark_color
    e3 = cr.color_ramp.elements.new(0.7); e3.color = bright_color
    e4 = cr.color_ramp.elements.new(1.0); e4.color = bright_color
    fac_out = noise1.outputs.get("Fac") or noise1.outputs[0]
    nt.links.new(fac_out, cr.inputs[0])

    # Mix color with fresnel tint
    mix_rgb = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_rgb, "data_type"):
        mix_rgb.data_type = "RGBA"
    nt.links.new(mul_f.outputs[0], mix_rgb.inputs[0])   # Factor
    nt.links.new(cr.outputs["Color"], mix_rgb.inputs[6])  # A
    mix_rgb.inputs[7].default_value = fresnel_color       # B

    # Second noise -> float curve for roughness
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.inputs["Scale"].default_value = 50.0
    fc = nt.nodes.new("ShaderNodeFloatCurve")
    fc.mapping.use_clip = False
    fc.mapping.curves[0].points[0].location = (0, 0.5)
    fc.mapping.curves[0].points[1].location = (1, 0.8)
    fc.mapping.curves[0].points[0].handle_type = "VECTOR"
    fc.mapping.curves[0].points[1].handle_type = "VECTOR"
    fc.mapping.update()
    fac2_out = noise2.outputs.get("Fac") or noise2.outputs[0]
    nt.links.new(fac2_out, fc.inputs["Value"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular
    nt.links.new(mix_rgb.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return mat
# End of inlined material

def log_uniform(lo, hi):
    return np.exp(np.random.uniform(np.log(lo), np.log(hi)))

# ── blender helpers ───────────────────────────────────────────────────────
def sel_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def set_active(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)

def apply_tf(o, loc=False):
    sel_none(); set_active(o)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    sel_none()

def spawn_cube():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    return bpy.context.active_object

# ── Geometry Nodes helper (minimal NodeWrangler) ──────────────────────────
class NW:
    def __init__(self, tree):
        self.tree = tree
        self._group_input = None

    def new_node(self, idname, input_args=None, input_kwargs=None, attrs=None,
                 expose_input=None):
        if input_args is None:
            input_args = []
        if input_kwargs is None:
            input_kwargs = {}
        if idname == "NodeGroupInput":
            if self._group_input is None:
                node = self.tree.nodes.new(idname)
                self._group_input = node
            else:
                node = self._group_input
        elif idname in bpy.data.node_groups:
            node = self.tree.nodes.new("GeometryNodeGroup")
            node.node_group = bpy.data.node_groups[idname]
        else:
            node = self.tree.nodes.new(idname)
        if attrs:
            for k, v in attrs.items():
                try:
                    setattr(node, k, v)
                except Exception:
                    pass
        if expose_input:
            for entry in expose_input:
                sock_type, name, default = entry
                existing = [s for s in self.tree.interface.items_tree
                            if s.name == name and getattr(s, 'in_out', None) == "INPUT"]
                if not existing:
                    item = self.tree.interface.new_socket(
                        name, in_out="INPUT", socket_type=sock_type)
                    if default is not None and hasattr(item, 'default_value'):
                        try:
                            item.default_value = default
                        except Exception:
                            pass
        all_inputs = list(enumerate(input_args)) + list(input_kwargs.items())
        for key, value in all_inputs:
            if value is None:
                continue
            if node.bl_idname == "NodeGroupOutput" and isinstance(key, str):
                if key not in node.inputs:
                    sock_type = self._infer_socket_type(value)
                    self.tree.interface.new_socket(
                        key, in_out="OUTPUT", socket_type=sock_type)
            self._connect(node, key, value)
        return node

    def _infer_socket_type(self, value):
        if isinstance(value, bpy.types.NodeSocket):
            return self._map_socket_type(value.bl_idname)
        elif isinstance(value, bpy.types.Node):
            if value.outputs:
                return self._map_socket_type(value.outputs[0].bl_idname)
        return "NodeSocketGeometry"

    @staticmethod
    def _map_socket_type(bl_idname):
        mapping = {
            "NodeSocketFloat": "NodeSocketFloat",
            "NodeSocketVector": "NodeSocketVector",
            "NodeSocketBool": "NodeSocketBool",
            "NodeSocketInt": "NodeSocketInt",
            "NodeSocketGeometry": "NodeSocketGeometry",
        }
        return mapping.get(bl_idname, "NodeSocketFloat")

    def _connect(self, node, key, value):
        try:
            sock = node.inputs[key]
        except (IndexError, KeyError):
            return
        if isinstance(value, bpy.types.NodeSocket):
            self.tree.links.new(value, sock)
        elif isinstance(value, bpy.types.Node):
            if value.outputs:
                self.tree.links.new(value.outputs[0], sock)
        elif isinstance(value, list):
            for v in value:
                if isinstance(v, bpy.types.NodeSocket):
                    self.tree.links.new(v, sock)
                elif isinstance(v, bpy.types.Node) and v.outputs:
                    self.tree.links.new(v.outputs[0], sock)
        else:
            try:
                sock.default_value = value
            except Exception:
                pass

    def math(self, operation, *nodes):
        return self.new_node("ShaderNodeMath", list(nodes), attrs={"operation": operation})

    def vector_math(self, operation, *nodes):
        return self.new_node("ShaderNodeVectorMath", list(nodes),
                             attrs={"operation": operation})

    def compare(self, operation, *nodes):
        return self.new_node("FunctionNodeCompare", list(nodes),
                             attrs={"operation": operation})

    def scale(self, vector, scalar):
        return self.new_node("ShaderNodeVectorMath",
                             input_kwargs={"Vector": vector, "Scale": scalar},
                             attrs={"operation": "SCALE"})

    def scalar_multiply(self, a, b):
        return self.math("MULTIPLY", a, b)

    def scalar_add(self, a, b):
        return self.math("ADD", a, b)

    def scalar_divide(self, a, b):
        return self.math("DIVIDE", a, b)

    def add(self, a, b):
        return self.vector_math("ADD", a, b)

    def build_float_curve(self, x, anchors, handle="VECTOR"):
        float_curve = self.new_node("ShaderNodeFloatCurve",
                                    input_kwargs={"Value": x})
        c = float_curve.mapping.curves[0]
        for i, p in enumerate(anchors):
            if i < 2:
                c.points[i].location = p
            else:
                c.points.new(*p)
            c.points[i].handle_type = handle
        float_curve.mapping.use_clip = False
        return float_curve

    def curve2mesh(self, curve, profile_curve=None, scale=None):
        kwargs = {"Curve": curve, "Profile Curve": profile_curve, "Fill Caps": True}
        if scale is not None and bpy.app.version >= (5, 0, 0):
            kwargs["Scale"] = scale
        ctm = self.new_node("GeometryNodeCurveToMesh", input_kwargs=kwargs)
        return self.new_node("GeometryNodeSetShadeSmooth", [ctm, None, False])

def make_geomod(name, geo_func, obj, input_args=None):
    if input_args is None:
        input_args = []
    mod = obj.modifiers.new(name=name, type="NODES")
    if mod.node_group is None:
        ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
        ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        mod.node_group = ng
    nw = NW(mod.node_group)
    geo_func(nw, *input_args)
    sel_none(); set_active(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    sel_none()

# ── Geometry Node functions ───────────────────────────────────────────────

def geo_extension(nw):
    noise_strength_val = uniform(0.1, 0.2)
    noise_scale = uniform(1.4, 2.8)
    geometry = nw.new_node("NodeGroupInput",
                           expose_input=[("NodeSocketGeometry", "Geometry", None)])
    pos = nw.new_node("GeometryNodeInputPosition")
    length = nw.vector_math("LENGTH", pos)
    inv_len = nw.scalar_divide(1.0, length.outputs["Value"])
    direction = nw.scale(pos, inv_len)
    rand_offset = uniform(-1, 1, 3)
    rand_vec = nw.new_node("FunctionNodeInputVector")
    rand_vec.vector = tuple(rand_offset)
    direction = nw.add(direction, rand_vec)
    musgrave = nw.new_node("ShaderNodeTexNoise",
                           [direction],
                           input_kwargs={"Scale": noise_scale},
                           attrs={"noise_dimensions": "2D"})
    musgrave_shifted = nw.scalar_add(musgrave.outputs[0], 0.25)
    musgrave_scaled = nw.scalar_multiply(musgrave_shifted, noise_strength_val)
    offset = nw.scale(pos, musgrave_scaled)
    geometry = nw.new_node("GeometryNodeSetPosition",
                           input_kwargs={"Geometry": geometry, "Offset": offset})
    nw.new_node("NodeGroupOutput", input_kwargs={"Geometry": geometry})

def geo_globular(nw):
    star_resolution = np.random.randint(6, 12)
    resolution = 64
    frequency = uniform(-0.2, 0.2)

    circle = nw.new_node("GeometryNodeMeshCircle", [star_resolution * 3])
    circle = circle.outputs["Mesh"]

    idx = nw.new_node("GeometryNodeInputIndex")
    mod2 = nw.math("MODULO", idx, 2)
    selection = nw.compare("EQUAL", mod2, 0)

    capture = nw.new_node("GeometryNodeCaptureAttribute",
                          [circle, selection])
    circle_out = capture.outputs["Geometry"]
    selection_out = capture.outputs[1]

    pos = nw.new_node("GeometryNodeInputPosition")
    scaled_pos = nw.scale(pos, uniform(1.1, 1.2))
    circle_out = nw.new_node("GeometryNodeSetPosition",
                             [circle_out, selection_out, scaled_pos])

    profile_curve = nw.new_node("GeometryNodeMeshToCurve", [circle_out])

    curve_line = nw.new_node("GeometryNodeCurvePrimitiveLine")
    curve = nw.new_node("GeometryNodeResampleCurve",
                         input_kwargs={"Curve": curve_line, "Count": resolution})

    anchors = [
        (0, uniform(0.2, 0.4)),
        (uniform(0.4, 0.6), log_uniform(0.5, 0.8)),
        (uniform(0.8, 0.85), uniform(0.4, 0.6)),
        (1.0, 0.05),
    ]
    spline_param = nw.new_node("GeometryNodeSplineParameter")
    radius = nw.build_float_curve(spline_param.outputs["Factor"], anchors, "AUTO")
    radius = nw.scalar_multiply(radius, log_uniform(0.5, 1.0))

    curve = nw.new_node("GeometryNodeSetCurveRadius", [curve, None, radius])

    spline_param2 = nw.new_node("GeometryNodeSplineParameter")
    tilt = nw.scalar_multiply(spline_param2.outputs["Factor"],
                              2 * np.pi * frequency)
    curve = nw.new_node("GeometryNodeSetCurveTilt", [curve, None, tilt])

    geometry = nw.curve2mesh(curve, profile_curve, scale=radius)

    geometry = nw.new_node("GeometryNodeStoreNamedAttribute",
                           input_kwargs={"Geometry": geometry,
                                         "Name": "selection",
                                         "Value": selection_out},
                           attrs={"data_type": "FLOAT", "domain": "POINT"})
    nw.new_node("NodeGroupOutput", input_kwargs={"Geometry": geometry})

# ── Build ─────────────────────────────────────────────────────────────────
# (base_hue = uniform(0.2, 0.4) inside FixedSeed(factory_seed) block).
with FixedSeed(FACTORY_SEED):
    _cactus_base_hue = float(np.random.uniform(0.2, 0.4))
    MAT_CACTUS = make_cactus_material(_cactus_base_hue, name="Cactus")

with FixedSeed(FACTORY_SEED):
    obj = spawn_cube()
    make_geomod("geo_globular", geo_globular, obj)
    make_geomod("geo_extension", geo_extension, obj)

    obj.scale = uniform(0.8, 1.5, 3)
    obj.rotation_euler[-1] = uniform(0, np.pi * 2)
    apply_tf(obj)

obj.data.materials.append(MAT_CACTUS)
obj.name = "GlobularCactus"

