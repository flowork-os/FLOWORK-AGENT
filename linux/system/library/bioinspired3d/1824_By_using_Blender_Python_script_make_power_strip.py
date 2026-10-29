# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_make_power_strip" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script make power strip.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the components
body_mat = bpy.data.materials.new(name="Gray Body")
body_mat.diffuse_color = (0.5, 0.5, 0.5, 1)
outlet_mat = bpy.data.materials.new(name="Dark Gray Outlet")
outlet_mat.diffuse_color = (0.1, 0.1, 0.1, 1)
switch_mat = bpy.data.materials.new(name="Red Switch")
switch_mat.diffuse_color = (0.8, 0.1, 0.1, 1)

# Create the main body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
main_body = bpy.context.object
main_body.name = "Body"
main_body.scale = (2, 0.5, 0.1)
main_body.data.materials.append(body_mat)

# Function to create outlets
def create_outlet(index):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(-1.5 + index * 0.5, 0.25, 0.05))
    outlet = bpy.context.object
    outlet.name = f"Outlet {index + 1}"
    outlet.data.materials.append(outlet_mat)

# Create outlets
for i in range(5):
    create_outlet(i)

# Create the switch
bpy.ops.mesh.primitive_cube_add(size=0.3, location=(1.5, 0.25, 0.05))
switch_obj = bpy.context.object
switch_obj.name = "Switch"
switch_obj.data.materials.append(switch_mat)


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
