# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_pizza_cutter_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build pizza cutter in blender python code

import bpy
import math

# Remove all meshes from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function for creating and returning a new cylinder with a set material

def add_cylinder(radius, height, position, object_name, color_tuple):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    new_cylinder = bpy.context.object
    new_cylinder.name = object_name
    new_material = bpy.data.materials.new(name=f'{object_name}Material')
    new_material.diffuse_color = color_tuple
    new_cylinder.data.materials.append(new_material)
    return new_cylinder

# Create the Blade, Handle, and Pivot
blade_cylinder = add_cylinder(0.3, 0.05, (0, 0, 0), 'Blade', (0.85, 0.85, 0.85, 1))
handle_cylinder = add_cylinder(0.1, 1, (0, -0.6, 0), 'Handle', (0.15, 0.15, 0.15, 1))
pivot_cylinder = add_cylinder(0.05, 0.15, (0, 0, 0.025), 'Pivot', (0.55, 0.55, 0.55, 1))

# Parent the Blade to the Pivot
bpy.context.view_layer.objects.active = pivot_cylinder
blade_cylinder.select_set(True)
pivot_cylinder.select_set(True)
bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)


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
