# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_blender_code_that_creates_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a blender code that creates sandwich.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define colors for each sandwich layer
bread_material = (0.9, 0.7, 0.5, 1)
lettuce_material = (0.2, 0.8, 0.2, 1)
tomato_material = (0.8, 0.1, 0.1, 1)
cheese_material = (1, 0.9, 0.1, 1)

# Function to add a sandwich layer
def add_sandwich_layer(name, position, height, color):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    layer = bpy.context.object
    layer.name = name
    layer.scale[2] = height
    material = bpy.data.materials.new(name=name + " Color")
    material.diffuse_color = color
    layer.data.materials.append(material)

# Create each layer of the sandwich
add_sandwich_layer("Bottom Slice", (0, 0, 0), 0.1, bread_material)
add_sandwich_layer("Lettuce Layer", (0, 0, 0.2), 0.05, lettuce_material)
add_sandwich_layer("Tomato Layer", (0, 0, 0.3), 0.1, tomato_material)
add_sandwich_layer("Cheese Layer", (0, 0, 0.4), 0.05, cheese_material)
add_sandwich_layer("Top Slice", (0, 0, 0.6), 0.1, bread_material)


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
