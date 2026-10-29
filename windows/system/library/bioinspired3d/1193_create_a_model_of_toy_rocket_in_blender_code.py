# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_toy_rocket_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of toy rocket in blender code

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define material properties for the model
red_material = bpy.data.materials.new(name='Red Material')
red_material.diffuse_color = (0.7, 0.1, 0.1, 1)
blue_material = bpy.data.materials.new(name='Blue Material')
blue_material.diffuse_color = (0.1, 0.1, 0.7, 1)
gray_material = bpy.data.materials.new(name='Gray Material')
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Create the main body using primitives
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=3, location=(0, 0, 1.5))
main_body = bpy.context.object
main_body.name = 'Main Body'
main_body.data.materials.append(red_material)

# Add the nose cone
bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=1, location=(0, 0, 3.5))
nose = bpy.context.object
nose.name = 'Nose'
nose.data.materials.append(red_material)

# Function to create fins at specified angles

def add_fin(index):
    angle = index * (2 * math.pi / 3)
    x_pos = 0.5 * math.cos(angle)
    y_pos = 0.5 * math.sin(angle)
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x_pos, y_pos, 0.25))
    fin = bpy.context.object
    fin.name = f'Fin {index + 1}'
    fin.scale[1] = 0.1
    fin.scale[2] = 2
    fin.rotation_euler[2] = angle
    fin.data.materials.append(blue_material)

# Create three fins
for i in range(3):
    add_fin(i)

# Create the window
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0.5, 0, 2.5))
window = bpy.context.object
window.name = 'View Window'
window.data.materials.append(gray_material)


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
