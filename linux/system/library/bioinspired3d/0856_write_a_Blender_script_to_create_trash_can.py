# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_script_to_create_trash_can" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender script to create trash can

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the objects
metal_material = bpy.data.materials.new(name="MetalMaterial")
metal_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray
plastic_material = bpy.data.materials.new(name="PlasticMaterial")
plastic_material.diffuse_color = (0.3, 0.3, 0.3, 1)  # Darker gray

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the trash can body
trash_can = create_cylinder(radius=0.5, depth=1.0, location=(0, 0, 0.5), name="TrashCanBody", material=metal_material)

# Create the lid
lid = create_cylinder(radius=0.55, depth=0.1, location=(0, 0, 1.05), name="Lid", material=plastic_material)

# Function to create a cube

def create_cube(size, location, name, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Create the foot pedal
pedal = create_cube(size=0.2, location=(0.6, 0, 0.1), name="FootPedal", scale=(1, 1, 0.05), material=plastic_material)


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
