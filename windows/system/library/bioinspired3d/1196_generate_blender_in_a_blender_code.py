# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender in a blender code

import bpy

# Reset the scene by removing all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the model
mat_base = bpy.data.materials.new(name="Material Base")
mat_base.diffuse_color = (0.1, 0.1, 0.1, 1)
mat_pitcher = bpy.data.materials.new(name="Material Pitcher")
mat_pitcher.diffuse_color = (0.8, 0.8, 0.8, 0.3)
mat_lid = bpy.data.materials.new(name="Material Lid")
mat_lid.diffuse_color = (0.1, 0.1, 0.1, 1)

# Create the base object
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.3, location=(0, 0, 0.15))
base_object = bpy.context.object
base_object.name = "Base"
base_object.data.materials.append(mat_base)

# Create the pitcher
bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=1, location=(0, 0, 0.8))
pitcher_object = bpy.context.object
pitcher_object.name = "Pitcher"
pitcher_object.data.materials.append(mat_pitcher)

# Create the lid
bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.1, location=(0, 0, 1.35))
lid_object = bpy.context.object
lid_object.name = "Lid"
lid_object.data.materials.append(mat_lid)

# Function to create markings

def create_marking(location):
    bpy.ops.mesh.primitive_plane_add(size=0.02, location=location)
    marking_object = bpy.context.object
    marking_object.scale[1] = 5
    marking_object.data.materials.append(mat_base)
    return marking_object

# Add markings
create_marking((0.4, 0, 0.6))
create_marking((0.4, 0, 0.9))
create_marking((0.4, 0, 1.2))


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
