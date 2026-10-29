# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_Python_script__create_a_model_of_trash_can" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender Python script, create a model of trash can

import bpy

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials
metallic_surface = bpy.data.materials.new(name="MetallicSurface")
metallic_surface.diffuse_color = (0.4, 0.4, 0.4, 1)  # Medium gray
plastic_surface = bpy.data.materials.new(name="PlasticSurface")
plastic_surface.diffuse_color = (0.25, 0.25, 0.25, 1)  # Slightly darker gray

# Create the trash can body
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, location=(0, 0, 0.5))
trash_can = bpy.context.object
trash_can.name = "CanBody"
trash_can.data.materials.append(metallic_surface)

# Add the lid
bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.1, location=(0, 0, 1.05))
lid_component = bpy.context.object
lid_component.name = "CanLid"
lid_component.data.materials.append(plastic_surface)

# Add the foot pedal
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.6, 0, 0.1))
pedal_component = bpy.context.object
pedal_component.name = "Pedal"
pedal_component.scale[2] = 0.05  # Flatten the pedal
pedal_component.data.materials.append(plastic_surface)


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
