# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_blender_code_to_make_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a blender code to make a model of blender

import bpy

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for different parts of the model
mat_base = bpy.data.materials.new(name='Material Base')
mat_base.diffuse_color = (0.2, 0.2, 0.2, 1)
mat_pitcher = bpy.data.materials.new(name='Material Pitcher')
mat_pitcher.diffuse_color = (0.8, 0.8, 0.8, 0.5)
mat_lid = bpy.data.materials.new(name='Material Lid')
mat_lid.diffuse_color = (0.1, 0.1, 0.1, 1)

# Create the main components of the model
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_object = bpy.context.object
base_object.name = 'Base'
base_object.data.materials.append(mat_base)

bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=2, location=(0, 0, 1.5))
pitcher_object = bpy.context.object
pitcher_object.name = 'Pitcher'
pitcher_object.data.materials.append(mat_pitcher)

bpy.ops.mesh.primitive_cylinder_add(radius=0.95, depth=0.1, location=(0, 0, 2.55))
lid_object = bpy.context.object
lid_object.name = 'Lid'
lid_object.data.materials.append(mat_lid)

bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.1, location=(0, 0, 2.65))
center_cap_object = bpy.context.object
center_cap_object.name = 'Center Cap'
center_cap_object.data.materials.append(mat_lid)

# Adding measurement indicators as small cubes
for i in range(1, 5):
    bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0.95, 0, 0.5 * i + 0.5))
    cube_marking = bpy.context.object
    cube_marking.name = f'Marking {i}'
    cube_marking.data.materials.append(mat_lid)


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
