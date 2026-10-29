# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_Python_script__build_toy_rocket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender Python script, build toy rocket

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts
primary_material = bpy.data.materials.new(name='Primary Material')
primary_material.diffuse_color = (0.9, 0.2, 0.2, 1)  # Bright red
secondary_material = bpy.data.materials.new(name='Secondary Material')
secondary_material.diffuse_color = (0.2, 0.2, 0.9, 1)  # Bright blue
tertiary_material = bpy.data.materials.new(name='Tertiary Material')
tertiary_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the main body
body = create_cylinder(0.5, 3, (0, 0, 1.5), 'Rocket Body', primary_material)

# Create the nose cone
nose_cone = bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=1, location=(0, 0, 3.5))

# Create fins using a loop
for index in range(3):
    angle_offset = index * (2 * math.pi / 3)
    fin_x = 0.5 * math.cos(angle_offset)
    fin_y = 0.5 * math.sin(angle_offset)
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(fin_x, fin_y, 0.25))
    fin = bpy.context.object
    fin.name = f'Fin {index + 1}'
    fin.scale[1] = 0.1
    fin.scale[2] = 2
    fin.rotation_euler[2] = angle_offset
    fin.data.materials.append(secondary_material)

# Create a window with a sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0.5, 0, 2.5))
window = bpy.context.object
window.name = 'Rocket Window'
window.data.materials.append(tertiary_material)


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
