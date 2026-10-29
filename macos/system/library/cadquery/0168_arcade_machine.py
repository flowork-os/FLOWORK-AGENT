# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, arcade_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: arcade_machine

from __future__ import annotations

import cadquery as cq
import math

# ===== shim core =====
def _rpy_R(r, p, y):
    """Rotation matrix Rz(yaw)@Ry(pitch)@Rx(roll) as rows (URDF convention)."""
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp,     cp * sr,                cp * cr),
    )

def _mat_mul(A, B):
    return tuple(
        tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )

def _mat_vec(A, v):
    return tuple(sum(A[i][k] * v[k] for k in range(3)) for i in range(3))

class _Tf:
    """Rigid transform: rotation matrix R (rows) + translation t."""
    __slots__ = ("R", "t")
    _I = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    def __init__(self, R=None, t=(0.0, 0.0, 0.0)):
        self.R = R if R is not None else _Tf._I
        self.t = (float(t[0]), float(t[1]), float(t[2]))

    @staticmethod
    def from_origin(origin):
        if origin is None:
            return _Tf()
        xyz = getattr(origin, "xyz", (0.0, 0.0, 0.0))
        rpy = getattr(origin, "rpy", (0.0, 0.0, 0.0))
        return _Tf(_rpy_R(rpy[0], rpy[1], rpy[2]), xyz)

    def __matmul__(self, o):
        return _Tf(_mat_mul(self.R, o.R),
                   tuple(a + b for a, b in zip(_mat_vec(self.R, o.t), self.t)))

    def location(self):
        R, t = self.R, self.t
        xdir = cq.Vector(R[0][0], R[1][0], R[2][0])
        zdir = cq.Vector(R[0][2], R[1][2], R[2][2])
        return cq.Location(cq.Plane(origin=cq.Vector(*t), xDir=xdir, normal=zdir))

class ValidationError(ValueError):
    pass

class ArticulationType:
    REVOLUTE = "revolute"
    CONTINUOUS = "continuous"
    PRISMATIC = "prismatic"
    FIXED = "fixed"
    FLOATING = "floating"

class Origin:
    __slots__ = ("xyz", "rpy")

    def __init__(self, xyz=(0.0, 0.0, 0.0), rpy=(0.0, 0.0, 0.0)):
        self.xyz = (float(xyz[0]), float(xyz[1]), float(xyz[2]))
        self.rpy = (float(rpy[0]), float(rpy[1]), float(rpy[2]))

class Material:
    def __init__(self, name, rgba=None, texture=None, *, color=None):
        self.name = str(name)
        c = rgba if rgba is not None else color
        if c is not None:
            c = tuple(float(v) for v in c)
            if len(c) == 3:
                c = c + (1.0,)
        self.rgba = c
        self.texture = texture

class MotionLimits:
    def __init__(self, effort=1.0, velocity=1.0, lower=None, upper=None):
        self.effort = float(effort)
        self.velocity = float(velocity)
        self.lower = None if lower is None else float(lower)
        self.upper = None if upper is None else float(upper)

class Box:
    __slots__ = ("size",)

    def __init__(self, size):
        self.size = (float(size[0]), float(size[1]), float(size[2]))

    def _cq(self):
        sx, sy, sz = self.size
        return cq.Solid.makeBox(sx, sy, sz, cq.Vector(-sx / 2, -sy / 2, -sz / 2))

def _to_shape(model):
    """Coerce a cadquery object (Workplane/Shape/Assembly) or a shim geometry
    wrapper into a single cq.Shape."""
    if isinstance(model, _CQMesh):
        return model.shape
    if hasattr(model, "_cq"):
        return model._cq()
    if isinstance(model, cq.Assembly):
        return model.toCompound()
    if isinstance(model, cq.Workplane):
        vals = [v for v in model.vals() if isinstance(v, cq.Shape)]
        if not vals:
            raise ValidationError("cadquery Workplane has no shape values")
        return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    if isinstance(model, cq.Shape):
        return model
    raise ValidationError("unsupported cadquery model type: %r" % type(model))

class _CQMesh:
    """Mesh stand-in that simply carries an exact cadquery B-rep shape."""
    __slots__ = ("shape", "name")

    def __init__(self, shape, name=None):
        self.shape = shape
        self.name = name

    def _cq(self):
        return self.shape

def mesh_from_cadquery(model, name=None, **kwargs):
    return _CQMesh(_to_shape(model), name=name if isinstance(name, str) else None)

class Visual:
    __slots__ = ("geometry", "origin", "material", "name")

    def __init__(self, geometry, origin=None, material=None, name=None):
        self.geometry = geometry
        self.origin = origin or Origin()
        self.material = material
        self.name = name

class Part:
    def __init__(self, name, visuals=None, inertial=None, meta=None):
        self.name = name
        self.visuals = list(visuals or [])
        self.collisions = []
        self.inertial = inertial
        self.meta = dict(meta or {})

    def visual(self, geometry, *, origin=None, material=None, color=None, name=None):
        if color is not None and material is None:
            material = color if isinstance(color, (str, Material)) else Material("inline", rgba=color)
        v = Visual(geometry, origin=origin, material=material, name=name)
        self.visuals.append(v)
        return v

    def get_visual(self, name):
        for v in self.visuals:
            if v.name == name:
                return v
        raise ValidationError("unknown visual %r" % name)

class Articulation:
    def __init__(self, name, articulation_type, parent, child, origin=None,
                 axis=(0.0, 0.0, 1.0), motion_limits=None, motion_properties=None,
                 mimic=None, meta=None):
        self.name = name
        self.articulation_type = articulation_type
        self.parent = parent if isinstance(parent, str) else parent.name
        self.child = child if isinstance(child, str) else child.name
        self.origin = origin or Origin()
        self.axis = tuple(float(a) for a in axis)
        self.motion_limits = motion_limits
        self.motion_properties = motion_properties
        self.mimic = mimic
        self.meta = dict(meta or {})

    # aliases used by some scripts
    @property
    def joint_type(self):
        return self.articulation_type

    @property
    def limit(self):
        return self.motion_limits

class ArticulatedObject:
    def __init__(self, name, parts=None, articulations=None, materials=None, meta=None, assets=None):
        self.name = name
        self.parts = list(parts or [])
        self.articulations = list(articulations or [])
        self.materials = list(materials or [])
        self.meta = dict(meta or {})
        self.assets = assets

    # ---- builders ----
    def part(self, name, *, visuals=None, inertial=None, meta=None):
        p = Part(name, visuals=visuals, inertial=inertial, meta=meta)
        self.parts.append(p)
        return p

    link = part

    def articulation(self, name, articulation_type, parent, child, *, origin=None,
                     axis=None, motion_limits=None, motion_properties=None, mimic=None, meta=None):
        a = Articulation(name, articulation_type, parent, child, origin=origin,
                         axis=axis or (0.0, 0.0, 1.0), motion_limits=motion_limits,
                         motion_properties=motion_properties, mimic=mimic, meta=meta)
        self.articulations.append(a)
        return a

    def joint(self, name, joint_type, parent, child, *, origin=None, axis=None,
              limit=None, dynamics=None, mimic=None, meta=None):
        return self.articulation(name, joint_type, parent, child, origin=origin, axis=axis,
                                 motion_limits=limit, motion_properties=dynamics, mimic=mimic, meta=meta)

    def material(self, name, *, rgba=None, color=None, texture=None):
        m = Material(name, rgba=rgba, color=color, texture=texture)
        self.materials.append(m)
        return m

    def set_assets(self, assets):
        self.assets = assets
        return assets

    # ---- queries ----
    def get_part(self, name):
        key = name if isinstance(name, str) else name.name
        for p in self.parts:
            if p.name == key:
                return p
        raise ValidationError("unknown part %r" % name)

    get_link = get_part

    def get_articulation(self, name):
        key = name if isinstance(name, str) else getattr(name, "name", name)
        for a in self.articulations:
            if a.name == key:
                return a
        raise ValidationError("unknown articulation %r" % name)

    get_joint = get_articulation

    def root_parts(self):
        children = {a.child for a in self.articulations}
        return [p for p in self.parts if p.name not in children]

    root_links = root_parts

    def validate(self, *a, **k):
        return None

    def to_urdf(self, *a, **k):
        raise ValidationError("URDF export is not available in self-contained CadQuery mode")

    # ---- rest-pose world transform per part (URDF forward kinematics, q=0) ----
    def _world_transforms(self):
        parent_of, joint_tf = {}, {}
        for a in self.articulations:
            parent_of[a.child] = a.parent
            joint_tf[a.child] = _Tf.from_origin(a.origin)
        cache = {}

        def world(name):
            if name in cache:
                return cache[name]
            if name in parent_of:
                tf = world(parent_of[name]) @ joint_tf[name]
            else:
                tf = _Tf()
            cache[name] = tf
            return tf

        return {p.name: world(p.name) for p in self.parts}

    # ---- assemble to a CadQuery Assembly in rest pose ----
    def to_cq(self):
        worlds = self._world_transforms()
        asm = cq.Assembly(name=self.name or "model")
        idx = 0
        for part in self.parts:
            wt = worlds.get(part.name, _Tf())
            for vis in part.visuals:
                try:
                    shape = _to_shape(vis.geometry)
                except Exception as exc:
                    raise ValidationError(
                        "part %r visual %r: %s" % (part.name, vis.name, exc)
                    )
                loc = (wt @ _Tf.from_origin(vis.origin)).location()
                rgba = None
                mat = vis.material
                if isinstance(mat, str):
                    mat = next((m for m in self.materials if m.name == mat), None)
                if isinstance(mat, Material) and mat.rgba:
                    rgba = mat.rgba
                kw = {"name": "%s_%d" % (part.name, idx)}
                if rgba:
                    kw["color"] = cq.Color(*rgba)
                asm.add(shape, loc=loc, **kw)
                idx += 1
        return asm

    # convenience aliases a few scripts might call
    def to_assembly(self):
        return self.to_cq()

    def compound(self):
        return self.to_cq().toCompound()

# ===== model =====
import math
import cadquery as cq
BODY_WIDTH = 0.82
BODY_REAR_X = -0.74
SCREEN_PITCH = -0.55
SCREEN_CENTER = (0.39, 0.0, 1.21)
SCREEN_SIZE = (0.03, 0.52, 0.33)
SEAT_ORIGIN = (-0.06, 0.0, 0.12)
CONSOLE_ORIGIN = (0.26, 0.0, 0.59)
WHEEL_CENTER = (0.135, 0.0, 0.958)
SHIFTER_PIVOT = (0.20, -0.25, 0.70)
DOOR_WIDTH = 0.42
DOOR_HEIGHT = 0.36
DOOR_THICKNESS = 0.024
DOOR_CENTER_Z = 0.30
DOOR_HINGE_Y = -DOOR_WIDTH / 2.0
def _body_shape() -> cq.Workplane:
    outer_profile = [
        (BODY_REAR_X, 0.00),
        (0.66, 0.00),
        (0.66, 0.12),
        (0.58, 0.32),
        (0.49, 0.86),
        (0.42, 1.24),
        (0.54, 1.62),
        (0.30, 1.70),
        (-0.02, 1.55),
        (-0.26, 1.00),
        (-0.54, 0.68),
        (BODY_REAR_X, 0.54),
    ]
    shell = (
        cq.Workplane("XZ")
        .polyline(outer_profile)
        .close()
        .extrude(BODY_WIDTH / 2.0, both=True)
        .edges("|Y")
        .fillet(0.025)
    )

    cockpit_cut = (
        cq.Workplane("XY")
        .box(1.00, 0.58, 1.10, centered=(True, True, False))
        .translate((-0.08, 0.0, 0.12))
    )
    footwell_cut = (
        cq.Workplane("XY")
        .box(0.28, 0.34, 0.48, centered=(True, True, False))
        .translate((0.19, 0.0, 0.10))
    )
    door_cut = (
        cq.Workplane("XY")
        .box(0.10, DOOR_WIDTH + 0.002, DOOR_HEIGHT + 0.002)
        .translate((BODY_REAR_X + 0.03, 0.0, DOOR_CENTER_Z))
    )
    screen_recess = (
        cq.Workplane("XY")
        .box(0.14, SCREEN_SIZE[1] + 0.08, SCREEN_SIZE[2] + 0.08)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), math.degrees(SCREEN_PITCH))
        .translate(SCREEN_CENTER)
    )

    return shell.cut(cockpit_cut).cut(footwell_cut).cut(door_cut).cut(screen_recess)
def _control_console_shape() -> cq.Workplane:
    deck = (
        cq.Workplane("XY")
        .box(0.32, 0.52, 0.06, centered=(True, True, False))
        .translate((0.0, 0.0, 0.0))
    )
    dash_riser = (
        cq.Workplane("XY")
        .box(0.12, 0.46, 0.10, centered=(True, True, False))
        .translate((0.10, 0.0, 0.06))
    )
    steering_column = (
        cq.Workplane("XY")
        .box(0.18, 0.14, 0.16)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 25.0)
        .translate((-0.01, 0.0, 0.19))
    )
    shifter_boot = (
        cq.Workplane("XY")
        .circle(0.055)
        .extrude(0.04)
        .translate((SHIFTER_PIVOT[0] - CONSOLE_ORIGIN[0], SHIFTER_PIVOT[1], 0.06))
    )
    shifter_flange = (
        cq.Workplane("XY")
        .circle(0.075)
        .extrude(0.010)
        .translate((SHIFTER_PIVOT[0] - CONSOLE_ORIGIN[0], SHIFTER_PIVOT[1], 0.09))
    )
    return (
        deck.union(dash_riser)
        .union(steering_column)
        .union(shifter_boot)
        .union(shifter_flange)
        .edges("|Z")
        .fillet(0.012)
    )
def _seat_shape() -> cq.Workplane:
    pedestal = (
        cq.Workplane("XY")
        .box(0.20, 0.22, 0.25, centered=(True, True, False))
        .translate((0.0, 0.0, 0.0))
    )
    cushion = (
        cq.Workplane("XY")
        .box(0.40, 0.46, 0.12, centered=(True, True, False))
        .translate((0.03, 0.0, 0.25))
    )
    back = (
        cq.Workplane("XY")
        .box(0.12, 0.40, 0.56)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -18.0)
        .translate((-0.10, 0.0, 0.61))
    )
    left_support = (
        cq.Workplane("XY")
        .box(0.16, 0.06, 0.24)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -18.0)
        .translate((-0.04, 0.20, 0.34))
    )
    right_support = (
        cq.Workplane("XY")
        .box(0.16, 0.06, 0.24)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -18.0)
        .translate((-0.04, -0.20, 0.34))
    )
    return (
        pedestal.union(cushion)
        .union(back)
        .union(left_support)
        .union(right_support)
        .edges("|Z")
        .fillet(0.018)
    )
def _door_shape() -> cq.Workplane:
    panel = (
        cq.Workplane("XY")
        .box(DOOR_THICKNESS, DOOR_WIDTH, DOOR_HEIGHT)
        .translate((0.0, DOOR_WIDTH / 2.0, 0.0))
    )
    hinge_barrel = (
        cq.Workplane("XY")
        .circle(0.006)
        .extrude(DOOR_HEIGHT * 0.86)
        .translate((0.0, 0.0, -DOOR_HEIGHT * 0.43))
    )
    handle = (
        cq.Workplane("XY")
        .box(0.04, 0.10, 0.035)
        .translate((-DOOR_THICKNESS / 2.0 - 0.015, DOOR_WIDTH * 0.76, 0.0))
    )
    return panel.union(hinge_barrel).union(handle)
def _wheel_shape() -> cq.Workplane:
    rim = cq.Workplane("YZ").circle(0.18).circle(0.135).extrude(0.018, both=True)
    hub = cq.Workplane("YZ").circle(0.055).extrude(0.03, both=True)
    hub_sleeve = cq.Workplane("YZ").circle(0.040).extrude(0.09)
    top_spoke = cq.Workplane("XY").box(0.028, 0.04, 0.18).translate((0.0, 0.0, 0.09))
    lower_left_spoke = (
        cq.Workplane("XY")
        .box(0.028, 0.16, 0.04)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 34.0)
        .translate((0.0, -0.06, -0.05))
    )
    lower_right_spoke = (
        cq.Workplane("XY")
        .box(0.028, 0.16, 0.04)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -34.0)
        .translate((0.0, 0.06, -0.05))
    )
    return (
        rim.union(hub)
        .union(hub_sleeve)
        .union(top_spoke)
        .union(lower_left_spoke)
        .union(lower_right_spoke)
    )
def _shifter_shape() -> cq.Workplane:
    base = cq.Workplane("XY").circle(0.022).extrude(0.05).translate((0.0, 0.0, -0.01))
    shaft = cq.Workplane("XY").circle(0.010).extrude(0.18).translate((0.0, 0.0, 0.02))
    knob = cq.Workplane("XY").sphere(0.030).translate((0.0, 0.0, 0.22))
    return base.union(shaft).union(knob).rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -12.0)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="sit_down_arcade_cabinet")

    body_finish = model.material("body_finish", rgba=(0.18, 0.20, 0.24, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.08, 0.09, 0.10, 1.0))
    seat_finish = model.material("seat_finish", rgba=(0.12, 0.14, 0.18, 1.0))
    screen_finish = model.material("screen_finish", rgba=(0.03, 0.03, 0.04, 1.0))

    cabinet_body = model.part("cabinet_body")
    cabinet_body.visual(
        mesh_from_cadquery(_body_shape(), "cabinet_body"),
        material=body_finish,
        name="body_shell",
    )

    cabinet_body.visual(
        mesh_from_cadquery(_seat_shape(), "seat"),
        origin=Origin(xyz=SEAT_ORIGIN),
        material=seat_finish,
        name="seat_shell",
    )
    cabinet_body.visual(
        mesh_from_cadquery(_control_console_shape(), "control_console"),
        origin=Origin(xyz=CONSOLE_ORIGIN),
        material=body_finish,
        name="console_shell",
    )
    cabinet_body.visual(
        Box(SCREEN_SIZE),
        origin=Origin(xyz=SCREEN_CENTER, rpy=(0.0, SCREEN_PITCH, 0.0)),
        material=screen_finish,
        name="screen_panel",
    )
    cabinet_body.visual(
        Box((0.14, 0.42, 0.24)),
        origin=Origin(xyz=SCREEN_CENTER, rpy=(0.0, SCREEN_PITCH, 0.0)),
        material=trim_finish,
        name="screen_housing",
    )

    steering_wheel = model.part("steering_wheel")
    steering_wheel.visual(
        mesh_from_cadquery(_wheel_shape(), "steering_wheel"),
        material=trim_finish,
        name="wheel_rim",
    )

    gear_shifter = model.part("gear_shifter")
    gear_shifter.visual(
        mesh_from_cadquery(_shifter_shape(), "gear_shifter"),
        material=trim_finish,
        name="shifter_lever",
    )

    service_door = model.part("service_door")
    service_door.visual(
        mesh_from_cadquery(_door_shape(), "service_door"),
        material=body_finish,
        name="door_panel",
    )

    model.articulation(
        "body_to_steering_wheel",
        ArticulationType.CONTINUOUS,
        parent=cabinet_body,
        child=steering_wheel,
        origin=Origin(xyz=WHEEL_CENTER),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=8.0),
    )
    model.articulation(
        "body_to_gear_shifter",
        ArticulationType.REVOLUTE,
        parent=cabinet_body,
        child=gear_shifter,
        origin=Origin(xyz=SHIFTER_PIVOT),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=5.0, velocity=4.0, lower=-0.30, upper=0.38),
    )
    model.articulation(
        "body_to_service_door",
        ArticulationType.REVOLUTE,
        parent=cabinet_body,
        child=service_door,
        origin=Origin(xyz=(BODY_REAR_X - 0.004, DOOR_HINGE_Y, DOOR_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=6.0, velocity=2.0, lower=0.0, upper=1.55),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
