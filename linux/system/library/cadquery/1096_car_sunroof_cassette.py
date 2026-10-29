# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_sunroof_cassette, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_sunroof_cassette

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

class MotionProperties:
    def __init__(self, damping=None, friction=None):
        self.damping = damping
        self.friction = friction

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
ALUMINIUM = Material("satin_anodized_aluminium", rgba=(0.72, 0.74, 0.73, 1.0))
BLACK_RUBBER = Material("black_epdm_gasket", rgba=(0.006, 0.006, 0.005, 1.0))
SHADOW_PLASTIC = Material("matte_black_plastic", rgba=(0.015, 0.014, 0.013, 1.0))
GLASS = Material("smoked_tempered_glass", rgba=(0.10, 0.18, 0.23, 0.42))
FRIT = Material("black_ceramic_frit", rgba=(0.0, 0.0, 0.0, 0.88))
FABRIC = Material("woven_grey_sunshade_fabric", rgba=(0.30, 0.31, 0.30, 1.0))
def _rounded_glass_panel() -> object:
    """A shallow tempered glass slab with radiused plan-view corners."""

    return (
        cq.Workplane("XY")
        .box(0.740, 0.560, 0.008)
        .edges("|Z")
        .fillet(0.025)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="electric_tilt_moonroof_cassette")
    for material in (ALUMINIUM, BLACK_RUBBER, SHADOW_PLASTIC, GLASS, FRIT, FABRIC):
        model.materials.append(material)

    frame = model.part("cassette_frame")

    # Vehicle-intrinsic frame: X is left-right, Y is front-to-rear, Z is upward.
    # The aluminium cassette is a continuous perimeter with overlapping miter
    # regions at the corners, leaving a clear central roof aperture.
    frame.visual(
        Box((0.090, 0.780, 0.035)),
        origin=Origin(xyz=(-0.455, 0.000, 0.000)),
        material=ALUMINIUM,
        name="side_rail_0",
    )
    frame.visual(
        Box((0.090, 0.780, 0.035)),
        origin=Origin(xyz=(0.455, 0.000, 0.000)),
        material=ALUMINIUM,
        name="side_rail_1",
    )
    frame.visual(
        Box((1.000, 0.100, 0.035)),
        origin=Origin(xyz=(0.000, -0.340, 0.000)),
        material=ALUMINIUM,
        name="front_rail",
    )
    frame.visual(
        Box((1.000, 0.100, 0.035)),
        origin=Origin(xyz=(0.000, 0.340, 0.000)),
        material=ALUMINIUM,
        name="rear_rail",
    )

    # Raised EPDM seals around the aperture and lower interior shade tracks.
    frame.visual(
        Box((0.018, 0.610, 0.010)),
        origin=Origin(xyz=(-0.392, 0.000, 0.022)),
        material=BLACK_RUBBER,
        name="side_gasket_0",
    )
    frame.visual(
        Box((0.018, 0.610, 0.010)),
        origin=Origin(xyz=(0.392, 0.000, 0.022)),
        material=BLACK_RUBBER,
        name="side_gasket_1",
    )
    frame.visual(
        Box((0.740, 0.018, 0.008)),
        origin=Origin(xyz=(0.000, -0.282, 0.016)),
        material=BLACK_RUBBER,
        name="front_gasket",
    )
    frame.visual(
        Box((0.740, 0.018, 0.010)),
        origin=Origin(xyz=(0.000, 0.292, 0.022)),
        material=BLACK_RUBBER,
        name="rear_gasket",
    )
    for x, name in ((-0.403, "shade_track_0"), (0.403, "shade_track_1")):
        frame.visual(
            Box((0.024, 0.620, 0.020)),
            origin=Origin(xyz=(x, 0.000, -0.024)),
            material=SHADOW_PLASTIC,
            name=name,
        )

    # Front hinge cross-shaft, two fixed bearing ears, and an electric tilt
    # drive pack on one cassette side.
    frame.visual(
        Cylinder(radius=0.006, length=0.760),
        origin=Origin(xyz=(0.000, -0.300, 0.022), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=ALUMINIUM,
        name="front_hinge_pin",
    )
    for x, name in ((-0.285, "hinge_ear_0"), (0.285, "hinge_ear_1")):
        frame.visual(
            Box((0.035, 0.020, 0.050)),
            origin=Origin(xyz=(x, -0.309, 0.004)),
            material=ALUMINIUM,
            name=name,
        )
    frame.visual(
        Box((0.070, 0.125, 0.052)),
        origin=Origin(xyz=(0.545, 0.120, -0.020)),
        material=SHADOW_PLASTIC,
        name="drive_motor",
    )
    frame.visual(
        Box((0.065, 0.040, 0.024)),
        origin=Origin(xyz=(0.500, 0.120, -0.012)),
        material=ALUMINIUM,
        name="motor_bracket",
    )
    frame.visual(
        Cylinder(radius=0.006, length=0.430),
        origin=Origin(xyz=(0.414, 0.075, -0.030), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=SHADOW_PLASTIC,
        name="drive_cable_tube",
    )

    # Roller shade bearing brackets are fixed to the front rail; the roller
    # itself is articulated so its spring-tension winding can follow the shade.
    for x, name in ((-0.360, "roller_bracket_0"), (0.360, "roller_bracket_1")):
        frame.visual(
            Box((0.014, 0.040, 0.052)),
            origin=Origin(xyz=(x, -0.335, -0.040)),
            material=ALUMINIUM,
            name=name,
        )

    glass = model.part("glass_panel")
    glass.visual(
        mesh_from_cadquery(_rounded_glass_panel(), "rounded_tempered_glass", tolerance=0.0008),
        origin=Origin(xyz=(0.000, 0.300, 0.006)),
        material=GLASS,
        name="glass_panel",
    )
    # Opaque ceramic frit border bonded to the glass perimeter.
    glass.visual(
        Box((0.740, 0.035, 0.0015)),
        origin=Origin(xyz=(0.000, 0.036, 0.010)),
        material=FRIT,
        name="front_frit",
    )
    glass.visual(
        Box((0.740, 0.035, 0.0015)),
        origin=Origin(xyz=(0.000, 0.564, 0.010)),
        material=FRIT,
        name="rear_frit",
    )
    glass.visual(
        Box((0.035, 0.560, 0.0015)),
        origin=Origin(xyz=(-0.352, 0.300, 0.010)),
        material=FRIT,
        name="side_frit_0",
    )
    glass.visual(
        Box((0.035, 0.560, 0.0015)),
        origin=Origin(xyz=(0.352, 0.300, 0.010)),
        material=FRIT,
        name="side_frit_1",
    )
    for x, name in ((-0.225, "glass_hinge_lug_0"), (0.225, "glass_hinge_lug_1")):
        glass.visual(
            Box((0.095, 0.040, 0.012)),
            origin=Origin(xyz=(x, 0.047, -0.002)),
            material=SHADOW_PLASTIC,
            name=name,
        )
    for x, name in ((-0.225, "hinge_knuckle_0"), (0.225, "hinge_knuckle_1")):
        glass.visual(
            Cylinder(radius=0.008, length=0.085),
            origin=Origin(xyz=(x, 0.000, 0.000), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=SHADOW_PLASTIC,
            name=name,
        )
    for x, name in ((-0.225, "hinge_strap_0"), (0.225, "hinge_strap_1")):
        glass.visual(
            Box((0.085, 0.024, 0.006)),
            origin=Origin(xyz=(x, 0.014, 0.005)),
            material=SHADOW_PLASTIC,
            name=name,
        )
    for x, name in ((-0.305, "rear_lift_pad_0"), (0.305, "rear_lift_pad_1")):
        glass.visual(
            Box((0.080, 0.035, 0.010)),
            origin=Origin(xyz=(x, 0.555, -0.001)),
            material=SHADOW_PLASTIC,
            name=name,
        )

    shade_roller = model.part("shade_roller")
    shade_roller.visual(
        Cylinder(radius=0.025, length=0.670),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=FABRIC,
        name="fabric_roll",
    )
    shade_roller.visual(
        Cylinder(radius=0.028, length=0.030),
        origin=Origin(xyz=(-0.350, 0.000, 0.000), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=SHADOW_PLASTIC,
        name="spring_end_cap",
    )
    shade_roller.visual(
        Cylinder(radius=0.028, length=0.030),
        origin=Origin(xyz=(0.350, 0.000, 0.000), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=SHADOW_PLASTIC,
        name="idle_end_cap",
    )

    shade = model.part("sunshade")
    shade.visual(
        Box((0.660, 0.610, 0.003)),
        origin=Origin(xyz=(0.000, -0.305, 0.000)),
        material=FABRIC,
        name="shade_cloth",
    )
    shade.visual(
        Box((0.700, 0.024, 0.025)),
        origin=Origin(xyz=(0.000, 0.000, 0.000)),
        material=SHADOW_PLASTIC,
        name="pull_bar",
    )
    for x, name in ((-0.392, "guide_shoe_0"), (0.392, "guide_shoe_1")):
        shade.visual(
            Box((0.035, 0.045, 0.012)),
            origin=Origin(xyz=(x, -0.004, -0.002)),
            material=SHADOW_PLASTIC,
            name=name,
        )
    for x, name in ((-0.365, "guide_stem_0"), (0.365, "guide_stem_1")):
        shade.visual(
            Box((0.030, 0.030, 0.010)),
            origin=Origin(xyz=(x, -0.004, -0.001)),
            material=SHADOW_PLASTIC,
            name=name,
        )

    glass_hinge = model.articulation(
        "front_glass_hinge",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=glass,
        origin=Origin(xyz=(0.000, -0.300, 0.022)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=120.0, velocity=0.35, lower=0.0, upper=0.23),
        motion_properties=MotionProperties(damping=1.5, friction=0.08),
    )
    glass_hinge.meta["description"] = "Tilt-only moonroof panel: positive rotation lifts the rear edge."

    shade_slide = model.articulation(
        "shade_slide",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=shade,
        origin=Origin(xyz=(0.000, 0.290, -0.032)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=35.0, velocity=0.45, lower=0.0, upper=0.520),
        motion_properties=MotionProperties(damping=0.7, friction=0.15),
    )
    shade_slide.meta["description"] = "Positive travel pulls the shade bar forward toward the spring roller."

    model.articulation(
        "roller_wind",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=shade_roller,
        origin=Origin(xyz=(0.000, -0.335, -0.060)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=8.0, lower=-15.0, upper=0.0),
        motion_properties=MotionProperties(damping=0.25, friction=0.04),
        meta={"description": "Spring-tension roller winds as the interior shade retracts."},
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
