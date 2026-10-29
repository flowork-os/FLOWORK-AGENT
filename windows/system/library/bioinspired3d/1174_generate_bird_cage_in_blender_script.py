# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_bird_cage_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate bird cage in blender script

import bpy
import math

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
metal_material = bpy.data.materials.new(name='Metal Material')
metal_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Bright gray metal
wood_material = bpy.data.materials.new(name='Wood Material')
wood_material.diffuse_color = (0.4, 0.2, 0.1, 1)  # Light brown wood

# Function for creating bars

def add_bar(radius, height, position, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    bar = bpy.context.object
    bar.name = name
    bar.data.materials.append(material)

# Base creation
add_bar(1, 0.1, (0, 0, 0), 'Base Cylinder', metal_material)

# Vertical bars
for i in range(16):
    angle = (i * 2 * math.pi) / 16
    x_pos = math.cos(angle)
    y_pos = math.sin(angle)
    add_bar(0.05, 2, (x_pos, y_pos, 1), f'Bar {i + 1}', metal_material)

# Dome creation
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
dome = bpy.context.object

dome.name = 'Dome Shape'
dome.scale[2] = 0.5

dome.data.materials.append(metal_material)

# Door creation
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 1))
door = bpy.context.object

door.name = 'Main Door'
door.data.materials.append(metal_material)

# Perch creation
add_bar(0.05, 1.8, (0, 0, 0.5), 'Perch', wood_material)


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
