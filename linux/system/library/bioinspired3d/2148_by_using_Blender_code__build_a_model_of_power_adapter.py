# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_code__build_a_model_of_power_adapter" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender code, build a model of power adapter

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the adapter
material_black = bpy.data.materials.new(name="BlackMaterial")
material_black.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to create a cube
def create_cube(size, location, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(material_black)
    return cube

# Create the adapter body
create_cube(2, (0, 0, 0), "Adapter Body")

# Create the plug
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1, location=(0, 1.1, 0))
plug = bpy.context.object
plug.name = "Plug"
plug.data.materials.append(material_black)

# Create USB ports using a loop
for i in range(4):
    position_x = -0.6 + i * 0.4
    create_cube(0.3, (position_x, -1.1, 0), f"USB Port {i + 1}")


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
