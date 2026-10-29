# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script_make_grooming_brush" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script make grooming brush.

import bpy

# Clear the current scene to start fresh
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the brush components
handle_mat = bpy.data.materials.new(name='HandleMaterial')
handle_mat.diffuse_color = (0.1, 0.1, 0.1, 1)  # Darker gray for the handle
bristle_mat = bpy.data.materials.new(name='BristleMaterial')
bristle_mat.diffuse_color = (0.9, 0.9, 0.9, 1)  # Lighter gray for the bristles

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the handle
handle_obj = create_cylinder(0.1, 1.0, (0, 0, 0.5), 'BrushHandle', handle_mat)

# Create the brush head as a cube
bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 1.3))
head_obj = bpy.context.object
head_obj.name = 'BrushHead'
head_obj.data.materials.append(handle_mat)

# Generate bristles using a nested loop
for row in range(5):
    for col in range(5):
        bristle_location = (row * 0.1 - 0.2, col * 0.1 - 0.2, 1.5)
        create_cylinder(0.02, 0.3, bristle_location, f'Bristle_{row}_{col}', bristle_mat)


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
