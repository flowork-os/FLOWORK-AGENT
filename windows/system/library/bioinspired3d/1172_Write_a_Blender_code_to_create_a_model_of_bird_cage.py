# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_to_create_a_model_of_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code to create a model of bird cage

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
metal_material = bpy.data.materials.new(name='Metallic Finish')
metal_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray metal
wood_material = bpy.data.materials.new(name='Wood Texture')
wood_material.diffuse_color = (0.54, 0.25, 0.05, 1)  # Darker brown wood

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Base structure
base_cylinder = create_cylinder(1, 0.1, (0, 0, 0), 'Base Cylinder', metal_material)

# Vertical bars
bar_count = 16
for index in range(bar_count):
    theta = index * (2 * math.pi / bar_count)
    x_pos = math.cos(theta)
    y_pos = math.sin(theta)
    create_cylinder(0.05, 2, (x_pos, y_pos, 1), f'Bar {index + 1}', metal_material)

# Dome shape
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
dome_shape = bpy.context.object

dome_shape.name = 'Dome Top'
dome_shape.scale[2] = 0.5

dome_shape.data.materials.append(metal_material)

# Door creation
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 1))
door_cube = bpy.context.object

door_cube.name = 'Entrance Door'
door_cube.data.materials.append(metal_material)

# Perch creation
create_cylinder(0.05, 1.8, (0, 0, 0.5), 'Bird Perch', wood_material)


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
