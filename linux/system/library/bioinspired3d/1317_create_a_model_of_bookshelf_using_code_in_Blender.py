# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_bookshelf_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of bookshelf using code in Blender

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create and assign a material
def assign_material(object, name, color):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    object.data.materials.append(material)

# Create wood-like material
wood_color = (0.55, 0.27, 0.07, 1)

# Shelf specifications
shelf_specs = {'height': 0.1, 'width': 1.0, 'depth': 0.3, 'count': 5}
spacing = 2.0 / (shelf_specs['count'] + 1)

# Function to create shelves
for index in range(shelf_specs['count']):
    z_position = (index + 1) * spacing
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z_position))
    current_shelf = bpy.context.object
    current_shelf.scale = (shelf_specs['width'], shelf_specs['depth'], shelf_specs['height'])
    current_shelf.name = f'Shelf_{index + 1}'
    assign_material(current_shelf, 'WoodMaterial', wood_color)

# Panel dimensions
panel_thickness = 0.05
panel_height = 2.0 + 2 * shelf_specs['height']
panel_depth = shelf_specs['depth'] + 2 * panel_thickness

# Create side panels
for side in ['Left', 'Right']:
    x_offset = -1 if side == 'Left' else 1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_offset * (shelf_specs['width'] / 2 + panel_thickness / 2), 0, 1.0))
    side_panel = bpy.context.object
    side_panel.scale = (panel_thickness, panel_depth, panel_height)
    side_panel.name = f'{side}_Panel'
    assign_material(side_panel, 'WoodMaterial', wood_color)

# Create the back panel
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -shelf_specs['depth'] / 2 - panel_thickness / 2, 1.0))
back_panel = bpy.context.object
back_panel.scale = (shelf_specs['width'] + 2 * panel_thickness, panel_thickness, panel_height)
back_panel.name = 'Back_Panel'
assign_material(back_panel, 'WoodMaterial', wood_color)


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
