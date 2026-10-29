# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_create_a_model_of_screwdriver" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script create a model of screwdriver

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the components
handle_material = bpy.data.materials.new(name='HandleMaterial')
handle_material.diffuse_color = (0.9, 0.1, 0.1, 1)  # Bright red for the handle
shaft_material = bpy.data.materials.new(name='ShaftMaterial')
shaft_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Lighter gray for the shaft

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create the handle using the helper function
handle = create_cylinder(0.2, 1.5, (0, 0, 0.75), 'Handle', handle_material)

# Create the shaft using the same helper function
shaft = create_cylinder(0.05, 2, (0, 0, 2.25), 'Shaft', shaft_material)

# Create the tip as a flattened cube
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, 3.25))
tip = bpy.context.object

tip.scale[2] = 0.04  # Adjust thickness to make it flat
tip.name = 'Tip'
tip.data.materials.append(shaft_material)


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
