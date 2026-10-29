# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_Python_script_build_travel_bag" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender Python script build travel bag

import bpy

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the bag components
black_material = bpy.data.materials.new(name='BlackMaterial')
black_material.diffuse_color = (0.1, 0.1, 0.1, 1)

light_gray_material = bpy.data.materials.new(name='LightGrayMaterial')
light_gray_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Create bag compartment
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
bag_compartment = bpy.context.object
bag_compartment.scale = (1, 0.5, 0.5)
bag_compartment.name = 'BagCompartment'
bag_compartment.data.materials.append(black_material)

# Add zipper
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, 0.55))
zipper_piece = bpy.context.object
zipper_piece.scale = (1, 0.05, 0.05)
zipper_piece.name = 'ZipperPiece'
zipper_piece.data.materials.append(light_gray_material)

# Create handles using a list comprehension
handle_positions = [0.8 * (i * 2 - 1) for i in range(2)]
for pos in handle_positions:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(pos, 0, 0.5), rotation=(0, 1.57, 0))
    handle_object = bpy.context.object
    handle_object.name = f'Handle_{int((pos + 0.8) / 1.6 + 1)}'
    handle_object.data.materials.append(black_material)


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
