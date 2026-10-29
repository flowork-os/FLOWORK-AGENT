# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_code_in_Blender_that_makes_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate code in Blender that makes a model of blender

import bpy

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
base_mat = bpy.data.materials.new(name="Base Material")
base_mat.diffuse_color = (0.2, 0.2, 0.2, 1)
container_mat = bpy.data.materials.new(name="Container Material")
container_mat.diffuse_color = (0.7, 0.7, 0.7, 0.5)
button_mat = bpy.data.materials.new(name="Button Material")
button_mat.diffuse_color = (1.0, 0.0, 0.0, 1)
lid_mat = bpy.data.materials.new(name="Lid Material")
lid_mat.diffuse_color = (0.2, 0.2, 0.2, 1)

# Create objects with specified parameters
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base = bpy.context.object
base.name = "Base"
base.data.materials.append(base_mat)

bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=1.5, location=(0, 0, 1.25))
container = bpy.context.object
container.name = "Container"
container.data.materials.append(container_mat)

bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.1, location=(0, 0, 2.05))
lid = bpy.context.object
lid.name = "Lid"
lid.data.materials.append(lid_mat)

# Adding control panel
bpy.ops.mesh.primitive_cube_add(size=0.4, location=(0, 1, 0.25))
control_panel = bpy.context.object
control_panel.name = "Control Panel"
control_panel.data.materials.append(base_mat)

# Create buttons in a row
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.1 + i * 0.15, 1.1, 0.25))
    button = bpy.context.object
    button.name = f"Button {i + 1}"
    button.data.materials.append(button_mat)


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
