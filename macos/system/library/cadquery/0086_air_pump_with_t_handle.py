# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_pump_with_t_handle, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_pump_with_t_handle

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
def _hollow_cylinder(length: float, outer_radius: float, inner_radius: float):
    """CadQuery tube centered on local Z with open ends."""
    outer = cq.Workplane("XY").circle(outer_radius).extrude(length)
    inner = (
        cq.Workplane("XY")
        .circle(inner_radius)
        .extrude(length + 0.020)
        .translate((0.0, 0.0, -0.010))
    )
    return outer.cut(inner).translate((0.0, 0.0, -length / 2.0))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="industrial_floor_air_pump")

    painted_steel = Material("painted_steel", rgba=(0.10, 0.15, 0.18, 1.0))
    blue_enamel = Material("blue_enamel", rgba=(0.02, 0.16, 0.42, 1.0))
    black_rubber = Material("black_rubber", rgba=(0.01, 0.01, 0.01, 1.0))
    polished_steel = Material("polished_steel", rgba=(0.72, 0.74, 0.76, 1.0))
    gauge_white = Material("gauge_face_white", rgba=(0.92, 0.90, 0.82, 1.0))
    red = Material("release_red", rgba=(0.85, 0.04, 0.02, 1.0))
    needle_red = Material("needle_red", rgba=(0.80, 0.02, 0.02, 1.0))

    frame = model.part("frame")
    frame.visual(
        Box((0.24, 0.16, 0.036)),
        origin=Origin(xyz=(0.0, 0.0, 0.018)),
        material=painted_steel,
        name="base_plate",
    )
    frame.visual(
        Box((0.52, 0.082, 0.010)),
        origin=Origin(xyz=(0.0, 0.0, 0.041)),
        material=painted_steel,
        name="guide_floor",
    )
    frame.visual(
        Box((0.52, 0.014, 0.056)),
        origin=Origin(xyz=(0.0, -0.034, 0.064)),
        material=painted_steel,
        name="guide_side_0",
    )
    frame.visual(
        Box((0.52, 0.014, 0.056)),
        origin=Origin(xyz=(0.0, 0.034, 0.064)),
        material=painted_steel,
        name="guide_side_1",
    )
    frame.visual(
        Box((0.52, 0.082, 0.010)),
        origin=Origin(xyz=(0.0, 0.0, 0.089)),
        material=painted_steel,
        name="guide_top",
    )
    frame.visual(
        mesh_from_cadquery(_hollow_cylinder(0.82, 0.055, 0.030), "barrel_shell"),
        origin=Origin(xyz=(0.0, 0.0, 0.545)),
        material=blue_enamel,
        name="barrel_shell",
    )
    frame.visual(
        mesh_from_cadquery(_hollow_cylinder(0.055, 0.070, 0.030), "lower_collar"),
        origin=Origin(xyz=(0.0, 0.0, 0.125)),
        material=painted_steel,
        name="lower_collar",
    )
    frame.visual(
        mesh_from_cadquery(_hollow_cylinder(0.045, 0.067, 0.026), "upper_collar"),
        origin=Origin(xyz=(0.0, 0.0, 0.975)),
        material=painted_steel,
        name="upper_collar",
    )
    for i, y in enumerate((-0.050, 0.050)):
        frame.visual(
            Box((0.090, 0.020, 0.070)),
            origin=Origin(xyz=(0.0, y, 0.095)),
            material=painted_steel,
            name=f"side_bracket_{i}",
        )
    for x in (-0.052, 0.052):
        frame.visual(
            Cylinder(radius=0.007, length=0.760),
            origin=Origin(xyz=(x, 0.033, 0.540)),
            material=polished_steel,
            name=f"tie_rod_{0 if x < 0 else 1}",
        )

    # Gauge housing and fixed gauge details on the front of the cylinder.
    frame.visual(
        Cylinder(radius=0.017, length=0.058),
        origin=Origin(xyz=(0.0, -0.080, 0.735), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=painted_steel,
        name="gauge_neck",
    )
    frame.visual(
        Cylinder(radius=0.078, length=0.060),
        origin=Origin(xyz=(0.0, -0.135, 0.735), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=painted_steel,
        name="gauge_body",
    )
    frame.visual(
        Cylinder(radius=0.064, length=0.004),
        origin=Origin(xyz=(0.0, -0.167, 0.735), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=gauge_white,
        name="gauge_face",
    )
    frame.visual(
        Box((0.008, 0.002, 0.056)),
        origin=Origin(xyz=(0.018, -0.170, 0.753), rpy=(0.0, 0.42, 0.0)),
        material=needle_red,
        name="gauge_needle",
    )
    for i, (x, z, sx, sz) in enumerate(
        (
            (0.0, 0.792, 0.006, 0.016),
            (-0.046, 0.735, 0.014, 0.006),
            (0.046, 0.735, 0.014, 0.006),
            (-0.030, 0.775, 0.010, 0.006),
            (0.030, 0.775, 0.010, 0.006),
        )
    ):
        frame.visual(
            Box((sx, 0.002, sz)),
            origin=Origin(xyz=(x, -0.170, z)),
            material=painted_steel,
            name=f"gauge_tick_{i}",
        )
    frame.visual(
        Cylinder(radius=0.018, length=0.006),
        origin=Origin(xyz=(0.050, -0.166, 0.675), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=black_rubber,
        name="button_collar",
    )

    piston = model.part("piston")
    piston.visual(
        Cylinder(radius=0.012, length=0.840),
        origin=Origin(xyz=(0.0, 0.0, -0.280)),
        material=polished_steel,
        name="piston_rod",
    )
    piston.visual(
        Cylinder(radius=0.018, length=0.110),
        origin=Origin(xyz=(0.0, 0.0, 0.096)),
        material=polished_steel,
        name="handle_stem",
    )
    piston.visual(
        Cylinder(radius=0.036, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=polished_steel,
        name="plunger_stop",
    )
    piston.visual(
        Cylinder(radius=0.034, length=0.430),
        origin=Origin(xyz=(0.0, 0.0, 0.165), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=black_rubber,
        name="t_handle_pad",
    )
    piston.visual(
        Sphere(radius=0.034),
        origin=Origin(xyz=(0.0, -0.215, 0.165)),
        material=black_rubber,
        name="handle_end_0",
    )
    piston.visual(
        Sphere(radius=0.034),
        origin=Origin(xyz=(0.0, 0.215, 0.165)),
        material=black_rubber,
        name="handle_end_1",
    )

    stabilizer = model.part("stabilizer")
    stabilizer.visual(
        Box((0.820, 0.042, 0.030)),
        origin=Origin(xyz=(0.0, 0.0, -0.003)),
        material=black_rubber,
        name="slide_bar",
    )
    stabilizer.visual(
        Box((0.120, 0.070, 0.018)),
        origin=Origin(xyz=(-0.380, 0.0, -0.022)),
        material=black_rubber,
        name="foot_pad_0",
    )
    stabilizer.visual(
        Box((0.120, 0.070, 0.018)),
        origin=Origin(xyz=(0.380, 0.0, -0.022)),
        material=black_rubber,
        name="foot_pad_1",
    )

    release_button = model.part("release_button")
    release_button.visual(
        Cylinder(radius=0.012, length=0.024),
        origin=Origin(xyz=(0.0, -0.012, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=red,
        name="button_cap",
    )
    release_button.visual(
        Sphere(radius=0.012),
        origin=Origin(xyz=(0.0, -0.024, 0.0)),
        material=red,
        name="button_dome",
    )

    model.articulation(
        "frame_to_piston",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=piston,
        origin=Origin(xyz=(0.0, 0.0, 0.9975)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=180.0, velocity=0.7, lower=0.0, upper=0.420),
    )
    model.articulation(
        "frame_to_stabilizer",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=stabilizer,
        origin=Origin(xyz=(0.0, 0.0, 0.064)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=80.0, velocity=0.35, lower=-0.180, upper=0.180),
    )
    model.articulation(
        "frame_to_release_button",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=release_button,
        origin=Origin(xyz=(0.050, -0.169, 0.675)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=0.04, lower=0.0, upper=0.010),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
