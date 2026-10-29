# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_blender_code__generate_trash_can" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using blender code, generate trash can

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials
metal_material = bpy.data.materials.new(name="Metal")
metal_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Light silver
plastic_material = bpy.data.materials.new(name="Plastic")
plastic_material.diffuse_color = (0.1, 0.1, 0.1, 1)  # Very dark gray

# Create the body of the trash can
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, location=(0, 0, 0.5))
can_body = bpy.context.object
can_body.name = "Body"
can_body.data.materials.append(metal_material)

# Create the lid of the trash can
bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.1, location=(0, 0, 1.05))
can_lid = bpy.context.object
can_lid.name = "Lid"
can_lid.data.materials.append(plastic_material)

# Create the foot pedal
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.6, 0, 0.1))
pedal = bpy.context.object
pedal.name = "FootPedal"
pedal.scale[2] = 0.05  # Flatten the pedal
pedal.data.materials.append(plastic_material)


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
