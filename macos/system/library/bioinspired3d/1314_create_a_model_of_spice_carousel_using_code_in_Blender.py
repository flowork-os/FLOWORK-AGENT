# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_spice_carousel_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of spice carousel using code in Blender

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the carousel
carousel_material = bpy.data.materials.new(name='Carousel Material')
carousel_material.diffuse_color = (0.7, 0.7, 0.7, 1)
jar_material = bpy.data.materials.new(name='Jar Material')
jar_material.diffuse_color = (1, 1, 1, 1)
lid_material = bpy.data.materials.new(name='Lid Material')
lid_material.diffuse_color = (0.05, 0.05, 0.05, 1)

# Create the carousel base
bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=0.2, location=(0, 0, 0))
base_object = bpy.context.object
base_object.name = 'Carousel Base'
base_object.data.materials.append(carousel_material)

# Create the handle
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(0, 0, 1.1))
handle_object = bpy.context.object
handle_object.name = 'Carousel Handle'
handle_object.data.materials.append(carousel_material)

# Create spice jars and their lids
for index in range(12):
    angle = index * (2 * math.pi / 12)
    x_pos = 1.5 * math.cos(angle)
    y_pos = 1.5 * math.sin(angle)
    
    # Create jar body
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.6, location=(x_pos, y_pos, 0.4))
    jar_object = bpy.context.object
    jar_object.name = f'Jar {index + 1}'
    jar_object.data.materials.append(jar_material)
    
    # Create jar lid
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.1, location=(x_pos, y_pos, 0.75))
    lid_object = bpy.context.object
    lid_object.name = f'Lid {index + 1}'
    lid_object.data.materials.append(lid_material)
    
    # Create shaker top
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.05, location=(x_pos, y_pos, 0.8))
    shaker_top_object = bpy.context.object
    shaker_top_object.name = f'Shaker Top {index + 1}'
    shaker_top_object.data.materials.append(lid_material)


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
