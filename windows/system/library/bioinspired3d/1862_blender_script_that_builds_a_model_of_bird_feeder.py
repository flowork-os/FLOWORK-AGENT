# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_that_builds_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script that builds a model of bird feeder.

import bpy

# Clear existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
feeder_material = bpy.data.materials.new(name='Feeder Material')
feeder_material.diffuse_color = (0.5, 0.3, 0.1, 1)  # Color for the feeder

roof_material = bpy.data.materials.new(name='Roof Material')
roof_material.diffuse_color = (0.2, 0.2, 0.2, 1)  # Color for the roof

# Function to add a cylinder
def add_cylinder(radius, depth, position, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the feeder body
feeder_body = add_cylinder(0.5, 1, (0, 0, 0.5), 'Feeder Body', feeder_material)

# Create the roof
bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.2, depth=0.5, location=(0, 0, 1.25))
roof = bpy.context.object
roof.name = 'Roof'
roof.data.materials.append(roof_material)

# Create the seed tray
seed_tray = add_cylinder(0.55, 0.1, (0, 0, 0.05), 'Seed Tray', feeder_material)

# Create the perch
perch = add_cylinder(0.05, 0.6, (0, 0.55, 0.1), 'Perch', feeder_material)


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
