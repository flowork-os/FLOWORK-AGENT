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
CABINET_WIDTH = 0.82
DOOR_WIDTH = 0.42
DOOR_HEIGHT = 0.34
DOOR_THICKNESS = 0.018
DOOR_CENTER_Z = 0.45
DOOR_AXIS_Y = 0.389
FLAP_WIDTH = 0.075
FLAP_HEIGHT = 0.045
FLAP_THICKNESS = 0.012
FLAP_CENTER_X = 0.145
FLAP_TOP_Z = 0.722
FLAP_AXIS_Y = 0.402
CONTROL_PANEL_ANGLE = math.atan2(0.12, 0.19)
SCREEN_ANGLE = math.atan2(0.06, 0.26)
def _cabinet_mesh() -> object:
    side_profile = [
        (-0.37, 0.00),
        (0.39, 0.00),
        (0.39, 0.92),
        (0.27, 0.97),
        (0.08, 1.09),
        (0.02, 1.23),
        (-0.04, 1.49),
        (-0.02, 1.63),
        (-0.15, 1.74),
        (-0.37, 1.74),
    ]

    shell = (
        cq.Workplane("YZ")
        .polyline(side_profile)
        .close()
        .extrude(CABINET_WIDTH / 2.0, both=True)
    )

    door_opening = (
        cq.Workplane("XY")
        .transformed(offset=(0.0, 0.31, DOOR_CENTER_Z))
        .box(DOOR_WIDTH + 0.028, 0.16, DOOR_HEIGHT + 0.04)
    )

    return shell.cut(door_opening)
def _panel_normal_offset(distance: float) -> tuple[float, float]:
    return (
        math.sin(CONTROL_PANEL_ANGLE) * distance,
        math.cos(CONTROL_PANEL_ANGLE) * distance,
    )
def _control_panel_y(z_pos: float) -> float:
    z0 = 0.97
    y0 = 0.27
    slope = -0.19 / 0.12
    return y0 + (z_pos - z0) * slope
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="upright_arcade_machine")

    cabinet_finish = model.material("cabinet_finish", rgba=(0.09, 0.09, 0.10, 1.0))
    bezel_finish = model.material("bezel_finish", rgba=(0.03, 0.03, 0.04, 1.0))
    screen_finish = model.material("screen_finish", rgba=(0.06, 0.08, 0.12, 1.0))
    marquee_finish = model.material("marquee_finish", rgba=(0.82, 0.72, 0.22, 1.0))
    coin_finish = model.material("coin_finish", rgba=(0.56, 0.58, 0.62, 1.0))
    door_finish = model.material("door_finish", rgba=(0.54, 0.08, 0.10, 1.0))
    joystick_finish = model.material("joystick_finish", rgba=(0.85, 0.10, 0.12, 1.0))
    joystick_alt = model.material("joystick_alt", rgba=(0.10, 0.35, 0.80, 1.0))
    button_finish = model.material("button_finish", rgba=(0.90, 0.90, 0.92, 1.0))

    cabinet = model.part("cabinet")
    cabinet.visual(
        mesh_from_cadquery(_cabinet_mesh(), "arcade_cabinet_shell"),
        material=cabinet_finish,
        name="cabinet_shell",
    )

    cabinet.visual(
        Box((0.64, 0.020, 0.48)),
        origin=Origin(xyz=(0.0, -0.008, 1.36), rpy=(SCREEN_ANGLE, 0.0, 0.0)),
        material=bezel_finish,
        name="screen_bezel",
    )
    cabinet.visual(
        Box((0.55, 0.010, 0.40)),
        origin=Origin(xyz=(0.0, -0.003, 1.36), rpy=(SCREEN_ANGLE, 0.0, 0.0)),
        material=screen_finish,
        name="screen_glass",
    )
    cabinet.visual(
        Box((0.70, 0.016, 0.20)),
        origin=Origin(xyz=(0.0, -0.010, 1.60), rpy=(0.10, 0.0, 0.0)),
        material=marquee_finish,
        name="marquee_panel",
    )
    cabinet.visual(
        Box((0.18, 0.004, 0.10)),
        origin=Origin(xyz=(0.11, 0.392, 0.72)),
        material=coin_finish,
        name="coin_plate",
    )
    cabinet.visual(
        Box((0.070, 0.003, 0.007)),
        origin=Origin(xyz=(0.075, 0.394, 0.758)),
        material=bezel_finish,
        name="coin_slot",
    )
    cabinet.visual(
        Box((0.030, 0.016, 0.320)),
        origin=Origin(xyz=(-0.225, 0.381, DOOR_CENTER_Z)),
        material=bezel_finish,
        name="door_jamb",
    )

    joystick_surface_z = 1.03
    joystick_surface_y = _control_panel_y(joystick_surface_z)
    washer_y_off, washer_z_off = _panel_normal_offset(0.0)
    shaft_y_off, shaft_z_off = _panel_normal_offset(0.058)
    ball_y_off, ball_z_off = _panel_normal_offset(0.133)
    for index, x_pos in enumerate((-0.22, 0.22)):
        ball_material = joystick_finish if index == 0 else joystick_alt
        cabinet.visual(
            Cylinder(radius=0.036, length=0.003),
            origin=Origin(
                xyz=(x_pos, joystick_surface_y + washer_y_off, joystick_surface_z + washer_z_off),
                rpy=(-CONTROL_PANEL_ANGLE, 0.0, 0.0),
            ),
            material=bezel_finish,
            name=f"joystick_{index}_washer",
        )
        cabinet.visual(
            Cylinder(radius=0.0065, length=0.120),
            origin=Origin(
                xyz=(x_pos, joystick_surface_y + shaft_y_off, joystick_surface_z + shaft_z_off),
                rpy=(-CONTROL_PANEL_ANGLE, 0.0, 0.0),
            ),
            material=coin_finish,
            name=f"joystick_{index}_shaft",
        )
        cabinet.visual(
            Sphere(radius=0.026),
            origin=Origin(
                xyz=(x_pos, joystick_surface_y + ball_y_off, joystick_surface_z + ball_z_off),
            ),
            material=ball_material,
            name=f"joystick_{index}_ball",
        )

    start_surface_z = 1.045
    start_surface_y = _control_panel_y(start_surface_z)
    start_y_off, start_z_off = _panel_normal_offset(0.005)
    for index, x_pos in enumerate((-0.08, 0.08)):
        cabinet.visual(
            Cylinder(radius=0.016, length=0.014),
            origin=Origin(
                xyz=(x_pos, start_surface_y + start_y_off, start_surface_z + start_z_off),
                rpy=(-CONTROL_PANEL_ANGLE, 0.0, 0.0),
            ),
            material=button_finish,
            name=f"start_button_{index}",
        )

    door = model.part("cashbox_door")
    door.visual(
        Box((DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT)),
        origin=Origin(xyz=(DOOR_WIDTH / 2.0, -DOOR_THICKNESS / 2.0, 0.0)),
        material=door_finish,
        name="door_panel",
    )
    door.visual(
        Cylinder(radius=0.012, length=0.020),
        origin=Origin(
            xyz=(DOOR_WIDTH - 0.055, 0.009, 0.0),
            rpy=(-math.pi / 2.0, 0.0, 0.0),
        ),
        material=coin_finish,
        name="door_pull",
    )
    door.visual(
        Box((0.010, 0.016, 0.320)),
        origin=Origin(xyz=(0.005, -0.008, 0.0)),
        material=bezel_finish,
        name="door_leaf",
    )

    flap = model.part("return_flap")
    flap.visual(
        Box((FLAP_WIDTH, FLAP_THICKNESS, FLAP_HEIGHT)),
        origin=Origin(
            xyz=(0.0, -FLAP_THICKNESS / 2.0, -FLAP_HEIGHT / 2.0),
        ),
        material=coin_finish,
        name="flap_panel",
    )

    model.articulation(
        "cabinet_to_cashbox_door",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=door,
        origin=Origin(xyz=(-DOOR_WIDTH / 2.0, DOOR_AXIS_Y, DOOR_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.45, effort=15.0, velocity=1.2),
    )
    model.articulation(
        "cabinet_to_return_flap",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=flap,
        origin=Origin(xyz=(FLAP_CENTER_X, FLAP_AXIS_Y, FLAP_TOP_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=0.85, effort=3.0, velocity=2.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
