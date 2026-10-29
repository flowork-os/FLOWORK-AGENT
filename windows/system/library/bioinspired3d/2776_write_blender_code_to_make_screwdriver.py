# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_to_make_screwdriver" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code to make screwdriver.

import bpy

# Step 1: Clear Existing Meshes
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the components
handle_material = bpy.data.materials.new(name='Handle Material')
handle_material.diffuse_color = (0.8, 0.3, 0.3, 1)  # Light red for the handle
metal_material = bpy.data.materials.new(name='Metallic Material')
metal_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Slightly darker gray for the shaft

# Step 2: Build the Handle
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(0, 0, 0.5))
handle_object = bpy.context.object
handle_object.name = 'Grip'
handle_object.data.materials.append(handle_material)

# Step 3: Build the Shaft
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1.5, location=(0, 0, -0.75))
shaft_object = bpy.context.object
shaft_object.name = 'Rod'
shaft_object.data.materials.append(metal_material)

# Step 4: Construct the Flat Tip
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, -1.55))
tip_object = bpy.context.object
tip_object.scale[1] = 0.01  # Flatten the cube
tip_object.name = 'End'
tip_object.data.materials.append(metal_material)


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
