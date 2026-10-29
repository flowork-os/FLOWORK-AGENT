# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_make_a_model_of_power_strip" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to make a model of power strip.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the components
mat_strip = bpy.data.materials.new(name="Strip")
mat_strip.diffuse_color = (0.8, 0.8, 0.8, 1)
mat_outlet = bpy.data.materials.new(name="Outlet")
mat_outlet.diffuse_color = (0, 0, 0, 1)
mat_switch = bpy.data.materials.new(name="Switch")
mat_switch.diffuse_color = (1, 0, 0, 1)
mat_plug = bpy.data.materials.new(name="Plug")
mat_plug.diffuse_color = (0, 0, 0, 1)

# Function to set up the power strip
def setup_power_strip():
    # Create the main body of the power strip
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    base = bpy.context.object
    base.name = "Power Strip Base"
    base.scale = (3, 0.5, 0.1)
    base.data.materials.append(mat_strip)

    # Create outlets
    for i in range(6):
        bpy.ops.mesh.primitive_cube_add(size=0.2, location=(-2.5 + i, 0, 0.1))
        outlet = bpy.context.object
        outlet.name = f"Outlet {i + 1}"
        outlet.data.materials.append(mat_outlet)

    # Create a switch
    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(-3.5, 0, 0.1))
    switch = bpy.context.object
    switch.name = "Switch"
    switch.data.materials.append(mat_switch)

    # Create a plug
    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(3.5, 0, 0.1))
    plug = bpy.context.object
    plug.name = "Plug"
    plug.data.materials.append(mat_plug)

setup_power_strip()


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
