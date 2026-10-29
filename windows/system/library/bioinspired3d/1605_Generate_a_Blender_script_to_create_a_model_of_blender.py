# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_script_to_create_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender script to create a model of blender

import bpy
import math

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

clear_scene()

mat_base = bpy.data.materials.new(name='MaterialBase')
mat_base.diffuse_color = (0.1, 0.1, 0.1, 1)  # Darker gray

mat_container = bpy.data.materials.new(name='MaterialContainer')
mat_container.diffuse_color = (0.85, 0.85, 0.85, 0.5)  # Light gray, semi-transparent

mat_blades = bpy.data.materials.new(name='MaterialBlades')
mat_blades.diffuse_color = (0.75, 0.75, 0.75, 1)  # Slightly lighter gray

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_object = bpy.context.object
base_object.name = 'BaseObject'
base_object.data.materials.append(mat_base)

bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2, location=(0, 0, 1.5))
container_object = bpy.context.object
container_object.name = 'ContainerObject'
container_object.data.materials.append(mat_container)

bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.1, location=(0, 0, 2.55))
lid_object = bpy.context.object
lid_object.name = 'LidObject'
lid_object.data.materials.append(mat_base)

bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.2, location=(0, 0, 2.65))
cap_object = bpy.context.object
cap_object.name = 'CapObject'
cap_object.data.materials.append(mat_base)

bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 1))
blades_object = bpy.context.object
blades_object.name = 'BladesObject'
blades_object.data.materials.append(mat_blades)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.transform.rotate(value=math.pi / 4, orient_axis='Z')
bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 1, 0.25))
control_panel_object = bpy.context.object
control_panel_object.name = 'ControlPanelObject'
control_panel_object.data.materials.append(mat_base)

for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.15 + i * 0.15, 1.1, 0.25))
    button_object = bpy.context.object
    button_object.name = f'Button_{i + 1}'
    button_object.data.materials.append(mat_base)


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
