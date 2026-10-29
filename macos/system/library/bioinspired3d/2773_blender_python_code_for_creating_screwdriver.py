# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_creating_screwdriver" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for creating screwdriver.

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts
handle_material = bpy.data.materials.new(name='HandleMaterial')
handle_material.diffuse_color = (0.9, 0.1, 0.1, 1)  # Bright red for the handle
shaft_material = bpy.data.materials.new(name='ShaftMaterial')
shaft_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray for the shaft

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Function to create a cube
def create_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the handle and shaft
handle = create_cylinder(0.1, 1.0, (0, 0, 0.5), 'Handle', handle_material)
shaft = create_cylinder(0.02, 2.0, (0, 0, -1.0), 'Shaft', shaft_material)

# Create the flat tip
flat_tip = create_cube(0.1, (0, 0, -2.05), 'FlatTip', shaft_material)
flat_tip.scale[1] = 0.02  # Flatten the tip


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
