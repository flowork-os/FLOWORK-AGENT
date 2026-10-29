# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_bird_cage_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make bird cage using Blender code

import bpy
import math

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a shiny metallic material
metallic_material = bpy.data.materials.new(name="ShinyMetal")
metallic_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray metallic finish

# Function to create a cylinder

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(metallic_material)
    return cylinder

# Create the base
base_cylinder = create_cylinder(1, 0.1, (0, 0, 0), "Base")

# Create vertical bars
bar_count = 16
for index in range(bar_count):
    theta = (2 * math.pi / bar_count) * index
    x_position = math.cos(theta)
    y_position = math.sin(theta)
    create_cylinder(0.05, 2, (x_position, y_position, 1), f"VerticalBar_{index + 1}")

# Create the dome top
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
dome_sphere = bpy.context.object

dome_sphere.name = "Dome"
dome_sphere.scale[2] = 0.5  # Flatten to create a dome shape

dome_sphere.data.materials.append(metallic_material)

# Create the door
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 1))
door_cube = bpy.context.object

door_cube.name = "EntranceDoor"
door_cube.scale[2] = 1.5  # Scale the door up

door_cube.rotation_euler[2] = math.pi / 2  # Rotate for vertical alignment

door_cube.location[0] = 1.05  # Slightly offset the door

door_cube.location[2] = 1  # Center vertically


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
