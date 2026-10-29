# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_blender_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of blender using blender script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_dark_gray = bpy.data.materials.new(name='DarkGrayMaterial')
material_dark_gray.diffuse_color = (0.2, 0.2, 0.2, 1)
material_red = bpy.data.materials.new(name='RedMaterial')
material_red.diffuse_color = (0.8, 0.1, 0.1, 1)
material_transparent_gray = bpy.data.materials.new(name='TransparentGrayMaterial')
material_transparent_gray.diffuse_color = (0.8, 0.8, 0.8, 0.3)
material_lid_dark_gray = bpy.data.materials.new(name='LidDarkGrayMaterial')
material_lid_dark_gray.diffuse_color = (0.2, 0.2, 0.2, 1)

def create_cylinder_mesh(radius, height, position, obj_name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    cylinder = bpy.context.object
    cylinder.name = obj_name
    cylinder.data.materials.append(mat)
    return cylinder

base_mesh = create_cylinder_mesh(1, 0.5, (0, 0, 0.25), 'Base', material_dark_gray)
container_mesh = create_cylinder_mesh(0.8, 1.5, (0, 0, 1.25), 'Container', material_transparent_gray)
lid_mesh = create_cylinder_mesh(0.85, 0.1, (0, 0, 2.05), 'Lid', material_lid_dark_gray)

button_locations = [(-0.5, 0.9, 0.25), (0, 0.9, 0.25), (0.5, 0.9, 0.25)]
for index, location in enumerate(button_locations):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=location)
    button_mesh = bpy.context.object
    button_mesh.name = f'Button_{index + 1}'
    button_mesh.data.materials.append(material_red)


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
