# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code__create_a_model_of_power_supply_unit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code, create a model of power supply unit.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials
material_light_gray = bpy.data.materials.new(name='MaterialLightGray')
material_light_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

material_black = bpy.data.materials.new(name='MaterialBlack')
material_black.diffuse_color = (0, 0, 0, 1)

# Class to create the PSU
class PowerSupplyUnit:
    def __init__(self):
        self.create_body()
        self.create_fan()
        self.create_switch()
        self.create_port()
        self.add_ventilation_holes()
        self.create_label()

    def create_body(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        body = bpy.context.object
        body.name = 'MainBody'
        body.scale = (1.5, 1, 0.5)
        body.data.materials.append(material_light_gray)

    def create_fan(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.1, location=(1.5, 0, 0))
        fan = bpy.context.object
        fan.name = 'Fan'
        fan.rotation_euler = (0, 1.5708, 0)
        fan.data.materials.append(material_black)

    def create_switch(self):
        bpy.ops.mesh.primitive_cube_add(size=0.2, location=(-1.5, 0.4, 0.2))
        switch = bpy.context.object
        switch.name = 'PowerSwitch'
        switch.data.materials.append(material_black)

    def create_port(self):
        bpy.ops.mesh.primitive_cube_add(size=0.3, location=(-1.5, -0.4, 0.2))
        port = bpy.context.object
        port.name = 'PowerPort'
        port.data.materials.append(material_black)

    def add_ventilation_holes(self):
        for i in range(-5, 6):
            for j in range(-2, 3):
                bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.1, location=(i * 0.3, j * 0.3, 0.5))
                vent = bpy.context.object
                vent.name = f'VentilationTop_{i}_{j}'
                vent.rotation_euler = (1.5708, 0, 0)
                vent.data.materials.append(material_black)

        for i in range(-3, 4):
            for j in range(-1, 2):
                bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.1, location=(1.5, i * 0.3, j * 0.3))
                vent = bpy.context.object
                vent.name = f'VentilationSide_{i}_{j}'
                vent.rotation_euler = (0, 1.5708, 0)
                vent.data.materials.append(material_black)

    def create_label(self):
        bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, -1.01, 0))
        label = bpy.context.object
        label.name = 'Label'
        label.rotation_euler = (1.5708, 0, 0)
        label.data.materials.append(material_light_gray)

        bpy.ops.object.text_add(location=(0, -1.01, 0.1))
        label_text = bpy.context.object
        label_text.name = 'LabelText'
        label_text.data.body = 'Voltage: 230V\nWattage: 500W'
        label_text.rotation_euler = (1.5708, 0, 0)
        label_text.scale = (0.1, 0.1, 0.1)
        label_text.data.materials.append(material_black)

# Instantiate the power supply unit
PowerSupplyUnit()


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
