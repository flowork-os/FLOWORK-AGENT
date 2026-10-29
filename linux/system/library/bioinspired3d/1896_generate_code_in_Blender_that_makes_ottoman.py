# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_code_in_Blender_that_makes_ottoman" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate code in Blender that makes ottoman

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the ottoman
material_ottoman = bpy.data.materials.new(name='Ottoman Material')
material_ottoman.diffuse_color = (0.4, 0.2, 0.1, 1)  # Darker brown hue

# Generate the base of the ottoman
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
ottoman_base = bpy.context.object
ottoman_base.name = 'Base'
ottoman_base.scale[2] = 0.1  # Flatten the cube
ottoman_base.data.materials.append(material_ottoman)

# Define parameters for the legs
height_of_legs = 0.5
radius_of_legs = 0.05
positions_of_legs = [(-0.8, -0.8, height_of_legs / 2), (0.8, -0.8, height_of_legs / 2), (-0.8, 0.8, height_of_legs / 2), (0.8, 0.8, height_of_legs / 2)]

# Create each leg using a loop
for index, position in enumerate(positions_of_legs):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_legs, depth=height_of_legs, location=position)
    leg = bpy.context.object
    leg.name = f'Leg_{index + 1}'
    leg.data.materials.append(material_ottoman)


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
