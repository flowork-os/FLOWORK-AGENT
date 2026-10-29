# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_code__build_a_model_of_fuse" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender code, build a model of fuse.

import bpy

# Clear existing meshes
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials
mat_glass = bpy.data.materials.new(name='Glass')
mat_glass.diffuse_color = (0.8, 0.8, 0.8, 1)
mat_metal = bpy.data.materials.new(name='Metal')
mat_metal.diffuse_color = (0.5, 0.5, 0.5, 1)

# Class to create 3D objects
class CylinderCreator:
    @staticmethod
    def create(radius, depth, loc, name, material):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(material)

# Instantiate the creator and build the glass body
creator = CylinderCreator()
creator.create(0.1, 1.0, (0, 0, 0), 'Glass Body', mat_glass)

# Create metal caps
creator.create(0.12, 0.2, (0, 0, -0.6), 'Cap Bottom', mat_metal)
creator.create(0.12, 0.2, (0, 0, 0.6), 'Cap Top', mat_metal)


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
