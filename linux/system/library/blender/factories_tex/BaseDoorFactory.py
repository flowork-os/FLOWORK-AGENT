# [FL_INDEX: keywords="blender_factory, procedural_3d, BaseDoorFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BaseDoorFactory | Category: factories_tex
# Prompt: A minimalist arched-top door panel rendered as a smooth 3D model, featuring a flat dark charcoal surface with a subtle dark blue metallic sheen along the curved arch at the top.

import os
import math
import random

import bmesh
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

WOOD_COLORS = [
    0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170,
    0x3D2B1F, 0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43,
    0x4E3828, 0x4E3828, 0xC09A6B, 0x944536, 0x3F0110, 0x773C12,
    0x6E4E37, 0x5C4033, 0x5C4033, 0x3C3034, 0x96704C, 0x371B1A,
    0x483B32, 0x43141A, 0x471713, 0xC3B090, 0x6B4423, 0x674D46,
    0x5D2E1A, 0x331C1F, 0x7A5640, 0xB99984, 0x71543D, 0x8F4B28,
    0x491A00, 0x836446, 0x7F461B, 0x6A3208, 0x724115, 0xA0522B,
    0x832A0C, 0x371B1A, 0xC7A373, 0x483B32, 0x635147, 0x664228,
    0x5C5248,
]

def _srgb_to_linear(c):
    if c < 0: return 0.0
    elif c < 0.04045: return c / 12.92
    else: return ((c + 0.055) / 1.055) ** 2.4

def _hex2rgba_linear(hexval):
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0)

def _wood_base_color(seed):
    """Sample wood color"""

    rng = np.random.RandomState(((seed + 7) * 2654435761) & 0xFFFFFFFF)
    hexval = WOOD_COLORS[rng.randint(0, len(WOOD_COLORS))]
    r, g, b, _ = _hex2rgba_linear(hexval)
    h, s, v = _colorsys.rgb_to_hsv(r, g, b)
    # Variation in wood color
    h2 = (h + rng.uniform(-0.0, 0.05)) % 1.0
    s2 = max(0, min(1, s + rng.uniform(-0.3, 0.2)))
    v2 = max(0, min(1, v * float(np.exp(rng.uniform(np.log(0.2), np.log(20))))))
    return _colorsys.hsv_to_rgb(h2, s2, v2)

def make_mat(seed, name="WoodMaterial"):
    """Wood material with color"""

    r1, g1, b1 = _wood_base_color(seed)
    r2, g2, b2 = _wood_base_color(seed + 3)
    c1 = (r1, g1, b1, 1.0)
    c2 = (r2, g2, b2, 1.0)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); ln(tc.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(np.random.uniform(5, 20))
    noise.inputs["Detail"].default_value = 5.0
    cr = nt.nodes.new("ShaderNodeValToRGB"); ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = c1
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = c2
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.3, 0.6))
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_handle_mat(seed, name="DoorHandleMetal"):
    """Brushed metal for door handle/knob/lever — material_assignments.metal_neutral."""

    roughness_val = float(np.random.uniform(0.2, 0.5))
    hue = float(np.random.uniform(0.05, 0.12))
    sat = float(np.random.uniform(0.0, 0.15))
    val = float(np.random.uniform(0.5, 0.85))
    base_color = _hsv2rgba(hue, sat, val)
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(20.0, 45.0))
    ln(tc.outputs["Object"], noise.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.1
    bump.inputs["Distance"].default_value = 0.001
    ln(noise.outputs[0], bump.inputs["Height"])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = roughness_val
    ln(bump.outputs[0], bsdf.inputs["Normal"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def _set_principled(bsdf, **kwargs):
    for key, value in kwargs.items():
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = value

def _metal_hsv():
    return (
        float(np.random.uniform(0.05, 0.12)),
        float(np.random.uniform(0.0, 0.15)),
        float(np.random.uniform(0.5, 0.85)),
    )

def _make_basic_metal(name, roughness=None):
    hue, sat, val = _metal_hsv()
    mat = _new_mat(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        **{
            "Base Color": _hsv2rgba(hue, sat, val),
            "Metallic": 1.0,
            "Roughness": float(roughness if roughness is not None else np.random.uniform(0.18, 0.55)),
        },
    )
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_metal_basic(name="MetalBasic"):
    """Port of material_assignments.metals option: metal_basic.shader_metal."""

    return _make_basic_metal(name)

def make_brushed_metal(name="BrushedMetal"):
    """Port of material_assignments.metals option: brushed_metal.shader_brushed_metal."""

    mat = _make_basic_metal(name, roughness=float(np.random.uniform(0.22, 0.48)))
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf is not None:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = float(np.random.uniform(35.0, 70.0))
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.055
        bump.inputs["Distance"].default_value = 0.0012
        nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
        nt.links.new(noise.outputs[0], bump.inputs["Height"])
        nt.links.new(bump.outputs[0], bsdf.inputs["Normal"])
    return mat

def make_galvanized_metal(name="GalvanizedMetal"):
    """Port of material_assignments.metals option: galvanized_metal.shader_galvanized_metal."""

    mat = _make_basic_metal(name, roughness=float(np.random.uniform(0.28, 0.62)))
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf is not None:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = float(np.random.uniform(18.0, 34.0))
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.30
        ramp.color_ramp.elements[1].position = 0.82
        ramp.color_ramp.elements[0].color = _hsv2rgba(0.08, 0.05, 0.35)
        ramp.color_ramp.elements[1].color = _hsv2rgba(0.10, 0.08, 0.82)
        nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
        nt.links.new(vor.outputs[0], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat

def make_grained_metal(name="GrainedMetal"):
    """Port of material_assignments.metals option: grained_and_polished_metal.shader_grained_metal."""

    mat = _make_basic_metal(name, roughness=float(np.random.uniform(0.16, 0.36)))
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf is not None:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.inputs["Scale"].default_value = float(np.random.uniform(12.0, 28.0))
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.035
        bump.inputs["Distance"].default_value = 0.0008
        nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
        nt.links.new(wave.outputs[1] if len(wave.outputs) > 1 else wave.outputs[0], bump.inputs["Height"])
        nt.links.new(bump.outputs[0], bsdf.inputs["Normal"])
    return mat

def make_hammered_metal(name="HammeredMetal"):
    """Port of material_assignments.metals option: hammered_metal.shader_hammered_metal."""

    mat = _make_basic_metal(name, roughness=float(np.random.uniform(0.32, 0.68)))
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf is not None:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = float(np.random.uniform(55.0, 110.0))
        noise.inputs["Detail"].default_value = 8.0
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.10
        bump.inputs["Distance"].default_value = 0.0020
        nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
        nt.links.new(noise.outputs[0], bump.inputs["Height"])
        nt.links.new(bump.outputs[0], bsdf.inputs["Normal"])
    return mat

def make_brushed_black_metal(name="BrushedBlackMetal"):
    """Port of material_assignments.metals option: appliance.shader_brushed_black_metal."""

    mat = _new_mat(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        **{"Base Color": (0.0167, 0.0167, 0.0167, 1.0), "Metallic": 1.0, "Roughness": 0.25},
    )
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

METALS_REGISTRY = [
    (make_metal_basic, 3.0),
    (make_brushed_metal, 2.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 0.7),
    (make_brushed_black_metal, 0.3),
]

def weighted_sample_mat(registry):
    weights = np.array([w for _, w in registry], dtype=float)
    weights /= weights.sum()
    idx = int(np.random.choice(len(registry), p=weights))
    return registry[idx][0]

def make_bar_handle_mat(seed, name="DoorBarHandleMetal"):
    """Metal for push-bar handles — samples material_assignments.metals."""

    return weighted_sample_mat(METALS_REGISTRY)(name)

WOOD_MAT = make_mat(SEED, "BaseDoorFactory_Wood")
WOOD_MAT.use_fake_user = True
# Backward-compat alias — earlier code references ELEM_MAT
ELEM_MAT = WOOD_MAT

# Save/restore np.random state so the subsequent build sampling is unchanged.
_saved_state = np.random.get_state()
HANDLE_MAT = make_handle_mat(SEED, "BaseDoorFactory_HandleMetal")
HANDLE_MAT.use_fake_user = True
BAR_HANDLE_MAT = make_bar_handle_mat(SEED, "BaseDoorFactory_BarMetal")
BAR_HANDLE_MAT.use_fake_user = True
np.random.set_state(_saved_state)

np.random.seed(SEED)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)

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
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=m.name)
    return obj

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

def mirror_handle_y(obj, depth):
    """Mirror handle geometry across Y=depth/2 to create handles on both sides.
    In our coord system door spans y=0..depth, so mirror around y=depth/2.
    Matches source nodegroup_symmetry_along_y: Scale(1, -1, 1) + FlipFaces,
    but source door is centered at y=0 while ours starts at y=0."""

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Duplicate all geometry
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    result = bmesh.ops.duplicate(bm, geom=geom)

    # Mirror duplicated verts around y=depth/2: y' = depth - y
    for v in result['vert_map'].values():
        v.co.y = depth - v.co.y

    # Flip normals of duplicated faces
    for f in result['face_map'].values():
        f.normal_flip()

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj

# -- Door slab ----------------------------------------------------------------
def make_door_slab(width, height, depth):
    """Plain door body: spans x=0..width, y=0..depth, z=0..height."""

    bpy.ops.mesh.primitive_cube_add(size=2.0)
    slab = bpy.context.active_object
    slab.location = (1, 1, 1)
    apply_tf(slab, loc=True)
    slab.scale = (width / 2, depth / 2, height / 2)
    apply_tf(slab)
    return slab

# -- Door frame ----------------------------------------------------------------
def make_door_frame(width, height, depth, frame_width, frame_style, is_double_door):
    """Door frame around the door opening."""

    parts = []
    door_frame_width = 2 * width if is_double_door else width

    if frame_style == "single_column":
        # Single column: just one vertical side piece
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        col = bpy.context.active_object
        col.scale = (frame_width / 2, depth / 2, height / 2)
        col.location = (-frame_width / 2, depth / 2, height / 2)
        apply_tf(col)
        parts.append(col)
    else:
        # Full frame: left + right vertical + top horizontal
        frame_height = height + frame_width  # columns extend above door

        # Left column
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        left = bpy.context.active_object
        left.scale = (frame_width / 2, depth / 2, frame_height / 2)
        left.location = (-frame_width / 2, depth / 2, frame_height / 2 - frame_width / 2)
        apply_tf(left)
        parts.append(left)

        # Right column
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        right = bpy.context.active_object
        right.scale = (frame_width / 2, depth / 2, frame_height / 2)
        right.location = (door_frame_width + frame_width / 2, depth / 2,
                          frame_height / 2 - frame_width / 2)
        apply_tf(right)
        parts.append(right)

        # Top piece (lintel) — only if not dome
        top_dome = (frame_style == "full_frame_dome")
        if not top_dome:
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            top = bpy.context.active_object
            top.scale = (door_frame_width / 2 + frame_width, depth / 2, frame_width / 2)
            top.location = (door_frame_width / 2, depth / 2, height + frame_width / 2)
            apply_tf(top)
            parts.append(top)

    if not parts:
        return None
    return join_objs(parts)

# -- Door arc (dome) -----------------------------------------------------------
def make_door_arc(width, height, depth):
    """Semicircular arch on top of the door.
    Matches source: CurveArc(radius=width/2, sweep=pi) extruded along depth*0.8"""

    arc_radius = width / 2
    n_seg = 32
    arc_depth = depth * 0.8

    bm = bmesh.new()

    center = (width / 2, 0, height)
    front_verts = []
    for i in range(n_seg + 1):
        angle = math.pi * i / n_seg
        x = center[0] + arc_radius * math.cos(angle)
        z = center[2] + arc_radius * math.sin(angle)
        front_verts.append(bm.verts.new((x, 0, z)))

    back_verts = []
    for i in range(n_seg + 1):
        angle = math.pi * i / n_seg
        x = center[0] + arc_radius * math.cos(angle)
        z = center[2] + arc_radius * math.sin(angle)
        back_verts.append(bm.verts.new((x, arc_depth, z)))

    for i in range(n_seg):
        bm.faces.new([front_verts[i], front_verts[i + 1],
                       back_verts[i + 1], back_verts[i]])

    bm.faces.new(front_verts)
    bm.faces.new(list(reversed(back_verts)))

    mesh = bpy.data.meshes.new("door_arc")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("door_arc", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Center Y on door depth
    obj.location.y = (depth - arc_depth) / 2
    apply_tf(obj, loc=True)

    return obj

# -- Handle: knob (revolution surface) ----------------------------------------
def make_revolution_surface(radii, depths, n_steps=24):
    """Create a solid of revolution around the Y axis using direct mesh construction.
    radii/depths: arrays of (radius, y_position) defining the profile.
    Returns a bmesh-based mesh object."""

    bm = bmesh.new()
    n_pts = len(radii)
    rings = []

    for i in range(n_pts):
        r = radii[i]
        y = depths[i]
        ring = []
        if r < 1e-6:
            # Degenerate ring: single vertex at center
            v = bm.verts.new((0, y, 0))
            ring.append(v)
        else:
            for j in range(n_steps):
                angle = 2 * math.pi * j / n_steps
                x = r * math.cos(angle)
                z = r * math.sin(angle)
                ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)

    # Connect adjacent rings with faces
    for i in range(n_pts - 1):
        r0 = rings[i]
        r1 = rings[i + 1]
        if len(r0) == 1 and len(r1) == 1:
            continue
        elif len(r0) == 1:
            # Fan from single vertex to ring
            center = r0[0]
            for j in range(n_steps):
                j1 = (j + 1) % n_steps
                bm.faces.new([center, r1[j], r1[j1]])
        elif len(r1) == 1:
            # Fan from ring to single vertex
            center = r1[0]
            for j in range(n_steps):
                j1 = (j + 1) % n_steps
                bm.faces.new([r0[j], center, r0[j1]])
        else:
            # Quad strip between two rings
            for j in range(n_steps):
                j1 = (j + 1) % n_steps
                bm.faces.new([r0[j], r1[j], r1[j1], r0[j1]])

    # Close the ends (cap the first ring if it's not a point)
    if len(rings[0]) > 2:
        bm.faces.new(rings[0])
    if len(rings[-1]) > 2:
        bm.faces.new(list(reversed(rings[-1])))

    mesh = bpy.data.meshes.new("revolution")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("revolution", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj

def make_knob(width, height, depth, handle_offset, handle_height):
    """Door knob using revolution surface matching source knob_radius_mid/knob_depth_mid."""

    knob_radius = np.random.uniform(0.03, 0.04)
    knob_depth_val = np.random.uniform(0.08, 0.1)

    # Source radius profile multipliers
    base_radius = np.random.uniform(1.1, 1.2)
    mid_radius = np.random.uniform(0.4, 0.5)
    tip_taper = np.random.uniform(0.6, 0.8)
    radius_mults = [base_radius, base_radius, mid_radius, mid_radius, 1.0, tip_taper, 0.0]

    # Source depth profile (normalized positions along Y)
    depth_mults = [0.0,
                   np.random.uniform(0.1, 0.15),
                   np.random.uniform(0.25, 0.3),
                   np.random.uniform(0.35, 0.45),
                   np.random.uniform(0.6, 0.8),
                   1.0,
                   1.0 + 1e-3]

    radii = np.array(radius_mults) * knob_radius
    depths = np.array(depth_mults) * knob_depth_val

    obj = make_revolution_surface(radii, depths, n_steps=24)

    # Position on back door face (y=depth), knob protrudes in +Y
    obj.location = (handle_offset, depth, handle_height)
    apply_tf(obj, loc=True)

    return obj

# -- Handle: lever (rosette + arm) --------------------------------------------
def make_lever(width, height, depth, handle_offset, handle_height):
    """Door lever: spin rosette + arm (wave/bent/cylinder type)."""

    lever_radius = np.random.uniform(0.03, 0.04)
    lever_mid_radius = np.random.uniform(0.01, 0.02)
    lever_depth_val = np.random.uniform(0.05, 0.08)
    lever_mid_depth = np.random.uniform(0.15, 0.25)
    lever_length = log_uniform(0.15, 0.2)
    lever_type = np.random.choice(["wave", "cylinder", "bent"])

    parts = []

    # Rosette (revolution surface) matching source
    radii = [lever_radius, lever_radius, lever_mid_radius, lever_mid_radius, 0.0]
    depths = np.array([0, lever_mid_depth, lever_mid_depth, 1.0, 1.0 + 1e-3]) * lever_depth_val

    rosette = make_revolution_surface(radii, depths, n_steps=16)
    parts.append(rosette)

    # Lever arm — build as extruded line with SOLIDIFY + SUBSURF
    n_arm_verts = 5
    bm = bmesh.new()
    averts = []
    for i in range(n_arm_verts):
        t = i / (n_arm_verts - 1)
        x = -t * lever_length
        z = 0.0
        if lever_type == "wave":
            if i == 1:
                z = -np.random.uniform(0.2, 0.3) * lever_length
            elif i == 3:
                z = np.random.uniform(0.1, 0.15) * lever_length
        elif lever_type == "bent" and i == n_arm_verts - 1:
            z = -np.random.uniform(0.2, 0.3) * lever_length
        averts.append(bm.verts.new((x, 0, z)))
    for i in range(len(averts) - 1):
        bm.edges.new((averts[i], averts[i + 1]))

    mesh = bpy.data.meshes.new("lever_arm")
    bm.to_mesh(mesh)
    bm.free()
    arm = bpy.data.objects.new("lever_arm", mesh)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)

    # Extrude edges upward, then solidify
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_edges_move(
        TRANSFORM_OT_translate={"value": (0, 0, lever_mid_radius * 2)})
    bpy.ops.object.mode_set(mode='OBJECT')

    add_mod(arm, "SOLIDIFY", thickness=lever_mid_radius, offset=0)
    add_mod(arm, "SUBSURF", render_levels=1, levels=1)

    arm.location = (-lever_mid_radius, lever_depth_val, -lever_mid_radius)
    apply_tf(arm, loc=True)
    parts.append(arm)

    result = join_objs(parts)

    # Position on back door face (y=depth), lever protrudes in +Y
    result.location = (handle_offset, depth, handle_height)
    apply_tf(result, loc=True)

    return result

# -- Handle: pull (U/T/Z shape) -----------------------------------------------
def make_pull(width, height, depth, handle_offset, handle_height):
    """Pull handle: U, T, or Z shape, circular or rectangular cross-section."""

    pull_size = log_uniform(0.1, 0.4)
    pull_depth_val = np.random.uniform(0.05, 0.08)
    pull_width_val = log_uniform(0.08, 0.15)
    pull_extension = np.random.uniform(0.05, 0.15)
    pull_radius = np.random.uniform(0.01, 0.02)
    pull_type = np.random.choice(["u", "tee", "zed"])
    is_circular = np.random.uniform() < 0.5 or pull_type == "zed"
    to_bevel = np.random.uniform() < 0.5
    bevel_width = np.random.uniform(0.02, 0.04)

    # Build edge skeleton
    bm = bmesh.new()
    if pull_type == "u":
        v0 = bm.verts.new((0, 0, pull_size))
        v1 = bm.verts.new((0, pull_depth_val, pull_size))
        v2 = bm.verts.new((0, pull_depth_val, 0))
        bm.edges.new((v0, v1))
        bm.edges.new((v1, v2))
    elif pull_type == "tee":
        v0 = bm.verts.new((0, 0, pull_size))
        v1 = bm.verts.new((0, pull_depth_val, pull_size))
        v2 = bm.verts.new((0, pull_depth_val, 0))
        v3 = bm.verts.new((0, pull_depth_val, pull_size + pull_extension))
        bm.edges.new((v0, v1))
        bm.edges.new((v1, v2))
        bm.edges.new((v1, v3))
    else:  # zed
        v0 = bm.verts.new((0, 0, pull_size))
        v1 = bm.verts.new((0, pull_depth_val, pull_size))
        v2 = bm.verts.new((pull_width_val, pull_depth_val, pull_size))
        v3 = bm.verts.new((pull_width_val, pull_depth_val, 0))
        bm.edges.new((v0, v1))
        bm.edges.new((v1, v2))
        bm.edges.new((v2, v3))

    mesh = bpy.data.meshes.new("pull_skel")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("pull_skel", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Mirror on Z axis (source: MIRROR use_axis=(False, False, True))
    add_mod(obj, "MIRROR", use_axis=(False, False, True))

    # Optional vertex bevel
    if to_bevel:
        add_mod(obj, "BEVEL", width=bevel_width, segments=4, affect='VERTICES')

    if is_circular:
        # Use GeoNodes: MeshToCurve → SetCurveRadius → CurveToMesh(circle)
        tree = bpy.data.node_groups.new("pull_geo_radius", 'GeometryNodeTree')
        tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

        inp = tree.nodes.new('NodeGroupInput')
        inp.location = (-400, 0)

        m2c = tree.nodes.new('GeometryNodeMeshToCurve')
        m2c.location = (-200, 0)
        tree.links.new(inp.outputs[0], m2c.inputs[0])

        scr = tree.nodes.new('GeometryNodeSetCurveRadius')
        scr.location = (0, 0)
        scr.inputs['Radius'].default_value = pull_radius
        tree.links.new(m2c.outputs[0], scr.inputs[0])

        circle = tree.nodes.new('GeometryNodeCurvePrimitiveCircle')
        circle.location = (0, -200)
        circle.inputs['Resolution'].default_value = 16
        circle.inputs['Radius'].default_value = 1.0

        c2m = tree.nodes.new('GeometryNodeCurveToMesh')
        c2m.location = (200, 0)
        tree.links.new(scr.outputs[0], c2m.inputs['Curve'])
        tree.links.new(circle.outputs[0], c2m.inputs['Profile Curve'])
        c2m.inputs['Fill Caps'].default_value = True
        # Scale input for Blender 5.0
        try:
            c2m.inputs['Scale'].default_value = pull_radius
        except (KeyError, IndexError):
            pass

        out = tree.nodes.new('NodeGroupOutput')
        out.location = (400, 0)
        tree.links.new(c2m.outputs[0], out.inputs[0])

        mod = obj.modifiers.new("geo", 'NODES')
        mod.node_group = tree
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    else:
        # Rectangular cross-section: extrude edges + solidify
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_edges_move(
            TRANSFORM_OT_translate={"value": (pull_radius * 2, 0, 0)})
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')

        obj.location = (-pull_radius, -pull_radius, -pull_radius)
        apply_tf(obj, loc=True)
        add_mod(obj, "SOLIDIFY", thickness=pull_radius * 2, offset=0)

    # Position on back door face (y=depth), pull protrudes in +Y
    obj.location = (handle_offset, depth, handle_height)
    apply_tf(obj, loc=True)

    return obj

# -- Handle: bar ---------------------------------------------------------------
def make_bar_handle(width, height, depth, handle_height):
    """Push bar handle: horizontal bar across the door width."""

    bar_length = width * np.random.uniform(0.7, 0.9)
    bar_thickness = height * np.random.uniform(0.025, 0.045)
    bar_aspect_ratio = np.random.uniform(0.4, 0.6)
    bar_height_ratio = np.random.uniform(0.7, 0.9)
    bar_length_ratio = np.random.uniform(0.5, 0.8)
    bar_end_length_ratio = np.random.uniform(0.1, 0.15)
    bar_end_height_ratio = np.random.uniform(1.8, 3.0)
    bar_z_offset = -np.random.uniform(0.0, 0.1) * height

    parts = []

    # Main horizontal bar
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    bar = bpy.context.active_object
    bar.scale = (bar_length / 2, bar_thickness * bar_aspect_ratio / 2,
                 bar_thickness * bar_height_ratio / 2)
    bar.location = (width / 2, depth + bar_thickness * 0.6,
                    handle_height + bar_z_offset)
    apply_tf(bar)
    parts.append(bar)

    # End mounting brackets
    end_w = bar_length * bar_end_length_ratio
    end_h = bar_thickness * bar_end_height_ratio
    end_depth = bar_thickness * 0.8
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        bracket = bpy.context.active_object
        bracket.scale = (end_w / 2, end_depth / 2, end_h / 2)
        bracket.location = (width / 2 + side * bar_length * bar_length_ratio / 2,
                            depth + end_depth / 2,
                            handle_height + bar_z_offset)
        apply_tf(bracket)
        parts.append(bracket)

    return join_objs(parts)

# -- Main builder --------------------------------------------------------------
def build_base_door():
    clear_scene()

    # Simulate RoomConstants
    wall_thickness = np.random.uniform(0.2, 0.3)
    segment_margin = 1.4
    door_width_ratio = np.random.uniform(0.7, 0.8)
    width = (segment_margin - wall_thickness) * door_width_ratio
    height = np.random.uniform(2.0, 2.4)
    depth = wall_thickness * log_uniform(0.25, 0.5)

    # Matching source parameter distributions
    panel_margin = log_uniform(0.08, 0.12)
    side_bevel = log_uniform(0.005, 0.015)

    # Door frame style (4 options matching source)
    frame_style = np.random.choice([
        "single_column", "full_frame_square",
        "full_frame_dome", "full_frame_double_door"])
    frame_width = np.random.uniform(0.02, 0.06)

    is_double_door = (frame_style == "full_frame_double_door")
    top_dome = (frame_style == "full_frame_dome")

    # Handle type (matching source)
    handle_type = np.random.choice(["knob", "lever", "pull", "bar", "none"])

    # Handle positioning (matching source: handle_offset = panel_margin * 0.5)
    handle_offset = panel_margin * 0.5
    handle_height = height * np.random.uniform(0.45, 0.50)

    # Center z offset for dome style (matches source)
    if top_dome:
        center_z_offset = -0.25 * width - frame_width / 4
    else:
        center_z_offset = 0.0

    parts = []

    door = make_door_slab(width, height, depth)
    door.name = "door_body"
    if center_z_offset != 0:
        door.location.z = center_z_offset
        apply_tf(door, loc=True)
    door.data.materials.append(WOOD_MAT)
    parts.append(door)

    # Second door slab for double door (mirrored) → WOOD_MAT
    if is_double_door:
        door2 = make_door_slab(width, height, depth)
        door2.name = "door_body_2"
        door2.location.x = width
        if center_z_offset != 0:
            door2.location.z = center_z_offset
        apply_tf(door2, loc=True)
        door2.data.materials.append(WOOD_MAT)
        parts.append(door2)

    # Door frame → WOOD_MAT
    frame = make_door_frame(width, height, depth, frame_width, frame_style, is_double_door)
    if frame:
        if center_z_offset != 0:
            frame.location.z = center_z_offset
            apply_tf(frame, loc=True)
        frame.data.materials.append(WOOD_MAT)
        parts.append(frame)

    # Door arc (dome top) → WOOD_MAT (default; picks "door"/"glass" 50/50)
    if top_dome:
        arc = make_door_arc(width, height, depth)
        if center_z_offset != 0:
            arc.location.z = center_z_offset
            apply_tf(arc, loc=True)
        arc.data.materials.append(WOOD_MAT)
        parts.append(arc)

    # Handle → HANDLE_MAT (self.handle_surface / metal_neutral)
    handle = None
    h_offset_x = handle_offset
    h_height = handle_height
    if center_z_offset != 0:
        h_height += center_z_offset

    if handle_type == "knob":
        handle = make_knob(width, height, depth, h_offset_x, h_height)
    elif handle_type == "lever":
        handle = make_lever(width, height, depth, h_offset_x, h_height)
    elif handle_type == "pull":
        handle = make_pull(width, height, depth, h_offset_x, h_height)
    elif handle_type == "bar":
        handle = make_bar_handle(width, height, depth, h_height)

    if handle and handle_type != "bar":
        handle = mirror_handle_y(handle, depth)

    if handle:
        handle.data.materials.append(BAR_HANDLE_MAT if handle_type == "bar" else HANDLE_MAT)
        parts.append(handle)

    result = join_objs(parts)

    # Apply bevel matching source (side_bevel on sharp edges)
    add_mod(result, "BEVEL", width=side_bevel, segments=1, limit_method='ANGLE',
            angle_limit=math.radians(30))

    result.name = "BaseDoorFactory"
    # Per-part materials were appended before join; slots preserved automatically.
    if result is not None and len(result.data.materials) == 0:
        result.data.materials.append(WOOD_MAT)
    return result

door = build_base_door()

