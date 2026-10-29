# [FL_INDEX: keywords="blender_factory, procedural_3d, GlowingRocksFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: GlowingRocksFactory | Category: factories_tex
# Prompt: A 3D model of a glowing rock rendered from a slightly elevated three-quarter perspective. The rock features a smooth, flat, elongated pebble-like shape with a translucent pale white appearance and a luminous glowing spot or embedded crystal element near its center, emitting a soft teal or green-tinted light against the surrounding surface.

import os
SEED = int(os.environ.get("SEED", "0"))

import bpy
import random
import colorsys
import numpy as np

random.seed(SEED)
np.random.seed(SEED)


# ══════════════════════════════════════════════════════════════════════════════
#   Color:  colors.hsv2rgba(colors.gem_hsv())
#           gem_hsv = (uniform(0,1), 0.85, uniform(0.5,1))
#
# Shader topology (no Emission BSDF — glow comes from parented POINT light):
#   ObjectInfo(Random) → WhiteNoise(4D, Vector=Random) → MixRGB(Fac=0.6,
#       Color1=white_noise.Color, Color2=gem_color)
#   mix → TranslucentBSDF
#   mix → TransparentBSDF
#   LightPath(Is Camera Ray) → MixShader(Fac, Transparent, Translucent)
#     → MaterialOutput.Surface
#
# Effect: camera rays see the transparent shader (rock is see-through), so the
# point light inside the rock shines out unattenuated; non-camera rays (shadow/
# diffuse/etc.) see translucent so light scatters through the rock material
# with the gem hue. This is what makes the rock "glow".
# ══════════════════════════════════════════════════════════════════════════════


def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0,
                                  max(0.0, min(1.0, float(s))),
                                  max(0.0, min(1.0, float(v))))
    return (r, g, b, 1.0)


def _gem_hsv():
    return (float(np.random.uniform(0, 1)), 0.85, float(np.random.uniform(0.5, 1)))


def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def make_glowrock_material(seed, name="GlowingRockMaterial"):
    gem_color = _hsv2rgba(*_gem_hsv())

    mat = _new_mat(name)
    nt = mat.node_tree
    link = nt.links.new

    # Object Info → Random
    object_info = nt.nodes.new("ShaderNodeObjectInfo")

    # the "Vector" input. "Random" is a scalar; Blender auto-converts the
    # float to a vector. We replicate that exactly.
    white_noise = nt.nodes.new("ShaderNodeTexWhiteNoise")
    try:
        white_noise.noise_dimensions = "4D"
    except Exception:
        white_noise.noise_dimensions = "3D"
    link(object_info.outputs["Random"], white_noise.inputs["Vector"])

    # MixRGB (legacy), Factor=0.6, Color1=white_noise.Color, Color2=gem_color
    mix_rgb = nt.nodes.new("ShaderNodeMix"); mix_rgb.data_type = "RGBA"
    mix_rgb.inputs[0].default_value = 0.6
    link(white_noise.outputs["Color"], mix_rgb.inputs[6])
    mix_rgb.inputs[7].default_value = gem_color

    # Translucent BSDF (color = mix)
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    link(mix_rgb.outputs[2], translucent.inputs["Color"])

    # Transparent BSDF (color = mix)
    transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
    link(mix_rgb.outputs[2], transparent.inputs["Color"])

    # Light Path → Is Camera Ray controls the shader mix.
    light_path = nt.nodes.new("ShaderNodeLightPath")

    # Mix Shader: Fac=Is Camera Ray, Shader1=Transparent, Shader2=Translucent
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    link(light_path.outputs["Is Camera Ray"], mix_shader.inputs[0])
    link(transparent.outputs["BSDF"], mix_shader.inputs[1])
    link(translucent.outputs["BSDF"], mix_shader.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    link(mix_shader.outputs["Shader"], out.inputs["Surface"])
    return mat


# np.random.randint(1e5) -- this is a single int draw, (2) shaderfunc_to_material
# invokes shader_glowrock which calls gem_hsv() (2 uniforms) then hsv2rgba.
# We replicate the material draw only; geometry rng is re-seeded inside build().
seed_all_np_random_state = np.random.get_state()
_ = int(np.random.randint(1e5))  # mirror BlenderRockFactory seed draw
MAT_GLOWROCK = make_glowrock_material(SEED, "GlowingRocksFactory_Material")
MAT_GLOWROCK.use_fake_user = True
# Restore so geometry below sees a clean seeded RNG in build().
np.random.set_state(seed_all_np_random_state)


# ══════════════════════════════════════════════════════════════════════════════
# Geometry — copied verbatim from objects_blender/rocks/GlowingRocksFactory.py
# ══════════════════════════════════════════════════════════════════════════════

def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)


class SelectObjects:
    def __init__(self, objs, active=0):
        self.objs = objs if isinstance(objs, (list, tuple)) else [objs]
        self.active = active

    def __enter__(self):
        self.prev_sel = list(bpy.context.selected_objects)
        self.prev_active = bpy.context.view_layer.objects.active
        _select_none()
        for o in self.objs:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if self.objs:
            bpy.context.view_layer.objects.active = self.objs[self.active]
            self.objs[self.active].select_set(True)
        return self

    def __exit__(self, *_):
        _select_none()
        for o in self.prev_sel or []:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if self.prev_active and self.prev_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = self.prev_active


def apply_transform(obj, loc=False, rot=True, scale=True):
    with SelectObjects(obj):
        bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    return obj


def apply_modifiers(obj):
    with SelectObjects(obj):
        for m in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception:
                pass
    return obj


def modify_mesh(obj, type, apply=True, **kwargs):
    mod = obj.modifiers.new(name=type, type=type)
    mod.show_viewport = not apply
    for k, v in kwargs.items():
        try:
            setattr(mod, k, v)
        except Exception:
            pass
    if apply:
        with SelectObjects(obj):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass
    return obj


def deep_clone_obj(obj, keep_modifiers=False, keep_materials=True):
    new = obj.copy()
    if obj.data:
        new.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(new)
    if not keep_modifiers:
        for m in list(new.modifiers):
            try:
                new.modifiers.remove(m)
            except Exception:
                pass
    if not keep_materials and getattr(new.data, 'materials', None):
        new.data.materials.clear()
    for ch in obj.children:
        ch_clone = deep_clone_obj(ch, keep_modifiers=keep_modifiers,
                                  keep_materials=keep_materials)
        ch_clone.parent = new
    return new


_DISPLACEMENT_LAYERS = [
    ('VORONOI', 0.8, 0.15),
    ('CLOUDS',  0.5, 0.08),
    ('VORONOI', 0.3, 0.04),
]


def create_blender_rock():
    """Create a single rock mesh: icosphere + multi-layer displacement."""

    zscale = np.random.uniform(0.2, 0.8)
    zrand = np.random.uniform(0, 0.7)
    rough = np.random.uniform(0.5, 1.0)

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=4, radius=0.5, location=(0, 0, 0),
    )
    obj = bpy.context.active_object
    obj.scale = (1.0, 1.0, np.random.uniform(zrand * zscale, zscale))
    apply_transform(obj)

    for tex_type, noise_scale, strength_mult in _DISPLACEMENT_LAYERS:
        tex = bpy.data.textures.new('rock_disp', tex_type)
        tex.noise_scale = noise_scale
        modify_mesh(obj, 'DISPLACE', texture=tex, strength=rough * strength_mult, mid_level=0.5)
        bpy.data.textures.remove(tex)

    modify_mesh(obj, 'SUBSURF', levels=1, render_levels=1)
    bpy.ops.object.shade_flat()
    apply_modifiers(obj)
    return obj


def build(seed=SEED):
    np.random.seed(seed)

    # Create 5 base rocks
    base_rocks = []
    for i in range(5):
        rock = create_blender_rock()
        modify_mesh(rock, 'SUBSURF', levels=2)
        base_rocks.append(rock)

    # Clone a random rock, apply random transform, add point light
    src_obj = np.random.choice(base_rocks)
    new_obj = deep_clone_obj(src_obj)
    new_obj.rotation_euler = np.random.uniform(-np.pi, np.pi, 3).tolist()
    new_obj.scale = (np.random.uniform(0.7, 1.5, 3) * 0.5).tolist()

    # Assign the glow-rock material BEFORE join-style ops (there's no join here)
    new_obj.data.materials.clear()
    new_obj.data.materials.append(MAT_GLOWROCK)

    # Point light inside the rock (the actual glow source)
    bbox = np.asarray(new_obj.bound_box)
    min_side_length = (bbox.max(axis=0) - bbox.min(axis=0)).min()
    bpy.ops.object.light_add(
        type='POINT', radius=float(min_side_length), location=(0, 0, 0),
    )
    point_light = bpy.context.selected_objects[0]
    point_light.data.energy = round(np.random.uniform(400, 800))
    point_light.parent = new_obj

    apply_transform(new_obj)
    new_obj.name = 'GlowingRocksFactory'

    # Delete all base rocks (src_obj was already cloned into new_obj)
    for r in base_rocks:
        bpy.data.objects.remove(r, do_unlink=True)

    return new_obj


# ---- Main ----

bpy.context.scene.cursor.location = (0, 0, 0)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

result = build(SEED)
print(f"GlowingRocksFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces, "
      f"{len(result.data.materials)} material slots")
