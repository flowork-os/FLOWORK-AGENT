# [FL_INDEX: keywords="blender_factory, procedural_3d, DustMoteFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: DustMoteFactory | Category: factories_tex
# Prompt: A 3D model of a dust mote particle rendered from a slightly elevated perspective, featuring a faceted geodesic sphere shape with irregular polygonal faces and a semi-translucent pinkish-brown appearance with subtle cloudy surface detail.

"""DustMoteFactory — texture-enabled conversion.

Geometry source: objects_blender/particles/DustMoteFactory.py (icosphere r=1 subdivisions=2)
                 (calls geo_dirt(geometry=False) -> base_color + roughness -> Principled BSDF)

The DustMoteFactory.finalize_assets calls dirt.Dirt().apply(assets), which adds
both a geomod displacement and the shader_dirt material. For this standalone converter
we preserve geometry verbatim from objects_blender/ and faithfully reproduce the shader
node tree (procedural dirt: 4D noise layers + voronoi cracks + color ramps).

No wear_tear in the source path for this factory.
"""


import os
import math
import random
import colorsys

import bpy
import numpy as np

# Seeding helpers

SEED = int(os.environ.get("SEED", 0))

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def _sample_ratio(x, sample_min=0.5, sample_max=2.0):
    """Port of sample_ratio: log-uniform around x."""

    if x == 0:
        return 0.0
    neg = 1
    if x < 0:
        x = -x
        neg = -1
    x_min = x * sample_min
    x_max = x * sample_max
    exp_val = np.random.uniform(math.log(x_min), math.log(x_max))
    return neg * math.exp(exp_val)

def _sample_color_offset(color, offset=0.05):
    """Port of sample_color (non-keep_sum path) — mutate RGB by uniform offset."""

    out = list(color)
    for i in range(3):
        out[i] += (random.random() - 0.5) * 2 * offset
        out[i] = max(0.0, min(1.0, out[i]))
    return tuple(out)

def _specular_key(bsdf):
    return "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"

def _noise_fac(noise_node):
    return noise_node.outputs.get("Fac") or noise_node.outputs.get("Factor") or noise_node.outputs[0]

def _set_noise_4d(nt, links, position_out, scale, detail=None, w_value=0.0):
    noise = nt.nodes.new("ShaderNodeTexNoise")
    # Blender 5.0 supports 4D; fall back to 3D if not available.
    try:
        noise.noise_dimensions = "4D"
    except Exception:
        noise.noise_dimensions = "3D"
    links.new(position_out, noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = float(scale)
    if detail is not None:
        noise.inputs["Detail"].default_value = float(detail)
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = float(w_value)
    return noise

def make_dirt_material(seed, name="DustMoteDirt"):
    """Faithfully reproduce shader_dirt on a fresh material.

    Mirrors geo_dirt(geometry=False) call order for numpy.random / random consumption:
      dens_crack, scal_crack, widt_crack,
      noise_texture_w, noise_texture_2_w, noise_texture_1_w,
      (no sampling for voronoi / colorramps 1&2 — only constants),
      noise_texture_3_w, sample_ratio(5, 3/4, 4/3),
      noise_texture_4_w, sample_ratio(20, 3/4, 4/3),
      sample_color on colorramp elements 1, 2 (uses python random).
    """

    seed_all(seed)

    # -- Sample shader parameters in order ------------------------
    dens_crack = float(np.random.uniform(0.0, 0.1))
    scal_crack = float(np.random.uniform(5.0, 15.0))
    widt_crack = float(np.random.uniform(0.01, 0.05))

    noise_w_main = float(np.random.uniform(0.0, 10.0))
    noise_w_2 = float(np.random.uniform(0.0, 10.0))
    noise_w_1 = float(np.random.uniform(0.0, 10.0))
    noise_w_3 = float(np.random.uniform(0.0, 10.0))
    ntex3_scale = _sample_ratio(5.0, 3.0 / 4.0, 4.0 / 3.0)
    noise_w_4 = float(np.random.uniform(0.0, 10.0))
    ntex4_scale = _sample_ratio(20.0, 3.0 / 4.0, 4.0 / 3.0)

    colorramp_mid = _sample_color_offset((0.18, 0.075, 0.05), offset=0.05)
    colorramp_hi = _sample_color_offset((0.19, 0.03, 0.02), offset=0.05)

    scale = 0.5

    # -- Build node tree ------------------------------------------------------
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    links = nt.links

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    position_out = geom.outputs["Position"]
    normal_out = geom.outputs["Normal"]

    # Noise textures (ntex main, ntex2, ntex1)
    ntex_main = _set_noise_4d(nt, links, position_out,
                              scale=8.0 * scale, detail=16.0, w_value=noise_w_main)
    ntex2 = _set_noise_4d(nt, links, position_out,
                          scale=5.0 * scale, w_value=noise_w_2)
    ntex1 = _set_noise_4d(nt, links, position_out,
                          scale=1.0 * scale, detail=16.0, w_value=noise_w_1)

    # colorramp_2: MapRange on ntex2.Fac, clamp, endpoints shifted by dens_crack
    mr2 = nt.nodes.new("ShaderNodeMapRange")
    mr2.clamp = True
    links.new(_noise_fac(ntex2), mr2.inputs["Value"])
    mr2.inputs[1].default_value = 0.445 + (2.0 * dens_crack) - 0.1  # From Min
    mr2.inputs[2].default_value = 0.505 + (2.0 * dens_crack) - 0.1  # From Max
    mr2.inputs[3].default_value = 0.0
    mr2.inputs[4].default_value = 1.0

    # Voronoi on ntex1.Color with DISTANCE_TO_EDGE feature
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        voronoi.feature = "DISTANCE_TO_EDGE"
    except Exception:
        pass
    links.new(ntex1.outputs["Color"], voronoi.inputs["Vector"])
    voronoi.inputs["Scale"].default_value = scal_crack * scale

    # colorramp_1: MapRange on voronoi Distance, clamp
    mr1 = nt.nodes.new("ShaderNodeMapRange")
    mr1.clamp = True
    links.new(voronoi.outputs["Distance"], mr1.inputs["Value"])
    mr1.inputs[1].default_value = 0.0
    mr1.inputs[2].default_value = widt_crack
    mr1.inputs[3].default_value = 0.0
    mr1.inputs[4].default_value = 1.0

    # mix_sub = (1,1,1) - colorramp_2
    mix_sub = nt.nodes.new("ShaderNodeVectorMath")
    mix_sub.operation = "SUBTRACT"
    mix_sub.inputs[0].default_value = (1.0, 1.0, 1.0)
    links.new(mr2.outputs["Result"], mix_sub.inputs[1])

    # mix_mul1 = mix_sub * colorramp_1
    mix_mul1 = nt.nodes.new("ShaderNodeVectorMath")
    mix_mul1.operation = "MULTIPLY"
    links.new(mix_sub.outputs["Vector"], mix_mul1.inputs[0])
    links.new(mr1.outputs["Result"], mix_mul1.inputs[1])

    # mix_mul2 = colorramp_2 * (0.5,0.5,0.5)
    mix_mul2 = nt.nodes.new("ShaderNodeVectorMath")
    mix_mul2.operation = "MULTIPLY"
    links.new(mr2.outputs["Result"], mix_mul2.inputs[0])
    mix_mul2.inputs[1].default_value = (0.5, 0.5, 0.5)

    # mix = mix_mul1 + mix_mul2 (vector ADD is default operation)
    mix_vec = nt.nodes.new("ShaderNodeVectorMath")
    mix_vec.operation = "ADD"
    links.new(mix_mul1.outputs["Vector"], mix_vec.inputs[0])
    links.new(mix_mul2.outputs["Vector"], mix_vec.inputs[1])

    # Base color: ColorRamp on ntex_main.Fac with 3 stops
    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    links.new(_noise_fac(ntex_main), cr_base.inputs["Fac"])
    # Add one extra stop (ValToRGB defaults to 2 elements).
    cr_base.color_ramp.elements.new(0.5)
    cr_base.color_ramp.elements[0].position = 0.223
    cr_base.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_base.color_ramp.elements[1].position = 0.71
    cr_base.color_ramp.elements[1].color = (colorramp_mid[0], colorramp_mid[1], colorramp_mid[2], 1.0)
    cr_base.color_ramp.elements[2].position = 1.0
    cr_base.color_ramp.elements[2].color = (colorramp_hi[0], colorramp_hi[1], colorramp_hi[2], 1.0)

    # dirt_base_color: MixRGB (fac=mix, color1=black, color2=cr_base)
    # Use ShaderNodeMix (new RGBA) for 5.0+ compatibility.
    mix_rgb = nt.nodes.new("ShaderNodeMix")
    mix_rgb.data_type = "RGBA"
    links.new(mix_vec.outputs["Vector"], mix_rgb.inputs[0])
    mix_rgb.inputs[6].default_value = (0.0, 0.0, 0.0, 1.0)
    links.new(cr_base.outputs["Color"], mix_rgb.inputs[7])

    # Roughness: ColorRamp on ntex_main.Fac, 2 stops at 0.08 and 0.768
    cr_rough = nt.nodes.new("ShaderNodeValToRGB")
    links.new(_noise_fac(ntex_main), cr_rough.inputs["Fac"])
    cr_rough.color_ramp.elements[0].position = 0.08
    cr_rough.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_rough.color_ramp.elements[1].position = 0.768
    cr_rough.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    links.new(mix_rgb.outputs[2], bsdf.inputs["Base Color"])
    links.new(cr_rough.outputs["Color"], bsdf.inputs["Roughness"])
    bsdf.inputs[_specular_key(bsdf)].default_value = 0.5

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # NOTE: geo_dirt also consumes noise_texture_3 and noise_texture_4
    # as displacement offsets via geometry nodes (geometry=True branch). For this
    # standalone shader-only conversion we reproduce shader_dirt (geometry=False),
    # which only uses cr_base, cr_rough, and mix_vec as above.
    _ = (ntex3_scale, noise_w_3, ntex4_scale, noise_w_4)  # sampled for RNG parity
    return mat

seed_all(SEED)
CATEG_MAT = make_dirt_material(SEED, "DustMoteFactory_Material")
CATEG_MAT.use_fake_user = True

# No wear_tear gates — DustMoteFactory does not apply scratch/edge-wear.

# Geometry (copied verbatim from objects_blender/particles/DustMoteFactory.py)

for _existing_obj in list(bpy.data.objects):
    bpy.data.objects.remove(_existing_obj, do_unlink=True)
bpy.context.scene.cursor.location = (0, 0, 0)

bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=2, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "DustMoteFactory"

# Attach material
obj.data.materials.clear()
obj.data.materials.append(CATEG_MAT)

print(
    f"DustMoteFactory built: {len(obj.data.vertices)} verts, "
    f"{len(obj.data.polygons)} faces, materials={len(obj.data.materials)}"
)

