# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cannon, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cannon

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
def _x_cylinder_origin(x: float, y: float, z: float) -> Origin:
    return Origin(xyz=(x, y, z), rpy=(0.0, math.pi / 2.0, 0.0))
def _y_cylinder_origin(x: float, y: float, z: float) -> Origin:
    return Origin(xyz=(x, y, z), rpy=(math.pi / 2.0, 0.0, 0.0))
def _hollow_x_tube(*, outer_radius: float, inner_radius: float, length: float, x0: float):
    """CadQuery tube along +X with a visible bore."""
    return (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((x0, 0.0, 0.0))
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="naval_deck_cannon")

    gunmetal = model.material("gunmetal", rgba=(0.13, 0.15, 0.16, 1.0))
    parkerized = model.material("parkerized", rgba=(0.05, 0.055, 0.06, 1.0))
    deck_gray = model.material("deck_gray", rgba=(0.30, 0.32, 0.34, 1.0))
    worn_steel = model.material("worn_steel", rgba=(0.52, 0.54, 0.55, 1.0))
    brass = model.material("oiled_bronze", rgba=(0.72, 0.55, 0.25, 1.0))
    shadow = model.material("bore_shadow", rgba=(0.005, 0.005, 0.004, 1.0))

    pedestal = model.part("pedestal")
    pedestal.visual(
        Cylinder(radius=0.62, length=0.10),
        origin=Origin(xyz=(0.0, 0.0, 0.05)),
        material=deck_gray,
        name="deck_flange",
    )
    pedestal.visual(
        Cylinder(radius=0.48, length=0.10),
        origin=Origin(xyz=(0.0, 0.0, 0.135)),
        material=gunmetal,
        name="lower_plinth",
    )
    pedestal.visual(
        Cylinder(radius=0.28, length=0.74),
        origin=Origin(xyz=(0.0, 0.0, 0.545)),
        material=gunmetal,
        name="pedestal_column",
    )
    pedestal.visual(
        Cylinder(radius=0.52, length=0.12),
        origin=Origin(xyz=(0.0, 0.0, 0.965)),
        material=deck_gray,
        name="top_bearing",
    )
    pedestal.visual(
        Cylinder(radius=0.22, length=0.08),
        origin=Origin(xyz=(0.0, 0.0, 1.055)),
        material=parkerized,
        name="center_spigot",
    )
    for index in range(12):
        angle = math.tau * index / 12.0
        x = 0.50 * math.cos(angle)
        y = 0.50 * math.sin(angle)
        pedestal.visual(
            Cylinder(radius=0.026, length=0.035),
            origin=Origin(xyz=(x, y, 0.107)),
            material=worn_steel,
            name=f"deck_bolt_{index:02d}",
        )
    for index in range(8):
        angle = math.tau * index / 8.0 + math.pi / 8.0
        x = 0.46 * math.cos(angle)
        y = 0.46 * math.sin(angle)
        pedestal.visual(
            Cylinder(radius=0.020, length=0.030),
            origin=Origin(xyz=(x, y, 1.035)),
            material=worn_steel,
            name=f"bearing_bolt_{index:02d}",
        )
    pedestal.inertial = Inertial.from_geometry(
        Cylinder(radius=0.62, length=1.10),
        mass=1850.0,
        origin=Origin(xyz=(0.0, 0.0, 0.55)),
    )

    carriage = model.part("carriage")
    carriage.visual(
        Cylinder(radius=0.39, length=0.10),
        origin=Origin(xyz=(0.0, 0.0, 0.05)),
        material=gunmetal,
        name="turntable_disk",
    )
    carriage.visual(
        Cylinder(radius=0.31, length=0.075),
        origin=Origin(xyz=(0.0, 0.0, 0.137)),
        material=parkerized,
        name="slew_housing",
    )
    carriage.visual(
        Box((0.74, 0.080, 0.52)),
        origin=Origin(xyz=(0.06, 0.240, 0.355)),
        material=gunmetal,
        name="cheek_0",
    )
    carriage.visual(
        Box((0.74, 0.080, 0.52)),
        origin=Origin(xyz=(0.06, -0.240, 0.355)),
        material=gunmetal,
        name="cheek_1",
    )
    carriage.visual(
        Box((0.28, 0.58, 0.10)),
        origin=Origin(xyz=(-0.24, 0.0, 0.155)),
        material=gunmetal,
        name="rear_crossmember",
    )
    carriage.visual(
        Box((0.20, 0.58, 0.09)),
        origin=Origin(xyz=(0.32, 0.0, 0.145)),
        material=gunmetal,
        name="front_crossmember",
    )
    carriage.visual(
        Cylinder(radius=0.135, length=0.105),
        origin=_y_cylinder_origin(0.0, 0.2475, 0.420),
        material=worn_steel,
        name="bearing_cap_0",
    )
    carriage.visual(
        Cylinder(radius=0.092, length=0.112),
        origin=_y_cylinder_origin(0.0, 0.2475, 0.420),
        material=brass,
        name="bearing_bush_0",
    )
    carriage.visual(
        Cylinder(radius=0.135, length=0.105),
        origin=_y_cylinder_origin(0.0, -0.2475, 0.420),
        material=worn_steel,
        name="bearing_cap_1",
    )
    carriage.visual(
        Cylinder(radius=0.092, length=0.112),
        origin=_y_cylinder_origin(0.0, -0.2475, 0.420),
        material=brass,
        name="bearing_bush_1",
    )
    for index, y in enumerate((0.255, -0.255)):
        carriage.visual(
            Box((0.08, 0.05, 0.33)),
            origin=Origin(xyz=(-0.19, y, 0.275), rpy=(0.0, -0.35, 0.0)),
            material=parkerized,
            name=f"rear_rib_{index}",
        )
        carriage.visual(
            Box((0.08, 0.05, 0.33)),
            origin=Origin(xyz=(0.29, y, 0.265), rpy=(0.0, 0.34, 0.0)),
            material=parkerized,
            name=f"front_rib_{index}",
        )
    carriage.visual(
        Box((0.34, 0.58, 0.08)),
        origin=Origin(xyz=(-0.10, 0.0, 0.655)),
        material=parkerized,
        name="top_tie",
    )
    carriage.inertial = Inertial.from_geometry(
        Box((0.82, 0.62, 0.66)),
        mass=900.0,
        origin=Origin(xyz=(0.05, 0.0, 0.32)),
    )

    barrel_tube = mesh_from_cadquery(
        _hollow_x_tube(outer_radius=0.092, inner_radius=0.038, length=1.18, x0=-0.02),
        "rifled_barrel_tube",
        tolerance=0.001,
        angular_tolerance=0.08,
    )
    muzzle_ring = mesh_from_cadquery(
        _hollow_x_tube(outer_radius=0.130, inner_radius=0.052, length=0.13, x0=1.08),
        "muzzle_reinforce_mesh",
        tolerance=0.001,
        angular_tolerance=0.08,
    )

    barrel = model.part("barrel")
    barrel.visual(
        Cylinder(radius=0.073, length=0.390),
        origin=_y_cylinder_origin(0.0, 0.0, 0.0),
        material=worn_steel,
        name="trunnion_pin",
    )
    barrel.visual(
        Cylinder(radius=0.155, length=0.30),
        origin=_x_cylinder_origin(-0.145, 0.0, 0.0),
        material=gunmetal,
        name="breech_reinforce",
    )
    barrel.visual(
        Sphere(radius=0.135),
        origin=Origin(xyz=(-0.315, 0.0, 0.0)),
        material=gunmetal,
        name="rounded_cascabel",
    )
    barrel.visual(
        Cylinder(radius=0.085, length=0.055),
        origin=_x_cylinder_origin(-0.425, 0.0, 0.0),
        material=brass,
        name="breech_knob",
    )
    barrel.visual(
        barrel_tube,
        material=gunmetal,
        name="barrel_tube",
    )
    barrel.visual(
        muzzle_ring,
        material=gunmetal,
        name="muzzle_reinforce",
    )
    barrel.visual(
        Cylinder(radius=0.054, length=0.010),
        origin=_x_cylinder_origin(1.205, 0.0, 0.0),
        material=shadow,
        name="bore_shadow",
    )
    barrel.visual(
        Cylinder(radius=0.112, length=0.070),
        origin=_x_cylinder_origin(0.060, 0.0, 0.0),
        material=parkerized,
        name="trunnion_band",
    )
    barrel.inertial = Inertial.from_geometry(
        Cylinder(radius=0.16, length=1.66),
        mass=1250.0,
        origin=_x_cylinder_origin(0.42, 0.0, 0.0),
    )

    model.articulation(
        "traverse",
        ArticulationType.CONTINUOUS,
        parent=pedestal,
        child=carriage,
        origin=Origin(xyz=(0.0, 0.0, 1.025)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=60000.0, velocity=0.55),
    )
    model.articulation(
        "elevation",
        ArticulationType.REVOLUTE,
        parent=carriage,
        child=barrel,
        origin=Origin(xyz=(0.0, 0.0, 0.420)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=42000.0, velocity=0.35, lower=-0.10, upper=0.45),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
