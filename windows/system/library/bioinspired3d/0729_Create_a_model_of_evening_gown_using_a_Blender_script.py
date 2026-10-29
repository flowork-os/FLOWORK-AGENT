# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_evening_gown_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of evening gown using a Blender script

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the gown
fabric_material = bpy.data.materials.new(name='Fabric Material')
fabric_material.diffuse_color = (0.1, 0.1, 0.3, 1)  # Deep blue shade

# Function to create a cylinder for the bodice
def create_bodice(location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.2, location=location)
    bodice_part = bpy.context.object
    bodice_part.name = 'Bodice'
    bodice_part.scale = (1, 1, 1.5)
    bodice_part.data.materials.append(fabric_material)

# Function to create a cone for the skirt
def create_skirt(location):
    bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0, depth=2, location=location)
    skirt_part = bpy.context.object
    skirt_part.name = 'Skirt'
    skirt_part.data.materials.append(fabric_material)

# Create the bodice and skirt
create_bodice((0, 0, 1.1))
create_skirt((0, 0, 0))

# Function to create sleeves
def create_sleeves(num_sleeves):
    for index in range(num_sleeves):
        x_offset = 0.35 * (index * 2 - 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=1.2, location=(x_offset, 0, 1.1))
        sleeve_part = bpy.context.object
        sleeve_part.name = f'Sleeve {index + 1}'
        sleeve_part.rotation_euler[1] = 1.57  # Horizontal orientation
        sleeve_part.data.materials.append(fabric_material)

# Create the sleeves
create_sleeves(2)

# Function to create neckline
def create_neckline(location):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.05, location=location)
    neckline_part = bpy.context.object
    neckline_part.name = 'Neckline'
    neckline_part.scale = (1, 1, 0.3)
    neckline_part.data.materials.append(fabric_material)

# Create neckline
create_neckline((0, 0, 1.7))

# Function to create zipper
def create_zipper(location):
    bpy.ops.mesh.primitive_cube_add(size=0.02, location=location)
    zipper_part = bpy.context.object
    zipper_part.name = 'Zipper'
    zipper_part.scale = (1, 1, 10)
    zipper_part.data.materials.append(fabric_material)

# Create the zipper
create_zipper((0, -0.3, 0.5))


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
