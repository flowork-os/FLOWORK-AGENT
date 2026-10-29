# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_code_make_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender code make bird cage.

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Setup material for the cage
cage_material = bpy.data.materials.new(name="Iron")
cage_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Light gray color

# Function to create the cage components

def create_cage():
    # Create the base
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.1, location=(0, 0, 0))
    base_object = bpy.context.object
    base_object.name = "Base"
    base_object.data.materials.append(cage_material)

    # Create the top
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.1, location=(0, 0, 2))
    top_object = bpy.context.object
    top_object.name = "Top"
    top_object.data.materials.append(cage_material)

    # Create bars
    for i in range(16):
        angle = (2 * math.pi / 16) * i
        x = math.cos(angle)
        y = math.sin(angle)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(x, y, 1))
        bar_object = bpy.context.object
        bar_object.name = f"Bar_{i + 1}"
        bar_object.data.materials.append(cage_material)

    # Create door
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 1))
    door_object = bpy.context.object
    door_object.name = "Door"
    door_object.data.materials.append(cage_material)

    # Create perch
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=(0, 0, 0.5), rotation=(0, math.pi/2, 0))
    perch_object = bpy.context.object
    perch_object.name = "Perch"
    perch_object.data.materials.append(cage_material)

# Execute the cage creation function
create_cage()


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
