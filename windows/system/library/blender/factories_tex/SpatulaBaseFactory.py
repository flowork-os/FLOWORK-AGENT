# [FL_INDEX: keywords="blender_factory, procedural_3d, SpatulaBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SpatulaBaseFactory | Category: factories_tex
# Prompt: A 3D model of a kitchen spatula rendered from a three-quarter perspective, featuring a flat rectangular blade at the bottom, a long straight handle, and a circular hanging hole at the top of the handle, with a uniform dark brown appearance.

"""Textured SpatulaBaseFactory — faithful shader port.

Geometry: copied verbatim from objects_blender/organizer/SpatulaBaseFactory.py
          (GeoNodes tree `spatula_geometry_nodes`).
Material: single material slot — `shader_rough_plastic`
          factory hard-codes this single shader inside its GeoNodes `SetMaterial`
          node, so there is no weighted registry lookup and no wear_tear pass
          (SpatulaBaseFactory does not override finalize_assets).

Mirrors the Phase-1/Phase-2 seeding convention documented in
`data_pipeline_operators/exp/exp_blender_texture.md`:
  - Materials are sampled on the raw `SEED` (__init__-equivalent).
  - Geometry re-seeds numpy.random inside `build()` via `int_hash((seed, 0))`.
"""


import os
import math
import bpy
import bmesh
import random
import colorsys
import hashlib
from types import SimpleNamespace

import numpy as np
from numpy.random import uniform

class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
        self.py_state = None
        self.np_state = None

    def __enter__(self):
        self.py_state = random.getstate()
        self.np_state = np.random.get_state()
        random.seed(self.seed)
        np.random.seed(self.seed)

    def __exit__(self, *_):
        random.setstate(self.py_state)
        np.random.set_state(self.np_state)

def _md5_hash(x):
    if isinstance(x, (tuple, list)):
        m = hashlib.md5()
        for s in x:
            m.update(str(s).encode("utf-8"))
        return m
    return hashlib.md5(str(x).encode("utf-8"))

def int_hash(x, max_val=(2 ** 32 - 1)):
    return abs(int(_md5_hash(x).hexdigest(), 16)) % max_val

def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

# Raw-bpy shader helpers (subset of MicrowaveFactory's toolbox)
def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

# shader_rough_plastic — faithful raw-bpy port of
# ----------------------------------------------------------------------------
# Original graph (per nodegroup_plastics):
#   Roughness (uniform 0..1) -> MapRange[0..1 -> 0.05..0.25] -> BSDF Roughness
#   TexCoord.Object -> NoiseTexture(4D, scale=Scale*2000, detail=15, distortion=2,
#                                    W=seed) -> Fac
#   Fac * (roughness_mapped * 0.4) * 0.003 -> Displacement height
def make_plastic_rough(name="PlasticRough", base_color=None) -> bpy.types.Material:
    if base_color is None:
        # Matches plastic_rough.shader_rough_plastic default branch (no clear):
        # hsv2rgba(uniform(0,1), uniform(0.5,0.8), log_uniform(0.01,0.5))
        base_color = hsv2rgba(
            (
                float(np.random.uniform(0.0, 1.0)),
                float(np.random.uniform(0.5, 0.8)),
                log_uniform(0.01, 0.5),
            )
        )
    roughness_input = float(np.random.uniform(0.0, 1.0))
    seed_input = float(np.random.uniform(-1000.0, 1000.0))

    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    # Original uses 4D noise (W = seed); fall back to 3D if unavailable.
    if hasattr(noise, "noise_dimensions"):
        try:
            noise.noise_dimensions = "4D"
        except TypeError:
            pass
    # Scale: group input Scale=1.0 * 2000.0 = 2000.0
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed_input
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    # MapRange: roughness -> [0.05, 0.25]
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[1].default_value = 0.0
    map_range.inputs[2].default_value = 1.0
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # roughness_mapped * 0.4
    mul1 = nt.nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul1.inputs[0])

    # noise.Fac * (roughness_mapped * 0.4)
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul2.inputs[0])
    nt.links.new(mul1.outputs[0], mul2.inputs[1])

    # * 0.003 displacement strength
    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    mul3.inputs[1].default_value = 0.003
    nt.links.new(mul2.outputs[0], mul3.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# Minimal GeoNodes shim — copied verbatim from
# objects_blender/organizer/SpatulaBaseFactory.py so the geometry tree can be
# re-constructed without imports.
def geometry_node_group_empty_new():
    group = bpy.data.node_groups.new("Geometry Nodes", "GeometryNodeTree")
    group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    inp = group.nodes.new("NodeGroupInput")
    out = group.nodes.new("NodeGroupOutput")
    out.is_active_output = True
    try:
        group.links.new(inp.outputs["Geometry"], out.inputs["Geometry"])
    except Exception:
        pass
    return group

def ng_inputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == "INPUT"}

def ng_outputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == "OUTPUT"}

def assign_curve(c, points, handles=None):
    for i, p in enumerate(points):
        if i < 2:
            c.points[i].location = p
        else:
            c.points.new(*p)
        if handles is not None:
            c.points[i].handle_type = handles[i]

node_utils = SimpleNamespace(assign_curve=assign_curve)

def _infer_output_socket(item):
    if isinstance(item, bpy.types.NodeSocket):
        return item
    if isinstance(item, tuple) and len(item) == 2 and hasattr(item[0], "outputs"):
        n, s = item
        try:
            return n.outputs[s]
        except Exception:
            return n.outputs[int(s)]
    if hasattr(item, "outputs"):
        for s in item.outputs:
            if getattr(s, "enabled", True):
                return s
        if len(item.outputs):
            return item.outputs[0]
    return None

def _socket_type_for_val(v):
    if isinstance(v, bool):
        return "NodeSocketBool"
    if isinstance(v, int):
        return "NodeSocketInt"
    if isinstance(v, float):
        return "NodeSocketFloat"
    if isinstance(v, (tuple, list, np.ndarray)):
        if len(v) == 3:
            return "NodeSocketVector"
        if len(v) == 4:
            return "NodeSocketColor"
    return "NodeSocketFloat"

def _socket_type_for_out(sock):
    if sock is None:
        return "NodeSocketFloat"
    sid = getattr(sock, "bl_idname", None)
    return sid if isinstance(sid, str) and sid.startswith("NodeSocket") else "NodeSocketFloat"

class NodeWrangler:
    def __init__(self, node_group_or_mod):
        if isinstance(node_group_or_mod, bpy.types.NodesModifier):
            self.modifier = node_group_or_mod
            self.node_group = self.modifier.node_group
        else:
            self.modifier = None
            self.node_group = node_group_or_mod
        self.nodes = self.node_group.nodes
        self.links = self.node_group.links

    def _group_io(self, bl_idname):
        for n in self.nodes:
            if n.bl_idname == bl_idname:
                return n
        n = self.nodes.new(bl_idname)
        if bl_idname == "NodeGroupOutput":
            n.is_active_output = True
        return n

    def expose_input(self, name, val=None, attribute=None, dtype=None, use_namednode=False):
        gi = self._group_io("NodeGroupInput")
        if name not in ng_inputs(self.node_group):
            socket_type = (
                dtype
                if isinstance(dtype, str) and dtype.startswith("NodeSocket")
                else _socket_type_for_val(val)
            )
            if val is None and name == "Geometry":
                socket_type = "NodeSocketGeometry"
            iface = self.node_group.interface.new_socket(
                name=name, in_out="INPUT", socket_type=socket_type
            )
            if val is not None and hasattr(iface, "default_value"):
                try:
                    iface.default_value = val
                except Exception:
                    try:
                        iface.default_value = tuple(val)
                    except Exception:
                        pass
            if self.modifier is not None and val is not None:
                try:
                    self.modifier[iface.identifier] = val
                except Exception:
                    pass
        return gi.outputs[name]

    def connect_input(self, sock, item):
        if isinstance(item, list):
            for it in item:
                self.connect_input(sock, it)
            return
        out = _infer_output_socket(item)
        if out is not None:
            self.links.new(out, sock)
            return
        if hasattr(sock, "default_value"):
            try:
                sock.default_value = item
            except Exception:
                try:
                    sock.default_value = tuple(item)
                except Exception:
                    pass

    def _make_node(self, node_type):
        if (
            isinstance(node_type, str)
            and node_type in bpy.data.node_groups
            and not node_type.startswith(
                ("ShaderNode", "GeometryNode", "FunctionNode", "CompositorNode", "NodeGroup")
            )
        ):
            n = self.nodes.new(
                "GeometryNodeGroup" if self.node_group.bl_idname == "GeometryNodeTree" else "ShaderNodeGroup"
            )
            n.node_tree = bpy.data.node_groups[node_type]
            return n
        if isinstance(node_type, str) and node_type in bpy.data.node_groups:
            try:
                return self.nodes.new(node_type)
            except Exception:
                n = self.nodes.new(
                    "GeometryNodeGroup"
                    if self.node_group.bl_idname == "GeometryNodeTree"
                    else "ShaderNodeGroup"
                )
                n.node_tree = bpy.data.node_groups[node_type]
                return n
        return self.nodes.new(node_type)

    def new_node(
        self,
        node_type,
        input_args=None,
        attrs=None,
        input_kwargs=None,
        label=None,
        expose_input=None,
        compat_mode=True,
        strict=True,
    ):
        input_args = [] if input_args is None else list(input_args)
        attrs = {} if attrs is None else dict(attrs)
        input_kwargs = {} if input_kwargs is None else dict(input_kwargs)
        if node_type == getattr(Nodes, "GroupInput", "NodeGroupInput"):
            node = self._group_io("NodeGroupInput")
        elif node_type == getattr(Nodes, "GroupOutput", "NodeGroupOutput"):
            node = self._group_io("NodeGroupOutput")
        else:
            node = self._make_node(node_type)
        if label is not None:
            node.label = label
            node.name = label
        if expose_input is not None:
            for dtype, name, val in expose_input:
                self.expose_input(name, val=val, dtype=dtype)
        for k, v in attrs.items():
            t = node
            if "." in k:
                parts = k.split(".")
                for p in parts[:-1]:
                    t = getattr(t, p)
                setattr(t, parts[-1], v)
            else:
                setattr(node, k, v)
        for k, v in list(enumerate(input_args)) + list(input_kwargs.items()):
            if v is None:
                continue
            if (
                node.bl_idname == "NodeGroupOutput"
                and not isinstance(k, int)
                and k not in node.inputs
            ):
                out_sock = _infer_output_socket(v)
                self.node_group.interface.new_socket(
                    name=k, in_out="OUTPUT", socket_type=_socket_type_for_out(out_sock)
                )
            try:
                sock = node.inputs[k]
            except Exception:
                sock = node.inputs[int(k)]
            self.connect_input(sock, v)
        return node

class Nodes:
    CombineXYZ = "ShaderNodeCombineXYZ"
    CurveCircle = "GeometryNodeCurvePrimitiveCircle"
    CurveToMesh = "GeometryNodeCurveToMesh"
    FloatCurve = "ShaderNodeFloatCurve"
    GroupOutput = "NodeGroupOutput"
    JoinGeometry = "GeometryNodeJoinGeometry"
    Math = "ShaderNodeMath"
    MeshBoolean = "GeometryNodeMeshBoolean"
    MeshCube = "GeometryNodeMeshCube"
    MeshLine = "GeometryNodeMeshLine"
    MeshToCurve = "GeometryNodeMeshToCurve"
    RealizeInstances = "GeometryNodeRealizeInstances"
    SetCurveRadius = "GeometryNodeSetCurveRadius"
    SetMaterial = "GeometryNodeSetMaterial"
    SplineParameter = "GeometryNodeSplineParameter"
    Transform = "GeometryNodeTransform"
    Value = "ShaderNodeValue"

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    if o is not None:
        o.select_set(True)

def add_geomod(
    objs, geo_func, name=None, apply=False, input_args=None, input_kwargs=None, attributes=None, **_ignored
):
    if input_args is None:
        input_args = []
    if input_kwargs is None:
        input_kwargs = {}
    if attributes is None:
        attributes = []
    if not isinstance(objs, list):
        objs = [objs]
    if not objs:
        return None
    ng = None
    mod_last = None
    for obj in objs:
        mod = obj.modifiers.new(name=name or geo_func.__name__, type="NODES")
        if ng is None:
            if mod.node_group is None:
                mod.node_group = geometry_node_group_empty_new()
            nw = NodeWrangler(mod)
            geo_func(nw, *input_args, **input_kwargs)
            ng = mod.node_group
            ng.name = name or geo_func.__name__
        else:
            mod.node_group = ng
        if apply:
            _select_none()
            _set_active(obj)
            bpy.ops.object.modifier_apply(modifier=mod.name)
        mod_last = mod
    return mod_last

# Geometry — copied verbatim from objects_blender/organizer/SpatulaBaseFactory.py
# (the only change is that the final SetMaterial now receives the Phase-1-sampled
# MAT_PLASTIC instead of the original `shaderfunc_to_material` stub).
def spatula_geometry_nodes(nw: NodeWrangler, **kwargs):
    # Code generated using version 2.6.5 of the node_transpiler

    handle_length = nw.new_node(Nodes.Value, label="handle_length")
    handle_length.outputs[0].default_value = kwargs["handle_length"]

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": handle_length})

    mesh_line = nw.new_node(
        Nodes.MeshLine,
        input_kwargs={"Count": 64, "Offset": combine_xyz},
        attrs={"mode": "END_POINTS"},
    )

    mesh_to_curve = nw.new_node(Nodes.MeshToCurve, input_kwargs={"Mesh": mesh_line})

    handle_radius = nw.new_node(Nodes.Value, label="handle_radius")
    handle_radius.outputs[0].default_value = kwargs["handle_radius"]

    spline_parameter = nw.new_node(Nodes.SplineParameter)

    float_curve = nw.new_node(
        Nodes.FloatCurve, input_kwargs={"Value": spline_parameter.outputs["Factor"]}
    )
    node_utils.assign_curve(
        float_curve.mapping.curves[0], kwargs["handle_control_points"]
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: handle_radius, 1: float_curve},
        attrs={"operation": "MULTIPLY"},
    )

    set_curve_radius = nw.new_node(
        Nodes.SetCurveRadius, input_kwargs={"Curve": mesh_to_curve, "Radius": multiply}
    )

    curve_circle = nw.new_node(Nodes.CurveCircle)

    # Blender 5.0: SetCurveRadius ignored by CurveToMesh — pass via Scale input
    curve_to_mesh = nw.new_node(
        Nodes.CurveToMesh,
        input_kwargs={
            "Curve": set_curve_radius,
            "Profile Curve": curve_circle.outputs["Curve"],
            "Fill Caps": True,
            "Scale": multiply,
        },
    )

    transform_geometry = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": curve_to_mesh,
            "Scale": (kwargs["handle_ratio"], 1.0, 1.0),
        },
    )

    hole_radius = nw.new_node(Nodes.Value, label="hole_radius")
    hole_radius.outputs[0].default_value = kwargs["hole_radius"]

    cylinder = nw.new_node(
        "GeometryNodeMeshCylinder",
        input_kwargs={"Radius": hole_radius, "Depth": 0.1000},
    )

    hole_place_ratio = nw.new_node(Nodes.Value, label="hole_placement")
    hole_place_ratio.outputs[0].default_value = kwargs["hole_placement"]

    multiply_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: handle_length, 1: hole_place_ratio},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_1})

    transform_geometry_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": cylinder.outputs["Mesh"],
            "Translation": combine_xyz_1,
            "Rotation": (0.0000, 1.5708, 0.0000),
            "Scale": (kwargs["hole_ratio"], 1.0000, 1.0000),
        },
    )

    difference = nw.new_node(
        Nodes.MeshBoolean,
        input_kwargs={"Mesh 1": transform_geometry, "Mesh 2": transform_geometry_1},
    )

    cube = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": (
                kwargs["plate_thickness"],
                kwargs["plate_width"],
                kwargs["plate_length"],
            ),
            "Vertices X": 2,
            "Vertices Y": 6,
            "Vertices Z": 6,
        },
    )

    transform_geometry_3 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": cube.outputs["Mesh"],
            "Translation": (0.0000, 0.0000, -kwargs["plate_length"] / 2.0),
        },
    )

    # Handle-plate transition collar
    collar = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": (
                kwargs["plate_thickness"],
                kwargs["plate_width"] * 0.5,
                0.005,
            ),
            "Vertices X": 2,
            "Vertices Y": 6,
            "Vertices Z": 2,
        },
    )

    transform_collar = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": collar.outputs["Mesh"],
            "Translation": (0.0000, 0.0000, -0.0025),
        },
    )

    join_geometry = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={
            "Geometry": [
                difference.outputs["Mesh"],
                transform_collar,
                transform_geometry_3,
            ]
        },
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry}
    )

    triangulate = nw.new_node(
        "GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances}
    )

    multiply_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_1, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_2})

    transform_geometry_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": triangulate, "Translation": combine_xyz_2},
    )

    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": transform_geometry_2,
            "Material": MAT_PLASTIC,
        },
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": set_material},
        attrs={"is_active_output": True},
    )

# Asset parameter sampler — copied verbatim
def get_asset_params(i=0):
    params = {}
    if params.get("hole_radius", None) is None:
        params["hole_radius"] = uniform(0.005, 0.010)
    if params.get("hole_placement", None) is None:
        params["hole_placement"] = uniform(0.75, 0.9)
    if params.get("hole_ratio", None) is None:
        params["hole_ratio"] = uniform(0.8, 2.0)

    if params.get("handle_length", None) is None:
        params["handle_length"] = uniform(0.15, 0.25)

    if params.get("handle_ratio", None) is None:
        params["handle_ratio"] = uniform(0.1, 0.4)
    if params.get("handle_control_points", None) is None:
        params["handle_control_points"] = [
            (0, uniform(0.55, 0.70)),
            (0.3, uniform(0.58, 0.72)),
            (0.65, uniform(0.50, 0.62)),
            (1.0, uniform(0.42, 0.55)),
        ]
    if params.get("handle_radius", None) is None:
        params["handle_radius"] = (
            params["hole_radius"] / params["handle_control_points"][0][1]
        ) / uniform(0.6, 0.8)

    if params.get("plate_thickness", None) is None:
        params["plate_thickness"] = uniform(0.005, 0.01)
    if params.get("plate_width", None) is None:
        params["plate_width"] = uniform(0.04, 0.06)
    if params.get("plate_length", None) is None:
        params["plate_length"] = uniform(0.05, 0.08)

    return params

#   `with FixedSeed(factory_seed): self.params = params.copy()` — which does NOT
#   consume numpy.random. But the SetMaterial node inside create_asset receives
#   a fresh `shaderfunc_to_material(shader_rough_plastic)` call, which is what
#   we replicate here: sample plastic_rough once on the raw seed.
# No wear_tear: SpatulaBaseFactory does not override finalize_assets, so no
SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)
MAT_PLASTIC = make_plastic_rough(name="SpatulaPlastic")

# `FixedSeed(int_hash((factory_seed, 0)))` so geometry RNG is decoupled from
# material RNG.
def build(seed=SEED):
    # Re-seed numpy to the geometry-specific state (int_hash((seed, 0))).
    # Materials are already captured in MAT_PLASTIC at module scope, so this
    # re-seed cannot affect them.
    np.random.seed(int_hash((int(seed), 0)))

    bpy.ops.mesh.primitive_plane_add(
        size=1,
        enter_editmode=False,
        align="WORLD",
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )
    obj = bpy.context.active_object

    obj_params = get_asset_params(0)
    add_geomod(
        obj,
        spatula_geometry_nodes,
        attributes=[],
        apply=True,
        input_kwargs=obj_params,
    )

    # Ensure the material slot exists on the object even if SetMaterial inside
    # the GeoNodes tree is the only path that references it. After apply the
    # material reference is baked into obj.data.materials automatically, but
    # we append defensively so there is always at least one material slot
    # for downstream wear_tear/export tooling.
    if MAT_PLASTIC.name not in [m.name for m in obj.data.materials if m is not None]:
        obj.data.materials.append(MAT_PLASTIC)
    for i in range(len(obj.data.materials)):
        if obj.data.materials[i] is None:
            obj.data.materials[i] = MAT_PLASTIC

    obj.name = "SpatulaBaseFactory"
    return obj

build(SEED)

