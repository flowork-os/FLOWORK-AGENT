# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_code_in_Blender_build_a_model_of_fedora" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using code in Blender build a model of fedora

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the hat and ribbon
hat_material = bpy.data.materials.new(name='HatMaterial')
hat_material.diffuse_color = (0.2, 0.2, 0.2, 1)  # Dark gray
ribbon_material = bpy.data.materials.new(name='RibbonMaterial')
ribbon_material.diffuse_color = (0.1, 0.1, 0.1, 1)  # Black

# Function to create a cylinder

def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Step 2: Create the brim of the hat
brim = add_cylinder(1.5, 0.1, (0, 0, 0), 'Brim', hat_material)

# Step 3: Create the crown
crown = add_cylinder(0.8, 1, (0, 0, 0.55), 'Crown', hat_material)

# Step 4: Create the indentation
bpy.ops.mesh.primitive_cone_add(radius1=0.4, radius2=0, depth=0.6, location=(0, 0, 1.1))
indentation = bpy.context.object
indentation.name = 'Indentation'
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers['Boolean'].operation = 'DIFFERENCE'
bpy.context.object.modifiers['Boolean'].object = crown
bpy.ops.object.modifier_apply(modifier='Boolean')
bpy.data.objects.remove(indentation)

# Step 5: Create the ribbon
ribbon = add_cylinder(0.85, 0.1, (0, 0, 0.55), 'Ribbon', ribbon_material)


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
