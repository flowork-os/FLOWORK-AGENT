# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_builds_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that builds a model of blender.

import bpy

# Clear the current mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with unique identifiers
mat_base = bpy.data.materials.new(name='BaseMaterial')
mat_base.diffuse_color = (0.1, 0.1, 0.1, 1)
mat_jug = bpy.data.materials.new(name='JugMaterial')
mat_jug.diffuse_color = (0.8, 0.8, 0.8, 0.5)
mat_button = bpy.data.materials.new(name='ButtonMaterial')
mat_button.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to add a cylinder with given parameters
def add_cylinder(radius, height, position, object_name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = object_name
    obj.data.materials.append(material)

# Create parts of the model
add_cylinder(1, 0.5, (0, 0, 0.25), 'Base', mat_base)
add_cylinder(0.8, 2, (0, 0, 1.5), 'Jug', mat_jug)
add_cylinder(0.85, 0.1, (0, 0, 2.55), 'Lid', mat_base)

# Create buttons using a loop
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.5 - i * 0.3, 0.9, 0.25))
    button_object = bpy.context.object
    button_object.name = f'Button_{i + 1}'
    button_object.data.materials.append(mat_button)


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
