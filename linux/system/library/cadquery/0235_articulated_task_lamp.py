# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, articulated_task_lamp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: articulated_task_lamp

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
PRIMARY_ARM_LENGTH = 0.42
SECONDARY_ARM_LENGTH = 0.285
PRIMARY_START = 0.019
SECONDARY_START = 0.016
HEAD_START = 0.014
def _box(size_x: float, size_y: float, size_z: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return cq.Workplane("XY").box(size_x, size_y, size_z).translate((x, y, z))
def _cyl_y(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return (
        cq.Workplane("XZ")
        .center(x, z)
        .circle(radius)
        .extrude(length / 2.0, both=True)
        .translate((0.0, y, 0.0))
    )
def _cyl_z(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z_bottom: float = 0.0):
    return cq.Workplane("XY").center(x, y).circle(radius).extrude(length).translate((0.0, 0.0, z_bottom))
def _build_clamp_base_shape():
    tower = _box(0.030, 0.044, 0.150, x=-0.020, z=-0.087)
    jaw = _box(0.092, 0.070, 0.012, x=-0.014, z=-0.124)
    rear_block = _box(0.032, 0.070, 0.070, x=-0.044, z=-0.157)
    throat_bridge = _box(0.056, 0.024, 0.018, x=-0.018, z=-0.148)
    screw_boss = _box(0.032, 0.044, 0.016, x=0.006, z=-0.165)

    shoulder_web = _box(0.018, 0.044, 0.034, x=-0.024, z=-0.004)
    shoulder_cheek_pos = _cyl_y(0.015, 0.008, x=0.0, y=0.017, z=0.0)
    shoulder_cheek_neg = _cyl_y(0.015, 0.008, x=0.0, y=-0.017, z=0.0)

    screw = _cyl_z(0.006, 0.075, x=0.010, z_bottom=-0.220)
    pressure_pad = _cyl_z(0.018, 0.005, x=0.010, z_bottom=-0.149)
    knob_bar = _cyl_y(0.005, 0.085, x=0.010, z=-0.223)

    clamp_shape = tower
    for solid in (
        jaw,
        rear_block,
        throat_bridge,
        screw_boss,
        shoulder_web,
        shoulder_cheek_pos,
        shoulder_cheek_neg,
        screw,
        pressure_pad,
        knob_bar,
    ):
        clamp_shape = clamp_shape.union(solid)
    return clamp_shape
def _build_primary_arm_shape():
    shoulder_lug = _cyl_y(0.012, 0.026, x=0.0, z=0.0)
    shoulder_neck = _box(0.018, 0.022, 0.016, x=0.015)
    heel = _box(0.062, 0.030, 0.020, x=PRIMARY_START + 0.031)
    beam = _box(0.316, 0.026, 0.014, x=0.237)
    upper_rib = _box(0.170, 0.016, 0.007, x=0.205, z=0.010)
    yoke_plate_pos = _box(0.046, 0.010, 0.020, x=PRIMARY_ARM_LENGTH - 0.027, y=0.016)
    yoke_plate_neg = _box(0.046, 0.010, 0.020, x=PRIMARY_ARM_LENGTH - 0.027, y=-0.016)
    elbow_cheek_pos = _cyl_y(0.013, 0.008, x=PRIMARY_ARM_LENGTH, y=0.016)
    elbow_cheek_neg = _cyl_y(0.013, 0.008, x=PRIMARY_ARM_LENGTH, y=-0.016)

    arm_shape = shoulder_lug.union(shoulder_neck).union(heel)
    for solid in (
        beam,
        upper_rib,
        yoke_plate_pos,
        yoke_plate_neg,
        elbow_cheek_pos,
        elbow_cheek_neg,
    ):
        arm_shape = arm_shape.union(solid)
    return arm_shape
def _build_secondary_arm_shape():
    elbow_lug = _cyl_y(0.0105, 0.022, x=0.0, z=0.0)
    elbow_neck = _box(0.014, 0.020, 0.014, x=0.012)
    heel = _box(0.054, 0.026, 0.018, x=SECONDARY_START + 0.027)
    beam = _box(0.176, 0.022, 0.013, x=0.156)
    upper_rib = _box(0.108, 0.014, 0.006, x=0.154, z=0.009)
    yoke_plate_pos = _box(0.040, 0.009, 0.018, x=SECONDARY_ARM_LENGTH - 0.023, y=0.0145)
    yoke_plate_neg = _box(0.040, 0.009, 0.018, x=SECONDARY_ARM_LENGTH - 0.023, y=-0.0145)
    head_cheek_pos = _cyl_y(0.0115, 0.0075, x=SECONDARY_ARM_LENGTH, y=0.0145)
    head_cheek_neg = _cyl_y(0.0115, 0.0075, x=SECONDARY_ARM_LENGTH, y=-0.0145)

    arm_shape = elbow_lug.union(elbow_neck).union(heel)
    for solid in (
        beam,
        upper_rib,
        yoke_plate_pos,
        yoke_plate_neg,
        head_cheek_pos,
        head_cheek_neg,
    ):
        arm_shape = arm_shape.union(solid)
    return arm_shape
def _build_head_shape():
    head_lug = _cyl_y(0.0100, 0.020, x=0.0, z=0.0)
    head_neck = _box(0.014, 0.018, 0.014, x=0.012, z=-0.003)
    head_shell = (
        cq.Workplane("XY")
        .box(0.168, 0.098, 0.036)
        .edges()
        .fillet(0.012)
        .translate((0.108, 0.0, -0.020))
    )
    neck = _box(0.050, 0.036, 0.020, x=0.040, z=-0.010)
    rear_mount = _box(0.032, 0.028, 0.018, x=HEAD_START + 0.016, z=-0.004)

    head_shape = head_lug.union(head_neck).union(head_shell).union(neck).union(rear_mount)
    return head_shape
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cantilever_task_lamp")

    graphite = model.material("graphite", rgba=(0.18, 0.19, 0.21, 1.0))
    aluminum = model.material("aluminum", rgba=(0.73, 0.75, 0.78, 1.0))
    head_white = model.material("head_white", rgba=(0.88, 0.88, 0.84, 1.0))
    diffuser = model.material("diffuser", rgba=(0.96, 0.96, 0.90, 0.92))

    clamp_base = model.part("clamp_base")
    clamp_base.visual(
        mesh_from_cadquery(_build_clamp_base_shape(), "clamp_base"),
        material=graphite,
        name="clamp_shell",
    )

    primary_arm = model.part("primary_arm")
    primary_arm.visual(
        mesh_from_cadquery(_build_primary_arm_shape(), "primary_arm"),
        material=aluminum,
        name="primary_shell",
    )

    secondary_arm = model.part("secondary_arm")
    secondary_arm.visual(
        mesh_from_cadquery(_build_secondary_arm_shape(), "secondary_arm"),
        material=aluminum,
        name="secondary_shell",
    )

    head = model.part("head")
    head.visual(
        mesh_from_cadquery(_build_head_shape(), "head"),
        material=head_white,
        name="head_shell",
    )
    head.visual(
        Box((0.122, 0.066, 0.006)),
        origin=Origin(xyz=(0.112, 0.0, -0.035)),
        material=diffuser,
        name="diffuser",
    )

    model.articulation(
        "clamp_to_primary",
        ArticulationType.REVOLUTE,
        parent=clamp_base,
        child=primary_arm,
        origin=Origin(),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=math.radians(-35.0),
            upper=math.radians(75.0),
            effort=30.0,
            velocity=1.6,
        ),
    )
    model.articulation(
        "primary_to_secondary",
        ArticulationType.REVOLUTE,
        parent=primary_arm,
        child=secondary_arm,
        origin=Origin(xyz=(PRIMARY_ARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=math.radians(-95.0),
            upper=math.radians(95.0),
            effort=18.0,
            velocity=1.8,
        ),
    )
    model.articulation(
        "secondary_to_head",
        ArticulationType.REVOLUTE,
        parent=secondary_arm,
        child=head,
        origin=Origin(xyz=(SECONDARY_ARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=math.radians(-65.0),
            upper=math.radians(45.0),
            effort=10.0,
            velocity=2.5,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
