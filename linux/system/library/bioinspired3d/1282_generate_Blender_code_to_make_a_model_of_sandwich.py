# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_to_make_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code to make a model of sandwich

import bpy

# Start by cleaning the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define the sandwich materials with unique colors
materials = {
    'Bread': (0.9, 0.7, 0.5, 1),
    'Lettuce': (0.2, 0.8, 0.2, 1),
    'Tomato': (0.8, 0.1, 0.1, 1),
    'Cheese': (1, 0.9, 0.1, 1),
    'Ham': (0.9, 0.6, 0.6, 1)
}

# Class to represent a sandwich layer
class SandwichLayer:
    def __init__(self, name, location, scale, color):
        self.name = name
        self.location = location
        self.scale = scale
        self.color = color

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=self.location)
        obj = bpy.context.object
        obj.name = self.name
        obj.scale = self.scale
        mat = bpy.data.materials.new(name=self.name)
        mat.diffuse_color = self.color
        obj.data.materials.append(mat)

# Create each layer of the sandwich
layers = [
    SandwichLayer('Bottom Bread', (0, 0, 0), (1, 1, 0.1), materials['Bread']),
    SandwichLayer('Lettuce', (0, 0, 0.15), (1, 1, 1), materials['Lettuce']),
    SandwichLayer('Tomato', (0, 0, 0.25), (1, 1, 1), materials['Tomato']),
    SandwichLayer('Cheese', (0, 0, 0.35), (1, 1, 1), materials['Cheese']),
    SandwichLayer('Ham', (0, 0, 0.45), (1, 1, 1), materials['Ham']),
    SandwichLayer('Top Bread', (0, 0, 0.6), (1, 1, 0.1), materials['Bread'])
]

for layer in layers:
    layer.create()


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
