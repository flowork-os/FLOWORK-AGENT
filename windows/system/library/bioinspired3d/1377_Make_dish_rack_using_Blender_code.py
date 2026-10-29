# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_dish_rack_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make dish rack using Blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize material for the model
material_metal = bpy.data.materials.new(name='Metallic')
material_metal.diffuse_color = (0.7, 0.7, 0.7, 1)  # Light gray shade

# Class to handle object creation
class ObjectBuilder:
    @staticmethod
    def add_cube(size, position, obj_name, scale_factors):
        bpy.ops.mesh.primitive_cube_add(size=size, location=position)
        new_cube = bpy.context.object
        new_cube.name = obj_name
        new_cube.scale = scale_factors
        new_cube.data.materials.append(material_metal)

# Build the base
ObjectBuilder.add_cube(2, (0, 0, 0.1), 'Base', (1, 1, 0.05))

# Create side bars using the builder
for idx in range(2):
    ObjectBuilder.add_cube(2, (0.9 * (idx * 2 - 1), 0, 0.6), f'Side Bar {idx + 1}', (0.05, 1, 0.5))

# Generate racks
for idx in range(5):
    ObjectBuilder.add_cube(2, (0, 0.8 * (idx / 4) - 0.4, 0.6), f'Rack {idx + 1}', (0.9, 0.05, 0.05))


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
