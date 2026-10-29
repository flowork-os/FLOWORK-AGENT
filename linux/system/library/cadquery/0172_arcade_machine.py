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
CABINET_WIDTH = 0.84
BASE_DEPTH = 1.78
BASE_HEIGHT = 0.05
DASH_ANGLE = math.radians(22.0)
DASH_ANGLE_DEG = math.degrees(DASH_ANGLE)
DASH_Y = 0.73
DASH_Z = 0.76
BUTTON_XS = (-0.15, -0.05, 0.05, 0.15)
BUTTON_CAP_WIDTH = 0.052
BUTTON_CAP_DEPTH = 0.030
BUTTON_CAP_HEIGHT = 0.010
BUTTON_STEM_WIDTH = 0.024
BUTTON_STEM_DEPTH = 0.012
BUTTON_STEM_HEIGHT = 0.042
BUTTON_TRAVEL = 0.008
COIN_DOOR_WIDTH = 0.29
COIN_DOOR_HEIGHT = 0.41
COIN_DOOR_THICKNESS = 0.018
COIN_OPENING_WIDTH = 0.26
COIN_OPENING_HEIGHT = 0.38
COIN_DOOR_BOTTOM = 0.13
STEERING_TILT = math.radians(40.0)
STEERING_CENTER = (0.0, 1.09, 0.87)
def _build_cabinet_shell() -> cq.Workplane:
    base = (
        cq.Workplane("XY")
        .box(CABINET_WIDTH, BASE_DEPTH, BASE_HEIGHT)
        .translate((0.0, BASE_DEPTH / 2.0, BASE_HEIGHT / 2.0))
    )

    front_profile_yz = [
        (0.00, 0.00),
        (0.00, 0.80),
        (0.10, 0.82),
        (0.22, 1.10),
        (0.37, 1.42),
        (0.51, 1.60),
        (0.77, 1.60),
        (0.89, 1.38),
        (0.93, 1.10),
        (0.94, 0.86),
        (0.80, 0.81),
        (0.62, 0.77),
        (0.32, 0.71),
        (0.10, 0.66),
        (0.00, 0.60),
    ]
    front_profile = [(z_pos, y_pos) for y_pos, z_pos in front_profile_yz]
    front_body = (
        cq.Workplane("YZ")
        .polyline(front_profile)
        .close()
        .extrude(CABINET_WIDTH * 0.48, both=True)
    )

    pod_profile_yz = [
        (0.68, 0.00),
        (0.74, 0.16),
        (0.86, 0.40),
        (1.02, 0.52),
        (1.24, 0.58),
        (1.43, 0.70),
        (1.59, 0.92),
        (1.72, 1.00),
        (1.78, 0.90),
        (1.78, 0.08),
    ]
    pod_profile = [(z_pos, y_pos) for y_pos, z_pos in pod_profile_yz]
    seat_pod = (
        cq.Workplane("YZ")
        .polyline(pod_profile)
        .close()
        .extrude(CABINET_WIDTH * 0.5, both=True)
    )

    shell = base.union(front_body).union(seat_pod)

    cockpit_cut = (
        cq.Workplane("XY")
        .box(0.46, 0.74, 0.68)
        .translate((0.0, 1.25, 0.64))
    )
    footwell_cut = (
        cq.Workplane("XY")
        .box(0.34, 0.58, 0.34)
        .translate((0.0, 0.98, 0.40))
    )
    coin_opening = (
        cq.Workplane("XY")
        .box(COIN_OPENING_WIDTH, 0.18, COIN_OPENING_HEIGHT)
        .translate((0.0, 0.09, COIN_DOOR_BOTTOM + COIN_OPENING_HEIGHT / 2.0))
    )
    shell = shell.cut(cockpit_cut).cut(footwell_cut).cut(coin_opening)

    for button_x in BUTTON_XS:
        slot = (
            cq.Workplane("XY")
            .box(0.030, 0.018, 0.090)
            .translate((0.0, 0.0, -0.044))
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -DASH_ANGLE_DEG)
            .translate((button_x, DASH_Y, DASH_Z))
        )
        shell = shell.cut(slot)

    return shell
def _build_button_shape() -> cq.Workplane:
    bezel = (
        cq.Workplane("XY")
        .box(0.036, 0.022, 0.002)
        .translate((0.0, 0.0, 0.001))
    )
    cap = (
        cq.Workplane("XY")
        .box(BUTTON_CAP_WIDTH, BUTTON_CAP_DEPTH, BUTTON_CAP_HEIGHT)
        .translate((0.0, 0.0, 0.002 + BUTTON_CAP_HEIGHT / 2.0))
    )
    stem = (
        cq.Workplane("XY")
        .box(BUTTON_STEM_WIDTH, BUTTON_STEM_DEPTH, BUTTON_STEM_HEIGHT)
        .translate((0.0, 0.0, 0.002 - BUTTON_STEM_HEIGHT / 2.0))
    )
    return bezel.union(cap).union(stem)
def _build_dash_plate() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .box(0.44, 0.16, 0.14)
        .translate((0.0, 0.0, -0.07))
    )
    for button_x in BUTTON_XS:
        slot = (
            cq.Workplane("XY")
            .box(0.028, 0.018, 0.060)
            .translate((button_x, 0.0, -0.030))
        )
        plate = plate.cut(slot)
    return plate
def _build_coin_door() -> cq.Workplane:
    panel = (
        cq.Workplane("XY")
        .box(COIN_DOOR_WIDTH, COIN_DOOR_THICKNESS, COIN_DOOR_HEIGHT)
        .translate((COIN_DOOR_WIDTH / 2.0, -COIN_DOOR_THICKNESS / 2.0, COIN_DOOR_HEIGHT / 2.0))
    )
    panel_recess = (
        cq.Workplane("XY")
        .box(COIN_DOOR_WIDTH - 0.050, COIN_DOOR_THICKNESS * 0.48, COIN_DOOR_HEIGHT - 0.070)
        .translate((COIN_DOOR_WIDTH / 2.0, -COIN_DOOR_THICKNESS * 0.72, COIN_DOOR_HEIGHT / 2.0))
    )
    ticket_boss = (
        cq.Workplane("XY")
        .box(0.082, COIN_DOOR_THICKNESS * 0.55, 0.044)
        .translate((COIN_DOOR_WIDTH * 0.35, -COIN_DOOR_THICKNESS * 0.64, COIN_DOOR_HEIGHT * 0.62))
    )
    pull_handle = (
        cq.Workplane("XY")
        .box(0.024, COIN_DOOR_THICKNESS * 0.72, 0.110)
        .translate((COIN_DOOR_WIDTH * 0.82, -COIN_DOOR_THICKNESS * 0.64, COIN_DOOR_HEIGHT * 0.34))
    )
    coin_slot = (
        cq.Workplane("XY")
        .box(0.060, COIN_DOOR_THICKNESS * 0.60, 0.010)
        .translate((COIN_DOOR_WIDTH * 0.34, -COIN_DOOR_THICKNESS * 0.72, COIN_DOOR_HEIGHT * 0.82))
    )
    lock_cylinder = (
        cq.Workplane("XZ")
        .circle(0.008)
        .extrude(COIN_DOOR_THICKNESS * 0.62)
        .translate((COIN_DOOR_WIDTH * 0.78, -COIN_DOOR_THICKNESS * 0.76, COIN_DOOR_HEIGHT * 0.48))
    )
    return panel.cut(panel_recess).cut(coin_slot).union(ticket_boss).union(pull_handle).union(lock_cylinder)
def _build_coin_frame() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .box(0.33, 0.18, 0.45)
        .translate((0.0, 0.09, 0.0))
    )
    inner = (
        cq.Workplane("XY")
        .box(COIN_OPENING_WIDTH, 0.20, COIN_OPENING_HEIGHT)
        .translate((0.0, 0.10, 0.0))
    )
    return outer.cut(inner)
def _build_steering_wheel() -> cq.Workplane:
    ring = cq.Workplane("XY").circle(0.18).circle(0.145).extrude(0.028, both=True)
    hub = cq.Workplane("XY").circle(0.045).extrude(0.036, both=True)
    wheel = ring.union(hub)
    for angle in (0.0, 120.0, 240.0):
        spoke = (
            cq.Workplane("XY")
            .transformed(rotate=(0.0, 0.0, angle))
            .center(0.092, 0.0)
            .rect(0.118, 0.020)
            .extrude(0.018, both=True)
        )
        wheel = wheel.union(spoke)
    return wheel
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="sit_down_arcade_racer")

    cabinet_finish = model.material("cabinet_finish", rgba=(0.10, 0.16, 0.28, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.08, 0.08, 0.09, 1.0))
    seat_finish = model.material("seat_finish", rgba=(0.16, 0.16, 0.17, 1.0))
    wheel_finish = model.material("wheel_finish", rgba=(0.06, 0.06, 0.06, 1.0))
    glass_finish = model.material("glass_finish", rgba=(0.09, 0.15, 0.18, 0.55))
    metal_finish = model.material("metal_finish", rgba=(0.56, 0.58, 0.62, 1.0))
    button_red = model.material("button_red", rgba=(0.88, 0.14, 0.16, 0.95))
    button_amber = model.material("button_amber", rgba=(0.95, 0.60, 0.10, 0.95))
    button_green = model.material("button_green", rgba=(0.20, 0.82, 0.34, 0.95))
    button_blue = model.material("button_blue", rgba=(0.16, 0.56, 0.96, 0.95))

    cabinet = model.part("cabinet")
    cabinet.visual(
        mesh_from_cadquery(_build_cabinet_shell(), "arcade_cabinet_shell"),
        material=cabinet_finish,
        name="shell",
    )
    cabinet.visual(
        Box((0.37, 0.36, 0.20)),
        origin=Origin(xyz=(0.0, 1.24, 0.31)),
        material=trim_finish,
        name="seat_pedestal",
    )
    cabinet.visual(
        Box((0.43, 0.40, 0.09)),
        origin=Origin(xyz=(0.0, 1.22, 0.45)),
        material=seat_finish,
        name="seat_base",
    )
    cabinet.visual(
        Box((0.41, 0.14, 0.54)),
        origin=Origin(xyz=(0.0, 1.43, 0.72), rpy=(-0.30, 0.0, 0.0)),
        material=seat_finish,
        name="seat_back",
    )
    cabinet.visual(
        Box((0.64, 0.22, 0.52)),
        origin=Origin(xyz=(0.0, 0.56, 1.02), rpy=(-0.20, 0.0, 0.0)),
        material=trim_finish,
        name="screen_shroud",
    )
    cabinet.visual(
        Box((0.50, 0.04, 0.32)),
        origin=Origin(xyz=(0.0, 0.49, 1.06), rpy=(-0.20, 0.0, 0.0)),
        material=glass_finish,
        name="screen",
    )
    cabinet.visual(
        mesh_from_cadquery(_build_dash_plate(), "arcade_dash_plate"),
        origin=Origin(xyz=(0.0, DASH_Y, DASH_Z), rpy=(-DASH_ANGLE, 0.0, 0.0)),
        material=trim_finish,
        name="dash_plate",
    )
    cabinet.visual(
        mesh_from_cadquery(_build_coin_frame(), "arcade_coin_frame"),
        origin=Origin(xyz=(0.0, 0.0, COIN_DOOR_BOTTOM + COIN_DOOR_HEIGHT / 2.0)),
        material=trim_finish,
        name="coin_frame",
    )
    cabinet.visual(
        Cylinder(radius=0.035, length=0.28),
        origin=Origin(xyz=(0.0, 0.99, 0.75), rpy=(-STEERING_TILT, 0.0, 0.0)),
        material=trim_finish,
        name="steering_column",
    )

    steering_wheel = model.part("steering_wheel")
    steering_wheel.visual(
        mesh_from_cadquery(_build_steering_wheel(), "arcade_steering_wheel"),
        material=wheel_finish,
        name="wheel",
    )
    model.articulation(
        "cabinet_to_steering_wheel",
        ArticulationType.CONTINUOUS,
        parent=cabinet,
        child=steering_wheel,
        origin=Origin(xyz=STEERING_CENTER, rpy=(-STEERING_TILT, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=8.0,
        ),
    )

    coin_door = model.part("coin_door")
    coin_door.visual(
        mesh_from_cadquery(_build_coin_door(), "arcade_coin_door"),
        material=metal_finish,
        name="door_panel",
    )
    model.articulation(
        "cabinet_to_coin_door",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=coin_door,
        origin=Origin(
            xyz=(
                -COIN_DOOR_WIDTH / 2.0,
                0.0,
                COIN_DOOR_BOTTOM,
            )
        ),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.6,
            lower=0.0,
            upper=1.35,
        ),
    )

    button_mesh = mesh_from_cadquery(_build_button_shape(), "arcade_gear_button")
    button_finishes = (button_red, button_amber, button_green, button_blue)
    for index, (button_x, finish) in enumerate(zip(BUTTON_XS, button_finishes)):
        button_part = model.part(f"gear_button_{index}")
        button_part.visual(
            button_mesh,
            material=finish,
            name="button",
        )
        model.articulation(
            f"cabinet_to_gear_button_{index}",
            ArticulationType.PRISMATIC,
            parent=cabinet,
            child=button_part,
            origin=Origin(xyz=(button_x, DASH_Y, DASH_Z), rpy=(-DASH_ANGLE, 0.0, 0.0)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=8.0,
                velocity=0.08,
                lower=0.0,
                upper=BUTTON_TRAVEL,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
