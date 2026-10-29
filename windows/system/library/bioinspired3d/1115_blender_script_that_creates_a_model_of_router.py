# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_creates_a_model_of_router" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that creates a model of router.

import bpy

# Step 1: Clear the scene of existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model components
main_material = bpy.data.materials.new(name='Main Material')
main_material.diffuse_color = (0.1, 0.1, 0.1, 1)
antenna_material = bpy.data.materials.new(name='Antenna Material')
antenna_material.diffuse_color = (0.1, 0.1, 0.1, 1)
light_material = bpy.data.materials.new(name='Light Material')
light_material.diffuse_color = (0, 1, 0, 1)

# Create the base shape
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
base = bpy.context.object
base.scale.x = 2
base.scale.y = 1
base.scale.z = 0.2
base.name = 'Base Model'
base.data.materials.append(main_material)

# Create antennae using a loop
antenna_positions = [(-1.5, 0, 1.2), (0, 0, 1.2), (1.5, 0, 1.2)]
for pos in antenna_positions:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=pos)
    antenna = bpy.context.object
    antenna.name = 'Antenna'
    antenna.data.materials.append(antenna_material)

# Create lights using a loop
light_positions = [(-0.5, 1.1, 0.6), (0, 1.1, 0.6), (0.5, 1.1, 0.6)]
for pos in light_positions:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=pos)
    light = bpy.context.object
    light.name = 'Light'
    light.data.materials.append(light_material)


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
