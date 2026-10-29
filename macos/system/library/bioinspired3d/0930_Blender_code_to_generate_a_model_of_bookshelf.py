# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_generate_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to generate a model of bookshelf

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the wood
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Class to handle shelf creation
class Shelf:
    def __init__(self, index, width, depth, height, spacing):
        self.index = index
        self.width = width
        self.depth = depth
        self.height = height
        self.spacing = spacing

    def create(self):
        z_position = self.index * self.spacing
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, z_position))
        shelf_object = bpy.context.object
        shelf_object.scale = (self.width / 2, self.depth / 2, self.height / 2)
        shelf_object.name = f'Shelf_{self.index + 1}'
        shelf_object.data.materials.append(wood_material)

# Create shelves
shelf_width = 2
shelf_height = 0.1
shelf_depth = 0.4
shelf_spacing = 0.5
num_shelves = 5

for i in range(num_shelves):
    shelf = Shelf(i, shelf_width, shelf_depth, shelf_height, shelf_spacing)
    shelf.create()

# Function to create side panels

def create_side_panel(index, thickness, height):
    x_position = shelf_width / 2 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(x_position, 0, height / 2))
    panel_object = bpy.context.object
    panel_object.scale = (thickness / 2, shelf_depth / 2, height / 2)
    panel_object.name = f'Panel_{index + 1}'
    panel_object.data.materials.append(wood_material)

# Create side panels
panel_thickness = 0.05
panel_height = num_shelves * shelf_spacing
for i in range(2):
    create_side_panel(i, panel_thickness, panel_height)


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
