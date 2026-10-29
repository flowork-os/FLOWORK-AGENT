# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_sandwich_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct sandwich in a blender code

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sandwich components
material_bread = bpy.data.materials.new(name="Bread Material")
material_bread.diffuse_color = (0.9, 0.7, 0.5, 1)
material_lettuce = bpy.data.materials.new(name="Lettuce Material")
material_lettuce.diffuse_color = (0.2, 0.8, 0.2, 1)
material_tomato = bpy.data.materials.new(name="Tomato Material")
material_tomato.diffuse_color = (0.8, 0.1, 0.1, 1)
material_cheese = bpy.data.materials.new(name="Cheese Material")
material_cheese.diffuse_color = (1, 0.9, 0.1, 1)

# Function to add a cube with specified properties

def add_cube(name, position, height, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    cube = bpy.context.object
    cube.name = name
    cube.scale[2] = height
    cube.data.materials.append(material)

# Create the sandwich layers
add_cube("Bottom Bread", (0, 0, 0), 0.1, material_bread)
add_cube("Lettuce Layer", (0, 0, 0.2), 0.05, material_lettuce)
add_cube("Tomato Slice", (0, 0, 0.3), 0.05, material_tomato)
add_cube("Cheese Layer", (0, 0, 0.4), 0.05, material_cheese)
add_cube("Top Bread", (0, 0, 0.6), 0.1, material_bread)


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
