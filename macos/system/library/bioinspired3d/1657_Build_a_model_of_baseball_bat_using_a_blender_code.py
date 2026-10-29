# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_baseball_bat_using_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of baseball bat using a blender code

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the bat
bat_color = bpy.data.materials.new(name='BatColor')
bat_color.diffuse_color = (0.5, 0.25, 0.1, 1)

# Function to add a tapered bat
def add_tapered_bat():
    # Create main bat body
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.2, location=(0, 0, 0.6))
    bat_body = bpy.context.object
    bat_body.name = 'Bat Body'
    bat_body.data.materials.append(bat_color)

    # Modify the vertices to taper the bat
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bat_body.data.vertices[0].select = True
    bat_body.data.vertices[1].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.resize(value=(0.5, 0.5, 1))
    bpy.ops.object.mode_set(mode='OBJECT')

    # Create the handle grip
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.3, location=(0, 0, -0.15))
    handle = bpy.context.object
    handle.name = 'Handle Grip'
    handle.data.materials.append(bat_color)

    # Create the knob at the end of the handle
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0, 0, -0.3))
    knob = bpy.context.object
    knob.name = 'Handle Knob'
    knob.data.materials.append(bat_color)

# Call the function to add the bat
add_tapered_bat()


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
