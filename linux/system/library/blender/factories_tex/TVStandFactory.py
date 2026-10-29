# [FL_INDEX: keywords="blender_factory, procedural_3d, TVStandFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TVStandFactory | Category: factories_tex
# Prompt: A 3D model of a low, wide TV stand rendered from a three-quarter perspective, featuring a long horizontal rectangular body with multiple open compartments divided by vertical partitions and diagonal cross-dividers inside each section, all in a light wood-grain appearance.

"""TVStandFactory — texture-enabled standalone port.

Geometry is copied verbatim from
    objects_blender/shelves/TVStandFactory.py
(see the "Original geometry" block below).

Shader sources translated faithfully from:
        shader_shelves_white        -> make_shelves_white
        shader_shelves_wood         -> make_shelves_wood
        shader_shelves_black_wood   -> make_shelves_black_wood
wear_tear, and TVStandFactory inherits from CellShelfFactory, so wear_tear
is intentionally NOT applied. Also, for TVStand, `has_base_frame` is
hard-coded to False, so base_material is unused. The standalone geometry
does not emit screw-head instances, so metals are unused as well. The only
material needed is `wood_material`.
"""


import os
import math
import bpy
import bmesh
import random
import colorsys
import numpy as np
from numpy.random import normal, randint, uniform

# --- material library ---

def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
    """Set Principled BSDF inputs with Blender-version-tolerant socket names."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

# ----------------------------------------------------------------------------
# Shelves wood-family shaders — faithful raw-bpy ports of plywood.py
# ----------------------------------------------------------------------------
def _sample_white_params():
    """shader_shelves_white_sampler (plywood.py:44)."""

    v = float(np.random.uniform(0.7, 1.0))
    return dict(
        rgb=[
            v * (1.0 + float(np.random.normal(0, 0.005))),
            v * (1.0 + float(np.random.normal(0, 0.005))),
            v * (1.0 + float(np.random.normal(0, 0.005))),
        ],
        roughness=float(np.random.uniform(0.7, 1.0)),
    )

def make_shelves_white(name="ShelvesWhite", params=None) -> bpy.types.Material:
    """Port of plywood.py:shader_shelves_white."""

    if params is None:
        params = _sample_white_params()
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*params["rgb"], 1.0)
    _set_principled(bsdf, Roughness=float(params["roughness"]))
    _connect_output(nt, bsdf)
    return mat

def _sample_black_wood_params():
    """shader_shelves_black_wood_sampler (plywood.py:221)."""

    return dict(
        wave_scale=float(np.random.uniform(1.0, 3.0)),
        dark_scale=float(np.random.uniform(0.0, 0.01)),
        gray_scale=float(np.random.uniform(0.01, 0.03)),
        rgb=[
            float(np.random.uniform(0.015, 0.035)),
            float(np.random.uniform(0.0, 0.01)),
            float(np.random.uniform(0.0, 0.01)),
        ],
        roughness=float(np.random.uniform(0.75, 1.0)),
    )

def _sample_wood_params():
    """shader_shelves_wood_sampler (plywood.py:386) — blond wood."""

    return dict(
        bright_hsv=[float(np.random.uniform(0.03, 0.09)),
                    float(np.random.uniform(0.5, 0.7)),
                    float(np.random.uniform(0.7, 1.0))],
        mid_hsv=[float(np.random.uniform(0.02, 0.06)),
                 float(np.random.uniform(0.6, 1.0)),
                 float(np.random.uniform(0.3, 0.6))],
        dark_hsv=[float(np.random.uniform(0.03, 0.05)),
                  float(np.random.uniform(0.6, 1.0)),
                  float(np.random.uniform(0.1, 0.3))],
        wave_scale=float(np.random.uniform(1.0, 3.0)),
        roughness=float(np.random.uniform(0.75, 1.0)),
    )

def _build_shelves_grain_chain(nt, tex_coord, wave_scale_val, z_axis_texture=False):
    """Shared wood-grain node chain for shader_shelves_wood and _black_wood.

    Replicates plywood.py lines 75-165 / 249-339 faithfully. Returns
    (mix_2_result_socket, displacement_node) so the caller can wire the
    final base-color ramp and the material-output displacement link.
    """
    # --- branch 1: voronoi / grain lines ------------------------------------
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    if z_axis_texture:
        mapping_1.inputs["Scale"].default_value = (0.1, 0.1, 2.0)
    else:
        mapping_1.inputs["Scale"].default_value = (0.1, 2.0, 2.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise_1.inputs:
        noise_1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise_1.inputs:
        noise_1.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = 40.0
    nt.links.new(_noise_fac_output(noise_1), voronoi.inputs["Vector"])

    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    fac_in1 = cr1.inputs.get("Fac") or cr1.inputs[0]
    color_out1 = voronoi.outputs.get("Color") or voronoi.outputs[0]
    nt.links.new(color_out1, fac_in1)
    cr1.color_ramp.elements[0].position = 0.0864
    cr1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr1.color_ramp.elements[1].position = 0.1091
    cr1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # --- branch 2: wave / warped grain body ---------------------------------
    mapping = nt.nodes.new("ShaderNodeMapping")
    if z_axis_texture:
        mapping.inputs["Scale"].default_value = (wave_scale_val, wave_scale_val, 0.1)
    else:
        mapping.inputs["Scale"].default_value = (wave_scale_val, 0.1, 0.1)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # Blender 5.0 removed ShaderNodeTexMusgrave; substitute a stretched
    # NoiseTexture driven by the previous noise's Fac output to keep the
    # "warped grain" character of the original shader.
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave.inputs:
        musgrave.inputs["Detail"].default_value = 3.0
    if "Distortion" in musgrave.inputs:
        musgrave.inputs["Distortion"].default_value = 0.0
    nt.links.new(_noise_fac_output(noise), musgrave.inputs["Vector"])

    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    nt.links.new(_noise_fac_output(musgrave), mix_1.inputs[6])
    noise_color = noise.outputs.get("Color") or noise.outputs[0]
    nt.links.new(noise_color, mix_1.inputs[7])

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    fac_in2 = cr2.inputs.get("Fac") or cr2.inputs[0]
    nt.links.new(mix_1.outputs[2], fac_in2)
    cr2.color_ramp.elements[0].position = 0.0818
    cr2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr2.color_ramp.elements[1].position = 0.8500
    cr2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # --- mix_2 (factor 0.6) drives the base-color ramp ----------------------
    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"):
        mix_2.data_type = "RGBA"
    mix_2.inputs[0].default_value = 0.6
    nt.links.new(cr1.outputs["Color"], mix_2.inputs[6])
    nt.links.new(cr2.outputs["Color"], mix_2.inputs[7])

    # --- mix_3 (factor 0.004) drives the displacement height ---------------
    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"):
        mix_3.data_type = "RGBA"
    mix_3.inputs[0].default_value = 0.004
    nt.links.new(cr1.outputs["Color"], mix_3.inputs[6])
    nt.links.new(cr2.outputs["Color"], mix_3.inputs[7])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    return mix_2.outputs[2], disp

def make_shelves_wood(name="ShelvesWood", params=None,
                      z_axis_texture=False) -> bpy.types.Material:
    """Port of plywood.py:shader_shelves_wood (blond plywood)."""

    if params is None:
        params = _sample_wood_params()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    driver_socket, disp = _build_shelves_grain_chain(
        nt, tex_coord, params["wave_scale"], z_axis_texture=z_axis_texture)

    # 3-stop color ramp: dark / mid / bright HSV triples
    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(driver_socket, fac_in)
    cr.color_ramp.elements.new(0.5)  # add third element
    cr.color_ramp.elements[0].position = 0.02
    cr.color_ramp.elements[0].color = hsv2rgba(params["dark_hsv"])
    cr.color_ramp.elements[1].position = 0.11
    cr.color_ramp.elements[1].color = hsv2rgba(params["mid_hsv"])
    cr.color_ramp.elements[2].position = 0.8
    cr.color_ramp.elements[2].color = hsv2rgba(params["bright_hsv"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=float(params["roughness"]))
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_shelves_black_wood(name="ShelvesBlackWood", params=None,
                            z_axis_texture=False) -> bpy.types.Material:
    """Port of plywood.py:shader_shelves_black_wood."""

    if params is None:
        params = _sample_black_wood_params()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    driver_socket, disp = _build_shelves_grain_chain(
        nt, tex_coord, params["wave_scale"], z_axis_texture=z_axis_texture)

    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(driver_socket, fac_in)
    cr.color_ramp.elements.new(0.5)
    dark = params["dark_scale"]
    gray = params["gray_scale"]
    cr.color_ramp.elements[0].position = 0.15
    cr.color_ramp.elements[0].color = (dark, dark, dark, 1.0)
    cr.color_ramp.elements[1].position = 0.5
    cr.color_ramp.elements[1].color = (gray, gray, gray, 1.0)
    cr.color_ramp.elements[2].position = 1.0
    cr.color_ramp.elements[2].color = (*params["rgb"], 1.0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=float(params["roughness"]))
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# Material registry — mirror cell_shelf.py:1464-1486 wood_material dispatch
# ----------------------------------------------------------------------------
WOOD_KEYS = ["black_wood", "white", "wood"]
WOOD_PROBS = [0.3, 0.2, 0.5]

def make_shelves_wood_from_key(key: str, name: str = None) -> bpy.types.Material:
    """Dispatch on the wood_material key exactly as cell_shelf.get_material_func."""

    if key == "black_wood":
        return make_shelves_black_wood(name or "ShelvesBlackWood")
    if key == "white":
        return make_shelves_white(name or "ShelvesWhite")
    if key == "wood":
        return make_shelves_wood(name or "ShelvesWood")
    raise NotImplementedError(f"unknown wood key: {key!r}")

# --- Original geometry code ---
# Copied verbatim from objects_blender/shelves/TVStandFactory.py, with the
# only edit being `parts[i].data.materials.append(MAT_WOOD)` inserted before
# the final `join_all(...)` so every sub-box carries the wood material slot.

# ── Scene helpers ─────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    bpy.context.scene.cursor.location = (0, 0, 0)

def add_box(cx, cy, cz, sx, sy, sz):
    """Add a cuboid centered at (cx,cy,cz) with full dimensions (sx,sy,sz)."""

    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, cz))
    obj = bpy.context.active_object
    obj.scale = (sx / 2, sy / 2, sz / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj

def join_all(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    result = bpy.context.active_object
    result.name = name
    return result

def sample_tv_stand_params():
    """Sample a TV-stand parameter set"""
    # TV stand specific dimensions (from TVStandFactory.sample_params)
    depth = uniform(0.3, 0.45)
    width = uniform(2 * 0.35, 6 * 0.35)  # horizontal span
    height = uniform(0.3, 0.5)

    # Derive cell counts from width/height
    h_cells = max(1, int(width / 0.35))
    cell_size = width / h_cells
    v_cells = max(1, int(height / cell_size))
    height = v_cells * cell_size  # snap height to cell grid

    # Board thicknesses (from CellShelfBase.get_asset_params)
    ext_thk = float(np.clip(normal(0.04, 0.005), 0.028, 0.052))
    div_thk = float(np.clip(normal(0.015, 0.005), 0.008, 0.022))

    return {
        'depth': depth,
        'width': width,
        'height': height,
        'h_cells': h_cells,
        'v_cells': v_cells,
        'cell_size': cell_size,
        'ext_thk': ext_thk,
        'div_thk': div_thk,
        'has_base_frame': False,  # TV stands don't have base frame
    }

# ── Shelf construction ────────────────────────────────────────────────────

def build_tv_stand(p):
    """Build a TV stand from sampled parameters."""

    depth = p['depth']
    width = p['width']
    height = p['height']
    h_cells = p['h_cells']
    v_cells = p['v_cells']
    cs = p['cell_size']
    ext = p['ext_thk']
    div = p['div_thk']

    parts = []

    # Top and bottom external boards (span full width+ext on both sides)
    total_w = width + 2 * ext
    top_z = height + ext / 2
    bot_z = ext / 2
    parts.append(add_box(0, 0, top_z, depth, total_w, ext))
    parts.append(add_box(0, 0, bot_z, depth, total_w, ext))

    # Left and right side boards
    left_y = -width / 2 - ext / 2
    right_y = width / 2 + ext / 2
    mid_z = (bot_z + top_z) / 2
    side_h = height + ext  # overlaps with top/bottom for clean joins
    parts.append(add_box(0, left_y, mid_z + ext/2, depth, ext, side_h))
    parts.append(add_box(0, right_y, mid_z + ext/2, depth, ext, side_h))

    # Interior horizontal dividers (v_cells - 1 of them)
    for i in range(1, v_cells):
        z = ext + i * cs - div / 2 + div / 2
        parts.append(add_box(0, 0, ext + i * cs, depth, width, div))

    # Interior vertical dividers (h_cells - 1 per row)
    for i in range(1, h_cells):
        y = -width / 2 + i * cs
        parts.append(add_box(0, y, ext + height / 2, depth, div, height))

    # Per-spec: append MAT_WOOD to each part BEFORE the join so the final
    # joined mesh exposes a single material slot bound to the wood shader.
    for part in parts:
        part.data.materials.append(MAT_WOOD)

    return join_all(parts, 'TVStandFactory')

#   Mirrors CellShelfBaseFactory.__init__ (cell_shelf.py:1419-1423), which
#   under FixedSeed(factory_seed) runs:
#       self.params = self.sample_params()      (TVStand variant, 3 uniforms)
#       self.params = self.get_asset_params()   (consumes more draws)
#
#   For TVStandFactory.sample_params (cell_shelf.py:1559-1579) the draws are:
#       uniform(0.3,0.45)      # Dimensions[0]
#       uniform(0.7, 2.1)      # Dimensions[1]
#       uniform(0.3, 0.5)      # Dimensions[2]
#   and then `depth`, `cell_size`, `horizontal_cell_num`, `vertical_cell_num`,
#   `has_base_frame`, `Dimensions` are all populated directly — no more RNG.
#
#   get_asset_params (cell_shelf.py:1425-1470) then sees depth / cell_size /
#   vertical_cell_num / horizontal_cell_num already set (skipped), runs:
#       normal → division_board_thickness
#       normal → external_board_thickness
#       (has_backboard already False, skipped)
#       (has_base_frame already False, skipped; has_base_frame branch skipped
#        so no base_leg_* / base_material draws)
#       normal → attachment_size
#       choice → wood_material  ← this is the key we need
#
#   We replay that exact numpy.random consumption sequence here so that the
#   wood_material key lands on the same branch would have picked
#   for the same raw factory_seed.
SEED = int(os.environ.get('SEED', 0))

# Scene cleanup (pre-Phase-1 so material sampling happens in a clean scene)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)

def make_shelves_screw_metal(name="TVStandScrewMetal"):
    """Brushed metal for shelf/cabinet screws and hardware. Faithful to
    cell_shelf.py line 1393: `weighted_sample(material_assignments.metals)()()`
    — any metal shader from the metals pool. Standalone uses a simple Principled BSDF
    with metallic=1 and slight roughness noise."""

    _s = ((SEED + 1) * 2654435761) & 0xFFFFFFFF
    _saved = np.random.get_state()
    np.random.seed(_s + 97)
    roughness_val = float(np.random.uniform(0.15, 0.40))
    hue = float(np.random.uniform(0.05, 0.12))
    sat = float(np.random.uniform(0.0, 0.12))
    val = float(np.random.uniform(0.55, 0.85))
    np.random.set_state(_saved)

    import colorsys
    rgb = colorsys.hsv_to_rgb(hue, sat, val)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = roughness_val
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

seed_all(SEED)
# Replay TVStandFactory.sample_params draws
_ = np.random.uniform(0.3, 0.45)
_ = np.random.uniform(2 * 0.35, 6 * 0.35)
_ = np.random.uniform(0.3, 0.5)
# Replay CellShelfBaseFactory.get_asset_params draws (has_base_frame=False)
_ = np.clip(np.random.normal(0.015, 0.005), 0.008, 0.022)  # div_thk
_ = np.clip(np.random.normal(0.04, 0.005), 0.028, 0.052)   # ext_thk
_ = np.clip(np.random.normal(0.05, 0.02), 0.02, 0.1)       # attachment_size
_WOOD_KEY = np.random.choice(WOOD_KEYS, p=WOOD_PROBS)
MAT_WOOD = make_shelves_wood_from_key(str(_WOOD_KEY), name="TVStandWood")

# Save/restore RNG state around metal material creation so geometry-sampling
# reads the same post-wood RNG state as before.
_saved_state = np.random.get_state()
MAT_SCREW = make_shelves_screw_metal("TVStandScrewMetal")
MAT_SCREW.use_fake_user = True
np.random.set_state(_saved_state)

# ── Main ──────────────────────────────────────────────────────────────────

def build(seed=0):
    global SEED
    SEED = seed
    # Geometry RNG uses the same raw SEED as the original objects_blender script.
    # Materials were already captured at module load time into MAT_WOOD / MAT_SCREW.
    np.random.seed(seed)
    clear_scene()
    params = sample_tv_stand_params()
    result = build_tv_stand(params)
    # Declare MAT_SCREW slot for structural completeness matching CellShelfFactory's
    # 2-material layout (wood + metal screws). The standalone TVStand does not emit
    # explicit screw geometry so this slot is declared but not per-face assigned.
    if result is not None and MAT_SCREW is not None:
        existing = {m.name for m in result.data.materials if m}
        if MAT_SCREW.name not in existing:
            result.data.materials.append(MAT_SCREW)
    return result

build(SEED)

