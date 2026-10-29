# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_for_creating_coffee_maker" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender for creating coffee maker.

import bpy

# Clear the existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
mat_black = bpy.data.materials.new(name="MatteBlack")
mat_black.diffuse_color = (0, 0, 0, 1)
mat_silver = bpy.data.materials.new(name="ShinySilver")
mat_silver.diffuse_color = (0.75, 0.75, 0.75, 1)

# Function to create a cylinder

def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Creating the components
base_cylinder = add_cylinder(1.2, 0.2, (0, 0, 0.1), "Base", mat_black)
reservoir_cylinder = add_cylinder(0.6, 1.5, (0, 0, 1.0), "Reservoir", mat_silver)

# Create the coffee dispenser
coffee_dispenser = add_cylinder(0.2, 0.5, (0, 0, 1.75), "Dispenser", mat_black)

# Create the cup
cup_cylinder = add_cylinder(0.3, 0.6, (0, 0, 0.3), "Cup", mat_silver)

# Create the cup handle
bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.05, location=(0.45, 0, 0.3), rotation=(1.57, 0, 0))
handle_torus = bpy.context.object
handle_torus.name = "CupHandle"
handle_torus.data.materials.append(mat_black)


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
