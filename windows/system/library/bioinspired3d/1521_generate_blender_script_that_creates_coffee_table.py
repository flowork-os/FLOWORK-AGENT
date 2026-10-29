# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_that_creates_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script that creates coffee table

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
material_wood = bpy.data.materials.new(name='Wood Texture')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create the tabletop
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
table_surface = bpy.context.object
table_surface.scale = (2, 1, 0.1)
table_surface.name = 'Table Surface'
table_surface.data.materials.append(material_wood)

# Create table legs
legs_info = {
    'positions': [(-1.9, -0.9, 0.25), (1.9, -0.9, 0.25), (-1.9, 0.9, 0.25), (1.9, 0.9, 0.25)],
    'radius': 0.05,
    'height': 0.5
}
for index, position in enumerate(legs_info['positions']):
    bpy.ops.mesh.primitive_cylinder_add(radius=legs_info['radius'], depth=legs_info['height'], location=position)
    leg = bpy.context.object
    leg.name = f'Leg_{index + 1}'
    leg.data.materials.append(material_wood)


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
