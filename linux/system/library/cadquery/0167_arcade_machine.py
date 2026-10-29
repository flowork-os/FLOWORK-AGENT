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

class Cylinder:
    __slots__ = ("radius", "length")

    def __init__(self, radius, length=None, *, height=None):
        self.radius = float(radius)
        self.length = float(height if length is None else length)

    @property
    def height(self):
        return self.length

    def _cq(self):
        return cq.Solid.makeCylinder(
            self.radius, self.length, cq.Vector(0, 0, -self.length / 2), cq.Vector(0, 0, 1)
        )

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
CABINET_WIDTH = 0.98
CABINET_LENGTH = 1.80
WALL_THICKNESS = 0.045
DOOR_WIDTH = 0.34
DOOR_HEIGHT = 0.48
DOOR_THICKNESS = 0.026
DOOR_CENTER_Z = 0.56
FLAP_WIDTH = 0.125
FLAP_HEIGHT = 0.055
FLAP_THICKNESS = 0.010
FLAP_CENTER_Z = -0.145
def _cabinet_shell_shape() -> cq.Workplane:
    outer_profile = [
        (0.00, 0.00),
        (CABINET_LENGTH, 0.00),
        (CABINET_LENGTH, 0.68),
        (1.73, 0.92),
        (1.56, 1.16),
        (1.36, 1.40),
        (1.10, 1.62),
        (0.74, 1.73),
        (0.44, 1.68),
        (0.28, 1.50),
        (0.16, 1.10),
        (0.08, 0.90),
        (0.00, 0.72),
    ]

    shell = (
        cq.Workplane("XZ")
        .polyline(outer_profile)
        .close()
        .extrude(CABINET_WIDTH * 0.5, both=True)
        .faces("<Z")
        .shell(-WALL_THICKNESS)
    )

    cockpit_cut = cq.Workplane("XY").box(0.94, 0.70, 1.10).translate((1.20, 0.0, 1.12))
    coin_door_cut = cq.Workplane("XY").box(
        0.16,
        DOOR_WIDTH + 0.002,
        DOOR_HEIGHT + 0.004,
    ).translate((0.07, 0.0, DOOR_CENTER_Z))
    side_entry_cut = cq.Workplane("XY").box(0.46, 0.92, 0.62).translate((1.56, 0.0, 0.63))

    return shell.cut(cockpit_cut).cut(coin_door_cut).cut(side_entry_cut)
def _seat_shape() -> cq.Workplane:
    seat_shell = (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.00, 0.22),
                (0.18, 0.22),
                (0.28, 0.26),
                (0.38, 0.40),
                (0.43, 0.82),
                (0.32, 0.98),
                (0.16, 0.94),
                (0.04, 0.76),
                (-0.02, 0.44),
            ]
        )
        .close()
        .extrude(0.26, both=True)
    )
    pedestal = cq.Workplane("XY").circle(0.060).extrude(0.22).translate((0.16, 0.0, 0.0))
    headrest = cq.Workplane("XY").box(0.10, 0.28, 0.12, centered=(True, True, False)).translate((0.34, 0.0, 0.90))
    return seat_shell.union(pedestal).union(headrest)
def _console_pod_shape() -> cq.Workplane:
    base = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.20, -0.11),
                (0.07, -0.11),
                (0.16, -0.03),
                (0.18, 0.05),
                (0.12, 0.12),
                (-0.02, 0.17),
                (-0.16, 0.10),
            ]
        )
        .close()
        .extrude(0.36, both=True)
    )
    hood = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.11, 0.02),
                (0.06, 0.02),
                (0.13, 0.08),
                (0.12, 0.14),
                (-0.02, 0.18),
                (-0.11, 0.11),
            ]
        )
        .close()
        .extrude(0.20, both=True)
        .translate((0.02, 0.0, 0.01))
    )
    return base.union(hood)
def _steering_wheel_shape() -> cq.Workplane:
    shaft = cq.Workplane("YZ").circle(0.024).extrude(0.16)
    hub = cq.Workplane("YZ").circle(0.055).extrude(0.06).translate((0.10, 0.0, 0.0))
    rim = (
        cq.Workplane("YZ")
        .circle(0.205)
        .circle(0.170)
        .extrude(0.028)
        .translate((0.13, 0.0, 0.0))
    )

    wheel = shaft.union(hub).union(rim)
    for angle_deg in (0.0, 120.0, 240.0):
        spoke = (
            cq.Workplane("YZ")
            .rect(0.032, 0.340)
            .extrude(0.018)
            .translate((0.118, 0.0, 0.0))
            .rotate((0.118, 0.0, 0.0), (1.118, 0.0, 0.0), angle_deg)
        )
        wheel = wheel.union(spoke)
    return wheel
def _coin_door_shape() -> cq.Workplane:
    door = (
        cq.Workplane("YZ")
        .rect(DOOR_WIDTH, DOOR_HEIGHT)
        .extrude(DOOR_THICKNESS)
        .translate((0.0, DOOR_WIDTH * 0.5, 0.0))
    )
    door = door.edges("|X").fillet(0.008)

    service_box = cq.Workplane("XY").box(0.020, 0.11, 0.18).translate((0.010, DOOR_WIDTH * 0.5, 0.10))
    service_slot = cq.Workplane("XY").box(0.040, 0.070, 0.012).translate((0.012, DOOR_WIDTH * 0.5, 0.17))
    flap_opening = cq.Workplane("XY").box(
        DOOR_THICKNESS + 0.020,
        FLAP_WIDTH + 0.001,
        FLAP_HEIGHT + 0.001,
    ).translate((DOOR_THICKNESS * 0.5, DOOR_WIDTH * 0.5, FLAP_CENTER_Z))
    latch_cut = cq.Workplane("XY").box(0.030, 0.050, 0.090).translate((0.012, DOOR_WIDTH * 0.74, 0.02))

    return door.union(service_box).cut(service_slot).cut(flap_opening).cut(latch_cut)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="sitdown_driving_arcade_cabinet")

    shell_blue = model.material("shell_blue", rgba=(0.09, 0.21, 0.59, 1.0))
    trim_black = model.material("trim_black", rgba=(0.10, 0.10, 0.11, 1.0))
    seat_black = model.material("seat_black", rgba=(0.11, 0.11, 0.12, 1.0))
    wheel_black = model.material("wheel_black", rgba=(0.07, 0.07, 0.08, 1.0))
    steel = model.material("steel", rgba=(0.58, 0.60, 0.63, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.27, 0.29, 0.31, 1.0))
    screen_glass = model.material("screen_glass", rgba=(0.05, 0.06, 0.08, 1.0))

    cabinet = model.part("cabinet")
    cabinet.visual(
        mesh_from_cadquery(_cabinet_shell_shape(), "arcade_cabinet_shell"),
        material=shell_blue,
        name="cabinet_shell",
    )
    cabinet.visual(
        Box((1.10, 1.00, 0.05)),
        origin=Origin(xyz=(1.25, 0.0, 0.215)),
        material=trim_black,
        name="floor_pan",
    )
    cabinet.visual(
        mesh_from_cadquery(_console_pod_shape(), "arcade_console_pod"),
        origin=Origin(xyz=(0.50, 0.0, 0.88), rpy=(0.0, -0.30, 0.0)),
        material=trim_black,
        name="console_pod",
    )
    cabinet.visual(
        Cylinder(radius=0.055, length=0.16),
        origin=Origin(xyz=(0.68, 0.0, 0.88), rpy=(0.0, math.pi * 0.5, 0.0)),
        material=trim_black,
        name="column_shroud",
    )
    cabinet.visual(
        Box((0.08, 0.68, 0.45)),
        origin=Origin(xyz=(0.39, 0.0, 1.17), rpy=(0.0, -0.56, 0.0)),
        material=screen_glass,
        name="screen_glass",
    )

    seat = model.part("seat")
    seat.visual(
        mesh_from_cadquery(_seat_shape(), "arcade_seat"),
        material=seat_black,
        name="seat_shell",
    )

    steering_wheel = model.part("steering_wheel")
    steering_wheel.visual(
        mesh_from_cadquery(_steering_wheel_shape(), "arcade_steering_wheel"),
        material=wheel_black,
        name="wheel_assembly",
    )

    coin_door = model.part("coin_door")
    coin_door.visual(
        mesh_from_cadquery(_coin_door_shape(), "arcade_coin_door"),
        material=steel,
        name="door_panel",
    )
    coin_door.visual(
        Cylinder(radius=0.006, length=DOOR_HEIGHT * 0.90),
        origin=Origin(xyz=(-0.003, 0.0, 0.0)),
        material=dark_steel,
        name="door_hinge_barrel",
    )

    coin_return = model.part("coin_return")
    coin_return.visual(
        Box((FLAP_THICKNESS, FLAP_WIDTH, FLAP_HEIGHT)),
        origin=Origin(xyz=(-FLAP_THICKNESS * 0.5, 0.0, -FLAP_HEIGHT * 0.5)),
        material=dark_steel,
        name="flap_panel",
    )

    model.articulation(
        "seat_mount",
        ArticulationType.FIXED,
        parent=cabinet,
        child=seat,
        origin=Origin(xyz=(1.14, 0.0, 0.24)),
    )
    model.articulation(
        "steering_wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=cabinet,
        child=steering_wheel,
        origin=Origin(xyz=(0.76, 0.0, 0.88)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=10.0),
    )
    model.articulation(
        "coin_door_hinge",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=coin_door,
        origin=Origin(xyz=(0.0, -DOOR_WIDTH * 0.5, DOOR_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.4,
            lower=0.0,
            upper=math.radians(78.0),
        ),
    )
    model.articulation(
        "coin_return_hinge",
        ArticulationType.REVOLUTE,
        parent=coin_door,
        child=coin_return,
        origin=Origin(xyz=(0.0005, DOOR_WIDTH * 0.5, FLAP_CENTER_Z + FLAP_HEIGHT * 0.5)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=3.0,
            lower=0.0,
            upper=math.radians(72.0),
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
