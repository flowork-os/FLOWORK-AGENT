# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_to_make_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code to make a model of bird feeder

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the feeder parts
material_feeder = bpy.data.materials.new(name="Feeder")
material_feeder.diffuse_color = (0.5, 0.3, 0.1, 1)

material_roof = bpy.data.materials.new(name="Roof")
material_roof.diffuse_color = (0.2, 0.2, 0.2, 1)

material_perch = bpy.data.materials.new(name="Perch")
material_perch.diffuse_color = (0.4, 0.2, 0.1, 1)

# Create the feeder body as a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, location=(0, 0, 0.5))
feeder_body = bpy.context.object
feeder_body.name = "Feeder Body"
feeder_body.data.materials.append(material_feeder)

# Create the roof as a cone
bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.2, depth=0.5, location=(0, 0, 1.25))
roof_object = bpy.context.object
roof_object.name = "Roof"
roof_object.data.materials.append(material_roof)

# Add the perch as a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.0, location=(0.55, 0, 0.5), rotation=(0, 1.57, 0))
perch_object = bpy.context.object
perch_object.name = "Perch"
perch_object.data.materials.append(material_perch)

# Add the hanger as a torus
bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.05, location=(0, 0, 1.25))
hanger_object = bpy.context.object
hanger_object.name = "Hanger"
hanger_object.data.materials.append(material_feeder)


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
