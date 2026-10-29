# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender_make_a_model_of_dog_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender make a model of dog bed

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for bed and cushion
material_bed = bpy.data.materials.new(name="Material for Bed")
material_bed.diffuse_color = (0.55, 0.27, 0.07, 1)
material_cushion = bpy.data.materials.new(name="Material for Cushion")
material_cushion.diffuse_color = (0.8, 0.8, 0.8, 1)

# Create the bed base
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.2, location=(0, 0, 0))
bed_base = bpy.context.object
bed_base.name = "Bed Base"
bed_base.data.materials.append(material_bed)

# Create the surrounding raised edges
bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.2, location=(0, 0, 0.2))
raised_edges = bpy.context.object
raised_edges.name = "Raised Edges"
raised_edges.data.materials.append(material_bed)

# Create the cushion component
bpy.ops.mesh.primitive_cylinder_add(radius=1.3, depth=0.15, location=(0, 0, 0.1))
cushion = bpy.context.object
cushion.name = "Cushion"
cushion.data.materials.append(material_cushion)


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
