# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_to_create_a_model_of_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script to create a model of sofa

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the sofa
new_sofa_color = bpy.data.materials.new(name="NewSofaColor")
new_sofa_color.diffuse_color = (0.3, 0.15, 0.15, 1)  # Lighter brown color

# Object-oriented approach to create sofa components
class Sofa:
    def __init__(self, material):
        self.material = material

    def add_base(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        base = bpy.context.object
        base.scale = (2, 1, 0.2)
        base.name = "SofaBase"
        base.data.materials.append(self.material)

    def add_backrest(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.9, 1.1))
        backrest = bpy.context.object
        backrest.scale = (2, 0.2, 0.7)
        backrest.name = "SofaBackrest"
        backrest.data.materials.append(self.material)

    def add_armrests(self):
        for i in range(2):
            bpy.ops.mesh.primitive_cube_add(size=2, location=(2 * (i * 2 - 1), 0, 0.75))
            armrest = bpy.context.object
            armrest.scale = (0.2, 1, 0.5)
            armrest.name = f"SofaArmrest{i + 1}"
            armrest.data.materials.append(self.material)

    def add_cushions(self):
        for i in range(3):
            bpy.ops.mesh.primitive_cube_add(size=2, location=((i - 1) * 1.5, 0, 0.75))
            cushion = bpy.context.object
            cushion.scale = (0.5, 1, 0.2)
            cushion.name = f"SofaCushion{i + 1}"
            cushion.data.materials.append(self.material)

# Instantiate Sofa and create components
sofa = Sofa(new_sofa_color)
sofa.add_base()
sofa.add_backrest()
sofa.add_armrests()
sofa.add_cushions()


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
