# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_python_code_to_make_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender python code to make blender.

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with clear names
base_mat = bpy.data.materials.new(name="Base Material")
base_mat.diffuse_color = (0.35, 0.35, 0.35, 1)  # Darker gray
jug_mat = bpy.data.materials.new(name="Jug Material")
jug_mat.diffuse_color = (0.75, 0.75, 0.75, 0.55)  # Light gray with transparency
button_mat = bpy.data.materials.new(name="Button Material")
button_mat.diffuse_color = (0.05, 0.05, 0.05, 1)  # Dark button color

# Create the primary base shape
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_shape = bpy.context.object
base_shape.name = "Base"
base_shape.data.materials.append(base_mat)

# Create the jug shape
bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=1.5, location=(0, 0, 1.25))
jug_shape = bpy.context.object
jug_shape.name = "Jug"
jug_shape.data.materials.append(jug_mat)

# Create the control panel
bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0.9, 0.4))
control_panel_shape = bpy.context.object
control_panel_shape.name = "Control Panel"
control_panel_shape.scale[0] = 1.5
control_panel_shape.scale[2] = 0.2
control_panel_shape.data.materials.append(base_mat)

# Create buttons in specified locations
button_positions = [(-0.3, 0.9, 0.45), (0, 0.9, 0.45), (0.3, 0.9, 0.45)]
for idx, pos in enumerate(button_positions):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=pos)
    button_shape = bpy.context.object
    button_shape.name = f"Button {idx + 1}"
    button_shape.data.materials.append(button_mat)


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
