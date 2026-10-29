# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender_generate_a_model_of_formal_top_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender generate a model of formal top hat

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the hat
hat_material = bpy.data.materials.new(name='HatMaterial')
hat_material.diffuse_color = (0.1, 0.1, 0.1, 1)  # Dark gray color

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create the top hat body
main_part = create_cylinder(radius=1, depth=2, location=(0, 0, 1), name='HatBody', material=hat_material)

# Create the brim of the hat
brim_part = create_cylinder(radius=1.5, depth=0.1, location=(0, 0, 0), name='HatBrim', material=hat_material)


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
