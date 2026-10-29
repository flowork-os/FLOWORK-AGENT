# [FL_INDEX: keywords="blender_factory, procedural_3d, SimpleDeskFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SimpleDeskFactory | Category: factories_geo
# Prompt: A 3D model of a simple desk rendered from a three-quarter perspective, featuring a wide rectangular tabletop supported by four angled legs with a lower shelf connecting the legs, displaying a two-tone design with a light-colored top surface and dark-colored leg framework.

"""SimpleDeskFactory (textured) — raw-bpy port of simple_desk.py.

Shaders from plywood.py: white, black_wood, white_metallic, black_metallic.
No finalize_assets / wear_tear in upstream.
"""
# SEED-deterministic: all random calls seeded from SEED

import os
import bpy
import bmesh
import math
import random
import hashlib
import numpy as np
from numpy.random import uniform, normal


def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    """Version-tolerant Principled BSDF socket setter."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break


def _noise_fac(noise_node):
    for k in ("Fac", "Factor"):
        if k in noise_node.outputs:
            return noise_node.outputs[k]
    return noise_node.outputs[0]


def _connect_output(nt, surface_socket, displacement_socket=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(surface_socket, out.inputs["Surface"])
    if displacement_socket is not None:
        nt.links.new(displacement_socket, out.inputs["Displacement"])
    return out


def make_shader_shelves_white(name="ShelvesWhite") -> bpy.types.Material:
    rgb = [0.9, 0.9, 0.9]
    roughness = 0.9
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    _connect_output(nt, bsdf.outputs[0])
    return mat


def make_shader_shelves_white_metallic(name="ShelvesWhiteMetallic") -> bpy.types.Material:
    rgb = [0.9, 0.9, 0.9]
    metallic = 0.65
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    _connect_output(nt, bsdf.outputs[0])
    return mat


def make_shader_shelves_black_metallic(name="ShelvesBlackMetallic") -> bpy.types.Material:
    rgb = [0.0, 0.0, 0.0]
    metallic = 0.65
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    _connect_output(nt, bsdf.outputs[0])
    return mat


# MusgraveTexture removed in Blender 5.0; substituted with stretched NoiseTexture.
def make_shader_shelves_black_wood(name="ShelvesBlackWood", z_axis_texture=False) -> bpy.types.Material:
    wave_scale_val = 2.0
    if z_axis_texture:
        wave_scale = (wave_scale_val, wave_scale_val, 0.1)
    else:
        wave_scale = (wave_scale_val, 0.1, 0.1)

    dark_scale = 0.005
    gray_scale = 0.02
    rgb = [0.02, 0.002, 0.002]
    roughness = 0.9

    mat = _new_material(name)
    nt = mat.node_tree

    # --- Branch 1 ---------------------------------------------------------
    tex_coord_1 = nt.nodes.new("ShaderNodeTexCoord")

    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (
        (0.1, 0.1, 2.0) if z_axis_texture else (0.1, 2.0, 2.0)
    )
    nt.links.new(tex_coord_1.outputs["Object"], mapping_1.inputs["Vector"])

    noise_texture_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_texture_1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise_texture_1.inputs:
        noise_texture_1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise_texture_1.inputs:
        noise_texture_1.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping_1.outputs["Vector"], noise_texture_1.inputs["Vector"])

    voronoi_texture = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi_texture.inputs["Scale"].default_value = 40.0
    nt.links.new(_noise_fac(noise_texture_1), voronoi_texture.inputs["Vector"])

    colorramp_1 = nt.nodes.new("ShaderNodeValToRGB")
    if "Color" in voronoi_texture.outputs:
        nt.links.new(voronoi_texture.outputs["Color"], colorramp_1.inputs["Fac"])
    else:
        # Blender 5.0: Voronoi can output "Distance"; fall back to index 0
        nt.links.new(voronoi_texture.outputs[0], colorramp_1.inputs["Fac"])
    colorramp_1.color_ramp.elements[0].position = 0.0864
    colorramp_1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_1.color_ramp.elements[1].position = 0.1091
    colorramp_1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # --- Branch 2 ---------------------------------------------------------
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = wave_scale
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise_texture = nt.nodes.new("ShaderNodeTexNoise")
    noise_texture.inputs["Scale"].default_value = 3.0
    if "Detail" in noise_texture.inputs:
        noise_texture.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise_texture.inputs:
        noise_texture.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise_texture.inputs["Vector"])

    # Musgrave substitute: another NoiseTexture at Scale 20 / Detail 3
    musgrave_texture = nt.nodes.new("ShaderNodeTexNoise")
    musgrave_texture.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave_texture.inputs:
        musgrave_texture.inputs["Detail"].default_value = 3.0
    nt.links.new(_noise_fac(noise_texture), musgrave_texture.inputs["Vector"])

    # mix_1: data_type RGBA; A (inputs[6]) = musgrave, B (inputs[7]) = noise.Color
    mix_1 = nt.nodes.new("ShaderNodeMix")
    mix_1.data_type = "RGBA"
    nt.links.new(_noise_fac(musgrave_texture), mix_1.inputs[6])
    if "Color" in noise_texture.outputs:
        nt.links.new(noise_texture.outputs["Color"], mix_1.inputs[7])
    else:
        nt.links.new(noise_texture.outputs[1], mix_1.inputs[7])

    colorramp_2 = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix_1.outputs[2], colorramp_2.inputs["Fac"])
    colorramp_2.color_ramp.elements[0].position = 0.0818
    colorramp_2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp_2.color_ramp.elements[1].position = 0.8500
    colorramp_2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # mix_2: factor 0.6, A = colorramp_1.Color, B = colorramp_2.Color
    mix_2 = nt.nodes.new("ShaderNodeMix")
    mix_2.data_type = "RGBA"
    mix_2.inputs[0].default_value = 0.6
    nt.links.new(colorramp_1.outputs["Color"], mix_2.inputs[6])
    nt.links.new(colorramp_2.outputs["Color"], mix_2.inputs[7])

    # Final color ramp: 3 stops (dark, gray, color)
    colorramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix_2.outputs[2], colorramp.inputs["Fac"])
    # Add a 3rd stop
    colorramp.color_ramp.elements.new(0.5)
    colorramp.color_ramp.elements[0].position = 0.15
    colorramp.color_ramp.elements[0].color = (dark_scale, dark_scale, dark_scale, 1.0)
    colorramp.color_ramp.elements[1].position = 0.5
    colorramp.color_ramp.elements[1].color = (gray_scale, gray_scale, gray_scale, 1.0)
    colorramp.color_ramp.elements[2].position = 1.0
    colorramp.color_ramp.elements[2].color = (rgb[0], rgb[1], rgb[2], 1.0)

    # mix_3: factor 0.0040, A = colorramp_1, B = colorramp_2 — for displacement
    mix_3 = nt.nodes.new("ShaderNodeMix")
    mix_3.data_type = "RGBA"
    mix_3.inputs[0].default_value = 0.004
    nt.links.new(colorramp_1.outputs["Color"], mix_3.inputs[6])
    nt.links.new(colorramp_2.outputs["Color"], mix_3.inputs[7])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(colorramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness

    _connect_output(nt, bsdf.outputs[0], displacement_socket=disp.outputs[0])
    return mat


def _get_top_material(kind: str) -> bpy.types.Material:
    if kind == "white":
        return make_shader_shelves_white(name="DeskTop_White")
    elif kind == "black_wood":
        return make_shader_shelves_black_wood(name="DeskTop_BlackWood")
    raise NotImplementedError(kind)


def _get_leg_material(kind: str) -> bpy.types.Material:
    if kind == "white":
        return make_shader_shelves_white_metallic(name="DeskLeg_WhiteMetallic")
    elif kind == "black":
        return make_shader_shelves_black_metallic(name="DeskLeg_BlackMetallic")
    raise NotImplementedError(kind)


def int_hash(x, mod=(2**32 - 1)):
    m = hashlib.md5()
    for s in (x if isinstance(x, (tuple, list)) else [x]):
        m.update(str(s).encode('utf-8'))
    return abs(int(m.hexdigest(), 16)) % mod


def apply_transform(obj, loc=False, rot=True, scale=True):
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    obj.select_set(False)
    return obj


def _add_box(bm, sx, sy, sz, cx, cy, cz):
    if sx <= 0 or sy <= 0 or sz <= 0:
        return []
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    v = [
        bm.verts.new((cx - hx, cy - hy, cz - hz)),
        bm.verts.new((cx + hx, cy - hy, cz - hz)),
        bm.verts.new((cx + hx, cy + hy, cz - hz)),
        bm.verts.new((cx - hx, cy + hy, cz - hz)),
        bm.verts.new((cx - hx, cy - hy, cz + hz)),
        bm.verts.new((cx + hx, cy - hy, cz + hz)),
        bm.verts.new((cx + hx, cy + hy, cz + hz)),
        bm.verts.new((cx - hx, cy + hy, cz + hz)),
    ]
    faces = []
    for f in [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
              (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]:
        try:
            faces.append(bm.faces.new([v[i] for i in f]))
        except ValueError:
            pass
    return faces


def _add_cylinder(bm, radius, depth, cx, cy, cz, segments=64):
    """Z-axis cylinder centered at (cx, cy, cz), length `depth`."""

    if radius <= 0 or depth <= 0:
        return []
    half = depth / 2.0
    lo, hi = [], []
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        c, s = math.cos(theta), math.sin(theta)
        lo.append(bm.verts.new((cx + radius * c, cy + radius * s, cz - half)))
        hi.append(bm.verts.new((cx + radius * c, cy + radius * s, cz + half)))
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        try:
            faces.append(bm.faces.new([lo[i], lo[j], hi[j], hi[i]]))
        except ValueError:
            pass
    try:
        faces.append(bm.faces.new(list(reversed(lo))))
    except ValueError:
        pass
    try:
        faces.append(bm.faces.new(hi))
    except ValueError:
        pass
    return faces


def _bmesh_to_obj(bm, name):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def build_desk_parts(params):
    """Build the desk as TWO separate objects — top panel and legs — so each
    can receive its own material slot before joining.

    Returns (top_obj, legs_obj).
    """

    width = params["width"]
    depth = params["depth"]
    height = params["height"]
    thickness = params["thickness"]
    leg_radius = params["leg_radius"]
    leg_dist = params["leg_dist"]

    # --- Top panel -------------------------------------------------------
    bm_top = bmesh.new()
    _add_box(bm_top, width, depth, thickness,
             0.0, 0.0, height - thickness / 2.0)
    top_obj = _bmesh_to_obj(bm_top, "simple_desk_top")

    # --- Legs ------------------------------------------------------------
    bm_legs = bmesh.new()
    leg_depth = height - thickness
    leg_cz = leg_depth / 2.0
    x_off = width / 2.0 - leg_dist
    y_off = depth / 2.0 - leg_dist
    for sx in (-1, 1):
        for sy in (-1, 1):
            _add_cylinder(bm_legs, leg_radius, leg_depth,
                          sx * x_off, sy * y_off, leg_cz, segments=64)
    legs_obj = _bmesh_to_obj(bm_legs, "simple_desk_legs")

    return top_obj, legs_obj


def join_objs(objs):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


class AssetFactory:
    def __init__(self, factory_seed, coarse=False):
        self.factory_seed = int(factory_seed)

    def create_asset(self, i=0, **params):
        raise NotImplementedError

    def __call__(self, i=0, **kwargs):
        py_state, np_state = random.getstate(), np.random.get_state()
        derived = int_hash((self.factory_seed, i))
        random.seed(derived)
        np.random.seed(derived)
        try:
            return self.create_asset(i=i, **kwargs)
        finally:
            random.setstate(py_state)
            np.random.set_state(np_state)


class SimpleDeskBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params=None, coarse=False):
        super().__init__(factory_seed, coarse=coarse)
        self.params = dict(params) if params else {}

    def sample_params(self):
        return self.params.copy()

    def get_asset_params(self, i=0):
        params = self.sample_params()
        if params.get("depth", None) is None:
            params["depth"] = float(np.clip(normal(0.6, 0.05), 0.45, 0.7))
        if params.get("width", None) is None:
            params["width"] = float(np.clip(normal(1.0, 0.1), 0.7, 1.3))
        if params.get("height", None) is None:
            params["height"] = float(np.clip(normal(0.73, 0.05), 0.6, 0.83))
        if params.get("top_material", None) is None:
            params["top_material"] = str(np.random.choice(["white", "black_wood"]))
        if params.get("leg_material", None) is None:
            params["leg_material"] = str(np.random.choice(["white", "black"]))
        if params.get("leg_radius", None) is None:
            params["leg_radius"] = float(uniform(0.01, 0.025))
        if params.get("leg_dist", None) is None:
            params["leg_dist"] = float(uniform(0.035, 0.07))
        if params.get("thickness", None) is None:
            params["thickness"] = float(uniform(0.01, 0.03))
        return params

    def create_asset(self, i=0, **kwargs):
        obj_params = self.get_asset_params(i)

        top_obj, legs_obj = build_desk_parts(obj_params)

        # Nodes.SetMaterial on the TableTop / TableLegs subtrees).
        top_mat = _get_top_material(obj_params["top_material"])
        leg_mat = _get_leg_material(obj_params["leg_material"])
        top_obj.data.materials.append(top_mat)
        legs_obj.data.materials.append(leg_mat)

        obj = join_objs([top_obj, legs_obj])
        # Original GeoNodes applied a +90° Z rotation; replicate it.
        obj.rotation_euler = (0.0, 0.0, math.pi / 2.0)
        apply_transform(obj, rot=True)

        if kwargs.get("ret_params", False):
            return obj, obj_params
        return obj


class SimpleDeskFactory(SimpleDeskBaseFactory):
    def sample_params(self):
        params = dict()
        params["Dimensions"] = (
            uniform(0.5, 0.75),
            uniform(0.8, 2.0),
            uniform(0.6, 0.8),
        )
        params["depth"] = params["Dimensions"][0]
        params["width"] = params["Dimensions"][1]
        params["height"] = params["Dimensions"][2]
        return params



def _clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)


def build(seed=0):
    seed = int(seed)
    _clear_scene()
    derived = int_hash((seed, 0))
    random.seed(derived)
    np.random.seed(derived)
    fac = SimpleDeskFactory(seed)
    return fac.create_asset(i=0)


SEED = int(os.environ.get("SEED", "0"))
build(SEED)
