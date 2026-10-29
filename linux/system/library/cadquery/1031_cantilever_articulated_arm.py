# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cantilever_articulated_arm, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cantilever_articulated_arm

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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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

class _NoOp:
    """Universal no-op sentinel that is callable AND Path-like, so asset/IO
    expressions in model scripts (e.g. ASSETS.mesh_dir.mkdir(); dir / 'x.obj')
    are harmless in self-contained mode."""
    def __call__(self, *a, **k):
        return self

    def __getattr__(self, _n):
        return self

    def __truediv__(self, _o):
        return self

    def __rtruediv__(self, _o):
        return self

    def __fspath__(self):
        return "/tmp/_articraft_noop"

    def mkdir(self, *a, **k):
        return None

_NOOP = _NoOp()

class _NoopMeta(type):
    def __getattr__(cls, _name):
        def _noop(*a, **k):
            return cls()
        return _noop

class AssetContext(metaclass=_NoopMeta):
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, _n):
        return _NOOP

# ===== model =====
import math
import cadquery as cq
ASSETS = AssetContext.from_script(__file__)
PLATE_LENGTH = 0.22
PLATE_WIDTH = 0.16
PLATE_THICKNESS = 0.016
COLUMN_LENGTH = 0.07
COLUMN_WIDTH = 0.09
COLUMN_HEIGHT = 0.13
SHOULDER_AXIS_X = 0.055
SHOULDER_AXIS_Z = PLATE_THICKNESS + COLUMN_HEIGHT - 0.006
UPPER_ARM_LENGTH = 0.205
UPPER_ARM_HEIGHT = 0.038
FOREARM_LENGTH = 0.175
FOREARM_HEIGHT = 0.034
WRIST_HUB_RADIUS = 0.009
WRIST_HUB_LENGTH = 0.022
TOOL_PLATE_LENGTH = 0.062
TOOL_PLATE_WIDTH = 0.058
TOOL_PLATE_HEIGHT = 0.042
SHOULDER_RANGE = math.radians(120.0)
ELBOW_RANGE = math.radians(135.0)
WRIST_RANGE = math.radians(90.0)
def _box_span(
    x0: float,
    x1: float,
    y_size: float,
    z_size: float,
    *,
    y: float = 0.0,
    z: float = 0.0,
) -> cq.Workplane:
    return cq.Workplane("XY").box(x1 - x0, y_size, z_size).translate(((x0 + x1) * 0.5, y, z))
def _cylinder_y(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XZ").circle(radius).extrude(length).translate((x, y - length * 0.5, z))
def _cylinder_x(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("YZ").circle(radius).extrude(length).translate((x - length * 0.5, y, z))
def _base_clevis_shape() -> cq.Workplane:
    web = _box_span(
        COLUMN_LENGTH * 0.28,
        SHOULDER_AXIS_X - 0.011,
        0.03,
        0.014,
        z=SHOULDER_AXIS_Z - 0.014,
    )
    brace = _box_span(
        SHOULDER_AXIS_X - 0.018,
        SHOULDER_AXIS_X - 0.011,
        0.038,
        0.024,
        z=SHOULDER_AXIS_Z - 0.006,
    )
    ear_y = 0.013
    ears = (
        _box_span(
            SHOULDER_AXIS_X - 0.01,
            SHOULDER_AXIS_X + 0.01,
            0.006,
            0.038,
            y=ear_y,
            z=SHOULDER_AXIS_Z,
        )
        .union(
            _box_span(
                SHOULDER_AXIS_X - 0.01,
                SHOULDER_AXIS_X + 0.01,
                0.006,
                0.038,
                y=-ear_y,
                z=SHOULDER_AXIS_Z,
            )
        )
    )
    return web.union(brace).union(ears)
def _upper_arm_beam_shape() -> cq.Workplane:
    half_h = UPPER_ARM_HEIGHT * 0.5
    profile = [
        (0.01, -half_h * 0.45),
        (0.022, -half_h * 0.9),
        (0.06, -half_h),
        (UPPER_ARM_LENGTH - 0.055, -half_h * 0.92),
        (UPPER_ARM_LENGTH - 0.02, -half_h * 0.62),
        (UPPER_ARM_LENGTH - 0.02, half_h * 0.62),
        (UPPER_ARM_LENGTH - 0.055, half_h * 0.92),
        (0.06, half_h),
        (0.022, half_h * 0.9),
        (0.01, half_h * 0.45),
    ]
    beam = cq.Workplane("XZ").polyline(profile).close().extrude(0.026).translate((0.0, -0.013, 0.0))
    rib = _box_span(0.05, UPPER_ARM_LENGTH - 0.07, 0.012, 0.042, z=0.0)
    return beam.union(rib)
def _shoulder_knuckle_shape() -> cq.Workplane:
    block = _box_span(-0.008, 0.012, 0.016, 0.026, z=0.0)
    cap = _cylinder_y(0.008, 0.014, x=0.002, z=0.0)
    return block.union(cap)
def _shoulder_body_shape() -> cq.Workplane:
    return _upper_arm_beam_shape().union(_upper_arm_clevis_shape())
def _upper_arm_clevis_shape() -> cq.Workplane:
    bridge = _box_span(
        UPPER_ARM_LENGTH - 0.022,
        UPPER_ARM_LENGTH - 0.008,
        0.028,
        0.012,
        z=-0.011,
    )
    ear_y = 0.013
    ears = (
        _box_span(
            UPPER_ARM_LENGTH - 0.008,
            UPPER_ARM_LENGTH + 0.01,
            0.006,
            0.036,
            y=ear_y,
            z=0.0,
        )
        .union(
            _box_span(
                UPPER_ARM_LENGTH - 0.008,
                UPPER_ARM_LENGTH + 0.01,
                0.006,
                0.036,
                y=-ear_y,
                z=0.0,
            )
        )
    )
    return bridge.union(ears)
def _forearm_beam_shape() -> cq.Workplane:
    half_h = FOREARM_HEIGHT * 0.5
    profile = [
        (0.01, -half_h * 0.45),
        (0.022, -half_h * 0.9),
        (0.05, -half_h),
        (FOREARM_LENGTH - 0.05, -half_h * 0.92),
        (FOREARM_LENGTH - 0.024, -half_h * 0.66),
        (FOREARM_LENGTH - 0.024, half_h * 0.66),
        (FOREARM_LENGTH - 0.05, half_h * 0.92),
        (0.05, half_h),
        (0.022, half_h * 0.9),
        (0.01, half_h * 0.45),
    ]
    beam = cq.Workplane("XZ").polyline(profile).close().extrude(0.024).translate((0.0, -0.012, 0.0))
    rib = _box_span(0.04, FOREARM_LENGTH - 0.08, 0.01, 0.038, z=0.0)
    return beam.union(rib)
def _elbow_knuckle_shape() -> cq.Workplane:
    block = _box_span(-0.008, 0.012, 0.016, 0.024, z=0.0)
    cap = _cylinder_y(0.0075, 0.014, x=0.002, z=0.0)
    return block.union(cap)
def _elbow_body_shape() -> cq.Workplane:
    root_bridge = _box_span(-0.002, 0.028, 0.014, 0.018, z=0.0)
    return root_bridge.union(_forearm_beam_shape()).union(_wrist_cage_shape())
def _wrist_cage_shape() -> cq.Workplane:
    mount_block = _box_span(FOREARM_LENGTH - 0.03, FOREARM_LENGTH - 0.006, 0.028, 0.024, z=0.0)
    ear_y = 0.018
    supports = (
        _box_span(
            FOREARM_LENGTH - 0.006,
            FOREARM_LENGTH + 0.01,
            0.006,
            0.04,
            y=ear_y,
            z=0.0,
        )
        .union(
            _box_span(
                FOREARM_LENGTH - 0.006,
                FOREARM_LENGTH + 0.01,
                0.006,
                0.04,
                y=-ear_y,
                z=0.0,
            )
        )
    )
    return mount_block.union(supports)
def _tool_plate_shape() -> cq.Workplane:
    neck = _box_span(0.01, 0.022, 0.022, 0.024, z=0.0)
    plate = _box_span(0.022, TOOL_PLATE_LENGTH, TOOL_PLATE_WIDTH, TOOL_PLATE_HEIGHT, z=0.0)
    slot_1 = _cylinder_x(0.0032, 0.05, x=0.04, y=0.014, z=0.0)
    slot_2 = _cylinder_x(0.0032, 0.05, x=0.04, y=-0.014, z=0.0)
    return neck.union(plate).cut(slot_1).cut(slot_2)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bench_tooling_arm", assets=ASSETS)

    dark_base = model.material("dark_base", rgba=(0.18, 0.20, 0.22, 1.0))
    arm_gray = model.material("arm_gray", rgba=(0.52, 0.57, 0.63, 1.0))
    steel = model.material("steel", rgba=(0.71, 0.73, 0.76, 1.0))
    tool_plate_color = model.material("tool_plate_color", rgba=(0.30, 0.36, 0.42, 1.0))

    base = model.part("base")
    base.visual(
        Box((PLATE_LENGTH, PLATE_WIDTH, PLATE_THICKNESS)),
        origin=Origin(xyz=(0.0, 0.0, PLATE_THICKNESS * 0.5)),
        material=dark_base,
        name="base_plate",
    )
    base.visual(
        Box((COLUMN_LENGTH, COLUMN_WIDTH, COLUMN_HEIGHT)),
        origin=Origin(xyz=(0.0, 0.0, PLATE_THICKNESS + COLUMN_HEIGHT * 0.5)),
        material=dark_base,
        name="column",
    )
    base.visual(
        mesh_from_cadquery(_base_clevis_shape(), "base_clevis.obj", assets=ASSETS),
        material=dark_base,
        name="shoulder_clevis",
    )
    base.inertial = Inertial.from_geometry(
        Box((PLATE_LENGTH, PLATE_WIDTH, COLUMN_HEIGHT + PLATE_THICKNESS)),
        mass=8.0,
        origin=Origin(xyz=(0.0, 0.0, (COLUMN_HEIGHT + PLATE_THICKNESS) * 0.5)),
    )

    shoulder = model.part("shoulder_link")
    shoulder.visual(
        mesh_from_cadquery(_shoulder_knuckle_shape(), "shoulder_knuckle.obj", assets=ASSETS),
        material=steel,
        name="shoulder_knuckle",
    )
    shoulder.visual(
        mesh_from_cadquery(_shoulder_body_shape(), "shoulder_body.obj", assets=ASSETS),
        material=arm_gray,
        name="shoulder_body",
    )
    shoulder.inertial = Inertial.from_geometry(
        Box((UPPER_ARM_LENGTH + 0.02, 0.04, 0.05)),
        mass=2.2,
        origin=Origin(xyz=(UPPER_ARM_LENGTH * 0.5, 0.0, 0.0)),
    )

    elbow = model.part("elbow_link")
    elbow.visual(
        mesh_from_cadquery(_elbow_knuckle_shape(), "elbow_knuckle.obj", assets=ASSETS),
        material=steel,
        name="elbow_knuckle",
    )
    elbow.visual(
        mesh_from_cadquery(_elbow_body_shape(), "elbow_body.obj", assets=ASSETS),
        material=arm_gray,
        name="elbow_body",
    )
    elbow.inertial = Inertial.from_geometry(
        Box((FOREARM_LENGTH + 0.03, 0.04, 0.05)),
        mass=1.6,
        origin=Origin(xyz=(FOREARM_LENGTH * 0.5, 0.0, 0.0)),
    )

    wrist = model.part("wrist_tool_plate")
    wrist.visual(
        Cylinder(radius=WRIST_HUB_RADIUS, length=WRIST_HUB_LENGTH),
        origin=Origin(rpy=(0.0, math.pi * 0.5, 0.0)),
        material=steel,
        name="roll_hub",
    )
    wrist.visual(
        mesh_from_cadquery(_tool_plate_shape(), "tool_plate.obj", assets=ASSETS),
        material=tool_plate_color,
        name="tool_plate",
    )
    wrist.inertial = Inertial.from_geometry(
        Box((TOOL_PLATE_LENGTH, TOOL_PLATE_WIDTH, TOOL_PLATE_HEIGHT)),
        mass=0.55,
        origin=Origin(xyz=(TOOL_PLATE_LENGTH * 0.5, 0.0, 0.0)),
    )

    model.articulation(
        "base_to_shoulder",
        ArticulationType.REVOLUTE,
        parent=base,
        child=shoulder,
        origin=Origin(xyz=(SHOULDER_AXIS_X, 0.0, SHOULDER_AXIS_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=80.0,
            velocity=1.6,
            lower=0.0,
            upper=SHOULDER_RANGE,
        ),
    )
    model.articulation(
        "shoulder_to_elbow",
        ArticulationType.REVOLUTE,
        parent=shoulder,
        child=elbow,
        origin=Origin(xyz=(UPPER_ARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=55.0,
            velocity=2.0,
            lower=-ELBOW_RANGE,
            upper=0.0,
        ),
    )
    model.articulation(
        "elbow_to_wrist",
        ArticulationType.REVOLUTE,
        parent=elbow,
        child=wrist,
        origin=Origin(xyz=(FOREARM_LENGTH, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=3.0,
            lower=-WRIST_RANGE,
            upper=WRIST_RANGE,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
