# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_python_code_that_makes_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender python code that makes sandwich

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for sandwich components
mat_bread = bpy.data.materials.new(name="Bread")
mat_bread.diffuse_color = (0.9, 0.7, 0.5, 1)
mat_lettuce = bpy.data.materials.new(name="Lettuce")
mat_lettuce.diffuse_color = (0.2, 0.8, 0.2, 1)
mat_tomato = bpy.data.materials.new(name="Tomato")
mat_tomato.diffuse_color = (0.8, 0.1, 0.1, 1)
mat_cheese = bpy.data.materials.new(name="Cheese")
mat_cheese.diffuse_color = (1, 0.9, 0.1, 1)

# Function to create a flattened cube

def create_flat_cube(name, loc, scale_factor, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    cube_obj = bpy.context.object
    cube_obj.name = name
    cube_obj.scale[2] = scale_factor
    cube_obj.data.materials.append(material)

# Layer creation process
create_flat_cube("Bottom Slice", (0, 0, 0), 0.1, mat_bread)
create_flat_cube("Lettuce", (0, 0, 0.2), 0.05, mat_lettuce)
create_flat_cube("Tomato", (0, 0, 0.3), 0.05, mat_tomato)
create_flat_cube("Cheese", (0, 0, 0.4), 0.05, mat_cheese)
create_flat_cube("Top Slice", (0, 0, 0.6), 0.1, mat_bread)


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
