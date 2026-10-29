# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_code_in_Blender__generate_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using code in Blender, generate a model of sofa.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sofa and cushions
sofa_mat = bpy.data.materials.new(name="SofaMaterial")
sofa_mat.diffuse_color = (0.5, 0.25, 0.25, 1)

cushion_mat = bpy.data.materials.new(name="CushionMaterial")
cushion_mat.diffuse_color = (0.8, 0.8, 0.8, 1)

# Add the sofa base
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
sofa_base = bpy.context.object
sofa_base.scale = (2, 1, 0.5)
sofa_base.name = "SofaBase"
sofa_base.data.materials.append(sofa_mat)

# Add the backrest
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.75, 1.25))
backrest = bpy.context.object
backrest.scale = (2, 0.25, 0.75)
backrest.name = "Backrest"
backrest.data.materials.append(sofa_mat)

# Function to add cushions

def add_cushions(count, base_location, cushion_scale, cushion_name, material):
    for i in range(count):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(base_location[0] + i * 1.25, base_location[1], base_location[2]))
        cushion = bpy.context.object
        cushion.scale = cushion_scale
        cushion.name = f"{cushion_name}_{i + 1}"
        cushion.data.materials.append(material)

# Create seat and backrest cushions
add_cushions(3, (-1.25, 0, 1), (0.6, 0.9, 0.2), "SeatCushion", cushion_mat)
add_cushions(3, (-1.25, -0.75, 1.75), (0.6, 0.2, 0.5), "BackrestCushion", cushion_mat)


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
