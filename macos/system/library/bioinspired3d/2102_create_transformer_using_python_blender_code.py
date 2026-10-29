# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_transformer_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create transformer using python blender code

import bpy

# Clear the current mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for different components
material_dark = bpy.data.materials.new(name="Dark Material")
material_dark.diffuse_color = (0.2, 0.2, 0.2, 1)
material_orange = bpy.data.materials.new(name="Orange Material")
material_orange.diffuse_color = (1, 0.5, 0, 1)
material_light = bpy.data.materials.new(name="Light Material")
material_light.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a scaled cube
def create_scaled_cube(name, scale_factors, mat):
    bpy.ops.mesh.primitive_cube_add(size=1)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale_factors
    cube.data.materials.append(mat)

# Build the Core
create_scaled_cube("Core", (0.5, 0.5, 1.5), material_dark)

# Generate Windings
for idx in range(2):
    x_position = 0.7 * (idx * 2 - 1)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.05, location=(x_position, 0, 0))
    winding_obj = bpy.context.object
    winding_obj.name = f"Winding_{idx + 1}"
    winding_obj.data.materials.append(material_orange)

# Create the Casing
create_scaled_cube("Casing", (1.5, 1.5, 2), material_light)

# Adjust the casing for transparency
material_light.use_nodes = True
node_bsdf = material_light.node_tree.nodes.get('Principled BSDF')
if node_bsdf:
    node_bsdf.inputs['Alpha'].default_value = 0.5
    bpy.context.object.show_transparent = True


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
