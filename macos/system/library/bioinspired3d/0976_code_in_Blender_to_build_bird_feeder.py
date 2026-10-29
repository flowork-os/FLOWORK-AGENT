# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_build_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to build bird feeder.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the wood texture
wood_material = bpy.data.materials.new(name="WoodMaterial")
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to create a cylinder

def add_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(wood_material)
    return obj

# Create the main structure
main_structure = add_cylinder(0.5, 1.0, (0, 0, 0.5), "MainStructure")

# Function to create a cone

def add_cone(radius1, radius2, depth, location, name):
    bpy.ops.mesh.primitive_cone_add(radius1=radius1, radius2=radius2, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(wood_material)
    return obj

# Create the roof
roof_structure = add_cone(0.5, 0.1, 0.5, (0, 0, 1.25), "RoofStructure")

# Create the perch using the cylinder function
perch_location = (0, 0.55, 0.5)
perch_rotation = (1.57, 0, 0)
add_cylinder(0.05, 1.0, perch_location, "Perch")


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
