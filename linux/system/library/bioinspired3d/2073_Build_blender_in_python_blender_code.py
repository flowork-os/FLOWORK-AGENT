# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_blender_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build blender in python blender code

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with specified colors
base_material = bpy.data.materials.new(name='Base Material')
base_material.diffuse_color = (0.5, 0.5, 0.5, 1)
switch_material = bpy.data.materials.new(name='Switch Material')
switch_material.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Construct the blender components
base = create_cylinder(1, 0.5, (0, 0, 0.25), 'Blender Base', base_material)
jar = create_cylinder(0.8, 1.5, (0, 0, 1.25), 'Blender Jar', base_material)
lid = create_cylinder(0.85, 0.1, (0, 0, 2), 'Blender Lid', base_material)

# Create the On/Off switch
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.9, 0, 0.25))
switch = bpy.context.object
switch.name = 'On/Off Switch'
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
