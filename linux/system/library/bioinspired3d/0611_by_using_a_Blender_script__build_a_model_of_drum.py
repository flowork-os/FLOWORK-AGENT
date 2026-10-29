# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__build_a_model_of_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, build a model of drum

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for the drum components
red_material = bpy.data.materials.new(name="Red Drum Body")
red_material.diffuse_color = (0.8, 0.2, 0.2, 1)
light_gray_material = bpy.data.materials.new(name="Light Gray Drumhead")
light_gray_material.diffuse_color = (0.9, 0.9, 0.9, 1)
brown_material = bpy.data.materials.new(name="Brown Drumsticks")
brown_material.diffuse_color = (0.5, 0.25, 0.1, 1)

# Function to create a cylinder with a given radius, depth, location, and material

def create_cylinder(radius, depth, location, material, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the drum body and drumhead
body = create_cylinder(1, 1.5, (0, 0, 0.75), red_material, "Drum Body")
drumhead = create_cylinder(1.05, 0.1, (0, 0, 1.5), light_gray_material, "Drumhead")

# Create the drumsticks using a loop
for index in range(2):
    position_x = 1.2 * (index * 2 - 1)
    create_cylinder(0.05, 1.5, (position_x, 0, 0.75), brown_material, f"Drumstick {index + 1}")


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
