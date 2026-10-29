# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_to_make_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code to make blender.

import bpy

# Clear all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with distinct colors
base_material = bpy.data.materials.new(name='MainBaseMaterial')
base_material.diffuse_color = (0.2, 0.2, 0.2, 1.0)
button_material = bpy.data.materials.new(name='PrimaryButtonMaterial')
button_material.diffuse_color = (0.8, 0.1, 0.1, 1.0)
container_material = bpy.data.materials.new(name='MainContainerMaterial')
container_material.diffuse_color = (0.8, 0.8, 0.8, 0.3)
lid_material = bpy.data.materials.new(name='MainLidMaterial')
lid_material.diffuse_color = (0.2, 0.2, 0.2, 1.0)

# Function to add a cylinder with specified parameters
def add_cylinder(radius, depth, location, name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)

# Create base, container, and lid
add_cylinder(1, 0.5, (0, 0, 0.25), 'Base', base_material)
add_cylinder(0.8, 1.5, (0, 0, 1.25), 'Container', container_material)
add_cylinder(0.85, 0.1, (0, 0, 2.05), 'Lid', lid_material)

# Define button locations
button_coords = [(-0.5, 0.9, 0.25), (0, 0.9, 0.25), (0.5, 0.9, 0.25)]
for idx, coord in enumerate(button_coords):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=coord)
    button_obj = bpy.context.object
    button_obj.name = f'Button_{idx + 1}'
    button_obj.data.materials.append(button_material)


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
