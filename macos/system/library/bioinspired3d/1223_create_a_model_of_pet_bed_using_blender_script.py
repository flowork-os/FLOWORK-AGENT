# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_pet_bed_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of pet bed using blender script

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the bed and cushion
bed_material = bpy.data.materials.new(name='Bed Material')
bed_material.diffuse_color = (0.4, 0.2, 0.1, 1)  # A different shade of brown
cushion_material = bpy.data.materials.new(name='Cushion Material')
cushion_material.diffuse_color = (0.75, 0.75, 0.75, 1)

# Create the bed base
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.25))
bed_base = bpy.context.object
bed_base.scale = (1, 1.5, 0.1)
bed_base.name = 'Bed Base'
bed_base.data.materials.append(bed_material)

# Create the sides of the bed
sides = [
    ((0, -1.5, 0.75), (1, 0.1, 0.5), 'Front Side'),
    ((0, 1.5, 0.75), (1, 0.1, 0.5), 'Back Side'),
    ((-1, 0, 0.75), (0.1, 1.5, 0.5), 'Left Side'),
    ((1, 0, 0.75), (0.1, 1.5, 0.5), 'Right Side')
]

for side in sides:
    bpy.ops.mesh.primitive_cube_add(size=2, location=side[0])
    new_side = bpy.context.object
    new_side.scale = side[1]
    new_side.name = side[2]
    new_side.data.materials.append(bed_material)

# Create the cushion
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.35))
cushion = bpy.context.object
cushion.scale = (0.9, 1.4, 0.05)
cushion.name = 'Cushion'
cushion.data.materials.append(cushion_material)


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
