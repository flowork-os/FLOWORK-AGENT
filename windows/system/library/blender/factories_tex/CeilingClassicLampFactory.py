# [FL_INDEX: keywords="blender_factory, procedural_3d, CeilingClassicLampFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CeilingClassicLampFactory | Category: factories_tex
# Prompt: A 3D model of a classic ceiling pendant lamp rendered from a slightly elevated perspective, featuring a translucent pinkish-white fabric shade with elegant draped folds and scalloped edges, suspended from a dark vertical rod with a thin wire frame visible at the top of the shade.

import os
SEED = int(os.environ.get('SEED', 0))
import math
import random

import bmesh
import bpy
import numpy as np

SEED = int(os.environ.get("SEED", 0))
random.seed(SEED)
np.random.seed(SEED)

# ── scene helpers ─────────────────────────────────────────────────────────────

import os as _os, random as _random, colorsys as _colorsys


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

def make_category_mat(seed, name="LampMaterial"):
    """Port of ceiling_classic_lamp.py:shader_lamp_material."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    textile_hsv = (
        float(np.random.uniform(0, 1)),
        float(np.random.uniform(0.15, 0.7)),
        float(np.random.uniform(0.1, 0.3)),
    )
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = _hsv2rgba(*textile_hsv)
    if "Subsurface Radius" in principled.inputs:
        principled.inputs["Subsurface Radius"].default_value = (0.1, 0.1, 0.1)
    principled.inputs["Roughness"].default_value = float(np.random.uniform(0.2, 0.9))
    if "Sheen Weight" in principled.inputs:
        principled.inputs["Sheen Weight"].default_value = 0.2068
    if "Coat Roughness" in principled.inputs:
        principled.inputs["Coat Roughness"].default_value = 0.1436
    if "Transmission Weight" in principled.inputs:
        principled.inputs["Transmission Weight"].default_value = 0.4045
    if "Emission Color" in principled.inputs:
        principled.inputs["Emission Color"].default_value = (0.9858, 0.9858, 0.9858, 1.0)
    if "Emission Strength" in principled.inputs:
        principled.inputs["Emission Strength"].default_value = 0.0
    if "Alpha" in principled.inputs:
        principled.inputs["Alpha"].default_value = 0.8614

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        voronoi.feature = "SMOOTH_F1"
    except Exception:
        pass
    voronoi.inputs["Scale"].default_value = 104.3
    voronoi.inputs["Randomness"].default_value = 0.0
    ln(tex_coord.outputs["Object"], voronoi.inputs["Vector"])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Scale"].default_value = 0.4
    ln(voronoi.outputs.get("Distance") or voronoi.outputs[0], disp.inputs["Height"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(principled.outputs["BSDF"], out.inputs["Surface"])
    ln(disp.outputs["Displacement"], out.inputs["Displacement"])
    return mat

def make_inside_metal_mat(name="CeilingClassicInsideMetal"):
    """Port of ceiling_classic_lamp.py:shader_inside_metal."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.0018, 0.0015, 0.0, 1.0)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.0682
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_cable_mat(name="CeilingClassicCable"):
    """Port of ceiling_classic_lamp.py:shader_cable."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.4273
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_bulb_nonemissive_mat(name="CeilingClassicBulb"):
    """Port of lamp_shaders.py:shader_lamp_bulb_nonemissive."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    light_path = nt.nodes.new("ShaderNodeLightPath")
    obj_info = nt.nodes.new("ShaderNodeObjectInfo")
    white_noise = nt.nodes.new("ShaderNodeTexWhiteNoise")
    try:
        white_noise.noise_dimensions = "4D"
    except Exception:
        pass
    ln(obj_info.outputs["Random"], white_noise.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.9
    ln(white_noise.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (0.5, 0.4444, 0.3669, 1.0)
    transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    ln(mix.outputs[2], transparent.inputs["Color"])
    ln(mix.outputs[2], translucent.inputs["Color"])
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    ln(light_path.outputs["Is Camera Ray"], mix_shader.inputs["Fac"])
    ln(transparent.outputs["BSDF"], mix_shader.inputs[1])
    ln(translucent.outputs["BSDF"], mix_shader.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_shader.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_metal_mat(seed, name="LampMetal", dark=False):
    """Brushed-metal shader"""

    roughness_val = float(np.random.uniform(0.15, 0.45))
    bump_scale = float(np.random.uniform(15.0, 40.0))
    bump_strength = float(np.random.uniform(0.05, 0.15))
    if dark:
        hue = float(np.random.uniform(0.0, 0.1))
        sat = float(np.random.uniform(0.0, 0.2))
        val = float(np.random.uniform(0.04, 0.12))
    else:
        hue = float(np.random.uniform(0.05, 0.12))
        sat = float(np.random.uniform(0.0, 0.15))
        val = float(np.random.uniform(0.55, 0.85))
    base_color = _hsv2rgba(hue, sat, val)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = bump_scale
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.001
    ln(noise.outputs[0], bump.inputs["Height"])
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Metallic"].default_value = 1.0
    principled.inputs["Roughness"].default_value = roughness_val
    ln(bump.outputs[0], principled.inputs["Normal"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(principled.outputs["BSDF"], out.inputs["Surface"])
    return mat

LAMPSHADE_MAT = make_category_mat(SEED, "CeilingClassicLampFactory_Lampshade")
LAMPSHADE_MAT.use_fake_user = True
CATEG_MAT = LAMPSHADE_MAT  # backward-compat alias

_saved_state = np.random.get_state()
METAL_BLACK_MAT = make_metal_mat(SEED, "CeilingClassicBlackMetal", dark=True)
METAL_MAT       = make_metal_mat(SEED, "CeilingClassicMetal", dark=False)
CABLE_MAT = make_cable_mat("CeilingClassicCable")
INSIDE_METAL_MAT = make_inside_metal_mat("CeilingClassicInsideMetal")
BULB_MAT = make_bulb_nonemissive_mat("CeilingClassicBulb")
METAL_BLACK_MAT.use_fake_user = True
METAL_MAT.use_fake_user = True
for _mat in (CABLE_MAT, INSIDE_METAL_MAT, BULB_MAT):
    _mat.use_fake_user = True
np.random.set_state(_saved_state)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def add_mod(obj, mtype, **kw):
    m = obj.modifiers.new("", mtype)
    for k, v in kw.items():
        setattr(m, k, v)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

# ── swept tube utility ────────────────────────────────────────────────────────

def build_swept_tube(path_pts, radii, n_circ=12, name="tube", caps=True):
    """Sweep a circle along path_pts with per-point radii."""

    n_pts = len(path_pts)
    if isinstance(radii, (int, float)):
        radii = [radii] * n_pts
    bm = bmesh.new()
    rings = []

    prev_right = None
    for i in range(n_pts):
        if i == 0:
            tan = path_pts[1] - path_pts[0]
        elif i == n_pts - 1:
            tan = path_pts[-1] - path_pts[-2]
        else:
            tan = path_pts[i + 1] - path_pts[i - 1]
        tl = np.linalg.norm(tan)
        if tl < 1e-10:
            tan = np.array([0.0, 0.0, 1.0])
        else:
            tan = tan / tl

        # Stable orthonormal frame with minimal twist
        if prev_right is None:
            up = np.array([0.0, 0.0, 1.0]) if abs(tan[2]) < 0.99 else np.array([1.0, 0.0, 0.0])
            right = np.cross(tan, up)
        else:
            right = prev_right - np.dot(prev_right, tan) * tan
        rl = np.linalg.norm(right)
        if rl < 1e-10:
            up = np.array([0.0, 0.0, 1.0]) if abs(tan[2]) < 0.99 else np.array([1.0, 0.0, 0.0])
            right = np.cross(tan, up)
            rl = np.linalg.norm(right)
        right /= rl
        up2 = np.cross(right, tan)
        prev_right = right

        r = radii[i]
        ring = []
        for j in range(n_circ):
            theta = 2 * math.pi * j / n_circ
            offset = right * math.cos(theta) * r + up2 * math.sin(theta) * r
            pos = path_pts[i] + offset
            ring.append(bm.verts.new(pos.tolist()))
        rings.append(ring)

    for i in range(n_pts - 1):
        for j in range(n_circ):
            j2 = (j + 1) % n_circ
            bm.faces.new([rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]])

    if caps:
        center_bot = bm.verts.new(path_pts[0].tolist())
        for j in range(n_circ):
            j2 = (j + 1) % n_circ
            bm.faces.new([center_bot, rings[0][j2], rings[0][j]])
        center_top = bm.verts.new(path_pts[-1].tolist())
        for j in range(n_circ):
            j2 = (j + 1) % n_circ
            bm.faces.new([center_top, rings[-1][j], rings[-1][j2]])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_tf(obj)
    return obj

# ── cable ─────────────────────────────────────────────────────────────────────

def build_cable(cable_length, cable_radius):
    """

    Thin vertical cylinder from z=0 to z=-cable_length.
    Resolution 87 matching CurveCircle resolution.
    """

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=87, radius=cable_radius, depth=cable_length,
        location=(0, 0, -cable_length * 0.5)
    )
    cable = bpy.context.active_object
    apply_tf(cable)
    return cable

# ── wire rack ─────────────────────────────────────────────────────────────────

def build_rack(outer_z, inner_z, outer_radius, inner_radius, rod_radius, n_spokes):
    """

    Wire rack with diagonal spokes.
    Outer ring at outer_z with outer_radius (shade narrow top).
    Inner ring at inner_z with inner_radius (cable bottom).
    Spokes connect them diagonally.
    inner CurveCircle(Thickness) at Z=0, duplicated lines connecting them,
    all swept with CurveCircle(Thickness) profile + Fill Caps.
    """

    if n_spokes < 1:
        return None

    parts = []

    # Outer ring (torus at outer_z)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=outer_radius, minor_radius=rod_radius,
        major_segments=64, minor_segments=8,
        location=(0, 0, outer_z)
    )
    outer_ring = bpy.context.active_object
    apply_tf(outer_ring)
    parts.append(outer_ring)

    # Inner ring (torus at inner_z)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=inner_radius, minor_radius=rod_radius,
        major_segments=24, minor_segments=8,
        location=(0, 0, inner_z)
    )
    inner_ring = bpy.context.active_object
    apply_tf(inner_ring)
    parts.append(inner_ring)

    # Diagonal spokes connecting inner ring (cable bottom) to outer ring (shade top)
    for i in range(n_spokes):
        angle = 2 * math.pi * i / n_spokes
        x0 = inner_radius * math.cos(angle)
        y0 = inner_radius * math.sin(angle)
        z0 = inner_z
        x1 = outer_radius * math.cos(angle)
        y1 = outer_radius * math.sin(angle)
        z1 = outer_z

        p0 = np.array([x0, y0, z0])
        p1 = np.array([x1, y1, z1])
        n_seg = 6
        path = np.array([p0 + (p1 - p0) * t / n_seg for t in range(n_seg + 1)])
        spoke = build_swept_tube(path, rod_radius, n_circ=8, name=f"spoke_{i}", caps=True)
        parts.append(spoke)

    return join_objs(parts)

# ── lampshade ─────────────────────────────────────────────────────────────────

def build_lampshade(narrow_z, wide_z, top_radius, bottom_radius,
                    n_spokes, spoke_angles):
    """

    Pleated/draped truncated cone lampshade with thin-shell walls.

    narrow_z: z of narrow end (top_radius, near cable)
    wide_z: z of wide end (bottom_radius, bottom opening)
    n_spokes: number of wire rack spokes
    spoke_angles: angular positions of spokes [radians]

    Approximates the Voronoi SMOOTH_F1 displacement (Scale=104.3,
    Displacement=0.4) as sinusoidal radial pleats deepening toward bottom,
    with pointed peaks between spokes at the top edge, and an irregular
    bottom edge.
    """

    n_sides = 128
    n_rows = 56

    shade_height = narrow_z - wide_z
    n_pleats = max(n_spokes * 2, 8)

    # Peak height relative to shade height (fabric bunching between spokes)
    peak_height = shade_height * 0.12

    bm = bmesh.new()
    rows = []

    for i in range(n_rows + 1):
        t = i / n_rows  # 0=top, 1=bottom

        # Z from (narrow_z + peak_height) down to wide_z
        total_span = shade_height + peak_height
        z_base = (narrow_z + peak_height) - t * total_span

        # Radius: linear interpolation from top_radius to bottom_radius
        base_r = top_radius + t * (bottom_radius - top_radius)

        # Pleat amplitude: relative to current radius, deepens toward bottom
        pleat_frac = 0.15 * (0.1 + 0.9 * t * t)

        row = []
        for j in range(n_sides):
            theta = 2 * math.pi * j / n_sides

            # Primary sinusoidal pleat
            primary = math.sin(n_pleats * theta + 0.3)
            # Secondary harmonic for irregularity
            secondary = 0.3 * math.sin(n_pleats * 2 * theta + 1.7)
            pleat = pleat_frac * (primary + secondary) / 1.3
            r = base_r * (1.0 + pleat)

            z_off = 0.0

            # Top edge peaks: fabric extends above wire rack between spokes
            if t < 0.18 and n_spokes > 0:
                min_spoke_dist = math.pi
                for sa in spoke_angles:
                    d = abs(theta - sa)
                    d = min(d, 2 * math.pi - d)
                    min_spoke_dist = min(min_spoke_dist, d)
                spoke_gap = math.pi / max(n_spokes, 1)
                peak_factor = min(min_spoke_dist / spoke_gap, 1.0)
                peak_factor = peak_factor ** 0.5  # sharpen peaks more
                edge_blend = 1.0 - t / 0.18
                z_off = peak_height * peak_factor * edge_blend
                # Pull radius inward near the ring (gathered fabric effect)
                r *= (1.0 - 0.25 * edge_blend * (1.0 - peak_factor))

            # Bottom edge irregularity: uneven draping (deeper hanging)
            if t > 0.75:
                edge_factor = (t - 0.75) / 0.25
                wave = 0.5 + 0.5 * math.sin(n_pleats * theta * 0.7 + 1.2)
                wave2 = 0.3 * math.sin(n_pleats * 0.5 * theta + 2.5)
                z_off -= shade_height * 0.12 * edge_factor * (wave + wave2) / 1.3

            row.append(bm.verts.new((
                r * math.cos(theta),
                r * math.sin(theta),
                z_base + z_off
            )))
        rows.append(row)

    # Create quad faces
    for i in range(n_rows):
        for j in range(n_sides):
            j2 = (j + 1) % n_sides
            bm.faces.new([rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]])

    mesh = bpy.data.meshes.new("shade")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("shade", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    apply_tf(obj)
    # Thin shell (matches FlipFaces + ExtrudeMesh 0.005)
    add_mod(obj, "SOLIDIFY", thickness=0.005, offset=0)
    return obj

# ── bulb ──────────────────────────────────────────────────────────────────────

def build_bulb(pos, radius=0.05):
    """IcoSphere bulb at position. Subdivisions=4"""

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=4, radius=radius, location=pos
    )
    bulb = bpy.context.active_object
    apply_tf(bulb)
    return bulb

# ── parameter sampling ────────────────────────────────────────────────────────

def sample_parameters():
        return {
        "cable_length": float(np.random.uniform(0.6, 0.71)),
        "cable_radius": float(np.random.uniform(0.015, 0.02)),
        "height": float(np.random.uniform(0.4, 0.71)),
        "top_radius": float(np.random.uniform(0.05, 0.2)),
        "bottom_radius": float(np.random.uniform(0.22, 0.35)),
        "Thickness": float(np.random.uniform(0.002, 0.006)),
        "Amount": int(np.random.randint(1, 8)),
    }

# ── main ──────────────────────────────────────────────────────────────────────

def build_ceiling_classic_lamp():
    np.random.seed(SEED)
    clear_scene()

    p = sample_parameters()

    cable_len = p["cable_length"]
    height = p["height"]
    top_r = p["top_radius"]
    bot_r = p["bottom_radius"]
    thickness = p["Thickness"]
    n_spokes = p["Amount"]

    # Key Z positions (from geometry_nodes analysis):
    # All relative to cable_length and height parameters
    cable_bot_z = -cable_len
    # Shade narrow end = cable bottom + height/2  (shade wraps above cable bottom)
    shade_narrow_z = cable_bot_z + height * 0.5
    shade_wide_z = cable_bot_z - 0.15
    # Rack outer ring matches shade narrow end
    rack_outer_z = shade_narrow_z
    # Rack inner ring at cable bottom
    rack_inner_z = cable_bot_z
    # Bulb at cable bottom (inside shade)
    bulb_z = cable_bot_z

    # Spoke angular positions (evenly distributed)
    spoke_angles = [2 * math.pi * i / n_spokes for i in range(n_spokes)]

    parts = []

    # 1. Cable → metal
    cable = build_cable(cable_len, p["cable_radius"])
    cable.data.materials.append(CABLE_MAT)
    parts.append(cable)

    # 2. Wire rack → metal
    rack = build_rack(
        outer_z=rack_outer_z,
        inner_z=rack_inner_z,
        outer_radius=top_r,
        inner_radius=thickness * 3,
        rod_radius=thickness,
        n_spokes=n_spokes
    )
    if rack:
        rack.data.materials.append(INSIDE_METAL_MAT)
        parts.append(rack)

    # 3. Lampshade → lampshade shader (translucent)
    shade = build_lampshade(
        narrow_z=shade_narrow_z,
        wide_z=shade_wide_z,
        top_radius=top_r,
        bottom_radius=bot_r,
        n_spokes=n_spokes,
        spoke_angles=spoke_angles
    )
    shade.data.materials.append(LAMPSHADE_MAT)
    parts.append(shade)

    # 4. Bulb → non-emissive bulb shader
    bulb = build_bulb((0, 0, bulb_z), radius=0.05)
    bulb.data.materials.append(BULB_MAT)
    parts.append(bulb)

    result = join_objs(parts)
    apply_tf(result)
    # Per-part materials were appended before join; slots preserved automatically.
    if result is not None and len(result.data.materials) == 0:
        result.data.materials.append(LAMPSHADE_MAT)
    return result

lamp = build_ceiling_classic_lamp()
lamp.name = "CeilingClassicLampFactory"

