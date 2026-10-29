# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_that_makes_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script that makes bird feeder

import bpy

# Start with a clean slate
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for different parts
material_feeder = bpy.data.materials.new(name='Material for Feeder')
material_feeder.diffuse_color = (0.5, 0.3, 0.1, 1)

material_roof = bpy.data.materials.new(name='Material for Roof')
material_roof.diffuse_color = (0.2, 0.2, 0.2, 1)

# Create functions to handle geometry creation

def create_cone(radius_top, radius_bottom, height, position, name, material):
    bpy.ops.mesh.primitive_cone_add(radius1=radius_bottom, radius2=radius_top, depth=height, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Build the feeder
create_cone(0.2, 0.6, 0.5, (0, 0, 1.25), 'Roof', material_roof)
feeder_body = bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=(0, 0, 0.5))
bpy.context.object.name = 'Feeder Body'
bpy.context.object.data.materials.append(material_feeder)

# Seed tray
bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.1, location=(0, 0, 0.05))
bpy.context.object.name = 'Seed Tray'
bpy.context.object.data.materials.append(material_feeder)

# Perch creation
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.6, location=(0, 0.55, 0.1), rotation=(0, 1.57, 0))
bpy.context.object.name = 'Perch'
bpy.context.object.data.materials.append(material_feeder)


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
