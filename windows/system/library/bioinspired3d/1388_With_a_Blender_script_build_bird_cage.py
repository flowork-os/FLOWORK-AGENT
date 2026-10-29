# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_script_build_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender script build bird cage

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the model
metal_material = bpy.data.materials.new(name="Metal Material")
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(metal_material)
    return obj

# Create the base cylinder
base_cylinder = create_cylinder(1, 0.1, (0, 0, 0), "Base")

# Generate vertical bars around the base
bar_count = 12
for index in range(bar_count):
    angle_position = (2 * math.pi / bar_count) * index
    x_position = math.cos(angle_position)
    y_position = math.sin(angle_position)
    create_cylinder(0.05, 2, (x_position, y_position, 1), f"Vertical Bar {index + 1}")

# Create the dome shape
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
dome_shape = bpy.context.object

dome_shape.name = "Dome"
dome_shape.scale[2] = 0.5  # Flatten to create dome shape

dome_shape.data.materials.append(metal_material)

# Edit mode to remove the lower half of the dome
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
mesh_data = dome_shape.data
for vertex in mesh_data.vertices:
    if vertex.co.z < 0:
        vertex.select = True
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.delete(type='VERT')
bpy.ops.object.mode_set(mode='OBJECT')


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
