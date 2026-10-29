# [FL_INDEX: keywords="blender_factory, procedural_3d, UrchinFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: UrchinFactory | Category: factories_geo
# Prompt: A 3D model of a sea urchin rendered from a top-down perspective. The urchin features a rounded central body covered in dense, long, sharp spines radiating outward in all directions, with a deep reddish-purple coloring concentrated at the spine tips and a darker core.

import os
import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import noise, Vector

SEED = int(os.environ.get("SEED", 0))# Urchin materials — port of shader_spikes / shader_girdle / shader_base
import colorsys as _colorsys

def _seed_mat(seed):
    # Separate material RNG from geometry RNG; hash prevents seed=0 trivial collision.
    _s = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s)
    random.seed(_s)

def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(
        float(h) % 1.0, max(0.0, min(1.0, float(s))), max(0.0, min(1.0, float(v)))
    )
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m

def _set_input(bsdf, key, value):
    if key in bsdf.inputs:
        bsdf.inputs[key].default_value = value

def _make_spike_mat(base_hue, name="urchin_spike"):
    """shader_spikes: translucent/SSS principled BSDF."""

    transmission = float(np.random.uniform(0.95, 0.99))
    subsurface = float(np.random.uniform(0.1, 0.2))
    roughness = float(np.random.uniform(0.5, 0.8))
    color = _hsv2rgba(base_hue, np.random.uniform(0.5, 1.0), _log_uniform(0.05, 1.0))

    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    # Blender 5.0 Principled uses "Subsurface Weight"; 4.x uses "Subsurface".
    _set_input(bsdf, "Subsurface Weight", subsurface)
    _set_input(bsdf, "Subsurface", subsurface)
    _set_input(bsdf, "Subsurface Color", color)
    # 5.0 uses "Transmission Weight"; 4.x uses "Transmission".
    _set_input(bsdf, "Transmission Weight", transmission)
    _set_input(bsdf, "Transmission", transmission)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def _make_matte_mat(base_hue, sat_lo, sat_hi, val_lo, val_hi, name):
    """shader_girdle / shader_base: plain matte principled BSDF."""

    roughness = float(np.random.uniform(0.5, 0.8))
    color = _hsv2rgba(
        base_hue, np.random.uniform(sat_lo, sat_hi), _log_uniform(val_lo, val_hi)
    )

    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_urchin_materials(seed):
    """Build (spike, girdle, base) — matches __init__ RNG order: base_hue then three shaders."""

    _seed_mat(seed)
    base_hue = float(np.random.uniform(-0.25, 0.15)) % 1.0
    spike_mat = _make_spike_mat(base_hue, "urchin_spike")
    girdle_mat = _make_matte_mat(base_hue, 0.4, 0.5, 0.02, 0.1, "urchin_girdle")
    base_mat = _make_matte_mat(base_hue, 0.8, 1.0, 0.01, 0.02, "urchin_base")
    return spike_mat, girdle_mat, base_mat

# Phase 1 — material sampling (own seed chain keeps it independent from geometry RNG)
SPIKE_MAT, GIRDLE_MAT, BASE_MAT = make_urchin_materials(SEED)

# Phase 2 — reset RNG for geometry
np.random.seed(SEED)
random.seed(SEED)

def clear_scene():
    bpy.context.scene.cursor.location = (0, 0, 0)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def log_uniform(lo, hi, rng):
    return float(np.exp(rng.uniform(np.log(lo), np.log(hi))))

def apply_geo_extension(obj, rng):
    """Displace each vertex radially based on a noise function, creating
    organic surface variation on the icosphere.
    """

    noise_strength = float(rng.uniform(0.1, 0.2))
    noise_scale = float(rng.uniform(1.4, 2.8))
    direction_offset = rng.uniform(-1, 1, 3)

    mesh = obj.data
    for v in mesh.vertices:
        pos = Vector(v.co)
        length = pos.length
        if length < 1e-6:
            continue
        direction = pos / length
        dir_offset = Vector((
            direction.x + direction_offset[0],
            direction.y + direction_offset[1],
            direction.z + direction_offset[2],
        ))
        noise_val = noise.noise(dir_offset * noise_scale)
        displacement = (noise_val + 0.25) * noise_strength
        v.co = pos + pos * displacement

    mesh.update()

def build(seed=SEED):
    rng = np.random.default_rng(seed)
    np.random.seed(seed)
    clear_scene()

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object

    apply_geo_extension(obj, rng)

    obj.scale.z = float(rng.uniform(0.8, 1.0))  # flatten Z
    apply_tf(obj)

    bv = obj.modifiers.new("bevel", "BEVEL")
    bv.offset_type = 'PERCENT'
    bv.width_pct = 25
    bv.angle_limit = 0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bv.name)

    # bmesh extrusion: tag faces spike/girdle during extrude for material slot mapping
    girdle_height = 0.1
    extrude_height = log_uniform(1.0, 5.0, rng)
    girdle_size = float(rng.uniform(0.6, 1.0))
    face_prob = 0.98
    perturb = 0.1

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Integer face layer: 0=base (default), 1=girdle, 2=spike.
    mat_layer = bm.faces.layers.int.new("urchin_mat_tag")

    spike_faces = [f for f in bm.faces
                   if len(f.verts) >= 5 and rng.random() < face_prob]

    for face in spike_faces:
        n = face.normal.copy()
        n_arr = np.array([n.x, n.y, n.z])
        n_perturb = n_arr + np.array([
            float(rng.uniform(-perturb, perturb)),
            float(rng.uniform(-perturb, perturb)),
            float(rng.uniform(-perturb, perturb))
        ])
        n_perturb_norm = n_perturb / (np.linalg.norm(n_perturb) + 1e-8)

        ret = bmesh.ops.extrude_face_region(bm, geom=[face])
        extruded_verts = [v for v in ret['geom'] if isinstance(v, bmesh.types.BMVert)]
        for v in extruded_verts:
            v.co += face.normal * girdle_height

        ext_faces = [f2 for f2 in ret['geom'] if isinstance(f2, bmesh.types.BMFace)]
        if not ext_faces:
            continue
        ext_face = ext_faces[0]

        fc = sum((v.co for v in ext_face.verts), Vector((0, 0, 0))) / len(ext_face.verts)
        for v in ext_face.verts:
            v.co = fc + (v.co - fc) * girdle_size

        # Extrude back down — side faces form the girdle ring (tag=1)
        ret1b = bmesh.ops.extrude_face_region(bm, geom=[ext_face])
        girdle_verts = [v for v in ret1b['geom'] if isinstance(v, bmesh.types.BMVert)]
        for v in girdle_verts:
            v.co -= face.normal * girdle_height
        girdle_faces_new = [f2 for f2 in ret1b['geom'] if isinstance(f2, bmesh.types.BMFace)]
        if not girdle_faces_new:
            continue
        girdle_face = girdle_faces_new[0]
        for f2 in girdle_faces_new:
            if f2 is not girdle_face:
                f2[mat_layer] = 1

        sp_height = float(rng.uniform(0.5 * extrude_height, extrude_height))
        ret2 = bmesh.ops.extrude_face_region(bm, geom=[girdle_face])
        spike_verts = [v for v in ret2['geom'] if isinstance(v, bmesh.types.BMVert)]
        for v in spike_verts:
            _d = n_perturb_norm * sp_height
            v.co.x += float(_d[0])
            v.co.y += float(_d[1])
            v.co.z += float(_d[2])

        spike_faces2 = [f2 for f2 in ret2['geom'] if isinstance(f2, bmesh.types.BMFace)]
        for sf in spike_faces2:
            sf[mat_layer] = 2
            fc2 = sum((v.co for v in sf.verts), Vector((0, 0, 0))) / len(sf.verts)
            for v in sf.verts:
                v.co = fc2 + (v.co - fc2) * 0.2

    tags = [f[mat_layer] for f in bm.faces]
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()

    slot_map = {0: 2, 1: 1, 2: 0}
    mat_indices = np.fromiter((slot_map[t] for t in tags), dtype=np.int32,
                              count=len(tags))
    obj.data.polygons.foreach_set("material_index", mat_indices)
    obj.data.update()

    ss = obj.modifiers.new("subsurf", "SUBSURF")
    ss.levels = 1
    ss.render_levels = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=ss.name)

    dims = max(obj.dimensions[:])
    if dims > 0:
        s = 2.0 / dims
        z_scale = log_uniform(0.6, 1.2, rng)
        obj.scale = (s, s, s * z_scale)
    apply_tf(obj)

    tex = bpy.data.textures.new("urchin_t", type="STUCCI")
    tex.noise_scale = 0.05
    disp = obj.modifiers.new("disp", "DISPLACE")
    disp.texture = tex
    disp.strength = 0.005
    disp.mid_level = 0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=disp.name)

    apply_tf(obj)
    obj.name = "UrchinFactory"

    obj.data.materials.clear()
    obj.data.materials.append(SPIKE_MAT)
    obj.data.materials.append(GIRDLE_MAT)
    obj.data.materials.append(BASE_MAT)

    return obj

build(SEED)
