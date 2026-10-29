# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_sandwich_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of sandwich in a Blender script

import bpy

# Step 1: Clear the Scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the sandwich components
bun_material = bpy.data.materials.new(name="Bun")
bun_material.diffuse_color = (0.9, 0.7, 0.5, 1)
leaf_material = bpy.data.materials.new(name="Leaf")
leaf_material.diffuse_color = (0.2, 0.8, 0.2, 1)
tomato_material = bpy.data.materials.new(name="Tomato")
tomato_material.diffuse_color = (0.8, 0.1, 0.1, 1)
cheese_material = bpy.data.materials.new(name="Cheese")
cheese_material.diffuse_color = (1, 0.9, 0.1, 1)

# Function to create a slice
def create_slice(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    slice_object = bpy.context.object
    slice_object.name = name
    slice_object.scale[2] = scale
    slice_object.data.materials.append(material)
    return slice_object

# Step 2: Create sandwich layers
create_slice("Bottom Bun", (0, 0, 0), 0.1, bun_material)
create_slice("Leaf", (0, 0, 0.2), 0.05, leaf_material)
create_slice("Tomato Slice", (0, 0, 0.3), 0.05, tomato_material)
create_slice("Cheese Layer", (0, 0, 0.4), 0.05, cheese_material)
create_slice("Top Bun", (0, 0, 0.6), 0.1, bun_material)


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
