# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, astronomical_telescope_on_tripod, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: astronomical_telescope_on_tripod

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
def _axis_rpy_from_z(p0: tuple[float, float, float], p1: tuple[float, float, float]) -> tuple[float, float, float]:
    """Return an rpy rotation that aligns a local +Z cylinder with p0 -> p1."""
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dz = p1[2] - p0[2]
    horizontal = math.hypot(dx, dy)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(horizontal, dz)
    return (0.0, pitch, yaw)
def _cylinder_between(part, p0, p1, *, radius: float, material, name: str) -> None:
    length = math.dist(p0, p1)
    mid = tuple((a + b) * 0.5 for a, b in zip(p0, p1))
    part.visual(
        Cylinder(radius=radius, length=length),
        origin=Origin(xyz=mid, rpy=_axis_rpy_from_z(p0, p1)),
        material=material,
        name=name,
    )
def _annular_x_tube(outer_radius: float, inner_radius: float, length: float):
    """Open cylindrical shell along local X for optical tubes."""
    return (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length, both=True)
    )
def _annular_z_ring(outer_radius: float, inner_radius: float, height: float):
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height, both=True)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="refractor_spotting_scope_tripod")

    satin_black = model.material("satin_black", rgba=(0.02, 0.023, 0.026, 1.0))
    graphite = model.material("graphite", rgba=(0.18, 0.19, 0.20, 1.0))
    anodized = model.material("anodized_aluminum", rgba=(0.38, 0.40, 0.42, 1.0))
    rubber = model.material("matte_rubber", rgba=(0.015, 0.015, 0.014, 1.0))
    glass = model.material("coated_glass", rgba=(0.13, 0.32, 0.48, 0.62))
    screw_metal = model.material("screw_metal", rgba=(0.72, 0.73, 0.70, 1.0))

    tripod = model.part("tripod")
    tripod.visual(
        Cylinder(radius=0.030, length=0.53),
        origin=Origin(xyz=(0.0, 0.0, 0.555)),
        material=anodized,
        name="center_column",
    )
    tripod.visual(
        Cylinder(radius=0.075, length=0.055),
        origin=Origin(xyz=(0.0, 0.0, 0.700)),
        material=graphite,
        name="leg_hub",
    )
    tripod.visual(
        Cylinder(radius=0.090, length=0.030),
        origin=Origin(xyz=(0.0, 0.0, 0.825)),
        material=graphite,
        name="top_plate",
    )
    tripod.visual(
        Cylinder(radius=0.038, length=0.055),
        origin=Origin(xyz=(0.0, 0.0, 0.782)),
        material=graphite,
        name="column_collar",
    )
    for i in range(3):
        a = 2.0 * math.pi * i / 3.0 + math.radians(30)
        top = (0.075 * math.cos(a), 0.075 * math.sin(a), 0.700)
        foot = (0.50 * math.cos(a), 0.50 * math.sin(a), 0.055)
        _cylinder_between(
            tripod,
            top,
            foot,
            radius=0.018,
            material=anodized,
            name=f"leg_{i}",
        )
        brace_top = (0.032 * math.cos(a), 0.032 * math.sin(a), 0.525)
        brace_foot = (0.355 * math.cos(a), 0.355 * math.sin(a), 0.245)
        _cylinder_between(
            tripod,
            brace_top,
            brace_foot,
            radius=0.010,
            material=graphite,
            name=f"brace_{i}",
        )
        tripod.visual(
            Box((0.14, 0.055, 0.020)),
            origin=Origin(xyz=foot, rpy=(0.0, 0.0, a)),
            material=rubber,
            name=f"foot_{i}",
        )
    tripod.inertial = Inertial.from_geometry(
        Cylinder(radius=0.55, length=0.85),
        mass=2.4,
        origin=Origin(xyz=(0.0, 0.0, 0.425)),
    )

    pan_head = model.part("pan_head")
    pan_head.visual(
        Cylinder(radius=0.080, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, 0.0175)),
        material=satin_black,
        name="pan_disc",
    )
    pan_head.visual(
        Cylinder(radius=0.036, length=0.062),
        origin=Origin(xyz=(0.0, 0.0, 0.066)),
        material=satin_black,
        name="pedestal_stem",
    )
    pan_head.visual(
        Cylinder(radius=0.065, length=0.030),
        origin=Origin(xyz=(0.0, 0.0, 0.085)),
        material=graphite,
        name="socket_flare",
    )
    pan_head.visual(
        mesh_from_cadquery(_annular_z_ring(0.078, 0.045, 0.020), "socket_ring"),
        origin=Origin(xyz=(0.0, 0.0, 0.105)),
        material=graphite,
        name="socket_ring",
    )
    pan_head.visual(
        Cylinder(radius=0.008, length=0.105),
        origin=Origin(xyz=(0.0, 0.102, 0.025), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=screw_metal,
        name="pan_lock_stem",
    )
    pan_head.visual(
        Cylinder(radius=0.018, length=0.030),
        origin=Origin(xyz=(0.0, 0.163, 0.025), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=rubber,
        name="pan_lock_knob",
    )
    pan_head.inertial = Inertial.from_geometry(
        Cylinder(radius=0.085, length=0.14),
        mass=0.55,
        origin=Origin(xyz=(0.0, 0.0, 0.070)),
    )

    tilt_head = model.part("tilt_head")
    tilt_head.visual(Sphere(radius=0.055), material=satin_black, name="ball")
    tilt_head.visual(
        Cylinder(radius=0.018, length=0.092),
        origin=Origin(xyz=(0.0, 0.0, 0.087)),
        material=satin_black,
        name="neck_post",
    )
    tilt_head.visual(
        Box((0.190, 0.130, 0.018)),
        origin=Origin(xyz=(0.0, 0.0, 0.137)),
        material=graphite,
        name="saddle_plate",
    )
    tilt_head.visual(
        Box((0.055, 0.014, 0.036)),
        origin=Origin(xyz=(-0.065, 0.062, 0.161)),
        material=graphite,
        name="clamp_lug_0",
    )
    tilt_head.visual(
        Box((0.055, 0.014, 0.036)),
        origin=Origin(xyz=(0.065, -0.062, 0.161)),
        material=graphite,
        name="clamp_lug_1",
    )
    tilt_head.visual(
        Cylinder(radius=0.007, length=0.090),
        origin=Origin(xyz=(0.0, -0.060, 0.100), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=screw_metal,
        name="tilt_lock_stem",
    )
    tilt_head.visual(
        Cylinder(radius=0.018, length=0.028),
        origin=Origin(xyz=(0.0, -0.115, 0.100), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=rubber,
        name="tilt_lock_knob",
    )
    tilt_head.inertial = Inertial.from_geometry(
        Sphere(radius=0.10),
        mass=0.75,
        origin=Origin(xyz=(0.0, 0.0, 0.090)),
    )

    scope = model.part("scope")
    scope.visual(
        mesh_from_cadquery(_annular_x_tube(0.050, 0.041, 0.480), "main_tube_shell"),
        material=satin_black,
        name="main_tube",
    )
    scope.visual(
        mesh_from_cadquery(_annular_x_tube(0.064, 0.049, 0.140), "dew_shield_shell"),
        origin=Origin(xyz=(0.245, 0.0, 0.0)),
        material=satin_black,
        name="dew_shield",
    )
    scope.visual(
        Cylinder(radius=0.049, length=0.008),
        origin=Origin(xyz=(0.315, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass,
        name="front_lens",
    )
    scope.visual(
        Cylinder(radius=0.056, length=0.052),
        origin=Origin(xyz=(-0.155, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=rubber,
        name="focus_ring",
    )
    scope.visual(
        Box((0.170, 0.048, 0.012)),
        origin=Origin(xyz=(0.0, 0.0, -0.044)),
        material=graphite,
        name="dovetail_foot",
    )
    scope.visual(
        Cylinder(radius=0.043, length=0.065),
        origin=Origin(xyz=(-0.270, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=graphite,
        name="rear_cell",
    )
    _cylinder_between(
        scope,
        (-0.300, 0.0, 0.020),
        (-0.360, 0.0, 0.090),
        radius=0.026,
        material=graphite,
        name="diagonal_body",
    )
    _cylinder_between(
        scope,
        (-0.356, 0.0, 0.085),
        (-0.418, 0.0, 0.156),
        radius=0.021,
        material=rubber,
        name="eyepiece_barrel",
    )
    scope.visual(
        Cylinder(radius=0.019, length=0.006),
        origin=Origin(xyz=(-0.420, 0.0, 0.158), rpy=_axis_rpy_from_z((-0.356, 0.0, 0.085), (-0.418, 0.0, 0.156))),
        material=glass,
        name="eyepiece_glass",
    )
    scope.inertial = Inertial.from_geometry(
        Cylinder(radius=0.07, length=0.62),
        mass=1.35,
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
    )

    model.articulation(
        "pan_bearing",
        ArticulationType.CONTINUOUS,
        parent=tripod,
        child=pan_head,
        origin=Origin(xyz=(0.0, 0.0, 0.840)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.2),
    )
    model.articulation(
        "tilt_axis",
        ArticulationType.REVOLUTE,
        parent=pan_head,
        child=tilt_head,
        origin=Origin(xyz=(0.0, 0.0, 0.155)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=1.0, lower=-0.55, upper=0.80),
    )
    model.articulation(
        "scope_mount",
        ArticulationType.FIXED,
        parent=tilt_head,
        child=scope,
        origin=Origin(xyz=(0.0, 0.0, 0.196)),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
