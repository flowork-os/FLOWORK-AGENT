# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script__construct_a_model_of_coffee_grinder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script, construct a model of coffee grinder

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model
metal_mat = bpy.data.materials.new(name='Metallic Finish')
metal_mat.diffuse_color = (0.5, 0.5, 0.5, 1)
wood_mat = bpy.data.materials.new(name='Wood Texture')
wood_mat.diffuse_color = (0.54, 0.27, 0.07, 1)

# Create objects
bpy.ops.mesh.primitive_cone_add(radius1=0.3, radius2=0.1, depth=0.4, location=(0, 0, 1.2))
hopper = bpy.context.object
hopper.name = 'Hopper'
hopper.data.materials.append(metal_mat)

bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.5, location=(0, 0, 0.75))
grinding_part = bpy.context.object
grinding_part.name = 'Grinding Part'
grinding_part.data.materials.append(metal_mat)

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0.25))
container_box = bpy.context.object
container_box.name = 'Container Box'
container_box.data.materials.append(wood_mat)

bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.8, location=(0.35, 0, 0.75), rotation=(0, math.pi/2, 0))
handle_part = bpy.context.object
handle_part.name = 'Handle Part'
handle_part.data.materials.append(metal_mat)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0.75, 0, 0.75))
handle_knob_part = bpy.context.object
handle_knob_part.name = 'Handle Knob'
handle_knob_part.data.materials.append(wood_mat)


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
