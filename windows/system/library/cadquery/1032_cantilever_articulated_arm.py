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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
BASE_LENGTH = 0.180
BASE_WIDTH = 0.110
BASE_THICKNESS = 0.016
COLUMN_X = -0.045
COLUMN_WIDTH = 0.052
COLUMN_DEPTH = 0.050
COLUMN_HEIGHT = 0.086
SHOULDER_X = 0.002
SHOULDER_Z = BASE_THICKNESS + COLUMN_HEIGHT + 0.018
JOINT_RADIUS = 0.018
FORK_OUTER_WIDTH = 0.046
CHEEK_THICKNESS = 0.009
HUB_LENGTH = FORK_OUTER_WIDTH - 2.0 * CHEEK_THICKNESS
LINK_THICKNESS = 0.028
UPPER_ARM_LENGTH = 0.205
FOREARM_LENGTH = 0.175
WRIST_NECK_LENGTH = 0.034
WRIST_FACE_RADIUS = 0.033
WRIST_FACE_THICKNESS = 0.012
SHOULDER_LIMITS = (-0.35, 1.10)
ELBOW_LIMITS = (-1.35, 1.20)
WRIST_LIMITS = (-1.05, 1.10)
def _cylinder_y(radius: float, length: float) -> cq.Workplane:
    return cq.Workplane("XZ").circle(radius).extrude(length).translate((0.0, length / 2.0, 0.0))
def _plate_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS)
        .edges("|Z")
        .fillet(0.008)
        .faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .pushPoints(
            [
                (-0.055, -0.032),
                (-0.055, 0.032),
                (0.055, -0.032),
                (0.055, 0.032),
            ]
        )
        .slot2D(0.024, 0.009, angle=90.0)
        .cutThruAll()
        .translate((0.0, 0.0, BASE_THICKNESS / 2.0))
    )
def _base_shape() -> cq.Workplane:
    plate = _plate_shape()
    column = (
        cq.Workplane("XY")
        .box(COLUMN_WIDTH, COLUMN_DEPTH, COLUMN_HEIGHT)
        .edges("|Z")
        .fillet(0.006)
        .translate((COLUMN_X, 0.0, BASE_THICKNESS + COLUMN_HEIGHT / 2.0))
    )
    lower_anchor = cq.Workplane("XY").box(0.030, FORK_OUTER_WIDTH, 0.018).translate((SHOULDER_X - 0.010, 0.0, SHOULDER_Z - 0.028))
    left_ear = cq.Workplane("XY").box(0.034, CHEEK_THICKNESS, 0.050).translate((SHOULDER_X + 0.006, -0.0185, SHOULDER_Z))
    right_ear = cq.Workplane("XY").box(0.034, CHEEK_THICKNESS, 0.050).translate((SHOULDER_X + 0.006, 0.0185, SHOULDER_Z))
    center_gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (COLUMN_X - 0.010, BASE_THICKNESS + 0.050),
                (SHOULDER_X - 0.016, SHOULDER_Z - 0.036),
                (SHOULDER_X + 0.004, SHOULDER_Z - 0.036),
                (COLUMN_X + 0.012, BASE_THICKNESS + 0.060),
            ]
        )
        .close()
        .extrude(0.020)
        .translate((0.0, -0.010, 0.0))
    )
    return plate.union(column).union(lower_anchor).union(left_ear).union(right_ear).union(center_gusset)
def _upper_arm_shape() -> cq.Workplane:
    hub = _cylinder_y(JOINT_RADIUS, HUB_LENGTH)
    root_neck = cq.Workplane("XY").box(0.026, 0.024, 0.022).translate((0.022, 0.0, 0.0))
    beam = cq.Workplane("XY").box(0.132, 0.034, LINK_THICKNESS).translate((0.099, 0.0, 0.0))
    elbow_block = cq.Workplane("XY").box(0.060, FORK_OUTER_WIDTH, 0.030).translate((UPPER_ARM_LENGTH - 0.011, 0.0, 0.0))
    elbow_slot = cq.Workplane("XY").box(0.060, HUB_LENGTH, 0.054).translate((UPPER_ARM_LENGTH + 0.002, 0.0, 0.0))
    return hub.union(root_neck).union(beam).union(elbow_block).cut(elbow_slot)
def _forearm_shape() -> cq.Workplane:
    hub = _cylinder_y(JOINT_RADIUS, HUB_LENGTH)
    root_neck = cq.Workplane("XY").box(0.024, 0.024, 0.022).translate((0.020, 0.0, 0.0))
    beam = cq.Workplane("XY").box(0.110, 0.032, 0.024).translate((0.085, 0.0, 0.0))
    wrist_block = cq.Workplane("XY").box(0.056, FORK_OUTER_WIDTH, 0.030).translate((FOREARM_LENGTH - 0.010, 0.0, 0.0))
    wrist_slot = cq.Workplane("XY").box(0.062, HUB_LENGTH, 0.054).translate((FOREARM_LENGTH + 0.004, 0.0, 0.0))
    return hub.union(root_neck).union(beam).union(wrist_block).cut(wrist_slot)
def _wrist_body_shape() -> cq.Workplane:
    hub = _cylinder_y(JOINT_RADIUS * 0.95, HUB_LENGTH)
    neck = cq.Workplane("XY").box(0.028, 0.022, 0.022).translate((0.020, 0.0, 0.0))
    return hub.union(neck)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bench_cantilever_arm")

    base_finish = model.material("base_finish", rgba=(0.20, 0.22, 0.24, 1.0))
    arm_finish = model.material("arm_finish", rgba=(0.69, 0.72, 0.75, 1.0))
    wrist_finish = model.material("wrist_finish", rgba=(0.32, 0.35, 0.38, 1.0))
    face_finish = model.material("face_finish", rgba=(0.78, 0.80, 0.83, 1.0))

    base = model.part("base")
    base.visual(mesh_from_cadquery(_base_shape(), "base"), material=base_finish, name="base_body")
    base.inertial = Inertial.from_geometry(
        Box((BASE_LENGTH, BASE_WIDTH, SHOULDER_Z + 0.040)),
        mass=6.0,
        origin=Origin(xyz=(COLUMN_X * 0.35, 0.0, (SHOULDER_Z + 0.040) / 2.0)),
    )

    upper_arm = model.part("upper_arm")
    upper_arm.visual(mesh_from_cadquery(_upper_arm_shape(), "upper_arm"), material=arm_finish, name="upper_arm_body")
    upper_arm.inertial = Inertial.from_geometry(
        Box((UPPER_ARM_LENGTH, FORK_OUTER_WIDTH, 0.040)),
        mass=1.2,
        origin=Origin(xyz=(UPPER_ARM_LENGTH / 2.0, 0.0, 0.0)),
    )

    forearm = model.part("forearm")
    forearm.visual(mesh_from_cadquery(_forearm_shape(), "forearm"), material=arm_finish, name="forearm_body")
    forearm.inertial = Inertial.from_geometry(
        Box((FOREARM_LENGTH, FORK_OUTER_WIDTH, 0.036)),
        mass=0.9,
        origin=Origin(xyz=(FOREARM_LENGTH / 2.0, 0.0, 0.0)),
    )

    wrist_face = model.part("wrist_face")
    wrist_face.visual(mesh_from_cadquery(_wrist_body_shape(), "wrist_body"), material=wrist_finish, name="wrist_body")
    wrist_face.visual(
        Cylinder(radius=WRIST_FACE_RADIUS, length=WRIST_FACE_THICKNESS),
        origin=Origin(
            xyz=(WRIST_NECK_LENGTH + WRIST_FACE_THICKNESS / 2.0, 0.0, 0.0),
            rpy=(0.0, pi / 2.0, 0.0),
        ),
        material=face_finish,
        name="face_plate",
    )
    wrist_face.inertial = Inertial.from_geometry(
        Box((0.080, 0.070, 0.070)),
        mass=0.45,
        origin=Origin(xyz=(0.040, 0.0, 0.0)),
    )

    model.articulation(
        "shoulder_pitch",
        ArticulationType.REVOLUTE,
        parent=base,
        child=upper_arm,
        origin=Origin(xyz=(SHOULDER_X, 0.0, SHOULDER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=SHOULDER_LIMITS[0],
            upper=SHOULDER_LIMITS[1],
            effort=42.0,
            velocity=1.2,
        ),
    )
    model.articulation(
        "elbow_pitch",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=forearm,
        origin=Origin(xyz=(UPPER_ARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=ELBOW_LIMITS[0],
            upper=ELBOW_LIMITS[1],
            effort=28.0,
            velocity=1.6,
        ),
    )
    model.articulation(
        "wrist_pitch",
        ArticulationType.REVOLUTE,
        parent=forearm,
        child=wrist_face,
        origin=Origin(xyz=(FOREARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=WRIST_LIMITS[0],
            upper=WRIST_LIMITS[1],
            effort=12.0,
            velocity=2.0,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
