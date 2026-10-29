# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_code_that_makes_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender code that makes a model of blender

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
base_material = bpy.data.materials.new(name="Base Material")
base_material.diffuse_color = (0.1, 0.1, 0.1, 1)
pitcher_material = bpy.data.materials.new(name="Pitcher Material")
pitcher_material.diffuse_color = (0.8, 0.8, 0.8, 0.3)
lid_material = bpy.data.materials.new(name="Lid Material")
lid_material.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Build the components of the model
create_cylinder(0.5, 0.3, (0, 0, 0.15), "Base", base_material)
create_cylinder(0.4, 1, (0, 0, 0.8), "Pitcher", pitcher_material)
create_cylinder(0.42, 0.1, (0, 0, 1.35), "Lid", lid_material)

# Create measurement lines
for i in range(3):
    bpy.ops.mesh.primitive_plane_add(size=0.02, location=(0.4, 0, 0.6 + i * 0.3))
    marking = bpy.context.object
    marking.name = f"Marking {i + 1}"
    marking.scale[1] = 5
    marking.data.materials.append(base_material)


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
