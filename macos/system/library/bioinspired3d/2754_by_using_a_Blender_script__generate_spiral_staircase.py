# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__generate_spiral_staircase" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, generate spiral staircase

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj

central_pole = create_cylinder(0.1, 5, (0, 0, 2.5), 'Main Pole')

num_steps = 20
step_height = 0.2
step_radius = 1.0

for i in range(num_steps):
    theta = i * (2 * math.pi / num_steps)
    x = step_radius * math.cos(theta)
    y = step_radius * math.sin(theta)
    z = i * step_height
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, z))
    step = bpy.context.object
    step.name = f'Step {i + 1}'
    step.rotation_euler[2] = theta

bpy.ops.curve.primitive_bezier_circle_add(radius=0.05)
braided_circle = bpy.context.object
braided_circle.name = 'Handrail Shape'

bpy.ops.curve.primitive_bezier_curve_add()
handrail_curve = bpy.context.object
handrail_curve.name = 'Handrail Route'
handrail_curve.data.splines.clear()

spline = handrail_curve.data.splines.new(type='BEZIER')
spline.bezier_points.add(num_steps - 1)

for i in range(num_steps):
    theta = i * (2 * math.pi / num_steps)
    x = (step_radius + 0.25) * math.cos(theta)
    y = (step_radius + 0.25) * math.sin(theta)
    z = i * step_height
    spline.bezier_points[i].co = (x, y, z)
    spline.bezier_points[i].handle_left_type = 'AUTO'
    spline.bezier_points[i].handle_right_type = 'AUTO'

handrail_curve.data.bevel_object = braided_circle
handrail_curve.data.fill_mode = 'FULL'
