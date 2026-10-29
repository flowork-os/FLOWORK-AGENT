# [FL_INDEX: keywords="blender_factory, procedural_3d, GrassTuftFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: GrassTuftFactory | Category: factories_geo
# Prompt: A 3D model of a tuft of grass rendered from a slightly elevated perspective, featuring numerous long, narrow dark green blades growing outward and upward from a central base, with the blades arching and curving naturally to form a compact clump of grass.

import os
SEED = int(os.environ.get("SEED", "0"))
import random

import bpy
import numpy as np

random.seed(SEED)
np.random.seed(SEED)

# ── scene helpers ─────────────────────────────────────────────────────────────


import random as _random, colorsys as _colorsys

def _seed_mat(seed):
    _s = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s); _random.seed(_s)

def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h)%1, max(0,min(1,float(s))), max(0,min(1,float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear()
    return m

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def make_category_mat(seed, name="GreeneryMaterial"):
    _seed_mat(seed)
    base_hue = float(np.random.uniform(0.22, 0.38))
    green_c = _hsv2rgba(base_hue, np.random.uniform(0.5, 0.9), np.random.uniform(0.08, 0.3))
    light_c = _hsv2rgba(base_hue + float(np.random.uniform(-0.05, 0.05)),
                         np.random.uniform(0.3, 0.6), np.random.uniform(0.15, 0.4))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.noise_dimensions = "4D"
    ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = float(np.random.uniform(-2, 2))
    noise.inputs["Scale"].default_value = float(np.random.uniform(5, 15))
    noise.inputs["Detail"].default_value = 5.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.color_mode = "HSV"
    cr.color_ramp.hue_interpolation = "NEAR"
    ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = green_c
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = light_c
    # Translucent + Principled mix (matches simple_greenery 60-90% translucent)
    trans = nt.nodes.new("ShaderNodeBsdfTranslucent"); ln(cr.outputs["Color"], trans.inputs["Color"])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.4, 0.8))
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = float(np.random.uniform(0.6, 0.9))
    ln(bsdf.outputs["BSDF"], mix.inputs[1]); ln(trans.outputs["BSDF"], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix.outputs["Shader"], out.inputs["Surface"])
    return mat

CATEG_MAT = make_category_mat(SEED, "GrassTuftFactory_Material")
CATEG_MAT.use_fake_user = True

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def build_nurbs_curve(points_2d, taper_obj, extrude_width, name="blade"):
    """

    Create a NURBS curve object from 2D points with bevel_depth (circular
    cross-section) and a taper object controlling width along the curve.
    Endpoints are doubled for sharp NURBS ends (pinning).

    Matches: Curve(points, taper=taper).to_curve_obj(extrude=width, resu=2)
    """

    curve_data = bpy.data.curves.new(f"{name}_curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 2
    curve_data.use_fill_caps = True
    curve_data.twist_mode = "MINIMUM"
    curve_data.bevel_depth = extrude_width

    if taper_obj is not None:
        curve_data.taper_object = taper_obj

    spline = curve_data.splines.new("NURBS")

    # Build points list with doubled endpoints for sharp NURBS ends
    pts = []
    for i, p in enumerate(points_2d):
        x, y = float(p[0]), float(p[1])
        pts.append((x, y, 0.0, 1.0))
        # Double first and last points for sharp ends
        if i == 0 or i == len(points_2d) - 1:
            pts.append((x, y, 0.0, 1.0))

    # Set spline points
    spline.points.add(len(pts) - 1)  # spline starts with 1 point
    for i, co in enumerate(pts):
        spline.points[i].co = co

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def build_taper_curve(taper_points, name="taper"):
    """

    Build a taper curve object from (x, y) control points.
    Blender uses the taper curve's Y values at each normalized X position
    to scale the bevel cross-section radius.

    Matches: Curve(taper_points).to_curve_obj()
    """

    curve_data = bpy.data.curves.new(f"{name}_curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 4
    curve_data.twist_mode = "MINIMUM"

    spline = curve_data.splines.new("NURBS")

    # Build with doubled endpoints
    pts = []
    for i, p in enumerate(taper_points):
        x, y = float(p[0]), float(p[1])
        pts.append((x, y, 0.0, 1.0))
        if i == 0 or i == len(taper_points) - 1:
            pts.append((x, y, 0.0, 1.0))

    spline.points.add(len(pts) - 1)
    for i, co in enumerate(pts):
        spline.points[i].co = co

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def curve_to_mesh(obj):
    """Convert a curve object to mesh."""

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    return obj

# ── grass tuft builder ────────────────────────────────────────────────────────

def build_grass_tuft():
    np.random.seed(SEED)
    clear_scene()

    # Parameters from GrassTuftFactory.__init__ (matches source exactly)
    n_seg = 4
    length_mean = np.random.uniform(0.05, 0.15)
    length_std = length_mean * np.random.uniform(0.2, 0.5)

    curl_mean = np.random.uniform(10, 70)
    curl_std = curl_mean * np.clip(np.random.normal(0.3, 0.1), 0.01, 0.6)
    curl_power = np.random.normal(1.2, 0.3)

    blade_width_pct_mean = np.random.uniform(0.01, 0.03)
    blade_width_var = np.random.uniform(0, 0.05)

    taper_var = np.random.uniform(0, 0.1)
    taper_y = np.linspace(1, 0, n_seg) * np.random.normal(1, taper_var, n_seg)
    taper_y = np.clip(taper_y, 0.0, 2.0)
    taper_x = np.linspace(0, 1, n_seg)
    taper_points = np.stack([taper_x, taper_y], axis=-1)

    base_spread = np.random.uniform(0, length_mean / 4)
    base_angle_var = np.random.uniform(0, 15)

    n_blades = np.random.randint(30, 60)

    # Build the shared taper curve object
    taper_obj = build_taper_curve(taper_points)

    # create_asset logic (matches source vectorized computation)
    blade_lengths = np.random.normal(length_mean, max(length_std, 1e-6), (n_blades, 1))
    seg_lens = blade_lengths / n_seg

    seg_curls = np.random.normal(curl_mean, max(curl_std, 0.1), (n_blades, n_seg))
    seg_curls *= np.power(
        np.linspace(0, 1, n_seg).reshape(1, n_seg), max(curl_power, 0.1)
    )
    seg_curls = np.deg2rad(seg_curls)

    point_rads = np.arange(n_seg).reshape(1, n_seg) * seg_lens
    point_angles = np.cumsum(seg_curls, axis=-1)
    point_angles -= point_angles[:, [0]]  # normalize: first angle = 0

    points = np.empty((n_blades, n_seg, 2))
    points[..., 0] = np.cumsum(point_rads * np.cos(point_angles), axis=-1)
    points[..., 1] = np.cumsum(point_rads * np.sin(point_angles), axis=-1)

    # Per-blade widths
    widths = blade_lengths.reshape(-1) * np.random.normal(
        blade_width_pct_mean, max(blade_width_var, 1e-6), n_blades
    )
    widths = np.abs(widths)

    # Build each blade as a NURBS curve with bevel
    objs = []
    for i in range(n_blades):
        obj = build_nurbs_curve(
            points[i], taper_obj, extrude_width=float(widths[i]),
            name=f"_blade_{i}"
        )
        objs.append(obj)

    # Convert all curves to mesh
    for obj in objs:
        curve_to_mesh(obj)

    # Delete taper object
    bpy.ops.object.select_all(action="DESELECT")
    taper_obj.select_set(True)
    bpy.ops.object.delete()

    # Randomly pose and arrange the blades in a circle-ish cluster
    base_angles = np.random.uniform(0, 2 * np.pi, n_blades)
    base_rads = np.random.uniform(0, base_spread, n_blades)
    facing_offsets = np.deg2rad(np.random.normal(0, base_angle_var, n_blades))

    for a, r, off, obj in zip(base_angles, base_rads, facing_offsets, objs):
        obj.location = (-r * np.cos(a), r * np.sin(a), -0.05 * length_mean)
        obj.rotation_euler = (np.pi / 2, -np.pi / 2, -a + off)

    # Apply transforms
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Join all blades
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()

    result = bpy.context.active_object
    result.data.materials.clear()
    result.data.materials.append(CATEG_MAT)

    result.name = "GrassTuftFactory"
    return result

tuft = build_grass_tuft()
