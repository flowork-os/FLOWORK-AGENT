# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_crankset_and_pedal_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_crankset_and_pedal_assembly

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
PI = math.pi
def _annular_cylinder_x(
    *,
    outer_radius: float,
    inner_radius: float,
    length: float,
    x: float = 0.0,
) -> cq.Workplane:
    """A hollow cylinder whose axis is the model X axis."""

    outer = cq.Workplane("YZ").circle(outer_radius).extrude(length / 2.0, both=True)
    inner = cq.Workplane("YZ").circle(inner_radius).extrude(length, both=True)
    return outer.cut(inner).translate((x, 0.0, 0.0))
def _annular_cylinder_y(
    *,
    outer_radius: float,
    inner_radius: float,
    length: float,
    y: float = 0.0,
) -> cq.Workplane:
    """A hollow cylinder whose axis is the model Y axis."""

    outer = cq.Workplane("XZ").circle(outer_radius).extrude(length / 2.0, both=True)
    inner = cq.Workplane("XZ").circle(inner_radius).extrude(length, both=True)
    return outer.cut(inner).translate((0.0, y, 0.0))
def _bottom_bracket_shell() -> cq.Workplane:
    """Sealed cartridge body with real through-bore for the spindle."""

    body = _annular_cylinder_x(outer_radius=0.025, inner_radius=0.0115, length=0.108)
    for x in (-0.058, 0.058):
        body = body.union(
            _annular_cylinder_x(
                outer_radius=0.030,
                inner_radius=0.0125,
                length=0.012,
                x=x,
            )
        )
    return body
def _chainring() -> cq.Workplane:
    """Single small chainring: thin toothed annulus in the YZ plane."""

    teeth = 36
    outer_radius = 0.074
    root_radius = 0.067
    points: list[tuple[float, float]] = []
    for i in range(teeth * 2):
        angle = 2.0 * PI * i / (teeth * 2)
        radius = outer_radius if i % 2 == 0 else root_radius
        points.append((radius * math.sin(angle), radius * math.cos(angle)))

    ring = cq.Workplane("YZ").polyline(points).close().extrude(0.002, both=True)
    center_cut = cq.Workplane("YZ").circle(0.046).extrude(0.006, both=True)
    ring = ring.cut(center_cut)

    # Five relief holes make the part read as a bicycle chainring, not a disk.
    for i in range(5):
        angle = 2.0 * PI * i / 5.0 + PI / 10.0
        y = 0.056 * math.sin(angle)
        z = 0.056 * math.cos(angle)
        relief = (
            cq.Workplane("YZ")
            .center(y, z)
            .circle(0.0055)
            .extrude(0.006, both=True)
        )
        ring = ring.cut(relief)

    return ring
def _torsion_spring() -> cq.Workplane:
    """Compact stack of touching spring turns around a pedal hinge pin."""

    spring = None
    for i in range(5):
        turn = _annular_cylinder_y(
            outer_radius=0.0095,
            inner_radius=0.0071,
            length=0.0018,
            y=0.0139 + i * 0.0009,
        )
        spring = turn if spring is None else spring.union(turn)
    return spring
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_folding_bike_crankset")

    satin_black = model.material("satin_black", rgba=(0.01, 0.012, 0.014, 1.0))
    dark_graphite = model.material("dark_graphite", rgba=(0.08, 0.085, 0.09, 1.0))
    brushed_aluminum = model.material("brushed_aluminum", rgba=(0.72, 0.70, 0.64, 1.0))
    polished_steel = model.material("polished_steel", rgba=(0.86, 0.84, 0.78, 1.0))
    rubber_black = model.material("rubber_black", rgba=(0.005, 0.005, 0.004, 1.0))
    spring_steel = model.material("spring_steel", rgba=(0.62, 0.64, 0.66, 1.0))

    bottom_bracket = model.part("bottom_bracket")
    bottom_bracket.visual(
        mesh_from_cadquery(_bottom_bracket_shell(), "sealed_bottom_bracket"),
        material=dark_graphite,
        name="cartridge_shell",
    )
    for x, name in ((-0.040, "bearing_race_0"), (0.040, "bearing_race_1")):
        bottom_bracket.visual(
            mesh_from_cadquery(
                _annular_cylinder_x(
                    outer_radius=0.014,
                    inner_radius=0.0110,
                    length=0.008,
                    x=x,
                ),
                name,
            ),
            material=polished_steel,
            name=name,
        )

    crankset = model.part("crankset")
    crankset.visual(
        Cylinder(radius=0.0110, length=0.190),
        origin=Origin(rpy=(0.0, PI / 2.0, 0.0)),
        material=polished_steel,
        name="spindle",
    )
    crankset.visual(
        Cylinder(radius=0.018, length=0.016),
        origin=Origin(xyz=(0.076, 0.0, 0.0), rpy=(0.0, PI / 2.0, 0.0)),
        material=brushed_aluminum,
        name="drive_hub",
    )
    crankset.visual(
        Cylinder(radius=0.018, length=0.016),
        origin=Origin(xyz=(-0.076, 0.0, 0.0), rpy=(0.0, PI / 2.0, 0.0)),
        material=brushed_aluminum,
        name="opposite_hub",
    )
    crankset.visual(
        Box((0.014, 0.022, 0.118)),
        origin=Origin(xyz=(0.074, 0.0, -0.068)),
        material=brushed_aluminum,
        name="drive_arm",
    )
    crankset.visual(
        Box((0.014, 0.022, 0.118)),
        origin=Origin(xyz=(-0.074, 0.0, 0.068)),
        material=brushed_aluminum,
        name="opposite_arm",
    )
    for x, z, name in (
        (0.087, -0.130, "drive_boss"),
        (-0.087, 0.130, "opposite_boss"),
    ):
        crankset.visual(
            Cylinder(radius=0.0155, length=0.025),
            origin=Origin(xyz=(x, 0.0, z), rpy=(0.0, PI / 2.0, 0.0)),
            material=brushed_aluminum,
            name=name,
        )

    crankset.visual(
        mesh_from_cadquery(_chainring(), "small_toothed_chainring"),
        origin=Origin(xyz=(0.068, 0.0, 0.0)),
        material=satin_black,
        name="chainring",
    )
    crankset.visual(
        Cylinder(radius=0.020, length=0.012),
        origin=Origin(xyz=(0.074, 0.0, 0.0), rpy=(0.0, PI / 2.0, 0.0)),
        material=brushed_aluminum,
        name="spider_hub",
    )
    for i in range(5):
        angle = 2.0 * PI * i / 5.0
        mid_radius = 0.035
        crankset.visual(
            Box((0.007, 0.010, 0.046)),
            origin=Origin(
                xyz=(0.072, mid_radius * math.sin(angle), mid_radius * math.cos(angle)),
                rpy=(-angle, 0.0, 0.0),
            ),
            material=brushed_aluminum,
            name=f"spider_arm_{i}",
        )
        bolt_radius = 0.053
        crankset.visual(
            Cylinder(radius=0.0033, length=0.004),
            origin=Origin(
                xyz=(0.075, bolt_radius * math.sin(angle), bolt_radius * math.cos(angle)),
                rpy=(0.0, PI / 2.0, 0.0),
            ),
            material=polished_steel,
            name=f"chainring_bolt_{i}",
        )

    def add_parent_knuckle(side: float, z: float, prefix: str) -> None:
        hinge_x = side * 0.107
        for y, suffix in ((0.019, "upper"), (-0.019, "lower")):
            crankset.visual(
                Box((0.018, 0.010, 0.024)),
                origin=Origin(xyz=(hinge_x, y, z)),
                material=brushed_aluminum,
                name=f"{prefix}_ear_{suffix}",
            )
        crankset.visual(
            mesh_from_cadquery(_torsion_spring(), f"{prefix}_spring"),
            origin=Origin(xyz=(hinge_x, 0.0, z)),
            material=spring_steel,
            name=f"{prefix}_spring",
        )

    add_parent_knuckle(1.0, -0.130, "drive")
    add_parent_knuckle(-1.0, 0.130, "opposite")

    def add_pedal(part_name: str, side: float) -> None:
        pedal = model.part(part_name)
        pedal.visual(
            Cylinder(radius=0.0065, length=0.026),
            origin=Origin(rpy=(-PI / 2.0, 0.0, 0.0)),
            material=polished_steel,
            name="hinge_barrel",
        )
        pedal.visual(
            Box((0.020, 0.034, 0.008)),
            origin=Origin(xyz=(side * 0.014, 0.0, 0.0)),
            material=dark_graphite,
            name="inner_bridge",
        )
        pedal.visual(
            Box((0.074, 0.008, 0.011)),
            origin=Origin(xyz=(side * 0.050, 0.026, 0.0)),
            material=dark_graphite,
            name="front_rail",
        )
        pedal.visual(
            Box((0.074, 0.008, 0.011)),
            origin=Origin(xyz=(side * 0.050, -0.026, 0.0)),
            material=dark_graphite,
            name="rear_rail",
        )
        pedal.visual(
            Box((0.010, 0.060, 0.011)),
            origin=Origin(xyz=(side * 0.015, 0.0, 0.0)),
            material=dark_graphite,
            name="inner_rail",
        )
        pedal.visual(
            Box((0.010, 0.060, 0.011)),
            origin=Origin(xyz=(side * 0.085, 0.0, 0.0)),
            material=dark_graphite,
            name="outer_rail",
        )
        for x_local in (0.038, 0.067):
            for y in (-0.026, 0.026):
                pedal.visual(
                    Box((0.014, 0.010, 0.003)),
                    origin=Origin(xyz=(side * x_local, y, 0.007)),
                    material=rubber_black,
                    name=f"tread_{x_local:.3f}_{'front' if y > 0.0 else 'rear'}",
                )
        return None

    add_pedal("drive_pedal", 1.0)
    add_pedal("opposite_pedal", -1.0)

    model.articulation(
        "bottom_bracket_to_crank",
        ArticulationType.CONTINUOUS,
        parent=bottom_bracket,
        child=crankset,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=30.0, velocity=12.0),
    )
    model.articulation(
        "crank_to_drive_pedal",
        ArticulationType.REVOLUTE,
        parent=crankset,
        child="drive_pedal",
        origin=Origin(xyz=(0.107, 0.0, -0.130)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=4.0, lower=0.0, upper=PI / 2.0),
    )
    model.articulation(
        "crank_to_opposite_pedal",
        ArticulationType.REVOLUTE,
        parent=crankset,
        child="opposite_pedal",
        origin=Origin(xyz=(-0.107, 0.0, 0.130)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=4.0, lower=0.0, upper=PI / 2.0),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
