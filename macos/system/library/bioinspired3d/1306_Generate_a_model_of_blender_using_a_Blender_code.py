# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_blender_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of blender using a Blender code

import bpy

# Clear the scene by deleting all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_main = bpy.data.materials.new(name='Main Material')
material_main.diffuse_color = (0.2, 0.2, 0.2, 1)
material_translucent = bpy.data.materials.new(name='Translucent Material')
material_translucent.diffuse_color = (0.8, 0.8, 0.8, 0.5)
material_dark = bpy.data.materials.new(name='Dark Material')
material_dark.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to add a cylinder

def add_cylinder(radius, height, position, name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)

# Create base, pitcher, lid, and center cap
add_cylinder(1, 0.5, (0, 0, 0.25), 'Base', material_main)
add_cylinder(0.9, 2, (0, 0, 1.5), 'Pitcher', material_translucent)
add_cylinder(0.95, 0.1, (0, 0, 2.55), 'Lid', material_dark)
add_cylinder(0.3, 0.1, (0, 0, 2.65), 'Center Cap', material_dark)

# Create small cubes for measurement marks
for index in range(1, 5):
    bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0.95, 0, 0.5 * index + 0.5))
    mark = bpy.context.object
    mark.name = f'Marking {index}'
    mark.data.materials.append(material_dark)


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
