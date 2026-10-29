# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script_make_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script make a model of sandwich

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for sandwich components
sandwich_materials = {
    'bread': (0.9, 0.7, 0.5, 1),
    'lettuce': (0.2, 0.8, 0.2, 1),
    'tomato': (0.8, 0.1, 0.1, 1),
    'cheese': (1, 0.9, 0.1, 1)
}

# Object-oriented approach for sandwich layers
class SandwichLayer:
    def __init__(self, name, location, scale, material_color):
        self.name = name
        self.location = location
        self.scale = scale
        self.material_color = material_color
        self.create_layer()

    def create_layer(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=self.location)
        layer = bpy.context.object
        layer.name = self.name
        layer.scale[2] = self.scale
        mat = bpy.data.materials.new(name=self.name + " Mat")
        mat.diffuse_color = self.material_color
        layer.data.materials.append(mat)

# Create each sandwich layer
SandwichLayer("Bottom Bread", (0, 0, 0), 0.1, sandwich_materials['bread'])
SandwichLayer("Lettuce", (0, 0, 0.2), 0.05, sandwich_materials['lettuce'])
SandwichLayer("Tomato", (0, 0, 0.3), 0.1, sandwich_materials['tomato'])
SandwichLayer("Cheese", (0, 0, 0.4), 0.05, sandwich_materials['cheese'])
SandwichLayer("Top Bread", (0, 0, 0.6), 0.1, sandwich_materials['bread'])


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
