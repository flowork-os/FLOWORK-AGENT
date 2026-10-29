# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, adjustable_weight_bench_with_hinged_backrest, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: adjustable_weight_bench_with_hinged_backrest

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
def _rounded_pad(length: float, width: float, thickness: float, name: str):
    pad = cq.Workplane("XY").box(length, width, thickness).edges().fillet(min(width, thickness) * 0.18)
    return mesh_from_cadquery(pad, name)
def _selector_rail(name: str):
    rail = cq.Workplane("XZ").rect(0.28, 0.065).extrude(0.006, both=True)
    holes = (
        cq.Workplane("XZ")
        .pushPoints([(-0.10, -0.012), (-0.05, 0.001), (0.0, 0.013), (0.05, 0.024), (0.10, 0.031)])
        .circle(0.008)
        .extrude(0.02, both=True)
    )
    return mesh_from_cadquery(rail.cut(holes), name)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="adjustable_decline_bench")

    frame_paint = model.material("frame_paint", rgba=(0.17, 0.18, 0.19, 1.0))
    upholstery = model.material("upholstery", rgba=(0.11, 0.11, 0.12, 1.0))
    hinge_steel = model.material("hinge_steel", rgba=(0.55, 0.57, 0.60, 1.0))
    trim = model.material("trim", rgba=(0.23, 0.24, 0.25, 1.0))
    foam = model.material("foam", rgba=(0.16, 0.16, 0.17, 1.0))
    wheel_rubber = model.material("wheel_rubber", rgba=(0.08, 0.08, 0.08, 1.0))

    frame = model.part("frame")
    frame.visual(Box((0.16, 0.56, 0.06)), origin=Origin(xyz=(-0.67, 0.0, 0.03)), material=frame_paint, name="rear_stabilizer")
    frame.visual(Box((0.08, 0.10, 0.28)), origin=Origin(xyz=(-0.58, 0.0, 0.17)), material=frame_paint, name="rear_upright")
    frame.visual(Box((1.16, 0.10, 0.08)), origin=Origin(xyz=(0.04, 0.0, 0.21)), material=frame_paint, name="main_spine")
    frame.visual(Box((0.10, 0.14, 0.14)), origin=Origin(xyz=(0.03, 0.0, 0.30)), material=frame_paint, name="back_hinge_support")
    frame.visual(Box((0.10, 0.16, 0.12)), origin=Origin(xyz=(0.35, 0.0, 0.29)), material=frame_paint, name="seat_hinge_support")
    frame.visual(Box((0.16, 0.50, 0.06)), origin=Origin(xyz=(0.65, 0.0, 0.03)), material=frame_paint, name="front_stabilizer")
    frame.visual(Box((0.08, 0.10, 0.32)), origin=Origin(xyz=(0.57, 0.0, 0.19)), material=frame_paint, name="front_upright")
    frame.visual(Box((0.24, 0.08, 0.08)), origin=Origin(xyz=(0.69, 0.0, 0.25)), material=frame_paint, name="front_bridge")
    frame.visual(Box((0.32, 0.08, 0.05)), origin=Origin(xyz=(0.22, 0.0, 0.29)), material=trim, name="seat_support_rail")
    frame.visual(Box((0.12, 0.10, 0.28)), origin=Origin(xyz=(0.81, 0.0, 0.18)), material=frame_paint, name="roller_post")
    frame.visual(Box((0.08, 0.10, 0.08)), origin=Origin(xyz=(0.87, 0.0, 0.28)), material=frame_paint, name="roller_head")
    frame.visual(Box((0.04, 0.08, 0.16)), origin=Origin(xyz=(-0.67, -0.24, 0.10)), material=frame_paint, name="wheel_bracket_0")
    frame.visual(Box((0.04, 0.08, 0.16)), origin=Origin(xyz=(-0.67, 0.24, 0.10)), material=frame_paint, name="wheel_bracket_1")
    frame.visual(
        _selector_rail("selector_rail"),
        origin=Origin(xyz=(-0.11, 0.0, 0.28)),
        material=hinge_steel,
        name="selector_rail",
    )

    back_pad = model.part("back_pad")
    back_pad.visual(
        _rounded_pad(0.92, 0.31, 0.07, "backrest_pad"),
        origin=Origin(xyz=(-0.46, 0.0, 0.055)),
        material=upholstery,
        name="backrest_pad",
    )
    back_pad.visual(
        Box((0.40, 0.10, 0.04)),
        origin=Origin(xyz=(-0.23, 0.0, 0.00)),
        material=frame_paint,
        name="back_support_arm",
    )
    back_pad.visual(
        Cylinder(radius=0.016, length=0.14),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=hinge_steel,
        name="back_hinge_barrel",
    )
    back_pad.visual(
        Box((0.03, 0.08, 0.03)),
        origin=Origin(xyz=(-0.015, 0.0, 0.0)),
        material=hinge_steel,
        name="back_hinge_lug",
    )
    back_pad.visual(
        Box((0.05, 0.12, 0.02)),
        origin=Origin(xyz=(-0.89, 0.0, 0.01)),
        material=trim,
        name="back_tail",
    )
    back_pad.visual(
        Box((0.05, 0.028, 0.04)),
        origin=Origin(xyz=(-0.18, 0.041, 0.0)),
        material=hinge_steel,
        name="selector_collar",
    )

    seat_pad = model.part("seat_pad")
    seat_pad.visual(
        _rounded_pad(0.30, 0.29, 0.06, "seat_pad"),
        origin=Origin(xyz=(-0.15, 0.0, 0.045)),
        material=upholstery,
        name="seat_pad",
    )
    seat_pad.visual(
        Box((0.17, 0.10, 0.035)),
        origin=Origin(xyz=(-0.085, 0.0, -0.0025)),
        material=frame_paint,
        name="seat_support_arm",
    )
    seat_pad.visual(
        Cylinder(radius=0.014, length=0.14),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=hinge_steel,
        name="seat_hinge_barrel",
    )
    seat_pad.visual(
        Box((0.05, 0.12, 0.02)),
        origin=Origin(xyz=(-0.25, 0.0, 0.01)),
        material=trim,
        name="seat_tail",
    )

    leg_roller_0 = model.part("leg_roller_0")
    leg_roller_0.visual(
        Cylinder(radius=0.07, length=0.16),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=foam,
        name="roller_body",
    )
    leg_roller_0.visual(
        Cylinder(radius=0.025, length=0.10),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=hinge_steel,
        name="roller_core",
    )

    leg_roller_1 = model.part("leg_roller_1")
    leg_roller_1.visual(
        Cylinder(radius=0.07, length=0.16),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=foam,
        name="roller_body",
    )
    leg_roller_1.visual(
        Cylinder(radius=0.025, length=0.10),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=hinge_steel,
        name="roller_core",
    )

    wheel_0 = model.part("wheel_0")
    wheel_0.visual(
        Cylinder(radius=0.06, length=0.05),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=wheel_rubber,
        name="wheel_tire",
    )
    wheel_0.visual(
        Cylinder(radius=0.032, length=0.056),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=hinge_steel,
        name="wheel_hub",
    )

    wheel_1 = model.part("wheel_1")
    wheel_1.visual(
        Cylinder(radius=0.06, length=0.05),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=wheel_rubber,
        name="wheel_tire",
    )
    wheel_1.visual(
        Cylinder(radius=0.032, length=0.056),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=hinge_steel,
        name="wheel_hub",
    )

    selector_knob = model.part("selector_knob")
    selector_knob.visual(
        Cylinder(radius=0.007, length=0.02),
        origin=Origin(xyz=(0.0, 0.01, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material=hinge_steel,
        name="knob_shaft",
    )
    selector_knob.visual(
        Cylinder(radius=0.018, length=0.018),
        origin=Origin(xyz=(0.0, 0.029, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material=trim,
        name="knob_head",
    )

    model.articulation(
        "back_hinge",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=back_pad,
        origin=Origin(xyz=(0.03, 0.0, 0.39)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=150.0, velocity=1.5, lower=-0.35, upper=1.15),
    )
    model.articulation(
        "seat_hinge",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=seat_pad,
        origin=Origin(xyz=(0.35, 0.0, 0.37)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=90.0, velocity=1.5, lower=0.0, upper=0.45),
    )
    model.articulation(
        "leg_roller_spin_0",
        ArticulationType.CONTINUOUS,
        parent=frame,
        child=leg_roller_0,
        origin=Origin(xyz=(0.87, -0.13, 0.28)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=25.0, velocity=20.0),
    )
    model.articulation(
        "leg_roller_spin_1",
        ArticulationType.CONTINUOUS,
        parent=frame,
        child=leg_roller_1,
        origin=Origin(xyz=(0.87, 0.13, 0.28)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=25.0, velocity=20.0),
    )
    model.articulation(
        "wheel_spin_0",
        ArticulationType.CONTINUOUS,
        parent=frame,
        child=wheel_0,
        origin=Origin(xyz=(-0.67, -0.305, 0.10)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=20.0),
    )
    model.articulation(
        "wheel_spin_1",
        ArticulationType.CONTINUOUS,
        parent=frame,
        child=wheel_1,
        origin=Origin(xyz=(-0.67, 0.305, 0.10)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=20.0),
    )
    model.articulation(
        "selector_pull",
        ArticulationType.PRISMATIC,
        parent=back_pad,
        child=selector_knob,
        origin=Origin(xyz=(-0.18, 0.055, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=0.12, lower=0.0, upper=0.03),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
