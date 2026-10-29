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
def _cyl_x(radius: float, length: float) -> tuple[Cylinder, Origin]:
    return Cylinder(radius=radius, length=length), Origin(rpy=(0.0, math.pi / 2.0, 0.0))
def _annular_x(outer_radius: float, inner_radius: float, length: float) -> cq.Workplane:
    """A centered annular cylinder whose axis is the local X axis."""
    return (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length, both=True)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="maksutov_alt_az_telescope")

    satin_black = model.material("satin_black", rgba=(0.01, 0.012, 0.014, 1.0))
    graphite = model.material("graphite_mount", rgba=(0.10, 0.11, 0.12, 1.0))
    dark_gray = model.material("dark_gray", rgba=(0.20, 0.21, 0.22, 1.0))
    rubber = model.material("rubber_feet", rgba=(0.025, 0.025, 0.023, 1.0))
    white = model.material("warm_white_tube", rgba=(0.86, 0.86, 0.80, 1.0))
    glass = model.material("blue_coated_glass", rgba=(0.20, 0.38, 0.55, 0.58))
    mirror = model.material("black_mirror_spot", rgba=(0.005, 0.007, 0.010, 1.0))
    metal = model.material("machined_metal", rgba=(0.55, 0.56, 0.55, 1.0))

    tripod = model.part("tripod")
    tripod.visual(
        Cylinder(radius=0.045, length=0.72),
        origin=Origin(xyz=(0.0, 0.0, 0.39)),
        material=dark_gray,
        name="center_column",
    )
    tripod.visual(
        Cylinder(radius=0.13, length=0.08),
        origin=Origin(xyz=(0.0, 0.0, 0.74)),
        material=graphite,
        name="tripod_collar",
    )
    tripod.visual(
        Cylinder(radius=0.16, length=0.08),
        origin=Origin(xyz=(0.0, 0.0, 0.92)),
        material=graphite,
        name="az_bearing_base",
    )
    tripod.visual(
        Cylinder(radius=0.075, length=0.16),
        origin=Origin(xyz=(0.0, 0.0, 0.82)),
        material=graphite,
        name="head_neck",
    )

    leg_top_z = 0.72
    leg_foot_z = 0.08
    leg_radius = 0.58
    leg_len = math.sqrt(leg_radius**2 + (leg_top_z - leg_foot_z) ** 2)
    leg_pitch = math.asin((leg_top_z - leg_foot_z) / leg_len)
    for idx, yaw in enumerate((math.radians(90), math.radians(210), math.radians(330))):
        foot_x = leg_radius * math.cos(yaw)
        foot_y = leg_radius * math.sin(yaw)
        center = (foot_x / 2.0, foot_y / 2.0, (leg_top_z + leg_foot_z) / 2.0)
        tripod.visual(
            Box((leg_len, 0.045, 0.035)),
            origin=Origin(xyz=center, rpy=(0.0, leg_pitch, yaw)),
            material=dark_gray,
            name=f"leg_{idx}",
        )
        tripod.visual(
            Box((0.16, 0.075, 0.080)),
            origin=Origin(xyz=(foot_x, foot_y, 0.045), rpy=(0.0, 0.0, yaw)),
            material=rubber,
            name=f"foot_{idx}",
        )
    for idx, yaw in enumerate((math.radians(30), math.radians(150), math.radians(270))):
        tripod.visual(
            Box((0.38, 0.025, 0.020)),
            origin=Origin(
                xyz=(0.19 * math.cos(yaw), 0.19 * math.sin(yaw), 0.36),
                rpy=(0.0, 0.0, yaw),
            ),
            material=graphite,
            name=f"spreader_{idx}",
        )

    arm = model.part("arm")
    arm.visual(
        Cylinder(radius=0.145, length=0.060),
        origin=Origin(xyz=(0.0, 0.0, 0.030)),
        material=graphite,
        name="az_turntable",
    )
    arm.visual(
        Cylinder(radius=0.115, length=0.070),
        origin=Origin(xyz=(0.0, 0.0, 0.095)),
        material=dark_gray,
        name="motor_dome",
    )
    arm.visual(
        Box((0.18, 0.34, 0.08)),
        origin=Origin(xyz=(0.0, -0.17, 0.105)),
        material=graphite,
        name="arm_foot",
    )
    arm.visual(
        Box((0.135, 0.105, 0.44)),
        origin=Origin(xyz=(0.0, -0.30, 0.285)),
        material=graphite,
        name="upright",
    )
    arm.visual(
        Cylinder(radius=0.090, length=0.140),
        origin=Origin(xyz=(0.0, -0.30, 0.58), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_gray,
        name="alt_bearing",
    )
    arm.visual(
        Box((0.15, 0.11, 0.08)),
        origin=Origin(xyz=(0.0, -0.30, 0.475)),
        material=graphite,
        name="bearing_boss",
    )

    tube = model.part("tube")
    tube_shell = mesh_from_cadquery(_annular_x(0.145, 0.125, 0.44), "maksutov_tube_shell")
    tube.visual(
        tube_shell,
        origin=Origin(xyz=(0.0, 0.30, 0.0)),
        material=white,
        name="tube_shell",
    )
    front_cell = mesh_from_cadquery(_annular_x(0.154, 0.112, 0.045), "front_corrector_cell")
    tube.visual(
        front_cell,
        origin=Origin(xyz=(0.222, 0.30, 0.0)),
        material=satin_black,
        name="front_cell",
    )
    rear_cell = mesh_from_cadquery(_annular_x(0.148, 0.050, 0.055), "rear_visual_cell")
    tube.visual(
        rear_cell,
        origin=Origin(xyz=(-0.238, 0.30, 0.0)),
        material=satin_black,
        name="rear_cell",
    )
    cx, co = _cyl_x(0.118, 0.010)
    tube.visual(
        cx,
        origin=Origin(xyz=(0.246, 0.30, 0.0), rpy=co.rpy),
        material=glass,
        name="corrector_lens",
    )
    tube.visual(
        Cylinder(radius=0.035, length=0.006),
        origin=Origin(xyz=(0.252, 0.30, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=mirror,
        name="secondary_spot",
    )
    tube.visual(
        Box((0.17, 0.06, 0.09)),
        origin=Origin(xyz=(-0.292, 0.30, 0.0)),
        material=satin_black,
        name="rear_back",
    )
    tube.visual(
        Cylinder(radius=0.030, length=0.095),
        origin=Origin(xyz=(-0.345, 0.30, -0.015), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal,
        name="eyepiece_tube",
    )
    tube.visual(
        Cylinder(radius=0.022, length=0.055),
        origin=Origin(xyz=(-0.403, 0.30, -0.015), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=satin_black,
        name="eyepiece",
    )
    tube.visual(
        Cylinder(radius=0.055, length=0.200),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="alt_shaft",
    )
    tube.visual(
        Box((0.21, 0.115, 0.110)),
        origin=Origin(xyz=(0.0, 0.135, 0.0)),
        material=satin_black,
        name="side_saddle",
    )
    tube.visual(
        Box((0.33, 0.045, 0.050)),
        origin=Origin(xyz=(0.0, 0.176, 0.0)),
        material=satin_black,
        name="dovetail_bar",
    )
    finder_geom = mesh_from_cadquery(_annular_x(0.033, 0.024, 0.25), "finder_scope_tube")
    tube.visual(
        finder_geom,
        origin=Origin(xyz=(0.010, 0.30, 0.205)),
        material=satin_black,
        name="finder_scope",
    )
    tube.visual(
        Box((0.038, 0.035, 0.085)),
        origin=Origin(xyz=(-0.080, 0.30, 0.157)),
        material=satin_black,
        name="finder_stem_0",
    )
    tube.visual(
        Box((0.038, 0.035, 0.085)),
        origin=Origin(xyz=(0.100, 0.30, 0.157)),
        material=satin_black,
        name="finder_stem_1",
    )

    model.articulation(
        "azimuth",
        ArticulationType.CONTINUOUS,
        parent=tripod,
        child=arm,
        origin=Origin(xyz=(0.0, 0.0, 0.960)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=30.0, velocity=1.5),
    )
    model.articulation(
        "altitude",
        ArticulationType.REVOLUTE,
        parent=arm,
        child=tube,
        origin=Origin(xyz=(0.0, -0.30, 0.58)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.2, lower=-0.30, upper=1.35),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
