# [FL_INDEX: keywords="blender_factory, procedural_3d, JellyfishFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: JellyfishFactory | Category: factories_geo
# Prompt: A jellyfish rendered as a textured 3D model. The creature features a large, translucent, softly lobed bell-shaped dome at the top in a delicate pale pink-lavender color with subtle faceted geometry on the surface. From beneath the bell, numerous long, extremely thin, wispy tentacles drape downward in a flowing, tangled cascade, rendered with translucent pink thread-like geometry. A single thicker, ribbon-like central oral arm spirals downward through the tentacle mass. The entire creature is semi-transparent, creating a luminous, ethereal quality. A blurred dark shadow appears beneath the tentacle mass.

import os
import math

import bmesh
import bpy
import numpy as np

SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
import random as _random, colorsys as _colorsys

def _seed_mat(seed):
    _mat_seed = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_mat_seed); _random.seed(_mat_seed)

def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h) % 1.0, max(0, min(1, float(s))), max(0, min(1, float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def _build_float_curve(nt, link_fn, input_socket, anchors):
    """Replicate NodeWrangler.build_float_curve: FloatCurve node with custom control points."""

    fc = nt.nodes.new("ShaderNodeFloatCurve")
    link_fn(input_socket, fc.inputs["Value"])
    curve = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
        curve.points[i].handle_type = "VECTOR"
    fc.mapping.use_clip = False
    return fc


def _shader_jellyfish(nt, base_hue, saturation, transparency_val, transparency_is_noise=False):
    """

    Topology: LayerWeight -> FloatCurve -> MixShader(emission, MixShader(glossy, transparent))
              -> MixShader(transparency, ..., transparent2) -> OutputMaterial
    """

    ln = nt.links.new

    emission_color = _hsv2rgba(base_hue, float(np.random.uniform(0.4, 0.6)), 1.0)
    transparent_color = _hsv2rgba(
        (base_hue + float(np.random.uniform(-0.1, 0.1))) % 1, saturation, 1.0
    )
    glossy_rough = float(np.random.uniform(0.8, 1.0))

    # 1. LayerWeight -> FloatCurve (fresnel remap)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.3
    curve_x = float(np.random.uniform(0.6, 0.9))
    fc = _build_float_curve(nt, ln, lw.outputs["Facing"],
                            [(0, 0), (0.4, 0), (curve_x, 1), (1, 1)])

    # 2. Emission
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = emission_color

    # 3. Glossy + Transparent -> mix1(0.5)
    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Color"].default_value = transparent_color
    glossy.inputs["Roughness"].default_value = glossy_rough
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    trans.inputs["Color"].default_value = transparent_color

    mix1 = nt.nodes.new("ShaderNodeMixShader")
    mix1.inputs["Fac"].default_value = 0.5
    ln(glossy.outputs["BSDF"], mix1.inputs[1])
    ln(trans.outputs["BSDF"], mix1.inputs[2])

    # 4. MixShader(float_curve, emission, mix1) -> mix2
    mix2 = nt.nodes.new("ShaderNodeMixShader")
    ln(fc.outputs["Value"], mix2.inputs["Fac"])
    ln(emit.outputs["Emission"], mix2.inputs[1])
    ln(mix1.outputs["Shader"], mix2.inputs[2])

    # 5. Final transparency: MixShader(transparency, mix2, transparent2)
    trans2 = nt.nodes.new("ShaderNodeBsdfTransparent")
    trans2.inputs["Color"].default_value = transparent_color

    mix3 = nt.nodes.new("ShaderNodeMixShader")
    if transparency_is_noise:
        # Dotted variant: NoiseTexture -> FloatCurve as transparency factor
        noise_scale = float(np.random.uniform(20, 50))
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = noise_scale
        noise_out = noise.outputs.get("Factor") or noise.outputs.get("Fac") or noise.outputs[0]
        dot_anchors = [
            (0, float(np.random.uniform(0.92, 0.96))),
            (0.62, float(np.random.uniform(0.92, 0.96))),
            (0.65, float(np.random.uniform(0.5, 0.6))),
            (1, float(np.random.uniform(0.5, 0.6))),
        ]
        dot_fc = _build_float_curve(nt, ln, noise_out, dot_anchors)
        ln(dot_fc.outputs["Value"], mix3.inputs["Fac"])
    else:
        mix3.inputs["Fac"].default_value = transparency_val

    ln(mix2.outputs["Shader"], mix3.inputs[1])
    ln(trans2.outputs["BSDF"], mix3.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix3.outputs["Shader"], out.inputs["Surface"])


def _make_jellyfish_mat(name, base_hue, saturation, transparency_val,
                        transparency_is_noise=False):
    mat = _new_mat(name)
    _shader_jellyfish(mat.node_tree, base_hue, saturation, transparency_val,
                      transparency_is_noise)
    return mat


def make_jellyfish_materials(seed):
    """

    Returns dict of: outside, inside, tentacle, arm_transparent, arm_opaque, arm_solid.
    Seeded via np.random.seed(seed) to match FixedSeed(factory_seed).
    """

    np.random.seed(seed); _random.seed(seed)
    base_hue = float(np.random.normal(0.57, 0.15))

    # outside: 80% transparent, 20% dotted
    hue = (base_hue + float(np.random.uniform(-0.1, 0.1))) % 1
    if np.random.uniform() < 0.8:
        outside = _make_jellyfish_mat("jf_outside", hue,
                                      float(np.random.uniform(0.1, 0.3)),
                                      float(np.random.uniform(0.88, 0.92)))
    else:
        outside = _make_jellyfish_mat("jf_outside", hue,
                                      float(np.random.uniform(0.5, 0.8)),
                                      0.0, transparency_is_noise=True)

    # inside: 80% transparent, 20% opaque
    hue = (base_hue + float(np.random.uniform(-0.1, 0.1))) % 1
    if np.random.uniform() < 0.8:
        inside = _make_jellyfish_mat("jf_inside", hue,
                                     float(np.random.uniform(0.1, 0.3)),
                                     float(np.random.uniform(0.88, 0.92)))
    else:
        inside = _make_jellyfish_mat("jf_inside", hue,
                                     float(np.random.uniform(0.3, 0.6)),
                                     float(np.random.uniform(0.75, 0.8)))

    # tentacle: transparent
    hue = (base_hue + float(np.random.uniform(-0.1, 0.1))) % 1
    tentacle = _make_jellyfish_mat("jf_tentacle", hue,
                                   float(np.random.uniform(0.1, 0.3)),
                                   float(np.random.uniform(0.88, 0.92)))

    # arm materials
    hue = (base_hue + float(np.random.uniform(-0.1, 0.1))) % 1
    arm_transparent = _make_jellyfish_mat("jf_arm_trans", hue,
                                          float(np.random.uniform(0.1, 0.3)),
                                          float(np.random.uniform(0.88, 0.92)))
    hue = (base_hue + float(np.random.uniform(-0.1, 0.1))) % 1
    arm_opaque = _make_jellyfish_mat("jf_arm_opaque", hue,
                                     float(np.random.uniform(0.3, 0.6)),
                                     float(np.random.uniform(0.75, 0.8)))
    hue = (base_hue + float(np.random.uniform(-0.1, 0.1))) % 1
    arm_solid = _make_jellyfish_mat("jf_arm_solid", hue,
                                    float(np.random.uniform(0.5, 0.8)),
                                    float(np.random.uniform(0.4, 0.5)))

    return {
        "outside": outside, "inside": inside, "tentacle": tentacle,
        "arm_transparent": arm_transparent, "arm_opaque": arm_opaque,
        "arm_solid": arm_solid,
    }


# Phase 1: creature materials (all slots)
MATS = make_jellyfish_materials(SEED)
np.random.seed(SEED)


# ── helpers ──────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.curves):
        bpy.data.curves.remove(block)
    for block in list(bpy.data.textures):
        bpy.data.textures.remove(block)

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_tf(obj, loc=True, rot=True, scale=True):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

def log_uniform(rng, lo, hi):
    return np.exp(rng.uniform(np.log(lo), np.log(hi)))

# ── bell / cap ───────────────────────────────────────────────────────────────

def apply_cap_dent(obj, cap_dent, rng):
    """Apply radial dents to bell surface for organic lobed shape.

    Original: polygon_angles -> per-vertex radial scaling based on angular
    proximity to random dent positions.
    """

    n_dent = rng.randint(6, 12)
    angles = np.sort(rng.uniform(0, 2 * math.pi, n_dent))
    dent_scales = rng.uniform(1 - cap_dent, 1, n_dent)
    margins = rng.uniform(0.02 * math.pi, 0.05 * math.pi, n_dent)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for v in bm.verts:
        angle = math.atan2(v.co.y, v.co.x) % (2 * math.pi)
        dists = np.abs(angles - angle)
        dists = np.minimum(dists, 2 * math.pi - dists)
        idx = int(np.argmin(dists))
        min_dist = dists[idx]

        if min_dist < margins[idx]:
            t = 1.0 - min_dist / margins[idx]
            s = 1.0 - (1.0 - dent_scales[idx]) * t
            v.co.x *= s
            v.co.y *= s
    bm.to_mesh(obj.data)
    bm.free()

def build_cap(cap_z_scale, cap_thickness, cap_inner_radius, cap_dent, rng):
    """Hollow bell dome.

    Original pipeline:
      1. Icosphere (6 subdivisions)
      2. Boolean DIFFERENCE with inner cutter sphere
      3. Remove lower hemisphere (z < -0.05)
      4. Optional radial denting
      5. Scale xy (0.4-0.6 each), z *= cap_z_scale
      6. Subdivision surface
    """
    # 1. outer sphere
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1.0)
    outer = bpy.context.active_object
    outer.name = "cap_outer"

    # 2. inner cutter sphere
    d = math.sqrt(max(0, 1 - cap_inner_radius ** 2)) + 1 - cap_thickness
    r_cut = (d * d + cap_inner_radius ** 2) / (2 * d)

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=r_cut)
    cutter = bpy.context.active_object
    cutter.location.z = 1 - cap_thickness - r_cut
    apply_tf(cutter)

    # boolean difference
    bool_m = outer.modifiers.new("bool", "BOOLEAN")
    bool_m.operation = "DIFFERENCE"
    bool_m.object = cutter
    select_only(outer)
    bpy.ops.object.modifier_apply(modifier=bool_m.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

    # 3. remove lower hemisphere
    bm = bmesh.new()
    bm.from_mesh(outer.data)
    to_del = [v for v in bm.verts if v.co.z < -0.05]
    bmesh.ops.delete(bm, geom=to_del, context="VERTS")
    bm.to_mesh(outer.data)
    bm.free()

    # 4. optional denting
    if cap_dent > 0:
        apply_cap_dent(outer, cap_dent, rng)

    # 5. scale
    sx = rng.uniform(0.4, 0.6)
    sy = rng.uniform(0.4, 0.6)
    outer.scale = (sx, sy, min(sx, sy) * cap_z_scale)
    apply_tf(outer)

    # 6. subdivision
    m = outer.modifiers.new("subsurf", "SUBSURF")
    m.levels = 2
    m.render_levels = 2
    select_only(outer)
    bpy.ops.object.modifier_apply(modifier=m.name)

    radius = cap_inner_radius * min(outer.dimensions.x, outer.dimensions.y) * 0.5
    return outer, radius

# ── arm / tentacle builder ───────────────────────────────────────────────────

def build_arm(size, length, bend_angle, length_scale, seed_i):
    """Screw-spiral arm or tentacle.

    Used for BOTH oral arms (thick) and tentacles (thin) -- same as original.
    Pipeline:
      1. Circle(16) -> elliptical scale -> remove half -> half-profile
      2. Screw modifier with tilted empty axis object -> curved spiral
      3. SIMPLE_DEFORM TAPER -> thick-to-thin
      4. MARBLE displacement x 2 -> wavy surface detail
      5. SIMPLE_DEFORM BEND -> overall curvature
      6. Recenter based on top vertices
    """

    rng = np.random.RandomState(SEED + seed_i)

    # 1. half-ellipse profile
    bpy.ops.mesh.primitive_circle_add(vertices=16, radius=1.0)
    arm = bpy.context.active_object
    arm.name = f"arm_{seed_i}"
    arm.scale = (size, size * rng.uniform(0.0, 1.0), 1.0)
    apply_tf(arm)

    bm = bmesh.new()
    bm.from_mesh(arm.data)
    flip = (-1) ** rng.randint(2)
    to_del = [v for v in bm.verts if v.co.y * flip > 0]
    bmesh.ops.delete(bm, geom=to_del, context="VERTS")
    bm.to_mesh(arm.data)
    bm.free()

    # 2. screw with tilted empty axis -> curved spiral
    empty = bpy.data.objects.new(f"axis_{seed_i}", None)
    empty.location = (0, 0, 1)
    empty.rotation_euler.y = -rng.uniform(0, math.pi / 24)
    bpy.context.scene.collection.objects.link(empty)

    screw = arm.modifiers.new("screw", "SCREW")
    screw.object = empty
    screw_sign = (-1) ** rng.randint(2)
    screw.angle = log_uniform(rng, 0.5, 3.0) * math.pi * screw_sign
    screw.screw_offset = -length * length_scale * rng.uniform(0.5, 1.0)
    screw.steps = 256
    screw.render_steps = 256
    select_only(arm)
    bpy.ops.object.modifier_apply(modifier=screw.name)

    bpy.data.objects.remove(empty, do_unlink=True)

    # 3. taper
    m = arm.modifiers.new("taper", "SIMPLE_DEFORM")
    m.deform_method = "TAPER"
    m.factor = rng.uniform(0.5, 1.0)
    m.deform_axis = "Z"
    select_only(arm)
    bpy.ops.object.modifier_apply(modifier=m.name)

    # 4. marble displacement x 2
    for pass_i, (direction, s_range, n_range) in enumerate([
        ("Y", (0.01, 0.02), (0.1, 0.2)),   # subtle
        ("X", (0.1,  0.2),  (0.1, 2.0)),   # stronger
    ]):
        tex = bpy.data.textures.new(f"marble_{seed_i}_{pass_i}", "MARBLE")
        tex.noise_scale = log_uniform(rng, n_range[0], n_range[1])

        disp = arm.modifiers.new(f"disp_{pass_i}", "DISPLACE")
        disp.texture = tex
        disp.direction = direction
        if pass_i == 0:
            disp.strength = rng.uniform(s_range[0], s_range[1])
        else:
            disp.strength = log_uniform(rng, s_range[0], s_range[1])
        select_only(arm)
        bpy.ops.object.modifier_apply(modifier=disp.name)

    # 5. bend
    if bend_angle > 0:
        factor = bend_angle * log_uniform(rng, 0.5, 1.5)
        m = arm.modifiers.new("bend", "SIMPLE_DEFORM")
        m.deform_method = "BEND"
        m.deform_axis = "Y"
        m.angle = factor
        select_only(arm)
        bpy.ops.object.modifier_apply(modifier=m.name)

    # 6. recenter based on top vertices
    co = np.array([list(v.co) for v in arm.data.vertices])
    if len(co) > 0:
        top_mask = co[:, 2] > -0.01
        if top_mask.any():
            center = co[top_mask].mean(axis=0)
            arm.location.x -= center[0]
            arm.location.y -= center[1]
            apply_tf(arm, loc=True, rot=False, scale=False)

    return arm

# ── placement ────────────────────────────────────────────────────────────────

def place_arms(cap, n_arms, arm_size, arm_length, arm_bend_angle,
               length_scale, radius, rng):
    """Place thick spiral oral arms on the underside of the bell."""

    arms = []
    for i in range(n_arms):
        arm = build_arm(size=arm_size, length=arm_length,
                        bend_angle=arm_bend_angle,
                        length_scale=length_scale, seed_i=i)

        angle = 2 * math.pi * i / n_arms + rng.uniform(-0.3, 0.3)
        r = rng.uniform(radius * 0.3, radius * 0.8)
        arm.location = (r * math.cos(angle),
                        r * math.sin(angle),
                        rng.uniform(-0.1, 0.0))
        arm.rotation_euler.z = (math.atan2(math.sin(angle), math.cos(angle))
                                + math.pi + rng.uniform(-math.pi / 6, math.pi / 6))
        apply_tf(arm)
        arms.append(arm)
    return arms

def place_tentacles(cap, n_tentacles, tentacle_size, tentacle_length,
                    tentacle_bend_angle, length_scale, radius, rng):
    """Place thin spiral tentacles along the bell rim boundary."""

    tentacles = []
    rim_r = radius * 0.95
    for i in range(n_tentacles):
        t = build_arm(size=tentacle_size, length=tentacle_length,
                      bend_angle=tentacle_bend_angle,
                      length_scale=length_scale, seed_i=200 + i)

        angle = (2 * math.pi * i / n_tentacles
                 + rng.uniform(-0.1, 0.1))
        t.location = (rim_r * math.cos(angle),
                      rim_r * math.sin(angle),
                      0.0)
        t.rotation_euler.z = (angle + math.pi
                              + rng.uniform(-math.pi / 6, math.pi / 6))
        apply_tf(t)
        tentacles.append(t)
    return tentacles

# ── main assembly ────────────────────────────────────────────────────────────

def build_jellyfish():
    clear_scene()
    rng = np.random.RandomState(SEED)

    # ── sample parameters (matching original distributions) ──
    has_arm = rng.uniform() < 0.5

    cap_thickness    = rng.uniform(0.05, 0.6)
    cap_inner_radius = rng.uniform(0.6, 0.8)
    cap_z_scale      = log_uniform(rng, 0.4, 1.5)
    cap_dent         = rng.uniform(0.15, 0.3) if rng.uniform() < 0.5 else 0.0

    length_scale = log_uniform(rng, 0.25, 2.0)

    # arm params
    arm_radius      = rng.uniform(0, 0.3)
    arm_size         = rng.uniform(0.03, 0.06)
    arm_length       = log_uniform(rng, 2, 5)
    arm_bend_angle   = rng.uniform(0, math.pi / 60)
    arm_min_distance = rng.uniform(0.06, 0.08)

    # tentacle params
    tentacle_size         = rng.uniform(0.005, 0.01)
    tentacle_length       = log_uniform(rng, 1.5, 2.5)
    tentacle_bend_angle   = rng.uniform(0, math.pi / 12)
    tentacle_min_distance = rng.uniform(0.04, 0.06)

    # ── 1. build bell ──
    cap, radius = build_cap(cap_z_scale, cap_thickness, cap_inner_radius,
                            cap_dent, rng)

    # ── 2. twist + bend deformations ──
    for axis in ["X", "Y"]:
        m = cap.modifiers.new("twist", "SIMPLE_DEFORM")
        m.deform_method = "TWIST"
        m.deform_axis = axis
        m.angle = rng.uniform(-math.pi / 3, math.pi / 3)
        select_only(cap)
        bpy.ops.object.modifier_apply(modifier=m.name)

    for axis in ["X", "Y"]:
        m = cap.modifiers.new("bend", "SIMPLE_DEFORM")
        m.deform_method = "BEND"
        m.deform_axis = axis
        m.angle = rng.uniform(-math.pi / 3, math.pi / 3)
        select_only(cap)
        bpy.ops.object.modifier_apply(modifier=m.name)

    # Assign materials to cap: outside (slot 0) + inside (slot 1)
    cap.data.materials.append(MATS["outside"])
    cap.data.materials.append(MATS["inside"])
    # Here we approximate: downward-facing normals = inside.
    bm = bmesh.new()
    bm.from_mesh(cap.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        if f.normal.z < 0:
            f.material_index = 1
    bm.to_mesh(cap.data)
    bm.free()

    all_parts = [cap]

    # ── 3. oral arms (thick spirals inside bell) ──
    if has_arm:
        n_arms = min(10, max(3, int(2 * math.pi * radius / arm_min_distance)))
        arms = place_arms(cap, n_arms, arm_size, arm_length, arm_bend_angle,
                          length_scale, radius, rng)
        arm_mat_choices = [MATS["arm_transparent"], MATS["arm_opaque"], MATS["arm_solid"]]
        mat_rng = np.random.RandomState(SEED + 9999)
        for arm in arms:
            chosen_mat = arm_mat_choices[mat_rng.randint(len(arm_mat_choices))]
            arm.data.materials.append(chosen_mat)
        all_parts.extend(arms)

    # ── 4. tentacles (thin spirals on bell rim) ──
    n_tentacles = min(30, max(8, int(2 * math.pi * radius / tentacle_min_distance)))
    tentacles = place_tentacles(cap, n_tentacles, tentacle_size, tentacle_length,
                                tentacle_bend_angle, length_scale, radius, rng)
    for t in tentacles:
        t.data.materials.append(MATS["tentacle"])
    all_parts.extend(tentacles)

    # ── 5. join ──
    bpy.ops.object.select_all(action="DESELECT")
    result = join_objs(all_parts)
    return result

jellyfish = build_jellyfish()
jellyfish.name = "JellyfishFactory"
