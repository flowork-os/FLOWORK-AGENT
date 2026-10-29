# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_Blender_script_construct_screwdriver" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a Blender script construct screwdriver

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model
red_material = bpy.data.materials.new(name='Red Handle')
red_material.diffuse_color = (0.9, 0.1, 0.1, 1)  # Bright red
gray_material = bpy.data.materials.new(name='Gray Shaft')
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Darker gray

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the handle
handle = create_cylinder(0.1, 1.0, (0, 0, 0.5), 'Handle', red_material)
# Create the shaft
shaft = create_cylinder(0.02, 1.5, (0, 0, -0.75), 'Shaft', gray_material)

# Step 4: Create the flat tip
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, -1.55))
tip = bpy.context.object
tip.scale[1] = 0.02  # Flatten the cube
tip.name = 'Tip'
tip.data.materials.append(gray_material)


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
