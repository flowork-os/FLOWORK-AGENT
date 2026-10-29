# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_that_creates_a_model_of_cutlery_tray" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script that creates a model of cutlery tray.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define the material for the tray
tray_material = bpy.data.materials.new(name='TrayColor')
tray_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray color

# Function to set up the tray and dividers
def setup_tray():
    # Create the main tray base
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base_tray = bpy.context.object
    base_tray.name = 'TrayBase'
    base_tray.scale[2] = 0.1
    base_tray.data.materials.append(tray_material)

    # Create dividers
    create_dividers()

def create_dividers():
    # Horizontal dividers
    for i in range(1, 3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, i * 0.5 - 0.5, 0.1))
        horizontal_divider = bpy.context.object
        horizontal_divider.name = f'HorizontalDivider_{i}'
        horizontal_divider.scale = (1, 0.05, 0.2)
        horizontal_divider.data.materials.append(tray_material)

    # Vertical dividers
    for i in range(1, 4):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 0.5 - 1, 0, 0.1))
        vertical_divider = bpy.context.object
        vertical_divider.name = f'VerticalDivider_{i}'
        vertical_divider.scale = (0.05, 1, 0.2)
        vertical_divider.data.materials.append(tray_material)

# Execute the tray setup function
setup_tray()


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
