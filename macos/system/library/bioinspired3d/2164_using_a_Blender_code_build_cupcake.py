# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_code_build_cupcake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender code build cupcake.

import bpy

# Clear existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the cupcake and frosting
base_material = bpy.data.materials.new(name='Base Material')
base_material.diffuse_color = (0.8, 0.4, 0.1, 1)
frosting_material = bpy.data.materials.new(name='Frosting Material')
frosting_material.diffuse_color = (1.0, 0.9, 0.75, 1)

# Function to create a cylinder for the cupcake base
def create_cupcake_base():
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, location=(0, 0, 0.5))
    base = bpy.context.object
    base.name = 'Cupcake Base'
    base.data.materials.append(base_material)

# Function to create frosting layers
def create_frosting_layers():
    for i, (radius, height) in enumerate([(1, 1.1), (0.8, 1.4), (0.6, 1.6)]):
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.3 - i * 0.05, location=(0, 0, height))
        frosting_layer = bpy.context.object
        frosting_layer.name = f'Frosting Layer {i + 1}'
        frosting_layer.data.materials.append(frosting_material)

# Function to create the top of the frosting
def create_frosting_top():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 1.9))
    top = bpy.context.object
    top.name = 'Frosting Top'
    top.data.materials.append(frosting_material)

# Execute the functions to create the cupcake
create_cupcake_base()
create_frosting_layers()
create_frosting_top()


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
