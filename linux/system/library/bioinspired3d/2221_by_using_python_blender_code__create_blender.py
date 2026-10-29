# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code__create_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code, create blender

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_base = bpy.data.materials.new(name="Base Material")
material_base.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray

material_container = bpy.data.materials.new(name="Container Material")
material_container.diffuse_color = (1, 1, 1, 0.2)  # Slightly more transparent

material_lid = bpy.data.materials.new(name="Lid Material")
material_lid.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray

# Function to create a cylinder with a specific material
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create the base
create_cylinder(1, 0.2, (0, 0, 0.1), "Base", material_base)

# Create the container
create_cylinder(0.9, 3, (0, 0, 1.6), "Container", material_container)

# Create the lid
create_cylinder(0.95, 0.1, (0, 0, 3.1), "Lid", material_lid)

# Create the removable cap
create_cylinder(0.3, 0.2, (0, 0, 3.25), "Cap", material_lid)

# Add measurement markings
for index in range(1, 11):
    bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0.9, 0, 0.2 * index))
    marking = bpy.context.object
    marking.name = f"Marking {index}"
    marking.data.materials.append(material_base)


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
