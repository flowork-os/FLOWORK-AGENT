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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
TRAVERSE_UPPER = 0.55
RECOIL_TRAVEL = 0.32
ELEVATION_UPPER = 0.32
def _barrel_body_shape() -> cq.Workplane:
    """Stubby cast-iron carronade tube, revolved about its local +X bore axis."""
    outer = (
        cq.Workplane("XZ")
        .moveTo(-0.22, 0.0)
        .lineTo(-0.22, 0.145)
        .lineTo(-0.14, 0.175)
        .lineTo(0.05, 0.168)
        .lineTo(0.18, 0.145)
        .lineTo(0.56, 0.118)
        .lineTo(0.70, 0.122)
        .lineTo(0.74, 0.168)
        .lineTo(0.84, 0.170)
        .lineTo(0.86, 0.145)
        .lineTo(0.86, 0.0)
        .close()
        .revolve(360.0, axisStart=(-0.30, 0.0, 0.0), axisEnd=(1.0, 0.0, 0.0))
    )

    bore = (
        cq.Workplane("YZ")
        .circle(0.064)
        .extrude(0.96)
        .translate((-0.03, 0.0, 0.0))
    )
    return outer.cut(bore)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="naval_carronade")

    model.material("dark_cast_iron", rgba=(0.015, 0.016, 0.015, 1.0))
    model.material("worn_iron", rgba=(0.08, 0.075, 0.065, 1.0))
    model.material("oiled_oak", rgba=(0.50, 0.31, 0.15, 1.0))
    model.material("end_grain", rgba=(0.34, 0.19, 0.09, 1.0))
    model.material("deck_oak", rgba=(0.58, 0.40, 0.22, 1.0))
    model.material("dark_groove", rgba=(0.045, 0.030, 0.018, 1.0))

    deck = model.part("deck")
    deck.visual(
        Box((2.45, 1.35, 0.08)),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material="deck_oak",
        name="deck_planks",
    )
    for index, y in enumerate((-0.45, -0.225, 0.0, 0.225, 0.45)):
        deck.visual(
            Box((2.46, 0.010, 0.006)),
            origin=Origin(xyz=(0.0, y, 0.043)),
            material="dark_groove",
            name=f"plank_seam_{index}",
        )
    deck.visual(
        Cylinder(radius=0.30, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.045)),
        material="worn_iron",
        name="traverse_wear_plate",
    )

    slide_base = model.part("slide_base")
    slide_base.visual(
        Cylinder(radius=0.23, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, 0.0275)),
        material="worn_iron",
        name="pivot_plate",
    )
    slide_base.visual(
        Cylinder(radius=0.045, length=0.095),
        origin=Origin(xyz=(0.0, 0.0, 0.0875)),
        material="worn_iron",
        name="pivot_pin",
    )
    slide_base.visual(
        Box((1.55, 0.36, 0.10)),
        origin=Origin(xyz=(0.10, 0.0, 0.09)),
        material="oiled_oak",
        name="rail_plank",
    )
    slide_base.visual(
        Box((1.42, 0.045, 0.010)),
        origin=Origin(xyz=(0.11, -0.14, 0.145)),
        material="worn_iron",
        name="wear_strip_0",
    )
    slide_base.visual(
        Box((1.42, 0.045, 0.010)),
        origin=Origin(xyz=(0.11, 0.14, 0.145)),
        material="worn_iron",
        name="wear_strip_1",
    )
    slide_base.visual(
        Box((0.22, 0.42, 0.08)),
        origin=Origin(xyz=(-0.58, 0.0, 0.10)),
        material="end_grain",
        name="rear_stop",
    )
    slide_base.visual(
        Box((0.18, 0.42, 0.08)),
        origin=Origin(xyz=(0.78, 0.0, 0.10)),
        material="end_grain",
        name="front_stop",
    )

    carriage = model.part("carriage_bed")
    carriage.visual(
        Box((0.64, 0.56, 0.12)),
        origin=Origin(xyz=(0.0, 0.0, 0.06)),
        material="oiled_oak",
        name="sled",
    )
    carriage.visual(
        Box((0.10, 0.58, 0.20)),
        origin=Origin(xyz=(-0.25, 0.0, 0.22)),
        material="end_grain",
        name="rear_transom",
    )
    carriage.visual(
        Box((0.09, 0.58, 0.12)),
        origin=Origin(xyz=(0.27, 0.0, 0.16)),
        material="end_grain",
        name="front_transom",
    )
    for index, y in enumerate((-0.30, 0.30)):
        carriage.visual(
            Box((0.46, 0.08, 0.34)),
            origin=Origin(xyz=(0.04, y, 0.29)),
            material="oiled_oak",
            name=f"cheek_{index}",
        )
    carriage.visual(
        Cylinder(radius=0.085, length=0.050),
        origin=Origin(xyz=(0.05, -0.235, 0.40), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="worn_iron",
        name="bearing_boss_0",
    )
    carriage.visual(
        Cylinder(radius=0.085, length=0.050),
        origin=Origin(xyz=(0.05, 0.235, 0.40), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="worn_iron",
        name="bearing_boss_1",
    )
    carriage.visual(
        Box((0.10, 0.10, 0.08)),
        origin=Origin(xyz=(-0.18, 0.0, 0.175)),
        material="worn_iron",
        name="elevation_screw_block",
    )
    carriage.visual(
        Cylinder(radius=0.018, length=0.12),
        origin=Origin(xyz=(-0.18, 0.0, 0.135)),
        material="worn_iron",
        name="elevation_screw",
    )

    barrel = model.part("barrel")
    barrel.visual(
        mesh_from_cadquery(_barrel_body_shape(), "barrel_body", tolerance=0.0012),
        material="dark_cast_iron",
        name="barrel_body",
    )
    barrel.visual(
        Cylinder(radius=0.055, length=0.48),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="dark_cast_iron",
        name="trunnion_axle",
    )
    barrel.visual(
        Cylinder(radius=0.060, length=0.14),
        origin=Origin(xyz=(-0.275, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material="dark_cast_iron",
        name="cascabel_neck",
    )
    barrel.visual(
        Sphere(radius=0.075),
        origin=Origin(xyz=(-0.36, 0.0, 0.0)),
        material="dark_cast_iron",
        name="cascabel_knob",
    )
    barrel.visual(
        Cylinder(radius=0.018, length=0.035),
        origin=Origin(xyz=(-0.09, 0.0, 0.175)),
        material="dark_cast_iron",
        name="touch_hole_boss",
    )

    model.articulation(
        "deck_to_slide_base",
        ArticulationType.REVOLUTE,
        parent=deck,
        child=slide_base,
        origin=Origin(xyz=(0.0, 0.0, 0.04)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-TRAVERSE_UPPER, upper=TRAVERSE_UPPER, effort=400.0, velocity=0.35),
    )
    model.articulation(
        "slide_base_to_carriage",
        ArticulationType.PRISMATIC,
        parent=slide_base,
        child=carriage,
        origin=Origin(xyz=(0.15, 0.0, 0.15)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=RECOIL_TRAVEL, effort=1200.0, velocity=0.45),
    )
    model.articulation(
        "carriage_to_barrel",
        ArticulationType.REVOLUTE,
        parent=carriage,
        child=barrel,
        origin=Origin(xyz=(0.05, 0.0, 0.40)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.08, upper=ELEVATION_UPPER, effort=250.0, velocity=0.6),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
