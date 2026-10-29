# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_building_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for building blender

import bpy

# Deselect all objects and remove mesh types
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define new materials for the model
container_color = bpy.data.materials.new(name='GreyContainer')
container_color.diffuse_color = (0.8, 0.8, 0.8, 1)
lid_color = bpy.data.materials.new(name='DarkLid')
lid_color.diffuse_color = (0.2, 0.2, 0.2, 1)
base_color = bpy.data.materials.new(name='AlmostBlackBase')
base_color.diffuse_color = (0.1, 0.1, 0.1, 1)
button_color = bpy.data.materials.new(name='MediumGreyButton')
button_color.diffuse_color = (0.5, 0.5, 0.5, 1)

# Create the container
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=3, location=(0, 0, 1.5))
container = bpy.context.object
container.name = 'Container'
container.data.materials.append(container_color)

# Create the lid
bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.2, location=(0, 0, 3.1))
lid = bpy.context.object
lid.name = 'Lid'
lid.data.materials.append(lid_color)

# Add an opening to the lid
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.2, location=(0, 0, 3.2))
opening = bpy.context.object
opening.name = 'LidOpening'
opening.data.materials.append(container_color)

# Create the base
bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=0.5, location=(0, 0, 0.25))
base = bpy.context.object
base.name = 'Base'
base.data.materials.append(base_color)

# Create the control panel
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 1.1, 0.5))
control_panel = bpy.context.object
control_panel.name = 'ControlPanel'
control_panel.data.materials.append(base_color)

# Generate buttons on the control panel
for index in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.15 + index * 0.15, 1.15, 0.5))
    button = bpy.context.object
    button.name = f'Button_{index + 1}'
    button.data.materials.append(button_color)


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
