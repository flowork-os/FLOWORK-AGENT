# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bench_vise_with_prismatic_jaw, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bench_vise_with_prismatic_jaw

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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
JAW_CENTER_Z = 0.155
SCREW_AXIS_Z = 0.102
PIPE_HINGE_X = -0.035
PIPE_HINGE_Z = 0.048
JAW_WIDTH = 0.126
JAW_HEIGHT = 0.028
SLIDE_TRAVEL = 0.140
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def _x_cylinder(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Workplane:
    return (
        cq.Workplane("YZ")
        .circle(radius)
        .extrude(length)
        .translate((center[0] - (length / 2.0), center[1], center[2]))
    )
def _make_body_shape() -> cq.Workplane:
    base = _box((0.240, 0.180, 0.018), (-0.030, 0.0, 0.009)).edges("|Z").fillet(0.020)
    pedestal = _box((0.100, 0.110, 0.055), (-0.075, 0.0, 0.0455))
    rear_web = _box((0.085, 0.095, 0.045), (-0.100, 0.0, 0.094))
    fixed_body = _box((0.170, 0.140, 0.080), (-0.085, 0.0, 0.140))
    front_bridge = _box((0.060, 0.082, 0.044), (-0.040, 0.0, 0.100))
    rail_0 = _box((0.180, 0.034, 0.030), (0.090, 0.053, 0.093))
    rail_1 = _box((0.180, 0.034, 0.030), (0.090, -0.053, 0.093))
    hinge_mount = _box((0.030, 0.080, 0.018), (-0.075, 0.0, 0.071))
    hinge_ear_0 = _box((0.018, 0.018, 0.028), (PIPE_HINGE_X, 0.055, 0.050))
    hinge_ear_1 = _box((0.018, 0.018, 0.028), (PIPE_HINGE_X, -0.055, 0.050))

    shell = (
        base.union(pedestal)
        .union(rear_web)
        .union(fixed_body)
        .union(front_bridge)
        .union(rail_0)
        .union(rail_1)
        .union(hinge_mount)
        .union(hinge_ear_0)
        .union(hinge_ear_1)
    )

    slide_slot = _box((0.220, 0.072, 0.032), (0.090, 0.0, 0.093))
    screw_bore = _x_cylinder(0.0145, 0.280, (-0.040, 0.0, SCREW_AXIS_Z))
    pipe_clearance = _box((0.090, 0.078, 0.050), (0.015, 0.0, 0.045))
    return shell.cut(slide_slot).cut(screw_bore).cut(pipe_clearance)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bench_vise")

    model.material("cast_blue", rgba=(0.19, 0.33, 0.56, 1.0))
    model.material("jaw_steel", rgba=(0.62, 0.66, 0.70, 1.0))
    model.material("bright_steel", rgba=(0.78, 0.80, 0.82, 1.0))
    model.material("dark_steel", rgba=(0.32, 0.34, 0.36, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_make_body_shape(), "body_shell"),
        material="cast_blue",
        name="body_shell",
    )
    body.visual(
        Box((0.008, JAW_WIDTH, JAW_HEIGHT)),
        origin=Origin(xyz=(-0.004, 0.0, JAW_CENTER_Z)),
        material="jaw_steel",
        name="fixed_jaw_face",
    )

    front_jaw = model.part("front_jaw")
    front_jaw.visual(
        Box((0.085, 0.146, 0.080)),
        origin=Origin(xyz=(0.0505, 0.0, 0.0)),
        material="cast_blue",
        name="jaw_shell",
    )
    front_jaw.visual(
        Box((0.090, 0.070, 0.040)),
        origin=Origin(xyz=(0.053, 0.0, -0.088)),
        material="cast_blue",
        name="jaw_lower",
    )
    front_jaw.visual(
        Box((0.060, 0.014, 0.050)),
        origin=Origin(xyz=(0.050, 0.022, -0.049)),
        material="cast_blue",
        name="jaw_brace_0",
    )
    front_jaw.visual(
        Box((0.060, 0.014, 0.050)),
        origin=Origin(xyz=(0.050, -0.022, -0.049)),
        material="cast_blue",
        name="jaw_brace_1",
    )
    front_jaw.visual(
        Cylinder(radius=0.024, length=0.026),
        origin=Origin(xyz=(0.152, 0.0, -0.053), rpy=(0.0, pi / 2.0, 0.0)),
        material="cast_blue",
        name="jaw_nose",
    )
    front_jaw.visual(
        Box((0.008, JAW_WIDTH, JAW_HEIGHT)),
        origin=Origin(xyz=(0.005, 0.0, 0.0)),
        material="jaw_steel",
        name="moving_jaw_face",
    )
    front_jaw.visual(
        Box((0.174, 0.056, 0.012)),
        origin=Origin(xyz=(0.070, 0.0, -0.072)),
        material="cast_blue",
        name="guide_shoe",
    )
    front_jaw.visual(
        Box((0.058, 0.060, 0.010)),
        origin=Origin(xyz=(0.046, 0.0, -0.080)),
        material="jaw_steel",
        name="pipe_saddle",
    )

    handle = model.part("handle")
    handle.visual(
        Cylinder(radius=0.018, length=0.040),
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
        material="bright_steel",
        name="handle_hub",
    )
    handle.visual(
        Cylinder(radius=0.011, length=0.190),
        origin=Origin(xyz=(-0.090, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material="dark_steel",
        name="lead_screw",
    )
    handle.visual(
        Cylinder(radius=0.006, length=0.220),
        origin=Origin(xyz=(0.006, 0.0, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material="bright_steel",
        name="handle_bar",
    )
    handle.visual(
        Cylinder(radius=0.010, length=0.024),
        origin=Origin(xyz=(0.006, 0.112, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material="bright_steel",
        name="bar_end_0",
    )
    handle.visual(
        Cylinder(radius=0.010, length=0.024),
        origin=Origin(xyz=(0.006, -0.112, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material="bright_steel",
        name="bar_end_1",
    )

    pipe_jaw = model.part("pipe_jaw")
    pipe_jaw.visual(
        Box((0.070, 0.060, 0.018)),
        origin=Origin(xyz=(0.040, 0.0, -0.014)),
        material="dark_steel",
        name="pipe_shell",
    )
    pipe_jaw.visual(
        Box((0.032, 0.060, 0.012)),
        origin=Origin(xyz=(0.062, 0.0, -0.002)),
        material="dark_steel",
        name="pipe_cap",
    )
    pipe_jaw.visual(
        Cylinder(radius=0.012, length=0.088),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material="dark_steel",
        name="pipe_barrel",
    )
    pipe_jaw.visual(
        Box((0.032, 0.096, 0.006)),
        origin=Origin(xyz=(0.059, 0.0, -0.002)),
        material="jaw_steel",
        name="pipe_face",
    )

    model.articulation(
        "jaw_slide",
        ArticulationType.PRISMATIC,
        parent=body,
        child=front_jaw,
        origin=Origin(xyz=(0.0, 0.0, JAW_CENTER_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=SLIDE_TRAVEL, effort=1800.0, velocity=0.22),
    )
    model.articulation(
        "handle_spin",
        ArticulationType.CONTINUOUS,
        parent=front_jaw,
        child=handle,
        origin=Origin(xyz=(0.185, 0.0, SCREW_AXIS_Z - JAW_CENTER_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=25.0, velocity=8.0),
    )
    model.articulation(
        "pipe_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=pipe_jaw,
        origin=Origin(xyz=(PIPE_HINGE_X, 0.0, PIPE_HINGE_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.25, effort=120.0, velocity=1.8),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
