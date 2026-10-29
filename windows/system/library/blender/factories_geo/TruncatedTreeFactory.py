# [FL_INDEX: keywords="blender_factory, procedural_3d, TruncatedTreeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TruncatedTreeFactory | Category: factories_geo
# Prompt: A truncated tree stump rendered as a textured 3D model. The object depicts the lower portion of a felled or broken tree — a thick, upright cylindrical stump with no branches or crown. The bark surface on the lower half is extremely rough and coarse with a large-grained bumpy texture in sandy tan-brown. The upper half transitions to dramatic jagged, splintered wood fiber geometry — pale cream-colored sharp splinters and torn wood fragments project upward from the break point, creating a highly irregular, explosive silhouette at the top. This represents the raw, splintered cross-section of a snapped or broken tree.

"""TruncatedTreeFactory -- standalone Blender script.

Parametric trunk with noise bark detail, ring-wave cross-section on top cap.
Bark and ring materials derived from SEED.

Usage:
    blender --background --python TruncatedTreeFactory.py
"""


import colorsys
import math
import os

import bpy
import numpy as np
from mathutils import Vector, noise as mnoise

SEED = int(os.environ.get("SEED", 0))
# SEED-deterministic: np.random.seed(seed) called at top of build_truncated_tree(); materials use that seeded state


def sel_none():
    for obj in list(bpy.context.selected_objects):
        obj.select_set(False)


def set_active(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def apply_tf(obj, loc=False):
    sel_none()
    set_active(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    sel_none()


def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)


def smoothstep(edge0, edge1, x):
    if edge0 == edge1:
        return 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.textures,
        bpy.data.images,
        bpy.data.curves,
    ):
        for item in list(block):
            if item.users == 0:
                block.remove(item)
    bpy.context.scene.cursor.location = (0, 0, 0)


def create_mesh_object(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj


def create_bark_material(base_hue=None):
    if base_hue is None:
        base_hue = np.random.uniform(0.02, 0.08)
    mat = bpy.data.materials.new("BarkMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value = 0.85
    links.new(bsdf.outputs[0], output.inputs[0])
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    noise_col = nodes.new('ShaderNodeTexNoise')
    noise_col.location = (-400, 200)
    noise_col.inputs['Scale'].default_value = np.random.uniform(8, 15)
    noise_col.inputs['Detail'].default_value = 6.0
    links.new(tex_coord.outputs['Object'], noise_col.inputs['Vector'])
    dark_r, dark_g, dark_b = colorsys.hsv_to_rgb(
        base_hue, np.random.uniform(0.5, 0.8), np.random.uniform(0.10, 0.22))
    bright_r, bright_g, bright_b = colorsys.hsv_to_rgb(
        base_hue, np.random.uniform(0.4, 0.7), np.random.uniform(0.35, 0.65))
    mix_col = nodes.new('ShaderNodeMix')
    mix_col.location = (0, 200)
    mix_col.data_type = 'RGBA'
    mix_col.inputs[6].default_value = (dark_r, dark_g, dark_b, 1)
    mix_col.inputs[7].default_value = (bright_r, bright_g, bright_b, 1)
    links.new(noise_col.outputs[0], mix_col.inputs[0])
    links.new(mix_col.outputs[2], bsdf.inputs['Base Color'])
    noise_bump1 = nodes.new('ShaderNodeTexNoise')
    noise_bump1.location = (-400, -100)
    noise_bump1.inputs['Scale'].default_value = np.random.uniform(15, 25)
    noise_bump1.inputs['Detail'].default_value = 8.0
    noise_bump1.inputs['Roughness'].default_value = 0.7
    links.new(tex_coord.outputs['Object'], noise_bump1.inputs['Vector'])
    bump1 = nodes.new('ShaderNodeBump')
    bump1.location = (0, -100)
    bump1.inputs['Strength'].default_value = 0.4
    bump1.inputs['Distance'].default_value = 0.02
    links.new(noise_bump1.outputs[0], bump1.inputs['Height'])
    noise_bump2 = nodes.new('ShaderNodeTexNoise')
    noise_bump2.location = (-400, -300)
    noise_bump2.inputs['Scale'].default_value = np.random.uniform(40, 80)
    noise_bump2.inputs['Detail'].default_value = 4.0
    links.new(tex_coord.outputs['Object'], noise_bump2.inputs['Vector'])
    bump2 = nodes.new('ShaderNodeBump')
    bump2.location = (0, -300)
    bump2.inputs['Strength'].default_value = 0.15
    bump2.inputs['Distance'].default_value = 0.005
    links.new(noise_bump2.outputs[0], bump2.inputs['Height'])
    links.new(bump1.outputs[0], bump2.inputs['Normal'])
    links.new(bump2.outputs[0], bsdf.inputs['Normal'])
    return mat


def create_ring_material(base_hue=None):
    if base_hue is None:
        base_hue = np.random.uniform(0.02, 0.08)
    mat = bpy.data.materials.new("RingMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value = 0.75
    links.new(bsdf.outputs[0], output.inputs[0])
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    wave = nodes.new('ShaderNodeTexWave')
    wave.location = (-200, 0)
    wave.wave_type = 'RINGS'
    wave.rings_direction = 'Z'
    wave.wave_profile = 'SAW'
    wave.inputs['Scale'].default_value = np.random.uniform(10, 20)
    wave.inputs['Distortion'].default_value = np.random.uniform(4, 10)
    links.new(tex_coord.outputs['Object'], wave.inputs['Vector'])
    dark_r, dark_g, dark_b = colorsys.hsv_to_rgb(
        (base_hue + np.random.uniform(-0.02, 0.02)) % 1,
        np.random.uniform(0.4, 0.8), np.random.uniform(0.02, 0.05))
    bright_r, bright_g, bright_b = colorsys.hsv_to_rgb(
        base_hue, np.random.uniform(0.4, 0.8), np.random.uniform(0.2, 0.6))
    mix_col = nodes.new('ShaderNodeMix')
    mix_col.location = (100, 0)
    mix_col.data_type = 'RGBA'
    mix_col.inputs[6].default_value = (dark_r, dark_g, dark_b, 1)
    mix_col.inputs[7].default_value = (bright_r, bright_g, bright_b, 1)
    links.new(wave.outputs[0], mix_col.inputs[0])
    links.new(mix_col.outputs[2], bsdf.inputs['Base Color'])
    return mat


def build_truncated_tree(seed):
    rng = np.random.RandomState(seed)
    clear_scene()
    np.random.seed(seed)
    base_hue = np.random.uniform(0.02, 0.08)
    bark_mat = create_bark_material(base_hue)
    ring_mat = create_ring_material(base_hue)

    phase = rng.uniform(0.0, math.tau, 12)
    noise_shift = rng.uniform(-8.0, 8.0, 3)

    n_theta = 180
    n_z = 352
    n_r_top = 60
    n_r_bottom = 60
    base_radius = 0.56
    trunk_height = 4.10

    verts = []
    faces = []
    side_rings = []
    side_radius_top = np.zeros(n_theta, dtype=np.float32)
    rim_height = np.zeros(n_theta, dtype=np.float32)
    side_radius_bottom = np.zeros(n_theta, dtype=np.float32)

    for j in range(n_z + 1):
        t = j / n_z
        z_base = trunk_height * t
        lift_env = smoothstep(0.80, 1.0, t)
        bark_env = 1.0 - smoothstep(0.50, 0.86, t)
        upper_env = smoothstep(0.42, 0.95, t)
        ring = []

        for i in range(n_theta):
            theta = math.tau * i / n_theta
            sin_t = math.sin(theta)
            cos_t = math.cos(theta)

            angular_low = (
                0.026 * math.sin(theta * 2.0 + phase[0])
                + 0.018 * math.sin(theta * 3.0 + phase[1])
                + 0.012 * math.sin(theta * 5.0 + phase[2])
            )
            angular_noise = mnoise.noise(
                Vector(
                    (
                        cos_t * 1.8 + noise_shift[0],
                        sin_t * 1.8 + noise_shift[1],
                        t * 0.7 + noise_shift[2],
                    )
                )
            )
            angular_profile = 1.0 + angular_low + 0.040 * angular_noise

            taper = 1.0 - 0.16 * t - 0.14 * t * t
            body_profile = (
                1.0
                + 0.05 * math.exp(-((t - 0.18) / 0.18) ** 2)
                - 0.08 * math.exp(-((t - 0.62) / 0.16) ** 2)
            )
            radius = base_radius * taper * body_profile * angular_profile

            bark_noise_a = mnoise.noise(
                Vector(
                    (
                        cos_t * 3.0 + noise_shift[0],
                        sin_t * 3.0 + noise_shift[1],
                        z_base * 0.35 + noise_shift[2],
                    )
                )
            )
            bark_noise_b = mnoise.noise(
                Vector(
                    (
                        cos_t * 6.8 - noise_shift[1],
                        sin_t * 6.8 + noise_shift[0],
                        z_base * 0.9 + noise_shift[2] * 0.3,
                    )
                )
            )
            bark_noise_c = mnoise.noise(
                Vector(
                    (
                        cos_t * 11.0 + z_base * 0.45 + noise_shift[2],
                        sin_t * 11.0 - z_base * 0.35 - noise_shift[0],
                        z_base * 1.4,
                    )
                )
            )
            bark_chunks = bark_env * (
                0.052 * abs(bark_noise_a)
                + 0.024 * bark_noise_b
                + 0.016 * bark_noise_c
                + 0.010 * math.sin(theta * 18.0 + z_base * 1.1 + phase[3])
            )

            fiber_noise = mnoise.noise(
                Vector(
                    (
                        cos_t * 8.5 + noise_shift[0],
                        sin_t * 8.5 - noise_shift[1],
                        z_base * 0.75 + noise_shift[2],
                    )
                )
            )
            fiber_gate = max(
                0.0,
                math.sin(theta * 24.0 + z_base * 1.65 + phase[4]) + 0.9 * fiber_noise,
            )
            fiber_ridges = upper_env * (
                0.080 * (fiber_gate**2.6)
                + 0.018 * math.sin(theta * 41.0 - z_base * 1.2 + phase[5])
            )
            grooves = upper_env * (
                0.026 * math.sin(theta * 16.0 + z_base * 1.9 + phase[6])
                + 0.020
                * abs(
                    mnoise.noise(
                        Vector(
                            (
                                cos_t * 4.0 - noise_shift[2],
                                sin_t * 4.0 + noise_shift[1],
                                z_base * 0.55,
                            )
                        )
                    )
                )
            )

            rim_signal = (
                0.42 * math.sin(theta * 7.0 + phase[7])
                + 0.24 * math.sin(theta * 13.0 + phase[8])
                + 0.20
                * mnoise.noise(
                    Vector(
                        (
                            cos_t * 2.4 + noise_shift[2],
                            sin_t * 2.4 - noise_shift[0],
                            0.0,
                        )
                    )
                )
            )
            rim_signal = max(0.0, rim_signal)
            rim_fine = max(
                0.0,
                0.55 * math.sin(theta * 29.0 + phase[9])
                + 0.40 * math.sin(theta * 37.0 + phase[10])
                + 0.35
                * mnoise.noise(
                    Vector(
                        (
                            cos_t * 9.0 + noise_shift[1],
                            sin_t * 9.0 - noise_shift[2],
                            t * 2.2,
                        )
                    )
                ),
            )
            top_delta = (0.14 + 0.36 * rim_signal + 0.18 * rim_fine) * (lift_env**2.35)

            radius = max(radius + bark_chunks + fiber_ridges - grooves, 0.12)
            x = radius * cos_t
            y = radius * sin_t
            z = z_base + top_delta

            ring.append(len(verts))
            verts.append((x, y, z))

            if j == 0:
                side_radius_bottom[i] = radius
            if j == n_z:
                side_radius_top[i] = radius
                rim_height[i] = z

        side_rings.append(ring)

    for j in range(n_z):
        outer = side_rings[j]
        inner = side_rings[j + 1]
        for i in range(n_theta):
            i1 = (i + 1) % n_theta
            faces.append((outer[i], outer[i1], inner[i1], inner[i]))

    top_rings = [side_rings[-1]]
    for k in range(1, n_r_top):
        u = 1.0 - k / n_r_top
        ring = []
        for i in range(n_theta):
            theta = math.tau * i / n_theta
            sin_t = math.sin(theta)
            cos_t = math.cos(theta)
            interior_noise = mnoise.noise(
                Vector(
                    (
                        u * 2.8 + noise_shift[0],
                        cos_t * 1.5 - noise_shift[1],
                        sin_t * 1.5 + noise_shift[2],
                    )
                )
            )
            wood_wave = math.sin(theta * 12.0 + u * 7.0 + phase[9])
            center_base = trunk_height + 0.03 + 0.05 * interior_noise
            z = center_base + (rim_height[i] - center_base) * (u**2.9)
            z += (0.034 * wood_wave + 0.024 * interior_noise) * u * (1.0 - u)

            radius = side_radius_top[i] * u * (
                1.0 + 0.020 * (1.0 - u) * math.sin(theta * 6.0 + phase[11])
            )
            ring.append(len(verts))
            verts.append((radius * cos_t, radius * sin_t, z))
        top_rings.append(ring)

    top_center = len(verts)
    verts.append((0.0, 0.0, trunk_height + 0.07))

    for k in range(len(top_rings) - 1):
        outer = top_rings[k]
        inner = top_rings[k + 1]
        for i in range(n_theta):
            i1 = (i + 1) % n_theta
            faces.append((outer[i], outer[i1], inner[i1], inner[i]))

    last_top_ring = top_rings[-1]
    for i in range(n_theta):
        i1 = (i + 1) % n_theta
        faces.append((last_top_ring[i], last_top_ring[i1], top_center))

    bottom_rings = [side_rings[0]]
    for k in range(1, n_r_bottom):
        u = 1.0 - k / n_r_bottom
        ring = []
        for i in range(n_theta):
            theta = math.tau * i / n_theta
            radius = side_radius_bottom[i] * u
            z = -0.015 * (1.0 - u) * u
            ring.append(len(verts))
            verts.append((radius * math.cos(theta), radius * math.sin(theta), z))
        bottom_rings.append(ring)

    bottom_center = len(verts)
    verts.append((0.0, 0.0, -0.015))

    for k in range(len(bottom_rings) - 1):
        outer = bottom_rings[k]
        inner = bottom_rings[k + 1]
        for i in range(n_theta):
            i1 = (i + 1) % n_theta
            faces.append((outer[i], inner[i], inner[i1], outer[i1]))

    last_bottom_ring = bottom_rings[-1]
    for i in range(n_theta):
        i1 = (i + 1) % n_theta
        faces.append((last_bottom_ring[i], bottom_center, last_bottom_ring[i1]))

    result = create_mesh_object("TruncatedTree", verts, faces)

    # Assign per-face material indices:
    # side + bottom → bark (index 0), top cap cross-section → ring (index 1)
    n_top_start = n_z * n_theta          # first face of top cap
    n_top_end   = n_top_start + n_r_top * n_theta  # one past last top-cap face
    result.data.materials.append(bark_mat)
    result.data.materials.append(ring_mat)
    for poly in result.data.polygons:
        if n_top_start <= poly.index < n_top_end:
            poly.material_index = 1   # ring material for cut cross-section
        else:
            poly.material_index = 0   # bark material for trunk surface

    sel_none()
    set_active(result)
    bpy.ops.object.shade_smooth()
    if hasattr(result.data, "use_auto_smooth"):
        result.data.use_auto_smooth = True
        result.data.auto_smooth_angle = math.radians(60.0)

    min_z = np.min(read_co(result)[:, 2])
    result.location.z -= min_z
    apply_tf(result, True)
    result.name = "TruncatedTree"
    return result


obj = build_truncated_tree(SEED)
print(
    f"TruncatedTree seed={SEED}: "
    f"{len(obj.data.vertices)} verts, {len(obj.data.polygons)} faces, "
    f"{len(obj.data.materials)} materials"
)
