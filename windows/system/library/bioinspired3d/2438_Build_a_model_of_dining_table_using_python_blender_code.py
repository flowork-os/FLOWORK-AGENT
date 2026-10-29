# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_dining_table_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of dining table using python blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize material for the table
material_wood = bpy.data.materials.new(name='TableWood')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create the tabletop
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
top_surface = bpy.context.object
# Adjust the dimensions of the tabletop
top_surface.scale[0] = 1.5  # Length
top_surface.scale[1] = 1  # Width
top_surface.scale[2] = 0.1  # Thickness
top_surface.name = 'Top Surface'
top_surface.data.materials.append(material_wood)

# Define leg parameters
height_of_leg = 1
radius_of_leg = 0.1

# Create legs
for i in range(4):
    x_position = 1.4 * (i % 2) - 0.7
    y_position = 0.9 * (i // 2) - 0.45
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_leg, depth=height_of_leg, location=(x_position, y_position, height_of_leg / 2))
    leg_object = bpy.context.object
    leg_object.name = f'Leg_{i + 1}'
    leg_object.data.materials.append(material_wood)


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
