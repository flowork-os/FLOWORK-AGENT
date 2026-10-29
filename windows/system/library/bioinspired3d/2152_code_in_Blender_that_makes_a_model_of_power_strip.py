# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_makes_a_model_of_power_strip" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that makes a model of power strip

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for different components
base_material = bpy.data.materials.new(name="BaseMaterial")
base_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray
outlet_material = bpy.data.materials.new(name="OutletMaterial")
outlet_material.diffuse_color = (0, 0, 0, 1)  # Black
switch_material = bpy.data.materials.new(name="SwitchMaterial")
switch_material.diffuse_color = (1, 0, 0, 1)  # Red
plug_material = bpy.data.materials.new(name="PlugMaterial")
plug_material.diffuse_color = (0, 0, 0, 1)  # Black

# Function to create a cube with specific properties
def create_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Create the main power strip base
base = create_cube(2, (0, 0, 0), "Power Strip Base", base_material)
base.scale[0] = 3  # Length
base.scale[1] = 0.5  # Width
base.scale[2] = 0.1  # Height

# Generate outlets
for index in range(6):
    create_cube(0.2, (-2.5 + index, 0, 0.1), f"Outlet {index + 1}", outlet_material)

# Add a switch
create_cube(0.3, (-3.5, 0, 0.1), "Switch", switch_material)

# Add a plug
create_cube(0.3, (3.5, 0, 0.1), "Plug", plug_material)


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
