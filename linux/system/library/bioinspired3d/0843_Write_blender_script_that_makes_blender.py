# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_that_makes_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script that makes blender

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model
container_material = bpy.data.materials.new(name="Container Material")
container_material.diffuse_color = (0.8, 0.8, 0.8, 1)
base_material = bpy.data.materials.new(name="Base Material")
base_material.diffuse_color = (0.1, 0.1, 0.1, 1)
button_material = bpy.data.materials.new(name="Button Material")
button_material.diffuse_color = (1, 0, 0, 1)
blade_material = bpy.data.materials.new(name="Blade Material")
blade_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function for adding a cylinder

def add_cylinder(rad, depth, loc, obj_name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=rad, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = obj_name
    obj.data.materials.append(mat)

# Create base, container, and lid
add_cylinder(1.2, 0.4, (0, 0, 0.2), "Base", base_material)
add_cylinder(1, 3, (0, 0, 2), "Container", container_material)
add_cylinder(1.05, 0.2, (0, 0, 3.6), "Lid", container_material)

# Create the blade base
bpy.ops.mesh.primitive_cone_add(radius1=0.1, radius2=0, depth=0.2, location=(0, 0, 0.1))
blade_base = bpy.context.object
blade_base.name = "Blade Base"
blade_base.data.materials.append(blade_material)

# Create blades around the base
for idx in range(4):
    rotation_angle = math.pi / 2 * idx
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0.3, 0.2))
    blade = bpy.context.object
    blade.name = f"Blade {idx + 1}"
    blade.rotation_euler = (0, rotation_angle, 0)
    blade.data.materials.append(blade_material)

# Add the control panel
bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 1.2, 0.4))
control_panel = bpy.context.object
control_panel.name = "Control Panel"
control_panel.data.materials.append(base_material)

# Add buttons to the control panel
for idx in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.2 + idx * 0.2, 1.25, 0.5))
    button = bpy.context.object
    button.name = f"Button {idx + 1}"
    button.data.materials.append(button_material)


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
