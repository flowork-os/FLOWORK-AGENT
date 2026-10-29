# [FL_INDEX: keywords="blender_factory, procedural_3d, LampFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LampFactory | Category: factories_tex
# Prompt: A 3D model of a standing lamp rendered from a slightly elevated three-quarter perspective, featuring a tapered conical off-white fabric shade at the top, a tall slender dark pole, a small circular tray element mounted partway up the pole, and a dark round base at the bottom.

import os
SEED = int(os.environ.get('SEED', 0))
import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import Vector

SEED = int(os.environ.get("SEED", 0))
random.seed(SEED)
np.random.seed(SEED)

# ── helpers ──────────────────────────────────────────────────────────────────

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
    """Lamp shade shader: LightPath-conditional mix of Principled and Translucent.
    Base color = white-noise-mixed hardcoded tan (0.5, 0.4444, 0.3669)."""
    # Sample parameters exactly as (matches RNG consumption order)
    noise_scale = float(np.random.uniform(1.0, 5.0))
    subsurface_weight = float(np.random.uniform(0.03, 0.08))
    roughness_val = float(np.random.uniform(0.5, 0.8))
    transmission_weight = float(np.random.uniform(0.05, 0.2))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    # TexCoord -> Noise -> fac
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    ln(texcoord.outputs["Generated"], noise.inputs["Vector"])

    # MixRGB: factor=0.9, A=white, B=tan, driven by noise fac
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.blend_type = "MIX"
    mix.inputs[0].default_value = 0.9
    # Use noise fac (named "Fac" in 4.x, "Factor" in 5.x)
    ln(_fac(noise), mix.inputs[0])
    mix.inputs[6].default_value = (1.0, 1.0, 1.0, 1.0)
    mix.inputs[7].default_value = (0.5, 0.4444, 0.3669, 1.0)

    # Principled BSDF (camera ray branch)
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix.outputs[2], principled.inputs["Base Color"])
    if "Subsurface Weight" in principled.inputs:
        principled.inputs["Subsurface Weight"].default_value = subsurface_weight
    elif "Subsurface" in principled.inputs:
        principled.inputs["Subsurface"].default_value = subsurface_weight
    principled.inputs["Roughness"].default_value = roughness_val
    if "Transmission Weight" in principled.inputs:
        principled.inputs["Transmission Weight"].default_value = transmission_weight
    elif "Transmission" in principled.inputs:
        principled.inputs["Transmission"].default_value = transmission_weight
    if "IOR" in principled.inputs:
        principled.inputs["IOR"].default_value = 4.0

    # Translucent BSDF (non-camera ray branch); no Roughness socket on this node
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    ln(mix.outputs[2], translucent.inputs["Color"])

    # LightPath -> MixShader (Fac=Is Camera Ray; slot1=Principled, slot2=Translucent)
    light_path = nt.nodes.new("ShaderNodeLightPath")
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    ln(light_path.outputs["Is Camera Ray"], mix_shader.inputs[0])
    ln(principled.outputs["BSDF"], mix_shader.inputs[1])
    ln(translucent.outputs["BSDF"], mix_shader.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_shader.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_metal_mat(seed, name="LampMetal", dark=False):
    """Brushed-metal shader's material_assignments.furniture_leg pool.
    Faithful-ish port of shader_brushed_metal: Principled BSDF with metallic=1, low roughness,
    slight color variation and bump noise."""

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

LAMPSHADE_MAT = make_category_mat(SEED, "LampFactory_Lampshade")
LAMPSHADE_MAT.use_fake_user = True
CATEG_MAT = LAMPSHADE_MAT  # backward-compat alias

# Save/restore np.random state around metal material creation so wear_tear
# gates below still consume from the post-lampshade state.
_saved_state = np.random.get_state()
METAL_BLACK_MAT = make_metal_mat(SEED, "LampBlackMetal", dark=True)
METAL_MAT       = make_metal_mat(SEED, "LampMetal", dark=False)
METAL_BLACK_MAT.use_fake_user = True
METAL_MAT.use_fake_user = True
np.random.set_state(_saved_state)

# --- wear_tear probability gates (mirror finalize_assets) ---
# Sampled here (module level) AFTER material sampling and BEFORE build(),
WEAR_DO_SCRATCH  = (np.random.uniform() <= 0.5)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= 0.5)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def eval_curve(pts, t):
    """Piecewise-linear interpolation of control points [(x,y), ...]."""

    if t <= pts[0][0]:
        return pts[0][1]
    if t >= pts[-1][0]:
        return pts[-1][1]
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        if x0 <= t <= x1:
            return y0 + (y1 - y0) * (t - x0) / max(x1 - x0, 1e-10)
    return pts[-1][1]

# ── swept tube (core geometry utility) ───────────────────────────────────────

def build_swept_tube(path, radii, n_circ=64, name="tube", caps=True):
    """

    Sweep a circle along path with per-point radii.
    path: list of 3-tuples
    radii: list of float (len == len(path)), or single float
    """

    bm = bmesh.new()
    n = len(path)
    pts = [np.array(p, dtype=float) for p in path]
    if isinstance(radii, (int, float)):
        radii = [float(radii)] * n

    # Tangents
    tangs = []
    for i in range(n):
        if i == 0:
            t = pts[min(1, n - 1)] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[max(-2, -n)]
        else:
            t = pts[i + 1] - pts[i - 1]
        tn = np.linalg.norm(t)
        tangs.append(t / tn if tn > 1e-10 else np.array([0, 0, 1]))

    # Reference vector for frame
    ref = np.array([1.0, 0, 0])
    if all(abs(np.dot(t, ref)) > 0.95 for t in tangs):
        ref = np.array([0, 1.0, 0])

    rings = []
    prev_nv = None
    for i in range(n):
        t = tangs[i]
        nv = ref - np.dot(ref, t) * t
        nn = np.linalg.norm(nv)
        if nn > 1e-10:
            nv /= nn
        else:
            nv = np.cross(t, np.array([0, 0, 1]))
            nn2 = np.linalg.norm(nv)
            nv = nv / nn2 if nn2 > 1e-10 else np.array([0, 1, 0])

        # Minimize twist by projecting previous normal
        if prev_nv is not None:
            proj = prev_nv - np.dot(prev_nv, t) * t
            pn = np.linalg.norm(proj)
            if pn > 1e-10:
                nv = proj / pn

        bv = np.cross(t, nv)
        bn = np.linalg.norm(bv)
        if bn > 1e-10:
            bv /= bn
        prev_nv = nv

        r = radii[i]
        ring = []
        if r < 1e-7:
            v = bm.verts.new(tuple(pts[i]))
            ring = [v] * n_circ
        else:
            for j in range(n_circ):
                theta = 2 * math.pi * j / n_circ
                off = r * (math.cos(theta) * nv + math.sin(theta) * bv)
                ring.append(bm.verts.new(tuple(pts[i] + off)))
        rings.append(ring)

    # Quad faces
    for i in range(n - 1):
        for j in range(n_circ):
            j2 = (j + 1) % n_circ
            vs = [rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]]
            unique = list(dict.fromkeys(vs))
            if len(unique) >= 3:
                try:
                    bm.faces.new(unique)
                except ValueError:
                    pass

    if caps:
        if radii[0] > 1e-7:
            c = bm.verts.new(tuple(pts[0]))
            for j in range(n_circ):
                j2 = (j + 1) % n_circ
                try:
                    bm.faces.new([c, rings[0][j2], rings[0][j]])
                except ValueError:
                    pass
        if radii[-1] > 1e-7:
            c = bm.verts.new(tuple(pts[-1]))
            for j in range(n_circ):
                j2 = (j + 1) % n_circ
                try:
                    bm.faces.new([c, rings[-1][j], rings[-1][j2]])
                except ValueError:
                    pass

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj

# ── cubic Bezier ─────────────────────────────────────────────────────────────

def cubic_bezier_pts(S, H1, H2, E, n=100):
    """Sample n+1 points on cubic Bezier."""

    S, H1, H2, E = [np.array(p) for p in [S, H1, H2, E]]
    ts = np.linspace(0, 1, n + 1)
    return [tuple((1 - t) ** 3 * S + 3 * (1 - t) ** 2 * t * H1 +
                  3 * (1 - t) * t ** 2 * H2 + t ** 3 * E) for t in ts]

def cubic_bezier_tangent(S, H1, H2, E, t):
    """Tangent of cubic Bezier at parameter t."""

    S, H1, H2, E = [np.array(p) for p in [S, H1, H2, E]]
    tang = 3 * (1 - t) ** 2 * (H1 - S) + 6 * (1 - t) * t * (H2 - H1) + 3 * t ** 2 * (E - H2)
    tn = np.linalg.norm(tang)
    return tuple(tang / tn) if tn > 1e-8 else (0, 0, 1)

# ── parameters ───────────────────────────────────────────────────────────────

def sample_parameters():
    """Match LampFactory.sample_parameters (lamp_type='FloorLamp')."""

    stand_radius = float(np.random.uniform(0.005, 0.015))
    base_radius = float(np.random.uniform(0.05, 0.15))
    base_height = float(np.random.uniform(0.01, 0.03))
    shade_height = float(np.random.uniform(0.18, 0.3))
    head_top_radius = float(np.random.uniform(0.07, 0.15))
    head_bot_radius = head_top_radius + float(np.random.uniform(0, 0.05))
    rack_thickness = float(np.random.uniform(0.001, 0.003))

    # FloorLamp height
    height = float(np.random.uniform(1.0, 1.5))

    z1 = float(np.random.uniform(base_height, height))
    z2 = float(np.random.uniform(z1, height))
    z3 = height

    return {
        "StandRadius": stand_radius,
        "BaseRadius": base_radius,
        "BaseHeight": base_height,
        "ShadeHeight": shade_height,
        "HeadTopRadius": head_top_radius,
        "HeadBotRadius": head_bot_radius,
        "ReverseLamp": True,
        "RackThickness": rack_thickness,
        "CurvePoint1": (0.0, 0.0, z1),
        "CurvePoint2": (0.0, 0.0, z2),
        "CurvePoint3": (0.0, 0.0, z3),
    }

# ── component builders ──────────────────────────────────────────────────────

def build_base(base_radius, base_height):
    """Capped cylinder at ground. Matches curve_to_mesh_1 with Fill Caps."""

    path = [(0, 0, 0), (0, 0, base_height)]
    return build_swept_tube(path, base_radius, n_circ=64, name="base")

def build_stand(base_height, cp1, cp2, cp3, stand_radius):
    """

    Cubic Bezier tube + straight ground segment.
    Matches bezier_segment + curve_line, both swept with StandRadius circle.
    Returns (obj, tip_pos, tangent).
    """

    parts = []

    # Straight segment from ground to base top
    ground_path = [(0, 0, 0), (0, 0, base_height)]
    parts.append(build_swept_tube(ground_path, stand_radius, n_circ=64, name="stand_gnd"))

    # Bezier segment from base top to CP3
    start = (0, 0, base_height)
    bez_path = cubic_bezier_pts(start, cp1, cp2, cp3, n=100)
    parts.append(build_swept_tube(bez_path, stand_radius, n_circ=64, name="stand_bez"))

    stand = join_objs(parts)
    tang = cubic_bezier_tangent(start, cp1, cp2, cp3, 1.0)
    return stand, cp3, tang

def build_lampshade(shade_height, top_r, bot_r, reverse, rack_height):
    """

    Truncated cone thin shell (double-walled).
    Matches FlipFaces + ExtrudeMesh(0.005) in nodegroup_lamp_head.
    Built at origin; caller positions it.
    """

    n = 100
    thickness = 0.005

    if reverse:
        start_z = rack_height
        end_z = -(shade_height - rack_height)
    else:
        start_z = -rack_height
        end_z = shade_height - rack_height

    bm = bmesh.new()

    # Outer surface
    o_top, o_bot = [], []
    for j in range(n):
        th = 2 * math.pi * j / n
        c, s = math.cos(th), math.sin(th)
        o_top.append(bm.verts.new((top_r * c, top_r * s, start_z)))
        o_bot.append(bm.verts.new((bot_r * c, bot_r * s, end_z)))

    # Inner surface (inset by thickness along surface normal)
    dz = end_z - start_z
    dr = bot_r - top_r
    cl = math.sqrt(dz * dz + dr * dr)
    if cl > 1e-6:
        nr, nz = dz / cl, -dr / cl
    else:
        nr, nz = 1.0, 0.0

    i_top_r = max(top_r - thickness * nr, 0.001)
    i_bot_r = max(bot_r - thickness * nr, 0.001)
    i_sz = start_z - thickness * nz
    i_ez = end_z - thickness * nz

    i_top, i_bot = [], []
    for j in range(n):
        th = 2 * math.pi * j / n
        c, s = math.cos(th), math.sin(th)
        i_top.append(bm.verts.new((i_top_r * c, i_top_r * s, i_sz)))
        i_bot.append(bm.verts.new((i_bot_r * c, i_bot_r * s, i_ez)))

    for j in range(n):
        j2 = (j + 1) % n
        bm.faces.new([o_top[j], o_top[j2], o_bot[j2], o_bot[j]])      # outer
        bm.faces.new([i_top[j], i_bot[j], i_bot[j2], i_top[j2]])       # inner
        bm.faces.new([o_top[j], i_top[j], i_top[j2], o_top[j2]])       # top edge
        bm.faces.new([o_bot[j], o_bot[j2], i_bot[j2], i_bot[j]])       # bot edge

    mesh = bpy.data.meshes.new("shade")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("shade", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def build_torus_ring(major_r, minor_r, z, n_major=64, n_minor=8, name="ring"):
    """Torus ring (tube bent into circle) at z-offset."""

    bm = bmesh.new()
    rings = []
    for i in range(n_major):
        th = 2 * math.pi * i / n_major
        cx, cy = major_r * math.cos(th), major_r * math.sin(th)
        rx, ry = math.cos(th), math.sin(th)
        ring = []
        for j in range(n_minor):
            phi = 2 * math.pi * j / n_minor
            x = cx + minor_r * math.cos(phi) * rx
            y = cy + minor_r * math.cos(phi) * ry
            zz = z + minor_r * math.sin(phi)
            ring.append(bm.verts.new((x, y, zz)))
        rings.append(ring)

    for i in range(n_major):
        i2 = (i + 1) % n_major
        for j in range(n_minor):
            j2 = (j + 1) % n_minor
            bm.faces.new([rings[i][j], rings[i][j2], rings[i2][j2], rings[i2][j]])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def build_rack(top_r, rack_thickness, outer_h, inner_r, inner_h, n_spokes=3):
    """Wire rack: outer ring + inner ring + spoke tubes."""

    parts = []

    # Outer ring at z=outer_h
    parts.append(build_torus_ring(top_r, rack_thickness, outer_h, name="rack_out"))

    # Inner ring at z=inner_h
    actual_inner_r = inner_r + rack_thickness
    parts.append(build_torus_ring(actual_inner_r, rack_thickness, inner_h, name="rack_in"))

    # Spoke connections
    for i in range(n_spokes):
        th = 2 * math.pi * i / n_spokes
        p1 = (actual_inner_r * math.cos(th), actual_inner_r * math.sin(th), inner_h)
        p2 = (top_r * math.cos(th), top_r * math.sin(th), outer_h)
        spoke = build_swept_tube([p1, p2], rack_thickness, n_circ=8, name=f"spoke{i}")
        parts.append(spoke)

    return join_objs(parts)

def build_bulb(scale, reverse):
    """

    Detailed bulb: glass body + tapered neck + base cylinder.
    Matches nodegroup_bulb + nodegroup_reversiable_bulb.
    """

    parts = []
    n_circ = 32

    # Glass body: z=0 to z=1, float curve radius profile
    glass_prof = [(0, 0.15), (0.05, 0.17), (0.15, 0.20), (0.55, 0.38),
                  (0.80, 0.35), (0.96, 0.22), (1.0, 0.0)]
    n_glass = 50
    glass_ts = np.linspace(0, 1, n_glass + 1)
    glass_path = [(0, 0, float(t)) for t in glass_ts]
    glass_radii = [eval_curve(glass_prof, float(t)) for t in glass_ts]
    parts.append(build_swept_tube(glass_path, glass_radii, n_circ=n_circ, name="glass"))

    # Tapered neck: z=-0.2 to z=-0.3, float curve [(0,1),(0.44,0.55),(1,0.275)] * 0.15
    neck_prof = [(0, 0.15), (0.44, 0.0825), (1.0, 0.04125)]
    n_neck = 20
    neck_ts = np.linspace(0, 1, n_neck + 1)
    neck_path = [(0, 0, -0.2 + float(t) * (-0.1)) for t in neck_ts]
    neck_radii = [eval_curve(neck_prof, float(t)) for t in neck_ts]
    parts.append(build_swept_tube(neck_path, neck_radii, n_circ=n_circ, name="neck"))

    # Base cylinder: z=-0.2 to z=0, r=0.15
    base_path = [(0, 0, -0.2), (0, 0, 0)]
    parts.append(build_swept_tube(base_path, 0.15, n_circ=n_circ, name="bulb_base"))

    bulb = join_objs(parts)

    # Translate Z +0.3 (matches nodegroup_bulb final transform)
    bulb.location.z = 0.3
    apply_tf(bulb)

    # Scale uniformly
    bulb.scale = (scale, scale, scale)
    apply_tf(bulb)

    # Reverse (rotate 180 around Y)
    if reverse:
        bulb.rotation_euler.y = math.pi
        apply_tf(bulb)

    return bulb

# ── main assembly ────────────────────────────────────────────────────────────

# --- helpers required by wear_tear block (not already in this factory) ---
def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _noise_fac_output(noise_node):
    """Blender 5.0 renamed Fac->Factor on some nodes; fall back to first output."""

    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _set_principled(bsdf, **kw):
    """Set Principled BSDF inputs with Blender-version-tolerant socket names."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
        "Sheen Tint": ("Sheen Tint",),
        "Subsurface Color": ("Subsurface Color",),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

# wear_tear post-processing
# Faithful raw-bpy translations of:
# Both follow the same pattern: walk obj.data.materials, find existing
# MaterialOutput / BSDF, inject a procedural wear graph, reconnect.
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"

def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)

def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    if in0 is not None:
        if hasattr(in0, "default_value") or hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "default_value") or hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    return n

def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    if in0 is not None:
        if hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    if scale is not None:
        # SCALE op uses inputs[3] (Scale) on VectorMath
        for inp in n.inputs:
            if inp.name == "Scale":
                inp.default_value = scale
                break
    return n

def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = value
    return n

def _color_ramp(nt, fac_socket, stops):
    """stops = [(position, (r,g,b,a)), ...]"""

    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(fac_socket, fac_in)
    elements = cr.color_ramp.elements
    for i, (pos, color) in enumerate(stops):
        if i < len(elements):
            elements[i].position = pos
            elements[i].color = color
        else:
            e = elements.new(pos)
            e.color = color
    return cr

def _noise_tex(nt, vector_socket, scale, detail=2.0, distortion=0.0, roughness=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_socket is not None:
        nt.links.new(vector_socket, n.inputs["Vector"])
    if isinstance(scale, (int, float)):
        n.inputs["Scale"].default_value = float(scale)
    else:
        nt.links.new(scale, n.inputs["Scale"])
    if "Detail" in n.inputs:
        n.inputs["Detail"].default_value = detail
    if "Distortion" in n.inputs:
        n.inputs["Distortion"].default_value = distortion
    if "Roughness" in n.inputs:
        n.inputs["Roughness"].default_value = roughness
    return n

def get_scratch_params():
    """Replica of wear_tear/scratches.py:get_scratch_params."""

    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=log_uniform(5, 80),
        scratch_mask_ratio=log_uniform(0.01, 0.9),
        scratch_mask_noise=log_uniform(5, 40),
        scratch_depth=log_uniform(0.1, 1.0),
    )

def _build_scratch_graph(nt, params):
    """Build the scratch displacement node graph and return the Displacement output socket.

    Faithful translation of wear_tear/scratches.py:scratch_shader.
    """

    n_angle1 = _value_node(nt, params["angle1"])
    n_angle2 = _value_node(nt, params["angle2"])
    n_scale = _value_node(nt, params["scratch_scale"])
    n_mask_ratio = _value_node(nt, params["scratch_mask_ratio"])
    n_mask_noise = _value_node(nt, params["scratch_mask_noise"])
    n_depth = _value_node(nt, params["scratch_depth"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # First scratch direction
    cxyz1 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle1.outputs[0], cxyz1.inputs["Y"])
    map1 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map1, "vector_type"):
        try: map1.vector_type = "TEXTURE"
        except TypeError: pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    # Second scratch direction
    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map2, "vector_type"):
        try: map2.vector_type = "TEXTURE"
        except TypeError: pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    # Mask noise
    map3 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map3, "vector_type"):
        try: map3.vector_type = "TEXTURE"
        except TypeError: pass
    map3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.1920)
    nt.links.new(tex_coord.outputs["Object"], map3.inputs["Vector"])
    noise3 = _noise_tex(nt, map3.outputs["Vector"], n_mask_noise.outputs[0], detail=1.0)
    cr_mask = _color_ramp(nt, _noise_fac_output(noise3),
                          [(0.4109, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))])
    mul_mask = _math(nt, "MULTIPLY", n_mask_ratio.outputs[0], cr_mask.outputs["Color"])
    add_combined = _math(nt, "ADD", add.outputs[0], mul_mask.outputs[0], clamp=True)

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.7
    map_range.inputs[2].default_value = 0.72
    map_range.inputs[4].default_value = 0.9
    nt.links.new(add_combined.outputs[0], map_range.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(map_range.outputs["Result"], disp.inputs["Height"])
    nt.links.new(n_depth.outputs[0], disp.inputs["Scale"])

    return disp.outputs[0]

def apply_scratches(obj, **params):
    """Faithful raw-bpy port of wear_tear/scratches.py:Scratches.apply_over."""

    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_scratch_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == SCRATCH_LABEL for n in nt.nodes):
            continue   # idempotency: already applied
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        try:
            disp_out = _build_scratch_graph(nt, params)
            nt.links.new(disp_out, mat_out.inputs["Displacement"])
            # Mark idempotency
            disp_out.node.label = SCRATCH_LABEL
        except Exception as e:
            print(f"  [scratches] failed on {mat.name}: {type(e).__name__}: {e}")

def get_edge_wear_params():
    """Replica of wear_tear/edge_wear.py:get_edge_wear_params."""

    return dict(
        worn_off_opacity=float(np.random.uniform(0, 0.01)),
        worn_off_radius=float(np.random.uniform(0.005, 0.01)),
        scratch_radius=float(np.random.uniform(0.01, 0.03)),
        worn_off_mask_randomness=float(np.random.uniform(2.5, 3.0)),
        edge_base_color_hue=float(np.random.uniform(0.0, 1.0)),
        edge_base_color_whiteness=float(np.random.uniform(0.1, 0.6)),
        scratch_mask_randomness=float(np.random.choice(
            [np.random.uniform(0.1, 5.0), np.random.uniform(1.0, 10.0)])),
        scratch_density=float(np.random.uniform(1.5, 10.0)),
        scratch_opacity=float(np.random.uniform(0.5, 1.0)),
    )

def _build_edge_wear_graph(nt, original_bsdf_node, original_displacement_node, params):
    """Faithful raw-bpy port of edge_wear.py:shader_edge_tear_free_node_group.

    Returns (final_bsdf_socket, final_displacement_socket).
    """

    p = params
    n_scratch_opacity = _value_node(nt, p["scratch_opacity"])
    n_scratch_mask_randomness = _value_node(nt, p["scratch_mask_randomness"])
    n_scratch_radius = _value_node(nt, p["scratch_radius"])
    n_worn_opacity = _value_node(nt, p["worn_off_opacity"])
    n_worn_radius = _value_node(nt, p["worn_off_radius"])
    n_worn_mask_randomness = _value_node(nt, p["worn_off_mask_randomness"])
    n_edge_whiteness = _value_node(nt, p["edge_base_color_whiteness"])
    n_edge_hue = _value_node(nt, p["edge_base_color_hue"])
    n_scratch_density = _value_node(nt, p["scratch_density"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    # Scratch mask noise
    noise_a = _noise_tex(nt, mapping.outputs["Vector"], n_scratch_mask_randomness.outputs[0], detail=1.0)
    cr_a = _color_ramp(nt, _noise_fac_output(noise_a),
                       [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    # Bevel edge detection (scratch radius)
    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.samples = 20
    nt.links.new(n_scratch_radius.outputs[0], bevel.inputs["Radius"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub = _vmath(nt, "SUBTRACT", bevel.outputs[0], geo.outputs["Normal"])
    abs_a = _math(nt, "ABSOLUTE", sub.outputs["Vector"])
    cr_b = _color_ramp(nt, abs_a.outputs[0],
                       [(0.0691, (0, 0, 0, 1)), (0.1564, (1, 1, 1, 1))])

    mul_a = _math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"], clamp=True)
    mul_a1 = _math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0], clamp=True)

    # Bevel edge detection (worn-off radius)
    bevel2 = nt.nodes.new("ShaderNodeBevel")
    bevel2.samples = 20
    nt.links.new(n_worn_radius.outputs[0], bevel2.inputs["Radius"])
    sub2 = _vmath(nt, "SUBTRACT", bevel2.outputs[0], geo.outputs["Normal"])
    abs_b = _math(nt, "ABSOLUTE", sub2.outputs["Vector"])

    noise_b = _noise_tex(nt, mapping.outputs["Vector"], n_worn_mask_randomness.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac_output(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
    cr_d = _color_ramp(nt, mul_b1.outputs[0],
                       [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])

    # Edge color HSV
    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    if hasattr(combine_color, "mode"):
        try: combine_color.mode = "HSV"
        except TypeError: pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_result"):
        try: mix.clamp_result = True
        except TypeError: pass
    if hasattr(mix, "clamp_factor"):
        try: mix.clamp_factor = False
        except TypeError: pass
    nt.links.new(n_edge_whiteness.outputs[0], mix.inputs[0])
    nt.links.new(combine_color.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

    # Worn-edge BSDFs (Principled)
    bsdf_worn1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn1.inputs["Base Color"])
    _set_principled(bsdf_worn1, Metallic=0.3745, Roughness=0.1436,
                    **{"Specular IOR Level": 0.0})

    # Mix the original BSDF with the worn version
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cr_d.outputs["Color"], mix_shader.inputs[0])
    nt.links.new(original_bsdf_node.outputs[0], mix_shader.inputs[1])
    nt.links.new(bsdf_worn1.outputs[0], mix_shader.inputs[2])

    # Scratch density via voronoi distance-to-edge (two perpendicular)
    map_h = nt.nodes.new("ShaderNodeMapping")
    map_h.inputs["Scale"].default_value = (10.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_h.inputs["Vector"])
    vor_h = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_h, "feature"):
        try: vor_h.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])

    # Scale density by 2 for vertical
    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_v, "feature"):
        try: vor_v.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_v.outputs["Vector"], vor_v.inputs["Vector"])
    nt.links.new(scale_v.outputs[0], vor_v.inputs["Scale"])

    dist_h = vor_h.outputs.get("Distance") or vor_h.outputs[0]
    dist_v = vor_v.outputs.get("Distance") or vor_v.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_e = _color_ramp(nt, mul_dist.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_e = _math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"], clamp=True)
    mul_f = _math(nt, "MULTIPLY", mul_a.outputs[0], mul_e.outputs[0], clamp=True)

    bsdf_worn2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn2.inputs["Base Color"])
    _set_principled(bsdf_worn2, Metallic=0.3855, Roughness=0.0,
                    **{"Specular IOR Level": 0.0})

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_a1.outputs[0], mix_shader_2.inputs[0])
    nt.links.new(mix_shader.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(bsdf_worn2.outputs[0], mix_shader_2.inputs[2])

    # Displacement
    scale_disp = _vmath(nt, "SCALE", in0=mul_f.outputs[0], scale=2.0)
    if original_displacement_node is None:
        total_displacement = scale_disp.outputs[0]
    else:
        add_disp = _math(nt, "ADD", original_displacement_node.outputs[0],
                         scale_disp.outputs[0], clamp=True)
        total_displacement = add_disp.outputs[0]

    return mix_shader_2.outputs[0], total_displacement

def apply_edge_wear(obj, **params):
    """Faithful raw-bpy port of wear_tear/edge_wear.py:EdgeWear.apply_over."""

    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_edge_wear_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == EDGE_WEAR_LABEL for n in nt.nodes):
            continue   # idempotency
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        # Find original BSDF feeding Surface
        surface_links = mat_out.inputs["Surface"].links
        if not surface_links:
            continue
        original_bsdf = surface_links[0].from_node
        # Find original displacement (if any)
        disp_links = mat_out.inputs["Displacement"].links
        original_disp = disp_links[0].from_node if disp_links else None
        try:
            final_bsdf_socket, final_disp_socket = _build_edge_wear_graph(
                nt, original_bsdf, original_disp, params)
            # Reconnect
            nt.links.new(final_bsdf_socket, mat_out.inputs["Surface"])
            nt.links.new(final_disp_socket, mat_out.inputs["Displacement"])
            # Mark idempotency on the new mix_shader
            final_bsdf_socket.node.label = EDGE_WEAR_LABEL
        except Exception as e:
            print(f"  [edge_wear] failed on {mat.name}: {type(e).__name__}: {e}")

def apply_wear_tear(obj):
    """

    Two independent 50% probability gates: scratches and edge_wear.
    """

    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    scratch_p, edge_p = WEAR_TEAR_PROB
    if np.random.uniform() <= scratch_p:
        apply_scratches(obj)
    if np.random.uniform() <= edge_p:
        apply_edge_wear(obj)

def build_lamp():
    np.random.seed(SEED)
    random.seed(SEED)
    clear_scene()

    p = sample_parameters()
    parts = []

    # 1. Base disc → black metal ("BlackMaterial" slot)
    base_obj = build_base(p["BaseRadius"], p["BaseHeight"])
    base_obj.data.materials.append(METAL_BLACK_MAT)
    parts.append(base_obj)

    # 2. Stand (cubic Bezier tube) → shiny metal ("MetalMaterial" slot)
    stand, tip, tang = build_stand(
        p["BaseHeight"], p["CurvePoint1"], p["CurvePoint2"], p["CurvePoint3"],
        p["StandRadius"]
    )
    stand.data.materials.append(METAL_MAT)
    parts.append(stand)

    # 3. Compute rack height (matches nodegroup_lamp_geometry)
    # multiply_add = ShadeHeight * 0.4 * ReverseLamp + ShadeHeight * 0.2
    rev = 1.0 if p["ReverseLamp"] else 0.0
    rack_h = p["ShadeHeight"] * 0.4 * rev + p["ShadeHeight"] * 0.2

    # 4. Build all head components at origin
    head_parts = []

    # 4a. Lampshade → lampshade shader (LightPath-conditional, "LampshadeMaterial")
    shade_obj = build_lampshade(
        p["ShadeHeight"], p["HeadTopRadius"], p["HeadBotRadius"],
        p["ReverseLamp"], rack_h
    )
    shade_obj.data.materials.append(LAMPSHADE_MAT)
    head_parts.append(shade_obj)

    # 4b. Wire rack → metal
    inner_r = p["HeadTopRadius"] * 0.8 * 0.15
    rack_support = (rev * 2 - 1) * -0.015
    outer_h = rack_h * (2 * rev - 1)
    inner_h_val = rack_support
    rack = build_rack(p["HeadTopRadius"], p["RackThickness"],
                      outer_h, inner_r, inner_h_val)
    if rack:
        rack.data.materials.append(METAL_MAT)
        head_parts.append(rack)

    # 4c. Bulb → metal (base + glass approximated as metal for simplicity)
    bulb_scale = p["HeadTopRadius"] * 0.8
    bulb_obj = build_bulb(bulb_scale, p["ReverseLamp"])
    bulb_obj.data.materials.append(METAL_MAT)
    head_parts.append(bulb_obj)

    # Join head
    head = join_objs(head_parts)

    # Align Z axis to tangent (for bent stands)
    tang_vec = Vector(tang)
    z_up = Vector((0, 0, 1))
    if z_up.cross(tang_vec).length > 1e-4:
        rot_quat = z_up.rotation_difference(tang_vec)
        head.rotation_euler = rot_quat.to_euler()

    # Translate to tip
    head.location = tip
    apply_tf(head)
    parts.append(head)

    result = join_objs(parts)
    apply_tf(result)
    # Per-part materials were appended to each sub-object before join_objs;
    # Blender preserves material slots and remaps face material_index on join.
    # Fallback only if somehow the join collapsed material slots to zero.
    if result is not None and len(result.data.materials) == 0:
        result.data.materials.append(LAMPSHADE_MAT)
    # --- wear_tear application ---
    if result is not None and WEAR_DO_SCRATCH:
        apply_scratches(result)
    if result is not None and WEAR_DO_EDGEWEAR:
        apply_edge_wear(result)
    return result

lamp = build_lamp()
lamp.name = "LampFactory"

