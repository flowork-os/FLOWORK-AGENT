# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_evening_gown_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of evening gown in blender python code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the dress
material_dress = bpy.data.materials.new(name='Dress Material')
material_dress.diffuse_color = (0.1, 0.1, 0.3, 1)  # Deep blue color

# Add bodice
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.2, location=(0, 0, 1.1))
bodice_obj = bpy.context.object
bodice_obj.name = 'Bodice'
bodice_obj.scale[2] = 1.5
bodice_obj.data.materials.append(material_dress)

# Add skirt
bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0, depth=2, location=(0, 0, 0))
skirt_obj = bpy.context.object
skirt_obj.name = 'Skirt'
skirt_obj.data.materials.append(material_dress)

# Create sleeves using a loop
for sleeve_index in range(2):
    sleeve_x_pos = 0.35 * (sleeve_index * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=1.2, location=(sleeve_x_pos, 0, 1.1))
    sleeve_obj = bpy.context.object
    sleeve_obj.name = f'Sleeve {sleeve_index + 1}'
    sleeve_obj.rotation_euler[1] = 1.57  # Rotate to horizontal
    sleeve_obj.data.materials.append(material_dress)

# Add neckline
bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.05, location=(0, 0, 1.7))
neckline_obj = bpy.context.object
neckline_obj.name = 'Neckline'
neckline_obj.scale[2] = 0.3
neckline_obj.data.materials.append(material_dress)

# Create zipper
bpy.ops.mesh.primitive_cube_add(size=0.02, location=(0, -0.3, 0.5))
zipper_obj = bpy.context.object
zipper_obj.name = 'Zipper'
zipper_obj.scale[2] = 10
zipper_obj.data.materials.append(material_dress)


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
