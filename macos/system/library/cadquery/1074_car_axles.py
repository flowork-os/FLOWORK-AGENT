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

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
def _add_cylinder_x(part, radius: float, length: float, *, xyz, material, name: str | None = None) -> None:
    part.visual(
        Cylinder(radius=radius, length=length),
        origin=Origin(xyz=xyz, rpy=(0.0, pi / 2.0, 0.0)),
        material=material,
        name=name,
    )
def _add_cylinder_y(part, radius: float, length: float, *, xyz, material, name: str | None = None) -> None:
    part.visual(
        Cylinder(radius=radius, length=length),
        origin=Origin(xyz=xyz, rpy=(pi / 2.0, 0.0, 0.0)),
        material=material,
        name=name,
    )
def _build_half_axle(
    model: ArticulatedObject,
    *,
    name: str,
    side_sign: float,
    tube_paint,
    machined_steel,
    rubber,
):
    part = model.part(name)
    part.inertial = Inertial.from_geometry(
        Box((0.18, 0.58, 0.18)),
        mass=26.0,
        origin=Origin(xyz=(0.0, 0.27 * side_sign, -0.01)),
    )

    part.visual(
        Box((0.140, 0.060, 0.160)),
        origin=Origin(xyz=(0.0, 0.075 * side_sign, 0.0)),
        material=tube_paint,
        name="pivot_bracket",
    )
    _add_cylinder_x(
        part,
        radius=0.040,
        length=0.140,
        xyz=(0.0, 0.030 * side_sign, 0.0),
        material=rubber,
        name="pivot_bushing",
    )
    _add_cylinder_y(
        part,
        radius=0.046,
        length=0.350,
        xyz=(0.0, 0.225 * side_sign, 0.0),
        material=tube_paint,
        name="axle_tube",
    )
    part.visual(
        Box((0.100, 0.200, 0.050)),
        origin=Origin(xyz=(0.0, 0.160 * side_sign, -0.055)),
        material=tube_paint,
        name="lower_brace",
    )
    _add_cylinder_y(
        part,
        radius=0.072,
        length=0.100,
        xyz=(0.0, 0.450 * side_sign, 0.0),
        material=machined_steel,
        name="outer_bell",
    )
    _add_cylinder_y(
        part,
        radius=0.061,
        length=0.020,
        xyz=(0.0, 0.510 * side_sign, 0.0),
        material=machined_steel,
        name="hub_mount_face",
    )
    _add_cylinder_x(
        part,
        radius=0.026,
        length=0.120,
        xyz=(0.0, 0.470 * side_sign, -0.018),
        material=machined_steel,
        name="pivot_reinforcement",
    )
    return part
def _build_hub(
    model: ArticulatedObject,
    *,
    name: str,
    side_sign: float,
    machined_steel,
    dark_steel,
):
    part = model.part(name)
    part.inertial = Inertial.from_geometry(
        Cylinder(radius=0.125, length=0.220),
        mass=10.0,
        origin=Origin(xyz=(0.0, 0.110 * side_sign, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
    )

    _add_cylinder_y(
        part,
        radius=0.056,
        length=0.080,
        xyz=(0.0, 0.040 * side_sign, 0.0),
        material=dark_steel,
        name="inner_collar",
    )
    _add_cylinder_y(
        part,
        radius=0.100,
        length=0.008,
        xyz=(0.0, 0.004 * side_sign, 0.0),
        material=dark_steel,
        name="backing_plate",
    )
    _add_cylinder_y(
        part,
        radius=0.093,
        length=0.120,
        xyz=(0.0, 0.140 * side_sign, 0.0),
        material=machined_steel,
        name="hub_drum",
    )
    _add_cylinder_y(
        part,
        radius=0.125,
        length=0.020,
        xyz=(0.0, 0.210 * side_sign, 0.0),
        material=machined_steel,
        name="wheel_flange",
    )
    _add_cylinder_y(
        part,
        radius=0.034,
        length=0.032,
        xyz=(0.0, 0.226 * side_sign, 0.0),
        material=dark_steel,
        name="dust_cap",
    )
    stud_radius = 0.078
    for stud_index in range(5):
        angle = 2.0 * pi * stud_index / 5.0
        _add_cylinder_y(
            part,
            radius=0.0075,
            length=0.032,
            xyz=(stud_radius * cos(angle), 0.226 * side_sign, stud_radius * sin(angle)),
            material=dark_steel,
        )
    return part
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="swing_axle_rear_suspension")

    beam_paint = model.material("beam_paint", rgba=(0.18, 0.19, 0.20, 1.0))
    cast_iron = model.material("cast_iron", rgba=(0.24, 0.25, 0.27, 1.0))
    tube_paint = model.material("tube_paint", rgba=(0.20, 0.20, 0.21, 1.0))
    machined_steel = model.material("machined_steel", rgba=(0.62, 0.64, 0.67, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.32, 0.33, 0.35, 1.0))
    rubber = model.material("rubber", rgba=(0.08, 0.08, 0.08, 1.0))

    center_beam = model.part("center_beam")
    center_beam.inertial = Inertial.from_geometry(
        Box((1.20, 0.18, 0.22)),
        mass=68.0,
        origin=Origin(xyz=(0.0, 0.0, 0.18)),
    )
    center_beam.visual(
        Box((1.18, 0.14, 0.16)),
        origin=Origin(xyz=(0.0, 0.0, 0.20)),
        material=beam_paint,
        name="beam_main",
    )
    center_beam.visual(
        Box((0.36, 0.16, 0.08)),
        origin=Origin(xyz=(0.0, 0.0, 0.08)),
        material=beam_paint,
        name="beam_saddle",
    )
    center_beam.visual(
        Box((0.14, 0.03, 0.10)),
        origin=Origin(xyz=(0.0, 0.055, 0.10)),
        material=beam_paint,
        name="left_saddle_gusset",
    )
    center_beam.visual(
        Box((0.14, 0.03, 0.10)),
        origin=Origin(xyz=(0.0, -0.055, 0.10)),
        material=beam_paint,
        name="right_saddle_gusset",
    )

    differential_housing = model.part("differential_housing")
    differential_housing.inertial = Inertial.from_geometry(
        Box((0.44, 0.56, 0.34)),
        mass=85.0,
        origin=Origin(xyz=(0.0, 0.0, -0.12)),
    )
    differential_housing.visual(
        Box((0.34, 0.22, 0.03)),
        origin=Origin(xyz=(0.0, 0.0, -0.015)),
        material=cast_iron,
        name="mount_flange",
    )
    differential_housing.visual(
        Box((0.140, 0.120, 0.100)),
        origin=Origin(xyz=(0.0, 0.0, -0.050)),
        material=cast_iron,
        name="mount_neck",
    )
    differential_housing.visual(
        Box((0.250, 0.240, 0.190)),
        origin=Origin(xyz=(0.0, 0.0, -0.185)),
        material=cast_iron,
        name="pumpkin_shell",
    )
    differential_housing.visual(
        Box((0.160, 0.068, 0.160)),
        origin=Origin(xyz=(0.0, 0.154, -0.185)),
        material=cast_iron,
        name="left_transition_case",
    )
    differential_housing.visual(
        Box((0.160, 0.068, 0.160)),
        origin=Origin(xyz=(0.0, -0.154, -0.185)),
        material=cast_iron,
        name="right_transition_case",
    )
    _add_cylinder_x(
        differential_housing,
        radius=0.102,
        length=0.050,
        xyz=(0.085, 0.0, -0.185),
        material=dark_steel,
        name="front_cover",
    )
    _add_cylinder_x(
        differential_housing,
        radius=0.078,
        length=0.050,
        xyz=(-0.080, 0.0, -0.185),
        material=cast_iron,
        name="rear_bearing_cap",
    )
    differential_housing.visual(
        Box((0.180, 0.014, 0.180)),
        origin=Origin(xyz=(0.0, 0.183, -0.185)),
        material=cast_iron,
        name="left_side_plate",
    )
    differential_housing.visual(
        Box((0.180, 0.014, 0.180)),
        origin=Origin(xyz=(0.0, -0.183, -0.185)),
        material=cast_iron,
        name="right_side_plate",
    )
    _add_cylinder_x(
        differential_housing,
        radius=0.055,
        length=0.120,
        xyz=(0.0, 0.205, -0.185),
        material=cast_iron,
        name="left_pivot_boss",
    )
    _add_cylinder_x(
        differential_housing,
        radius=0.055,
        length=0.120,
        xyz=(0.0, -0.205, -0.185),
        material=cast_iron,
        name="right_pivot_boss",
    )
    differential_housing.visual(
        Box((0.18, 0.24, 0.05)),
        origin=Origin(xyz=(0.0, 0.0, -0.295)),
        material=cast_iron,
        name="lower_rib",
    )
    for bolt_x in (-0.110, 0.110):
        for bolt_y in (-0.095, 0.095):
            differential_housing.visual(
                Cylinder(radius=0.010, length=0.020),
                origin=Origin(xyz=(bolt_x, bolt_y, 0.010)),
                material=machined_steel,
                name=f"mount_bolt_{'r' if bolt_x > 0 else 'l'}_{'u' if bolt_y > 0 else 'd'}",
            )
    cover_bolt_radius = 0.074
    for bolt_index in range(6):
        angle = 2.0 * pi * bolt_index / 6.0
        _add_cylinder_x(
            differential_housing,
            radius=0.008,
            length=0.022,
            xyz=(
                0.110,
                cover_bolt_radius * cos(angle),
                -0.185 + cover_bolt_radius * sin(angle),
            ),
            material=machined_steel,
            name=f"front_cover_bolt_{bolt_index}",
        )

    left_half_axle = _build_half_axle(
        model,
        name="left_half_axle",
        side_sign=1.0,
        tube_paint=tube_paint,
        machined_steel=machined_steel,
        rubber=rubber,
    )
    right_half_axle = _build_half_axle(
        model,
        name="right_half_axle",
        side_sign=-1.0,
        tube_paint=tube_paint,
        machined_steel=machined_steel,
        rubber=rubber,
    )
    left_hub = _build_hub(
        model,
        name="left_hub",
        side_sign=1.0,
        machined_steel=machined_steel,
        dark_steel=dark_steel,
    )
    right_hub = _build_hub(
        model,
        name="right_hub",
        side_sign=-1.0,
        machined_steel=machined_steel,
        dark_steel=dark_steel,
    )

    model.articulation(
        "beam_to_differential",
        ArticulationType.FIXED,
        parent=center_beam,
        child=differential_housing,
        origin=Origin(xyz=(0.0, 0.0, 0.040)),
    )
    model.articulation(
        "left_swing",
        ArticulationType.REVOLUTE,
        parent=differential_housing,
        child=left_half_axle,
        origin=Origin(xyz=(0.0, 0.230, -0.185)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.5, lower=-0.55, upper=0.35),
    )
    model.articulation(
        "right_swing",
        ArticulationType.REVOLUTE,
        parent=differential_housing,
        child=right_half_axle,
        origin=Origin(xyz=(0.0, -0.230, -0.185)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.5, lower=-0.35, upper=0.55),
    )
    model.articulation(
        "left_hub_spin",
        ArticulationType.CONTINUOUS,
        parent=left_half_axle,
        child=left_hub,
        origin=Origin(xyz=(0.0, 0.520, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=35.0, velocity=18.0),
    )
    model.articulation(
        "right_hub_spin",
        ArticulationType.CONTINUOUS,
        parent=right_half_axle,
        child=right_hub,
        origin=Origin(xyz=(0.0, -0.520, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=35.0, velocity=18.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
