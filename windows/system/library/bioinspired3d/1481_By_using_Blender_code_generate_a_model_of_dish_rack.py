# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_code_generate_a_model_of_dish_rack" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender code generate a model of dish rack

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material with a gray color
material_gray = bpy.data.materials.new(name="MaterialGray")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cube with specific parameters

def create_cube(size, location, name, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Create the base of the model
base_cube = create_cube(2, (0, 0, 0.1), "BaseCube", (1, 0.5, 0.05), material_gray)

# Parameters for the slots
slots_count = 5
slot_dimensions = (0.1, 0.05, 0.5)
for index in range(slots_count):
    x_position = -0.9 + index * 0.4
    create_cube(1, (x_position, 0, 0.35), f"Slot_{index + 1}", slot_dimensions, material_gray)

# Create the flat area for placing items
create_cube(1, (0, -0.35, 0.1), "FlatArea", (0.9, 0.4, 0.05), material_gray)


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
