# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_that_makes_a_model_of_cupcake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code that makes a model of cupcake.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the cupcake and frosting
material_cupcake = bpy.data.materials.new(name='Cupcake Base Material')
material_cupcake.diffuse_color = (0.75, 0.35, 0.1, 1)
material_frosting = bpy.data.materials.new(name='Frosting Base Material')
material_frosting.diffuse_color = (1.0, 0.88, 0.76, 1)

# Create cupcake base
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, location=(0, 0, 0.5))
cupcake = bpy.context.object
cupcake.name = 'Cupcake Base'
cupcake.data.materials.append(material_cupcake)

# Add frosting layers
z_positions = [1.1, 1.4, 1.6]
for i, z in enumerate(z_positions):
    bpy.ops.mesh.primitive_torus_add(major_radius=1 - i * 0.2, minor_radius=0.3 - i * 0.05, location=(0, 0, z))
    frosting_layer = bpy.context.object
    frosting_layer.name = f'Frosting Layer {i + 1}'
frosting_layer.data.materials.append(material_frosting)

# Create the frosting top
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 1.9))
frosting_top = bpy.context.object
frosting_top.name = 'Frosting Top'
frosting_top.data.materials.append(material_frosting)


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
