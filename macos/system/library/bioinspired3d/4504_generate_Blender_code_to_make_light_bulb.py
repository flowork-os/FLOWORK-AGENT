# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_to_make_light_bulb" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code to make light bulb

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
transparent_material = bpy.data.materials.new(name='Transparent Glass')
transparent_material.diffuse_color = (1, 1, 1, 0.1)  # Semi-transparent white
metallic_material = bpy.data.materials.new(name='Metallic Base')
metallic_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Standard gray

# Function to create a sphere

def create_sphere(radius, location, name, material):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    sphere = bpy.context.object
    sphere.name = name
    sphere.data.materials.append(material)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)

# Create the glass top
create_sphere(1, (0, 0, 1.5), 'Glass Top', transparent_material)

# Create the screw base
create_cylinder(0.5, 1, (0, 0, 0.5), 'Screw Base', metallic_material)

# Create the filament
create_sphere(0.2, (0, 0, 1.5), 'Filament', metallic_material)


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
