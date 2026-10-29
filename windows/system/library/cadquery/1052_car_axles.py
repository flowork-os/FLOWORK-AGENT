# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_axles, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_axles

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
STEEL = Material("satin_black_steel", rgba=(0.035, 0.036, 0.034, 1.0))
BRIGHT_STEEL = Material("machined_steel", rgba=(0.64, 0.66, 0.64, 1.0))
CAST_IRON = Material("dark_cast_iron", rgba=(0.12, 0.125, 0.12, 1.0))
RUBBER = Material("cv_boot_rubber", rgba=(0.006, 0.006, 0.005, 1.0))
ZINC = Material("zinc_plated_fasteners", rgba=(0.78, 0.76, 0.70, 1.0))
def _tube_along_x(outer_radius: float, inner_radius: float, length: float, start_x: float) -> cq.Workplane:
    """Return a hollow cylindrical shell running from start_x to start_x + length."""
    outer = cq.Workplane("YZ").circle(outer_radius).extrude(length)
    bore = cq.Workplane("YZ").circle(inner_radius).extrude(length + 0.004).translate((-0.002, 0.0, 0.0))
    return outer.cut(bore).translate((start_x, 0.0, 0.0))
def _x_cylinder(radius: float, length: float) -> Cylinder:
    return Cylinder(radius=radius, length=length)
def _origin_x(x: float, y: float = 0.0, z: float = 0.0) -> Origin:
    return Origin(xyz=(x, y, z), rpy=(0.0, math.pi / 2.0, 0.0))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="irs_rear_half_shaft")

    inboard = model.part("inboard_coupling")
    cup_shell = _tube_along_x(0.088, 0.064, 0.145, -0.145)
    cup_lip = _tube_along_x(0.098, 0.064, 0.030, -0.018)
    inboard.visual(
        mesh_from_cadquery(cup_shell, "inboard_cup_shell"),
        material=CAST_IRON,
        name="cup_shell",
    )
    inboard.visual(
        mesh_from_cadquery(cup_lip, "inboard_cup_lip"),
        material=CAST_IRON,
        name="cup_lip",
    )
    inboard.visual(
        _x_cylinder(0.110, 0.044),
        origin=_origin_x(-0.166),
        material=CAST_IRON,
        name="differential_flange",
    )
    inboard.visual(
        _x_cylinder(0.050, 0.055),
        origin=_origin_x(-0.182),
        material=BRIGHT_STEEL,
        name="input_stub",
    )
    for i in range(6):
        angle = 2.0 * math.pi * i / 6.0
        y = 0.082 * math.cos(angle)
        z = 0.082 * math.sin(angle)
        inboard.visual(
            _x_cylinder(0.0085, 0.020),
            origin=_origin_x(-0.198, y, z),
            material=ZINC,
            name=f"flange_bolt_{i}",
        )
    for i in range(3):
        angle = 2.0 * math.pi * i / 3.0 + math.pi / 6.0
        y = 0.084 * math.cos(angle)
        z = 0.084 * math.sin(angle)
        inboard.visual(
            _x_cylinder(0.009, 0.112),
            origin=_origin_x(-0.070, y, z),
            material=CAST_IRON,
            name=f"tulip_rib_{i}",
        )
    inboard.visual(
        Box((0.036, 0.050, 0.060)),
        origin=Origin(xyz=(0.0, 0.077, 0.0)),
        material=CAST_IRON,
        name="pivot_ear_0",
    )
    inboard.visual(
        Box((0.036, 0.050, 0.060)),
        origin=Origin(xyz=(0.0, -0.077, 0.0)),
        material=CAST_IRON,
        name="pivot_ear_1",
    )

    gimbal = model.part("inboard_tripod")
    gimbal.visual(
        Sphere(0.043),
        origin=Origin(),
        material=BRIGHT_STEEL,
        name="tripod_core",
    )
    gimbal.visual(
        _x_cylinder(0.026, 0.070),
        origin=_origin_x(0.035),
        material=BRIGHT_STEEL,
        name="splined_neck",
    )
    gimbal.visual(
        Cylinder(radius=0.010, length=0.104),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=BRIGHT_STEEL,
        name="cross_pin",
    )
    for i in range(3):
        angle = 2.0 * math.pi * i / 3.0 + math.pi / 2.0
        y = 0.045 * math.cos(angle)
        z = 0.045 * math.sin(angle)
        gimbal.visual(
            Sphere(0.010),
            origin=Origin(xyz=(0.0, y, z)),
            material=BRIGHT_STEEL,
            name=f"roller_{i}",
        )

    shaft = model.part("shaft")
    shaft.visual(
        _x_cylinder(0.030, 0.060),
        origin=_origin_x(0.030),
        material=BRIGHT_STEEL,
        name="inboard_spline",
    )
    shaft.visual(
        _x_cylinder(0.024, 0.540),
        origin=_origin_x(0.330),
        material=STEEL,
        name="shaft_tube",
    )
    shaft.visual(
        _x_cylinder(0.031, 0.060),
        origin=_origin_x(0.650),
        material=BRIGHT_STEEL,
        name="outboard_spline",
    )
    # Corrugated rubber boots at both CV ends, built from overlapping rings so
    # they read as one supported boot rather than separate floating bands.
    for i, x in enumerate((0.075, 0.095, 0.115, 0.135)):
        shaft.visual(
            _x_cylinder(0.040 + 0.003 * (i % 2), 0.026),
            origin=_origin_x(x),
            material=RUBBER,
            name=f"inboard_boot_{i}",
        )
    for i, x in enumerate((0.545, 0.568, 0.591, 0.614, 0.637)):
        shaft.visual(
            _x_cylinder(0.036 + 0.004 * (i % 2), 0.030),
            origin=_origin_x(x),
            material=RUBBER,
            name=f"outboard_boot_{i}",
        )

    hub = model.part("wheel_hub")
    hub.visual(
        _x_cylinder(0.034, 0.040),
        origin=_origin_x(0.020),
        material=BRIGHT_STEEL,
        name="cv_input_stub",
    )
    hub.visual(
        Sphere(0.072),
        origin=Origin(xyz=(0.088, 0.0, 0.0)),
        material=CAST_IRON,
        name="outboard_cv_body",
    )
    hub.visual(
        _x_cylinder(0.050, 0.080),
        origin=_origin_x(0.152),
        material=BRIGHT_STEEL,
        name="bearing_barrel",
    )
    hub.visual(
        _x_cylinder(0.116, 0.040),
        origin=_origin_x(0.205),
        material=CAST_IRON,
        name="wheel_flange",
    )
    hub.visual(
        _x_cylinder(0.043, 0.036),
        origin=_origin_x(0.243),
        material=BRIGHT_STEEL,
        name="pilot_nose",
    )
    for i in range(5):
        angle = 2.0 * math.pi * i / 5.0 + math.pi / 2.0
        y = 0.078 * math.cos(angle)
        z = 0.078 * math.sin(angle)
        hub.visual(
            _x_cylinder(0.0065, 0.036),
            origin=_origin_x(0.243, y, z),
            material=ZINC,
            name=f"wheel_stud_{i}",
        )

    model.articulation(
        "inboard_angulation",
        ArticulationType.REVOLUTE,
        parent=inboard,
        child=gimbal,
        origin=Origin(),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=120.0, velocity=2.5, lower=-0.32, upper=0.32),
    )
    model.articulation(
        "shaft_spin",
        ArticulationType.CONTINUOUS,
        parent=gimbal,
        child=shaft,
        origin=Origin(xyz=(0.070, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=80.0, velocity=80.0),
    )
    model.articulation(
        "hub_spin",
        ArticulationType.CONTINUOUS,
        parent=shaft,
        child=hub,
        origin=Origin(xyz=(0.680, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=80.0, velocity=80.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
