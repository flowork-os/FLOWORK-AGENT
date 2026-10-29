# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_bed_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of bed in blender script

import bpy

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the bed
frame_mat = bpy.data.materials.new(name='Wood Color')
frame_mat.diffuse_color = (0.5, 0.25, 0.1, 1)  # Brown
mattress_mat = bpy.data.materials.new(name='Soft Color')
mattress_mat.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light Gray

# Create bed components using a class structure
class BedComponent:
    def __init__(self, size, location, scale, name, material):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        self.object = bpy.context.object
        self.object.scale = scale
        self.object.name = name
        self.object.data.materials.append(material)

# Instantiate bed components
frame = BedComponent(2, (0, 0, 0.25), (1, 2, 0.25), 'Bed Frame', frame_mat)
headboard = BedComponent(2, (0, -2, 0.75), (1, 0.1, 0.75), 'Headboard', frame_mat)
footboard = BedComponent(2, (0, 2, 0.5), (1, 0.1, 0.5), 'Footboard', frame_mat)
mattress = BedComponent(2, (0, 0, 0.75), (0.95, 1.95, 0.2), 'Mattress', mattress_mat)


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
