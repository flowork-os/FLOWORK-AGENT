# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_coffee_grinder_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build coffee grinder in code in Blender

import bpy
import math

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials
metal_material = bpy.data.materials.new(name='Gray Metal')
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)
wood_material = bpy.data.materials.new(name='Brown Wood')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to add a cylinder to the scene

def add_cylinder(radius, height, position, obj_name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = obj_name
    obj.data.materials.append(mat)

# Create the base
add_cylinder(1, 0.2, (0, 0, 0), 'Base', wood_material)

# Create the body
add_cylinder(0.8, 1.5, (0, 0, 0.85), 'Body', metal_material)

# Create the top
add_cylinder(0.9, 0.1, (0, 0, 1.55), 'Top', metal_material)

# Create the handle
add_cylinder(0.05, 1, (0.9, 0, 1.65), 'Handle', metal_material)

# Rotate the handle
bpy.context.object.rotation_euler = (0, math.pi/2, 0)

# Create the knob
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(1.45, 0, 1.65))
knob = bpy.context.object
knob.name = 'Knob'
knob.data.materials.append(wood_material)


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
