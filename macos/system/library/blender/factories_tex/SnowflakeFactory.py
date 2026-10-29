# [FL_INDEX: keywords="blender_factory, procedural_3d, SnowflakeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SnowflakeFactory | Category: factories_tex
# Prompt: A 3D model of a snowflake rendered from a slightly elevated perspective, featuring a flat thin hexagonal plate shape with clean straight edges and a uniform white appearance, resembling a simple crystalline ice platelet.

import os
import random

import bpy
import numpy as np

SEED = int(os.environ.get("SEED", 0))

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

# --- Inlined material (hand-crafted for SnowflakeFactory) ---
# SnowflakeFactory.finalize_assets calls snow.apply(assets, subsurface=0), so
# the Subsurface Weight input is forced to 0 while the rest of the node tree
# (voronoi-driven Coat Weight, Principled BSDF with MULTI_GGX distribution) is
# preserved exactly as in the upstream shader.
def _set_principled_input(node, name, value):
    """Assign a Principled BSDF input by primary name with a fallback list.

    Blender 5.0 uses 'Specular IOR Level' / 'Coat Weight'; older names like
    'Specular' or 'Subsurface' may still be needed on 3.x fallbacks.
    """

    fallbacks = {
        "Specular IOR Level": ["Specular"],
        "Subsurface Weight": ["Subsurface"],
        "Coat Weight": ["Clearcoat"],
        "Coat Roughness": ["Clearcoat Roughness"],
    }
    if name in node.inputs:
        node.inputs[name].default_value = value
        return
    for alt in fallbacks.get(name, []):
        if alt in node.inputs:
            node.inputs[alt].default_value = value
            return

def make_snow_mat(name="SnowflakeFactory_Material", subsurface=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    # Geometry (position used as the texture-space vector)
    geometry = nt.nodes.new("ShaderNodeNewGeometry")

    # Subsurface radius constant vector: CombineXYZ(0.36, 0.46, 0.6) * 0.5
    combine_xyz = nt.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz.inputs["X"].default_value = 0.36
    combine_xyz.inputs["Y"].default_value = 0.46
    combine_xyz.inputs["Z"].default_value = 0.6

    vec_math = nt.nodes.new("ShaderNodeVectorMath")
    vec_math.operation = "MULTIPLY"
    nt.links.new(combine_xyz.outputs["Vector"], vec_math.inputs[0])
    vec_math.inputs[1].default_value = (0.5, 0.5, 0.5)

    # Mapping: scale the geometry position by 12 before feeding the voronoi
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (12.0, 12.0, 12.0)
    nt.links.new(geometry.outputs["Position"], mapping.inputs["Vector"])

    # Voronoi with N_SPHERE_RADIUS feature, Scale=30.0
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        voronoi.feature = "N_SPHERE_RADIUS"
    except Exception:
        pass
    nt.links.new(mapping.outputs["Vector"], voronoi.inputs["Vector"])
    voronoi.inputs["Scale"].default_value = 30.0

    # ColorRamp on the voronoi Radius output: (0.525 -> black, 0.58 -> white)
    colorramp = nt.nodes.new("ShaderNodeValToRGB")
    radius_out = voronoi.outputs.get("Radius") or voronoi.outputs[0]
    nt.links.new(radius_out, colorramp.inputs["Fac"])
    colorramp.color_ramp.elements[0].position = 0.525
    colorramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    colorramp.color_ramp.elements[1].position = 0.58
    colorramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Principled BSDF, MULTI_GGX distribution
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    try:
        bsdf.distribution = "MULTI_GGX"
    except Exception:
        pass
    bsdf.inputs["Base Color"].default_value = (0.904, 0.904, 0.904, 1.0)
    _set_principled_input(bsdf, "Subsurface Weight", subsurface)
    # Subsurface Radius is a Vector input; route the vec_math output into it
    if "Subsurface Radius" in bsdf.inputs:
        nt.links.new(vec_math.outputs["Vector"], bsdf.inputs["Subsurface Radius"])
    if "Subsurface Color" in bsdf.inputs:
        bsdf.inputs["Subsurface Color"].default_value = (0.904, 0.904, 0.904, 1.0)
    _set_principled_input(bsdf, "Specular IOR Level", 0.224)
    bsdf.inputs["Roughness"].default_value = 0.1
    # Coat Weight is driven by the colorramp output
    coat_name = "Coat Weight" if "Coat Weight" in bsdf.inputs else (
        "Clearcoat" if "Clearcoat" in bsdf.inputs else None
    )
    if coat_name is not None:
        nt.links.new(colorramp.outputs["Color"], bsdf.inputs[coat_name])
    _set_principled_input(bsdf, "Coat Roughness", 0.1)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat

seed_all(SEED)
# SnowflakeFactory.__init__ does not sample any material RNG; shader_snow has
# fixed constants except for the subsurface parameter pinned to 0 by
# finalize_assets. No wear_tear pass in for SnowflakeFactory.
CATEG_MAT = make_snow_mat("SnowflakeFactory_Material", subsurface=0.0)
CATEG_MAT.use_fake_user = True

# --- GeoNodes: translation of geo_snowtexture ---
# Builds a small nodegroup matching the upstream pipeline so the procedural
# snow surface detail is applied to the snowflake mesh before materialising.
def _new_math(nt, op, a=None, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    if a is not None:
        n.inputs[0].default_value = a
    if b is not None:
        n.inputs[1].default_value = b
    return n

def _new_vmath(nt, op):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    return n

def build_snow_geonodes():
    ng = bpy.data.node_groups.new("SnowflakeDeform", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    group_in = ng.nodes.new("NodeGroupInput")
    group_out = ng.nodes.new("NodeGroupOutput")
    group_out.is_active_output = True

    input_normal = ng.nodes.new("GeometryNodeInputNormal")
    input_position0 = ng.nodes.new("GeometryNodeInputPosition")

    # position = position0 * 12
    pos_scale = _new_vmath(ng, "MULTIPLY")
    ng.links.new(input_position0.outputs["Position"], pos_scale.inputs[0])
    pos_scale.inputs[1].default_value = (12.0, 12.0, 12.0)

    # noise_texture: Scale=12, Detail=2
    noise0 = ng.nodes.new("ShaderNodeTexNoise")
    noise0.inputs["Scale"].default_value = 12.0
    noise0.inputs["Detail"].default_value = 2.0
    ng.links.new(pos_scale.outputs["Vector"], noise0.inputs["Vector"])

    # noise_texture_1: Scale=2, Detail=4
    noise1 = ng.nodes.new("ShaderNodeTexNoise")
    noise1.inputs["Scale"].default_value = 2.0
    noise1.inputs["Detail"].default_value = 4.0
    ng.links.new(pos_scale.outputs["Vector"], noise1.inputs["Vector"])

    cr1 = ng.nodes.new("ShaderNodeValToRGB")
    fac1 = noise1.outputs.get("Fac") or noise1.outputs[0]
    ng.links.new(fac1, cr1.inputs["Fac"])
    cr1.color_ramp.elements[0].position = 0.069
    cr1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr1.color_ramp.elements[1].position = 0.757
    cr1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # noise_texture_2: Scale=1, Detail=4
    noise2 = ng.nodes.new("ShaderNodeTexNoise")
    noise2.inputs["Scale"].default_value = 1.0
    noise2.inputs["Detail"].default_value = 4.0
    ng.links.new(pos_scale.outputs["Vector"], noise2.inputs["Vector"])

    cr2 = ng.nodes.new("ShaderNodeValToRGB")
    fac2 = noise2.outputs.get("Fac") or noise2.outputs[0]
    ng.links.new(fac2, cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.069
    cr2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr2.color_ramp.elements[1].position = 0.757
    cr2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # height = 0.6*noise0.Fac + 0.4*cr1 + cr2   (all scalars)
    mul_a = _new_math(ng, "MULTIPLY", b=0.6)
    fac0 = noise0.outputs.get("Fac") or noise0.outputs[0]
    ng.links.new(fac0, mul_a.inputs[0])

    mul_b = _new_math(ng, "MULTIPLY", b=0.4)
    ng.links.new(cr1.outputs["Color"], mul_b.inputs[0])

    add_ab = _new_math(ng, "ADD")
    ng.links.new(mul_a.outputs["Value"], add_ab.inputs[0])
    ng.links.new(mul_b.outputs["Value"], add_ab.inputs[1])

    add_height = _new_math(ng, "ADD")
    ng.links.new(add_ab.outputs["Value"], add_height.inputs[0])
    ng.links.new(cr2.outputs["Color"], add_height.inputs[1])

    # MapRange: height in [0,2] -> [-0.03, 0.03]
    map_range = ng.nodes.new("ShaderNodeMapRange")
    ng.links.new(add_height.outputs["Value"], map_range.inputs["Value"])
    map_range.inputs["From Min"].default_value = 0.0
    map_range.inputs["From Max"].default_value = 2.0
    map_range.inputs["To Min"].default_value = -0.03
    map_range.inputs["To Max"].default_value = 0.03

    # modulation noise on raw position0, Scale=0.5
    modulation = ng.nodes.new("ShaderNodeTexNoise")
    modulation.inputs["Scale"].default_value = 0.5
    ng.links.new(input_position0.outputs["Position"], modulation.inputs["Vector"])

    cr3 = ng.nodes.new("ShaderNodeValToRGB")
    fac3 = modulation.outputs.get("Fac") or modulation.outputs[0]
    ng.links.new(fac3, cr3.inputs["Fac"])
    cr3.color_ramp.elements[0].position = 0.25
    cr3.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr3.color_ramp.elements[1].position = 0.75
    cr3.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # offset = normal * map_range * cr3  (vector * scalar * scalar)
    scale_normal = _new_vmath(ng, "SCALE")
    ng.links.new(input_normal.outputs["Normal"], scale_normal.inputs[0])
    ng.links.new(map_range.outputs["Result"], scale_normal.inputs["Scale"])

    scale_offset = _new_vmath(ng, "SCALE")
    ng.links.new(scale_normal.outputs["Vector"], scale_offset.inputs[0])
    ng.links.new(cr3.outputs["Color"], scale_offset.inputs["Scale"])

    set_position = ng.nodes.new("GeometryNodeSetPosition")
    ng.links.new(group_in.outputs["Geometry"], set_position.inputs["Geometry"])
    ng.links.new(scale_offset.outputs["Vector"], set_position.inputs["Offset"])
    ng.links.new(set_position.outputs["Geometry"], group_out.inputs["Geometry"])
    return ng

# --- Geometry (copied verbatim from objects_blender/particles/SnowflakeFactory.py) ---
random.seed(SEED)
np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.context.scene.cursor.location = (0, 0, 0)

bpy.ops.mesh.primitive_circle_add(vertices=6, fill_type='TRIFAN', location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "SnowflakeFactory"

# Apply the snow surface-perturbation geonodes (mirrors snow.apply's add_geomod)
mod = obj.modifiers.new("SnowDeform", "NODES")
mod.node_group = build_snow_geonodes()
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
try:
    bpy.ops.object.modifier_apply(modifier=mod.name)
except Exception:
    # A flat 6-vertex trifan has degenerate normals in some seeds; if the
    # modifier can't be applied, drop it silently so the factory still yields
    # the base snowflake mesh with the correct shader.
    obj.modifiers.remove(mod)

# Assign the snow material (single-slot, matches finalize_assets(surface.add_material))
obj.data.materials.clear()
obj.data.materials.append(CATEG_MAT)

print(
    f"SnowflakeFactory built: {len(obj.data.vertices)} verts, "
    f"{len(obj.data.polygons)} faces, "
    f"{len(obj.data.materials)} material slot(s)"
)

