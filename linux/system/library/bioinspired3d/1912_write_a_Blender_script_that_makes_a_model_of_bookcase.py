# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_script_that_makes_a_model_of_bookcase" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender script that makes a model of bookcase.

import bpy

# Clear the mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the wood
material_wood = bpy.data.materials.new(name='Wood Color')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Shelf specifications
shelf_dimensions = {'width': 2, 'height': 0.1, 'depth': 0.4}
spacing_between_shelves = 0.5
number_of_shelves = 3

# Function to add a shelf
def add_shelf(index):
    z_position = index * spacing_between_shelves
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (shelf_dimensions['width'] / 2, shelf_dimensions['depth'] / 2, shelf_dimensions['height'] / 2)
    shelf.name = f'Shelf {index + 1}'
    shelf.data.materials.append(material_wood)

# Loop to create shelves
for i in range(number_of_shelves):
    add_shelf(i)

# Create the top surface
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, number_of_shelves * spacing_between_shelves))
top_surface = bpy.context.object
top_surface.scale = (shelf_dimensions['width'] / 2, shelf_dimensions['depth'] / 2, 0.05)
top_surface.name = 'Top Surface'
top_surface.data.materials.append(material_wood)

# Create side panels
panel_thickness = 0.05
panel_height = number_of_shelves * spacing_between_shelves
for i in range(2):
    x_position = shelf_dimensions['width'] / 2 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, panel_height / 2))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness / 2, shelf_dimensions['depth'] / 2, panel_height / 2)
    side_panel.name = f'Side Panel {i + 1}'
    side_panel.data.materials.append(material_wood)


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
