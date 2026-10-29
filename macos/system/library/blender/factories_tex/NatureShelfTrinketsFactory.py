# [FL_INDEX: keywords="blender_factory, procedural_3d, NatureShelfTrinketsFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: NatureShelfTrinketsFactory | Category: factories_tex
# Prompt: A decorative nature-inspired trinket rendered as a 3D model, consisting of two oval disc shapes — a light cream/beige upper disc with concentric circular ridge patterns resembling a cross-section of a tree trunk or a zen sand garden rake pattern, and a slightly smaller dark charcoal base disc beneath it.

import os
import math
import random

import bpy
import numpy as np

SEED = 0
random.seed(SEED)
SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

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

def _srgb_to_linear(c):
    if c < 0: return 0.0
    elif c < 0.04045: return c / 12.92
    else: return ((c + 0.055) / 1.055) ** 2.4


def _make_coral_mat(seed, name="CoralMaterial"):
    """Pinkish-red organic coral with subtle noise variation."""

    rng = np.random.RandomState(((seed + 11) * 2654435761) & 0xFFFFFFFF)
    # Coral hues: pinkish-red to salmon-orange (H 0.95-0.08 wrapping around red)
    h_base = rng.choice([rng.uniform(0.95, 1.05) % 1.0, rng.uniform(0.0, 0.08)])
    s_base = rng.uniform(0.45, 0.75)
    v_base = rng.uniform(0.35, 0.65)
    r1, g1, b1 = _colorsys.hsv_to_rgb(h_base, s_base, v_base)
    # Secondary color: slightly shifted hue for variation
    h2 = (h_base + rng.uniform(-0.03, 0.03)) % 1.0
    r2, g2, b2 = _colorsys.hsv_to_rgb(h2, s_base * 0.8, v_base * 1.15)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(rng.uniform(8, 25))
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.7
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (r1, g1, b1, 1)
    cr.color_ramp.elements[1].position = 0.65; cr.color_ramp.elements[1].color = (r2, g2, b2, 1)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(rng.uniform(0.6, 0.85))
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _make_rock_mat(seed, name="RockMaterial"):
    """Grey/brown stone with fine noise for grain."""

    rng = np.random.RandomState(((seed + 13) * 2654435761) & 0xFFFFFFFF)
    # Stone hues: desaturated grey-brown (H 0.05-0.12, low S)
    h_base = rng.uniform(0.05, 0.12)
    s_base = rng.uniform(0.05, 0.25)
    v_base = rng.uniform(0.20, 0.55)
    r1, g1, b1 = _colorsys.hsv_to_rgb(h_base, s_base, v_base)
    r2, g2, b2 = _colorsys.hsv_to_rgb(h_base + rng.uniform(-0.02, 0.02),
                                        s_base * rng.uniform(0.6, 1.3),
                                        v_base * rng.uniform(0.7, 1.3))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # Coarse noise for large-scale color variation
    noise1 = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise1.inputs["Vector"])
    noise1.inputs["Scale"].default_value = float(rng.uniform(3, 8))
    noise1.inputs["Detail"].default_value = 4.0
    # Fine noise for grain
    noise2 = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise2.inputs["Vector"])
    noise2.inputs["Scale"].default_value = float(rng.uniform(20, 60))
    noise2.inputs["Detail"].default_value = 8.0
    # Mix coarse and fine
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = 'OVERLAY'
    mix.inputs[0].default_value = 0.3
    ln(_fac(noise1), mix.inputs[6])
    ln(_fac(noise2), mix.inputs[7])
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(mix.outputs[2], cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.25; cr.color_ramp.elements[0].color = (r1, g1, b1, 1)
    cr.color_ramp.elements[1].position = 0.75; cr.color_ramp.elements[1].color = (r2, g2, b2, 1)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(rng.uniform(0.75, 0.95))
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _make_pinecone_mat(seed, name="PineconeMaterial"):
    """Warm brown woody scale material."""

    rng = np.random.RandomState(((seed + 17) * 2654435761) & 0xFFFFFFFF)
    # Brown woody tones (H ~0.06-0.10)
    h_base = rng.uniform(0.06, 0.10)
    s_base = rng.uniform(0.40, 0.65)
    v_base = rng.uniform(0.15, 0.35)
    r1, g1, b1 = _colorsys.hsv_to_rgb(h_base, s_base, v_base)
    # Lighter tips
    r2, g2, b2 = _colorsys.hsv_to_rgb(h_base + 0.02, s_base * 0.7, v_base * 1.6)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(rng.uniform(12, 30))
    noise.inputs["Detail"].default_value = 5.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.30; cr.color_ramp.elements[0].color = (r1, g1, b1, 1)
    cr.color_ramp.elements[1].position = 0.70; cr.color_ramp.elements[1].color = (r2, g2, b2, 1)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(rng.uniform(0.7, 0.9))
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _make_shell_mat(seed, name="ShellMaterial"):
    """Pearlescent cream/tan shell with subtle iridescence."""

    rng = np.random.RandomState(((seed + 19) * 2654435761) & 0xFFFFFFFF)
    # Shell: warm cream/ivory/tan (H 0.06-0.14, low-mid S, high V)
    h_base = rng.uniform(0.06, 0.14)
    s_base = rng.uniform(0.10, 0.35)
    v_base = rng.uniform(0.55, 0.80)
    r1, g1, b1 = _colorsys.hsv_to_rgb(h_base, s_base, v_base)
    # Inner nacre: pinkish highlight
    r2, g2, b2 = _colorsys.hsv_to_rgb(rng.uniform(0.92, 1.0) % 1.0,
                                        rng.uniform(0.08, 0.20),
                                        v_base * rng.uniform(1.0, 1.3))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(rng.uniform(10, 30))
    noise.inputs["Detail"].default_value = 4.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = (r1, g1, b1, 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (r2, g2, b2, 1)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(rng.uniform(0.25, 0.45))
    bsdf.inputs["Specular IOR Level"].default_value = 0.6
    # Slight coat for nacre sheen
    bsdf.inputs["Coat Weight"].default_value = float(rng.uniform(0.15, 0.35))
    bsdf.inputs["Coat Roughness"].default_value = float(rng.uniform(0.1, 0.25))
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _make_creature_mat(seed, name="CreatureMaterial"):
    """Warm fur-like brown/tan with subtle variation for animal figurines."""

    rng = np.random.RandomState(((seed + 23) * 2654435761) & 0xFFFFFFFF)
    # Animal fur tones: brown/tawny/grey (H 0.04-0.12)
    h_base = rng.uniform(0.04, 0.12)
    s_base = rng.uniform(0.25, 0.55)
    v_base = rng.uniform(0.20, 0.50)
    r1, g1, b1 = _colorsys.hsv_to_rgb(h_base, s_base, v_base)
    # Lighter belly/underside tone
    r2, g2, b2 = _colorsys.hsv_to_rgb(h_base + rng.uniform(-0.01, 0.02),
                                        s_base * 0.6,
                                        v_base * rng.uniform(1.3, 1.8))
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # Use object Z to create dorsal-ventral gradient
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ln(tc.outputs["Object"], sep.inputs["Vector"])
    ramp_z = nt.nodes.new("ShaderNodeValToRGB"); ln(sep.outputs["Z"], ramp_z.inputs["Fac"])
    ramp_z.color_ramp.elements[0].position = 0.2; ramp_z.color_ramp.elements[0].color = (r2, g2, b2, 1)
    ramp_z.color_ramp.elements[1].position = 0.6; ramp_z.color_ramp.elements[1].color = (r1, g1, b1, 1)
    # Fine noise for fur-like stipple
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(rng.uniform(30, 80))
    noise.inputs["Detail"].default_value = 6.0
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = 'OVERLAY'
    mix.inputs[0].default_value = 0.15
    ln(ramp_z.outputs["Color"], mix.inputs[6])
    ln(_fac(noise), mix.inputs[7])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(rng.uniform(0.7, 0.9))
    bsdf.inputs["Specular IOR Level"].default_value = 0.15
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# Map trinket category to its material constructor
_TRINKET_MAT_MAKERS = {
    "Coral": _make_coral_mat,
    "Rock": _make_rock_mat,
    "Boulder": _make_rock_mat,
    "Pinecone": _make_pinecone_mat,
    "Mollusk": _make_shell_mat,
    "Auger": _make_shell_mat,
    "Clam": _make_shell_mat,
    "Conch": _make_shell_mat,
    "Mussel": _make_shell_mat,
    "Scallop": _make_shell_mat,
    "Volute": _make_shell_mat,
    "Carnivore": _make_creature_mat,
    "Herbivore": _make_creature_mat,
}

np.random.seed(SEED)

TARGET_SIZE = np.random.uniform(0.80, 1.20)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for t in list(bpy.data.textures):
        bpy.data.textures.remove(t)
    bpy.context.scene.cursor.location = (0, 0, 0)

def apply_tf(obj, loc=False):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if loc:
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    else:
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def add_mod(obj, mtype, **kw):
    m = obj.modifiers.new("", mtype)
    for k, v in kw.items():
        setattr(m, k, v)
    if mtype == "SUBSURF" and getattr(m, 'levels', 1) == 0:
        obj.modifiers.remove(m)
        return obj
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

def join_objs(objs):
    if not objs:
        return None
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def write_co(obj, co):
    obj.data.vertices.foreach_set("co", co.reshape(-1))
    obj.data.update()

def scale_to_target(obj, target=0.12):
    dims = obj.dimensions
    max_dim = max(dims.x, dims.y, dims.z)
    if max_dim > 1e-6:
        s = target / max_dim
        obj.scale = (s, s, s)
        apply_tf(obj)
    co = read_co(obj)
    if len(co) > 0:
        min_z = co[:, 2].min()
        obj.location.z = -min_z
        apply_tf(obj, loc=True)

def decorate_shell(obj, thickness=0.005):
    add_mod(obj, "SOLIDIFY", thickness=thickness, offset=-1)
    tex = bpy.data.textures.new("shell_detail", type="STUCCI")
    tex.noise_scale = float(np.exp(np.random.uniform(np.log(0.1), np.log(0.2))))
    add_mod(obj, "DISPLACE", texture=tex, strength=0.02, mid_level=0.0,
            direction="NORMAL")

# --- ROCKS ---

def make_rock_smooth():
    """Rounded rock: icosphere + two-layer CLOUDS displacement + SUBSURF."""

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(0, 0, 0))
    rock = bpy.context.active_object
    rock.scale = (np.random.uniform(0.7, 1.0),
                  np.random.uniform(0.6, 0.9),
                  np.random.uniform(0.45, 0.7))
    apply_tf(rock)
    # Primary large-scale displacement
    tex = bpy.data.textures.new("rock_clouds", type="CLOUDS")
    tex.noise_scale = np.random.uniform(0.3, 0.6)
    add_mod(rock, "DISPLACE", texture=tex, strength=0.18, mid_level=0.5)
    # Secondary fine-detail displacement
    tex2 = bpy.data.textures.new("rock_detail", type="CLOUDS")
    tex2.noise_scale = np.random.uniform(0.05, 0.12)
    add_mod(rock, "DISPLACE", texture=tex2, strength=0.06, mid_level=0.5,
            direction="NORMAL")
    add_mod(rock, "SUBSURF", levels=2, render_levels=2)
    return rock

def make_boulder():
    """Thicker, rougher rock variant with two-layer displacement."""

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(0, 0, 0))
    rock = bpy.context.active_object
    rock.scale = (np.random.uniform(0.8, 1.2),
                  np.random.uniform(0.8, 1.2),
                  np.random.uniform(0.5, 0.8))
    apply_tf(rock)
    # Primary coarse displacement
    tex = bpy.data.textures.new("boulder_clouds", type="CLOUDS")
    tex.noise_scale = np.random.uniform(0.5, 1.0)
    add_mod(rock, "DISPLACE", texture=tex, strength=0.35, mid_level=0.5)
    # Secondary fine-detail displacement
    tex2 = bpy.data.textures.new("boulder_detail", type="CLOUDS")
    tex2.noise_scale = np.random.uniform(0.08, 0.15)
    add_mod(rock, "DISPLACE", texture=tex2, strength=0.10, mid_level=0.5,
            direction="NORMAL")
    add_mod(rock, "SUBSURF", levels=1, render_levels=1)
    return rock

# --- CORAL ---

def make_coral():
    """Trunk + radial branches with joint blobs and variable thickness."""

    parts = []
    n_br = np.random.randint(5, 10)
    base_r = 0.06
    trunk_r = base_r * 1.6

    # Trunk with taper
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=trunk_r, depth=0.7,
                                         location=(0, 0, 0))
    trunk = bpy.context.active_object
    trunk.location.z = 0.35
    apply_tf(trunk)
    add_mod(trunk, "SIMPLE_DEFORM", deform_method="TAPER", factor=0.5, deform_axis="Z")
    parts.append(trunk)

    for i in range(n_br):
        br_len = np.random.uniform(0.25, 0.55)
        angle = 2 * math.pi * i / n_br + np.random.uniform(-0.3, 0.3)
        tilt = math.radians(np.random.uniform(30, 70))
        br_r = base_r * np.random.uniform(0.4, 0.7)
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=br_r, depth=br_len,
                                             location=(0, 0, 0))
        br = bpy.context.active_object
        br.rotation_euler.y = tilt
        br.rotation_euler.z = angle
        attach_z = np.random.uniform(0.25, 0.55)
        br.location = (math.cos(angle) * 0.05, math.sin(angle) * 0.05, attach_z)
        apply_tf(br)
        taper_factor = np.random.uniform(0.6, 0.85)
        add_mod(br, "SIMPLE_DEFORM", deform_method="TAPER", factor=taper_factor, deform_axis="Z")
        parts.append(br)

        # Joint blob — large enough to smooth branch-trunk transition
        blob_r = max(br_r * 1.8, trunk_r * 0.6)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8,
                                              radius=blob_r, location=(0, 0, 0))
        blob = bpy.context.active_object
        blob.location = (math.cos(angle) * 0.03, math.sin(angle) * 0.03, attach_z)
        apply_tf(blob)
        parts.append(blob)

    result = join_objs(parts)
    # Voxel remesh to fuse branches into trunk (eliminates clipping/intersection)
    add_mod(result, "REMESH", mode='VOXEL', voxel_size=0.008)
    add_mod(result, "SUBSURF", levels=2, render_levels=2)
    return result

# --- PINECONE ---

def make_pinecone():
    """Overlapping scale arrangement with spiral phyllotaxis."""

    n_layers = np.random.randint(8, 13)
    n_scales = np.random.randint(7, 12)
    parts = []
    golden_angle = 2.399963  # radians (137.508 degrees)

    scale_idx = 0
    for li in range(n_layers):
        t = li / n_layers
        layer_r = 0.42 * (1 - t * 0.75)
        layer_z = t * 1.1
        scale_size = 0.14 * (1 - t * 0.5)

        for si in range(n_scales):
            # Spiral phyllotaxis angle for overlapping pattern
            angle = golden_angle * scale_idx + np.random.uniform(-0.05, 0.05)
            scale_idx += 1

            # Use flattened sphere (overlapping scales) instead of cone
            bpy.ops.mesh.primitive_uv_sphere_add(
                segments=6, ring_count=4,
                radius=scale_size,
                location=(0, 0, 0))
            sc = bpy.context.active_object
            # Flatten to scale shape
            sc.scale = (1.0, 0.7, 0.35)
            apply_tf(sc)
            # Tilt outward
            sc.rotation_euler.x = math.radians(np.random.uniform(25, 50))
            sc.rotation_euler.z = angle
            sc.location = (layer_r * math.cos(angle),
                           layer_r * math.sin(angle),
                           layer_z + scale_size * 0.3)
            apply_tf(sc)
            parts.append(sc)

    # Central axis
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.07, depth=1.15,
                                         location=(0, 0, 0))
    axis = bpy.context.active_object
    axis.location.z = 0.575
    apply_tf(axis)
    add_mod(axis, "SIMPLE_DEFORM", deform_method="TAPER", factor=0.8, deform_axis="Z")
    parts.append(axis)

    return join_objs(parts)

# --- SPIRAL SHELLS (Auger, Conch, Volute) ---

def make_auger_shell():
    """Tall spiral shell (auger) via SCREW on open circle profile + SOLIDIFY."""

    bpy.ops.mesh.primitive_circle_add(vertices=12, radius=0.04, location=(0, 0, 0))
    profile = bpy.context.active_object
    profile.location.x = 0.10
    apply_tf(profile)

    screw_m = profile.modifiers.new("screw", "SCREW")
    screw_m.screw_offset = 0.12
    screw_m.angle = math.pi * np.random.uniform(6, 10)
    screw_m.steps = 64
    screw_m.render_steps = 64
    bpy.context.view_layer.objects.active = profile
    bpy.ops.object.modifier_apply(modifier=screw_m.name)

    add_mod(profile, "SIMPLE_DEFORM", deform_method="TAPER",
            factor=-np.random.uniform(0.7, 0.95), deform_axis="Z")

    decorate_shell(profile, thickness=0.003)
    return profile

def make_conch_shell():
    """Wide spiral shell with lip via SCREW on open profile + SOLIDIFY."""

    bpy.ops.mesh.primitive_circle_add(vertices=12, radius=0.06, location=(0, 0, 0))
    profile = bpy.context.active_object
    profile.location.x = 0.18
    apply_tf(profile)

    screw_m = profile.modifiers.new("screw", "SCREW")
    screw_m.screw_offset = 0.06
    screw_m.angle = math.pi * np.random.uniform(4, 6)
    screw_m.steps = 48
    screw_m.render_steps = 48
    bpy.context.view_layer.objects.active = profile
    bpy.ops.object.modifier_apply(modifier=screw_m.name)

    add_mod(profile, "SIMPLE_DEFORM", deform_method="TAPER",
            factor=-np.random.uniform(0.5, 0.8), deform_axis="Z")

    decorate_shell(profile, thickness=0.004)
    return profile

def make_volute_shell():
    """Wide spiral with bumps via SCREW on open profile + SOLIDIFY."""

    bpy.ops.mesh.primitive_circle_add(vertices=10, radius=0.05, location=(0, 0, 0))
    profile = bpy.context.active_object
    profile.location.x = 0.15
    apply_tf(profile)

    screw_m = profile.modifiers.new("screw", "SCREW")
    screw_m.screw_offset = 0.07
    screw_m.angle = math.pi * np.random.uniform(4, 7)
    screw_m.steps = 48
    screw_m.render_steps = 48
    bpy.context.view_layer.objects.active = profile
    bpy.ops.object.modifier_apply(modifier=screw_m.name)

    add_mod(profile, "SIMPLE_DEFORM", deform_method="TAPER",
            factor=-np.random.uniform(0.5, 0.85), deform_axis="Z")

    decorate_shell(profile, thickness=0.004)
    return profile

# --- BIVALVE SHELLS (Clam, Mussel, Scallop) ---

def _make_half_shell(sx=1.0, sy=1.0, sz=0.4, ridges=False):
    """Create a half-shell (dome) shape for bivalve shells."""

    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.15,
                                          location=(0, 0, 0))
    shell = bpy.context.active_object
    shell.scale = (sx, sy, sz)
    apply_tf(shell)

    # Remove bottom half
    bpy.context.view_layer.objects.active = shell
    shell.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    mesh = shell.data
    for v in mesh.vertices:
        v.select = (v.co.z < -0.001)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

    if ridges:
        # Add radial ridges via CLOUDS displacement (fine scale for ridge-like pattern)
        tex = bpy.data.textures.new("ridges", type="CLOUDS")
        tex.noise_scale = 0.05
        add_mod(shell, "DISPLACE", texture=tex, strength=0.012,
                mid_level=0.5, direction="NORMAL")
        # Second displacement for radial striations
        tex2 = bpy.data.textures.new("radial_ridges", type="WOOD")
        tex2.noise_scale = 0.03
        add_mod(shell, "DISPLACE", texture=tex2, strength=0.006,
                mid_level=0.5, direction="NORMAL")

    return shell

def _make_bivalve(half_shell_kw, angle_range, lower_angle_frac, hinge_sep=0.005):
    """Common bivalve shell: duplicate a half-shell, open upper/lower, flip lower normals."""

    upper = _make_half_shell(**half_shell_kw)
    bpy.ops.object.select_all(action="DESELECT")
    upper.select_set(True)
    bpy.context.view_layer.objects.active = upper
    bpy.ops.object.duplicate()
    lower = bpy.context.active_object

    open_angle = np.random.uniform(*angle_range)
    upper.rotation_euler.y = open_angle
    upper.location.z += hinge_sep
    lower.scale.z = -1
    lower.rotation_euler.y = -open_angle * lower_angle_frac
    lower.location.z -= hinge_sep
    apply_tf(upper)
    apply_tf(lower)

    bpy.context.view_layer.objects.active = lower
    lower.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode='OBJECT')

    result = join_objs([upper, lower])
    decorate_shell(result, thickness=0.003)
    return result

def make_clam_shell():
    return _make_bivalve(dict(sx=1.0, sy=1.2, sz=0.35), (0.25, 0.45), 0.5, 0.006)

def make_mussel_shell():
    return _make_bivalve(dict(sx=0.6, sy=1.5, sz=0.3), (0.20, 0.35), 0.3)

def make_scallop_shell():
    return _make_bivalve(dict(sx=1.0, sy=1.0, sz=0.25, ridges=True), (0.30, 0.50), 0.4)

# --- CREATURE SILHOUETTES ---

def make_herbivore_silhouette():
    """Multi-segment herbivore: body, rump, belly, neck, head, snout, 4 legs.
    All parts overlap with body for proper voxel remesh fusion."""

    parts = []

    # Main body barrel
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.5,
                                          location=(0, 0, 0))
    body = bpy.context.active_object
    body.scale = (1.3, 0.6, 0.5)
    body.location.z = 0.55
    apply_tf(body)
    parts.append(body)

    # Rump (slightly wider at back)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.28,
                                          location=(0, 0, 0))
    rump = bpy.context.active_object
    rump.scale = (0.9, 1.0, 0.9)
    rump.location = (-0.35, 0, 0.48)
    apply_tf(rump)
    parts.append(rump)

    # Belly
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.22,
                                          location=(0, 0, 0))
    belly = bpy.context.active_object
    belly.location = (0.0, 0, 0.38)
    apply_tf(belly)
    parts.append(belly)

    # Neck (thicker, deeper into body)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.14, depth=0.38,
                                         location=(0, 0, 0))
    neck = bpy.context.active_object
    neck.rotation_euler.y = math.radians(-25)
    neck.location = (0.50, 0, 0.70)
    apply_tf(neck)
    parts.append(neck)

    # Head
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.16,
                                          location=(0, 0, 0))
    head = bpy.context.active_object
    head.scale = (1.3, 0.85, 0.9)
    head.location = (0.70, 0, 0.88)
    apply_tf(head)
    parts.append(head)

    # Snout
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.09,
                                          location=(0, 0, 0))
    snout = bpy.context.active_object
    snout.scale = (1.4, 0.8, 0.7)
    snout.location = (0.86, 0, 0.84)
    apply_tf(snout)
    parts.append(snout)

    # 4 legs — thicker, positioned to overlap with body
    leg_positions = [(0.35, 0.20), (0.35, -0.20), (-0.35, 0.20), (-0.35, -0.20)]
    for lx, ly in leg_positions:
        # Upper leg (thigh — thicker for voxel remesh survival)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.10, depth=0.30,
                                             location=(0, 0, 0))
        thigh = bpy.context.active_object
        thigh.location = (lx, ly, 0.35)
        apply_tf(thigh)
        parts.append(thigh)
        # Lower leg
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.07, depth=0.24,
                                             location=(0, 0, 0))
        shin = bpy.context.active_object
        shin.location = (lx, ly, 0.12)
        apply_tf(shin)
        parts.append(shin)

    # Tail — attached INSIDE body (body x-extent is ±0.65)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.035, depth=0.3,
                                         location=(0, 0, 0))
    tail = bpy.context.active_object
    tail.rotation_euler.y = math.radians(30)
    tail.location = (-0.48, 0, 0.55)
    apply_tf(tail)
    parts.append(tail)

    result = join_objs(parts)
    # Voxel remesh to fuse all overlapping parts into single surface
    add_mod(result, "REMESH", mode='VOXEL', voxel_size=0.025)
    add_mod(result, "SUBSURF", levels=1, render_levels=1)
    return result

def make_carnivore_silhouette():
    """Multi-segment carnivore: body, chest, neck, head, jaw, 4 legs, tail.
    All parts overlap with body for proper voxel remesh fusion."""

    parts = []

    # Main body
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.45,
                                          location=(0, 0, 0))
    body = bpy.context.active_object
    body.scale = (1.4, 0.5, 0.48)
    body.location.z = 0.5
    apply_tf(body)
    parts.append(body)

    # Chest (broader at front)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.25,
                                          location=(0, 0, 0))
    chest = bpy.context.active_object
    chest.scale = (0.9, 1.0, 0.95)
    chest.location = (0.3, 0, 0.52)
    apply_tf(chest)
    parts.append(chest)

    # Neck (thicker, deeper into body)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.13, depth=0.30,
                                         location=(0, 0, 0))
    neck = bpy.context.active_object
    neck.rotation_euler.y = math.radians(-25)
    neck.location = (0.50, 0, 0.60)
    apply_tf(neck)
    parts.append(neck)

    # Head
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.18,
                                          location=(0, 0, 0))
    head = bpy.context.active_object
    head.scale = (1.2, 0.82, 0.85)
    head.location = (0.70, 0, 0.68)
    apply_tf(head)
    parts.append(head)

    # Jaw/snout
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.1,
                                          location=(0, 0, 0))
    jaw = bpy.context.active_object
    jaw.scale = (1.5, 0.75, 0.6)
    jaw.location = (0.88, 0, 0.62)
    apply_tf(jaw)
    parts.append(jaw)

    # 4 legs — thicker, positioned to overlap with body
    leg_positions = [(0.30, 0.16), (0.30, -0.16), (-0.30, 0.16), (-0.30, -0.16)]
    for lx, ly in leg_positions:
        # Thigh (thicker for voxel remesh survival)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.09, depth=0.30,
                                             location=(0, 0, 0))
        thigh = bpy.context.active_object
        thigh.location = (lx, ly, 0.33)
        apply_tf(thigh)
        parts.append(thigh)

        # Lower leg
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.065, depth=0.22,
                                             location=(0, 0, 0))
        shin = bpy.context.active_object
        shin.location = (lx, ly, 0.11)
        apply_tf(shin)
        parts.append(shin)

    # Tail — create at origin, apply bend there, THEN move to body
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.04, depth=0.45,
                                         location=(0, 0, 0))
    tail = bpy.context.active_object
    tail.rotation_euler.y = math.radians(-35)
    apply_tf(tail)
    # Bend upward: Y axis curves in X-Z plane (not X which curves sideways)
    add_mod(tail, "SIMPLE_DEFORM", deform_method="BEND",
            angle=math.radians(np.random.uniform(20, 45)), deform_axis="Y")
    # Now move to final position inside body
    tail.location = (-0.50, 0, 0.52)
    apply_tf(tail, loc=True)
    parts.append(tail)

    result = join_objs(parts)
    # Voxel remesh to fuse all overlapping parts into single surface
    add_mod(result, "REMESH", mode='VOXEL', voxel_size=0.025)
    add_mod(result, "SUBSURF", levels=1, render_levels=1)
    return result

# All trinket types with weights
TRINKET_FACTORIES = [
    ("Coral", make_coral, 1),
    ("Rock", make_rock_smooth, 1),
    ("Boulder", make_boulder, 1),
    ("Pinecone", make_pinecone, 1),
    ("Mollusk", make_conch_shell, 3),
    ("Auger", make_auger_shell, 2),
    ("Clam", make_clam_shell, 3),
    ("Conch", make_conch_shell, 2),
    ("Mussel", make_mussel_shell, 2),
    ("Scallop", make_scallop_shell, 2),
    ("Volute", make_volute_shell, 2),
    ("Carnivore", make_carnivore_silhouette, 5),
    ("Herbivore", make_herbivore_silhouette, 5),
]

def build_trinket():
    clear_scene()

    names = [t[0] for t in TRINKET_FACTORIES]
    funcs = [t[1] for t in TRINKET_FACTORIES]
    weights = np.array([t[2] for t in TRINKET_FACTORIES], dtype=float)
    probs = weights / weights.sum()

    idx = np.random.choice(len(TRINKET_FACTORIES), p=probs)
    name = names[idx]
    func = funcs[idx]

    obj = func()
    scale_to_target(obj, target=TARGET_SIZE)
    obj.name = f"NatureShelfTrinketsFactory_{name}"
    # Per-type material: coral, rock, shell, pinecone, or creature
    mat_maker = _TRINKET_MAT_MAKERS.get(name, _make_rock_mat)
    trinket_mat = mat_maker(SEED, f"NatureShelfTrinket_{name}_Material")
    if obj is not None:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(trinket_mat)
        elif obj.data.materials[0] is None:
            obj.data.materials[0] = trinket_mat
    return obj, name

trinket, variant_name = build_trinket()

