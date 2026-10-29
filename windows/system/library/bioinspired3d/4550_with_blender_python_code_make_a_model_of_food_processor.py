# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code_make_a_model_of_food_processor" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code make a model of food processor.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with distinct colors
material_base = bpy.data.materials.new(name='Main Material')
material_base.diffuse_color = (0.2, 0.2, 0.2, 1)
material_transparent = bpy.data.materials.new(name='Transparent Material')
material_transparent.diffuse_color = (1, 1, 1, 0.1)
material_lid = bpy.data.materials.new(name='Lid Material')
material_lid.diffuse_color = (0.8, 0.8, 0.8, 1)
material_button = bpy.data.materials.new(name='Button Material')
material_button.diffuse_color = (0.8, 0, 0, 1)

# Function to create a cube
def create_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create the base
base_object = create_cube(2, (0, 0, 0.5), 'Base', material_base)
base_object.scale = (1, 1, 0.5)

# Create the container
container_object = create_cylinder(0.75, 1.5, (0, 0, 1.75), 'Container', material_transparent)

# Create the lid
lid_object = create_cylinder(0.8, 0.1, (0, 0, 2.5), 'Lid', material_lid)

# Create the feed tube
feed_tube_object = create_cylinder(0.2, 0.5, (0, 0, 2.75), 'Feed Tube', material_lid)

# Create the control panel
control_panel_object = create_cube(0.5, (0, 1.05, 0.25), 'Control Panel', material_base)
control_panel_object.scale = (1, 0.1, 0.5)

# Create buttons
for index in range(3):
    button_position = (-0.2 + index * 0.2, 1.1, 0.25)
    create_cube(0.1, button_position, f'Button {index + 1}', material_button)


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
