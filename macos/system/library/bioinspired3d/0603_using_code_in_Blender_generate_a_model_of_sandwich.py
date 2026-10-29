# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_code_in_Blender_generate_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using code in Blender generate a model of sandwich

import bpy

# Reset the scene by deleting all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a function to add a material

def add_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Create materials for each ingredient
bread_material = add_material('Bread Material', (0.96, 0.87, 0.70, 1))
lettuce_material = add_material('Lettuce Material', (0.13, 0.55, 0.13, 1))
tomato_material = add_material('Tomato Material', (0.8, 0.1, 0.1, 1))
cheese_material = add_material('Cheese Material', (1, 0.83, 0, 1))

# Create components of the sandwich
components = [
    (0, 0, 0, 'Bottom Bread', bread_material, 0.1),
    (0, 0, 0.2, 'Lettuce', lettuce_material, 0.05),
    (0, 0, 0.3, 'Tomato', tomato_material, 0.05),
    (0, 0, 0.4, 'Cheese', cheese_material, 0.05),
    (0, 0, 0.6, 'Top Bread', bread_material, 0.1)
]

for loc in components:
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc[:3])
    obj = bpy.context.object
    obj.scale[2] = loc[5]
    obj.name = loc[3]
    obj.data.materials.append(loc[4])


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
