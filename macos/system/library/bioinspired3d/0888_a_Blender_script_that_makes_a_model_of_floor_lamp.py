# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_makes_a_model_of_floor_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that makes a model of floor lamp.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
metal_material = bpy.data.materials.new(name="Metal")
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)
shade_material = bpy.data.materials.new(name="Shade")
shade_material.diffuse_color = (1, 1, 1, 1)

# Function to add a cylinder
def add_cylinder(radius, height, position, obj_name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.name = obj_name
    obj.data.materials.append(mat)

# Add the lamp components
add_cylinder(0.05, 2, (0, 0, 1), "Stand", metal_material)
add_cylinder(0.5, 0.1, (0, 0, 0.05), "Base", metal_material)
add_cylinder(0.6, 0.8, (0, 0, 2.4), "Shade", shade_material)
add_cylinder(0.4, 0.2, (0, 0, 2.7), "Drum", metal_material)

# Create the foot switch as a cube
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0.5, 0, 0.05))
foot_switch = bpy.context.object
foot_switch.name = "Foot Switch"
foot_switch.data.materials.append(metal_material)


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
