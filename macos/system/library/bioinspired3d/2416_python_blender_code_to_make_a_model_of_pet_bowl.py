# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_make_a_model_of_pet_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to make a model of pet bowl.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the bowls
bowl_material = bpy.data.materials.new(name="BowlMaterial")
bowl_material.diffuse_color = (0.8, 0.5, 0.2, 1)  # Light brown shade

# Function to create a bowl
def create_bowl(location):
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=location)
    bowl = bpy.context.object
    bowl.data.materials.append(bowl_material)
    return bowl

# Generate the bowls using the helper function
create_bowl((-1.5, 0, 0)).name = "BowlA"
create_bowl((1.5, 0, 0)).name = "BowlB"

# Create a base for the bowls
bpy.ops.mesh.primitive_cube_add(size=5, location=(0, 0, -0.25))
base_object = bpy.context.object
base_object.name = "BasePlatform"
base_object.scale = (1, 0.5, 0.1)
base_object.data.materials.append(bowl_material)


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
