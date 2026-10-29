# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_blender_code_generate_a_model_of_cat_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a blender code generate a model of cat bed

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the bed's appearance
bed_texture = bpy.data.materials.new(name="BedTexture")
bed_texture.diffuse_color = (0.5, 0.35, 0.25, 1)  # A nice brown hue

# Step 1: Construct the bed base
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.1, location=(0, 0, 0))
base_object = bpy.context.object
base_object.name = "BedBase"
base_object.data.materials.append(bed_texture)

# Step 2: Create the edges using a toroidal shape
bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.2, location=(0, 0, 0.15))
edge_object = bpy.context.object
edge_object.name = "BedEdges"
edge_object.data.materials.append(bed_texture)

# Step 3: Indentation for the cat's comfort
bpy.ops.mesh.primitive_cylinder_add(radius=1.3, depth=0.1, location=(0, 0, 0.05))
indent_object = bpy.context.object
indent_object.name = "CatIndent"
indent_object.data.materials.append(bed_texture)

# Step 4: Utilize the boolean modifier to hollow out the base
bpy.context.view_layer.objects.active = base_object
bool_mod = base_object.modifiers.new(type="BOOLEAN", name="Hollow")
bool_mod.operation = 'DIFFERENCE'
bool_mod.object = indent_object
bpy.ops.object.modifier_apply(modifier="Hollow")

# Step 5: Remove the indentation object
bpy.data.objects.remove(indent_object, do_unlink=True)


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
