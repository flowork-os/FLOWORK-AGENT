# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_code_to_make_a_model_of_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender code to make a model of transformer.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts
material_core = bpy.data.materials.new(name="Material Core")
material_core.diffuse_color = (0.2, 0.2, 0.2, 1)
material_winding = bpy.data.materials.new(name="Material Winding")
material_winding.diffuse_color = (1, 0.5, 0, 1)
material_casing = bpy.data.materials.new(name="Material Casing")
material_casing.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to add a torus
def add_torus(name, location, radius_major=0.25, radius_minor=0.05):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius_major, minor_radius=radius_minor, location=location)
    torus = bpy.context.object
    torus.name = name
    return torus

# Create Core
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
core_obj = bpy.context.object
core_obj.name = "Core"
core_obj.scale = (0.5, 0.5, 1.5)
core_obj.data.materials.append(material_core)

# Create Windings
for i in range(2):
    x_location = 0.7 * (i * 2 - 1)
    winding_torus = add_torus(f"Winding_{i + 1}", (x_location, 0, 0))
    winding_torus.data.materials.append(material_winding)

# Create Casing
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
casing_obj = bpy.context.object
casing_obj.name = "Casing"
casing_obj.scale = (1.5, 1.5, 2)
casing_obj.data.materials.append(material_casing)

# Make the casing partially transparent
material_casing.use_nodes = True
bsdf = material_casing.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Alpha'].default_value = 0.5
    casing_obj.show_transparent = True


# --- 3DCodeVerse geo variant: neutralize materials (auto-derived, do not edit) ---
import bpy as _bpy_geo
_geo_mat = _bpy_geo.data.materials.get("geo_neutral") or _bpy_geo.data.materials.new("geo_neutral")
try:
    _geo_mat.use_nodes = False
except Exception:
    pass
try:
    _geo_mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
except Exception:
    pass
for _geo_obj in list(_bpy_geo.data.objects):
    if _geo_obj.type == "MESH" and _geo_obj.data is not None:
        try:
            _geo_obj.data.materials.clear()
            _geo_obj.data.materials.append(_geo_mat)
        except Exception:
            pass
# --- end geo variant ---
