# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_generates_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that generates sandwich

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to represent a sandwich layer
class SandwichLayer:
    def __init__(self, name, size, location, height, color):
        self.name = name
        self.size = size
        self.location = location
        self.height = height
        self.color = color
        self.create_layer()

    def create_layer(self):
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=self.location)
        layer = bpy.context.object
        layer.name = self.name
        layer.scale[2] = self.height
        mat = bpy.data.materials.new(name=self.name)
        mat.diffuse_color = self.color
        layer.data.materials.append(mat)

# Define colors for each layer
colors = {
    'Bread': (0.96, 0.87, 0.70, 1),
    'Lettuce': (0.13, 0.55, 0.13, 1),
    'Tomato': (0.89, 0.15, 0.07, 1),
    'Cheese': (1.0, 0.83, 0.0, 1),
    'Meat': (0.55, 0.27, 0.07, 1)
}

# Create each component of the sandwich
SandwichLayer('Bottom Bread', 2, (0, 0, 0), 0.1, colors['Bread'])
SandwichLayer('Lettuce', 1.8, (0, 0, 0.2), 0.05, colors['Lettuce'])
SandwichLayer('Tomato', 1.8, (0, 0, 0.3), 0.05, colors['Tomato'])
SandwichLayer('Cheese', 1.8, (0, 0, 0.4), 0.05, colors['Cheese'])
SandwichLayer('Meat', 1.8, (0, 0, 0.5), 0.1, colors['Meat'])
SandwichLayer('Top Bread', 2, (0, 0, 0.7), 0.1, colors['Bread'])


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
