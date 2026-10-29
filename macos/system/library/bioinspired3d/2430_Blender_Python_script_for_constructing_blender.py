# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_constructing_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for constructing blender.

import bpy

# Start fresh by clearing the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the 3D model
base_material = bpy.data.materials.new(name="Base Material")
base_material.diffuse_color = (0.25, 0.25, 0.25, 1)  # Dark gray

transparent_material = bpy.data.materials.new(name="Transparent Material")
transparent_material.diffuse_color = (1, 1, 1, 0.05)  # Very transparent
transparent_material.use_nodes = True

# Set up the alpha transparency
transparent_nodes = transparent_material.node_tree.nodes
principled_shader = transparent_nodes.get("Principled BSDF")
principled_shader.inputs['Alpha'].default_value = 0.05
transparent_material.blend_method = 'BLEND'

# Function to create and assign materials to cylinders
def add_cylinder(radius, height, position, obj_name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    cylinder = bpy.context.object
    cylinder.name = obj_name
    cylinder.data.materials.append(mat)

# Construct the main components
add_cylinder(1, 0.5, (0, 0, 0.25), "Base", base_material)
add_cylinder(0.8, 2, (0, 0, 1.5), "Container", transparent_material)
add_cylinder(0.85, 0.1, (0, 0, 2.55), "Lid", base_material)


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
