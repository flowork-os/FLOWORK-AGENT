# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_bird_feeder_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct bird feeder using blender code

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for different parts of the feeder
brown_material = bpy.data.materials.new(name="Brown Material")
brown_material.diffuse_color = (0.5, 0.3, 0.1, 1)

gray_material = bpy.data.materials.new(name="Gray Material")
gray_material.diffuse_color = (0.2, 0.2, 0.2, 1)

medium_brown = bpy.data.materials.new(name="Medium Brown")
medium_brown.diffuse_color = (0.4, 0.2, 0.1, 1)

# Function to create a cylinder for the feeder body

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create feeder body
feeder = create_cylinder(0.5, 1.0, (0, 0, 0.5), "Feeder Body", brown_material)

# Create roof using a cone shape
bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.2, depth=0.5, location=(0, 0, 1.25))
roof = bpy.context.object
roof.name = "Roof"
roof.data.materials.append(gray_material)

# Create perch
perch = create_cylinder(0.05, 1.0, (0.55, 0, 0.5), "Perch", medium_brown)
perch.rotation_euler[1] = 1.57

# Create hanger
bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.05, location=(0, 0, 1.25))
hanger = bpy.context.object
hanger.name = "Hanger"
hanger.data.materials.append(brown_material)


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
