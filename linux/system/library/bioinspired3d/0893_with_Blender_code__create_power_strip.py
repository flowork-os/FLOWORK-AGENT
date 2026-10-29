# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_code__create_power_strip" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender code, create power strip

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with distinct names
main_material = bpy.data.materials.new(name="Body")
main_material.diffuse_color = (0.5, 0.5, 0.5, 1)
dark_material = bpy.data.materials.new(name="Dark Outlet")
dark_material.diffuse_color = (0.1, 0.1, 0.1, 1)
switch_material = bpy.data.materials.new(name="Red Switch")
switch_material.diffuse_color = (0.8, 0.1, 0.1, 1)

# Create the main body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
body = bpy.context.object
body.name = "Main Body"
body.scale = (2, 0.5, 0.1)
body.data.materials.append(main_material)

# Create outlets using a different method
outlets = []
for i in range(5):
    outlet_location = (-1.5 + i * 0.5, 0.25, 0.05)
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=outlet_location)
    outlet = bpy.context.object
    outlet.name = f"Outlet {i + 1}"
    outlet.data.materials.append(dark_material)
    outlets.append(outlet)

# Create the switch
bpy.ops.mesh.primitive_cube_add(size=0.3, location=(1.5, 0.25, 0.05))
switch = bpy.context.object
switch.name = "Switch"
switch.data.materials.append(switch_material)


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
