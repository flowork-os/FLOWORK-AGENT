# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_code_in_Blender_to_make_a_model_of_pen_holder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write code in Blender to make a model of pen holder

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material with a gray shade
material_gray = bpy.data.materials.new(name="MaterialGray")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to add a cylinder

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_gray)
    return obj

# Create the base
base_object = create_cylinder(1.5, 0.1, (0, 0, 0), "Base")

# Create the main compartment
main_compartment_object = create_cylinder(1, 2, (0, 0, 1.05), "MainCompartment")

# Create smaller compartments
positions = [ (1, 1, 0.8), (-1, 1, 0.8), (1, -1, 0.8), (-1, -1, 0.8) ]
for i, pos in enumerate(positions, start=1):
    create_cylinder(0.5, 1.5, pos, f"Compartment_{i}")


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
