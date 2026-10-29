# [FL_INDEX: keywords="blender_factory, procedural_3d, RaindropFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: RaindropFactory | Category: factories_tex
# Prompt: A 3D model of a raindrop rendered from a slightly elevated front perspective, featuring a smooth hemispherical dome shape sitting on a flat circular base, with a translucent blue-gray glassy appearance and subtle specular highlights along the upper curved surface.

import os
import random

import bpy
import numpy as np

SEED = int(os.environ.get("SEED", 0))

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

# --- Inlined material (hand-crafted for RaindropFactory) ---
# Original: ShaderNodeBsdfPrincipled with IOR=1.33 (water) routed to MaterialOutput.
def make_raindrop_mat(name="RaindropFactory_Material"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    # IOR 1.33 corresponds to water; preserve upstream value exactly.
    glass.inputs["IOR"].default_value = 1.33
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0
    # Roughness is left at the Blender default (0.0) so the droplet refracts cleanly,
    # matching the upstream shader which does not set a roughness value.

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(glass.outputs["BSDF"], out.inputs["Surface"])

    # Enable blend/refraction for EEVEE previews so the glass is visibly transparent
    # in the texture-aware renderer; Cycles already handles the Glass BSDF directly.
    try:
        mat.blend_method = "BLEND"
    except Exception:
        pass
    try:
        mat.shadow_method = "HASHED"
    except Exception:
        pass

    return mat

seed_all(SEED)
# RaindropFactory.__init__ in does not sample any material RNG: the
# glass shader has fixed IOR=1.33, so we only need a constant material here.
CATEG_MAT = make_raindrop_mat("RaindropFactory_Material")
CATEG_MAT.use_fake_user = True

# --- Geometry (copied verbatim from objects_blender/particles/RaindropFactory.py) ---
random.seed(SEED)
np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.context.scene.cursor.location = (0, 0, 0)

def assign_curve(curve, points):
    """Set curve mapping points (first two exist by default, rest are added)."""

    for i, (x, y) in enumerate(points):
        if i < 2:
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)

def build_raindrop_geonodes():
    """Create GeoNodes group: Position -> VectorCurve -> SetPosition."""

    ng = bpy.data.node_groups.new("RaindropDeform", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    go.is_active_output = True
    pos = ng.nodes.new("GeometryNodeInputPosition")
    vc = ng.nodes.new("ShaderNodeVectorCurve")
    sp = ng.nodes.new("GeometryNodeSetPosition")

    # X,Y identity; Z pinches bottom for teardrop shape
    assign_curve(vc.mapping.curves[0], [(-1, -1), (1, 1)])
    assign_curve(vc.mapping.curves[1], [(-1, -1), (1, 1)])
    z_bottom = -0.15 * np.random.normal(1, 0.15)
    assign_curve(vc.mapping.curves[2], [(-1, z_bottom), (-0.6091, -0.0938), (1, 1)])
    vc.mapping.update()

    ng.links.new(pos.outputs["Position"], vc.inputs["Vector"])
    ng.links.new(gi.outputs["Geometry"], sp.inputs["Geometry"])
    ng.links.new(vc.outputs["Vector"], sp.inputs["Position"])
    ng.links.new(sp.outputs["Geometry"], go.inputs["Geometry"])
    return ng

# Build
bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=5, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "RaindropFactory"

mod = obj.modifiers.new("Deform", "NODES")
mod.node_group = build_raindrop_geonodes()
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.modifier_apply(modifier=mod.name)

# Assign the glass material (single-slot, matches finalize_assets(surface.add_material))
obj.data.materials.clear()
obj.data.materials.append(CATEG_MAT)

print(
    f"RaindropFactory built: {len(obj.data.vertices)} verts, "
    f"{len(obj.data.polygons)} faces, "
    f"{len(obj.data.materials)} material slot(s)"
)

