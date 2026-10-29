# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_builds_a_model_of_syringe_pump" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that builds a model of syringe pump.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create color materials
light_gray = bpy.data.materials.new(name="Light Gray")
light_gray.diffuse_color = (0.6, 0.6, 0.6, 1)
dim_gray = bpy.data.materials.new(name="Dim Gray")
dim_gray.diffuse_color = (0.2, 0.2, 0.2, 1)
azure = bpy.data.materials.new(name="Azure")
azure.diffuse_color = (0.1, 0.2, 0.8, 1)
leaf_green = bpy.data.materials.new(name="Leaf Green")
leaf_green.diffuse_color = (0.1, 0.8, 0.1, 1)

# Function to create a cube with specified properties
def create_cube(size, location, name, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Constructing the main body
main_structure = create_cube(2, (0, 0, 0), "Main Structure", (1, 0.5, 0.3), light_gray)

# Creating syringe slot
syringe_hole = create_cube(1, (0, 0.6, 0), "Syringe Hole", (0.8, 0.1, 0.2), dim_gray)

# Creating interface panel
interface_panel = create_cube(1, (0, -0.6, 0.1), "Interface Panel", (0.8, 0.1, 0.2), dim_gray)

# Adding buttons to the interface
for idx in range(3):
    button_position = (-0.3 + idx * 0.3, -0.7, 0.1)
    button = create_cube(0.1, button_position, f"Control Button {idx + 1}", (0.1, 0.05, 0.05), azure)

# Creating the display screen
screen_display = create_cube(0.4, (0.5, -0.7, 0.1), "Display Screen", (0.3, 0.05, 0.1), leaf_green)


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
