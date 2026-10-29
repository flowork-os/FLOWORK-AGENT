# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_Blender_script__make_a_model_of_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a Blender script, make a model of dining table.

import bpy

# Start by clearing the scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_texture = bpy.data.materials.new(name="Wood")
wood_texture.diffuse_color = (0.64, 0.32, 0.18, 1)  # Brown color

# Function to build the table

def build_table():
    # Create the tabletop
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    top_surface = bpy.context.object
    top_surface.scale = (1.5, 1, 0.1)
    top_surface.name = "Tabletop"
    top_surface.data.materials.append(wood_texture)

    # Create table legs
    leg_height = 0.9
    leg_radius = 0.05
    leg_locations = [(-1.4, -0.9, 0), (1.4, -0.9, 0), (-1.4, 0.9, 0), (1.4, 0.9, 0)]
    for i, loc in enumerate(leg_locations):
        bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=(loc[0], loc[1], leg_height / 2))
        leg = bpy.context.object
        leg.name = f"Table Leg {i + 1}"
        leg.data.materials.append(wood_texture)

# Execute table creation
build_table()


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
