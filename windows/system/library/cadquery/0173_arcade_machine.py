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

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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
CABINET_WIDTH = 0.79
CABINET_DEPTH = 0.88
CABINET_HEIGHT = 1.74
SIDE_CLEAR = 0.03
DOOR_WIDTH = 0.33
DOOR_HEIGHT = 0.46
DOOR_THICKNESS = 0.024
DOOR_BOTTOM = 0.10
MONITOR_TILT_DEG = 18.0
MONITOR_CENTER_Y = 0.36
MONITOR_CENTER_Z = 1.31
DECK_WIDTH = 0.66
DECK_DEPTH = 0.30
DECK_THICKNESS = 0.055
DECK_MOUNT_Y = 0.075
DECK_MOUNT_Z = 0.99
DECK_TILT_DEG = 12.0
JOYSTICK_X = -0.17
JOYSTICK_Y = -0.13
JOYSTICK_PIVOT_Z = -0.038
def _body_shell_shape():
    outer_profile = [
        (0.06, 0.00),
        (CABINET_DEPTH, 0.00),
        (CABINET_DEPTH, CABINET_HEIGHT),
        (0.56, CABINET_HEIGHT),
        (0.42, 1.60),
        (0.28, 1.08),
        (0.12, 1.00),
        (0.00, 0.90),
        (0.06, 0.82),
        (0.06, 0.00),
    ]
    inner_profile = [
        (0.12, 0.06),
        (CABINET_DEPTH - 0.04, 0.06),
        (CABINET_DEPTH - 0.04, CABINET_HEIGHT - 0.05),
        (0.58, CABINET_HEIGHT - 0.05),
        (0.46, 1.56),
        (0.35, 1.18),
        (0.21, 1.11),
        (0.12, 0.98),
        (0.16, 0.86),
        (0.16, 0.06),
    ]

    shell = (
        cq.Workplane("YZ")
        .polyline(outer_profile)
        .close()
        .extrude(CABINET_WIDTH / 2.0, both=True)
        .cut(
            cq.Workplane("YZ")
            .polyline(inner_profile)
            .close()
            .extrude((CABINET_WIDTH - 2.0 * SIDE_CLEAR) / 2.0, both=True)
        )
    )

    service_opening = cq.Workplane("XY").box(
        DOOR_WIDTH + 0.018,
        0.14,
        DOOR_HEIGHT + 0.024,
    ).translate((0.0, 0.072, DOOR_BOTTOM + DOOR_HEIGHT / 2.0))

    monitor_opening = (
        cq.Workplane("XY")
        .box(0.50, 0.18, 0.38)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -MONITOR_TILT_DEG)
        .translate((0.0, MONITOR_CENTER_Y, MONITOR_CENTER_Z))
    )

    return shell.cut(service_opening).cut(monitor_opening)
def _monitor_bezel_shape():
    frame = (
        cq.Workplane("XY")
        .box(0.58, 0.045, 0.46)
        .cut(cq.Workplane("XY").box(0.48, 0.12, 0.34))
    )
    visor = cq.Workplane("XY").box(0.64, 0.04, 0.05).translate((0.0, -0.02, 0.255))
    return frame.union(visor)
def _control_deck_shape():
    deck = cq.Workplane("XY").box(DECK_WIDTH, DECK_DEPTH, DECK_THICKNESS).translate(
        (0.0, -DECK_DEPTH / 2.0, -DECK_THICKNESS / 2.0)
    )
    front_apron = cq.Workplane("XY").box(DECK_WIDTH, 0.024, 0.075).translate(
        (0.0, -DECK_DEPTH + 0.012, -0.0375)
    )
    joystick_opening = (
        cq.Workplane("XY")
        .circle(0.019)
        .extrude(0.12)
        .translate((JOYSTICK_X, JOYSTICK_Y, -0.12))
    )
    return deck.union(front_apron).cut(joystick_opening)
def _stick_support_shape():
    top_ring = (
        cq.Workplane("XY")
        .circle(0.028)
        .circle(0.0185)
        .extrude(0.006)
        .translate((JOYSTICK_X, JOYSTICK_Y, -0.003))
    )
    lower_collar = (
        cq.Workplane("XY")
        .circle(0.022)
        .circle(0.013)
        .extrude(0.028)
        .translate((JOYSTICK_X, JOYSTICK_Y, -0.030))
    )
    return top_ring.union(lower_collar)
def _roll_yz(y_value: float, z_value: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return (
        y_value * math.cos(angle) - z_value * math.sin(angle),
        y_value * math.sin(angle) + z_value * math.cos(angle),
    )
def _deck_world(x_value: float, y_value: float, z_value: float = 0.0) -> tuple[float, float, float]:
    dy, dz = _roll_yz(y_value, z_value, DECK_TILT_DEG)
    return (x_value, DECK_MOUNT_Y + dy, DECK_MOUNT_Z + dz)
def _monitor_world(x_value: float, y_value: float, z_value: float = 0.0) -> tuple[float, float, float]:
    dy, dz = _roll_yz(y_value, z_value, -MONITOR_TILT_DEG)
    return (x_value, MONITOR_CENTER_Y + dy, MONITOR_CENTER_Z + dz)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="upright_arcade_cabinet")

    cabinet_finish = model.material("cabinet_finish", rgba=(0.11, 0.11, 0.12, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.16, 0.02, 0.02, 1.0))
    deck_finish = model.material("deck_finish", rgba=(0.08, 0.08, 0.09, 1.0))
    metal_finish = model.material("metal_finish", rgba=(0.60, 0.61, 0.64, 1.0))
    dark_metal = model.material("dark_metal", rgba=(0.22, 0.23, 0.25, 1.0))
    screen_finish = model.material("screen_finish", rgba=(0.03, 0.04, 0.05, 1.0))
    button_red = model.material("button_red", rgba=(0.76, 0.10, 0.12, 1.0))
    button_yellow = model.material("button_yellow", rgba=(0.88, 0.72, 0.12, 1.0))
    button_blue = model.material("button_blue", rgba=(0.18, 0.34, 0.78, 1.0))
    button_green = model.material("button_green", rgba=(0.16, 0.55, 0.22, 1.0))
    ball_finish = model.material("ball_finish", rgba=(0.75, 0.08, 0.10, 1.0))
    coin_finish = model.material("coin_finish", rgba=(0.25, 0.26, 0.28, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shell_shape(), "arcade_body"),
        material=cabinet_finish,
        name="shell",
    )
    body.visual(
        Box((0.30, 0.028, 0.18)),
        origin=Origin(xyz=(0.0, 0.074, 0.68)),
        material=coin_finish,
        name="coin_panel",
    )
    body.visual(
        Box((0.055, 0.010, 0.015)),
        origin=Origin(xyz=(-0.075, 0.063, 0.74)),
        material=metal_finish,
        name="coin_slot_0",
    )
    body.visual(
        Box((0.055, 0.010, 0.015)),
        origin=Origin(xyz=(0.075, 0.063, 0.74)),
        material=metal_finish,
        name="coin_slot_1",
    )

    body.visual(
        mesh_from_cadquery(_monitor_bezel_shape(), "monitor_bezel"),
        origin=Origin(
            xyz=_monitor_world(0.0, 0.0, 0.0),
            rpy=(math.radians(-MONITOR_TILT_DEG), 0.0, 0.0),
        ),
        material=trim_finish,
        name="bezel",
    )
    body.visual(
        Box((0.50, 0.018, 0.38)),
        origin=Origin(
            xyz=_monitor_world(0.0, 0.016, 0.0),
            rpy=(math.radians(-MONITOR_TILT_DEG), 0.0, 0.0),
        ),
        material=screen_finish,
        name="screen",
    )

    body.visual(
        mesh_from_cadquery(_control_deck_shape(), "control_deck"),
        origin=Origin(
            xyz=_deck_world(0.0, 0.0, 0.0),
            rpy=(math.radians(DECK_TILT_DEG), 0.0, 0.0),
        ),
        material=deck_finish,
        name="deck_shell",
    )
    body.visual(
        mesh_from_cadquery(_stick_support_shape(), "stick_support"),
        origin=Origin(
            xyz=_deck_world(0.0, 0.0, 0.0),
            rpy=(math.radians(DECK_TILT_DEG), 0.0, 0.0),
        ),
        material=dark_metal,
        name="stick_support",
    )

    button_positions = [
        ((0.11, -0.18), button_red),
        ((0.17, -0.15), button_yellow),
        ((0.23, -0.12), button_blue),
        ((0.29, -0.09), button_green),
    ]
    for index, ((x_pos, y_pos), cap_material) in enumerate(button_positions):
        body.visual(
            Cylinder(radius=0.014, length=0.028),
            origin=Origin(
                xyz=_deck_world(x_pos, y_pos, -0.008),
                rpy=(math.radians(DECK_TILT_DEG), 0.0, 0.0),
            ),
            material=dark_metal,
            name=f"button_barrel_{index}",
        )
        body.visual(
            Cylinder(radius=0.022, length=0.012),
            origin=Origin(
                xyz=_deck_world(x_pos, y_pos, 0.006),
                rpy=(math.radians(DECK_TILT_DEG), 0.0, 0.0),
            ),
            material=cap_material,
            name=f"button_cap_{index}",
        )

    door = model.part("door")
    door.visual(
        Box((DOOR_WIDTH + 0.026, 0.006, DOOR_HEIGHT + 0.030)),
        origin=Origin(
            xyz=((DOOR_WIDTH + 0.026) / 2.0, -0.003, (DOOR_HEIGHT + 0.030) / 2.0),
        ),
        material=trim_finish,
        name="door_flange",
    )
    door.visual(
        Box((DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT)),
        origin=Origin(xyz=(DOOR_WIDTH / 2.0, DOOR_THICKNESS / 2.0, DOOR_HEIGHT / 2.0)),
        material=cabinet_finish,
        name="door_panel",
    )
    door.visual(
        Box((0.026, 0.012, 0.10)),
        origin=Origin(xyz=(DOOR_WIDTH - 0.050, -0.006, 0.24)),
        material=metal_finish,
        name="door_pull",
    )
    door.visual(
        Box((0.018, 0.008, 0.018)),
        origin=Origin(xyz=(DOOR_WIDTH - 0.030, -0.004, 0.35)),
        material=metal_finish,
        name="door_lock",
    )
    model.articulation(
        "body_to_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=door,
        origin=Origin(xyz=(-DOOR_WIDTH / 2.0, 0.061, DOOR_BOTTOM)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.35, effort=12.0, velocity=1.2),
    )

    stick = model.part("stick")
    stick.visual(
        Sphere(radius=0.010),
        material=dark_metal,
        name="hub",
    )
    stick.visual(
        Cylinder(radius=0.0132, length=0.032),
        origin=Origin(xyz=(0.0, 0.0, -0.014)),
        material=dark_metal,
        name="pivot_boss",
    )
    stick.visual(
        Cylinder(radius=0.008, length=0.210),
        origin=Origin(xyz=(0.0, 0.0, 0.090)),
        material=metal_finish,
        name="shaft",
    )
    stick.visual(
        Sphere(radius=0.028),
        origin=Origin(xyz=(0.0, 0.0, 0.214)),
        material=ball_finish,
        name="ball_top",
    )
    stick.visual(
        Cylinder(radius=0.006, length=0.050),
        origin=Origin(xyz=(0.0, 0.0, -0.035)),
        material=dark_metal,
        name="actuator",
    )
    model.articulation(
        "body_to_stick",
        ArticulationType.REVOLUTE,
        parent=body,
        child=stick,
        origin=Origin(
            xyz=_deck_world(JOYSTICK_X, JOYSTICK_Y, JOYSTICK_PIVOT_Z),
            rpy=(math.radians(DECK_TILT_DEG), 0.0, 0.0),
        ),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=-0.35, upper=0.35, effort=4.0, velocity=3.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
