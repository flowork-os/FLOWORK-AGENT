# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_that_creates_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender that creates a model of bookshelf.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to initialize wood material

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Create wood material
wood_material = create_material('WoodMaterial', (0.55, 0.27, 0.07, 1))

# Parameters for shelves
shelf_params = {
    'height': 0.1,
    'width': 1.0,
    'depth': 0.3,
    'count': 5,
    'total_height': 2.0
}
spacing = shelf_params['total_height'] / (shelf_params['count'] + 1)

# Adding shelves using a loop
for i in range(shelf_params['count']):
    z_position = (i + 1) * spacing
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z_position))
    shelf = bpy.context.object
    shelf.scale = (shelf_params['width'], shelf_params['depth'], shelf_params['height'])
    shelf.name = f'Shelf_{i + 1}'
    shelf.data.materials.append(wood_material)

# Dimensions for side panels
panel_thickness = 0.05
panel_height = shelf_params['total_height'] + 2 * shelf_params['height']
panel_depth = shelf_params['depth'] + 2 * panel_thickness

# Creating side panels
for side in [(-1, 'Left_Panel'), (1, 'Right_Panel')]:
    x_offset, name = side
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_offset * (shelf_params['width'] / 2 + panel_thickness / 2), 0, shelf_params['total_height'] / 2))
    panel = bpy.context.object
    panel.scale = (panel_thickness, panel_depth, panel_height)
    panel.name = name
    panel.data.materials.append(wood_material)

# Back panel dimensions
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -shelf_params['depth'] / 2 - panel_thickness / 2, shelf_params['total_height'] / 2))
back_panel = bpy.context.object
back_panel.scale = (shelf_params['width'] + 2 * panel_thickness, panel_thickness, panel_height)
back_panel.name = 'Back_Panel'
back_panel.data.materials.append(wood_material)


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
