# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_script__build_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender script, build sandwich

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for sandwich layers
bread_mat = bpy.data.materials.new(name='Bread')
bread_mat.diffuse_color = (0.9, 0.7, 0.5, 1)

lettuce_mat = bpy.data.materials.new(name='Lettuce')
lettuce_mat.diffuse_color = (0.2, 0.8, 0.2, 1)

tomato_mat = bpy.data.materials.new(name='Tomato')
tomato_mat.diffuse_color = (0.8, 0.1, 0.1, 1)

cheese_mat = bpy.data.materials.new(name='Cheese')
cheese_mat.diffuse_color = (1, 0.9, 0.5, 1)

ham_mat = bpy.data.materials.new(name='Ham')
ham_mat.diffuse_color = (0.9, 0.5, 0.1, 1)

# Function to add cube layers
def add_cube_layer(location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.scale[2] = scale
    cube.name = name
    cube.data.materials.append(material)

# Create sandwich layers
add_cube_layer((0, 0, 0), 0.1, 'Bottom Bread', bread_mat)
add_cube_layer((0, 0, 0.2), 0.05, 'Lettuce', lettuce_mat)
add_cube_layer((0, 0, 0.3), 0.05, 'Tomato', tomato_mat)
add_cube_layer((0, 0, 0.4), 0.05, 'Cheese', cheese_mat)
add_cube_layer((0, 0, 0.5), 0.05, 'Ham', ham_mat)
add_cube_layer((0, 0, 0.7), 0.1, 'Top Bread', bread_mat)


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
