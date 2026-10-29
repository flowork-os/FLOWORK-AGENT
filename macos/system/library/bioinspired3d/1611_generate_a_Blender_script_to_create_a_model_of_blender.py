# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_to_create_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script to create a model of blender

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

base_mat = bpy.data.materials.new(name='BaseMaterial')
base_mat.diffuse_color = (0.2, 0.2, 0.2, 1.0)
jar_mat = bpy.data.materials.new(name='JarMaterial')
jar_mat.diffuse_color = (0.8, 0.8, 0.8, 0.3)
lid_mat = bpy.data.materials.new(name='LidMaterial')
lid_mat.diffuse_color = (0.1, 0.1, 0.1, 1.0)
panel_mat = bpy.data.materials.new(name='PanelMaterial')
panel_mat.diffuse_color = (0.5, 0.5, 0.5, 1.0)

def add_mesh_object(primitive, params, name, material):
    getattr(bpy.ops.mesh, primitive)(**params)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

add_mesh_object('primitive_cylinder_add', {'radius': 1, 'depth': 1, 'location': (0, 0, 0.5)}, 'Base', base_mat)
add_mesh_object('primitive_cube_add', {'size': 0.5, 'location': (0, 0.75, 0.25)}, 'Control Panel', panel_mat)
add_mesh_object('primitive_cylinder_add', {'radius': 0.8, 'depth': 2, 'location': (0, 0, 2)}, 'Jar', jar_mat)
add_mesh_object('primitive_cylinder_add', {'radius': 0.85, 'depth': 0.1, 'location': (0, 0, 3.05)}, 'Lid', lid_mat)

for mark in range(1, 5):
    add_mesh_object('primitive_cube_add', {'size': 0.05, 'location': (0.85, 0, 1 + mark * 0.4)}, f'Marking_{mark}', base_mat)
    bpy.context.object.scale = (0.02, 0.02, 0.2)


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
