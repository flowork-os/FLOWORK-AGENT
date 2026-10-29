# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_blender_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create blender in Blender Python script

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
base_material = bpy.data.materials.new(name="Base Material")
base_material.diffuse_color = (0.2, 0.2, 0.2, 1)
container_material = bpy.data.materials.new(name="Container Material")
container_material.diffuse_color = (0.8, 0.8, 0.8, 0.3)
button_material = bpy.data.materials.new(name="Button Material")
button_material.diffuse_color = (0.8, 0.1, 0.1, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create base and container
base_object = create_cylinder(1, 0.5, (0, 0, 0.25), "Base", base_material)
container_object = create_cylinder(0.8, 2, (0, 0, 1.5), "Container", container_material)

# Create buttons using a loop
for index in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.5 * (index - 1), 0.9, 0.25))
    button_object = bpy.context.object
    button_object.name = f"Button {index + 1}"
    button_object.data.materials.append(button_material)


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
