# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_picture_frame_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build picture frame using blender script

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()  

# Create a new material for the frame
frame_material = bpy.data.materials.new(name='FrameMaterial')
frame_material.diffuse_color = (0.5, 0.3, 0.1, 1)  # Brown tone

# Function to create a scaled cube

def create_cube(size, location, name, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(frame_material)
    return cube

# Create the outer frame
outer_cube = create_cube(1, (0, 0, 0), 'Outer Frame', (1, 0.1, 1.5))

# Create the inner frame (cutout)
inner_cube = create_cube(1, (0, 0, 0), 'Inner Frame', (0.9, 0.1, 1.4))

# Add a boolean modifier for the cutout
boolean_modifier = outer_cube.modifiers.new(type='BOOLEAN', name='Cutout')
boolean_modifier.operation = 'DIFFERENCE'
boolean_modifier.object = inner_cube
bpy.context.view_layer.objects.active = outer_cube
bpy.ops.object.modifier_apply(modifier='Cutout')

# Remove the inner cube as it is no longer needed
bpy.data.objects.remove(inner_cube, do_unlink=True)


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
