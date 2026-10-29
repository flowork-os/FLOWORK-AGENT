# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_to_make_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script to make a model of blender

import bpy

# Clear the current scene by removing all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with descriptive names
material_base = bpy.data.materials.new(name='Material_Base')
material_base.diffuse_color = (0.2, 0.2, 0.2, 1.0)  # Dark gray
material_jar = bpy.data.materials.new(name='Material_Jar')
material_jar.diffuse_color = (0.8, 0.8, 0.8, 0.3)  # Light gray with transparency
material_lid = bpy.data.materials.new(name='Material_Lid')
material_lid.diffuse_color = (0.1, 0.1, 0.1, 1.0)  # Black
material_panel = bpy.data.materials.new(name='Material_Panel')
material_panel.diffuse_color = (0.5, 0.5, 0.5, 1.0)  # Medium gray

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Function to create a cube

def create_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Construct the 3D model
base = create_cylinder(radius=1, depth=1, location=(0, 0, 0.5), name='Base', material=material_base)
panel = create_cube(size=0.5, location=(0, 0.75, 0.25), name='Control Panel', material=material_panel)
panel.scale = (0.5, 0.1, 0.5)
jar = create_cylinder(radius=0.8, depth=2, location=(0, 0, 2), name='Jar', material=material_jar)
lid = create_cylinder(radius=0.85, depth=0.1, location=(0, 0, 3.05), name='Lid', material=material_lid)

# Add measurement markings on the jar
for index in range(1, 5):
    marking_loc = (0.85, 0, 1 + index * 0.4)
    marking = create_cube(size=0.05, location=marking_loc, name=f'Marking_{index}', material=material_base)
    marking.scale = (0.02, 0.02, 0.2)


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
