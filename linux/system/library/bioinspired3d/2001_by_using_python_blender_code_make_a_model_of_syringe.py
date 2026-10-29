# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code_make_a_model_of_syringe" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code make a model of syringe.

import bpy
import math

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder with a specified material
def create_material_cylinder(radius, height, pos, obj_name, color):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=pos)
    obj = bpy.context.object
    obj.name = obj_name
    mat = bpy.data.materials.new(name=f'{obj_name}_Material')
    mat.diffuse_color = color
    obj.data.materials.append(mat)

# Build the barrel
create_material_cylinder(0.1, 2.0, (0, 0, 1.0), 'Barrel', (0.8, 0.8, 0.8, 1))
# Build the plunger
create_material_cylinder(0.08, 2.1, (0, 0, 1.05), 'Plunger', (0.6, 0.6, 0.6, 1))
# Build the needle
create_material_cylinder(0.01, 0.5, (0, 0, -0.25), 'Needle', (0.7, 0.7, 0.7, 1))

# Material for the measurement markings
markings_material = bpy.data.materials.new(name='MarkingsMaterial')
markings_material.diffuse_color = (0.0, 0.0, 0.0, 1)

# Add measurement markings
for i in range(1, 10):
    bpy.ops.mesh.primitive_plane_add(size=0.02, location=(0.11, 0, 0.2 * i))
    marking = bpy.context.object
    marking.name = f'Marking_{i}'
    marking.data.materials.append(markings_material)
    marking.rotation_euler = (math.pi / 2, 0, 0)


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
