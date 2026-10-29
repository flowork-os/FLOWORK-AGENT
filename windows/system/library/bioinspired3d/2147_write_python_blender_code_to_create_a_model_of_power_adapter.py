# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_python_blender_code_to_create_a_model_of_power_adapter" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write python blender code to create a model of power adapter

import bpy

# Step 1: Clear the workspace
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define material for the adapter
adapter_material = bpy.data.materials.new(name="DarkGray")
adapter_material.diffuse_color = (0.1, 0.1, 0.1, 1)

# Step 2: Construct the main component
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
main_body = bpy.context.object
main_body.name = "Main Adapter"
main_body.data.materials.append(adapter_material)

# Step 3: Add the cylindrical connector
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1, location=(0, 1.1, 0))
cylinder_connector = bpy.context.object
cylinder_connector.name = "Cylindrical Connector"
cylinder_connector.data.materials.append(adapter_material)

# Step 4: Insert USB connection ports
for index in range(4):
    position_x = -0.6 + index * 0.4
    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(position_x, -1.1, 0))
    usb_slot = bpy.context.object
    usb_slot.name = f"USB Slot {index + 1}"
    usb_slot.data.materials.append(adapter_material)


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
