# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_to_create_a_model_of_coffee_maker" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code to create a model of coffee maker

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
mat_black = bpy.data.materials.new(name="Matte Black")
mat_black.diffuse_color = (0.0, 0.0, 0.0, 1)
mat_silver = bpy.data.materials.new(name="Shiny Silver")
mat_silver.diffuse_color = (0.75, 0.75, 0.75, 1)
mat_transparent = bpy.data.materials.new(name="Translucent")
mat_transparent.diffuse_color = (0.8, 0.8, 0.8, 0.3)

# Function to create a cube

def create_cube(size, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Create the main body
body = create_cube(2, (0, 0, 1), (0.7, 0.5, 1.5), mat_black)
body.name = "Main Body"

# Create the carafe
bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.8, location=(0, 0.7, 0.4))
carafe = bpy.context.object
carafe.name = "Carafe"
carafe.data.materials.append(mat_silver)

# Create control panel
control_panel = create_cube(0.5, (0.8, 0, 1.2), (0.1, 0.3, 0.4), mat_silver)
control_panel.name = "Control Panel"

# Create buttons using a loop
for index in range(3):
    create_cube(0.1, (0.9, -0.2 + index * 0.2, 1.2), (0.05, 0.05, 0.05), mat_black).name = f"Button {index + 1}"

# Create the water reservoir
reservoir = create_cube(1.5, (0, -0.6, 1.2), (0.6, 0.1, 1.2), mat_transparent)
reservoir.name = "Water Reservoir"

# Create water level indicator
indicator = create_cube(1, (0, -0.7, 1.2), (0.05, 0.05, 1), mat_black)
indicator.name = "Water Level Indicator"


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
