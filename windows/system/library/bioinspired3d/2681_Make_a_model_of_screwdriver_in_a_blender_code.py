# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_screwdriver_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of screwdriver in a blender code

import bpy

# Clear existing meshes from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
metal_material = bpy.data.materials.new(name="Metal Material")
metal_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray
handle_material = bpy.data.materials.new(name="Handle Material")
handle_material.diffuse_color = (1, 0, 0, 1)  # Bright red

# Function to add a cylinder

def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the handle, shaft, and head
handle = add_cylinder(0.1, 1.0, (0, 0, 0.5), "Handle", handle_material)
shaft = add_cylinder(0.02, 1.5, (0, 0, 1.75), "Shaft", metal_material)

# Create the flat head using a cube
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, 2.55))
head = bpy.context.object
head.scale[1] = 0.02  # Flatten the cube
head.name = "Flat Head"
head.data.materials.append(metal_material)


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
