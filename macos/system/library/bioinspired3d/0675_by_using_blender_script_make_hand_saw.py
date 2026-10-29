# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_script_make_hand_saw" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender script make hand saw

import bpy
import math

# Clear the scene by removing all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create blade and handle materials
blade_mat = bpy.data.materials.new(name="BladeMaterial")
blade_mat.diffuse_color = (0.5, 0.5, 0.5, 1)
handle_mat = bpy.data.materials.new(name="HandleMaterial")
handle_mat.diffuse_color = (0.8, 0.4, 0.1, 1)

# Add blade geometry
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
blade_cube = bpy.context.object
blade_cube.name = "Blade"
blade_cube.scale[0] = 3
blade_cube.scale[1] = 0.05
blade_cube.scale[2] = 0.5
blade_cube.data.materials.append(blade_mat)

# Create teeth using a loop
for index in range(12):
    tooth_location = (-2.7 + index * 0.5, 0, -0.5)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.1, depth=0.2, location=tooth_location)
    tooth_cone = bpy.context.object
    tooth_cone.name = f"Tooth {index + 1}"
    tooth_cone.rotation_euler[1] = math.pi / 2
    tooth_cone.data.materials.append(blade_mat)

# Construct the handle
bpy.ops.mesh.primitive_cube_add(size=1, location=(3.5, 0, 0))
handle_cube = bpy.context.object
handle_cube.name = "Handle"
handle_cube.scale[0] = 0.5
handle_cube.scale[1] = 0.3
handle_cube.scale[2] = 1
handle_cube.data.materials.append(handle_mat)

# Add grips on either side of the handle
for offset in [0.2, -0.2]:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1, location=(3.5, offset, 0.5), rotation=(0, math.pi / 2, 0))
    grip_cylinder = bpy.context.object
    grip_cylinder.name = "Grip"
    grip_cylinder.data.materials.append(handle_mat)


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
