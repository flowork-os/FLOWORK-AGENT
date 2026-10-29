# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_bird_cage_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of bird cage using Blender code

import bpy
import math

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
metallic_color = bpy.data.materials.new(name='Metallic Color')
metallic_color.diffuse_color = (0.4, 0.4, 0.4, 1)  # Darker metallic shade
wooden_color = bpy.data.materials.new(name='Wooden Color')
wooden_color.diffuse_color = (0.5, 0.2, 0.1, 1)  # Rich brown wood

# Create a base cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=0.1, location=(0, 0, 0))
base_object = bpy.context.object
base_object.name = 'Base Cylinder'
base_object.data.materials.append(metallic_color)

# Generate vertical bars
bar_count = 16
for i in range(bar_count):
    angle = (i / bar_count) * (2 * math.pi)
    x_coord = math.cos(angle)
    y_coord = math.sin(angle)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(x_coord, y_coord, 1))
    vertical_bar = bpy.context.object
    vertical_bar.name = f'Vertical Bar {i + 1}'
    vertical_bar.data.materials.append(metallic_color)

# Create the dome on top
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
dome_object = bpy.context.object

dome_object.name = 'Dome'
dome_object.scale[2] = 0.5

dome_object.data.materials.append(metallic_color)

# Create the door
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 1))
door_object = bpy.context.object

door_object.name = 'Access Door'
door_object.data.materials.append(metallic_color)

# Create a perch
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.8, location=(0, 0, 0.5), rotation=(0, math.pi/2, 0))
perch_object = bpy.context.object
perch_object.name = 'Bird Perch'
perch_object.data.materials.append(wooden_color)


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
