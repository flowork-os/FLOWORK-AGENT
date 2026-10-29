# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_that_creates_hand_saw" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code that creates hand saw

import bpy
import math

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the knife components
blade_material = bpy.data.materials.new(name="MetallicBlade")
blade_material.diffuse_color = (0.5, 0.5, 0.5, 1)
handle_material = bpy.data.materials.new(name="WoodenHandle")
handle_material.diffuse_color = (0.8, 0.4, 0.1, 1)

# Function to create the blade

def create_blade():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    blade = bpy.context.object
    blade.name = "Blade"
    blade.scale[0] = 3
    blade.scale[1] = 0.05
    blade.scale[2] = 0.5
    blade.data.materials.append(blade_material)

create_blade()

# Create teeth on the blade
for index in range(12):
    tooth_position = (-2.7 + index * 0.5, 0, -0.5)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.1, depth=0.2, location=tooth_position)
    tooth = bpy.context.object
    tooth.name = f"Tooth {index + 1}"
    tooth.rotation_euler[1] = math.pi / 2
    tooth.data.materials.append(blade_material)

# Function to create the handle

def create_handle():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(3.5, 0, 0))
    handle = bpy.context.object
    handle.name = "Handle"
    handle.scale[0] = 0.5
    handle.scale[1] = 0.3
    handle.scale[2] = 1
    handle.data.materials.append(handle_material)

create_handle()

# Function to create grips

def create_grip(offset):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1, location=(3.5, offset, 0.5), rotation=(0, math.pi / 2, 0))
    grip = bpy.context.object
    grip.name = "Grip"
    grip.data.materials.append(handle_material)

create_grip(0.2)
create_grip(-0.2)


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
