# [FL_INDEX: keywords="blender_factory, procedural_3d, PrickyPearCactusFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PrickyPearCactusFactory | Category: factories_geo
# Prompt: A 3D model of a prickly pear cactus with flat oval pad segments stacked vertically. The cactus consists of multiple large flat elliptical pads connected end-to-end in a vertical column, with each pad densely covered in short white spines and bristles. The pads are bright green with a slightly flattened form. The overall shape is a tall stacked column of prickly pear segments tapering toward the top.

import os
import random
import bpy
import numpy as np
from numpy.random import uniform, normal

FACTORY_SEED = 0

# ── quadratic interpolation ───────────────────────────────────────────────
def quadratic_interp(points, num_out):
    n = len(points)
    if n == 1:
        return np.tile(points[0], (num_out, 1))
    if n == 2:
        t = np.linspace(0, 1, num_out)[:, None]
        return points[0] * (1 - t) + points[1] * t
    xs = np.linspace(0, n - 1, num_out)
    result = np.empty((num_out, points.shape[1]))
    for idx in range(num_out):
        x = xs[idx]
        seg = int(x)
        if seg >= n - 1:
            seg = n - 2
        if seg == 0:
            i0, i1, i2 = 0, 1, 2
        elif seg >= n - 2:
            i0, i1, i2 = n - 3, n - 2, n - 1
        else:
            i0, i1, i2 = seg - 1, seg, seg + 1
        x0, x1, x2 = float(i0), float(i1), float(i2)
        L0 = (x - x1) * (x - x2) / ((x0 - x1) * (x0 - x2))
        L1 = (x - x0) * (x - x2) / ((x1 - x0) * (x1 - x2))
        L2 = (x - x0) * (x - x1) / ((x2 - x0) * (x2 - x1))
        result[idx] = L0 * points[i0] + L1 * points[i1] + L2 * points[i2]
    return result

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

# ============================================================================
# Inlined material — hand-crafted for cactus category (single shader).
# ============================================================================

import math, colorsys

def _hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def make_cactus_material(base_hue, name="Cactus"):
    """Cactus surface shader: Fresnel tint over noise-driven color ramp."""

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

def log_uniform(lo, hi):
    return np.exp(np.random.uniform(np.log(lo), np.log(hi)))

# ── Blender helpers ────────────────────────────────────────────────────────
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

def apply_mod(o, mod_obj):
    sel_none(); set_active(o)
    bpy.ops.object.modifier_apply(modifier=mod_obj.name)
    sel_none()

def spawn_cube():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    return bpy.context.active_object

def join_objects(objs):
    if len(objs) == 1:
        return objs[0]
    sel_none()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    sel_none()
    return o

def data2mesh(vertices, edges, faces=None, name=""):
    mesh = bpy.data.meshes.new(name)
    if faces is None:
        faces = []
    if isinstance(vertices, list):
        vertices = np.array(vertices)
    if isinstance(edges, list):
        edges = np.array(edges)
    mesh.from_pydata(vertices.tolist(), edges.tolist(), faces)
    mesh.update()
    return mesh

def mesh2obj(mesh):
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

def read_co(o):
    a = np.zeros(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)

def deep_clone_obj(obj):
    new_mesh = obj.data.copy()
    new_obj = obj.copy()
    new_obj.data = new_mesh
    bpy.context.scene.collection.objects.link(new_obj)
    return new_obj

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
            return value.bl_idname
        elif isinstance(value, bpy.types.Node):
            if value.outputs:
                return value.outputs[0].bl_idname
        return "NodeSocketGeometry"

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

    def scalar_sub(self, a, b):
        return self.math("SUBTRACT", a, b)

    def add(self, a, b):
        return self.vector_math("ADD", a, b)

    def sub(self, a, b):
        return self.vector_math("SUBTRACT", a, b)

    def dot(self, a, b):
        return self.new_node("ShaderNodeVectorMath", [a, b],
                             attrs={"operation": "DOT_PRODUCT"}).outputs["Value"]

    def separate(self, vec):
        node = self.new_node("ShaderNodeSeparateXYZ", [vec])
        return node.outputs["X"], node.outputs["Y"], node.outputs["Z"]

    def nw_uniform(self, low=0.0, high=1.0, data_type="FLOAT"):
        seed = np.random.randint(int(1e5))
        if isinstance(low, (list, tuple, np.ndarray)):
            data_type = "FLOAT_VECTOR"
        return self.new_node("FunctionNodeRandomValue",
                             input_kwargs={"Min": low, "Max": high, "Seed": seed},
                             attrs={"data_type": data_type})

    def bernoulli(self, probability):
        seed = np.random.randint(int(1e5))
        return self.new_node("FunctionNodeRandomValue",
                             input_kwargs={"Probability": probability, "Seed": seed},
                             attrs={"data_type": "BOOLEAN"}).outputs[3]

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
        kwargs = {"Curve": curve,
                  "Profile Curve": profile_curve,
                  "Fill Caps": True}
        if scale is not None and bpy.app.version >= (5, 0, 0):
            kwargs["Scale"] = scale
        ctm = self.new_node("GeometryNodeCurveToMesh", input_kwargs=kwargs)
        return self.new_node("GeometryNodeSetShadeSmooth", [ctm, None, False])

    def capture_vector(self, geometry, value):
        """CaptureAttribute with FLOAT_VECTOR data type (for normals)."""

        node = self.tree.nodes.new("GeometryNodeCaptureAttribute")
        # Blender 5.0: capture_items starts empty; must add a channel
        try:
            if len(node.capture_items) == 0:
                node.capture_items.new('FLOAT_VECTOR', 'Value')
            else:
                node.capture_items[0].data_type = "FLOAT_VECTOR"
        except Exception:
            try:
                node.data_type = "FLOAT_VECTOR"
            except Exception:
                pass
        self._connect(node, "Geometry", geometry)
        self._connect(node, 1, value)
        return node

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

# ── Rodrigues rotation ────────────────────────────────────────────────────
def rodrigues_rot(vec, axis, angle):
    axis = np.array(axis, dtype=float)
    n = np.linalg.norm(axis)
    if n < 1e-12:
        return vec
    axis = axis / n
    cs, sn = np.cos(angle), np.sin(angle)
    return vec * cs + sn * np.cross(axis, vec) + axis * np.dot(axis, vec) * (1 - cs)

# ── Tree path generation ─────────────────────────────────────────────────
def rand_path(n_pts, sz=1, std=0.3, momentum=0.5, init_vec=None, init_pt=None,
              pull_dir=None, pull_init=1, pull_factor=0, sz_decay=1, decay_mom=True):
    if init_vec is None:
        init_vec = [0, 0, 1]
    if init_pt is None:
        init_pt = [0, 0, 0]
    init_vec = np.array(init_vec, dtype=float)
    if pull_dir is not None:
        pull_dir = np.array(pull_dir, dtype=float)
        init_vec = init_vec + pull_init * pull_dir
    n = np.linalg.norm(init_vec)
    if n > 1e-12:
        init_vec = init_vec / n
    path = np.zeros((n_pts, 3))
    path[0] = init_pt
    for i in range(1, n_pts):
        if i == 1:
            prev_delta = init_vec * sz
        else:
            prev_delta = path[i - 1] - path[i - 2]
        prev_sz = np.linalg.norm(prev_delta)
        new_delta = prev_delta + np.random.randn(3) * std
        if pull_dir is not None:
            new_delta = new_delta + pull_factor * pull_dir
        nd_norm = np.linalg.norm(new_delta)
        if nd_norm > 1e-12:
            new_delta = (new_delta / nd_norm) * prev_sz
        if decay_mom:
            tmp_momentum = 1 - (1 - momentum) * (i + 1) / n_pts
        else:
            tmp_momentum = momentum
        delta = prev_delta * tmp_momentum + new_delta * (1 - tmp_momentum)
        d_norm = np.linalg.norm(delta)
        if d_norm > 1e-12:
            delta = (delta / d_norm) * sz * (sz_decay ** i)
        path[i] = path[i - 1] + delta
    return path

def get_spawn_pt(path, rng=None, ang_min=np.pi / 6, ang_max=0.9 * np.pi / 2,
                 rnd_idx=None, ang_sign=None, axis2=None, init_vec=None, z_bias=0):
    if rng is None:
        rng = [0.5, 1]
    n = len(path)
    if n == 1:
        return 0, path[0], init_vec
    if rnd_idx is None:
        rnd_idx = np.random.randint(int(n * rng[0]), int(n * rng[1]))
    if init_vec is None:
        curr_vec = path[rnd_idx] - path[rnd_idx - 1]
        axis1 = np.array([curr_vec[1], -curr_vec[0], 0])
        if axis2 is None:
            axis2 = rodrigues_rot(curr_vec, axis1, np.pi / 2)
        if callable(axis2):
            axis2 = axis2()
        rnd_ang = np.random.rand() * (ang_max - ang_min) + ang_min
        if ang_sign is None:
            ang_sign = np.sign(np.random.randn())
        rnd_ang *= ang_sign
        init_vec = rodrigues_rot(curr_vec, axis2, rnd_ang)
    return rnd_idx, path[rnd_idx], init_vec

class FineTreeVertices:
    def __init__(self, vtxs=None, radius_fn=None, resolution=1):
        if vtxs is None:
            vtxs = np.array([[0, 0, 0]])
        elif isinstance(vtxs, list):
            vtxs = np.array(vtxs)
        self.vtxs = vtxs
        self.parent = [-1] * len(vtxs)
        self.level = [0] * len(vtxs)
        self.resolution = resolution
        if radius_fn is None:
            def radius_fn(base_radius, size, resolution):
                return [1] * size
        self.radius_fn = radius_fn
        self.detailed_locations = [[0, 0, 0]]
        self.radius = [1]
        self.detailed_parents = [-1]

    def get_idxs(self):
        return list(np.arange(len(self.vtxs)))

    def __len__(self):
        return len(self.vtxs)

    def append(self, v, p, l=None):
        self.vtxs = np.append(self.vtxs, v, axis=0)
        self.parent += p
        if l is None:
            l = [0] * len(v)
        elif isinstance(l, int):
            l = [l] * len(v)
        self.level += l
        ctrl_pts = np.concatenate([self.vtxs[p[0]:p[0] + 1], v])
        subdivided = quadratic_interp(ctrl_pts, len(v) * self.resolution + 1)
        self.detailed_locations.extend(subdivided[1:])
        base_radius = self.radius[p[0] * self.resolution]
        self.radius.extend(self.radius_fn(base_radius, len(v), self.resolution))
        self.detailed_parents.append(p[0] * self.resolution)
        self.detailed_parents.extend(
            np.arange(0, len(v) * self.resolution - 1)
            + len(self.detailed_parents) - 1
        )

    @property
    def edges(self):
        edges = np.stack(
            [np.arange(len(self.detailed_locations)),
             np.array(self.detailed_parents)], 1)
        return edges[edges[:, 1] != -1]

def recursive_path(tree, parent_idxs, level, path_kargs=None, spawn_kargs=None,
                   n=1, symmetry=False, children=None):
    if path_kargs is None:
        return
    if symmetry:
        n = 2 * n
    for branch_idx in range(n):
        curr_idx = branch_idx // 2 if symmetry else branch_idx
        curr_path = path_kargs(curr_idx)
        curr_spawn = spawn_kargs(curr_idx)
        if symmetry:
            curr_spawn["ang_sign"] = 2 * (branch_idx % 2) - 1
        parent_idx, init_pt, init_vec = get_spawn_pt(
            tree.vtxs[parent_idxs], **curr_spawn)
        parent_idx = parent_idxs[parent_idx]
        path = rand_path(**curr_path, init_pt=init_pt, init_vec=init_vec)
        new_vtxs = path[1:]
        new_idxs = list(np.arange(len(new_vtxs)) + len(tree))
        node_idxs = [parent_idx] + new_idxs
        tree.append(new_vtxs, node_idxs[:-1], level)
        if children is not None:
            for c in children:
                recursive_path(tree, node_idxs, level + 1, **c)

def build_radius_tree(radius_fn, branch_config, base_radius=0.002,
                      resolution=1, fix_first=False):
    vtx = FineTreeVertices(np.zeros((1, 3)), radius_fn=radius_fn,
                           resolution=resolution)
    recursive_path(vtx, vtx.get_idxs(), level=0, **branch_config)
    if fix_first:
        vtx.radius[0] = vtx.radius[1]
    obj = mesh2obj(data2mesh(
        np.array(vtx.detailed_locations), vtx.edges, name="tree"))
    vg = obj.vertex_groups.new(name="radius")
    for i, r in enumerate(vtx.radius):
        vg.add([i], base_radius * r, "REPLACE")
    return obj

# ── Geometry Node functions ───────────────────────────────────────────────
def align_tilt(nw, curve, axis=(1, 0, 0)):
    axis_node = nw.vector_math("NORMALIZE", axis)
    normal = nw.new_node("GeometryNodeInputNormal")
    tangent = nw.vector_math("NORMALIZE", nw.new_node("GeometryNodeInputTangent"))
    axis_node = nw.vector_math("NORMALIZE",
                               nw.sub(axis_node, nw.dot(axis_node, tangent)))
    cos_val = nw.dot(axis_node, normal)
    sin_val = nw.dot(nw.vector_math("CROSS_PRODUCT", normal, axis_node), tangent)
    tilt = nw.math("ARCTAN2", sin_val, cos_val)
    curve = nw.new_node("GeometryNodeSetCurveTilt", [curve, None, tilt])
    return curve

def geo_extension(nw):
    noise_strength = uniform(0.1, 0.2)
    noise_scale = uniform(1.4, 2.8)
    geometry = nw.new_node("NodeGroupInput",
                           expose_input=[("NodeSocketGeometry", "Geometry", None)])
    pos = nw.new_node("GeometryNodeInputPosition")
    direction = nw.scale(pos, nw.scalar_divide(1.0,
                         nw.vector_math("LENGTH", pos).outputs["Value"]))
    rand_offset = uniform(-1, 1, 3)
    rand_vec = nw.new_node("FunctionNodeInputVector")
    rand_vec.vector = tuple(rand_offset)
    direction = nw.add(direction, rand_vec)
    musgrave = nw.new_node("ShaderNodeTexNoise",
                           [direction],
                           input_kwargs={"Scale": noise_scale},
                           attrs={"noise_dimensions": "2D"})
    musgrave_scaled = nw.scalar_multiply(
        nw.scalar_add(musgrave.outputs[0], 0.25),
        noise_strength)
    offset = nw.scale(pos, musgrave_scaled)
    geometry = nw.new_node("GeometryNodeSetPosition",
                           input_kwargs={"Geometry": geometry, "Offset": offset})
    nw.new_node("NodeGroupOutput", input_kwargs={"Geometry": geometry})

# ── Spike utilities ───────────────────────────────────────────────────────
def sample_direction(min_z):
    for _ in range(100):
        x = normal(size=3)
        y = x / np.linalg.norm(x)
        if y[-1] > min_z:
            return y
    return np.array([0.0, 0.0, 1.0])

def geo_radius_spike(nw, merge_distance=0.001):
    skeleton = nw.new_node("NodeGroupInput",
                           expose_input=[("NodeSocketGeometry", "Geometry", None)])
    radius_attr = nw.new_node("GeometryNodeInputNamedAttribute",
                              input_kwargs={"Name": "radius"},
                              attrs={"data_type": "FLOAT"})
    radius = radius_attr.outputs["Attribute"]
    curve = nw.new_node("GeometryNodeMeshToCurve", [skeleton])
    curve = align_tilt(nw, curve, axis=(0, 0, 1))
    curve = nw.new_node("GeometryNodeSetCurveRadius", [curve, None, radius])
    profile = nw.new_node("GeometryNodeCurvePrimitiveCircle")
    profile = profile.outputs["Curve"]
    geometry = nw.curve2mesh(curve, profile, scale=radius)
    if merge_distance > 0:
        geometry = nw.new_node("GeometryNodeMergeByDistance",
                               input_kwargs={"Geometry": geometry, "Distance": merge_distance})
    nw.new_node("NodeGroupOutput", input_kwargs={"Geometry": geometry})

def build_single_spike(base_radius=0.002):
    n_branch = 4
    n_major = 9
    branch_config = {
        "n": n_branch,
        "path_kargs": lambda idx: {
            "n_pts": n_major,
            "std": 0.5,
            "momentum": 0.85,
            "sz": uniform(0.005, 0.01),
        },
        "spawn_kargs": lambda idx: {"init_vec": sample_direction(0.8)},
    }

    def radius_fn(base_radius, size, resolution):
        return base_radius * 0.5 ** (
            np.arange(size * resolution) / (size * resolution))

    obj = build_radius_tree(radius_fn, branch_config, base_radius)
    make_geomod("geo_radius_spike", geo_radius_spike, obj)
    return obj

def make_spike_collection(n=5, base_radius=0.002):
    col = bpy.data.collections.new("spikes")
    bpy.context.scene.collection.children.link(col)
    for i in range(n):
        np.random.choice(1, p=[1.0])
        spike_obj = build_single_spike(base_radius=base_radius)
        spike_obj.name = f"spike_{i}"
        bpy.context.scene.collection.objects.unlink(spike_obj)
        col.objects.link(spike_obj)
    col.hide_viewport = True
    col.hide_render = True
    return col

def geo_place_spikes(nw, spike_collection, spike_distance=0.08,
                     cap_percentage=0.1, density=5e4):
    geometry = nw.new_node("NodeGroupInput",
                           expose_input=[("NodeSocketGeometry", "Geometry", None)])
    selection_attr = nw.new_node("GeometryNodeInputNamedAttribute",
                                input_kwargs={"Name": "selection"},
                                attrs={"data_type": "FLOAT"})
    selection = selection_attr.outputs["Attribute"]

    normal_input = nw.new_node("GeometryNodeInputNormal")
    capture = nw.capture_vector(geometry, normal_input)
    geom_captured = capture.outputs["Geometry"]
    captured_normal = capture.outputs[1]

    selected = nw.compare("GREATER_THAN", selection, 0.8)

    spikes = nw.new_node("GeometryNodeCollectionInfo",
                         [spike_collection, True, True])

    rotation = nw.new_node("FunctionNodeAlignEulerToVector",
                           input_kwargs={"Vector": captured_normal},
                           attrs={"axis": "Z"})
    rotation = nw.new_node("FunctionNodeRotateEuler",
                           input_kwargs={"Rotation": rotation,
                                         "Angle": nw.nw_uniform(0, 2 * np.pi)},
                           attrs={"rotation_type": "AXIS_ANGLE", "space": "LOCAL"})
    rotation = nw.new_node("FunctionNodeAlignEulerToVector",
                           [rotation, nw.nw_uniform(0.2, 0.5)],
                           attrs={"axis": "Z"})
    rotation = nw.add(rotation, nw.nw_uniform([-0.05] * 3, [0.05] * 3))

    pos = nw.new_node("GeometryNodeInputPosition")
    _, _, z = nw.separate(pos)
    z_stat = nw.new_node("GeometryNodeAttributeStatistic",
                         [geom_captured, None, z])
    z_max = z_stat.outputs["Max"]
    z_range = z_stat.outputs["Range"]
    percentage = nw.scalar_divide(nw.scalar_sub(z_max, z), z_range)

    is_cap = nw.bernoulli(
        nw.build_float_curve(percentage,
                             [(0, 1), (cap_percentage, 0.5), (1, 0)]))
    cap = nw.new_node("GeometryNodeSeparateGeometry", [geom_captured, is_cap])
    cap = nw.new_node("GeometryNodeMergeByDistance",
                      input_kwargs={"Geometry": cap, "Distance": spike_distance / 2})

    points = nw.new_node("GeometryNodeDistributePointsOnFaces",
                         input_kwargs={"Mesh": geom_captured,
                                       "Selection": selected,
                                       "Density": density})
    points = points.outputs["Points"]
    points = nw.new_node("GeometryNodeMergeByDistance",
                         input_kwargs={"Geometry": points, "Distance": spike_distance})

    all_points = nw.new_node("GeometryNodeJoinGeometry", [[cap, points]])

    spike_instances = nw.new_node("GeometryNodeInstanceOnPoints",
                                 input_kwargs={
                                     "Points": all_points,
                                     "Instance": spikes,
                                     "Pick Instance": True,
                                     "Rotation": rotation,
                                     "Scale": nw.nw_uniform([0.5] * 3, [1.0] * 3),
                                 })

    realized = nw.new_node("GeometryNodeRealizeInstances", [spike_instances])
    nw.new_node("NodeGroupOutput", input_kwargs={"Geometry": realized})

# ── PrickyPear body ───────────────────────────────────────────────────────
def geo_leaf(nw):
    resolution = 64
    profile_curve = nw.new_node("GeometryNodeCurvePrimitiveCircle")
    profile_curve = profile_curve.outputs["Curve"]

    curve_line = nw.new_node("GeometryNodeCurvePrimitiveLine")
    curve = nw.new_node("GeometryNodeResampleCurve",
                         input_kwargs={"Curve": curve_line, "Count": resolution})

    anchors = [
        (0, uniform(0.15, 0.2)),
        (uniform(0.4, 0.6), log_uniform(0.4, 0.5)),
        (1.0, 0.05),
    ]
    spline_param = nw.new_node("GeometryNodeSplineParameter")
    radius = nw.build_float_curve(spline_param.outputs["Factor"], anchors, "AUTO")
    radius = nw.scalar_multiply(radius, log_uniform(0.5, 1.5))

    curve = nw.new_node("GeometryNodeSetCurveRadius", [curve, None, radius])
    geometry = nw.curve2mesh(curve, profile_curve, scale=radius)

    nw.new_node("NodeGroupOutput", input_kwargs={"Geometry": geometry})

def build_prickypear_leaf():
    obj = spawn_cube()
    make_geomod("geo_leaf", geo_leaf, obj)
    make_geomod("geo_extension", geo_extension, obj)
    obj.scale = uniform(0.8, 1.2), uniform(0.2, 0.25), uniform(0.8, 1.2)
    apply_tf(obj)
    return obj

def build_prickypear_leaves(level=0):
    if level == 0:
        return build_prickypear_leaf()

    n = np.random.randint(1, 3)
    leaves = [build_prickypear_leaves(level - 1) for _ in range(n)]
    base = build_prickypear_leaf()

    angles = np.random.permutation([
        -uniform(np.pi / 3, np.pi / 2),
        uniform(-np.pi / 16, np.pi / 16),
        uniform(np.pi / 3, np.pi / 2),
    ])[:n]
    vectors = [[np.sin(a), 0, np.cos(a) + 0.5] for a in angles]
    locations = read_co(base)

    for a, v, leaf in zip(angles, vectors, leaves):
        index = np.argmax(locations @ v)
        leaf.location[-1] -= 0.15
        apply_tf(leaf, loc=True)
        leaf.scale = [uniform(0.5, 0.75)] * 3
        leaf.location = locations[index]
        leaf.rotation_euler = 0, a, uniform(-np.pi / 3, np.pi / 3)

    obj = join_objects([base, *leaves])
    return obj

def build_prickypear():
    obj = build_prickypear_leaves(2)
    # Write "selection" attribute (all 1s — entire surface is spike-able)
    attr = obj.data.attributes.new("selection", "FLOAT", "POINT")
    vals = np.ones(len(obj.data.vertices))
    attr.data.foreach_set("value", vals)
    return obj, 0.02  # noise_strength

# ── Main pipeline ─────────────────────────────────────────────────────────
# SEED-deterministic: all random calls under FixedSeed(FACTORY_SEED) or FixedSeed(FACTORY_SEED+1)
with FixedSeed(FACTORY_SEED):
    _cactus_base_hue = float(np.random.uniform(0.2, 0.4))
    MAT_CACTUS = make_cactus_material(_cactus_base_hue, name="Cactus")

with FixedSeed(FACTORY_SEED):
    obj, noise_strength = build_prickypear()

# Voxel remesh (no random calls)
m_rm = obj.modifiers.new("RM", "REMESH")
m_rm.mode = 'VOXEL'
m_rm.voxel_size = 0.01
apply_mod(obj, m_rm)

# DISPLACE noise
if noise_strength > 0:
    t_choice = np.random.choice(["STUCCI", "MARBLE"])
    tex_noise = bpy.data.textures.new(name="cactus_noise", type=t_choice)
    tex_noise.noise_scale = log_uniform(0.1, 0.15)
    m_disp = obj.modifiers.new("DISPLACE", "DISPLACE")
    m_disp.strength = noise_strength
    m_disp.mid_level = 0
    m_disp.texture = tex_noise
    apply_mod(obj, m_disp)

# Spike prototypes and placement
spike_col = make_spike_collection(n=5, base_radius=0.002)
spike_obj = deep_clone_obj(obj)
spike_obj.name = "spikes_geo"
make_geomod("geo_place_spikes", geo_place_spikes, spike_obj,
            input_args=[spike_col, 0.08, 0.1, 5e4])

for s_obj in list(spike_col.objects):
    bpy.data.objects.remove(s_obj, do_unlink=True)
bpy.data.collections.remove(spike_col)

final = join_objects([obj, spike_obj])

final.data.materials.append(MAT_CACTUS)
final.name = "PrickyPearCactus"
