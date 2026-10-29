# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_code_create_picture_frame" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender code create picture frame.

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()  

# Create a material for the frame
material_frame = bpy.data.materials.new(name='FrameMaterial')
material_frame.diffuse_color = (0.5, 0.3, 0.1, 1)

# Create the outer frame cube
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
outer_frame = bpy.context.object
outer_frame.name = 'FrameOuter'
outer_frame.scale = (1, 0.1, 1.5)
outer_frame.data.materials.append(material_frame)

# Create the inner frame cube
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
inner_frame = bpy.context.object
inner_frame.name = 'FrameInner'
inner_frame.scale = (0.9, 0.1, 1.4)
inner_frame.data.materials.append(material_frame)

# Set up and apply the boolean modifier
bool_modifier = outer_frame.modifiers.new(type='BOOLEAN', name='BooleanCut')
bool_modifier.operation = 'DIFFERENCE'
bool_modifier.object = inner_frame
bpy.context.view_layer.objects.active = outer_frame
bpy.ops.object.modifier_apply(modifier='BooleanCut')

# Cleanup the inner frame
bpy.data.objects.remove(inner_frame, do_unlink=True)


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
