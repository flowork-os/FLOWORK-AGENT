# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_makes_citrus_juicer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that makes citrus juicer

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts of the model
container_material = bpy.data.materials.new(name='Container Material')
container_material.diffuse_color = (0.8, 0.8, 0.8, 1)
reamer_material = bpy.data.materials.new(name='Reamer Material')
reamer_material.diffuse_color = (0.5, 0.5, 0.5, 1)
handle_material = bpy.data.materials.new(name='Handle Material')
handle_material.diffuse_color = (0.2, 0.2, 0.2, 1)

# Create the container
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
container_object = bpy.context.object
container_object.name = 'Container'
container_object.data.materials.append(container_material)

# Create the reamer
bpy.ops.mesh.primitive_cone_add(radius1=0.8, radius2=0.2, depth=1.5, location=(0, 0, 2.75))
reamer_object = bpy.context.object
reamer_object.name = 'Reamer'
reamer_object.data.materials.append(reamer_material)

# Create the spout
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(1.1, 0, 1.5), rotation=(0, 1.57, 0))
spout_object = bpy.context.object
spout_object.name = 'Spout'
spout_object.data.materials.append(container_material)

# Create the handle
bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.1, location=(-1.1, 0, 1.5), rotation=(1.57, 0, 0))
handle_object = bpy.context.object
handle_object.name = 'Handle'
handle_object.data.materials.append(handle_material)


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
