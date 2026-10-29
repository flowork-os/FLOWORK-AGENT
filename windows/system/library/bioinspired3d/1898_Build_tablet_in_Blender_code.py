# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_tablet_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build tablet in Blender code

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the tablet
material_body = bpy.data.materials.new(name='Body Material')
material_body.diffuse_color = (0.1, 0.1, 0.1, 1)
material_screen = bpy.data.materials.new(name='Screen Material')
material_screen.diffuse_color = (0, 0, 0, 1)

# Function to create a tablet
def create_tablet():
    # Create the main body
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    tablet = bpy.context.object
    tablet.name = 'Main Tablet'
    tablet.scale = (1, 1.5, 0.05)
    tablet.data.materials.append(material_body)

    # Create the screen on top
    bpy.ops.mesh.primitive_plane_add(size=1.9, location=(0, 0, 0.051))
    display = bpy.context.object
    display.name = 'Display Screen'
    display.scale = (0.95, 1.45, 1)
    display.data.materials.append(material_screen)

create_tablet()


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
