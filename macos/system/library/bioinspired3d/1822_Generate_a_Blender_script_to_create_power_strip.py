# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_to_create_power_strip" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script to create power strip.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the components
material_body = bpy.data.materials.new(name="Main Body Material")
material_body.diffuse_color = (0.5, 0.5, 0.5, 1)
material_outlet = bpy.data.materials.new(name="Socket Material")
material_outlet.diffuse_color = (0.1, 0.1, 0.1, 1)
material_switch = bpy.data.materials.new(name="Toggle Material")
material_switch.diffuse_color = (0.8, 0.1, 0.1, 1)

# Function to create a cube with a given size, location, and material
def create_cube(size, location, material, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Create main body of the model
body = create_cube(2, (0, 0, 0), material_body, "Main Body")
body.scale = (2, 0.5, 0.1)

# Create outlets using a loop
for index in range(5):
    create_cube(0.2, (-1.5 + index * 0.5, 0.25, 0.05), material_outlet, f"Socket {index + 1}")

# Create the switch
create_cube(0.3, (1.5, 0.25, 0.05), material_switch, "Toggle")


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
