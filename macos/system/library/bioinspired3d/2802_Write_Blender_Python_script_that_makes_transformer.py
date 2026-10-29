# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_makes_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that makes transformer.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material Definitions
base_material = bpy.data.materials.new(name="Base Material")
base_material.diffuse_color = (0.2, 0.2, 0.2, 1)
coil_material = bpy.data.materials.new(name="Coil Material")
coil_material.diffuse_color = (1, 0.5, 0, 1)
casing_material = bpy.data.materials.new(name="Casing Material")
casing_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a cube
def create_cube(name, scale, material, location=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Create the Core
core = create_cube("Core", (0.5, 0.5, 1.5), base_material)

# Create Windings
for index in range(2):
    position = 0.7 * (index * 2 - 1)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.05, location=(position, 0, 0))
    coil = bpy.context.object
    coil.name = f"Coil {index + 1}"
    coil.data.materials.append(coil_material)

# Create the Casing
casing = create_cube("Casing", (1.5, 1.5, 2), casing_material)

# Adjust the casing material for transparency
casing_material.use_nodes = True
bsdf_node = casing_material.node_tree.nodes.get('Principled BSDF')
if bsdf_node:
    bsdf_node.inputs['Alpha'].default_value = 0.5
    casing.show_transparent = True


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
