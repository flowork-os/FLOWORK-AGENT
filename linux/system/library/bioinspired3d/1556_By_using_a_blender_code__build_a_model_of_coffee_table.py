# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code__build_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code, build a model of coffee table.

import bpy

# Remove existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material with a wood texture
material_wood = bpy.data.materials.new(name='Wood Texture')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)  # Dark brown shade

# Function to add a cube with specific scaling
def add_scaled_cube(size, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    return cube

# Add the table top
add_scaled_cube(2, (0, 0, 0.5), (2, 1, 0.1)).data.materials.append(material_wood)

# Define leg parameters
height_of_leg = 0.5
radius_of_leg = 0.05
positions_of_legs = [(-1.9, -0.9, height_of_leg / 2), (1.9, -0.9, height_of_leg / 2), (-1.9, 0.9, height_of_leg / 2), (1.9, 0.9, height_of_leg / 2)]

# Create each leg
for idx, pos in enumerate(positions_of_legs):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_leg, depth=height_of_leg, location=pos)
    leg_cylinder = bpy.context.object
    leg_cylinder.name = f'Leg_{idx + 1}'
    leg_cylinder.data.materials.append(material_wood)


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
