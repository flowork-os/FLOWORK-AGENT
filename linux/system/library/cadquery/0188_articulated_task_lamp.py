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
BASE_RADIUS = 0.115
BASE_THICKNESS = 0.024
COLUMN_HEIGHT = 0.138
SHOULDER_Z = BASE_THICKNESS + COLUMN_HEIGHT + 0.003
LOWER_ARM_LENGTH = 0.315
UPPER_ARM_LENGTH = 0.285
HEAD_OUTER_RADIUS = 0.088
HEAD_INNER_RADIUS = 0.060
HEAD_DEPTH = 0.018
HEAD_CENTER_X = 0.060
COVER_OUTER_RADIUS = 0.083
COVER_INNER_RADIUS = 0.061
COVER_DEPTH = 0.006
def _arm_frame(
    *,
    length: float,
    body_width: float,
    body_height: float,
    end_block_width: float,
    end_block_height: float,
    name: str,
) -> tuple[object, str]:
    root_block = (
        cq.Workplane("XY")
        .box(0.016, body_width + 0.004, body_height + 0.004, centered=(False, True, True))
        .translate((0.0, 0.0, 0.0))
    )

    main_beam = (
        cq.Workplane("XY")
        .box(length - 0.010, body_width, body_height, centered=(False, True, True))
        .translate((0.010, 0.0, 0.0))
    )

    mid_rib = (
        cq.Workplane("XY")
        .box(0.020, body_width + 0.010, body_height + 0.004)
        .translate((length * 0.55, 0.0, 0.0))
    )

    end_block = (
        cq.Workplane("XY")
        .box(0.018, end_block_width, end_block_height, centered=(False, True, True))
        .translate((length - 0.018, 0.0, 0.0))
    )

    arm_shape = (
        root_block.union(main_beam)
        .union(mid_rib)
        .union(end_block)
    )
    return arm_shape, name
def _head_housing() -> object:
    ring = (
        cq.Workplane("YZ", origin=(HEAD_CENTER_X - HEAD_DEPTH / 2.0, 0.0, 0.0))
        .circle(HEAD_OUTER_RADIUS)
        .circle(HEAD_INNER_RADIUS)
        .extrude(HEAD_DEPTH)
    )

    lower_neck = (
        cq.Workplane("XY")
        .box(HEAD_CENTER_X - 0.004, 0.018, 0.018, centered=(False, True, True))
        .translate((0.0, 0.0, -0.068))
    )
    rear_post = (
        cq.Workplane("XY")
        .box(0.016, 0.016, 0.038, centered=(False, True, True))
        .translate((0.0, 0.0, -0.055))
    )
    root_pad = (
        cq.Workplane("XY")
        .box(0.012, 0.016, 0.030, centered=(False, True, True))
        .translate((0.0, 0.0, -0.028))
    )

    top_bridge = (
        cq.Workplane("XY")
        .box(0.026, 0.016, 0.014)
        .translate((HEAD_CENTER_X - 0.004, 0.0, HEAD_OUTER_RADIUS - 0.008))
    )

    knuckle_left = (
        cq.Workplane("XZ", origin=(HEAD_CENTER_X + HEAD_DEPTH / 2.0 - 0.006, 0.015, HEAD_OUTER_RADIUS - 0.002))
        .circle(0.004)
        .extrude(0.0045, both=True)
    )
    knuckle_right = (
        cq.Workplane("XZ", origin=(HEAD_CENTER_X + HEAD_DEPTH / 2.0 - 0.006, -0.015, HEAD_OUTER_RADIUS - 0.002))
        .circle(0.004)
        .extrude(0.0045, both=True)
    )

    housing = (
        ring.union(lower_neck)
        .union(rear_post)
        .union(root_pad)
        .union(top_bridge)
        .union(knuckle_left)
        .union(knuckle_right)
    )
    return housing
def _cover_frame() -> object:
    frame = (
        cq.Workplane("YZ", origin=(0.0, 0.0, -0.073))
        .circle(COVER_OUTER_RADIUS)
        .circle(COVER_INNER_RADIUS)
        .extrude(COVER_DEPTH)
    )

    top_stem = (
        cq.Workplane("XY")
        .box(0.028, 0.018, 0.014)
        .translate((-0.004, 0.0, -0.002))
    )

    return frame.union(top_stem)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="magnifier_task_lamp")

    base_finish = model.material("base_finish", rgba=(0.14, 0.15, 0.17, 1.0))
    arm_finish = model.material("arm_finish", rgba=(0.66, 0.68, 0.71, 1.0))
    housing_finish = model.material("housing_finish", rgba=(0.90, 0.91, 0.89, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.23, 0.24, 0.26, 1.0))
    glass = model.material("glass", rgba=(0.82, 0.90, 0.95, 0.40))

    base = model.part("base")
    base.visual(
        Cylinder(radius=BASE_RADIUS, length=BASE_THICKNESS),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS / 2.0)),
        material=base_finish,
        name="base_disk",
    )
    base.visual(
        Cylinder(radius=0.018, length=COLUMN_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS + COLUMN_HEIGHT / 2.0 - 0.001)),
        material=base_finish,
        name="column",
    )
    base.visual(
        Box((0.030, 0.060, 0.016)),
        origin=Origin(xyz=(0.028, 0.0, SHOULDER_Z - 0.020)),
        material=base_finish,
        name="fork_bridge",
    )
    base.visual(
        Box((0.022, 0.010, 0.048)),
        origin=Origin(xyz=(0.028, 0.021, SHOULDER_Z)),
        material=base_finish,
        name="fork_left",
    )
    base.visual(
        Box((0.022, 0.010, 0.048)),
        origin=Origin(xyz=(0.028, -0.021, SHOULDER_Z)),
        material=base_finish,
        name="fork_right",
    )
    base.visual(
        Box((0.014, 0.018, 0.024)),
        origin=Origin(xyz=(0.036, 0.0, SHOULDER_Z)),
        material=base_finish,
        name="pivot_block",
    )

    lower_arm_shape, lower_name = _arm_frame(
        length=LOWER_ARM_LENGTH,
        body_width=0.014,
        body_height=0.011,
        end_block_width=0.022,
        end_block_height=0.022,
        name="lower_frame",
    )

    lower_arm = model.part("lower_arm")
    lower_arm.visual(
        mesh_from_cadquery(lower_arm_shape, lower_name),
        material=arm_finish,
        name="lower_frame",
    )

    upper_arm_shape, upper_name = _arm_frame(
        length=UPPER_ARM_LENGTH,
        body_width=0.013,
        body_height=0.010,
        end_block_width=0.020,
        end_block_height=0.020,
        name="upper_frame",
    )

    upper_arm = model.part("upper_arm")
    upper_arm.visual(
        mesh_from_cadquery(upper_arm_shape, upper_name),
        material=arm_finish,
        name="upper_frame",
    )

    head = model.part("head")
    head.visual(
        mesh_from_cadquery(_head_housing(), "head_housing"),
        material=housing_finish,
        name="housing",
    )
    head.visual(
        Cylinder(radius=0.061, length=0.005),
        origin=Origin(
            xyz=(HEAD_CENTER_X + HEAD_DEPTH / 2.0 - 0.003, 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=glass,
        name="lens",
    )
    head.visual(
        Cylinder(radius=0.071, length=0.004),
        origin=Origin(
            xyz=(HEAD_CENTER_X + HEAD_DEPTH / 2.0 - 0.001, 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=trim_finish,
        name="bezel",
    )

    cover = model.part("cover")
    cover.visual(
        mesh_from_cadquery(_cover_frame(), "cover_frame"),
        material=housing_finish,
        name="cover_frame",
    )
    cover.visual(
        Cylinder(radius=0.062, length=0.003),
        origin=Origin(
            xyz=(0.002, 0.0, -0.073),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=glass,
        name="cover_lens",
    )

    model.articulation(
        "base_hinge",
        ArticulationType.REVOLUTE,
        parent=base,
        child=lower_arm,
        origin=Origin(xyz=(0.039, 0.0, SHOULDER_Z), rpy=(0.0, math.radians(-58.0), 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=30.0,
            velocity=1.0,
            lower=math.radians(-42.0),
            upper=math.radians(34.0),
        ),
    )

    model.articulation(
        "elbow_hinge",
        ArticulationType.REVOLUTE,
        parent=lower_arm,
        child=upper_arm,
        origin=Origin(xyz=(LOWER_ARM_LENGTH, 0.0, 0.0), rpy=(0.0, math.radians(22.0), 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.2,
            lower=math.radians(-70.0),
            upper=math.radians(55.0),
        ),
    )

    model.articulation(
        "head_tilt",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=head,
        origin=Origin(xyz=(UPPER_ARM_LENGTH, 0.0, 0.0), rpy=(0.0, math.radians(78.0), 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=10.0,
            velocity=1.5,
            lower=math.radians(-20.0),
            upper=math.radians(85.0),
        ),
    )

    model.articulation(
        "cover_hinge",
        ArticulationType.REVOLUTE,
        parent=head,
        child=cover,
        origin=Origin(
            xyz=(HEAD_CENTER_X + HEAD_DEPTH / 2.0 + 0.017, 0.0, HEAD_OUTER_RADIUS - 0.002),
        ),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=2.0,
            velocity=2.0,
            lower=0.0,
            upper=math.radians(135.0),
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
