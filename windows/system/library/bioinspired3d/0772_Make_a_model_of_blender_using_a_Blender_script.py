# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_blender_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of blender using a Blender script

import bpy

# Remove all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with colors
base_color_material = bpy.data.materials.new(name='Gray Material')
base_color_material.diffuse_color = (0.2, 0.2, 0.2, 1)
button_color_material = bpy.data.materials.new(name='Red Material')
button_color_material.diffuse_color = (0.8, 0.1, 0.1, 1)

# Create the base cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base = bpy.context.object
base.name = 'Base'
base.data.materials.append(base_color_material)

# Create the jar as a cone
bpy.ops.mesh.primitive_cone_add(radius1=0.8, radius2=0, depth=2, location=(0, 0, 1.25))
jar = bpy.context.object
jar.name = 'Jar'
jar.data.materials.append(base_color_material)

# Create the button cube
bpy.ops.mesh.primitive_cube_add(size=0.3, location=(0, 0.9, 0.25))
button = bpy.context.object
button.name = 'Button'
button.data.materials.append(button_color_material)


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
